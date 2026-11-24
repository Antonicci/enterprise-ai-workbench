import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from types import SimpleNamespace
from unittest.mock import AsyncMock
import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from workbench.config import Settings
from workbench.main import create_app
from workbench.models import Citation
from workbench.providers import Provider
from workbench.usage import Admission, PromptLimitError, GeneratedAnswer, reported_usage
from workbench.observability import Observability
from workbench.governance import runtime_report, runtime_models

def headers(token="demo-ops"):
    return {"Authorization":"Bearer "+token}

def test_admission_sliding_window_user_isolation_and_capacity():
    now=[0.0]
    guard=Admission(Settings(_env_file=None,requests_per_minute=1,max_concurrent_requests=1),clock=lambda:now[0])
    guard.acquire("one")
    with pytest.raises(HTTPException) as rejected: guard.acquire("two")
    assert rejected.value.status_code==429
    guard.release()
    guard.acquire("two");guard.release()
    with pytest.raises(HTTPException): guard.acquire("one")
    now[0]=60
    guard.acquire("one");guard.release()
    assert len(guard.buckets)==1 and guard.snapshot()["active_requests"]==0

def test_api_quota_is_applied_before_retrieval_and_excluded_from_execution_rates():
    with TestClient(create_app(Settings(_env_file=None,requests_per_minute=1))) as client:
        body={"question":"API pedidos erros"}
        assert client.post("/api/chat",headers=headers(),json=body).status_code==200
        original=client.app.state.retrieval.search
        client.app.state.retrieval.search=lambda *args: pytest.fail("Rejected call must not retrieve")
        response=client.post("/api/chat",headers=headers(),json=body)
        assert response.status_code==429 and "retry-after" in response.headers
        snapshot=client.app.state.observability.snapshot()
        assert snapshot["requests"]==1 and snapshot["rejected_requests"]==1 and snapshot["success_rate_pct"]==100
        client.app.state.retrieval.search=original
        assert client.post("/api/chat",headers=headers("demo-analyst"),json=body).status_code==200

def test_concurrent_api_rejects_excess_and_releases_after_completion_and_failure():
    started,release=Event(),Event()
    async def slow(*args):
        started.set()
        while not release.is_set(): await asyncio.sleep(.01)
        return "Resposta de teste"
    with TestClient(create_app(Settings(_env_file=None,max_concurrent_requests=1))) as client:
        client.app.state.retrieval.provider.answer=slow
        with ThreadPoolExecutor() as pool:
            future=pool.submit(client.post,"/api/chat",headers=headers(),json={"question":"API pedidos erros"})
            try:
                assert started.wait(5)
                response=client.post("/api/chat",headers=headers("demo-analyst"),json={"question":"API pedidos erros"})
                assert response.status_code==429
            finally:
                release.set()
            assert future.result(timeout=5).status_code==200
        client.app.state.retrieval.provider.answer=AsyncMock(side_effect=RuntimeError("private"))
        assert client.post("/api/chat",headers=headers(),json={"question":"API pedidos erros"}).status_code==503
        assert client.app.state.admission.snapshot()["active_requests"]==0

@pytest.mark.asyncio
async def test_full_prompt_limit_rejects_before_generation():
    settings=Settings(_env_file=None,max_prompt_chars=4000)
    provider=Provider(settings)
    provider.chat=SimpleNamespace(ainvoke=AsyncMock())
    citation=Citation(id="x",document_id="x",title="Long",excerpt="x"*10000,score=.5)
    with pytest.raises(PromptLimitError):
        await provider.answer("Investigação",[citation],None)
    provider.chat.ainvoke.assert_not_called()

def test_prompt_rejection_returns_413_and_releases_capacity():
    with TestClient(create_app(Settings(_env_file=None))) as client:
        client.app.state.retrieval.provider.answer=AsyncMock(side_effect=PromptLimitError())
        response=client.post("/api/chat",headers=headers(),json={"question":"API pedidos erros"})
        assert response.status_code==413
        assert client.app.state.admission.snapshot()["active_requests"]==0
        assert client.app.state.observability.snapshot()["rejected_requests"]==1

def test_provider_usage_cost_and_missing_metadata_are_distinct():
    settings=Settings(_env_file=None,provider="openai-compatible",api_key="synthetic",auth_tokens={"synthetic":["query-l2"]},
                      chat_model="model-a",price_model="model-a",input_price_per_million="1",output_price_per_million="2")
    response=SimpleNamespace(usage_metadata={"input_tokens":100,"output_tokens":50},response_metadata={})
    usage=reported_usage(response,settings)
    assert usage["total_tokens"]==150 and usage["cost_estimate"]["amount"]=="0.0002"
    assert reported_usage(SimpleNamespace(),settings) is None
    settings.price_model="another-model"
    assert reported_usage(response,settings)["cost_estimate"] is None
    settings.provider="ollama"
    response=SimpleNamespace(response_metadata={"prompt_eval_count":100,"eval_count":50,"eval_duration":2000000000})
    usage=reported_usage(response,settings)
    assert usage["output_tokens_per_second"]==25 and usage["cost_estimate"] is None

def test_operational_math_window_and_partial_coverage():
    metrics=Observability()
    assert metrics.snapshot()["success_rate_pct"] is None
    usage={"input_tokens":100,"output_tokens":50,"cost_estimate":{"amount":"0.0002","currency":"USD"}}
    metrics.record(100,usage=usage)
    metrics.record(300,failed=True)
    metrics.reject()
    result=metrics.snapshot()
    assert result["requests"]==2 and result["successful_requests"]==1
    assert result["success_rate_pct"]==result["error_rate_pct"]==50
    assert result["token_usage"]["reported_requests"]==1
    assert result["cost"]["estimated_amount"]=="0.0002"
    assert result["latency_p95_ms"]==300 and result["rejected_requests"]==1
    assert result["started_at"] and result["instance_id"]
    for value in range(510): metrics.record(value)
    assert metrics.snapshot()["latency_sample_size"]==500
    assert len(metrics.snapshot()["recent_requests"])==12

def test_usage_reaches_api_and_operational_snapshot():
    with TestClient(create_app(Settings(_env_file=None))) as client:
        usage={"input_tokens":12,"output_tokens":5,"total_tokens":17,"cost_estimate":None,"output_tokens_per_second":None}
        client.app.state.retrieval.provider.answer=AsyncMock(return_value=GeneratedAnswer("Resposta de teste",usage))
        result=client.post("/api/chat",headers=headers(),json={"question":"API pedidos erros"}).json()
        assert result["usage"]["total_tokens"]==17
        stats=client.get("/api/observability",headers=headers()).json()["data"]
        assert stats["token_usage"]["total_tokens"]==17 and stats["admission"]["active_requests"]==0

@pytest.mark.parametrize("path",["/api/governance","/api/runtime"])
def test_new_endpoints_require_identity(path):
    with TestClient(create_app(Settings(_env_file=None))) as client:
        assert client.get(path).status_code==401

def test_governance_matrix_and_no_false_hardware_claim():
    with TestClient(create_app(Settings(_env_file=None))) as client:
        result=client.get("/api/governance",headers=headers("demo-analyst")).json()
        assert len(result["pillars"])==6
        assert result["identity"]["mode"]=="demo"
        assert result["limits"]["max_output_tokens"]==512
        for token in ("demo-analyst","demo-manager"):
            assert client.get("/api/runtime",headers=headers(token)).status_code==403
        runtime=client.get("/api/runtime",headers=headers()).json()
        assert not runtime["available"] and runtime["declared_host"]["vram_gb"] is None

@pytest.mark.asyncio
async def test_ollama_runtime_uses_fixed_readonly_endpoints(monkeypatch):
    calls=[]
    def handler(request):
        calls.append(request.url.path)
        if request.url.path=="/api/tags":
            return httpx.Response(200,json={"models":[{"name":"tiny:3b","size":100,"details":{"quantization_level":"Q4"}}]})
        return httpx.Response(200,json={"models":[{"name":"tiny:3b","size":200,"size_vram":120,"context_length":4096}]})
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr("workbench.governance.httpx.AsyncClient",lambda **kwargs:client)
    settings=Settings(_env_file=None,provider="ollama",auth_tokens={"synthetic":["query-l2"]})
    result=await runtime_report(settings)
    assert result["available"] and calls==["/api/tags","/api/ps"]
    assert result["models"][0]["loaded_vram_bytes"]==120
    assert result["declared_host"]["vram_gb"] is None
    assert "ollama_base_url" not in result

@pytest.mark.asyncio
async def test_ollama_runtime_dependency_failure_does_not_leak_details(monkeypatch):
    def handler(request):raise httpx.ConnectError("PRIVATE-ENDPOINT-SECRET")
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr("workbench.governance.httpx.AsyncClient",lambda **kwargs:client)
    result=await runtime_report(Settings(_env_file=None,provider="ollama",auth_tokens={"synthetic":["query-l2"]}))
    assert not result["available"] and "PRIVATE" not in str(result)

def test_unloaded_model_and_unknown_memory_are_not_zero():
    models=runtime_models([{"name":"tiny","details":{}}],[])
    assert models[0]["loaded"] is False
    assert models[0]["loaded_bytes"] is None and models[0]["loaded_vram_bytes"] is None

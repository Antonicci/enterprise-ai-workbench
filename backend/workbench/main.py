import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import Settings
from .models import DocumentInput, Question
from .security import Authenticator, require, authorize_tool, ROLE_LABELS
from .retrieval import Retrieval, resolve_scope
from .seed import seed
from .mcp_client import call_metrics, call_ai_metrics
from .observability import Observability
from .usage import Admission, PromptLimitError
from .governance import governance_report, runtime_report
from .numeric_checks import compare_runbook,validate_draft,safe_report

log=logging.getLogger("workbench.audit")
log.setLevel(logging.INFO)
if not log.handlers:
    handler=logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    log.addHandler(handler)
log.propagate=False
bearer=HTTPBearer(auto_error=False)

def create_app(settings: Settings | None = None):
    settings=settings or Settings()
    authenticator=Authenticator(settings)
    @asynccontextmanager
    async def lifespan(app):
        app.state.retrieval=await asyncio.to_thread(Retrieval,settings)
        await asyncio.to_thread(seed,app.state.retrieval)
        app.state.observability=Observability()
        app.state.admission=Admission(settings)
        yield
    app=FastAPI(title="Enterprise AI Workbench",version="0.4.0",lifespan=lifespan)
    app.state.authenticator=authenticator
    def identity(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if credentials is None: raise HTTPException(status_code=401,detail="Bearer token obrigatório")
        return authenticator.authenticate(credentials.credentials)

    @app.get("/health")
    def health():
        return {"status":"ok","provider":settings.provider,"store":settings.store,"auth_mode":settings.auth_mode,"synthetic_metrics":True}

    @app.get("/api/auth/config")
    def auth_config():
        return {"mode":settings.auth_mode,"authority":settings.oidc_issuer if settings.auth_mode=="oidc" else None,
                "client_id":settings.oidc_client_id,"scope":settings.oidc_scope}

    @app.get("/api/config")
    def config(user=Depends(identity)):
        return {"provider":settings.provider,"store":settings.store,"groups":user.groups,
                "name":user.name,"roles":user.roles,"role_labels":[ROLE_LABELS[r] for r in user.roles],
                "permissions":sorted(user.permissions),"auth_mode":settings.auth_mode,
                "chat_model":settings.chat_model if settings.provider!="demo" else "extractive-demo",
                "embedding_model":settings.embedding_model if settings.provider!="demo" else "hash-demo-256",
                "metrics_allowed":"metrics:read" in user.permissions}

    @app.get("/api/governance")
    def governance(user=Depends(identity)):
        require(user,"documents:search")
        return governance_report(settings,user)

    @app.get("/api/runtime")
    async def runtime(user=Depends(identity)):
        require(user,"ai-metrics:read")
        return await runtime_report(settings)

    @app.get("/api/documents")
    def documents(request: Request,user=Depends(identity)):
        require(user,"documents:search")
        return [{"id":d.id,"title":d.title,"access_level":d.access_level,"services":d.services} for d in request.app.state.retrieval.store.list_documents(user.groups)]

    @app.get("/api/documents/{document_id}")
    def document(document_id: str,request: Request,user=Depends(identity)):
        require(user,"documents:search")
        doc=request.app.state.retrieval.store.get_document(document_id,user.groups)
        if doc is None: raise HTTPException(status_code=404,detail="Documento não encontrado")
        return doc

    @app.post("/api/documents")
    async def ingest(doc: DocumentInput,request: Request,user=Depends(identity)):
        require(user,"documents:write")
        if doc.access_level not in user.groups: raise HTTPException(status_code=403,detail="Classificação não autorizada")
        count=await asyncio.to_thread(request.app.state.retrieval.ingest,doc)
        log.info("ingest subject=%s document_id=%s level=%s chunks=%s",user.subject,doc.id,doc.access_level,count)
        return {"id":doc.id,"chunks":count}

    @app.get("/api/observability")
    async def observability(request: Request,user=Depends(identity),credentials=Depends(bearer)):
        authorize_tool(user,"get_ai_quality_metrics")
        try:
            async with asyncio.timeout(settings.request_timeout):
                data=await call_ai_metrics(settings,credentials.credentials,request.app.state.observability.snapshot())
        except Exception:
            raise HTTPException(status_code=503,detail="Consulta MCP indisponível") from None
        return {"data":{**data,"admission":request.app.state.admission.snapshot()},"tool":"get_ai_quality_metrics","transport":"MCP stdio"}

    @app.post("/api/chat")
    async def chat(body: Question,request: Request,user=Depends(identity),credentials=Depends(bearer)):
        require(user,"documents:search")
        if body.include_metrics: authorize_tool(user,"get_service_metrics",body.service)
        scope=resolve_scope(body.question,body.document_scope,body.service if body.include_metrics else None)
        if body.include_metrics and scope not in (None,"all",body.service):
            raise HTTPException(status_code=422,detail="Escopo documental e serviço MCP devem coincidir ou usar Todos.")
        try:
            request.app.state.admission.acquire(user.subject)
        except HTTPException:
            request.app.state.observability.reject()
            raise
        started,trace_id=time.perf_counter(),uuid.uuid4().hex
        retrieval=request.app.state.retrieval
        execution=[]
        usage=None
        citations=[]
        metrics=None
        try:
            async with asyncio.timeout(settings.request_timeout):
                phase=time.perf_counter()
                citations=await asyncio.to_thread(retrieval.search,body.question,user.groups,scope)
                execution.append({"id":"retrieval","label":"Recuperação autorizada","elapsed_ms":round((time.perf_counter()-phase)*1000),"detail":f"{len(citations)} trechos recuperados","status":"completed"})
                phase=time.perf_counter()
                metrics=await call_metrics(settings,credentials.credentials,body.service) if body.include_metrics else None
                execution.append({"id":"mcp","label":"Ferramenta MCP","elapsed_ms":round((time.perf_counter()-phase)*1000) if metrics else None,"detail":"get_service_metrics · dados sintéticos" if metrics else "Não solicitada","status":"completed" if metrics else "skipped"})
                phase=time.perf_counter()
                comparisons=compare_runbook(citations,metrics)
                answer=await retrieval.provider.answer(body.question,citations,metrics,comparisons)
                usage=getattr(answer,"usage",None)
                execution.append({"id":"generation","label":"Geração por LLM" if settings.provider!="demo" else "Resposta extrativa","elapsed_ms":round((time.perf_counter()-phase)*1000),"detail":settings.chat_model if settings.provider!="demo" else "Sem LLM","status":"completed"})
        except PromptLimitError:
            request.app.state.observability.reject()
            raise HTTPException(status_code=413,detail="Contexto acima do limite configurado. Reduza o escopo dos documentos.") from None
        except Exception:
            request.app.state.observability.record(round((time.perf_counter()-started)*1000),len(citations),int(bool(metrics)),failed=True,execution=execution)
            log.warning("request_failed trace=%s subject=%s",trace_id,user.subject)
            raise HTTPException(status_code=503,detail={"message":"Dependência indisponível; verifique configuração e serviços.","trace_id":trace_id}) from None
        finally:
            request.app.state.admission.release()
        phase=time.perf_counter()
        answer_validation=validate_draft(answer,comparisons)
        if answer_validation['status']=='blocked':
            answer=safe_report(comparisons)
            log.warning('draft_blocked trace=%s subject=%s',trace_id,user.subject)
        execution.append({"id":"numeric_validation","label":"Verificação numérica","elapsed_ms":round((time.perf_counter()-phase)*1000) if comparisons else None,"detail":"Comparação no backend; guard de padrões limitado" if comparisons else "Nenhum limiar no formato reconhecido","status":"completed" if comparisons else "skipped"})
        elapsed=round((time.perf_counter()-started)*1000)
        request.app.state.observability.record(elapsed,len(citations),int(bool(metrics)),usage=usage,execution=execution,blocked=answer_validation["status"]=="blocked")
        log.info("chat trace=%s subject=%s sources=%s metrics=%s elapsed_ms=%s",trace_id,user.subject,len(citations),body.include_metrics,elapsed)
        return {"answer":answer,"usage":usage,"citations":[c.model_dump() for c in citations],"metrics":metrics,
                "trace_id":trace_id,"elapsed_ms":elapsed,"provider":settings.provider,"execution":execution,"comparisons":comparisons,"answer_validation":answer_validation,"retrieval_scope":scope or "all",
                "chat_model":settings.chat_model if settings.provider!="demo" else "extractive-demo",
                "tool_calls":[{"name":"get_service_metrics","transport":"MCP stdio","status":"ok"}] if metrics else []}
    return app

app=create_app()

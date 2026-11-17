import json
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from workbench.config import Settings
from workbench.main import create_app
from workbench.models import DocumentInput
from workbench.retrieval import Retrieval
from workbench.seed import seed

@pytest.fixture
def client():
    with TestClient(create_app(Settings(_env_file=None))) as c:
        yield c

def headers(token='demo-analyst'):
    return {'Authorization':f'Bearer {token}'}

def test_authentication_is_required(client):
    assert client.post('/api/chat',json={'question':'runbook'}).status_code == 401
    assert client.get('/api/config',headers=headers('invalid')).status_code == 401
    cfg = client.get('/api/config',headers=headers()).json()
    assert cfg['groups'] == ['level1']
    assert 'auth_tokens' not in cfg

def test_restricted_source_never_enters_model_context(client):
    provider=client.app.state.retrieval.provider
    captured=[]
    async def answer(question,citations,metrics):
        captured.extend(citations)
        return 'Resposta de teste'
    provider.answer=answer
    r=client.post('/api/chat',headers=headers(),json={'question':'OPS-RESTRICTED-7391 procedimento operações'})
    assert r.status_code==200
    assert all(c.document_id!='ops-internal' for c in captured)
    assert 'OPS-RESTRICTED-7391' not in json.dumps(r.json())
    r=client.post('/api/chat',headers=headers('demo-ops'),json={'question':'OPS-RESTRICTED-7391 procedimento operações'})
    assert any(c['document_id']=='ops-internal' for c in r.json()['citations'])

def test_metrics_denied_before_tool_call(client,monkeypatch):
    tool=AsyncMock()
    monkeypatch.setattr('workbench.main.call_metrics',tool)
    assert client.post('/api/chat',headers=headers(),json={'question':'erros API','include_metrics':True}).status_code==403
    tool.assert_not_called()

def test_ingestion_and_replacement(client):
    doc={'id':'new-doc','title':'Runbook Zephyr','text':'Zephyr utiliza uma fila dedicada para processamento de faturamento sintético.','access_level':'level1'}
    assert client.post('/api/documents',headers=headers(),json=doc).status_code==403
    assert client.post('/api/documents',headers=headers('demo-manager'),json={**doc,'access_level':'finance'}).status_code==422
    assert client.post('/api/documents',headers=headers('demo-manager'),json=doc).status_code==200
    r=client.post('/api/chat',headers=headers(),json={'question':'Zephyr fila faturamento'})
    assert any(c['document_id']=='new-doc' for c in r.json()['citations'])
    restricted={**doc,'text':'Zephyr agora usa um procedimento restrito de operações.','access_level':'level2'}
    assert client.post('/api/documents',headers=headers('demo-manager'),json=restricted).status_code==200
    r=client.post('/api/chat',headers=headers(),json={'question':'Zephyr procedimento'})
    assert all(c['document_id']!='new-doc' for c in r.json()['citations'])

def test_provider_failure_is_explicit(client):
    client.app.state.retrieval.provider.answer=AsyncMock(side_effect=RuntimeError('SECRET_INTERNAL'))
    r=client.post('/api/chat',headers=headers(),json={'question':'API pedidos'})
    assert r.status_code==503
    assert 'SECRET_INTERNAL' not in r.text
    assert r.json()['detail']['trace_id']

def test_input_limits(client):
    assert client.post('/api/chat',headers=headers(),json={'question':'x'*2001}).status_code==422
    assert client.post('/api/chat',headers=headers('demo-ops'),json={'question':'API pedidos','service':'../../shell','include_metrics':True}).status_code==422

def test_real_provider_rejects_demo_tokens():
    with pytest.raises(ValueError,match='Replace demo credentials'):
        Settings(provider='ollama',_env_file=None)

def test_empty_authorized_corpus_abstains(client):
    client.app.state.retrieval.store.chunks.clear()
    r=client.post('/api/chat',headers=headers(),json={'question':'Qual a causa do incidente?'})
    assert r.status_code==200
    assert not r.json()['citations']
    assert 'Não encontrei evidências' in r.json()['answer']

async def mcp_session_call(token,tool,args):
    params=StdioServerParameters(command=sys.executable,args=['-m','workbench.mcp_server'],
        env={'MCP_AUTH_TOKEN':token,'PROVIDER':'demo','STORE':'memory',
             'PYTHONPATH':str(Path(__file__).resolve().parents[1])},cwd='/tmp')
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            tools=await session.list_tools()
            assert {'search_documents','get_service_metrics','get_ai_quality_metrics'}=={t.name for t in tools.tools}
            return await session.call_tool(tool,args)

@pytest.mark.asyncio
async def test_mcp_protocol_authorization_and_search():
    denied=await mcp_session_call('demo-analyst','get_service_metrics',{'service':'orders-api'})
    assert denied.isError
    invalid=await mcp_session_call('invalid','search_documents',{'query':'pedidos'})
    assert invalid.isError
    result=await mcp_session_call('demo-analyst','search_documents',{'query':'OPS-RESTRICTED-7391 operações'})
    assert not result.isError
    assert 'OPS-RESTRICTED-7391' not in str(result.content)
    allowed=await mcp_session_call('demo-ops','get_service_metrics',{'service':'orders-api'})
    assert not allowed.isError
    data=json.loads(allowed.content[0].text)
    assert data['synthetic'] is True and data['observed_at']

def test_api_calls_real_mcp(client):
    r=client.post('/api/chat',headers=headers('demo-ops'),json={'question':'API pedidos erros','include_metrics':True})
    assert r.status_code==200,r.text
    assert r.json()['metrics']['synthetic'] is True
    assert r.json()['tool_calls'][0]['transport']=='MCP stdio'

@pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL'),reason='Set TEST_DATABASE_URL for pgvector integration')
def test_postgres_authorization_and_replace():
    settings=Settings(_env_file=None,store='postgres',database_url=os.environ['TEST_DATABASE_URL'])
    retrieval=Retrieval(settings)
    seed(retrieval)
    assert not any(c.document_id=='ops-internal' for c in retrieval.search('OPS-RESTRICTED-7391 operações',['level1']))
    assert any(c.document_id=='ops-internal' for c in retrieval.search('OPS-RESTRICTED-7391 operações',['level2']))
    doc=DocumentInput(id='integration-replace',title='Zephyr',text='Zephyr faturamento fila dedicada sintética.',access_level='level1')
    retrieval.ingest(doc)
    assert any(c.document_id==doc.id for c in retrieval.search('Zephyr faturamento',['level1']))
    retrieval.ingest(doc.model_copy(update={'access_level':'level2'}))
    assert not any(c.document_id==doc.id for c in retrieval.search('Zephyr faturamento',['level1']))

def test_execution_trace_distinguishes_measured_and_skipped_steps(client):
    result=client.post('/api/chat',headers=headers(),json={'question':'API pedidos erros'}).json()
    stages={stage['id']:stage for stage in result['execution']}
    assert stages['retrieval']['elapsed_ms']>=0
    assert stages['generation']['elapsed_ms']>=0
    assert stages['mcp']['status']=='skipped' and stages['mcp']['elapsed_ms'] is None
    assert result['chat_model']=='extractive-demo'

import json
import os
import uuid
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from workbench.config import Settings
from workbench.main import create_app
from workbench.models import Chunk,DocumentInput,Citation
from workbench.store import MemoryStore,PostgresStore
from workbench.providers import Provider

@pytest.mark.parametrize('kind',['memory','postgres'])
def test_service_and_access_filters_precede_ranking(kind):
    if kind=='postgres' and not os.getenv('TEST_DATABASE_URL'):
        pytest.skip('PostgreSQL integration requires TEST_DATABASE_URL')
    namespace='scope-test-'+uuid.uuid4().hex
    store=MemoryStore() if kind=='memory' else PostgresStore(os.environ['TEST_DATABASE_URL'],namespace)
    fixtures=[('wrong-service',['payments-api'],'level1',[1.,0.]),('restricted',['orders-api'],'level2',[1.,0.]),
              ('right-service',['orders-api'],'level1',[0.8,0.6]),('general',[],'level1',[0.6,0.8])]
    try:
        for id,services,level,vector in fixtures:
            doc=DocumentInput(id=id,title=id,text='Documento sintético com orientação verificável.',services=services,access_level=level)
            chunk=Chunk(id=id+'-1',document_id=id,title=id,text=doc.text,groups=[level],vector=vector,services=services)
            store.replace(id,[chunk],doc)
        found=store.search([1.,0.],['level1'],2,'orders-api')
        assert [c.document_id for c in found]==['right-service','general']
        assert 'restricted' not in [c.document_id for c in store.search([1.,0.],['level1'],10)]
    finally:
        if kind=='postgres':
            import psycopg
            with psycopg.connect(os.environ['TEST_DATABASE_URL']) as conn:
                conn.execute('DELETE FROM chunks WHERE namespace=%s',(namespace,))
                conn.execute('DELETE FROM documents WHERE namespace=%s',(namespace,))

def test_api_auto_scope_all_scope_and_mcp_mismatch():
    with TestClient(create_app(Settings(_env_file=None))) as client:
        headers={'Authorization':'Bearer demo-ops'}
        for query,scope,wrong in [('Como investigar pedidos?','orders-api','payments-runbook'),('Latência em pagamentos?','payments-api','orders-runbook')]:
            result=client.post('/api/chat',headers=headers,json={'question':query})
            assert result.status_code==200,result.text
            assert result.json()['retrieval_scope']==scope
            assert wrong not in [c['document_id'] for c in result.json()['citations']]
        result=client.post('/api/chat',headers=headers,json={'question':'pedidos e pagamentos','document_scope':'all'})
        assert result.json()['retrieval_scope']=='all'
        assert {'orders-runbook','payments-runbook'}.issubset({c['document_id'] for c in result.json()['citations']})
        assert client.post('/api/chat',headers=headers,json={'question':'API de pagamentos','include_metrics':True,'service':'orders-api'}).status_code==422
        assert client.post('/api/chat',headers=headers,json={'question':'API de pedidos','document_scope':'payments-api','include_metrics':True,'service':'orders-api'}).status_code==422

@pytest.mark.asyncio
async def test_model_context_keeps_observations_separate_from_runbook_thresholds():
    provider=Provider(Settings(_env_file=None))
    provider.chat=type('Chat',(),{'ainvoke':AsyncMock(return_value=type('Reply',(),{'content':'Teste de contrato, sem avaliação semântica.'})())})()
    citation=Citation(id='orders-1',document_id='orders',title='Runbook',excerpt='Taxa acima de 2% por 5 minutos exige investigação. Verifique pool e timeouts.',score=0.9,services=['orders-api'])
    metrics={'service':'orders-api','synthetic':True,'error_rate_pct':4.8,'latency_p95_ms':1450,'window_minutes':5,'observed_at':'2026-11-17T21:00:00Z'}
    await provider.answer('Como investigar pedidos?',[citation],metrics)
    messages=provider.chat.ainvoke.call_args.args[0]
    context=json.loads(messages[1].content.split('Evidências (JSON): ',1)[1])
    assert context['documents'][0]['source_type']=='document'
    assert '4.8' not in json.dumps(context['documents'])
    assert context['tool_results'][0]['source_id']=='mcp:get_service_metrics'
    assert context['tool_results'][0]['measurements']['error_rate_pct']==4.8
    assert context['tool_results'][0]['synthetic'] is True

@pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL'),reason='PostgreSQL integration requires TEST_DATABASE_URL')
def test_metadata_migration_preserves_edited_documents_and_explicit_general_scope():
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import make_conninfo
    dsn=os.environ['TEST_DATABASE_URL'];schema='scope_migration_'+uuid.uuid4().hex[:12]
    with psycopg.connect(dsn,autocommit=True) as conn:
        conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    isolated=make_conninfo(dsn,options=f'-c search_path={schema},public')
    try:
        with psycopg.connect(isolated) as conn:
            conn.execute('CREATE TABLE documents(namespace text,id text,title text,body text,access_level text,PRIMARY KEY(namespace,id))')
            conn.execute('CREATE TABLE chunks(namespace text,id text,document_id text,title text,body text,groups text[],embedding vector,PRIMARY KEY(namespace,id))')
            conn.execute("INSERT INTO documents VALUES('legacy','orders-runbook','Editado','Texto editado preservado para migração.','level2')")
            conn.execute("INSERT INTO chunks VALUES('legacy','orders-runbook-1','orders-runbook','Editado','Texto editado preservado para migração.',ARRAY['level2'],'[1,0]'::vector)")
        store=PostgresStore(isolated,'legacy')
        doc=store.get_document('orders-runbook',['level2'])
        assert doc.title=='Editado' and doc.text=='Texto editado preservado para migração.'
        assert doc.access_level=='level2' and doc.services==['orders-api']
        assert not store.search([1.,0.],['level1'],4,'orders-api')
        assert not store.search([1.,0.],['level2'],4,'payments-api')
        doc.services=[]
        chunk=Chunk(id='orders-runbook-1',document_id=doc.id,title=doc.title,text=doc.text,groups=['level2'],vector=[1.,0.],services=[])
        store.replace(doc.id,[chunk],doc)
        reopened=PostgresStore(isolated,'legacy')
        assert reopened.get_document(doc.id,['level2']).services==[]
        assert reopened.search([1.,0.],['level2'],4,'payments-api')
    finally:
        with psycopg.connect(dsn,autocommit=True) as conn:
            conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))

import base64
import json
import threading
import time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from types import SimpleNamespace
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from workbench.config import Settings
from workbench.main import create_app
from workbench.security import Authenticator

@pytest.fixture
def jwks_server():
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    public=key.public_key().public_numbers()
    def encoded(number):return base64.urlsafe_b64encode(number.to_bytes((number.bit_length()+7)//8,'big')).rstrip(b'=').decode()
    payload={'keys':[{'kty':'RSA','kid':'test-key','alg':'RS256','use':'sig','n':encoded(public.n),'e':encoded(public.e)}]}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            data=json.dumps(payload).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(data)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    settings=Settings(_env_file=None,auth_mode='oidc',oidc_issuer='https://identity.example/realms/lab',oidc_jwks_url=f'http://127.0.0.1:{server.server_port}/certs')
    def token(role='query-l1',**changes):
        claims={'sub':'user-123','iss':settings.oidc_issuer,'aud':'workbench-api','exp':int(time.time())+300,'iat':int(time.time()),'realm_access':{'roles':[role]}}
        claims.update(changes)
        return jwt.encode(claims,key,algorithm='RS256',headers={'kid':'test-key'})
    yield SimpleNamespace(settings=settings,token=token,key=key)
    server.shutdown();server.server_close();thread.join()

def header(token):return {'Authorization':'Bearer '+token}

def test_oidc_verifies_signature_issuer_audience_expiry_and_no_demo_fallback(jwks_server):
    with TestClient(create_app(jwks_server.settings)) as client:
        assert client.get('/api/auth/config').json()['mode']=='oidc'
        assert client.get('/api/config',headers=header(jwks_server.token())).json()['roles']==['query-l1']
        for token in [jwks_server.token(aud='another-api'),jwks_server.token(iss='https://evil.invalid'),
                      jwks_server.token(exp=int(time.time())-10),'demo-ops',
                      jwt.encode({'sub':'fake','exp':int(time.time())+300},'wrong-key-with-at-least-32-bytes-for-negative-test',algorithm='HS256',headers={'kid':'test-key'})]:
            assert client.get('/api/config',headers=header(token)).status_code==401
        assert client.get('/api/config',headers=header(jwks_server.token(role='unassigned'))).status_code==403

@pytest.mark.parametrize('token,can_write,can_metrics,restricted',[
    ('demo-analyst',False,False,False),('demo-ops',False,True,True),('demo-manager',True,False,True)])
def test_profile_matrix_and_document_apis(token,can_write,can_metrics,restricted):
    with TestClient(create_app(Settings(_env_file=None))) as client:
        h=header(token)
        cfg=client.get('/api/config',headers=h).json()
        assert ('documents:write' in cfg['permissions'])==can_write
        assert cfg['metrics_allowed']==can_metrics
        docs=client.get('/api/documents',headers=h).json()
        assert any(d['id']=='ops-internal' for d in docs)==restricted
        assert client.get('/api/documents/ops-internal',headers=h).status_code==(200 if restricted else 404)
        data={'id':'edit-test','title':'Teste','text':'Procedimento sintético para teste de edição.','access_level':'level1'}
        assert client.post('/api/documents',headers=h,json=data).status_code==(200 if can_write else 403)
        assert client.get('/api/observability',headers=h).status_code==(200 if can_metrics else 403)

def test_document_editor_preserves_exact_text_and_classification():
    with TestClient(create_app(Settings(_env_file=None))) as client:
        content='Procedimento Zephyr com conteúdo longo.\n'*100
        doc={'id':'editing','title':'Zephyr','text':content,'access_level':'level1'}
        manager=header('demo-manager')
        assert client.post('/api/documents',headers=manager,json=doc).status_code==200
        assert client.get('/api/documents/editing',headers=manager).json()['text']==content
        assert client.post('/api/documents',headers=manager,json={**doc,'text':'Nova versão do procedimento Zephyr, restrita.','access_level':'level2'}).status_code==200
        assert client.get('/api/documents/editing',headers=header('demo-analyst')).status_code==404
        assert client.get('/api/documents/editing',headers=header('demo-ops')).json()['access_level']=='level2'
        from workbench.seed import seed
        from workbench.models import DocumentInput
        seed_doc=client.get('/api/documents/orders-runbook',headers=manager).json()
        client.app.state.retrieval.ingest(DocumentInput(**{**seed_doc,'title':'Editado pelo gestor'}))
        seed(client.app.state.retrieval)
        assert client.get('/api/documents/orders-runbook',headers=manager).json()['title']=='Editado pelo gestor'

def test_measured_assistant_metrics_have_no_invented_cost_or_quality():
    with TestClient(create_app(Settings(_env_file=None))) as client:
        client.post('/api/chat',headers=header('demo-analyst'),json={'question':'API pedidos erros'})
        result=client.get('/api/observability',headers=header('demo-ops'))
        assert result.status_code==200,result.text
        stats=result.json()['data']
        assert stats['requests']==1 and stats['synthetic'] is False
        assert stats['latency_sample_size']==1 and stats['token_usage'] is None and stats['cost'] is None
        assert stats['groundedness'] is None and stats['retrieval_recall'] is None

@pytest.mark.asyncio
async def test_oidc_identity_is_revalidated_in_mcp_worker(jwks_server):
    from workbench.mcp_client import call_metrics
    result=await call_metrics(jwks_server.settings,jwks_server.token(role='query-l2'),'orders-api')
    assert result['synthetic'] is True
    with pytest.raises(RuntimeError,match='rejected'):
        await call_metrics(jwks_server.settings,jwks_server.token(role='knowledge-manager'),'orders-api')

def test_entra_style_app_roles_can_be_mapped(jwks_server):
    settings=jwks_server.settings.model_copy(update={'oidc_roles_claim':'roles'})
    user=Authenticator(settings).authenticate(jwks_server.token(role='unassigned',roles=['query-l2']))
    assert 'metrics:read' in user.permissions

@pytest.mark.parametrize('path',['/api/config','/api/documents','/api/documents/orders-runbook','/api/observability'])
def test_all_business_read_endpoints_require_login(path):
    with TestClient(create_app(Settings(_env_file=None))) as client:
        assert client.get(path).status_code==401

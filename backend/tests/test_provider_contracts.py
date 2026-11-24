"""Protocol contract checks with a local fake service; not real model evaluations."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import pytest
from workbench.config import Settings
from workbench.providers import Provider
from workbench.models import Citation

@pytest.fixture
def fake_provider(monkeypatch):
    # Contract tests use only loopback and must not inherit corporate proxy settings.
    for name in ("HTTP_PROXY","HTTPS_PROXY","ALL_PROXY","http_proxy","https_proxy","all_proxy"):
        monkeypatch.delenv(name,raising=False)
    seen=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            seen.append((self.path,body))
            if self.path=='/api/embed':
                result={'model':body['model'],'embeddings':[[1.0,0.0,0.0] for _ in body['input']]}
            elif self.path=='/api/chat':
                result={'model':body['model'],'created_at':'2026-11-17T12:00:00Z',
                        'message':{'role':'assistant','content':'Evidência [runbook-1].'},'done':True,
                        'done_reason':'stop','total_duration':100,'prompt_eval_count':12,'eval_count':5}
            elif self.path=='/v1/embeddings':
                result={'object':'list','data':[{'object':'embedding','index':i,'embedding':[1.0,0.0,0.0]} for i,_ in enumerate(body['input'])],
                        'model':body['model'],'usage':{'prompt_tokens':2,'total_tokens':2}}
            elif self.path=='/v1/chat/completions':
                result={'id':'fake','object':'chat.completion','created':1,'model':body['model'],
                        'choices':[{'index':0,'message':{'role':'assistant','content':'Evidência [runbook-1].'},'finish_reason':'stop'}],
                        'usage':{'prompt_tokens':12,'completion_tokens':5,'total_tokens':17}}
            else:
                self.send_error(404);return
            data=json.dumps(result).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    yield f'http://127.0.0.1:{server.server_port}',seen
    server.shutdown();server.server_close();thread.join()

@pytest.mark.asyncio
@pytest.mark.parametrize('mode',['ollama','openai-compatible'])
async def test_langchain_provider_contract(mode,fake_provider):
    url,seen=fake_provider
    settings=Settings(_env_file=None,provider=mode,auth_tokens={'synthetic-token':['employees']},
                      ollama_base_url=url,api_base_url=url+'/v1',api_key='synthetic-key',
                      chat_model='fake-chat',embedding_model='fake-embedding')
    provider=Provider(settings)
    assert provider.embed(['Runbook sintético'])==[[1.0,0.0,0.0]]
    citation=Citation(id='runbook-1',document_id='runbook',title='Runbook',excerpt='Verifique a fila.',score=0.8)
    answer=await provider.answer('Como investigar?',[citation],None)
    assert '[runbook-1]' in answer
    assert answer.usage['input_tokens']==12 and answer.usage['output_tokens']==5
    assert len(seen)==2
    chat_body=seen[-1][1]
    assert 'Verifique a fila.' in json.dumps(chat_body,ensure_ascii=False)
    assert not chat_body.get('tools')

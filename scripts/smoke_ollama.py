"""Exercise the real model path without printing a credential or claiming answer quality."""
import json
import time
import urllib.request
from pathlib import Path

# CI generates an ephemeral credential in .env. Never print it.
line=next(line for line in Path('.env').read_text().splitlines() if line.startswith('AUTH_TOKENS='))
token=next(iter(json.loads(line.split('=',1)[1])))
for attempt in range(90):
    try:
        with urllib.request.urlopen('http://localhost:8080/health',timeout=3) as response:
            if json.load(response)['provider']=='ollama': break
    except (OSError,ValueError): time.sleep(2)
else: raise RuntimeError('Backend did not start with Ollama')
request=urllib.request.Request('http://localhost:8080/api/chat',data=json.dumps({'question':'Quais verificações fazer para erros HTTP 500 na API de pedidos? Responda brevemente.','include_metrics':True}).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+token})
with urllib.request.urlopen(request,timeout=200) as response: result=json.load(response)
assert result['provider']=='ollama'
assert result['answer'].strip() and result['citations']
assert result['metrics']['synthetic'] is True
assert result['execution'][-1]['label']=='Geração por LLM'
assert all(step['elapsed_ms']>=0 for step in result['execution'])
print(json.dumps({'status':'PASS','model':result['chat_model'],'sources':len(result['citations']),'elapsed_ms':result['elapsed_ms'],'execution':result['execution'],'scope':'real Ollama CPU smoke; no quality or GPU benchmark'},ensure_ascii=False))

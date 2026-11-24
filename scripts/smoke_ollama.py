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
assert 'payments-runbook' not in [c['document_id'] for c in result['citations']]
assert result['metrics']['source_id']=='mcp:get_service_metrics'
assert next(step for step in result['execution'] if step['id']=='generation')['label']=='Geração por LLM'
assert result['comparisons'][0]['relation']=='>' and result['comparisons'][0]['triggered'] is True
assert all(step['elapsed_ms']>=0 for step in result['execution'])
assert result['usage']['input_tokens']>0 and result['usage']['output_tokens']>0
headers={'Authorization':'Bearer '+token}
with urllib.request.urlopen(urllib.request.Request('http://localhost:8080/api/observability',headers=headers),timeout=30) as response:
    stats=json.load(response)['data']
assert stats['requests']==1 and stats['successful_requests']==1 and stats['success_rate_pct']==100
assert stats['token_usage']['reported_requests']==1 and stats['cost'] is None
with urllib.request.urlopen(urllib.request.Request('http://localhost:8080/api/runtime',headers=headers),timeout=10) as response:
    runtime=json.load(response)
assert runtime['available'] and any(model['name']==result['chat_model'] for model in runtime['models'])
print(json.dumps({'status':'PASS','model':result['chat_model'],'sources':len(result['citations']),'elapsed_ms':result['elapsed_ms'],'execution':result['execution'],'usage':result['usage'],'operational_success_rate':stats['success_rate_pct'],'runtime':runtime,'answer_for_manual_review':result['answer'],'comparisons':result['comparisons'],'answer_validation':result['answer_validation'],'scope':'real Ollama CPU smoke; manual source-attribution review, no GPU benchmark'},ensure_ascii=False))

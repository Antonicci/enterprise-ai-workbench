"""Process-local admission controls and provider-reported generation usage."""
import time
from collections import deque
from threading import Lock
from decimal import Decimal
from fastapi import HTTPException

class PromptLimitError(ValueError):
    pass

class GeneratedAnswer(str):
    def __new__(cls, text, usage=None):
        value=super().__new__(cls,text)
        value.usage=usage
        return value

def reported_usage(response, settings):
    raw=getattr(response,"usage_metadata",None) or {}
    metadata=getattr(response,"response_metadata",None) or {}
    def count(value):
        return value if isinstance(value,int) and not isinstance(value,bool) and value>=0 else None
    inputs=count(raw.get("input_tokens"))
    outputs=count(raw.get("output_tokens"))
    if inputs is None: inputs=count(metadata.get("prompt_eval_count"))
    if outputs is None: outputs=count(metadata.get("eval_count"))
    if inputs is None or outputs is None: return None
    duration=metadata.get("eval_duration")
    tps=round(outputs/(duration/1e9),2) if isinstance(duration,(int,float)) and duration>0 else None
    estimate=None
    if settings.provider=="openai-compatible" and settings.price_model==settings.chat_model and settings.input_price_per_million is not None and settings.output_price_per_million is not None:
        estimate={"amount":str((Decimal(inputs)*settings.input_price_per_million+Decimal(outputs)*settings.output_price_per_million)/Decimal(1000000)),
                  "currency":settings.price_currency,"basis":"configured-generation-token-prices","model":settings.chat_model}
    return {"input_tokens":inputs,"output_tokens":outputs,"total_tokens":inputs+outputs,"source":"provider-reported",
            "scope":"generation-only","output_tokens_per_second":tps,"cost_estimate":estimate}

class Admission:
    def __init__(self, settings, clock=time.monotonic):
        self.settings=settings
        self.clock=clock
        self.lock=Lock()
        self.active=0
        self.buckets={}
    def acquire(self, subject):
        with self.lock:
            now=self.clock()
            for key in list(self.buckets):
                bucket=self.buckets[key]
                while bucket and bucket[0]<=now-60: bucket.popleft()
                if not bucket: del self.buckets[key]
            bucket=self.buckets.get(subject,deque())
            if len(bucket)>=self.settings.requests_per_minute:
                raise HTTPException(429,"Limite de consultas por usuário atingido. Aguarde a janela de 60 segundos.",headers={"Retry-After":str(max(1,int(60-(now-bucket[0]))+1))})
            if self.active>=self.settings.max_concurrent_requests:
                raise HTTPException(429,"Capacidade de consultas simultâneas atingida. Tente novamente.",headers={"Retry-After":"5"})
            if subject not in self.buckets and len(self.buckets)>=1000:
                raise HTTPException(429,"Capacidade do controle de uso atingida. Tente novamente.",headers={"Retry-After":"60"})
            bucket.append(now)
            self.buckets[subject]=bucket
            self.active+=1
    def release(self):
        with self.lock: self.active=max(0,self.active-1)
    def snapshot(self):
        with self.lock: return {"active_requests":self.active,"max_concurrent_requests":self.settings.max_concurrent_requests,
                               "requests_per_user_per_minute":self.settings.requests_per_minute,"scope":"backend-process"}

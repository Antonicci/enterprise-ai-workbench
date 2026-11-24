"""Operational measurements since this backend process started; no quality score."""
import time
import uuid
import math
from datetime import datetime, timezone
from decimal import Decimal
from collections import deque
from threading import Lock

class Observability:
    def __init__(self):
        self.started=time.monotonic()
        self.started_at=datetime.now(timezone.utc).isoformat()
        self.instance_id=uuid.uuid4().hex[:12]
        self.lock=Lock()
        self.samples=deque(maxlen=500)
        self.recent=deque(maxlen=12)
        self.total=self.failed=self.sources=self.tools=self.rejected=self.blocked=0
        self.input_tokens=self.output_tokens=self.accounted=0
        self.estimated_cost=Decimal(0)
        self.cost_samples=0
        self.currency=None
    def reject(self):
        with self.lock: self.rejected+=1
    def record(self, elapsed_ms, sources=0, tools=0, failed=False, usage=None, execution=None, blocked=False):
        with self.lock:
            self.total+=1
            self.failed+=int(failed)
            self.sources+=sources
            self.tools+=tools
            self.blocked+=int(blocked)
            self.samples.append(elapsed_ms)
            if usage:
                self.accounted+=1
                self.input_tokens+=usage["input_tokens"]
                self.output_tokens+=usage["output_tokens"]
                estimate=usage.get("cost_estimate")
                if estimate:
                    self.estimated_cost+=Decimal(estimate["amount"])
                    self.cost_samples+=1
                    self.currency=estimate["currency"]
            self.recent.append({"at":datetime.now(timezone.utc).isoformat(),"elapsed_ms":elapsed_ms,
                                "status":"failed" if failed else "completed","draft_blocked":blocked,
                                "stages":execution or [],"usage":usage})
    def snapshot(self):
        with self.lock:
            values=sorted(self.samples)
            succeeded=self.total-self.failed
            return {"available":True,"synthetic":False,"scope":"backend-process",
                    "instance_id":self.instance_id,"started_at":self.started_at,"collected_at":datetime.now(timezone.utc).isoformat(),
                    "uptime_seconds":round(time.monotonic()-self.started),
                    "requests":self.total,"successful_requests":succeeded,"failed_requests":self.failed,
                    "success_rate_pct":round(100*succeeded/self.total,2) if self.total else None,
                    "error_rate_pct":round(100*self.failed/self.total,2) if self.total else None,
                    "rejected_requests":self.rejected,"blocked_drafts":self.blocked,
                    "sources_returned":self.sources,"tool_calls":self.tools,
                    "latency_sample_size":len(values),"latency_window_limit":500,
                    "latency_avg_ms":round(sum(values)/len(values),2) if values else None,
                    "latency_p95_ms":values[max(0,math.ceil(len(values)*0.95)-1)] if values else None,
                    "token_usage":{"input_tokens":self.input_tokens,"output_tokens":self.output_tokens,
                                   "total_tokens":self.input_tokens+self.output_tokens,"reported_requests":self.accounted,
                                   "scope":"generation-only","source":"provider-reported"} if self.accounted else None,
                    "cost":{"estimated_amount":str(self.estimated_cost),"currency":self.currency,"priced_requests":self.cost_samples,
                            "scope":"generation-only; excludes embeddings, retries and infrastructure"} if self.cost_samples else None,
                    "recent_requests":list(reversed(self.recent)),
                    "groundedness":None,"retrieval_recall":None,
                    "limitations":["Contadores voláteis por processo; taxas excluem autenticação, validação e rejeições de política.",
                                   "Tokens cobrem respostas com uso informado pelo provedor; falhas, embeddings e retries podem consumir recursos não contabilizados.",
                                   "Sucesso de execução não equivale a correção da resposta."]}

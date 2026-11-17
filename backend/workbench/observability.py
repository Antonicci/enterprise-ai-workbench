"""Measured process-local operational counters; not a model quality evaluator."""
import time
from collections import deque
from threading import Lock

class Observability:
    def __init__(self):
        self.started=time.monotonic()
        self.lock=Lock()
        self.samples=deque(maxlen=500)
        self.total=0
        self.failed=0
        self.sources=0
        self.tools=0
    def record(self, elapsed_ms, sources=0, tools=0, failed=False):
        with self.lock:
            self.total+=1
            self.failed+=int(failed)
            self.sources+=sources
            self.tools+=tools
            self.samples.append(elapsed_ms)
    def snapshot(self):
        with self.lock:
            values=sorted(self.samples)
            return {"available":True,"synthetic":False,"scope":"backend-process", "uptime_seconds":round(time.monotonic()-self.started),
                    "requests":self.total,"failed_requests":self.failed,"sources_returned":self.sources,"tool_calls":self.tools,
                    "latency_sample_size":len(values),"latency_window_limit":500,
                    "latency_avg_ms":round(sum(values)/len(values),2) if values else None,
                    "latency_p95_ms":values[min(len(values)-1,int(len(values)*0.95))] if values else None,
                    "token_usage":None,"cost":None,"groundedness":None,"retrieval_recall":None,
                    "limitations":["Contadores voláteis, por processo; sem avaliação de qualidade ou medição de tokens/custo."]}

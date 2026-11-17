import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import Settings
from .models import DocumentInput, Question
from .security import authenticate, require_operations
from .retrieval import Retrieval
from .seed import seed
from .mcp_client import call_metrics

log = logging.getLogger("workbench.audit")
log.setLevel(logging.INFO)
if not log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    log.addHandler(handler)
log.propagate = False
bearer = HTTPBearer(auto_error=False)

def create_app(settings: Settings | None = None):
    settings = settings or Settings()
    @asynccontextmanager
    async def lifespan(app):
        app.state.retrieval = await asyncio.to_thread(Retrieval,settings)
        await asyncio.to_thread(seed,app.state.retrieval)
        yield
    app = FastAPI(title="Enterprise AI Workbench",version="0.1.0",lifespan=lifespan)
    def identity(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if credentials is None:
            raise HTTPException(status_code=401,detail="Bearer token obrigatório")
        return authenticate(credentials.credentials,settings.auth_tokens)

    @app.get("/health")
    def health():
        return {"status":"ok","provider":settings.provider,"store":settings.store,"synthetic_metrics":True}

    @app.get("/api/config")
    def config(user=Depends(identity)):
        return {"provider":settings.provider,"store":settings.store,"groups":user.groups,
                "chat_model":settings.chat_model if settings.provider != "demo" else "extractive-demo",
                "embedding_model":settings.embedding_model if settings.provider != "demo" else "hash-demo-256",
                "metrics_allowed":"operations" in user.groups}

    @app.post("/api/documents")
    async def ingest(doc: DocumentInput, request: Request, user=Depends(identity)):
        require_operations(user)
        if not set(doc.groups).issubset(set(user.groups)):
            raise HTTPException(status_code=403,detail="Não pode atribuir grupos fora do seu escopo")
        count = await asyncio.to_thread(request.app.state.retrieval.ingest,doc)
        log.info("ingest subject=%s document_id=%s chunks=%s",user.subject,doc.id,count)
        return {"id":doc.id,"chunks":count}

    @app.post("/api/chat")
    async def chat(body: Question,request: Request,user=Depends(identity),credentials=Depends(bearer)):
        if body.include_metrics:
            require_operations(user)
        started,trace_id = time.perf_counter(),uuid.uuid4().hex
        retrieval = request.app.state.retrieval
        try:
            async with asyncio.timeout(settings.request_timeout):
                citations = await asyncio.to_thread(retrieval.search,body.question,user.groups)
                metrics = await call_metrics(settings,credentials.credentials,body.service) if body.include_metrics else None
                answer = await retrieval.provider.answer(body.question,citations,metrics)
        except Exception:
            log.warning("request_failed trace=%s subject=%s",trace_id,user.subject)
            raise HTTPException(status_code=503,detail={"message":"Dependência indisponível; verifique configuração e serviços.","trace_id":trace_id}) from None
        elapsed = round((time.perf_counter()-started)*1000)
        log.info("chat trace=%s subject=%s sources=%s metrics=%s elapsed_ms=%s",trace_id,user.subject,len(citations),body.include_metrics,elapsed)
        return {"answer":answer,"citations":[c.model_dump() for c in citations],"metrics":metrics,
                "trace_id":trace_id,"elapsed_ms":elapsed,"provider":settings.provider,
                "tool_calls":[{"name":"get_service_metrics","transport":"MCP stdio","status":"ok"}] if metrics else []}
    return app

app = create_app()

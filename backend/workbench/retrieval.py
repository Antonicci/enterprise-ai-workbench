from .config import Settings
from .models import Chunk, DocumentInput
from .providers import Provider
from .store import MemoryStore, PostgresStore

class Retrieval:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider = Provider(settings)
        self.store = (PostgresStore(settings.database_url.get_secret_value(),settings.namespace)
                      if settings.store == "postgres" else MemoryStore())
    def ingest(self, document: DocumentInput):
        parts = [document.text[start:start+900] for start in range(0,len(document.text),750)]
        vectors = self.provider.embed(parts)
        chunks = [Chunk(id=f"{document.id}-{i+1}",document_id=document.id,title=document.title,
                        text=text,groups=[document.access_level],vector=vector,services=document.services)
                  for i,(text,vector) in enumerate(zip(parts,vectors,strict=True))]
        self.store.replace(document.id,chunks,document)
        return len(chunks)
    def search(self,query,groups,service=None):
        service = service if service is not None else infer_service(query)
        return self.store.search(self.provider.embed([query])[0],groups,self.settings.top_k,None if service=="all" else service)


def infer_service(query):
    import re,unicodedata
    query="".join(c for c in unicodedata.normalize("NFD",query.lower()) if unicodedata.category(c)!="Mn")
    matches=[]
    if re.search(r"\b(orders-api|pedidos?)\b",query): matches.append("orders-api")
    if re.search(r"\b(payments-api|pagamentos?|cobrancas?)\b",query): matches.append("payments-api")
    return matches[0] if len(matches)==1 else None


def resolve_scope(question,selected="auto",metrics_service=None):
    if selected=="all": return "all"
    if selected!="auto": return selected
    inferred=infer_service(question)
    if inferred and metrics_service and inferred!=metrics_service:
        from fastapi import HTTPException
        raise HTTPException(status_code=422,detail="A pergunta e o serviço MCP apontam para serviços diferentes. Ajuste a seleção ou use escopo Todos para comparar.")
    return inferred or metrics_service


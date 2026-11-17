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
                        text=text,groups=document.groups,vector=vector)
                  for i,(text,vector) in enumerate(zip(parts,vectors,strict=True))]
        self.store.replace(document.id,chunks)
        return len(chunks)
    def search(self,query,groups):
        return self.store.search(self.provider.embed([query])[0],groups,self.settings.top_k)

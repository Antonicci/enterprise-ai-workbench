"""Authorization is applied before ranking and before context construction."""
import math
from .models import Chunk, Citation, DocumentInput
from threading import RLock

class MemoryStore:
    def __init__(self):
        self.chunks: dict[str, Chunk] = {}
        self.documents: dict[str, DocumentInput] = {}
        self.lock = RLock()
    def replace(self, document_id: str, chunks: list[Chunk], document: DocumentInput):
        with self.lock:
            self.chunks = {k:v for k,v in self.chunks.items() if v.document_id != document_id}
            self.chunks.update({c.id:c for c in chunks})
            self.documents[document_id] = document
    def list_documents(self,groups):
        with self.lock:
            return [d.model_copy(deep=True) for d in self.documents.values() if d.access_level in groups]
    def get_document(self,document_id,groups):
        with self.lock:
            d = self.documents.get(document_id)
            return d.model_copy(deep=True) if d and d.access_level in groups else None
    def has_document(self,document_id):
        with self.lock:
            return document_id in self.documents
    def search(self, vector, groups, top_k):
        with self.lock:
            allowed = [c for c in self.chunks.values() if set(groups).intersection(c.groups)]
        def similarity(c):
            dot = sum(a*b for a,b in zip(vector,c.vector,strict=True))
            norm = math.sqrt(sum(x*x for x in vector)*sum(x*x for x in c.vector)) or 1
            return dot/norm
        ranked = sorted(((similarity(c),c) for c in allowed),key=lambda pair:pair[0],reverse=True)
        return [citation(c,s) for s,c in ranked[:top_k] if s > 0.05]

def citation(chunk,score):
    return Citation(id=chunk.id, document_id=chunk.document_id, title=chunk.title,
                    excerpt=chunk.text, score=round(float(score),4))

class PostgresStore:
    def __init__(self, dsn: str, namespace: str):
        import psycopg
        self.dsn, self.namespace = dsn, namespace
        with psycopg.connect(dsn) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.execute("""CREATE TABLE IF NOT EXISTS chunks (
                namespace text NOT NULL, id text NOT NULL, document_id text NOT NULL,
                title text NOT NULL, body text NOT NULL, groups text[] NOT NULL,
                embedding vector NOT NULL, PRIMARY KEY(namespace,id))""")
            conn.execute("""CREATE TABLE IF NOT EXISTS documents (
                namespace text NOT NULL, id text NOT NULL, title text NOT NULL,
                body text NOT NULL, access_level text NOT NULL,
                PRIMARY KEY(namespace,id))""")
    def list_documents(self,groups):
        import psycopg
        with psycopg.connect(self.dsn) as conn:
            rows = conn.execute("SELECT id,title,body,access_level FROM documents WHERE namespace=%s AND access_level=ANY(%s)",(self.namespace,list(groups))).fetchall()
        return [DocumentInput(id=a,title=b,text=c,access_level=d) for a,b,c,d in rows]
    def get_document(self,document_id,groups):
        return next((d for d in self.list_documents(groups) if d.id==document_id),None)
    def has_document(self,document_id):
        import psycopg
        with psycopg.connect(self.dsn) as conn:
            return conn.execute("SELECT 1 FROM documents WHERE namespace=%s AND id=%s",(self.namespace,document_id)).fetchone() is not None
    def replace(self,document_id,chunks,document):
        import psycopg
        with psycopg.connect(self.dsn) as conn:
            conn.execute("""INSERT INTO documents VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT(namespace,id) DO UPDATE SET title=EXCLUDED.title,body=EXCLUDED.body,access_level=EXCLUDED.access_level""",
                (self.namespace,document.id,document.title,document.text,document.access_level))
            conn.execute("DELETE FROM chunks WHERE namespace=%s AND document_id=%s",(self.namespace,document_id))
            for c in chunks:
                conn.execute("INSERT INTO chunks VALUES (%s,%s,%s,%s,%s,%s,%s::vector)",
                             (self.namespace,c.id,c.document_id,c.title,c.text,c.groups,str(c.vector)))
    def search(self,vector,groups,top_k):
        import psycopg
        with psycopg.connect(self.dsn) as conn:
            rows = conn.execute("""SELECT id,document_id,title,body,1-(embedding <=> %s::vector) AS score
                FROM chunks WHERE namespace=%s AND groups && %s::text[]
                ORDER BY embedding <=> %s::vector LIMIT %s""",
                (str(vector),self.namespace,list(groups),str(vector),top_k)).fetchall()
        return [Citation(id=r[0],document_id=r[1],title=r[2],excerpt=r[3],score=round(float(r[4]),4))
                for r in rows if r[4] > 0.05]

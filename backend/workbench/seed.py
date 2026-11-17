import json
from pathlib import Path
from .models import DocumentInput

def seed(retrieval):
    path = Path(__file__).with_name("sample_documents.json")
    for item in json.loads(path.read_text()):
        if not retrieval.store.has_document(item["id"]):
            retrieval.ingest(DocumentInput(**item))

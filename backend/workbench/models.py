from pydantic import BaseModel, Field

class DocumentInput(BaseModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    title: str = Field(min_length=1, max_length=160)
    text: str = Field(min_length=20, max_length=30000)
    groups: list[str] = Field(min_length=1, max_length=10)

class Question(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    include_metrics: bool = False
    service: str = Field(default="orders-api", pattern=r"^(orders-api|payments-api)$")

class Chunk(BaseModel):
    id: str
    document_id: str
    title: str
    text: str
    groups: list[str]
    vector: list[float]

class Citation(BaseModel):
    id: str
    document_id: str
    title: str
    excerpt: str
    score: float

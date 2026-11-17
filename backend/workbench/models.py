from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class DocumentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    title: str = Field(min_length=1, max_length=160)
    text: str = Field(min_length=20, max_length=30000)
    access_level: Literal["level1", "level2"] = "level1"
    services: list[Literal["orders-api", "payments-api"]] = Field(default_factory=list, max_length=2)

class Question(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    include_metrics: bool = False
    document_scope: Literal["auto", "all", "orders-api", "payments-api"] = "auto"
    service: str = Field(default="orders-api", pattern=r"^(orders-api|payments-api)$")

class Chunk(BaseModel):
    id: str
    document_id: str
    title: str
    text: str
    groups: list[str]
    vector: list[float]
    services: list[str] = Field(default_factory=list)

class Citation(BaseModel):
    id: str
    document_id: str
    title: str
    excerpt: str
    score: float
    source_type: Literal["document"] = "document"
    services: list[str] = Field(default_factory=list)

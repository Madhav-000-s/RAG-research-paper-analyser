import uuid
from typing import Literal

from pydantic import BaseModel


class QueryRequest(BaseModel):
    paper_id: uuid.UUID
    question: str
    conversation_id: uuid.UUID | None = None
    top_k: int = 10
    rerank_top_n: int = 5
    llm_provider: Literal["ollama", "anthropic", "openai"] = "ollama"


class Citation(BaseModel):
    chunk_id: uuid.UUID
    chunk_index: int
    page_number: int
    section_heading: str | None = None
    snippet: str


class QueryResponse(BaseModel):
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    answer: str
    citations: list[Citation]

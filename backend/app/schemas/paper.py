import uuid
from datetime import datetime

from pydantic import BaseModel


class PaperResponse(BaseModel):
    id: uuid.UUID
    filename: str
    title: str | None = None
    authors: list[str] | None = None
    page_count: int | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PaperDetailResponse(PaperResponse):
    chunk_count: int = 0


class ChunkResponse(BaseModel):
    id: uuid.UUID
    chunk_index: int
    content: str
    chunk_type: str
    page_number: int
    section_heading: str | None = None
    token_count: int

    model_config = {"from_attributes": True}

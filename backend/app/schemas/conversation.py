import uuid
from datetime import datetime

from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    citations: list | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationSummary(BaseModel):
    id: uuid.UUID
    paper_id: uuid.UUID
    created_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class ConversationDetail(BaseModel):
    id: uuid.UUID
    paper_id: uuid.UUID
    created_at: datetime
    messages: list[MessageResponse]

    model_config = {"from_attributes": True}

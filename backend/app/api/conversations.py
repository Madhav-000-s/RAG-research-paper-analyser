import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.conversation import Conversation, Message
from app.schemas.conversation import ConversationDetail, ConversationSummary

router = APIRouter()


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(
    paper_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(
        Conversation,
        func.count(Message.id).label("message_count"),
    ).outerjoin(Message).group_by(Conversation.id)

    if paper_id:
        query = query.where(Conversation.paper_id == paper_id)

    query = query.order_by(Conversation.created_at.desc())
    result = await db.execute(query)

    summaries = []
    for conv, msg_count in result.all():
        summaries.append(
            ConversationSummary(
                id=conv.id,
                paper_id=conv.paper_id,
                created_at=conv.created_at,
                message_count=msg_count,
            )
        )
    return summaries


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

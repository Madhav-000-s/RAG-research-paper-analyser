"""Generation pipeline: retrieve -> prompt -> generate -> parse citations."""

import logging
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.generation.llm import LLMClient
from app.generation.prompts import SYSTEM_PROMPT, build_user_prompt
from app.models.conversation import Conversation, Message
from app.retrieval.dense import ScoredChunk
from app.retrieval.embedder import Embedder
from app.retrieval.pipeline import retrieve
from app.retrieval.reranker import Reranker
from app.schemas.query import Citation, QueryRequest, QueryResponse

logger = logging.getLogger(__name__)


def parse_citations(
    answer: str, chunks: list[ScoredChunk]
) -> list[Citation]:
    """Extract [N] references from answer text and map to chunk metadata."""
    refs = sorted(set(int(m) for m in re.findall(r"\[(\d+)\]", answer)))
    citations = []

    for ref_num in refs:
        idx = ref_num - 1
        if 0 <= idx < len(chunks):
            c = chunks[idx]
            citations.append(
                Citation(
                    chunk_id=c.id,
                    chunk_index=c.chunk_index,
                    page_number=c.page_number,
                    section_heading=c.section_heading,
                    snippet=c.content[:200],
                )
            )

    return citations


async def answer_question(
    request: QueryRequest,
    db: AsyncSession,
    embedder: Embedder,
    reranker: Reranker,
    llm: LLMClient,
) -> QueryResponse:
    """
    Full generation pipeline:
    1. Retrieve relevant chunks
    2. Load conversation history (if continuing)
    3. Build prompt with context
    4. Generate answer via LLM
    5. Parse citations
    6. Persist conversation and messages
    """
    # Step 1: Retrieve
    chunks = await retrieve(
        query=request.question,
        paper_id=request.paper_id,
        db=db,
        embedder=embedder,
        reranker=reranker,
        top_k=request.top_k,
        rerank_top_n=request.rerank_top_n,
    )

    # Step 2: Load or create conversation
    conversation_history = None
    if request.conversation_id:
        result = await db.execute(
            select(Conversation).where(Conversation.id == request.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            # Load previous messages
            msg_result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.created_at)
            )
            messages = msg_result.scalars().all()
            conversation_history = [
                {"role": m.role, "content": m.content} for m in messages
            ]
    else:
        conversation = Conversation(paper_id=request.paper_id)
        db.add(conversation)
        await db.flush()

    # Step 3: Build prompt
    messages = build_user_prompt(request.question, chunks, conversation_history)

    # Step 4: Generate
    answer = await llm.generate(
        system=SYSTEM_PROMPT,
        messages=messages,
        provider=request.llm_provider,
    )

    # Step 5: Parse citations
    citations = parse_citations(answer, chunks)

    # Step 6: Persist messages
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.question,
    )
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        citations=[c.model_dump(mode="json") for c in citations],
    )
    db.add(user_msg)
    db.add(assistant_msg)
    await db.flush()

    return QueryResponse(
        conversation_id=conversation.id,
        message_id=assistant_msg.id,
        answer=answer,
        citations=citations,
    )

"""Dense vector search using pgvector."""

import uuid
from dataclasses import dataclass

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class ScoredChunk:
    id: uuid.UUID
    chunk_index: int
    content: str
    page_number: int
    section_heading: str | None
    score: float


async def dense_search(
    query_embedding: np.ndarray,
    paper_id: uuid.UUID,
    db: AsyncSession,
    top_k: int = 20,
) -> list[ScoredChunk]:
    """Search chunks by cosine similarity using pgvector."""
    embedding_list = query_embedding.tolist()

    result = await db.execute(
        text("""
            SELECT id, chunk_index, content, page_number, section_heading,
                   1 - (embedding <=> :query_vec::vector) AS score
            FROM chunks
            WHERE paper_id = :paper_id
            ORDER BY embedding <=> :query_vec::vector
            LIMIT :top_k
        """),
        {
            "query_vec": str(embedding_list),
            "paper_id": str(paper_id),
            "top_k": top_k,
        },
    )

    return [
        ScoredChunk(
            id=row.id,
            chunk_index=row.chunk_index,
            content=row.content,
            page_number=row.page_number,
            section_heading=row.section_heading,
            score=float(row.score),
        )
        for row in result.fetchall()
    ]

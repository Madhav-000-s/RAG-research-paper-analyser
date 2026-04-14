"""Sparse BM25-style search using PostgreSQL tsvector."""

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.retrieval.dense import ScoredChunk


async def sparse_search(
    query: str,
    paper_id: uuid.UUID,
    db: AsyncSession,
    top_k: int = 20,
) -> list[ScoredChunk]:
    """Search chunks using PostgreSQL full-text search with ts_rank_cd."""
    result = await db.execute(
        text("""
            SELECT id, chunk_index, content, page_number, section_heading,
                   ts_rank_cd(to_tsvector('english', content),
                              plainto_tsquery('english', :query)) AS score
            FROM chunks
            WHERE paper_id = :paper_id
              AND to_tsvector('english', content) @@ plainto_tsquery('english', :query)
            ORDER BY score DESC
            LIMIT :top_k
        """),
        {
            "query": query,
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

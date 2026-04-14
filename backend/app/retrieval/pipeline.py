"""Retrieval pipeline: dense + sparse -> RRF -> rerank."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.retrieval.dense import ScoredChunk, dense_search
from app.retrieval.embedder import Embedder
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.reranker import Reranker
from app.retrieval.sparse import sparse_search


async def retrieve(
    query: str,
    paper_id: uuid.UUID,
    db: AsyncSession,
    embedder: Embedder,
    reranker: Reranker,
    top_k: int = 20,
    rerank_top_n: int = 5,
) -> list[ScoredChunk]:
    """
    Full hybrid retrieval pipeline:
    1. Dense search (pgvector cosine similarity)
    2. Sparse search (PostgreSQL tsvector)
    3. Reciprocal Rank Fusion
    4. Cross-encoder re-ranking
    """
    # Encode query
    query_embedding = embedder.encode_query(query)

    # Run dense and sparse search
    dense_results = await dense_search(query_embedding, paper_id, db, top_k)
    sparse_results = await sparse_search(query, paper_id, db, top_k)

    # Fuse results
    fused = reciprocal_rank_fusion([dense_results, sparse_results])

    # Re-rank top candidates
    reranked = reranker.rerank(query, fused[:top_k], top_n=rerank_top_n)

    return reranked

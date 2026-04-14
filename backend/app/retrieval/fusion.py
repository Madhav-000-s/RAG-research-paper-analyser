"""Reciprocal Rank Fusion for combining ranked retrieval results."""

from app.config import settings
from app.retrieval.dense import ScoredChunk


def reciprocal_rank_fusion(
    ranked_lists: list[list[ScoredChunk]],
    k: int | None = None,
) -> list[ScoredChunk]:
    """
    Combine multiple ranked lists using Reciprocal Rank Fusion.

    RRF score for document d = sum over all lists of 1 / (k + rank(d))
    where rank is 1-indexed.

    Args:
        ranked_lists: List of ranked result lists
        k: RRF constant (default from settings, typically 60)

    Returns:
        Chunks sorted by RRF score descending
    """
    if k is None:
        k = settings.rrf_k

    # Map chunk_id -> (best ScoredChunk, cumulative RRF score)
    scores: dict[str, float] = {}
    chunks: dict[str, ScoredChunk] = {}

    for ranked_list in ranked_lists:
        for rank, chunk in enumerate(ranked_list, start=1):
            chunk_key = str(chunk.id)
            rrf_score = 1.0 / (k + rank)
            scores[chunk_key] = scores.get(chunk_key, 0.0) + rrf_score
            # Keep the chunk object (first occurrence is fine)
            if chunk_key not in chunks:
                chunks[chunk_key] = chunk

    # Sort by RRF score descending
    sorted_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)

    result = []
    for chunk_id in sorted_ids:
        chunk = chunks[chunk_id]
        # Replace the original score with the RRF score
        result.append(
            ScoredChunk(
                id=chunk.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                page_number=chunk.page_number,
                section_heading=chunk.section_heading,
                score=scores[chunk_id],
            )
        )

    return result

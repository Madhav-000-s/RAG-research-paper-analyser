"""Cross-encoder re-ranker using sentence-transformers."""

import logging

import numpy as np
from sentence_transformers import CrossEncoder

from app.retrieval.dense import ScoredChunk

logger = logging.getLogger(__name__)


class Reranker:
    def __init__(self, model_name: str):
        logger.info(f"Loading reranker model: {model_name}")
        self.model = CrossEncoder(model_name)
        logger.info("Reranker model loaded")

    def rerank(
        self,
        query: str,
        chunks: list[ScoredChunk],
        top_n: int = 5,
    ) -> list[ScoredChunk]:
        """
        Re-rank chunks using a cross-encoder model.

        Args:
            query: The user's question
            chunks: Candidate chunks from fusion
            top_n: Number of top chunks to return

        Returns:
            Top-n chunks sorted by cross-encoder score
        """
        if not chunks:
            return []

        pairs = [(query, c.content) for c in chunks]
        scores = self.model.predict(pairs)

        # Pair scores with chunks and sort
        scored = list(zip(scores, chunks))
        scored.sort(key=lambda x: x[0], reverse=True)

        return [
            ScoredChunk(
                id=chunk.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                page_number=chunk.page_number,
                section_heading=chunk.section_heading,
                score=float(score),
            )
            for score, chunk in scored[:top_n]
        ]

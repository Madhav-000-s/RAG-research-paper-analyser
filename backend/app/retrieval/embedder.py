"""Embedding wrapper using sentence-transformers."""

import logging

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self, model_name: str):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded")

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode a batch of texts into normalized embeddings."""
        if not texts:
            return np.array([])
        return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    def encode_query(self, query: str) -> np.ndarray:
        """Encode a single query string."""
        return self.model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]

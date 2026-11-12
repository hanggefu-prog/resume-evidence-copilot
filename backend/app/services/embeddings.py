"""Embedding provider abstraction.

Real embeddings use a local sentence-transformers model — zero per-call cost,
no external API. Tests use a deterministic hash-based fake so the suite
doesn't need to download a ~90MB model.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from functools import lru_cache

from app.config import settings
from app.models.candidate import EMBEDDING_DIM

MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        ...


class LocalSentenceTransformerEmbedding(EmbeddingProvider):
    def __init__(self):
        from sentence_transformers import SentenceTransformer  # lazy import, heavy

        self._model = SentenceTransformer(MODEL_NAME)

    def embed(self, text: str) -> list[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()


class FakeHashEmbedding(EmbeddingProvider):
    """Deterministic, dependency-free. Same text -> same vector. Not semantically
    meaningful — only for exercising code paths (storage, search plumbing) in tests."""

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # Repeat/trim the digest bytes to EMBEDDING_DIM floats in [0, 1)
        values = [(digest[i % len(digest)] / 255.0) for i in range(EMBEDDING_DIM)]
        return values


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    if settings.testing or settings.embedding_mode == "fake":
        return FakeHashEmbedding()
    return LocalSentenceTransformerEmbedding()

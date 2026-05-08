"""Mock embedding adapter for testing without an embedding service."""

from __future__ import annotations

import hashlib


class MockEmbeddingAdapter:
    """Deterministic mock embedding generator for testing.

    Generates a fixed-size vector based on hash of the input text,
    producing consistent embeddings for the same input.
    """

    def __init__(self, dimension: int = 128) -> None:
        self.dimension = dimension

    def embed(self, text: str) -> list[float]:
        """Generate a deterministic mock embedding."""
        return self._hash_to_vector(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate mock embeddings for a batch of texts."""
        return [self._hash_to_vector(t) for t in texts]

    def _hash_to_vector(self, text: str) -> list[float]:
        """Convert text hash to a pseudo-random vector."""
        h = hashlib.sha256(text.encode()).hexdigest()
        vec = []
        for i in range(self.dimension):
            val = int(h[(i * 2) % 64 : (i * 2 + 2) % 64], 16) / 255.0
            vec.append(val)
        return vec

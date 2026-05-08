"""Abstract embedding adapter interface."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingAdapter(Protocol):
    """Protocol for embedding providers."""

    def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text."""
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts."""
        ...

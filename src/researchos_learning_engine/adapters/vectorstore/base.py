"""Abstract vector store adapter interface."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class VectorStoreAdapter(Protocol):
    """Protocol for vector database backends."""

    def upsert(self, collection: str, vectors: list[dict[str, Any]]) -> None:
        """Upsert vectors with metadata into a collection."""
        ...

    def search(
        self,
        collection: str,
        query_vector: list[float],
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for nearest neighbors in a collection.

        Returns list of dicts with 'id', 'score', and 'metadata' keys.
        """
        ...

    def delete_collection(self, collection: str) -> None:
        """Delete an entire collection."""
        ...

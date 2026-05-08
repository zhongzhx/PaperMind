"""Abstract storage adapter interface.

Storage adapters provide persistence for memory records, patterns,
evidence graph data, and consolidation results. The Learning Engine
never accesses storage directly — always through this interface.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from researchos_learning_engine.domain.schemas import (
    ConsolidationResult,
    EvidenceGraphEdge,
    MemoryRecord,
    ResearchPattern,
)


@runtime_checkable
class StorageAdapter(Protocol):
    """Protocol for storage backends.

    Implementations can use JSON files, SQLite, or the main ResearchOS
    database — the engine treats them uniformly through this interface.
    """

    def save_memory(self, memory: MemoryRecord) -> None:
        """Persist a single memory record."""
        ...

    def load_memories(self, project_id: str | None = None) -> list[MemoryRecord]:
        """Load memory records, optionally filtered by project."""
        ...

    def save_pattern(self, pattern: ResearchPattern) -> None:
        """Persist a research pattern."""
        ...

    def load_patterns(self, project_id: str | None = None) -> list[ResearchPattern]:
        """Load research patterns, optionally filtered by project."""
        ...

    def save_edge(self, edge: EvidenceGraphEdge) -> None:
        """Persist an evidence graph edge."""
        ...

    def load_edges(self, project_id: str | None = None) -> list[EvidenceGraphEdge]:
        """Load evidence graph edges, optionally filtered by project."""
        ...

    def save_consolidation_result(self, result: ConsolidationResult) -> None:
        """Persist a consolidation result."""
        ...

    def load_latest_consolidation(
        self, project_id: str
    ) -> ConsolidationResult | None:
        """Load the most recent consolidation result for a project."""
        ...

    def save_raw(self, key: str, data: Any) -> None:
        """Save arbitrary data under a key (for extensibility)."""
        ...

    def load_raw(self, key: str) -> Any | None:
        """Load arbitrary data by key."""
        ...

"""File-based JSON storage adapter.

Stores data as JSON files on disk. Useful for prototyping, testing,
and single-user scenarios. Each data type is stored in its own file
under a workspace directory.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from researchos_learning_engine.domain.schemas import (
    ConsolidationResult,
    EvidenceGraphEdge,
    MemoryRecord,
    ResearchPattern,
)


class JSONStorageAdapter:
    """Simple file-based JSON storage.

    Each data collection is stored as a separate JSON file in the
    configured data directory.
    """

    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    # --- Path helpers ---

    def _path(self, key: str) -> Path:
        return self.data_dir / f"{key}.json"

    def _read_json(self, key: str) -> list[dict[str, Any]]:
        path = self._path(key)
        if not path.exists():
            return []
        with open(path, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]

    def _write_json(self, key: str, data: list[dict[str, Any]]) -> None:
        path = self._path(key)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    # --- Memory ---

    def save_memory(self, memory: MemoryRecord) -> None:
        memories = self._read_json("memories")
        # Remove existing record with same ID, then append
        memories = [m for m in memories if m.get("memory_id") != memory.memory_id]
        memories.append(memory.to_dict())
        self._write_json("memories", memories)

    def load_memories(self, project_id: str | None = None) -> list[MemoryRecord]:
        memories = self._read_json("memories")
        if project_id:
            memories = [m for m in memories if m.get("project_id") == project_id]
        return [MemoryRecord.from_dict(m) for m in memories]

    # --- Patterns ---

    def save_pattern(self, pattern: ResearchPattern) -> None:
        patterns = self._read_json("patterns")
        patterns = [p for p in patterns if p.get("pattern_id") != pattern.pattern_id]
        patterns.append(pattern.to_dict())
        self._write_json("patterns", patterns)

    def load_patterns(self, project_id: str | None = None) -> list[ResearchPattern]:
        patterns = self._read_json("patterns")
        if project_id:
            patterns = [p for p in patterns if p.get("project_id") == project_id]
        return [ResearchPattern.from_dict(p) for p in patterns]

    # --- Edges ---

    def save_edge(self, edge: EvidenceGraphEdge) -> None:
        edges = self._read_json("edges")
        edges = [e for e in edges if e.get("edge_id") != edge.edge_id]
        edges.append(edge.to_dict())
        self._write_json("edges", edges)

    def load_edges(self, project_id: str | None = None) -> list[EvidenceGraphEdge]:
        edges = self._read_json("edges")
        if project_id:
            edges = [e for e in edges if e.get("project_id") == project_id]
        return [EvidenceGraphEdge.from_dict(e) for e in edges]

    # --- Consolidation results ---

    def save_consolidation_result(self, result: ConsolidationResult) -> None:
        results = self._read_json("consolidations")
        results.append(result.to_dict())
        self._write_json("consolidations", results)

    def load_latest_consolidation(
        self, project_id: str
    ) -> ConsolidationResult | None:
        results = self._read_json("consolidations")
        project_results = [r for r in results if r.get("project_id") == project_id]
        if not project_results:
            return None
        return ConsolidationResult(**project_results[-1])

    # --- Raw ---

    def save_raw(self, key: str, data: Any) -> None:
        path = self._path(f"raw_{key}")
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def load_raw(self, key: str) -> Any | None:
        path = self._path(f"raw_{key}")
        if not path.exists():
            return None
        with open(path, "r") as f:
            return json.load(f)

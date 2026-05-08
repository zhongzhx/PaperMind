"""Evidence Graph service for managing entity-relationship graphs.

Builds, reinforces, and queries the evidence graph — a structured
knowledge representation of project entities, their relationships,
and supporting evidence.
"""

from __future__ import annotations

from typing import Any

from researchos_learning_engine.domain.constants import EdgeRelation, EdgeStatus
from researchos_learning_engine.domain.schemas import (
    ConsolidationInput,
    EvidenceGraphEdge,
    MemoryRecord,
    ResearchPattern,
)
from researchos_learning_engine.utils.ids import new_edge_id
from researchos_learning_engine.utils.time import now_iso


class EvidenceGraphService:
    """Service for managing evidence graph edges."""

    def __init__(self) -> None:
        self._edges: dict[str, EvidenceGraphEdge] = {}

    def add_edge(self, edge: EvidenceGraphEdge) -> None:
        """Add or update an edge."""
        self._edges[edge.edge_id] = edge

    def get_edge(self, edge_id: str) -> EvidenceGraphEdge | None:
        return self._edges.get(edge_id)

    def get_edges_by_project(self, project_id: str) -> list[EvidenceGraphEdge]:
        return [e for e in self._edges.values() if e.project_id == project_id]

    def get_edges_for_node(self, node_id: str) -> list[EvidenceGraphEdge]:
        return [
            e
            for e in self._edges.values()
            if e.source_node == node_id or e.target_node == node_id
        ]

    def reinforce_edge(self, edge_id: str, ref: str) -> EvidenceGraphEdge | None:
        """Reinforce an edge by adding a new evidence reference."""
        edge = self._edges.get(edge_id)
        if edge is None:
            return None

        edge.weight = min(1.0, edge.weight + 0.1)
        edge.last_reinforced = now_iso()
        if ref not in edge.evidence_refs:
            edge.evidence_refs.append(ref)

        # Promote edge status if weight is high enough
        if edge.weight >= 0.8 and edge.status == EdgeStatus.WEAK:
            edge.status = EdgeStatus.CONFIRMED
        elif edge.weight >= 0.5 and edge.status == EdgeStatus.WEAK:
            edge.status = EdgeStatus.ACTIVE

        return edge

    def build_edges_from_patterns(
        self,
        patterns: list[ResearchPattern],
        project_id: str,
    ) -> list[EvidenceGraphEdge]:
        """Create evidence graph edges from research patterns.

        Connects mechanism nodes to experimental model nodes
        based on pattern data.
        """
        new_edges: list[EvidenceGraphEdge] = []

        for pattern in patterns:
            for mechanism in pattern.mechanisms:
                for model in pattern.experimental_models:
                    edge = EvidenceGraphEdge(
                        edge_id=new_edge_id(),
                        project_id=project_id,
                        source_node=f"mechanism:{mechanism}",
                        target_node=f"model:{model}",
                        relation=EdgeRelation.SUPPORTS,
                        weight=0.5,
                        evidence_refs=[pattern.paper_id],
                        status=EdgeStatus.WEAK,
                        last_reinforced=now_iso(),
                    )
                    self.add_edge(edge)
                    new_edges.append(edge)

        return new_edges

    def clear(self) -> None:
        """Clear all edges (useful for testing)."""
        self._edges.clear()

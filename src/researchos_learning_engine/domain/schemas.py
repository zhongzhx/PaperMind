"""Pydantic schemas for the Learning Engine domain.

All core data structures used across the engine are defined here.
These are the stable, versioned contracts — inputs and outputs must
adhere to these schemas.

Schema version: 1.0
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any, Dict, List, Optional

from researchos_learning_engine.domain.constants import (
    ENGINE_VERSION,
    SCHEMA_VERSION,
    EdgeRelation,
    EdgeStatus,
    EvidenceLevel,
    MemoryStatus,
    MemoryType,
    PaperStatus,
    SourceType,
    StudyType,
)


# ---------------------------------------------------------------------------
# JSON serialization helpers
# ---------------------------------------------------------------------------


def _to_dict(obj: Any) -> Any:
    """Recursively convert a dataclass instance to a JSON-serializable dict.

    Guarantees: no Python objects, no datetime objects, no Enum objects
    in the output — everything is plain dicts, lists, strings, numbers,
    booleans, or None.
    """
    if obj is None:
        return None
    if is_dataclass(obj):
        result = {}
        for f in fields(obj):
            value = getattr(obj, f.name)
            result[f.name] = _to_dict(value)
        return result
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (list, tuple)):
        return [_to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {str(key): _to_dict(value) for key, value in obj.items()}
    if isinstance(obj, (int, float, bool, str)):
        return obj
    # Fallback: convert to string for any remaining non-serializable types
    # (e.g. datetime, Decimal, custom objects)
    if hasattr(obj, "isoformat"):
        return str(obj.isoformat())
    return str(obj)


# Need to import Enum here for the serialization check
from enum import Enum


# ---------------------------------------------------------------------------
# Paper & Research Pattern
# ---------------------------------------------------------------------------


@dataclass
class PaperRecord:
    """A research paper record with full text and metadata."""

    paper_id: str = ""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    source_type: SourceType = SourceType.ABSTRACT_ONLY
    full_text: str = ""
    chunks: List[str] = field(default_factory=list)
    project_relevance_score: float = 0.5
    evidence_value_score: float = 0.5
    status: PaperStatus = PaperStatus.PENDING
    abstract: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PaperRecord:
        # Handle enum fields
        data = dict(data)
        if "source_type" in data and isinstance(data["source_type"], str):
            data["source_type"] = SourceType(data["source_type"])
        if "status" in data and isinstance(data["status"], str):
            data["status"] = PaperStatus(data["status"])
        # Filter unknown fields
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class ResearchPattern:
    """A structured research pattern extracted from a paper."""

    pattern_id: str = ""
    paper_id: str = ""
    project_id: str = ""
    research_question: str = ""
    study_type: StudyType = StudyType.OTHER
    core_logic: str = ""
    experimental_models: List[str] = field(default_factory=list)
    assays: List[str] = field(default_factory=list)
    mechanisms: List[str] = field(default_factory=list)
    omics_methods: List[str] = field(default_factory=list)
    statistical_methods: List[str] = field(default_factory=list)
    figure_logic: str = ""
    writing_pattern: str = ""
    innovations: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    reusable_insights: List[str] = field(default_factory=list)
    evidence_level: EvidenceLevel = EvidenceLevel.L2
    confidence: float = 0.5
    extracted_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ResearchPattern:
        data = dict(data)
        if "study_type" in data and isinstance(data["study_type"], str):
            data["study_type"] = StudyType(data["study_type"])
        if "evidence_level" in data and isinstance(data["evidence_level"], str):
            data["evidence_level"] = EvidenceLevel(data["evidence_level"])
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------


@dataclass
class ScoreBreakdown:
    """Traceable breakdown of a memory health score computation."""

    source_confidence: float = 0.0
    user_confirmation: float = 0.0
    project_relevance: float = 0.0
    evidence_support: float = 0.0
    retrieval_usefulness: float = 0.0
    recency: float = 0.0
    contradiction_penalty: float = 0.0
    redundancy_penalty: float = 0.0
    final_score: float = 0.0
    raw_components: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ScoreBreakdown:
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class MemoryRecord:
    """A structured memory record within a research project."""

    memory_id: str = ""
    project_id: str = ""
    memory_type: MemoryType = MemoryType.PROJECT_FACT
    content: str = ""
    source_refs: List[str] = field(default_factory=list)
    confidence: float = 0.5
    importance: float = 0.5
    recency_score: float = 1.0
    project_relevance: float = 0.5
    evidence_level: EvidenceLevel = EvidenceLevel.L0
    retrieval_count: int = 0
    contradiction_count: int = 0
    status: MemoryStatus = MemoryStatus.NORMAL
    score_breakdown: Optional[ScoreBreakdown] = None
    health_score: float = 0.0
    created_at: str = ""
    updated_at: str = ""
    last_reviewed: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemoryRecord:
        data = dict(data)
        if "memory_type" in data and isinstance(data["memory_type"], str):
            data["memory_type"] = MemoryType(data["memory_type"])
        if "evidence_level" in data and isinstance(data["evidence_level"], str):
            data["evidence_level"] = EvidenceLevel(data["evidence_level"])
        if "status" in data and isinstance(data["status"], str):
            data["status"] = MemoryStatus(data["status"])
        if "score_breakdown" in data and isinstance(data["score_breakdown"], dict):
            data["score_breakdown"] = ScoreBreakdown.from_dict(data["score_breakdown"])
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


# ---------------------------------------------------------------------------
# Evidence Graph
# ---------------------------------------------------------------------------


@dataclass
class EvidenceGraphNode:
    """A node in the evidence graph."""

    node_id: str = ""
    project_id: str = ""
    label: str = ""
    node_type: str = "concept"
    description: str = ""
    source_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceGraphNode:
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class EvidenceGraphEdge:
    """A weighted, typed connection between two evidence graph nodes."""

    edge_id: str = ""
    project_id: str = ""
    source_node: str = ""
    target_node: str = ""
    relation: EdgeRelation = EdgeRelation.SUPPORTS
    weight: float = 0.5
    evidence_refs: List[str] = field(default_factory=list)
    status: EdgeStatus = EdgeStatus.WEAK
    last_reinforced: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceGraphEdge:
        data = dict(data)
        if "relation" in data and isinstance(data["relation"], str):
            data["relation"] = EdgeRelation(data["relation"])
        if "status" in data and isinstance(data["status"], str):
            data["status"] = EdgeStatus(data["status"])
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


# ---------------------------------------------------------------------------
# Consolidation
# ---------------------------------------------------------------------------


@dataclass
class ConsolidationInput:
    """Full input to the sleep-cycle consolidation process."""

    project_id: str = ""
    project_title: str = ""
    project_description: str = ""
    recent_conversations: List[Dict[str, Any]] = field(default_factory=list)
    paper_records: List[PaperRecord] = field(default_factory=list)
    rag_chunks: List[Dict[str, Any]] = field(default_factory=list)
    memory_records: List[MemoryRecord] = field(default_factory=list)
    skill_runs: List[Dict[str, Any]] = field(default_factory=list)
    data_contexts: List[Dict[str, Any]] = field(default_factory=list)
    current_project_summary: str = ""
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConsolidationInput:
        data = dict(data)
        if "paper_records" in data:
            data["paper_records"] = [
                PaperRecord.from_dict(p) if isinstance(p, dict) else p
                for p in data["paper_records"]
            ]
        if "memory_records" in data:
            data["memory_records"] = [
                MemoryRecord.from_dict(m) if isinstance(m, dict) else m
                for m in data["memory_records"]
            ]
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class ConsolidationResult:
    """Full output of the sleep-cycle consolidation process."""

    project_id: str = ""
    promoted_memories: List[MemoryRecord] = field(default_factory=list)
    archived_memories: List[MemoryRecord] = field(default_factory=list)
    superseded_memories: List[MemoryRecord] = field(default_factory=list)
    new_research_patterns: List[ResearchPattern] = field(default_factory=list)
    new_evidence_edges: List[EvidenceGraphEdge] = field(default_factory=list)
    contradictions_detected: List[Dict[str, Any]] = field(default_factory=list)
    updated_project_summary: str = ""
    recommended_literature_queries: List[str] = field(default_factory=list)
    recommended_user_actions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_log: List[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION
    engine_version: str = ENGINE_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConsolidationResult:
        data = dict(data)
        if "promoted_memories" in data:
            data["promoted_memories"] = [
                MemoryRecord.from_dict(m) if isinstance(m, dict) else m
                for m in data["promoted_memories"]
            ]
        if "archived_memories" in data:
            data["archived_memories"] = [
                MemoryRecord.from_dict(m) if isinstance(m, dict) else m
                for m in data["archived_memories"]
            ]
        if "superseded_memories" in data:
            data["superseded_memories"] = [
                MemoryRecord.from_dict(m) if isinstance(m, dict) else m
                for m in data["superseded_memories"]
            ]
        if "new_research_patterns" in data:
            data["new_research_patterns"] = [
                ResearchPattern.from_dict(p) if isinstance(p, dict) else p
                for p in data["new_research_patterns"]
            ]
        if "new_evidence_edges" in data:
            data["new_evidence_edges"] = [
                EvidenceGraphEdge.from_dict(e) if isinstance(e, dict) else e
                for e in data["new_evidence_edges"]
            ]
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})

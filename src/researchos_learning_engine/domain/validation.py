"""Lightweight validation utilities for Learning Engine schemas.

Provides basic validation without external dependencies. Used to verify
field types, enum values, score ranges, and structural integrity of
all core schema types.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from researchos_learning_engine.domain.constants import (
    SCORE_MAX,
    SCORE_MIN,
    EvidenceLevel,
    MemoryStatus,
    MemoryType,
)
from researchos_learning_engine.domain.schemas import (
    ConsolidationInput,
    ConsolidationResult,
    EvidenceGraphEdge,
    MemoryRecord,
    PaperRecord,
    ResearchPattern,
)


class ValidationError(Exception):
    """Raised when a schema validation fails."""

    pass


def validate_score(value: float, field_name: str = "score") -> Optional[str]:
    """Check that a score is within [0, 1].

    Returns an error message string, or None if valid.
    """
    if not isinstance(value, (int, float)):
        return f"{field_name} must be a number, got {type(value).__name__}"
    if value < SCORE_MIN or value > SCORE_MAX:
        return f"{field_name} must be between {SCORE_MIN} and {SCORE_MAX}, got {value}"
    return None


def validate_enum(value: Any, enum_class: type, field_name: str) -> Optional[str]:
    """Check that a value is a valid member of an enum class.

    Accepts both Enum instances and raw string values.
    Returns an error message string, or None if valid.
    """
    if isinstance(value, enum_class):
        return None
    if isinstance(value, str):
        try:
            enum_class(value)
            return None
        except (ValueError, KeyError):
            valid = [e.value for e in enum_class]
            return f"{field_name}: '{value}' is not a valid {enum_class.__name__}; expected one of {valid}"
    return f"{field_name} must be a {enum_class.__name__} or string, got {type(value).__name__}"


def validate_non_empty_str(value: Any, field_name: str) -> Optional[str]:
    """Check that a required string field is non-empty."""
    if not isinstance(value, str):
        return f"{field_name} must be a string, got {type(value).__name__}"
    if not value.strip():
        return f"{field_name} must not be empty"
    return None


def validate_list_of_str(value: Any, field_name: str) -> Optional[str]:
    """Check that a field is a list of strings."""
    if not isinstance(value, list):
        return f"{field_name} must be a list, got {type(value).__name__}"
    for i, item in enumerate(value):
        if not isinstance(item, str):
            return f"{field_name}[{i}] must be a string, got {type(item).__name__}"
    return None


def validate_memory_record(mem: Any, depth: int = 0) -> List[str]:
    """Validate a MemoryRecord, returning a list of error messages.

    Returns an empty list if the record is valid.
    """
    errors: List[str] = []
    if depth > 0:
        return errors

    if not isinstance(mem, MemoryRecord):
        return [f"Expected MemoryRecord, got {type(mem).__name__}"]

    # Required fields
    err = validate_non_empty_str(mem.memory_id, "memory_id")
    if err:
        errors.append(err)
    err = validate_non_empty_str(mem.project_id, "project_id")
    if err:
        errors.append(err)

    # Enum fields
    err = validate_enum(mem.memory_type, MemoryType, "memory_type")
    if err:
        errors.append(err)
    err = validate_enum(mem.evidence_level, EvidenceLevel, "evidence_level")
    if err:
        errors.append(err)
    err = validate_enum(mem.status, MemoryStatus, "status")
    if err:
        errors.append(err)

    # Score fields
    err = validate_score(mem.confidence, "confidence")
    if err:
        errors.append(err)
    err = validate_score(mem.importance, "importance")
    if err:
        errors.append(err)
    err = validate_score(mem.project_relevance, "project_relevance")
    if err:
        errors.append(err)
    err = validate_score(mem.health_score, "health_score")
    if err:
        errors.append(err)

    # Source refs
    err = validate_list_of_str(mem.source_refs, "source_refs")
    if err:
        errors.append(err)

    return errors


def validate_paper_record(paper: Any, depth: int = 0) -> List[str]:
    """Validate a PaperRecord, returning a list of error messages."""
    errors: List[str] = []
    if depth > 0:
        return errors

    if not isinstance(paper, PaperRecord):
        return [f"Expected PaperRecord, got {type(paper).__name__}"]

    err = validate_non_empty_str(paper.paper_id, "paper_id")
    if err:
        errors.append(err)

    err = validate_score(paper.project_relevance_score, "project_relevance_score")
    if err:
        errors.append(err)
    err = validate_score(paper.evidence_value_score, "evidence_value_score")
    if err:
        errors.append(err)

    return errors


def validate_research_pattern(pattern: Any, depth: int = 0) -> List[str]:
    """Validate a ResearchPattern."""
    errors: List[str] = []
    if depth > 0:
        return errors

    if not isinstance(pattern, ResearchPattern):
        return [f"Expected ResearchPattern, got {type(pattern).__name__}"]

    err = validate_non_empty_str(pattern.pattern_id, "pattern_id")
    if err:
        errors.append(err)
    err = validate_non_empty_str(pattern.paper_id, "paper_id")
    if err:
        errors.append(err)
    err = validate_non_empty_str(pattern.project_id, "project_id")
    if err:
        errors.append(err)

    err = validate_enum(pattern.evidence_level, EvidenceLevel, "evidence_level")
    if err:
        errors.append(err)

    err = validate_score(pattern.confidence, "confidence")
    if err:
        errors.append(err)

    return errors


def validate_evidence_graph_edge(edge: Any, depth: int = 0) -> List[str]:
    """Validate an EvidenceGraphEdge."""
    errors: List[str] = []
    if depth > 0:
        return errors

    if not isinstance(edge, EvidenceGraphEdge):
        return [f"Expected EvidenceGraphEdge, got {type(edge).__name__}"]

    err = validate_non_empty_str(edge.edge_id, "edge_id")
    if err:
        errors.append(err)
    err = validate_non_empty_str(edge.project_id, "project_id")
    if err:
        errors.append(err)
    err = validate_non_empty_str(edge.source_node, "source_node")
    if err:
        errors.append(err)
    err = validate_non_empty_str(edge.target_node, "target_node")
    if err:
        errors.append(err)

    err = validate_score(edge.weight, "weight")
    if err:
        errors.append(err)

    err = validate_list_of_str(edge.evidence_refs, "evidence_refs")
    if err:
        errors.append(err)

    return errors


def validate_consolidation_input(input_data: Any) -> List[str]:
    """Validate a full ConsolidationInput, returning all error messages."""
    errors: List[str] = []

    if not isinstance(input_data, ConsolidationInput):
        return [f"Expected ConsolidationInput, got {type(input_data).__name__}"]

    # Required project_id
    err = validate_non_empty_str(input_data.project_id, "project_id")
    if err:
        errors.append(err)

    # Validate nested paper records
    for i, paper in enumerate(input_data.paper_records):
        paper_errors = validate_paper_record(paper)
        for pe in paper_errors:
            errors.append(f"paper_records[{i}]: {pe}")

    # Validate nested memory records
    for i, mem in enumerate(input_data.memory_records):
        mem_errors = validate_memory_record(mem)
        for me in mem_errors:
            errors.append(f"memory_records[{i}]: {me}")

    # Check type of list-of-dict fields
    for field_name in ("recent_conversations", "rag_chunks", "skill_runs", "data_contexts"):
        value = getattr(input_data, field_name, [])
        if not isinstance(value, list):
            errors.append(f"{field_name} must be a list")

    return errors


def validate_consolidation_result(result: Any) -> List[str]:
    """Validate a full ConsolidationResult, returning all error messages."""
    errors: List[str] = []

    if not isinstance(result, ConsolidationResult):
        return [f"Expected ConsolidationResult, got {type(result).__name__}"]

    err = validate_non_empty_str(result.project_id, "project_id")
    if err:
        errors.append(err)

    # Validate nested memory lists
    for category in ("promoted_memories", "archived_memories", "superseded_memories"):
        for i, mem in enumerate(getattr(result, category, [])):
            mem_errors = validate_memory_record(mem)
            for me in mem_errors:
                errors.append(f"{category}[{i}]: {me}")

    # Validate patterns
    for i, pat in enumerate(result.new_research_patterns):
        pat_errors = validate_research_pattern(pat)
        for pe in pat_errors:
            errors.append(f"new_research_patterns[{i}]: {pe}")

    # Validate edges
    for i, edge in enumerate(result.new_evidence_edges):
        edge_errors = validate_evidence_graph_edge(edge)
        for ee in edge_errors:
            errors.append(f"new_evidence_edges[{i}]: {ee}")

    # processing_log should be present
    if not isinstance(result.processing_log, list):
        errors.append("processing_log must be a list")

    return errors


def raise_on_errors(errors: List[str], context: str = "Validation") -> None:
    """Raise ValidationError if there are any errors."""
    if errors:
        details = "\n  ".join(errors)
        raise ValidationError(f"{context} failed:\n  {details}")

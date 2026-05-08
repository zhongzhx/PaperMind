"""Rule-based confidence scoring for method knowledge records.

Computes 0.0–1.0 score from:
  - Source family / journal tier
  - Publication year recency
  - Section completeness (abstract, methods, results, discussion)
  - DOI presence
  - Text length
  - File type (PDF > TXT > MD)

Enhanced scoring (Phase 2) adds 6 more factors for deep learning data:
  - core_protocol_steps presence
  - quality_control_points presence
  - evidence_items presence
  - operation_reference_points presence
  - is_recent_and_deep_learned
  - extraction_warnings penalty

Phase 3 source policy update:
  - Source tier scoring is now graduated (tier_1=1.0 .. tier_4=0.3)
    instead of binary (Nature/Science/Cell=1.0 vs everything=0.0)
  - Source tier weight reduced; metadata completeness and method
    category clarity added as new factors
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Original 6-factor weights (Phase 3: reduced source_tier weight)
# ---------------------------------------------------------------------------

WEIGHT_SOURCE_TIER = 0.15          # was 0.30 — no longer binary
WEIGHT_RECENCY = 0.20              # was 0.15
WEIGHT_SECTION_COMPLETENESS = 0.30  # was 0.25
WEIGHT_DOI_PRESENCE = 0.10
WEIGHT_TEXT_LENGTH = 0.15           # was 0.10
WEIGHT_FILE_TYPE = 0.10

# ---------------------------------------------------------------------------
# Enhanced 15-factor weights (Phase 3: source_tier weight lowered,
# new factors for metadata_completeness, method_category_clarity,
# classic_foundational bonus)
# ---------------------------------------------------------------------------

ENHANCED_WEIGHT_SOURCE_TIER = 0.08           # was 0.20
ENHANCED_WEIGHT_SECTION_COMPLETENESS = 0.14  # was 0.15
ENHANCED_WEIGHT_RECENCY = 0.12               # was 0.10
ENHANCED_WEIGHT_DOI_PRESENCE = 0.04          # was 0.05
ENHANCED_WEIGHT_TEXT_LENGTH = 0.04           # was 0.05
ENHANCED_WEIGHT_FILE_TYPE = 0.04             # was 0.05
ENHANCED_WEIGHT_CORE_PROTOCOL_STEPS = 0.10
ENHANCED_WEIGHT_QUALITY_CONTROL = 0.05
ENHANCED_WEIGHT_EVIDENCE_ITEMS = 0.06        # was 0.05
ENHANCED_WEIGHT_OPERATION_REF_POINTS = 0.06  # was 0.05
ENHANCED_WEIGHT_RECENT_DEEP_LEARNED = 0.10
ENHANCED_WEIGHT_WARNINGS_PENALTY = 0.05
ENHANCED_WEIGHT_METADATA_COMPLETENESS = 0.06   # NEW
ENHANCED_WEIGHT_METHOD_CATEGORY_CLARITY = 0.04 # NEW
ENHANCED_WEIGHT_CLASSIC_FOUNDATIONAL = 0.02    # NEW
# Sum = 1.00


# ---------------------------------------------------------------------------
# Base scoring helpers (shared between original and enhanced)
# ---------------------------------------------------------------------------


def _score_source_tier(source_family: str) -> float:
    """Legacy binary scoring — 1.0 for Nature/Science/Cell, 0.0 otherwise."""
    return 1.0 if source_family in ("Nature", "Science", "Cell") else 0.0


def _score_source_tier_from_tier(source_tier: str) -> float:
    """Graduated scoring based on the new SourceTier enum value."""
    tier_scores = {
        "tier_1_high_impact": 1.0,
        "tier_2_field_leading": 0.8,
        "tier_3_standard_peer_reviewed": 0.6,
        "tier_4_uncertain_or_low_metadata": 0.3,
    }
    return tier_scores.get(source_tier, 0.0)


def _score_recency(year: Optional[int], recent_year_start: int) -> float:
    if year is None:
        return 0.0
    if year >= recent_year_start:
        return 1.0
    if year >= recent_year_start - 5:
        return 0.8
    if year >= 2010:
        return 0.5
    return 0.2


def _score_section_completeness(sections: Dict[str, bool]) -> float:
    essential = ["abstract", "methods", "results", "discussion"]
    present = sum(1 for s in essential if sections.get(s, False))
    return present / len(essential)


def _score_doi_presence(doi: str) -> float:
    return 1.0 if doi else 0.0


def _score_text_length(text: str) -> float:
    length = len(text)
    if length >= 10000:
        return 1.0
    if length >= 5000:
        return 0.8
    if length >= 1000:
        return 0.5
    if length >= 100:
        return 0.2
    return 0.0


def _score_file_type(source_type: str) -> float:
    return {"pdf": 1.0, "txt": 0.8, "md": 0.7}.get(source_type, 0.3)


def _score_title_presence(title: str) -> float:
    return 1.0 if title.strip() else 0.0


def _score_journal_presence(journal: str) -> float:
    return 1.0 if journal.strip() else 0.0


def _score_year_presence(year: Optional[int]) -> float:
    return 1.0 if year is not None else 0.0


def _score_has_method_category(category: str) -> float:
    return 1.0 if category.strip() else 0.0


# ---------------------------------------------------------------------------
# Phase 3: New scoring helpers
# ---------------------------------------------------------------------------


def _score_metadata_quality(assess: Optional[Dict[str, bool]]) -> float:
    """Score based on metadata quality flags."""
    if not assess or len(assess) == 0:
        return 0.0
    present = sum(1 for v in assess.values() if v)
    return present / len(assess)


def _score_method_category_clarity(category: str) -> float:
    return 1.0 if category and category.strip() else 0.0


def _score_is_classic_foundational(is_classic: bool) -> float:
    return 1.0 if is_classic else 0.0


# ---------------------------------------------------------------------------
# Enhanced scoring helpers (Phase 2)
# ---------------------------------------------------------------------------


def _score_core_protocol_steps(steps: Optional[List[str]]) -> float:
    if not steps:
        return 0.0
    return min(1.0, len(steps) / 5.0)


def _score_quality_control_points(points: Optional[List[str]]) -> float:
    if not points:
        return 0.0
    return min(1.0, len(points) / 3.0)


def _score_evidence_items(items: Optional[List[Any]]) -> float:
    if not items:
        return 0.0
    return min(1.0, len(items) / 5.0)


def _score_operation_reference_points(points: Optional[List[str]]) -> float:
    if not points:
        return 0.0
    return min(1.0, len(points) / 3.0)


def _score_is_recent_and_deep_learned(
    is_recent: bool, deep_learning: Optional[Any],
) -> float:
    if is_recent and deep_learning is not None:
        return 1.0
    if is_recent:
        return 0.5  # recent but no deep learning
    return 0.0


def _score_extraction_warnings(warnings: Optional[List[str]]) -> float:
    if not warnings:
        return 1.0  # no warnings = perfect score
    penalty = min(len(warnings) / 5.0, 1.0)
    return 1.0 - penalty


# ---------------------------------------------------------------------------
# Original compute_confidence (backward compatible, updated weights)
# ---------------------------------------------------------------------------


def compute_confidence(
    source_family: str = "",
    year: Optional[int] = None,
    has_doi: bool = False,
    text: str = "",
    source_type: str = "",
    sections: Optional[Dict[str, bool]] = None,
    recent_year_start: int = 2021,
    source_tier: str = "",  # NEW: use new graduated scoring if provided
) -> float:
    """Compute overall confidence score (0.0–1.0) — original 6-factor version.

    If source_tier is provided (non-empty), uses graduated source tier scoring.
    Otherwise falls back to legacy binary source_family scoring.
    """
    if sections is None:
        sections = {}
    src_score = (
        _score_source_tier_from_tier(source_tier) if source_tier
        else _score_source_tier(source_family)
    )
    score = (
        WEIGHT_SOURCE_TIER * src_score
        + WEIGHT_RECENCY * _score_recency(year, recent_year_start)
        + WEIGHT_SECTION_COMPLETENESS * _score_section_completeness(sections)
        + WEIGHT_DOI_PRESENCE * _score_doi_presence("x" if has_doi else "")
        + WEIGHT_TEXT_LENGTH * _score_text_length(text)
        + WEIGHT_FILE_TYPE * _score_file_type(source_type)
    )
    return round(min(max(score, 0.0), 1.0), 4)


def compute_confidence_with_breakdown(
    source_family: str = "",
    year: Optional[int] = None,
    has_doi: bool = False,
    text: str = "",
    source_type: str = "",
    sections: Optional[Dict[str, bool]] = None,
    recent_year_start: int = 2021,
    source_tier: str = "",  # NEW
) -> Dict[str, float]:
    """Compute confidence with per-component breakdown — original version."""
    if sections is None:
        sections = {}
    src_score = (
        _score_source_tier_from_tier(source_tier) if source_tier
        else _score_source_tier(source_family)
    )
    components = {
        "source_tier": src_score,
        "recency": _score_recency(year, recent_year_start),
        "section_completeness": _score_section_completeness(sections),
        "doi_presence": _score_doi_presence("x" if has_doi else ""),
        "text_length": _score_text_length(text),
        "file_type": _score_file_type(source_type),
    }
    total = (
        WEIGHT_SOURCE_TIER * components["source_tier"]
        + WEIGHT_RECENCY * components["recency"]
        + WEIGHT_SECTION_COMPLETENESS * components["section_completeness"]
        + WEIGHT_DOI_PRESENCE * components["doi_presence"]
        + WEIGHT_TEXT_LENGTH * components["text_length"]
        + WEIGHT_FILE_TYPE * components["file_type"]
    )
    return {
        "score": round(min(max(total, 0.0), 1.0), 4),
        "components": components,
    }


# ---------------------------------------------------------------------------
# Enhanced compute_confidence (Phase 2 + Phase 3, 15 factors)
# ---------------------------------------------------------------------------


def compute_enhanced_confidence(
    source_family: str = "",
    source_tier: str = "",  # NEW: use graduated scoring if provided
    year: Optional[int] = None,
    has_doi: bool = False,
    text: str = "",
    source_type: str = "",
    sections: Optional[Dict[str, bool]] = None,
    recent_year_start: int = 2021,
    title: str = "",
    journal: str = "",
    method_category: str = "",
    core_protocol_steps: Optional[List[str]] = None,
    quality_control_points: Optional[List[str]] = None,
    evidence_items: Optional[List[Any]] = None,
    operation_reference_points: Optional[List[str]] = None,
    deep_learning: Optional[Any] = None,
    extraction_warnings: Optional[List[str]] = None,
    is_recent: bool = False,
    # NEW Phase 3 parameters
    metadata_assessment: Optional[Dict[str, bool]] = None,
    is_classic_foundational: bool = False,
) -> float:
    """Compute enhanced confidence score (0.0–1.0) with 15 factors."""
    if sections is None:
        sections = {}
    if core_protocol_steps is None:
        core_protocol_steps = []
    if quality_control_points is None:
        quality_control_points = []
    if evidence_items is None:
        evidence_items = []
    if operation_reference_points is None:
        operation_reference_points = []
    if extraction_warnings is None:
        extraction_warnings = []

    src_score = (
        _score_source_tier_from_tier(source_tier) if source_tier
        else _score_source_tier(source_family)
    )

    score = (
        ENHANCED_WEIGHT_SOURCE_TIER * src_score
        + ENHANCED_WEIGHT_SECTION_COMPLETENESS * _score_section_completeness(sections)
        + ENHANCED_WEIGHT_RECENCY * _score_recency(year, recent_year_start)
        + ENHANCED_WEIGHT_DOI_PRESENCE * _score_doi_presence("x" if has_doi else "")
        + ENHANCED_WEIGHT_TEXT_LENGTH * _score_text_length(text)
        + ENHANCED_WEIGHT_FILE_TYPE * _score_file_type(source_type)
        + ENHANCED_WEIGHT_CORE_PROTOCOL_STEPS * _score_core_protocol_steps(core_protocol_steps)
        + ENHANCED_WEIGHT_QUALITY_CONTROL * _score_quality_control_points(quality_control_points)
        + ENHANCED_WEIGHT_EVIDENCE_ITEMS * _score_evidence_items(evidence_items)
        + ENHANCED_WEIGHT_OPERATION_REF_POINTS * _score_operation_reference_points(operation_reference_points)
        + ENHANCED_WEIGHT_RECENT_DEEP_LEARNED * _score_is_recent_and_deep_learned(is_recent, deep_learning)
        + ENHANCED_WEIGHT_WARNINGS_PENALTY * _score_extraction_warnings(extraction_warnings)
        + ENHANCED_WEIGHT_METADATA_COMPLETENESS * _score_metadata_quality(metadata_assessment)
        + ENHANCED_WEIGHT_METHOD_CATEGORY_CLARITY * _score_method_category_clarity(method_category)
        + ENHANCED_WEIGHT_CLASSIC_FOUNDATIONAL * _score_is_classic_foundational(is_classic_foundational)
    )
    return round(min(max(score, 0.0), 1.0), 4)


def compute_enhanced_confidence_with_breakdown(
    source_family: str = "",
    source_tier: str = "",  # NEW
    year: Optional[int] = None,
    has_doi: bool = False,
    text: str = "",
    source_type: str = "",
    sections: Optional[Dict[str, bool]] = None,
    recent_year_start: int = 2021,
    title: str = "",
    journal: str = "",
    method_category: str = "",
    core_protocol_steps: Optional[List[str]] = None,
    quality_control_points: Optional[List[str]] = None,
    evidence_items: Optional[List[Any]] = None,
    operation_reference_points: Optional[List[str]] = None,
    deep_learning: Optional[Any] = None,
    extraction_warnings: Optional[List[str]] = None,
    is_recent: bool = False,
    # NEW Phase 3 parameters
    metadata_assessment: Optional[Dict[str, bool]] = None,
    is_classic_foundational: bool = False,
) -> Dict[str, Any]:
    """Compute enhanced confidence with per-component breakdown."""
    if sections is None:
        sections = {}
    if core_protocol_steps is None:
        core_protocol_steps = []
    if quality_control_points is None:
        quality_control_points = []
    if evidence_items is None:
        evidence_items = []
    if operation_reference_points is None:
        operation_reference_points = []
    if extraction_warnings is None:
        extraction_warnings = []

    src_score = (
        _score_source_tier_from_tier(source_tier) if source_tier
        else _score_source_tier(source_family)
    )

    components = {
        "source_tier": src_score,
        "section_completeness": _score_section_completeness(sections),
        "recency": _score_recency(year, recent_year_start),
        "doi_presence": _score_doi_presence("x" if has_doi else ""),
        "text_length": _score_text_length(text),
        "file_type": _score_file_type(source_type),
        "core_protocol_steps": _score_core_protocol_steps(core_protocol_steps),
        "quality_control_points": _score_quality_control_points(quality_control_points),
        "evidence_items": _score_evidence_items(evidence_items),
        "operation_reference_points": _score_operation_reference_points(operation_reference_points),
        "is_recent_deep_learned": _score_is_recent_and_deep_learned(is_recent, deep_learning),
        "extraction_warnings": _score_extraction_warnings(extraction_warnings),
        "metadata_completeness": _score_metadata_quality(metadata_assessment),
        "method_category_clarity": _score_method_category_clarity(method_category),
        "classic_foundational": _score_is_classic_foundational(is_classic_foundational),
    }
    total = (
        ENHANCED_WEIGHT_SOURCE_TIER * components["source_tier"]
        + ENHANCED_WEIGHT_SECTION_COMPLETENESS * components["section_completeness"]
        + ENHANCED_WEIGHT_RECENCY * components["recency"]
        + ENHANCED_WEIGHT_DOI_PRESENCE * components["doi_presence"]
        + ENHANCED_WEIGHT_TEXT_LENGTH * components["text_length"]
        + ENHANCED_WEIGHT_FILE_TYPE * components["file_type"]
        + ENHANCED_WEIGHT_CORE_PROTOCOL_STEPS * components["core_protocol_steps"]
        + ENHANCED_WEIGHT_QUALITY_CONTROL * components["quality_control_points"]
        + ENHANCED_WEIGHT_EVIDENCE_ITEMS * components["evidence_items"]
        + ENHANCED_WEIGHT_OPERATION_REF_POINTS * components["operation_reference_points"]
        + ENHANCED_WEIGHT_RECENT_DEEP_LEARNED * components["is_recent_deep_learned"]
        + ENHANCED_WEIGHT_WARNINGS_PENALTY * components["extraction_warnings"]
        + ENHANCED_WEIGHT_METADATA_COMPLETENESS * components["metadata_completeness"]
        + ENHANCED_WEIGHT_METHOD_CATEGORY_CLARITY * components["method_category_clarity"]
        + ENHANCED_WEIGHT_CLASSIC_FOUNDATIONAL * components["classic_foundational"]
    )
    return {
        "score": round(min(max(total, 0.0), 1.0), 4),
        "components": components,
    }

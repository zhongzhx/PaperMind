"""Memory health scoring engine.

Provides rule-based, interpretable scoring for memory records.
The scoring formula is fully deterministic and produces a traceable
ScoreBreakdown for each memory.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from researchos_learning_engine.domain.constants import (
    EVIDENCE_LEVEL_CONFIDENCE,
    PENALTY_CONTRADICTION,
    PENALTY_REDUNDANCY,
    RECENCY_HALF_LIFE_DAYS,
    SCORE_THRESHOLDS,
    WEIGHT_EVIDENCE_SUPPORT,
    WEIGHT_PROJECT_RELEVANCE,
    WEIGHT_RECENCY,
    WEIGHT_RETRIEVAL_USEFULNESS,
    WEIGHT_SOURCE_CONFIDENCE,
    WEIGHT_USER_CONFIRMATION,
    EvidenceLevel,
    MemoryStatus,
)
from researchos_learning_engine.domain.schemas import MemoryRecord, ScoreBreakdown


def compute_recency_score(
    updated_at: str | None,
    half_life_days: float = RECENCY_HALF_LIFE_DAYS,
) -> float:
    """Compute a decay-adjusted recency score.

    Uses exponential decay: score = 2^(-days_since_update / half_life)
    Returns 1.0 for current timestamps, approaching 0.0 over time.
    """
    if not updated_at:
        return 0.5  # neutral default for unknown timestamps

    try:
        updated = datetime.fromisoformat(updated_at)
    except (ValueError, TypeError):
        return 0.5

    now = datetime.now(timezone.utc)
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)

    days_since = (now - updated).total_seconds() / 86400.0
    if days_since < 0:
        return 1.0  # future timestamps → max recency

    return float(2 ** (-days_since / half_life_days))


def compute_evidence_support(evidence_level: EvidenceLevel) -> float:
    """Map evidence level to a numeric support score (0-1)."""
    return EVIDENCE_LEVEL_CONFIDENCE.get(evidence_level, 0.1)


def assign_memory_status(score: float) -> MemoryStatus:
    """Assign memory lifecycle status based on health score thresholds."""
    if score >= SCORE_THRESHOLDS[MemoryStatus.ACTIVE]:
        return MemoryStatus.ACTIVE
    elif score >= SCORE_THRESHOLDS[MemoryStatus.NORMAL]:
        return MemoryStatus.NORMAL
    elif score >= SCORE_THRESHOLDS[MemoryStatus.ARCHIVED]:
        return MemoryStatus.ARCHIVED
    else:
        return MemoryStatus.DEPRECATED


def compute_memory_health_score(memory: MemoryRecord) -> tuple[float, ScoreBreakdown]:
    """Compute the memory health score with a full traceable breakdown.

    Formula:
        health_score =
          + 0.25 * source_confidence       (# confidence field)
          + 0.20 * user_confirmation        (# user facts / decisions → high)
          + 0.20 * project_relevance         (# project_relevance field)
          + 0.15 * evidence_support          (# from evidence_level)
          + 0.10 * retrieval_usefulness      (# from retrieval_count)
          + 0.05 * recency                   (# decay-adjusted)
          - 0.20 * contradiction_penalty     (# from contradiction_count)
          - 0.10 * redundancy_penalty        (# placeholder for future dedup)

    Returns:
        Tuple of (final_score, ScoreBreakdown)
    """
    # --- Raw component values ---

    # 1. Source confidence (from memory.confidence field)
    source_confidence = max(0.0, min(1.0, memory.confidence))

    # 2. User confirmation — user_fact / decision / failure types are more reliable
    user_confirmation_map = {
        "user_fact": 0.9,
        "project_fact": 0.7,
        "paper_evidence": 0.5,
        "experiment_result": 0.8,
        "decision": 0.85,
        "failure": 0.75,
        "skill_run": 0.4,
        "data_conclusion": 0.8,
    }
    user_confirmation = user_confirmation_map.get(
        memory.memory_type.value if hasattr(memory.memory_type, "value") else str(memory.memory_type),
        0.5,
    )

    # 3. Project relevance
    project_relevance = max(0.0, min(1.0, memory.project_relevance))

    # 4. Evidence support from evidence_level
    evidence_support = compute_evidence_support(memory.evidence_level)

    # 5. Retrieval usefulness — sigmoid-like scaling of retrieval_count
    #    More retrievals → higher usefulness, but diminishing returns.
    retrieval_usefulness = 1.0 - math.exp(-0.3 * memory.retrieval_count)

    # 6. Recency
    recency_s = compute_recency_score(memory.updated_at)

    # 7. Contradiction penalty
    contradiction_penalty = min(1.0, PENALTY_CONTRADICTION * memory.contradiction_count)

    # 8. Redundancy penalty (placeholder)
    redundancy_penalty = 0.0  # Future: detect duplicates

    # --- Weighted sum ---
    raw = {
        "source_confidence": source_confidence,
        "user_confirmation": user_confirmation,
        "project_relevance": project_relevance,
        "evidence_support": evidence_support,
        "retrieval_usefulness": retrieval_usefulness,
        "recency": recency_s,
    }

    final_score = (
        WEIGHT_SOURCE_CONFIDENCE * source_confidence
        + WEIGHT_USER_CONFIRMATION * user_confirmation
        + WEIGHT_PROJECT_RELEVANCE * project_relevance
        + WEIGHT_EVIDENCE_SUPPORT * evidence_support
        + WEIGHT_RETRIEVAL_USEFULNESS * retrieval_usefulness
        + WEIGHT_RECENCY * recency_s
        - contradiction_penalty
        - redundancy_penalty
    )

    # Clamp to [0, 1]
    final_score = max(0.0, min(1.0, final_score))

    breakdown = ScoreBreakdown(
        source_confidence=WEIGHT_SOURCE_CONFIDENCE * source_confidence,
        user_confirmation=WEIGHT_USER_CONFIRMATION * user_confirmation,
        project_relevance=WEIGHT_PROJECT_RELEVANCE * project_relevance,
        evidence_support=WEIGHT_EVIDENCE_SUPPORT * evidence_support,
        retrieval_usefulness=WEIGHT_RETRIEVAL_USEFULNESS * retrieval_usefulness,
        recency=WEIGHT_RECENCY * recency_s,
        contradiction_penalty=contradiction_penalty,
        redundancy_penalty=redundancy_penalty,
        final_score=final_score,
        raw_components=raw,
    )

    return final_score, breakdown


def score_and_update_memory(memory: MemoryRecord) -> MemoryRecord:
    """Compute health score, breakdown, and assign new status to a memory.

    This is the main scoring entry point for a single memory record.
    Returns an updated copy of the memory with new score/status/breakdown.
    """
    score, breakdown = compute_memory_health_score(memory)
    new_status = assign_memory_status(score)

    memory.health_score = score
    memory.score_breakdown = breakdown
    memory.status = new_status

    return memory

"""Rule-based paper quality scoring.

Scores a paper on a 0.0–1.0 scale based on journal tier, paper type,
section completeness, DOI presence, and recency. No LLM dependency.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from researchos_learning_engine.paper_learning.schemas import HighImpactPaperRecord, PaperSection

# Tier 1 — top general-science journals
_TIER_1: set[str] = {
    "nature", "science", "cell", "the lancet", "nejm", "nature medicine",
    "jama", "british medical journal", "bmj",
}

# Tier 2 — high-impact specialised journals
_TIER_2: set[str] = {
    "nature communications", "science advances", "cell research",
    "cell metabolism", "molecular cell", "nature immunology",
    "nature cell biology", "nature methods", "nature biotechnology",
    "nature genetics", "nature neuroscience", "immunity",
    "cancer cell", "cell stem cell", "neuron",
}

# Tier 3 — reputable field journals
_TIER_3: set[str] = {
    "journal of biological chemistry", "plos one", "scientific reports",
    "frontiers in immunology", "cell reports", "embo journal",
    "journal of ethnopharmacology", "phytomedicine", "biomedicine and pharmacotherapy",
    "international journal of molecular sciences", "molecules",
    "journal of agricultural and food chemistry", "food chemistry",
}

_CORE_SECTIONS: set[str] = {"introduction", "methods", "results", "discussion", "conclusion"}
_BONUS_SECTIONS: set[str] = {"abstract"}

_PAPER_TYPE_SCORE: dict[str, float] = {
    "meta_analysis": 25.0,
    "original_research": 22.0,
    "review": 18.0,
    "methods": 16.0,
    "protocol": 12.0,
}


def score_paper_quality(
    paper: HighImpactPaperRecord,
    sections: List[PaperSection],
) -> Tuple[float, Dict[str, float]]:
    """Score paper quality, returning (normalised_score, breakdown_dict).

    Raw score range 0–100, normalised to 0.0–1.0.

    Components:
      - Journal tier        (0–30)
      - Paper type          (0–25)
      - Section completeness (0–20)
      - DOI presence        (0–15)
      - Recency bonus       (0–10)
    """
    journal_pts = _journal_tier_score(paper.journal)
    type_pts = _paper_type_score(paper.paper_type)
    section_pts = _section_completeness(sections)
    doi_pts = 15.0 if paper.doi else 0.0
    recency_pts = _recency_bonus(paper.year, bool(paper.doi))

    raw = journal_pts + type_pts + section_pts + doi_pts + recency_pts
    normalised = max(0.0, min(1.0, raw / 100.0))

    breakdown = {
        "journal_tier": journal_pts,
        "paper_type": type_pts,
        "section_completeness": section_pts,
        "doi_presence": doi_pts,
        "recency": recency_pts,
        "raw_total": raw,
    }
    return normalised, breakdown


def _journal_tier_score(journal: str) -> float:
    if not journal or not journal.strip():
        return 10.0
    j = journal.strip().lower()
    if j in _TIER_1:
        return 30.0
    if j in _TIER_2:
        return 25.0
    if j in _TIER_3:
        return 20.0
    return 15.0


def _paper_type_score(paper_type: str) -> float:
    return _PAPER_TYPE_SCORE.get(paper_type, 5.0)


def _section_completeness(sections: List[PaperSection]) -> float:
    found: set[str] = set()
    for s in sections:
        st = s.section_type.lower() if s.section_type else ""
        if st in _CORE_SECTIONS or st in _BONUS_SECTIONS:
            found.add(st)

    core_present = len(_CORE_SECTIONS & found)
    score = core_present * 4.0  # 4 pts per core section, max 20
    return min(20.0, score)


def _recency_bonus(year: int, has_doi: bool) -> float:
    if year <= 0:
        return 0.0
    current = 2026
    age = current - year
    if age <= 1:
        return 10.0 if has_doi else 7.0
    if age <= 3:
        return 8.0 if has_doi else 5.0
    if age <= 5:
        return 5.0 if has_doi else 3.0
    if age <= 10:
        return 2.0
    return 0.0

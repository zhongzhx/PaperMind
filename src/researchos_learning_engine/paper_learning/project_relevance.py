"""Project relevance scorer.

Computes Jaccard similarity between paper content and a project
description. No LLM dependency — pure keyword overlap.
"""

from __future__ import annotations

import re
from typing import Set

from researchos_learning_engine.paper_learning.schemas import HighImpactPaperRecord

# Words too common to be meaningful for relevance matching
_STOP_WORDS: Set[str] = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "in", "of", "to", "and", "or", "for", "with", "on", "by", "from",
    "at", "as", "but", "not", "that", "this", "these", "those", "it",
    "its", "we", "our", "they", "their", "has", "have", "had", "do",
    "does", "did", "will", "would", "can", "could", "may", "might",
    "shall", "should", "about", "into", "over", "than", "then", "also",
    "very", "just", "each", "all", "both", "more", "most", "some",
    "any", "no", "nor", "not", "only", "same", "so", "such",
}


def score_project_relevance(
    paper: HighImpactPaperRecord,
    project_description: str,
) -> float:
    """Score relevance of a paper to a project description (0.0–1.0).

    Uses Jaccard similarity on tokenised text from:
    - Title (weight 0.35)
    - Abstract / first content words (weight 0.35)
    - Full text sample (weight 0.30)

    Returns 0.5 if project_description is empty.
    """
    if not project_description or not project_description.strip():
        return 0.5

    project_tokens = _tokenize(project_description)
    if not project_tokens:
        return 0.5

    # Title overlap
    title_tokens = _tokenize(paper.title)
    title_sim = _jaccard(title_tokens, project_tokens)

    # Content overlap — use full_text as proxy for abstract
    content_text = paper.full_text[:10000] if paper.full_text else ""
    content_tokens = _tokenize(content_text)
    content_sim = _jaccard(content_tokens, project_tokens)

    # Additional sample from full text (deeper parts)
    deeper_text = paper.full_text[10000:20000] if len(paper.full_text) > 10000 else ""
    deeper_tokens = _tokenize(deeper_text)
    deeper_sim = _jaccard(deeper_tokens, project_tokens)

    score = 0.35 * title_sim + 0.35 * content_sim + 0.30 * deeper_sim
    return max(0.0, min(1.0, score))


def _tokenize(text: str) -> Set[str]:
    """Lowercase, extract word tokens, remove stop words and short tokens."""
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9\-]+", text.lower())
    return {w for w in words if w not in _STOP_WORDS and len(w) > 1}


def _jaccard(a: Set[str], b: Set[str]) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)

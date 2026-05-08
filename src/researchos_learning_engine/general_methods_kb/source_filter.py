"""Classify paper metadata quality and detect red-flag files.

NEW POLICY (Phase 3):
  - All user-provided papers are processed — no hard source family filter.
  - Non-Nature/Science/Cell papers are NOT skipped; they receive a lower
    source_tier and potentially lower confidence, but still get extracted.
  - Only truly unprocessable files are skipped: empty, corrupted, non-paper
    content, or ones where the text is completely unparseable.
  - "Uncertain metadata" means we couldn't identify journal or year, but
    the paper is still processed with warnings.

This replaces the old behavior of filtering by allowed source families.
"""

from __future__ import annotations

from typing import Dict, List, Optional


def assess_metadata_quality(
    source_family: str,
    journal: str,
    year: Optional[int],
    doi: str,
    text_length: int,
    file_ext: str,
) -> Dict[str, bool]:
    """Assess metadata quality flags for a paper.

    Returns a dict of boolean quality indicators:
      - has_journal: journal name is recognizable
      - has_year: year was extracted
      - has_doi: DOI was found
      - has_content: text has substantial content
    """
    return {
        "has_journal": bool(journal and journal.strip()),
        "has_year": year is not None,
        "has_doi": bool(doi and doi.strip()),
        "has_content": text_length > 100,
    }


def should_skip_paper(
    text: str,
    file_ext: str,
    text_length: int,
    source_family: str,
) -> str:
    """Determine if a paper should be truly skipped (not processed at all).

    Returns empty string "" if the paper should be processed.
    Returns a non-empty string (reason) if the paper should be skipped.

    Skip reasons (only for truly unprocessable files):
      - "empty_content": text is empty or whitespace only
      - "too_short": text is too short to extract any useful information
      - "not_a_paper": text doesn't look like a research paper
    """
    if not text or not text.strip():
        return "empty_content"

    if text_length < 50:
        return "too_short"

    # Check for non-paper content indicators
    lower = text.lower().strip()
    non_paper_hints = [
        "newspaper article", "blog post", "forum discussion",
    ]
    for hint in non_paper_hints:
        if lower.startswith(hint) or hint in lower[:200]:
            return "not_a_paper"

    # Empty PDF bytes that produced no text
    if file_ext == ".pdf" and text_length < 100 and not source_family:
        return "pdf_extraction_failed"

    return ""


def classify_source(
    source_family: str,
    journal: str,
    file_stem: str,
    parent_dir_name: str,
    text_start: str,
) -> str:
    """Classify source metadata confidence.

    DEPRECATED — kept for backward compatibility.
    Returns "accepted" for all papers that can be processed.

    The real filtering now happens in should_skip_paper().
    """
    return "accepted"


def filter_papers(
    scanned_files: List[dict],
    metadata_list: List[dict],
) -> Dict[str, List[dict]]:
    """Filter scanned papers — all accepted by default.

    DEPRECATED — kept for backward compatibility.
    Returns all papers as "accepted".
    The real filtering now happens in kb_builder's build loop.

    Returns:
        {"accepted": [...], "skipped": [], "uncertain": []}
    """
    accepted: List[dict] = []
    for i, file_info in enumerate(scanned_files):
        meta = metadata_list[i] if i < len(metadata_list) else {}
        accepted.append({
            "file_info": file_info,
            "metadata": meta,
        })

    return {
        "accepted": accepted,
        "skipped": [],
        "uncertain": [],
    }

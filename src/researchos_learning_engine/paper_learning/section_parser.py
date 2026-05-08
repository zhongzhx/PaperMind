"""Paper section parser — splits full text into structured sections.

Uses regex-based heading detection to segment paper text into
Abstract, Introduction, Methods, Results, Discussion, Conclusion,
Figure Captions, and Supplementary sections.
"""

from __future__ import annotations

import re
from typing import List

from researchos_learning_engine.paper_learning.schemas import PaperSection, SectionType

# Section heading patterns in priority order.
# Matches headings at the start of a line (with optional numbering prefix).
_SECTION_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^\s*(?:Abstract|ABSTRACT)\s*$", re.MULTILINE), "abstract"),
    (re.compile(r"^\s*(?:Introduction|INTRODUCTION|Background|BACKGROUND)\s*$", re.MULTILINE), "introduction"),
    (re.compile(r"^\s*(?:Materials?\s+(?:and|&)\s+Methods|METHODS|[Mm]ethods|Materials?\s+and\s+Methods|Experimental\s+Procedures)\s*$", re.MULTILINE), "methods"),
    (re.compile(r"^\s*(?:Results|RESULTS)\s*$", re.MULTILINE), "results"),
    (re.compile(r"^\s*(?:Results?\s+(?:and|&)\s+Discussion|RESULTS\s+AND\s+DISCUSSION)\s*$", re.MULTILINE), "results_and_discussion"),
    (re.compile(r"^\s*(?:Discussion|DISCUSSION)\s*$", re.MULTILINE), "discussion"),
    (re.compile(r"^\s*(?:Conclusion|CONCLUSION|Conclusions|CONCLUSIONS)\s*$", re.MULTILINE), "conclusion"),
    (re.compile(r"^\s*(?:Figure\s+Captions?|FIGURE\s+CAPTIONS?|Figure\s+Legends?)\s*$", re.MULTILINE), "figure_caption"),
    (re.compile(r"^\s*(?:Supplementary|SUPPLEMENTARY|Supplemental|SUPPLEMENTAL|Supporting\s+Information|SUPPORTING\s+INFORMATION)\s*", re.MULTILINE), "supplementary"),
    (re.compile(r"^\s*(?:References|REFERENCES|Bibliography|BIBLIOGRAPHY)\s*$", re.MULTILINE), "references"),
]


def parse_sections(full_text: str, paper_id: str = "") -> List[PaperSection]:
    """Split full_text into PaperSection objects.

    Uses regex heading detection. Text before the first recognised
    heading is discarded (title/author block). Unknown headings
    between known sections are merged into the preceding section.

    Args:
        full_text: Raw paper text (may contain \n).
        paper_id: Identifier to attach to each section.

    Returns:
        List of PaperSection ordered as they appear in the text.
        Returns an empty list for empty input.
    """
    if not full_text or not full_text.strip():
        return []

    lines = full_text.split("\n")
    sections: List[PaperSection] = []
    found_any = False

    current_label: str = "preamble"
    current_lines: List[str] = []
    current_order: int = -1

    for line in lines:
        match = _match_heading(line)
        if match is not None:
            found_any = True
            # Flush previous section if it has content
            content = _flush(current_lines)
            if content:
                section_type = _label_to_section_type(current_label)
                if section_type is not None:
                    sections.append(PaperSection(
                        paper_id=paper_id,
                        section_type=section_type.value,
                        title=current_label,
                        text=content,
                        order=current_order,
                    ))
            current_label = match
            current_lines = []
            current_order += 1
        else:
            current_lines.append(line)

    # Flush final section
    content = _flush(current_lines)
    if content and current_label != "preamble":
        section_type = _label_to_section_type(current_label)
        if section_type is not None:
            sections.append(PaperSection(
                paper_id=paper_id,
                section_type=section_type.value,
                title=current_label,
                text=content,
                order=current_order,
            ))
    elif content and not found_any:
        # No headings found at all → return as a single body section
        sections.append(PaperSection(
            paper_id=paper_id,
            section_type="unknown",
            title="body",
            text=content,
            order=0,
        ))

    return sections


def _match_heading(line: str) -> str | None:
    """Check if a line matches a recognised section heading.

    Returns the matched label string, or None.
    """
    stripped = line.strip()
    if not stripped:
        return None
    # Exclude figure caption references (e.g. "Figure 1. ...")
    if re.match(r"^\s*(?:Fig(?:ure)?\.?\s*\d)", stripped):
        return None
    for pattern, label in _SECTION_PATTERNS:
        if pattern.match(line):
            return label
    # Also check for numbered headings like "1. Introduction"
    numbered = re.match(r"^\s*\d+\.?\s+(.+)", stripped)
    if numbered:
        candidate = numbered.group(1).strip()
        for pattern, label in _SECTION_PATTERNS:
            # Create a new pattern that matches just the heading text
            simple = re.compile(r"^\s*" + re.escape(candidate) + r"\s*$", re.MULTILINE)
            if simple.match(candidate):
                return label
    return None


def _flush(lines: List[str]) -> str:
    """Join lines and strip whitespace."""
    return "\n".join(lines).strip() if lines else ""


def _label_to_section_type(label: str) -> SectionType | None:
    """Map a matched label back to a SectionType enum."""
    mapping = {
        "abstract": SectionType.ABSTRACT,
        "introduction": SectionType.INTRODUCTION,
        "methods": SectionType.METHODS,
        "results": SectionType.RESULTS,
        "results_and_discussion": SectionType.RESULTS,
        "discussion": SectionType.DISCUSSION,
        "conclusion": SectionType.CONCLUSION,
        "figure_caption": SectionType.FIGURE_CAPTION,
        "supplementary": SectionType.SUPPLEMENTARY,
        "references": None,  # excluded from output
    }
    return mapping.get(label)

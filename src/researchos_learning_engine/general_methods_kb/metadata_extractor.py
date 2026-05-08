"""Extract metadata (title, journal, year, DOI, source family) from paper text
and file path information.

Rules:
  - DOI: regex-based detection in text
  - Year: first occurrence of 19xx or 20xx
  - Journal: heuristics from text + filename/parent directory
  - Source family: derived from journal match against allowed lists
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


DOI_PATTERN = re.compile(r"10\.\d{4,}/[-._;()/:a-zA-Z0-9]+")
YEAR_PATTERN = re.compile(r"(19|20)\d{2}")
JOURNAL_INDICATORS = [
    "nature", "science", "cell", "methods", "protocols", "biotechnology",
    "medicine", "immunology", "chemical biology", "reports", "advances",
    "signaling", "robotics", "molecular", "systems", "current biology",
    "trends in", "npj", "scientific reports", "star protocols",
]


def extract_doi(text: str) -> str:
    """Extract DOI from text. Returns first match or empty string."""
    m = DOI_PATTERN.search(text)
    return m.group(0) if m else ""


def extract_year(text: str, file_stem: str = "") -> Optional[int]:
    """Extract publication year from text or filename.

    Returns first 19xx/20xx match, or None.
    """
    for candidate in (file_stem, text[:2000]):
        for m in YEAR_PATTERN.finditer(candidate):
            val = int(m.group(0))
            if 1900 <= val <= 2099:
                return val
    return None


def extract_title(text: str, file_stem: str = "", max_lines: int = 5) -> str:
    """Extract paper title from text beginning.

    Takes first non-empty, non-header line as title candidate.
    Returns empty string if nothing reasonable found.
    """
    lines = text.split("\n")
    # Skip blank lines, PDF metadata headers
    for line in lines[:max_lines]:
        line = line.strip()
        if not line:
            continue
        # Skip lines that look like PDF headers or metadata
        if line.startswith("%") or line.startswith("<<"):
            continue
        if len(line) < 10:
            continue
        # Skip if it looks like a DOI or URL
        if DOI_PATTERN.match(line) or "http" in line:
            continue
        return line[:300]
    # Fallback: use file stem
    if file_stem:
        return file_stem.replace("_", " ").replace("-", " ").strip()
    return ""


def extract_journal(text: str, parent_dir_name: str = "", file_name: str = "") -> str:
    """Extract journal name from text + file path hints.

    Returns the best guess or empty string.
    """
    # First: check parent directory name
    dir_lower = parent_dir_name.lower().replace("_", " ").replace("-", " ")
    for indicator in JOURNAL_INDICATORS:
        if indicator in dir_lower:
            return _capitalize_journal(dir_lower)

    # Second: scan first 3000 chars of text
    text_start = text[:3000].lower()
    lines = text_start.split("\n")
    for line in lines:
        line_clean = line.strip()
        for indicator in JOURNAL_INDICATORS:
            if indicator in line_clean:
                return _capitalize_journal(line_clean)

    # Third: check file name
    name_lower = file_name.lower().replace("_", " ").replace("-", " ")
    for indicator in JOURNAL_INDICATORS:
        if indicator in name_lower:
            return _capitalize_journal(name_lower)

    return ""


def _capitalize_journal(name: str) -> str:
    """Simple journal name capitalization."""
    # Remove common prefixes
    name = re.sub(r"^[^a-z]+", "", name)
    words = name.split()
    # Simple title case
    return " ".join(w.capitalize() for w in words if w)


def detect_source_family(journal: str) -> Tuple[str, str]:
    """Detect source_family and source_journal_group from journal name.

    Returns (source_family, source_journal_group).
    Families: "Nature", "Science", "Cell"
    Groups: the specific journal name.
    """
    from researchos_learning_engine.general_methods_kb.taxonomy import (
        get_allowed_journals,
    )

    j_lower = journal.lower().strip()
    allowed = get_allowed_journals()

    for family, journals in allowed.items():
        for pattern in journals:
            if pattern in j_lower:
                # Determine the specific group
                if family == "Nature":
                    if j_lower.startswith("nature"):
                        if "methods" in j_lower:
                            return family, "Nature Methods"
                        if "protocols" in j_lower:
                            return family, "Nature Protocols"
                        if "biotechnology" in j_lower:
                            return family, "Nature Biotechnology"
                        if "medicine" in j_lower:
                            return family, "Nature Medicine"
                        if "immunology" in j_lower:
                            return family, "Nature Immunology"
                        if "chemical biology" in j_lower:
                            return family, "Nature Chemical Biology"
                        if "reviews" in j_lower:
                            return family, "Nature Reviews"
                        if j_lower == "nature" or j_lower.startswith("nature "):
                            return family, "Nature"
                    if "scientific reports" in j_lower:
                        return family, "Scientific Reports"
                    if j_lower.startswith("npj"):
                        return family, "npj"
                    return family, journal
                elif family == "Science":
                    if "advances" in j_lower:
                        return family, "Science Advances"
                    if "translational medicine" in j_lower:
                        return family, "Science Translational Medicine"
                    if "immunology" in j_lower:
                        return family, "Science Immunology"
                    if "robotics" in j_lower:
                        return family, "Science Robotics"
                    if "signaling" in j_lower:
                        return family, "Science Signaling"
                    if j_lower == "science":
                        return family, "Science"
                    return family, journal
                elif family == "Cell":
                    if j_lower.startswith("cell"):
                        if "reports" in j_lower and "medicine" in j_lower:
                            return family, "Cell Reports Medicine"
                        if "reports" in j_lower and "methods" in j_lower:
                            return family, "Cell Reports Methods"
                        if "reports" in j_lower:
                            return family, "Cell Reports"
                        if "systems" in j_lower:
                            return family, "Cell Systems"
                        if "molecular" in j_lower:
                            return family, "Molecular Cell"
                        if j_lower == "cell" or j_lower.startswith("cell "):
                            # Could be "Cell" itself
                            return family, "Cell"
                    if "star protocols" in j_lower:
                        return family, "STAR Protocols"
                    return family, journal

    return ("", "")

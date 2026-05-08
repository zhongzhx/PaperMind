"""Text cleaning and normalization utilities."""

from __future__ import annotations

import re


def normalize_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters into single spaces."""
    return re.sub(r"\s+", " ", text).strip()


def truncate(text: str, max_chars: int = 10000) -> str:
    """Truncate text to max_chars, preserving whole words at boundary."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "..."

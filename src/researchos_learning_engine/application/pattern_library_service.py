"""Research Pattern Library service.

Manages the research pattern library — stores, queries, and retrieves
patterns extracted from high-quality papers.
"""

from __future__ import annotations

from researchos_learning_engine.domain.schemas import ResearchPattern


class PatternLibraryService:
    """Service for managing the research pattern library."""

    def __init__(self) -> None:
        self._patterns: dict[str, ResearchPattern] = {}

    def add_pattern(self, pattern: ResearchPattern) -> None:
        """Add or update a pattern in the library."""
        self._patterns[pattern.pattern_id] = pattern

    def add_patterns(self, patterns: list[ResearchPattern]) -> None:
        """Add multiple patterns at once."""
        for p in patterns:
            self.add_pattern(p)

    def get_pattern(self, pattern_id: str) -> ResearchPattern | None:
        """Retrieve a pattern by ID."""
        return self._patterns.get(pattern_id)

    def get_patterns_by_project(self, project_id: str) -> list[ResearchPattern]:
        """Get all patterns for a given project."""
        return [p for p in self._patterns.values() if p.project_id == project_id]

    def get_patterns_by_paper(self, paper_id: str) -> list[ResearchPattern]:
        """Get all patterns extracted from a given paper."""
        return [p for p in self._patterns.values() if p.paper_id == paper_id]

    def get_all_patterns(self) -> list[ResearchPattern]:
        """Get all stored patterns."""
        return list(self._patterns.values())

    def clear(self) -> None:
        """Clear all patterns (useful for testing)."""
        self._patterns.clear()

"""Writing pattern extractor.

Uses LLM to extract narrative and writing patterns from the
introduction and discussion sections of a paper.
"""

from __future__ import annotations

from typing import List

from researchos_learning_engine.paper_learning.schemas import (
    HighImpactPaperRecord,
    PaperSection,
    WritingPattern,
)
from researchos_learning_engine.paper_learning.pattern_extractor import BasePatternExtractor

_WRITING_SYSTEM_PROMPT = """You are a writing pattern extraction system for scientific papers.
Analyze the given paper and extract writing and narrative patterns as JSON:

- writing_patterns: list of patterns, each containing:
  - introduction_logic: structure of the introduction (e.g. "funnel: broad → gap → hypothesis")
  - result_narrative: how results are presented (e.g. "figure-by-figure with transition sentences")
  - discussion_logic: structure of the discussion (e.g. "reverse funnel: findings → compare → mechanism → limits")
  - novelty_framing: how novelty is emphasised
  - limitation_framing: how limitations are presented
  - application_framing: how practical applications are proposed
  - reusable_sentences_or_templates: list of reusable sentence structures or templates

Output ONLY valid JSON. No additional text."""

_DEFAULT = {"writing_patterns": []}


class WritingPatternExtractor(BasePatternExtractor):
    """Extract narrative and writing patterns from paper sections."""

    def extract(
        self,
        sections: List[PaperSection],
        paper: HighImpactPaperRecord,
    ) -> List[WritingPattern]:
        """Run LLM-based extraction and return a list of WritingPattern."""
        intro_text = _find_section_text(sections, "introduction")
        discussion_text = _find_section_text(sections, "discussion")
        conclusion_text = _find_section_text(sections, "conclusion")

        parts = [f"Paper: {paper.title}"]
        if intro_text:
            parts.append(f"Introduction:\n{intro_text[:4000]}")
        if discussion_text:
            parts.append(f"Discussion:\n{discussion_text[:4000]}")
        if conclusion_text:
            parts.append(f"Conclusion:\n{conclusion_text[:2000]}")

        result = self._call_llm(
            system_prompt=_WRITING_SYSTEM_PROMPT,
            user_message="\n\n".join(parts),
            default=_DEFAULT,
        )

        patterns = []
        for wp in result.get("writing_patterns", []):
            patterns.append(WritingPattern(
                paper_id=paper.paper_id,
                introduction_logic=wp.get("introduction_logic", ""),
                result_narrative=wp.get("result_narrative", ""),
                discussion_logic=wp.get("discussion_logic", ""),
                novelty_framing=wp.get("novelty_framing", ""),
                limitation_framing=wp.get("limitation_framing", ""),
                application_framing=wp.get("application_framing", ""),
                reusable_sentences_or_templates=wp.get("reusable_sentences_or_templates", []),
            ))
        return patterns


def _find_section_text(sections: List[PaperSection], section_type: str) -> str:
    for s in sections:
        if s.section_type == section_type:
            return s.text
    return ""

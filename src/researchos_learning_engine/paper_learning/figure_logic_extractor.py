"""Figure logic pattern extractor.

Uses LLM to extract the logic, role, and key message of each figure
in a paper from results text and figure captions.
"""

from __future__ import annotations

from typing import List

from researchos_learning_engine.paper_learning.schemas import (
    FigureLogicPattern,
    HighImpactPaperRecord,
    PaperSection,
)
from researchos_learning_engine.paper_learning.pattern_extractor import BasePatternExtractor

_FIGURE_SYSTEM_PROMPT = """You are a figure logic extraction system for scientific papers.
Analyze the given paper and extract the logic of each figure as JSON:

- figure_logics: list of figures, each containing:
  - figure_id: the figure number (e.g. "Figure 1", "Figure 2A")
  - figure_role: what this figure demonstrates (e.g. "phenotypic validation", "mechanism probing")
  - data_type: type of data shown (e.g. "bar_chart", "western_blot", "microscopy", "flow_cytometry")
  - key_message: the key finding presented in this figure
  - supports_which_claim: which claim or conclusion this figure supports
  - reusable_figure_idea: the experimental/visual logic that could be reused

Output ONLY valid JSON. No additional text."""

_DEFAULT = {"figure_logics": []}


class FigureLogicExtractor(BasePatternExtractor):
    """Extract structured figure logic from paper text."""

    def extract(
        self,
        sections: List[PaperSection],
        paper: HighImpactPaperRecord,
    ) -> List[FigureLogicPattern]:
        """Run LLM-based extraction and return a list of FigureLogicPattern."""
        results_text = _find_section_text(sections, "results")
        fig_text = _find_section_text(sections, "figure_caption")

        parts = [f"Paper: {paper.title}"]
        if results_text:
            parts.append(f"Results:\n{results_text[:5000]}")
        if fig_text:
            parts.append(f"Figure Captions:\n{fig_text[:3000]}")

        result = self._call_llm(
            system_prompt=_FIGURE_SYSTEM_PROMPT,
            user_message="\n\n".join(parts),
            default=_DEFAULT,
        )

        figures = []
        for fig in result.get("figure_logics", []):
            figures.append(FigureLogicPattern(
                paper_id=paper.paper_id,
                figure_id=fig.get("figure_id", ""),
                figure_role=fig.get("figure_role", ""),
                data_type=fig.get("data_type", ""),
                key_message=fig.get("key_message", ""),
                supports_which_claim=fig.get("supports_which_claim", ""),
                reusable_figure_idea=fig.get("reusable_figure_idea", ""),
            ))
        return figures


def _find_section_text(sections: List[PaperSection], section_type: str) -> str:
    for s in sections:
        if s.section_type == section_type:
            return s.text
    return ""

"""Experiment design pattern extractor.

Uses LLM to extract structured experimental design information
from the methods and results sections of a paper.
"""

from __future__ import annotations

from typing import List

from researchos_learning_engine.paper_learning.schemas import (
    ExperimentDesignPattern,
    HighImpactPaperRecord,
    PaperSection,
)
from researchos_learning_engine.paper_learning.pattern_extractor import BasePatternExtractor

_EXPERIMENT_SYSTEM_PROMPT = """You are an experiment design extraction system.
Analyze the given paper's methods and results sections. Extract structured experiment design as JSON:

- research_question: the main research question
- hypothesis: the tested hypothesis
- experimental_models: list of model systems (cell lines, animals, samples)
- groups: list of experimental groups
- interventions: list of treatments or interventions applied
- doses_or_concentrations: list of doses/concentrations used
- timepoints: list of timepoints measured
- assays: list of experimental assays performed
- controls: list of controls used
- statistical_methods: list of statistical tests applied
- validation_chain: list of validation steps performed
- strengths: list of experimental design strengths
- limitations: list of experimental design weaknesses

Output ONLY valid JSON. No additional text."""

_DEFAULT = ExperimentDesignPattern()


class ExperimentDesignExtractor(BasePatternExtractor):
    """Extract structured experiment design from paper sections."""

    def extract(
        self,
        sections: List[PaperSection],
        paper: HighImpactPaperRecord,
    ) -> ExperimentDesignPattern:
        """Run LLM-based extraction and return an ExperimentDesignPattern."""
        methods_text = _find_section_text(sections, "methods")
        results_text = _find_section_text(sections, "results")

        user_parts = [f"Paper: {paper.title}"]
        if paper.authors:
            user_parts.append(f"Authors: {', '.join(paper.authors)}")
        if methods_text:
            user_parts.append(f"\nMethods:\n{methods_text[:5000]}")
        if results_text:
            user_parts.append(f"\nResults:\n{results_text[:5000]}")

        result = self._call_llm(
            system_prompt=_EXPERIMENT_SYSTEM_PROMPT,
            user_message="\n\n".join(user_parts),
            default=_DEFAULT.to_dict(),
        )

        return ExperimentDesignPattern(
            paper_id=paper.paper_id,
            research_question=result.get("research_question", ""),
            hypothesis=result.get("hypothesis", ""),
            experimental_models=result.get("experimental_models", []),
            groups=result.get("groups", []),
            interventions=result.get("interventions", []),
            doses_or_concentrations=result.get("doses_or_concentrations", []),
            timepoints=result.get("timepoints", []),
            assays=result.get("assays", []),
            controls=result.get("controls", []),
            statistical_methods=result.get("statistical_methods", []),
            validation_chain=result.get("validation_chain", []),
            strengths=result.get("strengths", []),
            limitations=result.get("limitations", []),
        )


def _find_section_text(sections: List[PaperSection], section_type: str) -> str:
    for s in sections:
        if s.section_type == section_type:
            return s.text
    return ""

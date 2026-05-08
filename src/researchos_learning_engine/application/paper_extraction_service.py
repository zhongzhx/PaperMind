"""Paper structure extraction service.

Extracts structured ResearchPattern objects from PaperRecords
using an LLM adapter. The LLM is prompted with a structured schema
to produce consistent results.
"""

from __future__ import annotations

import json
from typing import Any

from researchos_learning_engine.adapters.llm.base import LLMAdapter
from researchos_learning_engine.domain.constants import EvidenceLevel, StudyType
from researchos_learning_engine.domain.schemas import PaperRecord, ResearchPattern
from researchos_learning_engine.utils.ids import new_pattern_id
from researchos_learning_engine.utils.time import now_iso


EXTRACTION_SYSTEM_PROMPT = """You are a research pattern extraction system.
Analyze the given paper and extract structured research patterns.

Extract the following fields as JSON:
- research_question: the core research question
- study_type: one of: in_vivo, in_vitro, in_silico, clinical_trial, review, meta_analysis, computational, observational, other
- core_logic: the high-level experimental logic flow
- experimental_models: list of model systems used
- assays: list of assays and detection methods
- mechanisms: list of molecular/cellular mechanisms
- omics_methods: list of omics approaches
- statistical_methods: list of statistical methods
- figure_logic: how figures/data presentations are organized
- writing_pattern: narrative/writing structure
- innovations: list of novel contributions
- limitations: list of limitations
- reusable_insights: list of insights reusable in other projects

Output ONLY valid JSON. No additional text."""


class PaperExtractionService:
    """Extract structured ResearchPattern from PaperRecords via LLM."""

    def __init__(self, llm: LLMAdapter) -> None:
        self._llm = llm

    def extract(
        self,
        paper: PaperRecord,
        project_id: str = "default",
    ) -> ResearchPattern:
        """Extract a ResearchPattern from a single paper record."""
        text_for_llm = paper.full_text or " ".join(paper.chunks) or paper.title or ""

        if not text_for_llm:
            return ResearchPattern(
                pattern_id=new_pattern_id(),
                paper_id=paper.paper_id,
                project_id=project_id,
                research_question="",
                core_logic="No text available for extraction",
            )

        user_message = (
            f"Paper: {paper.title}\n"
            f"Authors: {', '.join(paper.authors)}\n"
            f"Year: {paper.year}\n"
            f"Journal: {paper.journal}\n\n"
            f"Text (truncated to 15000 chars):\n{text_for_llm[:15000]}"
        )

        result = self._llm.generate_json(
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            user_message=user_message,
            temperature=0.3,
            max_tokens=4096,
        )

        return self._build_pattern(paper, project_id, result)

    def _build_pattern(
        self,
        paper: PaperRecord,
        project_id: str,
        llm_result: dict[str, Any],
    ) -> ResearchPattern:
        """Build a ResearchPattern from LLM result dict."""
        study_type_str = llm_result.get("study_type", "other")
        try:
            study_type = StudyType(study_type_str)
        except ValueError:
            study_type = StudyType.OTHER

        return ResearchPattern(
            pattern_id=new_pattern_id(),
            paper_id=paper.paper_id,
            project_id=project_id,
            research_question=llm_result.get("research_question", ""),
            study_type=study_type,
            core_logic=llm_result.get("core_logic", ""),
            experimental_models=llm_result.get("experimental_models", []),
            assays=llm_result.get("assays", []),
            mechanisms=llm_result.get("mechanisms", []),
            omics_methods=llm_result.get("omics_methods", []),
            statistical_methods=llm_result.get("statistical_methods", []),
            figure_logic=llm_result.get("figure_logic", ""),
            writing_pattern=llm_result.get("writing_pattern", ""),
            innovations=llm_result.get("innovations", []),
            limitations=llm_result.get("limitations", []),
            reusable_insights=llm_result.get("reusable_insights", []),
            evidence_level=EvidenceLevel.L2,
            confidence=min(1.0, max(0.0, float(llm_result.get("confidence", 0.5)))),
            extracted_at=now_iso(),
        )

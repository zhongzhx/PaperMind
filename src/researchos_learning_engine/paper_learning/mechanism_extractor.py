"""Mechanism pattern extractor.

Uses LLM to extract molecular/cellular mechanism pathways
from the results and discussion sections of a paper.
"""

from __future__ import annotations

from typing import List

from researchos_learning_engine.paper_learning.schemas import (
    HighImpactPaperRecord,
    MechanismPattern,
    PaperSection,
)
from researchos_learning_engine.paper_learning.pattern_extractor import BasePatternExtractor

_MECHANISM_SYSTEM_PROMPT = """You are a mechanism extraction system for scientific papers.
Analyze the given paper and extract molecular/cellular mechanism information as JSON:

- pathway: the name of the signaling pathway or mechanism
- targets: list of key molecules, proteins, genes targeted
- upstream_factors: list of upstream signals or activators
- downstream_readouts: list of downstream effects or readouts measured
- evidence_types: list of evidence types provided (e.g., Western blot, qPCR, knockout)
- claim_strength: strength of the mechanistic claim (strong / moderate / weak)
- limitations: list of mechanistic interpretation limitations

Output ONLY valid JSON. No additional text."""

_DEFAULT = MechanismPattern()


class MechanismExtractor(BasePatternExtractor):
    """Extract structured mechanism pathway information."""

    def extract(
        self,
        sections: List[PaperSection],
        paper: HighImpactPaperRecord,
    ) -> MechanismPattern:
        """Run LLM-based extraction and return a MechanismPattern."""
        # Gather text from multiple sections
        parts = [f"Paper: {paper.title}"]
        for stype in ("results", "discussion", "conclusion", "introduction"):
            txt = _find_section_text(sections, stype)
            if txt:
                parts.append(f"{stype.capitalize()}:\n{txt[:4000]}")

        result = self._call_llm(
            system_prompt=_MECHANISM_SYSTEM_PROMPT,
            user_message="\n\n".join(parts),
            default=_DEFAULT.to_dict(),
        )

        return MechanismPattern(
            paper_id=paper.paper_id,
            pathway=result.get("pathway", ""),
            targets=result.get("targets", []),
            upstream_factors=result.get("upstream_factors", []),
            downstream_readouts=result.get("downstream_readouts", []),
            evidence_types=result.get("evidence_types", []),
            claim_strength=result.get("claim_strength", ""),
            limitations=result.get("limitations", []),
        )


def _find_section_text(sections: List[PaperSection], section_type: str) -> str:
    for s in sections:
        if s.section_type == section_type:
            return s.text
    return ""

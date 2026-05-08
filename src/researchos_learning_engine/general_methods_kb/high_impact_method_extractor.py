"""Orchestrator for high-impact method extraction from papers.

Coordinates deep learning (recent vs older) and evidence extraction,
providing a single entry point for the KB builder pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from researchos_learning_engine.general_methods_kb.evidence_normalizer import (
    EvidenceNormalizer,
)
from researchos_learning_engine.general_methods_kb.recent_paper_deep_learner import (
    RecentPaperDeepLearner,
)
from researchos_learning_engine.general_methods_kb.schemas import (
    DeepLearningFields,
    EvidenceItem,
)

_RECENT_YEAR_BOUNDARY = 2021


class HighImpactMethodExtractor:
    """Orchestrates deep learning and evidence extraction for a single paper.

    Typical usage:
        extractor = HighImpactMethodExtractor(llm)
        deep_fields, evidence, warnings = extractor.extract(text, metadata, year)
    """

    def __init__(self, llm: Any) -> None:
        self._deep_learner = RecentPaperDeepLearner(llm)
        self._evidence_normalizer = EvidenceNormalizer(llm)
        self._llm = llm

    def extract(
        self,
        text: str,
        metadata: Dict[str, Any],
        year: Optional[int],
        method_category: str = "",
    ) -> Tuple[Optional[DeepLearningFields], List[EvidenceItem], List[str]]:
        """Extract deep learning fields and evidence items from paper text.

        Args:
            text: Full paper text content.
            metadata: Dict with title, journal, doi, etc.
            year: Publication year (None if unknown).
            method_category: Classified method category.

        Returns:
            (deep_learning_fields, evidence_items, warnings).
            deep_learning_fields is None on catastrophic failure.
        """
        warnings: List[str] = []

        try:
            is_recent = year is not None and year >= _RECENT_YEAR_BOUNDARY

            # 1. Deep learning
            if is_recent:
                deep_fields = self._deep_learner.learn(text, metadata)
            else:
                deep_fields = self._deep_learner.learn_light(text, metadata)

            # Check for missing fields and add warnings
            self._check_missing_fields(deep_fields, is_recent, warnings)

            # 2. Evidence extraction
            metadata_for_evidence = {
                "title": metadata.get("title", ""),
                "journal": metadata.get("journal", ""),
                "doi": metadata.get("doi", ""),
            }
            evidence_items = self._evidence_normalizer.extract(
                text, metadata_for_evidence, is_recent=is_recent,
            )

            if not evidence_items:
                warnings.append("No evidence items extracted")

            return deep_fields, evidence_items, warnings

        except Exception as exc:
            warnings.append(f"Extraction failed: {type(exc).__name__}: {exc}")
            return None, [], warnings

    def _check_missing_fields(
        self,
        deep_fields: DeepLearningFields,
        is_recent: bool,
        warnings: List[str],
    ) -> None:
        """Check for missing fields and add warnings."""
        core_str_fields = [
            "high_impact_value_cn", "what_researchos_should_learn_cn",
            "applicable_scenarios_cn",
        ]
        for field_name in core_str_fields:
            if getattr(deep_fields, field_name, "") == "not_reported":
                warnings.append(f"Field '{field_name}' could not be determined from text")

        list_fields = [
            "core_protocol_steps", "quality_control_points",
            "reproducibility_points", "operation_reference_points",
        ]
        for field_name in list_fields:
            if not getattr(deep_fields, field_name, []):
                warnings.append(f"No entries found for '{field_name}'")

    def extract_with_defaults(
        self,
        text: str,
        metadata: Dict[str, Any],
        year: Optional[int],
        method_category: str = "",
    ) -> Tuple[DeepLearningFields, List[EvidenceItem], List[str]]:
        """Like extract() but returns empty DeepLearningFields on failure.

        Guarantees the first return value is never None, so callers
        don't need to handle None in the common case.
        """
        deep_fields, evidence, warnings = self.extract(
            text, metadata, year, method_category,
        )
        if deep_fields is None:
            deep_fields = DeepLearningFields()
        return deep_fields, evidence, warnings

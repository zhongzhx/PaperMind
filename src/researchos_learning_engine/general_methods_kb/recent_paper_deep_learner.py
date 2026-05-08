"""Deep learning extractor for recent (2021-2026) high-impact papers.

For recent papers: extracts all 19 DeepLearningFields via LLM.
For older papers: lighter extraction with fewer fields.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from researchos_learning_engine.general_methods_kb.schemas import DeepLearningFields

_NOT_REPORTED = "not_reported"

# Fields that are List[str] — will get [] instead of _NOT_REPORTED
_LIST_FIELDS = {
    "core_protocol_steps",
    "critical_parameters",
    "quality_control_points",
    "reproducibility_points",
    "common_pitfalls",
    "troubleshooting_hints",
    "data_outputs",
    "figure_logic_patterns",
    "reporting_checklist",
    "reusable_research_patterns",
    "operation_reference_points",
    "researchos_trigger_questions",
    "related_methods",
    "limitations",
}


class RecentPaperDeepLearner:
    """Extracts deep learning fields from paper text via LLM.

    For recent papers (>= 2021): full extraction with all 19 fields.
    For older papers: lightweight extraction with 5 core fields.
    """

    def __init__(self, llm: Any) -> None:
        self._llm = llm

    def learn(
        self,
        text: str,
        metadata: Dict[str, Any],
    ) -> DeepLearningFields:
        """Full deep learning for 2021-2026 papers.

        Uses LLM with 'deep method extraction' prompt to populate
        all 19 fields. Falls back to _NOT_REPORTED for missing fields.
        """
        system_prompt = (
            "You are a deep method extraction assistant for high-impact biomedical papers. "
            "Extract structured methodological knowledge as JSON. "
            "If a field cannot be determined from the text, use 'not_reported' for strings "
            "or an empty list for list fields. Do NOT fabricate information."
        )

        user_message = (
            f"Paper metadata:\n"
            f"Title: {metadata.get('title', '')}\n"
            f"Journal: {metadata.get('journal', '')}\n"
            f"Year: {metadata.get('year', '')}\n"
            f"DOI: {metadata.get('doi', '')}\n\n"
            f"Paper text:\n{text[:8000]}"
        )

        try:
            result = self._llm.generate_json(
                system_prompt="deep method extraction — " + system_prompt,
                user_message=user_message,
            )
            return self._validate_deep(result)
        except Exception:
            return self._default_empty()

    def learn_light(
        self,
        text: str,
        metadata: Dict[str, Any],
    ) -> DeepLearningFields:
        """Lightweight extraction for pre-2021 papers.

        Populates only the 5 most important fields:
          high_impact_value_cn, what_researchos_should_learn_cn,
          applicable_scenarios_cn, core_protocol_steps, limitations.
        """
        system_prompt = (
            "You are a lightweight method extractor for biomedical papers. "
            "Extract the most important methodological knowledge as JSON. "
            "Focus on: high_impact_value_cn, what_researchos_should_learn_cn, "
            "applicable_scenarios_cn, core_protocol_steps, limitations."
        )

        user_message = (
            f"Paper metadata:\n"
            f"Title: {metadata.get('title', '')}\n"
            f"Journal: {metadata.get('journal', '')}\n"
            f"Year: {metadata.get('year', '')}\n\n"
            f"Paper text:\n{text[:4000]}"
        )

        try:
            result = self._llm.generate_json(
                system_prompt="standard method extraction — " + system_prompt,
                user_message=user_message,
            )
            return self._validate_deep(result, light=True)
        except Exception:
            return self._default_empty(light=True)

    def _validate_deep(
        self, result: Dict[str, Any], light: bool = False,
    ) -> DeepLearningFields:
        """Validate LLM output and fill missing fields with defaults."""
        kwargs: Dict[str, Any] = {}
        for field_name in DeepLearningFields.__dataclass_fields__:  # type: ignore[attr-defined]
            raw = result.get(field_name)
            if raw is None or (isinstance(raw, str) and not raw.strip()):
                kwargs[field_name] = self._field_default(field_name, light)
            else:
                kwargs[field_name] = raw
        return DeepLearningFields(**kwargs)

    def _field_default(self, field_name: str, light: bool) -> Any:
        """Return appropriate default for a missing field."""
        if light and field_name not in {
            "high_impact_value_cn", "what_researchos_should_learn_cn",
            "applicable_scenarios_cn", "core_protocol_steps", "limitations",
        }:
            return _NOT_REPORTED if field_name not in _LIST_FIELDS else []
        if field_name in _LIST_FIELDS:
            return []
        return _NOT_REPORTED

    def _default_empty(self, light: bool = False) -> DeepLearningFields:
        """Return all fields as 'not_reported' or empty lists."""
        kwargs: Dict[str, Any] = {}
        for field_name in DeepLearningFields.__dataclass_fields__:  # type: ignore[attr-defined]
            kwargs[field_name] = self._field_default(field_name, light)
        return DeepLearningFields(**kwargs)

"""Base class for LLM-based pattern extractors."""

from __future__ import annotations

from typing import Any, Dict

from researchos_learning_engine.adapters.llm.base import LLMAdapter


class BasePatternExtractor:
    """Shared infrastructure for extractors that call the LLM.

    Provides a _call_llm helper with try/except fallback so that
    individual extractors don't need to repeat error handling.
    """

    def __init__(self, llm: LLMAdapter) -> None:
        self._llm = llm

    def _call_llm(
        self,
        system_prompt: str,
        user_message: str,
        default: Dict[str, Any],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Call LLM in JSON mode, returning the parsed dict or *default* on error."""
        try:
            return self._llm.generate_json(
                system_prompt=system_prompt,
                user_message=str(user_message),
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception:
            return dict(default)

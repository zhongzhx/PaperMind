"""Stable Python API for the Learning Engine.

This is the primary integration point for the main ResearchOS backend.
All external code should call run_sleep_cycle() — never access
application services directly.
"""

from __future__ import annotations

import os

from researchos_learning_engine.adapters.llm.mock_llm import MockLLMAdapter
from researchos_learning_engine.application.consolidation_service import (
    ConsolidationService,
)
from researchos_learning_engine.domain.schemas import (
    ConsolidationInput,
    ConsolidationResult,
)


def _load_env() -> None:
    """Minimal .env file loader (no external dependencies)."""
    for path in (".env", os.path.expanduser("~/.env")):
        if not os.path.isfile(path):
            continue
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, val = line.partition("=")
                    key, val = key.strip(), val.strip().strip("\"'")
                    if key and not os.environ.get(key):
                        os.environ[key] = val
        except OSError:
            pass


_load_env()


def _create_llm() -> MockLLMAdapter:
    """Create the appropriate LLM adapter based on environment configuration.

    If LLM_API_KEY is set, creates an OpenAI-compatible adapter.
    Otherwise, falls back to MockLLM for testing/development.
    """
    api_key = os.getenv("LLM_API_KEY", "")
    if api_key:
        try:
            from researchos_learning_engine.adapters.llm.openai_like import (
                OpenAICompatibleAdapter,
            )

            return OpenAICompatibleAdapter(api_key=api_key)  # type: ignore[return-value]
        except Exception:
            pass

    return MockLLMAdapter()


def run_sleep_cycle(input_data: ConsolidationInput) -> ConsolidationResult:
    """Execute the full sleep-cycle consolidation process.

    This is the main entry point for the Learning Engine. It takes a
    ConsolidationInput and returns a ConsolidationResult with all
    scored memories, new patterns, contradictions, edges, recommendations,
    and an updated project summary.

    Args:
        input_data: Complete project state for consolidation.

    Returns:
        ConsolidationResult with all processed outputs.
    """
    llm = _create_llm()
    service = ConsolidationService(llm=llm)
    return service.run(input_data)

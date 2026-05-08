"""Literature recommendation service.

Suggests next literature queries and user actions based on the
current state of project knowledge, gaps, and weaknesses.
"""

from __future__ import annotations

from researchos_learning_engine.adapters.llm.base import LLMAdapter
from researchos_learning_engine.domain.schemas import ConsolidationInput


RECOMMENDATION_SYSTEM_PROMPT = """You are a research literature recommendation system.
Based on the current project state, paper records, and known gaps,
recommend searches and actions that would strengthen the project.

Output JSON with:
- queries: list of suggested literature search queries (3-5 queries)
- reasoning: explanation of why these queries are relevant
- user_actions: list of suggested user actions (2-3 actions)"""


class RecommendationService:
    """Generate literature recommendations and suggested actions."""

    def __init__(self, llm: LLMAdapter) -> None:
        self._llm = llm

    def generate_recommendations(
        self, input_data: ConsolidationInput
    ) -> tuple[list[str], list[str]]:
        """Generate literature queries and user action recommendations."""
        paper_titles = [p.title for p in input_data.paper_records if p.title]
        memory_contents = [m.content[:200] for m in input_data.memory_records]

        user_message = (
            f"Project: {input_data.project_title}\n"
            f"Description: {input_data.project_description[:500]}\n"
            f"Current summary: {input_data.current_project_summary[:500]}\n\n"
            f"Papers ({len(paper_titles)}):\n" + "\n".join(f"- {t}" for t in paper_titles[:10]) + "\n\n"
            f"Key memories ({len(memory_contents)}):\n" + "\n".join(f"- {m[:100]}" for m in memory_contents[:10])
        )

        result = self._llm.generate_json(
            system_prompt=RECOMMENDATION_SYSTEM_PROMPT,
            user_message=user_message,
            temperature=0.4,
            max_tokens=2048,
        )

        queries = result.get("queries", [])
        actions = result.get("user_actions", [])

        # Ensure string lists
        queries = [str(q) for q in queries] if queries else []
        actions = [str(a) for a in actions] if actions else []

        return queries, actions

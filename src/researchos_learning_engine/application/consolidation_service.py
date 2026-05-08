"""Consolidation service — the main orchestrator of the sleep-cycle process.

Ties together memory scoring, pattern extraction, contradiction detection,
evidence graph building, summary consolidation, and recommendation generation
into a single consolidation pipeline.
"""

from __future__ import annotations

from typing import Any

from researchos_learning_engine.adapters.llm.base import LLMAdapter
from researchos_learning_engine.application.contradiction_service import (
    ContradictionService,
)
from researchos_learning_engine.application.evidence_graph_service import (
    EvidenceGraphService,
)
from researchos_learning_engine.application.memory_scoring_service import (
    MemoryScoringService,
)
from researchos_learning_engine.application.paper_extraction_service import (
    PaperExtractionService,
)
from researchos_learning_engine.application.pattern_library_service import (
    PatternLibraryService,
)
from researchos_learning_engine.application.recommendation_service import (
    RecommendationService,
)
from researchos_learning_engine.domain.schemas import (
    ConsolidationInput,
    ConsolidationResult,
    MemoryRecord,
    ResearchPattern,
)


SUMMARY_SYSTEM_PROMPT = """You are a project summary consolidation system.
Given the current project summary, active memories, and research patterns,
write an updated, consolidated project summary that reflects all key findings.

The summary should be 2-4 paragraphs, covering:
1. Core research question and objectives
2. Key findings and evidence
3. Methodological approaches
4. Current status and next steps

Output ONLY the summary text, no additional formatting."""


class ConsolidationService:
    """Main orchestrator of the sleep-cycle consolidation process.

    Runs the full pipeline: score memories, extract patterns, detect
    contradictions, build evidence graph, generate recommendations,
    consolidate summary.
    """

    def __init__(
        self,
        llm: LLMAdapter,
    ) -> None:
        self._llm = llm
        self.memory_scoring = MemoryScoringService()
        self.paper_extraction = PaperExtractionService(llm)
        self.pattern_library = PatternLibraryService()
        self.contradiction = ContradictionService(llm)
        self.evidence_graph = EvidenceGraphService()
        self.recommendation = RecommendationService(llm)

    def run(self, input_data: ConsolidationInput) -> ConsolidationResult:
        """Execute the full consolidation pipeline.

        Steps:
        1. Score all memory records
        2. Extract research patterns from papers
        3. Detect contradictions
        4. Resolve contradictions (mark superseded)
        5. Build evidence graph edges
        6. Generate literature recommendations
        7. Consolidate project summary
        8. Produce final ConsolidationResult
        """
        log: list[str] = []
        project_id = input_data.project_id

        log.append(f"[Step 1] Scoring {len(input_data.memory_records)} memory records")

        # Step 1: Score all memories
        original_memories = input_data.memory_records
        scored_memories = self.memory_scoring.score_all(input_data.memory_records)

        promoted, archived, superseded = self.memory_scoring.categorize_by_status_change(
            original_memories, scored_memories
        )
        log.append(
            f"  → {len(promoted)} promoted, "
            f"{len(archived)} archived, "
            f"{len(superseded)} superseded"
        )

        # Step 2: Extract research patterns
        log.append(f"[Step 2] Extracting patterns from {len(input_data.paper_records)} papers")
        new_patterns: list[ResearchPattern] = []
        for paper in input_data.paper_records:
            try:
                pattern = self.paper_extraction.extract(paper, project_id)
                self.pattern_library.add_pattern(pattern)
                new_patterns.append(pattern)
            except Exception as e:
                log.append(f"  ⚠ Failed to extract pattern for '{paper.title}': {e}")
        log.append(f"  → {len(new_patterns)} patterns extracted")

        # Step 3: Detect contradictions
        log.append("[Step 3] Detecting contradictions")
        contradictions = self.contradiction.scan_project_memories(
            scored_memories, use_llm=True
        )
        log.append(f"  → {len(contradictions)} contradictions detected")

        # Step 4: Resolve contradictions
        if contradictions:
            log.append("[Step 4] Resolving contradictions")
            scored_memories = self.contradiction.resolve_contradictions(
                contradictions, scored_memories
            )
            # Re-categorize after resolution
            promoted2, archived2, superseded2 = self.memory_scoring.categorize_by_status_change(
                original_memories, scored_memories
            )
            superseded = superseded2
            log.append(f"  → {len(superseded)} memories superseded")

        # Step 5: Build evidence graph
        log.append("[Step 5] Building evidence graph")
        new_edges = self.evidence_graph.build_edges_from_patterns(
            new_patterns, project_id
        )
        log.append(f"  → {len(new_edges)} edges created")

        # Step 6: Generate recommendations
        log.append("[Step 6] Generating recommendations")
        try:
            queries, actions = self.recommendation.generate_recommendations(input_data)
        except Exception as e:
            queries = []
            actions = []
            log.append(f"  ⚠ Recommendation generation failed: {e}")
        log.append(f"  → {len(queries)} queries, {len(actions)} actions")

        # Step 7: Consolidate project summary
        log.append("[Step 7] Consolidating project summary")
        updated_summary = self._consolidate_summary(input_data, scored_memories, new_patterns, log)
        log.append("  → Summary consolidated")

        # Build result
        result = ConsolidationResult(
            project_id=project_id,
            promoted_memories=promoted,
            archived_memories=archived,
            superseded_memories=superseded,
            new_research_patterns=new_patterns,
            new_evidence_edges=new_edges,
            contradictions_detected=contradictions,
            updated_project_summary=updated_summary,
            recommended_literature_queries=queries,
            recommended_user_actions=actions,
            warnings=[],
            processing_log=log,
        )

        return result

    def _consolidate_summary(
        self,
        input_data: ConsolidationInput,
        scored_memories: list[MemoryRecord],
        new_patterns: list[ResearchPattern],
        log: list[str],
    ) -> str:
        """Generate an updated project summary using LLM or fallback."""
        active_memories = [
            m for m in scored_memories if m.health_score >= 0.6
        ]
        memory_summary = "\n".join(
            f"- [{m.evidence_level.value}] {m.content[:200]}"
            for m in active_memories[:15]
        )
        pattern_summary = "\n".join(
            f"- {p.research_question[:150]}"
            for p in new_patterns[:5]
        )

        try:
            user_message = (
                f"Current summary: {input_data.current_project_summary[:1000]}\n\n"
                f"Active memories:\n{memory_summary}\n\n"
                f"New research patterns:\n{pattern_summary}"
            )
            return self._llm.generate(
                system_prompt=SUMMARY_SYSTEM_PROMPT,
                user_message=user_message,
                temperature=0.4,
                max_tokens=2048,
            )
        except Exception as e:
            log.append(f"  ⚠ LLM summary failed, using fallback: {e}")
            return self._fallback_summary(input_data, scored_memories)

    def _fallback_summary(
        self,
        input_data: ConsolidationInput,
        scored_memories: list[MemoryRecord],
    ) -> str:
        """Generate a fallback summary without LLM."""
        active_count = sum(1 for m in scored_memories if m.health_score >= 0.75)
        normal_count = sum(
            1 for m in scored_memories if 0.45 <= m.health_score < 0.75
        )
        total = len(scored_memories)
        high_evidence = sum(
            1
            for m in scored_memories
            if m.evidence_level.value in ("L4", "L5")
        )

        return (
            f"Project: {input_data.project_title}\n\n"
            f"This project has {total} memory records "
            f"({active_count} active, {normal_count} normal, "
            f"{high_evidence} with L4/L5 evidence).\n"
            f"Papers reviewed: {len(input_data.paper_records)}.\n"
            f"The current project description indicates: "
            f"{input_data.project_description[:300]}"
        )

"""High-Impact Paper Learning Library — main orchestration service.

Converts raw paper text into structured, reusable scientific knowledge
including experiment design patterns, mechanism pathways, figure logic,
writing patterns, and actionable research insights.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from researchos_learning_engine.adapters.llm.base import LLMAdapter
from researchos_learning_engine.paper_learning.schemas import (
    ExperimentDesignPattern,
    FigureLogicPattern,
    HighImpactPaperRecord,
    MechanismPattern,
    PaperLearningResult,
    ReusableResearchInsight,
    WritingPattern,
)
from researchos_learning_engine.paper_learning.section_parser import parse_sections
from researchos_learning_engine.paper_learning.paper_quality_scoring import score_paper_quality
from researchos_learning_engine.paper_learning.experiment_design_extractor import ExperimentDesignExtractor
from researchos_learning_engine.paper_learning.mechanism_extractor import MechanismExtractor
from researchos_learning_engine.paper_learning.figure_logic_extractor import FigureLogicExtractor
from researchos_learning_engine.paper_learning.writing_pattern_extractor import WritingPatternExtractor
from researchos_learning_engine.paper_learning.project_relevance import score_project_relevance


class HighImpactPaperLearningService:
    """Orchestrate the full paper learning pipeline.

    Usage:
        service = HighImpactPaperLearningService(llm)
        result = service.learn(paper, project_id="proj_123", project_description="...")
    """

    def __init__(self, llm: LLMAdapter) -> None:
        self._llm = llm
        self._experiment_extractor = ExperimentDesignExtractor(llm)
        self._mechanism_extractor = MechanismExtractor(llm)
        self._figure_extractor = FigureLogicExtractor(llm)
        self._writing_extractor = WritingPatternExtractor(llm)

    def learn(
        self,
        paper: HighImpactPaperRecord,
        project_id: str = "default",
        project_description: str = "",
    ) -> PaperLearningResult:
        """Run the full paper learning pipeline.

        Steps:
          1. Parse full text into sections
          2. Score paper quality
          3. Extract experiment design patterns
          4. Extract mechanism pathways
          5. Extract figure logic patterns
          6. Extract writing patterns
          7. Score project relevance
          8. Generate reusable insights
        """
        log: List[str] = []
        warnings: List[str] = []

        # Step 1 — Parse sections
        log.append("[Step 1] Parsing paper sections")
        sections = parse_sections(paper.full_text, paper_id=paper.paper_id)
        log.append(f"  → {len(sections)} sections found")

        # Step 2 — Quality scoring
        log.append("[Step 2] Scoring paper quality")
        quality_score, quality_breakdown = score_paper_quality(paper, sections)
        log.append(f"  → Quality score: {quality_score:.3f}")

        # Step 3 — Experiment design extraction
        log.append("[Step 3] Extracting experiment design patterns")
        experiment_patterns: List[ExperimentDesignPattern] = []
        try:
            ed = self._experiment_extractor.extract(sections, paper)
            if ed.research_question or ed.experimental_models:
                experiment_patterns = [ed]
                log.append(f"  → Models: {ed.experimental_models[:3]}")
            else:
                log.append("  → No experiment design data extracted")
        except Exception as e:
            log.append(f"  ⚠ Experiment design extraction failed: {e}")
            warnings.append(f"Experiment design extraction failed: {e}")

        # Step 4 — Mechanism extraction
        log.append("[Step 4] Extracting mechanism pathways")
        mechanism_patterns: List[MechanismPattern] = []
        try:
            mp = self._mechanism_extractor.extract(sections, paper)
            if mp.pathway or mp.targets:
                mechanism_patterns = [mp]
                log.append(f"  → Pathway: {mp.pathway or 'unspecified'}")
            else:
                log.append("  → No mechanism data extracted")
        except Exception as e:
            log.append(f"  ⚠ Mechanism extraction failed: {e}")
            warnings.append(f"Mechanism extraction failed: {e}")

        # Step 5 — Figure logic extraction
        log.append("[Step 5] Extracting figure logic patterns")
        figure_patterns: List[FigureLogicPattern] = []
        try:
            figure_patterns = self._figure_extractor.extract(sections, paper)
            log.append(f"  → {len(figure_patterns)} figures extracted")
        except Exception as e:
            log.append(f"  ⚠ Figure logic extraction failed: {e}")
            warnings.append(f"Figure logic extraction failed: {e}")

        # Step 6 — Writing pattern extraction
        log.append("[Step 6] Extracting writing patterns")
        writing_patterns: List[WritingPattern] = []
        try:
            writing_patterns = self._writing_extractor.extract(sections, paper)
            log.append(f"  → {len(writing_patterns)} writing patterns extracted")
        except Exception as e:
            log.append(f"  ⚠ Writing pattern extraction failed: {e}")
            warnings.append(f"Writing pattern extraction failed: {e}")

        # Step 7 — Project relevance
        log.append("[Step 7] Scoring project relevance")
        relevance_score = score_project_relevance(paper, project_description)
        log.append(f"  → Relevance score: {relevance_score:.3f}")

        # Step 8 — Generate reusable insights
        log.append("[Step 8] Generating reusable insights")
        insights = _generate_insights(
            paper.paper_id, project_id,
            experiment_design=experiment_patterns[0] if experiment_patterns else None,
            mechanism=mechanism_patterns[0] if mechanism_patterns else None,
            figure_patterns=figure_patterns,
            writing_patterns=writing_patterns,
        )
        log.append(f"  → {len(insights)} insights generated")

        return PaperLearningResult(
            paper_id=paper.paper_id,
            quality_score=quality_score,
            project_relevance_score=relevance_score,
            experiment_design_patterns=experiment_patterns,
            mechanism_patterns=mechanism_patterns,
            figure_logic_patterns=figure_patterns,
            writing_patterns=writing_patterns,
            reusable_insights=insights,
            warnings=warnings,
            processing_log=log,
        )


def learn_high_impact_paper(
    paper: HighImpactPaperRecord,
    llm: LLMAdapter,
    project_id: str = "default",
    project_description: str = "",
) -> PaperLearningResult:
    """Convenience function: create service, run pipeline, return result."""
    service = HighImpactPaperLearningService(llm)
    return service.learn(paper, project_id, project_description)


def _generate_insights(
    paper_id: str,
    project_id: str,
    experiment_design: Optional[ExperimentDesignPattern],
    mechanism: Optional[MechanismPattern],
    figure_patterns: List[FigureLogicPattern],
    writing_patterns: List[WritingPattern],
) -> List[ReusableResearchInsight]:
    """Rule-based insight synthesis from extracted patterns.

    No LLM call — purely derives insights from structured data.
    """
    insights: List[ReusableResearchInsight] = []
    counter = [0]

    def _next_id() -> str:
        counter[0] += 1
        return f"insight_{paper_id}_{counter[0]}"

    # From experiment design
    if experiment_design:
        if experiment_design.experimental_models:
            insights.append(ReusableResearchInsight(
                insight_id=_next_id(),
                paper_id=paper_id,
                project_id=project_id,
                insight_type="experiment_design",
                content=f"Model system: {'; '.join(experiment_design.experimental_models[:3])}",
                why_it_matters="Reusable model system for experimental design",
                applicability_score=0.7,
            ))
        if experiment_design.assays:
            insights.append(ReusableResearchInsight(
                insight_id=_next_id(),
                paper_id=paper_id,
                project_id=project_id,
                insight_type="experiment_design",
                content=f"Key assays: {'; '.join(experiment_design.assays[:4])}",
                why_it_matters="Detection methods applicable to similar studies",
                applicability_score=0.8,
                evidence_refs=experiment_design.assays[:4],
            ))
        if experiment_design.strengths:
            for s in experiment_design.strengths[:2]:
                insights.append(ReusableResearchInsight(
                    insight_id=_next_id(),
                    paper_id=paper_id,
                    project_id=project_id,
                    insight_type="experiment_design",
                    content=s,
                    why_it_matters="Experimental design strength worth replicating",
                    applicability_score=0.6,
                ))

    # From mechanism
    if mechanism and mechanism.pathway:
        insights.append(ReusableResearchInsight(
            insight_id=_next_id(),
            paper_id=paper_id,
            project_id=project_id,
            insight_type="mechanism",
            content=f"Pathway: {mechanism.pathway}",
            why_it_matters="Central mechanism that may generalise to other contexts",
            applicability_score=0.75,
            evidence_refs=mechanism.targets[:5],
        ))
        if mechanism.claim_strength:
            insights.append(ReusableResearchInsight(
                insight_id=_next_id(),
                paper_id=paper_id,
                project_id=project_id,
                insight_type="mechanism",
                content=f"Claim strength: {mechanism.claim_strength} — supported by {'; '.join(mechanism.evidence_types[:3])}",
                why_it_matters="Helps calibrate confidence when reusing this mechanism insight",
                applicability_score=0.6,
            ))

    # From figure patterns
    for fig in figure_patterns[:2]:
        if fig.key_message:
            insights.append(ReusableResearchInsight(
                insight_id=_next_id(),
                paper_id=paper_id,
                project_id=project_id,
                insight_type="figure_logic",
                content=fig.key_message[:200],
                why_it_matters=f"Figure design pattern: {fig.figure_role}",
                applicability_score=0.65,
            ))

    # From writing patterns
    for wp in writing_patterns[:1]:
        if wp.introduction_logic or wp.discussion_logic:
            logic = wp.introduction_logic or wp.discussion_logic
            insights.append(ReusableResearchInsight(
                insight_id=_next_id(),
                paper_id=paper_id,
                project_id=project_id,
                insight_type="writing",
                content=f"Writing structure: {logic[:200]}",
                why_it_matters="Reusable narrative framework for paper writing",
                applicability_score=0.5,
            ))

    # Fallback insight if nothing was extracted
    if not insights:
        insights.append(ReusableResearchInsight(
            insight_id=_next_id(),
            paper_id=paper_id,
            project_id=project_id,
            insight_type="experiment_design",
            content="Paper processed — no specific patterns extracted",
            why_it_matters="Placeholder until patterns are extracted",
            applicability_score=0.3,
        ))

    return insights

"""Rule-based evaluator for paper learning results.

Checks a PaperLearningResult for structural completeness, pattern
density, and critical gaps. Used for quality assurance of the
paper learning pipeline on real paper texts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from researchos_learning_engine.paper_learning.schemas import PaperLearningResult


@dataclass
class EvaluationReport:
    """Outcome of evaluating a single paper learning result."""

    paper_id: str = ""
    completeness_score: float = 0.0
    pattern_density_score: float = 0.0
    insight_usefulness_score: float = 0.0
    overall_score: float = 0.0
    warning_count: int = 0
    pass_or_fail: bool = False
    issues: List[str] = field(default_factory=list)


class PaperLearningResultEvaluator:
    """Rule-based QA evaluator for PaperLearningResult.

    Checks:
      - experiment_design_patterns non-empty       → hard fail if empty
      - mechanism_patterns non-empty               → warning if empty
      - reusable_insights >= 3                     → warning if fewer
      - quality_score >= 0.5                       → warning if lower
      - writing_patterns non-empty                 → warning if empty
      - figure_logic_patterns non-empty            → warning if empty
    """

    # Weights for the three sub-scores in overall_score
    _COMPLETENESS_WEIGHT = 0.40
    _DENSITY_WEIGHT = 0.30
    _USEFULNESS_WEIGHT = 0.30

    # Thresholds
    _MIN_EXPERIMENT_DESIGN = 1       # must-have → hard fail
    _MIN_INSIGHTS = 3
    _MIN_QUALITY_SCORE = 0.5
    _MIN_PATTERN_TYPES = 5           # all 5 types present for full completeness

    def evaluate(self, result: PaperLearningResult) -> EvaluationReport:
        """Run all checks and return a structured report."""
        issues: List[str] = []
        warnings = 0

        # --- Completeness: which pattern types are present ---
        has_experiment_design = len(result.experiment_design_patterns) > 0
        has_mechanism = len(result.mechanism_patterns) > 0
        has_figure = len(result.figure_logic_patterns) > 0
        has_writing = len(result.writing_patterns) > 0
        has_insights = len(result.reusable_insights) > 0

        type_count = sum([has_experiment_design, has_mechanism, has_figure, has_writing, has_insights])

        # --- Hard fail check ---
        if not has_experiment_design:
            issues.append("FAIL: No experiment design patterns extracted")
            warnings += 1

        # --- Warning checks ---
        if not has_mechanism:
            issues.append("WARN: No mechanism patterns extracted")
            warnings += 1
        if not has_figure:
            issues.append("WARN: No figure logic patterns extracted")
            warnings += 1
        if not has_writing:
            issues.append("WARN: No writing patterns extracted")
            warnings += 1
        if len(result.reusable_insights) < self._MIN_INSIGHTS:
            issues.append(
                f"WARN: Only {len(result.reusable_insights)} reusable insights "
                f"(expected >= {self._MIN_INSIGHTS})"
            )
            warnings += 1
        if result.quality_score < self._MIN_QUALITY_SCORE:
            issues.append(
                f"WARN: Quality score {result.quality_score:.3f} "
                f"(expected >= {self._MIN_QUALITY_SCORE})"
            )
            warnings += 1

        # --- Scores ---
        completeness_score = type_count / self._MIN_PATTERN_TYPES

        total_patterns = (
            len(result.experiment_design_patterns)
            + len(result.mechanism_patterns)
            + len(result.figure_logic_patterns)
            + len(result.writing_patterns)
        )
        # Pattern density: 0 for 0, approaches ~0.9 for 10 patterns
        pattern_density_score = min(total_patterns / 10.0, 0.9)

        if result.reusable_insights:
            avg_applicability = sum(
                i.applicability_score for i in result.reusable_insights
            ) / len(result.reusable_insights)
            insight_count_factor = min(len(result.reusable_insights) / self._MIN_INSIGHTS, 1.0)
            insight_usefulness_score = 0.5 * insight_count_factor + 0.5 * avg_applicability
        else:
            insight_usefulness_score = 0.0

        overall_score = (
            self._COMPLETENESS_WEIGHT * completeness_score
            + self._DENSITY_WEIGHT * pattern_density_score
            + self._USEFULNESS_WEIGHT * insight_usefulness_score
        )

        pass_or_fail = has_experiment_design

        return EvaluationReport(
            paper_id=result.paper_id,
            completeness_score=round(completeness_score, 3),
            pattern_density_score=round(pattern_density_score, 3),
            insight_usefulness_score=round(insight_usefulness_score, 3),
            overall_score=round(overall_score, 3),
            warning_count=warnings,
            pass_or_fail=pass_or_fail,
            issues=issues,
        )

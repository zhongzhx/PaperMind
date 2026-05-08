"""Tests for the High-Impact Paper Learning Library — integration & unit tests.

Covers section parsing, quality scoring, all 4 extractors, project
relevance, and the full pipeline via HighImpactPaperLearningService.
"""

from __future__ import annotations

import json
import unittest

from researchos_learning_engine.adapters.llm.mock_llm import MockLLMAdapter
from researchos_learning_engine.paper_learning.schemas import (
    ExperimentDesignPattern,
    FigureLogicPattern,
    HighImpactPaperRecord,
    MechanismPattern,
    PaperLearningResult,
    PaperSection,
    WritingPattern,
)
from researchos_learning_engine.paper_learning.section_parser import parse_sections
from researchos_learning_engine.paper_learning.paper_quality_scoring import score_paper_quality
from researchos_learning_engine.paper_learning.experiment_design_extractor import ExperimentDesignExtractor
from researchos_learning_engine.paper_learning.mechanism_extractor import MechanismExtractor
from researchos_learning_engine.paper_learning.figure_logic_extractor import FigureLogicExtractor
from researchos_learning_engine.paper_learning.writing_pattern_extractor import WritingPatternExtractor
from researchos_learning_engine.paper_learning.project_relevance import score_project_relevance
from researchos_learning_engine.paper_learning.library_service import (
    HighImpactPaperLearningService,
    learn_high_impact_paper,
)

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

_SHORT_TEXT = (
    "Abstract\n\nThis is a test abstract.\n\n"
    "Introduction\n\nBackground and hypothesis.\n\n"
    "Methods\n\nCell culture and treatments.\n\n"
    "Results\n\nKey findings.\n\n"
    "Discussion\n\nInterpretation.\n\n"
    "Conclusion\n\nSummary.\n\n"
)


def _make_test_paper(text: str = "") -> HighImpactPaperRecord:
    return HighImpactPaperRecord(
        paper_id="test_paper_001",
        title="Test Paper for Pipeline Testing",
        authors=["Author A", "Author B"],
        journal="Journal of Testing",
        doi="10.1016/j.test.2024.001",
        year=2024,
        paper_type="original_research",
        full_text=text or _SHORT_TEXT,
    )


# ---------------------------------------------------------------------------
# Section Parser Tests
# ---------------------------------------------------------------------------


class TestSectionParser(unittest.TestCase):
    def test_splits_standard_sections(self):
        sections = parse_sections(_SHORT_TEXT)
        types = [s.section_type for s in sections]
        for expected in ("abstract", "introduction", "methods", "results", "discussion", "conclusion"):
            self.assertIn(expected, types, f"Missing section: {expected}")
        self.assertGreaterEqual(len(sections), 5)

    def test_handles_missing_sections(self):
        text = "Methods\n\nOnly methods.\n\nResults\n\nOnly results."
        sections = parse_sections(text)
        self.assertGreaterEqual(len(sections), 1)

    def test_handles_empty_text(self):
        sections = parse_sections("")
        self.assertEqual(len(sections), 0)

    def test_no_recognized_headers_returns_body(self):
        text = "Some continuous text without any section headers. More text here."
        sections = parse_sections(text)
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].section_type, "unknown")

    def test_sections_have_order(self):
        sections = parse_sections(_SHORT_TEXT)
        for s in sections:
            self.assertIsInstance(s.order, int)
        if len(sections) > 1:
            self.assertLess(sections[0].order, sections[1].order)


# ---------------------------------------------------------------------------
# Quality Scoring Tests
# ---------------------------------------------------------------------------


class TestQualityScoring(unittest.TestCase):
    def test_top_journal_scores_high(self):
        paper = _make_test_paper()
        paper.journal = "Nature"
        sections = parse_sections(paper.full_text)
        score, _ = score_paper_quality(paper, sections)
        self.assertGreaterEqual(score, 0.7)

    def test_no_doi_reduces_score(self):
        paper = _make_test_paper()
        paper.doi = ""
        sections = parse_sections(paper.full_text)
        score_with, _ = score_paper_quality(paper, sections)
        paper.doi = "10.1016/j.test.2024.001"
        score_without, _ = score_paper_quality(paper, sections)
        self.assertGreater(score_without, score_with)

    def test_abstract_only_low_score(self):
        paper = HighImpactPaperRecord(
            paper_id="minimal",
            title="Minimal paper",
            paper_type="review",
            full_text="Abstract\n\nOnly abstract text here.",
        )
        sections = parse_sections(paper.full_text)
        score, _ = score_paper_quality(paper, sections)
        self.assertLess(score, 0.4)

    def test_score_in_zero_one_range(self):
        paper = _make_test_paper()
        sections = parse_sections(paper.full_text)
        score, _ = score_paper_quality(paper, sections)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


# ---------------------------------------------------------------------------
# Experiment Design Extractor Tests
# ---------------------------------------------------------------------------


class TestExperimentDesignExtractor(unittest.TestCase):
    def test_extract_experiment_design(self):
        llm = MockLLMAdapter()
        extractor = ExperimentDesignExtractor(llm)
        paper = _make_test_paper()
        sections = parse_sections(paper.full_text)
        result = extractor.extract(sections, paper)
        self.assertIsInstance(result, ExperimentDesignPattern)
        # Mock LLM returns B. subtilis FPR data
        self.assertTrue(result.experimental_models or result.research_question)


# ---------------------------------------------------------------------------
# Mechanism Extractor Tests
# ---------------------------------------------------------------------------


class TestMechanismExtractor(unittest.TestCase):
    def test_extract_mechanism(self):
        llm = MockLLMAdapter()
        extractor = MechanismExtractor(llm)
        paper = _make_test_paper()
        sections = parse_sections(paper.full_text)
        result = extractor.extract(sections, paper)
        self.assertIsInstance(result, MechanismPattern)
        # Mock LLM returns TLR4/MyD88/NF-kB data
        self.assertTrue(result.pathway or result.targets)


# ---------------------------------------------------------------------------
# Figure Logic Extractor Tests
# ---------------------------------------------------------------------------


class TestFigureLogicExtractor(unittest.TestCase):
    def test_extract_figure_logics(self):
        llm = MockLLMAdapter()
        extractor = FigureLogicExtractor(llm)
        paper = _make_test_paper()
        sections = parse_sections(paper.full_text)
        results = extractor.extract(sections, paper)
        self.assertIsInstance(results, list)
        if results:
            self.assertIsInstance(results[0], FigureLogicPattern)
            self.assertTrue(results[0].figure_id or results[0].key_message)


# ---------------------------------------------------------------------------
# Writing Pattern Extractor Tests
# ---------------------------------------------------------------------------


class TestWritingPatternExtractor(unittest.TestCase):
    def test_extract_writing_patterns(self):
        llm = MockLLMAdapter()
        extractor = WritingPatternExtractor(llm)
        paper = _make_test_paper()
        sections = parse_sections(paper.full_text)
        results = extractor.extract(sections, paper)
        self.assertIsInstance(results, list)
        if results:
            self.assertIsInstance(results[0], WritingPattern)
            self.assertTrue(results[0].introduction_logic or results[0].discussion_logic)


# ---------------------------------------------------------------------------
# Project Relevance Tests
# ---------------------------------------------------------------------------


class TestProjectRelevance(unittest.TestCase):
    def test_matching_description_high_score(self):
        paper = HighImpactPaperRecord(
            paper_id="rel_test",
            title="example research project pipeline testing",
            full_text=(
                "example research project pipeline testing "
                "example research project pipeline testing "
                "example research project pipeline "
                "testing analysis validation verification"
            ),
        )
        score = score_project_relevance(
            paper,
            "example research project pipeline testing",
        )
        self.assertGreater(score, 0.3)

    def test_unrelated_description_low_score(self):
        paper = HighImpactPaperRecord(
            paper_id="rel_test2",
            title="Quantum computing algorithms",
            full_text="Quantum circuits entanglement superposition gate operations",
        )
        score = score_project_relevance(
            paper,
            "example research project pipeline testing analysis",
        )
        self.assertLess(score, 0.3)

    def test_score_in_zero_one_range(self):
        paper = _make_test_paper()
        score = score_project_relevance(paper, "test project description")
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


# ---------------------------------------------------------------------------
# Library Service Integration Tests
# ---------------------------------------------------------------------------


class TestPaperLearningIntegration(unittest.TestCase):
    def setUp(self):
        self.llm = MockLLMAdapter()
        self.service = HighImpactPaperLearningService(self.llm)
        self.paper = _make_test_paper()

    def test_full_pipeline_returns_result(self):
        result = self.service.learn(self.paper, project_id="proj_test", project_description="test pipeline description")
        self.assertIsInstance(result, PaperLearningResult)
        self.assertEqual(result.paper_id, "test_paper_001")
        self.assertGreater(len(result.processing_log), 0)

    def test_experiment_design_patterns_not_empty(self):
        result = self.service.learn(self.paper, project_id="proj_test", project_description="test description")
        # With mock LLM, experiment design should be extracted
        self.assertGreater(len(result.experiment_design_patterns), 0)

    def test_mechanism_patterns_not_empty(self):
        result = self.service.learn(self.paper, project_id="proj_test", project_description="test description")
        self.assertGreater(len(result.mechanism_patterns), 0)

    def test_figure_logic_patterns_not_empty(self):
        result = self.service.learn(self.paper, project_id="proj_test", project_description="test")
        # Mock returns 3 figures
        self.assertGreater(len(result.figure_logic_patterns), 0)

    def test_writing_patterns_not_empty(self):
        result = self.service.learn(self.paper, project_id="proj_test", project_description="test")
        self.assertGreater(len(result.writing_patterns), 0)

    def test_reusable_insights_not_empty(self):
        result = self.service.learn(self.paper, project_id="proj_test", project_description="test")
        self.assertGreater(len(result.reusable_insights), 0)

    def test_quality_score_in_range(self):
        result = self.service.learn(self.paper, project_id="proj_test")
        self.assertGreaterEqual(result.quality_score, 0.0)
        self.assertLessEqual(result.quality_score, 1.0)

    def test_project_relevance_score_in_range(self):
        result = self.service.learn(self.paper, project_id="proj_test", project_description="test description")
        self.assertGreaterEqual(result.project_relevance_score, 0.0)
        self.assertLessEqual(result.project_relevance_score, 1.0)

    def test_learn_high_impact_paper_convenience_function(self):
        result = learn_high_impact_paper(
            self.paper,
            llm=self.llm,
            project_id="proj_test",
            project_description="test",
        )
        self.assertIsInstance(result, PaperLearningResult)

    def test_learning_result_can_serialize_to_json(self):
        result = self.service.learn(self.paper, project_id="proj_test")
        d = result.to_dict()
        json_str = json.dumps(d)
        self.assertIsInstance(json_str, str)
        # Verify key fields present in serialized output
        self.assertIn("paper_id", d)
        self.assertIn("schema_version", d)
        self.assertIn("engine_version", d)
        self.assertIn("processing_log", d)

    def test_empty_paper_does_not_crash(self):
        empty_paper = HighImpactPaperRecord(paper_id="empty")
        result = self.service.learn(empty_paper)
        self.assertIsInstance(result, PaperLearningResult)
        # Should have a fallback insight
        self.assertGreaterEqual(len(result.reusable_insights), 1)

    def test_mock_llm_output_is_deterministic(self):
        """Multiple calls with same input produce consistent output."""
        result1 = self.service.learn(self.paper)
        result2 = self.service.learn(self.paper)
        self.assertEqual(
            len(result1.experiment_design_patterns),
            len(result2.experiment_design_patterns),
        )

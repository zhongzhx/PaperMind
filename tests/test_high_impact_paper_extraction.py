"""Tests for High-Impact Paper Learning Library — schema serialization.

Covers round-trip to_dict/from_dict for all 8 paper_learning schemas,
JSON safety, forward compatibility, and PaperLearningResult structure.
"""

from __future__ import annotations

import json
import unittest

from researchos_learning_engine.paper_learning.schemas import (
    ExperimentDesignPattern,
    FigureLogicPattern,
    HighImpactPaperRecord,
    InsightType,
    LearningStatus,
    MechanismPattern,
    PaperLearningResult,
    PaperSection,
    PaperType,
    ReusableResearchInsight,
    SectionType,
    SourceType,
    WritingPattern,
)
from researchos_learning_engine.paper_learning.section_parser import parse_sections


# ---------------------------------------------------------------------------
# Round-trip Serialization Tests
# ---------------------------------------------------------------------------


class TestHighImpactPaperRecordSerialization(unittest.TestCase):
    def test_round_trip(self):
        original = HighImpactPaperRecord(
            paper_id="hip_001",
            title="Test Paper",
            authors=["Author A", "Author B"],
            year=2024,
            journal="Nature",
            doi="10.1038/nature.2024.001",
            source_type="oa_pdf",
            field="immunology",
            paper_type="original_research",
            full_text="Full text content here.",
            quality_score=0.85,
            project_relevance_score=0.75,
            learning_status="learned",
        )
        d = original.to_dict()
        restored = HighImpactPaperRecord.from_dict(d)
        self.assertEqual(restored.paper_id, original.paper_id)
        self.assertEqual(restored.title, original.title)
        self.assertEqual(restored.authors, original.authors)
        self.assertEqual(restored.year, original.year)
        self.assertEqual(restored.journal, original.journal)

    def test_from_dict_with_extra_fields(self):
        d = {
            "paper_id": "hip_extra",
            "title": "Extra",
            "unknown_field": "should_be_ignored",
            "another_unknown": 42,
        }
        restored = HighImpactPaperRecord.from_dict(d)
        self.assertEqual(restored.paper_id, "hip_extra")
        self.assertFalse(hasattr(restored, "unknown_field"))


class TestPaperSectionSerialization(unittest.TestCase):
    def test_round_trip(self):
        original = PaperSection(
            section_id="sec_001",
            paper_id="hip_001",
            section_type="methods",
            title="Materials and Methods",
            text="Cell culture...",
            order=2,
        )
        d = original.to_dict()
        restored = PaperSection.from_dict(d)
        self.assertEqual(restored.section_id, original.section_id)
        self.assertEqual(restored.section_type, original.section_type)
        self.assertEqual(restored.order, original.order)

    def test_from_dict_with_extra_fields(self):
        d = {"section_id": "sec_x", "paper_id": "p1", "section_type": "results", "title": "R", "text": "T", "order": 1, "extra": True}
        restored = PaperSection.from_dict(d)
        self.assertEqual(restored.section_id, "sec_x")
        self.assertFalse(hasattr(restored, "extra"))


class TestExperimentDesignPatternSerialization(unittest.TestCase):
    def test_round_trip(self):
        original = ExperimentDesignPattern(
            pattern_id="ed_001",
            paper_id="hip_001",
            research_question="Test question?",
            hypothesis="Test hypothesis",
            experimental_models=["Model A", "Model B"],
            groups=["Control", "Treatment"],
            interventions=["Test treatment"],
            doses_or_concentrations=["Low dose", "High dose"],
            timepoints=["0 h", "24 h"],
            assays=["ELISA", "Western blot"],
            controls=["Untreated"],
            statistical_methods=["ANOVA"],
            validation_chain=["Dose-response", "Mechanism validation"],
            strengths=["Multiple assays"],
            limitations=["In vitro only"],
        )
        d = original.to_dict()
        restored = ExperimentDesignPattern.from_dict(d)
        self.assertEqual(restored.pattern_id, original.pattern_id)
        self.assertEqual(restored.experimental_models, original.experimental_models)

    def test_json_safe(self):
        p = ExperimentDesignPattern(pattern_id="ed_001", paper_id="p1")
        json.dumps(p.to_dict())  # must not raise


class TestMechanismPatternSerialization(unittest.TestCase):
    def test_round_trip(self):
        original = MechanismPattern(
            pattern_id="mech_001",
            paper_id="hip_001",
            pathway="Example signaling pathway",
            targets=["Target A", "Target B"],
            upstream_factors=["Factor X", "Factor Y"],
            downstream_readouts=["Readout 1", "Readout 2"],
            evidence_types=["Western blot", "qPCR"],
            claim_strength="strong",
            limitations=["No knockout model"],
        )
        d = original.to_dict()
        restored = MechanismPattern.from_dict(d)
        self.assertEqual(restored.pathway, original.pathway)
        self.assertEqual(restored.targets, original.targets)

    def test_json_safe(self):
        p = MechanismPattern(pattern_id="m1", paper_id="p1")
        json.dumps(p.to_dict())


class TestFigureLogicPatternSerialization(unittest.TestCase):
    def test_round_trip(self):
        original = FigureLogicPattern(
            pattern_id="fig_001",
            paper_id="hip_001",
            figure_id="Figure 1",
            figure_role="phenotypic characterization",
            data_type="bar_chart",
            key_message="Cytokines upregulated",
            supports_which_claim="Macrophage activation",
            reusable_figure_idea="Dose-response bar chart",
        )
        d = original.to_dict()
        restored = FigureLogicPattern.from_dict(d)
        self.assertEqual(restored.figure_id, original.figure_id)
        self.assertEqual(restored.key_message, original.key_message)

    def test_json_safe(self):
        p = FigureLogicPattern(pattern_id="f1", paper_id="p1")
        json.dumps(p.to_dict())


class TestWritingPatternSerialization(unittest.TestCase):
    def test_round_trip(self):
        original = WritingPattern(
            pattern_id="wp_001",
            paper_id="hip_001",
            introduction_logic="Funnel: broad context → gap → hypothesis",
            result_narrative="Figure-guided narrative",
            discussion_logic="Reverse funnel structure",
            novelty_framing="First demonstration of the mechanism",
            limitation_framing="Presented as future directions",
            application_framing="Potential applications discussed",
            reusable_sentences_or_templates=["'These findings suggest that...'"],
        )
        d = original.to_dict()
        restored = WritingPattern.from_dict(d)
        self.assertEqual(restored.introduction_logic, original.introduction_logic)
        self.assertEqual(restored.reusable_sentences_or_templates, original.reusable_sentences_or_templates)

    def test_json_safe(self):
        p = WritingPattern(pattern_id="w1", paper_id="p1")
        json.dumps(p.to_dict())


class TestReusableResearchInsightSerialization(unittest.TestCase):
    def test_round_trip(self):
        original = ReusableResearchInsight(
            insight_id="insight_001",
            paper_id="hip_001",
            project_id="proj_test",
            insight_type="mechanism",
            content="Example mechanism insight",
            why_it_matters="Example relevance description",
            applicability_score=0.75,
            evidence_refs=["Western blot", "qPCR"],
        )
        d = original.to_dict()
        restored = ReusableResearchInsight.from_dict(d)
        self.assertEqual(restored.insight_id, original.insight_id)
        self.assertEqual(restored.insight_type, original.insight_type)
        self.assertEqual(restored.applicability_score, original.applicability_score)

    def test_json_safe(self):
        p = ReusableResearchInsight(insight_id="i1", paper_id="p1", project_id="p1")
        json.dumps(p.to_dict())

    def test_from_dict_with_extra_fields(self):
        d = {"insight_id": "i1", "paper_id": "p1", "project_id": "p1", "insight_type": "mechanism", "content": "c", "why_it_matters": "w", "applicability_score": 0.5, "evidence_refs": [], "unknown": True}
        restored = ReusableResearchInsight.from_dict(d)
        self.assertEqual(restored.insight_id, "i1")


class TestPaperLearningResultSerialization(unittest.TestCase):
    def test_round_trip(self):
        original = PaperLearningResult(
            paper_id="hip_001",
            schema_version="1.0",
            engine_version="0.1.0",
            quality_score=0.82,
            project_relevance_score=0.75,
            experiment_design_patterns=[
                ExperimentDesignPattern(pattern_id="ed_001", paper_id="hip_001"),
            ],
            mechanism_patterns=[
                MechanismPattern(pattern_id="mech_001", paper_id="hip_001"),
            ],
            figure_logic_patterns=[
                FigureLogicPattern(pattern_id="fig_001", paper_id="hip_001", figure_id="Figure 1"),
            ],
            writing_patterns=[
                WritingPattern(pattern_id="wp_001", paper_id="hip_001"),
            ],
            reusable_insights=[
                ReusableResearchInsight(insight_id="ins_001", paper_id="hip_001", project_id="proj_test"),
            ],
            warnings=["Test warning"],
            processing_log=["[Step 1] Parsing sections"],
        )
        d = original.to_dict()
        json_str = json.dumps(d)
        self.assertIsInstance(json_str, str)

        restored = PaperLearningResult.from_dict(d)
        self.assertEqual(restored.paper_id, original.paper_id)
        self.assertEqual(len(restored.experiment_design_patterns), 1)
        self.assertEqual(len(restored.mechanism_patterns), 1)
        self.assertEqual(len(restored.figure_logic_patterns), 1)
        self.assertEqual(len(restored.writing_patterns), 1)
        self.assertEqual(len(restored.reusable_insights), 1)
        self.assertEqual(len(restored.warnings), 1)
        self.assertEqual(len(restored.processing_log), 1)

    def test_to_dict_contains_only_json_types(self):
        result = PaperLearningResult(paper_id="p1")
        d = result.to_dict()
        json.dumps(d)  # must not raise TypeError

    def test_from_dict_with_extra_fields(self):
        d = {"paper_id": "p1", "schema_version": "1.0", "engine_version": "0.1.0", "quality_score": 0.5, "project_relevance_score": 0.5, "extra_field": "ignored"}
        restored = PaperLearningResult.from_dict(d)
        self.assertEqual(restored.paper_id, "p1")

    def test_full_pipeline_output_structure(self):
        """Simulate a full pipeline output and verify all fields."""
        from researchos_learning_engine.paper_learning.library_service import HighImpactPaperLearningService
        from researchos_learning_engine.adapters.llm.mock_llm import MockLLMAdapter

        llm = MockLLMAdapter()
        service = HighImpactPaperLearningService(llm)

        paper = HighImpactPaperRecord(
            paper_id="integration_test",
            title="Test pipeline integration paper",
            journal="Journal of Testing",
            doi="10.1016/j.test.2024.001",
            year=2024,
            paper_type="original_research",
            full_text=(
                "Abstract\n\nThis is test abstract.\n\n"
                "Introduction\n\nBackground of research.\n\n"
                "Methods\n\nStandard protocols followed.\n\n"
                "Results\n\nSignificant findings observed.\n\n"
                "Discussion\n\nFindings interpreted.\n\n"
                "Conclusion\n\nSummary of findings.\n\n"
            ),
        )

        result = service.learn(paper, project_id="proj_test", project_description="test description")
        self.assertEqual(result.paper_id, "integration_test")
        self.assertEqual(result.schema_version, "1.0")
        self.assertEqual(result.engine_version, "0.1.0")
        self.assertGreaterEqual(result.quality_score, 0.0)
        self.assertGreaterEqual(result.project_relevance_score, 0.0)
        self.assertGreater(len(result.processing_log), 0)
        self.assertIsInstance(result.to_dict(), dict)
        json.dumps(result.to_dict())  # full pipeline output must be JSON-serializable

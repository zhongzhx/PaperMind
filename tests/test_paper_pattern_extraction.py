"""Tests for paper pattern extraction with mock LLM."""

from __future__ import annotations

import unittest

from researchos_learning_engine.adapters.llm.mock_llm import MockLLMAdapter
from researchos_learning_engine.application.paper_extraction_service import (
    PaperExtractionService,
)
from researchos_learning_engine.domain.constants import SourceType, StudyType
from researchos_learning_engine.domain.schemas import PaperRecord


class TestPaperExtraction(unittest.TestCase):
    def setUp(self):
        self.llm = MockLLMAdapter()
        self.service = PaperExtractionService(self.llm)

    def test_extract_pattern_from_paper(self):
        paper = PaperRecord(
            paper_id="test_001",
            title="Test: Example Research Article",
            authors=["Test A"],
            year=2024,
            full_text="This is example text for testing paper extraction. It contains research content for pipeline validation.",
            source_type=SourceType.OA_PDF,
        )
        pattern = self.service.extract(paper, project_id="proj_test")

        self.assertEqual(pattern.paper_id, "test_001")
        self.assertEqual(pattern.project_id, "proj_test")
        self.assertTrue(pattern.pattern_id.startswith("pat_"))
        # Mock LLM should produce structured output; core_logic
        # may be empty if the mock LLM response falls through to
        # the default JSON response without extraction fields
        self.assertIsInstance(pattern.experimental_models, list)

    def test_extract_from_minimal_paper(self):
        paper = PaperRecord(
            paper_id="test_002",
            title="Minimal Paper",
            authors=[],
            source_type=SourceType.ABSTRACT_ONLY,
        )
        pattern = self.service.extract(paper, project_id="proj_test")
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.paper_id, "test_002")

    def test_study_type_mapping(self):
        paper = PaperRecord(
            paper_id="test_003",
            title="Clinical Trial",
            full_text="Clinical trial data showing effect of treatment in patients.",
        )
        pattern = self.service.extract(paper, project_id="proj_test")
        self.assertIn(pattern.study_type, (StudyType.OTHER, StudyType.COMPUTATIONAL))

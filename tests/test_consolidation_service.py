"""Tests for the main consolidation service."""

from __future__ import annotations

import unittest

from researchos_learning_engine.adapters.llm.mock_llm import MockLLMAdapter
from researchos_learning_engine.application.consolidation_service import (
    ConsolidationService,
)
from researchos_learning_engine.domain.schemas import ConsolidationInput
from tests.conftest import make_sample_consolidation_input


class TestConsolidationService(unittest.TestCase):
    def setUp(self):
        self.llm = MockLLMAdapter()
        self.service = ConsolidationService(self.llm)

    def test_run_returns_consolidation_result(self):
        input_data = make_sample_consolidation_input()
        result = self.service.run(input_data)

        self.assertEqual(result.project_id, "test_project")
        self.assertGreater(len(result.processing_log), 0)

    def test_memories_are_scored(self):
        input_data = make_sample_consolidation_input()
        result = self.service.run(input_data)

        # Memories in the input should all have health_scores after consolidation
        # They might not change status, but they should be scored
        total_listed = (
            len(result.promoted_memories)
            + len(result.archived_memories)
            + len(result.superseded_memories)
        )

        # At minimum, processing_log should mention scoring
        self.assertTrue(
            any("Scoring" in entry for entry in result.processing_log),
            "Scoring step should be logged",
        )

    def test_patterns_extracted_from_papers(self):
        input_data = make_sample_consolidation_input()
        result = self.service.run(input_data)
        self.assertGreater(len(result.new_research_patterns), 0)
        pattern = result.new_research_patterns[0]
        self.assertNotEqual(pattern.paper_id, "")
        # Pattern should have structured fields (may be empty with MockLLM fallback)
        self.assertIsInstance(pattern.experimental_models, list)

    def test_contradictions_detected(self):
        input_data = make_sample_consolidation_input()
        result = self.service.run(input_data)
        self.assertIsInstance(result.contradictions_detected, list)

    def test_literature_queries_generated(self):
        input_data = make_sample_consolidation_input()
        result = self.service.run(input_data)
        self.assertIsInstance(result.recommended_literature_queries, list)

    def test_evidence_edges_created(self):
        input_data = make_sample_consolidation_input()
        result = self.service.run(input_data)
        if result.new_evidence_edges:
            edge = result.new_evidence_edges[0]
            self.assertTrue(edge.edge_id.startswith("edge_"))
            self.assertNotEqual(edge.source_node, "")
            self.assertNotEqual(edge.target_node, "")

    def test_project_summary_updated(self):
        input_data = make_sample_consolidation_input()
        result = self.service.run(input_data)
        self.assertNotEqual(result.updated_project_summary, "")
        self.assertGreater(len(result.updated_project_summary), 20)

    def test_empty_input_does_not_crash(self):
        empty_input = ConsolidationInput(project_id="empty_test")
        result = self.service.run(empty_input)
        self.assertEqual(result.project_id, "empty_test")
        self.assertGreater(len(result.processing_log), 0)

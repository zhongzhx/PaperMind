"""Integration tests for the Python API."""

from __future__ import annotations

import unittest

from researchos_learning_engine.domain.schemas import (
    ConsolidationInput,
    ConsolidationResult,
)
from researchos_learning_engine.interfaces.python_api import run_sleep_cycle
from tests.conftest import make_sample_consolidation_input


class TestPythonAPI(unittest.TestCase):
    def test_run_sleep_cycle_returns_result(self):
        input_data = ConsolidationInput(
            project_id="api_test",
            project_title="API Test Project",
            project_description="Test description",
            current_project_summary="Test summary.",
        )
        result = run_sleep_cycle(input_data)
        self.assertIsInstance(result, ConsolidationResult)
        self.assertEqual(result.project_id, "api_test")

    def test_run_sleep_cycle_with_memories(self):
        input_data = make_sample_consolidation_input()
        result = run_sleep_cycle(input_data)
        self.assertIsInstance(result, ConsolidationResult)
        self.assertEqual(result.project_id, "test_project")

        log_entries = " ".join(result.processing_log)
        self.assertIn("Scoring", log_entries)
        self.assertIn("patterns", log_entries.lower())

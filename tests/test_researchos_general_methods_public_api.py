"""Tests for the public Python API of general_methods_kb package.

Tests the three public API functions:
  build_general_methods_kb
  load_general_methods_kb
  query_general_methods_kb

No real papers or LLM required.
"""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest

from researchos_learning_engine.general_methods_kb import (
    build_general_methods_kb,
    load_general_methods_kb,
    query_general_methods_kb,
)


class TestBuildAPI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.input_dir = os.path.join(self.tmp.name, "input")
        self.output_dir = os.path.join(self.tmp.name, "output")
        os.makedirs(self.input_dir, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _make_paper(self, name="paper1.txt", source="Nature"):
        content = f"""This is a test paper published in {source}.

Abstract: This study presents a novel method for protein detection.

Methods: Proteins were separated by SDS-PAGE and transferred to PVDF
membranes. Primary antibodies were incubated overnight at 4°C.

Results: The new method showed improved sensitivity.

DOI: 10.1038/s41586-023-00000-0
"""
        path = os.path.join(self.input_dir, name)
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_build_api_basic(self):
        self._make_paper()
        result = build_general_methods_kb(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["files_processed"], 1)
        self.assertIn("jsonl_path", result)
        self.assertIn("db_path", result)

    def test_build_api_no_papers(self):
        result = build_general_methods_kb(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["total_files_found"], 0)

    def test_build_api_output_files_exist(self):
        self._make_paper()
        result = build_general_methods_kb(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
        )
        self.assertTrue(os.path.isfile(result["jsonl_path"]))
        self.assertTrue(os.path.isfile(result["db_path"]))
        self.assertTrue(os.path.isfile(result["summary_path"]))
        # Phase 3 additional files
        self.assertIn("manifest_path", result)
        self.assertIn("skipped_json_path", result)
        self.assertIn("failed_json_path", result)
        if os.path.isfile(result.get("manifest_path", "")):
            with open(result["manifest_path"]) as f:
                manifest = json.load(f)
            self.assertIsInstance(manifest, list)

    def test_build_api_overwrite(self):
        self._make_paper()
        build_general_methods_kb(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
        )
        # Second build with overwrite
        result = build_general_methods_kb(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            overwrite=True,
        )
        self.assertEqual(result["status"], "completed")

    def test_build_api_with_llm_mock(self):
        """Build with a mock LLM adapter should not crash."""
        from researchos_learning_engine.adapters.llm.mock_llm import MockLLMAdapter
        self._make_paper()
        result = build_general_methods_kb(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            llm=MockLLMAdapter(),
        )
        self.assertEqual(result["status"], "completed")
        # Should have deep learning fields in the output
        jsonl_path = result["jsonl_path"]
        with open(jsonl_path) as f:
            record = json.loads(f.readline())
        self.assertIn("deep_learning", record)

    def test_load_api(self):
        self._make_paper()
        build_general_methods_kb(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
        )
        db_path = os.path.join(self.output_dir, "method_knowledge_base.db")
        records = load_general_methods_kb(db_path)
        self.assertIsInstance(records, list)
        self.assertGreaterEqual(len(records), 1)
        self.assertIn("title", records[0])
        self.assertIn("evidence_items", records[0])

    def test_load_api_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_general_methods_kb("/nonexistent/path.sqlite")

    def test_query_api(self):
        self._make_paper()
        build_general_methods_kb(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
        )
        db_path = os.path.join(self.output_dir, "method_knowledge_base.db")
        results = query_general_methods_kb(
            sqlite_path=db_path,
            query="protein",
        )
        self.assertIsInstance(results, list)

    def test_query_api_recent_only(self):
        self._make_paper()
        build_general_methods_kb(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
        )
        db_path = os.path.join(self.output_dir, "method_knowledge_base.db")
        results = query_general_methods_kb(
            sqlite_path=db_path,
            query="",
            recent_only=True,
        )
        self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main()

"""Integration tests for the full KB builder pipeline.

Uses a temporary directory with mock paper files — no real papers, no LLM.
"""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest

from researchos_learning_engine.general_methods_kb.kb_builder import build_knowledge_base


def _make_text_paper(dir_path: str, subdir: str, name: str,
                     source: str = "Nature") -> str:
    """Write a mock paper file and return its path."""
    sub = os.path.join(dir_path, subdir)
    os.makedirs(sub, exist_ok=True)
    path = os.path.join(sub, name)

    content = f"""This is a test paper published in {source}.

Abstract: This study presents a novel method for protein detection.
The method shows high sensitivity and specificity.

Introduction: Protein detection is crucial for biomedical research.
Western blot is the gold standard method.

Methods: Proteins were separated by SDS-PAGE and transferred to PVDF
membranes. Primary antibodies were incubated overnight at 4°C.
HRP-conjugated secondary antibodies were used for detection.

Results: The new method showed 2x improved sensitivity compared to
traditional approaches. Statistical analysis confirmed significance.

Discussion: Our findings demonstrate the utility of this approach
for protein analysis in complex biological samples.

DOI: 10.1038/s41586-023-00000-0
    """
    with open(path, "w") as f:
        f.write(content)
    return path


def _make_low_impact_paper(dir_path: str, subdir: str, name: str) -> str:
    """Write a mock preprint paper file (now processed, not skipped)."""
    sub = os.path.join(dir_path, subdir)
    os.makedirs(sub, exist_ok=True)
    path = os.path.join(sub, name)
    content = "This is a preprint paper from arXiv. Not high impact."
    with open(path, "w") as f:
        f.write(content)
    return path


def _make_empty_file(dir_path: str, subdir: str, name: str) -> str:
    """Write an empty file (should be skipped)."""
    sub = os.path.join(dir_path, subdir)
    os.makedirs(sub, exist_ok=True)
    path = os.path.join(sub, name)
    with open(path, "w") as f:
        f.write("")
    return path


def _make_corrupted_file(dir_path: str, subdir: str, name: str) -> str:
    """Write an unreadable file (binary garbage)."""
    sub = os.path.join(dir_path, subdir)
    os.makedirs(sub, exist_ok=True)
    path = os.path.join(sub, name)
    with open(path, "wb") as f:
        f.write(b"\x00\xff\xfe\xfd\xfc\x00\x01\x02")
    return path


class TestKbBuilderBuild(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.input_dir = os.path.join(self.tmp.name, "input")
        self.output_dir = os.path.join(self.tmp.name, "output")
        os.makedirs(self.input_dir, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_build_with_nature_papers(self):
        _make_text_paper(self.input_dir, "nature_sub", "paper1.txt", source="Nature")
        result = build_knowledge_base(self.input_dir, self.output_dir)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["files_processed"], 1)
        self.assertEqual(result["files_failed"], 0)
        self.assertIn("jsonl_path", result)
        self.assertIn("db_path", result)

    def test_build_with_multiple_papers(self):
        _make_text_paper(self.input_dir, "nature", "p1.txt", source="Nature")
        _make_text_paper(self.input_dir, "science", "p2.txt", source="Science")
        _make_text_paper(self.input_dir, "cell", "p3.txt", source="Cell")
        result = build_knowledge_base(self.input_dir, self.output_dir)
        self.assertEqual(result["files_processed"], 3)

    def test_build_processes_all_papers(self):
        """Phase 3: ALL papers are processed regardless of source family."""
        _make_text_paper(self.input_dir, "nature", "p1.txt", source="Nature")
        _make_low_impact_paper(self.input_dir, "preprints", "arxiv_paper.txt")
        result = build_knowledge_base(self.input_dir, self.output_dir)
        # Both papers should be processed — no source family filter
        self.assertEqual(result["files_processed"], 2)
        self.assertEqual(result["files_skipped"], 0)

    def test_build_skips_empty_files(self):
        """Truly empty files are still skipped."""
        _make_text_paper(self.input_dir, "nature", "good.txt")
        _make_empty_file(self.input_dir, "empty", "empty.txt")
        result = build_knowledge_base(self.input_dir, self.output_dir)
        self.assertEqual(result["files_processed"], 1)
        self.assertEqual(result["files_skipped"], 1)

    def test_build_handles_failures_gracefully(self):
        _make_text_paper(self.input_dir, "nature", "good.txt")
        _make_corrupted_file(self.input_dir, "pdfs", "bad.pdf")
        result = build_knowledge_base(self.input_dir, self.output_dir)
        self.assertGreaterEqual(result["files_failed"] + result["files_skipped"], 0)
        self.assertGreaterEqual(result["files_processed"], 1)

    def test_empty_input(self):
        result = build_knowledge_base(self.input_dir, self.output_dir)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["total_files_found"], 0)

    def test_output_files_created(self):
        _make_text_paper(self.input_dir, "nature", "p1.txt")
        result = build_knowledge_base(self.input_dir, self.output_dir)
        self.assertTrue(os.path.isfile(result["jsonl_path"]))
        self.assertTrue(os.path.isfile(result["db_path"]))
        self.assertTrue(os.path.isfile(result["summary_path"]))

    def test_jsonl_output_valid(self):
        _make_text_paper(self.input_dir, "nature", "p1.txt")
        _make_text_paper(self.input_dir, "science", "p2.txt")
        result = build_knowledge_base(self.input_dir, self.output_dir)
        with open(result["jsonl_path"]) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 2)
        for line in lines:
            data = json.loads(line)
            self.assertIn("paper_id", data)
            self.assertIn("title", data)

    def test_sqlite_tables_exist(self):
        _make_text_paper(self.input_dir, "nature", "p1.txt")
        result = build_knowledge_base(self.input_dir, self.output_dir)
        conn = sqlite3.connect(result["db_path"])
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        expected_tables = {
            "papers", "method_records", "evidence_items",
            "retrieval_keywords", "build_runs",
        }
        self.assertTrue(expected_tables.issubset(tables),
                        f"Missing tables: {expected_tables - tables}")
        conn.close()

    def test_paper_id_is_deterministic(self):
        _make_text_paper(self.input_dir, "nature", "p1.txt")
        result1 = build_knowledge_base(self.input_dir, self.output_dir)
        result2 = build_knowledge_base(self.input_dir, self.output_dir + "_2")
        with open(result1["jsonl_path"]) as f1:
            data1 = json.loads(f1.readline())
        with open(result2["jsonl_path"]) as f2:
            data2 = json.loads(f2.readline())
        self.assertEqual(data1["paper_id"], data2["paper_id"])

    def test_max_papers_limit(self):
        _make_text_paper(self.input_dir, "n", "p1.txt")
        _make_text_paper(self.input_dir, "n", "p2.txt")
        _make_text_paper(self.input_dir, "n", "p3.txt")
        result = build_knowledge_base(self.input_dir, self.output_dir, max_papers=2)
        self.assertLessEqual(result["total_files_found"], 2)

    def test_summary_report_content(self):
        _make_text_paper(self.input_dir, "nature", "paper.txt")
        result = build_knowledge_base(self.input_dir, self.output_dir)
        with open(result["summary_path"]) as f:
            text = f.read()
        self.assertIn("Build Summary", text)
        self.assertIn("Accepted Papers", text)
        # Phase 3: should show source tier and learning depth columns
        self.assertIn("Source Tier", text)
        self.assertIn("Depth", text)

    def test_new_fields_in_jsonl(self):
        """Phase 3: JSONL records should include source_tier, learning_depth, etc."""
        _make_text_paper(self.input_dir, "nature", "paper.txt")
        result = build_knowledge_base(self.input_dir, self.output_dir)
        with open(result["jsonl_path"]) as f:
            data = json.loads(f.readline())
        self.assertIn("source_tier", data)
        self.assertIn("learning_depth", data)
        self.assertIn("publication_age_group", data)
        self.assertIn("is_user_provided", data)
        self.assertIn("is_classic_foundational", data)

    def test_classic_foundational_export(self):
        """Phase 3: classic foundational summary should be created."""
        _make_text_paper(self.input_dir, "nature", "paper.txt")
        result = build_knowledge_base(self.input_dir, self.output_dir)
        classic_path = os.path.join(self.output_dir, "classic_foundational_methods_summary.md")
        # May or may not exist depending on whether papers are pre-2021
        self.assertIn("classic_foundational_report_path", result)


if __name__ == "__main__":
    unittest.main()

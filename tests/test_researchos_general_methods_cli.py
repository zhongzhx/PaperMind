"""Tests for the query CLI script.

All tests run the script via subprocess with a pre-built SQLite database.
No real papers or LLM required.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_QUERY_SCRIPT = os.path.join(
    _HERE, "..",
    "examples", "researchos_general_methods_kb", "query_kb.py",
)


def _build_test_db(path):
    """Create a test SQLite database at the given path with Phase 3 columns."""
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE papers (
            paper_id TEXT PRIMARY KEY, title TEXT, year INTEGER, journal TEXT,
            doi TEXT, source_family TEXT, source_journal_group TEXT,
            source_type TEXT, source_tier TEXT, learning_depth TEXT,
            learning_reason TEXT, is_recent_five_years INTEGER,
            is_user_provided INTEGER, is_classic_foundational INTEGER,
            publication_age_group TEXT,
            method_category TEXT, article_role TEXT, confidence_score REAL,
            created_at TEXT
        );
        CREATE TABLE method_records (
            paper_id TEXT PRIMARY KEY, method_category TEXT,
            method_subcategories TEXT, abstract_summary_cn TEXT,
            methodological_learning_value_cn TEXT, method_scope_cn TEXT,
            retrieval_keywords_cn TEXT, retrieval_keywords_en TEXT
        );
        CREATE TABLE evidence_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT, paper_id TEXT,
            claim TEXT, short_quote TEXT, section TEXT,
            evidence_type TEXT, confidence REAL
        );
        CREATE TABLE deep_learning_fields (
            paper_id TEXT PRIMARY KEY, high_impact_value_cn TEXT,
            what_researchos_should_learn_cn TEXT, applicable_scenarios_cn TEXT,
            core_protocol_steps TEXT, critical_parameters TEXT,
            quality_control_points TEXT, reproducibility_points TEXT,
            common_pitfalls TEXT, troubleshooting_hints TEXT,
            data_outputs TEXT, analysis_workflow TEXT,
            statistical_design TEXT, figure_logic_patterns TEXT,
            reporting_checklist TEXT, reusable_research_patterns TEXT,
            operation_reference_points TEXT, researchos_trigger_questions TEXT,
            related_methods TEXT, limitations TEXT
        );
    """)
    cur.execute(
        """INSERT INTO papers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("p1", "Western Blot Protocol", 2023, "Nature Protocols",
         "10.1038/...", "Nature", "Nature Protocols",
         "txt", "tier_1_high_impact", "deep", "Published 2023",
         1, 1, 0, "recent_five_years",
         "western_blot", "protocol", 0.85, ""),
    )
    cur.execute(
        "INSERT INTO method_records VALUES (?,?,?,?,?,?,?,?)",
        ("p1", "western_blot", '["standard_wb"]', "摘要", "高灵敏度检测",
         "适用范围", '["蛋白"]', '["western"]'),
    )
    cur.execute(
        "INSERT INTO evidence_items VALUES (?,?,?,?,?,?,?)",
        (1, "p1", "SDS-PAGE分离", "separated by SDS-PAGE",
         "methods", "protocol_step", 0.9),
    )
    cur.execute(
        """INSERT INTO deep_learning_fields VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("p1", "高灵敏度", "掌握WB", "适用范围",
         '["Step1"]', '["param1"]', '["QC1"]',
         '[]', '[]', '[]', '[]',
         '流程', '统计',
         '["Fig1"]', '["Checklist"]',
         '["Template"]',
         '["op1"]',
         '["Q1"]',
         '["Related"]', '["Limitation1"]'),
    )
    conn.commit()
    conn.close()


class TestQueryCLI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp.name, "test_kb.sqlite")
        _build_test_db(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _run(self, *args):
        cmd = [sys.executable, _QUERY_SCRIPT, "--sqlite-path", self.db_path]
        cmd.extend(args)
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    def test_query_by_category(self):
        r = self._run("--category", "western_blot")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Western Blot Protocol", r.stdout)
        self.assertIn("Found 1 result", r.stdout)

    def test_query_by_keyword(self):
        r = self._run("--query", "Western")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Western Blot Protocol", r.stdout)

    def test_query_recent_only(self):
        r = self._run("--recent-only")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Western Blot Protocol", r.stdout)

    def test_query_verbose(self):
        r = self._run("--category", "western_blot", "--verbose")
        self.assertEqual(r.returncode, 0)
        self.assertIn("QC Points", r.stdout)

    def test_query_json_output(self):
        r = self._run("--category", "western_blot", "--json")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Western Blot Protocol")

    def test_query_paper_id(self):
        r = self._run("--paper-id", "p1")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Western Blot Protocol", r.stdout)

    def test_query_evidence(self):
        r = self._run("--evidence-for", "p1")
        self.assertEqual(r.returncode, 0)
        self.assertIn("SDS-PAGE分离", r.stdout)

    def test_query_missing_db(self):
        r = subprocess.run(
            [sys.executable, _QUERY_SCRIPT, "--sqlite-path", "/nonexistent/db.sqlite"],
            capture_output=True, text=True, timeout=30,
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Error", r.stderr)

    def test_query_animal_subcategory(self):
        r = self._run("--animal-subcategory", "dosing")
        self.assertEqual(r.returncode, 0)

    def test_query_omics_subcategory(self):
        r = self._run("--omics-subcategory", "transcriptomics")
        self.assertEqual(r.returncode, 0)

    def test_query_no_results(self):
        r = self._run("--query", "nonexistent_keyword_xyz")
        self.assertEqual(r.returncode, 0)
        self.assertIn("No results found", r.stdout)


if __name__ == "__main__":
    unittest.main()

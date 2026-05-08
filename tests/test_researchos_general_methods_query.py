"""Tests for the General Methods KB query service.

Uses a real in-memory SQLite database built from scratch.
No real papers or LLM required.
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest

from researchos_learning_engine.general_methods_kb.query_service import (
    get_evidence_for_paper,
    get_record,
    list_animal_experiment_records,
    list_omics_records,
    query_by_category,
    query_by_keyword,
    query_general_methods_kb,
    query_operation_reference,
    query_recent_five_years,
)


def _build_test_db(db_path=":memory:"):
    """Create a SQLite test database with sample records and Phase 3 columns.

    Args:
        db_path: Path for the database. Default ":memory:" for in-memory.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
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

    # Insert papers with all columns (20 columns including new Phase 3 fields)
    papers = [
        ("p1", "Western Blot Protocol", 2023, "Nature Protocols",
         "10.1038/s41596-023-00001", "Nature", "Nature Protocols",
         "txt", "tier_1_high_impact", "deep", "Published 2023",
         1, 1, 0, "recent_five_years",
         "western_blot", "foundational_protocol", 0.85, ""),
        ("p2", "Animal Model for Cancer", 2022, "Nature",
         "10.1038/s41586-022-00002", "Nature", "Nature",
         "txt", "tier_1_high_impact", "deep", "Published 2022",
         1, 1, 0, "recent_five_years",
         "animal_experiment", "representative_high_impact_case", 0.80, ""),
        ("p3", "RNA-seq Analysis Pipeline", 2021, "Cell",
         "10.1016/j.cell.2021-00003", "Cell", "Cell",
         "txt", "tier_1_high_impact", "deep", "Published 2021",
         1, 1, 0, "recent_five_years",
         "omics_metabolomics_transcriptomics_proteomics",
         "data_analysis_workflow", 0.75, ""),
        ("p4", "Old Method Paper", 2015, "Science",
         "10.1126/science.2015-00004", "Science", "Science",
         "txt", "tier_1_high_impact", "standard", "Foundational review",
         0, 1, 1, "classic_foundational",
         "western_blot", "review", 0.50, ""),
    ]
    for p in papers:
        cur.execute(
            """INSERT INTO papers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            p,
        )

    # Insert method records
    cur.execute(
        "INSERT INTO method_records VALUES (?,?,?,?,?,?,?,?)",
        ("p1", "western_blot", '["standard_wb"]', "摘要", "高灵敏度蛋白检测",
         "适用于细胞裂解液", '["蛋白检测"]', '["western blot"]'),
    )
    cur.execute(
        "INSERT INTO method_records VALUES (?,?,?,?,?,?,?,?)",
        ("p2", "animal_experiment",
         '["dosing", "tissue_collection"]', "小鼠肿瘤模型",
         "小鼠肿瘤模型建立方法", "适用于皮下移植瘤",
         '["动物模型"]', '["animal model"]'),
    )
    cur.execute(
        "INSERT INTO method_records VALUES (?,?,?,?,?,?,?,?)",
        ("p3", "omics_metabolomics_transcriptomics_proteomics",
         '["transcriptomics", "metabolomics"]', "RNA-seq",
         "标准RNA-seq分析流程", "适用于转录组数据",
         '["RNA-seq"]', '["transcriptomics"]'),
    )
    cur.execute(
        "INSERT INTO method_records VALUES (?,?,?,?,?,?,?,?)",
        ("p4", "western_blot", '[]', "综述", "经典方法回顾",
         "方法学背景", "[]", "[]"),
    )

    # Insert evidence items
    evidence = [
        ("p1", "SDS-PAGE分离蛋白", "Proteins were separated", "methods",
         "protocol_step", 0.9),
        ("p1", "转膜到PVDF膜", "transferred to PVDF", "methods",
         "protocol_step", 0.85),
        ("p2", "小鼠皮下注射", "subcutaneous injection", "methods",
         "protocol_step", 0.8),
        ("p2", "肿瘤体积测量", "tumor volume was measured", "results",
         "data_analysis", 0.75),
    ]
    for ev in evidence:
        cur.execute(
            "INSERT INTO evidence_items (paper_id, claim, short_quote, section, evidence_type, confidence) VALUES (?,?,?,?,?,?)",
            ev,
        )

    # Insert deep learning fields
    cur.execute(
        """INSERT INTO deep_learning_fields VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("p1", "高灵敏度蛋白检测方法",
         "掌握Western Blot标准操作流程",
         "适用于细胞裂解液和组织样本",
         '["Sample prep", "SDS-PAGE", "Transfer", "Blocking", "Antibody incubation", "Detection"]',
         '["Temperature", "Time", "Antibody concentration"]',
         '["Positive control", "Negative control", "MW marker"]',
         '[]', '[]', '[]', '[]',
         '采集→分析→可视化', '三重复实验',
         '["Figure 1: protocol schematic"]', '["Antibody info", "Buffer composition"]',
         '["Standard WB template"]',
         '["Blocking step", "Wash step"]',
         '["How to reduce background?", "What antibody dilution?"]',
         '["Standard WB"]', '["Only for protein samples"]'),
    )
    cur.execute(
        """INSERT INTO deep_learning_fields VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("p2", "小鼠肿瘤模型建立方法",
         "掌握异位肿瘤模型建立",
         "适用于免疫缺陷小鼠",
         '["Tumor cell injection", "Tumor growth monitoring"]',
         '["Cell number", "Matrigel ratio", "Injection volume"]',
         '["Body weight", "Tumor size caliper"]',
         '["Detailed injection log"]', '["Tumor ulceration"]', '["Warm matrigel"]',
         '["Tumor size", "Body weight"]', '监测→测量→分析', '每组8只',
         '["Fig 2: growth curve"]', '["Animal welfare approval"]',
         '["Xenograft template"]',
         '["Anesthesia step", "Injection point"]',
         '["How to avoid tumor ulceration?"]',
         '["Xenograft model"]', '["Only for subcutaneous model"]'),
    )
    cur.execute(
        """INSERT INTO deep_learning_fields VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("p3", "转录组分析流程",
         "标准差异表达分析",
         "适用于bulk RNA-seq数据",
         '["Quality check", "Alignment", "Count", "DE analysis"]',
         '["p-value", "Fold change", "MAPQ"]',
         '["Sequence quality", "Mapping rate"]',
         '[]', '["Batch effect"]', '["Use RUVseq"]',
         '["Count matrix", "QC report"]',
         'FastQC→STAR→featureCounts→DESeq2',
         'FDR < 0.05, |log2FC| > 1',
         '["Fig 3: PCA", "Fig 4: Heatmap"]',
         '["Software versions"]',
         '["Bulk RNA-seq template"]',
         '["QC step", "DE cutoffs"]',
         '["What is the mapping rate?", "How many DEGs?"]',
         '["Bulk RNA-seq"]', '["Requires high quality RNA"]'),
    )

    conn.commit()
    return conn


class TestQueryService(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.db_path = self.tmp.name
        self.tmp.close()
        _build_test_db(self.db_path)

    def tearDown(self):
        import os
        if os.path.isfile(self.db_path):
            os.unlink(self.db_path)

    def test_query_by_category(self):
        results = query_by_category(self.db_path, "western_blot")
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertEqual(r["method_category"], "western_blot")

    def test_query_by_category_no_match(self):
        results = query_by_category(self.db_path, "flow_cytometry")
        self.assertEqual(results, [])

    def test_query_by_keyword(self):
        results = query_by_keyword(self.db_path, "Western")
        self.assertGreaterEqual(len(results), 1)
        titles = [r["title"] for r in results]
        self.assertIn("Western Blot Protocol", titles)

    def test_query_by_keyword_cn(self):
        results = query_by_keyword(self.db_path, "肿瘤")
        self.assertGreaterEqual(len(results), 1)

    def test_query_recent_five_years(self):
        results = query_recent_five_years(self.db_path)
        self.assertEqual(len(results), 3)  # p1, p2, p3
        for r in results:
            self.assertIsNotNone(r["year"])
            self.assertGreaterEqual(r["year"], 2021)

    def test_query_recent_five_years_with_category(self):
        results = query_recent_five_years(self.db_path, category="western_blot")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Western Blot Protocol")

    def test_query_operation_reference(self):
        results = query_operation_reference(self.db_path, "SDS-PAGE")
        self.assertGreaterEqual(len(results), 1)

    def test_get_record(self):
        r = get_record(self.db_path, "p1")
        self.assertIsNotNone(r)
        self.assertEqual(r["title"], "Western Blot Protocol")
        self.assertEqual(r["method_category"], "western_blot")
        self.assertIn("evidence_items", r)
        self.assertGreaterEqual(len(r["evidence_items"]), 2)
        self.assertIn("operation_reference_points", r)
        self.assertIn("Blocking step", r["operation_reference_points"])

    def test_get_record_not_found(self):
        r = get_record(self.db_path, "nonexistent")
        self.assertIsNone(r)

    def test_get_evidence_for_paper(self):
        items = get_evidence_for_paper(self.db_path, "p1")
        self.assertGreaterEqual(len(items), 2)
        types = {i["evidence_type"] for i in items}
        self.assertIn("protocol_step", types)

    def test_get_evidence_empty(self):
        items = get_evidence_for_paper(self.db_path, "p4")
        self.assertEqual(items, [])

    def test_list_animal_experiment_records(self):
        results = list_animal_experiment_records(self.db_path)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["method_category"], "animal_experiment")

    def test_list_animal_experiment_with_subcategory(self):
        results = list_animal_experiment_records(
            self.db_path, subcategory="dosing",
        )
        self.assertEqual(len(results), 1)

    def test_list_animal_experiment_subcategory_no_match(self):
        results = list_animal_experiment_records(
            self.db_path, subcategory="xenograft_nonexistent",
        )
        self.assertEqual(results, [])

    def test_list_omics_records(self):
        results = list_omics_records(self.db_path)
        self.assertEqual(len(results), 1)
        self.assertIn("omics", results[0]["method_category"])

    def test_list_omics_with_subcategory(self):
        results = list_omics_records(self.db_path, subcategory="transcriptomics")
        self.assertEqual(len(results), 1)

    def test_list_omics_subcategory_no_match(self):
        results = list_omics_records(self.db_path, subcategory="lipidomics")
        self.assertEqual(results, [])

    def test_invalid_db_path(self):
        with self.assertRaises(FileNotFoundError):
            query_by_category("/nonexistent/path.sqlite", "test")

    def test_result_fields_present(self):
        results = query_by_category(self.db_path, "animal_experiment")
        self.assertEqual(len(results), 1)
        r = results[0]
        expected_fields = {
            "title", "journal", "year", "doi", "source_family",
            "source_journal_group", "source_tier", "learning_depth",
            "publication_age_group", "is_recent_five_years",
            "method_category", "method_subcategories",
            "article_role", "methodological_learning_value_cn",
            "confidence_score", "operation_reference_points",
            "quality_control_points", "researchos_trigger_questions",
            "evidence_items", "core_protocol_steps",
        }
        self.assertTrue(expected_fields.issubset(r.keys()),
                        f"Missing fields: {expected_fields - set(r.keys())}")

    def test_unified_query_by_keyword(self):
        results = query_general_methods_kb(self.db_path, query="Western")
        self.assertGreaterEqual(len(results), 1)

    def test_unified_query_by_category(self):
        results = query_general_methods_kb(
            self.db_path, query="", category="western_blot",
        )
        self.assertEqual(len(results), 2)

    def test_unified_query_recent_only(self):
        results = query_general_methods_kb(
            self.db_path, query="", recent_only=True,
        )
        self.assertEqual(len(results), 3)

    def test_unified_query_recent_with_category(self):
        results = query_general_methods_kb(
            self.db_path, query="",
            category="western_blot", recent_only=True,
        )
        self.assertEqual(len(results), 1)

    def test_source_tier_in_results(self):
        """Phase 3: source_tier should be present in query results."""
        results = query_by_category(self.db_path, "western_blot")
        for r in results:
            self.assertIn("source_tier", r)
            self.assertIn("learning_depth", r)
            self.assertIn("publication_age_group", r)

    def test_is_recent_five_years_boolean(self):
        """Phase 3: is_recent_five_years should be a bool, not int."""
        results = query_recent_five_years(self.db_path)
        for r in results:
            self.assertIsInstance(r["is_recent_five_years"], bool)


if __name__ == "__main__":
    unittest.main()

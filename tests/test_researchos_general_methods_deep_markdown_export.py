"""Tests for deep learning markdown export functions."""

from __future__ import annotations

import os
import tempfile
import unittest

from researchos_learning_engine.general_methods_kb.export_service import (
    export_animal_experiment_methods_summary_md,
    export_omics_methods_summary_md,
    export_recent_five_years_deep_learning_md,
)
from researchos_learning_engine.general_methods_kb.schemas import (
    BuildRunRecord,
    DeepLearningFields,
    MethodKnowledgeRecord,
)


def _make_record(
    paper_id: str,
    title: str = "Test Paper",
    year: int = 2023,
    journal: str = "Nature Methods",
    category: str = "animal_experiment",
    subcategories=None,
    doi: str = "10.1038/s41592-023-00000-0",
    with_deep: bool = True,
) -> MethodKnowledgeRecord:
    dl = None
    if with_deep:
        dl = DeepLearningFields(
            high_impact_value_cn="这是一篇高价值方法学文章",
            what_researchos_should_learn_cn="学习其实验设计思路",
            applicable_scenarios_cn="适用于蛋白检测实验",
            core_protocol_steps=["样品制备", "抗体孵育", "信号检测", "数据分析"],
            critical_parameters=["温度", "时间", "浓度"],
            quality_control_points=["阳性对照", "阴性对照"],
            analysis_workflow="采集→分析→可视化",
            figure_logic_patterns=["图1展示原理", "图2展示验证"],
            reusable_research_patterns=["可作为SOP模板"],
            limitations=["仅适用于特定样品"],
        )
    return MethodKnowledgeRecord(
        paper_id=paper_id,
        title=title,
        year=year,
        journal=journal,
        doi=doi,
        source_family="Nature",
        method_category=category,
        method_subcategories=subcategories or [],
        deep_learning=dl,
    )


class TestDeepMarkdownExport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.outdir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_recent_five_years_export(self):
        records = [
            _make_record("p1", "Recent Paper", year=2023),
            _make_record("p2", "Old Paper", year=2015, with_deep=False),
        ]
        path = export_recent_five_years_deep_learning_md(records, self.outdir)
        self.assertTrue(os.path.isfile(path))
        with open(path) as f:
            content = f.read()
        self.assertIn("Recent Paper", content)
        self.assertIn("Deep Learning Report", content)
        self.assertNotIn("Old Paper", content)

    def test_recent_five_years_empty(self):
        records = [
            _make_record("p1", "Old Paper", year=2015, with_deep=False),
        ]
        path = export_recent_five_years_deep_learning_md(records, self.outdir)
        self.assertTrue(os.path.isfile(path))

    def test_animal_experiment_export(self):
        records = [
            _make_record("p1", "Animal Paper", category="animal_experiment",
                         subcategories=["dosing", "tissue_collection"]),
            _make_record("p2", "Western Paper", category="western_blot"),
        ]
        path = export_animal_experiment_methods_summary_md(records, self.outdir)
        self.assertTrue(os.path.isfile(path))
        with open(path) as f:
            content = f.read()
        self.assertIn("Animal Paper", content)
        self.assertNotIn("Western Paper", content)
        self.assertIn("Animal Experiment Methods", content)

    def test_animal_experiment_empty(self):
        records = [
            _make_record("p1", "Western Paper", category="western_blot"),
        ]
        path = export_animal_experiment_methods_summary_md(records, self.outdir)
        self.assertTrue(os.path.isfile(path))

    def test_omics_export(self):
        records = [
            _make_record("p1", "Omics Paper",
                         category="omics_metabolomics_transcriptomics_proteomics",
                         subcategories=["metabolomics", "transcriptomics"]),
            _make_record("p2", "Cell Paper", category="cell_culture"),
        ]
        path = export_omics_methods_summary_md(records, self.outdir)
        self.assertTrue(os.path.isfile(path))
        with open(path) as f:
            content = f.read()
        self.assertIn("Omics Paper", content)
        self.assertIn("Omics Methods", content)

    def test_omics_empty(self):
        records = [
            _make_record("p1", "Cell Paper", category="cell_culture"),
        ]
        path = export_omics_methods_summary_md(records, self.outdir)
        self.assertTrue(os.path.isfile(path))

    def test_no_records_at_all(self):
        """All three exports should handle empty list gracefully."""
        path1 = export_recent_five_years_deep_learning_md([], self.outdir)
        path2 = export_animal_experiment_methods_summary_md([], self.outdir)
        path3 = export_omics_methods_summary_md([], self.outdir)
        for p in (path1, path2, path3):
            self.assertTrue(os.path.isfile(p))


if __name__ == "__main__":
    unittest.main()

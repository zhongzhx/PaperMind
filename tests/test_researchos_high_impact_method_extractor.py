"""Tests for the high-impact method extractor pipeline."""

from __future__ import annotations

import json
import unittest

from researchos_learning_engine.general_methods_kb.high_impact_method_extractor import (
    HighImpactMethodExtractor,
)
from researchos_learning_engine.general_methods_kb.schemas import DeepLearningFields


class _DeepMockLLM:
    """Mock LLM that returns deep extraction results."""

    def __init__(self, fail=False):
        self._fail = fail

    def generate_json(self, system_prompt="", user_message="", temperature=0.3, max_tokens=4096):
        if self._fail:
            raise ValueError("Mock LLM failure")
        if "deep method extraction" in system_prompt.lower():
            return {
                "high_impact_value_cn": "深度学习方法学价值",
                "what_researchos_should_learn_cn": "值得学习的实验设计",
                "applicable_scenarios_cn": "适用场景描述",
                "core_protocol_steps": ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"],
                "critical_parameters": ["温度", "时间", "浓度"],
                "quality_control_points": ["阳性对照", "阴性对照", "重复性验证"],
                "reproducibility_points": ["详细记录参数", "内部标准"],
                "common_pitfalls": ["非特异性结合", "信号太弱"],
                "troubleshooting_hints": ["增加洗涤次数"],
                "data_outputs": ["原始信号", "标准曲线"],
                "analysis_workflow": "数据采集→分析→可视化",
                "statistical_design": "三重复，t检验",
                "figure_logic_patterns": ["图1展示方法原理"],
                "reporting_checklist": ["材料来源", "仪器型号"],
                "reusable_research_patterns": ["剂量反应设计"],
                "operation_reference_points": ["关键时间节点"],
                "researchos_trigger_questions": ["如何提高灵敏度?"],
                "related_methods": ["Western blot"],
                "limitations": ["仅适用于特定样品"],
            }
        elif "standard method extraction" in system_prompt.lower():
            return {
                "high_impact_value_cn": "经典方法学框架",
                "what_researchos_should_learn_cn": "基本原理和实验设计",
                "applicable_scenarios_cn": "方法学背景参考",
                "core_protocol_steps": ["准备试剂", "执行操作", "数据分析"],
                "limitations": ["技术更新较快"],
            }
        elif "evidence" in system_prompt.lower():
            return {
                "evidence_items": [
                    {
                        "claim": "方法灵敏度高",
                        "short_quote": "high sensitivity was achieved",
                        "section": "results",
                        "evidence_type": "parameter",
                        "confidence": 0.9,
                    },
                ],
            }
        return {}


class TestHighImpactMethodExtractor(unittest.TestCase):
    def test_extract_recent_paper(self):
        extractor = HighImpactMethodExtractor(_DeepMockLLM())
        deep_fields, evidence, warnings = extractor.extract(
            text="Paper content here",
            metadata={"title": "Test Paper", "journal": "Nature Methods", "doi": "10.xxx"},
            year=2023,
        )
        self.assertIsNotNone(deep_fields)
        self.assertEqual(deep_fields.high_impact_value_cn, "深度学习方法学价值")
        self.assertEqual(len(deep_fields.core_protocol_steps), 5)
        self.assertGreater(len(evidence), 0)

    def test_extract_older_paper(self):
        extractor = HighImpactMethodExtractor(_DeepMockLLM())
        deep_fields, evidence, warnings = extractor.extract(
            text="Old paper content",
            metadata={"title": "Old Paper", "journal": "Nature"},
            year=2015,
        )
        self.assertIsNotNone(deep_fields)
        self.assertEqual(deep_fields.high_impact_value_cn, "经典方法学框架")
        # Light extraction should have 5 core fields, others "not_reported"
        self.assertEqual(len(deep_fields.core_protocol_steps), 3)
        self.assertEqual(deep_fields.analysis_workflow, "not_reported")

    def test_extract_no_year(self):
        extractor = HighImpactMethodExtractor(_DeepMockLLM())
        deep_fields, evidence, warnings = extractor.extract(
            text="Paper content",
            metadata={"title": "Paper"},
            year=None,
        )
        # No year → treat as not recent → light extraction
        self.assertIsNotNone(deep_fields)
        # Light extraction produces warnings for missing list fields
        self.assertGreater(len(warnings), 0)

    def test_extract_failure_returns_empty_fields(self):
        """On LLM failure, extract returns empty DeepLearningFields (not None)."""
        extractor = HighImpactMethodExtractor(_DeepMockLLM(fail=True))
        deep_fields, evidence, warnings = extractor.extract(
            text="Content",
            metadata={"title": "Paper"},
            year=2023,
        )
        self.assertIsNotNone(deep_fields)
        self.assertIsInstance(deep_fields, DeepLearningFields)
        self.assertEqual(deep_fields.high_impact_value_cn, "not_reported")

    def test_extract_with_defaults_on_failure(self):
        """extract_with_defaults also returns empty fields on LLM failure."""
        extractor = HighImpactMethodExtractor(_DeepMockLLM(fail=True))
        deep_fields, evidence, warnings = extractor.extract_with_defaults(
            text="Content",
            metadata={"title": "Paper"},
            year=2023,
        )
        self.assertIsNotNone(deep_fields)
        self.assertIsInstance(deep_fields, DeepLearningFields)
        self.assertEqual(deep_fields.high_impact_value_cn, "not_reported")

    def test_extract_collects_warnings_for_missing_fields(self):
        extractor = HighImpactMethodExtractor(_DeepMockLLM())
        # Use a custom mock that returns empty data
        class _EmptyMockLLM:
            def generate_json(self, **kwargs):
                return {}

        empty_extractor = HighImpactMethodExtractor(_EmptyMockLLM())
        deep_fields, evidence, warnings = empty_extractor.extract(
            text="Content",
            metadata={"title": "Paper"},
            year=2023,
        )
        self.assertIsNotNone(deep_fields)
        # Should have warnings about missing fields
        self.assertGreater(len(warnings), 0)

    def test_recent_boundary(self):
        """Papers at exactly RECENT_YEAR_BOUNDARY should be treated as recent."""
        extractor = HighImpactMethodExtractor(_DeepMockLLM())
        deep_fields, evidence, warnings = extractor.extract(
            text="Content",
            metadata={"title": "Paper"},
            year=2021,
        )
        self.assertIsNotNone(deep_fields)
        self.assertEqual(deep_fields.high_impact_value_cn, "深度学习方法学价值")


if __name__ == "__main__":
    unittest.main()

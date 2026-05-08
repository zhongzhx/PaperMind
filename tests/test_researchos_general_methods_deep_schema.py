"""Tests for deep learning schemas (DeepLearningFields, EvidenceType)."""

from __future__ import annotations

import json
import unittest

from researchos_learning_engine.general_methods_kb.schemas import (
    DeepLearningFields,
    EvidenceItem,
    EvidenceType,
    MethodKnowledgeRecord,
)


class TestEvidenceType(unittest.TestCase):
    def test_values(self):
        self.assertEqual(EvidenceType.PROTOCOL_STEP.value, "protocol_step")
        self.assertEqual(EvidenceType.PARAMETER.value, "parameter")
        self.assertEqual(EvidenceType.QUALITY_CONTROL.value, "quality_control")
        self.assertEqual(EvidenceType.REPORTING_STANDARD.value, "reporting_standard")
        self.assertEqual(EvidenceType.EXPERIMENTAL_DESIGN.value, "experimental_design")
        self.assertEqual(EvidenceType.DATA_ANALYSIS.value, "data_analysis")
        self.assertEqual(EvidenceType.FIGURE_LOGIC.value, "figure_logic")
        self.assertEqual(EvidenceType.LIMITATION.value, "limitation")
        self.assertEqual(EvidenceType.REUSABLE_PATTERN.value, "reusable_pattern")

    def test_all_types_count(self):
        self.assertEqual(len(EvidenceType), 9)


class TestDeepLearningFields(unittest.TestCase):
    def test_defaults(self):
        dl = DeepLearningFields()
        self.assertEqual(dl.high_impact_value_cn, "")
        self.assertEqual(dl.core_protocol_steps, [])
        self.assertEqual(dl.analysis_workflow, "")

    def test_round_trip(self):
        dl = DeepLearningFields(
            high_impact_value_cn="高价值测试",
            core_protocol_steps=["Step 1", "Step 2", "Step 3"],
            quality_control_points=["QC1", "QC2"],
            limitations=["Limitation 1"],
        )
        d = dl.to_dict()
        restored = DeepLearningFields.from_dict(d)
        self.assertEqual(restored.high_impact_value_cn, "高价值测试")
        self.assertEqual(len(restored.core_protocol_steps), 3)
        self.assertEqual(len(restored.quality_control_points), 2)
        self.assertEqual(restored.limitations, ["Limitation 1"])

    def test_json_serializable(self):
        dl = DeepLearningFields(high_impact_value_cn="测试", core_protocol_steps=["Step"])
        text = json.dumps(dl.to_dict(), ensure_ascii=False)
        data = json.loads(text)
        self.assertEqual(data["high_impact_value_cn"], "测试")
        self.assertEqual(data["core_protocol_steps"], ["Step"])

    def test_all_fields_present_in_dict(self):
        dl = DeepLearningFields()
        d = dl.to_dict()
        expected_keys = {
            "high_impact_value_cn", "what_researchos_should_learn_cn",
            "applicable_scenarios_cn", "core_protocol_steps",
            "critical_parameters", "quality_control_points",
            "reproducibility_points", "common_pitfalls",
            "troubleshooting_hints", "data_outputs",
            "analysis_workflow", "statistical_design",
            "figure_logic_patterns", "reporting_checklist",
            "reusable_research_patterns", "operation_reference_points",
            "researchos_trigger_questions", "related_methods",
            "limitations",
        }
        self.assertEqual(set(d.keys()), expected_keys)

    def test_from_dict_missing_fields(self):
        dl = DeepLearningFields.from_dict({"high_impact_value_cn": "test"})
        self.assertEqual(dl.high_impact_value_cn, "test")
        self.assertEqual(dl.core_protocol_steps, [])


class TestMethodKnowledgeRecordWithDeep(unittest.TestCase):
    def test_deep_learning_default_none(self):
        rec = MethodKnowledgeRecord()
        self.assertIsNone(rec.deep_learning)

    def test_deep_learning_round_trip(self):
        dl = DeepLearningFields(
            high_impact_value_cn="高价值",
            core_protocol_steps=["Step A", "Step B"],
        )
        rec = MethodKnowledgeRecord(
            paper_id="test_001",
            title="Test Paper",
            year=2023,
            deep_learning=dl,
        )
        d = rec.to_dict()
        restored = MethodKnowledgeRecord.from_dict(d)
        self.assertIsNotNone(restored.deep_learning)
        self.assertEqual(restored.deep_learning.high_impact_value_cn, "高价值")
        self.assertEqual(len(restored.deep_learning.core_protocol_steps), 2)

    def test_deep_learning_in_json(self):
        dl = DeepLearningFields(high_impact_value_cn="测试")
        rec = MethodKnowledgeRecord(paper_id="t1", title="T", deep_learning=dl)
        text = json.dumps(rec.to_dict(), ensure_ascii=False)
        data = json.loads(text)
        self.assertIn("deep_learning", data)
        self.assertEqual(data["deep_learning"]["high_impact_value_cn"], "测试")

    def test_deep_learning_none_in_json(self):
        rec = MethodKnowledgeRecord(paper_id="t1", title="T")
        d = rec.to_dict()
        self.assertIsNone(d["deep_learning"])


if __name__ == "__main__":
    unittest.main()

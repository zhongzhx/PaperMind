"""Tests for the General Methods KB schemas."""

from __future__ import annotations

import json
import unittest

from researchos_learning_engine.general_methods_kb.schemas import (
    BuildRunRecord,
    EvidenceItem,
    MethodKnowledgeRecord,
    SourceFamily,
    SourceType,
)


class TestSourceFamily(unittest.TestCase):
    def test_values(self):
        self.assertEqual(SourceFamily.NATURE.value, "Nature")
        self.assertEqual(SourceFamily.SCIENCE.value, "Science")
        self.assertEqual(SourceFamily.CELL.value, "Cell")


class TestSourceType(unittest.TestCase):
    def test_values(self):
        self.assertEqual(SourceType.PDF.value, "pdf")
        self.assertEqual(SourceType.TXT.value, "txt")
        self.assertEqual(SourceType.MD.value, "md")
        self.assertEqual(SourceType.UNKNOWN.value, "unknown")


class TestEvidenceItem(unittest.TestCase):
    def test_defaults(self):
        item = EvidenceItem()
        self.assertEqual(item.claim, "")
        self.assertEqual(item.confidence, 0.0)

    def test_round_trip(self):
        item = EvidenceItem(
            claim="Testing shows X",
            short_quote="X is significant",
            section="results",
            page_ref="p5",
            chunk_id="chunk_01",
            evidence_type="statistical",
            confidence=0.85,
        )
        d = item.to_dict()
        restored = EvidenceItem.from_dict(d)
        self.assertEqual(restored.claim, "Testing shows X")
        self.assertEqual(restored.confidence, 0.85)

    def test_json_serializable(self):
        item = EvidenceItem(claim="Test", confidence=0.9)
        text = json.dumps(item.to_dict(), ensure_ascii=False)
        self.assertIn("Test", text)
        self.assertIn("0.9", text)


class TestMethodKnowledgeRecord(unittest.TestCase):
    def test_defaults(self):
        rec = MethodKnowledgeRecord()
        self.assertEqual(rec.paper_id, "")
        self.assertEqual(rec.authors, [])
        self.assertIsNone(rec.year)
        # Phase 3 new fields
        self.assertEqual(rec.source_tier, "")
        self.assertEqual(rec.learning_depth, "")
        self.assertEqual(rec.publication_age_group, "")
        self.assertTrue(rec.is_user_provided)
        self.assertFalse(rec.is_classic_foundational)

    def test_round_trip(self):
        rec = MethodKnowledgeRecord(
            paper_id="gmkb_test_001",
            title="Test Paper Title",
            authors=["Author A", "Author B"],
            year=2023,
            journal="Nature Methods",
            doi="10.1038/s41592-023-00000-0",
            source_family="Nature",
            source_journal_group="Nature Methods",
            source_type="pdf",
            # Phase 3 new fields
            source_tier="tier_1_high_impact",
            journal_tier="Nature Methods",
            learning_depth="deep",
            learning_reason="Published 2023 (within recent 2021+ window)",
            is_recent_five_years=True,
            is_user_provided=True,
            is_classic_foundational=False,
            publication_age_group="recent_five_years",
            method_category="western_blot",
            method_subcategories=["protein_detection"],
            article_role="foundational_protocol",
            abstract_summary_cn="测试摘要",
            methodological_learning_value_cn="学习方法论",
            method_scope_cn="western blot 方法",
            retrieval_keywords_cn=["western blot", "蛋白质检测"],
            retrieval_keywords_en=["western blot", "protein detection"],
            confidence_score=0.85,
            extraction_warnings=["No DOI found"],
            evidence_items=[
                EvidenceItem(claim="Claim 1", confidence=0.9),
            ],
        )
        d = rec.to_dict()
        restored = MethodKnowledgeRecord.from_dict(d)
        self.assertEqual(restored.paper_id, "gmkb_test_001")
        self.assertEqual(restored.year, 2023)
        self.assertEqual(restored.source_family, "Nature")
        self.assertEqual(restored.source_tier, "tier_1_high_impact")
        self.assertEqual(restored.learning_depth, "deep")
        self.assertEqual(restored.publication_age_group, "recent_five_years")
        self.assertEqual(len(restored.evidence_items), 1)
        self.assertEqual(restored.evidence_items[0].claim, "Claim 1")
        self.assertEqual(restored.retrieval_keywords_cn, ["western blot", "蛋白质检测"])

    def test_json_serializable(self):
        rec = MethodKnowledgeRecord(
            paper_id="test_001",
            title="Test",
            evidence_items=[EvidenceItem(claim="Ev")],
        )
        text = json.dumps(rec.to_dict(), ensure_ascii=False)
        data = json.loads(text)
        self.assertEqual(data["paper_id"], "test_001")
        self.assertEqual(len(data["evidence_items"]), 1)

    def test_forward_compat_ignores_unknown_fields(self):
        d = {
            "paper_id": "test",
            "title": "Test",
            "unknown_field": "should be ignored",
            "unknown_nested": {"a": 1},
        }
        rec = MethodKnowledgeRecord.from_dict(d)
        self.assertEqual(rec.paper_id, "test")
        self.assertEqual(rec.title, "Test")

    def test_from_dict_missing_fields(self):
        rec = MethodKnowledgeRecord.from_dict({})
        self.assertEqual(rec.paper_id, "")

    def test_source_tier_default(self):
        rec = MethodKnowledgeRecord()
        self.assertEqual(rec.source_tier, "")

    def test_learning_depth_default(self):
        rec = MethodKnowledgeRecord()
        self.assertEqual(rec.learning_depth, "")


class TestBuildRunRecord(unittest.TestCase):
    def test_defaults(self):
        rec = BuildRunRecord()
        self.assertEqual(rec.status, "completed")
        self.assertEqual(rec.engine_version, "0.1.0")
        # Phase 3 new fields
        self.assertEqual(rec.records_by_source_tier, {})
        self.assertEqual(rec.records_by_publication_age_group, {})
        self.assertEqual(rec.records_by_learning_depth, {})
        self.assertEqual(rec.records_by_category, {})

    def test_round_trip(self):
        rec = BuildRunRecord(
            build_id="build_001",
            started_at="2024-01-01T00:00:00",
            completed_at="2024-01-01T01:00:00",
            input_dir="/input",
            output_dir="/output",
            total_files_found=50,
            files_processed=30,
            files_skipped=15,
            files_failed=3,
            files_uncertain_source=2,
            files_uncertain_metadata=2,
            records_by_source_tier={"tier_1_high_impact": 10, "tier_3_standard_peer_reviewed": 5},
            records_by_publication_age_group={"recent_five_years": 8, "classic_foundational": 7},
            records_by_learning_depth={"deep": 8, "standard": 7},
            records_by_category={"western_blot": 5, "animal_experiment": 10},
            status="completed",
        )
        d = rec.to_dict()
        restored = BuildRunRecord.from_dict(d)
        self.assertEqual(restored.build_id, "build_001")
        self.assertEqual(restored.files_processed, 30)
        self.assertEqual(restored.files_uncertain_metadata, 2)
        self.assertEqual(restored.records_by_source_tier["tier_1_high_impact"], 10)
        self.assertEqual(restored.records_by_learning_depth["deep"], 8)

    def test_json_serializable(self):
        rec = BuildRunRecord(build_id="b1", status="completed")
        text = json.dumps(rec.to_dict(), ensure_ascii=False)
        self.assertIn("b1", text)

    def test_aggregate_stats_defaults(self):
        rec = BuildRunRecord()
        d = rec.to_dict()
        self.assertEqual(d.get("records_by_source_tier"), {})
        self.assertEqual(d.get("records_by_category"), {})


if __name__ == "__main__":
    unittest.main()

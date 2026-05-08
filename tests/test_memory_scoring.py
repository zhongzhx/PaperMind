"""Tests for the memory scoring engine."""

from __future__ import annotations

import unittest

from researchos_learning_engine.domain.constants import (
    EvidenceLevel,
    MemoryStatus,
    MemoryType,
)
from researchos_learning_engine.domain.schemas import MemoryRecord
from researchos_learning_engine.domain.scoring import (
    assign_memory_status,
    compute_memory_health_score,
    compute_recency_score,
    score_and_update_memory,
)


class TestRecencyScore(unittest.TestCase):
    def test_recent_memory_high_score(self):
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        score = compute_recency_score(now)
        self.assertGreater(score, 0.95)

    def test_old_memory_low_score(self):
        score = compute_recency_score("2023-01-01T00:00:00+00:00")
        self.assertLess(score, 0.1)

    def test_none_timestamp_returns_default(self):
        score = compute_recency_score(None)
        self.assertEqual(score, 0.5)

    def test_future_timestamp_returns_max(self):
        score = compute_recency_score("2030-01-01T00:00:00+00:00")
        self.assertEqual(score, 1.0)


class TestMemoryHealthScore(unittest.TestCase):
    def test_high_confidence_memory(self):
        mem = MemoryRecord(
            memory_id="test_high",
            project_id="p1",
            memory_type=MemoryType.PAPER_EVIDENCE,
            content="High quality evidence",
            confidence=0.95,
            importance=0.9,
            project_relevance=0.95,
            evidence_level=EvidenceLevel.L5,
            retrieval_count=50,
            contradiction_count=0,
            status=MemoryStatus.ACTIVE,
        )
        score, breakdown = compute_memory_health_score(mem)
        self.assertGreaterEqual(score, 0.7)
        self.assertEqual(breakdown.final_score, score)
        self.assertEqual(breakdown.raw_components["source_confidence"], 0.95)

    def test_low_confidence_memory(self):
        mem = MemoryRecord(
            memory_id="test_low",
            project_id="p1",
            memory_type=MemoryType.USER_FACT,
            content="Random thought",
            confidence=0.05,
            importance=0.1,
            project_relevance=0.05,
            evidence_level=EvidenceLevel.L0,
            retrieval_count=0,
            contradiction_count=3,
            status=MemoryStatus.NORMAL,
        )
        score, breakdown = compute_memory_health_score(mem)
        self.assertLess(score, 0.3)
        self.assertGreater(breakdown.contradiction_penalty, 0)

    def test_score_breakdown_components(self):
        mem = MemoryRecord(
            memory_id="test_breakdown",
            project_id="p1",
            memory_type=MemoryType.DECISION,
            content="Important decision",
            confidence=0.8,
            importance=0.8,
            project_relevance=0.8,
            evidence_level=EvidenceLevel.L3,
            retrieval_count=5,
            contradiction_count=0,
            status=MemoryStatus.ACTIVE,
        )
        _, breakdown = compute_memory_health_score(mem)
        self.assertGreaterEqual(breakdown.source_confidence, 0)
        self.assertGreaterEqual(breakdown.user_confirmation, 0)
        self.assertGreaterEqual(breakdown.project_relevance, 0)
        self.assertGreaterEqual(breakdown.evidence_support, 0)
        self.assertGreaterEqual(breakdown.retrieval_usefulness, 0)
        self.assertGreaterEqual(breakdown.recency, 0)
        self.assertGreaterEqual(breakdown.contradiction_penalty, 0)
        self.assertGreaterEqual(breakdown.redundancy_penalty, 0)

    def test_score_clamped_to_zero_one(self):
        mem = MemoryRecord(
            memory_id="test_clamp",
            project_id="p1",
            memory_type=MemoryType.PAPER_EVIDENCE,
            content="Perfect memory",
            confidence=2.0,
            importance=2.0,
            project_relevance=2.0,
            evidence_level=EvidenceLevel.L5,
            retrieval_count=1000,
            contradiction_count=0,
            status=MemoryStatus.ACTIVE,
        )
        score, _ = compute_memory_health_score(mem)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_score_and_update_memory(self):
        mem = MemoryRecord(
            memory_id="test_update",
            project_id="p1",
            memory_type=MemoryType.PROJECT_FACT,
            content="Test memory",
            confidence=0.5,
            importance=0.5,
            project_relevance=0.5,
            evidence_level=EvidenceLevel.L2,
            retrieval_count=3,
            contradiction_count=0,
            status=MemoryStatus.NORMAL,
        )
        updated = score_and_update_memory(mem)
        self.assertGreater(updated.health_score, 0)
        self.assertIsNotNone(updated.score_breakdown)
        self.assertEqual(updated.score_breakdown.final_score, updated.health_score)


class TestAssignMemoryStatus(unittest.TestCase):
    def test_active_threshold(self):
        self.assertEqual(assign_memory_status(0.80), MemoryStatus.ACTIVE)
        self.assertEqual(assign_memory_status(0.75), MemoryStatus.ACTIVE)

    def test_normal_threshold(self):
        self.assertEqual(assign_memory_status(0.60), MemoryStatus.NORMAL)
        self.assertEqual(assign_memory_status(0.45), MemoryStatus.NORMAL)

    def test_archived_threshold(self):
        self.assertEqual(assign_memory_status(0.30), MemoryStatus.ARCHIVED)
        self.assertEqual(assign_memory_status(0.20), MemoryStatus.ARCHIVED)

    def test_deprecated_threshold(self):
        self.assertEqual(assign_memory_status(0.10), MemoryStatus.DEPRECATED)
        self.assertEqual(assign_memory_status(0.0), MemoryStatus.DEPRECATED)

    def test_boundary_values(self):
        self.assertEqual(assign_memory_status(0.75), MemoryStatus.ACTIVE)
        self.assertEqual(assign_memory_status(0.45), MemoryStatus.NORMAL)
        self.assertEqual(assign_memory_status(0.20), MemoryStatus.ARCHIVED)

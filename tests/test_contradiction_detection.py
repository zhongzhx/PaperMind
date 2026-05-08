"""Tests for contradiction detection service."""

from __future__ import annotations

import unittest

from researchos_learning_engine.application.contradiction_service import (
    ContradictionService,
)
from researchos_learning_engine.domain.constants import EvidenceLevel, MemoryType
from researchos_learning_engine.domain.schemas import MemoryRecord


class TestRuleBasedContradiction(unittest.TestCase):
    def setUp(self):
        self.service = ContradictionService()

    def test_increase_decrease_contradiction(self):
        mem_a = MemoryRecord(
            memory_id="mem_a",
            project_id="p1",
            memory_type=MemoryType.PAPER_EVIDENCE,
            content="Treatment A increases cell proliferation.",
            confidence=0.8,
            evidence_level=EvidenceLevel.L2,
        )
        mem_b = MemoryRecord(
            memory_id="mem_b",
            project_id="p1",
            memory_type=MemoryType.PAPER_EVIDENCE,
            content="Treatment A decreases cell proliferation.",
            confidence=0.8,
            evidence_level=EvidenceLevel.L2,
        )
        result = self.service.detect_rule_based(mem_a, mem_b)
        self.assertNotEqual(result["severity"], "none")

    def test_activate_suppress_contradiction(self):
        mem_a = MemoryRecord(
            memory_id="mem_c",
            project_id="p1",
            memory_type=MemoryType.PAPER_EVIDENCE,
            content="Factor X activates transcription of target genes.",
        )
        mem_b = MemoryRecord(
            memory_id="mem_d",
            project_id="p1",
            memory_type=MemoryType.PAPER_EVIDENCE,
            content="Factor X suppresses transcription of target genes.",
        )
        result = self.service.detect_rule_based(mem_a, mem_b)
        self.assertNotEqual(result["severity"], "none")

    def test_no_contradiction_for_similar_content(self):
        mem_a = MemoryRecord(
            memory_id="mem_e",
            project_id="p1",
            memory_type=MemoryType.PAPER_EVIDENCE,
            content="Enzyme A is a key regulator in pathway B.",
        )
        mem_b = MemoryRecord(
            memory_id="mem_f",
            project_id="p1",
            memory_type=MemoryType.PAPER_EVIDENCE,
            content="Enzyme A is highly expressed in certain conditions.",
        )
        result = self.service.detect_rule_based(mem_a, mem_b)
        self.assertEqual(result["severity"], "none")

    def test_no_contradiction_for_unrelated_content(self):
        mem_a = MemoryRecord(
            memory_id="mem_g",
            project_id="p1",
            memory_type=MemoryType.PAPER_EVIDENCE,
            content="ATP production is important for cell survival.",
        )
        mem_b = MemoryRecord(
            memory_id="mem_h",
            project_id="p1",
            memory_type=MemoryType.PAPER_EVIDENCE,
            content="The cellular environment changes during development.",
        )
        result = self.service.detect_rule_based(mem_a, mem_b)
        self.assertEqual(result["severity"], "none")

    def test_scan_project_memories(self):
        mems = [
            MemoryRecord(
                memory_id="m1",
                project_id="p1",
                memory_type=MemoryType.PAPER_EVIDENCE,
                content="Treatment X activates the pathway.",
            ),
            MemoryRecord(
                memory_id="m2",
                project_id="p1",
                memory_type=MemoryType.PAPER_EVIDENCE,
                content="Treatment X suppresses the pathway.",
            ),
            MemoryRecord(
                memory_id="m3",
                project_id="p1",
                memory_type=MemoryType.PAPER_EVIDENCE,
                content="Cell viability is normal.",
            ),
        ]
        results = self.service.scan_project_memories(mems, use_llm=False)
        self.assertGreaterEqual(len(results), 1)
        found_pair = {results[0]["memory_a"], results[0]["memory_b"]}
        self.assertEqual(found_pair, {"m1", "m2"})


class TestContradictionResolution(unittest.TestCase):
    def setUp(self):
        self.service = ContradictionService()

    def test_older_memory_superseded(self):
        mem_a = MemoryRecord(
            memory_id="m1",
            project_id="p1",
            memory_type=MemoryType.PAPER_EVIDENCE,
            content="Treatment X activates the pathway.",
            health_score=0.8,
        )
        mem_b = MemoryRecord(
            memory_id="m2",
            project_id="p1",
            memory_type=MemoryType.PAPER_EVIDENCE,
            content="Treatment X suppresses the pathway.",
            health_score=0.3,
        )
        contradictions = [
            {
                "memory_a": "m1",
                "memory_b": "m2",
                "severity": "medium",
                "description": "Test contradiction",
            }
        ]
        memories = self.service.resolve_contradictions(contradictions, [mem_a, mem_b])
        mem_map = {m.memory_id: m for m in memories}
        self.assertEqual(mem_map["m2"].status.value, "superseded")

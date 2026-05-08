"""Tests for evidence normalizer module."""

from __future__ import annotations

import json
import unittest

from researchos_learning_engine.general_methods_kb.evidence_normalizer import (
    EvidenceNormalizer,
    _MAX_EVIDENCE_ITEMS,
    _MAX_SHORT_QUOTE_CHARS,
)
from researchos_learning_engine.general_methods_kb.schemas import EvidenceItem, EvidenceType


class _MockLLM:
    """Minimal mock LLM for testing evidence extraction."""

    def generate_json(self, system_prompt="", user_message="", temperature=0.3, max_tokens=4096):
        return {
            "evidence_items": [
                {
                    "claim": "Mock claim from LLM",
                    "short_quote": "LLM extracted quote",
                    "section": "results",
                    "evidence_type": "data_analysis",
                    "confidence": 0.85,
                },
            ],
        }


class TestEvidenceNormalizer(unittest.TestCase):
    def setUp(self):
        self.normalizer = EvidenceNormalizer()

    def test_empty_text(self):
        items = self.normalizer.extract("", {})
        self.assertEqual(items, [])

    def test_protocol_steps_extraction(self):
        text = "1. Prepare the samples by centrifugation at 3000g for 10 min.\n2. Incubate with primary antibody at 4°C overnight.\n3. Wash three times with PBST."
        items = self.normalizer.extract(text, {})
        self.assertGreater(len(items), 0)
        self.assertEqual(items[0].evidence_type, "protocol_step")

    def test_qc_points_extraction(self):
        text = "Positive and negative controls were included in each experiment. A standard curve was generated for quantification."
        items = self.normalizer.extract(text, {})
        qc_items = [i for i in items if i.evidence_type == "quality_control"]
        self.assertGreater(len(qc_items), 0)

    def test_parameter_extraction(self):
        text = "The incubation temperature was 37°C. Centrifugation at 12000g for 15 minutes."
        items = self.normalizer.extract(text, {})
        param_items = [i for i in items if i.evidence_type == "parameter"]
        self.assertGreater(len(param_items), 0)

    def test_deduplication(self):
        text = "1. Prepare samples. 1. Prepare samples. 1. Prepare samples."
        items = self.normalizer.extract(text, {})
        # Dedup should collapse similar items
        self.assertLessEqual(len(items), 2)

    def test_max_items_limit(self):
        text = "\n".join(f"{i}. Step number {i} of the protocol with details." for i in range(1, 50))
        items = self.normalizer.extract(text, {})
        self.assertLessEqual(len(items), _MAX_EVIDENCE_ITEMS)

    def test_llm_extraction(self):
        normalizer = EvidenceNormalizer(llm=_MockLLM())
        items = normalizer.extract("Some paper text", {}, is_recent=True)
        # Should have LLM items
        llm_items = [i for i in items if i.confidence == 0.85]
        self.assertGreater(len(llm_items), 0)

    def test_evidence_item_has_evidence_type(self):
        text = "1. Centrifuge at 3000g for 10 minutes."
        items = self.normalizer.extract(text, {})
        for item in items:
            self.assertTrue(isinstance(item.evidence_type, str))
            self.assertGreater(len(item.evidence_type), 0)

    def test_short_quote_truncated(self):
        long_text = "A" * (_MAX_SHORT_QUOTE_CHARS + 100)
        text = f"1. {long_text}"
        items = self.normalizer.extract(text, {})
        for item in items:
            self.assertLessEqual(len(item.short_quote), _MAX_SHORT_QUOTE_CHARS)

    def test_evidence_item_confidence_range(self):
        """All evidence items should have confidence in [0, 1]."""
        text = "1. Step one. 2. Step two. Positive control was used."
        items = self.normalizer.extract(text, {})
        for item in items:
            self.assertGreaterEqual(item.confidence, 0.0)
            self.assertLessEqual(item.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()

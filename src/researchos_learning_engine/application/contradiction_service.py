"""Contradiction detection service.

Detects contradictions between memory records within the same project.
Uses both rule-based heuristics and optional LLM-based semantic analysis.
"""

from __future__ import annotations

import re
from typing import Any

from researchos_learning_engine.adapters.llm.base import LLMAdapter
from researchos_learning_engine.domain.constants import MemoryStatus
from researchos_learning_engine.domain.schemas import MemoryRecord


# Simple negation patterns for rule-based contradiction detection
NEGATION_PATTERNS: list[tuple[str, str]] = [
    # (positive_pattern, negative_pattern)
    (r"\bincreases?\b", r"\bdecreases?\b"),
    (r"\benhances?\b", r"\binhibits?\b"),
    (r"\bactivates?\b", r"\bsuppresses?\b"),
    (r"\bpromotes?\b", r"\bprevents?\b"),
    (r"\bupregulat", r"\bdownregulat"),
    (r"\bpositive", r"\bnegative"),
    (r"\bpresence\b", r"\babsence\b"),
    (r"\brequired?\b", r"\bdispensable?\b"),
    (r"\bessential\b", r"\bnon-essential\b"),
    (r"\bsignificant", r"\bno significant"),
    (r"\bcorrelates?\b", r"\bdoes not correlate"),
]


CONTRADICTION_SYSTEM_PROMPT = """You are a contradiction detection system for scientific research memories.
Given two memory records from the same project, determine if they contradict each other.

Return JSON with:
- contradiction_detected: true/false
- severity: "high" / "medium" / "low" / "none"
- description: explanation of the contradiction (or empty if none)
- conflicting_aspects: list of specific conflicting claims"""


class ContradictionService:
    """Detect contradictions between memory records."""

    def __init__(self, llm: LLMAdapter | None = None) -> None:
        self._llm = llm

    def detect_rule_based(
        self, mem_a: MemoryRecord, mem_b: MemoryRecord
    ) -> dict[str, Any]:
        """Rule-based contradiction detection using lexical negation pairs."""
        content_a = mem_a.content.lower()
        content_b = mem_b.content.lower()

        for pos_pat, neg_pat in NEGATION_PATTERNS:
            has_pos_in_a = bool(re.search(pos_pat, content_a))
            has_neg_in_a = bool(re.search(neg_pat, content_a))
            has_pos_in_b = bool(re.search(pos_pat, content_b))
            has_neg_in_b = bool(re.search(neg_pat, content_b))

            # One memory uses positive form, the other uses negation
            if (has_pos_in_a and has_neg_in_b) or (has_neg_in_a and has_pos_in_b):
                return {
                    "memory_a": mem_a.memory_id,
                    "memory_b": mem_b.memory_id,
                    "description": (
                        f"Rule-based contradiction detected: "
                        f"pattern '{pos_pat}' vs '{neg_pat}'"
                    ),
                    "severity": "medium",
                    "detection_method": "rule_based",
                }

        return {
            "memory_a": mem_a.memory_id,
            "memory_b": mem_b.memory_id,
            "contradiction_detected": False,
            "severity": "none",
            "detection_method": "rule_based",
        }

    def detect_llm_based(
        self, mem_a: MemoryRecord, mem_b: MemoryRecord
    ) -> dict[str, Any]:
        """LLM-based semantic contradiction detection."""
        if not self._llm:
            return {
                "memory_a": mem_a.memory_id,
                "memory_b": mem_b.memory_id,
                "contradiction_detected": False,
                "severity": "none",
                "detection_method": "llm_skipped_no_adapter",
            }

        user_message = (
            f"Memory A ({mem_a.memory_id}): {mem_a.content}\n\n"
            f"Memory B ({mem_b.memory_id}): {mem_b.content}\n\n"
            f"Context: Both are from project '{mem_a.project_id}'."
        )

        result = self._llm.generate_json(
            system_prompt=CONTRADICTION_SYSTEM_PROMPT,
            user_message=user_message,
            temperature=0.2,
            max_tokens=1024,
        )

        result["memory_a"] = mem_a.memory_id
        result["memory_b"] = mem_b.memory_id
        result["detection_method"] = "llm_based"
        return result

    def scan_project_memories(
        self,
        memories: list[MemoryRecord],
        use_llm: bool = False,
    ) -> list[dict[str, Any]]:
        """Scan all memory pairs in a project for contradictions.

        Args:
            memories: All memory records for the project.
            use_llm: Whether to use LLM-based detection in addition to rules.

        Returns:
            List of contradiction results.
        """
        contradictions: list[dict[str, Any]] = []
        checked_pairs: set[tuple[str, str]] = set()

        for i, mem_a in enumerate(memories):
            for j, mem_b in enumerate(memories):
                if i >= j:
                    continue

                pair_key = tuple(sorted([mem_a.memory_id, mem_b.memory_id]))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)

                # Rule-based detection first
                rule_result = self.detect_rule_based(mem_a, mem_b)
                if rule_result.get("severity") != "none":
                    contradictions.append(rule_result)
                    continue

                # Optional LLM detection
                if use_llm:
                    llm_result = self.detect_llm_based(mem_a, mem_b)
                    if llm_result.get("severity") != "none":
                        llm_result["detection_method"] = "llm_based"
                        contradictions.append(llm_result)

        return contradictions

    def resolve_contradictions(
        self,
        contradictions: list[dict[str, Any]],
        memories: list[MemoryRecord],
    ) -> list[MemoryRecord]:
        """Mark superseded memories based on detected contradictions.

        Simple heuristic: the older (or lower-scored) memory in a
        contradiction pair gets marked as superseded.
        """
        mem_map = {m.memory_id: m for m in memories}
        superseded_ids: set[str] = set()

        for c in contradictions:
            if c.get("severity") in ("none", None):
                continue
            mem_a_id = c.get("memory_a", "")
            mem_b_id = c.get("memory_b", "")
            mem_a = mem_map.get(mem_a_id)
            mem_b = mem_map.get(mem_b_id)
            if mem_a is None or mem_b is None:
                continue
            # Older memory gets superseded
            if mem_a.health_score <= mem_b.health_score:
                superseded_ids.add(mem_a_id)
            else:
                superseded_ids.add(mem_b_id)

        for m in memories:
            if m.memory_id in superseded_ids and m.status != MemoryStatus.SUPERSEDED:
                m.status = MemoryStatus.SUPERSEDED

        return memories

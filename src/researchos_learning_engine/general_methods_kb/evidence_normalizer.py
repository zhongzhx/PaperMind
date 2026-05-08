"""Evidence extraction and normalization for method knowledge records.

Supports both rule-based extraction (numbered lists, QC mentions)
and LLM-based extraction for richer results.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Set

from researchos_learning_engine.general_methods_kb.schemas import (
    EvidenceItem,
    EvidenceType,
)

_MAX_SHORT_QUOTE_CHARS = 200
_MAX_EVIDENCE_ITEMS = 20


# ---------------------------------------------------------------------------
# Rule-based extraction patterns
# ---------------------------------------------------------------------------

_PROTOCOL_STEP_PATTERN = re.compile(
    r"(?:\d+[\.\)]\s*)([A-Z][^\.]+(?:\.[^\.]+){0,2})",
    re.MULTILINE,
)

_QC_PATTERNS = [
    r"(?:quality control|QC|internal control|positive control|negative control)",
    r"(?:calibration|standard curve|normalization)",
    r"(?:reproducibility|technical replicate|biological replicate)",
    r"(?:limit of detection|LOD|limit of quantification|LOQ)",
    r"(?:signal.?to.?noise|S/N ratio|background signal)",
]

_PARAMETER_PATTERNS = [
    r"(?:incubation|temperature|concentration|dilution|ratio)\s*(?::|is|was|of)\s*\d+",
    r"(?:pH|voltage|current|flow rate|pressure)\s*(?::|is|was|of)\s*\d+",
    r"(?:centrifug(?:ation|e)|speed|g-force)\s*(?::|at|of)\s*\d+",
]


class EvidenceNormalizer:
    """Extracts, normalizes, and deduplicates evidence items from paper text."""

    def __init__(self, llm: Optional[Any] = None) -> None:
        self._llm = llm

    def extract(
        self,
        text: str,
        metadata: Dict[str, Any],
        is_recent: bool = False,
    ) -> List[EvidenceItem]:
        """Extract evidence items from paper text.

        Uses rule-based extraction as baseline; if LLM is available,
        supplements with LLM-based extraction and deduplicates.
        """
        items: List[EvidenceItem] = []

        # Rule-based extraction
        items.extend(self._extract_protocol_steps(text))
        items.extend(self._extract_qc_points(text))
        items.extend(self._extract_parameters(text))

        # LLM-based extraction (richer, for recent papers)
        if self._llm is not None and is_recent:
            llm_items = self._extract_via_llm(text)
            items.extend(llm_items)

        # Deduplicate and limit
        items = self._deduplicate(items)
        items = items[:_MAX_EVIDENCE_ITEMS]
        return items

    def _extract_protocol_steps(self, text: str) -> List[EvidenceItem]:
        """Extract numbered protocol steps as evidence items."""
        items: List[EvidenceItem] = []
        seen: Set[str] = set()
        for m in _PROTOCOL_STEP_PATTERN.finditer(text[:10000]):
            claim = m.group(1).strip()[:150]
            if not claim or len(claim) < 15:
                continue
            dedup_key = claim[:50].lower()
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            items.append(EvidenceItem(
                claim=claim,
                short_quote=claim[:100],
                section="methods",
                evidence_type=EvidenceType.PROTOCOL_STEP.value,
                confidence=0.7,
            ))
        return items

    def _extract_qc_points(self, text: str) -> List[EvidenceItem]:
        """Extract quality control mentions as evidence items."""
        items: List[EvidenceItem] = []
        seen: Set[str] = set()
        lower = text[:10000].lower()
        for pattern in _QC_PATTERNS:
            for m in re.finditer(pattern, lower):
                # Grab surrounding context
                start = max(0, m.start() - 40)
                end = min(len(lower), m.end() + 60)
                context = lower[start:end].strip()
                dedup_key = context[:60]
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)
                items.append(EvidenceItem(
                    claim=f"Quality control: {context[:120]}",
                    short_quote=context[:_MAX_SHORT_QUOTE_CHARS],
                    section="methods",
                    evidence_type=EvidenceType.QUALITY_CONTROL.value,
                    confidence=0.75,
                ))
        return items

    def _extract_parameters(self, text: str) -> List[EvidenceItem]:
        """Extract parameter mentions as evidence items."""
        items: List[EvidenceItem] = []
        seen: Set[str] = set()
        for pattern in _PARAMETER_PATTERNS:
            for m in re.finditer(pattern, text[:10000], re.IGNORECASE):
                match_text = m.group(0).strip()
                dedup_key = match_text[:60].lower()
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)
                items.append(EvidenceItem(
                    claim=f"Parameter: {match_text[:120]}",
                    short_quote=match_text[:_MAX_SHORT_QUOTE_CHARS],
                    section="methods",
                    evidence_type=EvidenceType.PARAMETER.value,
                    confidence=0.65,
                ))
        return items

    def _extract_via_llm(self, text: str) -> List[EvidenceItem]:
        """Extract evidence items via LLM."""
        try:
            result = self._llm.generate_json(
                system_prompt=(
                    "You are an evidence extractor for biomedical methods papers. "
                    "Extract evidence items as a JSON object with key 'evidence_items' "
                    "containing a list of dicts with keys: claim, short_quote, section, "
                    "evidence_type, confidence."
                ),
                user_message=f"Extract evidence from this paper:\n\n{text[:5000]}",
            )
            raw_items = result.get("evidence_items", []) if isinstance(result, dict) else []
            items: List[EvidenceItem] = []
            for item in raw_items:
                if not isinstance(item, dict):
                    continue
                items.append(EvidenceItem(
                    claim=str(item.get("claim", ""))[:200],
                    short_quote=str(item.get("short_quote", ""))[:_MAX_SHORT_QUOTE_CHARS],
                    section=str(item.get("section", "")),
                    evidence_type=str(item.get("evidence_type", "")),
                    confidence=float(item.get("confidence", 0.5)),
                ))
            return items
        except Exception:
            return []

    def _deduplicate(self, items: List[EvidenceItem]) -> List[EvidenceItem]:
        """Deduplicate evidence items with similar claims."""
        seen: Set[str] = set()
        deduped: List[EvidenceItem] = []
        for item in items:
            key = item.claim[:80].lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

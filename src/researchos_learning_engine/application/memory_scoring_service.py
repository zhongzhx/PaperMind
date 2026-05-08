"""Memory scoring service — scores all memories and assigns lifecycle status.

Uses the rule-based scoring engine from domain.scoring. This service
orchestrates the scoring of multiple memory records, producing the
consolidation output categories (promoted, archived, deprecated, etc.).
"""

from __future__ import annotations

from researchos_learning_engine.domain.constants import MemoryStatus
from researchos_learning_engine.domain.schemas import MemoryRecord
from researchos_learning_engine.domain.scoring import score_and_update_memory


class MemoryScoringService:
    """Service for batch memory scoring and status assignment."""

    def score_all(self, memories: list[MemoryRecord]) -> list[MemoryRecord]:
        """Score all memories and return updated records.

        Scoring is deterministic and rule-based — no LLM calls needed.
        """
        return [score_and_update_memory(m) for m in memories]

    def categorize_by_status_change(
        self,
        original: list[MemoryRecord],
        updated: list[MemoryRecord],
    ) -> tuple[list[MemoryRecord], list[MemoryRecord], list[MemoryRecord]]:
        """Compare original vs updated statuses to find promoted/archived/superseded.

        Returns:
            Tuple of (promoted_memories, archived_memories, superseded_memories)
        """
        original_map = {m.memory_id: m.status for m in original}
        updated_map = {m.memory_id: m for m in updated}

        promoted: list[MemoryRecord] = []
        archived: list[MemoryRecord] = []
        superseded: list[MemoryRecord] = []

        status_rank = {
            MemoryStatus.DEPRECATED: 0,
            MemoryStatus.ARCHIVED: 1,
            MemoryStatus.NORMAL: 2,
            MemoryStatus.ACTIVE: 3,
            MemoryStatus.SUPERSEDED: 0,
        }

        for mem_id, original_status in original_map.items():
            if mem_id not in updated_map:
                continue
            updated_mem = updated_map[mem_id]
            new_status = updated_mem.status

            if new_status == MemoryStatus.SUPERSEDED and original_status != MemoryStatus.SUPERSEDED:
                superseded.append(updated_mem)
            elif status_rank.get(new_status, 0) > status_rank.get(original_status, 0):
                promoted.append(updated_mem)
            elif new_status in (MemoryStatus.ARCHIVED, MemoryStatus.DEPRECATED) and status_rank.get(new_status, 0) < status_rank.get(original_status, 0):
                archived.append(updated_mem)

        return promoted, archived, superseded

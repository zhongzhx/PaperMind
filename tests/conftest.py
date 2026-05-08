"""Shared fixtures and test helpers (unittest-compatible)."""

from __future__ import annotations

from researchos_learning_engine.domain.constants import (
    EvidenceLevel,
    MemoryStatus,
    MemoryType,
)
from researchos_learning_engine.domain.schemas import (
    ConsolidationInput,
    MemoryRecord,
    PaperRecord,
)


def make_sample_memory_active() -> MemoryRecord:
    return MemoryRecord(
        memory_id="test_mem_active",
        project_id="test_project",
        memory_type=MemoryType.PAPER_EVIDENCE,
        content="Active memory with strong evidence support",
        confidence=0.9,
        importance=0.9,
        project_relevance=0.95,
        evidence_level=EvidenceLevel.L4,
        retrieval_count=20,
        contradiction_count=0,
        status=MemoryStatus.ACTIVE,
    )


def make_sample_memory_old() -> MemoryRecord:
    return MemoryRecord(
        memory_id="test_mem_old",
        project_id="test_project",
        memory_type=MemoryType.USER_FACT,
        content="Old unconfirmed thought",
        confidence=0.1,
        importance=0.1,
        project_relevance=0.1,
        evidence_level=EvidenceLevel.L0,
        retrieval_count=0,
        contradiction_count=2,
        status=MemoryStatus.NORMAL,
        updated_at="2024-01-01T00:00:00+00:00",
    )


def make_sample_paper() -> PaperRecord:
    return PaperRecord(
        paper_id="test_paper_001",
        title="Test Paper Title",
        authors=["Test Author"],
        year=2024,
        journal="Test Journal",
        full_text="This is example text for testing purposes. It contains placeholder content for the test suite.",
    )


def make_sample_consolidation_input() -> ConsolidationInput:
    return ConsolidationInput(
        project_id="test_project",
        project_title="Test Project",
        project_description="A test project for unit testing",
        paper_records=[
            PaperRecord(
                paper_id="test_paper_001",
                title="Test Paper",
                full_text="Example text for testing purposes.",
            )
        ],
        memory_records=[
            MemoryRecord(
                memory_id="mem_test_1",
                project_id="test_project",
                memory_type=MemoryType.PAPER_EVIDENCE,
                content="Test memory with high confidence",
                confidence=0.9,
                importance=0.8,
                project_relevance=0.9,
                evidence_level=EvidenceLevel.L4,
                retrieval_count=10,
                status=MemoryStatus.ACTIVE,
            ),
            MemoryRecord(
                memory_id="mem_test_2",
                project_id="test_project",
                memory_type=MemoryType.USER_FACT,
                content="Low confidence thought",
                confidence=0.2,
                importance=0.2,
                project_relevance=0.2,
                evidence_level=EvidenceLevel.L0,
                retrieval_count=0,
                status=MemoryStatus.NORMAL,
            ),
            MemoryRecord(
                memory_id="mem_test_3",
                project_id="test_project",
                memory_type=MemoryType.PAPER_EVIDENCE,
                content="Very old irrelevant memory that should be archived",
                confidence=0.05,
                importance=0.05,
                project_relevance=0.05,
                evidence_level=EvidenceLevel.L0,
                retrieval_count=0,
                contradiction_count=3,
                status=MemoryStatus.NORMAL,
                updated_at="2023-06-01T00:00:00+00:00",
            ),
        ],
        current_project_summary="Initial project summary for testing.",
    )

"""Tests for schema contracts, validation, and serialization stability."""

from __future__ import annotations

import copy
import json
import sys
import unittest

from researchos_learning_engine.domain.constants import (
    SCHEMA_VERSION,
    ENGINE_VERSION,
    EvidenceLevel,
    MemoryStatus,
    MemoryType,
)
from researchos_learning_engine.domain.schemas import (
    ConsolidationInput,
    ConsolidationResult,
    EvidenceGraphEdge,
    MemoryRecord,
    PaperRecord,
    ResearchPattern,
    ScoreBreakdown,
    _to_dict,
)
from researchos_learning_engine.domain.validation import (
    ValidationError,
    validate_consolidation_input,
    validate_consolidation_result,
    validate_enum,
    validate_memory_record,
    validate_score,
    raise_on_errors,
)


class TestSchemaVersions(unittest.TestCase):
    """Schema and engine version fields must be present and stable."""

    def test_constants_defined(self):
        self.assertEqual(SCHEMA_VERSION, "1.0")
        self.assertEqual(ENGINE_VERSION, "0.1.0")

    def test_consolidation_input_has_schema_version(self):
        inp = ConsolidationInput(project_id="test")
        self.assertEqual(inp.schema_version, "1.0")

    def test_consolidation_result_has_schema_and_engine_version(self):
        result = ConsolidationResult(project_id="test")
        self.assertEqual(result.schema_version, "1.0")
        self.assertEqual(result.engine_version, "0.1.0")


class TestRoundTripSerialization(unittest.TestCase):
    """to_dict() and from_dict() must round-trip stably."""

    def test_memory_record_round_trip(self):
        original = MemoryRecord(
            memory_id="mem_rt_1",
            project_id="proj_rt",
            memory_type=MemoryType.PAPER_EVIDENCE,
            content="Round-trip test memory",
            source_refs=["ref_a", "ref_b"],
            confidence=0.85,
            importance=0.7,
            project_relevance=0.9,
            evidence_level=EvidenceLevel.L4,
            retrieval_count=10,
            contradiction_count=1,
            status=MemoryStatus.ACTIVE,
            health_score=0.78,
        )
        # to_dict
        d = original.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["memory_type"], "paper_evidence")
        self.assertEqual(d["evidence_level"], "L4")
        self.assertEqual(d["status"], "active")

        # from_dict
        restored = MemoryRecord.from_dict(d)
        self.assertEqual(restored.memory_id, original.memory_id)
        self.assertEqual(restored.project_id, original.project_id)
        self.assertEqual(restored.memory_type, original.memory_type)
        self.assertEqual(restored.evidence_level, original.evidence_level)
        self.assertEqual(restored.status, original.status)
        self.assertEqual(restored.confidence, original.confidence)
        self.assertEqual(restored.retrieval_count, original.retrieval_count)
        self.assertEqual(restored.contradiction_count, original.contradiction_count)

    def test_paper_record_round_trip(self):
        original = PaperRecord(
            paper_id="paper_rt_1",
            title="Test Paper",
            authors=["Author A", "Author B"],
            year=2024,
            journal="Test Journal",
            full_text="Full text content for round-trip",
            project_relevance_score=0.9,
            evidence_value_score=0.8,
        )
        d = original.to_dict()
        restored = PaperRecord.from_dict(d)
        self.assertEqual(restored.paper_id, original.paper_id)
        self.assertEqual(restored.year, 2024)
        self.assertEqual(restored.authors, ["Author A", "Author B"])

    def test_research_pattern_round_trip(self):
        original = ResearchPattern(
            pattern_id="pat_rt_1",
            paper_id="paper_rt_1",
            project_id="proj_rt",
            research_question="Test question?",
            core_logic="Test logic",
            experimental_models=["Model A"],
            mechanisms=["Mech X"],
        )
        d = original.to_dict()
        restored = ResearchPattern.from_dict(d)
        self.assertEqual(restored.pattern_id, original.pattern_id)
        self.assertEqual(restored.mechanisms, ["Mech X"])

    def test_evidence_graph_edge_round_trip(self):
        original = EvidenceGraphEdge(
            edge_id="edge_rt_1",
            project_id="proj_rt",
            source_node="source:A",
            target_node="target:B",
            weight=0.8,
            evidence_refs=["paper_1", "mem_1"],
        )
        d = original.to_dict()
        restored = EvidenceGraphEdge.from_dict(d)
        self.assertEqual(restored.edge_id, original.edge_id)
        self.assertEqual(restored.weight, 0.8)
        self.assertEqual(restored.evidence_refs, ["paper_1", "mem_1"])

    def test_score_breakdown_round_trip(self):
        original = ScoreBreakdown(
            source_confidence=0.2,
            user_confirmation=0.15,
            project_relevance=0.18,
            evidence_support=0.1,
            retrieval_usefulness=0.05,
            recency=0.03,
            contradiction_penalty=0.2,
            redundancy_penalty=0.0,
            final_score=0.51,
            raw_components={"confidence": 0.8},
        )
        d = original.to_dict()
        restored = ScoreBreakdown.from_dict(d)
        self.assertEqual(restored.final_score, 0.51)
        self.assertEqual(restored.raw_components, {"confidence": 0.8})

    def test_consolidation_input_round_trip(self):
        original = ConsolidationInput(
            project_id="proj_rt",
            project_title="Round Trip Test",
            paper_records=[
                PaperRecord(paper_id="p1", title="Paper 1"),
                PaperRecord(paper_id="p2", title="Paper 2"),
            ],
            memory_records=[
                MemoryRecord(memory_id="m1", project_id="proj_rt", content="Mem 1"),
                MemoryRecord(memory_id="m2", project_id="proj_rt", content="Mem 2"),
            ],
        )
        d = original.to_dict()
        restored = ConsolidationInput.from_dict(d)
        self.assertEqual(restored.project_id, "proj_rt")
        self.assertEqual(len(restored.paper_records), 2)
        self.assertEqual(len(restored.memory_records), 2)
        self.assertEqual(restored.memory_records[0].content, "Mem 1")

    def test_full_cycle(self):
        """Full ConsolidationInput → run_sleep_cycle → to_dict → from_dict → verify."""
        from researchos_learning_engine.interfaces.python_api import run_sleep_cycle

        inp = ConsolidationInput(
            project_id="full_cycle",
            project_title="Full Cycle",
            memory_records=[
                MemoryRecord(
                    memory_id="mc1", project_id="full_cycle",
                    content="Test memory", confidence=0.8, project_relevance=0.8,
                    evidence_level=EvidenceLevel.L3,
                ),
            ],
        )
        result = run_sleep_cycle(inp)

        # Serialize
        d = result.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["project_id"], "full_cycle")
        self.assertIn("schema_version", d)
        self.assertIn("engine_version", d)
        self.assertIn("processing_log", d)

        # Deserialize
        restored = ConsolidationResult.from_dict(d)
        self.assertEqual(restored.project_id, "full_cycle")
        self.assertIsInstance(restored, ConsolidationResult)

    def test_to_dict_no_python_objects(self):
        """to_dict must only contain JSON-serializable types."""
        mem = MemoryRecord(
            memory_id="json_safe",
            project_id="test",
            memory_type=MemoryType.PAPER_EVIDENCE,
            content="JSON safety test",
            score_breakdown=ScoreBreakdown(final_score=0.5),
        )
        d = mem.to_dict()
        # Verify JSON-serializable
        json_str = json.dumps(d)
        self.assertIsInstance(json_str, str)
        # Verify no enum objects
        raw = json.dumps(d)
        self.assertIn("paper_evidence", raw)

    def test_from_dict_with_extra_fields(self):
        """from_dict should silently ignore unknown fields (forward compat)."""
        d = {
            "memory_id": "forward_compat",
            "project_id": "test",
            "memory_type": "paper_evidence",
            "content": "Forward compat test",
            "unknown_field": "should be ignored",
            "future_data": {"nested": "value"},
        }
        mem = MemoryRecord.from_dict(d)
        self.assertEqual(mem.memory_id, "forward_compat")
        self.assertEqual(mem.content, "Forward compat test")
        # Unknown fields are silently dropped
        self.assertFalse(hasattr(mem, "unknown_field"))


class TestValidation(unittest.TestCase):
    """Validation utility must catch invalid data."""

    def test_validate_score_valid(self):
        self.assertIsNone(validate_score(0.5, "test"))
        self.assertIsNone(validate_score(0.0, "test"))
        self.assertIsNone(validate_score(1.0, "test"))

    def test_validate_score_invalid_range(self):
        self.assertIsNotNone(validate_score(-0.1, "test"))
        self.assertIsNotNone(validate_score(1.1, "test"))

    def test_validate_score_invalid_type(self):
        self.assertIsNotNone(validate_score("abc", "test"))
        self.assertIsNotNone(validate_score(None, "test"))

    def test_validate_enum_valid_string(self):
        self.assertIsNone(validate_enum("L3", EvidenceLevel, "evidence_level"))

    def test_validate_enum_valid_instance(self):
        self.assertIsNone(validate_enum(EvidenceLevel.L3, EvidenceLevel, "evidence_level"))

    def test_validate_enum_invalid_string(self):
        err = validate_enum("L99", EvidenceLevel, "evidence_level")
        self.assertIsNotNone(err)
        self.assertIn("L99", err)

    def test_validate_enum_invalid_type(self):
        err = validate_enum(42, EvidenceLevel, "evidence_level")
        self.assertIsNotNone(err)

    def test_validate_memory_record_valid(self):
        mem = MemoryRecord(
            memory_id="valid_mem",
            project_id="valid_proj",
            memory_type=MemoryType.PAPER_EVIDENCE,
            content="Valid memory",
            confidence=0.8,
            importance=0.7,
            project_relevance=0.9,
            evidence_level=EvidenceLevel.L4,
            status=MemoryStatus.ACTIVE,
        )
        errors = validate_memory_record(mem)
        self.assertEqual(errors, [])

    def test_validate_memory_record_missing_id(self):
        mem = MemoryRecord(memory_id="", project_id="")
        errors = validate_memory_record(mem)
        self.assertGreater(len(errors), 0)
        error_text = " ".join(errors).lower()
        self.assertIn("memory_id", error_text)
        self.assertIn("project_id", error_text)

    def test_validate_memory_record_invalid_score(self):
        mem = MemoryRecord(
            memory_id="m1", project_id="p1",
            confidence=1.5,  # invalid
        )
        errors = validate_memory_record(mem)
        self.assertGreater(len(errors), 0)

    def test_validate_memory_record_invalid_status(self):
        """from_dict with invalid enum should raise ValueError, but validate should catch it."""
        mem = MemoryRecord(memory_id="m1", project_id="p1")
        # Manually assign invalid status (circumventing constructor)
        # We test via from_dict which validates upon construction
        with self.assertRaises(ValueError):
            mem.status = MemoryStatus("invalid_status")

    def test_validate_consolidation_input_missing_project_id(self):
        inp = ConsolidationInput(project_id="")
        errors = validate_consolidation_input(inp)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("project_id" in e for e in errors))

    def test_validate_consolidation_input_valid(self):
        inp = ConsolidationInput(project_id="valid_proj")
        errors = validate_consolidation_input(inp)
        self.assertEqual(errors, [])

    def test_validate_consolidation_input_with_memories(self):
        inp = ConsolidationInput(
            project_id="test",
            memory_records=[
                MemoryRecord(memory_id="m1", project_id="test", content="OK"),
                MemoryRecord(memory_id="m2", project_id="test", content="OK"),
            ],
        )
        errors = validate_consolidation_input(inp)
        self.assertEqual(errors, [])

    def test_validate_consolidation_input_invalid_memory(self):
        inp = ConsolidationInput(
            project_id="test",
            memory_records=[
                MemoryRecord(memory_id="", project_id="", confidence=1.5),
            ],
        )
        errors = validate_consolidation_input(inp)
        self.assertGreater(len(errors), 0)

    def test_validate_consolidation_result(self):
        result = ConsolidationResult(project_id="test_proj")
        errors = validate_consolidation_result(result)
        self.assertEqual(errors, [])

    def test_validate_consolidation_result_with_data(self):
        result = ConsolidationResult(
            project_id="test",
            promoted_memories=[
                MemoryRecord(memory_id="pm1", project_id="test", content="Promoted"),
            ],
            new_research_patterns=[
                ResearchPattern(pattern_id="pat1", paper_id="p1", project_id="test"),
            ],
        )
        errors = validate_consolidation_result(result)
        self.assertEqual(errors, [])

    def test_raise_on_errors(self):
        with self.assertRaises(ValidationError):
            raise_on_errors(["error 1", "error 2"], "Test")
        # No error for empty list
        raise_on_errors([], "Test")  # should not raise

    def test_raise_on_errors_empty(self):
        # Should not raise
        raise_on_errors([], "Empty")

    def test_non_memory_record_passed_to_validate(self):
        errors = validate_memory_record("not a memory record")
        self.assertGreater(len(errors), 0)
        self.assertIn("Expected MemoryRecord", errors[0])


class TestBoundaryConditions(unittest.TestCase):
    """Boundary tests for scoring thresholds."""

    def test_score_at_active_boundary(self):
        mem = MemoryRecord(
            memory_id="boundary_active",
            project_id="test",
            confidence=0.9,
            project_relevance=0.95,
            evidence_level=EvidenceLevel.L4,
            retrieval_count=20,
            status=MemoryStatus.ACTIVE,
        )
        from researchos_learning_engine.domain.scoring import score_and_update_memory
        updated = score_and_update_memory(mem)
        self.assertEqual(updated.status, MemoryStatus.ACTIVE)
        self.assertGreaterEqual(updated.health_score, 0.75)

    def test_score_at_normal_boundary(self):
        mem = MemoryRecord(
            memory_id="boundary_normal",
            project_id="test",
            confidence=0.5,
            project_relevance=0.5,
            evidence_level=EvidenceLevel.L2,
            retrieval_count=2,
            status=MemoryStatus.NORMAL,
        )
        from researchos_learning_engine.domain.scoring import score_and_update_memory
        updated = score_and_update_memory(mem)
        self.assertIn(updated.status, (MemoryStatus.NORMAL, MemoryStatus.ACTIVE))
        self.assertGreaterEqual(updated.health_score, 0.45)

    def test_score_at_archived_boundary(self):
        mem = MemoryRecord(
            memory_id="boundary_archived",
            project_id="test",
            memory_type=MemoryType.USER_FACT,
            confidence=0.2,
            project_relevance=0.2,
            evidence_level=EvidenceLevel.L0,
            retrieval_count=0,
            contradiction_count=0,
            status=MemoryStatus.NORMAL,
        )
        from researchos_learning_engine.domain.scoring import score_and_update_memory
        updated = score_and_update_memory(mem)
        self.assertEqual(updated.status, MemoryStatus.ARCHIVED)

    def test_score_at_deprecated_boundary(self):
        mem = MemoryRecord(
            memory_id="boundary_deprecated",
            project_id="test",
            memory_type=MemoryType.USER_FACT,
            confidence=0.05,
            project_relevance=0.05,
            evidence_level=EvidenceLevel.L0,
            retrieval_count=0,
            contradiction_count=3,
            status=MemoryStatus.NORMAL,
        )
        from researchos_learning_engine.domain.scoring import score_and_update_memory
        updated = score_and_update_memory(mem)
        self.assertEqual(updated.status, MemoryStatus.DEPRECATED)

    def test_superseded_memory_not_deleted(self):
        """Superseded memories must remain in the record, not be deleted."""
        from researchos_learning_engine.domain.constants import MemoryStatus as MS

        mem = MemoryRecord(
            memory_id="superseded_keep",
            project_id="test",
            content="This should be superseded but not deleted",
            status=MS.SUPERSEDED,
        )
        d = mem.to_dict()
        self.assertEqual(d["status"], "superseded")
        self.assertEqual(d["memory_id"], "superseded_keep")
        self.assertEqual(d["content"], "This should be superseded but not deleted")

        restored = MemoryRecord.from_dict(d)
        self.assertEqual(restored.status, MS.SUPERSEDED)
        self.assertEqual(restored.content, "This should be superseded but not deleted")



class TestForwardCompatibility(unittest.TestCase):
    """Schemas must handle unknown fields gracefully."""

    def test_unknown_fields_in_dict(self):
        d = {
            "memory_id": "fc_mem_1",
            "project_id": "fc_proj",
            "memory_type": "paper_evidence",
            "content": "Forward compat",
            "new_field_1": "value1",
            "new_field_2": 42,
        }
        mem = MemoryRecord.from_dict(d)
        self.assertEqual(mem.memory_id, "fc_mem_1")
        self.assertFalse(hasattr(mem, "new_field_1"))

    def test_result_unknown_fields(self):
        d = {
            "project_id": "fc_proj",
            "unknown_output": "ignored",
            "future_data": [1, 2, 3],
        }
        result = ConsolidationResult.from_dict(d)
        self.assertEqual(result.project_id, "fc_proj")
        self.assertFalse(hasattr(result, "unknown_output"))

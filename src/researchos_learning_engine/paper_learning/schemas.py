"""Schemas for the High-Impact Paper Learning Library.

Defines data structures for extracting and storing structured
scientific knowledge from high-quality research papers.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any, Dict, List, Optional

from researchos_learning_engine.domain.schemas import _to_dict

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SourceType(str, Enum):
    OA_PDF = "oa_pdf"
    USER_UPLOADED_PDF = "user_uploaded_pdf"
    ABSTRACT_ONLY = "abstract_only"
    NON_OA_METADATA = "non_oa_metadata"


class PaperType(str, Enum):
    ORIGINAL_RESEARCH = "original_research"
    REVIEW = "review"
    METHODS = "methods"
    PROTOCOL = "protocol"
    META_ANALYSIS = "meta_analysis"


class SectionType(str, Enum):
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    METHODS = "methods"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"
    FIGURE_CAPTION = "figure_caption"
    SUPPLEMENTARY = "supplementary"
    UNKNOWN = "unknown"


class LearningStatus(str, Enum):
    PENDING = "pending"
    LEARNED = "learned"
    FAILED = "failed"
    SKIPPED = "skipped"


class InsightType(str, Enum):
    EXPERIMENT_DESIGN = "experiment_design"
    MECHANISM = "mechanism"
    FIGURE_LOGIC = "figure_logic"
    WRITING = "writing"
    STATISTICS = "statistics"
    APPLICATION = "application"
    REVIEWER_RISK = "reviewer_risk"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class HighImpactPaperRecord:
    """Metadata and content of a high-impact paper to be learned."""

    paper_id: str = ""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: int = 0
    journal: str = ""
    doi: str = ""
    source_type: str = "oa_pdf"
    paper_type: str = "original_research"
    full_text: str = ""
    sections: List["PaperSection"] = field(default_factory=list)
    chunks: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    project_relevance_score: float = 0.0
    learning_status: str = "pending"
    created_at: str = ""
    updated_at: str = ""
    field: str = ""  # scientific field (kept at end to not shadow dataclasses.field)

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HighImpactPaperRecord":
        data = dict(data)
        # Convert string enums
        if "source_type" in data and isinstance(data["source_type"], str):
            try:
                data["source_type"] = SourceType(data["source_type"]).value
            except ValueError:
                pass
        if "paper_type" in data and isinstance(data["paper_type"], str):
            try:
                data["paper_type"] = PaperType(data["paper_type"]).value
            except ValueError:
                pass
        if "learning_status" in data and isinstance(data["learning_status"], str):
            try:
                data["learning_status"] = LearningStatus(data["learning_status"]).value
            except ValueError:
                pass
        # Nested sections
        if "sections" in data and isinstance(data["sections"], list):
            data["sections"] = [
                PaperSection.from_dict(s) if isinstance(s, dict) else s
                for s in data["sections"]
            ]
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class PaperSection:
    """A single section parsed from a paper's full text."""

    section_id: str = ""
    paper_id: str = ""
    section_type: str = "unknown"
    title: str = ""
    text: str = ""
    order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PaperSection":
        data = dict(data)
        if "section_type" in data and isinstance(data["section_type"], str):
            try:
                data["section_type"] = SectionType(data["section_type"]).value
            except ValueError:
                pass
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class ExperimentDesignPattern:
    """Structured experimental design extracted from a paper."""

    pattern_id: str = ""
    paper_id: str = ""
    research_question: str = ""
    hypothesis: str = ""
    experimental_models: List[str] = field(default_factory=list)
    groups: List[str] = field(default_factory=list)
    interventions: List[str] = field(default_factory=list)
    doses_or_concentrations: List[str] = field(default_factory=list)
    timepoints: List[str] = field(default_factory=list)
    assays: List[str] = field(default_factory=list)
    controls: List[str] = field(default_factory=list)
    statistical_methods: List[str] = field(default_factory=list)
    validation_chain: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentDesignPattern":
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class MechanismPattern:
    """Molecular/cellular mechanism extracted from a paper."""

    pattern_id: str = ""
    paper_id: str = ""
    pathway: str = ""
    targets: List[str] = field(default_factory=list)
    upstream_factors: List[str] = field(default_factory=list)
    downstream_readouts: List[str] = field(default_factory=list)
    evidence_types: List[str] = field(default_factory=list)
    claim_strength: str = ""
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MechanismPattern":
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class FigureLogicPattern:
    """Logic and message of a single figure in a paper."""

    pattern_id: str = ""
    paper_id: str = ""
    figure_id: str = ""
    figure_role: str = ""
    data_type: str = ""
    key_message: str = ""
    supports_which_claim: str = ""
    reusable_figure_idea: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FigureLogicPattern":
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class WritingPattern:
    """Writing and narrative patterns extracted from a paper."""

    pattern_id: str = ""
    paper_id: str = ""
    introduction_logic: str = ""
    result_narrative: str = ""
    discussion_logic: str = ""
    novelty_framing: str = ""
    limitation_framing: str = ""
    application_framing: str = ""
    reusable_sentences_or_templates: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WritingPattern":
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class ReusableResearchInsight:
    """A synthesised, reusable insight from paper learning."""

    insight_id: str = ""
    paper_id: str = ""
    project_id: str = ""
    insight_type: str = "experiment_design"
    content: str = ""
    why_it_matters: str = ""
    applicability_score: float = 0.0
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReusableResearchInsight":
        data = dict(data)
        if "insight_type" in data and isinstance(data["insight_type"], str):
            try:
                data["insight_type"] = InsightType(data["insight_type"]).value
            except ValueError:
                pass
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class PaperLearningResult:
    """Complete output of the paper learning pipeline."""

    paper_id: str = ""
    schema_version: str = "1.0"
    engine_version: str = "0.1.0"
    quality_score: float = 0.0
    project_relevance_score: float = 0.0
    experiment_design_patterns: List[ExperimentDesignPattern] = field(default_factory=list)
    mechanism_patterns: List[MechanismPattern] = field(default_factory=list)
    figure_logic_patterns: List[FigureLogicPattern] = field(default_factory=list)
    writing_patterns: List[WritingPattern] = field(default_factory=list)
    reusable_insights: List[ReusableResearchInsight] = field(default_factory=list)
    recommended_memory_records: List[Dict[str, Any]] = field(default_factory=list)
    recommended_evidence_edges: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_log: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PaperLearningResult":
        data = dict(data)
        if "experiment_design_patterns" in data:
            data["experiment_design_patterns"] = [
                ExperimentDesignPattern.from_dict(p) if isinstance(p, dict) else p
                for p in data["experiment_design_patterns"]
            ]
        if "mechanism_patterns" in data:
            data["mechanism_patterns"] = [
                MechanismPattern.from_dict(p) if isinstance(p, dict) else p
                for p in data["mechanism_patterns"]
            ]
        if "figure_logic_patterns" in data:
            data["figure_logic_patterns"] = [
                FigureLogicPattern.from_dict(p) if isinstance(p, dict) else p
                for p in data["figure_logic_patterns"]
            ]
        if "writing_patterns" in data:
            data["writing_patterns"] = [
                WritingPattern.from_dict(p) if isinstance(p, dict) else p
                for p in data["writing_patterns"]
            ]
        if "reusable_insights" in data:
            data["reusable_insights"] = [
                ReusableResearchInsight.from_dict(i) if isinstance(i, dict) else i
                for i in data["reusable_insights"]
            ]
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})

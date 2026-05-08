"""Schemas for the General Methods Knowledge Base."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any, Dict, List, Optional

from researchos_learning_engine.domain.schemas import _to_dict
from researchos_learning_engine.general_methods_kb.taxonomy import (
    ArticleRole,
    MethodCategory,
)


# ---------------------------------------------------------------------------
# Source identification enums
# ---------------------------------------------------------------------------


class SourceFamily(str, Enum):
    NATURE = "Nature"
    SCIENCE = "Science"
    CELL = "Cell"


class SourceType(str, Enum):
    PDF = "pdf"
    TXT = "txt"
    MD = "md"
    UNKNOWN = "unknown"


class EvidenceType(str, Enum):
    """Type of evidence extracted from a paper."""
    PROTOCOL_STEP = "protocol_step"
    PARAMETER = "parameter"
    QUALITY_CONTROL = "quality_control"
    REPORTING_STANDARD = "reporting_standard"
    EXPERIMENTAL_DESIGN = "experimental_design"
    DATA_ANALYSIS = "data_analysis"
    FIGURE_LOGIC = "figure_logic"
    LIMITATION = "limitation"
    REUSABLE_PATTERN = "reusable_pattern"


# ---------------------------------------------------------------------------
# Deep Learning Fields (for 2021-2026 papers)
# ---------------------------------------------------------------------------


@dataclass
class DeepLearningFields:
    """Extended fields for deep learning on recent high-impact papers."""
    # Core value assessment
    high_impact_value_cn: str = ""
    what_researchos_should_learn_cn: str = ""
    applicable_scenarios_cn: str = ""

    # Protocol & method details
    core_protocol_steps: List[str] = field(default_factory=list)
    critical_parameters: List[str] = field(default_factory=list)
    quality_control_points: List[str] = field(default_factory=list)

    # Reproducibility
    reproducibility_points: List[str] = field(default_factory=list)
    common_pitfalls: List[str] = field(default_factory=list)
    troubleshooting_hints: List[str] = field(default_factory=list)

    # Data & analysis
    data_outputs: List[str] = field(default_factory=list)
    analysis_workflow: str = ""
    statistical_design: str = ""

    # Figure & reporting
    figure_logic_patterns: List[str] = field(default_factory=list)
    reporting_checklist: List[str] = field(default_factory=list)

    # Reusable knowledge
    reusable_research_patterns: List[str] = field(default_factory=list)
    operation_reference_points: List[str] = field(default_factory=list)
    researchos_trigger_questions: List[str] = field(default_factory=list)
    related_methods: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> DeepLearningFields:
        kwargs = {}
        for f in fields(cls):
            if f.name in d:
                kwargs[f.name] = d[f.name]
        return cls(**kwargs)


# ---------------------------------------------------------------------------
# Evidence item
# ---------------------------------------------------------------------------


@dataclass
class EvidenceItem:
    """A single extracted evidence snippet from a paper."""
    claim: str = ""
    short_quote: str = ""
    section: str = ""
    page_ref: str = ""
    chunk_id: str = ""
    evidence_type: str = ""
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> EvidenceItem:
        return cls(**{f.name: d.get(f.name, "") for f in fields(cls)})


# ---------------------------------------------------------------------------
# Main method knowledge record
# ---------------------------------------------------------------------------


@dataclass
class MethodKnowledgeRecord:
    """A single paper's structured entry in the general methods knowledge base."""
    paper_id: str = ""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    journal: str = ""
    doi: str = ""
    source_family: str = ""
    source_journal_group: str = ""
    source_type: str = ""
    # Phase 3 update: new source policy fields
    source_tier: str = ""  # tier_1_high_impact .. tier_4_uncertain_or_low_metadata
    journal_tier: str = ""
    learning_depth: str = ""  # deep, standard, light
    learning_reason: str = ""
    is_user_provided: bool = True
    is_recent_five_years: bool = False
    is_classic_foundational: bool = False
    publication_age_group: str = ""  # recent_five_years, classic_foundational, unknown
    # Original fields
    method_category: str = ""
    method_subcategories: List[str] = field(default_factory=list)
    article_role: str = ""
    abstract_summary_cn: str = ""
    methodological_learning_value_cn: str = ""
    method_scope_cn: str = ""
    retrieval_keywords_cn: List[str] = field(default_factory=list)
    retrieval_keywords_en: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    extraction_warnings: List[str] = field(default_factory=list)
    evidence_items: List[EvidenceItem] = field(default_factory=list)
    deep_learning: Optional[DeepLearningFields] = None

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> MethodKnowledgeRecord:
        kwargs = {}
        for f in fields(cls):
            key = f.name
            if key not in d:
                continue
            if key == "evidence_items" and isinstance(d[key], list):
                kwargs[key] = [EvidenceItem.from_dict(item) for item in d[key]]
            elif key == "deep_learning" and isinstance(d.get(key), dict):
                kwargs[key] = DeepLearningFields.from_dict(d[key])
            else:
                kwargs[key] = d[key]
        return cls(**kwargs)


# ---------------------------------------------------------------------------
# Build-run metadata
# ---------------------------------------------------------------------------


@dataclass
class BuildRunRecord:
    """Metadata about a single KB build run."""
    build_id: str = ""
    started_at: str = ""
    completed_at: str = ""
    input_dir: str = ""
    output_dir: str = ""
    total_files_found: int = 0
    files_processed: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    files_uncertain_source: int = 0  # now = uncertain metadata count
    files_uncertain_metadata: int = 0
    engine_version: str = "0.1.0"
    schema_version: str = "1.0"
    status: str = "completed"
    # Phase 3 update: aggregate stats
    records_by_source_tier: Dict[str, int] = field(default_factory=dict)
    records_by_publication_age_group: Dict[str, int] = field(default_factory=dict)
    records_by_learning_depth: Dict[str, int] = field(default_factory=dict)
    records_by_category: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> BuildRunRecord:
        kwargs = {}
        for f in fields(cls):
            key = f.name
            if key in d:
                kwargs[key] = d[key]
        return cls(**kwargs)

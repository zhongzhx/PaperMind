"""Constants and enumerations for the Learning Engine domain."""

from enum import Enum


class SourceType(str, Enum):
    """Source type for a paper record."""
    OA_PDF = "oa_pdf"
    USER_UPLOADED_PDF = "user_uploaded_pdf"
    ABSTRACT_ONLY = "abstract_only"
    NON_OA_METADATA = "non_oa_metadata"


class PaperStatus(str, Enum):
    """Processing status of a paper record."""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class MemoryType(str, Enum):
    """Type of a project memory record."""
    USER_FACT = "user_fact"
    PROJECT_FACT = "project_fact"
    PAPER_EVIDENCE = "paper_evidence"
    EXPERIMENT_RESULT = "experiment_result"
    DECISION = "decision"
    FAILURE = "failure"
    SKILL_RUN = "skill_run"
    DATA_CONCLUSION = "data_conclusion"


class EvidenceLevel(str, Enum):
    """Evidence level of a memory record.

    L0 = Casual thought or unconfirmed input
    L1 = User-confirmed project fact
    L2 = From literature, PDF, documentation or traceable source
    L3 = From user's own experimental data
    L4 = Multi-source consistent, used in project decisions
    L5 = Formalized in paper, report, or SOP
    """
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"


class MemoryStatus(str, Enum):
    """Lifecycle status of a memory record."""
    ACTIVE = "active"
    NORMAL = "normal"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"
    DEPRECATED = "deprecated"


class StudyType(str, Enum):
    """Type of research study."""
    IN_VIVO = "in_vivo"
    IN_VITRO = "in_vitro"
    IN_SILICO = "in_silico"
    CLINICAL_TRIAL = "clinical_trial"
    REVIEW = "review"
    META_ANALYSIS = "meta_analysis"
    COMPUTATIONAL = "computational"
    OBSERVATIONAL = "observational"
    OTHER = "other"


class EdgeRelation(str, Enum):
    """Relation type for evidence graph edges."""
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    ELABORATES = "elaborates"
    PREREQUISITE = "prerequisite"
    DERIVED_FROM = "derived_from"
    SIMILAR_TO = "similar_to"
    CAUSES = "causes"
    CORRELATES_WITH = "correlates_with"
    PART_OF = "part_of"


class EdgeStatus(str, Enum):
    """Status of an evidence graph edge."""
    ACTIVE = "active"
    WEAK = "weak"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"


# Scoring thresholds for memory status assignment
SCORE_THRESHOLDS = {
    MemoryStatus.ACTIVE: 0.75,
    MemoryStatus.NORMAL: 0.45,
    MemoryStatus.ARCHIVED: 0.20,
    # Below 0.20 → DEPRECATED
}

# Scoring weights for memory health score
WEIGHT_SOURCE_CONFIDENCE = 0.25
WEIGHT_USER_CONFIRMATION = 0.20
WEIGHT_PROJECT_RELEVANCE = 0.20
WEIGHT_EVIDENCE_SUPPORT = 0.15
WEIGHT_RETRIEVAL_USEFULNESS = 0.10
WEIGHT_RECENCY = 0.05
PENALTY_CONTRADICTION = 0.20
PENALTY_REDUNDANCY = 0.10

# Default recency half-life in days
RECENCY_HALF_LIFE_DAYS = 30.0

# Evidence level → numeric confidence mapping
EVIDENCE_LEVEL_CONFIDENCE = {
    EvidenceLevel.L0: 0.1,
    EvidenceLevel.L1: 0.3,
    EvidenceLevel.L2: 0.5,
    EvidenceLevel.L3: 0.7,
    EvidenceLevel.L4: 0.85,
    EvidenceLevel.L5: 1.0,
}

# Schema & engine versions
SCHEMA_VERSION = "1.0"
ENGINE_VERSION = "0.1.0"

# Valid score range
SCORE_MIN = 0.0
SCORE_MAX = 1.0

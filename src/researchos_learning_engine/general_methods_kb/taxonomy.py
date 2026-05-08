"""Taxonomy definitions for General Methods Knowledge Base categorization."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional


class MethodCategory(str, Enum):
    """Top-level method category (一级分类)."""
    QPCR_RT_QPCR = "qPCR_RT_qPCR"
    WESTERN_BLOT = "western_blot"
    FLOW_CYTOMETRY = "flow_cytometry"
    PCR_GENERAL = "PCR_general"
    OMICS = "omics_metabolomics_transcriptomics_proteomics"
    CELL_CULTURE = "cell_culture"
    CHEMICAL_SYNTHESIS = "chemical_synthesis"
    BIOSYNTHESIS = "biosynthesis"
    CLINICAL_DATA = "clinical_data"
    ANIMAL_EXPERIMENT = "animal_experiment"


class OmicsSubcategory(str, Enum):
    """二级标签: omics_metabolomics_transcriptomics_proteomics."""
    METABOLOMICS = "metabolomics"
    TRANSCRIPTOMICS = "transcriptomics"
    PROTEOMICS = "proteomics"
    MULTIOMICS = "multiomics"
    SAMPLE_PREPARATION = "sample_preparation"
    LC_MS = "LC_MS"
    GC_MS = "GC_MS"
    RNA_SEQ = "RNA_seq"
    DIA = "DIA"
    DDA = "DDA"
    DIFFERENTIAL_ANALYSIS = "differential_analysis"
    PATHWAY_ANALYSIS = "pathway_analysis"
    BATCH_EFFECT = "batch_effect"
    DATA_QUALITY_CONTROL = "data_quality_control"


class AnimalSubcategory(str, Enum):
    """二级标签: animal_experiment."""
    MODEL_ESTABLISHMENT = "model_establishment"
    DOSING = "dosing"
    ANESTHESIA = "anesthesia"
    SURGERY = "surgery"
    SAMPLING = "sampling"
    TISSUE_COLLECTION = "tissue_collection"
    BLOOD_COLLECTION = "blood_collection"
    ORGAN_INDEX = "organ_index"
    PATHOLOGY = "pathology"
    BEHAVIORAL_TEST = "behavioral_test"
    IMMUNE_MODEL = "immune_model"
    INFLAMMATION_MODEL = "inflammation_model"
    TUMOR_MODEL = "tumor_model"
    METABOLIC_MODEL = "metabolic_model"
    NEURO_MODEL = "neuro_model"
    WELFARE_AND_ENDPOINT = "welfare_and_endpoint"
    RANDOMIZATION_AND_BLINDING = "randomization_and_blinding"
    STATISTICAL_DESIGN = "statistical_design"


class ArticleRole(str, Enum):
    """Role this article plays in the methods knowledge base."""
    FOUNDATIONAL_PROTOCOL = "foundational_protocol"
    FOUNDATIONAL_METHOD = "foundational_method"
    UPDATED_PROTOCOL = "updated_protocol"
    BENCHMARK = "benchmark"
    REVIEW = "review"
    CLASSIC_REVIEW = "classic_review"
    GUIDELINE = "guideline"
    REPRESENTATIVE_HIGH_IMPACT_CASE = "representative_high_impact_case"
    REPRESENTATIVE_CASE = "representative_case"
    HISTORICAL_REFERENCE = "historical_reference"
    DATA_ANALYSIS_WORKFLOW = "data_analysis_workflow"
    EXPERIMENTAL_DESIGN_REFERENCE = "experimental_design_reference"
    REPORTING_STANDARD = "reporting_standard"


class SourceTier(str, Enum):
    """Source/journal impact tier for confidence calibration."""
    TIER_1_HIGH_IMPACT = "tier_1_high_impact"
    TIER_2_FIELD_LEADING = "tier_2_field_leading"
    TIER_3_STANDARD_PEER_REVIEWED = "tier_3_standard_peer_reviewed"
    TIER_4_UNCERTAIN_OR_LOW_METADATA = "tier_4_uncertain_or_low_metadata"


class LearningDepth(str, Enum):
    """Depth of LLM-based learning applied to a paper."""
    DEEP = "deep"
    STANDARD = "standard"
    LIGHT = "light"


class PublicationAgeGroup(str, Enum):
    """Age-based grouping for learning depth decisions."""
    RECENT_FIVE_YEARS = "recent_five_years"
    CLASSIC_FOUNDATIONAL = "classic_foundational"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Source tier detection
# ---------------------------------------------------------------------------

_TIER_1_JOURNALS: List[str] = [
    "nature", "science", "cell",
    "nature methods", "nature protocols", "nature biotechnology",
    "nature medicine", "nature immunology", "nature chemical biology",
    "science advances", "science translational medicine",
    "science immunology", "science robotics", "science signaling",
    "molecular cell", "cell systems", "cell reports methods",
    "cell reports medicine", "cell stem cell", "cell metabolism",
    "cancer cell", "immunity", "neuron", "developmental cell",
    "current biology", "cell press", "star protocols",
    "nature reviews molecular cell biology",
    "nature reviews cancer", "nature reviews immunology",
    "nature reviews genetics", "nature reviews drug discovery",
    "nature reviews methods primers",
]

_TIER_2_JOURNALS: List[str] = [
    "nucleic acids research", "genome biology", "bioinformatics",
    "analytical chemistry", "journal of proteome research",
    "metabolomics", "briefings in bioinformatics",
    "pnas", "proceedings of the national academy of sciences",
    "embo journal", "embo reports", "embo molecular medicine",
    "developmental cell",
    "elife", "plos biology", "plos genetics",
    "cell reports", "cell death & differentiation",
    "cell communication and signaling",
    "molecular systems biology",
    "genome research", "genome medicine",
    "nature communications", "nature chemical biology",
    "scientific reports", "npj",
    "journal of biological chemistry",
    "journal of cell biology", "journal of experimental medicine",
    "plant cell", "molecular plant",
    "molecular therapy", "human molecular genetics",
    "human gene therapy",
    "diabetes", "circulation", "blood", "cancer research",
]


def _journal_matches(tier_list: List[str], journal: str) -> bool:
    """Check if journal name matches any pattern in the tier list.

    Single-word patterns require exact match; multi-word patterns use
    substring matching.  Empty journal names never match.
    """
    j_lower = journal.lower().strip()
    if not j_lower:
        return False
    for pattern in tier_list:
        p_lower = pattern.lower().strip()
        if " " in p_lower:
            # Multi-word pattern: substring match
            if p_lower in j_lower:
                return True
        else:
            # Single-word pattern: exact match only
            if j_lower == p_lower:
                return True
    return False


def detect_source_tier(
    source_family: str,
    journal: str,
    source_journal_group: str = "",
) -> str:
    """Detect the source tier for a paper.

    Returns one of SourceTier values.
    """
    j_lower = journal.lower().strip()

    # 1. If source_family is a recognized high-impact family, check specific journal
    if source_family in ("Nature", "Science", "Cell"):
        if _journal_matches(_TIER_1_JOURNALS, j_lower):
            return SourceTier.TIER_1_HIGH_IMPACT
        if _journal_matches(_TIER_2_JOURNALS, j_lower):
            return SourceTier.TIER_2_FIELD_LEADING
        if j_lower:
            return SourceTier.TIER_2_FIELD_LEADING
        return SourceTier.TIER_3_STANDARD_PEER_REVIEWED

    # 2. Check against known tier 1 patterns
    if _journal_matches(_TIER_1_JOURNALS, j_lower):
        return SourceTier.TIER_1_HIGH_IMPACT

    # 3. Check against known tier 2 patterns
    if _journal_matches(_TIER_2_JOURNALS, j_lower):
        return SourceTier.TIER_2_FIELD_LEADING

    # 4. If we have a recognizable journal name
    if j_lower and len(j_lower) > 3:
        return SourceTier.TIER_3_STANDARD_PEER_REVIEWED

    # 5. Fallback — uncertain metadata
    return SourceTier.TIER_4_UNCERTAIN_OR_LOW_METADATA


def detect_learning_depth(
    year: Optional[int],
    article_role: str,
    source_tier: str,
    method_category: str,
    recent_year_start: int = 2021,
) -> tuple:
    """Determine learning depth and reason for a paper.

    Returns (learning_depth: str, learning_reason: str).
    """
    is_recent = year is not None and year >= recent_year_start

    if is_recent:
        reason = f"Published {year} (within recent {recent_year_start}+ window)"
        return LearningDepth.DEEP, reason

    # Pre-2021: check article role and source tier
    foundational_roles = {
        "foundational_protocol", "foundational_method", "benchmark",
    }
    high_value_roles = {
        "foundational_protocol", "foundational_method",
        "guideline", "benchmark", "review",
    }

    if article_role in foundational_roles:
        reason = f"Foundational {article_role} — standard depth for historical value"
        return LearningDepth.STANDARD, reason

    if article_role in high_value_roles and source_tier in (
        SourceTier.TIER_1_HIGH_IMPACT, SourceTier.TIER_2_FIELD_LEADING,
    ):
        reason = f"{article_role} from {source_tier} — standard depth"
        return LearningDepth.STANDARD, reason

    if source_tier == SourceTier.TIER_4_UNCERTAIN_OR_LOW_METADATA:
        reason = "Limited metadata — light extraction"
        return LearningDepth.LIGHT, reason

    # Standard depth for pre-2021 papers with clear method category
    if method_category:
        reason = f"Pre-{recent_year_start} with identifiable method category — standard depth"
        return LearningDepth.STANDARD, reason

    reason = f"Pre-{recent_year_start} without clear category — light extraction"
    return LearningDepth.LIGHT, reason


def compute_publication_age_group(
    year: Optional[int],
    recent_year_start: int = 2021,
) -> str:
    """Compute the publication age group for a paper."""
    if year is None:
        return PublicationAgeGroup.UNKNOWN
    if year >= recent_year_start:
        return PublicationAgeGroup.RECENT_FIVE_YEARS
    return PublicationAgeGroup.CLASSIC_FOUNDATIONAL


# ---------------------------------------------------------------------------
# Allowed source families → journal groups (for reference)
# ---------------------------------------------------------------------------


def get_allowed_journals() -> Dict[str, List[str]]:
    """Return mapping of source_family to its allowed journal names/groups.

    Returns dict: source_family → list of journal name patterns (lowercase).
    """
    return {
        "Cell": [
            "cell",
            "molecular cell",
            "cell systems",
            "cell reports",
            "cell reports medicine",
            "cell reports methods",
            "star protocols",
            "med",
            "trends in biotechnology",
            "trends in cell biology",
            "trends in pharmacological sciences",
            "chemistry & biology",
            "current biology",
            "cell press",
        ],
        "Nature": [
            "nature",
            "nature methods",
            "nature protocols",
            "nature biotechnology",
            "nature medicine",
            "nature immunology",
            "nature chemical biology",
            "nature reviews",
            "scientific reports",
            "npj",
        ],
        "Science": [
            "science",
            "science advances",
            "science translational medicine",
            "science immunology",
            "science robotics",
            "science signaling",
        ],
    }


def get_subcategory_map() -> Dict[str, List[str]]:
    """Return mapping of top-level category to valid subcategory values."""
    return {
        "animal_experiment": [e.value for e in AnimalSubcategory],
        "omics_metabolomics_transcriptomics_proteomics": [e.value for e in OmicsSubcategory],
    }


def has_valid_subcategory(category: str, subcategory: str) -> bool:
    """Check whether *subcategory* is valid for *category*."""
    sub_map = get_subcategory_map()
    if category not in sub_map:
        return True  # no subcategories validation needed
    return subcategory in sub_map[category]

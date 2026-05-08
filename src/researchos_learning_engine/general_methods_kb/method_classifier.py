"""Enhanced method category classification with optional LLM disambiguation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from researchos_learning_engine.general_methods_kb.taxonomy import ArticleRole

# ---------------------------------------------------------------------------
# Keyword-based method category classifier
# ---------------------------------------------------------------------------

CATEGORY_KEYWORDS: List[Tuple[str, str, List[str]]] = [
    # (category_value, subcategory, keywords)
    ("qPCR_RT_qPCR", "", ["qpcr", "rt-qpcr", "real-time pcr", "quantitative pcr",
                           "sybr green", "taqman", "ct value", "delta-delta ct"]),
    ("western_blot", "", ["western blot", "immunoblot", "sds-page",
                          "polyacrylamide gel", "pvdf", "nitrocellulose membrane",
                          "primary antibody", "secondary antibody", "hrp"]),
    ("flow_cytometry", "", ["flow cytometry", "facs", "fluorescence-activated",
                            "cell sorting", "forward scatter", "side scatter",
                            "fluorophore", "fitc", "pe-conjugated", "apc"]),
    ("PCR_general", "", ["pcr", "polymerase chain reaction", "primer",
                         "amplification", "thermocycler", "pcr product",
                         "gel electrophoresis", "dna polymerase"]),
    ("omics_metabolomics_transcriptomics_proteomics", "metabolomics",
     ["metabolomics", "metabolite", "lc-ms", "gc-ms", "uhplc", "mass spectrum",
      "mzxml", "mzml"]),
    ("omics_metabolomics_transcriptomics_proteomics", "transcriptomics",
     ["transcriptomics", "rna-seq", "rna sequencing", "single-cell rna",
      "scrna-seq", "gene expression", "dge", "differential expression",
      "transcriptome"]),
    ("omics_metabolomics_transcriptomics_proteomics", "proteomics",
     ["proteomics", "mass spectrometry", "tandem mass", "lc-ms/ms",
      "peptide", "trypsin", "digestion", "protein identification"]),
    ("omics_metabolomics_transcriptomics_proteomics", "multiomics",
     ["multi-omics", "multiomics", "integrated omics", "multi-omic"]),
    ("cell_culture", "", ["cell culture", "cell line", "culture medium",
                          "dmem", "rpmi", "fetal bovine", "fbs", "passaging",
                          "trypsinization", "mycoplasma", "incubator",
                          "5% co2", "subculture"]),
    ("chemical_synthesis", "", ["chemical synthesis", "organic synthesis",
                                "reaction mixture", "solvent", "catalyst",
                                "reflux", "purification", "column chromatography",
                                "nmr", "hplc"]),
    ("biosynthesis", "", ["biosynthesis", "fermentation", "biosynthetic",
                          "metabolic engineering", "pathway engineering",
                          "production strain", "bioreactor", "substrate",
                          "precursor"]),
    ("clinical_data", "", ["clinical trial", "patient", "cohort",
                           "case-control", "cross-sectional", "longitudinal",
                           "inclusion criteria", "exclusion criteria",
                           "informed consent", "ethical approval"]),
    ("animal_experiment", "model_establishment",
     ["animal model", "mouse", "rat", "murine", "rodent", "transgenic",
      "knockout", "model establishment"]),
    ("animal_experiment", "dosing",
     ["dosing", "administration", "oral gavage", "intraperitoneal injection",
      "intravenous", "subcutaneous", "dosage", "mg/kg"]),
    ("animal_experiment", "tissue_collection",
     ["tissue collection", "organ harvest", "tissue sampling",
      "tissue homogenization"]),
    ("animal_experiment", "blood_collection",
     ["blood collection", "cardiac puncture", "retro-orbital",
      "serum", "plasma"]),
    ("animal_experiment", "pathology",
     ["pathology", "histology", "h&e staining", "immunohistochemistry",
      "ihc", "tissue section"]),
]

# ---------------------------------------------------------------------------
# Article role inference
# ---------------------------------------------------------------------------

ROLE_KEYWORDS: Dict[str, List[str]] = {
    "foundational_protocol": ["protocol", "step-by-step", "procedure"],
    "review": ["meta-analysis", "systematic review"],
    "benchmark": ["benchmark", "benchmarking", "comparison"],
    "guideline": ["guideline", "recommendation", "consensus"],
    "data_analysis_workflow": ["data analysis", "workflow", "pipeline"],
}

DEFAULT_ROLE = "representative_high_impact_case"


def _infer_article_role(text: str) -> str:
    """Infer article role from text content via keyword matching."""
    lower = text[:2000].lower()
    for role, keywords in ROLE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return role
    return DEFAULT_ROLE


# ---------------------------------------------------------------------------
# MethodClassifier class
# ---------------------------------------------------------------------------


class MethodClassifier:
    """Classifies papers into method categories with optional LLM disambiguation."""

    def __init__(self, llm: Optional[Any] = None) -> None:
        self._llm = llm

    def classify(
        self, text: str, journal: str = "",
    ) -> Tuple[str, List[str]]:
        """Determine method category and subcategories from paper text.

        Args:
            text: Full paper text.
            journal: Journal name (used for extra hints).

        Returns:
            (primary_category, list_of_subcategories).
            Falls back to ("clinical_data", []) if nothing matches.
        """
        combined = f"{journal} {text[:5000]}".lower()
        matched_subcats: List[str] = []
        matched_cats: Dict[str, int] = {}

        for cat, subcat, keywords in CATEGORY_KEYWORDS:
            for kw in keywords:
                if kw in combined:
                    matched_cats[cat] = matched_cats.get(cat, 0) + 1
                    if subcat:
                        matched_subcats.append(subcat)
                    break

        if not matched_cats:
            return ("clinical_data", [])

        primary = max(matched_cats, key=matched_cats.get)  # type: ignore[arg-type]
        subcats = list(dict.fromkeys(matched_subcats))

        # LLM-assisted disambiguation when confidence is low
        if self._llm is not None and matched_cats[primary] <= 1:
            llm_result = self._llm_disambiguate(text, primary, list(matched_cats.keys()))
            if llm_result:
                primary = llm_result

        return (primary, subcats)

    def _llm_disambiguate(
        self, text: str, current_primary: str, candidates: List[str],
    ) -> Optional[str]:
        """Ask LLM to disambiguate when keyword matching is uncertain."""
        if not candidates:
            return None
        if len(candidates) <= 1:
            return None
        try:
            result = self._llm.generate_json(
                system_prompt=(
                    "You are a method classifier for biomedical research papers. "
                    "Given a list of candidate method categories, select the single "
                    "best-matching category based on the paper text preview."
                ),
                user_message=(
                    f"Candidates: {', '.join(candidates)}\n"
                    f"Text preview: {text[:2000]}"
                ),
            )
            if isinstance(result, dict) and "category" in result:
                return result["category"]
        except Exception:
            pass
        return None

    def infer_role(self, text: str) -> str:
        """Infer article role from text content."""
        return _infer_article_role(text)


def classify_method_category(text: str, journal: str = "") -> Tuple[str, List[str]]:
    """Convenience function — classify without LLM."""
    return MethodClassifier().classify(text, journal)


def infer_article_role(text: str) -> str:
    """Convenience function — infer article role."""
    return _infer_article_role(text)

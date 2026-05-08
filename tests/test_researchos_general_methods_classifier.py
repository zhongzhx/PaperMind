"""Tests for the enhanced method classifier module."""

from __future__ import annotations

import unittest

from researchos_learning_engine.general_methods_kb.method_classifier import (
    CATEGORY_KEYWORDS,
    MethodClassifier,
    _infer_article_role,
    classify_method_category,
    infer_article_role,
)


class TestMethodClassifier(unittest.TestCase):
    def setUp(self):
        self.classifier = MethodClassifier()

    def test_classify_western_blot(self):
        text = "Proteins were separated by SDS-PAGE and transferred to PVDF membrane. Primary antibody incubation was performed overnight."
        cat, subcats = self.classifier.classify(text)
        self.assertEqual(cat, "western_blot")

    def test_classify_qpcr(self):
        text = "Real-time PCR was performed using SYBR Green. The Ct values were analyzed using the delta-delta Ct method."
        cat, subcats = self.classifier.classify(text)
        self.assertEqual(cat, "qPCR_RT_qPCR")

    def test_classify_flow_cytometry(self):
        text = "Cells were analyzed by flow cytometry using FITC-conjugated antibodies and FACS sorting."
        cat, subcats = self.classifier.classify(text)
        self.assertEqual(cat, "flow_cytometry")

    def test_classify_animal_experiment(self):
        text = "Mice were used as animal models. Oral gavage was performed for dosing. Tissues were collected for histology."
        cat, subcats = self.classifier.classify(text)
        self.assertEqual(cat, "animal_experiment")

    def test_classify_omics(self):
        text = "RNA-seq analysis was performed. Differential gene expression was analyzed. Metabolomics data from LC-MS."
        cat, subcats = self.classifier.classify(text)
        self.assertEqual(cat, "omics_metabolomics_transcriptomics_proteomics")
        self.assertIn("transcriptomics", subcats)

    def test_classify_fallback(self):
        text = "The weather is nice today. No method keywords here."
        cat, subcats = self.classifier.classify(text)
        self.assertEqual(cat, "clinical_data")

    def test_classify_with_journal_hint(self):
        text = "A new protocol for protein analysis."
        cat, subcats = self.classifier.classify(text, journal="Nature Methods")
        # Without western blot keywords, should fallback
        self.assertEqual(cat, "clinical_data")

    def test_infer_role_protocol(self):
        role = _infer_article_role("This is a step-by-step protocol for ...")
        self.assertEqual(role, "foundational_protocol")

    def test_infer_role_review(self):
        role = _infer_article_role("A systematic review and meta-analysis of ...")
        self.assertEqual(role, "review")

    def test_infer_role_default(self):
        role = _infer_article_role("We report a novel finding in cancer biology.")
        self.assertEqual(role, "representative_high_impact_case")

    def test_convenience_function(self):
        cat, subcats = classify_method_category("qPCR analysis using SYBR Green.")
        self.assertEqual(cat, "qPCR_RT_qPCR")

    def test_categories_all_covered(self):
        """Verify CATEGORY_KEYWORDS covers all MethodCategory values."""
        cats = {cat for cat, _, _ in CATEGORY_KEYWORDS}
        expected = {
            "qPCR_RT_qPCR", "western_blot", "flow_cytometry",
            "PCR_general", "omics_metabolomics_transcriptomics_proteomics",
            "cell_culture", "chemical_synthesis", "biosynthesis",
            "clinical_data", "animal_experiment",
        }
        self.assertEqual(cats, expected)


if __name__ == "__main__":
    unittest.main()

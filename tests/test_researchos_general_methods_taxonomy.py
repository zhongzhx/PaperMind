"""Tests for the General Methods KB taxonomy module."""

from __future__ import annotations

import unittest

from researchos_learning_engine.general_methods_kb.taxonomy import (
    AnimalSubcategory,
    ArticleRole,
    LearningDepth,
    MethodCategory,
    OmicsSubcategory,
    PublicationAgeGroup,
    SourceTier,
    compute_publication_age_group,
    detect_learning_depth,
    detect_source_tier,
    get_allowed_journals,
    get_subcategory_map,
    has_valid_subcategory,
)


class TestMethodCategory(unittest.TestCase):
    def test_enum_values(self):
        """All 10 top-level categories are present."""
        values = {e.value for e in MethodCategory}
        expected = {
            "qPCR_RT_qPCR", "western_blot", "flow_cytometry",
            "PCR_general", "omics_metabolomics_transcriptomics_proteomics",
            "cell_culture", "chemical_synthesis", "biosynthesis",
            "clinical_data", "animal_experiment",
        }
        self.assertEqual(values, expected)

    def test_article_role_values(self):
        values = {e.value for e in ArticleRole}
        self.assertIn("foundational_protocol", values)
        self.assertIn("representative_high_impact_case", values)
        self.assertIn("review", values)


class TestSourceTier(unittest.TestCase):
    def test_enum_values(self):
        values = {e.value for e in SourceTier}
        self.assertIn("tier_1_high_impact", values)
        self.assertIn("tier_2_field_leading", values)
        self.assertIn("tier_3_standard_peer_reviewed", values)
        self.assertIn("tier_4_uncertain_or_low_metadata", values)

    def test_detect_nature_tier_1(self):
        tier = detect_source_tier("Nature", "Nature")
        self.assertEqual(tier, "tier_1_high_impact")

    def test_detect_cell_tier_1(self):
        tier = detect_source_tier("Cell", "Cell")
        self.assertEqual(tier, "tier_1_high_impact")

    def test_detect_nature_methods_tier_1(self):
        tier = detect_source_tier("Nature", "Nature Methods")
        self.assertEqual(tier, "tier_1_high_impact")

    def test_detect_nature_comm_tier_2(self):
        """Nature Communications is tier_2_field_leading."""
        tier = detect_source_tier("Nature", "Nature Communications")
        # Nature Communications matches _TIER_2_JOURNALS
        self.assertEqual(tier, "tier_2_field_leading")

    def test_detect_plos_tier_2(self):
        tier = detect_source_tier("", "PLOS Biology")
        self.assertEqual(tier, "tier_2_field_leading")

    def test_detect_unknown_journal_tier_3(self):
        tier = detect_source_tier("", "Journal of Some Field")
        self.assertEqual(tier, "tier_3_standard_peer_reviewed")

    def test_detect_no_journal_tier_4(self):
        tier = detect_source_tier("", "")
        self.assertEqual(tier, "tier_4_uncertain_or_low_metadata")

    def test_detect_science_family_no_journal_tier_2(self):
        """Science family with no specific journal → tier_2."""
        tier = detect_source_tier("Science", "Science")
        self.assertEqual(tier, "tier_1_high_impact")

    def test_detect_cell_reports_tier_2(self):
        tier = detect_source_tier("Cell", "Cell Reports")
        self.assertEqual(tier, "tier_2_field_leading")

    def test_detect_small_journal_name_tier_4(self):
        """Very short journal name (< 4 chars) with no family → tier_4."""
        tier = detect_source_tier("", "ab")
        self.assertEqual(tier, "tier_4_uncertain_or_low_metadata")


class TestLearningDepth(unittest.TestCase):
    def test_recent_deep(self):
        depth, reason = detect_learning_depth(2023, "", "", "")
        self.assertEqual(depth, LearningDepth.DEEP)

    def test_pre_2021_no_role_light(self):
        depth, reason = detect_learning_depth(2015, "", "tier_3_standard_peer_reviewed", "")
        self.assertEqual(depth, LearningDepth.LIGHT)

    def test_foundational_protocol_standard(self):
        depth, reason = detect_learning_depth(
            2015, "foundational_protocol", "tier_3_standard_peer_reviewed", "",
        )
        self.assertEqual(depth, LearningDepth.STANDARD)

    def test_tier_4_light(self):
        depth, reason = detect_learning_depth(
            2015, "", "tier_4_uncertain_or_low_metadata", "",
        )
        self.assertEqual(depth, LearningDepth.LIGHT)

    def test_with_method_category_standard(self):
        depth, reason = detect_learning_depth(
            2015, "", "tier_3_standard_peer_reviewed", "western_blot",
        )
        self.assertEqual(depth, LearningDepth.STANDARD)

    def test_high_value_role_tier_1_standard(self):
        depth, reason = detect_learning_depth(
            2015, "review", "tier_1_high_impact", "",
        )
        self.assertEqual(depth, LearningDepth.STANDARD)

    def test_foundational_method_standard(self):
        depth, reason = detect_learning_depth(
            2010, "foundational_method", "tier_3_standard_peer_reviewed", "",
        )
        self.assertEqual(depth, LearningDepth.STANDARD)

    def test_reason_is_not_empty(self):
        depth, reason = detect_learning_depth(2023, "review", "tier_1_high_impact", "")
        self.assertTrue(len(reason) > 0)

    def test_benchmark_standard(self):
        depth, reason = detect_learning_depth(
            2010, "benchmark", "tier_3_standard_peer_reviewed", "",
        )
        self.assertEqual(depth, LearningDepth.STANDARD)


class TestPublicationAgeGroup(unittest.TestCase):
    def test_recent_five_years(self):
        group = compute_publication_age_group(2023)
        self.assertEqual(group, PublicationAgeGroup.RECENT_FIVE_YEARS)

    def test_classic_foundational(self):
        group = compute_publication_age_group(2015)
        self.assertEqual(group, PublicationAgeGroup.CLASSIC_FOUNDATIONAL)

    def test_unknown(self):
        group = compute_publication_age_group(None)
        self.assertEqual(group, PublicationAgeGroup.UNKNOWN)

    def test_edge_year(self):
        group = compute_publication_age_group(2021)
        self.assertEqual(group, PublicationAgeGroup.RECENT_FIVE_YEARS)


class TestAllowedJournals(unittest.TestCase):
    def test_all_three_families(self):
        journals = get_allowed_journals()
        self.assertIn("Cell", journals)
        self.assertIn("Nature", journals)
        self.assertIn("Science", journals)

    def test_cell_journals_count(self):
        journals = get_allowed_journals()
        self.assertGreaterEqual(len(journals["Cell"]), 10)

    def test_nature_journals_count(self):
        journals = get_allowed_journals()
        self.assertGreaterEqual(len(journals["Nature"]), 8)

    def test_science_journals_count(self):
        journals = get_allowed_journals()
        self.assertGreaterEqual(len(journals["Science"]), 4)


class TestSubcategories(unittest.TestCase):
    def test_animal_subcategory_count(self):
        sub_map = get_subcategory_map()
        self.assertEqual(len(sub_map["animal_experiment"]), 18)

    def test_omics_subcategory_count(self):
        sub_map = get_subcategory_map()
        self.assertEqual(len(sub_map["omics_metabolomics_transcriptomics_proteomics"]), 14)

    def test_has_valid_subcategory_true(self):
        self.assertTrue(has_valid_subcategory("animal_experiment", "dosing"))

    def test_has_valid_subcategory_false(self):
        self.assertFalse(has_valid_subcategory("animal_experiment", "invalid_subcat"))

    def test_no_subcategory_validation_needed(self):
        self.assertTrue(has_valid_subcategory("western_blot", "anything"))


if __name__ == "__main__":
    unittest.main()

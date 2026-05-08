"""Tests for the source filter module.

Phase 3 policy:
  - classify_source() is deprecated — always returns "accepted"
  - filter_papers() is deprecated — returns all as "accepted"
  - should_skip_paper() replaces them for truly unprocessable files
  - assess_metadata_quality() provides metadata quality flags
"""

from __future__ import annotations

import unittest

from researchos_learning_engine.general_methods_kb.source_filter import (
    assess_metadata_quality,
    classify_source,
    filter_papers,
    should_skip_paper,
)


class TestClassifySourceDeprecated(unittest.TestCase):
    """classify_source is deprecated — always returns 'accepted'."""

    def test_accepted_nature(self):
        status = classify_source(
            source_family="Nature", journal="Nature",
            file_stem="paper", parent_dir_name="papers",
            text_start="some text",
        )
        self.assertEqual(status, "accepted")

    def test_accepted_empty(self):
        """Even empty source_family is now 'accepted'."""
        status = classify_source(
            source_family="", journal="",
            file_stem="paper", parent_dir_name="papers",
            text_start="some text",
        )
        self.assertEqual(status, "accepted")

    def test_accepted_arxiv(self):
        """arXiv papers are not filtered out anymore."""
        status = classify_source(
            source_family="", journal="",
            file_stem="arxiv_paper", parent_dir_name="arxiv",
            text_start="no hint",
        )
        self.assertEqual(status, "accepted")


class TestFilterPapersDeprecated(unittest.TestCase):
    """filter_papers is deprecated — returns all as accepted."""

    def test_empty_inputs(self):
        result = filter_papers([], [])
        self.assertEqual(result["accepted"], [])
        self.assertEqual(result["skipped"], [])
        self.assertEqual(result["uncertain"], [])

    def test_all_accepted(self):
        scanned = [{"file_stem": "test"}, {"file_stem": "preprint"}]
        metadata = [{"source_family": "Nature"}, {"source_family": ""}]
        result = filter_papers(scanned, metadata)
        self.assertEqual(len(result["accepted"]), 2)
        self.assertEqual(len(result["skipped"]), 0)
        self.assertEqual(len(result["uncertain"]), 0)

    def test_entry_structure(self):
        scanned = [{"file_stem": "p1", "parent_dir_name": "papers"}]
        metadata = [{"source_family": "Science", "journal": "Science"}]
        result = filter_papers(scanned, metadata)
        entry = result["accepted"][0]
        self.assertIn("file_info", entry)
        self.assertIn("metadata", entry)


class TestShouldSkipPaper(unittest.TestCase):
    """should_skip_paper is the new filter — only truly unprocessable files."""

    def test_empty_content(self):
        reason = should_skip_paper("", ".txt", 0, "")
        self.assertEqual(reason, "empty_content")

    def test_whitespace_only(self):
        reason = should_skip_paper("   \n  \t  ", ".txt", 10, "")
        self.assertEqual(reason, "empty_content")

    def test_too_short(self):
        reason = should_skip_paper("short", ".txt", 5, "")
        self.assertEqual(reason, "too_short")

    def test_normal_paper_not_skipped(self):
        reason = should_skip_paper(
            "This is a normal research paper with lots of content.", ".txt", 70, "Nature",
        )
        self.assertEqual(reason, "")

    def test_arxiv_preprint_not_skipped(self):
        """Preprints are no longer skipped."""
        reason = should_skip_paper(
            "This is a preprint paper from arXiv. Not high impact.", ".txt", 55, "",
        )
        self.assertEqual(reason, "")

    def test_not_a_paper_blog_post(self):
        reason = should_skip_paper(
            "blog post about science and research methods", ".txt", 60, "",
        )
        self.assertEqual(reason, "not_a_paper")

    def test_not_a_paper_newspaper(self):
        reason = should_skip_paper(
            "newspaper article from today about science experiments", ".txt", 65, "",
        )
        self.assertEqual(reason, "not_a_paper")

    def test_pdf_extraction_failed(self):
        reason = should_skip_paper(
            "short text", ".pdf", 80, "",
        )
        self.assertEqual(reason, "pdf_extraction_failed")

    def test_pdf_with_source_family_ok(self):
        """PDF with known source family should not be flagged as failed."""
        reason = should_skip_paper(
            "short text", ".pdf", 80, "Nature",
        )
        self.assertEqual(reason, "")


class TestAssessMetadataQuality(unittest.TestCase):
    def test_all_present(self):
        result = assess_metadata_quality("Nature", "Nature Methods", 2023, "10.1038/...", 5000, "pdf")
        self.assertTrue(result["has_journal"])
        self.assertTrue(result["has_year"])
        self.assertTrue(result["has_doi"])
        self.assertTrue(result["has_content"])

    def test_no_metadata(self):
        result = assess_metadata_quality("", "", None, "", 50, "txt")
        self.assertFalse(result["has_journal"])
        self.assertFalse(result["has_year"])
        self.assertFalse(result["has_doi"])
        self.assertFalse(result["has_content"])

    def test_partial_metadata(self):
        result = assess_metadata_quality("", "Some Journal", None, "", 50, "txt")
        self.assertTrue(result["has_journal"])
        self.assertFalse(result["has_year"])
        self.assertFalse(result["has_doi"])
        self.assertFalse(result["has_content"])

    def test_barely_enough_content(self):
        result = assess_metadata_quality("", "", None, "", 101, "txt")
        self.assertTrue(result["has_content"])

    def test_short_content(self):
        result = assess_metadata_quality("", "", None, "", 50, "txt")
        self.assertFalse(result["has_content"])


if __name__ == "__main__":
    unittest.main()

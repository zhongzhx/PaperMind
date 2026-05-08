"""Tests for the confidence scoring module."""

from __future__ import annotations

import unittest

from researchos_learning_engine.general_methods_kb.confidence_scoring import (
    compute_confidence,
    compute_confidence_with_breakdown,
)


class TestConfidenceScoring(unittest.TestCase):
    def test_full_score(self):
        """All factors maximized = near-1.0 score."""
        score = compute_confidence(
            source_family="Nature",
            year=2023,
            has_doi=True,
            text="x" * 10000,
            source_type="pdf",
            sections={"abstract": True, "methods": True, "results": True, "discussion": True},
            recent_year_start=2021,
        )
        self.assertGreaterEqual(score, 0.85)

    def test_minimal_score(self):
        """All factors minimized = near-0.0 score."""
        score = compute_confidence(
            source_family="",
            year=None,
            has_doi=False,
            text="",
            source_type="unknown",
            sections={},
            recent_year_start=2021,
        )
        self.assertLessEqual(score, 0.15)

    def test_mid_range_score(self):
        """Partial factors = mid-range score."""
        score = compute_confidence(
            source_family="Nature",
            year=2018,
            has_doi=True,
            text="x" * 1000,
            source_type="txt",
            sections={"abstract": True, "methods": True},
            recent_year_start=2021,
        )
        self.assertGreater(score, 0.2)
        self.assertLess(score, 0.9)

    def test_score_is_bounded(self):
        """Score is always within [0, 1]."""
        for _ in range(100):
            import random
            score = compute_confidence(
                source_family=random.choice(["Nature", "Science", "Cell", ""]),
                year=random.choice([2020, 2021, 2022, 2023, None]),
                has_doi=random.choice([True, False]),
                text="x" * random.randint(0, 20000),
                source_type=random.choice(["pdf", "txt", "md", "unknown"]),
                sections={"abstract": random.choice([True, False])},
            )
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_breakdown_contains_components(self):
        result = compute_confidence_with_breakdown(
            source_family="Science",
            year=2022,
            has_doi=True,
            text="x" * 5000,
            source_type="pdf",
            sections={"abstract": True, "methods": True, "results": True, "discussion": True},
        )
        self.assertIn("score", result)
        self.assertIn("components", result)
        self.assertIn("source_tier", result["components"])
        self.assertIn("recency", result["components"])

    def test_source_tier_science(self):
        score = compute_confidence(source_family="Science", year=2023, has_doi=True,
                                    text="x" * 10000, source_type="pdf",
                                    sections={"abstract": True, "methods": True,
                                              "results": True, "discussion": True})
        # Science should score well
        self.assertGreaterEqual(score, 0.85)

    def test_old_year_lowers_score(self):
        high = compute_confidence(
            source_family="Nature", year=2023, has_doi=True, text="x" * 10000,
            source_type="pdf", sections={"abstract": True, "methods": True,
                                          "results": True, "discussion": True},
        )
        low = compute_confidence(
            source_family="Nature", year=2005, has_doi=True, text="x" * 10000,
            source_type="pdf", sections={"abstract": True, "methods": True,
                                          "results": True, "discussion": True},
        )
        self.assertGreater(high, low)

    def test_no_doi_lowers_score(self):
        with_doi = compute_confidence(
            source_family="Nature", year=2023, has_doi=True, text="x" * 10000,
            source_type="pdf", sections={"abstract": True, "methods": True,
                                          "results": True, "discussion": True},
        )
        without_doi = compute_confidence(
            source_family="Nature", year=2023, has_doi=False, text="x" * 10000,
            source_type="pdf", sections={"abstract": True, "methods": True,
                                          "results": True, "discussion": True},
        )
        self.assertGreater(with_doi, without_doi)


if __name__ == "__main__":
    unittest.main()

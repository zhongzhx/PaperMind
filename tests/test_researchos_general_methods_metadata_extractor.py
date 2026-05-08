"""Tests for the metadata extractor module."""

from __future__ import annotations

import unittest

from researchos_learning_engine.general_methods_kb.metadata_extractor import (
    DOI_PATTERN,
    YEAR_PATTERN,
    _capitalize_journal,
    detect_source_family,
    extract_doi,
    extract_journal,
    extract_title,
    extract_year,
)


class TestExtractDoi(unittest.TestCase):
    def test_finds_doi(self):
        text = "Some text with DOI 10.1038/s41586-020-2009-0 in it."
        self.assertEqual(extract_doi(text), "10.1038/s41586-020-2009-0")

    def test_empty_on_no_doi(self):
        self.assertEqual(extract_doi("no DOI here"), "")

    def test_empty_on_empty_text(self):
        self.assertEqual(extract_doi(""), "")

    def test_doi_pattern_matches_various(self):
        self.assertIsNotNone(DOI_PATTERN.search("10.1002/jev2.12345"))
        self.assertIsNotNone(DOI_PATTERN.search("10.1126/science.abf1234"))
        self.assertIsNotNone(DOI_PATTERN.search("10.1016/j.cell.2023.01.001"))


class TestExtractYear(unittest.TestCase):
    def test_from_text(self):
        text = "Published in 2023. This paper..."
        self.assertEqual(extract_year(text), 2023)

    def test_from_file_stem(self):
        text = "no year here"
        self.assertEqual(extract_year(text, file_stem="paper_2022_review"), 2022)

    def test_none_when_no_year(self):
        self.assertIsNone(extract_year("no digits at all"))

    def test_skips_out_of_range(self):
        text = "year 1800 and year 2100"
        self.assertIsNone(extract_year(text))

    def test_first_year_in_text(self):
        text = "year 2019 and 2020"
        self.assertEqual(extract_year(text), 2019)


class TestExtractTitle(unittest.TestCase):
    def test_extracts_first_line(self):
        text = "This Is the Paper Title\n\nAbstract: ..."
        result = extract_title(text)
        self.assertIn("This Is the Paper Title", result)

    def test_skips_short_lines(self):
        text = "\n\n\nShort\nThis Is a Real Title Longer Than 10 Chars"
        self.assertEqual(extract_title(text), "This Is a Real Title Longer Than 10 Chars")

    def test_skips_doi_lines(self):
        text = "10.1038/s41586-020-2009-0\nThe Actual Title of the Paper"
        result = extract_title(text)
        self.assertNotEqual(result, "10.1038/s41586-020-2009-0")
        self.assertIn("Actual Title", result)

    def test_skips_url_lines(self):
        text = "http://example.com/paper\nThe Actual Title"
        result = extract_title(text)
        self.assertNotIn("http", result)

    def test_fallback_to_file_stem(self):
        result = extract_title("a", file_stem="my_great_paper")
        self.assertEqual(result, "my great paper")

    def test_empty_on_empty(self):
        self.assertEqual(extract_title(""), "")


class TestExtractJournal(unittest.TestCase):
    def test_from_parent_dir(self):
        text = "nothing here"
        result = extract_journal(text, parent_dir_name="Nature_Methods_2023")
        self.assertIn("Nature", result)

    def test_from_text(self):
        text = "Published in Nature Biotechnology. This is a study..."
        result = extract_journal(text)
        self.assertIn("Nature", result)

    def test_from_file_name(self):
        text = ""
        result = extract_journal(text, file_name="Science_2022_paper.pdf")
        self.assertIn("Science", result)

    def test_empty_when_no_match(self):
        self.assertEqual(extract_journal("no journal hints"), "")


class TestDetectSourceFamily(unittest.TestCase):
    def test_nature(self):
        family, group = detect_source_family("Nature")
        self.assertEqual(family, "Nature")
        self.assertEqual(group, "Nature")

    def test_nature_methods(self):
        family, group = detect_source_family("Nature Methods")
        self.assertEqual(family, "Nature")
        self.assertEqual(group, "Nature Methods")

    def test_science(self):
        family, group = detect_source_family("Science")
        self.assertEqual(family, "Science")
        self.assertEqual(group, "Science")

    def test_cell(self):
        family, group = detect_source_family("Cell")
        self.assertEqual(family, "Cell")
        self.assertEqual(group, "Cell")

    def test_cell_reports(self):
        family, group = detect_source_family("Cell Reports")
        self.assertEqual(family, "Cell")
        self.assertEqual(group, "Cell Reports")

    def test_unknown_journal(self):
        family, group = detect_source_family("Unknown Journal")
        self.assertEqual(family, "")
        self.assertEqual(group, "")

    def test_empty_journal(self):
        family, group = detect_source_family("")
        self.assertEqual(family, "")
        self.assertEqual(group, "")


class TestCapitalizeJournal(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(_capitalize_journal("nature methods"), "Nature Methods")

    def test_strips_prefix_junk(self):
        result = _capitalize_journal("!!nature methods")
        self.assertIn("Nature", result)


if __name__ == "__main__":
    unittest.main()

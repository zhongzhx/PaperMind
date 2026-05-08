"""Tests for the local folder scanner module."""

from __future__ import annotations

import os
import tempfile
import unittest

from researchos_learning_engine.general_methods_kb.local_folder_scanner import (
    scan_files_iter,
    scan_folder,
)


class TestScanFolder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        # Create test files
        for name in ("paper1.txt", "paper2.md", "paper3.pdf", "readme.txt", "notes.md"):
            path = os.path.join(self.dir, name)
            with open(path, "w") as f:
                f.write("test content")
        # Create subdirectory with more files
        sub = os.path.join(self.dir, "subdir")
        os.makedirs(sub, exist_ok=True)
        for name in ("deep_paper.pdf", "notes.txt"):
            path = os.path.join(sub, name)
            with open(path, "w") as f:
                f.write("test content")

    def tearDown(self):
        self.tmp.cleanup()

    def test_scan_folder_returns_all_supported(self):
        results = scan_folder(self.dir)
        stems = {r["file_stem"] for r in results}
        self.assertIn("paper1", stems)
        self.assertIn("paper2", stems)
        self.assertIn("paper3", stems)
        self.assertIn("deep_paper", stems)
        # readme.txt and notes.txt are also .txt so they will be found
        self.assertIn("readme", stems)
        self.assertIn("notes", stems)

    def test_scan_folder_structure(self):
        results = scan_folder(self.dir)
        for r in results:
            self.assertIn("file_path", r)
            self.assertIn("rel_path", r)
            self.assertIn("file_name", r)
            self.assertIn("file_stem", r)
            self.assertIn("ext", r)
            self.assertIn("parent_dir", r)
            self.assertIn("parent_dir_name", r)
            self.assertIn("size_bytes", r)

    def test_scan_folder_max_papers(self):
        results = scan_folder(self.dir, max_papers=3)
        self.assertLessEqual(len(results), 3)

    def test_scan_folder_empty_dir(self):
        with tempfile.TemporaryDirectory() as empty:
            results = scan_folder(empty)
            self.assertEqual(len(results), 0)

    def test_scan_folder_nonexistent_dir(self):
        results = scan_folder("/tmp/nonexistent_test_dir_12345")
        self.assertEqual(len(results), 0)

    def test_scan_files_iter(self):
        results = list(scan_files_iter(self.dir, max_papers=2))
        self.assertLessEqual(len(results), 2)
        for r in results:
            self.assertIn("file_path", r)

    def test_file_has_correct_extension(self):
        results = scan_folder(self.dir)
        for r in results:
            self.assertIn(r["ext"], (".txt", ".md", ".pdf"))


if __name__ == "__main__":
    unittest.main()

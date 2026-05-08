"""Tests for the RESEARCHOS_IMPORT_GUIDE.md generation.

Verifies that the import guide is correctly generated during a KB build.
No real papers or LLM required.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from researchos_learning_engine.general_methods_kb.kb_builder import (
    _write_import_guide,
    build_knowledge_base,
)


class TestResearchOSImportGuide(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.output_dir = os.path.join(self.tmp.name, "output")

    def tearDown(self):
        self.tmp.cleanup()

    def test_write_import_guide_creates_file(self):
        _write_import_guide(self.output_dir)
        path = os.path.join(self.output_dir, "RESEARCHOS_IMPORT_GUIDE.md")
        self.assertTrue(os.path.isfile(path))

    def test_write_import_guide_content(self):
        _write_import_guide(self.output_dir)
        path = os.path.join(self.output_dir, "RESEARCHOS_IMPORT_GUIDE.md")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("ResearchOS General Methods Knowledge Base", content)
        self.assertIn("Import Guide", content)
        # Key sections
        self.assertIn("JSONL 如何导入 ResearchOS", content)
        self.assertIn("SQLite 如何被 ResearchOS 查询", content)
        self.assertIn("Research Context Compiler", content)
        self.assertIn("evidence_items", content)
        self.assertIn("通识方法学知识库", content)
        # Should mention all 10 categories
        self.assertIn("animal_experiment", content)

    def test_import_guide_included_during_build(self):
        """The import guide should be created automatically during a build."""
        input_dir = os.path.join(self.tmp.name, "input")
        os.makedirs(input_dir, exist_ok=True)
        # Create a minimal paper
        paper_path = os.path.join(input_dir, "paper1.txt")
        with open(paper_path, "w") as f:
            f.write("Title: Test Paper\n\nAbstract: A test.\n\nDOI: 10.1038/s41586-023-00000-0\n")

        build_knowledge_base(input_dir, self.output_dir)
        guide_path = os.path.join(self.output_dir, "RESEARCHOS_IMPORT_GUIDE.md")
        self.assertTrue(os.path.isfile(guide_path))

    def test_import_guide_sections_complete(self):
        _write_import_guide(self.output_dir)
        path = os.path.join(self.output_dir, "RESEARCHOS_IMPORT_GUIDE.md")
        with open(path, encoding="utf-8") as f:
            content = f.read()

        expected_sections = [
            "这个知识库是什么",
            "它适合回答什么问题",
            "它包含哪些分类",
            "JSONL 如何导入 ResearchOS",
            "SQLite 如何被 ResearchOS 查询",
            "Research Context Compiler",
            "回答用户问题时如何带来源",
            "如何使用 evidence_items",
        ]
        for section in expected_sections:
            with self.subTest(section=section):
                self.assertIn(section, content)


if __name__ == "__main__":
    unittest.main()

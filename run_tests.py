#!/usr/bin/env python3
"""Run all tests using unittest."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Ensure src is on the path
ROOT = Path(__file__).resolve().parent
SRC_DIR = str(ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    tests_dir = ROOT / "tests"
    for test_file in sorted(tests_dir.glob("test_*.py")):
        module_name = f"tests.{test_file.stem}"
        try:
            __import__(module_name)
            module = sys.modules[module_name]
            tests = loader.loadTestsFromModule(module)
            suite.addTests(tests)
        except Exception as e:
            print(f"  ERROR loading {module_name}: {e}")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())

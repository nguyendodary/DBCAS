# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
ROOT = TOOLS.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from docs_qa_guard import ensure_safe_output, protected  # noqa: E402


class GuardTest(unittest.TestCase):
    def test_docs_qa_is_protected(self):
        target = ROOT / "docs" / "qa" / "word-verification" / "summary.md"
        self.assertTrue(protected(target))
        with self.assertRaises(ValueError):
            ensure_safe_output(target)

    def test_review_output_is_allowed(self):
        target = ROOT / "_review" / "tool-output" / "file.json"
        self.assertFalse(protected(target))
        self.assertEqual(ensure_safe_output(target), target.resolve())


if __name__ == "__main__":
    unittest.main()

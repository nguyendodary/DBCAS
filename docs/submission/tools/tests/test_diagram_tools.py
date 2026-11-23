# -*- coding: utf-8 -*-
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
ROOT = TOOLS.parents[2]
sys.path.insert(0, str(TOOLS))

import check_diagrams  # noqa: E402
import erd67  # noqa: E402
import trd67  # noqa: E402
from diagram_style import LEGEND_COUNTS  # noqa: E402


class DiagramToolTest(unittest.TestCase):
    def test_trd_continuation_is_67_tables_and_style(self):
        with tempfile.TemporaryDirectory(prefix="dbcas-trd-") as tmp:
            outputs, spec = trd67.build(
                ROOT / "docs/diagrams/schema-028/schema-introspection.json", Path(tmp))
            self.assertEqual(spec["counts"]["tables"], 67)
            self.assertEqual(spec["counts"]["columns"], 561)
            self.assertEqual(spec["counts"]["foreign_keys"], 122)
            self.assertEqual(spec["counts"]["migrations"], 28)
            self.assertEqual(spec["legend"], LEGEND_COUNTS)
            self.assertEqual(len(outputs), 6)
            self.assertEqual(check_diagrams.check(Path(tmp) / "trd-spec-67.json",
                                                  ROOT / "docs/diagrams/schema-028/schema-introspection.json"), [])
            from PIL import Image
            with Image.open(outputs[0][2]) as image:
                self.assertEqual(image.size, (3440, 2080))

    def test_erd_continuation_has_26_entities(self):
        with tempfile.TemporaryDirectory(prefix="dbcas-erd-") as tmp:
            svg, png, spec = erd67.build(
                ROOT / "docs/diagrams/schema-028/schema-introspection.json", Path(tmp))
            self.assertEqual(len(spec["tables"]), 26)
            self.assertTrue(svg.exists() and png.exists())
            from PIL import Image
            with Image.open(png) as image:
                self.assertEqual(image.size, (4300, 1677))


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
import json
import sys
import tempfile
import unittest
from pathlib import Path

from docx import Document
from docx.shared import Inches
from PIL import Image

TOOLS = Path(__file__).resolve().parents[1]
ROOT = TOOLS.parents[2]
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT / "scripts"))

import docx_toolkit as tool  # noqa: E402


def png(path, color=(200, 20, 20), size=(10, 10)):
    Image.new("RGB", size, color).save(path)


class DocxToolkitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dbcas-docx-tool-")
        self.dir = Path(self.tmp.name)
        self.src = self.dir / "fixture.docx"
        self.image_a = self.dir / "a.png"
        self.image_b = self.dir / "b.png"
        png(self.image_a)
        png(self.image_b, (20, 20, 200), (20, 10))
        doc = Document()
        doc.add_heading("Fixture cover", 0)
        p = doc.add_paragraph()
        run = p.add_run("Bold")
        run.bold = True
        p.add_run(" normal text")
        table = doc.add_table(rows=2, cols=2)
        table.cell(0, 0).text = "A"
        table.cell(0, 1).text = "B"
        table.cell(1, 0).text = "C"
        table.cell(1, 1).text = "D"
        doc.add_picture(str(self.image_a), width=Inches(1))
        doc.save(self.src)

    def tearDown(self):
        self.tmp.cleanup()

    def test_text_replacement_preserves_first_run_formatting(self):
        out = self.dir / "edited.docx"
        tool.replace_text(self.src, out, [{"old": "normal text", "new": "changed text"}])
        doc = Document(out)
        paragraph = next(p for p in doc.paragraphs if "changed text" in p.text)
        self.assertTrue(paragraph.runs[1].bold is not True)
        self.assertEqual(paragraph.runs[1].text.strip(), "changed text")

    def test_clone_paragraph_preserves_style_and_run_properties(self):
        doc = Document(self.src)
        source = next(p for p in doc.paragraphs if "Bold" in p.text)
        clone = tool.clone_paragraph(source, text="Clone")
        self.assertEqual(clone.style.name, source.style.name)
        self.assertTrue(clone.runs[0].bold)
        self.assertEqual(clone.text, "Clone")

    def test_clone_table_row_and_set_cell(self):
        doc = Document(self.src)
        table = doc.tables[0]
        row = tool.clone_table_row(table, values=["E", "F"])
        self.assertEqual([c.text for c in row.cells], ["E", "F"])
        tool.set_cell_text(table.cell(0, 0), "A2")
        self.assertEqual(table.cell(0, 0).text, "A2")

    def test_replace_image_keeps_inline_extent(self):
        out = self.dir / "image.docx"
        count = tool.replace_image(self.src, out, "word/media/image1.png", self.image_b)
        self.assertGreaterEqual(count, 1)
        before = Document(self.src).inline_shapes[0]
        after = Document(out).inline_shapes[0]
        self.assertEqual((before.width, before.height), (after.width, after.height))
        audit = tool.audit_package(self.src, out)
        self.assertTrue(all(audit["parts_c14n_equal"].values()))
        self.assertEqual(audit["images"]["changed_indices"], [0])

    def test_validate_and_pair(self):
        self.assertEqual(tool.validate_docx(self.src), [])
        pair = self.dir / "pair.png"
        tool.make_pair(self.image_a, self.image_b, pair)
        self.assertTrue(pair.exists())
        with Image.open(pair) as made, Image.open(self.image_a) as original:
            self.assertGreater(made.width, original.width)

    def test_fact_audit_from_fixture_inputs(self):
        schema = {
            "tables": [{"table": "a", "columns": [{"name": "id"}]},
                       {"table": "b", "columns": [{"name": "id"}, {"name": "x"}]}],
            "foreign_keys": [{"constraint": "b_a", "source": "b", "columns": ["x"],
                              "destination": "a", "reference_columns": ["id"]}],
            "indexes": [{"name": "a_pk"}],
            "migrations": [{"name": "001"}],
        }
        (self.dir / "schema.json").write_text(json.dumps(schema), encoding="utf-8")
        (self.dir / "openapi.json").write_text(json.dumps({
            "paths": {"/a": {"get": {}, "post": {}}, "/b": {"get": {}}}
        }), encoding="utf-8")
        (self.dir / "App.jsx").write_text('path="/a" path="/b"', encoding="utf-8")
        facts = tool.fact_audit(schema_path=self.dir / "schema.json",
                                openapi_path=self.dir / "openapi.json",
                                app_jsx=self.dir / "App.jsx")
        self.assertEqual((facts["tables"], facts["columns"], facts["foreign_keys"]), (2, 3, 1))
        self.assertEqual((facts["openapi_paths"], facts["operations"]), (2, 3))
        self.assertEqual(facts["frontend_routes"], 2)


if __name__ == "__main__":
    unittest.main()

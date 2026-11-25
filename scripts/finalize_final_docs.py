# -*- coding: utf-8 -*-
"""Finalise DOCX metadata and the explicit Normal style without re-rendering."""
from __future__ import annotations

from pathlib import Path

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

FINAL = Path(__file__).resolve().parents[1] / "docs/submission/final"


def explicit_normal(doc):
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(13)
    rPr = normal.element.find(qn("w:rPr"))
    if rPr is None:
        rPr = OxmlElement("w:rPr")
        normal.element.append(rPr)
    fonts = rPr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rPr.insert(0, fonts)
    for attr in ("w:ascii", "w:eastAsia", "w:hAnsi", "w:cs"):
        fonts.set(qn(attr), "Times New Roman")
    for tag in ("w:sz", "w:szCs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            rPr.append(el)
        el.set(qn("w:val"), "26")


def main():
    for path in sorted(FINAL.glob("C1SE.70_*_DBCAS_ver1.3.docx")):
        doc = docx.Document(str(path))
        cp = doc.core_properties
        cp.author = "Do, Nguyen Quoc"
        cp.last_modified_by = "Do, Nguyen Quoc"
        explicit_normal(doc)
        # never force a global field update; the TOC/list pages are already aligned
        settings = doc.settings.element
        for el in settings.findall(qn("w:updateFields")):
            settings.remove(el)
        doc.save(str(path))
        print("finalised", path.name)


if __name__ == "__main__":
    main()

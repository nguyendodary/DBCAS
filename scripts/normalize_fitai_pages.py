# -*- coding: utf-8 -*-
"""Normalise the two FITAI frames to the A4 geometry used by the other three
documents and make the longer DBCAS cover title fit its text box."""
from __future__ import annotations

from pathlib import Path

import docx
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "docs/submission/final"
DOCS = [
    "C1SE.70_CodeStandards_DBCAS_ver1.3.docx",
    "C1SE.70_TechnicalReport_DBCAS_ver1.3.docx",
]


def main():
    for name in DOCS:
        path = FINAL / name
        doc = docx.Document(str(path))
        for section in doc.sections:
            section.page_width = Cm(21.0)
            section.page_height = Cm(29.7)
            section.left_margin = Cm(3.5)
            section.right_margin = Cm(2.0)
            section.top_margin = Cm(2.0)
            section.bottom_margin = Cm(2.0)
            section.header_distance = Cm(1.0)
            section.footer_distance = Cm(1.0)
        changed = 0
        for p in doc.element.body.iter(qn("w:p")):
            text = "".join(t.text or "" for t in p.iter(qn("w:t")))
            if "Skill Gap Analysis" not in text:
                continue
            pPr = p.find(qn("w:pPr"))
            if pPr is None:
                continue
            spacing = pPr.find(qn("w:spacing"))
            if spacing is None:
                spacing = pPr.makeelement(qn("w:spacing"), {})
                pPr.append(spacing)
            spacing.set(qn("w:after"), "0")
            spacing.set(qn("w:line"), "240")
            spacing.set(qn("w:lineRule"), "auto")
            for r in p.iter(qn("w:r")):
                rPr = r.find(qn("w:rPr"))
                if rPr is None:
                    continue
                for sz in rPr.findall(qn("w:sz")):
                    sz.set(qn("w:val"), "28")
                for sz in rPr.findall(qn("w:szCs")):
                    sz.set(qn("w:val"), "28")
            para_rPr = pPr.find(qn("w:rPr"))
            if para_rPr is not None:
                for sz in para_rPr.findall(qn("w:sz")):
                    sz.set(qn("w:val"), "28")
            changed += 1
        doc.save(str(path))
        print(f"{name}: sections={len(doc.sections)}, title boxes adjusted={changed}")


if __name__ == "__main__":
    main()

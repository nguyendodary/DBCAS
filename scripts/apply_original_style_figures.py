# -*- coding: utf-8 -*-
"""Apply the two final figure decisions.

Code Standards Figure 1 has no baseline source, so it keeps the new diagram
drawn in the original ERD/TRD style (white ground, #F2F2F2 fill, black rules,
Arial).  Its image part is replaced in place and the caption/position kept; the
height is set from the 3000x1650 canvas so the figure is not stretched.

Technical Report Figure 1 is the baseline pipeline diagram, not a new drawing.
The embedded part is replaced with the byte-identical baseline media, keeping
its extent and caption.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import docx
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "docs/submission/final"
BASELINE = ROOT.parent / "Documents" / "Final-ver1.3"
ASSET_CS = FINAL / "assets/figures/backend-layering.png"


def body_image_parts(doc):
    parts = []
    for p in doc.paragraphs:
        for blip in p._p.iter(qn("a:blip")):
            rid = blip.get(qn("r:embed"))
            if rid and rid in doc.part.rels:
                parts.append((p, blip, doc.part.rels[rid].target_part))
                break
    return parts


def set_blob(part, blob: bytes):
    part._blob = blob
    try:
        part._image = None
    except Exception:
        pass


def set_extent(drawing, width_cm: float, height_cm: float):
    cx = str(int(round(width_cm * 360000)))
    cy = str(int(round(height_cm * 360000)))
    for el in drawing.iter(qn("wp:extent")):
        el.set("cx", cx)
        el.set("cy", cy)
    for el in drawing.iter(qn("a:ext")):
        el.set("cx", cx)
        el.set("cy", cy)


def main():
    cs_blob = ASSET_CS.read_bytes()

    cs_path = FINAL / "C1SE.70_CodeStandards_DBCAS_ver1.3.docx"
    doc = docx.Document(str(cs_path))
    figures = body_image_parts(doc)[1:]  # skip cover logo
    if len(figures) != 1:
        raise SystemExit(f"Code Standards: expected 1 body figure, found {len(figures)}")
    p, blip, part = figures[0]
    set_blob(part, cs_blob)
    drawing = blip.getparent()
    while drawing is not None and drawing.tag != qn("w:drawing"):
        drawing = drawing.getparent()
    if drawing is None:
        raise SystemExit("Code Standards: no drawing element")
    set_extent(drawing, 15.2, round(15.2 * 1650 / 3000, 2))
    doc.save(str(cs_path))
    print(f"Code Standards: applied new original-style figure ({len(cs_blob)} bytes)")

    source_zip = zipfile.ZipFile(BASELINE / "C1SE.70_ProposalDocument_DBCAS_ver1.3.docx")
    pipeline = source_zip.read("word/media/image5.png")
    tr_path = FINAL / "C1SE.70_TechnicalReport_DBCAS_ver1.3.docx"
    doc = docx.Document(str(tr_path))
    figures = body_image_parts(doc)[1:]
    if len(figures) != 1:
        raise SystemExit(f"Technical Report: expected 1 body figure, found {len(figures)}")
    p, blip, part = figures[0]
    set_blob(part, pipeline)
    doc.save(str(tr_path))
    print(f"Technical Report: restored baseline pipeline bytes ({len(pipeline)} bytes)")


if __name__ == "__main__":
    main()

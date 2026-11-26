# -*- coding: utf-8 -*-
"""Drop unreferenced image relationships from the five submission DOCX files.

The in-place figure restore replaces the bytes behind an existing image part,
but the packages also keep the previously used media parts.  Those orphans are
not visible in Word, yet a multi-megabyte duplicate can make Word's PDF export
stall.  This removes only image relationships that no document element uses;
every visible figure is untouched.
"""
from __future__ import annotations

from pathlib import Path

import docx
from docx.opc.constants import RELATIONSHIP_TYPE as RT

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "docs/submission/final"
DOCS = ["ProposalDocument", "ArchitectureDesign", "DatabaseDesign", "CodeStandards", "TechnicalReport"]


def used_rel_ids(doc) -> set[str]:
    attrs = (
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed",
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id",
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}link",
    )
    used = set()
    for el in doc.element.body.iter():
        for attr in attrs:
            value = el.get(attr)
            if value:
                used.add(value)
    return used


def main():
    for name in DOCS:
        path = FINAL / f"C1SE.70_{name}_DBCAS_ver1.3.docx"
        doc = docx.Document(str(path))
        used = used_rel_ids(doc)
        dropped = []
        for rid, rel in list(doc.part.rels.items()):
            if rel.reltype == RT.IMAGE and rid not in used:
                dropped.append(str(rel.target_part.partname))
                doc.part.drop_rel(rid)
        doc.save(str(path))
        print(f"{name}: dropped {len(dropped)} orphan image(s) {dropped}")


if __name__ == "__main__":
    main()

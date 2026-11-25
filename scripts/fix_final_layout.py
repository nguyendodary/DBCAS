# -*- coding: utf-8 -*-
"""Fix TOC tab stops and the revision-history table width in the final DOCX."""
from __future__ import annotations

from pathlib import Path

import docx
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm

FINAL = Path(__file__).resolve().parents[1] / "docs/submission/final"
TEXT_W_CM = 15.4


def fix_toc_styles(doc):
    for style in doc.styles:
        name = style.name.lower()
        if name.startswith("toc") or name == "table of figures":
            pf = style.paragraph_format
            pf.right_indent = Cm(0)
            pf.tab_stops.clear_all()
            pf.tab_stops.add_tab_stop(Cm(TEXT_W_CM), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)


def fix_toc_direct_tabs(doc):
    pos = str(int(TEXT_W_CM * 566.92913386))
    for p in doc.element.body.iter(qn("w:p")):
        pPr = p.find(qn("w:pPr"))
        if pPr is None:
            continue
        pStyle = pPr.find(qn("w:pStyle"))
        if pStyle is None:
            continue
        val = (pStyle.get(qn("w:val")) or "").lower()
        if not (val.startswith("toc") or val.startswith("tableoffigures")):
            continue
        old = pPr.find(qn("w:tabs"))
        if old is not None:
            pPr.remove(old)
        tabs = OxmlElement("w:tabs")
        tab = OxmlElement("w:tab")
        tab.set(qn("w:val"), "right")
        tab.set(qn("w:leader"), "dot")
        tab.set(qn("w:pos"), pos)
        tabs.append(tab)
        pPr.append(tabs)
        # remove a direct right indent if present
        ind = pPr.find(qn("w:ind"))
        if ind is not None:
            ind.set(qn("w:right"), "0")


def fix_revision_table(doc):
    for t in doc.tables:
        if len(t.rows) < 2:
            continue
        head = " | ".join(c.text.strip().lower() for c in t.rows[0].cells)
        if "version" in head and "date" in head:
            tblPr = t._tbl.tblPr
            tblW = tblPr.find(qn("w:tblW"))
            if tblW is not None:
                tblW.set(qn("w:w"), "8731")
                tblW.set(qn("w:type"), "dxa")
            # scale explicit cell widths to the text width
            widths = [c.width for c in t.rows[0].cells]
            total = sum(w for w in widths if w) or 1
            target = Cm(TEXT_W_CM)
            for row in t.rows:
                for cell, w in zip(row.cells, widths):
                    if w:
                        cell.width = int(target * (w / total))


def main():
    for path in sorted(FINAL.glob("C1SE.70_*_DBCAS_ver1.3.docx")):
        doc = docx.Document(str(path))
        fix_toc_styles(doc)
        fix_toc_direct_tabs(doc)
        fix_revision_table(doc)
        doc.save(str(path))
        print("fixed", path.name)


if __name__ == "__main__":
    main()

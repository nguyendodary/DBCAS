# -*- coding: utf-8 -*-
"""Rebuild TOC, List of Tables and List of Figures in the academic documents."""
from __future__ import annotations

import re
from pathlib import Path

import docx
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.text.paragraph import Paragraph

FINAL = Path(__file__).resolve().parents[1] / "docs/submission/final"
DOCS = [
    "C1SE.70_ProposalDocument_DBCAS_ver1.3.docx",
    "C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx",
    "C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx",
    "C1SE.70_CodeStandards_DBCAS_ver1.3.docx",
    "C1SE.70_TechnicalReport_DBCAS_ver1.3.docx",
]


def ensure_style(doc, name, size=11):
    try:
        return doc.styles[name]
    except KeyError:
        st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        st.base_style = doc.styles["Normal"]
        st.font.size = Pt(size)
        st.paragraph_format.space_after = Pt(0)
        return st


def add_par(before, doc, text="", style=None, size=11, bold=False):
    p = OxmlElement("w:p")
    before.addprevious(p)
    para = Paragraph(p, doc)
    if style:
        try:
            para.style = doc.styles[style]
        except KeyError:
            pass
    if text:
        r = para.add_run(text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(size)
        r.bold = bold
    return para


def add_field(before, doc):
    p = OxmlElement("w:p")
    before.addprevious(p)
    para = Paragraph(p, doc)
    run = para.add_run()
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve")
    instr.text = ' TOC \\o "1-2" \\h \\z \\u '
    sep = OxmlElement("w:fldChar"); sep.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    for el in (begin, instr, sep, end):
        run._r.append(el)
    return para


def main():
    for name in DOCS:
        path = FINAL / name
        doc = docx.Document(str(path))
        for style in ("TOC 1", "TOC 2", "table of figures"):
            ensure_style(doc, style)
        first_h1 = next(p for p in doc.paragraphs if p.style.name.startswith("Heading 1"))
        # remove content-control TOC fields before the first heading
        for child in list(doc.element.body.iterchildren()):
            if child is first_h1._p:
                break
            if child.tag == qn("w:sdt"):
                child.getparent().remove(child)
        # remove existing front-matter TOC/list paragraphs
        for p in list(doc.paragraphs):
            if p._p is first_h1._p:
                break
            low = p.text.strip().lower()
            normalized = p.style.name.lower().replace(" ", "")
            if (normalized.startswith("toc")
                    or normalized == "tableoffigures"
                    or re.match(r"^.+\t\d+$", p.text.strip())
                    or re.match(r"^\d+(?:\.\d+)*\.?\s.+?\d+$", p.text.strip())
                    or re.match(r"^(?:Figure|Table)\s.*\d+$", p.text.strip())
                    or low in ("table of contents", "table of content", "list of tables", "list of figures")):
                p._p.getparent().remove(p._p)

        # headings
        heads = []
        h1 = h2 = 0
        for p in doc.paragraphs:
            if not p.style.name.startswith("Heading"):
                continue
            text = p.text.strip()
            if not text or text.lower().startswith(("table of contents", "list of")):
                continue
            if p.style.name.startswith("Heading 1"):
                h1 += 1; h2 = 0
                heads.append((1, text, h1, 0))
            elif p.style.name.startswith("Heading 2"):
                h2 += 1
                heads.append((2, text, h1, h2))

        toc_head = add_par(first_h1._p, doc, "Table of Contents", size=14, bold=True)
        toc_head.paragraph_format.page_break_before = True
        add_field(first_h1._p, doc)
        for level, text, a, b in heads:
            if level == 1:
                label = text if re.match(r"^\d", text) or text.startswith("Appendix") or text in ("Abstract", "References") else f"{a}. {text}"
                add_par(first_h1._p, doc, label + "\t1", "TOC 1")
            else:
                label = text if re.match(r"^\d", text) or text.startswith("A.") else f"{a}.{b}. {text}"
                add_par(first_h1._p, doc, label + "\t1", "TOC 2")

        # lists
        for kind, label in (("Table", "List of Tables"), ("Figure", "List of Figures")):
            list_head = add_par(first_h1._p, doc, label, size=14, bold=True)
            list_head.paragraph_format.page_break_before = True
            caps = []
            for p in doc.paragraphs:
                if p.style.name.lower().replace(" ", "") == "tableoffigures":
                    continue
                text = p.text.strip()
                if kind == "Table" and re.match(r"^Table\s+(?:A\.)?\d+(?:\s*\(\d+/\d+\))?[.:]", text):
                    caps.append(text)
                elif kind == "Figure" and re.match(r"^Figure\s+\d+(?:\s*\(\d+/\d+\))?[.:]", text):
                    caps.append(text)
            for cap in caps:
                add_par(first_h1._p, doc, cap + "\t1", "table of figures")
        first_h1.paragraph_format.page_break_before = True
        doc.save(str(path))
        print(f"{name}: headings={len(heads)} rebuilt")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Normalize running heads/feet and body captions in the five final DOCX."""
from __future__ import annotations

import re
from pathlib import Path

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph

FINAL = Path(__file__).resolve().parents[1] / "docs/submission/final"
AUTHOR = "Do, Nguyen Quoc"
GREY = RGBColor(0x44, 0x54, 0x6A)
DOC_TITLES = {
    "ProposalDocument": "Proposal Document",
    "ArchitectureDesign": "Architecture Design Document",
    "DatabaseDesign": "Database Design Document",
    "CodeStandards": "Code Standards Document",
    "TechnicalReport": "Technical Report",
}


def clear_children(p):
    for child in list(p):
        if child.tag != qn("w:pPr"):
            p.remove(child)


def style_run(run, size=9):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.italic = True
    run.font.color.rgb = GREY


def add_field(paragraph, instr, placeholder="1", size=9):
    def run_with(child):
        run = paragraph.add_run()
        style_run(run, size)
        run._r.append(child)
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin")
    instr_el = OxmlElement("w:instrText"); instr_el.set(qn("xml:space"), "preserve"); instr_el.text = f" {instr} "
    sep = OxmlElement("w:fldChar"); sep.set(qn("w:fldCharType"), "separate")
    txt = OxmlElement("w:t"); txt.text = placeholder
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    for el in (begin, instr_el, sep, txt, end):
        run_with(el)


def border(paragraph, edge="bottom"):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = pPr.find(qn("w:pBdr"))
    if pBdr is None:
        pBdr = OxmlElement("w:pBdr")
        pPr.append(pBdr)
    el = OxmlElement(f"w:{edge}")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), "6")
    el.set(qn("w:space"), "1")
    el.set(qn("w:color"), "44546A")
    pBdr.append(el)


def rebuild_running_parts(section):
    width_cm = (section.page_width - section.left_margin - section.right_margin) / 360000
    section.header.is_linked_to_previous = False
    section.footer.is_linked_to_previous = False
    hp = section.header.paragraphs[0]
    clear_children(hp._p)
    hp.paragraph_format.tab_stops.clear_all()
    hp.paragraph_format.tab_stops.add_tab_stop(Cm(width_cm), WD_TAB_ALIGNMENT.RIGHT)
    r = hp.add_run("C1SE.70 · DBCAS")
    style_run(r)
    r = hp.add_run()
    style_run(r)
    r.add_tab()
    r = hp.add_run("International School Capstone 1 – 2026")
    style_run(r)
    border(hp, "bottom")
    fp = section.footer.paragraphs[0]
    clear_children(fp._p)
    fp.paragraph_format.tab_stops.clear_all()
    fp.paragraph_format.tab_stops.add_tab_stop(Cm(width_cm), WD_TAB_ALIGNMENT.RIGHT)
    r = fp.add_run(AUTHOR)
    style_run(r)
    r = fp.add_run()
    style_run(r)
    r.add_tab()
    r = fp.add_run("Page ")
    style_run(r)
    add_field(fp, "PAGE", "1")
    r = fp.add_run(" of ")
    style_run(r)
    add_field(fp, "NUMPAGES", "1")
    border(fp, "top")


def normalize_caption(p, doc):
    text = Paragraph(p, doc).text.strip()
    m = re.match(r"^(Figure|Table)\s+(\d+)(.*?)(\d+)$", text)
    if m and m.group(4) == m.group(2):
        text = text[: -len(m.group(4))].rstrip()
    # drop a stale "Figure ." pattern if one survived
    text = re.sub(r"^(Figure|Table)\s+\.\s*", r"\1. ", text)
    clear_children(p)
    para = Paragraph(p, doc)
    run = para.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(11)
    run.italic = True
    run.font.color.rgb = GREY
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER


def main():
    cap_re = re.compile(r"^(Figure|Table)\s+\d+(?:\s*\(\d+/\d+\))?[.:]\s")
    for path in sorted(FINAL.glob("C1SE.70_*_DBCAS_ver1.3.docx")):
        doc = docx.Document(str(path))
        for i, section in enumerate(doc.sections):
            if i > 0:
                rebuild_running_parts(section)
        fixed = 0
        for p in doc.element.body.iter(qn("w:p")):
            pPr = p.find(qn("w:pPr"))
            if pPr is None:
                continue
            ps = pPr.find(qn("w:pStyle"))
            style = (ps.get(qn("w:val")) or "").lower() if ps is not None else ""
            if style.startswith("tableoffigures") or style.startswith("toc"):
                continue
            text = Paragraph(p, doc).text.strip()
            if cap_re.match(text) and len(text) < 220:
                normalize_caption(p, doc)
                fixed += 1
        doc.save(str(path))
        print(f"{path.name}: captions normalized={fixed}")


if __name__ == "__main__":
    main()

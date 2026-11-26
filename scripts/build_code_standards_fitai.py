# -*- coding: utf-8 -*-
"""Build DBCAS Code Standards inside the FITAI Code Standard frame.

The FITAI cover, front matter and styles are retained. The FITAI body is
replaced with the measured DBCAS code-standard body. Text on the cover and the
project/document tables is rewritten to C1SE.70 / DBCAS.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path

import docx
from docx.oxml.ns import qn
from docx.shared import Pt

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/submission/final/C1SE.70_CodeStandards_DBCAS_ver1.3.docx"
SRC = ROOT.parent / "Archive/rejected-final-2-20261126/C1SE.70_CodeStandards_DBCAS_ver1.3.docx"


def elements(doc):
    return list(doc.element.body.iterchildren())


def text_of(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t"))).strip()


def is_h1(el, needle=None):
    if el.tag != qn("w:p"):
        return False
    pPr = el.find(qn("w:pPr"))
    if pPr is None:
        return False
    ps = pPr.find(qn("w:pStyle"))
    if ps is None:
        return False
    if (ps.get(qn("w:val")) or "").lower() not in ("heading1", "heading 1"):
        return False
    return needle is None or needle in text_of(el)


def replace_text_everywhere(doc, old, new):
    count = 0
    for t in doc.element.body.iter(qn("w:t")):
        if t.text and old in t.text:
            t.text = t.text.replace(old, new)
            count += 1
    for section in doc.sections:
        for part in (section.header, section.footer):
            for t in part._element.iter(qn("w:t")):
                if t.text and old in t.text:
                    t.text = t.text.replace(old, new)
                    count += 1
    return count


def set_cell(cell, text, size=9):
    cell.text = ""
    p = cell.paragraphs[0]
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)


def main():
    base = docx.Document(str(BASE))
    src = docx.Document(str(SRC))
    bc = elements(base)
    sc = elements(src)
    bstart = next(i for i, el in enumerate(bc) if is_h1(el, "Introduction"))
    # remove FITAI body, keep the final sectPr
    for el in bc[bstart:]:
        if el.tag == qn("w:sectPr"):
            continue
        el.getparent().remove(el)
    # locate the final sectPr in the live body
    live = elements(base)
    sect = next(el for el in reversed(live) if el.tag == qn("w:sectPr"))
    sstart = next(i for i, el in enumerate(sc) if is_h1(el, "1. Purpose and Scope"))
    inserted = 0
    for el in sc[sstart:]:
        if el.tag == qn("w:sectPr"):
            continue
        new = copy.deepcopy(el)
        for s in list(new.iter(qn("w:sectPr"))):
            s.getparent().remove(s)
        sect.addprevious(new)
        inserted += 1

    # cover and table text
    repl = {
        "CMU SE - 450_C1SE.56": "CMU-SE 450_C1SE.70",
        "CMU SE - 450_C1SE.70": "CMU-SE 450_C1SE.70",
        "Version 2.0": "Version 1.3",
        "October 12th, 2025": "November 26th, 2026",
        "FitAI – Smart Health & Fitness Assistant": "DBCAS – AI-Assisted Database Competency Assessment and Skill Gap Analysis",
        "FitAI � Smart Health & Fitness Assistant": "DBCAS – AI-Assisted Database Competency Assessment and Skill Gap Analysis",
        "Submitted by C1SE.56": "Submitted by C1SE.70",
        "MSc. Tran Nhat Vinh": "MSc Viet, Huynh Duc",
        "Tri, Vo Van Duc": "Thu, Nguyen Ngoc Anh - 29209245799",
        "Nhi, Nguyen ": "Nguyen, Nguyen Nhat - 26211227029",
        "Dung - 28209054723": "",
        "Toan, Pham Le Duc - 28211101330": "Truong, Nguyen Quang - 29212730635",
        "Tu, Tran Van - 28214827896": "Do, Nguyen Quoc - 29211156881",
        "Khanh, Truong Bao - 28211101470": "Han, Nguyen Ngoc - 29204423268",
        "FitAI": "DBCAS",
        "SHFA": "DBCAS",
        "C1SE.56": "C1SE.70",
    }
    for old, new in repl.items():
        replace_text_everywhere(base, old, new)

    # front-matter tables
    if len(base.tables) >= 3:
        t = base.tables[0]
        values = ["Code Standards Document", "Do, Nguyen Quoc", "Backend Developer", "26/11/2026",
                  "C1SE.70_CodeStandards_DBCAS_ver1.3.docx",
                  "[OWNER TO PROVIDE: public document URL]", "Project and CMU Program"]
        flat = [c for row in t.rows for c in row.cells]
        for cell, value in zip(flat, values):
            if cell.text.strip() or value:
                set_cell(cell, value)
        t1 = base.tables[1]
        # project information table: update known rows by row label
        for row in t1.rows:
            label = row.cells[0].text.strip().lower()
            if "acronym" in label:
                set_cell(row.cells[1], "DBCAS")
            elif "project title" in label:
                set_cell(row.cells[1], "DBCAS – AI-Assisted Database Competency Assessment and Skill Gap Analysis")
            elif "start" in label:
                set_cell(row.cells[1], "14/09/2026")
                if len(row.cells) > 4:
                    set_cell(row.cells[4], "26/12/2026")
            elif "lead institution" in label:
                set_cell(row.cells[1], "International School, Duy Tan University")
            elif "mentor" in label:
                set_cell(row.cells[1], "MSc Viet, Huynh Duc")
            elif "scrum" in label:
                set_cell(row.cells[1], "Thu, Nguyen Ngoc Anh / Email: 01258319907anhthu@gmail.com / Tel: 0919334040")
            elif "partner" in label:
                set_cell(row.cells[1], "Duy Tan University")
            elif "web url" in label:
                set_cell(row.cells[1], "[OWNER TO PROVIDE: public document or demo URL]")
        # team rows (labels empty in this template)
        team = [("Thu, Nguyen Ngoc Anh", "01258319907anhthu@gmail.com", "0919334040"),
                ("Nguyen, Nguyen Nhat", "nhnguyen240602@gmail.com", "0355772330"),
                ("Truong, Nguyen Quang", "quangtruongtt8@gmail.com", "0349039023"),
                ("Do, Nguyen Quoc", "nguyenquocdodary@gmail.com", "0388496885"),
                ("Han, Nguyen Ngoc", "Hannguyenngoc0506@gmail.com", "0899455605")]
        rows = [r for r in t1.rows if not r.cells[0].text.strip() and len(r.cells) >= 6]
        for row, (name, email, tel) in zip(rows, team):
            set_cell(row.cells[1], name); set_cell(row.cells[3], email); set_cell(row.cells[5], tel)
        t2 = base.tables[2]
        # revision history: keep header, replace/append 1.3
        if len(t2.rows) > 1:
            set_cell(t2.rows[1].cells[0], "1.0"); set_cell(t2.rows[1].cells[1], "18/09/2026")
            set_cell(t2.rows[1].cells[2], "Initial release"); set_cell(t2.rows[1].cells[3], "C1SE.70 Team")
        if len(t2.rows) > 2:
            set_cell(t2.rows[2].cells[0], "1.3"); set_cell(t2.rows[2].cells[1], "26/11/2026")
            set_cell(t2.rows[2].cells[2], "Rebuilt from the FITAI Code Standard frame with measured DBCAS standards")
            set_cell(t2.rows[2].cells[3], "Do, Nguyen Quoc")

    base.save(str(BASE))
    print(f"inserted body elements={inserted}; tables={len(base.tables)} images={len(base.inline_shapes)}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Build the DBCAS Technical Report inside the FITAI AI Documentation frame."""
from __future__ import annotations

import copy
import re
from pathlib import Path

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/submission/final/C1SE.70_TechnicalReport_DBCAS_ver1.3.docx"
SRC = ROOT.parent / "Archive/rejected-final-2-20261126/C1SE.70_TechnicalReport_DBCAS_ver1.3.docx"


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
    return count


def set_cell(cell, text, size=9):
    cell.text = ""
    run = cell.paragraphs[0].add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)


def add_toc(doc, before_element):
    # heading
    hp = OxmlElement("w:p")
    before_element.addprevious(hp)
    hpara = Paragraph(hp, doc)
    hpara.add_run("Table of Contents").bold = True
    # field
    fp = OxmlElement("w:p")
    before_element.addprevious(fp)
    fpara = Paragraph(fp, doc)
    run = fpara.add_run()
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = ' TOC \\o "1-2" \\h \\z \\u '
    sep = OxmlElement("w:fldChar"); sep.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    for el in (begin, instr, sep, end):
        run._r.append(el)
    # static entries so the page is useful before a Word field refresh
    heads = [(p.style.name, p.text.strip()) for p in doc.paragraphs
             if p.style.name.startswith("Heading") and p.text.strip() and p.text.strip() != "Table of Contents"]
    for style, text in heads:
        ep = OxmlElement("w:p")
        before_element.addprevious(ep)
        para = Paragraph(ep, doc)
        try:
            para.style = doc.styles["TOC 1" if style.startswith("Heading 1") else "TOC 2"]
        except KeyError:
            pass
        para.add_run(f"{text}\t1")


def main():
    base = docx.Document(str(BASE))
    src = docx.Document(str(SRC))
    bc = elements(base)
    bstart = next(i for i, el in enumerate(bc) if is_h1(el, "1. Introduction"))
    for el in bc[bstart:]:
        if el.tag == qn("w:sectPr"):
            continue
        el.getparent().remove(el)
    live = elements(base)
    sect = next(el for el in reversed(live) if el.tag == qn("w:sectPr"))
    sc = elements(src)
    sstart = next(i for i, el in enumerate(sc) if is_h1(el, "Abstract"))
    inserted = 0
    for el in sc[sstart:]:
        if el.tag == qn("w:sectPr"):
            continue
        new = copy.deepcopy(el)
        for s in list(new.iter(qn("w:sectPr"))):
            s.getparent().remove(s)
        sect.addprevious(new)
        inserted += 1

    # add TOC immediately before Abstract
    abstract = next(p for p in base.paragraphs if p.text.strip() == "Abstract")
    add_toc(base, abstract._p)

    repl = {
        "FitAI – Smart Health & Fitness Assistant": "DBCAS – AI-Assisted Database Competency Assessment and Skill Gap Analysis",
        "FitAI � Smart Health & Fitness Assistant": "DBCAS – AI-Assisted Database Competency Assessment and Skill Gap Analysis",
        "FitAI": "DBCAS",
        "SHFA": "DBCAS",
        "C1SE.56": "C1SE.70",
        "Version 2.0": "Version 1.3",
        "14/12/2025": "18/09/2026",
        "15/12/2025": "26/11/2026",
        "MSc.Tran Nhat Vinh": "MSc Viet, Huynh Duc",
        "Tri, Vo Van Duc": "Thu, Nguyen Ngoc Anh",
        "Nhi, Nguyen Thi": "Nguyen, Nguyen Nhat",
        "Dung": "",
        "Toan, Pham Le": "Truong, Nguyen Quang",
        "Duc": "",
        "Tu, Tran Van": "Do, Nguyen Quoc",
        "Khanh, Truong": "Han, Nguyen Ngoc",
        "Bao": "",
        "ninjaschool37@gmail.com": "01258319907anhthu@gmail.com",
        "0706007338": "0919334040",
        "dungnhi077@gmail.com": "nhnguyen240602@gmail.com",
        "0848091212": "0355772330",
        "phamlductoan@gmail.com": "quangtruongtt8@gmail.com",
        "0365000847": "0349039023",
        "tranvantu9@dtu.edu.vn": "nguyenquocdodary@gmail.com",
        "0935630298": "0388496885",
        "truongkhanh13572468@": "Hannguyenngoc0506@",
        "gmail.com": "gmail.com",
        "0795781375": "0899455605",
    }
    for old, new in repl.items():
        replace_text_everywhere(base, old, new)

    if len(base.tables) >= 2:
        t = base.tables[0]
        for row in t.rows:
            label = row.cells[0].text.strip().lower()
            if "acronym" in label:
                set_cell(row.cells[1], "DBCAS")
            elif "project title" in label:
                set_cell(row.cells[1], "DBCAS – AI-Assisted Database Competency Assessment and Skill Gap Analysis")
            elif "start" in label:
                set_cell(row.cells[1], "14/09/2026")
                if len(row.cells) > 4:
                    set_cell(row.cells[4], "26/12/2026")
            elif "mentor" in label:
                set_cell(row.cells[1], "MSc Viet, Huynh Duc")
            elif "scrum" in label:
                set_cell(row.cells[1], "Thu, Nguyen Ngoc Anh\nEmail: 01258319907anhthu@gmail.com\nTel: 0919334040")
            elif "web url" in label:
                set_cell(row.cells[1], "[OWNER TO PROVIDE: public document or demo URL]")
        team = [("Thu, Nguyen Ngoc Anh", "01258319907anhthu@gmail.com", "0919334040"),
                ("Nguyen, Nguyen Nhat", "nhnguyen240602@gmail.com", "0355772330"),
                ("Truong, Nguyen Quang", "quangtruongtt8@gmail.com", "0349039023"),
                ("Do, Nguyen Quoc", "nguyenquocdodary@gmail.com", "0388496885"),
                ("Han, Nguyen Ngoc", "Hannguyenngoc0506@gmail.com", "0899455605")]
        rows = [r for r in t.rows if not r.cells[0].text.strip() and len(r.cells) >= 5]
        for row, (name, email, tel) in zip(rows, team):
            set_cell(row.cells[1], name); set_cell(row.cells[3], email); set_cell(row.cells[4], tel)
        t1 = base.tables[1]
        if len(t1.rows) > 1:
            set_cell(t1.rows[1].cells[0], "1.0"); set_cell(t1.rows[1].cells[1], "18/09/2026")
            set_cell(t1.rows[1].cells[2], "Initial release"); set_cell(t1.rows[1].cells[3], "C1SE.70 Team")
        if len(t1.rows) > 2:
            set_cell(t1.rows[2].cells[0], "1.3"); set_cell(t1.rows[2].cells[1], "26/11/2026")
            set_cell(t1.rows[2].cells[2], "Rebuilt from the FITAI AI Documentation frame with measured DBCAS evidence")
            set_cell(t1.rows[2].cells[3], "Do, Nguyen Quoc")

    base.save(str(BASE))
    print(f"inserted body elements={inserted}; tables={len(base.tables)} images={len(base.inline_shapes)}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Rebuild the Code Standards and Technical Report from their confirmed FITAI
frames, keeping the DBCAS body and front-matter values that were measured in the
working copies.  The earlier front-matter edits deleted section breaks, so this
script starts again from the pristine frames and transplants the body with
relationship remapping.
"""
from __future__ import annotations

import copy
import io
import re
from collections import Counter
from pathlib import Path

import docx
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.oxml.ns import nsmap
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.opc.packuri import PackURI
from docx.shared import Pt, RGBColor
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "docs/submission/final"
RECOVERY = ROOT / "docs/submission/recovery/baselines-20261126"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

TITLE = "DBCAS – AI-Assisted Database Competency Assessment and Skill Gap Analysis"

DOCS = [
    {
        "name": "C1SE.70_CodeStandards_DBCAS_ver1.3.docx",
        "header": "C1SE.70 · DBCAS · Code Standards Document",
        "body_h1": "1. Purpose and Scope",
        "frame_h1": "Introduction",
        "tables": 3,
    },
    {
        "name": "C1SE.70_TechnicalReport_DBCAS_ver1.3.docx",
        "header": "C1SE.70 · DBCAS · Technical Report",
        "body_h1": "Abstract",
        "frame_h1": "1. Introduction",
        "tables": 2,
    },
]


def text_of(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def is_h1(el, needle):
    if el.tag != qn("w:p"):
        return False
    pPr = el.find(qn("w:pPr"))
    if pPr is None:
        return False
    ps = pPr.find(qn("w:pStyle"))
    if ps is None:
        return False
    if not (ps.get(qn("w:val")) or "").lower().startswith("heading1"):
        return False
    return needle in text_of(el)


def replace_rels(el, src_doc, dst_doc, cache):
    """Point every copied relationship at a relationship in the destination."""
    for node in el.iter():
        for key, value in list(node.attrib.items()):
            if not key.startswith(R):
                continue
            rel = src_doc.part.rels.get(value)
            if rel is None:
                continue
            cache_key = (id(rel.target_part) if not rel.is_external else rel.target_ref, rel.reltype)
            if cache_key in cache:
                new_id = cache[cache_key]
            elif rel.is_external:
                new_id = dst_doc.part.relate_to(rel.target_ref, rel.reltype, is_external=True)
                cache[cache_key] = new_id
            elif rel.reltype == RT.IMAGE:
                new_id, _ = dst_doc.part.get_or_add_image(io.BytesIO(rel.target_part.blob))
                cache[cache_key] = new_id
            else:
                new_id = dst_doc.part.relate_to(rel.target_part, rel.reltype)
                cache[cache_key] = new_id
            node.set(key, new_id)


def copy_body(src_doc, dst_doc, body_h1):
    src_elements = list(src_doc.element.body.iterchildren())
    start = next(i for i, el in enumerate(src_elements) if is_h1(el, body_h1))
    final_sect = next(i for i in range(len(src_elements) - 1, -1, -1)
                      if src_elements[i].tag == qn("w:sectPr"))
    cache = {}
    copied = []
    for el in src_elements[start:final_sect]:
        new = copy.deepcopy(el)
        # never carry a section break from the working copy
        for sect in list(new.iter(qn("w:sectPr"))):
            sect.getparent().remove(sect)
        replace_rels(new, src_doc, dst_doc, cache)
        copied.append(new)
    return copied


def replace_short_paragraphs(doc, mapping):
    count = 0
    for p in doc.element.body.iter(qn("w:p")):
        full = text_of(p)
        if not full or len(full) > 160:
            continue
        new = full
        for old, value in mapping.items():
            if old in new:
                new = new.replace(old, value)
        if new == full:
            continue
        runs = p.findall(qn("w:r"))
        if not runs:
            continue
        first = True
        for r in runs:
            ts = list(r.iter(qn("w:t")))
            if not ts:
                continue
            if first:
                ts[0].text = new
                for t in ts[1:]:
                    t.text = ""
                first = False
            else:
                for t in ts:
                    t.text = ""
        count += 1
    return count


def replace_runs(doc, mapping):
    count = 0
    for t in doc.element.body.iter(qn("w:t")):
        if not t.text:
            continue
        new = t.text
        for old, value in mapping.items():
            if old in new:
                new = new.replace(old, value)
        if new != t.text:
            t.text = new
            count += 1
    return count


def replace_table(doc, index, new_tbl, dst_doc, src_doc, cache):
    old = doc.tables[index]._tbl
    new = copy.deepcopy(new_tbl)
    replace_rels(new, src_doc, dst_doc, cache)
    old.addprevious(new)
    old.getparent().remove(old)


def clear_part(part):
    el = part._element
    for child in list(el):
        el.remove(child)
    el.append(OxmlElement("w:p"))


def add_run(paragraph, text, bold=False, italic=False, color="44546A", size=9):
    run = paragraph.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    return run


def add_field(paragraph, instr, placeholder="1"):
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), instr)
    run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts"); fonts.set(qn("w:ascii"), "Times New Roman"); fonts.set(qn("w:hAnsi"), "Times New Roman")
    size = OxmlElement("w:sz"); size.set(qn("w:val"), "18")
    color = OxmlElement("w:color"); color.set(qn("w:val"), "44546A")
    rPr.append(fonts); rPr.append(size); rPr.append(color)
    run.append(rPr)
    t = OxmlElement("w:t"); t.text = placeholder
    run.append(t)
    fld.append(run)
    paragraph._p.append(fld)


def fill_header(part, left_text):
    part.is_linked_to_previous = False
    clear_part(part)
    hp = part.paragraphs[0]
    hp.paragraph_format.space_after = Pt(0)
    pPr = hp._p.get_or_add_pPr()
    tabs = OxmlElement("w:tabs")
    tab = OxmlElement("w:tab"); tab.set(qn("w:val"), "right"); tab.set(qn("w:pos"), "8786")
    tabs.append(tab); pPr.append(tabs)
    border = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single"); bottom.set(qn("w:sz"), "6"); bottom.set(qn("w:space"), "1"); bottom.set(qn("w:color"), "44546A")
    border.append(bottom); pPr.append(border)
    add_run(hp, left_text, italic=True)
    hp.add_run().add_tab()
    add_run(hp, "International School Capstone 1 – 2026", italic=True)


def fill_footer(part):
    part.is_linked_to_previous = False
    clear_part(part)
    fp = part.paragraphs[0]
    fp.paragraph_format.space_after = Pt(0)
    pPr = fp._p.get_or_add_pPr()
    tabs = OxmlElement("w:tabs")
    tab = OxmlElement("w:tab"); tab.set(qn("w:val"), "right"); tab.set(qn("w:pos"), "8786")
    tabs.append(tab); pPr.append(tabs)
    add_run(fp, "Do, Nguyen Quoc")
    fp.add_run().add_tab()
    add_run(fp, "Page ")
    add_field(fp, " PAGE ")
    add_run(fp, " of ")
    add_field(fp, " NUMPAGES ")


def style_header_footer(section, left_text, first_section=False):
    if first_section:
        # the cover is the only page in this section that must stay bare
        if section.different_first_page_header_footer:
            clear_part(section.first_page_header)
            clear_part(section.first_page_footer)
            fill_header(section.header, left_text)
            fill_footer(section.footer)
        else:
            clear_part(section.header)
            clear_part(section.footer)
        return
    fill_header(section.header, left_text)
    fill_footer(section.footer)
    if section.different_first_page_header_footer:
        fill_header(section.first_page_header, left_text)
        fill_footer(section.first_page_footer)


def normalise_numbering(doc):
    for i, section in enumerate(doc.sections):
        sectPr = section._sectPr
        pg = sectPr.find(qn("w:pgNumType"))
        if i == 0:
            if pg is None:
                pg = OxmlElement("w:pgNumType")
                cols = sectPr.find(qn("w:cols"))
                if cols is not None:
                    cols.addprevious(pg)
                else:
                    sectPr.append(pg)
            pg.set(qn("w:start"), "1")
        elif pg is not None:
            sectPr.remove(pg)


def dedupe_partnames(doc):
    """Rename parts that ended up with the same package name after cloning."""
    parts = list(doc.part.package.iter_parts())
    used = {str(p.partname).lower() for p in parts}
    seen = set()
    for part in parts:
        name = str(part.partname)
        if name.lower() not in seen:
            seen.add(name.lower())
            continue
        folder, filename = name.rsplit("/", 1)
        stem, _, ext = filename.rpartition(".")
        n = 1
        while True:
            candidate = f"{folder}/{stem}-{n}.{ext}"
            if candidate.lower() not in used:
                break
            n += 1
        part.partname = PackURI(candidate)
        used.add(candidate.lower())


def set_metadata(doc):
    cp = doc.core_properties
    cp.author = "Do, Nguyen Quoc"
    cp.last_modified_by = "Do, Nguyen Quoc"
    cp.title = "C1SE.70 DBCAS"
    cp.subject = "DBCAS submission document"
    cp.comments = ""


def rebuild(spec):
    name = spec["name"]
    src = docx.Document(str(FINAL / name))
    dst = docx.Document(str(RECOVERY / name))

    # replace the frame's front-matter tables with the measured working values
    cache = {}
    for i in range(spec["tables"]):
        replace_table(dst, i, src.tables[i]._tbl, dst, src, cache)

    # remove the frame body, keep the final sectPr
    dst_elements = list(dst.element.body.iterchildren())
    start = next(i for i, el in enumerate(dst_elements) if is_h1(el, spec["frame_h1"]))
    final_sect = next(i for i in range(len(dst_elements) - 1, -1, -1)
                      if dst_elements[i].tag == qn("w:sectPr"))
    for el in dst_elements[start:final_sect]:
        el.getparent().remove(el)

    # insert the measured DBCAS body before the final sectPr
    body = copy_body(src, dst, spec["body_h1"])
    final = next(el for el in reversed(list(dst.element.body.iterchildren()))
                 if el.tag == qn("w:sectPr"))
    for el in body:
        final.addprevious(el)

    # cover and front-matter text
    short = {
        "Date: October 12th, 2025": "Date: November 26th, 2026",
        "Date: December 15th, 2025": "Date: November 26th, 2026",
        "Version 2.0": "Version 1.3",
        "AI ASSIST Document": "Technical Report",
        "FitAI – Smart Health & Fitness Assistant": TITLE,
        "FitAI - Smart Health & Fitness Assistant": TITLE,
        "Tri, Vo Van Duc - 28211101270": "Thu, Nguyen Ngoc Anh - 29209245799",
        "Nhi, Nguyen Thi Dung - 28209054723": "Nguyen, Nguyen Nhat - 26211227029",
        "Toan, Pham Le Duc - 28211101330": "Truong, Nguyen Quang - 29212730635",
        "Tu, Tran Van - 28214827896": "Do, Nguyen Quoc - 29211156881",
        "Khanh, Truong Bao - 28211101470": "Han, Nguyen Ngoc - 29204423268",
        "MSc. Tran Nhat Vinh": "MSc Viet, Huynh Duc",
        "MSc.Tran Nhat Vinh": "MSc Viet, Huynh Duc",
    }
    replace_short_paragraphs(dst, short)
    runs = {
        "CMU SE - 450_C1SE.56": "CMU-SE 450_C1SE.70",
        "Version 2.0": "Version 1.3",
        "Date: October 12th, 2025": "Date: November 26th, 2026",
        "Date: December 15th, 2025": "Date: November 26th, 2026",
        "AI ASSIST Document": "Technical Report",
        "FitAI – Smart Health & Fitness Assistant": TITLE,
        "FitAI - Smart Health & Fitness Assistant": TITLE,
        "FitAI": "DBCAS",
        "SHFA": "DBCAS",
        "C1SE.56": "C1SE.70",
        "MSc. Tran Nhat Vinh": "MSc Viet, Huynh Duc",
        "MSc.Tran Nhat Vinh": "MSc Viet, Huynh Duc",
        "Tri, Vo Van Duc": "Thu, Nguyen Ngoc Anh",
        "Nhi, Nguyen Thi Dung": "Nguyen, Nguyen Nhat",
        "Toan, Pham Le Duc": "Truong, Nguyen Quang",
        "Tu, Tran Van": "Do, Nguyen Quoc",
        "Khanh, Truong Bao": "Han, Nguyen Ngoc",
        "28211101270": "29209245799",
        "28209054723": "26211227029",
        "28211101330": "29212730635",
        "28214827896": "29211156881",
        "28211101470": "29204423268",
        "12 Oct 2025": "18/09/2026",
        "16 Oct 2025": "26/11/2026",
        "14/12/2025": "18/09/2026",
        "15/12/2025": "26/11/2026",
    }
    replace_runs(dst, runs)

    normalise_numbering(dst)
    for i, section in enumerate(dst.sections):
        style_header_footer(section, spec["header"], first_section=(i == 0))
    set_metadata(dst)
    dedupe_partnames(dst)
    dst.save(str(FINAL / name))
    print(f"{name}: body elements={len(body)}, sections={len(dst.sections)}")


if __name__ == "__main__":
    for spec in DOCS:
        rebuild(spec)

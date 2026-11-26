# -*- coding: utf-8 -*-
"""Replace a range of Heading-1 sections in a baseline with reference content.

Keeps the baseline cover/front matter and section properties; the reference is
used only for the body sections that are factually obsolete in the baseline.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import docx
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]


def body_children(doc):
    return list(doc.element.body.iterchildren())


def text_of(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t"))).strip()


def is_heading1(el):
    if el.tag != qn("w:p"):
        return False
    pPr = el.find(qn("w:pPr"))
    if pPr is None:
        return False
    ps = pPr.find(qn("w:pStyle"))
    return ps is not None and (ps.get(qn("w:val")) or "").lower() in ("heading1", "heading 1")


def find_heading(children, needle):
    for i, el in enumerate(children):
        if is_heading1(el) and needle in text_of(el):
            return i
    raise LookupError(needle)


def replace_range(base_path, ref_path, start_needle, end_needle):
    base = docx.Document(str(base_path))
    ref = docx.Document(str(ref_path))
    bc = body_children(base)
    rc = body_children(ref)
    bs = find_heading(bc, start_needle)
    be = find_heading(bc, end_needle)
    rs = find_heading(rc, start_needle)
    re_ = find_heading(rc, end_needle)
    # remove baseline content from start (inclusive) to end (exclusive)
    for el in bc[bs:be]:
        el.getparent().remove(el)
    end_el = be  # index is stale after removals; re-find end in the live body
    live = body_children(base)
    end_el = find_heading(live, end_needle)
    end_element = live[end_el]
    copied_p = copied_t = copied_img = 0
    for el in rc[rs:re_]:
        new = copy.deepcopy(el)
        for sect in list(new.iter(qn("w:sectPr"))):
            sect.getparent().remove(sect)
        if new.tag == qn("w:p"):
            copied_p += 1
            copied_img += len(new.findall(".//" + qn("w:drawing")))
        elif new.tag == qn("w:tbl"):
            copied_t += 1
        end_element.addprevious(new)
    base.save(str(base_path))
    print(f"replaced sections {start_needle!r} .. before {end_needle!r}: paragraphs={copied_p}, tables={copied_t}, images={copied_img}")


if __name__ == "__main__":
    replace_range(
        ROOT / "docs/submission/final/C1SE.70_ProposalDocument_DBCAS_ver1.3.docx",
        ROOT.parent / "Documents/Final-ver1.3/C1SE.70_ProposalDocument_DBCAS_ver1.3.docx",
        "6. Objectives and Scope",
        "15. References",
    )

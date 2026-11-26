# -*- coding: utf-8 -*-
"""Remove the last front-matter blank pages and make page numbering continuous
with an unnumbered cover across all five documents."""
from __future__ import annotations

from pathlib import Path

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "docs/submission/final"
DOCS = [
    "C1SE.70_ProposalDocument_DBCAS_ver1.3.docx",
    "C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx",
    "C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx",
    "C1SE.70_CodeStandards_DBCAS_ver1.3.docx",
    "C1SE.70_TechnicalReport_DBCAS_ver1.3.docx",
]


def clear_first_page(section):
    if not section.different_first_page_header_footer:
        section.different_first_page_header_footer = True
    for part in (section.first_page_header, section.first_page_footer):
        el = part._element
        for child in list(el):
            el.remove(child)
        el.append(OxmlElement("w:p"))


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
            pg.set(qn("w:start"), "0")
        elif pg is not None:
            sectPr.remove(pg)


def main():
    for name in DOCS:
        path = FINAL / name
        doc = docx.Document(str(path))
        normalise_numbering(doc)
        if name.startswith("C1SE.70_Proposal"):
            clear_first_page(doc.sections[0])
        doc.save(str(path))
        print(f"{name}: numbering normalised")
    # explicit page-break paragraphs that only create blank pages before the TOC
    for name, count in (("C1SE.70_ProposalDocument_DBCAS_ver1.3.docx", 2),
                        ("C1SE.70_CodeStandards_DBCAS_ver1.3.docx", 1)):
        path = FINAL / name
        doc = docx.Document(str(path))
        els = list(doc.element.body.iterchildren())
        toc = next(i for i, e in enumerate(els)
                   if e.tag == qn("w:p")
                   and "".join(t.text or "" for t in e.iter(qn("w:t"))).strip().lower() == "table of contents")
        removed = 0
        for e in els[:toc]:
            if removed >= count:
                break
            if e.tag != qn("w:p") or e.findall(".//" + qn("w:sectPr")):
                continue
            text = "".join(t.text or "" for t in e.iter(qn("w:t"))).strip()
            brs = [b.get(qn("w:type")) for b in e.findall(".//" + qn("w:br"))]
            if not text and "page" in brs:
                e.getparent().remove(e)
                removed += 1
        doc.save(str(path))
        print(f"{name}: removed {removed} front-matter page-break paragraphs")
    # cover date on the Database frame
    name = "C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx"
    path = FINAL / name
    doc = docx.Document(str(path))
    changed = 0
    for p in doc.element.body.iter(qn("w:p")):
        text = "".join(t.text or "" for t in p.iter(qn("w:t")))
        if "October 2nd, 2026" not in text:
            continue
        new = text.replace("October 2nd, 2026", "November 26th, 2026")
        if len(text) > 200:
            for t in p.iter(qn("w:t")):
                if t.text and "October 2nd, 2026" in t.text:
                    t.text = t.text.replace("October 2nd, 2026", "November 26th, 2026")
            changed += 1
            continue
        runs = p.findall(qn("w:r"))
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
        changed += 1
    doc.save(str(path))
    print(f"{name}: cover date paragraphs changed={changed}")


if __name__ == "__main__":
    main()

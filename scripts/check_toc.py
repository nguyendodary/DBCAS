# -*- coding: utf-8 -*-
"""Report TOC/List page-number mismatches against the rendered PDFs."""
from __future__ import annotations

import re
from pathlib import Path

import docx
import pymupdf
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "docs/submission/final"
RENDERED = FINAL / "rendered"


def norm(text):
    return re.sub(r"\s+", " ", text.replace("\u2013", "-").replace("\u2014", "-")).strip()


def style_of(p):
    pPr = p.find(qn("w:pPr"))
    if pPr is None:
        return ""
    ps = pPr.find(qn("w:pStyle"))
    return (ps.get(qn("w:val")) or "").lower() if ps is not None else ""


def main():
    total_bad = 0
    for docx_path in sorted(FINAL.glob("C1SE.70_*_DBCAS_ver1.3.docx")):
        pdf_path = RENDERED / docx_path.with_suffix(".pdf").name
        if not pdf_path.exists():
            continue
        pdf = pymupdf.open(pdf_path)
        pages = [norm(p.get_text("text")) for p in pdf]
        printed = {}
        for i, text in enumerate(pages):
            m = re.search(r"Page\s+(\d+)\s+of\s+\d+", text)
            if m:
                printed[i] = int(m.group(1))
        body_start = 0
        for i, text in enumerate(pages[:12]):
            head = text[:400].lower()
            if "table of contents" in head or "list of tables" in head or "list of figures" in head:
                body_start = i + 1
        doc = docx.Document(str(docx_path))
        bad = []
        for p in doc.element.body.iter(qn("w:p")):
            style = style_of(p)
            if not (style.startswith("toc") or style.startswith("tableoffigures")):
                continue
            full = Paragraph(p, doc).text
            if "\t" not in full:
                continue
            parts = full.split("\t")
            if len(parts) >= 3 and re.match(r"^\d+(?:\.\d+)*\.?$", parts[0].strip()):
                title, page = norm(parts[0] + " " + parts[1]), parts[-1].strip()
            else:
                title, page = norm(parts[0]), parts[-1].strip()
            if not page.isdigit() or not title:
                continue
            found = None
            for idx in range(body_start, len(pages)):
                if title[:60].lower() in pages[idx].lower():
                    found = idx + 1
                    break
            if found is None:
                for idx in range(body_start, len(pages)):
                    if title[:35].lower() in pages[idx].lower():
                        found = idx + 1
                        break
            if found is not None:
                shown = printed.get(found - 1, found)
                if shown != int(page):
                    bad.append((title[:60], page, shown))
        pdf.close()
        total_bad += len(bad)
        print(f"{docx_path.name}: {len(bad)} mismatches")
        for item in bad[:8]:
            print("  ", item)
    print("total mismatches", total_bad)


if __name__ == "__main__":
    main()

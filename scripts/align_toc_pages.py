# -*- coding: utf-8 -*-
"""Align cached TOC/TOF page numbers with the rendered PDFs.

Word cannot update the TOC fields on this baseline without hanging, so the
rendered pages are the authority: locate each heading/caption in the PDF and
write that page number into the last numeric run of the corresponding entry.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import docx
import pymupdf
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "docs/submission/final"
RENDERED = FINAL / "rendered"


def normalize(text):
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u2011", "-")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def entry_texts(p):
    return [t.text or "" for t in p.iter(qn("w:t"))]


def update_entry(p, page):
    ts = list(p.iter(qn("w:t")))
    if not ts:
        return False
    # the last text run that is only digits is the cached page number
    for t in reversed(ts):
        value = (t.text or "").strip()
        if value.isdigit():
            t.text = str(page)
            return True
    # otherwise append a page number at the end
    t = ts[-1]
    t.text = (t.text or "") + str(page)
    return True


def main():
    report = {}
    for docx_path in sorted(FINAL.glob("C1SE.70_*_DBCAS_ver1.3.docx")):
        pdf_path = RENDERED / docx_path.with_suffix(".pdf").name
        if not pdf_path.exists():
            continue
        pdf = pymupdf.open(pdf_path)
        pages = [normalize(page.get_text("text")) for page in pdf]
        printed = {}
        for i, text in enumerate(pages):
            m = re.search(r"Page\s+(\d+)\s+of\s+\d+", text)
            if m:
                printed[i] = int(m.group(1))
        # body starts after the last page that contains a TOC/List heading near the top
        body_start = 0
        for i, text in enumerate(pages[:12]):
            head = text[:400].lower()
            if "table of contents" in head or "list of tables" in head or "list of figures" in head:
                body_start = i + 1
        doc = docx.Document(str(docx_path))
        updated = 0
        unmatched = []
        for p in doc.element.body.iter(qn("w:p")):
            pPr = p.find(qn("w:pPr"))
            if pPr is None:
                continue
            ps = pPr.find(qn("w:pStyle"))
            if ps is None:
                continue
            style = (ps.get(qn("w:val")) or "").lower()
            if not (style.startswith("toc") or style.startswith("tableoffigures")):
                continue
            full = Paragraph(p, doc).text
            if not full or full.strip().lower() == "table of contents":
                continue
            parts = full.split("\t")
            if len(parts) >= 3 and re.match(r"^\d+(?:\.\d+)*\.?$", parts[0].strip()):
                title = normalize(parts[0] + " " + parts[1])
                page_text = parts[-1].strip()
            elif len(parts) >= 2:
                title = normalize(parts[0])
                page_text = parts[-1].strip()
            else:
                m = re.match(r"^(.*?)(\d+)$", normalize(full))
                if not m:
                    continue
                title, page_text = m.group(1).strip(" ."), m.group(2)
            if len(title) < 3 or not page_text.isdigit():
                continue
            found = None
            for idx in range(body_start, len(pages)):
                page_text = pages[idx]
                if title[:60].lower() in page_text.lower():
                    found = idx + 1
                    break
            if found is None:
                # try a shorter prefix
                short = title[:35]
                for idx in range(body_start, len(pages)):
                    if short.lower() in pages[idx].lower():
                        found = idx + 1
                        break
            if found is None:
                unmatched.append(title[:80])
                continue
            if update_entry(p, printed.get(found - 1, found)):
                updated += 1
        doc.save(str(docx_path))
        pdf.close()
        report[docx_path.name] = {"updated": updated, "unmatched": unmatched[:20]}
        print(f"{docx_path.name}: updated {updated}; unmatched {len(unmatched)}")
        if unmatched:
            print("  first unmatched:", unmatched[:5])
    (FINAL / "verification" / "toc-alignment.json").write_text(json.dumps(report, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

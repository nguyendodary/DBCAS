# -*- coding: utf-8 -*-
"""Rewrite the static List of Figures/Tables entries from the body captions."""
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


def norm(text):
    return re.sub(r"\s+", " ", text.replace("\u2013", "-").replace("\u2014", "-")).strip()


def style_of(p):
    pPr = p.find(qn("w:pPr"))
    if pPr is None:
        return ""
    ps = pPr.find(qn("w:pStyle"))
    return (ps.get(qn("w:val")) or "").lower() if ps is not None else ""


def main():
    report = {}
    for docx_path in sorted(FINAL.glob("C1SE.70_*_DBCAS_ver1.3.docx")):
        pdf_path = RENDERED / docx_path.with_suffix(".pdf").name
        if not pdf_path.exists():
            continue
        pdf = pymupdf.open(pdf_path)
        pages = [norm(page.get_text("text")) for page in pdf]
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
        cap_re = re.compile(r"^(Figure|Table)\s+(?:A\.)?\d+(?:\s*\(\d+/\d+\))?[.:]\s*")
        body_figs, body_tabs = [], []
        for p in doc.element.body.iter(qn("w:p")):
            style = style_of(p)
            if style not in ("caption", "normal", ""):
                continue
            text = norm(Paragraph(p, doc).text)
            if len(text) > 220 or not cap_re.match(text):
                continue
            if text.startswith("Figure"):
                body_figs.append(text)
            else:
                body_tabs.append(text)
        list_figs, list_tabs = [], []
        for p in doc.element.body.iter(qn("w:p")):
            if style_of(p) != "tableoffigures":
                continue
            text = norm(Paragraph(p, doc).text)
            if cap_re.match(text):
                if text.startswith("Figure"):
                    list_figs.append(p)
                else:
                    list_tabs.append(p)

        def page_for(title):
            needle = title[:60].lower()
            for idx in range(body_start, len(pages)):
                if needle in pages[idx].lower():
                    return idx + 1
            needle = title[:35].lower()
            for idx in range(body_start, len(pages)):
                if needle in pages[idx].lower():
                    return idx + 1
            return None

        def rewrite(p, title, page):
            if page is None:
                return False
            for child in list(p):
                if child.tag != qn("w:pPr"):
                    p.remove(child)
            para = Paragraph(p, doc)
            run = para.add_run(title)
            run.add_tab()
            para.add_run(str(page))
            return True

        changed = 0
        for entries, captions in ((list_figs, body_figs), (list_tabs, body_tabs)):
            for p, title in zip(entries, captions):
                page = page_for(title)
                if page is not None:
                    page = printed.get(page - 1, page)
                if rewrite(p, title, page):
                    changed += 1
        doc.save(str(docx_path))
        pdf.close()
        report[docx_path.name] = {"figure_entries": len(list_figs), "table_entries": len(list_tabs), "rewritten": changed}
        print(f"{docx_path.name}: figures={len(list_figs)} tables={len(list_tabs)} rewritten={changed}")
    (FINAL / "verification" / "list-alignment.json").write_text(json.dumps(report, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

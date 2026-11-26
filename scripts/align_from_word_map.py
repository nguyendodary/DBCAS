# -*- coding: utf-8 -*-
"""Align TOC and List page numbers from Word's own pagination map.

The map is produced by scripts/word_page_map.ps1.  Word reports the physical
page; the documents use an unnumbered cover with page numbering starting at 0,
so the printed TOC number is physical - 1.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import docx
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "docs/submission/final"
DOCS = [
    "C1SE.70_ProposalDocument_DBCAS_ver1.3.docx",
    "C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx",
    "C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx",
    "C1SE.70_CodeStandards_DBCAS_ver1.3.docx",
    "C1SE.70_TechnicalReport_DBCAS_ver1.3.docx",
]


def norm(text):
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def strip_number(text):
    return re.sub(r"^(?:\d+(?:\.\d+)*\.?|[a-z]\.\d+\.?)\s+", "", text).strip()


def style_of(p):
    pPr = p.find(qn("w:pPr"))
    if pPr is None:
        return ""
    ps = pPr.find(qn("w:pStyle"))
    return (ps.get(qn("w:val")) or "").lower() if ps is not None else ""


def update_entry(p, page):
    ts = list(p.iter(qn("w:t")))
    for t in reversed(ts):
        if (t.text or "").strip().isdigit():
            t.text = str(page)
            return True
    if ts:
        ts[-1].text = (ts[-1].text or "") + str(page)
        return True
    return False


def rebuild_entry(p, doc, title, page):
    for child in list(p):
        if child.tag != qn("w:pPr"):
            p.remove(child)
    para = Paragraph(p, doc)
    run = para.add_run(title)
    run.add_tab()
    para.add_run(str(page))


def best_match(title, items):
    target = norm(title)
    target_un = norm(strip_number(title))
    candidates = []
    for item in items:
        text = norm(item["text"])
        if text == target or norm(strip_number(item["text"])) == target_un:
            candidates.append(item)
    if not candidates:
        for item in items:
            text = norm(item["text"])
            if target and (text.startswith(target[:60]) or target.startswith(text[:60])):
                candidates.append(item)
    if not candidates:
        return None
    return candidates[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--maps", default=str(FINAL / "verification" / "word-maps"))
    args = parser.parse_args()
    map_dir = Path(args.maps)
    report = {}
    for name in DOCS:
        stem = name.replace("C1SE.70_", "").replace("_DBCAS_ver1.3.docx", "")
        map_path = map_dir / f"{stem}.json"
        if not map_path.exists():
            print("missing map", map_path)
            continue
        items = json.loads(map_path.read_text(encoding="utf-8"))
        heads = [i for i in items if i["kind"] in ("h1", "h2")]
        caps = [i for i in items if i["kind"] == "caption"
                and len(i["text"]) > 16
                and not re.fullmatch(r"(?:Table|Figure)\s+(?:A\.)?\d+(?:\s*\(\d+/\d+\))?", i["text"].strip())]
        path = FINAL / name
        doc = docx.Document(str(path))
        updated = 0
        unmatched = []
        for p in doc.element.body.iter(qn("w:p")):
            style = style_of(p)
            if not (style.startswith("toc") or style == "tableoffigures"):
                continue
            full = Paragraph(p, doc).text
            if "\t" not in full:
                continue
            parts = full.split("\t")
            if len(parts) >= 3 and re.match(r"^\d+(?:\.\d+)*\.?$", parts[0].strip()):
                title = (parts[0] + " " + parts[1]).strip()
            else:
                title = parts[0].strip()
            page_text = parts[-1].strip()
            if not title or not page_text.isdigit():
                continue
            pool = heads if style.startswith("toc") else caps
            item = best_match(title, pool)
            if item is None:
                unmatched.append(title[:90])
                continue
            new_page = max(item["page"] - 1, 1)
            if update_entry(p, new_page):
                updated += 1
            else:
                rebuild_entry(p, doc, title, new_page)
                updated += 1
        doc.save(str(path))
        report[name] = {"updated": updated, "unmatched": unmatched[:30]}
        print(f"{name}: updated={updated}, unmatched={len(unmatched)}")
        for item in unmatched[:6]:
            print("  ", item)
    (FINAL / "verification" / "toc-from-word.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()

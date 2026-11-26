# -*- coding: utf-8 -*-
"""Check TOC and List page numbers against the Word pagination map."""
from __future__ import annotations

import json
import re
from pathlib import Path

import docx
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "docs/submission/final"
MAPS = FINAL / "verification" / "word-maps"


def norm(text):
    return re.sub(r"\s+", " ", text.replace("\u2013", "-").replace("\u2014", "-")).strip().lower()


def strip_number(text):
    return re.sub(r"^(?:\d+(?:\.\d+)*\.?|[a-z]\.\d+\.?)\s+", "", text).strip()


def style_of(p):
    pPr = p.find(qn("w:pPr"))
    if pPr is None:
        return ""
    ps = pPr.find(qn("w:pStyle"))
    return (ps.get(qn("w:val")) or "").lower() if ps is not None else ""


def match(title, items):
    target = norm(title)
    un = norm(strip_number(title))
    for item in items:
        if norm(item["text"]) == target or norm(strip_number(item["text"])) == un:
            return item
    for item in items:
        text = norm(item["text"])
        if target and (text.startswith(target[:60]) or target.startswith(text[:60])):
            return item
    return None


def main():
    total = 0
    report = {}
    for path in sorted(FINAL.glob("C1SE.70_*_DBCAS_ver1.3.docx")):
        stem = path.name.replace("C1SE.70_", "").replace("_DBCAS_ver1.3.docx", "")
        map_path = MAPS / f"{stem}.json"
        if not map_path.exists():
            print(path.name, "map missing")
            continue
        items = json.loads(map_path.read_text(encoding="utf-8"))
        heads = [i for i in items if i["kind"] in ("h1", "h2")]
        caps = [i for i in items if i["kind"] == "caption"
                and len(i["text"]) > 16
                and not re.fullmatch(r"(?:Table|Figure)\s+(?:A\.)?\d+(?:\s*\(\d+/\d+\))?", i["text"].strip())]
        doc = docx.Document(str(path))
        bad = []
        checked = 0
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
            page = parts[-1].strip()
            if not title or not page.isdigit():
                continue
            item = match(title, heads if style.startswith("toc") else caps)
            if item is None:
                bad.append((title[:70], page, "unmatched"))
                continue
            checked += 1
            expected = max(item["page"] - 1, 1)
            if int(page) != expected:
                bad.append((title[:70], page, expected))
        total += len(bad)
        report[path.name] = {"checked": checked, "mismatches": len(bad), "details": bad[:20]}
        print(f"{path.name}: {len(bad)} mismatches ({checked} checked)")
        for row in bad[:8]:
            print("  ", row)
    report["_total_mismatches"] = total
    (FINAL / "verification" / "toc-verification.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print("total", total)


if __name__ == "__main__":
    main()

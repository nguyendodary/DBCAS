# -*- coding: utf-8 -*-
"""Focused, hash-grouped inventory of the five-document baselines."""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path

import docx
from docx.oxml.ns import qn

WS = Path(r"C:\Users\kudot\Downloads\proposal test")
REPO = WS / "DBCAS"
OUT_MD = REPO / "docs/agent/freeze-logs/baseline-inventory-focused-20261126.md"
OUT_JSON = REPO / "docs/agent/freeze-logs/baseline-inventory-focused-20261126.json"

DIRS = [
    WS / "Documents",
    WS / "Archive",
    WS / "FITAI - Documents",
    REPO / "docs/academic",
    REPO / "docs/submission",
    REPO / "docs/submission/final",
    REPO / "docs/submission/recovery/backups",
    REPO / "docs/submission/recovery/staging",
    REPO / "_review",
]


def rel(p: Path):
    try:
        return str(p.relative_to(WS))
    except ValueError:
        return str(p)


def pages_and_words(p: Path):
    pages = words = None
    try:
        with zipfile.ZipFile(p) as z:
            if "docProps/app.xml" in z.namelist():
                s = z.read("docProps/app.xml").decode("utf-8", "ignore")
                m = re.search(r"<Pages>(\d+)</Pages>", s)
                pages = int(m.group(1)) if m else None
                m = re.search(r"<Words>(\d+)</Words>", s)
                words = int(m.group(1)) if m else None
    except Exception:
        pass
    return pages, words


def pdf_pages(p: Path):
    q = p.with_suffix(".pdf")
    if not q.exists():
        return None
    try:
        import pymupdf
        d = pymupdf.open(q); n = d.page_count; d.close(); return n
    except Exception:
        return None


def toc3(p: Path):
    try:
        d = docx.Document(str(p))
    except Exception as e:
        return [f"UNREADABLE: {e}"]
    out = []
    for para in d.element.body.iter(qn("w:p")):
        pPr = para.find(qn("w:pPr"))
        if pPr is None:
            continue
        ps = pPr.find(qn("w:pStyle"))
        if ps is None:
            continue
        style = (ps.get(qn("w:val")) or "").lower()
        if not re.match(r"toc[1-9]", style):
            continue
        text = "".join(t.text or "" for t in para.iter(qn("w:t"))).strip()
        if text:
            out.append(text)
        if len(out) == 3:
            break
    return out


def sections(p: Path):
    try:
        d = docx.Document(str(p))
        return len(d.sections), sum(1 for s in d.sections if s.orientation == 1), len(d.inline_shapes)
    except Exception:
        return None, None, None


def main():
    files = set()
    for root in DIRS:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file() or p.name.startswith("~$"):
                continue
            low = p.name.lower()
            if p.suffix.lower() == ".docx":
                files.add(p.resolve())
            elif p.suffix.lower() == ".txt" and ("c1se.70" in low or "srs" in low):
                files.add(p.resolve())
    # root documents
    for p in WS.glob("*.docx"):
        files.add(p.resolve())
    for p in WS.glob("*.txt"):
        files.add(p.resolve())

    groups = defaultdict(list)
    for p in files:
        try:
            h = hashlib.sha256(p.read_bytes()).hexdigest()
        except Exception:
            h = f"ERR:{p}"
        groups[h].append(p)

    records = []
    for h, paths in groups.items():
        paths = sorted(paths, key=lambda p: rel(p).lower())
        rep = paths[0]
        rec = {
            "sha256": h[:16],
            "representative": rel(rep),
            "also_at": [rel(x) for x in paths[1:]],
            "copies": len(paths),
            "modified": rep.stat().st_mtime,
            "size": rep.stat().st_size,
        }
        if rep.suffix.lower() == ".docx":
            pages, words = pages_and_words(rep)
            title = author = modified = None
            try:
                d = docx.Document(str(rep))
                title = d.core_properties.title
                author = d.core_properties.author
                modified = str(d.core_properties.modified)
            except Exception:
                pass
            nsec, land, imgs = sections(rep)
            rec.update({"pages": pages, "pdf_pages": pdf_pages(rep), "words": words,
                        "title": title, "author": author, "core_modified": modified,
                        "toc": toc3(rep), "sections": nsec, "landscape": land, "images": imgs})
        else:
            text = rep.read_text(encoding="utf-8", errors="replace")
            rec.update({"pages": None, "pdf_pages": None,
                        "toc": [x.strip() for x in text.splitlines() if x.strip()][:3]})
        records.append(rec)

    records.sort(key=lambda r: r["representative"].lower())
    OUT_JSON.write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = ["# Focused baseline inventory — hash-grouped",
             "", "Read-only inventory, 2026-11-26. Identical files are grouped; the",
             "representative path is listed and duplicates are in `also at`.",
             "Pages are cached Word `docProps/app.xml`; `PDF` is the same-name export.",
             "", "| # | Path (representative) | Copies | Modified | Pages | PDF | Words | Version/title | TOC 1–3 | Also at |",
             "|---:|---|---:|---|---:|---:|---:|---|---|---|"]
    for i, r in enumerate(records, 1):
        title = (r.get("title") or "").replace("|", "/")[:70]
        toc = " / ".join(r.get("toc") or []).replace("|", "/")[:150]
        also = "<br>".join(r.get("also_at") or [])[:250]
        lines.append(
            f"| {i} | `{r['representative']}` | {r['copies']} | {r['modified']:.0f} | "
            f"{r.get('pages') if r.get('pages') is not None else 'n/a'} | "
            f"{r.get('pdf_pages') if r.get('pdf_pages') is not None else 'n/a'} | "
            f"{r.get('words') if r.get('words') is not None else 'n/a'} | {title} | {toc} | {also} |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"files={len(files)} unique={len(records)}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()

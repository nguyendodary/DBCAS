# -*- coding: utf-8 -*-
"""Inventory every candidate .docx/.txt baseline and dump a review table.

Read-only. Writes docs/agent/freeze-logs/baseline-inventory-20261126.md and .json
"""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import docx
from docx.oxml.ns import qn

WS = Path(r"C:\Users\kudot\Downloads\proposal test")
REPO = WS / "DBCAS"
OUT_MD = REPO / "docs/agent/freeze-logs/baseline-inventory-20261126.md"
OUT_JSON = REPO / "docs/agent/freeze-logs/baseline-inventory-20261126.json"

PATTERNS = [
    (WS / "Documents", "**/*.docx"),
    (WS / "Documents", "**/*.txt"),
    (WS / "Archive", "**/*.docx"),
    (WS / "Archive", "**/*.txt"),
    (WS / "FITAI - Documents", "**/*.docx"),
    (WS / "FITAI - Documents", "**/*.txt"),
    (WS, "*.docx"),
    (WS, "*.txt"),
    (REPO / "docs/academic", "*.docx"),
    (REPO / "docs/submission", "*.docx"),
    (REPO / "docs/submission/final", "*.docx"),
    (REPO / "docs/submission/recovery/backups", "*.docx"),
    (REPO / "docs/submission/recovery/staging", "*.docx"),
    (REPO / "_review", "**/*.docx"),
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(WS))
    except ValueError:
        return str(path)


def app_props(path: Path):
    pages = words = None
    try:
        with zipfile.ZipFile(path) as z:
            if "docProps/app.xml" in z.namelist():
                text = z.read("docProps/app.xml").decode("utf-8", "ignore")
                m = re.search(r"<Pages>(\d+)</Pages>", text)
                if m:
                    pages = int(m.group(1))
                m = re.search(r"<Words>(\d+)</Words>", text)
                if m:
                    words = int(m.group(1))
    except Exception:
        pass
    return pages, words


def pdf_pages(path: Path):
    pdf = path.with_suffix(".pdf")
    if not pdf.exists():
        return None
    try:
        import pymupdf
        d = pymupdf.open(pdf)
        n = d.page_count
        d.close()
        return n
    except Exception:
        return None


def toc_lines(path: Path):
    try:
        d = docx.Document(str(path))
    except Exception as error:
        return [f"UNREADABLE: {error}"]
    out = []
    for p in d.element.body.iter(qn("w:p")):
        pPr = p.find(qn("w:pPr"))
        if pPr is None:
            continue
        ps = pPr.find(qn("w:pStyle"))
        if ps is None:
            continue
        style = (ps.get(qn("w:val")) or "").lower()
        if not re.match(r"toc[1-9]", style):
            continue
        text = "".join(t.text or "" for t in p.iter(qn("w:t"))).strip()
        if text:
            out.append(text)
        if len(out) >= 3:
            break
    return out


def sec_info(path: Path):
    try:
        d = docx.Document(str(path))
        landscape = sum(1 for s in d.sections if s.orientation == 1)
        return len(d.sections), landscape, len(d.inline_shapes)
    except Exception:
        return None, None, None


def txt_info(path: Path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        text = ""
    lines = [line.strip() for line in text.splitlines() if line.strip()][:3]
    return lines


def main():
    files = {}
    for root, pattern in PATTERNS:
        if not root.exists():
            continue
        for path in root.glob(pattern):
            if not path.is_file() or path.name.startswith("~$"):
                continue
            files[path.resolve()] = path
    rows = []
    for path in sorted(files.values(), key=lambda p: rel(p).lower()):
        stat = path.stat()
        row = {
            "path": rel(path),
            "name": path.name,
            "suffix": path.suffix.lower(),
            "modified": stat.st_mtime,
            "size": stat.st_size,
        }
        if path.suffix.lower() == ".docx":
            pages, words = app_props(path)
            core_title = core_author = core_modified = None
            try:
                d = docx.Document(str(path))
                core_title = d.core_properties.title
                core_author = d.core_properties.author
                core_modified = str(d.core_properties.modified)
            except Exception:
                pass
            sections, landscape, images = sec_info(path)
            row.update({
                "pages": pages,
                "pdf_pages": pdf_pages(path),
                "words": words,
                "title": core_title,
                "author": core_author,
                "core_modified": core_modified,
                "toc": toc_lines(path),
                "sections": sections,
                "landscape": landscape,
                "images": images,
            })
        else:
            row.update({"pages": None, "pdf_pages": None, "toc": txt_info(path)})
        rows.append(row)

    OUT_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = [
        "# Baseline inventory — all .docx/.txt candidates",
        "",
        "Generated 2026-11-26, read-only. Pages are the cached Word `docProps/app.xml`",
        "value; `PDF` is the page count of a same-name PDF when one exists. TOC is the",
        "first three `TOC1` entries in the DOCX. Nothing was modified.",
        "",
        "| # | Path | Modified | Pages | PDF | Version/title | TOC 1–3 |",
        "|---:|---|---|---:|---:|---|---|",
    ]
    for i, row in enumerate(rows, 1):
        if row["suffix"] == ".docx":
            version = (row.get("title") or "").strip()
            toc = " / ".join(row.get("toc") or []) or "no TOC"
        else:
            version = "plain text"
            toc = " / ".join(row.get("toc") or []) or "empty"
        lines.append(
            f"| {i} | `{row['path']}` | {row['modified']:.0f} | "
            f"{row.get('pages') if row.get('pages') is not None else 'n/a'} | "
            f"{row.get('pdf_pages') if row.get('pdf_pages') is not None else 'n/a'} | "
            f"{version[:80]} | {toc[:160]} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_MD} ({len(rows)} files)")
    print(f"wrote {OUT_JSON}")


if __name__ == "__main__":
    main()

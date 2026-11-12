# -*- coding: utf-8 -*-
"""Dump paragraph/table text and embedded image metadata for the three v1.2 docs."""
import json
import sys
import zipfile
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[4]
ACA = ROOT / "docs/academic"
FILES = [
    ("proposal", "C1SE.70_ProposalDocument_DBCAS_ver1.2.docx"),
    ("architecture", "C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx"),
    ("database", "C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx"),
]
OUT = Path(__file__).resolve().parent


def para_text(p):
    return "".join(n.text or "" for n in p._p.iter(qn("w:t")))


def main():
    manifest = {}
    for slug, name in FILES:
        path = ACA / name
        doc = Document(str(path))
        rows = []
        for i, p in enumerate(doc.paragraphs):
            t = para_text(p).strip()
            if t:
                rows.append({"i": i, "style": p.style.name if p.style else "", "text": t})
        tables = []
        for ti, table in enumerate(doc.tables):
            for ri, row in enumerate(table.rows):
                cells = [" ".join(para_text(p).strip() for p in c.paragraphs).strip() for c in row.cells]
                tables.append({"table": ti, "row": ri, "cells": cells})
        with open(OUT / f"{slug}-paragraphs.json", "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
        with open(OUT / f"{slug}-tables.json", "w", encoding="utf-8") as f:
            json.dump(tables, f, ensure_ascii=False, indent=1)
        with open(OUT / f"{slug}-text.txt", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(f"[{r['i']}] ({r['style']}) {r['text']}\n")

        # media + header parts
        with zipfile.ZipFile(path) as z:
            media = []
            for n in z.namelist():
                if n.startswith("word/media/"):
                    b = z.read(n)
                    media.append({"name": n, "bytes": len(b), "sha256": __import__("hashlib").sha256(b).hexdigest(),
                                  "magic": b[:8].hex()})
            headers = [n for n in z.namelist() if n.startswith("word/header") or n.startswith("word/footer")]
            manifest[slug] = {"file": name, "paragraphs": len(doc.paragraphs),
                              "media": media, "headers_footers": headers,
                              "sections": len(doc.sections)}
    with open(OUT / "packages.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: {"paragraphs": v["paragraphs"], "media": len(v["media"]),
                          "sections": v["sections"]} for k, v in manifest.items()}, indent=1))


if __name__ == "__main__":
    main()

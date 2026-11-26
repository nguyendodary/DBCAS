# -*- coding: utf-8 -*-
"""Export every embedded body figure as its own PNG for owner review."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import docx
from docx.oxml.ns import qn
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "docs/submission/final"
OUT = FINAL / "verification" / "figures"
DOCS = ["ProposalDocument", "ArchitectureDesign", "DatabaseDesign", "CodeStandards", "TechnicalReport"]


def slug(text):
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")
    return text[:80] or "figure"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = ["# Figure package — owner review", "",
                "Every embedded body figure is exported as a standalone PNG. The table",
                "lists the document, caption, file and pixel size.", "",
                "| Document | Figure | File | Pixels |", "|---|---|---|---|"]
    for name in DOCS:
        doc = docx.Document(str(FINAL / f"C1SE.70_{name}_DBCAS_ver1.3.docx"))
        paras = doc.paragraphs
        for i, p in enumerate(paras):
            blips = list(p._p.iter(qn("a:blip")))
            if not blips:
                continue
            rid = blips[0].get(qn("r:embed"))
            if not rid or rid not in doc.part.rels:
                continue
            caption = ""
            # a caption may sit before the image (Code Standards) or after it;
            # choose the nearest one so a previous figure's caption is not reused
            cap_re = re.compile(r"^(?:Figure|Table)\s+(?:A\.)?\d+(?:\s*\(\d+/\d+\))?[.:]\s")
            candidates = []
            for j in range(max(0, i - 3), min(len(paras), i + 4)):
                if j == i:
                    continue
                if cap_re.match(paras[j].text.strip()):
                    candidates.append((abs(j - i), j, paras[j].text.strip()))
            if candidates:
                caption = min(candidates, key=lambda item: (item[0], -item[1]))[2]
            if not caption:
                continue
            part = doc.part.rels[rid].target_part
            blob = part.blob
            h = hashlib.sha256(blob).hexdigest()[:10]
            ext = Path(part.partname).suffix.lower() or ".png"
            filename = f"{name}-{slug(caption)}-{h}{ext}"
            path = OUT / filename
            path.write_bytes(blob)
            try:
                im = Image.open(path)
                size = f"{im.width}×{im.height}"
            except Exception:
                size = "n/a"
            manifest.append(f"| {name} | {caption[:120]} | `{filename}` | {size} |")
    (FINAL / "verification" / "figure-manifest.md").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    print(f"exported {len(manifest)-7} figures to {OUT}")


if __name__ == "__main__":
    main()

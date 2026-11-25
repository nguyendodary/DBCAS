# -*- coding: utf-8 -*-
"""Dump structure of a DOCX baseline: paragraphs, styles, tables, sections, images.

Usage: py docs/submission/tools/inspect_baseline.py <docx> [out.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


def image_rids(container):
    rids = []
    for blip in container._element.iter(qn("a:blip")):
        rid = blip.get(qn("r:embed"))
        if rid:
            rids.append(rid)
    return rids


def main():
    src = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".inspect.json")
    d = docx.Document(str(src))
    rels = d.part.rels
    paras = []
    for i, p in enumerate(d.paragraphs):
        text = p.text.strip()
        if not text:
            continue
        runs = []
        for r in p.runs:
            if r.text.strip():
                runs.append({
                    "text": r.text,
                    "size": r.font.size.pt if r.font.size else None,
                    "bold": r.bold,
                    "italic": r.italic,
                    "font": r.font.name,
                    "color": str(r.font.color.rgb) if r.font.color and r.font.color.rgb else None,
                })
        paras.append({
            "i": i,
            "style": p.style.name,
            "align": str(p.alignment),
            "text": text,
            "runs": runs,
            "images": [rels[x].target_ref for x in image_rids(p) if x in rels],
        })
    tables = []
    for ti, t in enumerate(d.tables):
        rows = []
        for r in t.rows[:4]:
            rows.append([c.text.strip().replace("\n", " ")[:80] for c in r.cells])
        tables.append({"i": ti, "rows": len(t.rows), "cols": len(t.columns), "head": rows})
    sections = []
    for si, s in enumerate(d.sections):
        sections.append({
            "i": si,
            "start": s.start_type,
            "orientation": str(s.orientation),
            "page_cm": [round(s.page_width.cm, 2), round(s.page_height.cm, 2)],
            "margins_cm": [round(s.left_margin.cm, 2), round(s.right_margin.cm, 2),
                           round(s.top_margin.cm, 2), round(s.bottom_margin.cm, 2)],
            "header": " | ".join(p.text for p in s.header.paragraphs if p.text.strip()),
            "footer": " | ".join(p.text for p in s.footer.paragraphs if p.text.strip()),
        })
    core = d.core_properties
    result = {
        "file": str(src),
        "size": src.stat().st_size,
        "core": {
            "author": core.author,
            "last_modified_by": core.last_modified_by,
            "title": core.title,
            "subject": core.subject,
            "created": str(core.created),
            "modified": str(core.modified),
            "revision": core.revision,
        },
        "sections": sections,
        "paragraphs": paras,
        "tables": tables,
        "inline_shapes": [
            {"width_cm": round(s.width.cm, 2), "height_cm": round(s.height.cm, 2)}
            for s in d.inline_shapes
        ],
    }
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {out} ({len(paras)} paragraphs, {len(tables)} tables, {len(sections)} sections)")


if __name__ == "__main__":
    main()

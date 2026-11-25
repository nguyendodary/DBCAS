# -*- coding: utf-8 -*-
"""Extract DOCX body text in document order, with paragraph and table markers."""
from __future__ import annotations

import sys
from pathlib import Path

import docx
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn


def iter_block_items(parent):
    body = parent.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, parent)
        elif child.tag == qn("w:tbl"):
            yield Table(child, parent)


def main():
    src = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2])
    d = docx.Document(str(src))
    lines = []
    pi = ti = 0
    for block in iter_block_items(d):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if text:
                lines.append(f"[P{pi:04d}|{block.style.name}] {text}")
            pi += 1
        else:
            lines.append(f"[TABLE {ti} rows={len(block.rows)} cols={len(block.columns)}]")
            for ri, row in enumerate(block.rows):
                cells = []
                for c in row.cells:
                    cells.append(c.text.strip().replace("\n", " / "))
                lines.append(f"  R{ri}: " + " || ".join(cells))
            lines.append("[/TABLE]")
            ti += 1
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out} ({len(lines)} lines)")


if __name__ == "__main__":
    main()

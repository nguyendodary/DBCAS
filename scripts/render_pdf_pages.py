# -*- coding: utf-8 -*-
"""Render every page of a PDF to PNG and build labelled contact sheets.

    python render_pdf_pages.py <pdf> <outdir> [dpi] [--no-sheets]
"""
import sys
from pathlib import Path

import pymupdf as fitz
from PIL import Image, ImageDraw

THUMB_W = 300
COLS, ROWS = 5, 4


def main():
    pdf, outdir = Path(sys.argv[1]), Path(sys.argv[2])
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 110
    outdir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    paths = []
    for i, page in enumerate(doc, 1):
        pix = page.get_pixmap(dpi=dpi)
        p = outdir / f"page-{i:03d}.png"
        pix.save(p)
        paths.append(p)
    print(f"{len(paths)} pages -> {outdir}")

    thumbs = []
    for i, p in enumerate(paths, 1):
        im = Image.open(p).convert("RGB")
        h = round(im.height * THUMB_W / im.width)
        thumbs.append((i, im.resize((THUMB_W, h), Image.LANCZOS)))
    per = COLS * ROWS
    for s in range(0, len(thumbs), per):
        batch = thumbs[s:s + per]
        cell_h = max(t[1].height for t in batch) + 26
        sheet = Image.new("RGB", (COLS * THUMB_W, ROWS * cell_h), "white")
        d = ImageDraw.Draw(sheet)
        for k, (n, im) in enumerate(batch):
            x = (k % COLS) * THUMB_W
            y = (k // COLS) * cell_h
            sheet.paste(im, (x, y + 22))
            d.text((x + 6, y + 4), f"page {n}", fill="black")
        sp = outdir / f"sheet-{s // per + 1}.png"
        sheet.save(sp)
        print("sheet", sp)
    doc.close()


if __name__ == "__main__":
    main()

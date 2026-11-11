# -*- coding: utf-8 -*-
"""Final evidence for the F6 TRD redo: page-1 original comparisons, a
five-page contact sheet, and one 12-region contact sheet per page.

Usage:
  node scripts/run_py.mjs scripts/make_trd_final_f6.py
"""
import os

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "docs", "diagrams", "rebuild", "trd")
OUT = os.path.join(ROOT, "docs", "qa", "rebuild-preview", "trd")
ORIG = os.path.join(ROOT, "docs", "qa", "diagram-originals",
                    "ArchitectureDesign_ver1.1_image9.png")
ARIAL = "C:/Windows/Fonts/arial.ttf"
ARIALB = "C:/Windows/Fonts/arialbd.ttf"


def font(size, bold=False):
    return ImageFont.truetype(ARIALB if bold else ARIAL, size)


def label(draw, xy, text, size=34, bold=True, fill=(20, 20, 20)):
    draw.text(xy, text, font=font(size, bold), fill=fill)


def main():
    os.makedirs(OUT, exist_ok=True)
    sb = os.path.join(OUT, "stage-b")
    os.makedirs(sb, exist_ok=True)
    pages = [Image.open(os.path.join(FIG, "trd-%d.png" % i)).convert("RGB")
             for i in range(1, 6)]
    orig = Image.open(ORIG).convert("RGB")
    orig.save(os.path.join(sb, "original.png"))

    # ---- page 1 vs original: side-by-side / overlay / diff
    gap = 24
    sbs = Image.new("RGB", (orig.width * 2 + gap, orig.height + 80),
                    (255, 255, 255))
    sbs.paste(orig, (0, 80))
    sbs.paste(pages[0], (orig.width + gap, 80))
    d = ImageDraw.Draw(sbs)
    label(d, (20, 18), "Original 3440x2080 (21 cards, single page)", 34)
    label(d, (orig.width + gap + 20, 18),
          "Redo page 1/5 (10 cards, full columns)", 34)
    for y in range(80, sbs.height):
        sbs.putpixel((orig.width + gap // 2, y), (120, 120, 120))
    sbs.save(os.path.join(sb, "side-by-side-original-page1.png"))

    ga = np.array(orig.convert("L")) < 160
    gb = np.array(pages[0].convert("L")) < 160
    ov = np.full(ga.shape + (3,), 255, dtype=np.uint8)
    ov[ga & gb] = (0, 0, 0)
    ov[ga & ~gb] = (220, 30, 30)
    ov[~ga & gb] = (30, 60, 220)
    Image.fromarray(ov).save(os.path.join(sb, "overlay-original-page1.png"))
    diff = ImageChops.difference(orig.convert("L"),
                                 pages[0].convert("L")).point(
                                     lambda p: min(255, p * 3))
    diff.save(os.path.join(sb, "diff-original-page1.png"))
    print("page1 overlay changed px:", int((ga ^ gb).sum()),
          "orig-only:", int((ga & ~gb).sum()),
          "new-only:", int((~ga & gb).sum()))

    # ---- per-page 12-region contact sheet
    for i in range(1, 6):
        rdir = os.path.join(sb, "page-%d" % i, "regions")
        tw, th = 430, 347
        cw, ch = tw * 4 + 5 * 12, 3 * (th + 34) + 20
        sheet = Image.new("RGB", (cw, ch), (255, 255, 255))
        dd = ImageDraw.Draw(sheet)
        count = 0
        for r in range(1, 4):
            for c in range(1, 5):
                p = os.path.join(rdir, "r%d%d.png" % (r, c))
                if not os.path.exists(p):
                    continue
                im = Image.open(p).convert("RGB").resize((tw, th),
                                                         Image.LANCZOS)
                x = 12 + (c - 1) * (tw + 12)
                y = 10 + (r - 1) * (th + 34)
                sheet.paste(im, (x, y))
                label(dd, (x + 4, y + th + 6), "r%d%d" % (r, c), 22, True)
                count += 1
        sheet.save(os.path.join(sb, "page-%d" % i,
                                "regions-contact-sheet.png"))
        print("page", i, "region sheet", count, "tiles", sheet.size)

    # ---- five-page contact sheet (3 x 2)
    sw, sh = 1720, 1040
    gx, gy = 24, 24
    W = 3 * sw + 2 * gx + 2 * 30
    H = 90 + 2 * (sh + 64) + gy + 30
    sheet = Image.new("RGB", (W, H), (255, 255, 255))
    dd = ImageDraw.Draw(sheet)
    label(dd, (30, 22), "Table Relationship Diagram - 5 pages | 41 tables | "
          "293 columns | 59 FKs | 19 migrations", 38, True)
    for idx, page in enumerate(pages):
        r, c = divmod(idx, 3)
        x = 30 + c * (sw + gx)
        y = 90 + r * (sh + 64)
        im = page.resize((sw, sh), Image.LANCZOS)
        sheet.paste(im, (x, y))
        label(dd, (x + 6, y + sh + 8), "Page %d/5" % (idx + 1), 30, True)
    sheet.save(os.path.join(OUT, "final-contact-sheet.png"))
    print("final contact sheet", sheet.size)


if __name__ == "__main__":
    main()

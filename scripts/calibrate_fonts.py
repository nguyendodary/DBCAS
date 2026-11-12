# -*- coding: utf-8 -*-
"""Calibrate Arial font sizes (regular/bold) against measured ink bboxes.

For every text in trace.json + text-content.json, render candidates with
PIL/Arial at integer sizes 8..60 and pick the (weight, size) whose ink
bbox best matches width AND height of the measured bbox.

Usage: python scripts/calibrate_fonts.py <trace.json> <text-content.json>
"""
import json
import sys

from PIL import Image, ImageDraw, ImageFont

REG = "C:/Windows/Fonts/arial.ttf"
BLD = "C:/Windows/Fonts/arialbd.ttf"
_cache = {}


def ink(text, weight, size):
    key = (weight, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(BLD if weight == "bold" else REG, size)
    f = _cache[key]
    im = Image.new("L", (2400, 200), 255)
    d = ImageDraw.Draw(im)
    d.text((50, 120), text, font=f, fill=0, anchor="ls")
    bb = im.point(lambda p: 255 if p < 128 else 0).getbbox()
    if bb is None:
        return None
    return (bb[0] - 50, bb[1] - 120, bb[2] - 50, bb[3] - 120)


def best(text, measured, weights=("regular", "bold")):
    x0, y0, x1, y1 = measured
    mw, mh = x1 - x0, y1 - y0
    rows = []
    for w in weights:
        for size in range(8, 61):
            b = ink(text, w, size)
            if b is None:
                continue
            iw, ih = b[2] - b[0], b[3] - b[1]
            err = abs(iw - mw) + abs(ih - mh)
            rows.append((err, w, size, iw, ih))
    rows.sort()
    return rows[0], mw, mh


def main():
    trace = json.load(open(sys.argv[1], encoding="utf-8"))
    cont = json.load(open(sys.argv[2], encoding="utf-8"))
    items = []
    # title: bold; flow labels: regular or bold (check both); box: bold or
    # regular; legend: regular or bold; DBCAS: bold
    for i, b in enumerate(trace["free_texts"]):
        wts = ("bold",) if i == 0 else ("regular", "bold")
        items.append(("T%02d" % i, cont["free_texts"][i], b, wts))
    for i, b in enumerate(trace["box_texts"]):
        wts = ("bold", "regular") if i < 3 else ("regular", "bold")
        items.append(("B%02d" % i, cont["box_texts"][i], b["text"], wts))
    for i, b in enumerate(trace["ellipse_texts"]):
        items.append(("E00", cont["ellipse_texts"][i], b, ("bold", "regular")))

    print("%-6s %-30s %-16s %-8s %-6s %s" %
          ("id", "text", "measured wxh", "best", "size", "rendered wxh"))
    verdicts = []
    for tid, text, b, wts in items:
        (err, w, size, iw, ih), mw, mh = best(text, b, wts)
        verdicts.append((tid, w, size, err))
        print("%-6s %-30.30s %-16s %-8s %-6s %dx%d (err %d)" %
              (tid, text, "%dx%d" % (mw, mh), w, size, iw, ih, err))
    print()
    # summary by group
    from collections import Counter
    for pref in ("T0", "T1", "B", "E"):
        sel = [v for v in verdicts if v[0].startswith(pref) and
               (pref != "T0" or v[0] in ("T00",)) ]
    print("sizes used:", Counter((v[1], v[2]) for v in verdicts))
    bad = [v for v in verdicts if v[3] > 6]
    print("texts with total err > 6px:", bad if bad else "none")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Owner rule-8 checker for rebuilt diagram SVGs (text-geometry gate).

Checks (all four must pass):
  (a) every text label bbox is listed in the report, and no two text
      bboxes intersect
  (b) no text bbox intersects a foreign line segment. Own-line exemption:
      a horizontal segment lying within 14px below the bbox with >= 60%
      x-overlap is the label's own flow line and is exempt (reported).
  (c) the multiset of label strings in the SVG equals the expected list
      from text-content.json (title + flow labels + box texts + ellipse)
  (d) no element appears twice (identical type + geometry signature)

Usage:
  python scripts/check_diagram_geometry.py <file.svg> <text-content.json>

Prints a full report to stdout. Exit code 0 = PASS, 1 = FAIL.
Text bboxes are computed with PIL Arial metrics from the SVG's own
x / baseline-y / font-size / font-weight / text-anchor attributes.
"""
import json
import math
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_fonts import ink  # noqa: E402  (PIL ink-offset helper)

REG = "C:/Windows/Fonts/arial.ttf"
BLD = "C:/Windows/Fonts/arialbd.ttf"
NS = "{http://www.w3.org/2000/svg}"
EPS = 0.01          # shrink for strict-interior intersection tests
OWN_LINE_MAX_DY = 14   # px below bbox bottom that still counts as own line
OWN_LINE_MIN_XOVL = 0.60  # >=60% of bbox width must be covered

_font_cache = {}


def font(weight, size):
    key = (weight, round(float(size), 2))
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(
            BLD if weight == "bold" else REG, key[1])
    return _font_cache[key]


# ------------------------------------------------------------------ parsing

def fnum(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def parse_path(d):
    """Absolute/relative M L H V Z only (what our SVGs emit)."""
    toks = re.findall(
        r"[MmZzLlHhVv]|[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?", d)
    subs, cur = [], []
    x = y = sx = sy = 0.0
    i = 0
    cmd = None

    def num():
        nonlocal i
        v = float(toks[i])
        i += 1
        return v

    while i < len(toks):
        t = toks[i]
        if re.match(r"[A-Za-z]$", t):
            cmd = t
            i += 1
            if cmd in "Zz":
                if cur:
                    cur.append((sx, sy))
                    subs.append(cur)
                    cur = []
                x, y = sx, sy
                continue
        if cmd in ("M", "m"):
            dx, dy = num(), num()
            if cmd == "m":
                dx += x
                dy += y
            if cur:
                subs.append(cur)
            x, y = dx, dy
            sx, sy = x, y
            cur = [(x, y)]
            cmd = "L" if cmd == "M" else "l"
        elif cmd in ("L", "l"):
            dx, dy = num(), num()
            if cmd == "l":
                dx += x
                dy += y
            x, y = dx, dy
            cur.append((x, y))
        elif cmd in ("H", "h"):
            dx = num()
            if cmd == "h":
                dx += x
            x = dx
            cur.append((x, y))
        elif cmd in ("V", "v"):
            dy = num()
            if cmd == "v":
                dy += y
            y = dy
            cur.append((x, y))
        else:
            raise ValueError("unsupported path command %r in %r" % (t, d))
    if cur:
        subs.append(cur)
    return subs


def ellipse_poly(cx, cy, rx, ry, n=128):
    return [(cx + rx * math.cos(2 * math.pi * k / n),
             cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n + 1)]


def extract_shapes(root):
    """-> (segments [(x0,y0,x1,y1)], signatures [(tag, geometry...)])"""
    segs, sigs = [], []

    def add_poly(pts, tag, geo, close=False):
        sigs.append((tag, geo))
        p = list(pts)
        if close and len(p) > 1 and p[0] != p[-1]:
            p.append(p[0])
        for a, b in zip(p, p[1:]):
            if a != b:
                segs.append((a[0], a[1], b[0], b[1]))

    for el in root.iter():
        tag = el.tag.replace(NS, "")
        if tag in ("defs", "marker", "style", "title", "desc"):
            continue
        if tag == "rect":
            x, y = fnum(el.get("x")), fnum(el.get("y"))
            w, h = fnum(el.get("width")), fnum(el.get("height"))
            if w <= 0 or h <= 0:
                continue
            add_poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
                     "rect", (round(x, 1), round(y, 1),
                              round(w, 1), round(h, 1)), close=True)
        elif tag in ("ellipse", "circle"):
            cx, cy = fnum(el.get("cx")), fnum(el.get("cy"))
            rx = fnum(el.get("rx"), fnum(el.get("r")))
            ry = fnum(el.get("ry"), fnum(el.get("r")))
            add_poly(ellipse_poly(cx, cy, rx, ry), "ellipse",
                     (round(cx, 1), round(cy, 1),
                      round(rx, 1), round(ry, 1)), close=True)
        elif tag == "line":
            x1, y1 = fnum(el.get("x1")), fnum(el.get("y1"))
            x2, y2 = fnum(el.get("x2")), fnum(el.get("y2"))
            add_poly([(x1, y1), (x2, y2)], "line",
                     (round(x1, 1), round(y1, 1),
                      round(x2, 1), round(y2, 1)))
        elif tag in ("polyline", "polygon"):
            pts = [(float(a), float(b)) for a, b in
                   re.findall(r"(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)",
                              el.get("points") or "")]
            add_poly(pts, tag, tuple((round(a, 1), round(b, 1))
                                     for a, b in pts),
                     close=(tag == "polygon"))
        elif tag == "path":
            d = el.get("d") or ""
            for sub in parse_path(d):
                add_poly(sub, "path", d)
    return segs, sigs


def extract_texts(root):
    texts = []
    for el in root.iter(NS + "text"):
        content = "".join(el.itertext())
        x, y = fnum(el.get("x")), fnum(el.get("y"))
        size = fnum(el.get("font-size"), 16.0)
        weight = "bold" if (el.get("font-weight") or "").lower() in (
            "bold", "bolder", "700", "800", "900") else "regular"
        anchor = (el.get("text-anchor") or "start").lower()
        f = font(weight, size)
        adv = f.getlength(content)
        pen_x = x - (adv if anchor == "end" else
                     adv / 2.0 if anchor == "middle" else 0.0)
        ix0, iy0, ix1, iy1 = ink(content, weight, size)
        bbox = (pen_x + ix0, y + iy0, pen_x + ix1, y + iy1)
        texts.append({"content": content, "anchor": anchor,
                      "x": x, "y": y, "size": size, "weight": weight,
                      "bbox": bbox})
    return texts


# ------------------------------------------------------------------ geometry

def seg_intersects_bbox(s, b):
    """Strict-interior segment vs AABB test (axis-aligned segments and
    general segments via Liang-Barsky against the shrunk box)."""
    x0, y0, x1, y1 = b[0] + EPS, b[1] + EPS, b[2] - EPS, b[3] - EPS
    if x1 <= x0 or y1 <= y0:
        return False
    sx0, sy0, sx1, sy1 = s
    dx, dy = sx1 - sx0, sy1 - sy0
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, sx0 - x0), (dx, x1 - sx0),
                 (-dy, sy0 - y0), (dy, y1 - sy0)):
        if abs(p) < 1e-12:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                if r > t1:
                    return False
                t0 = max(t0, r)
            else:
                if r < t0:
                    return False
                t1 = min(t1, r)
    return t0 <= t1


def own_line_exempt(s, b):
    sx0, sy0, sx1, sy1 = s
    if abs(sy0 - sy1) > 0.01:          # horizontal only
        return False
    sy = sy0
    if not (b[3] - 1 <= sy <= b[3] + OWN_LINE_MAX_DY):
        return False
    ov = min(b[2], max(sx0, sx1)) - max(b[0], min(sx0, sx1))
    return ov >= OWN_LINE_MIN_XOVL * (b[2] - b[0])


def boxes_intersect(a, b):
    ox = min(a[2], b[2]) - max(a[0], b[0])
    oy = min(a[3], b[3]) - max(a[1], b[1])
    return ox > 0 and oy > 0, ox, oy


# ------------------------------------------------------------------ main

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    svg_path, content_path = sys.argv[1], sys.argv[2]
    out = []
    problems = []

    tree = ET.parse(svg_path)
    root = tree.getroot()
    segs, sigs = extract_shapes(root)
    texts = extract_texts(root)

    cont = json.load(open(content_path, encoding="utf-8"))
    expected = (list(cont["free_texts"]) + list(cont["box_texts"]) +
                list(cont["ellipse_texts"]))

    out.append("rule-8 checker: %s" % svg_path)
    out.append("expected labels: %d (title + %d flow labels + %d box + "
               "%d ellipse)" % (len(expected), len(cont["free_texts"]) - 1,
                                len(cont["box_texts"]),
                                len(cont["ellipse_texts"])))
    out.append("svg: %d text elements, %d line segments, %d shape elements"
               % (len(texts), len(segs), len(sigs)))
    out.append("")

    # ---------------------------------------------------------- (a)
    out.append("== (a) text label bboxes (%d) ==" % len(texts))
    for i, t in enumerate(texts):
        b = t["bbox"]
        out.append("[%2d] (%7.1f,%7.1f,%7.1f,%7.1f)  size %-5s %-7s  %s"
                   % (i, b[0], b[1], b[2], b[3], t["size"], t["weight"],
                      t["content"]))
    out.append("-- pairwise text intersections --")
    n_int = 0
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            hit, ox, oy = boxes_intersect(texts[i]["bbox"], texts[j]["bbox"])
            if hit:
                n_int += 1
                msg = ("text-text overlap: #%d %r vs #%d %r "
                       "(%.1f x %.1f px)" % (i, texts[i]["content"],
                                             j, texts[j]["content"], ox, oy))
                out.append("FAIL: " + msg)
                problems.append(msg)
    if n_int == 0:
        out.append("OK: no two text bboxes intersect")
    out.append("")

    # ---------------------------------------------------------- (b)
    out.append("== (b) text bbox vs foreign line segments ==")
    n_hit, n_exempt = 0, 0
    for i, t in enumerate(texts):
        b = t["bbox"]
        for s in segs:
            if not seg_intersects_bbox(s, b):
                continue
            if own_line_exempt(s, b):
                n_exempt += 1
                out.append("exempt (own line, 0-14px below bbox): #%d %r "
                           "segment y=%.1f x=%.0f..%.0f"
                           % (i, t["content"], s[1], s[0], s[2]))
                continue
            n_hit += 1
            msg = ("text vs foreign segment: #%d %r bbox=(%.0f,%.0f,%.0f,"
                   "%.0f) segment (%.1f,%.1f)-(%.1f,%.1f)"
                   % (i, t["content"], b[0], b[1], b[2], b[3], *s))
            out.append("FAIL: " + msg)
            problems.append(msg)
    if n_hit == 0:
        out.append("OK: no text bbox intersects a foreign segment "
                   "(%d own-line exemptions)" % n_exempt)
    out.append("")

    # ---------------------------------------------------------- (c)
    out.append("== (c) label set vs expected list ==")
    got = Counter(t["content"] for t in texts)
    exp = Counter(expected)
    missing = list((exp - got).elements())
    extra = list((got - exp).elements())
    if missing:
        out.append("FAIL: missing labels: %s" % missing)
        problems.append("missing labels: %s" % missing)
    if extra:
        out.append("FAIL: unexpected labels: %s" % extra)
        problems.append("unexpected labels: %s" % extra)
    if got != exp:
        out.append("FAIL: distinct label count %d (svg) != %d (expected)"
                   % (len(got), len(exp)))
        problems.append("label count mismatch")
    else:
        out.append("OK: %d labels exactly match the expected list"
                   % len(exp))
    out.append("")

    # ---------------------------------------------------------- (d)
    out.append("== (d) duplicate elements ==")
    sig_list = list(sigs)
    for t in texts:
        sig_list.append(("text", t["content"],
                         round(t["x"], 1), round(t["y"], 1),
                         t["size"], t["weight"]))
    counts = Counter(repr(s) for s in sig_list)
    dups = {k: v for k, v in counts.items() if v > 1}
    if dups:
        for k, v in sorted(dups.items()):
            out.append("FAIL: element appears %d times: %s" % (v, k))
            problems.append("duplicate element: %s x%d" % (k, v))
    else:
        out.append("OK: %d elements, each appears exactly once"
                   % len(sig_list))
    out.append("")

    # ---------------------------------------------------------- verdict
    if problems:
        out.append("RESULT: FAIL (%d problem(s))" % len(problems))
    else:
        out.append("RESULT: PASS (checks a/b/c/d all clean)")
    report = "\n".join(out) + "\n"
    sys.stdout.write(report)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()

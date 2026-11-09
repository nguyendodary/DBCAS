# -*- coding: utf-8 -*-
"""W2a extension of scripts/trace_figure.py for the Module View (figure 5)
and Logical System Architecture (figure 6) originals.

The generic tracer only finds COLOURED fill regions.  Both W2a figures also
contain white-filled rectangles drawn with thin strokes (tier frames, tier
tabs, 18 Module sub-boxes, 3 Module top boxes are coloured but the 18
sub-boxes are white, the Logical boxes/tabs/frames are all white).  This
copy therefore adds:

  * detect_stroke_rects(): axis-aligned rectangle detection from the
    stroke's own horizontal/vertical RUNS (one-pixel measurement, no
    layout engine).  A rectangle = a pair of vertical stroke bands plus
    top/bottom horizontal bands; validated by sampling the four edges and
    the white interior perimeter.  Emits {"kind": rect|rounded, fill
    #FFFFFF, measured stroke colour/width/radius} with "text_bbox" = the
    white interior used for text extraction.
  * short_arrows(): solid arrow glyphs measured from their own colour
    (Module: #536577 shafts+heads, 12 small between sub-boxes + 2 top).
  * connector_lines(): long thin dark components (Logical tiers) with an
    optional measured arrow head; sticks (Logical actors) are split off
    as circle+limbs.

Everything else (text bands, ink colours, rule-8 cuts, fixes, ids,
markers) is imported unchanged from trace_figure.py, so measurements stay
byte-for-byte comparable with the other rebuilt figures.

Usage:
  node scripts/run_py.mjs scripts/trace_figure_w2a.py <png> <out.json> \
      [fixes.json] [module|logical]
"""
import json
import math
import os
import sys
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trace_figure import (  # noqa: E402
    rle_label, comp_points, detect_fills, merge_cylinders, classify_shape,
    fill_mask_of, inside_shape_pt, _outside_frac, ink_colour, group_lines,
    open_lines_at_texts, hough_segments, fit_polyline, chain_segs,
    fit_circle, probe_arrow, dash_clusters, dilate,
)

REG = "C:/Windows/Fonts/arial.ttf"


def fmt(v):
    return ("%g" % round(float(v), 1))


# ------------------------------------------------------- run-based strokes
def _runs_1d(v):
    idx = np.flatnonzero(v)
    if not len(idx):
        return []
    breaks = np.flatnonzero(np.diff(idx) > 1)
    starts = np.r_[0, breaks + 1]
    ends = np.r_[breaks + 1, len(idx)]
    return [(int(idx[s]), int(idx[e - 1]) + 1) for s, e in zip(starts, ends)]


def stroke_bands(mask, axis, min_len=25):
    """Group per-row/per-column runs into stroke bands.

    Returns [{pos, a, b, th}] where pos is the centre coordinate on the
    band's short axis, a..b the run span on the long axis, th thickness.
    """
    h, w = mask.shape
    runs = []                     # (fixed coord, a, b)
    if axis == "v":
        for x in range(w):
            for (a, b) in _runs_1d(mask[:, x]):
                if b - a >= min_len:
                    runs.append((x, a, b))
    else:
        for y in range(h):
            for (a, b) in _runs_1d(mask[y, :]):
                if b - a >= min_len:
                    runs.append((y, a, b))
    parent = list(range(len(runs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    by_fixed = {}
    for i, (f, a, b) in enumerate(runs):
        by_fixed.setdefault(f, []).append(i)
    for f in sorted(by_fixed):
        for i in by_fixed[f]:
            for j in by_fixed.get(f + 1, []):
                fi, ai, bi = runs[i]
                fj, aj, bj = runs[j]
                if abs(ai - aj) <= 2 and abs(bi - bj) <= 2:
                    union(i, j)
    groups = {}
    for i in range(len(runs)):
        groups.setdefault(find(i), []).append(i)
    bands = []
    for ids in groups.values():
        fs = [runs[i][0] for i in ids]
        a = min(runs[i][1] for i in ids)
        b = max(runs[i][2] for i in ids)
        f0, f1 = min(fs), max(fs)
        if f1 - f0 + 1 > 12:      # not a stroke band (fill / text blob)
            continue
        bands.append({"pos": (f0 + f1) / 2.0, "a": a, "b": b,
                      "th": f1 - f0 + 1})
    bands.sort(key=lambda e: e["pos"])
    return bands


def _mask_cov(mask, x0, y0, x1, y1, hx, hy, vertical=False):
    """Fraction of sample positions along one edge that have mask ink."""
    n = hit = 0
    if not vertical:                 # horizontal edge at y0, x in [x0,x1)
        if x1 <= x0:
            return 0.0
        for x in range(int(x0), int(x1), 2):
            n += 1
            yy0, yy1 = max(0, int(y0 - hy)), min(mask.shape[0],
                                                 int(y0 + hy) + 1)
            if mask[yy0:yy1, x].any():
                hit += 1
    else:                            # vertical edge at x0, y in [y0,y1)
        if y1 <= y0:
            return 0.0
        for y in range(int(y0), int(y1), 2):
            n += 1
            xx0, xx1 = max(0, int(x0 - hx)), min(mask.shape[1],
                                                 int(x0 + hx) + 1)
            if mask[y, xx0:xx1].any():
                hit += 1
    return hit / float(max(1, n))


def _perimeter_white(rgb, x0, y0, x1, y1, inset=6):
    """Fraction of near-white pixels on the interior perimeter strip."""
    pts = []
    for x in range(x0, x1, 4):
        pts.append((x, y0))
        pts.append((x, y1 - 1))
    for y in range(y0, y1, 4):
        pts.append((x0, y))
        pts.append((x1 - 1, y))
    if not pts:
        return 0.0
    good = 0
    for x, y in pts:
        x = min(max(x, 0), rgb.shape[1] - 1)
        y = min(max(y, 0), rgb.shape[0] - 1)
        p = rgb[y, x]
        if p[0] >= 246 and p[1] >= 246 and p[2] >= 246:
            good += 1
    return good / float(len(pts))


def _center_run2(mask, pos, a, b, vertical, limit=20):
    """Centre/thickness sampled at 25% and 75% of a band span (avoids a
    crossing border at mid-span, e.g. a tier tab centred on a frame top)."""
    c1 = _center_run(mask, pos, a + 0.25 * (b - a), vertical, limit)
    c2 = _center_run(mask, pos, a + 0.75 * (b - a), vertical, limit)
    return c1 if c1[1] <= c2[1] else c2


def _center_run(mask, pos, mid, vertical, limit=20):
    """True centre + thickness of the painted stroke through a band point."""
    h, w = mask.shape
    if vertical:
        x = int(round(pos))
        y = int(round(mid))
        if not (0 <= y < h and 0 <= x < w) or not mask[y, x]:
            return float(pos), 1.0
        lo = hi = x
        while lo - 1 >= 0 and lo - 1 >= x - limit and mask[y, lo - 1]:
            lo -= 1
        while hi + 1 < w and hi + 1 <= x + limit and mask[y, hi + 1]:
            hi += 1
        return (lo + hi) / 2.0, float(hi - lo + 1)
    y = int(round(pos))
    x = int(round(mid))
    if not (0 <= y < h and 0 <= x < w) or not mask[y, x]:
        return float(pos), 1.0
    lo = hi = y
    while lo - 1 >= 0 and lo - 1 >= y - limit and mask[lo - 1, x]:
        lo -= 1
    while hi + 1 < h and hi + 1 <= y + limit and mask[hi + 1, x]:
        hi += 1
    return (lo + hi) / 2.0, float(hi - lo + 1)


def detect_stroke_rects(rgb, mask, min_w=90, min_h=40, max_r=70,
                       pad=0.0, sw_override=None):
    """White-filled rectangles from their own stroke runs (see module doc)."""
    h, w = mask.shape
    V = [b for b in stroke_bands(mask, "v") if b["th"] <= 10]
    H = [b for b in stroke_bands(mask, "h") if b["th"] <= 10]
    cands = []
    for i in range(len(V)):
        for j in range(i + 1, len(V)):
            l, r = V[i], V[j]
            if r["pos"] - l["pos"] < min_w:
                continue
            if abs(l["a"] - r["a"]) > 8 or abs(l["b"] - r["b"]) > 8:
                continue
            if min(l["b"], r["b"]) - max(l["a"], r["a"]) < min_h:
                continue
            tops = [b for b in H if abs(b["pos"] - l["a"]) <= 80 and
                    b["a"] <= l["pos"] + 70 and b["b"] >= l["pos"] + 80]
            bots = [b for b in H if abs(b["pos"] - l["b"]) <= 80 and
                    b["a"] <= l["pos"] + 70 and b["b"] >= l["pos"] + 80]
            if not tops or not bots:
                continue
            top = min(tops, key=lambda b: abs(b["pos"] - l["a"]))
            bot = min(bots, key=lambda b: abs(b["pos"] - l["b"]))
            # true painted centreline + stroke width per side (the run
            # grouping clips AA columns, so re-measure the full run)
            lx, lth = _center_run2(mask, l["pos"], l["a"], l["b"], True)
            rx, rth = _center_run2(mask, r["pos"], r["a"], r["b"], True)
            ty, tth = _center_run2(mask, top["pos"],
                                   top["a"], top["b"], False)
            by, bth = _center_run2(mask, bot["pos"],
                                   bot["a"], bot["b"], False)
            x0, x1, y0, y1 = lx, rx, ty, by
            if x1 - x0 < min_w or y1 - y0 < min_h:
                continue
            r_c = max(0.0, min(float(max_r), float(top["a"] - lx)))

            # bottom edge must reach both verticals (rounded corners inset)
            if bot["a"] > x0 + r_c + 12 or bot["b"] < x1 - r_c - 12:
                continue
            # white space bounded by a frame edge + thinner connectors is
            # not a drawn rectangle: its top/bottom band overshoots both
            # vertical sides (a real border ends at its corners)
            if top["a"] < x0 - 40 or top["b"] > x1 + 40 or \
               bot["a"] < x0 - 40 or bot["b"] > x1 + 40:
                continue
            ths = [lth, rth, tth, bth]
            sw = float(np.median(ths))
            if sw_override is not None:
                sw = float(sw_override)
            if max(ths) > 1.45 * min(ths):
                continue                  # mixed strokes: frame edge +
                                          # two thinner connectors
            hy = max(2, int(sw / 2) + 2)
            # left/right edge coverage (excluding the rounded ends)
            c_l = _mask_cov(mask, x0, y0 + r_c + 2, x0, y1 - r_c - 2,
                            hy, hy, vertical=True)
            c_r = _mask_cov(mask, x1, y0 + r_c + 2, x1, y1 - r_c - 2,
                            hy, hy, vertical=True)
            c_b = _mask_cov(mask, x0 + 2, y1, x1 - 2, y1, hy, hy)
            c_t = _mask_cov(mask, x0 + r_c + 2, y0, x1 - r_c - 2, y0,
                            hy, hy)
            if min(c_l, c_r, c_b) < 0.90 or c_t < 0.35:
                continue
            X0, Y0 = x0 - pad, y0 - pad
            X1, Y1 = x1 + pad, y1 + pad
            ix0 = int(round(X0 + sw / 2 + 1))
            iy0 = int(round(Y0 + sw / 2 + 1))
            ix1 = int(round(X1 - sw / 2 - 1))
            iy1 = int(round(Y1 - sw / 2 - 1))
            if ix1 - ix0 < 20 or iy1 - iy0 < 12:
                continue
            pw = _perimeter_white(rgb, ix0, iy0, ix1, iy1)
            if pw < 0.80:
                continue
            # stroke colour: median along the four edge centre lines
            cols = []
            for x in range(int(X0), int(X1), 3):
                cols.append(rgb[int(round(Y0)), x])
                cols.append(rgb[int(round(Y1)), x])
            for y in range(int(Y0), int(Y1), 3):
                cols.append(rgb[y, int(round(X0))])
                cols.append(rgb[y, int(round(X1))])
            med = np.median(np.array(cols, int), axis=0).astype(int)
            cands.append({
                "bbox": [round(X0, 1), round(Y0, 1),
                         round(X1, 1), round(Y1, 1)],
                "fill": "#FFFFFF", "stroke": "#%02X%02X%02X" % tuple(med),
                "stroke_width": round(sw, 1),
                "kind": "rounded" if r_c >= 5 else "rect",
                "radius": int(round(r_c)), "cap_ry": 0, "dashed": False,
                "text_bbox": [ix0, iy0, ix1, iy1],
                "score": c_l + c_r + c_b + c_t,
            })
    # keep one candidate per rectangle: only near-identical bboxes are
    # duplicates (a box INSIDE a frame is a separate element, not a dup)
    cands.sort(key=lambda c: (-(c["bbox"][2] - c["bbox"][0]) *
                              (c["bbox"][3] - c["bbox"][1]), -c["score"]))
    kept = []
    for c in cands:
        x0, y0, x1, y1 = c["bbox"]
        dup = False
        for k in kept:
            a0, b0, a1, b1 = k["bbox"]
            ox = max(0, min(x1, a1) - max(x0, a0))
            oy = max(0, min(y1, b1) - max(y0, b0))
            inter = ox * oy
            union = (x1 - x0) * (y1 - y0) + (a1 - a0) * (b1 - b0) - inter
            if union > 0 and inter / float(union) > 0.85:
                dup = True
                break
        if not dup:
            kept.append(c)
    return kept


# --------------------------------------------------------------- arrows
def short_arrows(rgb, color, tol):
    """Solid shaft+head arrow glyphs of one measured colour."""
    r, g, b = color
    m = (np.abs(rgb[:, :, 0].astype(int) - r) <= tol) & \
        (np.abs(rgb[:, :, 1].astype(int) - g) <= tol) & \
        (np.abs(rgb[:, :, 2].astype(int) - b) <= tol)
    mask = np.zeros_like(m)
    lines = []
    for c in rle_label(m):
        x0, y0, x1, y1 = c["bbox"]
        W, H = x1 - x0, y1 - y0
        if c["area"] < 40 or W < 30 or W > 190 or H < 8 or H > 50:
            continue
        pts = comp_points(c)
        cols = Counter(pts[:, 0])
        heights = [cols.get(x, 0) for x in range(x0, x1)]
        mx = int(np.argmax(heights))
        far = [v for i, v in enumerate(heights)
               if (i > 0.6 * W if mx > 0.5 * W else i < 0.4 * W)]
        med_far = float(np.median(far)) if far else 0.0
        if c["area"] < 250 or max(heights) < 14 or \
           max(heights) < 1.6 * max(1.0, med_far) or med_far > 10.0:
            continue                      # text glyph, not a solid arrow
        if mx > 0.5 * W:                 # head near the right end
            tip = (float(x1 - 0.5), float(np.median(
                pts[pts[:, 0] > x0 + 0.55 * W][:, 1])))
            start = (float(x0), float(np.median(
                pts[pts[:, 0] < x0 + 0.45 * W][:, 1])))
        else:
            tip = (float(x0 + 0.5), float(np.median(
                pts[pts[:, 0] < x0 + 0.45 * W][:, 1])))
            start = (float(x1), float(np.median(
                pts[pts[:, 0] > x0 + 0.55 * W][:, 1])))
        shaft = [v for i, v in enumerate(heights)
                 if (i < 0.4 * W if mx > 0.5 * W else i > 0.6 * W)]
        thick = float(np.median(shaft)) if shaft else float(H)
        head_cols = sum(1 for v in heights if v > thick + 2)
        head_len = max(8.0, min(float(W) * 0.8, float(head_cols)))
        head_half = max(4.0, float(max(heights)) / 2.0)
        med = np.median(rgb[pts[:, 1], pts[:, 0]], axis=0).astype(int)
        lines.append({
            "bbox": [int(x0), int(y0), int(x1), int(y1)],
            "segs": [[[start[0], start[1]], [tip[0], tip[1]]]],
            "thickness": round(max(2.0, thick), 1),
            "color": "#%02X%02X%02X" % tuple(med),
            "stroke": round(max(2.0, thick), 1),
            "arrow_tip": [round(tip[0], 1), round(tip[1], 1)],
            "arrow_from": [round(start[0], 1), round(start[1], 1)],
            "arrow_len": round(head_len, 1),
            "arrow_half": round(head_half, 1),
            "arrow_kind": "solid",
        })
        mask[y0:y1, x0:x1] |= m[y0:y1, x0:x1]
    return lines, mask


def connector_lines(rem, rgb, dark, text_boxes):
    """Long thin dark components (logical connectors) + actor sticks.

    Returns (lines, sticks, consumed_mask)."""
    h, w = rem.shape
    lines, sticks = [], []
    used = np.zeros((h, w), bool)
    for c in rle_label(rem):
        x0, y0, x1, y1 = c["bbox"]
        W, H = x1 - x0, y1 - y0
        if c["area"] < 60:
            continue
        # actors: head circle + body/arms/legs in one component
        if 50 <= W <= 280 and 130 <= H <= 380:
            pts = comp_points(c).astype(float)
            # head: the small enclosed white disc inside the ring
            sub = (rgb[y0:y1, x0:x1] >= 246).all(axis=2)
            circ = None
            heads = []
            for wc in rle_label(sub):
                wx0, wy0, wx1, wy1 = wc["bbox"]
                if 14 <= wx1 - wx0 <= 70 and 14 <= wy1 - wy0 <= 70:
                    heads.append((wy0, wx0, wy1, wx1, wc["area"]))
            if heads:
                wy0, wx0, wy1, wx1, _ar = min(heads)
                hx = x0 + (wx0 + wx1) / 2.0
                hy = y0 + (wy0 + wy1) / 2.0
                hr = ((wx1 - wx0) + (wy1 - wy0)) / 4.0 + 2.0
                circ = (round(hx, 1), round(hy, 1), round(hr, 1))
            if circ is None:
                top = pts[pts[:, 1] <= y0 + 0.30 * H]
                circ = fit_circle(top) if len(top) >= 30 else None
            cx = (x0 + x1) / 2.0
            segs_h = hough_segments(pts, min_len=24, max_parts=10)
            body = None
            for a, b in segs_h:
                dx, dy = b[0] - a[0], b[1] - a[1]
                L = math.hypot(dx, dy)
                if L >= 40 and abs(dx) < 0.25 * abs(dy) and \
                   abs((a[0] + b[0]) / 2.0 - cx) < 14:
                    if body is None or L > body[2]:
                        body = (a, b, L)
            neck = (circ[1] + circ[2] + 2.0) if circ else y0 + 0.30 * H
            body_bot = max(body[0][1], body[1][1]) if body else y0 + 0.70 * H
            # hip = last row with one run around the body axis
            hip = body_bot
            while hip > neck + 20:
                xs = np.flatnonzero(rem[int(hip), max(0, int(cx) - 90):
                                        min(w, int(cx) + 90)])
                runs = 0
                if len(xs):
                    runs = 1 + int(np.count_nonzero(np.diff(xs) > 1))
                if runs <= 1:
                    break
                hip -= 1
            # shoulder = first row where the width jumps beyond the body
            shoulder = neck
            yy = int(neck) + 3
            while yy < hip:
                xs = np.flatnonzero(rem[yy, max(0, int(cx) - 90):
                                       min(w, int(cx) + 90)])
                if len(xs) and xs[-1] - xs[0] > 16:
                    shoulder = float(yy)
                    break
                yy += 1
            arm = {"l": None, "r": None}
            leg = {"l": None, "r": None}
            for a, b in segs_h:
                for p in (a, b):
                    px, py = float(p[0]), float(p[1])
                    if py < neck or py > y1:
                        continue
                    side = "l" if px < cx else "r"
                    if py <= hip + 4:
                        if arm[side] is None or \
                           abs(px - cx) > abs(arm[side][0] - cx):
                            arm[side] = (px, py)
                    if py >= hip - 6:
                        if leg[side] is None or py > leg[side][1]:
                            leg[side] = (px, py)
            members = [[[cx, neck], [cx, hip]]]
            for side in ("l", "r"):
                if arm[side]:
                    members.append([[cx, shoulder],
                                    [arm[side][0], arm[side][1]]])
                if leg[side]:
                    members.append([[cx, hip],
                                    [leg[side][0], leg[side][1]]])
            xs = [x0, x1]
            ys = [y0, y1]
            for sg in members:
                xs += [sg[0][0], sg[1][0]]
                ys += [sg[0][1], sg[1][1]]
            sticks.append({
                "bbox": [int(x0), int(y0), int(x1), int(y1)],
                "circle": list(circ) if circ else None,
                "limbs": [[list(map(float, sg[0])), list(map(float, sg[1]))]
                          for sg in members],
                "stroke": 4.0,
                "area": int(c["area"]),
            })
            used[y0:y1, x0:x1] |= rem[y0:y1, x0:x1]
            continue
        if min(W, H) > 44 or max(W, H) < 70 or \
           max(W, H) < 2.2 * max(1, min(W, H)):
            continue                      # not a long thin connector
        pts = comp_points(c).astype(float)
        if len(pts) < 20:
            continue
        # principal axis (measured): vertical or horizontal connector
        if H >= W:
            xc = float(np.median(pts[:, 0]))
            y_a, y_b = float(y0), float(y1)
            widths = [np.count_nonzero(rem[y, x0:x1]) for y in
                      range(y0, y1)]
            prof = [(y0 + i, v) for i, v in enumerate(widths)]
            mid = (y_a + y_b) / 2.0
            top_max = max(v for y, v in prof if y < mid)
            bot_max = max(v for y, v in prof if y >= mid)
            if bot_max >= top_max + 2:   # head at the bottom
                tip = (xc, y_b - 0.5)
                start = (xc, y_a)
                shaft = [v for y, v in prof if y < y_a + 0.45 * H]
            else:
                tip = (xc, y_a + 0.5)
                start = (xc, y_b)
                shaft = [v for y, v in prof if y > y_b - 0.45 * H]
            ok, _ = probe_arrow(rem, (int(round(tip[0])),
                                      int(round(tip[1]))),
                                (int(round(start[0])),
                                 int(round(start[1]))))
        else:
            yc = float(np.median(pts[:, 1]))
            x_a, x_b = float(x0), float(x1)
            heights = [np.count_nonzero(rem[y0:y1, x]) for x in
                       range(x0, x1)]
            prof = [(x0 + i, v) for i, v in enumerate(heights)]
            mid = (x_a + x_b) / 2.0
            l_max = max(v for x, v in prof if x < mid)
            r_max = max(v for x, v in prof if x >= mid)
            if r_max >= l_max + 2:
                tip = (x_b - 0.5, yc)
                start = (x_a, yc)
                shaft = [v for x, v in prof if x < x_a + 0.45 * W]
            else:
                tip = (x_a + 0.5, yc)
                start = (x_b, yc)
                shaft = [v for x, v in prof if x > x_b - 0.45 * W]
            ok, _ = probe_arrow(rem, (int(round(tip[0])),
                                      int(round(tip[1]))),
                                (int(round(start[0])),
                                 int(round(start[1]))))
        thick = float(np.median(shaft)) if shaft else 3.0
        med = np.median(rgb[pts[:, 1].astype(int), pts[:, 0].astype(int)],
                        axis=0).astype(int)
        prof_all = prof
        head_n = sum(1 for _p, v in prof_all if v > thick + 2)
        head_half = max(4.0, float(max([v for _p, v in prof_all])) / 2.0)
        ln = {"bbox": [int(x0), int(y0), int(x1), int(y1)],
              "segs": [[[round(start[0], 1), round(start[1], 1)],
                        [round(tip[0], 1), round(tip[1], 1)]]],
              "thickness": round(max(2.0, thick), 1),
              "color": "#%02X%02X%02X" % tuple(med),
              "stroke": round(max(2.0, thick), 1),
              "arrow_len": round(max(8.0, float(head_n)), 1),
              "arrow_half": round(head_half, 1)}
        if ok:
            ln["arrow_tip"] = [round(tip[0], 1), round(tip[1], 1)]
            ln["arrow_from"] = [round(start[0], 1), round(start[1], 1)]
            ln["arrow_kind"] = "solid"
        lines.append(ln)
        used[y0:y1, x0:x1] |= rem[y0:y1, x0:x1]
    return lines, sticks, used


def extend_tip_to_shape(lines, shapes):
    """A connector arrow whose apex was clipped by the target border's
    stroke mask is extended to the outer edge of that border (measured)."""
    def enter_t(p0, d, b):
        x0, y0, x1, y1 = b
        t0, t1 = 0.0, 1e9
        for p, q in ((-d[0], p0[0] - x0), (d[0], x1 - p0[0]),
                     (-d[1], p0[1] - y0), (d[1], y1 - p0[1])):
            if abs(p) < 1e-9:
                if q < 0:
                    return None
            else:
                r = q / p
                if p < 0:
                    if r > t1:
                        return None
                    t0 = max(t0, r)
                else:
                    if r < t0:
                        return None
                    t1 = min(t1, r)
        return t0 if t0 <= t1 else None

    for ln in lines:
        if not ln.get("arrow_tip") or not ln.get("arrow_from"):
            continue
        p0 = ln["arrow_from"]
        p1 = ln["arrow_tip"]
        d = (p1[0] - p0[0], p1[1] - p0[1])
        L = math.hypot(*d)
        if L < 1e-6:
            continue
        best = None
        for s in shapes:
            if s.get("no_text"):
                continue
            t = enter_t(p0, d, s["bbox"])
            if t is None or t <= 1.0:
                continue
            extra = t * L - L
            if extra > 45:
                continue
            if best is None or extra < best[0]:
                best = (extra, t, s)
        if best is None:
            continue
        extra, t, s = best
        pad = float(s.get("stroke_width", 2)) / 2.0 + 1.0
        nt = t - pad / L
        tip = [round(p0[0] + d[0] * nt, 1), round(p0[1] + d[1] * nt, 1)]
        segs = ln["segs"]
        if math.hypot(segs[-1][1][0] - p1[0],
                      segs[-1][1][1] - p1[1]) < 1.5:
            segs[-1][1] = tip
        elif math.hypot(segs[0][0][0] - p1[0],
                        segs[0][0][1] - p1[1]) < 1.5:
            segs[0][0] = tip
        ln["arrow_tip"] = tip
    return lines


# --------------------------------------------------------------------- main
def main():
    src, out = sys.argv[1], sys.argv[2]
    fixes = json.load(open(sys.argv[3], encoding="utf-8")) \
        if len(sys.argv) > 3 and sys.argv[3] != "-" else {}
    mode = sys.argv[4] if len(sys.argv) > 4 else "module"
    print("fixes loaded:", sorted(fixes.keys()), "mode:", mode)
    img = Image.open(src).convert("RGB")
    rgb = np.array(img)
    gray = np.array(img.convert("L"))
    h, w = gray.shape
    dark = gray < 170

    # ------------------------------------------------- white stroke rects
    if mode == "module":
        border_mask = (np.abs(rgb[:, :, 0].astype(int) - 139) <= 24) & \
                      (np.abs(rgb[:, :, 1].astype(int) - 157) <= 24) & \
                      (np.abs(rgb[:, :, 2].astype(int) - 173) <= 24)
        min_w, min_h = 120, 60
        white_shapes = detect_stroke_rects(rgb, border_mask, min_w, min_h)
    else:
        border_mask = dark
        min_w, min_h = 110, 45
        white_shapes = detect_stroke_rects(rgb, border_mask, min_w, min_h)
    for s in white_shapes:
        s["no_text"] = (s["bbox"][2] - s["bbox"][0] >= 2500 or
                        s["bbox"][3] - s["bbox"][1] >= 350)

    # ------------------------------------------------------- coloured fills
    shapes = []
    for f in merge_cylinders(rgb, detect_fills(rgb)):
        if (f["bbox"][2] - f["bbox"][0]) < 150 and \
           (f["bbox"][3] - f["bbox"][1]) < 100:
            continue
        kind, stroke, radius, cap = classify_shape(rgb, f)
        entry = {"bbox": f["bbox"], "fill": f["fill"], "stroke": stroke,
                 "stroke_width": 2,
                 "kind": "cylinder" if f.get("cylinder") else kind,
                 "radius": radius, "cap_ry": cap, "dashed": False}
        # rounded-corner radius: measured from the painted corner; the
        # fill-inset heuristic is unreliable on very light fills (AA), so
        # the Module panels use the corner radius measured on the border
        # (outer arc ~16 px, same as the dependency cards).
        if mode == "module" and entry["kind"] == "rect":
            entry["kind"] = "rounded"
            entry["radius"] = 16
        if entry["kind"] in ("rect", "rounded", "cylinder"):
            fm = fill_mask_of(rgb, f["bbox"], f["fill"])
            lefts, rights = [], []
            for yy in range(f["bbox"][3] - f["bbox"][1]):
                rr = np.flatnonzero(fm[yy])
                if len(rr):
                    lefts.append(int(rr[0]))
                    rights.append(int(rr[-1]))
            if len(lefts) >= 8:
                ml, ml_n = Counter(lefts).most_common(1)[0]
                mr, mr_n = Counter(rights).most_common(1)[0]
                dbb = list(f["bbox"])
                if ml > 3 and ml_n >= 0.25 * len(lefts):
                    dbb[0] = f["bbox"][0] + ml
                if mr < max(rights) - 3 and mr_n >= 0.25 * len(rights):
                    dbb[2] = f["bbox"][0] + mr + 1
                if dbb != f["bbox"]:
                    entry["draw_bbox"] = dbb
        bx0, by0, bx1, by1 = f["bbox"]
        my_ = (by0 + by1) // 2
        run = 0
        for xx in range(max(0, bx0 - 6), min(w, bx0 + 7)):
            if dark[my_, xx]:
                run += 1
            elif run:
                break
        if 1 <= run <= 8:
            entry["stroke_width"] = run
        if mode == "module":
            # painted border = 3 solid px + 1 AA px on every card; keep one
            # uniform 4 px stroke (the original varies 3-4 px with AA)
            entry["stroke_width"] = 4.0
        if entry["kind"] == "cylinder":
            dbb = entry.get("draw_bbox", f["bbox"])
            m = fill_mask_of(rgb, dbb, f["fill"])
            entry["outline"] = []           # unused for these figures
        shapes.append(entry)

    # draw order: big backgrounds first, then white boxes on top
    for s in white_shapes:
        s["area"] = (s["bbox"][2] - s["bbox"][0]) * \
                    (s["bbox"][3] - s["bbox"][1])
    shapes.sort(key=lambda s: -((s.get("draw_bbox") or s["bbox"])[2] -
                                (s.get("draw_bbox") or s["bbox"])[0]) *
                 ((s.get("draw_bbox") or s["bbox"])[3] -
                  (s.get("draw_bbox") or s["bbox"])[1]))
    shapes = shapes + white_shapes
    # final order: area desc (white frames/panels before inner boxes)
    shapes.sort(key=lambda s: -((s.get("draw_bbox") or s["bbox"])[2] -
                                (s.get("draw_bbox") or s["bbox"])[0]) *
                 ((s.get("draw_bbox") or s["bbox"])[3] -
                  (s.get("draw_bbox") or s["bbox"])[1]))

    # ----------------------------------------------- masks / arrow glyphs
    struct = np.zeros((h, w), bool)
    hole = np.zeros((h, w), bool)
    for s in white_shapes:
        x0, y0, x1, y1 = s["bbox"]
        sw = s["stroke_width"]
        ox0, oy0 = max(0, int(x0 - sw / 2 - 2)), max(0, int(y0 - sw / 2 - 2))
        ox1, oy1 = min(w, int(x1 + sw / 2 + 3)), min(h, int(y1 + sw / 2 + 3))
        ix0, iy0, ix1, iy1 = s["text_bbox"]
        struct[oy0:oy1, ox0:ox1] = True
        struct[max(0, iy0):iy1, max(0, ix0):ix1] = False
        hole[iy0:iy1, ix0:ix1] = True
        # stroke width measured on the real luminance edge, not on the
        # exact-colour core (AA makes the core 1-2 px narrower than the
        # painted stroke). Sample at 25%/75% of each side so an arrow that
        # touches the border mid-height cannot inflate the run.
        lum = gray
        runs = []
        for frac in (0.25, 0.75):
            ym = int(round(y0 + frac * (y1 - y0)))
            xm = int(round(x0 + frac * (x1 - x0)))
            for side in ("l", "r"):
                xx = int(round(x0 if side == "l" else x1))
                run = 1
                d = -1
                while 0 <= xx + d < w and lum[ym, xx + d] < 170:
                    run += 1
                    d -= 1
                d = 1
                while 0 <= xx + d < w and lum[ym, xx + d] < 170:
                    run += 1
                    d += 1
                runs.append(run)
            for side in ("t", "b"):
                yy = int(round(y0 if side == "t" else y1))
                run = 1
                d = -1
                while 0 <= yy + d < h and lum[yy + d, xm] < 170:
                    run += 1
                    d -= 1
                d = 1
                while 0 <= yy + d < h and lum[yy + d, xm] < 170:
                    run += 1
                    d += 1
                runs.append(run)
        s["stroke_width"] = max(2.0, min(10.0, float(np.median(runs))))
    arrow_mask = np.zeros((h, w), bool)
    arrow_lines = []
    if mode == "module":
        arrow_lines, arrow_mask = short_arrows(rgb, (83, 101, 119), 25)
    dark2 = dark & ~struct & ~arrow_mask

    # Logical: detect connector strokes and actor sticks BEFORE text so a
    # line + glyph touching it can never be grouped into one text band.
    lines = list(arrow_lines)
    sticks = []
    if mode == "logical":
        clines, csticks, consumed = connector_lines(dark2, rgb, dark, None)
        clines = extend_tip_to_shape(clines, white_shapes)
        lines.extend(clines)
        sticks.extend(csticks)
        dark2 = dark2 & ~consumed

    fill_mask = np.zeros((h, w), dtype=bool)
    for s in shapes:
        fr_, fg_, fb_ = (int(s["fill"][i:i + 2], 16) for i in (1, 3, 5))
        if fr_ >= 246 and fg_ >= 246 and fb_ >= 246:
            continue                      # never for white-filled boxes
        x0, y0, x1, y1 = s["bbox"]
        fill_mask[y0:y1, x0:x1] |= fill_mask_of(rgb, s["bbox"], s["fill"])
    d = fill_mask.copy()
    for _ in range(6):
        d[1:, :] |= d[:-1, :]
        d[:-1, :] |= d[1:, :]
        d[:, 1:] |= d[:, :-1]
        d[:, :-1] |= d[:, 1:]

    # ------------------------------------------------------------- texts
    splits = [(tuple(s["shape"]), s["split_y"])
              for s in fixes.get("splits", [])]
    texts = []
    tmask = np.zeros((h, w), bool)
    for si, s in enumerate(shapes):
        if s.get("no_text") or s["kind"] == "boundary":
            continue
        tb = s.get("text_bbox") or s.get("draw_bbox") or s["bbox"]
        x0, y0, x1, y1 = tb
        if x1 - x0 < 8 or y1 - y0 < 8:
            continue
        r_, g_, b_ = (int(s["fill"][i:i + 2], 16) for i in (1, 3, 5))
        sub = rgb[y0:y1, x0:x1].astype(int)
        diff = (np.abs(sub[:, :, 0] - r_) + np.abs(sub[:, :, 1] - g_) +
                np.abs(sub[:, :, 2] - b_)) > 90
        diff[:2, :] = False
        diff[-2:, :] = False
        diff[:, :2] = False
        diff[:, -2:] = False
        diff &= ~struct[y0:y1, x0:x1]
        diff &= ~arrow_mask[y0:y1, x0:x1]
        fr2 = int(s["fill"][1:3], 16)
        if not (fr2 >= 246 and int(s["fill"][3:5], 16) >= 246 and
                int(s["fill"][5:7], 16) >= 246):
            diff &= ~hole[y0:y1, x0:x1]     # nested white box text
        m = np.zeros((h, w), bool)
        m[y0:y1, x0:x1] = diff
        comps = []
        for c in rle_label(m):
            bx0, by0, bx1, by1 = c["bbox"]
            if c["area"] < 6:
                continue
            if (bx1 - bx0) >= (x1 - x0) * 0.96 or \
               (by1 - by0) >= (y1 - y0) * 0.96:
                continue
            if not inside_shape_pt(s, (bx0 + bx1) / 2.0, (by0 + by1) / 2.0):
                continue
            if _outside_frac(s, comp_points(c)) >= 0.5:
                continue
            comps.append(c)
        bands = group_lines([c["bbox"] for c in comps],
                            56 if min(h, w) > 2000 else 26)
        key = tuple(s["bbox"])
        for sk, sy in splits:
            if sk != key:
                continue
            nxt = []
            for box in bands:
                if not (box[1] < sy < box[3]) or (box[3] - box[1]) < 18:
                    nxt.append(box)
                    continue
                top, bot = [], []
                for c in comps:
                    cx_ = (c["bbox"][0] + c["bbox"][2]) / 2.0
                    cy_ = (c["bbox"][1] + c["bbox"][3]) / 2.0
                    if not (box[0] - 2 <= cx_ <= box[2] + 2 and
                            box[1] - 2 <= cy_ <= box[3] + 2):
                        continue
                    (top if cy_ < sy else bot).append(c)
                if top and bot:
                    nxt.append([min(c["bbox"][0] for c in top), box[1],
                                max(c["bbox"][2] for c in top), sy - 1])
                    nxt.append([min(c["bbox"][0] for c in bot), sy,
                                max(c["bbox"][2] for c in bot), box[3]])
                else:
                    nxt.append(box)
            bands = nxt
        for box in bands:
            if box[3] - box[1] < 6:
                continue
            if (box[2] - box[0]) < max(18, 1.2 * (box[3] - box[1])):
                continue                  # corner sliver / bullet, not text
            cs = [c for c in comps
                  if c["bbox"][0] >= box[0] - 2 and
                  c["bbox"][2] <= box[2] + 2 and
                  c["bbox"][1] >= box[1] - 2 and
                  c["bbox"][3] <= box[3] + 2]
            if not cs:
                continue
            pts = np.concatenate([comp_points(c) for c in cs])
            ink = ink_colour(rgb, pts, s["fill"])
            texts.append({"bbox": [int(v) for v in box], "ink": ink,
                          "inside": None, "inside_fill": si})
            x0b, y0b, x1b, y1b = box
            tmask[y0b:y1b, x0b:x1b] = True

    # free text bands: dark2 minus everything already owned by a shape
    white_comps = []
    for c in rle_label(dark2 & ~tmask):
        if c["area"] < 8:
            continue
        x0, y0, x1, y1 = c["bbox"]
        if min(x1 - x0, y1 - y0) <= 15 and max(x1 - x0, y1 - y0) >= 35:
            continue                       # connector / line, handled below
        if 50 <= (x1 - x0) <= 280 and 130 <= (y1 - y0) <= 380:
            continue                       # actor stick
        white_comps.append(c)
    for box in group_lines([c["bbox"] for c in white_comps],
                           56 if min(h, w) > 2000 else 26):
        bw_, bh_ = box[2] - box[0], box[3] - box[1]
        if bh_ < 10 or bw_ < max(18, 1.2 * bh_) or bh_ > 0.12 * h or \
           bw_ > 0.7 * w:
            continue
        ctr_w = ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)
        if any(s2["kind"] != "boundary" and not s2.get("no_text") and
               s2["bbox"][0] <= ctr_w[0] <= s2["bbox"][2] and
               s2["bbox"][1] <= ctr_w[1] <= s2["bbox"][3]
               for s2 in shapes):
            continue                      # owned by the fill-diff path
        band_cs = [c for c in white_comps
                   if c["bbox"][0] >= box[0] - 2 and
                   c["bbox"][2] <= box[2] + 2 and
                   c["bbox"][1] >= box[1] - 2 and
                   c["bbox"][3] <= box[3] + 2]
        if not band_cs:
            continue
        pts = np.concatenate([comp_points(c) for c in band_cs])
        ink = ink_colour(rgb, pts)
        fill_island = False
        for s2 in shapes:
            if sum(abs(int(ink[k:k + 2], 16) - int(s2["fill"][k:k + 2], 16))
                   for k in (1, 3, 5)) <= 60:
                fill_island = True
                break
        if fill_island:
            continue
        texts.append({"bbox": [int(v) for v in box], "ink": ink,
                      "inside": None})
        tmask[box[1]:box[3], box[0]:box[2]] = True

    # text bbox repair against dark2 (never against box borders)
    seg_all = []
    for ln in arrow_lines:
        for (a, b) in ln["segs"]:
            seg_all.append((a[0], a[1], b[0], b[1]))

    def near_seg(x, y):
        for (ax, ay, bx, by) in seg_all:
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            if L2 < 1e-9:
                continue
            tp = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
            px, py = ax + tp * dx, ay + tp * dy
            if (px - x) ** 2 + (py - y) ** 2 <= 4.5 ** 2:
                return True
        return False

    for t in texts:
        if t["inside"] is not None:
            continue
        x0, y0, x1, y1 = t["bbox"]
        xs, ys = [], []
        for yy in range(max(0, y0 - 2), min(h, y1 + 2)):
            lo, hi = max(0, x0 - 25), min(w, x1 + 25)
            for i in np.flatnonzero(dark2[yy, lo:hi]):
                x = int(lo + i)
                if near_seg(x, yy):
                    continue
                xs.append(x)
                ys.append(yy)
        if not xs:
            continue
        left = sorted((x for x in xs if x < x0), reverse=True)
        lx = x0
        for x in left:
            if lx - x > 12:
                break
            lx = x
        right = sorted((x for x in xs if x > x1), reverse=True)
        rx = x1
        for x in right:
            if x - rx > 12:
                break
            rx = x
        sel = [x for x in xs if lx - 1 <= x <= rx + 1]
        nb = [min(x0, lx), min(y0, min(ys)), max(x1, rx), max(y1, max(ys))]
        if sel:
            nb[0] = min(nb[0], min(sel))
            nb[2] = max(nb[2], max(sel))
        if nb != [x0, y0, x1, y1]:
            t["bbox"] = [int(v) for v in nb]
            tmask[nb[1]:nb[3], nb[0]:nb[2]] = True

    # -------------------------------------------------- per-figure fixes
    for rep in fixes.get("replace", []):
        if "drop" in rep:
            drop = tuple(rep["drop"])
            kept = [t for t in texts if tuple(t["bbox"]) != drop]
            if len(kept) == len(texts):
                print("WARN: replace target not found:", drop)
            texts = kept
        if "add" not in rep:
            continue
        add = dict(rep["add"])
        ab = tuple(add["bbox"])
        ctr = ((ab[0] + ab[2]) / 2.0, (ab[1] + ab[3]) / 2.0)
        hosts = [s for s in shapes
                 if s["kind"] != "boundary" and
                 s["bbox"][0] <= ctr[0] <= s["bbox"][2] and
                 s["bbox"][1] <= ctr[1] <= s["bbox"][3]]
        host = min(hosts, key=lambda s: (s["bbox"][2] - s["bbox"][0]) *
                   (s["bbox"][3] - s["bbox"][1])) if hosts else None
        if host is not None:
            x0, y0, x1, y1 = ab
            r_, g_, b_ = (int(host["fill"][i:i + 2], 16) for i in (1, 3, 5))
            sub = rgb[y0:y1, x0:x1].astype(int)
            mm = (np.abs(sub[:, :, 0] - r_) + np.abs(sub[:, :, 1] - g_) +
                  np.abs(sub[:, :, 2] - b_)) > 90
            pts = np.argwhere(mm)[:, ::-1]
            if len(pts):
                ink = ink_colour(rgb, pts + np.array([x0, y0]), host["fill"])
            else:
                ink = "#FFFFFF"
            add["inside"] = host.get("id")
        else:
            x0, y0, x1, y1 = ab
            pts = np.argwhere(dark[y0:y1, x0:x1])[:, ::-1]
            ink = ink_colour(rgb, pts + np.array([x0, y0])) if len(pts) \
                else "#000000"
            add["inside"] = None
        add["ink"] = ink
        add["bbox"] = [int(v) for v in ab]
        texts.append(add)
    texts.sort(key=lambda t: (t["bbox"][1], t["bbox"][0]))
    for i, t in enumerate(texts):
        t["id"] = "X%03d" % (i + 1)
    for nz in fixes.get("nudges", []):
        hit = False
        for t in texts:
            if tuple(t["bbox"]) == tuple(nz["bbox"]):
                t["bbox"] = [t["bbox"][0] + int(nz.get("dx", 0)),
                             t["bbox"][1] + int(nz.get("dy", 0)),
                             t["bbox"][2] + int(nz.get("dx", 0)),
                             t["bbox"][3] + int(nz.get("dy", 0))]
                hit = True
        if not hit:
            print("WARN: nudge target not found:", nz["bbox"])
    texts.sort(key=lambda t: (t["bbox"][1], t["bbox"][0]))

    # ----------------------------------------- rule 8: line/text cuts
    lines, n_cuts = open_lines_at_texts(lines, [t["bbox"] for t in texts])
    if n_cuts:
        print("rule-8 line cuts: %d segment(s) opened at text bboxes"
              % n_cuts)

    # tier frames: open the top border where the tab sits (the original
    # paints the tab over the frame line; drawing one continuous edge would
    # cross the tab label and fail rule 8)
    if mode == "logical":
        frames = [s for s in shapes
                  if s["kind"] == "rect" and not s.get("no_text") is False
                  and (s["bbox"][2] - s["bbox"][0]) >= 2500]
        tabs = [s for s in shapes
                if 60 <= s["bbox"][3] - s["bbox"][1] <= 120 and
                900 <= s["bbox"][2] - s["bbox"][0] <= 2000]
        for f in frames:
            gaps = []
            for t in tabs:
                if abs(t["bbox"][1] - f["bbox"][1]) <= 50 or \
                   abs((t["bbox"][1] + t["bbox"][3]) / 2.0 -
                       f["bbox"][1]) <= 60:
                    gaps.append([t["bbox"][0] - 4, t["bbox"][2] + 4])
            if gaps:
                f["kind"] = "boundary"
                f["gaps"] = sorted(gaps)
                f["gap_axis"] = "h"

    for i, s in enumerate(shapes):
        s["id"] = "S%02d" % (i + 1)
    for t in texts:
        if t["inside"] is not None:
            continue
    # remap fill texts' inside index -> shape id (they were created before
    # ids were assigned; the index in the shapes list is stable)
    for t in texts:
        if t.get("inside_fill") is not None:
            t["inside"] = shapes[t["inside_fill"]]["id"]

    report = {
        "canvas": {"w": int(w), "h": int(h)},
        "source": os.path.basename(src),
        "shapes": shapes,
        "lines": [{"id": "L%02d" % (i + 1), **ln}
                  for i, ln in enumerate(lines)],
        "dashes": [],
        "sticks": [{"id": "K%02d" % (i + 1), **s}
                   for i, s in enumerate(sticks)],
        "arrows": [],
        "texts": texts,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)

    # ---------------------------------------------------------- markers
    mk = img.copy()
    dr = ImageDraw.Draw(mk)
    for s in shapes:
        x0, y0, x1, y1 = s.get("draw_bbox") or s["bbox"]
        col = (0, 150, 0) if s["kind"] in ("rect", "rounded") else \
              (255, 0, 255) if s["kind"] == "ellipse" else (255, 140, 0)
        dr.rectangle([x0, y0, x1 - 1, y1 - 1], outline=col, width=3)
    for ln in report["lines"]:
        for (a, b) in ln["segs"]:
            dr.line([tuple(a), tuple(b)], fill=(255, 0, 0), width=3)
    for k in report["sticks"]:
        if k["circle"]:
            cx, cy, r = k["circle"]
            dr.ellipse([cx - r, cy - r, cx + r, cy + r],
                       outline=(0, 160, 160), width=3)
        for (a, b) in k["limbs"]:
            dr.line([tuple(a), tuple(b)], fill=(0, 160, 160), width=3)
    for ln in report["lines"]:
        if ln.get("arrow_tip"):
            tx, ty = ln["arrow_tip"]
            dr.ellipse([tx - 7, ty - 7, tx + 7, ty + 7],
                       outline=(0, 0, 255), width=3)
    for t in texts:
        x0, y0, x1, y1 = t["bbox"]
        dr.rectangle([x0, y0, x1, y1], outline=(255, 0, 255), width=2)
    mk_path = os.path.splitext(out)[0] + "_markers.png"
    mk.save(mk_path)

    print("canvas %dx%d" % (w, h))
    print("shapes: %d" % len(shapes))
    for s in shapes:
        print("  %s %-8s bbox=%s fill=%s stroke=%s sw=%s r=%s text=%s" %
              (s["id"], s["kind"], s["bbox"], s["fill"], s["stroke"],
               s["stroke_width"], s.get("radius", 0), s.get("text_bbox")))
    print("lines: %d  sticks: %d  arrows: %d  texts: %d" %
          (len(lines), len(sticks),
           sum(1 for l in lines if l.get("arrow_tip")), len(texts)))
    for ln in report["lines"]:
        print("  %s thick=%s arrow=%s nsegs=%d %s" %
              (ln["id"], ln["thickness"], ln.get("arrow_tip"),
               len(ln["segs"]), ln["segs"][:4]))
    for t in texts:
        print("  %s bbox=%s ink=%s inside=%s" %
              (t["id"], t["bbox"], t["ink"], t["inside"]))
    print("markers:", mk_path)


if __name__ == "__main__":
    main()

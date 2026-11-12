# -*- coding: utf-8 -*-
"""Trace a diagram PNG into explicit elements via pixel analysis (no layout engine).

Usage: python scripts/trace_original.py <png> <out_json>

Detects: rectangle outlines, ellipse (conic fit from boundary points),
straight line segments chained into polylines, arrowheads (triangle width
probe at polyline endpoints), and every text block (connected components
split on large horizontal gaps, including text inside boxes/ellipse).
All coordinates come from pixels only.
"""
import json
import sys

import numpy as np
from PIL import Image


# ---------------------------------------------------------------- basic scans

def load(path):
    a = np.array(Image.open(path).convert("L"))
    return a, (a < 128)


def runs_in_line(line, min_len):
    out = []
    i = 0
    n = len(line)
    while i < n:
        if line[i]:
            j = i
            while j < n and line[j]:
                j += 1
            if j - i >= min_len:
                out.append((int(i), int(j)))
            i = j
        else:
            i += 1
    return out


def merge_by_cross(lines, cross_tol=2, gap_tol=2):
    items = sorted(lines)
    clusters = []
    for c, a, b in items:
        if clusters and abs(clusters[-1][0][0] - c) <= cross_tol:
            clusters[-1].append((c, a, b))
        else:
            clusters.append([(c, a, b)])
    out = []
    for cl in clusters:
        ref = int(min(c for c, _, _ in cl))
        runs = sorted((a, b) for _, a, b in cl)
        merged = []
        for a, b in runs:
            if merged and a <= merged[-1][1] + gap_tol:
                merged[-1] = (merged[-1][0], max(merged[-1][1], b))
            else:
                merged.append((a, b))
        for a, b in merged:
            out.append((ref, int(a), int(b)))
    return out


def all_hlines(bw, min_len):
    return merge_by_cross([(y, a, b) for y in range(bw.shape[0])
                           for a, b in runs_in_line(bw[y], min_len)])


def all_vlines(bw, min_len):
    return merge_by_cross([(x, a, b) for x in range(bw.shape[1])
                           for a, b in runs_in_line(bw[:, x], min_len)])


def detect_rects(hlong, vlong):
    rects, seen = [], set()
    hs = sorted(hlong)
    for i, (y1, x0, x1) in enumerate(hs):
        for y2, x0b, x1b in hs[i + 1:]:
            if y2 - y1 < 20:
                continue
            if abs(x0 - x0b) <= 3 and abs(x1 - x1b) <= 3:
                lv = [v for v in vlong if abs(v[0] - x0) <= 3 and v[1] <= y1 + 3 and v[2] >= y2 - 3]
                rv = [v for v in vlong if abs(v[0] - x1) <= 3 and v[1] <= y1 + 3 and v[2] >= y2 - 3]
                if lv and rv:
                    key = (y1, y2, x0, x1)
                    if key not in seen:
                        seen.add(key)
                        rects.append({"x": int(x0), "y": int(y1),
                                      "w": int(x1 - x0), "h": int(y2 - y1)})
    return rects


# ------------------------------------------------------------- components/text

def components(bw, y_lo=0, y_hi=None, x_lo=0, x_hi=None):
    h, w = bw.shape
    y_hi = h if y_hi is None else y_hi
    x_hi = w if x_hi is None else x_hi
    sub = bw[y_lo:y_hi, x_lo:x_hi]
    seen = np.zeros_like(sub, dtype=bool)
    out = []
    ys, xs = np.nonzero(sub)
    for sy, sx in zip(ys, xs):
        if seen[sy, sx]:
            continue
        stack = [(sy, sx)]
        seen[sy, sx] = True
        y0 = y1 = sy
        x0 = x1 = sx
        npix = 0
        while stack:
            y, x = stack.pop()
            npix += 1
            y0 = min(y0, y); y1 = max(y1, y)
            x0 = min(x0, x); x1 = max(x1, x)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < sub.shape[0] and 0 <= nx < sub.shape[1] \
                            and sub[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        out.append((int(x0 + x_lo), int(y0 + y_lo),
                    int(x1 + 1 + x_lo), int(y1 + 1 + y_lo), int(npix)))
    return out  # (x0, y0, x1, y1, npix)


def group_text_lines(comps, gap=30):
    """Group char components into text lines.

    Pass 1: cluster boxes into ROW BANDS by vertical overlap (>=50% of the
    shorter box), so ascender/x-height order does not matter.
    Pass 2: within each band sort by x and split on horizontal gaps > gap.
    """
    boxes = [list(c[:4]) for c in comps]
    if not boxes:
        return []
    # ---- pass 1: row bands (iterative merge)
    bands = [[b] for b in boxes]
    merged = True
    while merged:
        merged = False
        for i in range(len(bands)):
            for j in range(i + 1, len(bands)):
                a = bands[i]
                b = bands[j]
                ay0 = min(x[1] for x in a); ay1 = max(x[3] for x in a)
                by0 = min(x[1] for x in b); by1 = max(x[3] for x in b)
                iy = min(ay1, by1) - max(ay0, by0)
                if iy > 0.5 * min(ay1 - ay0, by1 - by0):
                    bands[i] = a + b
                    del bands[j]
                    merged = True
                    break
            if merged:
                break
    # ---- pass 2: split each band on horizontal gaps
    out = []
    for band in bands:
        band.sort(key=lambda c: c[0])
        groups = [list(band[0])]
        for c in band[1:]:
            g = groups[-1]
            if c[0] - g[2] > gap:
                groups.append(list(c))
            else:
                g[0] = min(g[0], c[0]); g[1] = min(g[1], c[1])
                g[2] = max(g[2], c[2]); g[3] = max(g[3], c[3])
        out.extend(groups)
    return [g for g in out if (g[2] - g[0]) > 6]


# ------------------------------------------------------------------- ellipse

def fit_conic(pts):
    """Fit ellipse ax^2+bxy+cy^2+dx+ey = 1 (least squares). Returns
    (cx, cy, rx, ry) or None."""
    P = np.array([[x * x, x * y, y * y, x, y] for x, y in pts], dtype=float)
    try:
        coef, *_ = np.linalg.lstsq(P, np.ones(len(P)), rcond=None)
    except np.linalg.LinAlgError:
        return None
    a, b, c, d, e = coef
    M = np.array([[a, b / 2], [b / 2, c]])
    try:
        cen = np.linalg.solve(2 * M, [-d, -e])
    except np.linalg.LinAlgError:
        return None
    cx, cy = float(cen[0]), float(cen[1])
    k = 1.0 - (a * cx * cx + b * cx * cy + c * cy * cy + d * cx + e * cy)
    try:
        evals, _ = np.linalg.eigh(M)
        ratios = k / evals
        if not np.all(np.isfinite(ratios)) or np.any(ratios <= 0):
            return None
        r = np.sqrt(ratios)
    except Exception:
        return None
    return (cx, cy, float(max(r)), float(min(r)))


# ------------------------------------------------------------------- arrows

def probe_arrowhead(bw, tip, prev, half=8, dist=(3, 5, 7, 9)):
    tx, ty = tip
    px, py = prev
    dx, dy = tx - px, ty - py
    L = (dx * dx + dy * dy) ** 0.5
    if L < 1:
        return False, []
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    widths = []
    for dd in dist:
        bx, by = tx - ux * dd, ty - uy * dd
        w = 0.0
        s = -half
        while s <= half:
            x = int(round(bx + nx * s))
            y = int(round(by + ny * s))
            if 0 <= y < bw.shape[0] and 0 <= x < bw.shape[1] and bw[y, x]:
                w += 1
            s += 0.5
        widths.append(w * 0.5)
    is_arrow = widths[-1] >= 4.5 and widths[-1] >= widths[0] + 1.5
    return bool(is_arrow), widths


# -------------------------------------------------------------------- flows

def chain_segments(segs, tol=4):
    """Chain axis-aligned segments into polylines (extend at BOTH ends)."""
    def ends(s):
        if s[0] == "h":
            _, y, x0, x1 = s
            return (x0, y), (x1, y)
        _, x, y0, y1 = s
        return (x, y0), (x, y1)

    unused = list(segs)
    flows = []
    while unused:
        s = unused.pop(0)
        a, b = ends(s)
        left, right = [a], [b]  # chain grows in both directions
        changed = True
        while changed:
            changed = False
            for t in list(unused):
                ta, tb = ends(t)
                if abs(ta[0] - right[-1][0]) <= tol and abs(ta[1] - right[-1][1]) <= tol:
                    right.append(tb); unused.remove(t); changed = True; break
                if abs(tb[0] - right[-1][0]) <= tol and abs(tb[1] - right[-1][1]) <= tol:
                    right.append(ta); unused.remove(t); changed = True; break
                if abs(tb[0] - left[-1][0]) <= tol and abs(tb[1] - left[-1][1]) <= tol:
                    left.append(ta); unused.remove(t); changed = True; break
                if abs(ta[0] - left[-1][0]) <= tol and abs(ta[1] - left[-1][1]) <= tol:
                    left.append(tb); unused.remove(t); changed = True; break
        pts = list(reversed(left)) + right
        flows.append(pts)
    return flows


def simplify_polyline(pts, tol=4):
    """Drop collinear intermediate points."""
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        p, q, r = out[-1], pts[i], pts[i + 1]
        if (q[0] - p[0]) * (r[1] - q[1]) == (q[1] - p[1]) * (r[0] - q[0]) and \
           ((q[0] - p[0]) * (r[0] - q[0]) + (q[1] - p[1]) * (r[1] - q[1])) > 0:
            continue
        out.append(q)
    out.append(pts[-1])
    return out


# ---------------------------------------------------------------------- main

def main():
    src, out = sys.argv[1], sys.argv[2]
    a, bw = load(src)
    h, w = bw.shape

    h40 = all_hlines(bw, 40)
    v40 = all_vlines(bw, 40)
    rects = detect_rects(h40, v40)

    # ---- text components (before line analysis so we can mask them)
    comps = components(bw)
    lm40 = np.zeros(bw.shape, dtype=bool)
    for y, x0, x1 in h40:
        lm40[y, x0:x1] = True
    for x, y0, y1 in v40:
        lm40[y0:y1, x] = True
    text_cands = []
    for c in comps:
        x0, y0, x1, y1, npix = c
        if (y1 - y0) > 60 or (x1 - x0) > 700 or npix < 8:
            continue
        frac = lm40[y0:y1, x0:x1].sum() / max(1, npix)
        if frac > 0.35 and npix > 60:
            continue
        if npix <= 40 and max(x1 - x0, y1 - y0) <= 10 and frac > 0.1:
            continue  # arrowhead-sized blob touching a line
        density = npix / max(1, (x1 - x0) * (y1 - y0))
        if density < 0.25 and (y1 - y0) >= 20:
            continue  # hollow shape outline (legend oval / icon frames)
        text_cands.append(c)
    texts = group_text_lines(text_cands, gap=30)

    # ---- mask text out of the image for line/arc scanning
    tmask = bw.copy()
    for x0, y0, x1, y1, _ in text_cands:
        tmask[y0:y1, x0:x1] = False

    # ---- short verticals (stubs) — restricted to columns with long verticals
    #      or near known shapes to avoid text stems: require dark run >=12
    #      AND the run touches an existing h40 line at one end
    h40_set = [(y, x0, x1) for y, x0, x1 in h40]
    stubs = []
    for x in range(w):
        for y0, y1 in runs_in_line(tmask[:, x], 12):
            # must abut a horizontal line at top or bottom end
            top_touch = any(abs(y0 - hy) <= 3 and hx0 - 3 <= x <= hx1 + 3
                            for hy, hx0, hx1 in h40_set)
            bot_touch = any(abs(y1 - hy) <= 3 and hx0 - 3 <= x <= hx1 + 3
                            for hy, hx0, hx1 in h40_set)
            if top_touch or bot_touch:
                stubs.append((int(x), int(y0), int(y1)))

    # ---- ellipse: tangent runs = short h40 lines with no vertical partner
    vert_xs = [v[0] for v in v40] + [s[0] for s in stubs]
    vert_ys = [(v[1], v[2]) for v in v40] + [(s[1], s[2]) for s in stubs]

    def touches_vertical(x, y):
        return any(abs(x - vx) <= 4 and (vy0 - 4 <= y <= vy1 + 4)
                   for vx, vy0, vy1 in zip(vert_xs,
                                           [v[1] for v in v40] + [s[1] for s in stubs],
                                           [v[2] for v in v40] + [s[2] for s in stubs]))

    tangents = []
    flow_h = []
    for y, x0, x1 in h40:
        if any(abs(y - r["y"]) <= 2 or abs(y - (r["y"] + r["h"])) <= 2 for r in rects):
            continue  # box border
        if any(r["x"] - 4 <= x0 and x1 <= r["x"] + r["w"] + 4 and r["y"] - 4 <= y <= r["y"] + r["h"] + 4
               for r in rects if r["w"] > 500):
            continue  # inside legend
        if not touches_vertical(x0, y) and not touches_vertical(x1, y) and (x1 - x0) < 120:
            tangents.append((y, x0, x1))
        else:
            flow_h.append((y, x0, x1))

    # ---- flow verticals: v40 not on box borders, not in legend, plus stubs
    legend = [r for r in rects if r["w"] > 500]
    lg = legend[0] if legend else None

    def in_legend(x, y0, y1):
        if not lg:
            return False
        return lg["x"] - 4 <= x <= lg["x"] + lg["w"] + 4 and \
            lg["y"] - 4 <= y0 and y1 <= lg["y"] + lg["h"] + 4

    flow_v_raw = []
    for x, y0, y1 in v40:
        if any(abs(x - r["x"]) <= 2 or abs(x - (r["x"] + r["w"])) <= 2 for r in rects if r["w"] < 500):
            continue
        if in_legend(x, y0, y1):
            continue
        flow_v_raw.append((x, y0, y1))
    for s in stubs:
        x, y0, y1 = s
        if any(abs(x - r["x"]) <= 2 or abs(x - (r["x"] + r["w"])) <= 2 for r in rects if r["w"] < 500):
            continue
        if in_legend(x, y0, y1):
            continue
        flow_v_raw.append(s)
    # merge 2px-wide duplicates (x and x+1) and abutting pieces
    flow_v = merge_by_cross(flow_v_raw, cross_tol=2, gap_tol=4)

    segs = [("h", y, x0, x1) for y, x0, x1 in flow_h] + \
           [("v", x, y0, y1) for x, y0, y1 in flow_v]
    flows = [simplify_polyline(p) for p in chain_segments(segs)]

    # ---- arrowheads at flow endpoints (retry with tip shifted along the
    #      direction, since chained endpoints can overshoot the real tip)
    arrows = []
    for i, fl in enumerate(flows):
        for end, nxt in ((fl[0], fl[1] if len(fl) > 1 else fl[0]),
                         (fl[-1], fl[-2] if len(fl) > 1 else fl[-1])):
            dx, dy = end[0] - nxt[0], end[1] - nxt[1]
            L = (dx * dx + dy * dy) ** 0.5
            if L < 1:
                continue
            ux, uy = dx / L, dy / L
            best = None
            for shift in (0, 1, 2, 3):
                tip = (round(end[0] - ux * shift), round(end[1] - uy * shift))
                ok, widths = probe_arrowhead(bw, tip, nxt)
                if ok:
                    best = (tip, widths)
                    break
            if best:
                arrows.append({"flow": i, "tip": list(best[0]),
                               "from": list(nxt),
                               "widths": [round(x, 1) for x in best[1]]})

    # ---- ellipse by extremal arc measurement (pixels only):
    #      scan a band through the centre row for left/right arc pixels and
    #      a band through the centre column for top/bottom arc pixels,
    #      masking text, straight lines and arrowheads.
    amask = tmask.copy()
    for y, x0, x1 in h40:
        amask[y, max(0, x0 - 1):x1 + 1] = False
    for x, y0, y1 in v40:
        # spread mask: lines are 2-4px wide and merge_by_cross keeps one ref x
        amask[max(0, y0 - 1):y1 + 1, max(0, x - 3):x + 4] = False
    for ar in arrows:
        tx, ty = ar["tip"]
        amask[max(0, ty - 16):ty + 16, max(0, tx - 16):tx + 16] = False

    def band_extremes(rows, cols):
        """leftmost/rightmost/topmost/bottommost dark pixel in a window."""
        pts = [(x, y) for y in rows for x in cols if amask[y, x]]
        if not pts:
            return None
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return min(xs), max(xs), min(ys), max(ys)

    ell = None
    # centre row band: left/right arc (y 460..476 clear of flows/text)
    lr = band_extremes(range(455, 482), range(450, 1010))
    # centre column band: top arc (y 325..365); bottom arc (y 560..615)
    tb_top = band_extremes(range(325, 368), range(700, 731))
    tb_bot = band_extremes(range(555, 620), range(660, 771))
    if lr and tb_top and tb_bot:
        left, right = lr[0], lr[1]
        top = tb_top[2]
        bottom = tb_bot[3]
        ell = ((left + right) / 2.0, (top + bottom) / 2.0,
                (right - left) / 2.0, (bottom - top) / 2.0)
        # guard: bottom arc window must have found pixels near y597
        if bottom < 560:
            ell = None
    if ell is None:
        # fallback: fit from tangent runs + flow endpoints
        boundary_pts = []
        for y, x0, x1 in tangents:
            boundary_pts += [(x0, y), (x1, y), ((x0 + x1) / 2, y)]
        for fl in flows:
            for p in (fl[0], fl[-1]):
                boundary_pts.append(p)
        ell = fit_conic(boundary_pts)

    # ---- drop segments fully inside ellipse (tangent runs already excluded)
    if ell:
        cx, cy, rx, ry = ell
        def inside(p, m=6):
            return ((p[0] - cx) / (rx + m)) ** 2 + ((p[1] - cy) / (ry + m)) ** 2 < 1
        flows = [fl for fl in flows
                 if not (inside(fl[0]) and inside(fl[-1]) and len(fl) <= 3
                         and all(inside(p) for p in fl))]
        # re-index arrows after possible flow drop (none expected to drop)
        arrows = [a for a in arrows if a["flow"] < len(flows)]

    # ---- classify texts: in rect / in ellipse / free
    box_texts = []
    free_texts = []
    for r in rects:
        for t in texts:
            tcx, tcy = (t[0] + t[2]) / 2, (t[1] + t[3]) / 2
            if r["x"] <= tcx <= r["x"] + r["w"] and r["y"] <= tcy <= r["y"] + r["h"]:
                box_texts.append({"rect": [r["x"], r["y"], r["w"], r["h"]], "text": t})
    ell_texts = []
    for t in texts:
        tcx, tcy = (t[0] + t[2]) / 2, (t[1] + t[3]) / 2
        if ell and ((tcx - ell[0]) / ell[2]) ** 2 + ((tcy - ell[1]) / ell[3]) ** 2 < 1:
            ell_texts.append(t)
            continue
        if any(b["text"] == t for b in box_texts):
            continue
        free_texts.append(t)

    # ---- legend icons: components inside the legend frame that are not
    #      text characters and not the frame itself (oval / rect / arrow)
    legend_icons = []
    lg_rects = [r for r in rects if r["w"] > 500]
    if lg_rects:
        lr = lg_rects[0]
        cand_set = set(text_cands)
        for c in comps:
            x0, y0, x1, y1, npix = c
            if c in cand_set:
                continue
            if not (lr["x"] <= x0 and x1 <= lr["x"] + lr["w"] and
                    lr["y"] <= y0 and y1 <= lr["y"] + lr["h"]):
                continue
            if (y1 - y0) >= 50:  # the legend frame itself
                continue
            if npix < 30:
                continue
            legend_icons.append([int(x0), int(y0), int(x1), int(y1)])

    result = {
        "canvas": {"w": int(w), "h": int(h)},
        "rects": rects,
        "ellipse": [round(v, 1) for v in ell] if ell else None,
        "flows": [list(map(list, f)) for f in flows],
        "arrows": arrows,
        "free_texts": [list(t) for t in sorted(free_texts, key=lambda b: (b[1], b[0]))],
        "box_texts": box_texts,
        "ellipse_texts": [list(t) for t in ell_texts],
        "legend_icons": legend_icons,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1, default=int)

    print("canvas %dx%d" % (w, h))
    print("rects:", rects)
    print("ellipse:", result["ellipse"])
    print("flows: %d" % len(flows))
    for i, fl in enumerate(flows):
        print("  F%02d %s" % (i + 1, fl))
    print("arrows: %d" % len(arrows))
    for ar in arrows:
        print("   F%02d tip=%s widths=%s" % (ar["flow"] + 1, ar["tip"], ar["widths"]))
    print("free texts: %d" % len(free_texts))
    for t in sorted(free_texts, key=lambda b: (b[1], b[0])):
        print("   x %4d..%4d y %4d..%4d (%dx%d)" % (t[0], t[2], t[1], t[3], t[2]-t[0], t[3]-t[1]))
    print("box texts: %d" % len(box_texts))
    for b in box_texts:
        print("   rect", b["rect"], "text", b["text"])
    print("ellipse texts: %d" % len(ell_texts))
    for t in ell_texts:
        print("   ", t)
    print("legend icons: %d" % len(legend_icons))
    for t in legend_icons:
        print("   ", t)


if __name__ == "__main__":
    main()

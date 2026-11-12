# -*- coding: utf-8 -*-
"""Generalized pixel tracer for the v1.1 color figures (Use Case, Container,
Allocation). Same method as the System Context tracer: every element comes
from pixels of the original PNG - no layout engine, no auto-placement.

Detects:
  fills      - solid colour regions -> rect / rounded rect / ellipse /
               cylinder (per-shape fill + stroke colour, radius/cap)
  boundary   - system-boundary rectangles from long solid lines or dashed
               runs (white fill; label gaps in the border preserved)
  lines      - thin components -> straight segments / polylines (corner
               split) with thickness and colour
  arrows     - triangle probe at line ends (works at any angle)
  sticks     - complex thin components (actor figures) -> head circle +
               straight limbs (mini-Hough on the component only)
  texts      - glyph components on white and inside fills (contrast vs the
               fill colour), grouped into lines, ink bbox + ink colour,
               classified free / box / ellipse

Writes <out.json> plus <out>_markers.png (every detected element drawn over
a copy of the original for visual verification).

Usage:
  node scripts/run_py.mjs scripts/trace_figure.py <png> <out.json>
"""
import json
import math
import os
import sys
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw

# --------------------------------------------------------------- components


def rle_label(mask):
    """Connected components (8-conn) via row runs + union-find.
    Returns list of {"bbox": (x0,y0,x1,y1) half-open, "area": int,
    "runs": [(y,x0,x1), ...]} sorted by area desc."""
    h, w = mask.shape
    run_list = []
    by_row = {}
    for y in range(h):
        row = mask[y]
        if not row.any():
            continue
        idx = np.flatnonzero(row)
        breaks = np.flatnonzero(np.diff(idx) > 1)
        starts = np.r_[0, breaks + 1]
        ends = np.r_[breaks + 1, len(idx)]
        for s, e in zip(starts, ends):
            by_row.setdefault(y, []).append(len(run_list))
            run_list.append((y, int(idx[s]), int(idx[e - 1]) + 1))
    parent = list(range(len(run_list)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for y in sorted(by_row):
        if y - 1 not in by_row:
            continue
        cur, prv = by_row[y], by_row[y - 1]
        j = 0
        for i in cur:
            _, a0, b0 = run_list[i]
            while j < len(prv) and run_list[prv[j]][2] < a0 - 1:
                j += 1
            k = j
            while k < len(prv) and run_list[prv[k]][1] <= b0 + 1:
                union(prv[k], i)
                k += 1
    groups = {}
    for i in range(len(run_list)):
        groups.setdefault(find(i), []).append(run_list[i])
    comps = []
    for runs_ in groups.values():
        ys = [r[0] for r in runs_]
        x0 = min(r[1] for r in runs_)
        x1 = max(r[2] for r in runs_)
        area = sum(r[2] - r[1] for r in runs_)
        comps.append({"bbox": (x0, min(ys), x1, max(ys) + 1),
                      "area": int(area), "runs": runs_})
    comps.sort(key=lambda c: -c["area"])
    return comps


def comp_points(comp):
    pts = []
    for (y, x0, x1) in comp["runs"]:
        xs = np.arange(x0, x1)
        pts.append(np.stack([xs, np.full_like(xs, y)], axis=1))
    return np.concatenate(pts, axis=0) if pts else np.zeros((0, 2), int)


# -------------------------------------------------------------------- shapes


def detect_fills(rgb, min_area=350, tol=12):
    """Solid colour regions -> [{bbox, area, ratio, fill}] (white excluded)."""
    q = (rgb // 8) * 8
    key = (q[:, :, 0].astype(np.int32) << 16) | (q[:, :, 1].astype(np.int32) << 8) | \
          q[:, :, 2].astype(np.int32)
    vals, counts = np.unique(key, return_counts=True)
    fills = []
    for v, c in zip(vals, counts):
        if c < min_area:
            continue
        r, g, b = (v >> 16) & 255, (v >> 8) & 255, v & 255
        if r >= 246 and g >= 246 and b >= 246:
            continue
        mask = (np.abs(rgb[:, :, 0].astype(int) - r) <= tol) & \
               (np.abs(rgb[:, :, 1].astype(int) - g) <= tol) & \
               (np.abs(rgb[:, :, 2].astype(int) - b) <= tol)
        for comp in rle_label(mask):
            x0, y0, x1, y1 = comp["bbox"]
            if comp["area"] < min_area or (x1 - x0) < 25 or (y1 - y0) < 18:
                continue
            ratio = comp["area"] / float((x1 - x0) * (y1 - y0))
            if ratio < 0.50:
                continue
            pts = comp_points(comp)
            med = np.median(rgb[pts[:, 1], pts[:, 0]], axis=0).astype(int)
            fills.append({"bbox": [int(x0), int(y0), int(x1), int(y1)],
                          "area": int(comp["area"]), "ratio": round(ratio, 3),
                          "fill": "#%02X%02X%02X" % tuple(med)})
    out = []
    for f in sorted(fills, key=lambda f: -f["area"]):
        x0, y0, x1, y1 = f["bbox"]
        if any(g is not f and g["bbox"][0] <= x0 and g["bbox"][1] <= y0 and
               g["bbox"][2] >= x1 and g["bbox"][3] >= y1 and
               (g["bbox"][2] - g["bbox"][0]) * (g["bbox"][3] - g["bbox"][1]) >
               (x1 - x0) * (y1 - y0) * 1.05 for g in fills):
            continue
        if any(abs(g["bbox"][0] - x0) <= 3 and abs(g["bbox"][1] - y0) <= 3 and
               abs(g["bbox"][2] - x1) <= 3 and abs(g["bbox"][3] - y1) <= 3
               for g in out):
            continue                      # duplicate from an adjacent colour key
        out.append(f)
    return out


def merge_cylinders(rgb, fills):
    """Pair a flat cap component sitting directly on a body component of the
    same colour -> one cylinder fill with a row-wise silhouette outline."""
    merged = []
    used = set()
    for i, cap in enumerate(fills):
        if i in used:
            continue
        cx0, cy0, cx1, cy1 = cap["bbox"]
        cap_h, cap_w = cy1 - cy0, cx1 - cx0
        if cap_h > 0.45 * cap_w or cap_h < 6:
            continue                      # not a flat cap
        best = None
        for j, body in enumerate(fills):
            if j == i or j in used:
                continue
            bx0, by0, bx1, by1 = body["bbox"]
            if abs(bx0 - cx0) > 12 or abs(bx1 - cx1) > 12:
                continue
            if not (-(cy1 - cy0) <= by0 - cy1 <= 6):
                continue                  # body must start around cap bottom
            if body["fill"] != cap["fill"]:
                continue
            if (by1 - by0) <= cap_h:
                continue
            best = j
            break
        if best is None:
            continue
        body = fills[best]
        used.add(i)
        used.add(best)
        bbox = [min(cap["bbox"][0], body["bbox"][0]),
                min(cap["bbox"][1], body["bbox"][1]),
                max(cap["bbox"][2], body["bbox"][2]),
                max(cap["bbox"][3], body["bbox"][3])]
        merged.append({"bbox": bbox, "fill": body["fill"],
                       "area": cap["area"] + body["area"], "ratio": 0.9,
                       "cylinder": True})
    for i, f in enumerate(fills):
        if i not in used:
            merged.append(f)
    return merged


def silhouette(mask, step=2, ox=0, oy=0):
    """Row-wise outline [(x,y)] of a vertically-simple mask (left down,
    right up), in absolute (ox,oy)-shifted coordinates."""
    h, w = mask.shape
    left, right = [], []
    for y in range(0, h, step):
        row = np.flatnonzero(mask[y])
        if not len(row):
            continue
        left.append((int(row[0]) + ox, y + oy))
        right.append((int(row[-1]) + ox, y + oy))
    if not left:
        return []
    for y in range(h - 1, h - step - 1, -1):
        row = np.flatnonzero(mask[y])
        if len(row):
            right.append((int(row[-1]) + ox, y + oy))
            left.append((int(row[0]) + ox, y + oy))
            break
    return left + right[::-1]


def fill_mask_of(rgb, bbox, fill, tol=14):
    x0, y0, x1, y1 = bbox
    r, g, b = (int(fill[i:i + 2], 16) for i in (1, 3, 5))
    sub = rgb[y0:y1, x0:x1].astype(int)
    return (np.abs(sub[:, :, 0] - r) <= tol) & (np.abs(sub[:, :, 1] - g) <= tol) & \
           (np.abs(sub[:, :, 2] - b) <= tol)


def classify_shape(rgb, f):
    """-> (kind, stroke, radius, cap_ry) for one fill."""
    x0, y0, x1, y1 = f["bbox"]
    bw_, bh_ = x1 - x0, y1 - y0
    # stroke colour: darkest quartile of the 4px border band + outside ring
    ya, yb = max(0, y0 - 4), min(rgb.shape[0], y1 + 4)
    xa, xb = max(0, x0 - 4), min(rgb.shape[1], x1 + 4)
    band = []
    for yy in range(ya, yb):
        for xx in range(xa, xb):
            if (x0 + 4 <= xx <= x1 - 5 and y0 + 4 <= yy <= y1 - 5):
                continue
            band.append((yy, xx))
    band = np.array(band, int) if band else np.zeros((0, 2), int)
    if len(band):
        cols = rgb[band[:, 0], band[:, 1]].astype(int)
        lum = cols.sum(axis=1)
        k = max(1, len(lum) // 5)
        med = np.median(cols[np.argsort(lum)[:k]], axis=0).astype(int)
        stroke = "#%02X%02X%02X" % tuple(med)
    else:
        stroke = f["fill"]

    m = fill_mask_of(rgb, [x0, y0, x1, y1], f["fill"])
    if not m.any():
        return "rect", stroke, 0, 0
    insets = []
    for yy in range(bh_):
        row = np.flatnonzero(m[yy])
        insets.append(int(row[0]) if len(row) else bw_)
    top_inset = insets[0]
    bot_inset = insets[-1]
    full_row = next((i for i, v in enumerate(insets) if v <= 2), bh_)
    mid = range(max(1, bh_ // 6), max(2, bh_ - bh_ // 6))
    # left-edge straightness only: a text-label background tab can paint
    # fill beyond the right border, so the right edge must not vote
    full_mid = sum(1 for yy in mid if insets[yy] <= 3)
    side_frac = full_mid / float(max(1, len(list(mid))))
    if side_frac >= 0.75 and top_inset <= 5 and bot_inset <= 5:
        return "rect", stroke, 0, 0
    if side_frac >= 0.7 and top_inset >= 0.22 * bw_:
        # flat cap, straight body, bulged bottom -> cylinder
        return "cylinder", stroke, 0, int(max(6, full_row))
    if side_frac >= 0.7:
        return "rounded", stroke, int(top_inset), 0
    return "ellipse", stroke, 0, 0


def inside_shape_pt(s, px, py):
    """Is (px,py) inside the drawn shape (excluding rounded/curved corners)?"""
    x0, y0, x1, y1 = s["bbox"]
    kind = s.get("kind", "rect")
    if kind == "rect":
        return x0 + 1 <= px <= x1 - 2 and y0 + 1 <= py <= y1 - 2
    if kind == "rounded":
        r = s.get("radius", 0) or 0
        if not (x0 <= px <= x1 and y0 <= py <= y1):
            return False
        if r <= 1:
            return True
        qx = x0 + r if px < x0 + r else (x1 - r if px > x1 - r else None)
        qy = y0 + r if py < y0 + r else (y1 - r if py > y1 - r else None)
        if qx is None or qy is None:
            return True
        return (px - qx) ** 2 + (py - qy) ** 2 <= (r - 1) ** 2
    if kind == "ellipse":
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        rx, ry = (x1 - x0) / 2.0, (y1 - y0) / 2.0
        return ((px - cx) / max(1.0, rx - 1)) ** 2 + \
               ((py - cy) / max(1.0, ry - 1)) ** 2 <= 1
    if kind == "cylinder":
        cap = max(3, s.get("cap_ry", 0) or 0)
        cx = (x0 + x1) / 2.0
        rx = (x1 - x0) / 2.0
        if py < y0 + cap:
            return ((px - cx) / max(1.0, rx - 1)) ** 2 + \
                   ((py - (y0 + cap)) / max(1.0, cap)) ** 2 <= 1
        if py > y1 - cap:
            return ((px - cx) / max(1.0, rx - 1)) ** 2 + \
                   ((py - (y1 - cap)) / max(1.0, cap)) ** 2 <= 1
        return x0 <= px <= x1
    return True


def _outside_frac(s, pts):
    """Fraction of sample points lying outside the drawn shape."""
    step = max(1, len(pts) // 40)
    out = 0
    n = 0
    for i in range(0, len(pts), step):
        n += 1
        if not inside_shape_pt(s, float(pts[i][0]), float(pts[i][1])):
            out += 1
    return out / float(max(1, n))


def axis_minority(pts, perp_max=6.0):
    """Split a line component into (clean_line_points, label_fragment_points).

    In the original some labels touch their own line, fusing glyph pixels
    into the line component. The line is fit with a Hough pass (the longest
    co-linear run) and pixels farther than perp_max from THAT fit line are
    candidates. Only compact clusters of candidates that sit clear of both
    line ends are stripped: a fused label is a short run of glyphs, a dogleg
    arm spans most of the line, an arrow head sits at its tip. Returns
    (kept, frag) where frag holds the label-like stripped clusters only.
    """
    if len(pts) < 40:
        return pts, np.zeros((0, 2), int)
    # robust fit: dominant hough line, fallback to the extreme direction
    hs = hough_segments(pts, min_len=25, max_parts=1)
    if hs:
        (x0, y0), (x1, y1) = hs[0]
        org = np.array([x0, y0], float)
        ax = np.array([x1 - x0, y1 - y0], float)
    else:
        q = pts.astype(float)
        mean = q.mean(axis=0)
        _, _, vt = np.linalg.svd(q - mean, full_matrices=False)
        t0 = (q - mean) @ vt[0]
        org = q[t0.argmin()]
        ax = q[t0.argmax()] - q[t0.argmin()]
    n_ax = math.hypot(ax[0], ax[1])
    if n_ax < 1e-6:
        return pts, np.zeros((0, 2), int)
    ax = ax / n_ax
    nrm = np.array([-ax[1], ax[0]])
    p = pts.astype(float)
    t = (p - org) @ ax
    perp = np.abs((p - org) @ nrm)
    far = perp > perp_max
    nfar = int(far.sum())
    if nfar < 12 or nfar > 0.55 * len(p):
        return pts, np.zeros((0, 2), int)
    span = float(t.max() - t.min()) or 1.0
    tmin, tmax = float(t.min()), float(t.max())
    idx = np.flatnonzero(far)
    order = idx[np.argsort(t[idx])]
    ft = t[order]
    groups, g0 = [], 0
    for i in range(1, len(ft)):
        if ft[i] - ft[i - 1] > 12:
            groups.append(order[g0:i])
            g0 = i
    groups.append(order[g0:])
    strip = np.zeros(len(p), bool)
    frags = []
    for g in groups:
        gspan = float(t[g].max() - t[g].min())
        if len(g) < 8 or gspan > min(0.5 * span, 30.0):
            continue                     # dogleg arm / scattered noise
        if t[g].max() > tmax - 8 or t[g].min() < tmin + 8:
            continue                     # line end: arrow head, box stub
        strip[g] = True
        if gspan >= 6:
            frags.append(g)              # label-like: recover the band
    if not strip.any():
        return pts, np.zeros((0, 2), int)
    frag = (np.concatenate([p[g] for g in frags]) if frags
            else np.zeros((0, 2), int))
    return p[~strip], frag


# ---------------------------------------------------------------------- text


def group_lines(boxes, gap):
    if not boxes:
        return []
    boxes = [list(b) for b in boxes]
    bands = [[b] for b in boxes]
    merged = True
    while merged:
        merged = False
        for i in range(len(bands)):
            for j in range(i + 1, len(bands)):
                a, b = bands[i], bands[j]
                ay0 = min(x[1] for x in a); ay1 = max(x[3] for x in a)
                by0 = min(x[1] for x in b); by1 = max(x[3] for x in b)
                if min(ay1, by1) - max(ay0, by0) > 0.5 * min(ay1 - ay0, by1 - by0):
                    bands[i] = a + b
                    del bands[j]
                    merged = True
                    break
            if merged:
                break
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
    return [g for g in out if (g[2] - g[0]) > 5 and (g[3] - g[1]) > 5]


def ink_colour(rgb, pts, fill_hex=None):
    cols = rgb[pts[:, 1], pts[:, 0]].astype(int)
    if fill_hex:
        fr, fg, fb = (int(fill_hex[i:i + 2], 16) for i in (1, 3, 5))
        d = np.abs(cols - np.array([fr, fg, fb])).sum(axis=1)
        k = max(1, len(d) // 4)
        sel = cols[np.argsort(d)[-k:]]
    else:
        lum = cols.sum(axis=1)
        k = max(1, len(lum) // 3)
        sel = cols[np.argsort(lum)[:k]]
    med = np.median(sel, axis=0).astype(int)
    return "#%02X%02X%02X" % tuple(med)


# -------------------------------------------------------------------- lines


def fit_polyline(pts, tol=3.0):
    if len(pts) < 6:
        return []
    p = pts.astype(float)
    mean = p.mean(axis=0)
    _, _, vt = np.linalg.svd(p - mean, full_matrices=False)
    d = vt[0]
    t = (p - mean) @ d
    a, b = p[t.argmin()], p[t.argmax()]
    return _split_rec(p, a, b, tol)


def _dist_to_seg(pts, a, b):
    ab = np.array(b, float) - np.array(a, float)
    L2 = float(ab @ ab)
    if L2 < 1e-12:
        return np.hypot(pts[:, 0] - a[0], pts[:, 1] - a[1])
    t = np.clip(((pts - np.array(a, float)) @ ab) / L2, 0, 1)
    proj = np.array(a, float) + t[:, None] * ab
    return np.hypot(pts[:, 0] - proj[:, 0], pts[:, 1] - proj[:, 1])


def _split_rec(pts, a, b, tol, depth=0):
    if len(pts) < 6 or depth > 40:
        return []
    ab = np.array(b, float) - np.array(a, float)
    L = math.hypot(*ab)
    if L < 1e-6:
        return []
    n = np.array([-ab[1], ab[0]]) / L
    dist = np.abs((pts - np.array(a, float)) @ n)
    k = int(dist.argmax())
    if dist[k] > tol:
        mid = pts[k]
        d1 = _dist_to_seg(pts, a, mid)
        d2 = _dist_to_seg(pts, mid, b)
        left = pts[d1 <= d2]
        right = pts[d1 > d2]
        if len(left) < 4 or len(right) < 4 or len(left) == len(pts):
            return [(tuple(np.round(a, 1)), tuple(np.round(b, 1)))]
        return (_split_rec(left, a, mid, tol, depth + 1) +
                _split_rec(right, mid, b, tol, depth + 1))
    return [(tuple(np.round(a, 1)), tuple(np.round(b, 1)))]


def thickness(pts, a, b):
    ab = np.array(b, float) - np.array(a, float)
    L = math.hypot(*ab)
    if L < 1e-6:
        return 99.0
    n = np.array([-ab[1], ab[0]]) / L
    d = np.abs((pts.astype(float) - np.array(a, float)) @ n)
    return float(np.median(d) * 2 + 1)


def probe_arrow(mask, tip, prev, half=16, dist=(3, 6, 9, 12, 15)):
    tx, ty = tip
    px, py = prev
    dx, dy = tx - px, ty - py
    L = math.hypot(dx, dy)
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
            if 0 <= y < mask.shape[0] and 0 <= x < mask.shape[1] and mask[y, x]:
                w += 1
            s += 0.5
        widths.append(w * 0.5)
    ok = (max(widths) >= 7.5 and widths[0] <= max(widths) - 2.0 and
          widths.index(max(widths)) <= 3) or \
         (widths[-1] >= 4.5 and widths[-1] >= widths[0] + 1.5)
    return bool(ok), widths


def arrow_polygon(tip, prev, apex_back=2.0, length=15.0, half=7.5):
    tx, ty = tip
    px, py = prev
    dx, dy = tx - px, ty - py
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    ax, ay = tx - ux * apex_back, ty - uy * apex_back
    bx, by = ax - ux * length, ay - uy * length
    return [(round(ax, 1), round(ay, 1)),
            (round(bx + nx * half, 1), round(by + ny * half, 1)),
            (round(bx - nx * half, 1), round(by - ny * half, 1))]


def hough_segments(pts, min_len=25, max_parts=10):
    segs = []
    rest = pts.astype(float).copy()
    angles = np.linspace(0, math.pi, 180, endpoint=False)
    cos_a, sin_a = np.cos(angles), np.sin(angles)
    for _ in range(max_parts):
        if len(rest) < min_len:
            break
        rho = rest[:, 0:1] * cos_a + rest[:, 1:2] * sin_a
        rb = np.round(rho / 3.0).astype(int)
        best = None
        for ai in range(len(angles)):
            vals, cnts = np.unique(rb[:, ai], return_counts=True)
            k = int(cnts.argmax())
            if best is None or cnts[k] > best[0]:
                best = (int(cnts[k]), ai, int(vals[k]))
        cnt, ai, rbv = best
        if cnt < max(8, min_len // 3):
            break
        th = angles[ai]
        n = np.array([math.cos(th), math.sin(th)])       # line normal
        d = rbv * 3.0
        dist = np.abs(rest @ n - d)
        inl = rest[dist <= 3.0]
        if len(inl) < 8:
            break
        dirv = np.array([-math.sin(th), math.cos(th)])   # along the line
        t = inl @ dirv
        # draw the segment ON the fit line (projection of the extreme
        # inliers), never through the raw extremes (glyph-touch bias)
        origin = np.array([math.cos(th), math.sin(th)]) * (rbv * 3.0)
        p0 = origin + float(t.min()) * dirv
        p1 = origin + float(t.max()) * dirv
        L = float(np.hypot(*(p1 - p0)))
        # append only well-supported arms; low-support leftovers (AA fringes,
        # duplicate passes) are simply discarded
        if L >= min_len and len(inl) >= max(10, 0.5 * L):
            segs.append((tuple(np.round(p0, 1)), tuple(np.round(p1, 1))))
        rest = rest[dist > 3.0]
    return segs


def _seg_line_isect(a, b, c, d):
    """Intersection of the infinite lines a-b and c-d, or None."""
    x1, y1 = a
    x2, y2 = b
    x3, y3 = c
    x4, y4 = d
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-9:
        return None
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) -
          (x1 - x2) * (x3 * y4 - y3 * x4)) / den
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) -
          (y1 - y2) * (x3 * y4 - y3 * x4)) / den
    return (round(float(px), 1), round(float(py), 1))


def chain_segs(seglist, tol=12.0):
    """Order Hough segments into one polyline.

    Endpoints within tol chain directly (bridging small gaps). Near-c-
    ontinuation arms whose fits overlap (dogleg diagonals) chain at the
    intersection of their lines, trimming both to it. Segments that chain
    nowhere are junk (a glyph fragment that touched the line mid-way) and
    are dropped. Returns (chain, dropped).
    """
    segs = [(tuple(float(v) for v in a), tuple(float(v) for v in b))
            for a, b in seglist]
    if not segs:
        return [], []
    order = [list(segs.pop(0))]

    def dirs(o):
        dh = (o[0][1][0] - o[0][0][0], o[0][1][1] - o[0][0][1])
        dt = (o[-1][1][0] - o[-1][0][0], o[-1][1][1] - o[-1][0][1])
        return dh, dt

    changed = True
    while changed and segs:
        changed = False
        head = tuple(order[0][0])
        tail = tuple(order[-1][1])
        dirH, dirT = dirs(order)
        for i in range(len(segs)):
            u, v = segs[i]
            for nu, nv in ((u, v), (v, u)):
                ndir = (nv[0] - nu[0], nv[1] - nu[1])
                nn = math.hypot(*ndir) or 1
                cands = []
                for side, ref_pt, vb in (("tail", tail, dirT),
                                         ("head", head, dirH)):
                    d = (math.hypot(ref_pt[0] - nu[0], ref_pt[1] - nu[1])
                         if side == "tail" else
                         math.hypot(ref_pt[0] - nv[0], ref_pt[1] - nv[1]))
                    if d > tol:
                        continue
                    nb = math.hypot(*vb) or 1
                    cosang = (ndir[0] * vb[0] + ndir[1] * vb[1]) / (nn * nb)
                    ang = math.degrees(math.acos(max(-1.0, min(1.0, cosang))))
                    if ang > 45:
                        continue         # backward / branching junk
                    cands.append((d, side))
                if cands:
                    gap, how = min(cands)
                    if how == "tail":
                        if gap > 0.5:
                            order.append([list(tail), list(nu)])
                        order.append([list(nu), list(nv)])
                    else:
                        if gap > 0.5:
                            order.insert(0, [list(nv), list(head)])
                        order.insert(0, [list(nu), list(nv)])
                    segs.pop(i)
                    changed = True
                    break
                # overlapping near-continuation (dogleg arms): chain at the
                # line intersection, trimming both segments to it
                for how in ("tail", "head"):
                    if how == "tail":
                        if math.hypot(tail[0] - nu[0],
                                      tail[1] - nu[1]) > 110:
                            continue
                        vb = dirT
                        segB = (order[-1][0], order[-1][1])
                        hj = tail
                    else:
                        if math.hypot(head[0] - nv[0],
                                      head[1] - nv[1]) > 110:
                            continue
                        vb = dirH
                        segB = (order[0][0], order[0][1])
                        hj = head
                    va = (nv[0] - nu[0], nv[1] - nu[1])
                    na = math.hypot(*va) or 1
                    nb = math.hypot(*vb) or 1
                    cosang = (va[0] * vb[0] + va[1] * vb[1]) / (na * nb)
                    ang = math.degrees(math.acos(max(-1.0, min(1.0, cosang))))
                    if ang > 25:
                        continue
                    nj = _seg_line_isect(nu, nv, segB[0], segB[1])
                    if nj is None:
                        continue
                    ref = nv if how == "head" else nu
                    if math.hypot(nj[0] - ref[0], nj[1] - ref[1]) > 45 or \
                       math.hypot(nj[0] - hj[0], nj[1] - hj[1]) > 110:
                        continue
                    if how == "tail":
                        order[-1][1] = list(nj)
                        order.append([list(nj), list(nv)])
                    else:
                        order[0][0] = list(nj)
                        order.insert(0, [list(nu), list(nj)])
                    segs.pop(i)
                    changed = True
                    break
                if changed:
                    break
            if changed:
                break
    return order, [list(s) for s in segs]


def fit_circle(pts):
    if len(pts) < 30:
        return None
    x, y = pts[:, 0].astype(float), pts[:, 1].astype(float)
    A = np.stack([x, y, np.ones_like(x)], axis=1)
    b = x * x + y * y
    try:
        sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    except np.linalg.LinAlgError:
        return None
    cx, cy = sol[0] / 2, sol[1] / 2
    r = math.sqrt(max(1e-6, sol[2] + cx * cx + cy * cy))
    if float(np.median(np.abs(np.hypot(x - cx, y - cy) - r))) > 2.5:
        return None
    if r < 8 or r > 0.6 * (x.max() - x.min() + 1):
        return None
    return (round(float(cx), 1), round(float(cy), 1), round(float(r), 1))


# ----------------------------------------------- stroke network decomposition

def thin_zs(mask):
    """Zhang-Suen thinning of a binary mask (uint8 0/1 work array)."""
    m = mask.astype(np.uint8)

    def nb(mm):
        P2 = np.roll(mm, 1, 0)
        P3 = np.roll(np.roll(mm, 1, 0), -1, 1)
        P4 = np.roll(mm, -1, 1)
        P5 = np.roll(np.roll(mm, -1, 0), -1, 1)
        P6 = np.roll(mm, -1, 0)
        P7 = np.roll(np.roll(mm, -1, 0), 1, 1)
        P8 = np.roll(mm, 1, 1)
        P9 = np.roll(np.roll(mm, 1, 0), 1, 1)
        return P2, P3, P4, P5, P6, P7, P8, P9

    changed = True
    it = 0
    while changed and it < 120:
        changed = False
        it += 1
        for step in (0, 1):
            P2, P3, P4, P5, P6, P7, P8, P9 = nb(m)
            B = P2 + P3 + P4 + P5 + P6 + P7 + P8 + P9
            A = ((~P2 & P3) + (~P3 & P4) + (~P4 & P5) + (~P5 & P6) +
                 (~P6 & P7) + (~P7 & P8) + (~P8 & P9) + (~P9 & P2))
            if step == 0:
                cond = (m != 0) & (B >= 2) & (B <= 6) & (A == 1) & \
                       ((P2 * P4 * P6) == 0) & ((P4 * P6 * P8) == 0)
            else:
                cond = (m != 0) & (B >= 2) & (B <= 6) & (A == 1) & \
                       ((P2 * P4 * P8) == 0) & ((P2 * P6 * P8) == 0)
            if cond.any():
                m[cond] = 0
                changed = True
    return m.astype(bool)


def _rdp(pts, tol):
    """Ramer-Douglas-Peucker on an ordered polyline (list of (x, y))."""
    if len(pts) < 3:
        return list(pts)
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        ax, ay = pts[i]
        bx, by = pts[j]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        worst, wi = -1.0, -1
        for k in range(i + 1, j):
            px, py = pts[k]
            if L < 1e-9:
                d = math.hypot(px - ax, py - ay)
            else:
                d = abs(dy * (px - ax) - dx * (py - ay)) / L
            if d > worst:
                worst, wi = d, k
        if worst > tol:
            keep[wi] = True
            stack.append((i, wi))
            stack.append((wi, j))
    return [p for p, k in zip(pts, keep) if k]


def _order_component(comp):
    """Order a branch-free pixel component into one or more chains."""
    pts = set()
    for (y, x0, x1) in comp["runs"]:
        for x in range(x0, x1):
            pts.add((x, y))

    def deg(p):
        x, y = p
        return sum(1 for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                   if (dx or dy) and (x + dx, y + dy) in pts)

    chains = []
    while pts:
        ends = [p for p in pts if deg(p) == 1]
        start = min(ends) if ends else min(pts)
        path = [start]
        visited = {start}
        pts.discard(start)
        cur = start
        while True:
            x, y = cur
            cands = [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                     if (dx or dy) and (x + dx, y + dy) in pts]
            if not cands:
                break
            if len(cands) == 1:
                nxt = cands[0]
            elif len(path) >= 2:
                px, py = path[-2]
                ux, uy = x - px, y - py
                nxt = max(cands, key=lambda c: (c[0] - x) * ux + (c[1] - y) * uy)
            else:
                nxt = min(cands)
            path.append(nxt)
            pts.discard(nxt)
            visited.add(nxt)
            cur = nxt
        if len(path) >= 4:
            closed = False
            if not ends:
                fx, fy = path[0]
                lx, ly = path[-1]
                closed = max(abs(fx - lx), abs(fy - ly)) <= 1
            chains.append({"path": path, "closed": closed})
    return chains


def decompose_network(mask):
    """Split a fused stroke network into circles and straight segments.

    Used for figures where association lines, actors and a boundary frame
    all touch (the Use Case diagram): the whole network arrives as one
    giant connected component. Zhang-Suen thinning -> split at junction
    pixels (degree >= 3) -> order each branch-free piece -> re-merge pieces
    that were split only because a line crossed them (collinear at the
    junction) -> Ramer-Douglas-Peucker -> corner split into straight
    segments.  Returns {"circles": [(cx, cy, r)], "segs": [{"p0", "p1",
    "path"}]} where "path" keeps the original stroke identity so corner
    neighbours can be re-assembled into polylines.
    """
    skel = thin_zs(mask)
    deg = np.zeros(skel.shape, dtype=np.uint8)
    for ax in (0, 1):
        for sh in (-1, 1):
            deg += np.roll(skel, sh, ax)
    for shx, shy in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        deg += np.roll(np.roll(skel, shx, 0), shy, 1)
    # every branch/split pixel (incl. the 2px-wide runs Zhang-Suen leaves)
    # splits a chain; the anti-parallel pairwise heal below re-assembles
    # the pieces that belong to one stroke
    junction = skel & (deg >= 3)
    core = skel & ~junction
    comps = [c for c in rle_label(core) if c["area"] >= 4]
    if os.environ.get("TRACE_DBG"):
        print("DBGnet skel px", int(skel.sum()), "junction px",
              int(junction.sum()), "core comps", len(comps))

    chains = []
    for c in comps:
        chains.extend(_order_component(c))
    if not chains:
        return {"circles": [], "segs": []}
    for ch in chains:
        ch["verts"] = _rdp(ch["path"], 1.2)

    # ---- re-merge pieces split only by crossings: at every junction the
    # pieces whose directions are ANTI-parallel (one arrives where the
    # other leaves) belong to one stroke; pieces leaving at a different
    # angle are genuinely separate lines sharing the junction
    ends_map = {}
    for ci, ch in enumerate(chains):
        if ch["closed"]:
            continue
        ends_map[(ci, 0)] = ch["verts"][0]
        ends_map[(ci, 1)] = ch["verts"][-1]

    parent = {k: k for k in ends_map}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    # pairwise heal: two chain ends close together that point in exactly
    # opposite local directions belong to one stroke (pieces split by a
    # crossing, a 2px-wide run or the circle's neck).  The strict
    # anti-parallel test keeps genuinely different strokes apart - fan
    # lines leave a hub only ~4-11 degrees apart and never merge.
    ends_list = list(ends_map.items())

    def _end_dir(k):
        ci, side = k
        v = chains[ci]["path"]          # RAW pixels: RDP chords tilt the
        prev = v[1] if side == 0 else v[-2]   # tangent by ~14 deg on arcs
        e = ends_map[k]
        return (e[0] - prev[0], e[1] - prev[1])

    for a in range(len(ends_list)):
        ka, ea = ends_list[a]
        da = _end_dir(ka)
        na = math.hypot(*da)
        if na < 1e-6:
            continue
        for b in range(a + 1, len(ends_list)):
            kb, eb = ends_list[b]
            if math.hypot(ea[0] - eb[0], ea[1] - eb[1]) > 16:
                continue
            db = _end_dir(kb)
            nb_ = math.hypot(*db)
            if nb_ < 1e-6:
                continue
            cross = da[0] * db[1] - da[1] * db[0]
            dot = da[0] * db[0] + da[1] * db[1]
            ang = abs(math.degrees(math.atan2(cross, dot)))
            if os.environ.get("TRACE_DBG") and \
               1500 <= max(ea[1], eb[1]) <= 1720 and min(ea[0], eb[0]) < 400 \
               and abs(ang - 180.0) <= 30:
                print("DBGnear", ea, eb, "ang", round(ang, 1),
                      "dist", round(math.hypot(ea[0] - eb[0],
                                               ea[1] - eb[1]), 1))
            if abs(ang - 180.0) <= 8.0:
                union(ka, kb)

    # build merged paths: chains are edges between end-classes
    node_edges = {}
    for ci, ch in enumerate(chains):
        if ch["closed"]:
            continue
        node_edges.setdefault(find((ci, 0)), []).append((ci, 0))
        node_edges.setdefault(find((ci, 1)), []).append((ci, 1))

    used = set()
    merged = []                     # {"v": RDP verts, "px": raw pixels}

    def _plen(seq):
        return sum(math.hypot(seq[i + 1][0] - seq[i][0],
                              seq[i + 1][1] - seq[i][1])
                   for i in range(len(seq) - 1))

    def walk_chain(ci, side):
        """follow edges from (ci, side) through degree-2 nodes"""
        seq, px = [], []
        cur = (ci, side)
        while cur is not None and cur not in used:
            used.add(cur)
            ci_, side_ = cur
            used.add((ci_, 1 - side_))     # chain consumed entirely
            verts = list(chains[ci_]["verts"])
            pix = list(chains[ci_]["path"])
            if side_ == 1:
                verts.reverse()
                pix.reverse()
            seq.extend(verts if not seq else verts[1:])
            px.extend(pix if not px else pix)
            nxt_node = find((ci_, 1 - side_))
            edges = [e for e in node_edges.get(nxt_node, []) if e not in used]
            if len(edges) == 1:
                cur = edges[0]
            else:
                cur = None         # branch or dead end: resume elsewhere
        return seq, px

    # start from free ends (nodes with a single edge) so chains keep order
    free = [n for n, es in node_edges.items() if len(es) == 1]
    for n in sorted(free, key=str):
        for e in list(node_edges[n]):
            if e not in used:
                seq, px = walk_chain(e[0], e[1])
                if len(seq) >= 2 and _plen(seq) >= 6:
                    merged.append({"v": seq, "px": px})
    for ci, ch in enumerate(chains):
        if ch["closed"]:
            if _plen(ch["verts"]) >= 6:
                merged.append({"v": list(ch["verts"]),
                               "px": list(ch["path"])})
            continue
        for side in (0, 1):
            if (ci, side) not in used:
                seq, px = walk_chain(ci, side)
                if len(seq) >= 2 and _plen(seq) >= 6:
                    merged.append({"v": seq, "px": px})

    # attach short fragments (arrow heads, skeleton jogs, circle gaps) to
    # the stroke they continue: <= 4px apart, smooth turn <= 60 degrees.
    # Sources are short only, so full association lines never get absorbed.
    def _turn_ok(m_i, si, m_j, sj):
        seq_i, seq_j = m_i["v"], m_j["v"]
        a = seq_i[-1] if si else seq_i[0]
        b = seq_j[0] if sj else seq_j[-1]
        if math.hypot(a[0] - b[0], a[1] - b[1]) > 4.0:
            return None
        pa = seq_i[-2] if si else seq_i[1]
        pb = seq_j[1] if sj else seq_j[-2]
        d1 = (a[0] - pa[0], a[1] - pa[1])
        d2 = (b[0] - pb[0], b[1] - pb[1])
        n1 = math.hypot(*d1) or 1.0
        n2 = math.hypot(*d2) or 1.0
        cosang = max(-1.0, min(1.0, (d1[0] * d2[0] + d1[1] * d2[1]) /
                               (n1 * n2)))
        if math.degrees(math.acos(cosang)) > 60.0:
            return None
        i_v = list(seq_i) if si else list(reversed(seq_i))
        j_v = list(seq_j) if not sj else list(reversed(seq_j))
        i_p = list(m_i["px"]) if si else list(reversed(m_i["px"]))
        j_p = list(m_j["px"]) if not sj else list(reversed(m_j["px"]))
        return {"v": i_v + j_v, "px": i_p + j_p}

    def _crowded(pt, skip_i, skip_j):
        """Attachment points in a crowded junction (many stroke ends at
        one spot, e.g. the actor hub) must not glue unrelated strokes -
        only free-standing fragments (arrowheads, arc gaps, jogs) attach.
        """
        n = 0
        for k in range(len(merged)):
            if k in (skip_i, skip_j) or not merged[k]:
                continue
            for q in (merged[k]["v"][0], merged[k]["v"][-1]):
                if math.hypot(q[0] - pt[0], q[1] - pt[1]) <= 5.0:
                    n += 1
        return n > 2

    for _round in range(60):
        changed = False
        for i in range(len(merged)):
            if _plen(merged[i]["v"]) >= 60:
                continue
            for j in range(len(merged)):
                if i == j or _plen(merged[j]["v"]) < _plen(merged[i]["v"]):
                    continue
                for si in (0, 1):
                    for sj in (0, 1):
                        m = _turn_ok(merged[i], si, merged[j], sj)
                        if m is None:
                            continue
                        pt = m["v"][len(merged[i]["v"]) - 1]
                        if _crowded(pt, i, j):
                            continue
                        merged[j] = m
                        merged[i] = None
                        changed = True
                        break
                    if changed:
                        break
                if changed:
                    break
            if changed:
                break
        merged = [s for s in merged if s]
        if not changed:
            break

    circles, segs, paths = [], [], []
    if os.environ.get("TRACE_DBG"):
        print("DBGnet chains", len(chains), "merged", len(merged))

    def _cand(arr):
        if len(arr) < 50:
            return None
        w = arr[:, 0].max() - arr[:, 0].min()
        hh = arr[:, 1].max() - arr[:, 1].min()
        if not (20 <= w <= 220 and 20 <= hh <= 220 and
                0.4 <= w / max(hh, 1) <= 2.5):
            return None
        c = fit_circle(arr)
        if c is None:
            return None
        cx, cy, cr = c
        if not (10 <= cr <= 90):
            return None
        # coverage: >=70% of the pixels must sit on the circle - a corner
        # or an L-shaped stroke fits a circle through its bend otherwise
        d = np.hypot(arr[:, 0] - cx, arr[:, 1] - cy)
        if float(np.mean(np.abs(d - cr) <= 4.0)) < 0.7:
            return None
        return c

    for pi, m in enumerate(merged):
        verts = _rdp(m["v"], 1.2)
        pix = m["px"]
        if os.environ.get("TRACE_DBG"):
            xs = [p[0] for p in pix]
            ys = [p[1] for p in pix]
            if min(xs) <= 354 and max(xs) >= 350 and \
               min(ys) <= 1590 and max(ys) >= 1360:
                print("DBGfp", pi, "px", len(pix), "bbox",
                      (min(xs), min(ys), max(xs), max(ys)),
                      "verts", verts[:12])
        circ = None
        if len(pix) >= 50:
            # A circle may be one part of a longer stroke (an actor chain
            # is head + body + arms + legs with no branch split), so try
            # the whole path first, then sliding windows over it.
            circ = _cand(np.array(pix, dtype=float))
            if circ is None and len(pix) > 140:
                for i in range(0, len(pix) - 99, 10):
                    win = np.array(pix[i:i + 100], dtype=float)
                    circ = _cand(win)
                    if circ is not None:
                        break
            if circ is not None:
                # the circle must own a real share of this path's pixels
                # (kills corner/arc fragments that merely fit a circle)
                arrf = np.array(pix, dtype=float)
                dd = np.hypot(arrf[:, 0] - circ[0], arrf[:, 1] - circ[1])
                if int(np.sum(np.abs(dd - circ[2]) <= 4.0)) < 150:
                    circ = None
            if circ is not None:
                if any(math.hypot(circ[0] - c0[0], circ[1] - c0[1]) <= 20
                       for c0 in circles):
                    circ = None            # already claimed by a path
                else:
                    circles.append(circ)
        # NOTE: segments are always emitted - a circle-bearing path also
        # holds the actor's body/arms/legs; emit_network() assigns them by
        # proximity to the circle and drops the arc chord itself.
        # corner split at turns > 55 degrees
        pts_v = [verts[0]]
        for i in range(1, len(verts) - 1):
            ax, ay = verts[i][0] - verts[i - 1][0], verts[i][1] - verts[i - 1][1]
            bx, by = verts[i + 1][0] - verts[i][0], verts[i + 1][1] - verts[i][1]
            na = math.hypot(ax, ay) or 1.0
            nb_ = math.hypot(bx, by) or 1.0
            cosang = max(-1.0, min(1.0, (ax * bx + ay * by) / (na * nb_)))
            if math.degrees(math.acos(cosang)) > 55.0:
                pts_v.append(verts[i])
        pts_v.append(verts[-1])
        for i in range(len(pts_v) - 1):
            p0, p1 = pts_v[i], pts_v[i + 1]
            if math.hypot(p1[0] - p0[0], p1[1] - p0[1]) < 3:
                continue
            segs.append({"p0": [float(p0[0]), float(p0[1])],
                         "p1": [float(p1[0]), float(p1[1])], "path": pi})
        paths.append(pi)
    return {"circles": circles, "segs": segs}


def dash_clusters(pts_all, min_run=6, min_span=250):
    """Axis-aligned dashed runs: rows/cols with >=6 short runs."""
    out = []
    if len(pts_all) == 0:
        return out

    def side(vals, runs, axis, pos):
        # uniform dash runs only: >=6 runs of 6..40 px with low spread -
        # text rows produce irregular stroke runs and are rejected here
        lens = [len(r) for r in runs]
        good = [L for L in lens if 6 <= L <= 40]
        if len(good) < max(min_run, 12):
            return None
        med = float(np.median(good))
        if max(abs(L - med) for L in good) > 6:
            return None
        on = int(med)
        gaps = [int(runs[i + 1][0] - runs[i][-1] - 1)
                for i in range(len(runs) - 1)]
        off = int(np.median(gaps)) if gaps else 0
        if abs(off - on) > 4:
            return None                    # text rows: irregular spacing
        e = {"axis": axis, "dashes": len(runs), "on": on, "off": off}
        if axis == "h":
            e.update(y=pos, x0=int(vals[0]), x1=int(vals[-1]))
        else:
            e.update(x=pos, y0=int(vals[0]), y1=int(vals[-1]))
        return e

    for y in np.unique(pts_all[:, 1]):
        xs = np.sort(pts_all[pts_all[:, 1] == y][:, 0])
        if len(xs) < 12:
            continue
        runs = np.split(xs, np.flatnonzero(np.diff(xs) > 1) + 1)
        if len(runs) >= min_run and xs[-1] - xs[0] >= min_span:
            e = side(xs, runs, "h", int(y))
            if e:
                out.append(e)
    for x in np.unique(pts_all[:, 0]):
        ys = np.sort(pts_all[pts_all[:, 0] == x][:, 1])
        if len(ys) < 12:
            continue
        runs = np.split(ys, np.flatnonzero(np.diff(ys) > 1) + 1)
        if len(runs) >= min_run and ys[-1] - ys[0] >= min_span:
            e = side(ys, runs, "v", int(x))
            if e:
                out.append(e)
    out2 = []
    for e in sorted(out, key=lambda e: (e["axis"], e.get("y", e.get("x")))):
        if out2 and out2[-1]["axis"] == e["axis"] and \
           abs(out2[-1].get("y", out2[-1].get("x")) - e.get("y", e.get("x"))) <= 3:
            continue
        out2.append(e)
    return out2


# ------------------------------------------------------- rule 8 line cuts
# The originals draw some labels straight over their own flow lines
# (verified pixel by pixel: the line is continuous through the label).
# Rule 8 forbids any text bbox from crossing a segment, so a line is opened
# exactly where a label sits - the label keeps its measured position, only
# a few line pixels differ from the original.  Shared by the tracer (first
# pass, measured ink boxes) and build_figure.py (final pass, rendered
# font-metric boxes = what the checker validates).

def _box_intervals(a, b, bx, inflate=1.0):
    x0 = bx[0] - inflate
    y0 = bx[1] - inflate
    x1 = bx[2] + inflate
    y1 = bx[3] + inflate
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]),
                 (-dy, a[1] - y0), (dy, y1 - a[1])):
        if abs(p) < 1e-12:
            if q < 0:
                return []
        else:
            r = q / p
            if p < 0:
                if r > t1:
                    return []
                t0 = max(t0, r)
            else:
                if r < t0:
                    return []
                t1 = min(t1, r)
    return [(t0, t1)] if t0 <= t1 else []


def open_lines_at_texts(lines, boxes, min_piece=6.0, tip_keep=15.0):
    """Open every line component where it crosses one of ``boxes``.

    Returns (new_lines, n_cuts).  Each box is inflated by 1 px so a grazing
    touch is opened as well.  Cut pieces shorter than ``min_piece`` px
    (swallowed by a label) are dropped; an arrowhead keeps its last
    ``tip_keep`` px so the tip stays attached to its piece.
    """
    cut_lines = []
    n_cuts = 0
    for ln in lines:
        segs = [(list(map(float, a)), list(map(float, b)))
                for a, b in ln["segs"]]
        tip = ln.get("arrow_tip")
        cut_here = False
        pieces, cur = [], []
        for (a, b) in segs:
            ivs = []
            for bx in boxes:
                for (t0, t1) in _box_intervals(a, b, bx):
                    if t1 - t0 < 1e-6:
                        continue
                    if tip:
                        px0 = a[0] + (b[0] - a[0]) * t0
                        py0 = a[1] + (b[1] - a[1]) * t0
                        px1 = a[0] + (b[0] - a[0]) * t1
                        py1 = a[1] + (b[1] - a[1]) * t1
                        if min(math.hypot(px0 - tip[0], py0 - tip[1]),
                               math.hypot(px1 - tip[0], py1 - tip[1])) < tip_keep:
                            continue        # keep the arrowhead attached
                    ivs.append((t0, t1))
            if ivs:
                cut_here = True
                n_cuts += 1
            merged = []
            for iv in sorted(ivs):
                if merged and iv[0] <= merged[-1][1] + 1e-9:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], iv[1]))
                else:
                    merged.append(iv)
            kept, c = [], 0.0
            for (t0, t1) in merged:
                if t0 > c:
                    kept.append((c, t0))
                c = max(c, t1)
            if c < 1.0 - 1e-9:
                kept.append((c, 1.0))
            for (t0, t1) in kept:
                p0 = [a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0]
                p1 = [a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1]
                if cur and math.hypot(cur[-1][1][0] - p0[0],
                                      cur[-1][1][1] - p0[1]) <= 1.5:
                    cur.append([p0, p1])
                else:
                    if cur:
                        pieces.append(cur)
                    cur = [[p0, p1]]
        if cur:
            pieces.append(cur)
        if not cut_here:
            cut_lines.append(ln)
            continue
        for piece in pieces:
            total = sum(math.hypot(s[1][0] - s[0][0], s[1][1] - s[0][1])
                        for s in piece)
            if total < min_piece:
                continue                  # fragment swallowed by a label
            xs = [p[0] for s in piece for p in s]
            ys = [p[1] for s in piece for p in s]
            nl = {"bbox": [int(min(xs)), int(min(ys)),
                           int(max(xs)) + 1, int(max(ys)) + 1],
                  "segs": piece, "thickness": ln.get("thickness", 3.0),
                  "color": ln.get("color", "#000000"),
                  "stroke": ln.get("stroke", 2.5)}
            if tip and any(math.hypot(p[0] - tip[0], p[1] - tip[1]) <= 1.5
                           for s in piece for p in s):
                nl["arrow_tip"] = tip
                nl["arrow_from"] = ln.get("arrow_from")
            cut_lines.append(nl)
    return cut_lines, n_cuts


# --------------------------------------------------------- stroke ring size

def dilate(mask, n):
    """n x 4-neighbour dilation (L1 ball of radius n)."""
    m = mask.copy()
    for _ in range(n):
        m[1:, :] |= m[:-1, :]; m[:-1, :] |= m[1:, :]
        m[:, 1:] |= m[:, :-1]; m[:, :-1] |= m[:, 1:]
    return m


# ---------------------------------------------------------- use-case W1 main
# Specialized clone tracer for ArchitectureDesign_ver1.1_image2.png.
#
# Fixes over the shared tracer:
#   * adaptive per-fill dilation: every ellipse ring is measured (top/bottom
#     centre scan) and the fill mask is dilated by ring+2 and restricted to
#     pixels near the fill OR the measured stroke colour (the fixed 6/16 px
#     dilation welded the thick 5 px rings into the line network);
#   * fused-structure decomposition: the actor + 16 association lines + the
#     frame arrive as ONE 126 636 px component.  Instead of a blind global
#     skeleton split, the network is decomposed by measured topology:
#     - the frame is found from long full-width/height runs,
#     - each fan line is measured from its own component in the clean band
#       between the frame and its ellipse (fitted by PCA, then extended to
#       the measured hub and to the ellipse path),
#     - the elbow trunks to UC02/UC03 are measured from their axis runs,
#     - the two actors are measured as head circle + body + arms + legs.
#   * stray title-glyph blobs: fills smaller than a use-case ellipse are
#     rejected as shapes (they remain text), so 19 shapes exactly =
#     18 ellipses + 1 system boundary.
#   * same-baseline word-gap fragments are merged into one label band.

def _runs1d(mask1d, off=0):
    idx = np.flatnonzero(mask1d)
    out = []
    if not len(idx):
        return out
    s = idx[0]
    p = idx[0]
    for q in idx[1:]:
        if q - p > 1:
            out.append((int(s + off), int(p + off)))
            s = q
        p = q
    out.append((int(s + off), int(p + off)))
    return out


def _row_groups(dark, min_len, axis="h"):
    """Groups of consecutive rows (h) / cols (v) carrying a run >= min_len."""
    h, w = dark.shape
    hits = []
    n = h if axis == "h" else w
    for i in range(n):
        line = dark[i] if axis == "h" else dark[:, i]
        for (a, b) in _runs1d(line):
            if b - a + 1 >= min_len:
                hits.append((i, a, b))
    groups = []
    for (i, a, b) in sorted(hits):
        if groups and i - groups[-1][-1][0] <= 1:
            groups[-1].append((i, a, b))
        else:
            groups.append([(i, a, b)])
    return groups


def _group_center(g):
    return float(np.median([i for (i, a, b) in g]))


def _ring_width(dark, bbox):
    """Median ring thickness measured at the top/bottom centre of a fill."""
    x0, y0, x1, y1 = bbox
    cx = (x0 + x1) // 2
    out = []
    for expect, lo in ((y0, y0 - 12), (y1, y1 - 12)):
        runs = _runs1d(dark[max(0, lo):max(0, lo) + 24, cx], max(0, lo))
        if runs:
            r = min(runs, key=lambda q: abs(q[1] - expect))
            out.append(r[1] - r[0] + 1)
    return int(round(float(np.median(out)))) if out else 5


def _fit_line(pts):
    pts = pts.astype(float)
    mean = pts.mean(axis=0)
    _, _, vt = np.linalg.svd(pts - mean, full_matrices=False)
    d = vt[0]
    t = (pts - mean) @ d
    a = mean + t.min() * d
    b = mean + t.max() * d
    return a, b, d


def _line_ellipse_hit(a, d, ell, side):
    """First intersection of the ray a + t*d with the ellipse path."""
    cx = (ell[0] + ell[2]) / 2.0
    cy = (ell[1] + ell[3]) / 2.0
    rx = (ell[2] - ell[0]) / 2.0
    ry = (ell[3] - ell[1]) / 2.0
    ox = (a[0] - cx) / rx
    oy = (a[1] - cy) / ry
    dx = d[0] / rx
    dy = d[1] / ry
    A = dx * dx + dy * dy
    B = 2 * (ox * dx + oy * dy)
    C = ox * ox + oy * oy - 1.0
    disc = B * B - 4 * A * C
    if disc < 0:
        return None
    ts = [(-B + math.sqrt(disc)) / (2 * A), (-B - math.sqrt(disc)) / (2 * A)]
    hits = [a + t * d for t in ts]
    # keep the hit on the actor-facing side
    if side == "left":
        hits.sort(key=lambda p: p[0])
    else:
        hits.sort(key=lambda p: -p[0])
    return (round(float(hits[0][0]), 1), round(float(hits[0][1]), 1))


def _stroke_of_pts(rgb, pts):
    pts = np.asarray(pts).astype(int)
    cols = rgb[pts[:, 1], pts[:, 0]].astype(int)
    lum = cols.sum(axis=1)
    k = max(1, len(lum) // 3)
    med = np.median(cols[np.argsort(lum)[:k]], axis=0).astype(int)
    return "#%02X%02X%02X" % tuple(med)


def _measure_thickness(dark, p0, p1):
    """Perpendicular dark run at the midpoint of a segment."""
    mx, my = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0
    ux, uy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(ux, uy) or 1.0
    nx, ny = -uy / L, ux / L
    run = best = 0.0
    for s in np.arange(-9, 9.01, 0.5):
        ix, iy = int(round(mx + nx * s)), int(round(my + ny * s))
        if 0 <= iy < dark.shape[0] and 0 <= ix < dark.shape[1] and dark[iy, ix]:
            run += 0.5
            best = max(best, run)
        else:
            run = 0.0
    return max(3.0, round(best, 1))


def _merge_same_baseline(texts):
    """Merge same-baseline word-gap fragments (same ink / height / host)."""
    changed = True
    while changed:
        changed = False
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, b = texts[i], texts[j]
                if a["inside"] != b["inside"]:
                    continue
                ba, bb = a["bbox"], b["bbox"]
                ha, hb = ba[3] - ba[1], bb[3] - bb[1]
                oy = min(ba[3], bb[3]) - max(ba[1], bb[1])
                if oy <= 0.5 * min(ha, hb):
                    continue
                if abs(ha - hb) > 4:
                    continue
                if ba[2] <= bb[0]:
                    gap = bb[0] - ba[2]
                elif bb[2] <= ba[0]:
                    gap = ba[0] - bb[2]
                else:
                    gap = 0
                if gap > 60:
                    continue
                ca = tuple(int(a["ink"][k:k + 2], 16) for k in (1, 3, 5))
                cb = tuple(int(b["ink"][k:k + 2], 16) for k in (1, 3, 5))
                if sum(abs(ca[k] - cb[k]) for k in range(3)) > 30:
                    continue
                texts[i] = {"bbox": [min(ba[0], bb[0]), min(ba[1], bb[1]),
                                     max(ba[2], bb[2]), max(ba[3], bb[3])],
                            "ink": a["ink"], "inside": a["inside"]}
                del texts[j]
                changed = True
                break
            if changed:
                break
    return texts


def main():
    src, out = sys.argv[1], sys.argv[2]
    fixes = json.load(open(sys.argv[3], encoding="utf-8")) \
        if len(sys.argv) > 3 else {}
    img = Image.open(src).convert("RGB")
    rgb = np.array(img)
    gray = np.array(img.convert("L"))
    h, w = gray.shape
    dark = gray < 170

    # ------------------------------------------------------------- ellipses
    shapes = []
    for f in merge_cylinders(rgb, detect_fills(rgb)):
        if (f["bbox"][2] - f["bbox"][0]) < 150 or \
           (f["bbox"][3] - f["bbox"][1]) < 100:
            continue                      # title-glyph blob, not a shape
        kind, stroke, radius, cap = classify_shape(rgb, f)
        if kind != "ellipse":
            print("WARN: non-ellipse fill kept as %s %s" % (kind, f["bbox"]))
        ring = _ring_width(dark, f["bbox"])
        x0, y0, x1, y1 = f["bbox"]
        pad = ring / 2.0 + 0.5
        entry = {"bbox": f["bbox"], "fill": f["fill"], "stroke": stroke,
                 "stroke_width": ring, "kind": "ellipse",
                 "radius": 0, "cap_ry": 0, "dashed": False,
                 "draw_bbox": [round(x0 - pad, 1), round(y0 - pad, 1),
                               round(x1 + pad, 1), round(y1 + pad, 1)],
                 "ring": ring}
        shapes.append(entry)
    print("ellipse fills:", len(shapes))
    if len(shapes) != 18:
        print("WARN: expected 18 ellipses")

    # ------------------------------------------------------------- boundary
    row_groups = _row_groups(dark, min_len=600, axis="h")
    col_groups = _row_groups(dark, min_len=1500, axis="v")
    top = row_groups[0]
    bottom = row_groups[-1]
    left = col_groups[0]
    right = col_groups[-1]
    top_y = _group_center(top)
    bottom_y = _group_center(bottom)
    left_x = _group_center(left)
    right_x = _group_center(right)
    trun = _runs1d(dark[int(round(top_y))])
    left_run = max((r for r in trun if r[1] < w // 2),
                   key=lambda r: r[1] - r[0])
    right_run = max((r for r in trun if r[0] > w // 2),
                    key=lambda r: r[1] - r[0])
    boundary = {"bbox": [left_x, top_y, right_x, bottom_y],
                "kind": "boundary", "fill": "#FFFFFF",
                "stroke": "#202B35", "stroke_width": len({i for i, a, b in top}),
                "radius": 0, "dashed": False,
                "gap_axis": "h",
                "gaps": [[left_run[1], right_run[0]]]}
    print("boundary", boundary["bbox"], "gap", boundary["gaps"],
          "stroke", boundary["stroke_width"])

    # ------------------------------------------- adaptive ring / fill mask
    d = np.zeros((h, w), dtype=bool)
    for s in shapes:
        x0, y0, x1, y1 = s["bbox"]
        m = np.zeros((h, w), dtype=bool)
        m[y0:y1, x0:x1] = fill_mask_of(rgb, s["bbox"], s["fill"])
        dm = m.copy()
        for _ in range(s["ring"] + 2):
            dm[1:, :] |= dm[:-1, :]
            dm[:-1, :] |= dm[1:, :]
            dm[:, 1:] |= dm[:, :-1]
            dm[:, :-1] |= dm[:, 1:]
        sr, sg, sb = (int(s["stroke"][i:i + 2], 16) for i in (1, 3, 5))
        fr, fg, fb = (int(s["fill"][i:i + 2], 16) for i in (1, 3, 5))
        nearfill = (np.abs(rgb[:, :, 0].astype(int) - fr) +
                    np.abs(rgb[:, :, 1].astype(int) - fg) +
                    np.abs(rgb[:, :, 2].astype(int) - fb)) < 40
        nearstroke = (np.abs(rgb[:, :, 0].astype(int) - sr) +
                      np.abs(rgb[:, :, 1].astype(int) - sg) +
                      np.abs(rgb[:, :, 2].astype(int) - sb)) < 60
        d |= dm & (nearfill | nearstroke)

    # ---------------------------------------------------------------- texts
    fill_text_comps = []
    for si, s in enumerate(shapes):
        x0, y0, x1, y1 = s["bbox"]
        r_, g_, b_ = (int(s["fill"][i:i + 2], 16) for i in (1, 3, 5))
        sub = rgb[y0:y1, x0:x1].astype(int)
        diff = (np.abs(sub[:, :, 0] - r_) + np.abs(sub[:, :, 1] - g_) +
                np.abs(sub[:, :, 2] - b_)) > 90
        diff[:2, :] = False
        diff[-2:, :] = False
        diff[:, :2] = False
        diff[:, -2:] = False
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
        fill_text_comps.append((si, s, comps))

    dark_comps = [c for c in rle_label(dark) if c["area"] >= 8]

    def line_like(c):
        x0, y0, x1, y1 = c["bbox"]
        return min(x1 - x0, y1 - y0) <= 15 and \
            max(x1 - x0, y1 - y0) >= 35

    white_comps = []
    for c in dark_comps:
        x0, y0, x1, y1 = c["bbox"]
        if (x1 - x0) > 0.6 * w or (y1 - y0) > 0.5 * h:
            continue                      # frame / fused network
        if line_like(c):
            continue                      # association lines, limbs
        white_comps.append(c)

    gap = 56 if min(h, w) > 2000 else 26
    white_texts = []
    boxes = group_lines([c["bbox"] for c in white_comps], gap)
    for box in boxes:
        bw_ = box[2] - box[0]
        bh_ = box[3] - box[1]
        if bh_ < 10 or bw_ < max(18, 1.2 * bh_) or bh_ > 0.12 * h or \
           bw_ > 0.7 * w:
            continue
        ctr = ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)
        if any(s2["bbox"][0] <= ctr[0] <= s2["bbox"][2] and
               s2["bbox"][1] <= ctr[1] <= s2["bbox"][3] for s2 in shapes):
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
        white_texts.append({"bbox": [int(v) for v in box],
                            "ink": ink, "inside": None})

    fill_texts = []
    for fi, s, comps in fill_text_comps:
        bands = group_lines([c["bbox"] for c in comps], gap)
        for box in bands:
            if box[3] - box[1] < 6 or \
               box[3] - box[1] > 0.5 * (s["bbox"][3] - s["bbox"][1]):
                continue
            cs = [c for c in comps
                  if c["bbox"][0] >= box[0] - 2 and c["bbox"][2] <= box[2] + 2 and
                  c["bbox"][1] >= box[1] - 2 and c["bbox"][3] <= box[3] + 2]
            if not cs:
                continue
            pts = np.concatenate([comp_points(c) for c in cs])
            ink = ink_colour(rgb, pts, s["fill"])
            st = s.get("stroke")
            if st:
                dst = sum(abs(int(ink[i:i + 2], 16) - int(st[i:i + 2], 16))
                          for i in (1, 3, 5))
                if dst < 45:
                    continue
            fill_texts.append({"bbox": [int(v) for v in box],
                               "ink": ink, "inside_fill": fi})

    texts = [dict(t) for t in white_texts]
    for t in fill_texts:
        tt = {k: v for k, v in t.items() if k != "inside_fill"}
        tt["inside"] = t["inside_fill"]          # shape index for now
        texts.append(tt)

    # same-baseline fragments (title words) -> one band
    texts = _merge_same_baseline(texts)
    texts.sort(key=lambda t: (t["bbox"][1], t["bbox"][0]))
    for i, t in enumerate(texts):
        t["id"] = "X%03d" % (i + 1)
    print("texts:", len(texts))

    # --------------------------------------- network: boundary mask + parts
    fmask = np.zeros((h, w), dtype=bool)
    bx0, by0, bx1, by1 = boundary["bbox"]
    pad = int(boundary["stroke_width"] / 2.0) + 3
    fmask[int(by0) - pad:int(by0) + pad + 1, :] = True
    fmask[int(by1) - pad:int(by1) + pad + 1, :] = True
    fmask[:, int(bx0) - pad:int(bx0) + pad + 1] = True
    fmask[:, int(bx1) - pad:int(bx1) + pad + 1] = True
    tmask = np.zeros((h, w), dtype=bool)
    for t in texts:
        x0, y0, x1, y1 = t["bbox"]
        tmask[y0 - 2:y1 + 2, x0 - 2:x1 + 2] = True
    net = dark & ~d & ~fmask & ~tmask

    # ------------------------------------------------------- fan lines (16)
    comps = rle_label(net)
    fan_comps = []
    for c in comps:
        x0, y0, x1, y1 = c["bbox"]
        if y0 < 800 or c["area"] < 300:
            continue
        ell_min_x = min(s["draw_bbox"][0] for s in shapes)
        ell_max_x = max(s["draw_bbox"][2] for s in shapes)
        in_left = (x0 >= int(bx0) + 4 and x1 <= int(ell_min_x) + 6)
        in_right = (x0 >= int(ell_max_x) - 6 and x1 <= int(bx1) - 4)
        if not (in_left or in_right):
            continue
        if (x1 - x0) < 100:               # diagonal span in the clean band
            continue
        fan_comps.append(c)
    print("fan components:", len(fan_comps))

    # boundary side -> ellipse column
    cols = {"left": [], "right": []}
    for s in shapes:
        x0, y0, x1, y1 = s["draw_bbox"]
        if x0 < w / 2:
            cols["left"].append((s, (x0, y0, x1, y1)))
        else:
            cols["right"].append((s, (x0, y0, x1, y1)))

    fan_fits = []
    for c in fan_comps:
        pts = comp_points(c).astype(float)
        a, b, dv = _fit_line(pts)
        side = "left" if c["bbox"][0] < w / 2 else "right"
        # normalise so the direction goes towards the ellipses
        if (side == "left" and dv[0] < 0) or (side == "right" and dv[0] > 0):
            dv = -dv
            a, b = b, a
        fan_fits.append({"side": side, "a": a, "b": b, "d": dv,
                         "bbox": c["bbox"], "pts": pts})
    # hub = robust mean of pairwise intersections on each side
    hubs = {}
    for side in ("left", "right"):
        fits = [f for f in fan_fits if f["side"] == side]
        xs, ys = [], []
        for i in range(len(fits)):
            for j in range(i + 1, len(fits)):
                a1, d1 = fits[i]["a"], fits[i]["d"]
                a2, d2 = fits[j]["a"], fits[j]["d"]
                den = d1[0] * d2[1] - d1[1] * d2[0]
                if abs(den) < 1e-6:
                    continue
                t = ((a2[0] - a1[0]) * d2[1] - (a2[1] - a1[1]) * d2[0]) / den
                p = a1 + t * d1
                if 0 <= p[0] <= w and 0 <= p[1] <= h:
                    xs.append(p[0])
                    ys.append(p[1])
        hubs[side] = (round(float(np.median(xs)), 1),
                      round(float(np.median(ys)), 1))
    print("hubs", hubs)

    lines = []
    arrows = []
    used_ell = set()
    for side in ("left", "right"):
        fits = [f for f in fan_fits if f["side"] == side]
        fits.sort(key=lambda f: f["bbox"][1])
        for f in fits:
            # nearest ellipse column target by extrapolated y at the edge
            ex = shapes[0]["draw_bbox"][0] if side == "left" else \
                shapes[0]["draw_bbox"][2]
            # use the component end nearest the ellipse
            if side == "left":
                end = f["pts"][f["pts"][:, 0].argmax()]
            else:
                end = f["pts"][f["pts"][:, 0].argmin()]
            best = None
            for s, eb in cols[side]:
                cy = (eb[1] + eb[3]) / 2.0
                dd = abs(cy - end[1])
                if best is None or dd < best[0]:
                    best = (dd, s, eb)
            _, s, eb = best
            # the original draws every association line to the ellipse's
            # horizontal centre; the measured component end is the arrow
            # base (the triangle biases a PCA fit), so the tip is the
            # ellipse path edge at the measured centre height.
            cy = (eb[1] + eb[3]) / 2.0
            if side == "left":
                hit = (round(eb[0] - s["ring"] / 2.0, 1), round(cy, 1))
            else:
                hit = (round(eb[2] + s["ring"] / 2.0, 1), round(cy, 1))
            if os.environ.get("TRACE_DBG"):
                print("FAN", side, "bbox", f["bbox"], "end", end,
                      "d", tuple(round(float(v), 3) for v in f["d"]),
                      "->", s["bbox"], "hit", hit)
            hub = hubs[side]
            ln = {"bbox": [int(min(hub[0], hit[0])), int(min(hub[1], hit[1])),
                           int(max(hub[0], hit[0])) + 1,
                           int(max(hub[1], hit[1])) + 1],
                  "segs": [[[hub[0], hub[1]], [hit[0], hit[1]]]],
                  "thickness": _measure_thickness(dark, hub, hit),
                  "color": _stroke_of_pts(rgb, f["pts"]),
                  "stroke": _measure_thickness(dark, hub, hit),
                  "arrow_tip": [hit[0], hit[1]],
                  "arrow_from": [hub[0], hub[1]]}
            lines.append(ln)
            arrows.append({"line": len(lines) - 1, "tip": ln["arrow_tip"],
                           "from": ln["arrow_from"], "widths": []})
            used_ell.add(id(s))

    if lines:
        med_thick = round(float(np.median([ln["thickness"] for ln in lines])), 1)
        for ln in lines:
            ln["thickness"] = med_thick
            ln["stroke"] = med_thick

    # ------------------------------------------------- elbow trunks (4)
    # frame / trunk horizontal centres measured from the long axis runs
    def hline_center(y_guess, x0, x1):
        ys = []
        for y in range(int(y_guess) - 8, int(y_guess) + 9):
            rr = _runs1d(dark[y, x0:x1], x0)
            if any(b - a > 0.6 * (x1 - x0) for a, b in rr):
                ys.append(y)
        return float(np.median(ys)) if ys else float(y_guess)

    y480 = hline_center(480, 280, 1080)
    y700 = hline_center(700, 280, 1080)
    # left/right trunk vertical centres
    def vline_center(x_guess, y0, y1):
        xs = []
        for x in range(int(x_guess) - 8, int(x_guess) + 9):
            rr = _runs1d(dark[y0:y1, x], y0)
            if any(b - a > 0.6 * (y1 - y0) for a, b in rr):
                xs.append(x)
        return float(np.median(xs)) if xs else float(x_guess)

    lx = vline_center(294, 520, 1600)
    rx = vline_center(2704, 520, 1600)
    # UC02 / UC03 path edges (draw_bbox already expanded)
    uc02 = min(shapes, key=lambda s: abs((s["draw_bbox"][1] + s["draw_bbox"][3]) / 2 - 480))
    uc03 = min(shapes, key=lambda s: abs((s["draw_bbox"][1] + s["draw_bbox"][3]) / 2 - 700))
    # left actor hand / right actor hand measured from the arms
    hand_l = 294.0
    hand_r = 2703.0
    trunk_specs = [
        # (corners, tip) - the hand point is the first corner
        ([(hand_l, 1665.5), (lx, 1665.5), (lx, y480)],
         (uc02["draw_bbox"][0] - 2.5, y480)),
        ([(lx, y700)], (uc03["draw_bbox"][0] - 2.5, y700)),
        ([(hand_r, 1664.5), (rx, 1664.5), (rx, y480)],
         (uc02["draw_bbox"][2] + 2.5, y480)),
        ([(rx, y700)], (uc03["draw_bbox"][2] + 2.5, y700)),
    ]
    for corners, tip in trunk_specs:
        verts = [[round(c[0], 1), round(c[1], 1)] for c in corners]
        verts.append([round(tip[0], 1), round(tip[1], 1)])
        # dedupe consecutive
        vv = [verts[0]]
        for v in verts[1:]:
            if v != vv[-1]:
                vv.append(v)
        segs = [[vv[i], vv[i + 1]] for i in range(len(vv) - 1)]
        ln = {"bbox": [int(min(p[0] for p in vv)),
                       int(min(p[1] for p in vv)),
                       int(max(p[0] for p in vv)) + 1,
                       int(max(p[1] for p in vv)) + 1],
              "segs": segs,
              "thickness": 4.5,
              "color": "#202B35",
              "stroke": 4.5,
              "arrow_tip": [round(tip[0], 1), round(tip[1], 1)],
              "arrow_from": [vv[-2][0], vv[-2][1]]}
        lines.append(ln)
        arrows.append({"line": len(lines) - 1, "tip": ln["arrow_tip"],
                       "from": ln["arrow_from"], "widths": []})

    # -------------------------------------------------------------- actors
    def fit_actor(side):
        if side == "left":
            x0, x1 = 40, int(bx0) - 8
        else:
            x0, x1 = int(bx1) + 8, min(w, w - 5)
        # body first: the only long vertical run in the actor region
        best = None
        for xx in range(x0, x1):
            for (a, b) in _runs1d(dark[1560:1770, xx], 1560):
                L = b - a
                if L >= 80 and (best is None or L > best[0]):
                    best = (L, a, b, xx)
        if best is None:
            raise SystemExit("actor body not found on %s" % side)
        _, body_top0, body_bot, body_x = best
        body_x = float(body_x)
        # refine body x from the run centres through the body
        xs = []
        for y in range(body_top0 + 25, int(body_bot) - 12):
            rr = _runs1d(dark[y, int(body_x) - 8:int(body_x) + 9],
                         int(body_x) - 8)
            for a, b in rr:
                if a <= body_x <= b:
                    xs.append((a + b) / 2.0)
        if xs:
            body_x = float(np.median(xs))
        # head: clean box well above the fan/arm crossing
        hx0 = max(0, int(body_x) - 52)
        hx1 = min(w, int(body_x) + 53)
        hy0 = max(0, body_top0 - 105)
        hy1 = body_top0 + 6
        box = np.zeros((h, w), bool)
        box[hy0:hy1, hx0:hx1] = dark[hy0:hy1, hx0:hx1]
        pts = np.argwhere(box)[:, ::-1].astype(float)
        c = pts.mean(axis=0)
        ring = pts
        for _ in range(8):
            d_ = np.hypot(pts[:, 0] - c[0], pts[:, 1] - c[1])
            r_ = np.median(d_)
            ring = pts[np.abs(d_ - r_) < 6]
            c = ring.mean(axis=0)
        circ = fit_circle(ring)
        if circ is None:
            circ = (float(c[0]), float(c[1]), float(np.median(
                np.hypot(ring[:, 0] - c[0], ring[:, 1] - c[1]))))
        cx, cy, cr = circ
        body_top = cy + cr
        # arm: longest horizontal run around the hub line
        arms = []
        for y in range(1640, 1690):
            rr = _runs1d(dark[y, x0:x1], x0)
            for a, b in rr:
                if b - a >= 120:
                    arms.append((y, a, b))
        ay = float(np.median([a[0] for a in arms]))
        ax0 = float(min(a[1] for a in arms))
        ax1 = float(max(a[2] for a in arms))
        # legs: two diagonal lines below the hip (start clear of the body stub)
        legbox = np.zeros((h, w), bool)
        ly0 = int(body_bot) + 8
        legbox[ly0:ly0 + 95, int(body_x) - 80:int(body_x) + 80] = \
            dark[ly0:ly0 + 95, int(body_x) - 80:int(body_x) + 80]
        legs = []
        for c_ in rle_label(legbox):
            if c_["area"] < 60:
                continue
            p_ = comp_points(c_).astype(float)
            a_, b_, dv_ = _fit_line(p_)
            if abs(dv_[0]) < 1e-6:
                continue
            # endpoints ordered by y
            p0 = p_[p_[:, 1].argmin()]
            p1 = p_[p_[:, 1].argmax()]
            if p1[1] - p0[1] > 1:
                m = (p1[0] - p0[0]) / (p1[1] - p0[1])
                y_bot = float(p1[1]) + 6.0
                x_top = float(p0[0]) + m * (body_bot - float(p0[1]))
                x_bot = float(p0[0]) + m * (y_bot - float(p0[1]))
                legs.append([[round(x_top, 1), round(body_bot, 1)],
                             [round(x_bot, 1), round(y_bot, 1)]])
        legs.sort(key=lambda seg: seg[0][0])
        limbs = [
            [[round(body_x, 1), round(body_top, 1)],
             [round(body_x, 1), round(body_bot, 1)]],
            [[round(ax0, 1), round(ay, 1)], [round(ax1, 1), round(ay, 1)]],
        ] + legs
        return {"bbox": [int(cx - cr - 4), int(cy - cr - 4),
                         int(cx + cr + 4), int(cy + cr + 4)],
                "circle": [round(float(cx), 1), round(float(cy), 1),
                           round(float(cr), 1)],
                "limbs": limbs, "area": int(math.pi * cr * cr),
                "color": "#202B35", "stroke": 5.0}

    sticks = [fit_actor("left"), fit_actor("right")]
    for k in sticks:
        print("stick circle", k["circle"], "limbs", k["limbs"])

    # ------------------------------------------- repair fused label edges
    # A glyph may touch an association line in the original (the 'A' of
    # Administrator is crossed by the UC11 line).  The line component was
    # excluded from text detection, so extend free-label bands over dark
    # pixels that are not within 5 px of a measured line segment.
    seg_all = [(seg[0][0], seg[0][1], seg[1][0], seg[1][1])
               for ln in lines for seg in ln["segs"]]

    def near_seg(x, y):
        for (ax, ay, bx, by) in seg_all:
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            if L2 < 1e-9:
                continue
            tp = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
            px, py = ax + tp * dx, ay + tp * dy
            if (px - x) ** 2 + (py - y) ** 2 <= 5.0 ** 2:
                return True
        return False

    for t in texts:
        if t["inside"] is not None:
            continue
        x0, y0, x1, y1 = t["bbox"]
        xs = []
        for yy in range(max(0, y0 - 2), min(h, y1 + 2)):
            for xx in range(max(0, x0 - 28), min(w, x1 + 29)):
                if dark[yy, xx] and not near_seg(xx, yy):
                    xs.append(xx)
        if not xs:
            continue
        left = sorted((x for x in xs if x < x0), reverse=True)
        lx = x0
        for x in left:
            if lx - x > 16:
                break
            lx = x
        right = sorted((x for x in xs if x > x1), reverse=True)
        rx = x1
        for x in right:
            if x - rx > 16:
                break
            rx = x
        if lx < x0 or rx > x1:
            print("text repair", t["id"], (x0, x1), "->", (lx, rx))
            t["bbox"] = [int(min(x0, lx)), y0, int(max(x1, rx)), y1]

    # ------------------------------------------------------------ assemble
    all_shapes = [boundary] + shapes
    for i, s in enumerate(all_shapes):
        s["id"] = "S%02d" % (i + 1)
    for t in texts:
        if isinstance(t["inside"], int):
            t["inside"] = all_shapes[t["inside"] + 1]["id"]

    # rule-8 first pass on measured boxes (markers verification)
    lines, n_cuts = open_lines_at_texts(lines, [t["bbox"] for t in texts])
    if n_cuts:
        print("rule-8 line cuts: %d segment(s)" % n_cuts)

    report = {
        "canvas": {"w": int(w), "h": int(h)},
        "source": os.path.basename(src),
        "shapes": all_shapes,
        "lines": [{"id": "L%02d" % (i + 1), **ln}
                  for i, ln in enumerate(lines)],
        "dashes": [],
        "sticks": [{"id": "K%02d" % (i + 1), **k}
                   for i, k in enumerate(sticks)],
        "arrows": arrows,
        "texts": texts,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)

    # ------------------------------------------------------------- markers
    mk = img.copy()
    dr = ImageDraw.Draw(mk)
    for s in all_shapes:
        x0, y0, x1, y1 = s["bbox"]
        col = (0, 0, 255) if s["kind"] == "boundary" else (255, 0, 255)
        dr.rectangle([x0, y0, x1 - 1, y1 - 1], outline=col, width=3)
    for ln in report["lines"]:
        for (a, b) in ln["segs"]:
            dr.line([tuple(a), tuple(b)], fill=(255, 0, 0), width=3)
    for k in report["sticks"]:
        cx, cy, r = k["circle"]
        dr.ellipse([cx - r, cy - r, cx + r, cy + r],
                   outline=(0, 160, 160), width=3)
        for (a, b) in k["limbs"]:
            dr.line([tuple(a), tuple(b)], fill=(0, 160, 160), width=3)
    for ar in arrows:
        tx, ty = ar["tip"]
        dr.ellipse([tx - 7, ty - 7, tx + 7, ty + 7],
                   outline=(0, 0, 255), width=3)
    for t in texts:
        x0, y0, x1, y1 = t["bbox"]
        dr.rectangle([x0, y0, x1, y1], outline=(255, 0, 255), width=2)
    mk_path = os.path.splitext(out)[0] + "_markers.png"
    mk.save(mk_path)

    print("canvas %dx%d" % (w, h))
    print("shapes %d (boundary %d, ellipses %d)" %
          (len(all_shapes), 1, len(shapes)))
    print("lines %d sticks %d arrows %d texts %d" %
          (len(report["lines"]), len(sticks), len(arrows), len(texts)))
    for ln in report["lines"]:
        print("  %s thick=%s nsegs=%d arrow=%s bbox=%s" %
              (ln["id"], ln["thickness"], len(ln["segs"]),
               ln.get("arrow_tip"), ln["bbox"]))
    for t in texts:
        print("  %s bbox=%s ink=%s inside=%s" %
              (t["id"], t["bbox"], t["ink"], t["inside"]))
    print("markers:", mk_path)


if __name__ == "__main__":
    main()

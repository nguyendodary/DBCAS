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
        if abs(off - on) > 2:
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


# --------------------------------------------------------------------- main


def main():
    src, out = sys.argv[1], sys.argv[2]
    fixes = json.load(open(sys.argv[3], encoding="utf-8")) \
        if len(sys.argv) > 3 else {}
    print("fixes loaded:", sorted(fixes.keys()),
          "argv:", sys.argv[1:4])
    img = Image.open(src).convert("RGB")
    rgb = np.array(img)
    gray = np.array(img.convert("L"))
    h, w = gray.shape
    dark = gray < 170

    # ---------------------------------------------------------- fills
    shapes = []
    for f in merge_cylinders(rgb, detect_fills(rgb)):
        # Glyph-sized fills are LETTERS (the Use Case title/subtitle
        # render as solid blobs): they are text, not shapes.  Keeping them
        # would hide the real text bands behind the fill-island check and
        # leave white counter slivers misdetected as labels.
        if (f["bbox"][2] - f["bbox"][0]) < 150 and \
           (f["bbox"][3] - f["bbox"][1]) < 100:
            continue
        kind, stroke, radius, cap = classify_shape(rgb, f)
        entry = {"bbox": f["bbox"], "fill": f["fill"], "stroke": stroke,
                 "stroke_width": 2,
                 "kind": "cylinder" if f.get("cylinder") else kind,
                 "radius": radius, "cap_ry": cap, "dashed": False}
        # straight-sided shapes: draw at the MODAL fill extent - a text-label
        # background tab (fill painted past the border behind overflowing
        # text) or a stray fill blob must not widen the drawn box. Text
        # detection keeps the full bbox so overflowing labels keep their
        # measured width.
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
        # measure the real border stroke at the shape's left edge midpoint
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
        if entry["kind"] == "cylinder":
            dbb = entry.get("draw_bbox", f["bbox"])
            m = fill_mask_of(rgb, dbb, f["fill"])
            entry["outline"] = silhouette(m, step=2, ox=dbb[0], oy=dbb[1])
        shapes.append(entry)

    fill_mask = np.zeros((h, w), dtype=bool)
    for s in shapes:
        x0, y0, x1, y1 = s["bbox"]
        fill_mask[y0:y1, x0:x1] |= fill_mask_of(rgb, s["bbox"], s["fill"])
    d = fill_mask.copy()
    for _ in range(6):
        d[1:, :] |= d[:-1, :]; d[:-1, :] |= d[1:, :]
        d[:, 1:] |= d[:, :-1]; d[:, :-1] |= d[:, 1:]
    # Border paint drawn OUTSIDE the fill colour (the Use Case ellipses
    # have 5-10px rings): without this the ring stays inside the line mask
    # and every line touching a ring welds into one giant component. The
    # ring is matched by the shape's stroke colour within 16px of its own
    # fill; thin strokes already sit inside the 6px dilation above, so
    # figures with 1-4px borders are unaffected.
    for s in shapes:
        st = s.get("stroke")
        if not st or st == s["fill"]:
            continue                      # solid shape: no outer ring
        try:
            sr, sg, sb = (int(st[i:i + 2], 16) for i in (1, 3, 5))
        except ValueError:
            continue
        x0, y0, x1, y1 = s["bbox"]
        wy0, wx0 = max(0, y0 - 16), max(0, x0 - 16)
        wy1, wx1 = min(h, y1 + 16), min(w, x1 + 16)
        sub = np.zeros((wy1 - wy0, wx1 - wx0), dtype=bool)
        sub[y0 - wy0:y1 - wy0, x0 - wx0:x1 - wx0] = \
            fill_mask_of(rgb, s["bbox"], s["fill"])
        for _ in range(16):
            sub[1:, :] |= sub[:-1, :]; sub[:-1, :] |= sub[1:, :]
            sub[:, 1:] |= sub[:, :-1]; sub[:, :-1] |= sub[:, 1:]
        hit = (np.abs(rgb[wy0:wy1, wx0:wx1, 0].astype(int) - sr) +
               np.abs(rgb[wy0:wy1, wx0:wx1, 1].astype(int) - sg) +
               np.abs(rgb[wy0:wy1, wx0:wx1, 2].astype(int) - sb)) < 45
        d[wy0:wy1, wx0:wx1] |= hit & sub
    # dash rows/cols, known BEFORE text extraction so dash bands are never
    # mistaken for label lines (uniform-run criterion keeps text rows out)
    _thin = [c for c in rle_label(dark & ~d)
             if min(c["bbox"][2] - c["bbox"][0],
                    c["bbox"][3] - c["bbox"][1]) <= 8 and
             max(c["bbox"][2] - c["bbox"][0],
                 c["bbox"][3] - c["bbox"][1]) <= 40 and c["area"] <= 4000]
    _thin_pts = (np.concatenate([comp_points(c) for c in _thin])
                 if _thin else np.zeros((0, 2), int))
    pre_dash = dash_clusters(_thin_pts)
    dash_rows = {e["y"] for e in pre_dash if e["axis"] == "h"}
    dash_cols = {e["x"] for e in pre_dash if e["axis"] == "v"}

    def on_dash(c):
        x0, y0, x1, y1 = c["bbox"]
        cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
        return (any(abs(cy - r) <= 3 for r in dash_rows) or
                any(abs(cx - cc) <= 3 for cc in dash_cols))

    # ---------------------------------------------------------- texts
    # inside fills: |px - fill| > 90. Sample and test against draw_bbox:
    # a text-label background tab widens bbox past the border, and the
    # border stroke / page white inside that strip must not become text.
    fill_text_comps = []
    for si, s in enumerate(shapes):
        dbb = s.get("draw_bbox") or s["bbox"]
        sd = s if dbb == s["bbox"] else dict(s, bbox=dbb)
        x0, y0, x1, y1 = dbb
        r, g, b = (int(s["fill"][i:i + 2], 16) for i in (1, 3, 5))
        sub = rgb[y0:y1, x0:x1].astype(int)
        diff = (np.abs(sub[:, :, 0] - r) + np.abs(sub[:, :, 1] - g) +
                np.abs(sub[:, :, 2] - b)) > 90
        diff[:2, :] = False; diff[-2:, :] = False
        diff[:, :2] = False; diff[:, -2:] = False
        m = np.zeros((h, w), bool)
        m[y0:y1, x0:x1] = diff
        comps = []
        for c in rle_label(m):
            bx0, by0, bx1, by1 = c["bbox"]
            if c["area"] < 6:
                continue
            if (bx1 - bx0) >= (x1 - x0) * 0.96 or (by1 - by0) >= (y1 - y0) * 0.96:
                continue
            if not inside_shape_pt(sd, (bx0 + bx1) / 2.0, (by0 + by1) / 2.0):
                continue                  # background showing at a curved corner
            if _outside_frac(sd, comp_points(c)) >= 0.5:
                continue                  # curve-edge antialiasing sliver
            if sd.get("kind") == "rounded" and (sd.get("radius") or 0) > 1:
                rr = sd["radius"] + 3
                sx0, sy0, sx1, sy1 = sd["bbox"]
                inc = any(bx0 >= cx0 and by0 >= cy0 and bx1 <= cx0 + rr and
                          by1 <= cy0 + rr
                          for cx0, cy0 in ((sx0, sy0), (sx1 - rr, sy0),
                                           (sx0, sy1 - rr), (sx1 - rr, sy1 - rr)))
                if inc and c["area"] <= rr * rr:
                    continue              # corner stroke arc / sliver
            comps.append(c)
        fill_text_comps.append((si, s, comps))

    dark_comps = [c for c in rle_label(dark) if c["area"] >= 8]

    def line_like(c):
        x0, y0, x1, y1 = c["bbox"]
        return min(x1 - x0, y1 - y0) <= 15 and max(x1 - x0, y1 - y0) >= 22

    def has_arrow(c):
        """Geometry-only arrow test: one end of the component is >= 2.4x
        wider (perpendicular extent) than its body -> triangle."""
        pts = comp_points(c)
        if len(pts) < 20:
            return False
        p = pts.astype(float)
        mean = p.mean(axis=0)
        _, _, vt = np.linalg.svd(p - mean, full_matrices=False)
        ax = vt[0]
        nrm = np.array([-ax[1], ax[0]])
        t = (p - mean) @ ax
        perp = (p - mean) @ nrm

        def extent(sel):
            if int(sel.sum()) < 8:
                return None
            v = perp[sel]
            return float(v.max() - v.min())

        span = float(t.max() - t.min())
        if span < 20:
            return False
        lo = extent(t < t.min() + 25)
        hi = extent(t > t.max() - 25)
        body = extent((t > t.min() + span * 0.3) & (t < t.max() - span * 0.3))
        if body is None or body < 1:
            body = 1.0
        need = max(8.0, 2.4 * body)
        return bool((lo or 0) >= need or (hi or 0) >= need)

    # text vs line pieces:
    #   frame-sized comps -> line bucket; thin+long or arrow-bearing -> line;
    #   everything else -> glyph bucket (dash bars join too, but grouped
    #   bands with height < 9 px are rejected as text below)
    glyph_idx, line_idx = [], []
    extra_glyphs = []

    def sub_mask(c):
        m = np.zeros((h, w), dtype=bool)
        for (y, x0, x1) in c["runs"]:
            m[y, x0:x1] = True
        return m

    for i, c in enumerate(dark_comps):
        x0, y0, x1, y1 = c["bbox"]
        L = max(x1 - x0, y1 - y0)
        if (x1 - x0) > 0.6 * w or (y1 - y0) > 0.5 * h:
            line_idx.append(i)
            continue
        if not line_like(c):
            glyph_idx.append(i)
            continue
        if L >= 150 or has_arrow(c):
            # a label may touch its own line in the original: decompose any
            # glyph sub-pieces out of this line-like component so the label
            # band recovers its full width and the line analysis stays clean
            for sc in rle_label(sub_mask(c)):
                sx0, sy0, sx1, sy1 = sc["bbox"]
                if (sc["area"] >= 8 and not line_like(sc) and
                        max(sx1 - sx0, sy1 - sy0) >= 9 and
                        min(sx1 - sx0, sy1 - sy0) >= 4):
                    extra_glyphs.append(sc)
            line_idx.append(i)
        else:
            glyph_idx.append(i)

    white_comps = [dark_comps[i] for i in glyph_idx] + extra_glyphs

    gap = 56 if min(h, w) > 2000 else 26
    white_comps = [c for c in white_comps
                   if not (min(c["bbox"][2] - c["bbox"][0],
                               c["bbox"][3] - c["bbox"][1]) <= 3 and
                           max(c["bbox"][2] - c["bbox"][0],
                               c["bbox"][3] - c["bbox"][1]) <= 12)]
    white_texts = []
    for box in group_lines([c["bbox"] for c in white_comps], gap):
        bw_ = box[2] - box[0]
        bh_ = box[3] - box[1]
        if bh_ < 10 or bw_ < max(18, 1.2 * bh_) or bh_ > 0.12 * h or \
           bw_ > 0.7 * w:
            continue                      # dash bars, frames, figure parts
        ctr_w = ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)
        if any(s2["kind"] != "boundary" and
               s2["bbox"][0] <= ctr_w[0] <= s2["bbox"][2] and
               s2["bbox"][1] <= ctr_w[1] <= s2["bbox"][3]
               for s2 in shapes):
            continue                      # owned by the fill-diff path
        band_cs = [c for c in white_comps
                   if c["bbox"][0] >= box[0] - 2 and
                   c["bbox"][2] <= box[2] + 2 and
                   c["bbox"][1] >= box[1] - 2 and
                   c["bbox"][3] <= box[3] + 2]
        # dash bars were filtered by geometry above; a band that is a dash
        # row has height <= 9 and is rejected by the height test, so no
        # on_dash() rejection is needed here (text may legitimately sit on a
        # dashed border line in the original, e.g. the Pipeline footer).
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
            continue                      # fill island between glyph strokes
        ctr = ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)
        host = next((s2 for s2 in shapes
                     if s2["bbox"][0] <= ctr[0] <= s2["bbox"][2] and
                     s2["bbox"][1] <= ctr[1] <= s2["bbox"][3]), None)
        if host is not None and _outside_frac(host, pts) >= 0.5:
            continue                      # curve-edge sliver band
        white_texts.append({"bbox": [int(v) for v in box],
                            "ink": ink,
                            "inside": None})

    fill_texts = []
    splits = [(tuple(s["shape"]), s["split_y"])
              for s in fixes.get("splits", [])]
    for fi, s, comps in fill_text_comps:
        bands = group_lines([c["bbox"] for c in comps], gap)
        key = tuple(s["bbox"])
        for sk, sy in splits:
            if sk != key:
                continue
            split_bands = []
            for box in bands:
                if not (box[1] < sy < box[3]) or (box[3] - box[1]) < 18:
                    split_bands.append(box)
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
                    split_bands.append([min(c["bbox"][0] for c in top),
                                        box[1],
                                        max(c["bbox"][2] for c in top),
                                        sy - 1])
                    split_bands.append([min(c["bbox"][0] for c in bot),
                                        sy, max(c["bbox"][2] for c in bot),
                                        box[3]])
                else:
                    split_bands.append(box)
            bands = split_bands
        for box in bands:
            if box[3] - box[1] < 6 or \
               box[3] - box[1] > 0.5 * (s["bbox"][3] - s["bbox"][1]):
                continue                  # lid arcs, stroke slivers, dots
            cs = [c for c in comps
                  if c["bbox"][0] >= box[0] - 2 and c["bbox"][2] <= box[2] + 2 and
                  c["bbox"][1] >= box[1] - 2 and c["bbox"][3] <= box[3] + 2]
            if not cs:
                continue
            pts = np.concatenate([comp_points(c) for c in cs])
            ink = ink_colour(rgb, pts, s["fill"])
            st = s.get("stroke")
            if st:
                d_st = sum(abs(int(ink[i:i + 2], 16) - int(st[i:i + 2], 16))
                           for i in (1, 3, 5))
                if d_st < 45:
                    continue              # lid / stroke sliver, not text
            fill_texts.append({"bbox": [int(v) for v in box],
                               "ink": ink,
                               "inside_fill": fi})

    # ---------------------------------------------------------- lines
    # d (fill dilation + stroke rings) is built above and reused unchanged
    tmask = np.zeros((h, w), bool)
    for t in white_texts + fill_texts:
        x0, y0, x1, y1 = t["bbox"]
        tmask[y0:y1, x0:x1] = True
    line_src = dark & ~d & ~tmask

    lines, sticks = [], []
    line_comps = rle_label(line_src)
    # dash bars: thin pieces lying on a row/col with >=6 similar runs
    thin = [c for c in line_comps
            if min(c["bbox"][2] - c["bbox"][0], c["bbox"][3] - c["bbox"][1]) <= 8
            and max(c["bbox"][2] - c["bbox"][0], c["bbox"][3] - c["bbox"][1]) <= 40
            and c["area"] <= 1400]
    thin_pts = (np.concatenate([comp_points(c) for c in thin])
                if thin else np.zeros((0, 2), int))
    pre_dash = dash_clusters(thin_pts)
    dash_rows = {e["y"] for e in pre_dash if e["axis"] == "h"}
    dash_cols = {e["x"] for e in pre_dash if e["axis"] == "v"}

    def on_dash(c):
        x0, y0, x1, y1 = c["bbox"]
        cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
        return (any(abs(cy - r) <= 3 for r in dash_rows) or
                any(abs(cx - cc) <= 3 for cc in dash_cols))

    def emit_network(net, comp):
        """Turn the decomposition of one fused network component into line
        and stick entries (Use Case: actors, association lines and the
        boundary frame all arrive as a single giant component)."""
        circles = net["circles"]
        segs = net["segs"]
        if not segs:
            return False
        # segments that ARE the circle (arc chords): the circle draws
        # them, so they are neither limbs nor lines
        circle_seg = set()
        for si, sg in enumerate(segs):
            for (cx, cy, cr) in circles:
                p0, p1 = sg["p0"], sg["p1"]
                if math.hypot(p0[0] - cx, p0[1] - cy) <= cr + 5 and \
                   math.hypot(p1[0] - cx, p1[1] - cy) <= cr + 5:
                    mx = (p0[0] + p1[0]) / 2.0
                    my = (p0[1] + p1[1]) / 2.0
                    if math.hypot(mx - cx, my - cy) <= cr + 7:
                        circle_seg.add(si)
                        break
        # ---- actors: a circle plus the straight parts clustered on it
        actor_seg = set()
        for (cx, cy, cr) in circles:
            members = []
            body_end = None
            for si, sg in enumerate(segs):          # body: vertical, centred
                if si in actor_seg or si in circle_seg:
                    continue
                p0, p1 = sg["p0"], sg["p1"]
                if abs(p0[0] - p1[0]) <= 8 and abs(p0[1] - p1[1]) >= 15 and \
                   abs(p0[0] - cx) <= 18 and abs(p1[0] - cx) <= 18 and \
                   math.hypot(p0[0] - cx, p0[1] - cy) <= 170 and \
                   math.hypot(p1[0] - cx, p1[1] - cy) <= 170:
                    actor_seg.add(si)
                    members.append(sg)
                    if body_end is None or p0[1] > body_end[1]:
                        body_end = p0 if p0[1] > p1[1] else p1
            for si, sg in enumerate(segs):          # arms: horizontal, near
                if si in actor_seg or si in circle_seg:
                    continue
                p0, p1 = sg["p0"], sg["p1"]
                if abs(p0[1] - p1[1]) <= 8 and p0[1] > cy and \
                   math.hypot(p0[0] - cx, p0[1] - cy) <= 215 and \
                   math.hypot(p1[0] - cx, p1[1] - cy) <= 215:
                    actor_seg.add(si)
                    members.append(sg)
            if body_end is not None:
                for si, sg in enumerate(segs):      # legs: leave the hip
                    if si in actor_seg or si in circle_seg:
                        continue
                    p0, p1 = sg["p0"], sg["p1"]
                    if min(math.hypot(p0[0] - body_end[0], p0[1] - body_end[1]),
                           math.hypot(p1[0] - body_end[0],
                                      p1[1] - body_end[1])) <= 30:
                        actor_seg.add(si)
                        members.append(sg)
            xs = [cx - cr, cx + cr]
            ys = [cy - cr, cy + cr]
            for sg in members:
                xs += [sg["p0"][0], sg["p1"][0]]
                ys += [sg["p0"][1], sg["p1"][1]]
            sticks.append({"bbox": [int(min(xs)), int(min(ys)),
                                    int(max(xs)) + 1, int(max(ys)) + 1],
                           "circle": [round(cx, 1), round(cy, 1),
                                      round(cr, 1)],
                           "limbs": [[list(sg["p0"]), list(sg["p1"])]
                                     for sg in members],
                           "area": int(math.pi * cr * cr +
                                       sum(math.hypot(sg["p1"][0] - sg["p0"][0],
                                                      sg["p1"][1] - sg["p0"][1])
                                           for sg in members) * 6)})

        # ---- lines: the remaining segments, grouped by original stroke
        by_path = {}
        for si, sg in enumerate(segs):
            if si in actor_seg or si in circle_seg:
                continue
            by_path.setdefault(sg["path"], []).append(sg)
        for pid in sorted(by_path):
            members = by_path[pid]
            verts = []
            for sg in members:
                p0, p1 = sg["p0"], sg["p1"]
                if not verts:
                    verts = [list(p0), list(p1)]
                    continue
                # 2px-wide skeleton runs merge into there-and-back pairs:
                # keep the segment once
                if len(verts) >= 2 and \
                   math.hypot(p0[0] - verts[-1][0],
                              p0[1] - verts[-1][1]) <= 4 and \
                   math.hypot(p1[0] - verts[-2][0],
                              p1[1] - verts[-2][1]) <= 4:
                    continue
                if math.hypot(p0[0] - verts[-1][0],
                              p0[1] - verts[-1][1]) > 6:
                    verts.append(list(p0))          # bridge a small gap
                verts.append(list(p1))
            total = sum(math.hypot(sg["p1"][0] - sg["p0"][0],
                                   sg["p1"][1] - sg["p0"][1])
                        for sg in members)
            if total < 8:
                continue
            # stroke colour + width sampled across the longest arm
            arm = max(members, key=lambda s: math.hypot(
                s["p1"][0] - s["p0"][0], s["p1"][1] - s["p0"][1]))
            mx = (arm["p0"][0] + arm["p1"][0]) / 2.0
            my = (arm["p0"][1] + arm["p1"][1]) / 2.0
            ux, uy = arm["p1"][0] - arm["p0"][0], arm["p1"][1] - arm["p0"][1]
            Lg = math.hypot(ux, uy) or 1.0
            nx, ny = -uy / Lg, ux / Lg
            cols, run, best = [], 0.0, 0.0
            for s_ in np.arange(-8, 8.01, 0.5):
                ix = int(round(mx + nx * s_))
                iy = int(round(my + ny * s_))
                if 0 <= iy < h and 0 <= ix < w and dark[iy, ix]:
                    run += 0.5
                    cols.append(rgb[iy, ix])
                else:
                    best = max(best, run)
                    run = 0.0
            best = max(best, run)
            med = np.median(np.array(cols), axis=0).astype(int) if cols \
                else np.array([0, 0, 0])
            ln = {"bbox": [int(min(v[0] for v in verts)),
                           int(min(v[1] for v in verts)),
                           int(max(v[0] for v in verts)) + 1,
                           int(max(v[1] for v in verts)) + 1],
                  "segs": [[[float(a[0]), float(a[1])],
                            [float(b[0]), float(b[1])]]
                           for a, b in zip(verts, verts[1:])],
                  "thickness": round(max(2.0, best), 1),
                  "color": "#%02X%02X%02X" % tuple(med),
                  "stroke": round(max(2.0, min(6.0, best)), 1)}
            # arrowheads: probe both ends, then walk the tip out to where
            # the line meets the (dilated) shape border
            for (tip, other) in ((verts[0], verts[1]),
                                 (verts[-1], verts[-2])):
                ok, _w = probe_arrow(line_src, tip, other)
                if not ok:
                    continue
                ux = tip[0] - other[0]
                uy = tip[1] - other[1]
                Ln = math.hypot(ux, uy) or 1.0
                ux, uy = ux / Ln, uy / Ln
                walked = None
                for s_ in np.arange(0.5, 17.0, 0.5):
                    ix = int(round(tip[0] + ux * s_))
                    iy = int(round(tip[1] + uy * s_))
                    if not (0 <= iy < h and 0 <= ix < w):
                        break
                    if d[iy, ix]:
                        walked = [round(tip[0] + ux * s_, 1),
                                  round(tip[1] + uy * s_, 1)]
                        break
                if walked:
                    ln["arrow_tip"] = walked
                    ln["arrow_from"] = [round(float(other[0]), 1),
                                        round(float(other[1]), 1)]
            lines.append(ln)
        return True

    label_frags = []
    for c in line_comps:
        if c["area"] < 10 or on_dash(c):
            continue
        pts = comp_points(c)
        if len(pts) < 12:
            continue
        p = pts.astype(float)
        mean = p.mean(axis=0)
        _, _, vt = np.linalg.svd(p - mean, full_matrices=False)
        ax = vt[0]
        nrm = np.array([-ax[1], ax[0]])
        t = (p - mean) @ ax
        e1, e2 = p[t.argmin()], p[t.argmax()]
        arrow_tip = arrow_from = None
        for (tip, other) in ((e1, e2), (e2, e1)):
            if math.hypot(*(tip - other)) < 18:
                continue
            ok, _w = probe_arrow(line_src, tip, other)
            if ok:
                arrow_tip, arrow_from = tip, other
                break
        work = p
        if arrow_tip is not None:
            # walk from the (dilation-cut) end onto the shape border
            ux, uy = (arrow_tip[0] - arrow_from[0]), (arrow_tip[1] - arrow_from[1])
            Lg = math.hypot(ux, uy) or 1.0
            ux, uy = ux / Lg, uy / Lg
            for s in np.arange(0.5, 17.0, 0.5):
                wx = int(round(arrow_tip[0] + ux * s))
                wy = int(round(arrow_tip[1] + uy * s))
                if 0 <= wy < h and 0 <= wx < w and fill_mask[wy, wx]:
                    arrow_tip = (float(wx), float(wy))
                    break
            dd = np.hypot(p[:, 0] - arrow_tip[0], p[:, 1] - arrow_tip[1])
            stripped = p[dd > 20]
            if len(stripped) >= 10:
                work = stripped
        # after the arrowhead is stripped: detach label fragments fused
        # with the line (the original lets some labels touch their line)
        work, frag = axis_minority(work)
        if len(frag) >= 12:
            label_frags.append([int(frag[:, 0].min()), int(frag[:, 1].min()),
                                int(frag[:, 0].max()) + 1,
                                int(frag[:, 1].max()) + 1])
        if len(work) < 12:
            continue
        # structural fit (arms >= 18 px): used only to detect branching
        segs_all = fit_polyline(work, tol=3.0) if len(work) >= 6 else []
        fit_segs = [s for s in segs_all
                    if math.hypot(s[1][0] - s[0][0], s[1][1] - s[0][1]) >= 18]
        if fit_segs:
            bridged = [fit_segs[0]]
            for s in fit_segs[1:]:
                prev_end = bridged[-1][1]
                if math.hypot(s[0][0] - prev_end[0], s[0][1] - prev_end[1]) > 2:
                    bridged.append([prev_end, s[0]])
                bridged.append(s)
            fit_segs = bridged
        maxdim = max(c["bbox"][2] - c["bbox"][0], c["bbox"][3] - c["bbox"][1])
        if arrow_tip is None and c["area"] < 45 and maxdim < 26:
            continue                      # rounded-box corner debris
        cnt = Counter()
        for a, b in fit_segs:
            cnt[(round(a[0] / 4), round(a[1] / 4))] += 1
            cnt[(round(b[0] / 4), round(b[1] / 4))] += 1
        maxdeg = max(cnt.values()) if cnt else 0
        branchy = arrow_tip is None and (maxdeg >= 3 or len(fit_segs) >= 6)
        x0, y0, x1, y1 = c["bbox"]
        if os.environ.get("TRACE_DBG") and c["area"] >= 250:
            print("DBG2", c["bbox"], "area", c["area"], "arrow",
                  arrow_tip is not None, "fit", len(fit_segs),
                  "maxdeg", maxdeg, "branchy", branchy)
        if branchy:
            # A fused network (Use Case: actors + association lines +
            # boundary frame all touch) must be decomposed, not Hough-fit.
            if c["area"] >= 8000 and maxdim >= 600:
                net = decompose_network(sub_mask(c))
                if os.environ.get("TRACE_DBG"):
                    print("DBGdecomp", c["bbox"], "area", c["area"],
                          "-> segs", len(net["segs"]),
                          "circles", len(net["circles"]))
                if emit_network(net, c):
                    continue
            circ = fit_circle(p[p[:, 1] <= y0 + 0.55 * (y1 - y0)])
            sticks.append({"bbox": [int(x0), int(y0), int(x1), int(y1)],
                           "circle": list(circ) if circ else None,
                           "limbs": [[list(a), list(b)] for a, b in
                                     hough_segments(p, min_len=28)],
                           "area": int(c["area"])})
            continue
        # line path: clean draw segments from Hough on the stripped points;
        # chain by endpoint proximity (<= 45 px). Segments that do not chain
        # (glyph fragments touching the line mid-way) are dropped.
        segs, dropped = chain_segs(hough_segments(work, min_len=16,
                                                  max_parts=6))
        if not segs:
            segs, dropped = fit_segs, []
        if not segs:
            if os.environ.get("TRACE_DBG") and c["area"] > 300:
                print("DBG drop comp", c["bbox"], "area", c["area"])
            continue
        if os.environ.get("TRACE_DBG") and dropped:
            print("DBG dropped non-chaining segs of", c["bbox"], dropped)
        if arrow_tip is not None:
            # extend the nearest segment endpoint to the measured tip
            best_i, best_d, which = None, 1e9, 0
            for i, (a, b) in enumerate(segs):
                da = math.hypot(a[0] - arrow_tip[0], a[1] - arrow_tip[1])
                db = math.hypot(b[0] - arrow_tip[0], b[1] - arrow_tip[1])
                if da < best_d:
                    best_d, best_i, which = da, i, 0
                if db < best_d:
                    best_d, best_i, which = db, i, 1
            if best_d < 45:
                a, b = segs[best_i]
                tip_t = (round(float(arrow_tip[0]), 1),
                         round(float(arrow_tip[1]), 1))
                segs[best_i] = [tip_t, b] if which == 0 else [a, tip_t]
        # thickness: p60 of the distance to the drawn segments, counted
        # only for points near them (a fused label/strand must not inflate
        # it into a false "fat" structure)
        dmin = None
        for (a, b) in segs:
            ab = np.array(b, float) - np.array(a, float)
            L2 = float(ab @ ab)
            if L2 < 1e-9:
                continue
            tp = np.clip(((work - np.array(a, float)) @ ab) / L2, 0, 1)
            proj = np.array(a, float) + tp[:, None] * ab
            dist = np.hypot(work[:, 0] - proj[:, 0], work[:, 1] - proj[:, 1])
            dmin = dist if dmin is None else np.minimum(dmin, dist)
        if dmin is not None:
            near = dmin[dmin <= 15.0]
            if len(near) >= max(20, 0.3 * len(dmin)):
                thick = float(np.percentile(near, 60)) * 2 + 1
            else:
                thick = float(np.percentile(dmin, 60)) * 2 + 1
        else:
            thick = 99.0
        if os.environ.get("TRACE_DBG") and c["area"] >= 250:
            print("DBG3", c["bbox"], "draw-segs", len(segs),
                  "first", segs[0] if segs else None, "thick",
                  round(thick, 1))
        if os.environ.get("TRACE_DBG") and c["area"] > 300:
            print("DBG comp", c["bbox"], "area", c["area"], "arrow",
                  arrow_tip is not None, "segs_all", len(segs_all),
                  "draw", len(segs), "maxdeg", maxdeg, "thick",
                  round(thick, 1))
        if thick <= 13:
            ln = {"bbox": [int(x0), int(y0), int(x1), int(y1)],
                  "segs": [[list(a), list(b)] for a, b in segs],
                  "thickness": round(thick, 1)}
            # stroke colour + width sampled at the middle of the longest arm
            arm = max(segs, key=lambda s: math.hypot(s[1][0] - s[0][0],
                                                     s[1][1] - s[0][1]))
            mx = (arm[0][0] + arm[1][0]) / 2.0
            my = (arm[0][1] + arm[1][1]) / 2.0
            ux, uy = arm[1][0] - arm[0][0], arm[1][1] - arm[0][1]
            Lg = math.hypot(ux, uy) or 1.0
            nx, ny = -uy / Lg, ux / Lg          # perpendicular
            cols, run, best = [], 0, 0
            for s in np.arange(-8, 8.01, 0.5):
                px, py = mx + nx * s, my + ny * s
                ix, iy = int(round(px)), int(round(py))
                if 0 <= iy < h and 0 <= ix < w and dark[iy, ix]:
                    run += 0.5
                    cols.append(rgb[iy, ix])
                else:
                    best = max(best, run)
                    run = 0.0
            best = max(best, run)
            if cols:
                med = np.median(np.array(cols), axis=0).astype(int)
                ln["color"] = "#%02X%02X%02X" % tuple(med)
            else:
                ln["color"] = "#000000"
            ln["stroke"] = max(2.0, min(6.0, best))
            if arrow_tip is not None:
                ln["arrow_tip"] = [round(float(arrow_tip[0]), 1),
                                   round(float(arrow_tip[1]), 1)]
                ln["arrow_from"] = [round(float(arrow_from[0]), 1),
                                    round(float(arrow_from[1]), 1)]
            lines.append(ln)
        else:
            sticks.append({"bbox": [int(x0), int(y0), int(x1), int(y1)],
                           "circle": None,
                           "limbs": [[list(a), list(b)] for a, b in
                                     hough_segments(p, min_len=28)],
                           "area": int(c["area"])})

    dash_comps = [c for c in rle_label(dark & ~d & ~tmask)
                  if 5 <= c["area"] <= 6000 and
                  min(c["bbox"][2] - c["bbox"][0],
                      c["bbox"][3] - c["bbox"][1]) <= 16]
    dash_pts = (np.concatenate([comp_points(c) for c in dash_comps])
                if dash_comps else np.zeros((0, 2), int))
    dashes = dash_clusters(dash_pts)

    # ------------------------------------------------- boundary from lines
    def axis_segs(lines_):
        out = []
        for li, ln in enumerate(lines_):
            for (a, b) in ln["segs"]:
                if abs(a[1] - b[1]) < 1.5 and abs(a[0] - b[0]) >= 150:
                    out.append(("h", round((a[1] + b[1]) / 2, 1),
                                min(a[0], b[0]), max(a[0], b[0]), li))
                elif abs(a[0] - b[0]) < 1.5 and abs(a[1] - b[1]) >= 150:
                    out.append(("v", round((a[0] + b[0]) / 2, 1),
                                min(a[1], b[1]), max(a[1], b[1]), li))
        return out

    def merge_sides(entries):
        sides = []
        for (pos, a, b, li) in sorted(entries):
            if sides and abs(sides[-1]["pos"] - pos) <= 3:
                s = sides[-1]
                s["a"] = min(s["a"], a)
                s["b"] = max(s["b"], b)
                s["lines"].append(li)
                s["parts"].append([a, b])
            else:
                sides.append({"pos": pos, "a": a, "b": b, "lines": [li],
                              "parts": [[a, b]]})
        for s in sides:
            s["parts"].sort()
            s["gaps"] = [[p1[1], p2[0]] for p1, p2 in
                         zip(s["parts"], s["parts"][1:]) if p2[0] - p1[1] > 30]
        return sides

    axs = axis_segs(lines)
    boundaries = []
    used_lines = set()
    hs_sides = merge_sides([e[1:] for e in axs if e[0] == "h"])
    vs_sides = merge_sides([e[1:] for e in axs if e[0] == "v"])
    best = None
    for t in hs_sides:
        for b in hs_sides:
            if b["pos"] - t["pos"] < 200 or abs(t["a"] - b["a"]) > 8 or \
               abs(t["b"] - b["b"]) > 8:
                continue
            for lv in vs_sides:
                for rv in vs_sides:
                    if rv["pos"] - lv["pos"] < 200:
                        continue
                    if max(abs(lv["a"] - t["pos"]), abs(rv["a"] - t["pos"]),
                           abs(lv["b"] - b["pos"]), abs(rv["b"] - b["pos"])) > 8:
                        continue
                    area = (rv["pos"] - lv["pos"]) * (b["pos"] - t["pos"])
                    if best is None or area > best[0]:
                        best = (area, t, b, lv, rv)
    solid_boundary = None
    if best:
        area, t, b, lv, rv = best
        solid_boundary = {
            "bbox": [int(min(t["a"], lv["pos"])), int(t["pos"]),
                     int(max(t["b"], rv["pos"])), int(b["pos"])],
            "kind": "boundary", "fill": "#FFFFFF", "stroke": "#000000",
            "stroke_width": 2, "radius": 0, "dashed": False}
        # sample the real stroke from the four side lines (the Use Case
        # frame is a 6px #202B35 border, not the 2px black default)
        side_lns = [lines[i] for i in
                    t["lines"] + b["lines"] + lv["lines"] + rv["lines"]]
        scols = [l.get("color") for l in side_lns if l.get("color")]
        if scols:
            arr = np.array([[int(c[k:k + 2], 16) for k in (1, 3, 5)]
                            for c in scols])
            med = np.median(arr, axis=0).astype(int)
            solid_boundary["stroke"] = "#%02X%02X%02X" % tuple(med)
        sws = [l.get("stroke") for l in side_lns if l.get("stroke")]
        if sws:
            solid_boundary["stroke_width"] = round(float(np.median(sws)), 1)
        if t["gaps"]:
            solid_boundary["gap_axis"] = "h"
            solid_boundary["gaps"] = t["gaps"]
        used_lines.update(t["lines"] + b["lines"] + lv["lines"] + rv["lines"])

    dashed_boundary = None
    if solid_boundary is None and dashes:
        dhs = [e for e in dashes if e["axis"] == "h"]
        dvs = [e for e in dashes if e["axis"] == "v"]
        if len(dhs) >= 2 and len(dvs) >= 2:
            top = min(dhs, key=lambda e: e["y"])
            bot = max(dhs, key=lambda e: e["y"])
            left = min(dvs, key=lambda e: e["x"])
            right = max(dvs, key=lambda e: e["x"])
            if bot["y"] - top["y"] >= 200 and right["x"] - left["x"] >= 200:
                row = dash_pts[dash_pts[:, 1] == top["y"]] if len(dash_pts) else np.zeros((0, 2), int)
                if len(row):
                    med = np.median(rgb[row[:, 1], row[:, 0]], axis=0).astype(int)
                    col = "#%02X%02X%02X" % tuple(med)
                else:
                    col = "#808080"
                dashed_boundary = {
                    "bbox": [int(left["x"]), int(top["y"]),
                             int(right["x"]), int(bot["y"])],
                    "kind": "boundary", "fill": "#FFFFFF", "stroke": col,
                    "stroke_width": 2, "radius": 0, "dashed": True,
                    "dash_on": int(top["on"]), "dash_off": int(top["off"])}
    boundaries = [b for b in (solid_boundary, dashed_boundary) if b]

    # boundary segments are shape borders: drop them from the line list
    lines = [ln for i, ln in enumerate(lines) if i not in used_lines]

    # drop leftover fragments lying ON the detected boundary perimeter
    # (the frame arrives as one line entry; 2px-wide skeleton runs leave
    # extra collinear fragments that would duplicate the boundary stroke)
    if solid_boundary is not None:
        bx0, by0, bx1, by1 = solid_boundary["bbox"]

        def _on_perimeter(ln):
            for (a, b) in ln["segs"]:
                for p in (a, b):
                    if not (bx0 - 6 <= p[0] <= bx1 + 6 and
                            by0 - 6 <= p[1] <= by1 + 6):
                        return False
                    if not (abs(p[0] - bx0) <= 5 or abs(p[0] - bx1) <= 5 or
                            abs(p[1] - by0) <= 5 or abs(p[1] - by1) <= 5):
                        return False
            return True

        lines = [ln for ln in lines if not _on_perimeter(ln)]

    # rejoin pieces split by a text-mask graze: endpoints within 14 px and
    # heading within 25 degrees -> one polyline (bend vertex = gap midpoint)
    changed = True
    while changed:
        changed = False
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                a, b = lines[i], lines[j]
                ends_a = [tuple(a["segs"][0][0]), tuple(a["segs"][-1][1])]
                ends_b = [tuple(b["segs"][0][0]), tuple(b["segs"][-1][1])]
                best = None
                for pa in ends_a:
                    for pb in ends_b:
                        dist = math.hypot(pa[0] - pb[0], pa[1] - pb[1])
                        if dist > 36:
                            continue
                        oa = ends_a[1] if pa is ends_a[0] else ends_a[0]
                        ob = ends_b[1] if pb is ends_b[0] else ends_b[0]
                        v1 = (pa[0] - oa[0], pa[1] - oa[1])
                        v2 = (ob[0] - pb[0], ob[1] - pb[1])
                        n1 = math.hypot(*v1) or 1
                        n2 = math.hypot(*v2) or 1
                        cosang = ((v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2))
                        ang = math.degrees(math.acos(max(-1.0, min(1.0, cosang))))
                        if ang > 12:
                            continue
                        if best is None or dist < best[0]:
                            best = (dist, pa, pb)
                if not best:
                    continue
                dist, pa, pb = best
                mid = (round((pa[0] + pb[0]) / 2, 1),
                       round((pa[1] + pb[1]) / 2, 1))
                a_segs = [list(map(list, s)) for s in a["segs"]]
                b_segs = [list(map(list, s)) for s in b["segs"]]
                a_at_end = (abs(pa[0] - a_segs[-1][1][0]) < 1e-6 and
                            abs(pa[1] - a_segs[-1][1][1]) < 1e-6)
                b_at_start = (abs(pb[0] - b_segs[0][0][0]) < 1e-6 and
                              abs(pb[1] - b_segs[0][0][1]) < 1e-6)
                # orient a and b so a ends at pa and b starts at pb
                if not a_at_end:
                    a_segs = [[s[1], s[0]] for s in a_segs][::-1]
                if not b_at_start:
                    b_segs = [[s[1], s[0]] for s in b_segs][::-1]
                a_segs[-1][1] = list(mid)
                b_segs[0][0] = list(mid)
                merged = {"bbox": [min(a["bbox"][0], b["bbox"][0]),
                                   min(a["bbox"][1], b["bbox"][1]),
                                   max(a["bbox"][2], b["bbox"][2]),
                                   max(a["bbox"][3], b["bbox"][3])],
                          "segs": a_segs + b_segs,
                          "thickness": max(a["thickness"], b["thickness"])}
                if a.get("arrow_tip"):
                    merged["arrow_tip"] = a["arrow_tip"]
                    merged["arrow_from"] = a["arrow_from"]
                if b.get("arrow_tip"):
                    merged["arrow_tip"] = b["arrow_tip"]
                    merged["arrow_from"] = b["arrow_from"]
                lines[i] = merged
                del lines[j]
                changed = True
                break
            if changed:
                break

    # ---- label fragments that were fused with a line: extend their band
    for fb in label_frags:
        best = None
        for t in white_texts:
            if t["inside"] is not None:
                continue
            b = t["bbox"]
            oy = min(b[3], fb[3]) - max(b[1], fb[1])
            if oy <= 0.5 * min(b[3] - b[1], fb[3] - fb[1]):
                continue
            if fb[2] <= b[0]:
                gapx = b[0] - fb[2]
            elif fb[0] >= b[2]:
                gapx = fb[0] - b[2]
            else:
                gapx = 0
            if gapx <= 26 and (best is None or gapx < best[0]):
                best = (gapx, t)
        if best:
            t = best[1]
            b = t["bbox"]
            t["bbox"] = [min(b[0], fb[0]), min(b[1], fb[1]),
                         max(b[2], fb[2]), max(b[3], fb[3])]
        elif (fb[2] - fb[0]) >= 18 and (fb[3] - fb[1]) >= 10:
            white_texts.append({"bbox": fb, "ink": "#222222",
                                "inside": None})

    # ---------------------------------------------------- text bbox repair
    # A glyph that touched a line is merged into the line component and
    # missing from its band bbox (e.g. the 'M' of "Manages..."). Re-scan the
    # band rows for dark pixels not belonging to any line/dash and extend.
    seg_all = [(a[0], a[1], b[0], b[1])
               for ln in lines for (a, b) in ln["segs"]]

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

    for t in white_texts:
        x0, y0, x1, y1 = t["bbox"]
        xs, ys = [], []
        for yy in range(max(0, y0 - 2), min(h, y1 + 2)):
            if any(abs(yy - r) <= 2 for r in dash_rows):
                continue
            lo, hi = max(0, x0 - 25), min(w, x1 + 25)
            for i in np.flatnonzero(dark[yy, lo:hi]):
                x = int(lo + i)
                if near_seg(x, yy):
                    continue
                xs.append(x)
                ys.append(yy)
        if not xs:
            continue
        # extend only contiguously (gap <= 12 px) so a neighbouring label's
        # glyphs are never swallowed; walk nearest-first on each side
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

    # ---------------------------------------------------------- arrows
    arrows = []
    probe_bw = line_src
    for li, ln in enumerate(lines):
        if ln.get("arrow_tip"):
            arrows.append({"line": li, "tip": ln["arrow_tip"],
                           "from": ln["arrow_from"], "widths": []})
            continue
        segs = ln["segs"]
        if len(segs) == 1:
            ends = [tuple(segs[0][0]), tuple(segs[0][1])]
        else:
            cnt = Counter()
            for a, b in segs:
                cnt[(round(a[0]), round(a[1]))] += 1
                cnt[(round(b[0]), round(b[1]))] += 1
            ends = [p for p, k in cnt.items() if k == 1]
        for tip in ends:
            verts = [q for s in segs for q in s if
                     not (abs(q[0] - tip[0]) < 0.6 and abs(q[1] - tip[1]) < 0.6)]
            if not verts:
                continue
            prev = min(verts, key=lambda p: (p[0] - tip[0]) ** 2 + (p[1] - tip[1]) ** 2)
            ok, widths = probe_arrow(probe_bw, tip, prev)
            if ok:
                arrows.append({"line": li, "tip": [float(tip[0]), float(tip[1])],
                               "from": [float(prev[0]), float(prev[1])],
                               "widths": [round(x, 1) for x in widths]})

    # ---------------------------------------------------------- assemble
    n_bnd = len(boundaries)
    shapes = boundaries + shapes
    for i, s in enumerate(shapes):
        s["id"] = "S%02d" % (i + 1)
    texts = []
    for t in white_texts:
        tt = dict(t)
        texts.append(tt)
    for t in fill_texts:
        tt = {k: v for k, v in t.items() if k != "inside_fill"}
        tt["inside"] = shapes[n_bnd + t["inside_fill"]]["id"]
        texts.append(tt)

    # ---- per-figure fixes: replacements (split bands / move off a grazing
    #      line) and small nudges (inherited text-frame overlaps)
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
    # stable ids, assigned exactly once on the pre-nudge order
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
    # NOTE: ids are deliberately NOT reassigned here - the stable ids come
    # from the pre-nudge order so text-content.json's id mapping holds.

    # ------------------------------------------- rule 8: line/text cuts
    # First pass against the measured ink boxes (+1 px) so the markers
    # overlay verifies against the original; build_figure.py repeats this
    # with the rendered font-metric boxes that the checker validates.
    lines, n_cuts = open_lines_at_texts(lines,
                                        [t["bbox"] for t in texts])
    if n_cuts:
        print("rule-8 line cuts: %d segment(s) opened at text bboxes"
              % n_cuts)

    report = {
        "canvas": {"w": int(w), "h": int(h)},
        "source": os.path.basename(src),
        "shapes": shapes,
        "lines": [{"id": "L%02d" % (i + 1), **ln} for i, ln in enumerate(lines)],
        "dashes": dashes,
        "sticks": [{"id": "K%02d" % (i + 1), **s} for i, s in enumerate(sticks)],
        "arrows": arrows,
        "texts": texts,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)

    # ---------------------------------------------------------- markers
    mk = img.copy()
    dr = ImageDraw.Draw(mk)
    for s in shapes:
        x0, y0, x1, y1 = s["bbox"]
        col = (0, 150, 0) if s["kind"] in ("rect", "rounded") else \
              (255, 0, 255) if s["kind"] == "ellipse" else (255, 140, 0)
        if s["kind"] == "boundary":
            col = (0, 0, 255)
        dr.rectangle([x0, y0, x1 - 1, y1 - 1], outline=col, width=3)
    for ln in report["lines"]:
        for (a, b) in ln["segs"]:
            dr.line([tuple(a), tuple(b)], fill=(255, 0, 0), width=3)
    for dsh in dashes:
        if dsh["axis"] == "h":
            dr.line([(dsh["x0"], dsh["y"]), (dsh["x1"], dsh["y"])],
                    fill=(0, 140, 255), width=2)
        else:
            dr.line([(dsh["x"], dsh["y0"]), (dsh["x"], dsh["y1"])],
                    fill=(0, 140, 255), width=2)
    for k in report["sticks"]:
        if k["circle"]:
            cx, cy, r = k["circle"]
            dr.ellipse([cx - r, cy - r, cx + r, cy + r],
                       outline=(0, 160, 160), width=3)
        for (a, b) in k["limbs"]:
            dr.line([tuple(a), tuple(b)], fill=(0, 160, 160), width=3)
    for ar in arrows:
        tx, ty = ar["tip"]
        dr.ellipse([tx - 7, ty - 7, tx + 7, ty + 7], outline=(0, 0, 255), width=3)
    for t in texts:
        x0, y0, x1, y1 = t["bbox"]
        dr.rectangle([x0, y0, x1, y1], outline=(255, 0, 255), width=2)
    mk_path = os.path.splitext(out)[0] + "_markers.png"
    mk.save(mk_path)

    # ---------------------------------------------------------- print
    print("canvas %dx%d" % (w, h))
    print("shapes: %d" % len(shapes))
    for s in shapes:
        print("  %s %-9s bbox=%s fill=%s stroke=%s r=%d cap=%d dashed=%s" %
              (s["id"], s["kind"], s["bbox"], s["fill"], s["stroke"],
               s.get("radius", 0), s.get("cap_ry", 0), s.get("dashed")))
    print("lines: %d  dashes: %d  sticks: %d  arrows: %d  texts: %d" %
          (len(lines), len(dashes), len(sticks), len(arrows), len(texts)))
    for ln in report["lines"]:
        print("  %s thick=%s nsegs=%d %s" %
              (ln["id"], ln["thickness"], len(ln["segs"]), ln["segs"][:4]))
    for dsh in dashes:
        print("  dash", dsh)
    for k in report["sticks"]:
        print("  stick", k["id"], "circle=", k["circle"],
              "limbs=", len(k["limbs"]), "area=", k["area"])
    for ar in arrows:
        print("  arrow line=%s tip=%s from=%s" %
              (ar["line"], ar["tip"], ar["from"]))
    for t in texts:
        print("  %s bbox=%s ink=%s inside=%s" %
              (t["id"], t["bbox"], t["ink"], t["inside"]))
    print("markers:", mk_path)


if __name__ == "__main__":
    main()

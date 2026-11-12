# -*- coding: utf-8 -*-
"""Pixel tracer for the Chen ERD (black line-art on white).

The stock trace_figure.py is tuned for solid-colour fills, so it finds no
shapes on this figure.  This copy detects the *closed white regions* that
sit behind every entity rectangle, relationship diamond and key ellipse
(flood-fill components of the near-white mask), classifies them by size /
fill ratio, reconstructs the outer stroke bbox, reads the label ink inside
each shape, and traces the orthogonal connector network after masking all
shapes and free labels.

Outputs <figure_dir>/trace.json and trace_markers.png (verification overlay).
No coordinates are invented: every value comes from the original PNG.

Usage:
  node scripts/run_py.mjs scripts/trace_erd_w3a.py <png> <out_dir>
"""
import ast
import json
import os
import sys
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trace_figure import rle_label  # noqa: E402


# --------------------------------------------------------------- label names
# measured shape centres -> semantic name (read from the original crops)
ENTITY_NAMES = {
    (462, 177): "Role",
    (1100, 177): "Account",
    (1740, 177): "UserProfile",
    (2380, 177): "Rubric",
    (462, 561): "CourseLearningOutcome",
    (1100, 561): "Assessment",
    (1740, 561): "QuestionCandidate",
    (2380, 561): "Question",
    (3020, 561): "SQLTestDataset",
    (1100, 945): "Concept",
    (1740, 945): "AssessmentSession",
    (2380, 945): "SelectionLog",
    (3020, 945): "MCQOption",
    (462, 1329): "LLMCache",
    (1100, 1329): "ConceptCompetency",
    (1740, 1329): "CompetencyGap",
    (3020, 1329): "Attempt",
}
KEY_NAMES = {
    (1100, 67): "account id",
    (2380, 67): "rubric id",
    (462, 288): "role id",
    (1740, 288): "user id",
    (1740, 451): "candidate id",
    (140, 561): "clo id",
    (780, 561): "assessment id",
    (2060, 561): "question id",
    (3020, 672): "dataset id",
    (780, 945): "concept id",
    (1420, 945): "session id",
    (2380, 1056): "log id",
    (2700, 945): "option id",
    (462, 1440): "cache id",
    (1100, 1440): "competency id",
    (1740, 1440): "gap id",
    (3020, 1440): "attempt id",
}
DIAMOND_NAMES = {
    (780, 176): "assigned",
    (1420, 176): "has",
    (780, 368): "defines",
    (1100, 368): "configures",
    (1740, 368): "authors",
    (2380, 368): "graded by",
    (1420, 560): "takes",
    (2700, 560): "tested by",
    (2060, 640): "promoted to",
    (780, 752): "maps to",
    (1100, 752): "targets",
    (1740, 752): "tagged with",
    (2380, 752): "chosen in",
    (2700, 752): "offers",
    (1420, 816): "instantiates",
    (1100, 1136): "measured by",
    (1420, 1136): "yields",
    (1740, 1136): "flags",
    (2380, 1168): "records",
    (2700, 1024): "answered in",
    (3020, 1136): "selected in",
    (1420, 1232): "diagnosed in",
    (2060, 944): "logs",
    (1420, 688): "seeds",
}


def nearest(mapping, cx, cy, tol=6):
    best, bd = None, 1e9
    for (x, y), name in mapping.items():
        d = (x - cx) ** 2 + (y - cy) ** 2
        if d < bd:
            best, bd = name, d
    if bd > tol * tol:
        raise SystemExit("no label mapped near %s,%s" % (cx, cy))
    return best


# ------------------------------------------------------------------ helpers

def inside_frac(kind, cx, cy, x0, y0, x1, y1):
    """Position of a point inside the inscribed diamond / ellipse / rect."""
    w, h = x1 - x0, y1 - y0
    dx = (cx - (x0 + x1 - 1) / 2.0) / (w / 2.0)
    dy = (cy - (y0 + y1 - 1) / 2.0) / (h / 2.0)
    if kind == "diamond":
        return abs(dx) + abs(dy)
    if kind == "ellipse":
        return (dx * dx + dy * dy) ** 0.5
    return max(abs(dx), abs(dy))


def shape_text(kind, dark, x0, y0, x1, y1, W, H):
    """Union ink bbox of the label glyphs inside one shape.

    Diamonds / ellipses: cut the stroke ring away first (a label can touch
    its outline, e.g. "promoted to" whose p descender meets the lower-left
    edge), then take every remaining glyph inside the white interior.
    Rectangles: glyphs never touch the border, so the inner box is enough.
    """
    w, h = x1 - x0, y1 - y0
    work = dark
    if kind in ("diamond", "ellipse"):
        cx = (x0 + x1 - 1) / 2.0
        cy = (y0 + y1 - 1) / 2.0
        ring = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(ring)
        if kind == "diamond":
            d.polygon([(cx, y0 - 10), (x1 + 12, cy), (cx, y1 + 10),
                       (x0 - 12, cy)], fill=255)
            d.polygon([(cx, y0 + 4), (x1 - 4, cy), (cx, y1 - 4),
                       (x0 + 4, cy)], fill=0)
        else:
            d.ellipse([x0 - 8, y0 - 8, x1 + 7, y1 + 7], fill=255)
            d.ellipse([x0 + 3, y0 + 3, x1 - 4, y1 - 4], fill=0)
        work = dark & ~(np.array(ring) > 0)
    sub = work[y0 + 2:y1 - 2, x0 + 2:x1 - 2]
    ox, oy = x0 + 2, y0 + 2
    boxes = []
    for c in rle_label(sub):
        bx0, by0, bx1, by1 = c["bbox"]
        ww, hh = bx1 - bx0, by1 - by0
        if c["area"] < 6 or hh < 5 or hh > 45 or ww > 0.85 * w:
            continue
        if kind == "rect" or kind == "entity":
            cx = (bx0 + bx1) / 2.0 + ox
            cy = (by0 + by1) / 2.0 + oy
            if inside_frac(kind, cx, cy, x0, y0, x1, y1) > 0.90:
                continue
        boxes.append([bx0 + ox, by0 + oy, bx1 + ox, by1 + oy])
    if not boxes:
        return None
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def runs(mask, axis, minlen=8):
    """Horizontal / vertical dark runs -> centre-line segments."""
    segs = []
    if axis == "h":
        for y in range(mask.shape[0]):
            xs = np.flatnonzero(mask[y])
            if len(xs) == 0:
                continue
            br = np.flatnonzero(np.diff(xs) > 1)
            starts = np.r_[0, br + 1]
            ends = np.r_[br + 1, len(xs)]
            for a, b in zip(starts, ends):
                x0, x1 = int(xs[a]), int(xs[b - 1]) + 1
                if x1 - x0 >= minlen:
                    segs.append((y, x0, x1))
    else:
        for x in range(mask.shape[1]):
            ys = np.flatnonzero(mask[:, x])
            if len(ys) == 0:
                continue
            br = np.flatnonzero(np.diff(ys) > 1)
            starts = np.r_[0, br + 1]
            ends = np.r_[br + 1, len(ys)]
            for a, b in zip(starts, ends):
                y0, y1 = int(ys[a]), int(ys[b - 1]) + 1
                if y1 - y0 >= minlen:
                    segs.append((x, y0, y1))
    clusters = []
    for p, a, b in segs:
        placed = False
        for c in clusters:
            if abs(a - c["a"]) <= 4 and abs(b - c["b"]) <= 4 and \
               p - c["ps"][-1] <= 1:
                c["ps"].append(p)
                placed = True
                break
        if not placed:
            clusters.append({"ps": [p], "a": a, "b": b})
    out = []
    for c in clusters:
        pos = round(sum(c["ps"]) / float(len(c["ps"])), 1)
        width = len(c["ps"])
        out.append((pos, c["a"], c["b"], width))
    # merge parallel centre-lines that anti-aliasing split into two rows /
    # columns 1-2 px apart (they would otherwise draw as a double stroke)
    merged = []
    for pos, a, b, width in sorted(out, key=lambda s: s[0]):
        placed = False
        for m in merged:
            ov = min(m[2], b) - max(m[1], a)
            if abs(m[0] - pos) <= 2 and ov >= 0.7 * min(m[2] - m[1], b - a):
                m[1] = min(m[1], a)
                m[2] = max(m[2], b)
                m[0] = round((m[0] + pos) / 2.0, 1)
                placed = True
                break
        if not placed:
            merged.append([pos, a, b, width])
    return [tuple(m) for m in merged]


# --------------------------------------------------------------------- main

def main():
    src, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    img = Image.open(src).convert("RGB")
    gray = np.array(img.convert("L"))
    white = gray > 240
    dark = gray < 200
    h, w = gray.shape

    shapes = []
    for c in rle_label(white):
        x0, y0, x1, y1 = c["bbox"]
        bw, bh = x1 - x0, y1 - y0
        area = c["area"]
        ratio = area / float(bw * bh)
        if 370 <= bw <= 390 and 90 <= bh <= 100 and ratio > 0.85:
            shapes.append({"kind": "entity", "inner": [x0, y0, x1, y1],
                           "bbox": [x0 - 4, y0 - 4, x1 + 4, y1 + 4]})
        elif 138 <= bw <= 148 and 65 <= bh <= 75 and abs(ratio - 0.47) < 0.09:
            cx, cy = (x0 + x1 - 1) / 2.0, (y0 + y1 - 1) / 2.0
            shapes.append({"kind": "diamond", "inner": [x0, y0, x1, y1],
                           "center": [cx, cy],
                           "bbox": [cx - 81, cy - 38, cx + 81, cy + 38]})
        elif 195 <= bw <= 206 and 50 <= bh <= 60 and ratio > 0.6:
            cx, cy = (x0 + x1 - 1) / 2.0, (y0 + y1 - 1) / 2.0
            shapes.append({"kind": "ellipse", "inner": [x0, y0, x1, y1],
                           "center": [cx, cy],
                           "bbox": [cx - 105.5, cy - 32, cx + 105.5, cy + 32]})
        elif 1720 <= bw <= 1730 and 100 <= bh <= 110:
            shapes.append({"kind": "legend", "inner": [x0, y0, x1, y1],
                           "bbox": [760, 1522, 2490, 1633]})

    # drop the white components that are not shapes (background islands)
    shapes = [s for s in shapes if s.get("center") or s["kind"] in
              ("entity", "legend")]

    # legend icons (measured directly; they are not 17-entity-sized)
    shapes.append({"kind": "legend_rect", "bbox": [808, 1555, 882, 1600]})
    shapes.append({"kind": "legend_diamond", "bbox": [1050, 1546, 1158, 1610]})
    shapes.append({"kind": "legend_key", "bbox": [1394, 1552, 1505, 1603]})

    texts = []
    for s in shapes:
        if s["kind"] == "legend":
            continue
        if s["kind"] in ("legend_rect", "legend_diamond", "legend_key"):
            continue
        inner = s["inner"]
        tb = shape_text(s["kind"], dark, inner[0], inner[1], inner[2],
                        inner[3], w, h)
        if tb is None:
            raise SystemExit("no text inside %s %s" % (s["kind"], s["inner"]))
        cx = (inner[0] + inner[2] - 1) / 2.0
        cy = (inner[1] + inner[3] - 1) / 2.0
        if s["kind"] == "entity":
            name = nearest(ENTITY_NAMES, cx, cy, 8)
            style = "entity"
        elif s["kind"] == "diamond":
            name = nearest(DIAMOND_NAMES, cx, cy, 8)
            style = "diamond"
        else:
            name = nearest(KEY_NAMES, cx, cy, 8)
            style = "key"
        s["name"] = name
        s["text_bbox"] = list(tb)
        texts.append({"content": name, "bbox": list(tb), "style": style,
                      "shape": s["kind"]})

    # free labels: the band list was measured by the stock component pass;
    # replicate it here from the original so the tracer is self-contained.
    comps = []
    for c in rle_label(dark):
        x0, y0, x1, y1 = c["bbox"]
        bw, bh = x1 - x0, y1 - y0
        if 8 <= bh <= 45 and 2 <= bw <= 60 and 10 <= c["area"] <= 2500:
            comps.append(c)
    boxes = [list(c["bbox"]) for c in comps]
    bands = []
    for b in sorted(boxes, key=lambda b: b[0]):
        placed = False
        for band in bands:
            by0 = min(x[1] for x in band)
            by1 = max(x[3] for x in band)
            ov = min(by1, b[3]) - max(by0, b[1])
            if ov > 0.5 * min(by1 - by0, b[3] - b[1]):
                bx0 = min(x[0] for x in band)
                bx1 = max(x[2] for x in band)
                if b[0] - bx1 <= 18 and bx0 - b[2] <= 18:
                    band.append(b)
                    placed = True
                    break
        if not placed:
            bands.append([b])
    changed = True
    while changed:
        changed = False
        for i in range(len(bands)):
            for j in range(i + 1, len(bands)):
                a, b = bands[i], bands[j]
                ay0 = min(x[1] for x in a); ay1 = max(x[3] for x in a)
                ax0 = min(x[0] for x in a); ax1 = max(x[2] for x in a)
                by0 = min(x[1] for x in b); by1 = max(x[3] for x in b)
                bx0 = min(x[0] for x in b); bx1 = max(x[2] for x in b)
                ov = min(ay1, by1) - max(ay0, by0)
                if ov > 0.5 * min(ay1 - ay0, by1 - by0) and \
                   not (bx0 - ax1 > 18 or ax0 - bx1 > 18):
                    bands[i] = a + b
                    del bands[j]
                    changed = True
                    break
            if changed:
                break
    band_boxes = []
    for band in bands:
        x0 = min(b[0] for b in band); y0 = min(b[1] for b in band)
        x1 = max(b[2] for b in band); y1 = max(b[3] for b in band)
        if x1 - x0 >= 8 and y1 - y0 >= 10:
            band_boxes.append((x0, y0, x1, y1))

    def in_shape(b):
        x0, y0, x1, y1 = b
        for s in shapes:
            sx0, sy0, sx1, sy1 = s["bbox"]
            if x0 >= sx0 and y0 >= sy0 and x1 <= sx1 and y1 <= sy1:
                return True
        return False

    free = []
    for b in band_boxes:
        if in_shape(b):
            continue
        x0, y0, x1, y1 = b
        bw = x1 - x0
        content = "1" if bw <= 11 else ("N" if bw <= 20 else "M")
        free.append({"content": content, "bbox": [x0, y0, x1, y1]})

    # legend texts (inside the legend box, left out of the band filter above)
    legend_texts = [
        ("Entity", [902, 1570, 966, 1595], "legend"),
        ("Relationship", [1180, 1569, 1323, 1595], "legend"),
        ("key", [1435, 1570, 1465, 1591], "legend_key"),
        ("Key attribute", [1525, 1569, 1676, 1595], "legend"),
        ("1 = one, N / M = many", [1788, 1570, 2169, 1595], "legend_bold"),
        ("(M : N = many-to-many)", [2183, 1570, 2365, 1594], "legend"),
    ]
    for content, bb, st in legend_texts:
        free.append({"content": content, "bbox": bb, "legend": True,
                     "style": st})

    # connector network: mask shapes + all text, then run orthogonal runs
    work = dark.copy()
    for s in shapes:
        x0, y0, x1, y1 = [int(round(v)) for v in s["bbox"]]
        work[max(0, y0 - 2):y1 + 2, max(0, x0 - 2):x1 + 2] = False
    for t in texts:
        x0, y0, x1, y1 = t["bbox"]
        work[max(0, y0 - 2):y1 + 2, max(0, x0 - 2):x1 + 2] = False
    for t in free:
        x0, y0, x1, y1 = t["bbox"]
        work[max(0, y0 - 2):y1 + 2, max(0, x0 - 2):x1 + 2] = False

    hs = runs(work, "h")
    vs = runs(work, "v")
    lines = []
    for y, x0, x1, th in hs:
        lines.append({"segs": [[x0, y], [x1, y]], "width": th,
                      "color": "#1A1A1A"})
    for x, y0, y1, th in vs:
        lines.append({"segs": [[x, y0], [x, y1]], "width": th,
                      "color": "#1A1A1A"})

    trace = {"canvas": {"w": w, "h": h}, "shapes": shapes, "lines": lines,
             "texts": texts + free,
             "source": "pixel measurements of ArchitectureDesign_ver1.1_image8.png"}
    with open(os.path.join(outdir, "trace.json"), "w", encoding="utf-8") as f:
        json.dump(trace, f, indent=1)

    # verification overlay
    ov = img.copy()
    d = ImageDraw.Draw(ov)
    for s in shapes:
        x0, y0, x1, y1 = s["bbox"]
        d.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=2)
    for ln in lines:
        (ax, ay), (bx, by) = ln["segs"][0], ln["segs"][-1]
        d.line([(ax, ay), (bx, by)], fill=(0, 0, 255), width=1)
    for t in texts + free:
        x0, y0, x1, y1 = t["bbox"]
        d.rectangle([x0, y0, x1, y1], outline=(0, 160, 0), width=1)
    ov.save(os.path.join(outdir, "trace_markers.png"))
    print("shapes: %d  diamonds: %d  ellipses: %d  entities: %d" %
          (len(shapes), sum(1 for s in shapes if s["kind"] == "diamond"),
           sum(1 for s in shapes if s["kind"] == "ellipse"),
           sum(1 for s in shapes if s["kind"] == "entity")))
    print("lines: %d  texts: %d (free %d)" %
          (len(lines), len(texts) + len(free), len(free)))


if __name__ == "__main__":
    main()

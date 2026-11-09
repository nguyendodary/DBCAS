# -*- coding: utf-8 -*-
"""W3b tracer for the v1.1 Table Relationship Diagram (original card grid).

Reads ArchitectureDesign_ver1.1_image9.png (3440x2080) and measures, from
pixels only:
  * the 21 full card rectangles (white body + #E8E8E8 header band) from the
    card border, not from the header fill alone;
  * the header title band and every body text row (name / [PK,FK] / type)
    plus the row separator lines;
  * the legend frame, its four text groups and its two relationship symbols;
  * the crow's-foot connector network (orthogonal runs plus the short
    diagonal prongs), outside the cards and the legend.

Writes trace.json and trace_markers.png (all detected elements drawn over a
copy of the original for visual verification).

Usage:
  tools/.venv/Scripts/python.exe scripts/trace_trd_w3b.py \
      docs/qa/diagram-originals/ArchitectureDesign_ver1.1_image9.png \
      docs/diagrams/rebuild/trd/trace.json
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trace_figure import rle_label, group_lines, comp_points, ink_colour  # noqa: E402

HDR_FILL = 232          # #E8E8E8
DARK = 150
SEP_MIN, SEP_MAX = 195, 240


def card_rects(gray, rgb):
    """Header bands -> full card rects by extending to the card border."""
    m = (np.abs(rgb[:, :, 0].astype(int) - HDR_FILL) <= 2) & \
        (np.abs(rgb[:, :, 1].astype(int) - HDR_FILL) <= 2) & \
        (np.abs(rgb[:, :, 2].astype(int) - HDR_FILL) <= 2)
    heads = []
    for c in rle_label(m):
        x0, y0, x1, y1 = c["bbox"]
        if c["area"] > 4000 and (x1 - x0) > 200 and (y1 - y0) < 200:
            heads.append([x0, y0, x1, y1])
    heads.sort(key=lambda b: (b[0], b[1]))
    cards = []
    for x0, y0, x1, y1 in heads:
        # full card left/top: one pixel of border outside the header fill
        cx0, cy0, cx1 = x0 - 1, y0 - 1, x1
        bottom = None
        for y in range(y1 + 5, min(gray.shape[0], y1 + 900)):
            cnt = int((gray[y, cx0 + 3:cx1 - 3] < DARK).sum())
            if cnt > (cx1 - cx0) * 0.8:
                bottom = y
                break
        if bottom is None:
            raise SystemExit("card bottom not found for header %s" % ([x0, y0, x1, y1],))
        # separator rows: light gray full-width bands inside the body
        seps = []
        for y in range(y1 + 3, bottom - 2):
            row = rgb[y, cx0 + 6:cx1 - 6]
            cnt = int(((row[:, 0] >= SEP_MIN) & (row[:, 0] <= SEP_MAX)).sum())
            if cnt > (cx1 - cx0) * 0.85:
                seps.append(y)
        groups = []
        for y in seps:
            if groups and y == groups[-1][-1] + 1:
                groups[-1].append(y)
            else:
                groups.append([y])
        sep_centers = [sum(g) / float(len(g)) for g in groups]
        # row boundaries; body starts after the header bottom border/shadow
        body_top = y1 + 4
        bounds = [body_top] + sep_centers + [bottom]
        rows = [{"top": round(bounds[i], 1), "bottom": round(bounds[i + 1], 1),
                 "baseline": round(bounds[i + 1] - 12, 1)}
                for i in range(len(bounds) - 1)]
        cards.append({"header": [cx0, cy0, cx1, y1],
                      "bbox": [cx0, cy0, cx1, bottom],
                      "body_top": body_top, "bottom": bottom,
                      "separators": [[g[0], g[-1]] for g in groups],
                      "rows": rows})
    return cards


def text_groups(gray, rgb, cards):
    """Header title + one bbox per body row (name/marker/type clusters)."""
    out = []
    for ci, c in enumerate(cards):
        x0, y0, x1, y1 = c["header"]
        sub = gray[y0 + 4:y1 - 2, x0 + 4:x1 - 4]
        dm = sub < DARK
        comps = []
        for comp in rle_label(dm):
            if comp["area"] < 6:
                continue
            bx0, by0, bx1, by1 = comp["bbox"]
            comps.append([bx0 + x0 + 4, by0 + y0 + 4,
                          bx1 + x0 + 4, by1 + y0 + 4])
        bands = group_lines(comps, 30)
        bands = [b for b in bands if b[2] - b[0] > 4 and b[3] - b[1] > 7]
        bands.sort(key=lambda b: (b[1], b[0]))
        title = bands[0] if bands else None
        rows = []
        for ri, row in enumerate(c["rows"]):
            ry0 = int(round(row["top"])) + 3
            ry1 = int(round(row["bottom"])) - 2
            ry0 = max(ry0, c["body_top"] + 2)
            sub2 = gray[ry0:ry1, x0 + 6:x1 - 4]
            dm2 = sub2 < DARK
            comps2 = []
            for comp in rle_label(dm2):
                if comp["area"] < 5:
                    continue
                bx0, by0, bx1, by1 = comp["bbox"]
                comps2.append([bx0 + x0 + 6, by0 + ry0,
                               bx1 + x0 + 6, by1 + ry0])
            bands2 = group_lines(comps2, 30)
            bands2 = [b for b in bands2 if b[2] - b[0] > 3 and b[3] - b[1] > 7]
            bands2.sort(key=lambda b: b[0])
            rows.append({"index": ri, "bands": bands2})
        out.append({"card": ci, "title": title, "rows": rows})
    return out


def extract_connectors(gray, cards):
    """All crow's-foot network pieces outside the cards and legend."""
    d = gray < 120
    m = d.copy()
    for c in cards:
        x0, y0, x1, y1 = c["bbox"]
        m[max(0, y0 - 4):y1 + 4, max(0, x0 - 4):x1 + 4] = False
    # legend frame + its symbols/text: measured below, excluded here
    m[1904:2028, 872:2568] = False

    H, W = m.shape
    # ---- horizontal runs, merged across thickness
    runs = []
    for y in range(H):
        xs = np.flatnonzero(m[y])
        if not len(xs):
            continue
        for r in np.split(xs, np.flatnonzero(np.diff(xs) > 1) + 1):
            if len(r) >= 10:
                runs.append([int(r[0]), y, int(r[-1]) + 1])
    runs.sort(key=lambda s: (s[1], s[0]))
    hgroups = []
    for x0, y, x1 in runs:
        placed = False
        for g in reversed(hgroups):
            if g["y1"] >= y - 1 and abs(g["x0"] - x0) <= 2 and \
               abs(g["x1"] - x1) <= 2:
                g["y1"] = y + 1
                g["x0"] = min(g["x0"], x0)
                g["x1"] = max(g["x1"], x1)
                placed = True
                break
            if y - g["y1"] > 2:
                break
        if not placed:
            hgroups.append({"x0": x0, "x1": x1, "y0": y, "y1": y + 1})

    # ---- vertical runs
    runs = []
    for x in range(W):
        ys = np.flatnonzero(m[:, x])
        if not len(ys):
            continue
        for r in np.split(ys, np.flatnonzero(np.diff(ys) > 1) + 1):
            if len(r) >= 10:
                runs.append([x, int(r[0]), int(r[-1]) + 1])
    runs.sort(key=lambda s: (s[0], s[1]))
    vgroups = []
    for x, y0, y1 in runs:
        placed = False
        for g in reversed(vgroups):
            if g["x1"] >= x - 1 and abs(g["y0"] - y0) <= 2 and \
               abs(g["y1"] - y1) <= 2:
                g["x1"] = x + 1
                g["y0"] = min(g["y0"], y0)
                g["y1"] = max(g["y1"], y1)
                placed = True
                break
            if x - g["x1"] > 2:
                break
        if not placed:
            vgroups.append({"x0": x, "x1": x + 1, "y0": y0, "y1": y1})

    # ---- residual diagonal prongs (crow's feet + rounded-corner AA)
    cov = np.zeros_like(m)
    for g in hgroups:
        cov[g["y0"]:g["y1"], g["x0"]:g["x1"]] = True
    for g in vgroups:
        cov[g["y0"]:g["y1"], g["x0"]:g["x1"]] = True
    rest = m & ~cov
    diags = []
    for comp in rle_label(rest):
        if comp["area"] < 25:
            continue
        x0, y0, x1, y1 = comp["bbox"]
        if max(x1 - x0, y1 - y0) < 12 or max(x1 - x0, y1 - y0) > 90:
            continue
        pts = comp_points(comp).astype(float)
        mean = pts.mean(axis=0)
        _, _, vt = np.linalg.svd(pts - mean, full_matrices=False)
        d = vt[0]
        t = (pts - mean) @ d
        a = mean + d * t.min()
        b = mean + d * t.max()
        diags.append([round(float(a[0]), 1), round(float(a[1]), 1),
                      round(float(b[0]), 1), round(float(b[1]), 1)])

    # ---- dedupe exactly overlapping pieces (many AA rows collapse to one)
    def clean(lst):
        out = []
        seen = set()
        for e in sorted(lst, key=lambda z: (round(z[1]), round(z[0]))):
            key = tuple(round(v, 1) for v in e)
            if key in seen:
                continue
            seen.add(key)
            out.append([round(v, 1) for v in e])
        return out

    H_ = []
    for g in hgroups:
        if g["x1"] - g["x0"] >= 10:
            H_.append([g["x0"], round((g["y0"] + g["y1"] - 1) / 2.0, 1),
                       g["x1"], round((g["y0"] + g["y1"] - 1) / 2.0, 1)])
    V_ = []
    for g in vgroups:
        if g["y1"] - g["y0"] >= 10:
            V_.append([round((g["x0"] + g["x1"] - 1) / 2.0, 1), g["y0"],
                       round((g["x0"] + g["x1"] - 1) / 2.0, 1), g["y1"]])
    return {"h": clean(H_), "v": clean(V_), "diag": clean(diags)}


def legend(rgb, gray):
    """Legend frame, text bands and the two drawn relationship symbols."""
    # frame: measured dark border around the legend
    sub = gray[1890:2040, 860:2580]
    dm = sub < DARK
    border = None
    for y in range(dm.shape[0]):
        if int(dm[y].sum()) > 1200:
            border = [860, 1890 + y, 860 + dm.shape[1], 1890 + y]
            break
    # proper extents from full-frame rows/cols
    tops = [1890 + y for y in range(dm.shape[0]) if int(dm[y].sum()) > 1200]
    lefts = [860 + x for x in range(dm.shape[1]) if int(dm[:, x].sum()) > 80]
    frame = [min(lefts), min(tops), max(lefts) + 2, max(tops) + 2]
    x0, y0, x1, y1 = frame
    comps = []
    for comp in rle_label(dm):
        if comp["area"] < 5:
            continue
        bx0, by0, bx1, by1 = comp["bbox"]
        comps.append([bx0 + 860, by0 + 1890, bx1 + 860, by1 + 1890])
    comps = [c for c in comps
             if not (c[0] <= x0 + 4 or c[2] >= x1 - 4 or
                     c[1] <= y0 + 4 or c[3] >= y1 - 4)]
    bands = group_lines(comps, 40)
    bands = [b for b in bands if b[3] - b[1] > 8]
    bands.sort(key=lambda b: (b[1], b[0]))
    return {"frame": frame, "text_bands": bands}


def main():
    src, out = sys.argv[1], sys.argv[2]
    img = Image.open(src).convert("RGB")
    rgb = np.array(img)
    gray = np.array(img.convert("L"))
    cards = card_rects(gray, rgb)
    texts = text_groups(gray, rgb, cards)
    conn = extract_connectors(gray, cards)
    leg = legend(rgb, gray)

    report = {
        "canvas": {"w": int(gray.shape[1]), "h": int(gray.shape[0])},
        "source": os.path.basename(src),
        "cards": cards,
        "texts": texts,
        "connectors": conn,
        "legend": leg,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)

    # ---- markers overlay
    mk = img.copy()
    dr = ImageDraw.Draw(mk)
    for c in cards:
        dr.rectangle(c["bbox"], outline=(0, 150, 0), width=3)
        dr.rectangle(c["header"], outline=(255, 0, 255), width=2)
        for s in c["separators"]:
            dr.line([(c["bbox"][0], s[0]), (c["bbox"][2], s[1])],
                    fill=(0, 160, 255), width=2)
    for g in conn["h"]:
        dr.line(g, fill=(255, 0, 0), width=2)
    for g in conn["v"]:
        dr.line(g, fill=(255, 0, 0), width=2)
    for g in conn["diag"]:
        dr.line(g, fill=(255, 120, 0), width=2)
    for t in texts:
        for r in t["rows"]:
            for b in r["bands"]:
                dr.rectangle(b, outline=(255, 0, 255), width=1)
        if t["title"]:
            dr.rectangle(t["title"], outline=(255, 0, 255), width=2)
    dr.rectangle(leg["frame"], outline=(0, 0, 255), width=2)
    mk_path = os.path.splitext(out)[0] + "_markers.png"
    mk.save(mk_path)

    print("canvas %dx%d" % (gray.shape[1], gray.shape[0]))
    print("cards", len(cards))
    for c in cards:
        print(" card", c["bbox"], "rows", len(c["rows"]),
              "seps", c["separators"])
    print("connector pieces: h=%d v=%d diag=%d" %
          (len(conn["h"]), len(conn["v"]), len(conn["diag"])))
    print("legend frame", leg["frame"], "bands", len(leg["text_bands"]))
    for b in leg["text_bands"]:
        print("  legend band", b)
    print("markers:", mk_path)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Build the System Context clone (Stage A) from measured trace data.

Inputs:
  trace.json          - pixel-measured elements (tracer output)
  text-content.json   - text strings read from original crops
  original PNG        - sampled for stroke centers (2px runs) and to snap
                        polyline segments to exact orthogonal coordinates

Outputs (same folder as trace.json):
  spec.json           - build spec (all coords, fonts, text bboxes)
  system-context.svg  - exact export (rendered to PNG by Chrome)
  system-context.drawio - mxGraph XML (draw.io CLI unavailable on this
                        machine; XML hand-authored, orthogonal edges with
                        explicit waypoints)

Usage:
  python scripts/build_system_context.py <trace.json> <text-content.json> \
      <original.png> <out_dir>
"""
import json
import os
import sys
import xml.sax.saxutils as saxutils

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_fonts import ink  # noqa: E402  (PIL ink-bbox helper)

REG = "C:/Windows/Fonts/arial.ttf"
BLD = "C:/Windows/Fonts/arialbd.ttf"

# ---------------------------------------------------------------- sampling


def runs_in(arr, lo, hi, min_len=1):
    """dark runs (<128) of arr[lo:hi] as (start,end) absolute half-open."""
    out = []
    i = lo
    while i < hi:
        if arr[i]:
            j = i
            while j < hi and arr[j]:
                j += 1
            if j - i >= min_len:
                out.append((i, j))
            i = j
        else:
            i += 1
    return out


def sample_cross_center(bw, p0, p1, axis, skip_a=8, skip_b=8):
    """Median stroke center of a (near-)orthogonal segment.

    axis 'v': segment vertical, returns median x of dark runs crossing it.
    axis 'h': segment horizontal, returns median y.
    Samples the middle of the segment only (skip px at both ends to avoid
    borders/arrowheads/corners). Runs wider than 5px (crossing lines) or
    farther than 4px from the assumed coordinate are discarded.
    Returns None when no valid sample exists.
    """
    if axis == "v":
        x = (p0[0] + p1[0]) / 2.0
        ya, yb = sorted((p0[1], p1[1]))
        lo, hi = ya + skip_a, yb - skip_b
        if hi - lo < 4:
            return None
        step = max(3, int((hi - lo) // 8))
        vals = []
        for y in range(int(lo), int(hi), step):
            for (s, e) in runs_in(bw[y], int(x) - 4, int(x) + 5):
                if e - s > 5:
                    continue
                if abs((s + e) / 2.0 - x) > 4:
                    continue
                vals.append((s + e) / 2.0)  # center of half-open run [s,e)
        if not vals:
            return None
        return round(float(np.median(vals)), 1)
    else:
        y = (p0[1] + p1[1]) / 2.0
        xa, xb = sorted((p0[0], p1[0]))
        lo, hi = xa + skip_a, xb - skip_b
        if hi - lo < 4:
            return None
        step = max(3, int((hi - lo) // 8))
        vals = []
        for x in range(int(lo), int(hi), step):
            col = bw[:, x]
            for (s, e) in runs_in(col, int(y) - 4, int(y) + 5):
                if e - s > 5:
                    continue
                if abs((s + e) / 2.0 - y) > 4:
                    continue
                vals.append((s + e) / 2.0)
        if not vals:
            return None
        return round(float(np.median(vals)), 1)


def border_center(bw, axis, guess, a, b, span=60):
    """Center of a box border line. axis 'h': horizontal border at row ~guess,
    sampled across columns a..b. axis 'v': vertical border at col ~guess."""
    if axis == "h":
        vals = []
        for x in range(a, b, max(5, (b - a) // span)):
            for (s, e) in runs_in(bw[:, x], guess - 3, guess + 4):
                if e - s <= 4 and abs((s + e) / 2.0 - guess) <= 3:
                    vals.append((s + e) / 2.0)
        return round(float(np.median(vals)), 1) if vals else None
    else:
        vals = []
        for y in range(a, b, max(5, (b - a) // span)):
            for (s, e) in runs_in(bw[y], guess - 3, guess + 4):
                if e - s <= 4 and abs((s + e) / 2.0 - guess) <= 3:
                    vals.append((s + e) / 2.0)
        return round(float(np.median(vals)), 1) if vals else None


# ---------------------------------------------------------------- snapping


def snap_flow(fl, arrow_at):
    """Snap one polyline to exact orthogonal segments.

    Returns (points, cross) where cross is per-segment cross-coordinate.
    Arrow-tip segments are anchored to the measured tip; other end segments
    keep the measured along-axis coordinate (box border row).
    """
    pts = [tuple(float(v) for v in p) for p in fl]
    n = len(pts) - 1
    axes = []
    for i in range(n):
        a, b = pts[i], pts[i + 1]
        if a[0] == b[0]:
            axes.append("v")
        elif a[1] == b[1]:
            axes.append("h")
        else:
            axes.append("v" if abs(a[0] - b[0]) < abs(a[1] - b[1]) else "h")

    cross = [None] * n
    for i in range(n):
        touches_tip = ((arrow_at == "end" and i == n - 1) or
                       (arrow_at == "start" and i == 0))
        if touches_tip:
            tip = pts[-1] if arrow_at == "end" else pts[0]
            cross[i] = tip[0] if axes[i] == "v" else tip[1]
            continue
        c = sample_cross_center(bw, pts[i], pts[i + 1], axes[i])
        if c is None:
            c = pts[i][0] if axes[i] == "v" else pts[i][1]
        cross[i] = c

    # rebuild vertices
    out = [None] * (n + 1)
    # start: along = measured, cross = cross[0]
    if axes[0] == "v":
        out[0] = (cross[0], pts[0][1])
    else:
        out[0] = (pts[0][0], cross[0])
    for i in range(1, n):
        prev_ax, cur_ax = axes[i - 1], axes[i]
        if prev_ax == "v" and cur_ax == "h":
            out[i] = (cross[i - 1], cross[i])
        elif prev_ax == "h" and cur_ax == "v":
            out[i] = (cross[i], cross[i - 1])
        else:  # collinear continuation (should not happen)
            out[i] = (cross[i - 1], cross[i]) if cur_ax == "v" else (cross[i], cross[i - 1])
    # end: arrow tip -> exact measured tip both coords; else measured along
    tip = pts[-1]
    if arrow_at == "end":
        out[n] = tip
    elif axes[-1] == "v":
        out[n] = (cross[-1], tip[1])
    else:
        out[n] = (tip[0], cross[-1])
    # snap tiny float noise
    out = [(round(x, 1), round(y, 1)) for x, y in out]
    return out, cross


def arrow_polygon(tip, prev_pt, apex_back=1.5, length=11.0, half=5.5):
    """Triangle apex1.5px back from measured line-end tip along -u,
    base `length` further back, half-width `half`."""
    tx, ty = tip
    px, py = prev_pt
    dx, dy = tx - px, ty - py
    L = (dx * dx + dy * dy) ** 0.5 or 1.0
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    ax, ay = tx - ux * apex_back, ty - uy * apex_back
    bx, by = ax - ux * length, ay - uy * length
    return [(round(ax, 1), round(ay, 1)),
            (round(bx + nx * half, 1), round(by + ny * half, 1)),
            (round(bx - nx * half, 1), round(by - ny * half, 1))]


# ---------------------------------------------------------------- fonts

FONT_PLAN = [
    # (selector, weight, size)
    ("T00", "bold", 36.5),
    ("FLOW", "regular", 18),
    ("B00", "bold", 29),
    ("B01", "bold", 29),
    ("B02", "bold", 30),
    ("B03", "regular", 17),
    ("B04", "regular", 17),
    ("B05", "regular", 17),
    ("E00", "bold", 42),
]


def font_for(weight, size):
    return ImageFont.truetype(BLD if weight == "bold" else REG, size)


def place_text(text, weight, size, measured):
    """Return (svg_x, baseline_y, ink_bbox_at_placement)."""
    m0 = measured
    f = font_for(weight, size)
    im = Image.new("L", (2600, 240), 255)
    d = ImageDraw.Draw(im)
    pen_x, pen_y = 60, 160  # baseline
    d.text((pen_x, pen_y), text, font=f, fill=0, anchor="ls")
    bb = im.point(lambda p: 255 if p < 128 else 0).getbbox()
    ix0, iy0 = bb[0] - pen_x, bb[1] - pen_y
    x = m0[0] - ix0
    baseline = m0[1] - iy0
    return round(x, 1), round(baseline, 1), (m0[0], m0[1], m0[2], m0[3])


# ---------------------------------------------------------------- outputs

def svg_escape(s):
    return saxutils.escape(s)


def write_svg(path, shapes, ell, icons, flows, arrows, texts):
    W, H = 1431, 1061
    p = []
    a = p.append
    a('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
      'viewBox="0 0 %d %d">' % (W, H, W, H))
    a('<rect width="%d" height="%d" fill="#FFFFFF"/>' % (W, H))
    a('<g fill="none" stroke="#000000" stroke-width="2">')
    for r in shapes:
        a('<rect x="%s" y="%s" width="%s" height="%s"/>' %
          (r["x"], r["y"], r["w"], r["h"]))
    a('<ellipse cx="%s" cy="%s" rx="%s" ry="%s"/>' %
      (ell["cx"], ell["cy"], ell["rx"], ell["ry"]))
    for ic in icons:
        if ic["kind"] == "ellipse":
            a('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" stroke-width="1.5"/>' %
              (ic["cx"], ic["cy"], ic["rx"], ic["ry"]))
        elif ic["kind"] == "rect":
            a('<rect x="%s" y="%s" width="%s" height="%s" stroke-width="1.5"/>' %
              (ic["x"], ic["y"], ic["w"], ic["h"]))
        elif ic["kind"] == "line":
            a('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke-width="1.5"/>' %
              (ic["x1"], ic["y1"], ic["x2"], ic["y2"]))
    for fl in flows:
        pts = " ".join("%s,%s" % (x, y) for x, y in fl["points"])
        a('<polyline points="%s"/>' % pts)
    a('</g>')
    a('<g fill="#000000" stroke="none">')
    for ar in arrows:
        pts = " ".join("%s,%s" % (x, y) for x, y in ar["poly"])
        a('<polygon points="%s"/>' % pts)
    for ic in icons:
        if ic["kind"] == "tri":
            pts = " ".join("%s,%s" % (x, y) for x, y in ic["points"])
            a('<polygon points="%s"/>' % pts)
    a('</g>')
    a('<g font-family="Arial, Helvetica, sans-serif" fill="#000000">')
    for t in texts:
        fw = "bold" if t["weight"] == "bold" else "normal"
        a('<text x="%s" y="%s" font-size="%s" font-weight="%s">%s</text>' %
          (t["x"], t["y"], t["size"], fw, svg_escape(t["content"])))
    a('</g>')
    a('</svg>')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(p))


def write_drawio(path, shapes, ell, icons, flows, arrows, texts, box_texts):
    """mxGraph XML. Rect/ellipse vertices carry their centered labels;
    flow labels are absolute text vertices; flows are edges with explicit
    source/target points + orthogonal waypoints."""
    esc = saxutils.escape
    E = []
    a = E.append
    a('<mxfile host="dbcas-rebuild">')
    a('<diagram id="system-context" name="System Context">')
    a('<mxGraphModel dx="1431" dy="1061" grid="1" gridSize="10" guides="1" '
      'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
      'pageWidth="1431" pageHeight="1061" math="0" shadow="0">')
    a('<root>')
    a('<mxCell id="0"/>')
    a('<mxCell id="1" parent="0"/>')

    def vertex(id_, value, style, x, y, w, h):
        a('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="1">'
          % (id_, esc(value), style))
        a('<mxGeometry x="%s" y="%s" width="%s" height="%s" as="geometry"/>'
          % (x, y, w, h))
        a('</mxCell>')

    box_style = ("rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;"
                 "strokeColor=#000000;strokeWidth=2;fontFamily=Arial;"
                 "fontStyle=1;align=center;verticalAlign=middle;spacing=0;")
    for i, r in enumerate(shapes):
        vid = "R%d" % (i + 1)
        fs = {0: 29, 1: 29, 2: 30}.get(i)
        if i < 3:
            st = box_style + "fontSize=%d;" % fs
            val = box_texts[i]
        else:
            st = ("rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;"
                  "strokeColor=#000000;strokeWidth=2;")
            val = ""
        vertex(vid, val, st, r["x"], r["y"], r["w"], r["h"])

    vertex("E1", "DBCAS",
           "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;"
           "strokeWidth=2;fontFamily=Arial;fontSize=42;fontStyle=1;align=center;"
           "verticalAlign=middle;spacing=0;",
           round(ell["cx"] - ell["rx"], 1), round(ell["cy"] - ell["ry"], 1),
           round(ell["rx"] * 2, 1), round(ell["ry"] * 2, 1))

    for i, ic in enumerate(icons):
        if ic["kind"] == "ellipse":
            vertex("I%d" % (i + 1), "",
                   "ellipse;whiteSpace=wrap;html=1;fillColor=none;"
                   "strokeColor=#000000;strokeWidth=1.5;",
                   round(ic["cx"] - ic["rx"], 1), round(ic["cy"] - ic["ry"], 1),
                   round(ic["rx"] * 2, 1), round(ic["ry"] * 2, 1))
        elif ic["kind"] == "rect":
            vertex("I%d" % (i + 1), "",
                   "rounded=0;whiteSpace=wrap;html=1;fillColor=none;"
                   "strokeColor=#000000;strokeWidth=1.5;",
                   ic["x"], ic["y"], ic["w"], ic["h"])
        elif ic["kind"] == "line":
            a('<mxCell id="I%d" style="edgeStyle=none;html=1;strokeColor=#000000;'
              'strokeWidth=1.5;endArrow=none;endFill=0;" edge="1" parent="1">'
              % (i + 1))
            a('<mxGeometry relative="1" as="geometry">')
            a('<mxPoint x="%s" y="%s" as="sourcePoint"/>' % (ic["x1"], ic["y1"]))
            a('<mxPoint x="%s" y="%s" as="targetPoint"/>' % (ic["x2"], ic["y2"]))
            a('</mxGeometry>')
            a('</mxCell>')
        elif ic["kind"] == "tri":
            xs = [p[0] for p in ic["points"]]
            ys = [p[1] for p in ic["points"]]
            vertex("I3b", "",
                   "shape=triangle;direction=east;whiteSpace=wrap;html=1;"
                   "fillColor=#000000;strokeColor=#000000;",
                   min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

    # flows as edges with explicit waypoints
    for i, fl in enumerate(flows):
        pts = fl["points"]
        ar = arrows[i]
        arrow_at = fl["arrow_at"]
        if arrow_at == "end":
            es = ("edgeStyle=orthogonalConnector;rounded=0;jettySize=auto;html=1;"
                  "strokeColor=#000000;strokeWidth=2;endArrow=classic;endFill=1;"
                  "endSize=11;endFill=1;")
        elif arrow_at == "start":
            es = ("edgeStyle=orthogonalConnector;rounded=0;jettySize=auto;html=1;"
                  "strokeColor=#000000;strokeWidth=2;endArrow=none;"
                  "startArrow=classic;startFill=1;startSize=11;")
        else:
            es = ("edgeStyle=orthogonalConnector;rounded=0;jettySize=auto;html=1;"
                  "strokeColor=#000000;strokeWidth=2;endArrow=none;")
        a('<mxCell id="%s" style="%s" edge="1" parent="1">' % (fl["id"], es))
        a('<mxGeometry relative="1" as="geometry">')
        a('<mxPoint x="%s" y="%s" as="sourcePoint"/>' % (pts[0][0], pts[0][1]))
        a('<mxPoint x="%s" y="%s" as="targetPoint"/>' % (pts[-1][0], pts[-1][1]))
        if len(pts) > 2:
            a('<Array as="points">')
            for (x, y) in pts[1:-1]:
                a('<mxPoint x="%s" y="%s"/>' % (x, y))
            a('</Array>')
        a('</mxGeometry>')
        a('</mxCell>')

    # flow labels + title as absolute text vertices
    for t in texts:
        fs = int(round(float(t["size"])))
        fw = 1 if t["weight"] == "bold" else 0
        b = t["measured"]
        vertex(t["id"], esc(t["content"]),
               "text;html=1;strokeColor=none;fillColor=none;align=left;"
               "verticalAlign=top;fontFamily=Arial;fontSize=%d;fontStyle=%d;"
               "whiteSpace=wrap;spacingLeft=0;spacingTop=0;" % (fs, fw),
               b[0], b[1], b[2] - b[0], b[3] - b[1])

    a('</root>')
    a('</mxGraphModel>')
    a('</diagram>')
    a('</mxfile>')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(E))


# ---------------------------------------------------------------- main

def main():
    trace_path, content_path, png_path, out_dir = sys.argv[1:5]
    t = json.load(open(trace_path, encoding="utf-8"))
    c = json.load(open(content_path, encoding="utf-8"))
    global bw
    img = Image.open(png_path).convert("L")
    bw = np.array(img) < 128

    # ---- box rects: measure all four borders (stroke centers)
    rect_specs = [
        ("Learner", 87, 96, 349, 191),
        ("Administrator", 1081, 96, 1343, 191),
        ("LLM Provider", 104, 865, 489, 961),
        ("legend", 392, 986, 1038, 1042),
    ]
    shapes = []
    for name, lx, ty, rx_, by in rect_specs:
        left = border_center(bw, "v", lx + 1, ty + 20, by - 20)
        right = border_center(bw, "v", rx_ - 1, ty + 20, by - 20)
        top = border_center(bw, "h", ty + 1, lx + 20, rx_ - 20)
        bottom = border_center(bw, "h", by, lx + 20, rx_ - 20)
        shapes.append({"name": name, "x": left, "y": top,
                       "w": round(right - left, 1), "h": round(bottom - top, 1),
                       "borders": [left, top, right, bottom]})

    # ---- ellipse: extremal arc measurement (text/line masked already by
    #      window choice); bottom arc sampled at columns clear of flow lines
    def arc_center_rows(cols, rows):
        vals = []
        for x in cols:
            for (s, e) in runs_in(bw[:, x], rows[0], rows[1]):
                if e - s <= 4:
                    vals.append((s + e) / 2.0)
        return round(float(np.median(vals)), 1) if vals else None

    def arc_center_cols(rows, cols):
        vals = []
        for y in rows:
            for (s, e) in runs_in(bw[y], cols[0], cols[1]):
                if e - s <= 4:
                    vals.append((s + e) / 2.0)
        return round(float(np.median(vals)), 1) if vals else None

    # Apex windows chosen to avoid arrowheads (F01 arrow covers cols ~691-703,
    # F02 ~726-738, rows 327-339) and the F18 vertical at x715/716; long runs
    # (flow lines) are dropped by the e-s<=4 guard inside arc_center_*.
    top_c = arc_center_rows([705, 710, 712, 718, 720], (330, 350))
    bot_c = arc_center_rows([700, 705, 710, 720, 725], (585, 612))
    # left/right arcs sampled only at rows 465..471 (around the horizontal
    # extremal row 468): rows farther from cy are biased ~0.5-1px by
    # curvature. Verified against raw pixels: left edge 506.0, right 925.0
    # -> rx 209.5, cx 715.5 (top 339.0 / bottom 598.0 -> cy 468.5, ry 129.5).
    left_c = arc_center_cols(list(range(465, 472)), (495, 520))
    right_c = arc_center_cols(list(range(465, 472)), (915, 940))
    ell = {"cx": round((left_c + right_c) / 2.0, 1),
           "cy": round((top_c + bot_c) / 2.0, 1),
           "rx": round((right_c - left_c) / 2.0, 1),
           "ry": round((bot_c - top_c) / 2.0, 1)}

    # ---- legend icons
    icons = [
        {"kind": "ellipse", "cx": 465.0, "cy": 1014.5, "rx": 20.5, "ry": 14.0},
        {"kind": "rect", "x": 619.5, "y": 1000.5, "w": 40.0, "h": 28.0},
        {"kind": "line", "x1": 794.5, "y1": 1015.0, "x2": 870.0, "y2": 1015.0},
        {"kind": "tri", "points": [(881.0, 1015.0), (870.0, 1010.0),
                                   (870.0, 1020.0)]},
    ]

    # ---- flows: snap to orthogonal, build arrow polygons
    arrows_by_flow = {a_["flow"]: a_ for a_ in t["arrows"]}
    flows, arrows = [], []
    for i, fl in enumerate(t["flows"]):
        ar = arrows_by_flow.get(i)
        arrow_at = None
        if ar:
            tip = tuple(ar["tip"])
            # classify by nearest endpoint (tips can be 1px off a vertex)
            d0 = ((tip[0] - fl[0][0]) ** 2 + (tip[1] - fl[0][1]) ** 2) ** 0.5
            d1 = ((tip[0] - fl[-1][0]) ** 2 + (tip[1] - fl[-1][1]) ** 2) ** 0.5
            arrow_at = "start" if d0 <= d1 else "end"
        pts, cross = snap_flow(fl, arrow_at)
        flows.append({"id": "F%02d" % (i + 1), "points": pts,
                      "arrow_at": arrow_at, "cross": cross})
        if ar:
            # polygon anchored to the MEASURED tip, direction from snapped line
            if arrow_at == "end":
                poly = arrow_polygon(tuple(ar["tip"]), pts[-2])
            else:
                poly = arrow_polygon(tuple(ar["tip"]), pts[1])
            arrows.append({"flow": i, "tip": list(ar["tip"]), "poly": poly})
        else:
            arrows.append({"flow": i, "tip": None, "poly": None})
    arrows = [a_ for a_ in arrows if a_["poly"]]
    assert len(arrows) == len(flows), "every flow must have exactly one arrow"

    # ---- texts: calibrated fonts, placement from measured ink bboxes
    texts = []
    for i, b in enumerate(t["free_texts"]):
        content = c["free_texts"][i]
        if i == 0:
            weight, size = "bold", 36.5
        else:
            weight, size = "regular", 18
        x, y, mb = place_text(content, weight, size, b)
        texts.append({"id": "T%02d" % i, "kind": "title" if i == 0 else "flow_label",
                      "content": content, "weight": weight, "size": size,
                      "x": x, "y": y, "measured": list(b)})
    for i, entry in enumerate(t["box_texts"]):
        content = c["box_texts"][i]
        weight, size = {0: ("bold", 29), 1: ("bold", 29), 2: ("bold", 30),
                        3: ("regular", 17), 4: ("regular", 17),
                        5: ("regular", 17)}[i]
        x, y, mb = place_text(content, weight, size, entry["text"])
        texts.append({"id": "B%02d" % i, "kind": "box_label",
                      "content": content, "weight": weight, "size": size,
                      "x": x, "y": y, "measured": list(entry["text"])})
    for i, b in enumerate(t["ellipse_texts"]):
        content = c["ellipse_texts"][i]
        weight, size = "bold", 42
        x, y, mb = place_text(content, weight, size, b)
        texts.append({"id": "E%02d" % i, "kind": "ellipse_label",
                      "content": content, "weight": weight, "size": size,
                      "x": x, "y": y, "measured": list(b)})

    # ---- outputs
    os.makedirs(out_dir, exist_ok=True)
    svg_path = os.path.join(out_dir, "system-context.svg")
    drawio_path = os.path.join(out_dir, "system-context.drawio")
    spec_path = os.path.join(out_dir, "spec.json")

    write_svg(svg_path, shapes, ell, icons, flows, arrows, texts)
    write_drawio(drawio_path, shapes, ell, icons, flows, arrows, texts,
                 c["box_texts"][:3])

    spec = {
        "canvas": t["canvas"],
        "source": "trace.json + text-content.json + pixel-sampled stroke centers",
        "rects": [{"name": r["name"], "stroke_rect": [r["x"], r["y"], r["w"], r["h"]],
                   "stroke_width": 2 if r["name"] != "legend" else 2}
                  for r in shapes],
        "ellipse": {"cx": ell["cx"], "cy": ell["cy"], "rx": ell["rx"],
                    "ry": ell["ry"], "stroke_width": 2, "label": "DBCAS"},
        "legend_icons": icons,
        "flows": [{"id": f["id"], "points": f["points"], "arrow_at": f["arrow_at"],
                   "arrow_tip": arrows[i]["tip"], "arrow_poly": arrows[i]["poly"]}
                  for i, f in enumerate(flows)],
        "texts": texts,
        "style": {"font_family": "Arial, Helvetica, sans-serif",
                  "stroke": "#000000", "fill": "#FFFFFF"},
    }
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=1)

    print("wrote", svg_path)
    print("wrote", drawio_path)
    print("wrote", spec_path)
    print("rects:", [(r["name"], r["borders"]) for r in shapes])
    print("ellipse:", ell)
    print("flows:", len(flows), "arrows:", len(arrows), "texts:", len(texts))
    for f_ in flows:
        print(" ", f_["id"], f_["points"], "arrow@", f_["arrow_at"])


if __name__ == "__main__":
    main()

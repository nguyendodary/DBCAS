# -*- coding: utf-8 -*-
"""Build a traced figure (Stage A clone) to SVG + drawio + spec.json.

Inputs (in <figure_dir>): trace.json (pixel measurements), text-content.json
(strings, same order as the tracer's texts), font-plan.json (per-label
weight/size/anchor).

Outputs: <name>.svg (authoritative export), <name>.drawio (hand-authored
mxGraph, orthogonal edges + waypoints), spec.json (full element list).

Every coordinate comes from the trace - no auto layout. Canvas is the
original's exact pixel size.

Usage:
  node scripts/run_py.mjs scripts/build_figure.py <figure_dir>
"""
import json
import math
import os
import sys
import xml.sax.saxutils as saxutils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_system_context import arrow_polygon, place_text  # noqa: E402
from calibrate_fonts import ink  # noqa: E402  (PIL ink-offset helper)
from trace_figure import open_lines_at_texts  # noqa: E402  (rule-8 cut)

REG = "C:/Windows/Fonts/arial.ttf"


def fmt(v):
    return ("%g" % round(float(v), 1))


# ---------------------------------------------------------------------- svg

def build_svg(trace, dashes, texts, name):
    W, H = trace["canvas"]["w"], trace["canvas"]["h"]
    p = []
    a = p.append
    a('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
      'viewBox="0 0 %d %d">' % (W, H, W, H))
    a('<rect width="%d" height="%d" fill="#FFFFFF"/>' % (W, H))

    for s in trace["shapes"]:
        x0, y0, x1, y1 = s.get("draw_bbox") or s["bbox"]
        sw = s.get("stroke_width", 2)
        st = s.get("stroke", "#000000")
        fl = s.get("fill", "#FFFFFF")
        if s["kind"] == "boundary" and s.get("dashed"):
            continue                      # emitted as dash runs below
        if s["kind"] == "boundary":
            gaps = s.get("gaps") or []
            segs_h = [[x0, x1]]
            for g in gaps:
                new = []
                for a0, b0 in segs_h:
                    if g[0] > a0 and g[1] < b0:
                        new.append([a0, g[0]])
                        new.append([g[1], b0])
                    else:
                        new.append([a0, b0])
                segs_h = new
            a('<g fill="none" stroke="%s" stroke-width="%s">' % (st, sw))
            for a0, b0 in segs_h:
                a('<line x1="%s" y1="%s" x2="%s" y2="%s"/>'
                  % (fmt(a0), fmt(y0), fmt(b0), fmt(y0)))
                a('<line x1="%s" y1="%s" x2="%s" y2="%s"/>'
                  % (fmt(a0), fmt(y1), fmt(b0), fmt(y1)))
            a('<line x1="%s" y1="%s" x2="%s" y2="%s"/>'
              % (fmt(x0), fmt(y0), fmt(x0), fmt(y1)))
            a('<line x1="%s" y1="%s" x2="%s" y2="%s"/>'
              % (fmt(x1), fmt(y0), fmt(x1), fmt(y1)))
            a('</g>')
        elif s["kind"] == "cylinder":
            pts = " ".join("%s,%s" % (fmt(x), fmt(y)) for x, y in
                           s.get("outline", []))
            a('<polygon points="%s" fill="%s" stroke="%s" '
              'stroke-width="%s"/>' % (pts, fl, st, sw))
            cap = max(3, s.get("cap_ry", 0))
            a('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="none" '
              'stroke="%s" stroke-width="%s"/>'
              % (fmt((x0 + x1) / 2.0), fmt(y0 + cap),
                 fmt((x1 - x0) / 2.0), fmt(cap), st, sw))
        elif s["kind"] == "ellipse":
            a('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" '
              'stroke="%s" stroke-width="%s"/>'
              % (fmt((x0 + x1) / 2.0), fmt((y0 + y1) / 2.0),
                 fmt((x1 - x0) / 2.0), fmt((y1 - y0) / 2.0), fl, st, sw))
        elif s["kind"] in ("rect", "rounded"):
            rx = s.get("radius", 0) if s["kind"] == "rounded" else 0
            a('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" '
              'fill="%s" stroke="%s" stroke-width="%s"/>'
              % (fmt(x0), fmt(y0), fmt(x1 - x0), fmt(y1 - y0), fmt(rx),
                 fl, st, sw))

    for d in dashes:
        st = "#808080"
        sw = 2
        for s in trace["shapes"]:
            if s["kind"] == "boundary":
                st = s.get("stroke", "#808080")
                sw = s.get("stroke_width", 2)
        if d["axis"] == "h":
            y, span0, span1 = d["y"], d["x0"], d["x1"]
            step = d["on"] + d["off"]
            x = span0
            while x <= span1:
                a('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" '
                  'stroke-width="%s"/>'
                  % (fmt(x), fmt(y), fmt(min(x + d["on"], span1)), fmt(y),
                     st, fmt(sw)))
                x += step
        else:
            x, span0, span1 = d["x"], d["y0"], d["y1"]
            step = d["on"] + d["off"]
            y = span0
            while y <= span1:
                a('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" '
                  'stroke-width="%s"/>'
                  % (fmt(x), fmt(y), fmt(x), fmt(min(y + d["on"], span1)),
                     st, fmt(sw)))
                y += step

    a('<g fill="none">')
    for ln in trace["lines"]:
        pts = " ".join("%s,%s" % (fmt(x), fmt(y)) for seg in ln["segs"]
                       for (x, y) in seg)
        a('<polyline points="%s" stroke="%s" stroke-width="%s"/>'
          % (pts, ln.get("color", "#000000"), fmt(ln.get("stroke", 2.5))))
    a('</g>')
    a('<g stroke="none">')
    for st_ in trace.get("sticks", []):
        sw_st = fmt(st_.get("stroke", 3))
        if st_.get("circle"):
            cx, cy, r = st_.get("circle")
            a('<circle cx="%s" cy="%s" r="%s" fill="none" stroke="#000000" '
              'stroke-width="%s"/>' % (fmt(cx), fmt(cy), fmt(r), sw_st))
        for seg in st_.get("limbs", []):
            a('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#000000" '
              'stroke-width="%s" fill="none"/>'
              % (fmt(seg[0][0]), fmt(seg[0][1]), fmt(seg[1][0]),
                 fmt(seg[1][1]), sw_st))
    for ln in trace["lines"]:
        if not ln.get("arrow_tip"):
            continue
        poly = arrow_polygon(tuple(ln["arrow_tip"]),
                             tuple(ln.get("arrow_from") or ln["segs"][-1][0]),
                             apex_back=2.0,
                             length=float(ln.get("arrow_len", 15.0)),
                             half=float(ln.get("arrow_half", 7.5)))
        pts = " ".join("%s,%s" % (fmt(x), fmt(y)) for x, y in poly)
        a('<polygon points="%s" fill="%s"/>'
          % (pts, ln.get("color", "#000000")))
    a('</g>')
    a('<g font-family="Arial, Helvetica, sans-serif">')
    for t in texts:
        fs = fmt(t["size"])               # half-point sizes kept exact
        fw = "bold" if t["weight"] == "bold" else "normal"
        ls_attr = ""
        if t.get("ls"):
            ls_attr = ' letter-spacing="%s"' % ("%.2f" % t["ls"])
        a('<text x="%s" y="%s" font-size="%s" font-weight="%s"%s '
          'fill="%s">%s</text>'
          % (t["x"], t["y"], fs, fw, ls_attr, t["ink"],
             saxutils.escape(t["content"])))
    a('</g>')
    a('</svg>')
    return "\n".join(p) + "\n"


# ------------------------------------------------------------------- drawio

def build_drawio(trace, dashes, texts):
    esc = saxutils.escape
    E = []
    a = E.append
    W, H = trace["canvas"]["w"], trace["canvas"]["h"]
    a('<mxfile host="dbcas-rebuild">')
    a('<diagram id="figure" name="Figure">')
    a('<mxGraphModel dx="%d" dy="%d" grid="1" gridSize="10" guides="1" '
      'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
      'pageWidth="%d" pageHeight="%d" math="0" shadow="0">'
      % (W, H, W, H))
    a('<root>')
    a('<mxCell id="0"/>')
    a('<mxCell id="1" parent="0"/>')

    def vertex(id_, value, style, x, y, w, h):
        a('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="1">'
          % (id_, esc(value), style))
        a('<mxGeometry x="%s" y="%s" width="%s" height="%s" as="geometry"/>'
          % (fmt(x), fmt(y), fmt(w), fmt(h)))
        a('</mxCell>')

    for i, s in enumerate(trace["shapes"]):
        x0, y0, x1, y1 = s.get("draw_bbox") or s["bbox"]
        st = ("strokeColor=%s;strokeWidth=%s;fillColor=%s;"
              % (s.get("stroke", "#000000"), s.get("stroke_width", 2),
                 s.get("fill", "#FFFFFF")))
        if s["kind"] == "boundary":
            st = "rounded=0;whiteSpace=wrap;html=1;" + st
            if s.get("dashed"):
                st += "dashed=1;"
            vertex("S%d" % (i + 1), "", st, x0, y0, x1 - x0, y1 - y0)
        elif s["kind"] == "cylinder":
            vertex("S%d" % (i + 1), "",
                   "shape=cylinder;whiteSpace=wrap;html=1;" + st +
                   "direction=north;",
                   x0, y0, x1 - x0, y1 - y0)
        elif s["kind"] == "ellipse":
            vertex("S%d" % (i + 1), "",
                   "ellipse;whiteSpace=wrap;html=1;" + st,
                   x0, y0, x1 - x0, y1 - y0)
        else:
            rx = s.get("radius", 0) if s["kind"] == "rounded" else 0
            vertex("S%d" % (i + 1), "",
                   "rounded=0;whiteSpace=wrap;html=1;" + st +
                   ("arcSize=%d;" % int(100.0 * rx / max(1, min(x1 - x0,
                                                                 y1 - y0) / 2))
                    if rx else ""),
                   x0, y0, x1 - x0, y1 - y0)

    for i, ln in enumerate(trace["lines"]):
        pts = [list(map(list, seg)) for seg in ln["segs"]]
        # the arrowhead must sit on the target end of the mx edge
        if ln.get("arrow_tip"):
            tip = tuple(ln["arrow_tip"])
            d_start = math.hypot(tip[0] - pts[0][0][0], tip[1] - pts[0][0][1])
            d_end = math.hypot(tip[0] - pts[-1][1][0],
                               tip[1] - pts[-1][1][1])
            if d_start < d_end:
                pts = [[seg[1], seg[0]] for seg in pts][::-1]
        es = ("edgeStyle=none;html=1;strokeColor=%s;strokeWidth=%s;"
              % (ln.get("color", "#000000"), fmt(ln.get("stroke", 2.5))))
        if ln.get("arrow_tip"):
            es += "endArrow=classic;endFill=1;endSize=11;"
        else:
            es += "endArrow=none;"
        a('<mxCell id="L%d" style="%s" edge="1" parent="1">'
          % (i + 1, es))
        a('<mxGeometry relative="1" as="geometry">')
        first, last = pts[0][0], pts[-1][1]
        a('<mxPoint x="%s" y="%s" as="sourcePoint"/>'
          % (fmt(first[0]), fmt(first[1])))
        a('<mxPoint x="%s" y="%s" as="targetPoint"/>'
          % (fmt(last[0]), fmt(last[1])))
        mids = [p for seg in pts[1:-1] for p in seg]
        if len(pts) > 1:
            inner = [seg[0] for seg in pts[:-1]]
            if inner:
                a('<Array as="points">')
                for (x, y) in inner:
                    a('<mxPoint x="%s" y="%s"/>' % (fmt(x), fmt(y)))
                a('</Array>')
        a('</mxGeometry>')
        a('</mxCell>')

    for t in texts:
        b = t["measured"]
        fw = 1 if t["weight"] == "bold" else 0
        a('<mxCell id="%s" value="%s" style="text;html=1;strokeColor=none;'
          'fillColor=none;align=left;verticalAlign=top;fontFamily=Arial;'
          'fontSize=%d;fontStyle=%d;whiteSpace=wrap;spacingLeft=0;'
          'spacingTop=0;" vertex="1" parent="1">'
          % (t["id"], esc(t["content"]), int(round(float(t["size"]))), fw))
        a('<mxGeometry x="%s" y="%s" width="%s" height="%s" as="geometry"/>'
          % (fmt(b[0]), fmt(b[1]), fmt(b[2] - b[0]), fmt(b[3] - b[1])))
        a('</mxCell>')
    a('</root>')
    a('</mxGraphModel>')
    a('</diagram>')
    a('</mxfile>')
    return "\n".join(E) + "\n"


# -------------------------------------------------------------------- main

def rendered_bbox(t):
    """Rendered ink box of an emitted SVG <text> - identical math to
    check_diagram_geometry.extract_texts (PIL Arial metrics from the
    emitted x / baseline-y / font-size / font-weight / letter-spacing)."""
    content = t["content"]
    x, y = float(t["x"]), float(t["y"])
    size = float(fmt(t["size"]))           # what the SVG attribute holds
    ls = float("%.2f" % (t.get("ls") or 0.0))   # what "%.2f" emits
    ix0, iy0, ix1, iy1 = ink(content, t["weight"], size)
    if ls and len(content) > 1:
        ix1 = ix1 + ls * (len(content) - 1)
    return (x + ix0, y + iy0, x + ix1, y + iy1)


def main():
    d = sys.argv[1]
    name = os.path.basename(os.path.normpath(d))
    trace = json.load(open(os.path.join(d, "trace.json"), encoding="utf-8"))
    cont = json.load(open(os.path.join(d, "text-content.json"),
                          encoding="utf-8"))
    plan = json.load(open(os.path.join(d, "font-plan.json"), encoding="utf-8"))
    calib_path = os.path.join(d, "letter-spacing.json")
    calib = (json.load(open(calib_path, encoding="utf-8"))
             if os.path.exists(calib_path) else {})
    by_id = {t["id"]: t for t in trace["texts"]}
    if cont.get("free_ids") and cont.get("box_ids"):
        pairs = ([(by_id[i], s) for i, s in
                  zip(cont["free_ids"], cont["free_texts"])] +
                 [(by_id[i], s) for i, s in
                  zip(cont["box_ids"], cont["box_texts"])])
    else:
        free = [t for t in trace["texts"] if t["inside"] is None]
        box = [t for t in trace["texts"] if t["inside"] is not None]
        assert len(free) == len(cont["free_texts"])
        assert len(box) == len(cont["box_texts"])
        pairs = ([(t, s) for t, s in zip(free, cont["free_texts"])] +
                 [(t, s) for t, s in zip(box, cont["box_texts"])])

    texts = []
    for t, s in pairs:
        pl = plan[t["id"]]
        x0, y0, x1, y1 = t["bbox"]
        iw, ih = pl["ink"]
        if pl["anchor"] == "bottom":
            m = [x0, y1 - ih, x0 + iw, y1]
        else:
            m = [x0, y0, x0 + iw, y0 + ih]
        tx, ty, _ = place_text(s, pl["weight"], pl["size"], m)
        # letter-spacing so the rendered ink width equals the measured band
        # width exactly: hinted widths jump in integer steps and the
        # original's font sits between two of them. letter-spacing.json
        # (from calibrate_letter_spacing.py) overrides the PIL estimate
        # with measurements taken from the real renderer.
        mw = t["bbox"][2] - t["bbox"][0]
        ls = (mw - iw) / float(max(1, len(s) - 1))
        if abs(ls) < 0.05:
            ls = 0.0
        ls = round(ls, 2)
        c = calib.get(t["id"])
        if c:
            ls = c.get("ls", ls)
            tx = c.get("x", tx)          # absolute x from the real renderer
        texts.append({"id": t["id"], "content": s, "weight": pl["weight"],
                      "size": pl["size"], "anchor": pl["anchor"],
                      "x": tx, "y": ty, "ink": t.get("ink", "#000000"),
                      "ls": ls,
                      "measured": t["bbox"], "inside": t["inside"]})

    # rule 8 - final line/text cut against the RENDERED text boxes
    # (font metrics + letter-spacing): exactly the boxes the checker
    # computes, so no segment can cross a label in the emitted SVG.
    boxes = [rendered_bbox(t) for t in texts]
    trace["lines"], n_cut = open_lines_at_texts(trace["lines"], boxes)
    if n_cut:
        print("rule-8 final cut: %d segment(s) opened at rendered text "
              "boxes" % n_cut)

    svg = build_svg(trace, trace.get("dashes", []), texts, name)
    with open(os.path.join(d, name + ".svg"), "w", encoding="utf-8") as f:
        f.write(svg)
    with open(os.path.join(d, name + ".drawio"), "w", encoding="utf-8") as f:
        f.write(build_drawio(trace, trace.get("dashes", []), texts))

    spec = {"canvas": trace["canvas"],
            "source": "trace.png pixel measurements + text-content.json "
                      "(strings read from original crops) + font-plan.json",
            "shapes": trace["shapes"],
            "dashes": trace.get("dashes", []),
            "lines": trace["lines"],
            "sticks": trace.get("sticks", []),
            "texts": texts,
            "style": {"font_family": "Arial, Helvetica, sans-serif",
                      "stroke": "#000000", "fill": "#FFFFFF"}}
    with open(os.path.join(d, "spec.json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=1)
    print("wrote %s.svg, %s.drawio, spec.json" % (name, name))
    print("shapes %d, lines %d, dashes %d, texts %d"
          % (len(trace["shapes"]), len(trace["lines"]),
             len(trace.get("dashes", [])), len(texts)))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Build the Chen ERD Stage A clone (SVG + drawio + spec + text-content)
from trace_erd_w3a.py measurements.

All geometry comes from trace.json (pixel measurements of the original
ArchitectureDesign_ver1.1_image8.png). No layout engine, no auto-placement.

Usage:
  node scripts/run_py.mjs scripts/build_erd_w3a.py <figure_dir> [--stage-b-spec spec.json]
"""
import json
import math
import os
import sys
import xml.sax.saxutils as saxutils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_fonts import ink  # noqa: E402

FONT = "Arial, Helvetica, sans-serif"
INK = "#1A1A1A"
LABEL_INK = "#222222"


def fmt(v):
    return ("%g" % round(float(v), 2))


def place(text, weight, size, measured):
    ix0, iy0, ix1, iy1 = ink(text, weight, size)
    x = measured[0] - ix0
    baseline = measured[3] - iy1
    return round(x, 2), round(baseline, 2), ix1 - ix0


STYLE_SIZES = {
    "entity": list(range(29, 35)),
    "diamond": list(range(17, 21)),
    "key": list(range(23, 28)),
    "card": list(range(24, 29)),
    "legend": list(range(24, 29)),
    "legend_key": [19, 20, 21],
}


def plan_text(t, idx):
    style = t.get("style", "legend")
    weight = "bold" if style in ("entity", "card") else "regular"
    m = t["bbox"]
    target_w = m[2] - m[0]
    best = None
    for size in STYLE_SIZES[style]:
        x, y, w = place(t["content"], weight, size, m)
        score = abs(w - target_w)
        if best is None or score < best[0]:
            best = (score, size, x, y, w)
    _, size, x, y, w = best
    ls = (target_w - w) / float(max(1, len(t["content"]) - 1))
    if abs(ls) < 0.05:
        ls = 0.0
    return {"id": "T%03d" % idx, "content": t["content"], "style": style,
            "weight": weight, "size": size, "x": x, "y": y,
            "ls": round(ls, 2), "measured": m,
            "italic": style == "diamond",
            "underline": style == "key"}


def build_svg(trace, texts, name):
    W, H = trace["canvas"]["w"], trace["canvas"]["h"]
    p = []
    a = p.append
    a('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
      'viewBox="0 0 %d %d">' % (W, H, W, H))
    a('<rect width="%d" height="%d" fill="#FFFFFF"/>' % (W, H))
    for s in trace["shapes"]:
        x0, y0, x1, y1 = s["bbox"]
        kind = s["kind"]
        if kind == "entity":
            a('<rect x="%s" y="%s" width="%s" height="%s" rx="0" '
              'fill="#FFFFFF" stroke="%s" stroke-width="4"/>'
              % (fmt(x0 + 2), fmt(y0 + 2), fmt(x1 - x0 - 4),
                 fmt(y1 - y0 - 4), INK))
        elif kind == "diamond":
            cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            pts = [(cx, y0 + 2.5), (x1 - 2.5, cy), (cx, y1 - 2.5),
                   (x0 + 2.5, cy)]
            a('<polygon points="%s" fill="#FFFFFF" stroke="%s" '
              'stroke-width="5"/>'
              % (" ".join("%s,%s" % (fmt(x), fmt(y)) for x, y in pts), INK))
        elif kind == "ellipse":
            cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            a('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="#FFFFFF" '
              'stroke="%s" stroke-width="4.5"/>'
              % (fmt(cx), fmt(cy), fmt((x1 - x0) / 2.0 - 2),
                 fmt((y1 - y0) / 2.0 - 2), INK))
        elif kind == "legend":
            a('<rect x="%s" y="%s" width="%s" height="%s" rx="26" '
              'fill="#FFFFFF" stroke="%s" stroke-width="3"/>'
              % (fmt(x0 + 1.5), fmt(y0 + 1.5), fmt(x1 - x0 - 3),
                 fmt(y1 - y0 - 3), INK))
        elif kind == "legend_rect":
            a('<rect x="%s" y="%s" width="%s" height="%s" fill="#FFFFFF" '
              'stroke="%s" stroke-width="4"/>'
              % (fmt(x0 + 2), fmt(y0 + 2), fmt(x1 - x0 - 4),
                 fmt(y1 - y0 - 4), INK))
        elif kind == "legend_diamond":
            cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            a('<polygon points="%s,%s %s,%s %s,%s %s,%s" fill="#FFFFFF" '
              'stroke="%s" stroke-width="4"/>'
              % (fmt(x0 + 2), fmt(cy), fmt(cx), fmt(y0 + 2),
                 fmt(x1 - 2), fmt(cy), fmt(cx), fmt(y1 - 2), INK))
        elif kind == "legend_key":
            cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            a('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="#FFFFFF" '
              'stroke="%s" stroke-width="3.5"/>'
              % (fmt(cx), fmt(cy), fmt((x1 - x0) / 2.0 - 1.5),
                 fmt((y1 - y0) / 2.0 - 1.5), INK))

    a('<g fill="none" stroke-linecap="butt">')
    for ln in trace["lines"]:
        for (ax, ay), (bx, by) in zip(ln["segs"], ln["segs"][1:]):
            a('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" '
              'stroke-width="4"/>'
              % (fmt(ax), fmt(ay), fmt(bx), fmt(by), ln.get("color", INK)))
    # key underlines (the original underlines every key-attribute label)
    for t in texts:
        if t["underline"]:
            x0, y0, x1, y1 = t["measured"]
            a('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" '
              'stroke-width="2"/>'
              % (fmt(x0), fmt(y1 + 3), fmt(x1), fmt(y1 + 3), LABEL_INK))
    a('</g>')
    a('<g font-family="%s">' % FONT)
    for t in texts:
        extra = ""
        if t["italic"]:
            extra += ' font-style="italic"'
        if t.get("ls"):
            extra += ' letter-spacing="%s"' % ("%.2f" % t["ls"])
        a('<text x="%s" y="%s" font-size="%s" font-weight="%s"%s '
          'fill="%s">%s</text>'
          % (t["x"], t["y"], t["size"], t["weight"], extra, LABEL_INK,
             saxutils.escape(t["content"])))
    a('</g>')
    a('</svg>')
    return "\n".join(p) + "\n"


def build_drawio(trace, texts):
    esc = saxutils.escape
    E = []
    a = E.append
    W, H = trace["canvas"]["w"], trace["canvas"]["h"]
    a('<mxfile host="dbcas-rebuild">')
    a('<diagram id="figure" name="ERD">')
    a('<mxGraphModel dx="%d" dy="%d" grid="1" gridSize="10" guides="1" '
      'tooltips="1" connect="1" arrows="0" fold="1" page="1" pageScale="1" '
      'pageWidth="%d" pageHeight="%d" math="0" shadow="0">'
      % (W, H, W, H))
    a('<root>')
    a('<mxCell id="0"/>')
    a('<mxCell id="1" parent="0"/>')

    def vertex(id_, value, style, x, y, w_, h_):
        a('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="1">'
          % (id_, esc(value), style))
        a('<mxGeometry x="%s" y="%s" width="%s" height="%s" as="geometry"/>'
          % (fmt(x), fmt(y), fmt(w_), fmt(h_)))
        a('</mxCell>')

    for i, s in enumerate(trace["shapes"]):
        x0, y0, x1, y1 = s["bbox"]
        kind = s["kind"]
        base = "whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=%s;" % INK
        if kind == "entity":
            vertex("S%03d" % (i + 1), "", "rounded=0;" + base +
                   "strokeWidth=4;", x0, y0, x1 - x0, y1 - y0)
        elif kind == "diamond":
            vertex("S%03d" % (i + 1), "", "rhombus;" + base +
                   "strokeWidth=5;", x0, y0, x1 - x0, y1 - y0)
        elif kind == "ellipse":
            vertex("S%03d" % (i + 1), "", "ellipse;" + base +
                   "strokeWidth=4.5;", x0, y0, x1 - x0, y1 - y0)
        elif kind == "legend":
            vertex("S%03d" % (i + 1), "", "rounded=1;arcSize=8;" + base +
                   "strokeWidth=3;", x0, y0, x1 - x0, y1 - y0)
        elif kind == "legend_rect":
            vertex("S%03d" % (i + 1), "", "rounded=0;" + base +
                   "strokeWidth=4;", x0, y0, x1 - x0, y1 - y0)
        elif kind == "legend_diamond":
            vertex("S%03d" % (i + 1), "", "rhombus;" + base +
                   "strokeWidth=4;", x0, y0, x1 - x0, y1 - y0)
        elif kind == "legend_key":
            vertex("S%03d" % (i + 1), "", "ellipse;" + base +
                   "strokeWidth=3.5;", x0, y0, x1 - x0, y1 - y0)

    for i, ln in enumerate(trace["lines"]):
        (ax, ay), (bx, by) = ln["segs"][0], ln["segs"][-1]
        a('<mxCell id="L%03d" style="edgeStyle=none;html=1;endArrow=none;'
          'strokeColor=%s;strokeWidth=4;" edge="1" parent="1">'
          % (i + 1, ln.get("color", INK)))
        a('<mxGeometry relative="1" as="geometry">')
        a('<mxPoint x="%s" y="%s" as="sourcePoint"/>' % (fmt(ax), fmt(ay)))
        a('<mxPoint x="%s" y="%s" as="targetPoint"/>' % (fmt(bx), fmt(by)))
        a('</mxGeometry></mxCell>')

    for t in texts:
        b = t["measured"]
        fw = 1 if t["weight"] == "bold" else 0
        fs = 2 if t["italic"] else 0
        a('<mxCell id="%s" value="%s" style="text;html=1;strokeColor=none;'
          'fillColor=none;align=left;verticalAlign=top;fontFamily=Arial;'
          'fontSize=%d;fontStyle=%d;whiteSpace=wrap;spacingLeft=0;'
          'spacingTop=0;" vertex="1" parent="1">'
          % (t["id"], esc(t["content"]), int(t["size"]), fw + fs))
        a('<mxGeometry x="%s" y="%s" width="%s" height="%s" as="geometry"/>'
          % (fmt(b[0]), fmt(b[1]), fmt(b[2] - b[0]), fmt(b[3] - b[1])))
        a('</mxCell>')
    a('</root></mxGraphModel></diagram></mxfile>')
    return "\n".join(E) + "\n"


def main():
    d = os.path.abspath(sys.argv[1])
    name = os.path.basename(os.path.normpath(d))
    trace_path = os.path.join(d, "trace.json")
    trace = json.load(open(trace_path, encoding="utf-8"))
    texts = [plan_text(t, i + 1) for i, t in enumerate(trace["texts"])]

    svg = build_svg(trace, texts, name)
    with open(os.path.join(d, name + ".svg"), "w", encoding="utf-8") as f:
        f.write(svg)
    with open(os.path.join(d, name + ".drawio"), "w", encoding="utf-8") as f:
        f.write(build_drawio(trace, texts))

    cont = {"free_texts": [t["content"] for t in texts
                           if t["style"] in ("diamond", "card", "legend",
                                             "legend_key")],
            "box_texts": [t["content"] for t in texts
                          if t["style"] == "entity"],
            "ellipse_texts": [t["content"] for t in texts
                              if t["style"] == "key"]}
    with open(os.path.join(d, "text-content.json"), "w", encoding="utf-8") as f:
        json.dump(cont, f, indent=1)

    spec = {"canvas": trace["canvas"],
            "source": "trace_erd_w3a.py pixel measurements + Arial calibration",
            "shapes": trace["shapes"], "lines": trace["lines"],
            "texts": texts,
            "style": {"font_family": FONT, "stroke": INK,
                      "fill": "#FFFFFF"}}
    with open(os.path.join(d, "spec.json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=1)

    print("wrote %s.svg, %s.drawio, spec.json, text-content.json" % (name, name))
    print("shapes %d, lines %d, texts %d (free %d / box %d / ellipse %d)"
          % (len(trace["shapes"]), len(trace["lines"]), len(texts),
             len(cont["free_texts"]), len(cont["box_texts"]),
             len(cont["ellipse_texts"])))


if __name__ == "__main__":
    main()

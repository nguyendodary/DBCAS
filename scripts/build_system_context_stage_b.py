# -*- coding: utf-8 -*-
"""Apply the owner-approved Stage B content delta to the System Context clone.

Reads the Stage A outputs (spec.json + text-content.json) from <out_dir>,
applies ONLY the content delta and rewrites the four deliverables
(spec.json, text-content.json, system-context.svg, system-context.drawio).

Delta (nothing else moves, resizes, merges or restyles):
  1. "Assessment requests"      -> "Practice requests"
  2. "Assessment configuration" -> "Result flow & settings"
  3. two actor-style boxes bottom right: "OAuth Providers", "Email Service"
     (same style as the original boxes: stroke 2, white fill, bold centred
     label; new label size 30 >= original box labels 29/29/30)
  4. three orthogonal flows with arrowheads at the target end:
       DBCAS -> OAuth Providers : "OAuth sign-in request"
       OAuth Providers -> DBCAS : "Identity assertion"
       DBCAS -> Email Service   : "Password-reset email"
     flow labels regular 18 px, same as the 21 original flow labels.

Canvas stays 1431 x 1061 (all new geometry fits in the free bottom-right
space); every existing element keeps its exact coordinates.

Usage:
  node scripts/run_py.mjs scripts/build_system_context_stage_b.py \
      docs/diagrams/rebuild/system-context
"""
import json
import os
import sys
import xml.sax.saxutils as saxutils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_system_context import (  # noqa: E402  (shared Stage A helpers)
    arrow_polygon, place_text, write_svg,
)
from calibrate_fonts import ink  # noqa: E402

# ------------------------------------------------------------------ delta

RENAMES = {"T02": "Practice requests", "T08": "Result flow & settings"}

BOXES = [
    {"name": "OAuth Providers", "rect": [1020.0, 640.0, 300.0, 95.0]},
    {"name": "Email Service", "rect": [1020.0, 830.0, 300.0, 95.0]},
]
BOX_LABEL_SIZE = 30          # >= original box labels (29 / 29 / 30)

# Arc endpoints lie on the Stage A ellipse (cx 715.5, cy 468.5, rx 209.5,
# ry 129.5): x = cx + rx*sqrt(1-((y-cy)/ry)^2).
FLOWS = [
    {"id": "F22", "label": "OAuth sign-in request",
     "points": [[892.3, 538.0], [1170.0, 538.0], [1170.0, 640.0]],
     "arrow_at": "end", "tip": [1170.0, 640.0],
     "label_center": 1031.15, "label_top": 544.0},
    {"id": "F23", "label": "Identity assertion",
     "points": [[1080.0, 640.0], [1080.0, 569.0], [847.6, 569.0]],
     "arrow_at": "end", "tip": [847.6, 569.0],
     "label_center": 963.8, "label_top": 576.0},
    {"id": "F24", "label": "Password-reset email",
     "points": [[915.5, 507.0], [1350.0, 507.0], [1350.0, 782.5],
                [1170.0, 782.5], [1170.0, 830.0]],
     "arrow_at": "end", "tip": [1170.0, 830.0],
     "label_center": 1132.75, "label_top": 513.0},
]
FLOW_LABEL_SIZE = 18         # same as the original flow labels


# ------------------------------------------------------------------ drawio

def write_drawio(path, shapes, ell, icons, flows, arrows, texts, box_labels):
    """mxGraph XML, identical format to the Stage A writer; the two new
    boxes carry bold 30 px centred labels like the actor boxes."""
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
    sizes = {0: 29, 1: 29, 2: 30, 4: BOX_LABEL_SIZE, 5: BOX_LABEL_SIZE}
    for i, r in enumerate(shapes):
        if i in sizes:
            st = box_style + "fontSize=%d;" % sizes[i]
            val = box_labels[i]
        else:
            st = ("rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;"
                  "strokeColor=#000000;strokeWidth=2;")
            val = ""
        vertex("R%d" % (i + 1), val, st, r["x"], r["y"], r["w"], r["h"])

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

    for i, fl in enumerate(flows):
        pts = fl["points"]
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


# ------------------------------------------------------------------ main

def main():
    out_dir = sys.argv[1]
    spec = json.load(open(os.path.join(out_dir, "spec.json"), encoding="utf-8"))
    cont = json.load(open(os.path.join(out_dir, "text-content.json"),
                          encoding="utf-8"))

    texts = spec["texts"]

    # ---- 1/2: rename two flow labels, keep their ink top-left anchor
    for t in texts:
        if t["id"] in RENAMES:
            new = RENAMES[t["id"]]
            x0, y0 = t["measured"][0], t["measured"][1]
            ix0, iy0, ix1, iy1 = ink(new, t["weight"], t["size"])
            m = [x0, y0, x0 + (ix1 - ix0), y0 + (iy1 - iy0)]
            x, y, _ = place_text(new, t["weight"], t["size"], m)
            t["content"], t["x"], t["y"] = new, x, y
            t["measured"] = [round(v, 1) for v in m]

    # ---- 3: two actor-style boxes + centred bold labels
    shapes = []
    for r in spec["rects"]:
        x, y, w, h = r["stroke_rect"]
        shapes.append({"x": x, "y": y, "w": w, "h": h})
    box_labels = [t["content"] for t in texts
                  if t["id"] in ("B00", "B01", "B02")] + [""]
    for i, b in enumerate(BOXES):
        x, y, w, h = b["rect"]
        shapes.append({"x": x, "y": y, "w": w, "h": h})
        box_labels.append(b["name"])
        cx, cy = x + w / 2.0, y + h / 2.0
        ix0, iy0, ix1, iy1 = ink(b["name"], "bold", BOX_LABEL_SIZE)
        m = [cx - (ix1 - ix0) / 2.0, cy - (iy1 - iy0) / 2.0,
             cx + (ix1 - ix0) / 2.0, cy + (iy1 - iy0) / 2.0]
        tx, ty, _ = place_text(b["name"], "bold", BOX_LABEL_SIZE, m)
        texts.insert(len(texts) - 1,  # before the ellipse label
                     {"id": "B%02d" % (6 + i), "kind": "box_label",
                      "content": b["name"], "weight": "bold",
                      "size": BOX_LABEL_SIZE, "x": tx, "y": ty,
                      "measured": [round(v, 1) for v in m]})

    # ---- 4: three flows + arrow polygons + individually placed labels
    flows = list(spec["flows"])
    arrows = [{"flow": i, "tip": f["arrow_tip"], "poly": f["arrow_poly"]}
              for i, f in enumerate(flows)]
    for i, f in enumerate(FLOWS):
        pts = [tuple(p) for p in f["points"]]
        poly = arrow_polygon(tuple(f["tip"]), pts[-2])
        flows.append({"id": f["id"], "points": [list(p) for p in pts],
                      "arrow_at": f["arrow_at"], "arrow_tip": list(f["tip"]),
                      "arrow_poly": poly})
        arrows.append({"flow": len(flows) - 1, "tip": list(f["tip"]),
                       "poly": poly})
        ix0, iy0, ix1, iy1 = ink(f["label"], "regular", FLOW_LABEL_SIZE)
        w_, h_ = ix1 - ix0, iy1 - iy0
        m = [f["label_center"] - w_ / 2.0, f["label_top"],
             f["label_center"] + w_ / 2.0, f["label_top"] + h_]
        tx, ty, _ = place_text(f["label"], "regular", FLOW_LABEL_SIZE, m)
        at = next(j for j, t in enumerate(texts) if t["id"] == "B00")
        texts.insert(at,
                     {"id": "T%02d" % (22 + i), "kind": "flow_label",
                      "content": f["label"], "weight": "regular",
                      "size": FLOW_LABEL_SIZE, "x": tx, "y": ty,
                      "measured": [round(v, 1) for v in m]})

    ell = spec["ellipse"]
    icons = spec["legend_icons"]

    # ---- outputs
    svg_path = os.path.join(out_dir, "system-context.svg")
    drawio_path = os.path.join(out_dir, "system-context.drawio")
    spec_path = os.path.join(out_dir, "spec.json")
    cont_path = os.path.join(out_dir, "text-content.json")

    write_svg(svg_path, shapes, ell, icons, flows, arrows, texts)
    write_drawio(drawio_path, shapes, ell, icons, flows, arrows, texts,
                 box_labels)

    new_spec = dict(spec)
    new_spec["source"] = ("Stage A spec (trace.json + text-content.json + "
                          "pixel-sampled stroke centers) + Stage B content "
                          "delta")
    new_spec["stage_b_delta"] = {
        "renamed": [{"id": k, "to": v} for k, v in sorted(RENAMES.items())],
        "added_rects": [b["name"] for b in BOXES],
        "added_flows": [{"id": f["id"], "label": f["label"]} for f in FLOWS],
    }
    # keep Stage A order: the original four rects first, then the new boxes
    new_spec["rects"] = ([r for r in spec["rects"]] +
                         [{"name": b["name"], "stroke_rect": b["rect"],
                           "stroke_width": 2} for b in BOXES])
    new_spec["flows"] = flows
    new_spec["texts"] = texts
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(new_spec, f, indent=1)

    # ---- text-content.json: the checker's expected label list
    ft = [RENAMES.get("T%02d" % i, s) if i in (2, 8) else s
          for i, s in enumerate(cont["free_texts"])]
    ft += [f["label"] for f in FLOWS]
    bt = list(cont["box_texts"]) + [b["name"] for b in BOXES]
    fl = dict(cont["flow_label_to_flow"])
    fl["T02->F01"] = RENAMES["T02"]
    fl["T08->F08"] = RENAMES["T08"]
    for i, f in enumerate(FLOWS):
        fl["T%02d->%s" % (22 + i, f["id"])] = f["label"]
    new_cont = {
        "note": ("Text content read visually from "
                 "ProposalDocument_ver1.1_image3.png crops, plus the owner-"
                 "approved Stage B delta (two renamed labels, two new boxes, "
                 "three new flow labels). free_texts order matches spec.json "
                 "for T00..T24, box_texts for B00..B07."),
        "free_texts": ft,
        "box_texts": bt,
        "ellipse_texts": list(cont["ellipse_texts"]),
        "flow_label_to_flow": fl,
    }
    with open(cont_path, "w", encoding="utf-8") as f:
        json.dump(new_cont, f, indent=1, ensure_ascii=False)

    print("wrote", svg_path)
    print("wrote", drawio_path)
    print("wrote", spec_path)
    print("wrote", cont_path)
    print("rects:", len(shapes), "flows:", len(flows),
          "arrows:", len(arrows), "texts:", len(texts))
    for t in texts:
        if t["id"] in RENAMES or t["id"] in ("T22", "T23", "T24",
                                             "B06", "B07"):
            print(" ", t["id"], t["content"], t["measured"], "size",
                  t["size"], t["weight"])


if __name__ == "__main__":
    main()

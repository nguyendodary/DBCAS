# -*- coding: utf-8 -*-
"""W2b Component Stage A: finish the tracer output for Architecture Fig 4.

The generic tracer measures all 26 boxes and 133 text bands, but the three
dashed system boundaries are not emitted (two verticals are shorter than the
dash-cluster minimum span), several lines are split at boundary crossings,
and the SQL Sandbox cylinder is classified as a rounded rect.  All values
below come from the PNG: dash spans/on-off from row/column runs, line
endpoints from the tracer's own segments plus row/column scans recorded in
the report.

Usage:
  node scripts/run_py.mjs scripts/supplement_component_w2b.py \
      docs/qa/diagram-originals/ArchitectureDesign_ver1.1_image5.png \
      docs/diagrams/rebuild/component/trace.json
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trace_figure import fill_mask_of, silhouette  # noqa: E402

LINE = "#333333"
SW = 3.0


def main():
    src, trace_path = sys.argv[1], sys.argv[2]
    rgb = np.array(Image.open(src).convert("RGB"))
    t = json.load(open(trace_path, encoding="utf-8"))

    # ---- boundaries (measured dashed rectangles)
    boundaries = [
        {"id": "S27", "kind": "boundary", "bbox": [60, 60, 2300, 305],
         "fill": "#FFFFFF", "stroke": "#666666", "stroke_width": 2,
         "radius": 0, "dashed": True, "dash_on": 14, "dash_off": 15},
        {"id": "S28", "kind": "boundary", "bbox": [145, 360, 2215, 622],
         "fill": "#FFFFFF", "stroke": "#666666", "stroke_width": 2,
         "radius": 0, "dashed": True, "dash_on": 14, "dash_off": 15},
        {"id": "S29", "kind": "boundary", "bbox": [145, 679, 2262, 941],
         "fill": "#FFFFFF", "stroke": "#666666", "stroke_width": 2,
         "radius": 0, "dashed": True, "dash_on": 14, "dash_off": 15},
    ]
    t["shapes"] = boundaries + [s for s in t["shapes"]
                                if s["kind"] != "boundary"]

    # ---- SQL Sandbox: a real cylinder (tracer saw a rounded rect)
    for s in t["shapes"]:
        if s["id"] == "S25":
            s["kind"] = "cylinder"
            s["cap_ry"] = 9
            s["radius"] = 0
            m = fill_mask_of(rgb, s.get("draw_bbox") or s["bbox"], s["fill"])
            s["outline"] = silhouette(m, step=2, ox=s["bbox"][0],
                                      oy=s["bbox"][1])

    # ---- dash runs: four sides per boundary (spans measured)
    def h(y, x0, x1):
        return {"axis": "h", "y": y, "x0": x0, "x1": x1,
                "dashes": int((x1 - x0) // 29) + 1, "on": 14, "off": 15}

    def v(x, y0, y1):
        return {"axis": "v", "x": x, "y0": y0, "y1": y1,
                "dashes": int((y1 - y0) // 29) + 1, "on": 14, "off": 15}

    t["dashes"] = [
        h(60, 73, 2296), h(304, 60, 2300),
        v(60, 64, 305), v(2299, 73, 305),
        h(360, 145, 2215), h(622, 145, 2200),
        v(145, 360, 622), v(2215, 360, 622),
        h(679, 145, 2249), h(941, 145, 2262),
        v(145, 679, 941), v(2262, 682, 942),
    ]

    # ---- lines: 24 measured flows (7 + 7 + 7 + cache + provider + sandbox)
    # id, points, tip
    specs = [
        ("L01", [(238.0, 285.1), (289.0, 460.0)], (289.0, 460.0)),
        ("L02", [(552.9, 284.8), (585.0, 450.0)], (585.0, 450.0)),
        ("L03", [(865.5, 284.9), (884.0, 450.0)], (884.0, 450.0)),
        ("L04", [(1180.0, 282.0), (1180.0, 441.0)], (1180.0, 441.0)),
        ("L05", [(1494.0, 282.0), (1479.0, 441.0)], (1479.0, 441.0)),
        ("L06", [(1808.9, 285.0), (1778.0, 431.0)], (1778.0, 431.0)),
        ("L07", [(2122.0, 282.0), (2081.0, 431.0)], (2081.0, 431.0)),
        ("L08", [(302.0, 570.0), (304.0, 769.0)], (304.0, 769.0)),
        ("L09", [(595.0, 579.0), (598.0, 769.0)], (598.0, 769.0)),
        ("L10", [(888.0, 580.0), (885.0, 769.0)], (885.0, 769.0)),
        ("L11", [(1181.0, 589.0), (1182.0, 750.0)], (1182.0, 750.0)),
        ("L12", [(1473.0, 589.0), (1470.0, 778.0)], (1470.0, 778.0)),
        ("L13", [(1765.0, 599.0), (1763.0, 769.0)], (1763.0, 769.0)),
        ("L14", [(2064.0, 599.0), (2081.0, 778.0)], (2081.0, 778.0)),
        ("L15", [(381.0, 906.0), (932.0, 1049.0)], (932.0, 1049.0)),
        ("L16", [(679.0, 905.0), (994.0, 1044.0)], (994.0, 1044.0)),
        ("L17", [(963.0, 904.0), (1119.0, 1040.0)], (1119.0, 1040.0)),
        ("L18", [(1181.0, 923.0), (1178.0, 1040.0)], (1178.0, 1040.0)),
        ("L19", [(1407.0, 894.0), (1241.0, 1040.0)], (1241.0, 1040.0)),
        ("L20", [(2001.0, 895.0), (1432.0, 1041.0)], (1432.0, 1041.0)),
        ("L21", [(1681.0, 904.0), (1367.0, 1044.0)], (1367.0, 1044.0)),
        ("L22", [(837.0, 1102.0), (927.0, 1102.0)], (927.0, 1102.0)),
        ("L23", [(613.0, 1153.0), (614.0, 1290.0)], (614.0, 1290.0)),
        ("L24", [(1685.5, 1153.0), (1685.5, 1294.0)], (1685.5, 1294.0)),
    ]
    lines = []
    for lid, pts, tip in specs:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        segs = [[list(map(float, a)), list(map(float, b))]
                for a, b in zip(pts, pts[1:])]
        lines.append({
            "id": lid,
            "bbox": [int(min(xs)), int(min(ys)), int(max(xs)) + 1,
                     int(max(ys)) + 1],
            "segs": segs, "thickness": SW, "color": LINE, "stroke": SW,
            "arrow_tip": [tip[0], tip[1]],
            "arrow_from": [float(pts[-2][0]), float(pts[-2][1])],
        })
    t["lines"] = lines
    t["arrows"] = [{"line": i, "tip": l["arrow_tip"],
                    "from": l["arrow_from"], "widths": []}
                   for i, l in enumerate(lines)]

    json.dump(t, open(trace_path, "w", encoding="utf-8"), indent=1)

    # ---- verification markers
    im = Image.open(src).convert("RGB")
    dr = ImageDraw.Draw(im)
    for s in t["shapes"]:
        x0, y0, x1, y1 = s["bbox"]
        col = (0, 0, 255) if s["kind"] == "boundary" else (0, 150, 0)
        dr.rectangle([x0, y0, x1 - 1, y1 - 1], outline=col, width=2)
    for l in t["lines"]:
        for a, b in l["segs"]:
            dr.line([tuple(a), tuple(b)], fill=(255, 0, 0), width=2)
        tx, ty = l["arrow_tip"]
        dr.ellipse([tx - 6, ty - 6, tx + 6, ty + 6], outline=(0, 0, 255),
                   width=2)
    for d in t["dashes"]:
        if d["axis"] == "h":
            dr.line([(d["x0"], d["y"]), (d["x1"], d["y"])],
                    fill=(0, 160, 255), width=1)
        else:
            dr.line([(d["x"], d["y0"]), (d["x"], d["y1"])],
                    fill=(0, 160, 255), width=1)
    for x in t["texts"]:
        dr.rectangle(x["bbox"], outline=(255, 0, 255), width=1)
    mk = os.path.splitext(trace_path)[0] + "_markers.png"
    im.save(mk)
    print("wrote", trace_path, "and", mk)
    print("shapes", len(t["shapes"]), "lines", len(t["lines"]),
          "dashes", len(t["dashes"]), "texts", len(t["texts"]))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""W2b Pipeline Stage A: finish the tracer output for Proposal Fig 4.

The generic tracer measures the 8 boxes and all 35 text bands, but this
figure's short arrows are fused to the box border strokes (so they never
form their own component), its dashed boundary is a stepped/open outline,
and the boxes have 10 px rounded corners that the fill-only classifier
reports as sharp rects.  Everything here is still measured from the PNG:
the arrow endpoints below were read from the pixel runs with
scripts/crop_w2b.py crops + row/column scans recorded in the report.

Usage:
  node scripts/run_py.mjs scripts/supplement_pipeline_w2b.py \
      docs/qa/diagram-originals/ProposalDocument_ver1.1_image5.png \
      docs/diagrams/rebuild/pipeline/trace.json
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trace_figure import fill_mask_of, silhouette  # noqa: E402

RADIUS = 9
LINE = "#34383B"
SW = 2.0


def main():
    src, trace_path = sys.argv[1], sys.argv[2]
    rgb = np.array(Image.open(src).convert("RGB"))
    t = json.load(open(trace_path, encoding="utf-8"))
    canvas = t["canvas"]

    # ---- shapes: rounded boxes drawn on the measured stroke centreline
    for s in t["shapes"]:
        if s["kind"] == "boundary":
            s["bbox"] = [10, 107, 1322, 614]
            s["stroke"] = "#5E6163"
            s["stroke_width"] = 2
            # stepped OPEN outline (the top-right is outside the boundary in
            # the original): five measured polylines, drawn dashed
            s["paths"] = [
                [[10, 107], [407, 107]],
                [[10, 107], [10, 614]],
                [[10, 614], [1322, 614]],
                [[1322, 298], [1322, 614]],
                [[1195, 294.5], [1322, 294.5]],
            ]
            continue
        x0, y0, x1, y1 = s["bbox"]
        s["bbox"] = [x0 - 1.5, y0 - 1.5, x1 + 0.5, y1 + 0.5]
        s["kind"] = "rounded"
        s["radius"] = RADIUS
        s["stroke_width"] = 2

    # ---- lines: 8 arrows, all read from pixel runs
    # (id, [(x,y), ...], tip, label)
    specs = [
        ("L01", [(261.0, 200.5), (289.5, 200.5)], (290.0, 200.5),
         "Opening -> Grade each answer"),
        ("L02", [(525.0, 200.5), (552.5, 200.5)], (553.0, 200.5),
         "Grade each answer -> Evidence"),
        ("L03", [(786.0, 200.5), (814.5, 200.5)], (815.0, 200.5),
         "Evidence -> Adaptive selection"),
        ("L04", [(1049.0, 200.5), (1077.5, 200.5)], (1078.0, 200.5),
         "Adaptive selection -> Next item"),
        ("L05", [(1195.5, 267.5), (1195.5, 437.5)], (1195.5, 438.5),
         "Next item -> Complete assessment"),
        ("L06", [(670.5, 438.5), (670.5, 384.5), (932.5, 384.5),
                 (932.5, 268.0)], (932.5, 267.5),
         "Validated item bank -> Adaptive selection (feedback)"),
        ("L07", [(369.0, 514.0), (510.0, 514.0)], (510.5, 514.0),
         "Candidate preparation -> Validated item bank"),
        ("L08", [(406.5, 107.0), (406.5, 131.0)], (406.5, 131.5),
         "entry flow from live evidence"),
    ]
    lines = []
    for lid, pts, tip, note in specs:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        segs = [[list(map(float, a)), list(map(float, b))]
                for a, b in zip(pts, pts[1:])]
        lines.append({
            "id": lid,
            "bbox": [int(min(xs)), int(min(ys)), int(max(xs)) + 1,
                     int(max(ys)) + 1],
            "segs": segs, "thickness": 3.0, "color": LINE, "stroke": SW,
            "arrow_tip": [tip[0], tip[1]],
            "arrow_from": [float(pts[-2][0]), float(pts[-2][1])],
            "note": note,
        })
    # the entry arrow starts ON the dashed top border (the original has only
    # a short 107..114 tick plus the head); keep the measured run.
    t["lines"] = lines
    t["arrows"] = [{"line": i, "tip": l["arrow_tip"],
                    "from": l["arrow_from"], "widths": []}
                   for i, l in enumerate(lines)]

    # ---- dashed boundary runs (measured spans / on-off from row scans)
    t["dashes"] = [
        {"axis": "h", "y": 107, "x0": 10, "x1": 401, "dashes": 33,
         "on": 7, "off": 5},
        {"axis": "v", "x": 10, "y0": 107, "y1": 615, "dashes": 43,
         "on": 7, "off": 5},
        {"axis": "h", "y": 614, "x0": 10, "x1": 508, "dashes": 46,
         "on": 6, "off": 5},
        {"axis": "h", "y": 614, "x0": 850, "x1": 1323, "dashes": 44,
         "on": 6, "off": 5},
        {"axis": "v", "x": 1322, "y0": 298, "y1": 615, "dashes": 27,
         "on": 6, "off": 6},
        {"axis": "h", "y": 294, "x0": 1195, "x1": 1322, "dashes": 11,
         "on": 6, "off": 6},
    ]
    # NOTE: the bottom run is split around the footer label that sits on
    # the dashed line in the original (text 522..842, measured); the real
    # PNG also shows the dashes interrupted there.

    # ---- cylinder check: none in this figure
    json.dump(t, open(trace_path, "w", encoding="utf-8"), indent=1)

    # ---- verification markers on a copy of the original
    im = Image.open(src).convert("RGB")
    dr = ImageDraw.Draw(im)
    for s in t["shapes"]:
        x0, y0, x1, y1 = s["bbox"]
        col = (0, 0, 255) if s["kind"] == "boundary" else (0, 150, 0)
        dr.rectangle([x0, y0, x1 - 1, y1 - 1], outline=col, width=2)
        if s["kind"] == "rounded":
            dr.rounded_rectangle([x0, y0, x1 - 1, y1 - 1],
                                 radius=s.get("radius", 0), outline=col,
                                 width=1)
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

# -*- coding: utf-8 -*-
"""F4 owner-fix build helpers (pipeline + two-page component split).

Reuses the Stage B SVG/drawio emitters, but takes an explicit element list
instead of a pixel trace, so the fix round can move/resize a small, declared
set of elements and prove every other element stayed identical.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_figure_w2b import build_drawio, build_svg  # noqa: E402
from calibrate_fonts import ink  # noqa: E402
from trace_figure import open_lines_at_texts  # noqa: E402


def fmt(v):
    return ("%g" % round(float(v), 1))


def rendered_bbox(t):
    x, y = float(t["x"]), float(t["y"])
    size = float(fmt(t["size"]))
    ls = float("%.2f" % (t.get("ls") or 0.0))
    ix0, iy0, ix1, iy1 = ink(t["content"], t["weight"], size)
    if ls and len(t["content"]) > 1:
        ix1 = ix1 + ls * (len(t["content"]) - 1)
    return (x + ix0, y + iy0, x + ix1, y + iy1)


def text_left_for_ink(content, weight, size, target_left, ls=0.0):
    """Pen x so the rendered ink starts at target_left."""
    ix0, _, _, _ = ink(content, weight, size)
    return target_left - ix0


def text_center_for_ink(content, weight, size, center, ls=0.0):
    ix0, _, ix1, _ = ink(content, weight, size)
    if ls and len(content) > 1:
        ix1 += ls * (len(content) - 1)
    return center - (ix0 + ix1) / 2.0


def text_top_baseline(content, weight, size, top):
    """Baseline y so the rendered ink top is at `top`."""
    _, iy0, _, _ = ink(content, weight, size)
    return top - iy0


def translate_shape(s, dx=0.0, dy=0.0):
    out = json.loads(json.dumps(s))
    out["bbox"] = [round(s["bbox"][0] + dx, 1), round(s["bbox"][1] + dy, 1),
                   round(s["bbox"][2] + dx, 1), round(s["bbox"][3] + dy, 1)]
    if "outline" in out:
        out["outline"] = [[round(x + dx, 1), round(y + dy, 1)]
                          for x, y in s["outline"]]
    return out


def translate_text(t, dx=0.0, dy=0.0):
    out = json.loads(json.dumps(t))
    out["x"] = round(t["x"] + dx, 1)
    out["y"] = round(t["y"] + dy, 1)
    if t.get("measured"):
        out["measured"] = [round(v + (dx if i % 2 == 0 else dy), 1)
                           for i, v in enumerate(t["measured"])]
    return out


def specs_from_texts(texts, shapes):
    """measured bboxes from the emitted text geometry (documentation only)."""
    by_shape = {s["id"]: s["bbox"] for s in shapes}
    for t in texts:
        b = rendered_bbox(t)
        t["measured"] = [round(v, 1) for v in b]
        if t.get("inside") in by_shape:
            sb = by_shape[t["inside"]]
            assert sb[0] - 2 <= b[0] and b[2] <= sb[2] + 2, (
                "text %s outside %s: %s vs %s" % (t["id"], t["inside"], b, sb))
            assert sb[1] - 2 <= b[1] and b[3] <= sb[3] + 2, (
                "text %s outside %s vertically: %s vs %s"
                % (t["id"], t["inside"], b, sb))
    return texts


def build_page(outdir, name, canvas, shapes, dashes, lines, texts,
               sticks=None, spec_filename="spec.json"):
    sticks = sticks or []
    os.makedirs(outdir, exist_ok=True)
    trace = {"canvas": canvas, "shapes": shapes, "dashes": dashes,
             "lines": lines, "sticks": sticks}
    specs_from_texts(texts, shapes)
    boxes = [rendered_bbox(t) for t in texts]
    trace["lines"], n_cut = open_lines_at_texts(trace["lines"], boxes)
    if n_cut:
        print("%s: rule-8 cut %d segment(s) at text boxes" % (name, n_cut))
    svg = build_svg(trace, dashes, texts, name)
    with open(os.path.join(outdir, name + ".svg"), "w",
              encoding="utf-8") as f:
        f.write(svg)
    with open(os.path.join(outdir, name + ".drawio"), "w",
              encoding="utf-8") as f:
        f.write(build_drawio(trace, dashes, texts))
    spec = {"canvas": canvas,
            "source": "F4 owner fix round: explicit layout deltas over the "
                      "Stage B build (unchanged elements proved identical)",
            "shapes": shapes, "dashes": dashes, "lines": trace["lines"],
            "sticks": sticks, "texts": texts,
            "style": {"font_family": "Arial, Helvetica, sans-serif",
                      "stroke": "#000000", "fill": "#FFFFFF"}}
    with open(os.path.join(outdir, spec_filename), "w",
              encoding="utf-8") as f:
        json.dump(spec, f, indent=1)
    print("wrote %s: shapes %d, dashes %d, lines %d, texts %d"
          % (os.path.join(outdir, name), len(shapes), len(dashes),
             len(trace["lines"]), len(texts)))
    return spec


def write_text_content(path, free_ids, free_texts, box_ids, box_texts,
                       bold, note):
    data = {"note": note, "free_ids": free_ids, "free_texts": free_texts,
            "box_ids": box_ids, "box_texts": box_texts, "bold": bold,
            "ellipse_texts": []}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print("wrote", path)


def write_font_plan(path, texts):
    plan = {}
    for t in texts:
        plan[t["id"]] = {"weight": t["weight"], "size": t["size"],
                         "anchor": "top", "measured": t["measured"],
                         "ink": [round(rendered_bbox(t)[2] - rendered_bbox(t)[0], 1),
                                 round(rendered_bbox(t)[3] - rendered_bbox(t)[1], 1)]}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=1)
    print("wrote", path)


def write_letter_spacing(path, texts):
    data = {t["id"]: {"ls": t.get("ls") or 0.0,
                      "x": t["x"],
                      "width": round(rendered_bbox(t)[2] - rendered_bbox(t)[0], 1)}
            for t in texts}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print("wrote", path)

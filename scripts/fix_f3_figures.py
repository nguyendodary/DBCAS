# -*- coding: utf-8 -*-
"""F3 owner fix round (2026-11-09) for figure 05 Module and 06 Logical.

Module: wrap `Attempt / Evidence Repository` onto three lines at the same
34 px size so line 1 gets clear padding from the white service box border.
No shape, line, arrow or other label changes.

Logical: (a) emit continuous bottom edges for the four tier frames - the
measured gap belongs only to the TOP edge under each title tab (the tab is
painted over the line in the original).  (b) re-fit the Administrator
Management Portal description with -0.64 px tracking at the unchanged
34 px size so both sides get >= 13 px padding from the inner box edge.
No shape, line, arrow or other label changes.

Run AFTER scripts/build_stage_b_w2a.py; this script reads spec-stage-b.json,
writes spec.json + spec-stage-b.json + SVG + drawio + fix-f3.json.

Usage:
  node scripts/run_py.mjs scripts/fix_f3_figures.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_figure_w2a_f3 import build_svg, build_drawio  # noqa: E402
from calibrate_fonts import ink  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, "docs", "diagrams", "rebuild", "module")
LOG = os.path.join(ROOT, "docs", "diagrams", "rebuild", "logical")


def place(text, weight, size, cx, top):
    ix0, iy0, ix1, iy1 = ink(text, weight, size)
    w, h = ix1 - ix0, iy1 - iy0
    x = cx - (ix0 + ix1) / 2.0
    y = top - iy0
    return x, y, [cx - w / 2.0, top, cx + w / 2.0, top + h], w


def mk_text(old, content, cx, top, ls=0.0):
    x, y, measured, w = place(content, old["weight"], float(old["size"]),
                              cx, top)
    t = dict(old)
    t["content"] = content
    t["x"] = round(x, 1)
    t["y"] = round(y, 1)
    t["measured"] = [round(v, 1) for v in measured]
    t["measure_w"] = round(w, 1)
    if ls:
        t["ls"] = round(ls, 2)
    else:
        t.pop("ls", None)
    return t


def save_svg_drawio(d, name, spec):
    texts = spec["texts"]
    svg = build_svg(spec, spec.get("dashes", []), texts, name)
    with open(os.path.join(d, name + ".svg"), "w", encoding="utf-8") as f:
        f.write(svg)
    with open(os.path.join(d, name + ".drawio"), "w", encoding="utf-8") as f:
        f.write(build_drawio(spec, spec.get("dashes", []), texts))


def module_fix():
    spec_path = os.path.join(MOD, "spec-stage-b.json")
    spec = json.load(open(spec_path, encoding="utf-8"))
    old = {t["id"]: t for t in spec["texts"]}
    box = next(s for s in spec["shapes"] if s["id"] == "S16")
    cx = (box["bbox"][0] + box["bbox"][2]) / 2.0
    tops = [1131.0, 1169.0, 1207.0]
    new = [
        mk_text(old["X038"], "Attempt /", cx, tops[0]),
        mk_text(old["X047"], "Evidence", cx, tops[1]),
        mk_text(old["X047"], "Repository", cx, tops[2]),
    ]
    new[0]["id"] = "X038"
    new[1]["id"] = "X038-L2"
    new[2]["id"] = "X047"
    keep = [t for t in spec["texts"]
            if t["id"] not in ("X038", "X038-L2", "X047")]
    spec["texts"] = keep + new
    spec["source"] = ("Stage A pixel trace + Stage B content delta + F3 "
                      "owner fix (2026-11-09): Attempt/Evidence wrapped to "
                      "3 lines for border padding; shapes/lines unchanged")
    with open(os.path.join(MOD, "spec.json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=1)
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=1)
    save_svg_drawio(MOD, "module", spec)

    tc_path = os.path.join(MOD, "text-content.json")
    tc = json.load(open(tc_path, encoding="utf-8"))
    ids, texts = [], []
    for i, s in zip(tc["box_ids"], tc["box_texts"]):
        if i in ("X038", "X038-L2", "X047"):
            continue
        ids.append(i)
        texts.append(s)
    ids += ["X038", "X038-L2", "X047"]
    texts += ["Attempt /", "Evidence", "Repository"]
    tc["box_ids"], tc["box_texts"] = ids, texts
    tc["note"] = ("Stage B expected labels + F3 fix (Attempt/Evidence on 3 "
                  "lines). free_texts + box_texts = %d + %d."
                  % (len(tc["free_texts"]), len(tc["box_texts"])))
    with open(tc_path, "w", encoding="utf-8") as f:
        json.dump(tc, f, indent=1)

    fix = {
        "figure": "Module View (Architecture Fig 5)",
        "round": "F3 owner fix 2026-11-09",
        "reason": "line 1 of the Attempt / Evidence Repository label was "
                  "6 px from the white box border",
        "ops": [{"id": "X038", "old": "Attempt / Evidence",
                 "new": ["Attempt /", "Evidence", "Repository"],
                 "size": 34, "line_tops": tops, "center_x": cx,
                 "box": "S16 same bbox [1830,1092,2100,1278] unchanged"}],
        "note": "Shapes, lines, arrowheads and all other labels byte-identical "
                "to spec-stage-a.json (proved by check_rebuild_delta_f3.py).",
    }
    with open(os.path.join(MOD, "fix-f3.json"), "w", encoding="utf-8") as f:
        json.dump(fix, f, indent=1, ensure_ascii=False)
    print("module: X038/X038-L2/X047 ->", [(t["id"], t["content"],
                                            t["measured"]) for t in new])


def logical_fix():
    spec_path = os.path.join(LOG, "spec-stage-b.json")
    spec = json.load(open(spec_path, encoding="utf-8"))
    box = next(s for s in spec["shapes"] if s["id"] == "S09")
    cx = (box["bbox"][0] + box["bbox"][2]) / 2.0
    old = next(t for t in spec["texts"] if t["id"] == "X007")
    content = old["content"]
    ix0, iy0, ix1, iy1 = ink(content, old["weight"], float(old["size"]))
    natural = ix1 - ix0
    target_w = 1036.0
    ls = round((target_w - natural) / (len(content) - 1), 2)
    x, y, measured, w = place(content, old["weight"], float(old["size"]),
                              cx, 615.0)
    w_eff = w + ls * (len(content) - 1)
    x -= (w_eff - w) / 2.0
    old["x"] = round(x, 1)
    old["y"] = round(y, 1)
    old["ls"] = ls
    old["measure_w"] = round(w, 1)
    old["measured"] = [round(cx - w_eff / 2.0, 1), 615.0,
                       round(cx + w_eff / 2.0, 1), round(615.0 + (iy1 - iy0), 1)]
    spec["source"] = ("Stage A pixel trace + Stage B content delta + F3 "
                      "owner fix (2026-11-09): tier-frame bottom edges "
                      "continuous; Administrator description padding; "
                      "shapes/lines unchanged")
    with open(os.path.join(LOG, "spec.json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=1)
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=1)
    save_svg_drawio(LOG, "logical", spec)

    inner_l = box["bbox"][0] + box["stroke_width"] / 2.0
    inner_r = box["bbox"][2] - box["stroke_width"] / 2.0
    fix = {
        "figure": "Logical System Architecture (Proposal Fig 6)",
        "round": "F3 owner fix 2026-11-09",
        "ops": [
            {"type": "frame-bottom-edges", "frames": ["S01", "S02", "S03",
                                                     "S04"],
             "note": "gaps apply to the TOP edge only, under the title tabs; "
                     "bottom edges continuous x0..x1"},
            {"type": "text-fit", "id": "X007", "size": 34,
             "old_ls": -0.52, "new_ls": ls,
             "old_width": 1044.2, "new_width": round(w_eff, 1),
             "inner_padding_left": round(old["measured"][0] - inner_l, 1),
             "inner_padding_right": round(inner_r - old["measured"][2], 1)},
        ],
        "note": "Shapes, lines, arrows, sticks and all other labels "
                "byte-identical to spec-stage-a.json (proved by "
                "check_rebuild_delta_f3.py).",
    }
    with open(os.path.join(LOG, "fix-f3.json"), "w", encoding="utf-8") as f:
        json.dump(fix, f, indent=1, ensure_ascii=False)
    print("logical: X007", old["measured"], "ls", ls,
          "pad %.1f / %.1f" % (old["measured"][0] - inner_l,
                               inner_r - old["measured"][2]))


def main():
    module_fix()
    logical_fix()


if __name__ == "__main__":
    main()

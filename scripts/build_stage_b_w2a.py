# -*- coding: utf-8 -*-
"""Apply a Stage B content delta to a traced figure WITHOUT moving the
layout: unchanged texts keep their Stage A spec objects byte-for-byte;
changed labels are re-anchored on their old ink centre/baseline at the
SAME font size/weight (never smaller), and multi-line blocks keep the
original line grid.  Shapes, lines, arrows, sticks and the canvas are
copied from the Stage A spec unchanged.

Usage:
  node scripts/run_py.mjs scripts/build_stage_b_w2a.py <figure_dir> <delta.json>
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_fonts import ink  # noqa: E402
from build_figure_w2a import (rendered_bbox, build_svg, build_drawio)  # noqa
from trace_figure import open_lines_at_texts  # noqa: E402


def text_obj(old, content, x, y, measured, ls=0.0):
    t = {k: v for k, v in old.items() if k != "ls"}
    t["content"] = content
    t["x"] = round(float(x), 1)
    t["y"] = round(float(y), 1)
    t["measured"] = [round(float(v), 1) for v in measured]
    if ls:
        t["ls"] = round(float(ls), 2)
    return t


def place(text, weight, size, cx, top):
    ix0, iy0, ix1, iy1 = ink(text, weight, size)
    w, h = ix1 - ix0, iy1 - iy0
    x = cx - (ix0 + ix1) / 2.0
    y = top - iy0
    return x, y, [cx - w / 2.0, top, cx + w / 2.0, top + h], w


def main():
    d = sys.argv[1]
    delta = json.load(open(sys.argv[2], encoding="utf-8"))
    name = os.path.basename(os.path.normpath(d))
    spec_path = os.path.join(d, "spec.json")
    base_path = os.path.join(d, "spec-stage-a.json")
    spec = json.load(open(base_path if os.path.exists(base_path)
                          else spec_path, encoding="utf-8"))
    tc_path = os.path.join(d, "text-content.json")
    tc = json.load(open(tc_path, encoding="utf-8"))
    by_id = {t["id"]: t for t in spec["texts"]}
    if not os.path.exists(os.path.join(d, "spec-stage-a.json")):
        shutil.copy(spec_path, os.path.join(d, "spec-stage-a.json"))
        shutil.copy(tc_path, os.path.join(d, "text-content-stage-a.json"))

    ops = delta.get("ops", [])
    dropped, added = set(), []
    print("%-6s %-52s %-6s %s" % ("id", "new text", "size", "placement"))
    for op in ops:
        ids = op["ids"]
        lines = op["lines"]
        old = [by_id[i] for i in ids]
        weight = op.get("weight") or old[0]["weight"]
        size = op.get("size") or max(float(t["size"]) for t in old)
        if op.get("max_width") and len(lines) == 1 and len(lines[0]) > 1:
            _, _, _, w = place(lines[0], weight, size, 0, 0)
            ls = (float(op["max_width"]) - w) / float(len(lines[0]) - 1)
            ls = max(-3.0, min(3.0, round(ls, 2)))
        else:
            ls = 0.0
        if op.get("center_x") is not None:
            cx = float(op["center_x"])
        else:
            cx = (min(t["measured"][0] for t in old) +
                  max(t["measured"][2] for t in old)) / 2.0
        if op.get("center_y") is not None:
            # one line centred on the old multi-line block centre
            assert len(lines) == 1
            _, _, m0, _ = place(lines[0], weight, size, 0, 0)
            h = m0[3] - m0[1]
            top = float(op["center_y"]) - h / 2.0
            tops = [top]
        elif op.get("line_tops"):
            tops = [float(v) for v in op["line_tops"]]
        else:
            tops = [float(old[0]["measured"][1])]
        if len(tops) != len(lines):
            raise SystemExit("line_tops/lines mismatch for %s" % ids)
        for k, (content, top) in enumerate(zip(lines, tops)):
            base = old[min(k, len(old) - 1)]
            x, y, measured, w = place(content, weight, size, cx, top)
            if ls:
                w_eff = w + ls * (len(content) - 1)
                x -= (w_eff - w) / 2.0
                measured = [cx - w_eff / 2.0, top,
                            cx + w_eff / 2.0, top + (measured[3] - top)]
            t = text_obj(base, content, x, y, measured, ls=ls)
            t["id"] = ids[0] if k == 0 else ids[0] + "-L%d" % (k + 1)
            t["weight"] = weight
            t["size"] = size
            t["measure_w"] = round(w, 1)
            added.append(t)
            print("%-6s %-52.52s %-6s x=%.1f y=%.1f ls=%s" %
                  (t["id"], content, size, x, y, ls))
        dropped.update(ids)

    new_texts = [t for t in spec["texts"] if t["id"] not in dropped] + added

    # rule-8 final cut against the RENDERED boxes of the Stage B texts
    boxes = [rendered_bbox(t) for t in new_texts]
    spec["lines"], n_cut = open_lines_at_texts(spec["lines"], boxes)
    if n_cut:
        print("rule-8 final cut: %d segment(s) opened" % n_cut)

    d2 = dict(spec)
    d2["source"] = "Stage A pixel trace + Stage B content delta " \
                   "(same canvas/layout; unchanged elements byte-identical)"
    d2["texts"] = new_texts
    svg = build_svg(d2, d2.get("dashes", []), new_texts, name + "-stage-b")
    with open(os.path.join(d, name + ".svg"), "w", encoding="utf-8") as f:
        f.write(svg)
    with open(os.path.join(d, name + ".drawio"), "w", encoding="utf-8") as f:
        f.write(build_drawio(d2, d2.get("dashes", []), new_texts))
    with open(os.path.join(d, "spec-stage-b.json"), "w", encoding="utf-8") as f:
        json.dump(d2, f, indent=1)
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(d2, f, indent=1)

    # Stage B expected-text file for the rule-8 checker
    free = [t for t in new_texts if t["inside"] is None]
    box = [t for t in new_texts if t["inside"] is not None]
    tc_b = {"note": "Stage B expected labels (same canvas/layout; content "
                    "delta only). free_texts + box_texts = %d + %d." %
                    (len(free), len(box)),
            "free_ids": [t["id"] for t in free],
            "free_texts": [t["content"] for t in free],
            "box_ids": [t["id"] for t in box],
            "box_texts": [t["content"] for t in box],
            "bold_ids": [t["id"] for t in new_texts if t["weight"] == "bold"],
            "ellipse_texts": []}
    with open(tc_path, "w", encoding="utf-8") as f:
        json.dump(tc_b, f, indent=1)

    print("Stage B: %d texts (%d dropped, %d added) | %d labels for checker"
          % (len(new_texts), len(dropped), len(added),
             len(free) + len(box)))
    print("wrote %s.svg, %s.drawio, spec-stage-b.json, text-content.json"
          % (name, name))


if __name__ == "__main__":
    main()

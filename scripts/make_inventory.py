# -*- coding: utf-8 -*-
"""Generate the pre-build element inventory (owner rule 2) from trace.json
+ text-content.json: every element with measured coordinates, each exactly
once, before anything is built.

Usage: python scripts/make_inventory.py <trace.json> <text-content.json> <out.md>
"""
import json
import sys


def main():
    trace_path, content_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    t = json.load(open(trace_path, encoding="utf-8"))
    c = json.load(open(content_path, encoding="utf-8"))
    free = c["free_texts"]
    boxt = c["box_texts"]
    ellt = c["ellipse_texts"]

    lines = []
    a = lines.append
    a("# System Context — pre-build element inventory (Round 1 REDO, Stage A)")
    a("")
    a("Generated from `trace.json` (pixel-measured) + `text-content.json`")
    a("(content read from original PNG crops). Every element listed exactly")
    a("once. Total must be **79 elements**.")
    a("")
    a("Canvas: **%d x %d**" % (t["canvas"]["w"], t["canvas"]["h"]))
    a("")

    n = 0
    a("## Rectangles (4)")
    a("")
    a("| # | id | x | y | w | h | label |")
    a("|---|----|---|---|---|---|-------|")
    rect_ids = ["R1 Learner", "R2 Administrator", "R3 LLM Provider", "R4 legend frame"]
    for i, r in enumerate(t["rects"]):
        n += 1
        a("| %d | %s | %d | %d | %d | %d | %s |" %
          (n, rect_ids[i], r["x"], r["y"], r["w"], r["h"],
           boxt[i] if i < 3 else "(frame; holds System/Actor/Interaction)"))
    a("")

    n += 1
    a("## Ellipse (1)")
    a("")
    cx, cy, rx, ry = t["ellipse"]
    a("- **E1** center (%.0f, %.0f), rx %.0f, ry %.0f (pixel bbox "
      "%.0f..%.0f x %.0f..%.0f) — label: %s [%d, %d, %d, %d]" %
      (cx, cy, rx, ry, cx - rx, cx + rx, cy - ry, cy + ry, ellt[0],
       *t["ellipse_texts"][0]))
    a("")

    a("## Legend icons (3)")
    a("")
    a("| # | id | bbox (x0,y0,x1,y1) | shape |")
    a("|---|----|--------------------|-------|")
    icon_ids = ["I1 oval", "I2 rect", "I3 arrow"]
    icon_shapes = ["hollow oval", "hollow rectangle", "arrow symbol"]
    for i, b in enumerate(t["legend_icons"]):
        n += 1
        a("| %d | %s | (%d, %d, %d, %d) | %s |" %
          (n, icon_ids[i], b[0], b[1], b[2], b[3], icon_shapes[i]))
    a("")

    a("## Flows (21 polylines) + arrows (21) + flow labels (21)")
    a("")
    a("One arrowhead per flow. Arrow tip positions measured; triangle "
      "approx. 11 px tall x 11 px base; line stroke 2 px.")
    a("")
    a("| # | id | polyline points | arrow tip | label bbox | label |")
    a("|---|----|-----------------|-----------|------------|-------|")
    # flow_label_to_flow mapping keys: Txx->Fxx
    lab_by_flow = {}
    for key, val in c["flow_label_to_flow"].items():
        if key.startswith("comment"):
            continue
        ti, fi = key.split("->")
        lab_by_flow[int(fi[1:]) - 1] = (int(ti[1:]), val)
    arrows_by_flow = {a_["flow"]: a_ for a_ in t["arrows"]}
    for i, fl in enumerate(t["flows"]):
        n += 1  # the polyline itself
        n += 1  # its arrowhead (listed in the same row, counted as own element)
        pts = " -> ".join("(%d, %d)" % (p[0], p[1]) for p in fl)
        ar = arrows_by_flow[i]
        ti, label = lab_by_flow[i]
        lb = t["free_texts"][ti]
        a("| %d + %d | F%02d (line, arrow) | %s | (%d, %d) | (%d, %d, %d, %d) | %s |" %
          (n - 1, n, i + 1, pts, ar["tip"][0], ar["tip"][1],
           lb[0], lb[1], lb[2], lb[3], label))
    a("")
    a("Flow labels themselves are counted once more below, in **Texts (29)** — "
      "they are referenced (not re-counted) in this table.")

    a("## Texts (29)")
    a("")
    a("### Free texts (22 = 1 title + 21 flow labels)")
    a("")
    a("| # | bbox | content |")
    a("|---|------|---------|")
    for i, b in enumerate(t["free_texts"]):
        n += 1
        kind = "title" if i == 0 else "flow label F%02d" % (
            {v[0]: k + 1 for k, v in lab_by_flow.items()}.get(i, 0))
        a("| %d | (%d, %d, %d, %d) %s | %s |" %
          (n, b[0], b[1], b[2], b[3], kind, free[i]))
    a("")
    a("### Box texts (6)")
    a("")
    a("| # | bbox | content | inside |")
    a("|---|------|---------|--------|")
    for i, b in enumerate(t["box_texts"]):
        n += 1
        a("| %d | (%d, %d, %d, %d) | %s | rect %s |" %
          (n, b["text"][0], b["text"][1], b["text"][2], b["text"][3],
           boxt[i], rect_ids[i] if i < 3 else "R4 legend frame"))
    a("")
    a("### Ellipse text (1)")
    a("")
    n += 1
    b = t["ellipse_texts"][0]
    a("- **%d** (%d, %d, %d, %d) — %s" % (n, b[0], b[1], b[2], b[3], ellt[0]))
    a("")
    a("## Total")
    a("")
    a("4 rects + 1 ellipse + 3 legend icons + 21 flows + 21 arrows + "
      "29 texts = **%d elements** (flows/arrows/labels counted per item; "
      "4+1+3+21+21+29 = 79)." % (4 + 1 + 3 + 21 + 21 + 29))
    assert n == 79, "count mismatch: %d" % n

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote", out, "elements counted:", n)


if __name__ == "__main__":
    main()

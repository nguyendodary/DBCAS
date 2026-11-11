# -*- coding: utf-8 -*-
"""Corrected pre/post-build element inventory (W1 figures).

Same idea as make_figure_inventory.py, with the counting bug fixed:
  * an arrowhead is counted only when the line has one;
  * stick figures are listed as one actor element with their primitives;
  * a boundary label gap is shown explicitly.

Usage:
  python scripts/make_figure_inventory_w1.py <figure_dir>
Writes <figure_dir>/inventory.md.
"""
import json
import os
import sys


def main():
    d = sys.argv[1]
    t = json.load(open(os.path.join(d, "trace.json"), encoding="utf-8"))
    c = json.load(open(os.path.join(d, "text-content.json"), encoding="utf-8"))
    name = os.path.basename(os.path.normpath(d))
    L = []
    a = L.append
    a("# %s - element inventory" % name.replace("-", " ").title())
    a("")
    a("Generated from `trace.json` (pixel-measured) + `text-content.json`")
    a("(strings read from original crops). Every element is listed exactly")
    a("once. Stage A/B label counts are stated where they differ.")
    a("")
    a("Canvas: **%d x %d**" % (t["canvas"]["w"], t["canvas"]["h"]))
    a("")
    a("## Shapes (%d)" % len(t["shapes"]))
    a("")
    a("| # | id | kind | bbox (x0,y0,x1,y1) | fill | stroke | sw | extra |")
    a("|---|----|------|--------------------|------|--------|----|-------|")
    n = 0
    for s in t["shapes"]:
        n += 1
        extra = ""
        if s["kind"] == "rounded":
            extra = "radius %s" % s.get("radius", 0)
        if s["kind"] == "cylinder":
            extra = "cap %s, %d outline pts" % (s.get("cap_ry"),
                                                len(s.get("outline", [])))
        if s.get("dashed"):
            extra = "dashed %s/%s" % (s.get("dash_on"), s.get("dash_off"))
        if s.get("gaps"):
            extra = "label gap(s) %s" % s["gaps"]
        a("| %d | %s | %s | %s | %s | %s | %s | %s |" %
          (n, s["id"], s["kind"], s.get("draw_bbox") or s["bbox"],
           s.get("fill"), s.get("stroke"), s.get("stroke_width"), extra))
    a("")
    a("## Dash runs (%d)" % len(t.get("dashes", [])))
    a("")
    if t.get("dashes"):
        a("| # | axis | pos | span | dashes | on | off |")
        a("|---|------|-----|------|--------|----|-----|")
        for dd in t["dashes"]:
            n += 1
            if dd["axis"] == "h":
                span = "%d..%d" % (dd["x0"], dd["x1"])
                pos = dd["y"]
            else:
                span = "%d..%d" % (dd["y0"], dd["y1"])
                pos = dd["x"]
            a("| %d | %s | %s | %s | %d | %d | %d |" %
              (n, dd["axis"], pos, span, dd["dashes"], dd["on"],
               dd["off"]))
    else:
        a("- none")
    a("")
    arrows = sum(1 for x in t["lines"] if x.get("arrow_tip"))
    a("## Lines (%d) + arrowheads (%d)" % (len(t["lines"]), arrows))
    a("")
    a("| # | id | segments | stroke | colour | arrow tip |")
    a("|---|----|----------|--------|--------|-----------|")
    for ln in t["lines"]:
        n += 1
        arrow = "yes" if ln.get("arrow_tip") else "none"
        segs = " -> ".join("(%g,%g)-(%g,%g)" % (s[0][0], s[0][1],
                                                s[1][0], s[1][1])
                           for s in ln["segs"])
        a("| %d | %s | %s | %s | %s | %s |" %
          (n, ln["id"], segs, ln.get("stroke"), ln.get("color"), arrow))
        if ln.get("arrow_tip"):
            n += 1
            a("| %d | %s-A | arrowhead at %s | - | %s | - |" %
              (n, ln["id"], ln["arrow_tip"], ln.get("color")))
    a("")
    sticks = t.get("sticks", [])
    a("## Actor stick figures (%d)" % len(sticks))
    a("")
    for s_ in sticks:
        n += 1
        a("- **%s %d**: head circle %s (1 primitive); %d limb primitives."
          % (s_["id"], n, s_.get("circle"), len(s_.get("limbs", []))))
    a("")
    a("## Texts (%d)" % len(t["texts"]))
    a("")
    a("| # | id | bbox | inside | ink | content |")
    a("|---|----|------|--------|-----|---------|")
    by_id = {x["id"]: x for x in t["texts"]}
    items = ([(by_id[i], s) for i, s in
              zip(c["free_ids"], c["free_texts"])] +
             [(by_id[i], s) for i, s in
              zip(c["box_ids"], c["box_texts"])])
    cont_by_id = {x["id"]: s for x, s in items}
    for x in t["texts"]:
        n += 1
        a("| %d | %s | %s | %s | %s | %s |" %
          (n, x["id"], x["bbox"], x["inside"], x.get("ink"),
           cont_by_id[x["id"]].replace("|", "\\|")))
    a("")
    a("## Total")
    a("")
    a("%d shapes + %d dash runs + %d lines + %d arrowheads + %d actor "
      "stick figures + %d texts = **%d elements**, each listed exactly "
      "once." %
      (len(t["shapes"]), len(t.get("dashes", [])), len(t["lines"]),
       arrows, len(sticks), len(t["texts"]), n))
    out = os.path.join(d, "inventory.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", out, "elements counted:", n)


if __name__ == "__main__":
    main()

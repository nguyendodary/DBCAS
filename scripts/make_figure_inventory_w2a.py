# -*- coding: utf-8 -*-
"""Pre-build element inventory for a traced figure (owner rule 2): every
element listed exactly once with its measured coordinates, generated from
trace.json + text-content.json BEFORE anything is rendered.

Usage:
  node scripts/run_py.mjs scripts/make_figure_inventory.py <figure_dir>
Writes <figure_dir>/inventory.md
"""
import json
import os
import sys


def main():
    d = sys.argv[1]
    t = json.load(open(os.path.join(d, "trace.json"), encoding="utf-8"))
    c = json.load(open(os.path.join(d, "text-content.json"), encoding="utf-8"))
    name = os.path.basename(os.path.normpath(d))
    free = [x for x in t["texts"] if x["inside"] is None]
    box = [x for x in t["texts"] if x["inside"] is not None]
    L = []
    a = L.append
    a("# %s - pre-build element inventory (Stage A clone)" % name.replace("-", " ").title())
    a("")
    a("Generated from `trace.json` (pixel-measured) + `text-content.json`")
    a("(strings read from original crops). Every element listed exactly")
    a("once.")
    a("")
    a("Canvas: **%d x %d**" % (t["canvas"]["w"], t["canvas"]["h"]))
    a("")
    n = 0
    a("## Shapes (%d)" % len(t["shapes"]))
    a("")
    a("| # | id | kind | bbox (x0,y0,x1,y1) | fill | stroke | sw | extra |")
    a("|---|----|------|--------------------|------|--------|----|-------|")
    for s in t["shapes"]:
        n += 1
        extra = ""
        if s["kind"] == "rounded":
            extra = "radius %s" % s.get("radius", 0)
        if s["kind"] == "cylinder":
            extra = "cap %s, %d outline pts" % (s.get("cap_ry"),
                                                len(s.get("outline", [])))
        if s.get("dashed"):
            extra = ("dashed %s/%s" % (s.get("dash_on"), s.get("dash_off")))
        a("| %d | %s | %s | %s | %s | %s | %s | %s |" %
          (n, s["id"], s["kind"], s["bbox"], s.get("fill"),
           s.get("stroke"), s.get("stroke_width"), extra))
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
              (n, dd["axis"], pos, span, dd["dashes"], dd["on"], dd["off"]))
    else:
        a("- none")
    a("")
    a("## Lines (%d) + arrowheads (%d)" %
      (len(t["lines"]), sum(1 for l in t["lines"] if l.get("arrow_tip"))))
    a("")
    a("| # | id | segments | stroke | colour | arrow tip |")
    a("|---|----|----------|--------|--------|-----------|")
    for l in t["lines"]:
        n += 1                      # the polyline
        if l.get("arrow_tip"):
            n += 1                  # its arrowhead (same row)
        segs = " -> ".join("(%g,%g)-(%g,%g)" % (s[0][0], s[0][1],
                                                s[1][0], s[1][1])
                           for s in l["segs"])
        a("| %d + %d | %s | %s | %s | %s | %s |" %
          (n - 1, n, l["id"], segs, l.get("stroke"), l.get("color"),
           l.get("arrow_tip")))
    a("")
    for k in ("sticks",):
        for s_ in t.get(k, []):
            n += 1
            a("- **%s %d** circle=%s limbs=%d" %
              (s_["id"], n, s_.get("circle"), len(s_.get("limbs", []))))
    a("")
    a("## Texts (%d)" % len(t["texts"]))
    a("")
    a("| # | id | bbox | inside | ink | content |")
    a("|---|----|------|--------|-----|---------|")
    # strings aligned exactly like the builder/font plan (by stable id)
    trace_texts = t["texts"]
    if c.get("free_ids") and c.get("box_ids"):
        by_id = {x["id"]: x for x in trace_texts}
        items = ([(by_id[i], s) for i, s in
                  zip(c["free_ids"], c["free_texts"])] +
                 [(by_id[i], s) for i, s in
                  zip(c["box_ids"], c["box_texts"])])
    else:
        free = [x for x in trace_texts if x["inside"] is None]
        box = [x for x in trace_texts if x["inside"] is not None]
        items = ([(x, s) for x, s in zip(free, c["free_texts"])] +
                 [(x, s) for x, s in zip(box, c["box_texts"])])
    cont_by_id = {x["id"]: s for x, s in items}
    for x in t["texts"]:
        n += 1
        a("| %d | %s | %s | %s | %s | %s |" %
          (n, x["id"], x["bbox"], x["inside"], x.get("ink"),
           cont_by_id[x["id"]].replace("|", "\\|")))
    a("")
    a("## Total")
    a("")
    nsticks = len(t.get("sticks", []))
    a("%d shapes + %d dash runs + %d lines + %d arrowheads + %d actor "
      "sticks + %d texts = **%d elements**, each listed exactly once."
      % (len(t["shapes"]), len(t.get("dashes", [])), len(t["lines"]),
         sum(1 for l in t["lines"] if l.get("arrow_tip")), nsticks,
         len(t["texts"]), n))
    out = os.path.join(d, "inventory.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", out, "elements counted:", n)


if __name__ == "__main__":
    main()

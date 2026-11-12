# -*- coding: utf-8 -*-
"""Inventory for an F4 split page (same table as make_figure_inventory.py,
but with explicit trace/content/output names).

Usage:
  python scripts/make_figure_inventory_f4.py <dir> <trace.json> <text-content.json> <out.md>
"""
import json
import os
import sys


def main():
    d, trace_name, content_name, out_name = sys.argv[1:5]
    t = json.load(open(os.path.join(d, trace_name), encoding="utf-8"))
    c = json.load(open(os.path.join(d, content_name), encoding="utf-8"))
    name = os.path.basename(os.path.normpath(d))
    free = [x for x in t["texts"] if x["inside"] is None]
    box = [x for x in t["texts"] if x["inside"] is not None]
    L = []
    a = L.append
    a("# %s - F4 split page inventory" % name.replace("-", " ").title())
    a("")
    a("Generated from `%s` + `%s`. Every element listed exactly once."
      % (trace_name, content_name))
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
                span = "%s..%s" % (dd["x0"], dd["x1"])
                pos = dd["y"]
            else:
                span = "%s..%s" % (dd["y0"], dd["y1"])
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
        n += 1
        line_no = n
        tip_no = ""
        if l.get("arrow_tip"):
            n += 1
            tip_no = " + %d" % n
        segs = " -> ".join("(%g,%g)-(%g,%g)" % (s[0][0], s[0][1],
                                                s[1][0], s[1][1])
                           for s in l["segs"])
        a("| %d%s | %s | %s | %s | %s | %s |" %
          (line_no, tip_no, l.get("id"), segs, l.get("stroke"),
           l.get("color"), l.get("arrow_tip")))
    a("")
    a("## Texts (%d)" % len(t["texts"]))
    a("")
    a("| # | id | bbox | inside | ink | content |")
    a("|---|----|------|--------|-----|---------|")
    trace_texts = t["texts"]
    if c.get("free_ids") and c.get("box_ids"):
        by_id = {x["id"]: x for x in trace_texts}
        items = ([(by_id[i], s) for i, s in
                  zip(c["free_ids"], c["free_texts"])] +
                 [(by_id[i], s) for i, s in
                  zip(c["box_ids"], c["box_texts"])])
    else:
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
    a("%d shapes + %d dash runs + %d lines + %d arrowheads + %d texts = "
      "**%d elements**, each listed exactly once."
      % (len(t["shapes"]), len(t.get("dashes", [])), len(t["lines"]),
         sum(1 for l in t["lines"] if l.get("arrow_tip")), len(t["texts"]),
         n))
    out = os.path.join(d, out_name)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", out, "elements:", n)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Calibrate per-label font weight/size for a traced figure (width-driven).

For every label in text-content.json (aligned with trace.json texts) pick the
Arial (regular/bold) size 8..140 whose ink WIDTH best matches the measured
ink width (height only breaks ties). Labels whose measured height is below
75% of the rendered ink height are occluded in the original (text-frame
overlap) and get anchor=bottom: they render with their ink BOTTOM on the
measured bottom, so the full line is visible at the original baseline.

Usage:
  node scripts/run_py.mjs scripts/make_font_plan.py <figure_dir>
Writes <figure_dir>/font-plan.json  {id: {weight,size,anchor,measured}}.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_fonts import ink  # noqa: E402


def main():
    d = sys.argv[1]
    trace = json.load(open(os.path.join(d, "trace.json"), encoding="utf-8"))
    cont = json.load(open(os.path.join(d, "text-content.json"),
                          encoding="utf-8"))
    by_id = {t["id"]: t for t in trace["texts"]}
    if cont.get("free_ids") and cont.get("box_ids"):
        items = ([(by_id[i], s) for i, s in
                  zip(cont["free_ids"], cont["free_texts"])] +
                 [(by_id[i], s) for i, s in
                  zip(cont["box_ids"], cont["box_texts"])])
    else:
        free = [t for t in trace["texts"] if t["inside"] is None]
        box = [t for t in trace["texts"] if t["inside"] is not None]
        assert len(free) == len(cont["free_texts"]), \
            (len(free), len(cont["free_texts"]))
        assert len(box) == len(cont["box_texts"]), \
            (len(box), len(cont["box_texts"]))
        items = ([(t, s) for t, s in zip(free, cont["free_texts"])] +
                 [(t, s) for t, s in zip(box, cont["box_texts"])])
    bold_set = set(cont.get("bold", []))
    plan = {}
    print("%-6s %-46s %-6s %-5s %-6s %s" %
          ("id", "text", "wt", "size", "anchor", "measured/rendered"))
    for t, s in items:
        W = t["bbox"][2] - t["bbox"][0]
        H = t["bbox"][3] - t["bbox"][1]
        best = None
        weights = ("bold",) if (bold_set and s in bold_set) else \
            (("regular",) if bold_set else ("regular", "bold"))
        for wt in weights:
            # integer sizes only: Chrome and PIL agree on hinted integer
            # widths, but diverge at fractional sizes (letter-spacing then
            # corrects the remaining step jump to the measured width)
            for size in range(8, 141):
                ib = ink(s, wt, size)
                if ib is None:
                    continue
                iw, ih = ib[2] - ib[0], ib[3] - ib[1]
                err = abs(iw - W) + 0.05 * abs(ih - H)
                if best is None or err < best[0]:
                    best = (err, wt, size, iw, ih)
        _, wt, size, iw, ih = best
        anchor = "bottom" if H < 0.75 * ih else "top"
        plan[t["id"]] = {"weight": wt, "size": size, "anchor": anchor,
                         "measured": t["bbox"], "ink": [iw, ih]}
        print("%-6s %-46s %-6s %-5d %-6s %s / %dx%d (err %.1f)" %
              (t["id"], s[:46], wt, size, anchor, "%dx%d" % (W, H),
               iw, ih, best[0]))
    with open(os.path.join(d, "font-plan.json"), "w",
              encoding="utf-8") as f:
        json.dump(plan, f, indent=1)
    print("wrote", os.path.join(d, "font-plan.json"), len(plan), "entries")


if __name__ == "__main__":
    main()

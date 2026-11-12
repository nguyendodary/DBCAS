# -*- coding: utf-8 -*-
"""Resolve text/text overlaps on the RENDERED geometry of a traced figure.

The rendered ink bbox of a label is (left, top, left+iw, top+ih) for
anchor=top and (left, bottom-ih, left+iw, bottom) for anchor=bottom, where
iw/ih come from font-plan.json - these can be 1-3 px taller than the
measured band, which pushes sibling labels into each other.

For every overlapping pair the LOWER label is pushed down by overlap+2 px
(box labels only: box interiors have free vertical space and contain no
lines). The shifts are appended to text-fixes.json as "nudges" (owner rule:
enlarge spacing, never shrink) so the pipeline stays reproducible.

Usage:
  node scripts/run_py.mjs scripts/resolve_text_spacing.py <figure_dir>
Exit 0 = no overlaps remain (after this pass or if none existed).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_system_context import place_text  # noqa: E402


def rendered_bbox(t, pl):
    x0, y0, x1, y1 = t["bbox"]
    iw, ih = pl["ink"]
    if pl["anchor"] == "bottom":
        return (x0, y1 - ih, x0 + iw, y1)
    return (x0, y0, x0 + iw, y0 + ih)


def overlap(a, b):
    ox = min(a[2], b[2]) - max(a[0], b[0])
    oy = min(a[3], b[3]) - max(a[1], b[1])
    return (ox > 0 and oy > 0), ox, oy


def main():
    d = sys.argv[1]
    trace = json.load(open(os.path.join(d, "trace.json"), encoding="utf-8"))
    plan = json.load(open(os.path.join(d, "font-plan.json"), encoding="utf-8"))
    fixes_path = os.path.join(d, "text-fixes.json")
    fixes = (json.load(open(fixes_path, encoding="utf-8"))
             if os.path.exists(fixes_path) else {})
    # trace.json already reflects the recorded nudges - use bboxes as-is
    base = {t["id"]: list(t["bbox"]) for t in trace["texts"]}

    box_texts = [t for t in trace["texts"] if t["inside"] is not None]
    shifts = {}          # id -> cumulative dy
    for _ in range(12):
        placed = []
        for t in box_texts:
            b = base[t["id"]][:]
            b[1] += shifts.get(t["id"], 0)
            b[3] += shifts.get(t["id"], 0)
            pl = plan[t["id"]]
            if pl["anchor"] == "bottom":
                rb = (b[0], b[3] - pl["ink"][1], b[0] + pl["ink"][0], b[3])
            else:
                rb = (b[0], b[1], b[0] + pl["ink"][0], b[1] + pl["ink"][1])
            placed.append((t, rb))
        any_ov = False
        for i in range(len(placed)):
            for j in range(i + 1, len(placed)):
                hit, ox, oy = overlap(placed[i][1], placed[j][1])
                if not hit:
                    continue
                lo = placed[j][0] if placed[j][0]["bbox"][1] >= \
                    placed[i][0]["bbox"][1] else placed[i][0]
                shifts[lo["id"]] = shifts.get(lo["id"], 0) + oy + 2
                any_ov = True
        if not any_ov:
            break

    new_nudges = []
    for tid, dy in sorted(shifts.items()):
        if dy:
            tb = next(x for x in trace["texts"] if x["id"] == tid)["bbox"]
            new_nudges.append({"bbox": tb, "dy": dy})
    if new_nudges:
        fixes.setdefault("nudges", []).extend(new_nudges)
        with open(fixes_path, "w", encoding="utf-8") as f:
            json.dump(fixes, f, indent=1)
    print("shifted:", {k: v for k, v in shifts.items() if v})
    print("appended nudges:", len(new_nudges))
    # verify on the post-shift geometry
    bad = 0
    cur = {}
    for t in box_texts:
        b = list(t["bbox"])
        b[1] += shifts.get(t["id"], 0)
        b[3] += shifts.get(t["id"], 0)
        pl = plan[t["id"]]
        if pl["anchor"] == "bottom":
            rb = (b[0], b[3] - pl["ink"][1], b[0] + pl["ink"][0], b[3])
        else:
            rb = (b[0], b[1], b[0] + pl["ink"][0], b[1] + pl["ink"][1])
        cur[t["id"]] = rb
    ids = list(cur)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            hit, ox, oy = overlap(cur[ids[i]], cur[ids[j]])
            if hit:
                bad += 1
                print("REMAINS:", ids[i], cur[ids[i]], ids[j],
                      cur[ids[j]], ox, oy)
    print("remaining box-text overlaps:", bad)
    sys.exit(1 if bad else 0)


def trace_bbox(trace, tid):
    return next(t["bbox"] for t in trace["texts"] if t["id"] == tid)


if __name__ == "__main__":
    main()

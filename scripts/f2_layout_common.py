# -*- coding: utf-8 -*-
"""Shared layout helpers for the F2 owner-fix round (Container + Allocation).

These helpers compute deterministic Arial ink boxes so the measured band of a
label equals the box the rule-8 checker will compute.  Used only by
scripts/build_container_fix_f2.py and scripts/build_allocation_fix_f2.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_fonts import ink  # noqa: E402


def ink_size(text, weight, size):
    b = ink(text, weight, size)
    return b[2] - b[0], b[3] - b[1], b


def text_entry(tid, content, weight, size, left=None, center=None, top=None,
               inside=None, colour="#222222"):
    """Return a trace text entry whose measured bbox is exactly the Arial
    ink box at the requested position (so PLACE + checker agree)."""
    iw, ih, b = ink_size(content, weight, size)
    if center is not None:
        left = center - (b[0] + b[2]) / 2.0
    if left is None or top is None:
        raise ValueError("left/center and top required")
    left = round(left, 1)
    top = round(top, 1)
    return {"id": tid, "bbox": [left, top, round(left + iw, 1),
                                round(top + ih, 1)],
            "ink": colour, "inside": inside}


def plan_entry(entry, weight, size):
    b = entry["bbox"]
    return {"weight": weight, "size": size, "anchor": "top",
            "measured": b, "ink": [round(b[2] - b[0], 1),
                                   round(b[3] - b[1], 1)]}


def reflow_box(trace, texts_by_id, plan, box_id, lines, pad_top, pad_bottom,
               gap, fixed_height=None, centre=False):
    """Lay out the box's text lines top-to-bottom with equal ink gaps.

    lines: list of (text_id, weight, size) in reading order; strings come from
    text-content.json and are not needed here.  Updates the shape y1 (grow
    only) and every text bbox, and returns the new height.
    """
    shape = next(s for s in trace["shapes"] if s["id"] == box_id)
    x0, y0, x1, y1 = shape["bbox"]
    cx = (x0 + x1) / 2.0
    heights = []
    for tid, weight, size, _content in lines:
        t = texts_by_id[tid]
        iw, ih, b = ink_size(_content, weight, size)
        heights.append((t, weight, size, iw, ih, b))
    body = sum(h[4] for h in heights) + gap * (len(heights) - 1)
    if fixed_height is not None:
        height = fixed_height
    else:
        height = pad_top + body + pad_bottom
    height = max(height, y1 - y0)
    top = y0 + ((height - body) / 2.0 if centre else pad_top)
    cy = top
    for t, weight, size, iw, ih, b in heights:
        # keep the traced ink-left anchor so untouched labels cannot drift
        bx0 = round(t["bbox"][0], 1)
        by0 = round(cy, 1)
        t["bbox"] = [bx0, by0, round(bx0 + iw, 1), round(by0 + ih, 1)]
        plan[t["id"]] = plan_entry(t, weight, size)
        cy += ih + gap
    shape["bbox"] = [x0, y0, x1, round(y0 + height, 1)]
    return height


def add_shape(trace, sid, bbox, fill, stroke, stroke_width, radius):
    trace["shapes"].append({
        "bbox": list(bbox), "kind": "rounded", "fill": fill,
        "stroke": stroke, "stroke_width": stroke_width, "radius": radius,
        "dashed": False, "dash_on": 0, "dash_off": 0, "id": sid})


def add_line(trace, lid, segs, colour, stroke, tip=None, source=None):
    trace["lines"].append({
        "id": lid, "bbox": [min(min(p[0] for p in seg) for seg in segs),
                            min(min(p[1] for p in seg) for seg in segs),
                            max(max(p[0] for p in seg) for seg in segs),
                            max(max(p[1] for p in seg) for seg in segs)],
        "segs": [[list(p) for p in seg] for seg in segs],
        "thickness": stroke + 2, "color": colour, "stroke": stroke,
        "arrow_tip": tip, "arrow_from": source})

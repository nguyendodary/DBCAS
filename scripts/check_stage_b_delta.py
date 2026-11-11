# -*- coding: utf-8 -*-
"""Stage B delta checker: unchanged elements + no-crossing rules.

The rule-8 checker (check_diagram_geometry.py) proves text geometry; this
script proves the owner's two remaining Stage B rules against the specs:

  (1) DO NOT MOVE/RESTYLE: every Stage A element is present unchanged in
      Stage B. Only the two renamed flow labels differ, and they must keep
      their exact ink top-left anchor, font size and weight.
  (2) NO CROSSING: no new line segment (flow edge, arrowhead edge, new box
      border) crosses an existing line/box/label or another new segment.
      Touching at a segment endpoint (the ellipse / box-border connection
      points) is allowed and reported.

Usage:
  node scripts/run_py.mjs scripts/check_stage_b_delta.py \
      docs/qa/rebuild-preview/system-context/spec-stage-a.json \
      docs/diagrams/rebuild/system-context/spec.json

Prints a full report. Exit 0 = PASS, 1 = FAIL.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_diagram_geometry import ellipse_poly  # noqa: E402

TOUCH = 1.0        # px: intersection at a new-segment endpoint = connection
N_ELLIPSE = 128


# ------------------------------------------------------------------ helpers

def rect_edges(x, y, w, h):
    return [((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)),
            ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))]


def poly_edges(pts, close=False):
    p = list(pts)
    if close and len(p) > 1 and p[0] != p[-1]:
        p.append(p[0])
    return [(a, b) for a, b in zip(p, p[1:]) if a != b]


def spec_segments(spec):
    """All line segments of a spec as (tag, (p0, p1))."""
    segs = []
    for r in spec["rects"]:
        x, y, w, h = r["stroke_rect"]
        for e in rect_edges(x, y, w, h):
            segs.append(("rect:%s" % r["name"], e))
    e = spec["ellipse"]
    pts = ellipse_poly(e["cx"], e["cy"], e["rx"], e["ry"], N_ELLIPSE)
    for ed in poly_edges(pts, close=True):
        segs.append(("ellipse", ed))
    for i, ic in enumerate(spec["legend_icons"]):
        if ic["kind"] == "ellipse":
            p = ellipse_poly(ic["cx"], ic["cy"], ic["rx"], ic["ry"], 64)
            for ed in poly_edges(p, close=True):
                segs.append(("icon%d" % i, ed))
        elif ic["kind"] == "rect":
            for ed in rect_edges(ic["x"], ic["y"], ic["w"], ic["h"]):
                segs.append(("icon%d" % i, ed))
        elif ic["kind"] == "line":
            segs.append(("icon%d" % i, ((ic["x1"], ic["y1"]),
                                        (ic["x2"], ic["y2"]))))
        elif ic["kind"] == "tri":
            for ed in poly_edges(ic["points"], close=True):
                segs.append(("icon%d" % i, ed))
    for f in spec["flows"]:
        for ed in poly_edges([tuple(p) for p in f["points"]]):
            segs.append((f["id"], ed))
        for ed in poly_edges([tuple(p) for p in f["arrow_poly"]], close=True):
            segs.append((f["id"] + ":arrow", ed))
    return segs


def spec_texts(spec):
    return {t["id"]: t for t in spec["texts"]}


def seg_intersect(a, b):
    """Return the intersection point of segments a,b, or None."""
    (ax0, ay0), (ax1, ay1) = a
    (bx0, by0), (bx1, by1) = b
    dx1, dy1 = ax1 - ax0, ay1 - ay0
    dx2, dy2 = bx1 - bx0, by1 - by0
    den = dx1 * dy2 - dy1 * dx2
    if abs(den) < 1e-12:
        return None                      # parallel / collinear: no clean point
    t = ((bx0 - ax0) * dy2 - (by0 - ay0) * dx2) / den
    u = ((bx0 - ax0) * dy1 - (by0 - ay0) * dx1) / den
    if -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= u <= 1 + 1e-9:
        return (ax0 + t * dx1, ay0 + t * dy1)
    return None


def near_endpoint(pt, seg):
    (x0, y0), (x1, y1) = seg
    return (math.hypot(pt[0] - x0, pt[1] - y0) <= TOUCH or
            math.hypot(pt[0] - x1, pt[1] - y1) <= TOUCH)


def bbox_hits_segment(bb, seg):
    (x0, y0), (x1, y1) = seg
    bx0, by0, bx1, by1 = bb
    if max(x0, x1) < bx0 or min(x0, x1) > bx1:
        return False
    if max(y0, y1) < by0 or min(y0, y1) > by1:
        return False
    return seg_intersect(seg, ((bx0, by0), (bx1, by0))) is not None or \
        seg_intersect(seg, ((bx1, by0), (bx1, by1))) is not None or \
        seg_intersect(seg, ((bx1, by1), (bx0, by1))) is not None or \
        seg_intersect(seg, ((bx0, by1), (bx0, by0))) is not None or \
        (bx0 <= x0 <= bx1 and by0 <= y0 <= by1)


def seg_gap(bb, seg):
    """Rough min distance from bbox to segment (0 if touching)."""
    (x0, y0), (x1, y1) = seg
    bx0, by0, bx1, by1 = bb
    best = 1e9
    steps = 64
    for i in range(steps + 1):
        t = i / steps
        px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        dx = max(bx0 - px, 0, px - bx1)
        dy = max(by0 - py, 0, py - by1)
        best = min(best, math.hypot(dx, dy))
    return best


# ------------------------------------------------------------------ main

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    a_path, b_path = sys.argv[1], sys.argv[2]
    A = json.load(open(a_path, encoding="utf-8"))
    B = json.load(open(b_path, encoding="utf-8"))
    out, problems = [], []

    out.append("stage-b delta checker")
    out.append("  stage A: %s" % a_path)
    out.append("  stage B: %s" % b_path)
    out.append("")

    # ---------------------------------------------------- (1) unchanged
    out.append("== (1) Stage A elements unchanged in Stage B ==")
    renamed = {"T02", "T08"}

    if [(r["name"], r["stroke_rect"], r["stroke_width"]) for r in A["rects"]] != \
       [(r["name"], r["stroke_rect"], r["stroke_width"])
        for r in B["rects"][:len(A["rects"])]]:
        problems.append("Stage A rects changed")
        out.append("FAIL: Stage A rects changed")
    else:
        out.append("OK: %d Stage A rects identical (position, size, name)"
                   % len(A["rects"]))

    if A["ellipse"] != B["ellipse"]:
        problems.append("ellipse changed")
        out.append("FAIL: ellipse changed")
    else:
        out.append("OK: ellipse identical (%s)" % A["ellipse"])

    if A["legend_icons"] != B["legend_icons"]:
        problems.append("legend changed")
        out.append("FAIL: legend changed")
    else:
        out.append("OK: legend icons identical (%d icons - no new element "
                   "type, legend not updated)" % len(A["legend_icons"]))

    if A["canvas"] != B["canvas"]:
        problems.append("canvas changed")
        out.append("FAIL: canvas changed %s -> %s"
                   % (A["canvas"], B["canvas"]))
    else:
        out.append("OK: canvas unchanged %s" % A["canvas"])

    a_flows = {f["id"]: f for f in A["flows"]}
    b_flows = {f["id"]: f for f in B["flows"]}
    same = [i for i in a_flows if i in b_flows and a_flows[i] == b_flows[i]]
    if len(same) != len(a_flows):
        problems.append("Stage A flows changed")
        out.append("FAIL: Stage A flows changed: %s"
                   % [i for i in a_flows if a_flows.get(i) != b_flows.get(i)])
    else:
        out.append("OK: all %d Stage A flows identical (points, arrow, tip)"
                   % len(a_flows))

    a_tx, b_tx = spec_texts(A), spec_texts(B)
    moved = []
    for tid, t in a_tx.items():
        n = b_tx.get(tid)
        if n is None:
            problems.append("text %s missing" % tid)
            moved.append(tid + " missing")
            continue
        if tid in renamed:
            if (t["measured"][:2] != n["measured"][:2] or
                    t["size"] != n["size"] or t["weight"] != n["weight"] or
                    t["kind"] != n["kind"]):
                problems.append("renamed text %s moved/resized" % tid)
                moved.append(tid + " renamed but moved/resized")
            elif t["content"] == n["content"]:
                problems.append("text %s not renamed" % tid)
                moved.append(tid + " not renamed")
        elif t != n:
            problems.append("text %s changed" % tid)
            moved.append(tid + " changed")
    if moved:
        out.append("FAIL: %s" % moved)
    else:
        out.append("OK: %d Stage A texts unchanged; T02/T08 renamed in place "
                   "(same ink top-left %s / %s, same size, same weight)"
                   % (len(a_tx) - 2, a_tx["T02"]["measured"][:2],
                      a_tx["T08"]["measured"][:2]))

    # ---------------------------------------------------- (2) new elements
    out.append("")
    out.append("== (2) Stage B delta inventory ==")
    new_rects = [r for r in B["rects"] if r["name"] not in
                 {x["name"] for x in A["rects"]}]
    new_flows = [f for f in B["flows"] if f["id"] not in a_flows]
    new_texts = [t for t in B["texts"] if t["id"] not in a_tx]
    out.append("added rects (%d): %s"
               % (len(new_rects),
                  ", ".join("%s %s" % (r["name"], r["stroke_rect"])
                            for r in new_rects)))
    out.append("added flows (%d): %s"
               % (len(new_flows),
                  ", ".join("%s (%d pts, arrow at %s)"
                            % (f["id"], len(f["points"]), f["arrow_at"])
                            for f in new_flows)))
    out.append("added texts (%d): %s"
               % (len(new_texts),
                  ", ".join("%s %r" % (t["id"], t["content"])
                            for t in new_texts)))
    out.append("renamed texts: T02 %r -> %r ; T08 %r -> %r"
               % (a_tx["T02"]["content"], b_tx["T02"]["content"],
                  a_tx["T08"]["content"], b_tx["T08"]["content"]))
    if len(new_rects) != 2 or len(new_flows) != 3 or len(new_texts) != 5:
        problems.append("unexpected delta size")
        out.append("FAIL: expected +2 rects / +3 flows / +5 texts")
    else:
        out.append("OK: delta is exactly +2 boxes, +3 flows, +5 labels, "
                   "2 renames")

    # ---------------------------------------------------- (3) no crossing
    out.append("")
    out.append("== (3) new geometry vs everything else (no crossing) ==")
    a_segs = spec_segments(A)
    b_segs = spec_segments(B)
    a_ids = {s[0] for s in a_segs}
    # a segment is "new" when its tag does not exist in Stage A
    new_segs = [s for s in b_segs if s[0] not in a_ids]

    def base(tag):
        """Flow id without the ':arrow' suffix (line + arrowhead are one
        visual unit - the shaft legitimately runs through its triangle)."""
        return tag.split(":", 1)[0]

    out.append("stage A segments: %d ; stage B segments: %d ; new: %d"
               % (len(a_segs), len(b_segs), len(new_segs)))

    n_cross = n_touch = 0
    for tag, seg in new_segs:
        for otag, oseg in a_segs:
            if base(tag) == base(otag):
                continue
            p = seg_intersect(seg, oseg)
            if p is None:
                continue
            if near_endpoint(p, seg) or near_endpoint(p, oseg):
                n_touch += 1
                out.append("touch (connection point): new %s at (%.1f,%.1f) "
                           "on stage A %s" % (tag, p[0], p[1], otag))
            else:
                n_cross += 1
                msg = ("new segment %s (%.1f,%.1f)-(%.1f,%.1f) crosses stage "
                       "A %s at (%.1f,%.1f)"
                       % (tag, seg[0][0], seg[0][1], seg[1][0], seg[1][1],
                          otag, p[0], p[1]))
                problems.append(msg)
                out.append("FAIL: " + msg)
    for i in range(len(new_segs)):
        for j in range(i + 1, len(new_segs)):
            if base(new_segs[i][0]) == base(new_segs[j][0]):
                continue
            p = seg_intersect(new_segs[i][1], new_segs[j][1])
            if p is None:
                continue
            if near_endpoint(p, new_segs[i][1]) or \
               near_endpoint(p, new_segs[j][1]):
                n_touch += 1
                out.append("touch (connection point): new %s at (%.1f,%.1f) "
                           "on new %s" % (new_segs[i][0], p[0], p[1],
                                          new_segs[j][0]))
            else:
                n_cross += 1
                msg = ("new segment %s crosses new %s at (%.1f,%.1f)"
                       % (new_segs[i][0], new_segs[j][0], p[0], p[1]))
                problems.append(msg)
                out.append("FAIL: " + msg)

    # new segments vs every text bbox (Stage A + Stage B)
    all_tx = dict(a_tx)
    all_tx.update(b_tx)
    n_txt = 0
    for tag, seg in new_segs:
        for tid, t in sorted(all_tx.items()):
            if bbox_hits_segment(tuple(t["measured"]), seg):
                n_txt += 1
                msg = "new segment %s hits text %s %r bbox=%s" % (
                    tag, tid, t["content"], t["measured"])
                problems.append(msg)
                out.append("FAIL: " + msg)

    # new boxes vs everything
    for r in new_rects:
        bedges = rect_edges(*r["stroke_rect"])
        for e in bedges:
            for otag, oseg in a_segs:
                p = seg_intersect(e, oseg)
                if p is not None and not near_endpoint(p, e) and \
                   not near_endpoint(p, oseg):
                    msg = "new box %s edge crosses stage A %s at (%.1f,%.1f)" \
                          % (r["name"], otag, p[0], p[1])
                    problems.append(msg)
                    out.append("FAIL: " + msg)
            for tid, t in sorted(all_tx.items()):
                if bbox_hits_segment(tuple(t["measured"]), e):
                    msg = "new box %s edge hits text %s %r" % (
                        r["name"], tid, t["content"])
                    problems.append(msg)
                    out.append("FAIL: " + msg)

    if n_cross == 0 and n_txt == 0:
        out.append("OK: %d new segments x %d stage A segments + %d new-new "
                   "pairs + %d texts - 0 crossings (%d endpoint connections)"
                   % (len(new_segs), len(a_segs),
                      len(new_segs) * (len(new_segs) - 1) // 2,
                      len(all_tx), n_touch))
    else:
        out.append("FAIL: %d crossings, %d text hits" % (n_cross, n_txt))

    # ---------------------------------------------------- (4) clearances
    out.append("")
    out.append("== (4) new label clearances (nearest foreign segment) ==")
    foreign = [s for s in b_segs if s[0] not in
               {f["id"] for f in new_flows} and
               s[0] not in {"rect:%s" % r["name"] for r in new_rects}]
    for t in new_texts + [b_tx["T02"], b_tx["T08"]]:
        bb = tuple(t["measured"])
        gaps = sorted((seg_gap(bb, s[1]), s[0]) for s in foreign)
        g, tag = gaps[0]
        out.append("%-4s %-24r bbox=%s  nearest foreign segment %s at "
                   "%.1f px" % (t["id"], t["content"], list(bb), tag, g))

    out.append("")
    if problems:
        out.append("RESULT: FAIL (%d problem(s))" % len(problems))
    else:
        out.append("RESULT: PASS (unchanged elements intact, no crossing)")
    report = "\n".join(out) + "\n"
    sys.stdout.write(report)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()

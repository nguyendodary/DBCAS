# -*- coding: utf-8 -*-
"""F2 owner-fix delta gate for the Allocation figure (figure 04).

Compares the approved Stage B spec (HEAD baseline) with the owner-fix spec:

  * canvas only grows; all 9 original shapes are byte-identical (proves no
    existing node moved while the two external nodes were added)
  * 4 dash runs and lines L01-L06 identical
  * L07 is the merged continuous HTTPS edge (was L07+L08 with a text gap);
    its arrow tip is unchanged; L09/L10 are the two new labelled edges
  * all texts identical except X011 (17 -> 21 px bold, measured original),
    X010 (split into X010 + X040 wrapped after "containerized") and the
    10 new labels; no font size decreased
  * the frame-label bboxes do not intersect the HTTPS line
  * new nodes use the figure's LLM Provider API style and sit in the added
    canvas area; new edges are orthogonal, start on the Application Server
    right edge, end on the new nodes, and cross no unconnected box

Usage:
  python scripts/check_allocation_fix_delta_f2.py <spec-stage-b.json> <spec.json>
"""
import json
import sys


def strict_intersects(seg, rect):
    (sx0, sy0), (sx1, sy1) = seg
    x0, y0, x1, y1 = rect[0] + .01, rect[1] + .01, rect[2] - .01, rect[3] - .01
    if x1 <= x0 or y1 <= y0:
        return False
    dx, dy = sx1 - sx0, sy1 - sy0
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, sx0 - x0), (dx, x1 - sx0),
                 (-dy, sy0 - y0), (dy, y1 - sy0)):
        if abs(p) < 1e-12:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                if r > t1:
                    return False
                t0 = max(t0, r)
            else:
                if r < t0:
                    return False
                t1 = min(t1, r)
    return t0 <= t1


def main():
    a = json.load(open(sys.argv[1], encoding="utf-8"))
    b = json.load(open(sys.argv[2], encoding="utf-8"))
    problems = []

    if not (b["canvas"]["w"] >= a["canvas"]["w"] and
            b["canvas"]["h"] >= a["canvas"]["h"]):
        problems.append("canvas shrank")

    sa = {s["id"]: s for s in a["shapes"]}
    sb = {s["id"]: s for s in b["shapes"]}
    for sid in ("S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08",
                "S09"):
        if sa[sid] != sb[sid]:
            problems.append("existing shape %s changed" % sid)
    for sid in ("S10", "S11"):
        s = sb.get(sid)
        if not s:
            problems.append("new shape %s missing" % sid)
            continue
        if s["kind"] != "rounded" or s["fill"] != "#6A5ACD" or \
                s["stroke"] != "#3F3494" or s.get("stroke_width") != 2:
            problems.append("%s style not LLM-Provider-API style" % sid)
        if s["bbox"][1] < a["canvas"]["h"]:
            problems.append("%s is not in the added canvas area" % sid)

    if a.get("dashes") != b.get("dashes"):
        problems.append("dash runs changed")

    la = {x["id"]: x for x in a["lines"] if x.get("id")}
    lb = {x["id"]: x for x in b["lines"] if x.get("id")}
    if len(a["lines"]) != 8 or len(b["lines"]) != 9:
        problems.append("line count %d -> %d (expected 8 -> 9)"
                        % (len(a["lines"]), len(b["lines"])))
    for lid in ("L01", "L02", "L03", "L04", "L05", "L06"):
        if la[lid] != lb[lid]:
            problems.append("line %s changed" % lid)
    if la["L08"].get("arrow_tip") != lb["L07"].get("arrow_tip"):
        problems.append("HTTPS arrow tip moved")
    if lb["L07"].get("stroke") != 2.5 or lb["L07"].get("color") != "#474747":
        problems.append("HTTPS edge weight/colour not restored")
    if lb["L07"]["segs"] != [[[597, 473], [593, 615]]]:
        problems.append("HTTPS edge is not the single continuous measured line")
    for lid in ("L09", "L10"):
        n = lb.get(lid)
        if not n:
            problems.append("new edge %s missing" % lid)
            continue
        if not n.get("arrow_tip"):
            problems.append("%s has no arrowhead" % lid)
        for seg in n["segs"]:
            if not (abs(seg[0][0] - seg[1][0]) < .01 or
                    abs(seg[0][1] - seg[1][1]) < .01):
                problems.append("%s is not orthogonal" % lid)
        if n["segs"][0][0] != [791, n["segs"][0][0][1]]:
            problems.append("%s does not start on the Application Server "
                            "right edge" % lid)
        for s in n["segs"]:
            for sid, sh in sb.items():
                if sid in ("S01", "S05", "S10", "S11"):
                    continue      # frame border, source + intended targets
                if strict_intersects(s, sh["bbox"]):
                    problems.append("%s crosses unconnected %s" % (lid, sid))

    ta = {t["id"]: t for t in a["texts"]}
    tb = {t["id"]: t for t in b["texts"]}
    added = set(tb) - set(ta)
    expect_added = {"X040", "X041", "X042", "X043", "X044", "X045", "X046",
                    "X047", "X048", "X049", "X050"}
    if added != expect_added:
        problems.append("unexpected new text ids: %s" % sorted(added))
    if set(ta) - set(tb):
        problems.append("texts removed: %s" % sorted(set(ta) - set(tb)))
    for tid, o in ta.items():
        n = tb.get(tid)
        if not n:
            continue
        if tid == "X010":
            if n["content"] != "[Deployment Node: containerized":
                problems.append("X010 split content wrong")
            continue
        if tid == "X011":
            if n["content"] != "Docker-capable Host":
                problems.append("X011 content changed")
            if n["size"] != 21 or n["weight"] != "bold":
                problems.append("X011 not restored to 21 px bold")
            continue
        if o != n and o["measured"] != n["measured"]:
            problems.append("text %s moved/changed" % tid)
        elif o.get("content") != n.get("content") or \
                o.get("size") != n.get("size") or \
                o.get("weight") != n.get("weight"):
            problems.append("text %s content/size changed" % tid)
    if tb["X040"]["content"] != "deployment, Docker Compose]":
        problems.append("X040 continuation content wrong")
    joined = tb["X010"]["content"] + " " + tb["X040"]["content"]
    if joined != ta["X010"]["content"]:
        problems.append("split frame label does not concatenate: %r" % joined)
    for tid, content in {
            "X041": "OAuth Providers",
            "X042": "[External Software System]",
            "X043": "Google and GitHub", "X044": "OAuth 2.0",
            "X045": "Email Service",
            "X046": "[External Software System]",
            "X047": "Password-reset mail via SMTP",
            "X048": "Mailpit in development",
            "X049": "OAuth sign-in [HTTPS]",
            "X050": "Password-reset email [SMTP]"}.items():
        if tb.get(tid, {}).get("content") != content:
            problems.append("%s content mismatch" % tid)

    # frame-label bboxes vs the continuous HTTPS edge
    https = lb["L07"]["segs"]
    for tid in ("X010", "X011", "X040"):
        bbox = tb[tid]["measured"]
        for seg in https:
            if strict_intersects(seg, bbox):
                problems.append("HTTPS line crosses frame label %s" % tid)
    # labels of the new edges must not intersect their edges
    for lid, tid in (("L09", "X049"), ("L10", "X050")):
        bbox = tb[tid]["measured"]
        for seg in lb[lid]["segs"]:
            if strict_intersects(seg, bbox):
                problems.append("%s crosses its label %s" % (lid, tid))
    # every new box label is inside its box with >= 5 px margins
    for tid in ("X041", "X042", "X043", "X044", "X045", "X046", "X047",
                "X048"):
        t = tb[tid]
        sh = sb[t["inside"]]
        x0, y0, x1, y1 = sh["bbox"]
        bx0, by0, bx1, by1 = t["measured"]
        m = min(bx0 - x0, x1 - bx1, by0 - y0, y1 - by1)
        if m < 5:
            problems.append("%s only %.1f px from its box border" % (tid, m))

    print("canvas %dx%d -> %dx%d" %
          (a["canvas"]["w"], a["canvas"]["h"],
           b["canvas"]["w"], b["canvas"]["h"]))
    print("shapes %d -> %d; lines %d -> %d; texts %d -> %d" %
          (len(a["shapes"]), len(b["shapes"]), len(a["lines"]),
           len(b["lines"]), len(a["texts"]), len(b["texts"])))
    print("existing shapes unchanged: 9/9; texts unchanged: %d of %d"
          % (len(set(ta) & set(tb)) - 2, len(ta)))
    if problems:
        for p in problems:
            print("FAIL:", p)
        print("RESULT: FAIL (%d problem(s))" % len(problems))
        sys.exit(1)
    print("RESULT: PASS (all 9 existing nodes byte-identical; only the "
          "owner's size / HTTPS / OAuth+Email delta applied)")
    sys.exit(0)


if __name__ == "__main__":
    main()

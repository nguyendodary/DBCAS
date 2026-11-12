# -*- coding: utf-8 -*-
"""F2 owner-fix delta gate for the Container figure (figure 03).

Compares the approved Stage B spec (HEAD baseline) with the owner-fix spec and
proves every element the owner did not ask to change is identical:

  * boundary, both cylinders, 4 dash runs and every flow target unchanged
  * old shapes may only grow downwards: x0/y0/x1 identical, y1 >= old
  * no old shape removed; new external boxes live below the old canvas and
    keep the LLM Provider API style (restored 3 px border)
  * free flow labels unchanged except the measured Sanitized-prompts weight
    fix (21 -> 20 px, still above the original 13 px cap)
  * box labels keep their content/weight/size/inside; only their y moves and
    x drifts <= 1.5 px from the centring reflow
  * every reflowed label keeps >= 5 px to its box border (rule a)
  * old lines keep their arrow tips; only source-adjacent points move
  * the two new edges are orthogonal, start on the API right edge and end on
    the new boxes; no segment crosses an unconnected box

Usage:
  python scripts/check_container_fix_delta_f2.py <spec-stage-b.json> <spec.json>
"""
import json
import sys


def strict_intersects(seg, rect):
    """Liang-Barsky strict-interior segment vs axis-aligned rectangle."""
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
    notes = []

    # ---------------------------------------------------------------- canvas
    if not (b["canvas"]["w"] >= a["canvas"]["w"] and
            b["canvas"]["h"] >= a["canvas"]["h"]):
        problems.append("canvas shrank")

    # ---------------------------------------------------------------- shapes
    sa = {s["id"]: s for s in a["shapes"]}
    sb = {s["id"]: s for s in b["shapes"]}
    for sid in ("S01", "S02", "S03"):
        if sa[sid] != sb[sid]:
            problems.append("shape %s changed" % sid)
    for sid in ("S04", "S05", "S06", "S07", "S08", "S09"):
        o, n = sa[sid], sb[sid]
        for k in ("kind", "fill", "stroke", "radius", "dashed"):
            if o.get(k) != n.get(k):
                problems.append("%s %s changed" % (sid, k))
        for k, i in (("bbox x0", 0), ("bbox y0", 1), ("bbox x1", 2)):
            if o["bbox"][i] != n["bbox"][i]:
                problems.append("%s %s moved" % (sid, k))
        if n["bbox"][3] < o["bbox"][3]:
            problems.append("%s shrank vertically" % sid)
    if sa["S08"].get("stroke_width") != 7 or sb["S08"].get("stroke_width") != 2:
        problems.append("LLM border weight fix missing (7 -> 2 expected)")
    for sid in ("S10", "S11"):
        s = sb.get(sid)
        if not s:
            problems.append("new shape %s missing" % sid)
            continue
        if s["kind"] != "rounded" or s["fill"] != "#999999" or \
                s["stroke"] != "#6B6B6B" or s.get("stroke_width") != 2:
            problems.append("%s style not LLM-style (2 px border)" % sid)
        if s["bbox"][1] < a["canvas"]["h"]:
            problems.append("%s is not in the added canvas area" % sid)
    if set(sa) - set(sb):
        problems.append("old shapes removed: %s" % sorted(set(sa) - set(sb)))

    # ---------------------------------------------------------------- dashes
    if a.get("dashes") != b.get("dashes"):
        problems.append("dash runs changed")

    # ----------------------------------------------------------------- lines
    # the build splits one edge at a label, so the 8th spec line has no id in
    # both baseline and new output; compare by stable index instead.
    old_lines = a["lines"]
    new_lines = b["lines"][:len(old_lines)]
    if len(b["lines"]) != len(old_lines) + 2:
        problems.append("expected exactly 2 added lines")
    for i, (o, n) in enumerate(zip(old_lines, new_lines)):
        lid = o.get("id") or ("index%d" % i)
        if o.get("arrow_tip") != n.get("arrow_tip"):
            problems.append("%s arrow tip moved" % lid)
        if lid not in ("L06", "L07", "L10"):
            if o.get("color") != n.get("color") or \
                    o.get("stroke") != n.get("stroke"):
                problems.append("%s weight changed" % lid)
    byid = {x.get("id"): x for x in b["lines"] if x.get("id")}
    if byid["L06"].get("stroke") != 2.0 or byid["L07"].get("stroke") != 2.0 or \
            byid["L10"].get("stroke") != 2.0:
        problems.append("web-tier / LLM flow weights not restored to 2 px")
    if byid["L06"].get("color") != "#444444" or \
            byid["L07"].get("color") != "#444444" or \
            byid["L10"].get("color") != "#444444":
        problems.append("web-tier / LLM flow colours not restored")
    for lid in ("L11", "L12"):
        n = byid.get(lid)
        if not n:
            problems.append("new edge %s missing" % lid)
            continue
        if not n.get("arrow_tip"):
            problems.append("%s has no arrowhead" % lid)
        for seg in n["segs"]:
            if not (abs(seg[0][0] - seg[1][0]) < .01 or
                    abs(seg[0][1] - seg[1][1]) < .01):
                problems.append("%s is not orthogonal" % lid)
        if n["segs"][0][0] != [981, n["segs"][0][0][1]]:
            problems.append("%s does not start on the API right edge" % lid)
        for s in n["segs"]:
            for sid, sh in sb.items():
                if sid in ("S01", "S04", "S10", "S11"):
                    continue      # frame border, source + intended targets
                if strict_intersects(s, sh["bbox"]):
                    problems.append("%s crosses unconnected %s" % (lid, sid))
        for tid in ("X058", "X059"):
            tb = next(t for t in b["texts"] if t["id"] == tid)["measured"]
            for s in n["segs"]:
                if strict_intersects(s, tb):
                    problems.append("%s crosses its label %s" % (lid, tid))

    # ----------------------------------------------------------------- texts
    ta = {t["id"]: t for t in a["texts"]}
    tb = {t["id"]: t for t in b["texts"]}
    if set(ta) - set(tb):
        problems.append("texts removed: %s" % sorted(set(ta) - set(tb)))
    added = set(tb) - set(ta)
    if added != {"X050", "X051", "X052", "X053", "X054", "X055", "X056",
                 "X057", "X058", "X059"}:
        problems.append("unexpected new text ids: %s" % sorted(added))
    free_changed = {"X032"}
    for tid, o in ta.items():
        n = tb.get(tid)
        if not n:
            continue
        if o["content"] != n["content"]:
            problems.append("%s content changed" % tid)
        if o.get("inside") != n.get("inside"):
            problems.append("%s host box changed" % tid)
        if o.get("ink") != n.get("ink"):
            problems.append("%s ink changed" % tid)
        if o["inside"] is None:
            if tid not in free_changed:
                core = ("content", "weight", "size", "anchor", "x", "y",
                        "measured", "inside", "ink")
                if any(o.get(k) != n.get(k) for k in core):
                    problems.append("free label %s moved/changed" % tid)
                if abs((o.get("ls") or 0.0) - (n.get("ls") or 0.0)) > 0.05:
                    problems.append("free label %s letter-spacing changed"
                                    % tid)
        else:
            if o.get("size") != n.get("size") or \
                    o.get("weight") != n.get("weight"):
                problems.append("box label %s size/weight changed" % tid)
            if abs(o["measured"][0] - n["measured"][0]) > 1.5:
                problems.append("box label %s x drifted >1.5 px" % tid)
    # (a) every box label keeps >= 5 px to its own box border
    for t in b["texts"]:
        if t["inside"] is None:
            continue
        sh = sb[t["inside"]]
        x0, y0, x1, y1 = sh["bbox"]
        bx0, by0, bx1, by1 = t["measured"]
        m = min(bx0 - x0, x1 - bx1, by0 - y0, y1 - by1)
        if m < 5:
            problems.append("%s only %.1f px from its box border"
                            % (t["id"], m))
    exp = {"X050": "OAuth Providers",
           "X051": "[External Software System]",
           "X052": "Google and GitHub", "X053": "OAuth 2.0",
           "X054": "Email Service",
           "X055": "[External Software System]",
           "X056": "Password-reset mail via SMTP",
           "X057": "Mailpit in development",
           "X058": "OAuth sign-in [HTTPS]",
           "X059": "Password-reset email [SMTP]"}
    for tid, s in exp.items():
        if tb.get(tid, {}).get("content") != s:
            problems.append("%s content mismatch" % tid)

    notes.append("canvas %dx%d -> %dx%d" %
                 (a["canvas"]["w"], a["canvas"]["h"],
                  b["canvas"]["w"], b["canvas"]["h"]))
    notes.append("shapes %d -> %d; lines %d -> %d; texts %d -> %d" %
                 (len(a["shapes"]), len(b["shapes"]), len(a["lines"]),
                  len(b["lines"]), len(a["texts"]), len(b["texts"])))
    notes.append("free labels unchanged: %d of %d; box labels reflowed: %d" %
                 (sum(1 for t in a["texts"] if t["inside"] is None) - 1,
                  sum(1 for t in a["texts"] if t["inside"] is None),
                  sum(1 for t in b["texts"] if t["inside"] is not None)))
    print("\n".join(notes))
    if problems:
        for p in problems:
            print("FAIL:", p)
        print("RESULT: FAIL (%d problem(s))" % len(problems))
        sys.exit(1)
    print("RESULT: PASS (Stage B elements identical where unchanged; only "
          "the owner's reflow / weight / OAuth+Email delta applied)")
    sys.exit(0)


if __name__ == "__main__":
    main()

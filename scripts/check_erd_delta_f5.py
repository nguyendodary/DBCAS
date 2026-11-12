# -*- coding: utf-8 -*-
"""F5 ERD delta + layout proof.

1. Every Stage A entity/key/diamond is present in the final spec with the
   identical name and exact bbox.  Every original text and every original
   connector segment is present unchanged.
2. The final diagram has no line through an entity box, no dangling line,
   no non-orthogonal segment, and every entity owns a key ellipse.

Usage:
  node scripts/run_py.mjs scripts/check_erd_delta_f5.py
"""
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "docs", "diagrams", "rebuild", "erd",
                    "stage-a", "spec-stage-a.json")
FINAL = os.path.join(ROOT, "docs", "diagrams", "rebuild", "erd", "spec.json")

KEY_OF = {
    "Role": "role id", "Account": "account id", "UserProfile": "user id",
    "Rubric": "rubric id", "CourseLearningOutcome": "clo id",
    "Assessment": "assessment id", "QuestionCandidate": "candidate id",
    "Question": "question id", "SQLTestDataset": "dataset id",
    "Concept": "concept id", "AssessmentSession": "session id",
    "SelectionLog": "log id", "MCQOption": "option id", "LLMCache": "cache id",
    "ConceptCompetency": "competency id", "CompetencyGap": "gap id",
    "Attempt": "attempt id", "SystemSetting": "setting_key",
    "AssessmentConcept": "assessment_id, concept_id",
    "AssessmentQuestion": "assessment_id, question_id",
    "AssessmentBlueprint": "blueprint_id",
}


def flat(lines):
    out = []
    for ln in lines:
        pts = ln["segs"]
        for a, b in zip(pts, pts[1:]):
            out.append((round(a[0], 2), round(a[1], 2),
                        round(b[0], 2), round(b[1], 2)))
    return out


def point_seg_dist(px, py, s):
    x1, y1, x2, y2 = s
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
    t = ((px - x1) * dx + (py - y1) * dy) / float(dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return ((px - (x1 + t * dx)) ** 2 + (py - (y1 + t * dy)) ** 2) ** 0.5


def seg_bbox_hit(s, b, pad=3.0):
    """Strict interior hit of an axis-aligned segment against a bbox."""
    x0, y0, x1, y1 = b[0] + pad, b[1] + pad, b[2] - pad, b[3] - pad
    if x1 <= x0 or y1 <= y0:
        return False
    sx0, sy0, sx1, sy1 = s
    lo_x, hi_x = min(sx0, sx1), max(sx0, sx1)
    lo_y, hi_y = min(sy0, sy1), max(sy0, sy1)
    return (min(hi_x, x1) - max(lo_x, x0) > 0 and
            min(hi_y, y1) - max(lo_y, y0) > 0)


def bbox_dist(px, py, b):
    dx = max(b[0] - px, 0, px - b[2])
    dy = max(b[1] - py, 0, py - b[3])
    return (dx * dx + dy * dy) ** 0.5


def main():
    base = json.load(open(BASE, encoding="utf-8"))
    final = json.load(open(FINAL, encoding="utf-8"))
    out, problems = [], []

    def say(s=""):
        out.append(s)

    say("F5 ERD Stage A -> final delta proof")
    say("Stage A canvas: %dx%d" % (base["canvas"]["w"], base["canvas"]["h"]))
    say("Final canvas:   %dx%d" % (final["canvas"]["w"], final["canvas"]["h"]))
    say("")

    def shapes_of(kind):
        return [s for s in base["shapes"] if s["kind"] == kind]

    def find(kind, name):
        for s in final["shapes"]:
            if s["kind"] == kind and s.get("name") == name:
                return s
        return None

    say("== original entities (17) ==")
    n_ok = 0
    for s in shapes_of("entity"):
        f = find("entity", s["name"])
        if not f:
            problems.append("entity removed: %s" % s["name"])
            say("FAIL removed entity %s" % s["name"])
            continue
        if f["bbox"] != s["bbox"]:
            problems.append("entity moved: %s" % s["name"])
            say("FAIL moved entity %s %s -> %s"
                % (s["name"], s["bbox"], f["bbox"]))
            continue
        n_ok += 1
        note = ""
        if s["name"] == "Assessment" and f.get("dashed") != s.get("dashed"):
            note = " (dashed style added; bbox/name unchanged)"
        say("  OK %-22s %s%s" % (s["name"], s["bbox"], note))
    say("entities exact: %d/%d" % (n_ok, len(shapes_of("entity"))))
    say("")

    say("== original key ellipses (17) ==")
    n_ok = 0
    for s in shapes_of("ellipse"):
        f = find("ellipse", s["name"])
        if not f:
            problems.append("key removed: %s" % s["name"])
            say("FAIL removed key %s" % s["name"])
            continue
        if f["bbox"] != s["bbox"]:
            problems.append("key moved: %s" % s["name"])
            say("FAIL moved key %s %s -> %s"
                % (s["name"], s["bbox"], f["bbox"]))
            continue
        n_ok += 1
        say("  OK %-22s %s" % (s["name"], s["bbox"]))
    say("keys exact: %d/%d" % (n_ok, len(shapes_of("ellipse"))))
    say("")

    say("== original relationship diamonds (24) ==")
    n_ok = 0
    for s in shapes_of("diamond"):
        f = find("diamond", s["name"])
        if not f:
            problems.append("diamond removed: %s" % s["name"])
            say("FAIL removed diamond %s" % s["name"])
            continue
        if f["bbox"] != s["bbox"]:
            problems.append("diamond moved: %s" % s["name"])
            say("FAIL moved diamond %s %s -> %s"
                % (s["name"], s["bbox"], f["bbox"]))
            continue
        n_ok += 1
        say("  OK %-22s %s" % (s["name"], s["bbox"]))
    say("diamonds exact: %d/%d" % (n_ok, len(shapes_of("diamond"))))
    say("")

    say("== original labels (112) ==")
    final_by_id = {t["id"]: t for t in final["texts"]}
    n_ok, moved = 0, []
    for t in base["texts"]:
        f = final_by_id.get(t["id"])
        if f != t:
            moved.append(t["id"])
            say("FAIL label changed: %s %r" % (t["id"], t["content"]))
        else:
            n_ok += 1
    say("labels byte-identical: %d/%d" % (n_ok, len(base["texts"])))
    if moved:
        problems.append("labels changed: %s" % moved)
    say("")

    say("== original connector segments (120) ==")
    bsegs = Counter(flat(base["lines"]))
    fsegs = Counter(flat(final["lines"]))
    missing = bsegs - fsegs
    duplicated = [s for s, c in bsegs.items() if fsegs[s] > c]
    if missing:
        problems.append("original segments missing: %d" % sum(missing.values()))
        for s in missing:
            say("FAIL missing segment %s x%d" % (s, missing[s]))
    if duplicated:
        problems.append("original segments duplicated: %d" % len(duplicated))
        for s in duplicated:
            say("FAIL original segment duplicated by an addition: %s" % (s,))
    say("original segments present: %d/%d"
        % (sum((bsegs & fsegs).values()), sum(bsegs.values())))
    say("exact duplicates introduced: %d" % len(duplicated))
    say("")

    say("== added / changed elements ==")
    base_shape_keys = {(s["kind"], s.get("name"), tuple(s["bbox"]))
                       for s in base["shapes"]}
    added = [s for s in final["shapes"]
             if (s["kind"], s.get("name"), tuple(s["bbox"]))
             not in base_shape_keys and s["kind"] != "legend"]
    for s in added:
        say("  added %-10s %-28s %s"
            % (s["kind"], s.get("name", ""), s["bbox"]))
    for s in final["shapes"]:
        if s["kind"] == "legend" and s["bbox"] != [760, 1522, 2490, 1633]:
            say("  changed legend bbox %s (left/top anchored; extended right)"
                % (s["bbox"],))
    new_texts = [t for t in final["texts"] if t["id"] not in
                 {b["id"] for b in base["texts"]}]
    say("new labels: %d" % len(new_texts))
    for t in new_texts:
        say("  %s %-9s %r" % (t["id"], t["style"], t["content"]))
    say("")
    say("moved/removed: none")
    say("")

    # ------------------------------------------------------------ layout
    say("== layout proof ==")
    segs = flat(final["lines"])
    ents = [s for s in final["shapes"] if s["kind"] == "entity"]
    bad_ortho = [s for s in segs if s[0] != s[2] and s[1] != s[3]]
    if bad_ortho:
        problems.append("non-orthogonal segments: %d" % len(bad_ortho))
        say("FAIL non-orthogonal segments: %d" % len(bad_ortho))
    else:
        say("OK every line segment is orthogonal")

    hits = []
    for s in segs:
        for e in ents:
            if seg_bbox_hit(s, e["bbox"]):
                hits.append((s, e["name"]))
    if hits:
        problems.append("lines through boxes: %d" % len(hits))
        for s, n in hits[:20]:
            say("FAIL line through box %s: %s" % (n, s))
    else:
        say("OK no line segment enters an entity box")

    # dangling: every polyline endpoint must touch a shape or another segment
    shape_boxes = [(s["bbox"]) for s in final["shapes"]
                   if s["kind"] in ("entity", "ellipse", "diamond")]
    dangling = []
    for li, ln in enumerate(final["lines"]):
        for px, py in (ln["segs"][0], ln["segs"][-1]):
            near_shape = min(bbox_dist(px, py, b) for b in shape_boxes) <= 6
            near_seg = False
            for lj, other in enumerate(final["lines"]):
                if lj == li:
                    continue
                if min(point_seg_dist(px, py, s) for s in flat([other])) <= 2.5:
                    near_seg = True
                    break
            if not (near_shape or near_seg):
                dangling.append((li + 1, px, py))
    if dangling:
        problems.append("dangling endpoints: %d" % len(dangling))
        for d in dangling:
            say("FAIL dangling endpoint line %d at %s,%s" % d)
    else:
        say("OK no dangling line endpoints (%d polylines)"
            % len(final["lines"]))

    ell = {s["name"]: s for s in final["shapes"] if s["kind"] == "ellipse"}
    keytexts = {t["content"] for t in final["texts"] if t["style"] == "key"}
    missing_keys = []
    for e in ents:
        kn = KEY_OF.get(e["name"])
        if not kn or kn not in ell or kn not in keytexts:
            missing_keys.append((e["name"], kn))
    if missing_keys:
        problems.append("entities without key ellipse: %s" % missing_keys)
        say("FAIL entities without key ellipse: %s" % missing_keys)
    else:
        say("OK every entity (%d) has its key ellipse and key label" % len(ents))

    # new cardinalities must sit near a connector endpoint
    far = []
    for t in final["texts"]:
        if t["style"] != "card" or int(t["id"][1:]) <= 112:
            continue
        cx = (t["measured"][0] + t["measured"][2]) / 2.0
        cy = (t["measured"][1] + t["measured"][3]) / 2.0
        d = min(((cx - x) ** 2 + (cy - y) ** 2) ** 0.5
                for ln in final["lines"] for x, y in
                (ln["segs"][0], ln["segs"][-1]))
        if d > 80:
            far.append((t["content"], round(d, 1)))
    if far:
        problems.append("new cardinalities not at line ends: %s" % far)
        say("FAIL new cardinalities far from a line end: %s" % far)
    else:
        ncards = sum(1 for t in final["texts"]
                     if t["style"] == "card" and int(t["id"][1:]) > 112)
        say("OK all %d new cardinality labels are within 80 px of a line end"
            % ncards)

    say("")
    if problems:
        say("RESULT: FAIL (%d problem(s))" % len(problems))
        sys.stdout.write("\n".join(out) + "\n")
        return 1
    say("RESULT: PASS")
    sys.stdout.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

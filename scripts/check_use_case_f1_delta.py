# -*- coding: utf-8 -*-
"""F1 owner-fix delta gate for the Use Case figure.

Proves that the right-margin fix changed ONLY the canvas width:

  * Stage B canvas 3000x3300 -> F1 canvas 3120x3300 (height unchanged)
  * every shape, line, dash and stick is identical (dict equality)
  * every text is identical (content, x, y, size, weight, letter-spacing,
    measured band, host) - the Administrator actor and label do not move
  * the Administrator label's right ink edge keeps >= 120 px of clear
    canvas margin, and its measured bbox stays centred under the actor

Usage:
  python scripts/check_use_case_f1_delta.py <spec-stage-b.json> <spec.json>
Exit 0 = PASS.
"""
import json
import sys

MIN_RIGHT_MARGIN = 120


def main():
    a = json.load(open(sys.argv[1], encoding="utf-8"))
    b = json.load(open(sys.argv[2], encoding="utf-8"))
    problems = []

    ca, cb = a["canvas"], b["canvas"]
    if ca["h"] != cb["h"]:
        problems.append("canvas height changed %s -> %s" % (ca["h"], cb["h"]))
    if cb["w"] <= ca["w"]:
        problems.append("canvas width did not grow %s -> %s"
                        % (ca["w"], cb["w"]))
    if cb["w"] != 3120:
        problems.append("unexpected F1 canvas width %s" % cb["w"])

    for key in ("shapes", "lines", "sticks", "dashes"):
        if a.get(key) != b.get(key):
            problems.append("%s changed" % key)

    ta = {t["id"]: t for t in a["texts"]}
    tb = {t["id"]: t for t in b["texts"]}
    if set(ta) != set(tb):
        problems.append("text ids changed: %s"
                        % sorted(set(ta) ^ set(tb)))
    for tid in sorted(set(ta) & set(tb)):
        if ta[tid] != tb[tid]:
            problems.append("text %s differs" % tid)

    label = tb.get("X014")
    actor = next((s for s in b.get("sticks", []) if s["id"] == "K02"), None)
    if label is None:
        problems.append("Administrator label X014 missing")
    else:
        right = label["measured"][2]
        margin = cb["w"] - right
        if margin < MIN_RIGHT_MARGIN:
            problems.append("Administrator right margin %s < %s"
                            % (margin, MIN_RIGHT_MARGIN))
        center = (label["measured"][0] + right) / 2.0
        if actor is None:
            problems.append("Administrator actor K02 missing")
        else:
            ax = actor["circle"][0]
            if abs(center - ax) > 2.0:
                problems.append("label centre %.1f not under actor %.1f"
                                % (center, ax))

    print("canvas: %sx%s -> %sx%s (only width changed)"
          % (ca["w"], ca["h"], cb["w"], cb["h"]))
    print("shapes: %d = %d; lines: %d = %d; sticks: %d = %d; dashes: %d = %d"
          % (len(a["shapes"]), len(b["shapes"]), len(a["lines"]),
             len(b["lines"]), len(a.get("sticks", [])),
             len(b.get("sticks", [])), len(a.get("dashes", [])),
             len(b.get("dashes", []))))
    print("texts: %d = %d; every text identical" % (len(ta), len(tb)))
    if label:
        print("Administrator X014 measured %s, right edge %s, canvas %s, "
              "right margin %s px"
              % (label["measured"], label["measured"][2], cb["w"],
                 cb["w"] - label["measured"][2]))
    if problems:
        for p in problems:
            print("FAIL:", p)
        print("RESULT: FAIL (%d problem(s))" % len(problems))
        sys.exit(1)
    print("RESULT: PASS (only the canvas width grew; every element is "
          "byte-identical to Stage B)")
    sys.exit(0)


if __name__ == "__main__":
    main()

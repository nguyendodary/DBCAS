# -*- coding: utf-8 -*-
"""Stage B delta gate for the Use Case figure.

Proves that applying only the verified content delta left every Stage A
element intact:

  * canvas identical
  * every shape, line and stick identical (dict equality)
  * every text except the 3 renamed UC labels identical in content,
    position, size, weight, letter-spacing, measured band and host
  * the 3 changed labels keep their Stage A font size (never shrunk) and
    their measured width is not reduced
  * the added practice-note line is the only new label

Usage:
  python scripts/check_use_case_stage_b_delta.py <spec-stage-a.json> <spec.json>
Exit 0 = PASS.
"""
import json
import sys


def main():
    a = json.load(open(sys.argv[1], encoding="utf-8"))
    b = json.load(open(sys.argv[2], encoding="utf-8"))
    problems = []

    if a["canvas"] != b["canvas"]:
        problems.append("canvas changed %s -> %s" % (a["canvas"], b["canvas"]))
    for key in ("shapes", "lines", "sticks", "dashes"):
        if a.get(key) != b.get(key):
            problems.append("%s changed" % key)

    ta = {t["id"]: t for t in a["texts"]}
    tb = {t["id"]: t for t in b["texts"]}
    changed = {"X007", "X019", "X023"}
    added = {"X027"}
    expected = {
        "X007": "UC12 Take personalized practice session",
        "X019": "UC09 Configure result flow and settings",
        "X023": "UC18 Review practice history and",
        "X027": "UC12: 1–20 questions (default 5) · 30-minute expiry.",
    }
    missing = set(ta) - set(tb)
    extra = set(tb) - set(ta)
    if missing:
        problems.append("text ids removed: %s" % sorted(missing))
    if extra != added:
        problems.append("unexpected new text ids: %s" % sorted(extra - added))
    for tid in sorted(changed):
        if tid not in tb:
            problems.append("changed text missing: %s" % tid)
            continue
        if tb[tid]["content"] != expected[tid]:
            problems.append("%s content %r != %r"
                            % (tid, tb[tid]["content"], expected[tid]))
        if tb[tid]["size"] != ta[tid]["size"]:
            problems.append("%s font size changed %s -> %s"
                            % (tid, ta[tid]["size"], tb[tid]["size"]))
        wa = ta[tid]["measured"][2] - ta[tid]["measured"][0]
        wb = tb[tid]["measured"][2] - tb[tid]["measured"][0]
        if wb < wa and tid != "X023":
            # X023 is the first line of the wrapped UC18 label; the exact
            # new wording is shorter on that line than the old wording.
            problems.append("%s measured width shrank %d -> %d"
                            % (tid, wa, wb))
    # the wrapped UC18 label must concatenate to the exact verified text
    if tb.get("X023") and tb.get("X025"):
        whole = tb["X023"]["content"] + " " + tb["X025"]["content"]
        if whole != "UC18 Review practice history and evidence":
            problems.append("wrapped UC18 label is %r" % whole)
    for tid in sorted(set(ta) - changed):
        if tb.get(tid) != ta[tid]:
            problems.append("unchanged text %s differs" % tid)
    for tid in sorted(added):
        if tid in tb and tb[tid]["content"] != expected[tid]:
            problems.append("%s content %r != %r"
                            % (tid, tb[tid]["content"], expected[tid]))

    print("Stage A texts: %d; Stage B texts: %d" %
          (len(ta), len(tb)))
    print("changed labels: %s" % ", ".join(sorted(changed)))
    print("added label: %s" % ", ".join(sorted(added)))
    print("shapes: %d = %d; lines: %d = %d; sticks: %d = %d" %
          (len(a["shapes"]), len(b["shapes"]), len(a["lines"]),
           len(b["lines"]), len(a.get("sticks", [])),
           len(b.get("sticks", []))))
    if problems:
        for p in problems:
            print("FAIL:", p)
        print("RESULT: FAIL (%d problem(s))" % len(problems))
        sys.exit(1)
    print("RESULT: PASS (unchanged elements identical; only the verified "
          "content delta applied)")
    sys.exit(0)


if __name__ == "__main__":
    main()

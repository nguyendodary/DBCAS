# -*- coding: utf-8 -*-
"""Stage B delta gate for the Allocation figure.

  * canvas, 9 shapes, 4 dash runs and 8 lines identical
  * every text except X020/X021/X038 identical
  * the three rewritten labels keep their Stage A font size
  * no Email/OAuth node was invented (shapes identical proves it)

Usage:
  python scripts/check_allocation_stage_b_delta.py <spec-stage-a.json> <spec.json>
Exit 0 = PASS.
"""
import json
import sys


CHANGED = {"X020", "X021", "X038"}
EXPECT = {
    "X020": "Business logic: JWT / RBAC, grading,",
    "X021": "practice plan assembly, competency engine",
    "X038": "learner role; 256 MB, 3 s timeout",
}


def main():
    a = json.load(open(sys.argv[1], encoding="utf-8"))
    b = json.load(open(sys.argv[2], encoding="utf-8"))
    problems = []
    if a["canvas"] != b["canvas"]:
        problems.append("canvas changed")
    for key in ("shapes", "lines", "sticks", "dashes"):
        if a.get(key) != b.get(key):
            problems.append("%s changed" % key)
    ta = {t["id"]: t for t in a["texts"]}
    tb = {t["id"]: t for t in b["texts"]}
    if set(ta) != set(tb):
        problems.append("text id set changed")
    for tid in sorted(CHANGED):
        if tb[tid]["content"] != EXPECT[tid]:
            problems.append("%s content %r != %r"
                            % (tid, tb[tid]["content"], EXPECT[tid]))
        if tb[tid]["size"] != ta[tid]["size"]:
            problems.append("%s font size changed %s -> %s"
                            % (tid, ta[tid]["size"], tb[tid]["size"]))
    for tid in sorted(set(ta) - CHANGED):
        if tb.get(tid) != ta[tid]:
            problems.append("unchanged text %s differs" % tid)
    print("Stage A texts: %d; Stage B texts: %d" % (len(ta), len(tb)))
    print("changed labels: %s" % ", ".join(sorted(CHANGED)))
    print("shapes: %d = %d; dashes: %d = %d; lines: %d = %d" %
          (len(a["shapes"]), len(b["shapes"]), len(a["dashes"]),
           len(b["dashes"]), len(a["lines"]), len(b["lines"])))
    if problems:
        for p in problems:
            print("FAIL:", p)
        print("RESULT: FAIL (%d problem(s))" % len(problems))
        sys.exit(1)
    print("RESULT: PASS (unchanged elements identical; only the verified "
          "content delta applied; no Email/OAuth node added)")
    sys.exit(0)


if __name__ == "__main__":
    main()

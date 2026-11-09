# -*- coding: utf-8 -*-
"""Stage B delta gate for the Container figure.

Proves that applying only the verified content delta left every Stage A
geometry element intact:

  * canvas, 9 shapes, 4 dash runs, 10 lines and every arrow identical
  * every text except the verified changed bands identical (content,
    position, size, weight, letter-spacing, measured band, host)
  * the rewritten labels keep their Stage A font size (no text shrunk)
  * the two added bands are the SPA container versions line 2 and the
    Database "(41 tables)" line; wrapped labels concatenate exactly
  * no Email/OAuth box was invented (shapes identical proves it)

Usage:
  python scripts/check_container_stage_b_delta.py <spec-stage-a.json> <spec.json>
Exit 0 = PASS.
"""
import json
import sys


CHANGED = {
    "X007", "X008", "X009", "X015", "X017", "X020", "X021", "X022",
    "X023", "X027", "X028", "X029", "X045",
}
ADDED = {"X048", "X049"}

EXPECT = {
    "X007": "curates content and maintains system settings",
    "X008": "database practice",
    "X009": "Takes practice sessions,",
    "X015": "[Container: Nginx 1.29]",
    "X017": "SPA bundle",
    "X020": "Single Page Application",
    "X021": "[Container: React 19.3, Vite 8.3.1,",
    "X022": "Learner and Administrator portals,",
    "X023": "SQL editor, radar and bar charts",
    "X027": "[Container: FastAPI 0.141.1, Python 3.13]",
    "X028": "Authentication, practice sessions, plan assembly,",
    "X029": "grading, competency and gap engines",
    "X045": "sessions, evidence, cached LLM responses",
    "X048": "Tailwind CSS 4.3.3, Chart.js 4.5.1]",
    "X049": "(41 tables)",
}

WHOLE = [
    (["X005", "X008"],
     "Undergraduate student taking database practice"),
    (["X006", "X007"],
     "Faculty / course manager who curates content and maintains system settings"),
    (["X016", "X017"], "Delivers static content and the SPA bundle"),
    (["X021", "X048"],
     "[Container: React 19.3, Vite 8.3.1, Tailwind CSS 4.3.3, Chart.js 4.5.1]"),
    (["X022", "X023"],
     "Learner and Administrator portals, SQL editor, radar and bar charts"),
    (["X028", "X029"],
     "Authentication, practice sessions, plan assembly, grading, competency "
     "and gap engines"),
    (["X042", "X045", "X049"],
     "Users, CLOs, concepts, question bank, sessions, evidence, cached LLM "
     "responses (41 tables)"),
    (["X009", "X011"], "Takes practice sessions, views competency profile"),
]


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
    if set(ta) - set(tb):
        problems.append("text ids removed: %s" % sorted(set(ta) - set(tb)))
    if set(tb) - set(ta) != ADDED:
        problems.append("unexpected new text ids: %s"
                        % sorted(set(tb) - set(ta) - ADDED))
    for tid in sorted(CHANGED):
        if tid not in tb:
            problems.append("changed text missing: %s" % tid)
            continue
        if tb[tid]["content"] != EXPECT[tid]:
            problems.append("%s content %r != %r"
                            % (tid, tb[tid]["content"], EXPECT[tid]))
        if tb[tid]["size"] != ta[tid]["size"]:
            problems.append("%s font size changed %s -> %s"
                            % (tid, ta[tid]["size"], tb[tid]["size"]))
    for tid in sorted(set(ta) - CHANGED):
        if tb.get(tid) != ta[tid]:
            problems.append("unchanged text %s differs" % tid)
    for tid in sorted(ADDED):
        if tb.get(tid, {}).get("content") != EXPECT[tid]:
            problems.append("%s content mismatch" % tid)
    for ids, text in WHOLE:
        got = " ".join(tb[i]["content"] for i in ids if i in tb)
        if got != text:
            problems.append("wrapped %s is %r" % ("+".join(ids), got))

    print("Stage A texts: %d; Stage B texts: %d" %
          (len(ta), len(tb)))
    print("changed labels: %s" % ", ".join(sorted(CHANGED)))
    print("added bands: %s" % ", ".join(sorted(ADDED)))
    print("shapes: %d = %d; dashes: %d = %d; lines: %d = %d" %
          (len(a["shapes"]), len(b["shapes"]), len(a["dashes"]),
           len(b["dashes"]), len(a["lines"]), len(b["lines"])))
    if problems:
        for p in problems:
            print("FAIL:", p)
        print("RESULT: FAIL (%d problem(s))" % len(problems))
        sys.exit(1)
    print("RESULT: PASS (unchanged elements identical; only the verified "
          "content delta applied; no Email/OAuth box added)")
    sys.exit(0)


if __name__ == "__main__":
    main()

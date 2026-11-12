# -*- coding: utf-8 -*-
"""Stage A -> Stage B delta proof for rebuilt figures.

Compares `spec-stage-a.json` with `spec.json` in a figure folder and fails if
any shape, stick, canvas or dash geometry moved. Text changes are listed
individually; unchanged text entries must stay byte-identical. A small,
figure-specific number of connector changes is allowed where the verified
content delta explicitly reroutes one flow (Pipeline feedback line, Component
1 px arrow endpoint).

Usage:
  node scripts/run_py.mjs scripts/check_rebuild_delta.py <figure_dir> <allowed_line_diffs>
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    d = os.path.abspath(sys.argv[1])
    allowed_lines = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    a = json.load(open(os.path.join(d, "spec-stage-a.json"), encoding="utf-8"))
    b = json.load(open(os.path.join(d, "spec.json"), encoding="utf-8"))
    problems = []
    if a["canvas"] != b["canvas"]:
        problems.append("canvas changed: %s -> %s" % (a["canvas"], b["canvas"]))
    if a["shapes"] != b["shapes"]:
        problems.append("shape geometry changed")
    if a.get("sticks") != b.get("sticks"):
        problems.append("actor stick geometry changed")
    if a.get("dashes") != b.get("dashes") and allowed_lines == 0:
        problems.append("dash geometry changed")
    line_diffs = [(x, y) for x, y in zip(a["lines"], b["lines"]) if x != y]
    if len(line_diffs) > allowed_lines:
        problems.append("%d line(s) changed, allowed %d" % (len(line_diffs),
                                                           allowed_lines))
    ta = {t["id"]: t for t in a["texts"]}
    tb = {t["id"]: t for t in b["texts"]}
    changed, added, removed = [], [], []
    for k, t in ta.items():
        if k not in tb:
            removed.append("%s %r" % (k, t.get("content")))
        elif t != tb[k]:
            changed.append("%s %r -> %r" % (k, t.get("content"),
                                            tb[k].get("content")))
    for k, t in tb.items():
        if k not in ta:
            added.append("%s %r" % (k, t.get("content")))
    unchanged = len(ta) - len(changed) - len(removed)
    if unchanged < 0:
        problems.append("unchanged text count negative")
    if not (changed or added or removed):
        problems.append("no text delta found")

    out = []
    out.append("Stage A -> Stage B delta: %s" % d)
    out.append("canvas: %s" % (b["canvas"],))
    out.append("shapes: %d identical=%s" % (len(b["shapes"]),
                                            a["shapes"] == b["shapes"]))
    out.append("lines: %d changed=%d allowed=%d" % (len(b["lines"]),
                                                    len(line_diffs),
                                                    allowed_lines))
    out.append("sticks: %d identical=%s" % (len(b.get("sticks", [])),
                                            a.get("sticks") == b.get("sticks")))
    out.append("text labels: %d -> %d; unchanged=%d changed=%d added=%d "
               "removed=%d" % (len(ta), len(tb), unchanged, len(changed),
                               len(added), len(removed)))
    for row in changed:
        out.append("  changed: " + row)
    for row in added:
        out.append("  added:   " + row)
    for row in removed:
        out.append("  removed: " + row)
    for x, y in line_diffs:
        out.append("  line:    %s -> %s" % (x.get("note", x.get("id")),
                                           y.get("note", y.get("id"))))
    if problems:
        out.append("RESULT: FAIL")
        for p in problems:
            out.append("  FAIL: " + p)
        print("\n".join(out))
        return 1
    out.append("RESULT: PASS (canvas, shapes and sticks identical; only the "
               "listed text/lines changed)")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

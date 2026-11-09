# -*- coding: utf-8 -*-
"""Gate for the rebuilt v1.2 diagrams (Stage A clone + Stage B delta).

Every figure must have, under docs/qa/rebuild-preview/<figure>/:
  original.png, clone.png, final.png, side-by-side*, overlay*, diff*
  checker PASS, deliberately broken checker FAIL

The TRD is one figure split into five pages: it must have trd-1..5.png,
checker-b-1..5 PASS, checker-b-broken FAIL and spec counts 41/293/59/19.

Final canvases must equal the original for the nine single-canvas figures.
Exit 0 = PASS.
"""
import json
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = os.path.join(ROOT, "docs", "qa", "rebuild-preview")
FIGURES = ["system-context", "use-case", "container", "allocation",
           "module", "logical", "pipeline", "component", "erd"]


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG: %s" % path)
    return struct.unpack(">II", head[16:24])


def first(pattern, folder):
    for name in sorted(os.listdir(folder)):
        if re.fullmatch(pattern, name):
            return os.path.join(folder, name)
    return None


def checker_verdict(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    if "RESULT: PASS" in text:
        return "PASS"
    if "RESULT: FAIL" in text:
        return "FAIL"
    return "MISSING"


def main():
    problems = []
    rows = []
    for fig in FIGURES:
        d = os.path.join(PREVIEW, fig)
        if not os.path.isdir(d):
            problems.append("%s: preview folder missing" % fig)
            continue
        for required in ("original.png", "clone.png", "final.png"):
            if not os.path.isfile(os.path.join(d, required)):
                problems.append("%s: missing %s" % (fig, required))
        for label, pattern in (("side-by-side", r"side-by-side.*\.png"),
                               ("overlay", r"overlay.*\.png"),
                               ("diff", r"diff.*\.png")):
            if not first(pattern, d):
                problems.append("%s: missing %s image" % (fig, label))
        pass_files = [n for n in os.listdir(d)
                      if re.fullmatch(r"checker.*(pass|stage-b|final).*\.txt", n)
                      and "broken" not in n and "delta" not in n]
        broken_files = [n for n in os.listdir(d)
                        if "broken" in n and n.endswith(".txt")]
        if not pass_files:
            problems.append("%s: no PASS checker file" % fig)
        else:
            verdicts = {n: checker_verdict(os.path.join(d, n)) for n in pass_files}
            if "FAIL" in verdicts.values() or "MISSING" in verdicts.values():
                problems.append("%s: checker not PASS: %s" % (fig, verdicts))
        if not broken_files:
            problems.append("%s: no deliberately broken checker file" % fig)
        elif not any(checker_verdict(os.path.join(d, n)) == "FAIL"
                     for n in broken_files):
            problems.append("%s: broken checker did not FAIL" % fig)
        orig = os.path.join(d, "original.png")
        final = os.path.join(d, "final.png")
        if os.path.isfile(orig) and os.path.isfile(final):
            so, sf = png_size(orig), png_size(final)
            if so != sf:
                problems.append("%s: canvas %s != original %s" % (fig, sf, so))
        rows.append((fig, len(pass_files), len(broken_files)))

    # TRD: five pages, all checkers PASS, one broken FAIL, spec counts.
    trd = os.path.join(PREVIEW, "trd")
    spec_path = os.path.join(ROOT, "docs", "diagrams", "rebuild", "trd",
                             "spec.json")
    if not os.path.isfile(spec_path):
        problems.append("trd: spec.json missing")
    else:
        spec = json.load(open(spec_path, encoding="utf-8"))
        counts = spec.get("counts", {})
        for key, want in (("tables", 41), ("columns", 293),
                          ("foreign_keys", 59), ("migrations", 19),
                          ("pages", 5)):
            if counts.get(key) != want:
                problems.append("trd: %s %r != %r" % (key, counts.get(key), want))
        page_of = {c["table"]: p["page"] for p in spec["pages"]
                   for c in p["cards"]}
        if len(page_of) != 41:
            problems.append("trd: %d distinct tables != 41" % len(page_of))
    for i in range(1, 6):
        for name in ("trd-%d.png" % i,):
            if not os.path.isfile(os.path.join(ROOT, "docs", "diagrams",
                                               "rebuild", "trd", name)):
                problems.append("trd: missing %s" % name)
        checker = os.path.join(trd, "checker-b-%d.txt" % i)
        if not os.path.isfile(checker) or checker_verdict(checker) != "PASS":
            problems.append("trd: checker-b-%d not PASS" % i)
    broken = os.path.join(trd, "checker-b-broken.txt")
    if not os.path.isfile(broken) or checker_verdict(broken) != "FAIL":
        problems.append("trd: deliberately broken checker did not FAIL")
    if not os.path.isfile(os.path.join(trd, "index.md")):
        problems.append("trd: index.md missing")

    index = os.path.join(PREVIEW, "index.md")
    if not os.path.isfile(index):
        problems.append("approval index missing")
    else:
        text = open(index, encoding="utf-8").read()
        for fig in FIGURES + ["trd"]:
            if fig not in text:
                problems.append("approval index does not mention %s" % fig)

    if problems:
        print("rebuild figures: %d problem(s)" % len(problems))
        for p in problems:
            print("FAIL:", p)
        return 1
    print("rebuild figures: PASS")
    for fig, np, nb in rows:
        print("  %-15s checkers PASS=%d broken-FAIL=%d" % (fig, np, nb))
    print("  trd             5 pages, 41 tables / 293 columns / 59 FKs / "
          "19 migrations")
    return 0


if __name__ == "__main__":
    sys.exit(main())

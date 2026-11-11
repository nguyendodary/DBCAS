# -*- coding: utf-8 -*-
"""F4 owner-fix delta proof: previous Stage B spec -> fixed spec.

Asserts that ONLY the declared elements changed. Every other shape, dash
run, line, stick and text entry must be byte-identical (json equality).

Usage:
  python scripts/check_f4_pipeline_delta.py <old_spec.json> <new_spec.json>
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ALLOWED_SHAPES = {"S06", "S08"}
ALLOWED_LINES = {"L06"}
ALLOWED_TEXTS = {"B003", "B008", "B009", "B013", "B014", "B018", "B019",
                 "B023", "B024", "B025", "B026", "B027", "B030", "B033",
                 "B036", "B037", "B039", "B040"}
ADDED_TEXTS = {"B041"}


def main():
    old = json.load(open(sys.argv[1], encoding="utf-8"))
    new = json.load(open(sys.argv[2], encoding="utf-8"))
    problems = []
    if old["canvas"] != new["canvas"]:
        problems.append("canvas changed")
    if old.get("dashes") != new.get("dashes"):
        problems.append("dash geometry changed")
    if old.get("sticks") != new.get("sticks"):
        problems.append("stick geometry changed")

    old_shapes = {s["id"]: s for s in old["shapes"]}
    new_shapes = {s["id"]: s for s in new["shapes"]}
    changed_shapes = sorted(k for k in old_shapes
                            if old_shapes[k] != new_shapes.get(k))
    missing_shapes = sorted(set(old_shapes) - set(new_shapes))
    extra_shapes = sorted(set(new_shapes) - set(old_shapes))

    old_lines = {(l.get("id") or "no-id-%d" % i): l
                 for i, l in enumerate(old["lines"])}
    new_lines = {(l.get("id") or "no-id-%d" % i): l
                 for i, l in enumerate(new["lines"])}
    changed_lines = sorted(k for k in old_lines
                           if old_lines[k] != new_lines.get(k))
    missing_lines = sorted(set(old_lines) - set(new_lines))
    extra_lines = sorted(set(new_lines) - set(old_lines))

    old_texts = {t["id"]: t for t in old["texts"]}
    new_texts = {t["id"]: t for t in new["texts"]}

    def sig(t):
        # `measured` is a derived documentation bbox; compare the emitted
        # geometry/content instead.
        return {k: t.get(k) for k in ("content", "weight", "size", "anchor",
                                      "x", "y", "ink", "ls", "inside")}

    changed_texts = sorted(k for k in old_texts
                           if sig(old_texts[k]) != sig(new_texts.get(k)))
    missing_texts = sorted(set(old_texts) - set(new_texts))
    extra_texts = sorted(set(new_texts) - set(old_texts))

    if set(changed_shapes) != ALLOWED_SHAPES:
        problems.append("changed shapes %s != allowed %s"
                        % (changed_shapes, sorted(ALLOWED_SHAPES)))
    if missing_shapes or extra_shapes:
        problems.append("shape add/remove: -%s +%s"
                        % (missing_shapes, extra_shapes))
    if set(changed_lines) != ALLOWED_LINES:
        problems.append("changed lines %s != allowed %s"
                        % (changed_lines, sorted(ALLOWED_LINES)))
    if missing_lines or extra_lines:
        problems.append("line add/remove: -%s +%s" % (missing_lines,
                                                      extra_lines))
    if set(changed_texts) != ALLOWED_TEXTS:
        problems.append("changed texts %s != allowed %s"
                        % (changed_texts, sorted(ALLOWED_TEXTS)))
    if set(extra_texts) != ADDED_TEXTS:
        problems.append("added texts %s != allowed %s"
                        % (extra_texts, sorted(ADDED_TEXTS)))
    if missing_texts:
        problems.append("removed texts %s" % (missing_texts,))

    lines = []
    lines.append("F4 pipeline delta: %s -> %s" % (sys.argv[1], sys.argv[2]))
    lines.append("canvas: %s identical=%s" % (new["canvas"],
                                              old["canvas"] == new["canvas"]))
    lines.append("shapes: %d; changed=%s; others identical=%d"
                 % (len(new_shapes), changed_shapes,
                    len(new_shapes) - len(changed_shapes)))
    lines.append("lines: %d; changed=%s; others identical=%d"
                 % (len(new_lines), changed_lines,
                    len(new_lines) - len(changed_lines)))
    lines.append("texts: %d -> %d; changed=%s; added=%s; unchanged=%d"
                 % (len(old_texts), len(new_texts), changed_texts,
                    extra_texts,
                    len(old_texts) - len(changed_texts) - len(missing_texts)))
    for tid in changed_texts:
        lines.append("  changed %s: %r -> %r"
                     % (tid, old_texts[tid].get("content"),
                        new_texts[tid].get("content")))
    lines.append("RESULT: %s" % ("FAIL" if problems else "PASS"))
    for p in problems:
        lines.append("  FAIL: " + p)
    print("\n".join(lines))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

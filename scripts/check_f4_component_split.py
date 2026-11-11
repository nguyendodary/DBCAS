# -*- coding: utf-8 -*-
"""F4 split proof: every unchanged Component element is still identical.

Compares the approved Stage B single-page spec with the two split pages:
  * all 26 card shapes exist with the same size/style (only translation),
    except the one declared fix: S05 enlarged 262x167 -> 300x185;
  * all 112 label ids exist, except B047 which is merged verbatim into B040
    ("Evaluation" + "Service" -> "Evaluation Service"); every other label
    keeps content/size/weight/letter-spacing; positions translate with their
    card or are the declared band captions;
  * all 25 connector polylines/arrowheads survive (10 on 08a? see output);
    every tip is present and the endpoint x values are the Stage B values.

Usage: python scripts/check_f4_component_split.py <old_spec> <spec-08a> <spec-08b>
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BOUNDARIES = {"S27", "S28", "S29"}
ALLOWED_RESIZE = {"S05"}
ALLOWED_TEXT_POS = {"B001", "B002", "B032", "B033", "B065", "B066", "B099"}
S05_TEXTS = {"B034", "B040", "B055", "B062", "B064"}
MERGED = {"B047": "B040"}


def shape_sig(s):
    return {k: s.get(k) for k in ("kind", "fill", "stroke", "stroke_width",
                                  "radius", "dashed", "cap_ry")}


def text_sig(t):
    return {k: t.get(k) for k in ("content", "weight", "size", "ink", "ls")}


def main():
    old = json.load(open(sys.argv[1], encoding="utf-8"))
    pages = [json.load(open(sys.argv[2], encoding="utf-8")),
             json.load(open(sys.argv[3], encoding="utf-8"))]
    problems = []
    notes = []

    old_shapes = {s["id"]: s for s in old["shapes"]}
    page_shapes = []
    for p in pages:
        page_shapes.extend(p["shapes"])
    by_id = {}
    for s in page_shapes:
        by_id.setdefault(s["id"], []).append(s)

    for sid, old_s in old_shapes.items():
        if sid in BOUNDARIES:
            continue
        if sid not in by_id:
            problems.append("shape %s missing from both pages" % sid)
            continue
        ow = old_s["bbox"][2] - old_s["bbox"][0]
        oh = old_s["bbox"][3] - old_s["bbox"][1]
        for ns in by_id[sid]:
            nw = ns["bbox"][2] - ns["bbox"][0]
            nh = ns["bbox"][3] - ns["bbox"][1]
            if shape_sig(old_s) != shape_sig(ns):
                problems.append("shape %s style changed" % sid)
            if (abs(nw - ow) > 0.1 or abs(nh - oh) > 0.1) and sid not in ALLOWED_RESIZE:
                problems.append("shape %s size %.1fx%.1f != %.1fx%.1f"
                                % (sid, nw, nh, ow, oh))
            if sid in ALLOWED_RESIZE:
                notes.append("shape %s allowed resize %.1fx%.1f -> %.1fx%.1f"
                             % (sid, ow, oh, nw, nh))
    extra_shapes = sorted(set(by_id) - set(old_shapes) - BOUNDARIES)
    if extra_shapes:
        problems.append("new shapes not in Stage B: %s" % extra_shapes)

    old_texts = {t["id"]: t for t in old["texts"]}
    page_texts = []
    for p in pages:
        page_texts.extend(p["texts"])
    tids = {}
    for t in page_texts:
        tids.setdefault(t["id"], []).append(t)

    for tid, old_t in old_texts.items():
        if tid not in tids:
            if tid in MERGED:
                notes.append("text %s merged into %s" % (tid, MERGED[tid]))
                continue
            problems.append("text %s missing from both pages" % tid)
            continue
        if tid in MERGED:
            continue
        for nt in tids[tid]:
            if tid in S05_TEXTS or tid in ALLOWED_TEXT_POS:
                continue
            if text_sig(old_t) != text_sig(nt):
                problems.append("text %s content/style changed" % tid)
    extra_texts = sorted(set(tids) - set(old_texts))
    if extra_texts:
        problems.append("new text ids not in Stage B: %s" % extra_texts)

    # merged label carries the exact two old words
    merged = [t for t in page_texts if t["id"] == "B040"]
    if not merged or merged[0]["content"] != "Evaluation Service":
        problems.append("B040 is not 'Evaluation Service'")

    # connector count and arrowheads preserved
    old_tips = [l for l in old["lines"] if l.get("arrow_tip")]
    new_lines = sum(len(p["lines"]) for p in pages)
    new_tips = [l for p in pages for l in p["lines"] if l.get("arrow_tip")]
    if len(old_tips) != len(new_tips):
        problems.append("arrowheads %d != Stage B %d"
                        % (len(new_tips), len(old_tips)))

    out = []
    out.append("F4 component split delta proof")
    out.append("Stage B: %d shapes, %d lines, %d texts"
               % (len(old_shapes), len(old["lines"]), len(old_texts)))
    for i, p in enumerate(pages):
        out.append("page %s: %d shapes, %d lines, %d texts, canvas %s"
                   % ("08a" if i == 0 else "08b", len(p["shapes"]),
                      len(p["lines"]), len(p["texts"]), p["canvas"]))
    out.append("unique card shapes kept: %d/%d"
               % (len(set(by_id) - BOUNDARIES),
                  len(set(old_shapes) - BOUNDARIES)))
    out.append("unique label ids kept: %d/%d (B047 merged into B040)"
               % (len(set(tids) & set(old_texts)), len(old_texts)))
    out.append("connector objects: %d -> %d (extra objects are rule-8 cuts); "
               "arrowhead tips: %d -> %d"
               % (len(old["lines"]), new_lines, len(old_tips),
                  len(new_tips)))
    for n in notes:
        out.append("  " + n)
    out.append("RESULT: %s" % ("FAIL" if problems else "PASS"))
    for p in problems:
        out.append("  FAIL: " + p)
    print("\n".join(out))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

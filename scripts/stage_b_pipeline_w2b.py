# -*- coding: utf-8 -*-
"""W2b Pipeline Stage B: apply the verified content delta to the Stage A
clone.  Geometry (8 boxes, boundary runs, arrows) is untouched; only the
text layer changes.  Font sizes are the Stage A sizes (never smaller); long
new body lines are wrapped at spaces (same font size, spacing only).

Writes trace.json / text-content.json / font-plan.json in the figure dir.
Usage:
  node scripts/run_py.mjs scripts/stage_b_pipeline_w2b.py <figure_dir>
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_fonts import ink  # noqa: E402

# box id -> (title lines, body lines, title size, body size)
BOX = {
    "S06": (["Practice setup"], [
        "Concepts · difficulty bands",
        "EASY 1–2 / MEDIUM 3 /",
        "HARD 4–5 · count 1–20",
        "(default 5) · source bank",
        "or AI",
    ], 22, 16),
    "S08": (["Plan assembly &", "freeze"], [
        "Exact count · selected concepts",
        "spread as count allows · no",
        "repeated version families · SQL",
        "bank-only · AI MCQ/essay",
    ], 22, 16),
    "S07": (["Serve planned item"], [
        "Only validated bank /",
        "approved AI items, in",
        "the frozen plan order",
    ], 22, 16),
    "S09": (["Grade each answer"], [
        "MCQ key · SQL sandbox ·",
        "essay rubric (Prompt",
        "Builder → Evaluator)",
    ], 22, 16),
    "S05": (["Record evidence"], [
        "Score · question snapshot ·",
        "concept tags · validation",
        "flags",
    ], 22, 16),
    "S03": (["Candidate preparation"], [
        "AI drafts → automated checks",
        "→ administrator approval",
    ], 22, 16),
    "S04": (["Validated item bank"], [
        "Approved items only · source",
        "for all SQL · bank fallback",
    ], 21, 16),
    "S02": (["Complete session"], [
        "All planned items served or 30-minute",
        "expiry/00:00 · deterministic",
        "per-concept competency · ranked",
        "“What to study next”",
    ], 21, 16),
}

# Stage A measured tops (absolute y) used as anchors
TITLE_TOP = {"S06": 150, "S08": 143, "S07": 150, "S09": 150, "S05": 150,
             "S03": 456, "S04": 456, "S02": 453}
BODY_TOP = {"S06": 183, "S08": 186, "S07": 183, "S09": 183, "S05": 183,
            "S03": 493, "S04": 493, "S02": 483}

TITLE = "Evidence-based Competency & Gap Evaluation Pipeline"
SUBTITLE = ("Complete practice plan frozen before question one • every "
            "served item comes from the plan")
REPEAT = ("Serve the next item from the frozen plan; repeat until all "
          "planned items are served or the 30-minute timer expires")
FOOTER = ("Session length 1–20 (default 5) · 30-minute expiry · SQL always "
          "from the validated bank; AI fallback shows one bank_mixed notice.")
FOOTNOTE = ("Ranked gap topics only; long-term learning paths and "
            "course-document retrieval are outside scope.")


def main():
    d = sys.argv[1]
    trace = json.load(open(os.path.join(d, "trace-stage-a.json"),
                           encoding="utf-8"))
    shapes = {s["id"]: s for s in trace["shapes"]}

    texts = []

    def add(content, weight, size, x0, y0, inside):
        b = ink(content, weight, size)
        iw, ih = b[2] - b[0], b[3] - b[1]
        texts.append({
            "bbox": [int(round(x0)), int(y0), int(round(x0 + iw)),
                     int(y0 + ih)],
            "ink": "#222527" if inside else "#17191A",
            "inside": inside,
            "content": content,
            "weight": weight,
            "size": size,
            "x": float(round(x0)), "y": float(y0),
            "anchor": "top", "inkwh": [iw, ih],
        })

    # boxes
    for sid, (tlines, blines, tsize, bsize) in BOX.items():
        s = shapes[sid]
        x0, y0, x1, y1 = s["bbox"]
        cx = (x0 + x1) / 2.0
        y = TITLE_TOP[sid]
        for ln in tlines:
            b = ink(ln, "bold", tsize)
            iw, ih = b[2] - b[0], b[3] - b[1]
            add(ln, "bold", tsize, cx - iw / 2.0, y, sid)
            y += ih + 2
        y = max(BODY_TOP[sid], y + 4)
        for ln in blines:
            b = ink(ln, "regular", bsize)
            iw, ih = b[2] - b[0], b[3] - b[1]
            assert x0 + 3 <= cx - iw / 2.0 and cx + iw / 2.0 <= x1 - 3, \
                (sid, ln, iw, x1 - x0)
            add(ln, "regular", bsize, cx - iw / 2.0, y, sid)
            y += ih + 2
        assert y - 2 <= y1 - 1, (sid, "text overflow", y, y1)

    # free labels (centred on the canvas)
    W = trace["canvas"]["w"]
    cx = W / 2.0
    b = ink(TITLE, "bold", 31)
    add(TITLE, "bold", 31, cx - (b[2] - b[0]) / 2.0, 11, None)
    b = ink(SUBTITLE, "regular", 18)
    add(SUBTITLE, "regular", 18, cx - (b[2] - b[0]) / 2.0, 54, None)
    b = ink(REPEAT, "regular", 17)
    add(REPEAT, "regular", 17, cx - (b[2] - b[0]) / 2.0, 607, None)
    b = ink(FOOTER, "bold", 20)
    fw = b[2] - b[0]
    if fw <= W - 60:
        add(FOOTER, "bold", 20, cx - fw / 2.0, 652, None)
        foot_y = 687
    else:                                   # two centred lines
        cut = FOOTER.rfind("SQL always")
        l1, l2 = FOOTER[:cut].rstrip(), FOOTER[cut:]
        for i, ln in enumerate((l1, l2)):
            bb = ink(ln, "bold", 20)
            add(ln, "bold", 20, cx - (bb[2] - bb[0]) / 2.0, 648 + i * 24,
                None)
        foot_y = 700
    b = ink(FOOTNOTE, "regular", 16)
    add(FOOTNOTE, "regular", 16, cx - (b[2] - b[0]) / 2.0, foot_y, None)

    # stable ids in (y,x) order - the same order the builders use
    texts.sort(key=lambda t: (t["bbox"][1], t["bbox"][0]))
    for i, t in enumerate(texts):
        t["id"] = "B%03d" % (i + 1)

    # ---- dashes: split the bottom run around the wider repeat label
    rep = next(t for t in texts if t["content"] == REPEAT)
    left_end = int(rep["bbox"][0]) - 10
    right_start = int(rep["bbox"][2]) + 10
    dashes = []
    for dd in trace["dashes"]:
        if dd["axis"] == "h" and dd["y"] == 614 and dd["x0"] == 10:
            dd = dict(dd, x1=left_end)
            dashes.append(dd)
            dashes.append({"axis": "h", "y": 614, "x0": right_start,
                           "x1": 1323,
                           "dashes": int((1323 - right_start) // 11) + 1,
                           "on": 6, "off": 5})
        elif dd["axis"] == "h" and dd["y"] == 614:
            continue
        else:
            dashes.append(dd)

    # ---- lines: bank feeds the plan (orthogonal elbow to box 2)
    lines = trace["lines"]
    for ln in lines:
        if ln["id"] == "L06":
            ln["segs"] = [[[670.5, 438.5], [670.5, 384.5]],
                          [[670.5, 384.5], [407.0, 384.5]],
                          [[407.0, 384.5], [407.0, 268.0]]]
            ln["arrow_tip"] = [407.0, 267.5]
            ln["arrow_from"] = [407.0, 384.5]
            ln["bbox"] = [407, 268, 671, 439]
            ln["dashed"] = True
            ln["note"] = ("Validated item bank -> Plan assembly & freeze "
                          "(bank fallback, dashed)")

    # ---- text-content / font-plan
    free = [t for t in texts if t["inside"] is None]
    box = [t for t in texts if t["inside"] is not None]
    cont = {
        "note": ("Pipeline Stage B (content delta verified 2026-11-09): "
                 "same canvas/boxes/arrows as Stage A; text layer replaced "
                 "with the section-6 labels. %d free + %d box = %d labels."
                 % (len(free), len(box), len(texts))),
        "free_ids": [t["id"] for t in free],
        "free_texts": [t["content"] for t in free],
        "box_ids": [t["id"] for t in box],
        "box_texts": [t["content"] for t in box],
        "bold": [t["content"] for t in texts if t["weight"] == "bold"],
        "ellipse_texts": [],
    }
    plan = {}
    for t in texts:
        plan[t["id"]] = {"weight": t["weight"], "size": t["size"],
                         "anchor": "top", "measured": t["bbox"],
                         "ink": t["inkwh"]}
    out_trace = dict(trace, texts=[{k: v for k, v in t.items()
                                    if k not in ("content", "weight",
                                                 "size", "x", "y",
                                                 "anchor", "inkwh")}
                                    for t in texts],
                     dashes=dashes, lines=lines)
    json.dump(out_trace, open(os.path.join(d, "trace.json"), "w",
                              encoding="utf-8"), indent=1)
    json.dump(cont, open(os.path.join(d, "text-content.json"), "w",
                         encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump(plan, open(os.path.join(d, "font-plan.json"), "w",
                         encoding="utf-8"), indent=1, ensure_ascii=False)
    print("stage B pipeline: %d texts, title/body fit, dashes split at "
          "x=%d..%d" % (len(texts), left_end, right_start))


if __name__ == "__main__":
    main()

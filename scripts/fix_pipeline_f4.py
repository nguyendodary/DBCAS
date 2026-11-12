# -*- coding: utf-8 -*-
"""F4 owner fixes for the Pipeline figure (Proposal Fig 4).

Changes, and nothing else:
  (b) enlarge "Practice setup" (S06) and "Plan assembly & freeze" (S08)
      boxes downward; 5 body lines max; even 21 px line grid; text never
      touches the border; all fonts unchanged (>= original).
  (c) replace the bold bottom line with the approved disclosure wording
      (no code identifiers), wrapped over two 20 px bold lines with a wide
      left/right margin (the exact 164-char string measures 1577 px on one
      line, wider than the 1342 px canvas, so the same wording is wrapped at
      the clause boundary, not shortened).
  (d) restore the solid arrow from Validated item bank to Plan assembly &
      freeze, arrowhead on the plan box (was dashed).
  (e) even line spacing in Complete session (23 px baseline grid).

Usage: python scripts/fix_pipeline_f4.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f4_build_lib import (build_page, text_center_for_ink, write_font_plan,
                          write_letter_spacing, write_text_content)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "docs", "diagrams", "rebuild", "pipeline")


def main():
    spec = json.load(open(os.path.join(D, "spec-stage-b-prefix.json"),
                           encoding="utf-8"))
    shapes = spec["shapes"]
    by_id = {s["id"]: s for s in shapes}
    by_id["S06"]["bbox"] = [26.0, 130.0, 261.0, 304.0]
    by_id["S08"]["bbox"] = [289.0, 130.0, 524.0, 304.0]

    lines = spec["lines"]
    lby = {ln.get("id"): ln for ln in lines}
    l06 = lby["L06"]
    l06.pop("dashed", None)
    l06["segs"] = [[[670.5, 438.5], [670.5, 384.5]],
                   [[670.5, 384.5], [407.0, 384.5]],
                   [[407.0, 384.5], [407.0, 303.5]]]
    l06["arrow_tip"] = [407.0, 303.5]
    l06["arrow_from"] = [407.0, 384.5]
    l06["note"] = "Validated item bank -> Plan assembly & freeze (solid)"

    texts = spec["texts"]
    tby = {t["id"]: t for t in texts}

    # (b) even 21 px body grid inside the two enlarged boxes
    for tid, y in (("B009", 194), ("B014", 215), ("B019", 236),
                   ("B024", 257), ("B026", 278)):
        tby[tid]["y"] = y
    for tid, y in (("B003", 163), ("B008", 185), ("B013", 212),
                   ("B018", 233), ("B023", 254), ("B025", 275)):
        tby[tid]["y"] = y

    # (e) even 23 px body grid in Complete session
    tby["B027"]["y"] = 470
    for tid, y in (("B030", 503), ("B033", 526), ("B036", 549),
                   ("B037", 572)):
        tby[tid]["y"] = y

    # (c) approved bottom line, no code identifiers, two centred lines
    l1 = ("Session length 1-20 questions (default 5) · 30-minute expiry · "
          "SQL always from the validated bank")
    l2 = ("bank questions used when AI generation falls short are disclosed")
    b039 = tby["B039"]
    b039["content"] = l1
    b039["ls"] = 0.0
    b039["x"] = text_center_for_ink(l1, "bold", 20, 671.0)
    b039["y"] = 650.0
    b039["measured"] = [0, 0, 0, 0]
    b041 = {"id": "B041", "content": l2, "weight": "bold", "size": 20,
            "anchor": "top",
            "x": text_center_for_ink(l2, "bold", 20, 671.0), "y": 675.0,
            "ink": "#17191A", "ls": 0.0, "measured": [0, 0, 0, 0],
            "inside": None}
    texts.insert(texts.index(b039) + 1, b041)
    tby["B040"]["y"] = 705.0

    canvas = spec["canvas"]
    spec_out = build_page(D, "pipeline", canvas, shapes, spec["dashes"],
                          lines, texts)

    # text-content for the rule-8 checker: 6 free + 35 box = 41 labels
    free_ids = ["B001", "B002", "B038", "B039", "B041", "B040"]
    box_ids = [t["id"] for t in spec_out["texts"] if t["inside"] is not None]
    tby2 = {t["id"]: t for t in spec_out["texts"]}
    write_text_content(
        os.path.join(D, "text-content.json"), free_ids,
        [tby2[i]["content"] for i in free_ids], box_ids,
        [tby2[i]["content"] for i in box_ids],
        [t["content"] for t in spec_out["texts"] if t["weight"] == "bold"],
        "Pipeline F4 fix: 6 free + 35 box = 41 labels. Title/caption exact; "
        "footer is the approved disclosure wording on two centred 20 px bold "
        "lines; 5 body lines max in the two enlarged boxes.")
    write_font_plan(os.path.join(D, "font-plan.json"), spec_out["texts"])
    write_letter_spacing(os.path.join(D, "letter-spacing.json"),
                         spec_out["texts"])

    # trace.json is the build/inventory input: keep it in sync
    trace = {"canvas": canvas, "source": "pipeline Stage B + F4 owner fixes",
             "shapes": shapes, "dashes": spec["dashes"],
             "lines": spec_out["lines"], "sticks": [],
             "texts": [dict(t, bbox=t["measured"]) for t in spec_out["texts"]]}
    with open(os.path.join(D, "trace.json"), "w", encoding="utf-8") as f:
        json.dump(trace, f, indent=1)
    print("wrote", os.path.join(D, "trace.json"))


if __name__ == "__main__":
    main()

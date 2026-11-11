# -*- coding: utf-8 -*-
"""F2 owner-fix build for the Container figure (figure 03).

Applies only the owner's three fixes:
  (a) reflow the text inside the 6 rounded boxes + the 2 cylinders with equal
      line gaps and clear borders; box heights grow downwards (top-left
      anchors unchanged); original font sizes kept.
  (b) restore the measured original weights: LLM Provider API border
      7 px -> 2 px (#6B6B6B; original coverage 1.95 px), Sanitized-prompts
      label 21 -> 20 px regular, and the API->LLM flow line 2.5 px black ->
      2 px #444444.  The two vertical web-tier flow lines are restored to
      their measured 2 px #444444 as well (they were 2.5/4 px #7D7D7D).
  (c) add two external boxes, OAuth Providers and Email Service, in the
      LLM Provider API style, plus the labelled edges
      "OAuth sign-in [HTTPS]" and "Password-reset email [SMTP]".
      Canvas grows right/bottom (1444x1418 -> 1780x1645); every existing
      top-left anchor stays put.

Writes trace.json, text-content.json, font-plan.json and an empty
letter-spacing.json (the calibration pass refills it).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f2_layout_common import (add_line, add_shape, plan_entry,
                              reflow_box, text_entry)  # noqa: E402

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "docs", "diagrams", "rebuild", "container")


def load(name):
    return json.load(open(os.path.join(D, name), encoding="utf-8"))


def dump(name, obj):
    with open(os.path.join(D, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)


def main():
    trace = load("trace.json")
    cont = load("text-content.json")
    plan = load("font-plan.json")
    by_id = {t["id"]: t for t in trace["texts"]}
    strings = {}
    for i, s in zip(cont["free_ids"], cont["free_texts"]):
        strings[i] = s
    for i, s in zip(cont["box_ids"], cont["box_texts"]):
        strings[i] = s

    # ---------------------------------------------------------------- canvas
    trace["canvas"] = {"w": 1780, "h": 1645}

    # ------------------------------------------------- (a) box text reflow
    # (pad_top, pad_bottom, gap, fixed height) chosen per box family.
    reflow_box(trace, by_id, plan, "S07", [
        ("X001", "bold", 25, strings["X001"]),
        ("X003", "regular", 19, strings["X003"]),
        ("X005", "regular", 20, strings["X005"]),
        ("X008", "regular", 19, strings["X008"]),
    ], 14, 14, 7)
    reflow_box(trace, by_id, plan, "S05", [
        ("X002", "bold", 25, strings["X002"]),
        ("X004", "regular", 19, strings["X004"]),
        ("X006", "regular", 20, strings["X006"]),
        ("X007", "regular", 20, strings["X007"]),
    ], 14, 14, 7)
    reflow_box(trace, by_id, plan, "S09", [
        ("X014", "bold", 25, strings["X014"]),
        ("X015", "regular", 23, strings["X015"]),
        ("X016", "regular", 20, strings["X016"]),
        ("X017", "regular", 20, strings["X017"]),
    ], 14, 14, 7)
    reflow_box(trace, by_id, plan, "S06", [
        ("X020", "bold", 25, strings["X020"]),
        ("X021", "regular", 21, strings["X021"]),
        ("X048", "regular", 21, strings["X048"]),
        ("X022", "regular", 19, strings["X022"]),
        ("X023", "regular", 20, strings["X023"]),
    ], 14, 14, 7)
    reflow_box(trace, by_id, plan, "S04", [
        ("X026", "bold", 24, strings["X026"]),
        ("X027", "regular", 20, strings["X027"]),
        ("X028", "regular", 19, strings["X028"]),
        ("X029", "regular", 20, strings["X029"]),
    ], 14, 14, 7)
    # cylinders: keep the measured 147 px body, 26 px lid clearance, 4 px
    # ink gaps, 8 px above the bottom curve (grow would move the silhouette).
    reflow_box(trace, by_id, plan, "S02", [
        ("X036", "bold", 26, strings["X036"]),
        ("X039", "regular", 26, strings["X039"]),
        ("X042", "regular", 19, strings["X042"]),
        ("X045", "regular", 19, strings["X045"]),
        ("X049", "regular", 19, strings["X049"]),
    ], 26, 8, 4, fixed_height=147)
    reflow_box(trace, by_id, plan, "S03", [
        ("X037", "bold", 24, strings["X037"]),
        ("X040", "regular", 22, strings["X040"]),
        ("X044", "regular", 20, strings["X044"]),
        ("X046", "regular", 20, strings["X046"]),
    ], 26, 8, 4, fixed_height=147)
    reflow_box(trace, by_id, plan, "S08", [
        ("X038", "bold", 25, strings["X038"]),
        ("X041", "regular", 20, strings["X041"]),
        ("X043", "regular", 20, strings["X043"]),
        ("X047", "regular", 19, strings["X047"]),
    ], 14, 14, 7)

    # ------------------------------------------------------ (b) line weights
    # original crop: the LLM border is a 2 px #6B6B6B stroke (row profile
    # 146/107/143 over fill 153 => ~1.95 px coverage), not the 7 px stub.
    heavy_llm = next(s for s in trace["shapes"] if s["id"] == "S08")
    heavy_llm["stroke_width"] = 2

    for ln in trace["lines"]:
        if ln["id"] in ("L06", "L07"):
            ln["color"] = "#444444"
            ln["stroke"] = 2.0
        if ln["id"] == "L10":
            ln["color"] = "#444444"
            ln["stroke"] = 2.0

    # Sanitized-prompts label: measured original cap height 13 px; Arial 20 px
    # has a 14 px cap, i.e. still above the original; 21 px looked heavier.
    t = by_id["X032"]
    e = text_entry("X032", strings["X032"], "regular", 20,
                   left=t["bbox"][0], top=t["bbox"][1])
    t["bbox"] = e["bbox"]
    plan["X032"] = plan_entry(t, "regular", 20)

    # ------------------------------------------- box/label text baselines move
    # (reflow_box already rewrote the bbox; only flow lines keep their bands)

    # ------------------------------------- (c) new external boxes + edges
    add_shape(trace, "S10", [1069, 1480, 1403, 1610],
              "#999999", "#6B6B6B", 2, 22)
    add_shape(trace, "S11", [1420, 1480, 1754, 1610],
              "#999999", "#6B6B6B", 2, 22)

    oauth = [
        ("X050", "bold", 25, "OAuth Providers"),
        ("X051", "regular", 20, "[External Software System]"),
        ("X052", "regular", 19, "Google and GitHub"),
        ("X053", "regular", 19, "OAuth 2.0"),
    ]
    email = [
        ("X054", "bold", 25, "Email Service"),
        ("X055", "regular", 20, "[External Software System]"),
        ("X056", "regular", 19, "Password-reset mail via SMTP"),
        ("X057", "regular", 19, "Mailpit in development"),
    ]
    for box_id, lines in (("S10", oauth), ("S11", email)):
        shape = next(s for s in trace["shapes"] if s["id"] == box_id)
        x0, y0, x1, y1 = shape["bbox"]
        cx = (x0 + x1) / 2.0
        heights = []
        for tid, weight, size, content in lines:
            from f2_layout_common import ink_size
            iw, ih, b = ink_size(content, weight, size)
            heights.append((tid, weight, size, content, iw, ih, b))
        body = sum(h[5] for h in heights) + 7 * (len(lines) - 1)
        cy = y0 + (y1 - y0 - body) / 2.0
        for tid, weight, size, content, iw, ih, b in heights:
            left = cx - (b[0] + b[2]) / 2.0
            ent = text_entry(tid, content, weight, size, left=left, top=cy,
                             inside=box_id, colour="#FFFFFF")
            trace["texts"].append(ent)
            by_id[tid] = ent
            plan[tid] = plan_entry(ent, weight, size)
            cy += ih + 7

    # edge labels: 4 px above their own horizontal bus, never on a box.
    for tid, content, left, top in (
            ("X058", "OAuth sign-in [HTTPS]", 1090, 1363),
            ("X059", "Password-reset email [SMTP]", 1400, 1333)):
        ent = text_entry(tid, content, "regular", 19, left=left, top=top,
                         inside=None, colour="#222222")
        trace["texts"].append(ent)
        by_id[tid] = ent
        plan[tid] = plan_entry(ent, "regular", 19)

    # new orthogonal edges (API Application -> external boxes)
    add_line(trace, "L11",
             [[(981, 950), (1038, 950)], [(1038, 950), (1038, 1385)],
              [(1038, 1385), (1236, 1385)], [(1236, 1385), (1236, 1480)]],
             "#444444", 2.0, tip=[1236, 1480], source=[981, 950])
    add_line(trace, "L12",
             [[(981, 970), (1052, 970)], [(1052, 970), (1052, 1355)],
              [(1052, 1355), (1587, 1355)], [(1587, 1355), (1587, 1480)]],
             "#444444", 2.0, tip=[1587, 1480], source=[981, 970])

    # ------------------------------------------------------- line endpoints
    for ln in trace["lines"]:
        if ln["id"] == "L01":
            ln["segs"][0][0] = [620.7, 1030.0]
        elif ln["id"] == "L03":
            ln["segs"][0][0] = [903.4, 170.0]
        elif ln["id"] == "L04":
            ln["arrow_from"] = [903.0, 170.0]
        elif ln["id"] == "L05":
            ln["segs"][0][1] = [509.0, 169.0]
            ln["arrow_from"] = [509.0, 169.0]
        elif ln["id"] == "L06":
            ln["segs"][0][0] = [696.0, 482.0]
            ln["arrow_from"] = [697.0, 482.0]
        elif ln["id"] == "L07":
            ln["segs"][0][0] = [696.0, 785.0]
            ln["arrow_from"] = [697.0, 785.0]
        elif ln["id"] == "L09":
            ln["segs"][0][1] = [715.3, 1030.0]
        elif ln["id"] == "L10":
            ln["segs"][0][0] = [881.0, 1032.0]
            ln["arrow_from"] = [881.0, 1032.0]

    # ------------------------------------------------------- text-content
    cont["note"] = ("Container owner-fix (F2): box text reflowed with equal "
                    "line gaps and clear borders; LLM border/label weights "
                    "restored; OAuth Providers + Email Service external "
                    "boxes and the two labelled edges added. Canvas "
                    "1780x1645.")
    cont["box_ids"].extend(["X050", "X051", "X052", "X053",
                            "X054", "X055", "X056", "X057"])
    cont["box_texts"].extend([s for _, _, _, s in oauth] +
                             [s for _, _, _, s in email])
    cont["free_ids"].extend(["X058", "X059"])
    cont["free_texts"].extend(["OAuth sign-in [HTTPS]",
                               "Password-reset email [SMTP]"])
    for b in ("OAuth Providers", "Email Service"):
        if b not in cont["bold"]:
            cont["bold"].append(b)

    dump("trace.json", trace)
    dump("text-content.json", cont)
    dump("font-plan.json", plan)
    dump("letter-spacing.json", {})

    print("shapes", len(trace["shapes"]), "lines", len(trace["lines"]),
          "texts", len(trace["texts"]), "canvas", trace["canvas"])
    for s in trace["shapes"]:
        print(" ", s["id"], s["bbox"], "sw", s["stroke_width"])
    for ln in trace["lines"]:
        print(" ", ln["id"], ln["segs"])


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""F2 owner-fix build for the Allocation figure (figure 04).

Applies only the owner's three fixes:
  (a) `Docker-capable Host` and the deployment-node bracket text restored to
      the measured original weights/sizes (title 17 -> 21 px bold, bracket
      20 px regular, moved down to the original baseline; the bracket is
      wrapped after "containerized" so the HTTPS line has a clear channel).
  (b) the Internet -> Web Server HTTPS edge is one continuous line at the
      measured 2.5 px #474747 and no longer runs through the frame title.
  (c) add OAuth Providers + Email Service external nodes in the figure's
      LLM Provider API style with labelled edges from Application Server:
      "OAuth sign-in [HTTPS]" and "Password-reset email [SMTP]".
      Canvas grows right/bottom 1331x1283 -> 1725x1600; all existing nodes
      keep their exact geometry.

Writes trace.json, text-content.json, font-plan.json and an empty
letter-spacing.json.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f2_layout_common import (add_line, add_shape, ink_size, plan_entry,
                              text_entry)  # noqa: E402

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "docs", "diagrams", "rebuild", "allocation")


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

    trace["canvas"] = {"w": 1725, "h": 1600}

    # ------------------------------------------------ (a) frame label sizes
    # measured original: title cap 15 px (Arial bold 21), bracket cap ~14 px
    # (Arial regular 20); original baseline y=562, second band y=584.
    title = text_entry("X011", strings["X011"], "bold", 21, left=60, top=547)
    by_id["X011"]["bbox"] = title["bbox"]
    plan["X011"] = plan_entry(by_id["X011"], "bold", 21)

    a = text_entry("X010", "[Deployment Node: containerized", "regular", 20,
                   left=288, top=547)
    by_id["X010"]["bbox"] = a["bbox"]
    plan["X010"] = plan_entry(by_id["X010"], "regular", 20)

    b = text_entry("X040", "deployment, Docker Compose]", "regular", 20,
                   left=66, top=570)
    trace["texts"].append(b)
    by_id["X040"] = b
    plan["X040"] = plan_entry(b, "regular", 20)

    # replace the single long bracket string with its two wrapped runs
    k = cont["free_ids"].index("X010")
    cont["free_ids"][k:k + 1] = ["X010", "X040"]
    cont["free_texts"][k:k + 1] = ["[Deployment Node: containerized",
                                   "deployment, Docker Compose]"]

    # ------------------------------------------------ (b) one continuous HTTPS line
    for i, ln in enumerate(trace["lines"]):
        if ln["id"] == "L07":
            ln["segs"] = [[[597, 473], [593, 615]]]
            ln["bbox"] = [593, 473, 597, 615]
            ln["color"] = "#474747"
            ln["stroke"] = 2.5
            ln["arrow_tip"] = [593, 615]
            ln["arrow_from"] = [597, 473]
        elif ln["id"] == "L08":
            del trace["lines"][i]
            break

    # ------------------------------------- (c) external nodes + labelled edges
    add_shape(trace, "S10", [900, 1420, 1291, 1565],
              "#6A5ACD", "#3F3494", 2, 15)
    add_shape(trace, "S11", [1308, 1420, 1699, 1565],
              "#6A5ACD", "#3F3494", 2, 15)

    def box_texts(box_id, lines):
        shape = next(s for s in trace["shapes"] if s["id"] == box_id)
        x0, y0, x1, y1 = shape["bbox"]
        cx = (x0 + x1) / 2.0
        heights = []
        for tid, weight, size, content in lines:
            iw, ih, bb = ink_size(content, weight, size)
            heights.append((tid, weight, size, content, iw, ih, bb))
        body = sum(h[5] for h in heights) + 7 * (len(lines) - 1)
        cy = y0 + (y1 - y0 - body) / 2.0
        for tid, weight, size, content, iw, ih, bb in heights:
            left = cx - (bb[0] + bb[2]) / 2.0
            ent = text_entry(tid, content, size=size, weight=weight,
                             left=left, top=cy, inside=box_id,
                             colour="#FFFFFF")
            trace["texts"].append(ent)
            by_id[tid] = ent
            plan[tid] = plan_entry(ent, weight, size)
            cy += ih + 7

    box_texts("S10", [
        ("X041", "bold", 23, "OAuth Providers"),
        ("X042", "regular", 18, "[External Software System]"),
        ("X043", "regular", 18, "Google and GitHub"),
        ("X044", "regular", 18, "OAuth 2.0"),
    ])
    box_texts("S11", [
        ("X045", "bold", 23, "Email Service"),
        ("X046", "regular", 18, "[External Software System]"),
        ("X047", "regular", 18, "Password-reset mail via SMTP"),
        ("X048", "regular", 18, "Mailpit in development"),
    ])
    cont["box_ids"].extend(["X041", "X042", "X043", "X044",
                            "X045", "X046", "X047", "X048"])
    cont["box_texts"].extend([
        "OAuth Providers", "[External Software System]",
        "Google and GitHub", "OAuth 2.0",
        "Email Service", "[External Software System]",
        "Password-reset mail via SMTP", "Mailpit in development"])
    for label in ("OAuth Providers", "Email Service"):
        if label not in cont["bold"]:
            cont["bold"].append(label)

    for tid, content, left, top in (
            ("X049", "OAuth sign-in [HTTPS]", 900, 1359),
            ("X050", "Password-reset email [SMTP]", 1200, 1329)):
        ent = text_entry(tid, content, "regular", 18, left=left, top=top,
                         inside=None, colour="#222222")
        trace["texts"].append(ent)
        by_id[tid] = ent
        plan[tid] = plan_entry(ent, "regular", 18)
    cont["free_ids"].extend(["X049", "X050"])
    cont["free_texts"].extend(["OAuth sign-in [HTTPS]",
                               "Password-reset email [SMTP]"])

    add_line(trace, "L09",
             [[(791, 890), (870, 890)], [(870, 890), (870, 1380)],
              [(870, 1380), (1095, 1380)], [(1095, 1380), (1095, 1420)]],
             "#444444", 2.0, tip=[1095, 1420], source=[791, 890])
    add_line(trace, "L10",
             [[(791, 910), (880, 910)], [(880, 910), (880, 1350)],
              [(880, 1350), (1503, 1350)], [(1503, 1350), (1503, 1420)]],
             "#444444", 2.0, tip=[1503, 1420], source=[791, 910])

    cont["note"] = ("Allocation owner-fix (F2): frame label restored to "
                    "measured 21 px bold / 20 px regular and wrapped below "
                    "the border; HTTPS edge continuous and clear of the "
                    "label; OAuth Providers + Email Service external nodes "
                    "and the two labelled edges added. Canvas 1725x1600.")

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

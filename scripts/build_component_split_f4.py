# -*- coding: utf-8 -*-
"""F4 owner fixes for the Component figure (Architecture Fig 4).

The approved Stage B components/labels are kept verbatim.  The single
2361 px page is re-laid out as two horizontal pages (08a left columns,
08b right columns) so the printed minimum font size stays above 7 pt at the
docx display width of 9.15 in:

    pt = px / page_width_px * 9.15 * 72
    08a: 20 px / 1400 * 658.8 = 9.41 pt
    08b: 17 px / 1400 * 658.8 = 8.00 pt

Nothing is shrunk.  The only in-page content fix is the Grading & Evaluation
Service box: widened to 300 px and heightened to 190 px so its five rendered
lines ("Grading &" / "Evaluation Service" + 3 body lines) sit on an even
28/25/25/25 px grid with 30.5 px padding.

Usage: python scripts/build_component_split_f4.py [--prefix]
  --prefix renders the pre-fix (old 262x167 S05, six lines) at the same page
           coordinates, for the overlay/diff proof only.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f4_build_lib import (build_page, text_center_for_ink, text_left_for_ink,
                          translate_shape, translate_text, write_font_plan,
                          write_letter_spacing, write_text_content)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "docs", "diagrams", "rebuild", "component")
PREFIX = "--prefix" in sys.argv

W, H = 1400, 980

# tier centres / band rectangles
CTRL_TOP, CTRL_BOT = 20.0, 225.0
SVC_TOP, SVC_BOT = 240.0, 470.0
REPO_TOP, REPO_BOT = 485.0, 723.0

P1_BANDS = [(60.0, CTRL_TOP, 1336.0, CTRL_BOT),
            (145.0, SVC_TOP, 1336.0, SVC_BOT),
            (145.0, REPO_TOP, 1336.0, REPO_BOT)]
P2_BANDS = [(266.0, CTRL_TOP, 1261.0, CTRL_BOT),
            (237.0, SVC_TOP, 1176.0, SVC_BOT),
            (237.0, REPO_TOP, 1223.0, REPO_BOT)]

P1_CAPTIONS = {"B001": (81, 49), "B002": (224, 48),
               "B032": (166, 266), "B033": (274, 266),
               "B065": (166, 510), "B066": (319, 513)}
P2_CAPTIONS = {"B001": (287, 49), "B002": (430, 48),
               "B032": (258, 266), "B033": (366, 266),
               "B065": (258, 510), "B066": (411, 513)}


def band_dashes(bands):
    out = []
    for (x0, y0, x1, y1) in bands:
        span_h = int(x1 - x0)
        span_v = int(y1 - y0)
        out.append({"axis": "h", "y": y0, "x0": x0 + 13, "x1": x1 - 4,
                    "dashes": span_h // 29 + 1, "on": 14, "off": 15})
        out.append({"axis": "h", "y": y1 - 1, "x0": x0, "x1": x1,
                    "dashes": span_h // 29 + 1, "on": 14, "off": 15})
        out.append({"axis": "v", "x": x0, "y0": y0 + 4, "y1": y1,
                    "dashes": span_v // 29 + 1, "on": 14, "off": 15})
        out.append({"axis": "v", "x": x1 - 1, "y0": y0 + 13, "y1": y1 - 1,
                    "dashes": span_v // 29 + 1, "on": 14, "off": 15})
    return out


def boundary(bid, x0, y0, x1, y1):
    return {"id": bid, "kind": "boundary", "bbox": [x0, y0, x1, y1],
            "fill": "#FFFFFF", "stroke": "#666666", "stroke_width": 2,
            "radius": 0, "dashed": True, "dash_on": 14, "dash_off": 15}


def line(lid, segs, tip, source, note, stroke=2.0):
    xs = [p[0] for seg in segs for p in seg]
    ys = [p[1] for seg in segs for p in seg]
    return {"id": lid, "bbox": [min(xs), min(ys), max(xs), max(ys)],
            "segs": segs, "thickness": 3.0, "color": "#34383B",
            "stroke": stroke, "arrow_tip": tip, "arrow_from": source,
            "note": note}


def text(tid, content, weight, size, x, y, inside, ink="#222527", ls=0.0):
    return {"id": tid, "content": content, "weight": weight, "size": size,
            "anchor": "top", "x": x, "y": y, "ink": ink, "ls": ls,
            "measured": [0, 0, 0, 0], "inside": inside}


def make_page(ids, bands, captions, dx_map, dy_map, lines, extra_texts=None,
              old_s05=False):
    spec = json.load(open(os.path.join(D, "spec.json"), encoding="utf-8"))
    shapes = []
    for s in spec["shapes"]:
        if s["id"] not in ids:
            continue
        if s["id"] in ("S27", "S28", "S29"):
            continue
        if s["id"] == "S05":
            ns = json.loads(json.dumps(s))
            if old_s05:
                ns["bbox"] = [556.0, 275.0, 818.0, 442.0]
            else:
                ns["bbox"] = [556.0, 275.0, 856.0, 460.0]
            shapes.append(ns)
            continue
        shapes.append(translate_shape(s, dx_map.get(s["id"], 0.0),
                                      dy_map.get(s["id"], 0.0)))
    texts = []
    for t in spec["texts"]:
        if t.get("inside") in ids:
            if t["inside"] == "S05":
                continue                    # rebuilt below
            dx = dx_map.get(t["inside"], 0.0)
            dy = dy_map.get(t["inside"], 0.0)
            texts.append(translate_text(t, dx, dy))
        elif t["id"] in captions:
            nt = translate_text(t, 0.0, 0.0)
            nt["x"], nt["y"] = captions[t["id"]]
            texts.append(nt)
    if "S05" in ids:
        if old_s05:
            old = {t["id"]: t for t in spec["texts"]}
            for tid in ("B034", "B040", "B047", "B055", "B062", "B064"):
                texts.append(translate_text(old[tid], 556 - 1635,
                                            275 - 431))
        else:
            cx = (556 + 856) / 2.0
            rows = [("B034", "Grading &", "bold", 28, 323.0),
                    ("B040", "Evaluation Service", "bold", 28, 357.0),
                    ("B055", "MCQ key, SQL", "regular", 23, 382.0),
                    ("B062", "sandbox, Prompt", "regular", 23, 407.0),
                    ("B064", "Builder → Evaluator", "regular", 23, 432.0)]
            for tid, s, w, size, y in rows:
                texts.append(text(tid, s, w, size,
                                  text_center_for_ink(s, w, size, cx), y,
                                  "S05"))
    for extra in (extra_texts or []):
        texts.append(extra)
    shapes.extend([boundary("S27", *bands[0]), boundary("S28", *bands[1]),
                   boundary("S29", *bands[2])])
    # preserve the original text order as far as possible
    order = {t["id"]: i for i, t in enumerate(spec["texts"])}
    texts.sort(key=lambda t: order.get(t["id"], 999))
    # duplicate-id guard per page
    seen = set()
    for t in texts:
        assert t["id"] not in seen, "duplicate text id %s" % t["id"]
        seen.add(t["id"])
    return shapes, texts, lines


def build_08a():
    ids = {"S07", "S13", "S09", "S14", "S24", "S22", "S21", "S11",
           "S17", "S23", "S19", "S04", "S02", "S16", "S01"}
    dx = {"S02": 179 - 392, "S16": 179 - 408, "S01": 714 - 927}
    dy = {"S07": 55.5 - 131, "S13": 56 - 131, "S09": 56 - 131,
          "S14": 56 - 131,
          "S24": 315 - 460, "S22": 305.5 - 450, "S21": 305.5 - 450,
          "S11": 296 - 441,
          "S17": 549.5 - 769, "S23": 549.5 - 769, "S19": 549.5 - 769,
          "S04": 530.5 - 750,
          "S02": 746 - 1048, "S16": 884 - 1290, "S01": 738 - 1040}
    lines = [
        line("L01", [[[238.0, 209.5], [289.0, 315.0]]], [289.0, 315.0],
             [238.0, 209.5], "Auth Controller -> Auth Service"),
        line("L02", [[[552.9, 209.0], [585.0, 305.5]]], [585.0, 305.5],
             [552.9, 209.0], "Practice Controller -> Practice Service"),
        line("L03", [[[865.5, 209.0], [884.0, 305.5]]], [884.0, 305.5],
             [865.5, 209.0], "Curriculum Controller -> Curriculum Service"),
        line("L04", [[[1180.0, 209.0], [1180.0, 296.0]]], [1180.0, 296.0],
             [1180.0, 209.0], "Question Bank Controller -> Question Bank Service"),
        line("L08", [[[302.0, 431.0], [304.0, 549.5]]], [304.0, 549.5],
             [302.0, 431.0], "Auth Service -> Account Repository"),
        line("L09", [[[595.0, 440.5], [598.0, 549.5]]], [598.0, 549.5],
             [595.0, 440.5], "Practice Service -> Session & Plan Repository"),
        line("L10", [[[888.0, 440.5], [885.0, 549.5]]], [885.0, 549.5],
             [888.0, 440.5], "Curriculum Service -> Curriculum Repository"),
        line("L11", [[[1181.0, 450.0], [1182.0, 530.5]]], [1182.0, 530.5],
             [1181.0, 450.0], "Question Bank Service -> Question Repository"),
        line("L15", [[[381.0, 684.5], [719.0, 738.0]]], [719.0, 738.0],
             [381.0, 684.5], "Account Repository -> Database"),
        line("L16", [[[679.0, 684.5], [781.0, 738.0]]], [781.0, 738.0],
             [679.0, 684.5], "Session & Plan Repository -> Database"),
        line("L17", [[[963.0, 684.5], [906.0, 738.0]]], [906.0, 738.0],
             [963.0, 684.5], "Curriculum Repository -> Database"),
        line("L18", [[[1181.0, 703.5], [965.0, 738.0]]], [965.0, 738.0],
             [1181.0, 703.5], "Question Repository -> Database"),
        line("L22", [[[618.0, 798.5], [714.0, 798.5]]], [714.0, 798.5],
             [618.0, 798.5], "LLM Gateway -> Database (cache)"),
        line("L23", [[[613.0, 851.0], [614.0, 884.0]]], [614.0, 884.0],
             [613.0, 851.0], "LLM Gateway -> LLM Provider API"),
    ]
    shapes, texts, lines = make_page(ids, P1_BANDS, P1_CAPTIONS, dx, dy, lines)
    # cache label: centred in the 96 px Gateway->Database gap, above the line
    cache = {"id": "B099", "content": "cache", "weight": "regular",
             "size": 22, "anchor": "top", "y": 791.0, "ink": "#222527",
             "ls": 0.0, "measured": [0, 0, 0, 0], "inside": None}
    cache["x"] = text_center_for_ink("cache", "regular", 22, 666.0)
    texts.append(cache)
    order = {t["id"]: i for i, t in enumerate(texts)}
    texts.sort(key=lambda t: 0 if t["id"] in ("B001", "B002", "B032",
                                              "B033", "B065", "B066",
                                              "B099") else 1)
    return shapes, texts, lines


def build_08b():
    ids = {"S10", "S08", "S12", "S15", "S05", "S06", "S26", "S18", "S20",
           "S03", "S25", "S01"}
    dx = {"S10": -1079, "S08": -1079, "S12": -1039,
          "S15": -1079, "S06": -1039,
          "S26": -1079, "S18": -1079, "S20": -1039,
          "S03": 179 - 1466, "S25": 179 - 1466, "S01": 714 - 927}
    dy = {"S10": 55.5 - 131, "S08": 55.5 - 131, "S12": 56 - 131,
          "S15": 296 - 441, "S06": 286.5 - 431,
          "S26": 549.5 - 769, "S18": 549.5 - 769, "S20": 558.5 - 778,
          "S03": 746 - 1048, "S25": 884 - 1294, "S01": 738 - 1040}
    lines = [
        line("L05", [[[415.0, 208.5], [400.0, 296.0]]], [400.0, 296.0],
             [415.0, 208.5], "Analytics Controller -> Competency & Gap Service"),
        line("L06", [[[729.9, 209.5], [699.0, 275.0]]], [699.0, 275.0],
             [729.9, 209.5], "Grading Controller -> Grading & Evaluation Service"),
        line("L07", [[[1083.0, 209.0], [1042.0, 286.5]]], [1042.0, 286.5],
             [1083.0, 209.0], "Accounts Controller -> Admin & Settings Service"),
        line("L12", [[[394.0, 450.0], [391.0, 549.5]]], [391.0, 549.5],
             [394.0, 450.0], "Competency & Gap Service -> Competency Repository"),
        line("L13", [[[686.0, 466.0], [684.0, 549.5]]], [684.0, 549.5],
             [686.0, 466.0], "Grading & Evaluation Service -> Grading Repository"),
        line("L14", [[[1025.0, 459.5], [1042.0, 558.5]]], [1042.0, 558.5],
             [1025.0, 459.5], "Admin & Settings Service -> Audit & Settings Repository"),
        line("L19", [[[394.5, 684.5], [850.0, 738.0]]], [850.0, 738.0],
             [394.5, 684.5], "Competency Repository -> Database"),
        line("L20", [[[1043.5, 675.5], [1050.0, 738.0]]], [1050.0, 738.0],
             [1043.5, 675.5], "Audit & Settings Repository -> Database"),
        line("L21", [[[687.0, 684.5], [950.0, 738.0]]], [950.0, 738.0],
             [687.0, 684.5], "Grading Repository -> Database"),
        line("L24", [[[398.5, 851.0], [398.5, 884.0]]], [398.5, 884.0],
             [398.5, 851.0], "Sandbox Runner -> SQL Sandbox"),
    ]
    shapes, texts, lines = make_page(ids, P2_BANDS, P2_CAPTIONS, dx, dy,
                                     lines, old_s05=PREFIX)
    return shapes, texts, lines


def write_trace(name, canvas, shapes, dashes, lines, texts):
    trace = {"canvas": canvas, "source": "component Stage B + F4 split",
             "shapes": shapes, "dashes": dashes, "lines": lines,
             "sticks": [],
             "texts": [dict(t, bbox=t["measured"]) for t in texts]}
    with open(os.path.join(D, "trace-%s.json" % name), "w",
              encoding="utf-8") as f:
        json.dump(trace, f, indent=1)


def main():
    suffix = "-prefix" if PREFIX else ""
    pages = [("08a", P1_BANDS, build_08a), ("08b", P2_BANDS, build_08b)]
    summary = {"canvas": {"w": W, "h": H},
               "display_width_in": 9.15,
               "note": "F4 two-page horizontal split; unchanged cards keep "
                       "their exact size/text, only x/y translate. 08b "
                       "repeats the shared Database cylinder so its three "
                       "right-hand repositories keep a visible sink.",
               "pages": {}}
    for name, bands, fn in pages:
        shapes, texts, lines = fn()
        dashes = band_dashes(bands)
        spec = build_page(D, "component-%s%s" % (name, suffix),
                          {"w": W, "h": H}, shapes, dashes, lines, texts,
                          spec_filename="spec-%s%s.json" % (name, suffix))
        if not PREFIX:
            write_trace(name, spec["canvas"], shapes, dashes,
                        spec["lines"], spec["texts"])
            free = [t for t in spec["texts"] if t.get("inside") is None]
            box = [t for t in spec["texts"] if t.get("inside") is not None]
            write_text_content(
                os.path.join(D, "text-content-%s.json" % name),
                [t["id"] for t in free], [t["content"] for t in free],
                [t["id"] for t in box], [t["content"] for t in box],
                [t["content"] for t in spec["texts"]
                 if t["weight"] == "bold"],
                "Component page %s of the F4 two-page split: %d labels "
                "(%d free + %d box). Same approved content as Stage B; "
                "layout only." % (name, len(spec["texts"]), len(free),
                                  len(box)))
            write_font_plan(os.path.join(D, "font-plan-%s.json" % name),
                            spec["texts"])
            write_letter_spacing(
                os.path.join(D, "letter-spacing-%s.json" % name),
                spec["texts"])
            summary["pages"][name] = {
                "file": "component-%s" % name,
                "canvas": {"w": W, "h": H},
                "labels": len(spec["texts"]),
                "free": len(free), "box": len(box),
                "shapes": len(shapes), "dashes": len(dashes),
                "lines": len(spec["lines"]),
                "arrowheads": sum(1 for ln in spec["lines"]
                                  if ln.get("arrow_tip")),
                "min_font_px": min(t["size"] for t in spec["texts"]),
                "min_pt_at_9.15in": round(min(t["size"]
                                              for t in spec["texts"])
                                          / W * 9.15 * 72, 2),
                "printed_size_in": [9.15, round(9.15 * H / W, 2)],
            }
    if not PREFIX:
        with open(os.path.join(D, "split.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=1)
        print("wrote", os.path.join(D, "split.json"))


if __name__ == "__main__":
    main()

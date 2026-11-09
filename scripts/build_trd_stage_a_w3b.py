# -*- coding: utf-8 -*-
"""Build the Stage A clone of the v1.1 Table Relationship Diagram from the
measured trace (no content delta, same 3440x2080 canvas).

Usage:
  tools/.venv/Scripts/python.exe scripts/build_trd_stage_a_w3b.py \
      docs/diagrams/rebuild/trd
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trd_common_w3b import (ORIGINAL_CARDS, LEGACY, bbox_of, drawio_page,
                            svg_page, text_item, page_text_content, fmt)

TITLE_SIZE = 34
NAME_SIZE = 26
MARKER_SIZE = 20
TYPE_SIZE = 24
HEADER_H = 66
LEGEND_SIZE = 30


def main():
    d = sys.argv[1]
    trace = json.load(open(os.path.join(d, "trace.json"), encoding="utf-8"))
    cards_geo = sorted(trace["cards"], key=lambda c: (c["bbox"][0], c["bbox"][1]))
    if len(cards_geo) != len(ORIGINAL_CARDS):
        raise SystemExit("trace cards %d != original cards %d"
                         % (len(cards_geo), len(ORIGINAL_CARDS)))

    cards = []
    texts = []
    underlines = []
    for ci, (geo, (title, rows)) in enumerate(zip(cards_geo, ORIGINAL_CARDS)):
        x, y, x1, y1 = geo["bbox"]
        w, h = x1 - x, y1 - y
        n = len(rows)
        if n != len(geo["rows"]):
            raise SystemExit("%s: data rows %d != trace rows %d"
                             % (title, n, len(geo["rows"])))
        row_h = (h - HEADER_H) / float(n)
        t = text_item("T%02d" % (ci + 1), title, x + w / 2.0,
                      y + HEADER_H / 2.0 + 12, TITLE_SIZE, "bold", "middle",
                      measured=geo["header"])
        texts.append(t)
        rows_out = []
        for ri, (name, marker, typ) in enumerate(rows):
            baseline = y + HEADER_H + (ri + 1) * row_h - 12
            is_bold = bool(marker)
            nt = text_item("N%02d_%02d" % (ci + 1, ri + 1), name,
                           x + 20, baseline, NAME_SIZE,
                           "bold" if is_bold else "regular", "start")
            texts.append(nt)
            if "[PK" in marker:
                b = bbox_of(nt)
                underlines.append([b[0], baseline + 5.5, b[2], baseline + 5.5])
            if marker:
                texts.append(text_item("M%02d_%02d" % (ci + 1, ri + 1),
                                       marker, x + w - 101, baseline,
                                       MARKER_SIZE, "bold", "end"))
            texts.append(text_item("Y%02d_%02d" % (ci + 1, ri + 1), typ,
                                   x + w - 20, baseline, TYPE_SIZE,
                                   "regular", "end"))
            rows_out.append({"name": name, "type": typ, "marker": marker,
                             "pk": "[PK" in marker, "fk": "FK" in marker})
        cards.append({"title": title, "bbox": [x, y, w, h],
                      "header_h": HEADER_H, "row_h": row_h,
                      "title_size": TITLE_SIZE, "row_size": NAME_SIZE,
                      "rows": rows_out, "legacy": False,
                      "underlines": underlines[-n:] if n else []})

    # ---- legend (measured frame + transcribed text)
    legend_texts = [
        text_item("LG1", "name", 925, 1981, LEGEND_SIZE, "bold", "start"),
        text_item("LG2", "= primary key", 1011, 1981, LEGEND_SIZE, "regular", "start"),
        text_item("LG3", "[FK] = foreign key", 1411, 1981, LEGEND_SIZE, "regular", "start"),
        text_item("LG4", "= one", 1939, 1981, LEGEND_SIZE, "regular", "start"),
        text_item("LG5", "= many", 2269, 1981, LEGEND_SIZE, "regular", "start"),
    ]
    for t in legend_texts:
        t["free"] = True
    texts.extend(legend_texts)
    legend = {
        "bbox": [879, 1912, 2562, 2021],
        "texts": [],
        "segments": [
            [925, 1986, 1000, 1986],
            [1776, 1968, 1885, 1968],
            [1907, 1949, 1907, 1987],
            [2112, 1968, 2170, 1968],
            [2170, 1968, 2237, 1949],
            [2170, 1968, 2237, 1987],
        ],
    }

    # ---- measured connectors
    conn = trace["connectors"]
    segments = []
    for h in conn["h"]:
        segments.append(h)
    for v in conn["v"]:
        segments.append(v)
    for dg in conn["diag"]:
        segments.append(dg)

    page = {
        "name": "Table Relationship Diagram (original style)",
        "canvas": trace["canvas"],
        "cards": cards,
        "texts": texts,
        "segments": segments,
        "legend": legend,
        "underlines": underlines,
    }
    # underlines are drawn at page level in the SVG
    for card in cards:
        card["underlines"] = []
    page["underlines"] = underlines

    svg_page(page, os.path.join(d, "trd-original-style.svg"))
    drawio_page(page, os.path.join(d, "trd-original-style.drawio"))
    spec = {"canvas": trace["canvas"], "source": trace["source"],
            "cards": cards, "texts": texts, "segments": segments,
            "legend": legend, "underlines": underlines,
            "style": {"font_family": "Arial", "header_fill": "#E8E8E8",
                      "body_fill": "#FFFFFF", "stroke": "#1A1A1A",
                      "row_separator": "#DCDCDC"}}
    with open(os.path.join(d, "spec.json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=1)
    with open(os.path.join(d, "text-content.json"), "w", encoding="utf-8") as f:
        json.dump(page_text_content(page), f, indent=1)
    print("wrote trd-original-style.svg/.drawio, spec.json, text-content.json")
    print("cards %d, texts %d, segments %d, underlines %d"
          % (len(cards), len(texts), len(segments), len(underlines)))


if __name__ == "__main__":
    main()

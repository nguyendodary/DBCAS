# -*- coding: utf-8 -*-
"""Stage B: content-delta Table Relationship Diagram split into six legible
consecutive pages (3440x2080 landscape), same card grammar as the v1.1
original. 41 real tables, 293 columns, 59 FKs, 19 migrations.

No layout engine: deterministic 4-column / 2-row card grid. Every FK gets a
crow's-foot connector; FKs crossing a page boundary end at the top page edge
with a labelled stub naming the target table and column(s), and the target
page carries the matching incoming stub.

Usage:
  tools/.venv/Scripts/python.exe scripts/build_trd_stage_b_w3b.py \
      docs/diagrams/rebuild/trd
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trd_common_w3b import (bbox_of, dedupe_segments, drawio_page, fmt,
                            load_schema, page_text_content, svg_page,
                            text_item)

CANVAS = {"w": 3440, "h": 2080}
COL_X = [40, 890, 1740, 2590]
CARD_W = 810
HEADER_H = 74
ROW_H = 62
PAGE_ROW_H = [78, 78, 66, 62, 70]
TOP_Y = 220
BOTTOM_Y = 1120
TITLE_SIZE = 38
NAME_SIZE = 32
MARKER_SIZE = 22
TYPE_SIZE = 24
LEGEND_W = 810
STUB_SIZE = 20

PAGE_ROWS = [
    [["account", "account_identity", "account_role_audit", "user_profile"],
     ["refresh_session", "oauth_handoff", "role", "account_role"],
     ["login_throttle", "assessment_question"]],
    [["concept", "question_candidate", "course_learning_outcome",
      "clo_concept"],
     ["question_concept", "password_reset_token", "llm_cache",
      "assessment_concept"],
     ["concept_dependency", "password_reset_audit", "system_setting"]],
    [["question", "question_translation", "mcq_option", "rubric"],
     ["selection_log", "sql_test_dataset", "competency_gap"]],
    [["assessment_session", "attempt", "session_question_plan",
      "session_start_request"],
     ["adaptive_event", "evaluation_record", "result_release_event"]],
    [["assessment", "assessment_blueprint", "grade_review", "grading_job"],
     ["grade_edit_audit", "concept_competency"]],
]
PAGES = [sum(rows, []) for rows in PAGE_ROWS]
TOP_Y = 160
ROW_GAP = 40


def make_cards(tables_by_name, page_rows, row_h):
    cards = []
    y = TOP_Y
    for rowi, names in enumerate(page_rows):
        row_cards = []
        for col, name in enumerate(names):
            t = tables_by_name[name]
            h = HEADER_H + len(t["columns"]) * row_h
            row_cards.append({"title": name, "bbox": [COL_X[col], y, CARD_W, h],
                              "header_h": HEADER_H, "row_h": row_h,
                              "title_size": TITLE_SIZE,
                              "row_size": NAME_SIZE,
                              "rows": t["columns"], "legacy": t["legacy"],
                              "col": col, "grid_row": rowi, "table": name})
        cards.extend(row_cards)
        y += max(c["bbox"][3] for c in row_cards) + ROW_GAP
    return cards


def card_texts(cards):
    texts = []
    underlines = []
    for ci, card in enumerate(cards):
        x, y, w, h = card["bbox"]
        texts.append(text_item("T%02d" % (ci + 1), card["title"],
                               x + w / 2.0, y + HEADER_H / 2.0 + 13,
                               TITLE_SIZE, "bold", "middle"))
        if card["legacy"]:
            texts.append(text_item("G%02d" % (ci + 1), "LEGACY",
                                   x + w - 12, y + 30, 20, "bold", "end",
                                   color="#7A0000"))
        for ri, row in enumerate(card["rows"]):
            baseline = y + HEADER_H + (ri + 1) * card["row_h"] - 9
            nt = text_item("N%02d_%02d" % (ci + 1, ri + 1), row["name"],
                           x + 20, baseline, NAME_SIZE,
                           "bold" if row["marker"] else "regular", "start")
            texts.append(nt)
            if row["pk"]:
                b = bbox_of(nt)
                underlines.append([b[0], baseline + 6.5, b[2], baseline + 6.5])
            if row["marker"]:
                texts.append(text_item("M%02d_%02d" % (ci + 1, ri + 1),
                                       row["marker"], x + w - 320, baseline,
                                       MARKER_SIZE, "bold", "end"))
            typ = row["type"] + (" NOT NULL" if not row["nullable"] else " NULL")
            texts.append(text_item("Y%02d_%02d" % (ci + 1, ri + 1), typ,
                                   x + w - 20, baseline, TYPE_SIZE,
                                   "regular", "end"))
    return texts, underlines


def row_y(card, column):
    for ri, r in enumerate(card["rows"]):
        if r["name"] == column:
            return card["bbox"][1] + HEADER_H + (ri + 0.5) * card["row_h"]
    raise SystemExit("column %s not in %s" % (column, card["table"]))


def crowfoot(segments, edge, y, side):
    """Three prongs touching the card edge; the many side."""
    px = edge + 22 if side == "right" else edge - 22
    segments += [[px, y, edge, y - 14], [px, y, edge, y],
                 [px, y, edge, y + 14]]
    return px


def one_tick(segments, edge, y, side):
    x = edge + 12 if side == "right" else edge - 12
    segments.append([x, y - 15, x, y + 15])


def add_path(segments, pts):
    for a, b in zip(pts, pts[1:]):
        if abs(a[0] - b[0]) < 0.01 and abs(a[1] - b[1]) < 0.01:
            continue
        segments.append([a[0], a[1], b[0], b[1]])


def page_layout_metrics(cards):
    top_h = max(c["bbox"][3] - c["bbox"][1]
                for c in cards if c["grid_row"] == 0)
    bottom_ends = [c["bbox"][1] + c["bbox"][3] - c["bbox"][1]
                   for c in cards if c["grid_row"] == 1]
    return top_h, bottom_ends


def main():
    d = sys.argv[1]
    raw, tables = load_schema()
    by_name = {t["table"]: t for t in tables}
    total_cols = sum(len(t["columns"]) for t in tables)
    total_fks = len(raw["foreign_keys"])
    total_mig = len(raw["migrations"])
    legacy = sorted(by_name[t]["table"] for t in by_name
                    if by_name[t]["legacy"])
    page_of = {name: pi + 1 for pi, names in enumerate(PAGES) for name in names}

    fk_by_source = {}
    for fk in raw["foreign_keys"]:
        fk_by_source.setdefault(fk["source"], []).append(fk)

    pages = []
    cross = []
    for pi, names in enumerate(PAGES):
        cards = make_cards(by_name, PAGE_ROWS[pi], PAGE_ROW_H[pi])
        by_table = {c["table"]: c for c in cards}
        texts, underlines = card_texts(cards)
        segments = []

        # ---------------- within-page FK connectors
        internal = 0
        for fk in raw["foreign_keys"]:
            s, dst = fk["source"], fk["destination"]
            if s not in by_table or dst not in by_table:
                continue
            internal += 1
            src, dcard = by_table[s], by_table[dst]
            ys = row_y(src, fk["columns"][0])
            yd = row_y(dcard, fk["reference_columns"][0])
            sx0, sy0, sw, sh = src["bbox"]
            dx0, dy0, dw, dh = dcard["bbox"]
            # self reference: loop on the right edge
            if s == dst:
                edge = sx0 + sw
                p = crowfoot(segments, edge, ys, "right")
                add_path(segments, [[p, ys], [edge + 40, ys],
                                    [edge + 40, yd], [edge + 22, yd]])
                one_tick(segments, edge, yd, "right")
                continue
            side = "right" if dx0 >= sx0 else "left"
            src_edge = sx0 + sw if side == "right" else sx0
            src_out = crowfoot(segments, src_edge, ys, side)
            dst_edge = dx0 if side == "right" else dx0 + dw
            dst_out = dst_edge - 22 if side == "right" else dst_edge + 22
            xc = src_edge + 22 if side == "right" else src_edge - 22
            xd = dst_edge - 22 if side == "right" else dst_edge + 22
            # corridor: in the 40 px gap below the upper of the two rows;
            # column gaps carry the vertical run past any intermediate row
            row_bottom = {r: max(c["bbox"][1] + c["bbox"][3]
                                 for c in cards if c["grid_row"] == r)
                          for r in range(max(src["grid_row"],
                                             dcard["grid_row"]) + 1)}
            upper = min(src["grid_row"], dcard["grid_row"])
            corr = row_bottom[upper] + 20
            add_path(segments, [[src_out, ys], [xc, ys], [xc, corr],
                                [xd, corr], [xd, yd], [dst_out, yd]])
            # the destination tick sits outside the edge the connector enters
            one_tick(segments, dst_edge, yd,
                     "left" if side == "right" else "right")

        # ---------------- cross-page FK stubs
        outgoing, incoming = [], []
        for fk in raw["foreign_keys"]:
            s, dst = fk["source"], fk["destination"]
            if s not in by_table and dst not in by_table:
                continue
            cols = ",".join(fk["columns"])
            refs = ",".join(fk["reference_columns"])
            if s in by_table and dst not in by_table:
                outgoing.append((s, cols, dst, refs, page_of[dst]))
            if dst in by_table and s not in by_table:
                incoming.append((s, cols, dst, refs, page_of[s]))

        stubs = []
        for s, cols, dst, refs, p in outgoing:
            stubs.append({"dir": "out", "text": "→ %s(%s) · p%d" % (dst, refs, p),
                          "src": s, "col": cols, "dst": dst, "p": p})
        for s, cols, dst, refs, p in incoming:
            stubs.append({"dir": "in", "text": "← %s(%s) · p%d" % (s, cols, p),
                          "src": s, "col": cols, "dst": dst, "p": p})
        stubs.sort(key=lambda z: (z["dir"] != "out", z["text"]))
        if len(stubs) > 20:
            raise SystemExit("page %d has %d stubs (max 20)" % (pi + 1, len(stubs)))
        slots = 5
        nrows = (len(stubs) + slots - 1) // slots
        size = STUB_SIZE if nrows <= 3 else 18
        slot_w = 688
        for si, stub in enumerate(stubs):
            slot = si % slots
            rowi = si // slots
            slot_start = 20 + slot * slot_w
            line_x = slot_start + 18
            baseline = (44 + rowi * 30) if nrows <= 3 else (44 + rowi * 24)
            label = text_item("S%02d_%02d" % (pi + 1, si + 1), stub["text"],
                              slot_start + 120, baseline, size,
                              "regular", "start")
            label["free"] = True
            texts.append(label)
            if stub["dir"] == "out":
                card = by_table[stub["src"]]
                y = row_y(card, stub["col"].split(",")[0])
                x0, yy, w, h = card["bbox"]
                side = "right" if card["col"] < 3 else "left"
                edge = x0 + w if side == "right" else x0
                p = crowfoot(segments, edge, y, side)
                xc = edge + 22 if side == "right" else edge - 22
                add_path(segments, [[p, y], [xc, y], [xc, 145],
                                    [line_x, 145], [line_x, 20]])
            else:
                card = by_table[stub["dst"]]
                # destination row = referenced column(s)
                refcol = None
                for fk in raw["foreign_keys"]:
                    if fk["source"] == stub["src"] and fk["destination"] == stub["dst"]:
                        refcol = fk["reference_columns"][0]
                        break
                y = row_y(card, refcol)
                x0, yy, w, h = card["bbox"]
                side = "right" if card["col"] < 3 else "left"
                edge = x0 + w if side == "right" else x0
                xd = edge + 22 if side == "right" else edge - 22
                add_path(segments, [[line_x, 20], [line_x, 145], [xd, 145],
                                    [xd, y], [edge, y]])
                one_tick(segments, edge, y, side)

        # ---------------- legend
        legend_y = max(c["bbox"][1] for c in cards)
        lx = COL_X[3]
        legend_bbox = [lx, legend_y, LEGEND_W, 440]
        legend_texts = [
            text_item("LGT", "Legend", lx + 24, legend_y + 44, 30, "bold", "start"),
            text_item("LG1", "name", lx + 24, legend_y + 88, 26, "bold", "start"),
            text_item("LG2", "= primary key", lx + 110, legend_y + 88, 26, "regular", "start"),
            text_item("LG3", "[FK] = foreign key (target shown after →)", lx + 24, legend_y + 128, 22, "regular", "start"),
            text_item("LG4", "= one", lx + 150, legend_y + 166, 26, "regular", "start"),
            text_item("LG5", "= many", lx + 210, legend_y + 206, 26, "regular", "start"),
            text_item("LG6", "LEGACY (dashed card) = legacy table, historical rows only",
                      lx + 24, legend_y + 250, 22, "regular", "start"),
            text_item("LG7", "%d tables · %d columns · %d FKs · %d migrations"
                      % (len(tables), total_cols, total_fks, total_mig),
                      lx + 24, legend_y + 306, 24, "bold", "start"),
            text_item("LG8", "Cross-page stub: arrow names target/source table, column(s), page",
                      lx + 24, legend_y + 348, 18, "regular", "start"),
            text_item("LG9", "Page %d of %d" % (pi + 1, len(PAGES)),
                      lx + 24, legend_y + 400, 24, "bold", "start"),
        ]
        for t in legend_texts:
            t["free"] = True
        texts.extend(legend_texts)
        legend_segments = [
            [lx + 24, legend_y + 98, lx + 95, legend_y + 98],
            [lx + 24, legend_y + 166, lx + 105, legend_y + 166],
            [lx + 120, legend_y + 149, lx + 120, legend_y + 183],
            [lx + 24, legend_y + 206, lx + 105, legend_y + 206],
            [lx + 105, legend_y + 206, lx + 170, legend_y + 188],
            [lx + 105, legend_y + 206, lx + 170, legend_y + 224],
        ]
        # legend "name" underline
        nb = bbox_of(legend_texts[1])
        legend_segments.insert(0, [nb[0], legend_y + 96, nb[2], legend_y + 96])

        page = {
            "name": "Table Relationship Diagram (%d/%d)" % (pi + 1, len(PAGES)),
            "canvas": CANVAS,
            "cards": cards,
            "texts": texts,
            "segments": dedupe_segments(segments),
            "legend": {"bbox": legend_bbox, "texts": [],
                       "segments": legend_segments},
            "underlines": underlines,
            "page": pi + 1,
            "tables": names,
            "internal_fks": internal,
            "stub_out": [s["text"] for s in stubs if s["dir"] == "out"],
            "stub_in": [s["text"] for s in stubs if s["dir"] == "in"],
            "counts": {"tables": len(cards),
                       "columns": sum(len(c["rows"]) for c in cards),
                       "fks_internal": internal,
                       "stubs_in": len([s for s in stubs if s["dir"] == "in"]),
                       "stubs_out": len([s for s in stubs if s["dir"] == "out"])},
        }
        # legacy tag text is already in page texts
        # self-check: no overlapping text bboxes
        for i in range(len(texts)):
            bi = bbox_of(texts[i])
            for j in range(i + 1, len(texts)):
                bj = bbox_of(texts[j])
                ox = min(bi[2], bj[2]) - max(bi[0], bj[0])
                oy = min(bi[3], bj[3]) - max(bi[1], bj[1])
                if ox > 0.5 and oy > 0.5:
                    raise SystemExit("page %d text overlap: %r vs %r (%.1fx%.1f)"
                                     % (pi + 1, texts[i]["content"],
                                        texts[j]["content"], ox, oy))
        name = "trd-%d" % (pi + 1)
        svg_page(page, os.path.join(d, name + ".svg"))
        drawio_page(page, os.path.join(d, name + ".drawio"))
        with open(os.path.join(d, "text-content-p%d.json" % (pi + 1)),
                  "w", encoding="utf-8") as f:
            json.dump(page_text_content(page), f, indent=1)
        pages.append(page)
        print("page %d: %s | cards %d columns %d internalFK %d stubs out %d in %d"
              % (pi + 1, ",".join(names), len(cards),
                 sum(len(c["rows"]) for c in cards), internal,
                 len(page["stub_out"]), len(page["stub_in"])))

    # cross-page FK ledger
    for fk in raw["foreign_keys"]:
        s, dst = fk["source"], fk["destination"]
        if page_of[s] != page_of[dst]:
            cross.append({"source": s, "columns": fk["columns"],
                          "destination": dst,
                          "reference_columns": fk["reference_columns"],
                          "source_page": page_of[s],
                          "target_page": page_of[dst]})
    spec = {
        "canvas": CANVAS,
        "layout": {"columns": 4, "card_width": CARD_W, "header_height": HEADER_H,
                   "row_height": ROW_H, "page_row_heights": PAGE_ROW_H,
                   "top": TOP_Y, "top_stub_band": 160,
                   "note": "deterministic grid, no layout engine; pages are "
                           "consecutive figures in the original card grammar"},
        "counts": {"tables": len(tables), "columns": total_cols,
                   "foreign_keys": total_fks, "migrations": total_mig,
                   "pages": len(pages), "legacy": legacy},
        "pages": [{"page": p["page"], "tables": p["tables"],
                   "counts": p["counts"], "stub_out": p["stub_out"],
                   "stub_in": p["stub_in"],
                   "canvas": p["canvas"], "cards": p["cards"],
                   "texts": p["texts"], "segments": p["segments"],
                   "underlines": p["underlines"], "legend": p["legend"]}
                  for p in pages],
        "cross_page_fks": cross,
        "style": {"font_family": "Arial", "header_fill": "#E8E8E8",
                  "body_fill": "#FFFFFF", "stroke": "#1A1A1A",
                  "row_separator": "#DCDCDC"},
    }
    with open(os.path.join(d, "spec.json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=1)
    with open(os.path.join(d, "text-content.json"), "w", encoding="utf-8") as f:
        json.dump({("p%d" % p["page"]): page_text_content(p) for p in pages},
                  f, indent=1)
    with open(os.path.join(d, "cross-page-fks.json"), "w", encoding="utf-8") as f:
        json.dump(cross, f, indent=1)
    print("cross-page FKs %d (stubs %d both directions)" % (len(cross), 2 * len(cross)))
    print("totals: %d tables, %d columns, %d FKs, %d migrations"
          % (len(tables), total_cols, total_fks, total_mig))


if __name__ == "__main__":
    main()

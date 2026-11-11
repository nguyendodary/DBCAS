# -*- coding: utf-8 -*-
"""Stage B (owner fix round F6): Table Relationship Diagram, 5 pages.

Same card grammar and page split as the accepted Stage B layout, but:
  * no top stub band and no page-edge bus: every cross-page FK is a labelled
    stub inside the owning card row ("to <table> (pN)") with a reciprocal
    stub on the target row ("from <table> (pM)");
  * every same-page FK is one real orthogonal connector: crow's foot at the
    source row edge, one bar at the destination row edge, routed only in the
    free gutters/row gaps between cards;
  * 41 tables / 293 columns / 59 FKs / 19 migrations, legacy cards dashed.

Usage:
  tools/.venv/Scripts/python.exe scripts/build_trd_stage_b_f6.py \
      docs/diagrams/rebuild/trd
"""
import json
import math
import os
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trd_common_f6 import (bbox_of, dedupe_segments, drawio_page, fmt,
                           load_schema, page_text_content, row_heights,
                           row_top, svg_page, text_item)

CANVAS = {"w": 3440, "h": 2080}
COL_X = [40, 890, 1740, 2590]
CARD_W = 795
HEADER_H = 74
ROW_GAP = 60
TOP_Y = 42
BASE_ROW_H = [72, 70, 62, 58, 64]
TITLE_SIZE = 38
NAME_SIZE = 32
MARKER_SIZE = 22
TYPE_SIZE = 24
STUB_SIZE = 24
STUB_LINE = 30
STUB_TOP = 4
STUB_COL_GAP = 18
LEGEND_H = 432
LEGACY = {"assessment", "assessment_concept", "assessment_question",
          "assessment_blueprint"}

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


def adv_w(text, weight="regular", size=STUB_SIZE):
    from trd_common_f6 import _adv
    return _adv(text, weight, size)


def block_layout(texts, start_x, avail):
    """Rows of labels across the card, sorted column-major; minimal height."""
    n = len(texts)
    best = None
    for nc in range(min(n, 5), 0, -1):
        rows = int(math.ceil(n / float(nc)))
        widths = []
        for c in range(nc):
            seg = texts[c * rows:(c + 1) * rows]
            if seg:
                widths.append(max(adv_w(x) for x in seg))
        total = sum(widths) + max(0, len(widths) - 1) * STUB_COL_GAP
        if total <= avail:
            best = {"cols": len(widths), "rows": rows, "widths": widths}
            break
    if best is None:
        best = {"cols": 1, "rows": n,
                "widths": [max(adv_w(x) for x in texts)]}
    return best


def make_stub_layout(col, row, node, base_h):
    x = COL_X[col]
    w = CARD_W
    typ = row["type"] + (" NOT NULL" if not row["nullable"] else " NULL")
    name_w = adv_w(row["name"], "bold" if row["marker"] else "regular",
                   NAME_SIZE)
    marker_w = adv_w(row["marker"], "bold", MARKER_SIZE) if row["marker"] else 0
    type_w = adv_w(typ, "regular", TYPE_SIZE)
    marker_start = x + w - 300 - marker_w if row["marker"] else x + w
    type_start = x + w - 20 - type_w
    inline_limit = min(marker_start, type_start) - 16
    start = x + 20 + name_w + 20
    texts = [z["text"] for z in node]
    widths = [adv_w(t) for t in texts]
    inline_w = sum(widths) + max(0, len(widths) - 1) * STUB_COL_GAP
    if start + inline_w <= inline_limit:
        return {"mode": "inline", "rows": 1, "cols": 1,
                "start_x": start, "widths": [inline_w],
                "height": 0, "name_baseline": base_h / 2.0 + 11,
                "texts": texts}
    lay = block_layout(texts, x + 20, w - 40)
    lay.update({"mode": "block",
                "start_x": x + 20,
                "height": 50 + lay["rows"] * STUB_LINE + 6,
                "name_baseline": 24,
                "texts": texts})
    return lay


def make_cards(tables_by_name, page_rows, base_h, stubs):
    cards = []
    y = TOP_Y
    for rowi, names in enumerate(page_rows):
        row_cards = []
        for col, name in enumerate(names):
            t = tables_by_name[name]
            heights, layouts = [], []
            for ri, row in enumerate(t["columns"]):
                node = stubs.get((name, row["name"]), [])
                if node:
                    lay = make_stub_layout(col, row, node, base_h)
                    heights.append(max(base_h, lay["height"]))
                    layouts.append(lay)
                else:
                    heights.append(base_h)
                    layouts.append(None)
            h = HEADER_H + sum(heights)
            row_cards.append({"title": name, "bbox": [COL_X[col], y, CARD_W, h],
                              "header_h": HEADER_H, "row_h": base_h,
                              "row_heights": heights, "stub_layouts": layouts,
                              "title_size": TITLE_SIZE,
                              "row_size": NAME_SIZE,
                              "rows": t["columns"], "legacy": t["legacy"],
                              "col": col, "grid_row": rowi, "table": name})
        cards.extend(row_cards)
        y += max(c["bbox"][3] for c in row_cards) + ROW_GAP
    return cards


def row_index(card, column):
    for i, r in enumerate(card["rows"]):
        if r["name"] == column:
            return i
    raise SystemExit("column %s not in %s" % (column, card["table"]))


def row_center(card, ri):
    return row_top(card, ri) + row_heights(card)[ri] / 2.0


def card_texts(cards, stubs):
    texts, underlines = [], []
    si = 0
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
            top = row_top(card, ri)
            hh = row_heights(card)[ri]
            lay = card["stub_layouts"][ri]
            if lay and lay["mode"] == "block":
                baseline = top + lay["name_baseline"]
            else:
                baseline = top + hh / 2.0 + 11
            nt = text_item("N%02d_%02d" % (ci + 1, ri + 1), row["name"],
                           x + 20, baseline, NAME_SIZE,
                           "bold" if row["marker"] else "regular", "start")
            texts.append(nt)
            if row["pk"]:
                b = bbox_of(nt)
                underlines.append([b[0], baseline + 6.5, b[2], baseline + 6.5])
            if row["marker"]:
                texts.append(text_item("M%02d_%02d" % (ci + 1, ri + 1),
                                       row["marker"], x + w - 300, baseline,
                                       MARKER_SIZE, "bold", "end"))
            typ = row["type"] + (" NOT NULL" if not row["nullable"] else " NULL")
            texts.append(text_item("Y%02d_%02d" % (ci + 1, ri + 1), typ,
                                   x + w - 20, baseline, TYPE_SIZE,
                                   "regular", "end"))
            node = stubs.get((card["table"], row["name"]), [])
            if node:
                col_x = lay["start_x"]
                if lay["mode"] == "inline":
                    for z in node:
                        si += 1
                        st = text_item("S%03d" % si, z["text"], col_x,
                                       baseline, STUB_SIZE, "regular", "start",
                                       color=z["color"])
                        texts.append(st)
                        z["text_id"] = st["id"]
                        z["stub_mode"] = "inline"
                        z["stub_line"] = 0
                        col_x += adv_w(z["text"]) + STUB_COL_GAP
                else:
                    for c in range(lay["cols"]):
                        seg = node[c * lay["rows"]:(c + 1) * lay["rows"]]
                        for k, z in enumerate(seg):
                            si += 1
                            baseline2 = top + 50 + k * STUB_LINE
                            st = text_item("S%03d" % si, z["text"], col_x,
                                           baseline2, STUB_SIZE, "regular",
                                           "start", color=z["color"])
                            texts.append(st)
                            z["text_id"] = st["id"]
                            z["stub_mode"] = "block"
                            z["stub_line"] = k
                        col_x += lay["widths"][c] + STUB_COL_GAP
    return texts, underlines


def gutter_x(g, edge, side, off):
    return edge + off if side == "R" else edge - off


def gutter_for(col, side):
    return col if side == "R" else col - 1


def add_path(segments, pts):
    for a, b in zip(pts, pts[1:]):
        if abs(a[0] - b[0]) < 0.01 and abs(a[1] - b[1]) < 0.01:
            continue
        segments.append([a[0], a[1], b[0], b[1]])


def build_connectors(page, cards, raw, page_of, fk_list):
    by_table = {c["table"]: c for c in cards}
    nrows = max(c["grid_row"] for c in cards) + 1
    row_bottom = {r: max(c["bbox"][1] + c["bbox"][3]
                         for c in cards if c["grid_row"] == r)
                  for r in range(nrows)}
    row_starts = {0: TOP_Y}
    for r in range(1, nrows):
        row_starts[r] = row_bottom[r - 1] + ROW_GAP
    gap_mid = {r: row_bottom[r] + ROW_GAP / 2.0 for r in range(nrows - 1)}
    # destination fan: distribute several same-page FKs referencing one column
    dest_groups = OrderedDict()
    for fk in fk_list:
        key = (fk["destination"], fk["reference_columns"][0])
        dest_groups.setdefault(key, []).append(fk)
    dpos = {}
    for key in sorted(dest_groups):
        fks = sorted(dest_groups[key], key=lambda z: z["constraint"])
        card = by_table[key[0]]
        ri = row_index(card, key[1])
        top = row_top(card, ri)
        hh = row_heights(card)[ri]
        n = len(fks)
        if n == 1:
            ys = [top + hh / 2.0]
        else:
            lo, hi = top + 20, top + hh - 20
            if hi <= lo:
                lo, hi = top + 8, top + hh - 8
            ys = [lo + i * (hi - lo) / (n - 1.0) for i in range(n)]
        for fk, yv in zip(fks, ys):
            dpos[fk["constraint"]] = yv

    specs = []
    for fk in fk_list:
        s, dst = fk["source"], fk["destination"]
        src, dcard = by_table[s], by_table[dst]
        sri = row_index(src, fk["columns"][0])
        dri = row_index(dcard, fk["reference_columns"][0])
        ys = row_center(src, sri)
        yd = dpos[fk["constraint"]]
        if fk["columns"][0] == fk["reference_columns"][0] and s == dst:
            yd = row_center(dcard, dri)
        same_col = src["col"] == dcard["col"]
        if same_col:
            side = "L" if src["col"] == 0 else "R"
            side_s = side_d = side
            s_edge = src["bbox"][0] if side == "L" else \
                src["bbox"][0] + src["bbox"][2]
            d_edge = dcard["bbox"][0] if side == "L" else \
                dcard["bbox"][0] + dcard["bbox"][2]
            if src["grid_row"] == dcard["grid_row"]:
                g = src["grid_row"] if src["grid_row"] < nrows - 1 \
                    else src["grid_row"] - 1
            elif src["grid_row"] < dcard["grid_row"]:
                g = dcard["grid_row"] - 1
            else:
                g = dcard["grid_row"]
            s_gut = gutter_for(src["col"], side)
            d_gut = gutter_for(dcard["col"], side)
        else:
            if dcard["bbox"][0] > src["bbox"][0]:
                side_s, side_d = "R", "L"
            else:
                side_s, side_d = "L", "R"
            s_edge = src["bbox"][0] + src["bbox"][2] if side_s == "R" else \
                src["bbox"][0]
            d_edge = dcard["bbox"][0] if side_d == "L" else \
                dcard["bbox"][0] + dcard["bbox"][2]
            if src["grid_row"] == dcard["grid_row"]:
                g = src["grid_row"] if src["grid_row"] < nrows - 1 \
                    else src["grid_row"] - 1
            elif src["grid_row"] < dcard["grid_row"]:
                g = dcard["grid_row"] - 1
            else:
                g = dcard["grid_row"]
            s_gut = gutter_for(src["col"], side_s)
            d_gut = gutter_for(dcard["col"], side_d)
        specs.append({"fk": fk, "src": src, "dst": dcard, "ys": ys, "yd": yd,
                      "s_edge": s_edge, "d_edge": d_edge,
                      "side_s": side_s, "side_d": side_d,
                      "s_gut": s_gut, "d_gut": d_gut, "gap": g})

    # assign lanes per physical gutter / row gap
    v_off = [12, 17, 22, 27, 32, 37, 42, 47, 52]
    h_off = [-21, -15, -9, -3, 3, 9, 15, 21, -24, 24]
    vcount, hcount = {}, {}
    for sp in specs:
        for k, gut in (("s", sp["s_gut"]), ("d", sp["d_gut"])):
            idx = vcount.get(gut, 0)
            off = v_off[idx % len(v_off)]
            if gut == -1:
                off = min(off, 34)
            sp[k + "_lane"] = gutter_x(gut, sp["s_edge"] if k == "s"
                                       else sp["d_edge"],
                                       sp["side_s"] if k == "s"
                                       else sp["side_d"], off)
            vcount[gut] = idx + 1
        idx = hcount.get(sp["gap"], 0)
        sp["gy"] = gap_mid[sp["gap"]] + h_off[idx % len(h_off)]
        hcount[sp["gap"]] = idx + 1

    connectors = []
    segments = []
    for sp in specs:
        fk = sp["fk"]
        sx, ys = sp["s_edge"], sp["ys"]
        dx, yd = sp["d_edge"], sp["yd"]
        xsl, xdl, gy = sp["s_lane"], sp["d_lane"], sp["gy"]
        apex = (xsl, ys)
        prongs = [[sx, ys - 14, xsl, ys], [sx, ys, xsl, ys],
                  [sx, ys + 14, xsl, ys]]
        path = [[xsl, ys], [xsl, gy], [xdl, gy], [xdl, yd], [dx, yd]]
        segs = list(prongs)
        add_path(segs, path)
        sign = 1 if sp["side_d"] == "R" else -1
        bx = dx + sign * 10
        bar = [bx, yd - 10, bx, yd + 10]
        segs.append(bar)
        segments.extend(segs)
        connectors.append({
            "fk": fk["constraint"], "source": fk["source"],
            "columns": fk["columns"], "destination": fk["destination"],
            "reference_columns": fk["reference_columns"],
            "source_page": page["page"], "target_page": page_of[fk["destination"]],
            "src_anchor": [sx, ys], "dst_anchor": [dx, yd],
            "apex": [xsl, ys], "bar": bar,
            "src_side": sp["side_s"], "dst_side": sp["side_d"],
            "segments": segs,
        })
    return connectors, segments


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

    # cross-page stub requirements
    stubs_by_row = OrderedDict()
    cross_meta = OrderedDict()
    for fk in raw["foreign_keys"]:
        s, dst = fk["source"], fk["destination"]
        if page_of[s] == page_of[dst]:
            continue
        out = {"text": "to %s (p%d)" % (dst, page_of[dst]),
               "color": "#1F3A93", "dir": "out", "fk": fk["constraint"],
               "table": s, "column": fk["columns"][0],
               "other": dst, "other_page": page_of[dst], "page": page_of[s]}
        inc = {"text": "from %s (p%d)" % (s, page_of[s]),
               "color": "#0B6B3A", "dir": "in", "fk": fk["constraint"],
               "table": dst, "column": fk["reference_columns"][0],
               "other": s, "other_page": page_of[s], "page": page_of[dst]}
        stubs_by_row.setdefault((s, fk["columns"][0]), []).append(out)
        stubs_by_row.setdefault((dst, fk["reference_columns"][0]), []).append(inc)
        cross_meta[fk["constraint"]] = {
            "source": s, "columns": fk["columns"], "destination": dst,
            "reference_columns": fk["reference_columns"],
            "source_page": page_of[s], "target_page": page_of[dst]}

    pages = []
    for pi, names in enumerate(PAGES):
        cards = make_cards(by_name, PAGE_ROWS[pi], BASE_ROW_H[pi],
                           stubs_by_row)
        by_table = {c["table"]: c for c in cards}
        texts, underlines = card_texts(cards, stubs_by_row)
        fks_here = [fk for fk in raw["foreign_keys"]
                    if page_of[fk["source"]] == pi + 1 and
                    page_of[fk["destination"]] == pi + 1]
        page = {"name": "Table Relationship Diagram (%d/%d)"
                        % (pi + 1, len(PAGES)),
                "canvas": CANVAS, "cards": cards, "texts": texts,
                "underlines": underlines, "page": pi + 1, "tables": names}

        connectors, segments = build_connectors(page, cards, raw, page_of,
                                                fks_here)
        page["connectors"] = connectors
        page["segments"] = dedupe_segments(segments)

        # stub ledger: attach actual bbox/row after card placement
        stub_list = []
        for key, node in stubs_by_row.items():
            tname, col = key
            if tname not in by_table:
                continue
            card = by_table[tname]
            ri = row_index(card, col)
            top = row_top(card, ri)
            for z in node:
                if z["page"] != pi + 1:
                    continue
                tid = z["text_id"]
                txt = next(t for t in texts if t["id"] == tid)
                stub_list.append({"fk": z["fk"], "dir": z["dir"],
                                  "table": tname, "column": col,
                                  "text": z["text"], "color": z["color"],
                                  "mode": z.get("stub_mode"),
                                  "line": z.get("stub_line", 0),
                                  "row": ri, "row_top": top,
                                  "row_bottom": top + row_heights(card)[ri],
                                  "bbox": list(bbox_of(txt)),
                                  "text_id": tid,
                                  "other": z["other"],
                                  "other_page": z["other_page"],
                                  "page": pi + 1})
        page["stubs"] = stub_list

        # legend, in the empty 4th column of the bottom grid row
        legend_y = max(c["bbox"][1] for c in cards)
        lx = COL_X[3]
        legend_bbox = [lx, legend_y, CARD_W, LEGEND_H]
        legend_texts = [
            text_item("LGT", "Legend", lx + 24, legend_y + 44, 30, "bold", "start"),
            text_item("LG1", "name", lx + 24, legend_y + 88, 26, "bold", "start"),
            text_item("LG2", "= primary key", lx + 110, legend_y + 88, 26, "regular", "start"),
            text_item("LG3", "[FK] = foreign key", lx + 24, legend_y + 128, 22, "regular", "start"),
            text_item("LG4", "= one", lx + 170, legend_y + 166, 26, "regular", "start"),
            text_item("LG5", "= many", lx + 230, legend_y + 206, 26, "regular", "start"),
            text_item("LG6", "LEGACY (dashed card) = legacy table, historical rows only",
                      lx + 24, legend_y + 250, 22, "regular", "start"),
            text_item("LG7", "%d tables · %d columns · %d FKs · %d migrations"
                      % (len(tables), total_cols, total_fks, total_mig),
                      lx + 24, legend_y + 306, 24, "bold", "start"),
            text_item("LG8", 'Cross-page FK: "to table (pN)" on source row; '
                      '"from table (pM)" on target row',
                      lx + 24, legend_y + 348, 19, "regular", "start"),
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
        nb = bbox_of(legend_texts[1])
        legend_segments.insert(0, [nb[0], legend_y + 96, nb[2], legend_y + 96])
        page["legend"] = {"bbox": legend_bbox, "texts": [],
                          "segments": legend_segments}

        # no text outside the canvas / no overlap (checker repeats this)
        for i in range(len(texts)):
            bi = bbox_of(texts[i])
            if bi[1] < 0 or bi[3] > CANVAS["h"] or bi[0] < 0 or bi[2] > CANVAS["w"]:
                raise SystemExit("page %d text outside canvas: %r %s"
                                 % (pi + 1, texts[i]["content"], bi))
            for j in range(i + 1, len(texts)):
                bj = bbox_of(texts[j])
                ox = min(bi[2], bj[2]) - max(bi[0], bj[0])
                oy = min(bi[3], bj[3]) - max(bi[1], bj[1])
                if ox > 0.5 and oy > 0.5:
                    raise SystemExit("page %d text overlap: %r vs %r (%.1fx%.1f)"
                                     % (pi + 1, texts[i]["content"],
                                        texts[j]["content"], ox, oy))
        if legend_y + LEGEND_H > CANVAS["h"] - 20:
            raise SystemExit("page %d legend overflows: %d"
                             % (pi + 1, legend_y + LEGEND_H))

        page["counts"] = {
            "tables": len(cards),
            "columns": sum(len(c["rows"]) for c in cards),
            "fks_internal": len(connectors),
            "fks_cross": len([s for s in page["stubs"] if s["dir"] == "out"]),
            "stubs_in": len([s for s in page["stubs"] if s["dir"] == "in"]),
            "stubs_out": len([s for s in page["stubs"] if s["dir"] == "out"]),
        }
        name = "trd-%d" % (pi + 1)
        svg_page(page, os.path.join(d, name + ".svg"))
        drawio_page(page, os.path.join(d, name + ".drawio"))
        with open(os.path.join(d, "text-content-p%d.json" % (pi + 1)),
                  "w", encoding="utf-8") as f:
            json.dump(page_text_content(page), f, indent=1)
        pages.append(page)
        print("page %d: %s | cards %d columns %d same-page FKs %d "
              "stubs out %d in %d | bottom %d legend %d..%d"
              % (pi + 1, ",".join(names), len(cards),
                 sum(len(c["rows"]) for c in cards), len(connectors),
                 page["counts"]["stubs_out"], page["counts"]["stubs_in"],
                 max(c["bbox"][1] + c["bbox"][3] for c in cards),
                 legend_y, legend_y + LEGEND_H))

    # cross-page FK ledger
    cross = []
    for fk in raw["foreign_keys"]:
        s, dst = fk["source"], fk["destination"]
        if page_of[s] != page_of[dst]:
            cross.append({"constraint": fk["constraint"], "source": s,
                          "columns": fk["columns"], "destination": dst,
                          "reference_columns": fk["reference_columns"],
                          "source_page": page_of[s],
                          "target_page": page_of[dst]})
    spec = {
        "canvas": CANVAS,
        "layout": {"columns": 4, "card_width": CARD_W, "header_height": HEADER_H,
                   "base_row_heights": BASE_ROW_H, "row_gap": ROW_GAP,
                   "top": TOP_Y, "top_stub_band": 0,
                   "stub_size": STUB_SIZE,
                   "note": "deterministic grid, no layout engine; cross-page "
                           "FKs are labelled stubs inside the owning rows"},
        "counts": {"tables": len(tables), "columns": total_cols,
                   "foreign_keys": total_fks, "migrations": total_mig,
                   "pages": len(pages), "legacy": legacy,
                   "same_page_connectors": sum(len(p["connectors"]) for p in pages),
                   "cross_page_fks": len(cross),
                   "stubs": sum(len(p["stubs"]) for p in pages)},
        "pages": [{"page": p["page"], "tables": p["tables"],
                   "counts": p["counts"], "canvas": p["canvas"],
                   "cards": p["cards"], "texts": p["texts"],
                   "segments": p["segments"], "underlines": p["underlines"],
                   "legend": p["legend"], "connectors": p["connectors"],
                   "stubs": p["stubs"]} for p in pages],
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
    print("cross-page FKs %d (stubs %d)" % (len(cross), 2 * len(cross)))
    print("totals: %d tables, %d columns, %d FKs, %d migrations"
          % (len(tables), total_cols, total_fks, total_mig))


if __name__ == "__main__":
    main()

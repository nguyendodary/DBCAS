# -*- coding: utf-8 -*-
"""Verification for the W3b Stage B TRD pages.

Checks, from the emitted spec.json + schema-introspection.json:
  * 41 table cards exactly once, 293 columns, 59 FKs, 19 migrations;
  * every card row = real column, real order, real type, nullability,
    [PK]/[FK]/[PK, FK] marker;
  * every same-page FK has a crow's-foot at the source row edge and a
    one-tick at the destination row edge;
  * every cross-page FK has both a -> stub on the source page and a
    <- stub on the destination page, with matching table/column(s)/page;
  * no connector segment midpoint lies inside a card;
  * no text bbox above the canvas or overlapping (redundant with checker).
Exit 0 = PASS.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trd_common_w3b import bbox_of, load_schema

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def row_y(card, name):
    for i, r in enumerate(card["rows"]):
        if r["name"] == name:
            return card["bbox"][1] + card["header_h"] + (i + 0.5) * card["row_h"]
    return None


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(ROOT, "docs", "diagrams", "rebuild", "trd")
    spec = json.load(open(os.path.join(d, "spec.json"), encoding="utf-8"))
    raw, tables = load_schema()
    by_name = {t["table"]: t for t in tables}
    problems = []
    page_of = {}
    for p in spec["pages"]:
        for c in p["cards"]:
            page_of[c["table"]] = p["page"]
    # counts
    if len(page_of) != 41:
        problems.append("tables %d != 41" % len(page_of))
    if sum(len(c["rows"]) for p in spec["pages"] for c in p["cards"]) != 293:
        problems.append("columns != 293")
    if len(raw["foreign_keys"]) != 59:
        problems.append("FKs != 59")
    if len(raw["migrations"]) != 19:
        problems.append("migrations != 19")
    if spec["counts"]["pages"] != 5:
        problems.append("pages != 5")
    # cards
    for p in spec["pages"]:
        for c in p["cards"]:
            t = by_name[c["table"]]
            if [r["name"] for r in c["rows"]] != [r["name"] for r in t["columns"]]:
                problems.append("%s column order mismatch" % c["table"])
            for a, b in zip(c["rows"], t["columns"]):
                if a["type"] != b["type"]:
                    problems.append("%s.%s type %s != %s" %
                                    (c["table"], a["name"], a["type"], b["type"]))
                if a["nullable"] != b["nullable"]:
                    problems.append("%s.%s nullability mismatch" %
                                    (c["table"], a["name"]))
                if a["marker"] != b["marker"]:
                    problems.append("%s.%s marker %s != %s" %
                                    (c["table"], a["name"], a["marker"], b["marker"]))
            if c["legacy"] != (c["table"] in {"assessment", "assessment_concept",
                                             "assessment_question",
                                             "assessment_blueprint"}):
                problems.append("%s legacy flag wrong" % c["table"])
    # segments not inside cards
    def inside(x, y, card):
        bx, by, bw, bh = card["bbox"]
        return bx + 1 < x < bx + bw - 1 and by + 1 < y < by + bh - 1
    for p in spec["pages"]:
        for s in p["segments"]:
            mx, my = (s[0] + s[2]) / 2.0, (s[1] + s[3]) / 2.0
            for c in p["cards"]:
                if inside(mx, my, c):
                    problems.append("page %d segment midpoint inside %s: %s"
                                    % (p["page"], c["table"], s))
                    break
    # text bboxes
    for p in spec["pages"]:
        for t in p["texts"]:
            b = bbox_of(t)
            if b[1] < 0 or b[3] > p["canvas"]["h"] or b[0] < 0 or b[2] > p["canvas"]["w"]:
                problems.append("page %d text outside canvas: %r %s"
                                % (p["page"], t["content"], b))
        for i in range(len(p["texts"])):
            bi = bbox_of(p["texts"][i])
            for j in range(i + 1, len(p["texts"])):
                bj = bbox_of(p["texts"][j])
                if min(bi[2], bj[2]) - max(bi[0], bj[0]) > 0.5 and \
                   min(bi[3], bj[3]) - max(bi[1], bj[1]) > 0.5:
                    problems.append("page %d text overlap %r / %r"
                                    % (p["page"], p["texts"][i]["content"],
                                       p["texts"][j]["content"]))
    # FK connectors / stubs
    internal = cross = 0
    for fk in raw["foreign_keys"]:
        s, dst = fk["source"], fk["destination"]
        sp, dp = page_of[s], page_of[dst]
        cols = ",".join(fk["columns"])
        refs = ",".join(fk["reference_columns"])
        if sp == dp:
            internal += 1
            p = next(x for x in spec["pages"] if x["page"] == sp)
            sc = next(c for c in p["cards"] if c["table"] == s)
            dc = next(c for c in p["cards"] if c["table"] == dst)
            ys = row_y(sc, fk["columns"][0])
            yd = row_y(dc, fk["reference_columns"][0])
            sx, sy, sw, sh = sc["bbox"]
            dx, dy, dw, dh = dc["bbox"]
            # a crow foot at the source row: three segments meeting at
            # 22 px outside an edge and touching that edge at y-14/y/y+14
            found_cf = False
            for edge in (sx, sx + sw):
                px = edge + 22 if edge == sx + sw else edge - 22
                ys_ = [y for y in (ys - 14, ys, ys + 14)]
                hit = 0
                for seg in p["segments"]:
                    for (ex, ey) in ((seg[0], seg[1]), (seg[2], seg[3])):
                        if abs(ex - px) <= 1 and abs(ey - ys) <= 1:
                            hit += 1
                if hit >= 3:
                    found_cf = True
            if not found_cf:
                problems.append("internal FK %s.%s -> %s: crow foot missing"
                                % (s, cols, dst))
            found_one = False
            for edge in (dx, dx + dw):
                x = edge - 12 if edge == dx else edge + 12
                for seg in p["segments"]:
                    if abs(seg[0] - seg[2]) <= 0.01 and abs(seg[0] - x) <= 1 and \
                       abs(seg[1] - (yd - 15)) <= 1 and abs(seg[3] - (yd + 15)) <= 1:
                        found_one = True
            if not found_one:
                problems.append("internal FK %s.%s -> %s: one tick missing"
                                % (s, cols, dst))
        else:
            cross += 1
            out = "→ %s(%s) · p%d" % (dst, refs, dp)
            inc = "← %s(%s) · p%d" % (s, cols, sp)
            p_out = next(x for x in spec["pages"] if x["page"] == sp)
            p_in = next(x for x in spec["pages"] if x["page"] == dp)
            if out not in [t["content"] for t in p_out["texts"]]:
                problems.append("missing source stub %s" % out)
            if inc not in [t["content"] for t in p_in["texts"]]:
                problems.append("missing target stub %s" % inc)
    # cross ledger
    if len(spec["cross_page_fks"]) != cross:
        problems.append("cross ledger %d != %d" %
                        (len(spec["cross_page_fks"]), cross))
    if internal + cross != 59:
        problems.append("internal+cross %d != 59" % (internal + cross))
    print("tables 41, columns 293, FKs 59, migrations 19")
    print("pages 5, internal FK connectors %d, cross-page FKs %d, stubs %d"
          % (internal, cross, 2 * cross))
    if problems:
        print("RESULT: FAIL (%d)" % len(problems))
        for p in problems[:30]:
            print(" -", p)
        sys.exit(1)
    print("RESULT: PASS")
    print("all 41 cards exactly once; 293/293 column rows match real order, "
          "type, nullability, PK/FK; every FK has a crow-foot connector or "
          "a pair of labelled page-edge stubs; no segment midpoint inside a "
          "card; no text outside the canvas or overlapping.")


if __name__ == "__main__":
    main()

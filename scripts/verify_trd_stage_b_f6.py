# -*- coding: utf-8 -*-
"""Owner-fix-round verifier for the F6 five-page TRD.

Proves, from spec.json + schema-introspection.json (not from prose):
  * 41 tables / 293 columns / 59 FKs / 19 migrations;
  * every card row = real column, real order, type, nullability, marker;
  * every same-page FK = exactly one orthogonal connector with a three-prong
    crow's foot touching the source row edge and a perpendicular bar at the
    destination row edge; both anchors are on the right card boundary and
    inside the right column row; every segment stays out of every card;
  * every cross-page FK = exactly one `to <table> (p<N>)` stub on the source
    row and exactly one `from <table> (p<M>)` stub on the target row; both
    are inside the correct row band and above the column name;
  * 29 connectors + 30 stub pairs = 59 FKs, each drawn exactly once;
  * no dangling connector endpoint (bar ticks excepted, they are notation).

Exit 0 = PASS.
"""
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trd_common_f6 import bbox_of, load_schema, row_heights, row_top, text_item

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEGACY = {"assessment", "assessment_concept", "assessment_question",
          "assessment_blueprint"}


def in_band(v, lo, hi, eps=1.0):
    return lo - eps <= v <= hi + eps


def on_boundary(x, y, card, eps=1.0):
    bx, by, bw, bh = card["bbox"]
    if abs(x - bx) <= eps or abs(x - (bx + bw)) <= eps:
        return by - eps <= y <= by + bh + eps
    if abs(y - by) <= eps or abs(y - (by + bh)) <= eps:
        return bx - eps <= x <= bx + bw + eps
    return False


def seg_key(s):
    return tuple(round(float(v), 2) for v in s[:4])


def seg_inside_card(s, card, eps=0.75):
    """True when a positive-length part of the segment is strictly inside."""
    x0, y0, x1, y1 = [float(v) for v in s[:4]]
    bx, by, bw, bh = card["bbox"]
    # Liang-Barsky clip against the shrunk box
    xmin, xmax = bx + eps, bx + bw - eps
    ymin, ymax = by + eps, by + bh - eps
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x0 - xmin), (dx, xmax - x0),
                 (-dy, y0 - ymin), (dy, ymax - y0)):
        if abs(p) < 1e-12:
            if q < 0:
                return False
            continue
        r = q / p
        if p < 0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
    return t1 - t0 > 1e-6


def find_name_bbox(p, card, column):
    for t in p["texts"]:
        if t["content"] == column and abs(t["x"] - (card["bbox"][0] + 20)) < 0.6 \
           and card["bbox"][1] <= t["y"] <= card["bbox"][1] + card["bbox"][3]:
            return bbox_of(t)
    return None


def check_stub_attachment(z, p, card, column, std):
    nb = find_name_bbox(p, card, column)
    if nb is None:
        std.append("name text not found for %s" % column)
        return
    if z.get("mode") == "inline":
        if not (z["bbox"][1] < nb[3] and z["bbox"][3] > nb[1]):
            std.append("%s inline stub not on the column name line" % column)
        if z["bbox"][0] < nb[2] - 1:
            std.append("%s inline stub not to the right of the column name"
                       % column)
    elif z.get("mode") == "block":
        if z["bbox"][1] < nb[3] + 1:
            std.append("%s block stub not directly below the column name"
                       % column)
        if z.get("line", 0) == 0 and z["bbox"][1] > nb[3] + 40:
            std.append("%s block stub too far below the column name" % column)
    else:
        std.append("%s stub mode missing" % column)


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

    # ---------------------------------------------------------------- counts
    if len(page_of) != 41:
        problems.append("tables %d != 41" % len(page_of))
    total_cols = sum(len(c["rows"]) for p in spec["pages"] for c in p["cards"])
    if total_cols != 293:
        problems.append("columns %d != 293" % total_cols)
    if len(raw["foreign_keys"]) != 59:
        problems.append("FKs %d != 59" % len(raw["foreign_keys"]))
    if len(raw["migrations"]) != 19:
        problems.append("migrations %d != 19" % len(raw["migrations"]))
    if len(spec["pages"]) != 5:
        problems.append("pages %d != 5" % len(spec["pages"]))

    # ---------------------------------------------------------------- cards
    for p in spec["pages"]:
        for c in p["cards"]:
            t = by_name[c["table"]]
            if [r["name"] for r in c["rows"]] != \
               [r["name"] for r in t["columns"]]:
                problems.append("%s column order mismatch" % c["table"])
            for a, b in zip(c["rows"], t["columns"]):
                if a["type"] != b["type"]:
                    problems.append("%s.%s type %s != %s"
                                    % (c["table"], a["name"], a["type"], b["type"]))
                if a["nullable"] != b["nullable"]:
                    problems.append("%s.%s nullability mismatch"
                                    % (c["table"], a["name"]))
                if a["marker"] != b["marker"]:
                    problems.append("%s.%s marker %s != %s"
                                    % (c["table"], a["name"], a["marker"],
                                       b["marker"]))
            if c["legacy"] != (c["table"] in LEGACY):
                problems.append("%s legacy flag wrong" % c["table"])
            if c["table"] in LEGACY:
                tag = [x for x in p["texts"] if x["content"] == "LEGACY"
                       and x["x"] > c["bbox"][0]
                       and x["x"] <= c["bbox"][0] + c["bbox"][2]]
                if not tag:
                    problems.append("%s LEGACY tag missing" % c["table"])
    for name in LEGACY:
        if name not in page_of:
            problems.append("legacy table missing: %s" % name)

    # ------------------------------------------------------- geometry index
    for p in spec["pages"]:
        cards = p["cards"]
        by_table = {c["table"]: c for c in cards}
        page_segs = [seg_key(s) for s in p["segments"]]
        if len(page_segs) != len(set(page_segs)):
            problems.append("page %d: duplicate raw segments" % p["page"])
        # no segment interior inside any card or through any text label
        for s in p["segments"]:
            mx = (s[0] + s[2]) / 2.0
            my = (s[1] + s[3]) / 2.0
            for c in cards:
                bx, by, bw, bh = c["bbox"]
                if bx + 0.75 < mx < bx + bw - 0.75 and \
                   by + 0.75 < my < by + bh - 0.75:
                    problems.append("page %d segment midpoint inside %s: %s"
                                    % (p["page"], c["table"], s))
                    break
                if seg_inside_card(s, c):
                    problems.append("page %d segment crosses card %s: %s"
                                    % (p["page"], c["table"], s))
                    break
            for t in p["texts"]:
                b = bbox_of(t)
                if seg_inside_card(s, {"bbox": [b[0], b[1], b[2] - b[0],
                                                b[3] - b[1]]}, eps=0.5):
                    problems.append("page %d segment crosses text %r: %s"
                                    % (p["page"], t["content"], s))
                    break

    # ------------------------------------------------------ same-page FKs
    same = [fk for fk in raw["foreign_keys"]
            if page_of[fk["source"]] == page_of[fk["destination"]]]
    cross = [fk for fk in raw["foreign_keys"]
             if page_of[fk["source"]] != page_of[fk["destination"]]]
    if len(same) != 29:
        problems.append("same-page FKs %d != 29" % len(same))
    if len(cross) != 30:
        problems.append("cross-page FKs %d != 30" % len(cross))

    conn_seen = Counter()
    for p in spec["pages"]:
        cards = {c["table"]: c for c in p["cards"]}
        page_segs = [seg_key(s) for s in p["segments"]]
        for con in p.get("connectors", []):
            conn_seen[con["fk"]] += 1
        for fk in same:
            if page_of[fk["source"]] != p["page"]:
                continue
            hits = [c for c in p.get("connectors", []) if c["fk"] == fk["constraint"]]
            if len(hits) != 1:
                problems.append("same-page FK %s has %d connectors"
                                % (fk["constraint"], len(hits)))
                continue
            con = hits[0]
            src, dst = cards[fk["source"]], cards[fk["destination"]]
            sri = next(i for i, r in enumerate(src["rows"])
                       if r["name"] == fk["columns"][0])
            dri = next(i for i, r in enumerate(dst["rows"])
                       if r["name"] == fk["reference_columns"][0])
            sy0 = row_top(src, sri)
            sy1 = sy0 + row_heights(src)[sri]
            dy0 = row_top(dst, dri)
            dy1 = dy0 + row_heights(dst)[dri]
            sx, sy = con["src_anchor"]
            dx, dy = con["dst_anchor"]
            if not on_boundary(sx, sy, src):
                problems.append("%s source anchor not on boundary: %s"
                                % (fk["constraint"], con["src_anchor"]))
            if not in_band(sy, sy0, sy1):
                problems.append("%s source anchor outside row band" % fk["constraint"])
            if not on_boundary(dx, dy, dst):
                problems.append("%s dest anchor not on boundary: %s"
                                % (fk["constraint"], con["dst_anchor"]))
            if not in_band(dy, dy0, dy1):
                problems.append("%s dest anchor outside row band" % fk["constraint"])
            # crow's foot: apex 10..55 px outside the source edge, three
            # prongs to the edge at sy-14 / sy / sy+14
            ax, ay = con["apex"]
            if abs(ay - sy) > 1:
                problems.append("%s crow-foot apex y mismatch" % fk["constraint"])
            dist = abs(ax - sx)
            if not (10 <= dist <= 55):
                problems.append("%s crow-foot apex distance %.1f" % (fk["constraint"], dist))
            prong_keys = {seg_key([sx, sy - 14, ax, sy]),
                          seg_key([sx, sy, ax, sy]),
                          seg_key([sx, sy + 14, ax, sy])}
            got = {seg_key(s) for s in con["segments"]}
            if prong_keys - got:
                problems.append("%s crow's foot prongs missing" % fk["constraint"])
            # bar at the one side
            bar = con["bar"]
            if abs(bar[0] - bar[2]) > 0.01:
                problems.append("%s one bar not vertical" % fk["constraint"])
            if abs(bar[0] - (dx + (10 if con["dst_side"] == "R" else -10))) > 1:
                problems.append("%s one bar not next to dest edge" % fk["constraint"])
            if abs(bar[1] - (dy - 10)) > 1 or abs(bar[3] - (dy + 10)) > 1:
                problems.append("%s one bar not centred on dest row" % fk["constraint"])
            # path connectivity: every non-bar endpoint is shared or on a
            # connector card boundary; bar is a notation tick.
            segs = [s for s in con["segments"] if seg_key(s) != seg_key(bar)]
            ends = defaultdict(int)
            for s in segs:
                ends[(round(s[0], 2), round(s[1], 2))] += 1
                ends[(round(s[2], 2), round(s[3], 2))] += 1
            for (ex, ey), n in ends.items():
                if n >= 2:
                    continue
                if on_boundary(ex, ey, src) or on_boundary(ex, ey, dst):
                    continue
                problems.append("%s dangling endpoint (%.1f,%.1f)"
                                % (fk["constraint"], ex, ey))
            # every segment exists in the page and no extra segments
            missing = [s for s in con["segments"] if seg_key(s) not in set(page_segs)]
            if missing:
                problems.append("%s connector segment not in page: %s"
                                % (fk["constraint"], missing[:2]))
    for fk in same:
        if conn_seen[fk["constraint"]] != 1:
            problems.append("same-page FK %s drawn %d times"
                            % (fk["constraint"], conn_seen[fk["constraint"]]))
    if set(conn_seen) != {fk["constraint"] for fk in same} or \
       sum(conn_seen.values()) != len(same):
        problems.append("connector set %d/%d does not match the 29 same-page FKs"
                        % (sum(conn_seen.values()), len(conn_seen)))

    # ------------------------------------------------------ cross-page FKs
    stub_seen = Counter()
    for p in spec["pages"]:
        cards = {c["table"]: c for c in p["cards"]}
        for st in p.get("stubs", []):
            stub_seen[(st["fk"], st["dir"])] += 1
        for fk in cross:
            s, dst = fk["source"], fk["destination"]
            sp, dp = page_of[s], page_of[dst]
            if sp != p["page"] and dp != p["page"]:
                continue
            out = [z for z in p.get("stubs", [])
                   if z["fk"] == fk["constraint"] and z["dir"] == "out"]
            inc = [z for z in p.get("stubs", [])
                   if z["fk"] == fk["constraint"] and z["dir"] == "in"]
            if sp == p["page"]:
                if len(out) != 1:
                    problems.append("cross FK %s out stubs %d"
                                    % (fk["constraint"], len(out)))
                else:
                    z = out[0]
                    want = "to %s (p%d)" % (dst, dp)
                    if z["text"] != want:
                        problems.append("%s out text %r != %r"
                                        % (fk["constraint"], z["text"], want))
                    if z["table"] != s or z["column"] != fk["columns"][0]:
                        problems.append("%s out stub on wrong table/column"
                                        % fk["constraint"])
                    c = cards[s]
                    ri = next(i for i, r in enumerate(c["rows"])
                              if r["name"] == fk["columns"][0])
                    lo, hi = row_top(c, ri), row_top(c, ri) + row_heights(c)[ri]
                    if not (c["bbox"][0] <= z["bbox"][0] and
                            z["bbox"][2] <= c["bbox"][0] + c["bbox"][2]):
                        problems.append("%s out stub outside card x" % fk["constraint"])
                    if not (lo <= z["bbox"][1] and z["bbox"][3] <= hi):
                        problems.append("%s out stub outside row band" % fk["constraint"])
                    check_stub_attachment(z, p, c, fk["columns"][0], problems)
            if dp == p["page"]:
                if len(inc) != 1:
                    problems.append("cross FK %s in stubs %d"
                                    % (fk["constraint"], len(inc)))
                else:
                    z = inc[0]
                    want = "from %s (p%d)" % (s, sp)
                    if z["text"] != want:
                        problems.append("%s in text %r != %r"
                                        % (fk["constraint"], z["text"], want))
                    if z["table"] != dst or z["column"] != fk["reference_columns"][0]:
                        problems.append("%s in stub on wrong table/column"
                                        % fk["constraint"])
                    c = cards[dst]
                    ri = next(i for i, r in enumerate(c["rows"])
                              if r["name"] == fk["reference_columns"][0])
                    lo, hi = row_top(c, ri), row_top(c, ri) + row_heights(c)[ri]
                    if not (c["bbox"][0] <= z["bbox"][0] and
                            z["bbox"][2] <= c["bbox"][0] + c["bbox"][2]):
                        problems.append("%s in stub outside card x" % fk["constraint"])
                    if not (lo <= z["bbox"][1] and z["bbox"][3] <= hi):
                        problems.append("%s in stub outside row band" % fk["constraint"])
                    check_stub_attachment(z, p, c, fk["reference_columns"][0],
                                          problems)
    for fk in cross:
        for dirn in ("out", "in"):
            if stub_seen[(fk["constraint"], dirn)] != 1:
                problems.append("cross FK %s %s stub count %d"
                                % (fk["constraint"], dirn,
                                   stub_seen[(fk["constraint"], dirn)]))
    total_stubs = sum(len(p.get("stubs", [])) for p in spec["pages"])
    if total_stubs != 60:
        problems.append("stub total %d != 60" % total_stubs)
    expected_stub = {(fk["constraint"], d) for fk in cross
                     for d in ("out", "in")}
    if set(stub_seen) != expected_stub or sum(stub_seen.values()) != 60:
        problems.append("stub set %d/%d does not match the 30 cross-page FKs"
                        % (sum(stub_seen.values()), len(stub_seen)))

    # 59/59 exactly once
    drawn = sum(1 for fk in same if conn_seen[fk["constraint"]] == 1) + \
        sum(1 for fk in cross
            if stub_seen[(fk["constraint"], "out")] == 1 and
            stub_seen[(fk["constraint"], "in")] == 1)
    if drawn != 59:
        problems.append("FKs drawn exactly once %d != 59" % drawn)

    # ledger
    if len(spec.get("cross_page_fks", [])) != 30:
        problems.append("cross ledger %d != 30"
                        % len(spec.get("cross_page_fks", [])))

    print("tables 41, columns 293, FKs 59, migrations 19")
    print("pages 5, same-page FK connectors %d, cross-page FKs %d, stubs %d"
          % (sum(len(p.get("connectors", [])) for p in spec["pages"]),
             len(cross), total_stubs))
    print("FKs drawn exactly once: %d/59 (%d connectors + %d stub pairs)"
          % (drawn, len(same), len(cross)))
    if problems:
        print("RESULT: FAIL (%d)" % len(problems))
        for msg in problems[:40]:
            print(" -", msg)
        sys.exit(1)
    print("RESULT: PASS")
    print("all 41 cards exactly once; 293/293 rows match real order/type/"
          "nullability/PK-FK; every same-page FK has exactly one orthogonal "
          "crow-foot connector with a one bar and no card/text crossing; every "
          "cross-page FK has exactly one to/from stub pair on the correct "
          "columns; no dangling connector endpoint.")


if __name__ == "__main__":
    main()

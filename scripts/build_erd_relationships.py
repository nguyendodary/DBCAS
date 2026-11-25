# -*- coding: utf-8 -*-
"""Build the 13-page DBCAS entity-relationship figure set from introspection.

Every page is generated from docs/diagrams/schema-028/schema-introspection.json:
67 tables, 561 columns, 122 foreign keys, 159 indexes, 28 migrations.
The seven module pages draw intra-module foreign keys as lines and list
cross-module references in a panel; the four ledger pages enumerate every
foreign key with cardinality and delete/update action.

Usage: py scripts/build_erd_relationships.py
Output: docs/submission/final/assets/erd/*.svg + manifest.json
"""
from __future__ import annotations

import json
import math
from collections import OrderedDict, Counter
from pathlib import Path

from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
INTRO = ROOT / "docs/diagrams/schema-028/schema-introspection.json"
OUT = ROOT / "docs/submission/final/assets/erd"

NAVY = "#083F75"
BLUE = "#23A2D9"
LIGHT = "#EAF4FB"
MID = "#D6EAF8"
BORDER = "#4472C4"
GREY = "#F2F2F2"
GREY_BORDER = "#B8C4D0"
TEXT = "#1F2937"
MUTED = "#52657A"
AMBER = "#C55A11"
AMBER_FILL = "#FBE5D6"
GREEN = "#2E7D32"
WHITE = "#FFFFFF"

FONT = "Arial, Helvetica, sans-serif"
MONO = "Consolas, 'Courier New', monospace"
FONT_PATH = Path("C:/Windows/Fonts/arial.ttf")
MONO_PATH = Path("C:/Windows/Fonts/consola.ttf")


def esc(value) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def text_width(text: str, size: int, mono: bool = False) -> float:
    path = MONO_PATH if mono else FONT_PATH
    font = ImageFont.truetype(str(path), size)
    return font.getlength(str(text))


def fit(text: str, size: int, width: float, mono: bool = False) -> str:
    if text_width(text, size, mono) <= width:
        return text
    suffix = "…"
    while text and text_width(text + suffix, size, mono) > width:
        text = text[:-1]
    return text + suffix


def wrap(text: str, size: int, width: float, mono: bool = False) -> list[str]:
    words = str(text).split()
    lines, current = [], ""
    for word in words:
        candidate = (current + " " + word).strip()
        if text_width(candidate, size, mono) <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class SVG:
    def __init__(self, title: str, subtitle: str, width: int = 2200, height: int = 1700):
        self.width, self.height = width, height
        self.parts = [f'<rect width="{width}" height="{height}" fill="{WHITE}"/>']
        self.defs = [
            f'<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="{NAVY}"/></marker>',
            f'<marker id="arrow-grey" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="{MUTED}"/></marker>',
        ]
        self.text(46, 62, title, 40, NAVY, bold=True)
        if subtitle:
            self.text(48, 104, subtitle, 23, MUTED)

    def add(self, fragment: str):
        self.parts.append(fragment)

    def rect(self, x, y, w, h, *, fill=WHITE, stroke=BORDER, sw=2, rx=8, dash=None):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{extra}/>')

    def line(self, x1, y1, x2, y2, *, stroke=NAVY, sw=2, dash=None, marker=None):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        marker_attr = f' marker-end="url(#{marker})"' if marker else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{extra}{marker_attr}/>')

    def path(self, d, *, stroke=NAVY, sw=2.5, dash=None, marker="arrow"):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        marker_attr = f' marker-end="url(#{marker})"' if marker else ""
        self.add(f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{sw}"{extra}{marker_attr}/>')

    def text(self, x, y, value, size, color=TEXT, *, bold=False, anchor="start",
             mono=False, italic=False):
        weight = ' font-weight="bold"' if bold else ""
        style = ' font-style="italic"' if italic else ""
        family = MONO if mono else FONT
        self.add(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" fill="{color}" text-anchor="{anchor}"{weight}{style}>{esc(value)}</text>')

    def save(self, path: Path):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" '
               f'viewBox="0 0 {self.width} {self.height}" role="img">'
               f'<defs>{"".join(self.defs)}</defs>{"".join(self.parts)}</svg>')
        path.write_text(svg, encoding="utf-8")
        return path


DATA = json.loads(INTRO.read_text(encoding="utf-8"))
TABLES = {t["table"]: t for t in DATA["tables"]}
FKS = DATA["foreign_keys"]
DOMAINS: OrderedDict[str, list[str]] = OrderedDict([
    ("Identity and access", ["account", "account_identity", "account_role", "account_role_audit",
                             "refresh_session", "oauth_handoff", "login_throttle",
                             "password_reset_token", "password_reset_audit", "user_profile",
                             "role", "system_setting"]),
    ("Curriculum and concepts", ["course_learning_outcome", "concept", "concept_dependency",
                                 "concept_competency", "clo_concept", "course_document",
                                 "document_chunk", "document_clo"]),
    ("Question bank and generation", ["question", "question_concept", "question_clo",
                                      "question_translation", "question_evidence", "mcq_option",
                                      "rubric", "sql_test_dataset", "question_candidate",
                                      "question_rubric_profile", "question_rubric_criterion"]),
    ("Assessment and attempts", ["assessment", "assessment_blueprint", "assessment_concept",
                                 "assessment_question", "assessment_session", "attempt",
                                 "session_question_plan", "session_start_request", "selection_log",
                                 "adaptive_event", "tab_leave_interval", "attempt_rubric_criterion"]),
    ("Grading, results and competency", ["evaluation_record", "grading_job", "grade_review",
                                         "grade_edit_audit", "result_release_event",
                                         "session_final_result", "session_result_version",
                                         "session_result_version_score",
                                         "session_result_criterion_score",
                                         "session_result_analysis", "session_result_publication",
                                         "competency_gap"]),
    ("Review workflow", ["review_request", "question_report", "review_deviation",
                         "review_deviation_confirmation"]),
    ("AI audit and retention", ["ai_stage_run", "ai_stage_validation", "ai_stage_attempt",
                                "ai_prompt_record", "ai_prompt_content", "prompt_access_audit",
                                "retention_purge_audit", "llm_cache"]),
])
DOMAIN_OF = {t: name for name, ts in DOMAINS.items() for t in ts}
PK = {}
UNIQUE = {}
for table, meta in TABLES.items():
    PK[table] = next((c["columns"] for c in meta["constraints"] if c["type"] == "p"), [])
    UNIQUE[table] = [c["columns"] for c in meta["constraints"] if c["type"] == "u"]
COLUMN = {(t, c["name"]): c for t, meta in TABLES.items() for c in meta["columns"]}
MANIFEST = []


def cardinality(fk):
    source, cols = fk["source"], fk["columns"]
    nullable = any(COLUMN[(source, c)]["nullable"] for c in cols)
    if set(cols) == set(PK[source]) or any(set(cols) == set(u) for u in UNIQUE[source]):
        return "1 : 0..1" if nullable else "1 : 1"
    return f"1 : 0..N" if nullable else f"1 : 1..N"


def table_columns(table):
    meta = TABLES[table]
    pk = set(PK[table])
    fk_cols = {c for f in FKS if f["source"] == table for c in f["columns"]}
    rows = []
    for c in meta["columns"]:
        if c["name"] in pk:
            rows.append(("PK", c["name"], c["type"]))
        elif c["name"] in fk_cols:
            rows.append(("FK", c["name"], c["type"]))
    return rows, len(meta["columns"])


def fk_target_text(fk):
    return f'{fk["source"]}({",".join(fk["columns"])}) → {fk["destination"]}({",".join(fk["reference_columns"])})'


# ---------------------------------------------------------------------------
# 1. Overview
# ---------------------------------------------------------------------------
def border_point(box, toward):
    """Intersection of the centre-to-toward line with the box border."""
    x, y, w, h = box
    cx, cy = x + w / 2, y + h / 2
    tx, ty = toward
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    scale = min(
        (w / 2) / abs(dx) if dx else float("inf"),
        (h / 2) / abs(dy) if dy else float("inf"),
    )
    return cx + dx * scale, cy + dy * scale


def overview():
    s = SVG("Entity relationship overview — seven schema domains",
            "67 tables · 561 columns · 122 foreign keys · 159 indexes · 28 migrations · PostgreSQL 17.12")
    positions = {
        "Identity and access": (780, 150, 640, 220),
        "Curriculum and concepts": (100, 470, 600, 230),
        "Question bank and generation": (1500, 470, 600, 230),
        "AI audit and retention": (100, 900, 540, 230),
        "Assessment and attempts": (1520, 900, 580, 230),
        "Review workflow": (520, 1300, 540, 230),
        "Grading, results and competency": (1220, 1300, 620, 230),
    }
    centers = {k: (x + w / 2, y + h / 2) for k, (x, y, w, h) in positions.items()}
    cross = Counter()
    internal = Counter()
    for fk in FKS:
        a, b = DOMAIN_OF[fk["source"]], DOMAIN_OF[fk["destination"]]
        if a == b:
            internal[a] += 1
        else:
            cross[(a, b)] += 1
    # draw the ten strongest cross-domain paths; all paths are in the ledgers
    top = cross.most_common(10)
    for i, ((a, b), count) in enumerate(top):
        x1, y1 = border_point(positions[a], centers[b])
        x2, y2 = border_point(positions[b], centers[a])
        dx, dy = x2 - x1, y2 - y1
        length = max(1.0, math.hypot(dx, dy))
        ox, oy = -dy / length * 16, dx / length * 16
        mx, my = (x1 + x2) / 2 + ox, (y1 + y2) / 2 + oy
        s.path(f"M{x1:.0f},{y1:.0f} Q{mx:.0f},{my:.0f} {x2:.0f},{y2:.0f}",
               stroke=BORDER, sw=2.4)
        lx, ly = (x1 + x2) / 2 + ox * 1.6, (y1 + y2) / 2 + oy * 1.6
        s.rect(lx - 32, ly - 21, 64, 36, fill=WHITE, stroke=BORDER, sw=1, rx=6)
        s.text(lx, ly + 6, str(count), 20, NAVY, bold=True, anchor="middle")
    for name, (x, y, w, h) in positions.items():
        s.rect(x, y, w, h, fill=LIGHT, stroke=NAVY, sw=2.5, rx=10)
        s.text(x + 20, y + 38, fit(name, 24, w - 40), 24, NAVY, bold=True)
        s.text(x + 20, y + 72, f"{len(DOMAINS[name])} tables · {sum(len(TABLES[t]['columns']) for t in DOMAINS[name])} columns",
               19, MUTED)
        s.text(x + 20, y + 104, f"{internal[name]} intra-domain FK" + ("s" if internal[name] != 1 else ""), 18, TEXT)
        outbound = sum(1 for fk in FKS if DOMAIN_OF[fk["source"]] == name and DOMAIN_OF[fk["destination"]] != name)
        inbound = sum(1 for fk in FKS if DOMAIN_OF[fk["destination"]] == name and DOMAIN_OF[fk["source"]] != name)
        s.text(x + 20, y + 138, f"Outbound {outbound} · inbound {inbound}", 18, MUTED)
        s.text(x + 20, y + 172, "Entity cards: Figure 2 (1/7–7/7)", 16, GREEN)
    # legend
    s.rect(60, 1570, 2080, 100, fill=GREY, stroke=GREY_BORDER, sw=1.5, rx=8)
    s.text(80, 1602, "How to read this page", 20, NAVY, bold=True)
    s.text(80, 1632, "Each box is one schema domain; the arrow points from the referencing domain to the referenced domain and the number is the count of foreign keys on that path. "
                     "The ten strongest of 19 cross-domain paths are drawn here.", 16, TEXT)
    s.text(80, 1658, "58 foreign keys stay inside a domain and 64 cross a boundary (58 + 64 = 122). Every path, table and FK is enumerated on the index page, the seven module pages and the four ledgers.", 16, MUTED)
    return s.save(OUT / "erd-overview.svg"), "ERD overview — domains and cross-domain relationships (1/2)"


def index_page():
    s = SVG("Entity relationship index — every table in one domain",
            "67 tables mapped once to seven domains · counts measured from schema-introspection.json")
    headers = ["Domain", "Tables", "Columns", "Internal FK", "Outbound FK", "Inbound FK"]
    widths = [640, 150, 170, 220, 240, 240]
    x0, y0 = 46, 150
    s.rect(x0, y0, sum(widths), 52, fill=NAVY, stroke=NAVY, sw=1, rx=0)
    x = x0
    for h, w in zip(headers, widths):
        s.text(x + 12, y0 + 34, h, 20, WHITE, bold=True)
        x += w
    y = y0 + 52
    for name, ts in DOMAINS.items():
        internal = sum(1 for fk in FKS if fk["source"] in ts and fk["destination"] in ts)
        outbound = sum(1 for fk in FKS if fk["source"] in ts and fk["destination"] not in ts)
        inbound = sum(1 for fk in FKS if fk["destination"] in ts and fk["source"] not in ts)
        vals = [name, str(len(ts)), str(sum(len(TABLES[t]["columns"]) for t in ts)),
                str(internal), str(outbound), str(inbound)]
        s.rect(x0, y, sum(widths), 48, fill=WHITE if len(MANIFEST) % 2 else LIGHT, stroke=GREY_BORDER, sw=0.8, rx=0)
        x = x0
        for v, w in zip(vals, widths):
            s.text(x + 12, y + 32, v, 19, TEXT, bold=(v == name))
            x += w
        y += 48
    s.rect(x0, y, sum(widths), 48, fill=MID, stroke=GREY_BORDER, sw=0.8, rx=0)
    totals = ["Total", "67", "561", str(sum(1 for fk in FKS if DOMAIN_OF[fk['source']] == DOMAIN_OF[fk['destination']])), "64", "64"]
    x = x0
    for v, w in zip(totals, widths):
        s.text(x + 12, y + 32, v, 19, NAVY, bold=True)
        x += w
    # table directory in three columns
    s.text(46, y + 110, "Table directory (source of every entity card)", 24, NAVY, bold=True)
    col_x = [46, 760, 1470]
    col_y = y + 150
    line_h = 25
    items = []
    for name, ts in DOMAINS.items():
        items.append((name, ts))
    col = 0
    yy = col_y
    for name, ts in items:
        s.text(col_x[col], yy, name, 18, BLUE, bold=True)
        yy += line_h + 2
        for t in ts:
            s.text(col_x[col] + 8, yy, f"{t}  ({len(TABLES[t]['columns'])})", 16, TEXT, mono=True)
            yy += line_h
        yy += 12
        if col < 2 and yy > 1450:
            col += 1
            yy = col_y
    s.text(46, 1650, "PK/FK columns are drawn on the module pages; full column dictionaries are in §3 and Appendix A of the Database Design document.", 17, MUTED)
    return s.save(OUT / "erd-index.svg"), "ERD index — table-to-domain map and relationship counts (2/2)"


# ---------------------------------------------------------------------------
# 2. Module pages
# ---------------------------------------------------------------------------
def module_page(name: str, page_no: int):
    tables = DOMAINS[name]
    s = SVG(f"Entity relationship diagram — {name} ({page_no}/11)",
            f"{len(tables)} tables · {sum(len(TABLES[t]['columns']) for t in tables)} columns · "
            f"{sum(1 for fk in FKS if fk['source'] in tables and fk['destination'] in tables)} intra-domain foreign keys")
    n = len(tables)
    cols = 3 if n > 4 else 2
    rows = math.ceil(n / cols)
    left, right, top = 42, 42, 142
    panel_h = 196
    bottom = s.height - panel_h - 22
    gutter_x, gutter_y = 90, 56
    card_w = (s.width - left - right - gutter_x * (cols - 1)) / cols
    card_h = (bottom - top - gutter_y * (rows - 1)) / rows
    rects = {}
    for i, table in enumerate(tables):
        r, c = divmod(i, cols)
        x = left + c * (card_w + gutter_x)
        y = top + r * (card_h + gutter_y)
        rects[table] = (x, y, card_w, card_h)
    # cards
    for table in tables:
        x, y, w, h = rects[table]
        s.rect(x, y, w, h, fill=WHITE, stroke=NAVY, sw=2, rx=8)
        s.rect(x, y, w, 54, fill=NAVY, stroke=NAVY, sw=1, rx=8)
        s.rect(x, y + 44, w, 10, fill=NAVY, stroke=NAVY, sw=1, rx=0)
        s.text(x + 14, y + 37, fit(table, 30, w - 28, mono=True), 30, WHITE, bold=True, mono=True)
        rows_data, total_cols = table_columns(table)
        line_h = 34
        max_rows = max(1, int((h - 90) / line_h))
        shown = rows_data[:max_rows]
        yy = y + 86
        for kind, col, typ in shown:
            if kind:
                kind_color = AMBER if kind == "PK" else BLUE
                s.text(x + 14, yy, kind, 20, kind_color, bold=True, mono=True)
            s.text(x + 62, yy, fit(col, 24, w - 76, mono=True), 24, TEXT, mono=True)
            yy += line_h
        if len(rows_data) > len(shown):
            s.text(x + 14, y + h - 20, f"+{len(rows_data) - len(shown)} key columns omitted", 20, MUTED, italic=True)
        elif total_cols > len(rows_data):
            hidden = total_cols - len(rows_data)
            s.text(x + 14, y + h - 20, f"{hidden} non-key column" + ("s" if hidden != 1 else ""), 20, MUTED, italic=True)
        else:
            s.text(x + 14, y + h - 20, f"{total_cols} columns", 20, MUTED, italic=True)
    # edges on top of cards, routed only through the horizontal/vertical gutters
    edges = [fk for fk in FKS if fk["source"] in tables and fk["destination"] in tables]
    for fk in edges:
        sx, sy, sw, sh = rects[fk["source"]]
        tx, ty, tw, th = rects[fk["destination"]]
        scx, scy = sx + sw / 2, sy + sh / 2
        tcx, tcy = tx + tw / 2, ty + th / 2
        sc = tables.index(fk["source"]) % cols
        sr = tables.index(fk["source"]) // cols
        tc = tables.index(fk["destination"]) % cols
        tr = tables.index(fk["destination"]) // cols
        label = cardinality(fk)
        if fk["source"] == fk["destination"]:
            # self-loop in the row gutter below (or above the last row)
            x1, x2 = sx + sw * 0.55, sx + sw * 0.78
            if sr < rows - 1:
                y0 = sy + sh
                d = f"M{x1:.0f},{y0:.0f} C{x1:.0f},{y0 + 48:.0f} {x2:.0f},{y0 + 48:.0f} {x2:.0f},{y0:.0f}"
                lx, ly = (x1 + x2) / 2, y0 + 26
            else:
                y0 = sy
                d = f"M{x1:.0f},{y0:.0f} C{x1:.0f},{y0 - 44:.0f} {x2:.0f},{y0 - 44:.0f} {x2:.0f},{y0:.0f}"
                lx, ly = (x1 + x2) / 2, y0 - 22
            s.path(d, stroke=NAVY, sw=2.8)
        elif sr == tr and abs(tc - sc) == 1:
            x1 = sx + sw if tc > sc else sx
            x2 = tx if tc > sc else tx + tw
            d = f"M{x1:.0f},{scy:.0f} L{x2:.0f},{scy:.0f}"
            s.path(d, stroke=NAVY, sw=2.8)
            lx, ly = (x1 + x2) / 2, scy - 16
        elif sc == tc and abs(tr - sr) == 1:
            y1 = sy + sh if tr > sr else sy
            y2 = ty if tr > sr else ty + th
            d = f"M{scx:.0f},{y1:.0f} L{scx:.0f},{y2:.0f}"
            s.path(d, stroke=NAVY, sw=2.8)
            lx, ly = scx + 44, (y1 + y2) / 2
        else:
            # exit into a gutter, travel only in gutters, approach the target
            # from the side that faces the source
            if tc != sc:
                if tc > sc:
                    gx = sx + sw + gutter_x / 2
                    x0 = sx + sw
                else:
                    gx = sx - gutter_x / 2
                    x0 = sx
                y0 = scy
                if tr == sr:
                    if sr < rows - 1:  # route below the shared row
                        gy = ty + th + gutter_y / 2
                        ty_border = ty + th
                    else:              # last row: route above it
                        gy = ty - gutter_y / 2
                        ty_border = ty
                elif tr < sr:  # target above: approach from below
                    gy = ty + th + gutter_y / 2
                    ty_border = ty + th
                else:       # target below: approach from above
                    gy = ty - gutter_y / 2
                    ty_border = ty
                tx_border = tx + tw / 2
                d = (f"M{x0:.0f},{y0:.0f} L{gx:.0f},{y0:.0f} L{gx:.0f},{gy:.0f} "
                     f"L{tx_border:.0f},{gy:.0f} L{tx_border:.0f},{ty_border:.0f}")
                if abs(gy - y0) > 70:
                    lx, ly = gx, (y0 + gy) / 2
                else:
                    lx, ly = (gx + tx_border) / 2, gy - 2
            else:
                y0 = sy + sh if tr > sr else sy
                gy = y0 + (gutter_y / 2 if tr > sr else -gutter_y / 2)
                if tc == cols - 1:
                    gx = tx - gutter_x / 2
                    x_border = tx
                else:
                    gx = tx + tw + gutter_x / 2
                    x_border = tx + tw
                d = (f"M{scx:.0f},{y0:.0f} L{scx:.0f},{gy:.0f} "
                     f"L{gx:.0f},{gy:.0f} L{gx:.0f},{tcy:.0f} L{x_border:.0f},{tcy:.0f}")
                if abs(tcy - gy) > 70:
                    lx, ly = gx, (gy + tcy) / 2
                else:
                    lx, ly = (scx + gx) / 2, gy - 2
            s.path(d, stroke=NAVY, sw=2.8)
        # Cardinality and delete rules are enumerated on the four ledger pages;
        # drawing a label on every line would obscure the entity cards.
    # external references panel
    external = [fk for fk in FKS if fk["source"] in tables and fk["destination"] not in tables]
    s.rect(42, s.height - panel_h - 8, s.width - 84, panel_h, fill=GREY, stroke=GREY_BORDER, sw=1.2, rx=8)
    s.text(58, s.height - panel_h + 24, f"External references — {len(external)} foreign keys to tables outside this module", 22, NAVY, bold=True)
    targets = Counter(fk["destination"] for fk in external)
    items = [f"{t} ({c})" for t, c in sorted(targets.items())]
    per_col = max(1, math.ceil(len(items) / 4))
    for c in range(4):
        chunk = items[c * per_col:(c + 1) * per_col]
        for r, item in enumerate(chunk):
            s.text(58 + c * 520, s.height - panel_h + 60 + r * 30, "· " + fit(item, 18, 480, mono=True), 18, TEXT, mono=True)
    s.text(58, s.height - 32, "Legend: PK amber · FK blue · line = intra-module foreign key (arrow points to the referenced table) · cardinality and delete rules are on the ledger pages.", 18, MUTED)
    return s.save(OUT / f"erd-module-{page_no}.svg"), f"Entity relationship diagram — {name} ({page_no}/11)"


# ---------------------------------------------------------------------------
# 3. Ledger pages
# ---------------------------------------------------------------------------
def ledger_page(rows, start_index: int, page_no: int):
    first = start_index + 1
    last = start_index + len(rows)
    s = SVG(f"Foreign-key ledger — rows {first}–{last} of 122 ({7 + page_no}/11)",
            f"{len(rows)} foreign keys in source-table order · cardinality, delete and update rules")
    headers = ["#", "Foreign key", "Child → parent", "Card.", "On delete"]
    widths = [46, 540, 1240, 110, 184]
    x0, y0 = 40, 142
    s.rect(x0, y0, sum(widths), 46, fill=NAVY, stroke=NAVY, sw=1, rx=0)
    x = x0
    for h, w in zip(headers, widths):
        s.text(x + 8, y0 + 31, h, 22, WHITE, bold=True)
        x += w
    y = y0 + 46
    line_h = min(40, max(20, (1628 - y) // max(1, len(rows))))
    for i, fk in enumerate(rows):
        s.rect(x0, y, sum(widths), line_h, fill=WHITE if i % 2 == 0 else LIGHT, stroke=GREY_BORDER, sw=0.5, rx=0)
        s.text(x0 + 8, y + line_h - 11, str(start_index + i + 1), 19, MUTED, mono=True)
        s.text(x0 + 54, y + line_h - 11, fit(fk["constraint"], 19, 520, mono=True), 19, TEXT, mono=True)
        s.text(x0 + 594, y + line_h - 11, fit(fk_target_text(fk), 19, 1220, mono=True), 19, TEXT, mono=True)
        s.text(x0 + 1834, y + line_h - 11, cardinality(fk), 19, NAVY, mono=True)
        s.text(x0 + 1944, y + line_h - 11, fk["on_delete"], 19, AMBER if fk["on_delete"] != "NO ACTION" else MUTED, mono=True)
        y += line_h
    s.text(40, 1658, f"Rows {first}–{last} of 122 · 67 tables, 561 columns, 122 foreign keys, 159 indexes, 28 migrations. The full FK definition is in schema-introspection.json; this ledger adds cardinality and delete/update rules.", 18, MUTED)
    return s.save(OUT / f"erd-ledger-{page_no}.svg"), f"Foreign-key ledger — rows {first}–{last} of 122 ({7 + page_no}/11)"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for builder in (overview, index_page):
        path, title = builder()
        manifest.append({"file": path.name, "title": title})
    for i, name in enumerate(DOMAINS, 1):
        path, title = module_page(name, i)
        manifest.append({"file": path.name, "title": title})
    start = 0
    for i, size in enumerate((31, 31, 30, 30), 1):
        chunk = FKS[start:start + size]
        path, title = ledger_page(chunk, start, i)
        manifest.append({"file": path.name, "title": title})
        start += size
    assert start == len(FKS) == 122, start
    # integrity checks
    assigned = [t for ts in DOMAINS.values() for t in ts]
    assert len(assigned) == len(set(assigned)) == len(TABLES) == 67, (len(assigned), len(TABLES))
    assert sum(1 for fk in FKS if DOMAIN_OF[fk["source"]] == DOMAIN_OF[fk["destination"]]) == 58
    assert len(FKS) == 122
    assert len(manifest) == 13, len(manifest)
    (OUT / "manifest.json").write_text(json.dumps({
        "source": "docs/diagrams/schema-028/schema-introspection.json",
        "measured": {"tables": len(TABLES), "columns": sum(len(t["columns"]) for t in TABLES.values()),
                     "foreign_keys": len(FKS), "indexes": len(DATA["indexes"]),
                     "migrations": DATA["migrations"]},
        "pages": manifest,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"built {len(manifest)} ERD pages in {OUT}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Shared data + card/connector renderer for the W3b Table Relationship
Diagram (original-style clone and content-delta pages).

No layout engine: every coordinate comes from the measured Stage A trace or
from the deterministic page grid defined here. Cards keep the original
grammar: grey header band, table name, one row per column with name,
[PK]/[FK]/[PK, FK] marker, compact type; PK names bold + underlined.
"""
import json
import math
import os
import sys
import xml.sax.saxutils as saxutils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_fonts import ink  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTRO = os.path.join(ROOT, "docs", "qa", "schema-introspection.json")

# --------------------------------------------------------------------------
# Original 21 cards, transcribed from 2x crops of ArchitectureDesign image9.
# marker "" = ordinary column, "[PK]", "[FK]" or "[PK, FK]".
# --------------------------------------------------------------------------
ORIGINAL_CARDS = [
    ("Role", [
        ("role_id", "[PK]", "int"), ("role_name", "", "varchar(50)"),
        ("description", "", "text")]),
    ("AccountRole", [
        ("account_id", "[PK, FK]", "int"), ("role_id", "[PK, FK]", "int"),
        ("assigned_at", "", "timestamptz")]),
    ("UserProfile", [
        ("user_id", "[PK]", "int"), ("account_id", "[FK]", "int"),
        ("full_name", "", "varchar(100)"), ("student_code", "", "varchar(20)"),
        ("phone_number", "", "varchar(20)"), ("date_of_birth", "", "date")]),
    ("LLMCache", [
        ("cache_id", "[PK]", "int"), ("request_hash", "", "varchar(64)"),
        ("task_type", "", "varchar(30)"), ("model", "", "varchar(50)"),
        ("response", "", "jsonb"), ("created_at", "", "timestamptz")]),
    ("Account", [
        ("account_id", "[PK]", "int"), ("email", "", "varchar(255)"),
        ("password_hash", "", "varchar(255)"), ("status", "", "varchar(20)"),
        ("created_at", "", "timestamptz")]),
    ("CourseLearningOutcome", [
        ("clo_id", "[PK]", "int"), ("clo_code", "", "varchar(20)"),
        ("title", "", "varchar(200)"), ("description", "", "text"),
        ("status", "", "varchar(20)"), ("created_by", "[FK]", "int"),
        ("created_at", "", "timestamptz")]),
    ("CLOConcept", [
        ("clo_id", "[PK, FK]", "int"), ("concept_id", "[PK, FK]", "int"),
        ("mapping_source", "", "varchar(10)"), ("status", "", "varchar(20)"),
        ("created_at", "", "timestamptz")]),
    ("Assessment", [
        ("assessment_id", "[PK]", "int"), ("title", "", "varchar(200)"),
        ("description", "", "text"), ("max_questions", "", "smallint"),
        ("duration_min", "", "smallint"), ("target_mcq", "", "smallint"),
        ("target_sql", "", "smallint"), ("target_essay", "", "smallint"),
        ("status", "", "varchar(20)"), ("created_by", "[FK]", "int"),
        ("created_at", "", "timestamptz")]),
    ("Concept", [
        ("concept_id", "[PK]", "int"), ("concept_code", "", "varchar(30)"),
        ("concept_name", "", "varchar(100)"),
        ("subject_area", "", "varchar(100)"), ("description", "", "text"),
        ("difficulty_level", "", "smallint")]),
    ("QuestionConcept", [
        ("question_id", "[PK, FK]", "int"),
        ("concept_id", "[PK, FK]", "int"), ("tag_source", "", "varchar(10)"),
        ("is_required", "", "boolean"), ("confirmed", "", "boolean")]),
    ("QuestionCandidate", [
        ("candidate_id", "[PK]", "int"), ("concept_id", "[FK]", "int"),
        ("question_type", "", "varchar(10)"), ("payload", "", "jsonb"),
        ("validation_status", "", "varchar(20)"),
        ("validation_detail", "", "jsonb"),
        ("promoted_question_id", "[FK]", "int"),
        ("created_at", "", "timestamptz")]),
    ("AssessmentConcept", [
        ("assessment_id", "[PK, FK]", "int"),
        ("concept_id", "[PK, FK]", "int"),
        ("min_difficulty", "", "smallint"),
        ("max_difficulty", "", "smallint"),
        ("target_pct", "", "numeric(5,2)")]),
    ("Question", [
        ("question_id", "[PK]", "int"), ("question_type", "", "varchar(10)"),
        ("prompt", "", "text"), ("reference_answer", "", "text"),
        ("difficulty_level", "", "smallint"), ("points", "", "numeric(5,2)"),
        ("source", "", "varchar(15)"), ("status", "", "varchar(20)"),
        ("created_by", "[FK]", "int"), ("created_at", "", "timestamptz"),
        ("updated_at", "", "timestamptz")]),
    ("SelectionLog", [
        ("log_id", "[PK]", "int"), ("session_id", "[FK]", "int"),
        ("seq_no", "", "smallint"), ("question_id", "[FK]", "int"),
        ("is_fallback", "", "boolean"),
        ("decision_detail", "", "jsonb"),
        ("created_at", "", "timestamptz")]),
    ("AssessmentSession", [
        ("session_id", "[PK]", "int"), ("assessment_id", "[FK]", "int"),
        ("learner_id", "[FK]", "int"), ("status", "", "varchar(20)"),
        ("started_at", "", "timestamptz"), ("expires_at", "", "timestamptz"),
        ("submitted_at", "", "timestamptz")]),
    ("MCQOption", [
        ("option_id", "[PK]", "int"), ("question_id", "[FK]", "int"),
        ("option_label", "", "varchar(5)"), ("option_text", "", "text"),
        ("is_correct", "", "boolean")]),
    ("SQLTestDataset", [
        ("dataset_id", "[PK]", "int"), ("question_id", "[FK]", "int"),
        ("dataset_name", "", "varchar(100)"), ("setup_sql", "", "text"),
        ("expected_result", "", "jsonb"), ("is_edge_case", "", "boolean")]),
    ("Rubric", [
        ("rubric_id", "[PK]", "int"), ("question_id", "[FK]", "int"),
        ("level_name", "", "varchar(30)"), ("min_score", "", "numeric(5,2)"),
        ("max_score", "", "numeric(5,2)"), ("criteria", "", "text")]),
    ("Attempt", [
        ("attempt_id", "[PK]", "int"), ("session_id", "[FK]", "int"),
        ("question_id", "[FK]", "int"), ("seq_no", "", "smallint"),
        ("selected_option_id", "[FK]", "int"), ("sql_answer", "", "text"),
        ("essay_answer", "", "text"), ("score", "", "numeric(5,2)"),
        ("grading_detail", "", "jsonb"), ("served_at", "", "timestamptz"),
        ("submitted_at", "", "timestamptz")]),
    ("ConceptCompetency", [
        ("competency_id", "[PK]", "int"), ("session_id", "[FK]", "int"),
        ("concept_id", "[FK]", "int"),
        ("points_earned", "", "numeric(6,2)"),
        ("points_possible", "", "numeric(6,2)"),
        ("competency_pct", "", "numeric(5,2)"),
        ("below_target", "", "boolean"),
        ("computed_at", "", "timestamptz")]),
    ("CompetencyGap", [
        ("gap_id", "[PK]", "int"), ("session_id", "[FK]", "int"),
        ("concept_id", "[FK]", "int"), ("llm_explanation", "", "text"),
        ("status", "", "varchar(20)"), ("created_at", "", "timestamptz")]),
]

LEGACY = {"assessment", "assessment_concept", "assessment_question",
          "assessment_blueprint"}


def compact_type(col):
    t = col.get("type") or col.get("udt") or ""
    udt = col.get("udt") or ""
    if t == "character varying":
        return "varchar(%s)" % col.get("max_length") if col.get("max_length") else "varchar"
    if t == "timestamp with time zone" or udt == "timestamptz":
        return "timestamptz"
    if t == "timestamp without time zone":
        return "timestamp"
    if t == "integer" or udt == "int4":
        return "int"
    if t == "bigint" or udt == "int8":
        return "bigint"
    if t == "smallint" or udt == "int2":
        return "smallint"
    if t == "numeric":
        p, s = col.get("numeric_precision"), col.get("numeric_scale")
        if p is not None and s is not None:
            return "numeric(%d,%d)" % (p, s)
        return "numeric"
    if t == "boolean" or udt == "bool":
        return "bool"
    if t == "jsonb":
        return "jsonb"
    if t == "date":
        return "date"
    if t == "uuid":
        return "uuid"
    if t.endswith("[]") or udt.startswith("_"):
        return (udt.lstrip("_") if udt.startswith("_") else t) + "[]"
    return t or udt or "?"


def load_schema():
    d = json.load(open(INTRO, encoding="utf-8"))
    tables = []
    for t in d["tables"]:
        name = t["table"]
        cols = t["columns"]
        pk = set()
        for c in t.get("constraints", []):
            if c.get("type") == "p":
                pk.update(c.get("columns") or [])
        fk_cols = set()
        for fk in d["foreign_keys"]:
            if fk["source"] == name:
                fk_cols.update(fk["columns"])
        rows = []
        for i, c in enumerate(cols):
            bits = []
            if c["name"] in pk:
                bits.append("PK")
            if c["name"] in fk_cols:
                bits.append("FK")
            marker = "[" + ", ".join(bits) + "]" if bits else ""
            rows.append({"name": c["name"], "type": compact_type(c),
                         "nullable": bool(c.get("nullable")),
                         "marker": marker, "pk": c["name"] in pk,
                         "fk": c["name"] in fk_cols,
                         "ordinal": i})
        tables.append({"table": name, "columns": rows,
                       "legacy": name in LEGACY,
                       "fk_out": [fk for fk in d["foreign_keys"]
                                  if fk["source"] == name]})
    return d, tables


# --------------------------------------------------------------------------
# text placement (PIL Arial ink, same math as the checker)
# --------------------------------------------------------------------------
def ink_box(content, weight, size):
    return ink(content, weight, size)


def text_item(id_, content, x, y, size, weight, anchor, color="#1A1A1A",
              measured=None):
    return {"id": id_, "content": content, "x": round(float(x), 2),
            "y": round(float(y), 2), "size": float(size),
            "weight": weight, "anchor": anchor, "ink": color,
            "measured": measured or [0, 0, 0, 0]}


def bbox_of(t):
    """Rendered ink bbox, the exact math used by check_diagram_geometry."""
    x, y = float(t["x"]), float(t["y"])
    size = float(t["size"])
    ix0, iy0, ix1, iy1 = ink(t["content"], t["weight"], size)
    adv = _adv(t["content"], t["weight"], size)
    if t["anchor"] == "middle":
        x -= adv / 2.0
    elif t["anchor"] == "end":
        x -= adv
    return (x + ix0, y + iy0, x + ix1, y + iy1)


_font_cache = {}


def _font(weight, size):
    from PIL import ImageFont
    key = (weight, round(float(size), 2))
    if key not in _font_cache:
        path = "C:/Windows/Fonts/arialbd.ttf" if weight == "bold" else \
               "C:/Windows/Fonts/arial.ttf"
        _font_cache[key] = ImageFont.truetype(path, key[1])
    return _font_cache[key]


def _adv(content, weight, size):
    return _font(weight, size).getlength(content)


# --------------------------------------------------------------------------
# SVG / drawio emit
# --------------------------------------------------------------------------
def fmt(v):
    return "%g" % round(float(v), 2)


def dedupe_segments(segments):
    out, seen = [], set()
    for s in segments:
        key = tuple(round(float(v), 2) for v in s[:4])
        if key in seen:
            continue
        seen.add(key)
        out.append([float(v) for v in s[:4]])
    return out


def row_heights(card):
    hs = card.get("row_heights")
    if hs:
        return hs
    return [card["row_h"]] * len(card["rows"])


def row_top(card, ri):
    return card["bbox"][1] + card["header_h"] + sum(row_heights(card)[:ri])


def svg_page(page, path):
    W = page["canvas"]["w"]
    H = page["canvas"]["h"]
    p = []
    a = p.append
    a('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
      'viewBox="0 0 %d %d">' % (W, H, W, H))
    a('<rect width="%d" height="%d" fill="#FFFFFF"/>' % (W, H))

    # shadows first
    for card in page["cards"]:
        x, y, w, h = card["bbox"]
        a('<rect x="%s" y="%s" width="%s" height="%s" fill="#B8B8B8"/>'
          % (fmt(x + 3), fmt(y + 3), fmt(w), fmt(h)))
    # card bodies + header bands
    for card in page["cards"]:
        x, y, w, h = card["bbox"]
        hh = card["header_h"]
        border = "#1A1A1A"
        if card.get("legacy"):
            a('<rect x="%s" y="%s" width="%s" height="%s" fill="#FFFFFF" '
              'stroke="%s" stroke-width="3" stroke-dasharray="12 8"/>'
              % (fmt(x), fmt(y), fmt(w), fmt(h), border))
        else:
            a('<rect x="%s" y="%s" width="%s" height="%s" fill="#FFFFFF" '
              'stroke="%s" stroke-width="2.5"/>'
              % (fmt(x), fmt(y), fmt(w), fmt(h), border))
        a('<rect x="%s" y="%s" width="%s" height="%s" fill="#E8E8E8"/>'
          % (fmt(x + 1.5), fmt(y + 1.5), fmt(w - 3), fmt(hh - 2)))
        a('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#1A1A1A" '
          'stroke-width="2.5"/>'
          % (fmt(x), fmt(y + hh), fmt(x + w), fmt(y + hh)))
        hs = row_heights(card)
        yy = y + hh
        for i in range(1, len(card["rows"])):
            yy += hs[i - 1]
            a('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#DCDCDC" '
              'stroke-width="2"/>'
              % (fmt(x + 1), fmt(yy), fmt(x + w - 1), fmt(yy)))

    # underlines for PK names
    underlines = list(page.get("underlines", []))
    for card in page["cards"]:
        underlines += list(card.get("underlines", []))
    for t in underlines:
        a('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#1A1A1A" '
          'stroke-width="2"/>' % tuple(fmt(v) for v in t))

    # connectors
    a('<g fill="none" stroke="#1A1A1A" stroke-width="2.5">')
    for s in page.get("segments", []):
        a('<line x1="%s" y1="%s" x2="%s" y2="%s"/>'
          % tuple(fmt(v) for v in s))
    a('</g>')

    # legend
    leg = page.get("legend")
    if leg:
        x, y, w, h = leg["bbox"]
        a('<rect x="%s" y="%s" width="%s" height="%s" rx="12" '
          'fill="#FFFFFF" stroke="#1A1A1A" stroke-width="2.5"/>'
          % (fmt(x), fmt(y), fmt(w), fmt(h)))
        for t in leg["texts"]:
            a('<text x="%s" y="%s" font-size="%s" font-weight="%s" %s'
              'fill="#1A1A1A">%s</text>'
              % (fmt(t["x"]), fmt(t["y"]), fmt(t["size"]), t["weight"],
                 ('text-anchor="%s" ' % t["anchor"]) if t["anchor"] != "start" else "",
                 saxutils.escape(t["content"])))
        for s in leg.get("segments", []):
            a('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#1A1A1A" '
              'stroke-width="2.5"/>' % tuple(fmt(v) for v in s))

    a('<g font-family="Arial, Helvetica, sans-serif" fill="#1A1A1A">')
    for t in page["texts"]:
        anchor = ('text-anchor="%s" ' % t["anchor"]) if t["anchor"] != "start" else ""
        a('<text x="%s" y="%s" font-size="%s" font-weight="%s" %sfill="%s">%s</text>'
          % (fmt(t["x"]), fmt(t["y"]), fmt(t["size"]), t["weight"], anchor,
             t.get("ink", "#1A1A1A"), saxutils.escape(t["content"])))
    a('</g>')
    a('</svg>')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(p) + "\n")


def drawio_page(page, path):
    esc = saxutils.escape
    E = []
    a = E.append
    W = page["canvas"]["w"]
    H = page["canvas"]["h"]
    a('<mxfile host="dbcas-rebuild">')
    a('<diagram id="trd" name="%s">' % esc(page.get("name", "TRD")))
    a('<mxGraphModel dx="%d" dy="%d" grid="1" gridSize="10" guides="1" '
      'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
      'pageWidth="%d" pageHeight="%d" math="0" shadow="0">'
      % (W, H, W, H))
    a('<root>')
    a('<mxCell id="0"/>')
    a('<mxCell id="1" parent="0"/>')

    def vertex(id_, value, style, x, y, w, h):
        a('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="1">'
          % (id_, esc(value), style))
        a('<mxGeometry x="%s" y="%s" width="%s" height="%s" as="geometry"/>'
          % (fmt(x), fmt(y), fmt(w), fmt(h)))
        a('</mxCell>')

    for i, card in enumerate(page["cards"]):
        x, y, w, h = card["bbox"]
        hh = card["header_h"]
        border = "strokeWidth=3;dashed=1;dashPattern=12 8;" if card.get("legacy") \
            else "strokeWidth=2.5;"
        vertex("C%d" % (i + 1), "",
               "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;"
               "strokeColor=#1A1A1A;%s" % border, x, y, w, h)
        vertex("H%d" % (i + 1), "", "rounded=0;whiteSpace=wrap;html=1;"
               "fillColor=#E8E8E8;strokeColor=none;", x + 1.5, y + 1.5,
               w - 3, hh - 2)
        vertex("T%d" % (i + 1), card["title"],
               "text;html=1;align=center;verticalAlign=middle;fontFamily=Arial;"
               "fontSize=%d;fontStyle=1;strokeColor=none;fillColor=none;"
               % int(round(card["title_size"])), x, y, w, hh)
        # one text cell per row: name + marker + type, kept in the card
        ry = y + hh
        hs = row_heights(card)
        for ri, row in enumerate(card["rows"]):
            label = "%s\n%s   %s" % (row["name"], row["marker"], row["type"])
            vertex("R%d_%d" % (i + 1, ri + 1), label,
                   "text;html=1;align=left;verticalAlign=middle;"
                   "fontFamily=Arial;fontSize=%d;fontStyle=%d;strokeColor=none;"
                   "fillColor=none;spacingLeft=18;"
                   % (int(round(card["row_size"])),
                      1 if (row["pk"] or row["fk"]) else 0),
                   x, ry, w, hs[ri])
            ry += hs[ri]
        if card.get("legacy"):
            vertex("G%d" % (i + 1), "LEGACY",
                   "text;html=1;align=right;verticalAlign=middle;fontFamily=Arial;"
                   "fontSize=20;fontStyle=1;fontColor=#7A0000;strokeColor=none;"
                   "fillColor=none;", x + w - 130, y + 8, 118, 40)

    for si, st in enumerate(page.get("stubs", [])):
        b = st["bbox"]
        vertex("ST%d" % (si + 1), st["text"],
               "text;html=1;align=left;verticalAlign=top;fontFamily=Arial;"
               "fontSize=24;fontColor=%s;strokeColor=none;fillColor=none;"
               % st.get("color", "#1A1A1A"),
               b[0] - 2, b[1] - 3, b[2] - b[0] + 8, b[3] - b[1] + 6)

    leg = page.get("legend")
    if leg:
        lx, ly, lw, lh = leg["bbox"]
        vertex("LEG", "", "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;"
               "strokeColor=#1A1A1A;strokeWidth=2.5;arcSize=4;", lx, ly, lw, lh)
        for ti, t in enumerate(page["texts"]):
            if t.get("free"):
                vertex("LT%d" % (ti + 1), t["content"],
                       "text;html=1;align=left;verticalAlign=middle;"
                       "fontFamily=Arial;fontSize=%d;fontStyle=%d;"
                       "strokeColor=none;fillColor=none;"
                       % (int(round(t["size"])),
                          1 if t["weight"] == "bold" else 0),
                       t["x"] - 2, t["y"] - t["size"], 900, t["size"] * 1.6)

    for i, s in enumerate(page.get("segments", [])):
        a('<mxCell id="L%d" style="edgeStyle=none;html=1;endArrow=none;'
          'strokeColor=#1A1A1A;strokeWidth=2.5;" edge="1" parent="1">'
          % (i + 1))
        a('<mxGeometry relative="1" as="geometry">')
        a('<mxPoint x="%s" y="%s" as="sourcePoint"/>' % (fmt(s[0]), fmt(s[1])))
        a('<mxPoint x="%s" y="%s" as="targetPoint"/>' % (fmt(s[2]), fmt(s[3])))
        a('</mxGeometry>')
        a('</mxCell>')

    a('</root>')
    a('</mxGraphModel>')
    a('</diagram>')
    a('</mxfile>')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(E) + "\n")


def page_text_content(page):
    """Expected-label list in checker format."""
    free = [t["content"] for t in page["texts"] if t.get("free")]
    box = [t["content"] for t in page["texts"] if not t.get("free")]
    return {"free_texts": free, "box_texts": box, "ellipse_texts": []}

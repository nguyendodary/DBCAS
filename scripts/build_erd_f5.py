# -*- coding: utf-8 -*-
"""F5 owner-fix rebuild of the Chen ERD (figure 09).

Base: the complete Stage A clone is kept verbatim (same 17 entities, 17 keys,
24 relationship diamonds, 120 traced connector segments, 112 labels).  New
content is added only in the free right/bottom space: SystemSetting, the three
missing legacy tables, and five FK-backed diamonds.

Usage:
  node scripts/run_py.mjs scripts/build_erd_f5.py
"""
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_erd_w3a import build_svg, plan_text, fmt  # noqa: E402
from PIL import ImageFont  # noqa: E402
import xml.sax.saxutils as saxutils  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "diagrams", "rebuild", "erd",
                   "stage-a", "spec-stage-a.json")
OUT = os.path.join(ROOT, "docs", "diagrams", "rebuild", "erd")
BLD = "C:/Windows/Fonts/arialbd.ttf"
REG = "C:/Windows/Fonts/arial.ttf"
ITA = "C:/Windows/Fonts/ariali.ttf"
INK = "#1A1A1A"
LEGACY_INK = "#666666"

W, H = 4300, 1677

# Original slots are untouched.  New column starts at x=3600.
ENTITIES = [
    ("SystemSetting", (3600, 126, 3988, 229), False, 340),
    ("AssessmentQuestion", (3600, 894, 3988, 997), True, 340),
    ("AssessmentBlueprint", (3600, 1278, 3988, 1381), True, 340),
]
# AssessmentConcept is a junction table: it sits next to the retained
# `targets` diamond (not in the far column) and is joined to that diamond by
# a short labelled association, not a second diamond.
ACONCEPT = (700, 1000, 1000, 1103)
KEYS = [
    ("setting_key", 3794, 67, 211, 64, 24),
    ("assessment_id, question_id", 3794, 1056, 330, 74, 20),
    ("blueprint_id", 3794, 1440, 211, 64, 24),
    ("assessment_id, concept_id", 850, 1160, 320, 64, 20),
]
DIAMONDS = [
    ("updates", 2987, 176),
    ("pools", 3420, 944),
    ("versions", 3420, 1160),
    ("uses", 4100, 1160),
]
DW, DH = 162, 76


def text_width(txt, font_path, size):
    return ImageFont.truetype(font_path, size).getlength(txt)


def mk(content, bbox, style, color="#222222"):
    return {"content": content, "bbox": [int(round(v)) for v in bbox],
            "style": style, "color": color}


def entity_text(name, x0, y0, x1, y1, max_width=340):
    cx = (x0 + x1) / 2.0
    size = 32
    while size > 24 and text_width(name, BLD, size) > max_width:
        size -= 1
    tw = text_width(name, BLD, size)
    return mk(name, (cx - tw / 2, y0 + 39, cx + tw / 2, y0 + 63), "entity")


def key_text(name, x0, y0, x1, y1, size):
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    tw = text_width(name, REG, size)
    return mk(name, (cx - tw / 2, cy - 9, cx + tw / 2, cy + 9), "key")


def diamond_text(label, cx, cy):
    tw = text_width(label, ITA, 18)
    return mk(label, (cx - tw / 2, cy - 9, cx + tw / 2, cy + 9), "diamond")


def card(content, x, y):
    tw = text_width(content, BLD, 26)
    return mk(content, (x, y, x + tw, y + 19), "card")


def tag(x1, y1):
    tw = text_width("LEGACY", BLD, 13)
    return mk("LEGACY", (x1 - tw - 14, y1 - 29, x1 - 14, y1 - 14),
              "legacy_tag", LEGACY_INK)


def poly(*pts):
    return {"segs": [[float(x), float(y)] for x, y in pts],
            "color": INK}


def build_drawio_f5(trace, texts):
    """Hand-authored mxGraph; multi-segment routes keep their waypoints."""
    esc = saxutils.escape
    E = []
    a = E.append
    W, H = trace["canvas"]["w"], trace["canvas"]["h"]
    a('<mxfile host="dbcas-rebuild">')
    a('<diagram id="figure" name="ERD">')
    a('<mxGraphModel dx="%d" dy="%d" grid="1" gridSize="10" guides="1" '
      'tooltips="1" connect="1" arrows="0" fold="1" page="1" pageScale="1" '
      'pageWidth="%d" pageHeight="%d" math="0" shadow="0">'
      % (W, H, W, H))
    a('<root>')
    a('<mxCell id="0"/>')
    a('<mxCell id="1" parent="0"/>')

    def vertex(id_, value, style, x, y, w_, h_):
        a('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="1">'
          % (id_, esc(value), style))
        a('<mxGeometry x="%s" y="%s" width="%s" height="%s" as="geometry"/>'
          % (fmt(x), fmt(y), fmt(w_), fmt(h_)))
        a('</mxCell>')

    for i, s in enumerate(trace["shapes"]):
        x0, y0, x1, y1 = s["bbox"]
        kind = s["kind"]
        base = "whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=%s;" % INK
        if kind == "entity":
            dash = "dashed=1;dashPattern=10 7;" if s.get("dashed") else ""
            vertex("S%03d" % (i + 1), "", "rounded=0;" + base +
                   "strokeWidth=4;" + dash, x0, y0, x1 - x0, y1 - y0)
        elif kind == "diamond":
            vertex("S%03d" % (i + 1), "", "rhombus;" + base +
                   "strokeWidth=5;", x0, y0, x1 - x0, y1 - y0)
        elif kind == "ellipse":
            vertex("S%03d" % (i + 1), "", "ellipse;" + base +
                   "strokeWidth=4.5;", x0, y0, x1 - x0, y1 - y0)
        elif kind == "legend":
            vertex("S%03d" % (i + 1), "", "rounded=1;arcSize=8;" + base +
                   "strokeWidth=3;", x0, y0, x1 - x0, y1 - y0)
        elif kind == "legend_rect":
            vertex("S%03d" % (i + 1), "", "rounded=0;" + base +
                   "strokeWidth=4;", x0, y0, x1 - x0, y1 - y0)
        elif kind == "legend_diamond":
            vertex("S%03d" % (i + 1), "", "rhombus;" + base +
                   "strokeWidth=4;", x0, y0, x1 - x0, y1 - y0)
        elif kind == "legend_key":
            vertex("S%03d" % (i + 1), "", "ellipse;" + base +
                   "strokeWidth=3.5;", x0, y0, x1 - x0, y1 - y0)
        elif kind == "legend_legacy":
            vertex("S%03d" % (i + 1), "", "rounded=0;" + base +
                   "strokeWidth=3;dashed=1;dashPattern=9 6;", x0, y0,
                   x1 - x0, y1 - y0)

    for i, ln in enumerate(trace["lines"]):
        pts = ln["segs"]
        (ax, ay), (bx, by) = pts[0], pts[-1]
        a('<mxCell id="L%03d" style="edgeStyle=none;html=1;endArrow=none;'
          'strokeColor=%s;strokeWidth=4;" edge="1" parent="1">'
          % (i + 1, ln.get("color", INK)))
        a('<mxGeometry relative="1" as="geometry">')
        a('<mxPoint x="%s" y="%s" as="sourcePoint"/>' % (fmt(ax), fmt(ay)))
        a('<mxPoint x="%s" y="%s" as="targetPoint"/>' % (fmt(bx), fmt(by)))
        if len(pts) > 2:
            a('<Array as="points">')
            for px, py in pts[1:-1]:
                a('<mxPoint x="%s" y="%s"/>' % (fmt(px), fmt(py)))
            a('</Array>')
        a('</mxGeometry></mxCell>')

    for t in texts:
        b = t["measured"]
        fw = 1 if t["weight"] == "bold" else 0
        fs = 2 if t["italic"] else 0
        a('<mxCell id="%s" value="%s" style="text;html=1;strokeColor=none;'
          'fillColor=none;align=left;verticalAlign=top;fontFamily=Arial;'
          'fontSize=%d;fontStyle=%d;whiteSpace=wrap;spacingLeft=0;'
          'spacingTop=0;" vertex="1" parent="1">'
          % (t["id"], esc(t["content"]), int(t["size"]), fw + fs))
        a('<mxGeometry x="%s" y="%s" width="%s" height="%s" as="geometry"/>'
          % (fmt(b[0]), fmt(b[1]), fmt(b[2] - b[0]), fmt(b[3] - b[1])))
        a('</mxCell>')
    a('</root></mxGraphModel></diagram></mxfile>')
    return "\n".join(E) + "\n"


def main():
    base = json.load(open(SRC, encoding="utf-8"))
    shapes = copy.deepcopy(base["shapes"])
    lines = copy.deepcopy(base["lines"])
    texts = copy.deepcopy(base["texts"])

    # Assessment is the fourth legacy table: dashed, bbox unchanged.
    for s in shapes:
        if s.get("kind") == "entity" and s.get("name") == "Assessment":
            s["dashed"] = True
        if s.get("kind") == "legend":
            s["inner"] = [763, 1525, 3057, 1630]
            s["bbox"] = [760, 1522, 3060, 1633]

    # ---------------------------------------------------------- new entities
    for name, bbox, legacy, maxw in ENTITIES:
        x0, y0, x1, y1 = bbox
        sh = {"kind": "entity", "name": name, "bbox": list(bbox)}
        if legacy:
            sh["dashed"] = True
        shapes.append(sh)
        texts.append(entity_text(name, x0, y0, x1, y1, maxw))
        if legacy:
            texts.append(tag(x1, y1))

    # AssessmentConcept: legacy junction table next to the retained `targets`
    # diamond (the only relation it implements).  It is joined to that
    # diamond by a short labelled association, not by a second diamond.
    ax0, ay0, ax1, ay1 = ACONCEPT
    shapes.append({"kind": "entity", "name": "AssessmentConcept",
                   "bbox": list(ACONCEPT), "dashed": True})
    texts.append(entity_text("AssessmentConcept", ax0, ay0, ax1, ay1, 280))
    texts.append(tag(ax1, ay1))
    # Assessment tag (original box, now legacy)
    texts.append(tag(1295, 613))

    # ---------------------------------------------------------- new keys
    for name, cx, cy, ew, eh, size in KEYS:
        x0, y0 = cx - ew / 2.0, cy - eh / 2.0
        x1, y1 = cx + ew / 2.0, cy + eh / 2.0
        shapes.append({"kind": "ellipse", "name": name,
                       "bbox": [x0, y0, x1, y1], "center": [cx, cy]})
        texts.append(key_text(name, x0, y0, x1, y1, size))

    # ---------------------------------------------------------- new diamonds
    for name, cx, cy in DIAMONDS:
        shapes.append({"kind": "diamond", "name": name,
                       "bbox": [cx - DW / 2.0, cy - DH / 2.0,
                                cx + DW / 2.0, cy + DH / 2.0],
                       "center": [cx, cy]})
        texts.append(diamond_text(name, cx, cy))

    # ---------------------------------------------------------- new routes
    # 1 updates: Account -> SystemSetting (system_setting.updated_by)
    lines.append(poly((1295, 132), (1310, 132), (1310, 20), (2870, 20),
                      (2870, 176), (2906, 176)))
    lines.append(poly((3068, 176), (3600, 176)))
    # 2 pools: Assessment -> AssessmentQuestion (assessment_question.assessment_id)
    lines.append(poly((907, 600), (671, 600), (671, 1498), (3300, 1498),
                      (3300, 944), (3339, 944)))
    lines.append(poly((3501, 944), (3600, 944)))
    # 3 versions: Assessment -> AssessmentBlueprint
    #    (assessment_blueprint.assessment_id)
    lines.append(poly((907, 608), (683, 608), (683, 1506), (3420, 1506),
                      (3420, 1198)))
    lines.append(poly((3501, 1160), (3560, 1160), (3560, 1300),
                      (3600, 1300)))
    # 4 uses: AssessmentSession -> AssessmentBlueprint
    #    (assessment_session.blueprint_id)
    lines.append(poly((1930, 894), (1930, 888), (4100, 888), (4100, 1122)))
    lines.append(poly((4100, 1198), (4100, 1300), (3988, 1300)))
    # 5 junction association: retained `targets` diamond -> AssessmentConcept
    #    (assessment_concept.assessment_id + concept_id).  Not a diamond and
    #    not a new relationship verb: the label is the table name only.
    lines.append(poly((900, 1000), (900, 800), (990, 800), (990, 752),
                      (1019, 752)))
    # key leaders
    for x, y0, y1 in ((3794, 101, 124), (850, 1105, 1126),
                      (3794, 999, 1017), (3794, 1383, 1406)):
        lines.append(poly((x, y0), (x, y1)))

    # ---------------------------------------------------------- new labels
    texts += [
        # updates
        card("1", 1340, 26), card("N", 3560, 145),
        # pools
        card("1", 890, 612), card("N", 3560, 912),
        # versions
        card("1", 890, 632), card("N", 3570, 1268),
        # uses
        card("N", 1940, 860), card("1", 4000, 1268),
    ]
    # label for the targets <-> AssessmentConcept junction association
    texts.append(mk("assessment_concept", (730, 808, 890, 828), "diamond"))
    texts.append(mk("junction", (995, 810, 1065, 828), "diamond"))
    # legend: new dashed swatch + entry
    shapes.append({"kind": "legend_legacy", "bbox": [2540, 1555, 2592, 1600]})
    entry = "Legacy table (historical rows only)"
    tw = text_width(entry, REG, 24)
    texts.append(mk(entry, (2610, 1570, 2610 + tw, 1595), "legend"))

    # ---------------------------------------------------------- plan texts
    # The original text objects T001..T112 are already calibrated; keep them
    # byte-for-byte.  Only the appended labels go through plan_text.
    planned = [dict(t) for t in texts[:112]]
    for i, t in enumerate(texts[112:]):
        planned.append(plan_text(t, 113 + i))

    trace = {"canvas": {"w": W, "h": H}, "shapes": shapes,
             "lines": lines, "texts": planned,
             "source": "Stage A clone + F5 free-space additions"}
    svg = build_svg(trace, planned, "erd")
    with open(os.path.join(OUT, "erd.svg"), "w", encoding="utf-8") as f:
        f.write(svg)
    with open(os.path.join(OUT, "erd.drawio"), "w", encoding="utf-8") as f:
        f.write(build_drawio_f5(trace, planned))

    spec = {"canvas": trace["canvas"],
            "source": trace["source"],
            "shapes": shapes, "lines": lines, "texts": planned,
            "style": {"font_family": "Arial, Helvetica, sans-serif",
                      "stroke": INK, "fill": "#FFFFFF"}}
    with open(os.path.join(OUT, "spec.json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=1)
    with open(os.path.join(OUT, "trace.json"), "w", encoding="utf-8") as f:
        json.dump(trace, f, indent=1)

    cont = {
        "free_texts": [t["content"] for t in planned
                       if t["style"] in ("diamond", "card", "legend",
                                         "legend_key", "legend_bold",
                                         "legacy_tag")],
        "box_texts": [t["content"] for t in planned if t["style"] == "entity"],
        "ellipse_texts": [t["content"] for t in planned
                          if t["style"] == "key"],
    }
    with open(os.path.join(OUT, "text-content.json"), "w",
              encoding="utf-8") as f:
        json.dump(cont, f, indent=1)

    print("entities %d, keys %d, diamonds %d, lines %d, texts %d"
          % (sum(1 for s in shapes if s["kind"] == "entity"),
             sum(1 for s in shapes if s["kind"] == "ellipse"),
             sum(1 for s in shapes if s["kind"] == "diamond"),
             sum(len(l["segs"]) - 1 for l in lines), len(planned)))
    print("wrote erd.svg, erd.drawio, spec.json, text-content.json, trace.json")


if __name__ == "__main__":
    main()

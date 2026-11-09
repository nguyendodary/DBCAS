# -*- coding: utf-8 -*-
"""Stage B content delta for the Chen ERD (W3a).

Writes <out_dir>/trace.json in the same schema as trace_erd_w3a.py, then
build_erd_w3a.py renders it.  Geometry reuses the Stage A entity slots so
the canvas stays 3251 x 1677 and every original label position that survives
the delta keeps its measured coordinate.  Relationships and cardinalities
are taken from docs/qa/content-delta-verified.md section 8 (15 core
FK-backed relations + 5 legacy relations), not invented.

Usage:
  node scripts/run_py.mjs scripts/build_erd_stage_b_w3a.py <out_dir>
"""
import json
import os
import sys

from PIL import ImageFont

BLD = "C:/Windows/Fonts/arialbd.ttf"
REG = "C:/Windows/Fonts/arial.ttf"
ITA = "C:/Windows/Fonts/ariali.ttf"

W, H = 3251, 1677
CANVAS = {"w": W, "h": H}

# entity outer bboxes: original slots (same as Stage A) ----------------------
ENTS = {
    "Role": (267, 126, 655, 229),
    "Account": (907, 126, 1295, 229),
    "UserProfile": (1547, 126, 1935, 229),
    "SystemSetting": (2187, 126, 2575, 229),
    "CourseLearningOutcome": (267, 510, 655, 613),
    "Assessment": (907, 510, 1295, 613),
    "AssessmentConcept": (1547, 510, 1935, 613),
    "Question": (2187, 510, 2575, 613),
    "Concept": (907, 894, 1295, 997),
    "AssessmentSession": (1547, 894, 1935, 997),
    "AssessmentQuestion": (2187, 894, 2575, 997),
    "MCQOption": (2827, 894, 3215, 997),
    "AssessmentBlueprint": (267, 1278, 655, 1381),
    "ConceptCompetency": (907, 1278, 1295, 1381),
    "CompetencyGap": (1547, 1278, 1935, 1381),
    "Attempt": (2827, 1278, 3215, 1381),
}
LEGACY = {"Assessment", "AssessmentConcept", "AssessmentQuestion",
          "AssessmentBlueprint"}

KEY_ELLIPSES = {
    "role_id": (460, 288, 201, 54),
    "account_id": (1100, 67, 201, 54),
    "user_id": (1740, 288, 201, 54),
    "setting_key": (2380, 288, 201, 54),
    "clo_id": (140, 561, 201, 54),
    "assessment_id": (780, 561, 201, 54),
    "assessment_id, concept_id": (1740, 451, 320, 64),
    "question_id": (2060, 561, 201, 54),
    "assessment_id, question_id": (2380, 1056, 320, 64),
    "concept_id": (780, 945, 201, 54),
    "session_id": (1420, 945, 201, 54),
    "option_id": (2700, 945, 201, 54),
    "blueprint_id": (460, 1440, 201, 54),
    "attempt_id": (3020, 1440, 201, 54),
    "competency_id": (1100, 1440, 201, 54),
    "gap_id": (1740, 1440, 201, 54),
}

# name -> (cx, cy)
DIAMONDS = {
    "assigned": (780, 176),
    "has": (1420, 176),
    "defines": (780, 368),
    "updates": (1740, 368),
    "versions": (2680, 560),
    "takes": (1420, 560),
    "targets_legacy": (2060, 688),
    "tagged with": (1740, 752),
    "offers": (2700, 752),
    "requires": (1100, 752),
    "instantiates": (1420, 816),
    "pools": (2060, 944),
    "uses": (780, 1024),
    "yields": (1420, 1136),
    "measured by": (1100, 1136),
    "diagnosed": (1740, 1136),
    "selected in": (3020, 1136),
    "versions_legacy": (780, 1136),
    "records": (2380, 1168),
    "targets": (1420, 1232),
}

DW, DH = 162, 76  # outer diamond bbox


def dvert(name, side):
    cx, cy = DIAMONDS[name]
    return {"left": (cx - DW // 2, cy), "right": (cx + DW // 2, cy),
            "top": (cx, cy - DH // 2), "bottom": (cx, cy + DH // 2)}[side]


def text_width(txt, font_path, size):
    f = ImageFont.truetype(font_path, size)
    return f.getlength(txt)


def mk_text(content, bbox, style, color="#222222"):
    return {"content": content, "bbox": [int(round(v)) for v in bbox],
            "style": style, "color": color}


def entity_text(name):
    x0, y0, x1, y1 = ENTS[name]
    cx = (x0 + x1) / 2.0
    size = 32
    while size > 24 and text_width(name, BLD, size) > 340:
        size -= 1
    tw = text_width(name, BLD, size)
    return mk_text(name, (cx - tw / 2, y0 + 39, cx + tw / 2, y0 + 63),
                   "entity")


def key_text(name):
    cx, cy, ew, eh = KEY_ELLIPSES[name]
    size = 20 if "," in name else 24
    tw = text_width(name, REG, size)
    return mk_text(name, (cx - tw / 2, cy - 9, cx + tw / 2, cy + 9), "key")


def diamond_text(label, dname):
    cx, cy = DIAMONDS[dname]
    size = 18
    tw = text_width(label, ITA, size)
    return mk_text(label, (cx - tw / 2, cy - 9, cx + tw / 2, cy + 9),
                   "diamond")


def card(content, x, y):
    """Cardinality label, top-left (x,y); 26 px bold, ink height 19."""
    tw = text_width(content, BLD, 26)
    return mk_text(content, (x, y, x + tw, y + 19), "card")


def poly(*pts):
    return {"segs": [[float(x), float(y)] for x, y in pts],
            "color": "#1A1A1A"}


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    shapes, lines, texts = [], [], []

    for name, (x0, y0, x1, y1) in ENTS.items():
        shapes.append({"kind": "entity", "name": name, "bbox": [x0, y0, x1, y1],
                       "dashed": name in LEGACY})
        texts.append(entity_text(name))
        if name in LEGACY:
            texts.append(mk_text("LEGACY", (x1 - 96, y1 - 30, x1 - 14,
                                            y1 - 12), "legacy_tag",
                                 "#666666"))

    for name, (cx, cy, ew, eh) in KEY_ELLIPSES.items():
        shapes.append({"kind": "ellipse", "name": name,
                       "bbox": [cx - ew / 2, cy - eh / 2,
                                cx + ew / 2, cy + eh / 2],
                       "center": [cx, cy]})
        texts.append(key_text(name))

    for name, (cx, cy) in DIAMONDS.items():
        shapes.append({"kind": "diamond", "name": name,
                       "bbox": [cx - DW / 2, cy - DH / 2,
                                cx + DW / 2, cy + DH / 2],
                       "center": [cx, cy]})
        label = {"targets_legacy": "targets", "versions_legacy": "versions"}.get(
            name, name)
        texts.append(diamond_text(label, name))

    # ---------------------------------------------------------- relationships
    # (source -> diamond paths, diamond -> target paths, cardinality labels)
    L = []

    # 1 assigned: Account M:N Role
    L.append((poly((655, 176), dvert("assigned", "left")),
              poly(dvert("assigned", "right"), (907, 176))))
    texts += [card("N", 668, 145), card("M", 873, 145)]
    # 2 has: Account 1:1 UserProfile
    L.append((poly((1295, 176), dvert("has", "left")),
              poly(dvert("has", "right"), (1547, 176))))
    texts += [card("1", 1305, 145), card("1", 1508, 145)]
    # 3 defines: Account 1:N CLO
    L.append((poly((958, 229), (958, 368), dvert("defines", "right")),
              poly(dvert("defines", "left"), (604, 368), (604, 510))))
    texts += [card("1", 966, 240), card("N", 612, 480)]
    # 4 takes: Account 1:N Session
    L.append((poly((1250, 229), (1250, 480), (1339, 480),
                   dvert("takes", "left")),
              poly(dvert("takes", "right"), (1535, 560), (1535, 850),
                   (1700, 850), (1700, 894))))
    texts += [card("1", 1258, 240), card("N", 1708, 858)]
    # 5 tagged with: Question M:N Concept
    L.append((poly((2250, 613), (2250, 752), dvert("tagged with", "right")),
              poly(dvert("tagged with", "left"), (1300, 752),
                   (1300, 945), (1295, 945))))
    texts += [card("M", 2258, 715), card("N", 1308, 905)]
    # 6 offers: Question 1:N MCQOption
    L.append((poly((2500, 613), (2500, 752), dvert("offers", "left")),
              poly(dvert("offers", "right"), (2850, 752), (2850, 894))))
    texts += [card("1", 2508, 715), card("N", 2858, 860)]
    # 7 selected in: Attempt N:1 MCQOption
    L.append((poly((3020, 997), dvert("selected in", "top")),
              poly(dvert("selected in", "bottom"), (3020, 1278))))
    texts += [card("1", 3028, 1010), card("N", 3028, 1240)]
    # 8 records: Session 1:N Attempt
    L.append((poly((1850, 997), (1850, 1100), (2100, 1100),
                   (2100, 1168), dvert("records", "left")),
              poly(dvert("records", "right"), (2700, 1168), (2700, 1278))))
    texts += [card("1", 1860, 1010), card("N", 2708, 1240)]
    # 9 yields: Session 1:N ConceptCompetency
    L.append((poly((1600, 997), (1600, 1136), dvert("yields", "right")),
              poly(dvert("yields", "left"), (1200, 1136), (1200, 1278))))
    texts += [card("1", 1608, 1040), card("N", 1208, 1240)]
    # 10 measured by: Concept 1:N ConceptCompetency
    L.append((poly((1100, 997), dvert("measured by", "top")),
              poly(dvert("measured by", "bottom"), (1100, 1278))))
    texts += [card("1", 1108, 1040), card("N", 1108, 1240)]
    # 11 diagnosed: Session 1:N CompetencyGap
    L.append((poly((1740, 997), dvert("diagnosed", "top")),
              poly(dvert("diagnosed", "bottom"), (1740, 1278))))
    texts += [card("1", 1748, 1010), card("N", 1748, 1240)]
    # 12 targets: Concept 1:N CompetencyGap
    L.append((poly((1250, 997), (1250, 1232), dvert("targets", "left")),
              poly(dvert("targets", "right"), (1600, 1232), (1600, 1278))))
    texts += [card("1", 1258, 1040), card("N", 1608, 1240)]
    # 13 versions: Question 1:N Question (family_id self-FK) -- a true
    # self-loop on Question's right side, not a link through SystemSetting.
    L.append((poly((2575, 535), (2615, 535), (2615, 560),
                   dvert("versions", "left")),
              poly((2575, 613), (2575, 630), (2795, 630), (2795, 560),
                   dvert("versions", "right"))))
    texts += [card("1", 2585, 505), card("N", 2585, 635)]
    # 14 updates: Account 1:N SystemSetting
    L.append((poly((1295, 229), (1295, 300), (1500, 300),
                   (1500, 368), (1657, 368)),
              poly(dvert("updates", "right"), (2250, 368), (2250, 229))))
    texts += [card("1", 1320, 370), card("N", 2258, 250)]
    # 15 requires: Concept M:N Concept (concept_dependency)
    L.append((poly((1019, 894), dvert("requires", "left")),
              poly((1181, 894), dvert("requires", "right"))))
    texts += [card("M", 1027, 850), card("N", 1189, 850)]

    # legacy relations ------------------------------------------------------
    # 16 targets: Assessment 1:N AssessmentConcept
    L.append((poly((1250, 613), (1250, 688),
                   dvert("targets_legacy", "left")),
              poly(dvert("targets_legacy", "right"), (2200, 688),
                   (2200, 750), (1900, 750), (1900, 613))))
    texts += [card("1", 1160, 650), card("N", 1908, 640)]
    # 17 pools: Assessment 1:N AssessmentQuestion
    L.append((poly((1250, 613), (1250, 700), (1979, 700),
                   dvert("pools", "left")),
              poly(dvert("pools", "right"), (2187, 944))))
    texts += [card("1", 1258, 650), card("N", 2152, 910)]
    # 18 versions: Assessment 1:N AssessmentBlueprint
    L.append((poly((907, 613), (620, 613), (620, 1136),
                   dvert("versions_legacy", "left")),
              poly(dvert("versions_legacy", "right"), (900, 1136),
                   (900, 1200), (600, 1200), (600, 1278))))
    texts += [card("1", 730, 625), card("N", 608, 1240)]
    # 19 instantiates: Session N:1 Assessment
    L.append((poly((1150, 613), (1150, 816), dvert("instantiates", "left")),
              poly(dvert("instantiates", "right"), (1530, 816),
                   (1530, 920), (1547, 920))))
    texts += [card("N", 1158, 780), card("1", 1500, 870)]
    # 20 uses: Session N:1 AssessmentBlueprint
    L.append((poly((1650, 997), (1650, 1024), dvert("uses", "right")),
              poly(dvert("uses", "left"), (500, 1024), (500, 1278))))
    texts += [card("N", 1658, 1015), card("1", 508, 1240)]

    for a, b in L:
        lines.append(a)
        lines.append(b)

    # legend -----------------------------------------------------------------
    shapes.append({"kind": "legend", "bbox": [560, 1522, 3000, 1633]})
    shapes.append({"kind": "legend_rect", "bbox": [808, 1555, 882, 1600]})
    shapes.append({"kind": "legend_diamond", "bbox": [1050, 1546, 1158, 1610]})
    shapes.append({"kind": "legend_key", "bbox": [1394, 1552, 1505, 1603]})
    shapes.append({"kind": "legend_legacy", "bbox": [2470, 1555, 2522, 1600]})
    texts += [
        mk_text("Entity", (902, 1570, 966, 1595), "legend"),
        mk_text("Relationship", (1180, 1569, 1323, 1595), "legend"),
        mk_text("key", (1435, 1570, 1465, 1591), "legend_key"),
        mk_text("Key attribute", (1525, 1569, 1676, 1595), "legend"),
        mk_text("1 = one, N / M = many", (1788, 1570, 2169, 1595),
                "legend_bold"),
        mk_text("(M : N = many-to-many)", (2183, 1570, 2365, 1594),
                "legend"),
        mk_text("Legacy table (historical rows only)",
                (2540, 1570, 2920, 1595), "legend"),
    ]

    trace = {"canvas": CANVAS, "shapes": shapes, "lines": lines,
             "texts": texts,
             "source": "Stage B content delta (content-delta-verified.md "
                       "section 8) on the Stage A measured coordinates"}
    with open(os.path.join(outdir, "trace.json"), "w", encoding="utf-8") as f:
        json.dump(trace, f, indent=1)
    print("entities %d, keys %d, diamonds %d, lines %d, texts %d" %
          (len(ENTS), len(KEY_ELLIPSES), len(DIAMONDS), len(lines),
           len(texts)))


if __name__ == "__main__":
    main()

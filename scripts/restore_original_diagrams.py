# -*- coding: utf-8 -*-
"""Restore the academic document figures to the original Final-ver1.3 media.

The owner requires 1:1 original diagram style.  This script replaces the image
part behind each existing figure in place, keeps the caption paragraph objects,
sets the original extent (so nothing is stretched) and rewrites only the caption
text needed to match the original figures.
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

import docx
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "docs/submission/final"
SOURCE = ROOT.parent / "Documents" / "Final-ver1.3"
OUT = FINAL / "verification" / "diagram-restore" / "original"

PROPOSAL = {
    "target": "C1SE.70_ProposalDocument_DBCAS_ver1.3.docx",
    "source": "C1SE.70_ProposalDocument_DBCAS_ver1.3.docx",
    "figures": [
        ("image2.png", 15.50, 11.50),
        ("image3.png", 15.50, 11.49),
        ("image4.png", 15.24, 15.05),
        ("image5.png", 15.50, 8.80),
    ],
    "captions": {
        "Figure 1: Agile delivery roadmap and official faculty milestones":
            "Figure 1: Agile Scrum Sprint Roadmap & Official Faculty Milestones",
    },
}

ARCHITECTURE = {
    "target": "C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx",
    "source": "C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx",
    "figures": [
        ("image2.png", 15.50, 16.39),
        ("image3.png", 15.50, 11.49),
        ("image4.png", 15.50, 14.32),
        ("image5.png", 20.32, 14.22),
        ("image6.png", 20.32, 14.22),
        ("image7.png", 22.76, 14.14),
        ("image8.png", 15.09, 13.99),
        ("image9.png", 24.20, 9.44),
        ("image10.png", 24.20, 9.44),
        ("image11.png", 21.88, 13.23),
        ("image12.png", 21.88, 13.23),
        ("image13.png", 21.88, 13.23),
        ("image14.png", 21.88, 13.23),
        ("image15.png", 21.88, 13.23),
        ("image16.png", 21.88, 13.23),
        ("image17.png", 21.88, 13.23),
        ("image18.png", 21.88, 13.23),
        ("image19.png", 21.88, 13.23),
        ("image20.png", 21.88, 13.23),
        ("image21.png", 21.88, 13.23),
    ],
    "captions": {
        "Figure 7. Entity relationship overview (1/2)":
            "Figure 7. Entity Relationship Diagram (1/2)",
        "Figure 7. Entity relationship index (2/2)":
            "Figure 7. Entity Relationship Diagram — additional tables (2/2)",
        "Figure 8. Entity relationship diagram — Identity and access (1/11)":
            "Figure 8. Table Relationship Diagram (1/11)",
        "Figure 8. Entity relationship diagram — Curriculum and concepts (2/11)":
            "Figure 8. Table Relationship Diagram (2/11)",
        "Figure 8. Entity relationship diagram — Question bank and generation (3/11)":
            "Figure 8. Table Relationship Diagram (3/11)",
        "Figure 8. Entity relationship diagram — Assessment and attempts (4/11)":
            "Figure 8. Table Relationship Diagram (4/11)",
        "Figure 8. Entity relationship diagram — Grading, results and competency (5/11)":
            "Figure 8. Table Relationship Diagram (5/11)",
        "Figure 8. Entity relationship diagram — Review workflow (6/11)":
            "Figure 8. Table Relationship Diagram (6/11)",
        "Figure 8. Entity relationship diagram — AI audit and retention (7/11)":
            "Figure 8. Table Relationship Diagram (7/11)",
        "Figure 8. Foreign-key ledger — rows 1–31 of 122 (8/11)":
            "Figure 8. Table Relationship Diagram (8/11)",
        "Figure 8. Foreign-key ledger — rows 32–62 of 122 (9/11)":
            "Figure 8. Table Relationship Diagram (9/11)",
        "Figure 8. Foreign-key ledger — rows 63–92 of 122 (10/11)":
            "Figure 8. Table Relationship Diagram (10/11)",
        "Figure 8. Foreign-key ledger — rows 93–122 of 122 (11/11)":
            "Figure 8. Table Relationship Diagram (11/11)",
    },
}

DATABASE = {
    "target": "C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx",
    "source": "C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx",
    "figures": [
        ("image3.png", 24.20, 9.44),
        ("image4.png", 24.20, 9.44),
        ("image5.png", 24.03, 14.53),
        ("image6.png", 24.03, 14.53),
        ("image7.png", 24.03, 14.53),
        ("image8.png", 24.03, 14.53),
        ("image9.png", 24.03, 14.53),
        ("image10.png", 24.03, 14.53),
        ("image11.png", 24.03, 14.53),
        ("image12.png", 24.03, 14.53),
        ("image13.png", 24.03, 14.53),
        ("image14.png", 24.03, 14.53),
        ("image15.png", 24.03, 14.53),
    ],
    "captions": {
        "Figure 1: Entity relationship overview (1/2)":
            "Figure 1: Entity Relationship Diagram (1/2)",
        "Figure 1: Entity relationship index (2/2)":
            "Figure 1: Entity Relationship Diagram — additional tables (2/2)",
        "Figure 2: Entity relationship diagram — Identity and access (1/11)":
            "Figure 2: Table Relationship Diagram (1/11)",
        "Figure 2: Entity relationship diagram — Curriculum and concepts (2/11)":
            "Figure 2: Table Relationship Diagram (2/11)",
        "Figure 2: Entity relationship diagram — Question bank and generation (3/11)":
            "Figure 2: Table Relationship Diagram (3/11)",
        "Figure 2: Entity relationship diagram — Assessment and attempts (4/11)":
            "Figure 2: Table Relationship Diagram (4/11)",
        "Figure 2: Entity relationship diagram — Grading, results and competency (5/11)":
            "Figure 2: Table Relationship Diagram (5/11)",
        "Figure 2: Entity relationship diagram — Review workflow (6/11)":
            "Figure 2: Table Relationship Diagram (6/11)",
        "Figure 2: Entity relationship diagram — AI audit and retention (7/11)":
            "Figure 2: Table Relationship Diagram (7/11)",
        "Figure 2: Foreign-key ledger — rows 1–31 of 122 (8/11)":
            "Figure 2: Table Relationship Diagram (8/11)",
        "Figure 2: Foreign-key ledger — rows 32–62 of 122 (9/11)":
            "Figure 2: Table Relationship Diagram (9/11)",
        "Figure 2: Foreign-key ledger — rows 63–92 of 122 (10/11)":
            "Figure 2: Table Relationship Diagram (10/11)",
        "Figure 2: Foreign-key ledger — rows 93–122 of 122 (11/11)":
            "Figure 2: Table Relationship Diagram (11/11)",
    },
    "intro_old_prefix": "Figures 1 and 2 show the domain overview",
    "intro_new": (
        "Figure 1 is the conceptual model: the many-to-many relationships (assigned, maps to, tagged with, "
        "targets) are implemented by the junction tables AccountRole, CLOConcept, QuestionConcept and the "
        "legacy AssessmentConcept shown in Figure 2. SystemSetting stores historical/operational platform "
        "values; result release is no longer selectable. The four legacy tables (Assessment, "
        "AssessmentConcept, AssessmentQuestion and AssessmentBlueprint) are marked as historical rows only. "
        "Tables added by later migrations (account identity, role audit, OAuth handoff, login throttling, "
        "concept prerequisites, question translations, the frozen session question plan, session start-request "
        "bindings, evaluation records, grading jobs, grade reviews, grade-edit audit, result-release events, "
        "refresh sessions, system settings, password-reset tokens and password-reset audit) are documented in "
        "the sections below, all 67 tables appear across the 11 pages of Figure 2, and Appendix A documents "
        "the additional tables in detail."
    ),
}


def replace_image(part, blob: bytes):
    part._blob = blob
    try:
        part._image = None
    except Exception:
        pass


def set_extent(drawing, width_cm, height_cm):
    cx = str(int(round(width_cm * 360000)))
    cy = str(int(round(height_cm * 360000)))
    for el in drawing.iter(qn("wp:extent")):
        el.set("cx", cx)
        el.set("cy", cy)
    for el in drawing.iter(qn("a:ext")):
        el.set("cx", cx)
        el.set("cy", cy)


def set_paragraph_text(paragraph, text):
    runs = paragraph.runs
    if not runs:
        paragraph.add_run(text)
        return
    runs[0].text = text
    for run in runs[1:]:
        run.text = ""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for spec in (PROPOSAL, ARCHITECTURE, DATABASE):
        target_path = FINAL / spec["target"]
        source_path = SOURCE / spec["source"]
        source_zip = zipfile.ZipFile(source_path)
        doc = docx.Document(str(target_path))
        image_paras = []
        for p in doc.paragraphs:
            for blip in p._p.iter(qn("a:blip")):
                rid = blip.get(qn("r:embed"))
                if rid and rid in doc.part.rels:
                    image_paras.append((p, blip, doc.part.rels[rid].target_part))
                    break
        # skip the cover logo: body figures follow the first heading
        first_heading = next(i for i, p in enumerate(doc.paragraphs)
                             if p.style.name.startswith("Heading 1"))
        para_index = {id(p._p): i for i, p in enumerate(doc.paragraphs)}
        body = [(p, blip, part) for p, blip, part in image_paras
                if para_index[id(p._p)] > first_heading]
        if len(body) != len(spec["figures"]):
            raise SystemExit(f"{spec['target']}: found {len(body)} body figures, expected {len(spec['figures'])}")
        for (p, blip, part), (media, w, h) in zip(body, spec["figures"]):
            blob = source_zip.read("word/media/" + media)
            replace_image(part, blob)
            drawing = blip.getparent()
            while drawing is not None and drawing.tag != qn("w:drawing"):
                drawing = drawing.getparent()
            if drawing is None:
                raise SystemExit(f"{spec['target']}: no drawing for {media}")
            set_extent(drawing, w, h)
            # save the original and restored image for the audit contact sheet
            name = spec["target"].replace("C1SE.70_", "").replace("_DBCAS_ver1.3.docx", "")
            (OUT / name).mkdir(parents=True, exist_ok=True)
            (OUT / name / media).write_bytes(blob)
        # caption text
        for old, new in spec["captions"].items():
            found = False
            for p in doc.paragraphs:
                if p.text.strip() == old:
                    set_paragraph_text(p, new)
                    found = True
                    break
            if not found:
                print(f"caption not found in {spec['target']}: {old}")
        # database intro paragraph
        if spec.get("intro_old_prefix"):
            for p in doc.paragraphs:
                if p.text.startswith(spec["intro_old_prefix"]):
                    set_paragraph_text(p, spec["intro_new"])
                    break
        doc.save(str(target_path))
        print(f"{spec['target']}: restored {len(body)} figures")


if __name__ == "__main__":
    main()

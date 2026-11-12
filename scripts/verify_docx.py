# -*- coding: utf-8 -*-
"""Programmatic verification of the three in-place v1.2 Word documents.

    python scripts/verify_docx.py

Checks, from the actual .docx packages:
  - every document opens and still contains its original media;
  - version/date/revision metadata is 1.2 / 08-11-2026;
  - the Database Design documents exactly 41 tables and 293 columns, matching
    docs/qa/schema-introspection.json (names, types, nullability);
  - the Table Overview lists all 41 tables;
  - no retired formal/adaptive statements or Vietnamese body text remains;
  - all three documents state 41 tables and mandatory administrator review;
  - the four legacy tables are explicitly marked in Architecture/Database.
"""
import json
import re
import sys
import zipfile
from pathlib import Path

from extract_docx_inventory import extract
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
ACA = ROOT / "docs/academic"
SCHEMA = json.load(open(ROOT / "docs/qa/schema-introspection.json", encoding="utf-8"))
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
q = lambda t: f"{{{W}}}{t}"

FILES = [
    ACA / "C1SE.70_ProposalDocument_DBCAS_ver1.2.docx",
    ACA / "C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx",
    ACA / "C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx",
]
EXPECTED_MEDIA = {
    "ProposalDocument": 5,
    "ArchitectureDesign": 14,
    "DatabaseDesign": 8,
}
LEGACY = ["assessment", "assessment_concept", "assessment_question", "assessment_blueprint"]

problems = []
checks = 0


def require(label, ok, detail=""):
    global checks
    checks += 1
    if not ok:
        problems.append(f"{label}: {detail}")


def text_of(el):
    return "".join((n.text or "") for n in el.iter(q("t"))).strip()


def base_type(c):
    t = c["type"].lower()
    if t == "array":
        return (c.get("udt") or "_text").lstrip("_").upper() + "[]"
    if t in ("character varying", "character"):
        return f"VARCHAR({c['max_length']})" if c.get("max_length") else "VARCHAR"
    if t == "timestamp with time zone":
        return "TIMESTAMPTZ"
    if t == "timestamp without time zone":
        return "TIMESTAMP"
    if t == "numeric":
        return f"NUMERIC({c['numeric_precision']},{c['numeric_scale']})"
    return {"integer": "INT", "bigint": "BIGINT", "boolean": "BOOLEAN", "text": "TEXT",
            "jsonb": "JSONB", "date": "DATE", "smallint": "SMALLINT"}.get(t, t.upper())


def norm(t):
    return t.strip().upper().replace(" ", "")


def doc_sections(docx):
    """Heading2 -> rows of the following six-column data table."""
    with zipfile.ZipFile(docx) as z:
        root = etree.fromstring(z.read("word/document.xml"))
    body = root.find(q("body"))
    current = None
    sections = {}
    for el in body:
        if el.tag == q("p"):
            ppr = el.find(q("pPr"))
            style = ppr.find(q("pStyle")).get(q("val")) if ppr is not None and ppr.find(q("pStyle")) is not None else None
            if style == "Heading2":
                current = text_of(el)
        elif el.tag == q("tbl") and current:
            rows = [[text_of(tc) for tc in tr.findall(q("tc"))] for tr in el.findall(q("tr"))]
            if rows and rows[0] and rows[0][0] == "Attributes":
                sections[current] = rows
            current = None
    return sections


def main():
    texts = {}
    for f in FILES:
        require(f"{f.name} exists", f.exists())
        d = extract(f)
        t = "\n".join(p["text"] for p in d["paragraphs"])
        t += "\n" + "\n".join(" ".join(row) for tb in d["tables"] for row in tb)
        texts[f.name] = t
        stem = f.name.split("_")[1]
        with zipfile.ZipFile(f) as z:
            media = [n for n in z.namelist() if n.startswith("word/media/")]
            xml_root = etree.fromstring(z.read("word/document.xml"))
        duplicate_captions = []
        for paragraph in xml_root.iter(q("p")):
            prefix = ""
            for node in paragraph.iter():
                if node.tag == q("t"):
                    prefix += node.text or ""
                elif node.tag == q("instrText") and re.search(r"\bSEQ\s+Table\b", node.text or ""):
                    if re.match(r"Table\s+\d+\.", prefix) and r"\h" not in (node.text or ""):
                        duplicate_captions.append(prefix)
                    break
        require(f"no duplicate caption sequence {stem}", not duplicate_captions,
                "; ".join(duplicate_captions))
        require(f"media count {stem}", len(media) == EXPECTED_MEDIA[stem], f"{len(media)}")
        require(f"Version 1.2 {stem}", "Version 1.2" in t)
        require(f"document date {stem}", "November 8th, 2026" in t or "08/11/2026" in t)
        require(f"revision row {stem}", "1.2" in t and "08/11/2026" in t)
        require(f"41 tables {stem}", "41 tables" in t)
        require(f"mandatory review {stem}", bool(re.search(
            r"administrator (review|approval)|review and approval|admin review|admin approval",
            t, re.I)))
        require(f"OAuth sign-up {stem}", bool(re.search(r"Google(?: and | or | / |/)GitHub", t, re.I))
                and "sign-up" in t.lower())
        require(f"OAuth rotating sessions {stem}", "access/refresh" in t.lower())
        if stem != "DatabaseDesign":
            require(f"practice count {stem}", "1–20" in t or "1 to 20" in t or "1 - 20" in t)
            require(f"OAuth discovery {stem}", "Login and Register" in t and "unconfigured provider" in t.lower())

    alltext = "\n".join(texts.values())

    retired = [
        "36 tables", "13-question", "13 questions", "60-minute contract",
        "10 MCQ / 2 SQL / 1 Essay", "10 MCQ / 2 SQL / 1 essay",
        "FORMAL session", "FORMAL (", "PRACTICE with an exact",
        "Configure Adaptive Assessment", "Take a Personalized Adaptive",
        "Adaptive Engine Service", "Exam Interface Usability",
        "The change is stored once and applies to every subsequent result publication.",
        "The setting row records updated_by and updated_at.",
        "Invalid setting value -- Display a validation error",
        "Unknown setting key -- Reject the request",
    ]
    found = [r for r in retired if r in alltext]
    require("no retired statements", not found, ",".join(found))

    # English only: Vietnamese-specific letters (not shared Latin accents).
    vi = set("ăâđêôơưĂÂĐÊÔƠƯạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ"
             "ẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸ")
    hits = sorted({c for c in alltext if c in vi})
    require("English only", not hits, "".join(hits))

    # Data dictionary exactness.
    db = FILES[2]
    sections = doc_sections(db)
    real = {t["table"]: t for t in SCHEMA["tables"]}
    key = lambda s: s.lower().replace("_", "").replace(" ", "")
    by_key = {key(n): n for n in real}
    require("data-dictionary sections", len(sections) == len(real), f"{len(sections)}")
    wrong = []
    seen = set()
    for heading, rows in sections.items():
        name = by_key.get(key(heading))
        if not name:
            wrong.append("unknown section " + heading)
            continue
        seen.add(name)
        doc = {r[0]: (r[1], r[2]) for r in rows[1:] if r and r[0]}
        for c in real[name]["columns"]:
            if c["name"] not in doc:
                wrong.append(f"{name}.{c['name']} missing")
            else:
                dt, dn = doc[c["name"]]
                if norm(dt) != norm(base_type(c)):
                    wrong.append(f"{name}.{c['name']} type {dt}!={base_type(c)}")
                if (dn.lower().startswith("not")) == c["nullable"]:
                    wrong.append(f"{name}.{c['name']} null={dn}")
        for c in doc:
            if c not in {x["name"] for x in real[name]["columns"]}:
                wrong.append(f"{name}.{c} extra")
    require("data-dictionary exact", not wrong and len(seen) == 41, "; ".join(wrong[:8]))
    require("documented columns 293", sum(len(r) - 1 for r in sections.values()) == 293)

    # Table Overview completeness.
    overview = None
    for tb in extract(db)["tables"]:
        if tb and tb[0] and tb[0][0] == "Table Name":
            overview = tb
            break
    require("Table Overview present", overview is not None)
    if overview:
        listed = [r[0] for r in overview[1:] if r and r[0]]
        require("Table Overview 41 rows", len(listed) == 41, f"{len(listed)}")
        listed_keys = {key(n) for n in listed}
        require("Table Overview names", all(key(n) in listed_keys for n in real), "missing names")

    # Legacy marking.
    display = {"assessment": "Assessment", "assessment_concept": "AssessmentConcept",
               "assessment_question": "AssessmentQuestion",
               "assessment_blueprint": "AssessmentBlueprint"}
    for n in LEGACY:
        require(f"legacy {n} in Database", display[n] in texts[db.name])
        require(f"legacy {n} in Architecture",
                display[n] in texts["C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx"])
    for name in ["C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx",
                 "C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx"]:
        require(f"legacy wording {name[:20]}", "legacy" in texts[name].lower()
                and "historical" in texts[name].lower())

    print(f"verify_docx: {checks} assertions, {len(problems)} failures")
    print(f"  files: {[f.name for f in FILES]}")
    print(f"  database sections: {len(sections)}; columns: {sum(len(r) - 1 for r in sections.values())}")
    if problems:
        for p in problems:
            print("FAIL:", p)
        sys.exit(1)
    print("PASS: in-place v1.2 documents match the schema and language/fact rules")


if __name__ == "__main__":
    main()

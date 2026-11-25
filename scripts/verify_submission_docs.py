# -*- coding: utf-8 -*-
"""Verify the five C1SE.70 DBCAS ver1.3 Word deliverables.

    python scripts/verify_submission_docs.py            # check + write report
    python scripts/verify_submission_docs.py --only proposal,database

Checks, all read-only:
  * file set and file names
  * A4 page size and 3.5 / 2 / 2 / 2 cm margins, per section
  * Normal style: Times New Roman 13 pt, line spacing 1.5
  * every body paragraph resolves to 13 pt and 1.5 spacing; every other size is
    listed as a documented exception (tables, captions, code, cover, header)
  * core properties: author and last modified by "Do, Nguyen Quoc"
  * table of contents field, header and footer present
  * measured numbers in the text agree with the repository
  * obsolete terms and SRS references are absent
  * traceability: Proposal sections, FR ids, Database tables
Writes docs/submission/final/verification/verification-report.{md,json} and
docs/submission/final/TRACEABILITY.md.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import OrderedDict, defaultdict
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "docs" / "submission" / "final"
REPORT_DIR = FINAL / "verification"

EXPECTED = OrderedDict([
    ("proposal", "C1SE.70_ProposalDocument_DBCAS_ver1.3.docx"),
    ("architecture", "C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx"),
    ("database", "C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx"),
    ("codestandards", "C1SE.70_CodeStandards_DBCAS_ver1.3.docx"),
    ("technicalreport", "C1SE.70_TechnicalReport_DBCAS_ver1.3.docx"),
])

PROPOSAL_SECTIONS = [
    "1. Project Title", "2. Team Members", "3. Supervisor(s)",
    "4. Problem Statement", "5. Survey / Existing Solutions",
    "6. Objectives and Scope", "7. Key Features & Requirements",
    "8. Constraints and Assumptions", "9. Target Users / Stakeholders",
    "10. Technology Stack", "11. Methodology & Development Plan",
    "12. System Architecture Overview", "13. Potential Risks and Mitigation Strategies",
    "14. Expected Outcomes / Deliverables", "15. References",
]

OBSOLETE = ["OpenRouter", "free model", "66 tables", "27 migrations",
            "1-20 questions", "five destinations", "OWNER UNKNOWN"]

MARGINS_CM = {"left": 3.5, "right": 2.0, "top": 2.0, "bottom": 2.0}
TOLERANCE_CM = 0.05
BODY_PT = 13.0
LINE = 1.5

checks: list[dict] = []
exceptions: list[dict] = []


def check(cid, ok, detail=""):
    checks.append({"id": cid, "status": "PASS" if ok else "FAIL",
                   "detail": detail})
    return ok


def walk(doc):
    """Yield ('p', paragraph) and ('tbl', table) in document order."""
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    body = doc.element.body
    for child in body.iterchildren():
        if child.tag.endswith('}p'):
            yield "p", Paragraph(child, doc)
        elif child.tag.endswith('}tbl'):
            yield "tbl", Table(child, doc)


def effective_size(run, paragraph):
    if run.font.size is not None:
        return run.font.size.pt
    style = paragraph.style
    while style is not None:
        if style.font.size is not None:
            return style.font.size.pt
        style = style.base_style
    return None


def paragraph_spacing(paragraph):
    value = paragraph.paragraph_format.line_spacing
    if value is not None:
        return value
    style = paragraph.style
    while style is not None:
        if style.paragraph_format.line_spacing is not None:
            return style.paragraph_format.line_spacing
        style = style.base_style
    return None


def doc_text(doc):
    parts = []
    for kind, item in walk(doc):
        if kind == "p":
            text = item.text.strip()
            if text:
                parts.append(text)
        else:
            for row in item.rows:
                cells = [c.text.strip() for c in row.cells]
                if any(cells):
                    parts.append(" | ".join(cells))
    return "\n".join(parts)


def has_field(doc, code):
    xml = doc.element.xml
    headers = "".join(p._element.xml for s in doc.sections
                      for p in s.header.paragraphs)
    footers = "".join(p._element.xml for s in doc.sections
                      for p in s.footer.paragraphs)
    return code in xml or code in headers or code in footers


def verify_layout(key, path):
    doc = Document(str(path))
    heading_texts = []
    body_sizes = defaultdict(int)
    bad_body = []
    spacing_bad = []
    exception_counts = defaultdict(int)

    table_ids = set()
    for tbl in doc.tables:
        table_ids.add(id(tbl._tbl))

    parent = {}
    for kind, item in walk(doc):
        if kind == "tbl":
            for row in item.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        parent[id(p._p)] = "table"

    seen_heading = False
    for paragraph in doc.paragraphs:
        style_name = paragraph.style.name if paragraph.style else ""
        if style_name.startswith("Heading 1"):
            seen_heading = True
        in_table = parent.get(id(paragraph._p)) == "table"
        toc_label = paragraph.text.strip() in ("Table of Contents", "List of Tables", "List of Figures")
        caption_label = bool(re.match(r"^(Figure|Table)\s+\d+", paragraph.text.strip())) and len(paragraph.text.strip()) < 220
        for run in paragraph.runs:
            if not run.text.strip():
                continue
            size = effective_size(run, paragraph)
            context = "table" if in_table else style_name
            if not in_table and seen_heading and not toc_label and not caption_label and style_name in ("Normal", "List Bullet"):
                body_sizes[size] += 1
                if size is None or abs(size - BODY_PT) > 0.01:
                    bad_body.append((paragraph.text[:60], size))
                spacing = paragraph_spacing(paragraph)
                if spacing is None or abs(float(spacing) - LINE) > 0.01:
                    spacing_bad.append((paragraph.text[:60], spacing))
            else:
                exception_counts[f"{context}:{size}"] += 1
        if style_name.startswith("Heading 1"):
            heading_texts.append(paragraph.text.strip())

    sections = doc.sections
    section_info = []
    for section in sections:
        section_info.append({
            "width_cm": round(section.page_width.cm, 2),
            "height_cm": round(section.page_height.cm, 2),
            "left": round(section.left_margin.cm, 2),
            "right": round(section.right_margin.cm, 2),
            "top": round(section.top_margin.cm, 2),
            "bottom": round(section.bottom_margin.cm, 2),
        })

    check(f"{key}: file opens", True)
    def is_a4(s):
        portrait = abs(s["width_cm"] - 21.0) <= 0.05 and abs(s["height_cm"] - 29.7) <= 0.05
        landscape = abs(s["width_cm"] - 29.7) <= 0.05 and abs(s["height_cm"] - 21.0) <= 0.05
        return portrait or landscape
    check(f"{key}: page size A4 (portrait or landscape)",
          all(is_a4(s) for s in section_info),
          json.dumps(section_info))
    margin_ok = all(
        abs(s["left"] - MARGINS_CM["left"]) <= TOLERANCE_CM
        and abs(s["right"] - MARGINS_CM["right"]) <= TOLERANCE_CM
        and abs(s["top"] - MARGINS_CM["top"]) <= TOLERANCE_CM
        and abs(s["bottom"] - MARGINS_CM["bottom"]) <= TOLERANCE_CM
        for s in section_info)
    check(f"{key}: margins 3.5/2/2/2 cm", margin_ok,
          json.dumps([{k: s[k] for k in ("left", "right", "top", "bottom")}
                      for s in section_info]))

    normal = doc.styles["Normal"]
    normal_size = normal.font.size.pt if normal.font.size else None
    check(f"{key}: Normal 13 pt", normal_size is not None and abs(normal_size - 13) < 0.01,
          f"{normal_size}")
    normal_font = normal.font.name
    check(f"{key}: Normal Times New Roman", normal_font == "Times New Roman",
          str(normal_font))
    normal_line = normal.paragraph_format.line_spacing
    check(f"{key}: Normal line spacing 1.5",
          normal_line is not None and abs(float(normal_line) - 1.5) < 0.01,
          str(normal_line))
    check(f"{key}: body runs are 13 pt", not bad_body,
          f"{len(bad_body)} offending runs; first: {bad_body[:3]}")
    check(f"{key}: body spacing 1.5", not spacing_bad,
          f"{len(spacing_bad)} offending paragraphs; first: {spacing_bad[:3]}")

    core = doc.core_properties
    check(f"{key}: author", core.author == "Do, Nguyen Quoc", str(core.author))
    check(f"{key}: last modified by",
          core.last_modified_by == "Do, Nguyen Quoc", str(core.last_modified_by))

    check(f"{key}: table of contents field", has_field(doc, 'TOC \\o'))
    header_text = " ".join(p.text for s in sections for p in s.header.paragraphs)
    footer_text = " ".join(p.text for s in sections for p in s.footer.paragraphs)
    check(f"{key}: header", "C1SE.70" in header_text, header_text.strip())
    check(f"{key}: footer page field", has_field(doc, "PAGE"), footer_text.strip())

    for ctx, count in sorted(exception_counts.items()):
        exceptions.append({"document": key, "context_size": ctx,
                           "runs": count})
    return {
        "headings": heading_texts,
        "text": doc_text(doc),
        "sections": section_info,
        "body_runs": sum(body_sizes.values()),
        "body_sizes": {str(k): v for k, v in body_sizes.items()},
        "exception_runs": dict(exception_counts),
    }


def measure_repository():
    intro = json.loads((ROOT / "docs" / "diagrams" / "schema-028"
                        / "schema-introspection.json").read_text(encoding="utf-8"))
    tables = [t["table"] for t in intro["tables"]]
    columns = sum(len(t["columns"]) for t in intro["tables"])
    measured = {
        "tables": len(tables),
        "columns": columns,
        "foreign_keys": len(intro["foreign_keys"]),
        "indexes": len(intro["indexes"]),
        "migrations": len(intro["migrations"]),
        "table_names": tables,
        "column_counts": {t["table"]: len(t["columns"]) for t in intro["tables"]},
        "column_names": sorted({c["name"] for t in intro["tables"]
                                for c in t["columns"]}),
    }
    sys.path.insert(0, str(ROOT / "backend"))
    try:
        from app.main import app  # noqa: E402
        spec = app.openapi()
        measured["paths"] = len(spec["paths"])
        measured["operations"] = sum(
            1 for item in spec["paths"].values()
            for method in item if method in ("get", "post", "put", "patch", "delete"))
    except Exception as error:  # pragma: no cover - reported, not hidden
        measured["openapi_error"] = repr(error)
    facts = json.loads((ROOT / "docs" / "qa" / "project-facts.json")
                       .read_text(encoding="utf-8"))
    measured["frontend_routes"] = len(facts["frontend_routes"])
    return measured


def content_checks(docs, measured):
    all_text = {key: value["text"] for key, value in docs.items()}

    for key, text in all_text.items():
        for term in OBSOLETE:
            check(f"{key}: no obsolete term '{term}'", term not in text, "")
        check(f"{key}: no SRS owner reference", "SRS" not in text, "")

    # headings of the proposal, in order
    proposal_headings = docs["proposal"]["headings"]
    check("proposal: 15 required sections in order",
          proposal_headings[:15] == PROPOSAL_SECTIONS,
          json.dumps(proposal_headings[:15], ensure_ascii=False))

    # numeric claims
    patterns = {
        "tables": (r"(\d+)\s+(?:application\s+)?tables", measured["tables"]),
        "migrations": (r"(\d+)\s+(?:forward(?:-only)?\s+)?migrations",
                       measured["migrations"]),
        "foreign_keys": (r"(\d+)\s+foreign keys", measured["foreign_keys"]),
        "indexes": (r"(\d+)\s+indexes", measured["indexes"]),
    }
    for key, text in all_text.items():
        headings = set(docs[key]["headings"])
        body = "\n".join(line for line in text.split("\n") if line not in headings)
        for label, (pattern, expected) in patterns.items():
            found = {int(m) for m in re.findall(pattern, body)}
            bad = {value for value in found if value != expected}
            check(f"{key}: {label} claims match measured {expected}",
                  not bad, f"found={sorted(found)}")
        for claimed in re.findall(r"(\d+)\s+API paths", body):
            check(f"{key}: API path claim {claimed}",
                  int(claimed) == measured["paths"], str(measured["paths"]))
        for claimed in re.findall(r"(\d+)\s+operations", body):
            check(f"{key}: operation claim {claimed}",
                  int(claimed) == measured["operations"], str(measured["operations"]))

    # dictionary blocks: captions "Table N: Database Design (Name)" followed by
    # the column table. The baseline uses CamelCase for the 41 core tables and
    # the physical snake_case name for the 26 Appendix A tables.
    database_text = all_text["database"]
    database_doc = Document(str(FINAL / EXPECTED["database"]))
    pending = None
    found_tables = {}
    for kind, item in walk(database_doc):
        if kind == "p":
            match = re.match(r"Table (?:A\.)?\d+: Database Design \((.+)\)",
                             item.text.strip())
            if match:
                pending = match.group(1).strip()
        elif pending is not None:
            found_tables[pending] = len(item.rows) - 1
            pending = None

    def normalized(name):
        return re.sub(r"[^a-z0-9]", "", name.lower())

    schema_by_key = {normalized(name): name for name in measured["table_names"]}
    canonical = {}
    for name, count in found_tables.items():
        key = normalized(name)
        canonical[schema_by_key.get(key, name)] = count
    check("database: every table has a dictionary block",
          set(canonical) == set(measured["table_names"]),
          f"missing={sorted(set(measured['table_names']) - set(canonical))} "
          f"extra={sorted(set(canonical) - set(measured['table_names']))}")
    wrong = {name: (count, measured["column_counts"].get(name))
             for name, count in canonical.items()
             if measured["column_counts"].get(name) != count}
    check("database: every column count matches", not wrong, json.dumps(wrong))

    # FR traceability: proposal defines, architecture uses, no orphan ids
    proposal_fr = set(re.findall(r"FR-(\d\d)", all_text["proposal"]))
    architecture_fr = set(re.findall(r"FR-(\d\d)", all_text["architecture"]))
    check("traceability: every Architecture FR exists in the Proposal",
          architecture_fr <= proposal_fr,
          f"orphans={sorted(architecture_fr - proposal_fr)}")
    check("traceability: every Proposal FR appears in the Architecture",
          proposal_fr <= architecture_fr,
          f"missing={sorted(proposal_fr - architecture_fr)}")
    nfr = set(re.findall(r"NFR-(\d\d)", all_text["proposal"]))
    check("proposal: at least nine NFRs", len(nfr) >= 9, str(sorted(nfr)))

    # every *_id token mentioned in the Database document must be a real column
    known_columns = set(measured["column_names"])
    known_tables = set(measured["table_names"])
    mentioned_ids = set(re.findall(r"\b([a-z][a-z0-9_]*_id)\b", database_text))
    invented = mentioned_ids - known_columns - known_tables
    check("database: no invented column names", not invented,
          f"{sorted(invented)[:5]}")
    return {"proposal_fr": sorted(proposal_fr),
            "architecture_fr": sorted(architecture_fr),
            "nfr": sorted(nfr),
            "database_tables": len(canonical),
            "database_blocks": canonical}


def page_counts():
    path = REPORT_DIR / "page-counts.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_traceability(docs, measured, content):
    lines = ["# Traceability matrix", "",
             "Generated by `scripts/verify_submission_docs.py`. Do not edit by "
             "hand.", "",
             "## Documents", "",
             "| Document | File | Sections | Tables in document |",
             "|---|---|---:|---:|"]
    for key, name in EXPECTED.items():
        doc = Document(str(FINAL / name))
        lines.append(f"| {key} | `{name}` | {len(docs[key]['headings'])} | "
                     f"{len(doc.tables)} |")
    lines += ["", "## Functional requirements", "",
              "| FR | In Proposal | In Architecture |", "|---|---|---|"]
    for fr in sorted(set(content["proposal_fr"]) | set(content["architecture_fr"])):
        lines.append(f"| FR-{fr} | "
                     f"{'yes' if fr in content['proposal_fr'] else 'no'} | "
                     f"{'yes' if fr in content['architecture_fr'] else 'no'} |")
    lines += ["", "## Schema tables", "",
              f"Every table in `db/schema.sql` must have a dictionary block in "
              f"the Database Design document. Measured: "
              f"{len(measured['table_names'])} tables.", "",
              "| Table | Columns | In Database document |", "|---|---:|---|"]
    blocks = content.get("database_blocks", {})
    for name in measured["table_names"]:
        lines.append(f"| `{name}` | {measured['column_counts'][name]} | "
                     f"{'yes' if name in blocks else 'MISSING'} |")
    lines += ["", "## Features", "",
              "| Feature | Documented in Proposal | Referenced in Architecture |",
              "|---|---|---|"]
    for index in range(1, 8):
        lines.append(f"| F{index} | "
                     f"{'yes' if f'F{index}' in docs['proposal']['text'] else 'no'} | "
                     f"{'yes' if f'FR-0{index}' in docs['architecture']['text'] else 'no'} |")
    (FINAL / "TRACEABILITY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", default="")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    wanted = {k.strip() for k in args.only.split(",") if k.strip()}

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    check("file set", True, "")
    for key, name in EXPECTED.items():
        path = FINAL / name
        if wanted and key not in wanted:
            continue
        if not check(f"{key}: file exists", path.exists(), name):
            continue
        with zipfile.ZipFile(path) as archive:
            broken = archive.testzip()
        check(f"{key}: package readable", broken is None, str(broken))

    docs = {}
    for key, name in EXPECTED.items():
        if wanted and key not in wanted:
            continue
        path = FINAL / name
        if not path.exists():
            continue
        docs[key] = verify_layout(key, path)

    extra = sorted(p.name for p in FINAL.glob("*.docx")
                   if p.name not in EXPECTED.values())
    check("final directory holds only the five documents", not extra,
          json.dumps(extra))

    measured = measure_repository()
    content = {}
    if set(docs) >= {"proposal", "architecture", "database"}:
        content = content_checks(docs, measured)
        write_traceability(docs, measured, content)

    pages = page_counts()
    if pages:
        for key, name in EXPECTED.items():
            if name in pages:
                check(f"{key}: page count recorded", pages[name] > 0,
                      str(pages[name]))

    failed = [c for c in checks if c["status"] == "FAIL"]
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "verification-report.json").write_text(
        json.dumps({"checks": checks, "exceptions": exceptions,
                    "measured": {k: v for k, v in measured.items()
                                 if k not in ("table_names", "column_counts",
                                              "column_names")},
                    "content": content, "pages": pages},
                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# Submission document verification", "",
             f"Documents checked: {len(docs)}; assertions: {len(checks)}; "
             f"failures: {len(failed)}.", ""]
    lines += ["| Assertion | Result | Detail |", "|---|---|---|"]
    for item in checks:
        detail = str(item["detail"]).replace("|", "\\|")[:160]
        lines.append(f"| {item['id']} | {item['status']} | {detail} |")
    lines += ["", "## Documented size and spacing exceptions", "",
              "| Document | Context:size (pt) | Runs |", "|---|---|---:|"]
    for item in exceptions:
        lines.append(f"| {item['document']} | {item['context_size']} | "
                     f"{item['runs']} |")
    (REPORT_DIR / "verification-report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")

    if not args.quiet:
        print(f"submission documents: {len(docs)} checked, {len(checks)} "
              f"assertions, {len(failed)} failures")
        if measured.get("openapi_error"):
            print("OpenAPI:", measured["openapi_error"])
        for item in failed:
            print("FAIL:", item["id"], "-", item["detail"])
        print("report:", (REPORT_DIR / "verification-report.md").relative_to(ROOT))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

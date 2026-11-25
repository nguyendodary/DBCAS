# -*- coding: utf-8 -*-
"""Build the four DBCAS ver1.3 Word deliverables from preserved review copies.

The source packages in docs/submission are never modified.  The generator keeps
their media, fields, covers and package parts, applies explicit fact corrections,
normalizes the shared FITAI interpretation, and writes only to a separate output
directory (Documents/Final-ver1.3 by default).

    py scripts/build_ver13_documents.py
    py scripts/build_ver13_documents.py --audit-only
    py scripts/build_ver13_documents.py --metadata-only

SRS naming note: no authoritative C1SE.70 SRS filename exists in the repository
or supplied workspace.  The fallback C1SE.70_SRS_DBCAS_ver1.3.docx follows the
three academic C1SE.70 names without inventing a different document type.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import posixpath
import subprocess
import sys
import zipfile
from pathlib import Path

from lxml import etree

from docx_inplace import apply_edits
from docs_qa_guard import ensure_safe_output

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "docs" / "submission"
DEFAULT_OUTPUT = ROOT.parent / "Documents" / "Final-ver1.3"
VERSION = "ver1.3"
VISIBLE_VERSION = "1.3"
REVISION_DATE = "25/11/2026"
COVER_DATE = "November 25th, 2026"
CREATOR = "Do, Nguyen Quoc"
GROUP = "C1SE.70"
PROJECT = "DBCAS"
TIMESTAMP = "2026-11-25T00:00:00Z"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC = "http://purl.org/dc/elements/1.1/"
DCTERMS = "http://purl.org/dc/terms/"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
EP = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
VT = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
CUSTOM = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
NS = {"w": W, "r": R}

DOCUMENTS = {
    "ProposalDocument": {
        "source": "Proposal.docx",
        "filename": "C1SE.70_ProposalDocument_DBCAS_ver1.3.docx",
        "title": "Project Proposal Document",
        "header": "PROPOSAL DOCUMENT",
    },
    "ArchitectureDesign": {
        "source": "Architecture.docx",
        "filename": "C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx",
        "title": "Architecture Design Document",
        "header": "ARCHITECTURE DESIGN",
    },
    "DatabaseDesign": {
        "source": "Database.docx",
        "filename": "C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx",
        "title": "Database Design Document",
        "header": "DATABASE DESIGN",
    },
    "SRS": {
        "source": "SRS.docx",
        "filename": "C1SE.70_SRS_DBCAS_ver1.3.docx",
        "title": "Software Requirements Specification",
        "header": "SOFTWARE REQUIREMENTS SPECIFICATION",
    },
}

PRACTICE_LIMITS = (
    "1–13 legacy; typed single-type caps MCQ 50 / SQL 5 / essay 10; "
    "mixed total 25 with caps MCQ 20 / SQL 2 / essay 3; default 5"
)
AI_OFFICIAL_NOTE = (
    "AI-official V1 has no per-question administrator comments; "
    "a separate seven-day review case may lead to V2 after reanalysis"
)


def q(ns: str, tag: str) -> str:
    return f"{{{ns}}}{tag}"


def parse(data: bytes):
    return etree.fromstring(data, etree.XMLParser(remove_blank_text=False, huge_tree=True))


def serialize(root) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def text_of(element) -> str:
    return "".join(element.xpath(".//w:t/text()", namespaces=NS))


def set_text(element, value: str):
    """Set an element's text in its first w:t and clear later w:t nodes."""
    nodes = element.xpath(".//w:t", namespaces=NS)
    if nodes:
        nodes[0].text = value
        for node in nodes[1:]:
            node.text = ""
    else:
        paragraph = element if element.tag == q(W, "p") else element.find(".//" + q(W, "p"))
        if paragraph is None:
            paragraph = etree.SubElement(element, q(W, "p"))
        run = etree.SubElement(paragraph, q(W, "r"))
        text = etree.SubElement(run, q(W, "t"))
        text.text = value


def set_cell(cell, value: str):
    paragraphs = cell.findall(q(W, "p"))
    if not paragraphs:
        paragraphs = [etree.SubElement(cell, q(W, "p"))]
    set_text(paragraphs[0], value)
    for paragraph in paragraphs[1:]:
        set_text(paragraph, "")


def row_values(row):
    return [text_of(cell) for cell in row.findall(q(W, "tc"))]


def tables(root):
    return root.xpath("./w:body/w:tbl", namespaces=NS)


def find_table(root, marker: str):
    for table in tables(root):
        if marker in {text_of(cell) for cell in table.xpath("./w:tr[1]/w:tc", namespaces=NS)}:
            return table
    raise ValueError(f"table not found: {marker}")


def find_table_with_row(root, label: str):
    for table in tables(root):
        if any(row_values(row)[:1] == [label] for row in table.findall(q(W, "tr"))):
            return table
    raise ValueError(f"table with row not found: {label}")


def set_row(table, label: str, values: list[str]):
    for row in table.findall(q(W, "tr")):
        cells = row.findall(q(W, "tc"))
        if cells and text_of(cells[0]) == label:
            for cell, value in zip(cells, values):
                set_cell(cell, value)
            return
    raise ValueError(f"row not found in table: {label}")


def replace_required(root, edits: list[tuple[str, str, int | None]]):
    payload = [{"old": old, "new": new, "count": count} for old, new, count in edits]
    counts = apply_edits(root, payload)
    failures = []
    for old, done, wanted in counts:
        if (wanted is None and not done) or (wanted is not None and done != wanted):
            failures.append(f"{old[:70]!r}: {done}, expected {wanted}")
    if failures:
        raise ValueError("unmatched content edits: " + "; ".join(failures))
    return counts


def paragraph(style: str, value: str, *, page_break: bool = False) -> object:
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/><w:keepNext/></w:pPr>'
    br = '<w:r><w:br w:type="page"/></w:r>' if page_break else ""
    return etree.fromstring(
        f'<w:p xmlns:w="{W}">{ppr}{br}<w:r><w:t xml:space="preserve">{value}</w:t></w:r></w:p>'.encode()
    )


def make_table(rows: list[list[str]], widths: list[int]) -> object:
    grid = "".join(f'<w:gridCol w:w="{width}"/>' for width in widths)
    body = []
    for ri, values in enumerate(rows):
        cells = []
        for value, width in zip(values, widths):
            shade = '<w:shd w:val="clear" w:fill="D9D9D9"/>' if ri == 0 else ""
            bold = "<w:b/>" if ri == 0 else ""
            cells.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shade}</w:tcPr>'
                f'<w:p><w:r><w:rPr>{bold}<w:sz w:val="18"/></w:rPr>'
                f'<w:t xml:space="preserve">{value}</w:t></w:r></w:p></w:tc>'
            )
        body.append("<w:tr>" + "".join(cells) + "</w:tr>")
    return etree.fromstring(
        (
            f'<w:tbl xmlns:w="{W}"><w:tblPr><w:tblStyle w:val="TableGrid"/>'
            '<w:tblW w:w="9072" w:type="dxa"/><w:tblBorders>'
            + "".join(
                f'<w:{side} w:val="single" w:sz="4" w:color="7F7F7F"/>'
                for side in ("top", "left", "bottom", "right", "insideH", "insideV")
            )
            + f'</w:tblBorders></w:tblPr><w:tblGrid>{grid}</w:tblGrid>'
            + "".join(body)
            + "</w:tbl>"
        ).encode()
    )


def toc_field() -> object:
    return etree.fromstring(
        (
            f'<w:p xmlns:w="{W}"><w:r><w:fldChar w:fldCharType="begin"/></w:r>'
            '<w:r><w:instrText xml:space="preserve"> TOC \\o "1-3" \\h \\z \\u </w:instrText></w:r>'
            '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
            '<w:r><w:t>Update this table of contents in Word (F9).</w:t></w:r>'
            '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>'
        ).encode()
    )


def add_srs_cover_logo(parts: dict[str, bytes], root):
    proposal = read_package(SOURCE_DIR / DOCUMENTS["ProposalDocument"]["source"])
    proposal_root = parse(proposal["word/document.xml"])
    logo_paragraph = next(
        p for p in proposal_root.xpath("./w:body/w:p", namespaces=NS)
        if p.xpath(".//wp:inline", namespaces={"wp": WP})
    )
    logo_blip = logo_paragraph.find(".//" + q(A, "blip"))
    proposal_rels = parse(proposal["word/_rels/document.xml.rels"])
    target = next(rel.get("Target") for rel in proposal_rels if rel.get("Id") == logo_blip.get(q(R, "embed")))
    logo_bytes = proposal["word/" + target]
    rels = parse(parts["word/_rels/document.xml.rels"])
    used = {rel.get("Id") for rel in rels}
    number = 1
    while f"rId{number}" in used:
        number += 1
    rid = f"rId{number}"
    etree.SubElement(rels, q(REL, "Relationship"), Id=rid, Type=R + "/image",
                     Target="media/dbcas-cover-logo.png")
    parts["word/_rels/document.xml.rels"] = serialize(rels)
    parts["word/media/dbcas-cover-logo.png"] = logo_bytes
    content = parse(parts["[Content_Types].xml"])
    if not any(node.get("Extension") == "png" for node in content):
        etree.SubElement(content, q(CT, "Default"), Extension="png", ContentType="image/png")
    parts["[Content_Types].xml"] = serialize(content)
    cloned = copy.deepcopy(logo_paragraph)
    cloned_blip = cloned.find(".//" + q(A, "blip"))
    cloned_blip.set(q(R, "embed"), rid)
    docpr = cloned.find(".//" + q(WP, "docPr"))
    if docpr is not None:
        docpr.set("name", "Duy Tan University logo")
        docpr.set("descr", "Duy Tan University logo from the preserved DBCAS Proposal cover")
    body = root.find(q(W, "body"))
    body.replace(body[0], cloned)


def add_srs_frontmatter(root):
    introduction = next(
        p for p in root.xpath("./w:body/w:p", namespaces=NS)
        if text_of(p) == "Introduction" and p.find("w:pPr/w:pStyle", NS) is not None
        and p.find("w:pPr/w:pStyle", NS).get(q(W, "val")) == "Heading1"
    )
    revision = make_table(
        [
            ["Version", "Date", "Description", "Author"],
            ["1.2", "08/11/2026", "DBCAS SRS prepared from the FITAI cover and repository facts", "C1SE.70 Team"],
            ["1.3", REVISION_DATE, "Reconcile verified facts and shared FITAI style; owner approval pending", "C1SE.70 Team"],
        ],
        [900, 1500, 4672, 2000],
    )
    note = paragraph(
        "Normal",
        "Approval status: UNKNOWN — owner must confirm; ver1.3 does not assert approval.",
    )
    elements = [
        paragraph("Heading1", "REVISION HISTORY"),
        revision,
        note,
        paragraph("Heading1", "Table of Contents"),
        toc_field(),
        paragraph("Normal", "", page_break=True),
    ]
    index = list(root.find(q(W, "body"))).index(introduction)
    for element in elements:
        root.find(q(W, "body")).insert(index, element)
        index += 1


def add_revision_row(root, key: str):
    table = find_table(root, "Version")
    rows = table.findall(q(W, "tr"))
    header = row_values(rows[0])
    new_row = copy.deepcopy(rows[-1])
    if header[1] == "Person(s)":
        values = [VISIBLE_VERSION, "C1SE.70 Team", REVISION_DATE,
                  "Reconcile verified facts and shared FITAI style; owner approval pending"]
    else:
        values = [VISIBLE_VERSION, REVISION_DATE,
                  "Reconcile verified facts and shared FITAI style; owner approval pending", "C1SE.70 Team"]
    for cell, value in zip(new_row.findall(q(W, "tc")), values):
        set_cell(cell, value)
    table.append(new_row)


def update_frontmatter_tables(root, key: str, filename: str, baseline: str):
    if key != "SRS":
        project = find_table(root, "Project acronym")
        set_row(project, "Project Web URL", ["Project Web URL", "OWNER UNKNOWN — no public URL verified"])
        info = find_table(root, "DOCUMENT INFORMATION")
        for row in info.findall(q(W, "tr")):
            cells = row.findall(q(W, "tc"))
            if not cells:
                continue
            label = text_of(cells[0])
            if label == "Date":
                set_cell(cells[1], REVISION_DATE)
                set_cell(cells[3], filename)
            elif label == "URL":
                set_cell(cells[1], "OWNER UNKNOWN — no public URL verified")
    else:
        boundary = find_table(root, "Boundary")
        set_row(boundary, "Version", ["Version", VISIBLE_VERSION])
        set_row(boundary, "Baseline", ["Baseline", baseline])


def correct_proposal(root):
    replace_required(root, [
        ("Version 1.2", "Version 1.3", 1),
        ("Date: November 8th, 2026", f"Date: {COVER_DATE}", 1),
        ("The following signatures are required for approval of this document.",
         "The following signatures are required for approval of this document. Approval status: UNKNOWN — owner must confirm; ver1.3 does not assert approval.", 1),
        ("1–13 legacy; 25 mixed / 50 single-type; default 5", PRACTICE_LIMITS, 2),
        ("1–13 legacy; 25 mixed / 50 single-type (default 5)", PRACTICE_LIMITS, 2),
        ("Long-term learning paths and RAG-based course-document retrieval are outside scope.",
         "Long-term learning-path automation remains outside scope; administrator course-document grounding and grounded candidate generation are implemented.", 1),
        ("read-only SQL queries run in a secure PostgreSQL 17 Docker sandbox",
         "SQL queries run in a secure PostgreSQL 17 Docker sandbox (read-only by default; opt-in writable demo is ephemeral and rolled back)", 1),
        ("an isolated Docker container sandbox to run read-only learner SQL safely",
         "an isolated Docker container sandbox to run learner SQL safely (read-only by default)", 1),
        ("submit multiple-choice responses, read-only SQL queries, and written conceptual answers",
         "submit multiple-choice responses, SQL queries (read-only by default), and written conceptual answers", 1),
        ("and results released after administrator review and approval.",
         "and results released according to policy: FIXED Test publishes AI-official V1; legacy/practice requires administrator review and approval.", 1),
        ("executes read-only SQL queries in a sandboxed environment",
         "executes SQL in a sandboxed environment (read-only by default; opt-in writable demo is rolled back)", 1),
        ("learner SQL is read-only and always drawn from the validated bank, and FIXED Test results publish AI-official V1; legacy/practice results publish after administrator review and approval.",
         "learner SQL is read-only by default (the opt-in writable demo is ephemeral and rolled back) and always drawn from the validated bank, and FIXED Test results publish AI-official V1; legacy/practice results publish after administrator review and approval. " + AI_OFFICIAL_NOTE + ".", 1),
        ("read-only SELECT statements run in the Docker sandbox",
         "SELECT statements run by default in the Docker sandbox; the opt-in writable demo is ephemeral and rolled back", 1),
        ("DML/DDL are never executed; that knowledge is assessed through MCQ and essay items.",
         "DML/DDL execute only in the opt-in writable demo inside the disposable container and are always rolled back; grading remains read-only.", 1),
        ("Out-of-Scope Items: To maintain high engineering quality within the 15-week timeline, the following topics are outside the project scope:",
         "Out-of-Scope Items: To maintain high engineering quality within the 15-week timeline, the following topics are outside the project scope. OTP authentication is not adopted; account recovery uses single-use emailed reset links when SMTP is configured. Free/Pro remains a UI-only demo with no payment or backend plan:", 1),
        ("fails closed with an explicit unavailable response rather than serving an unvalidated item.",
         "falls back to validated bank items with one bank_mixed notice; a genuine bank shortage stops the start with an explicit explanation.", 1),
        ("DML/DDL are assessed, never executed",
         "DML/DDL are assessed through MCQ/essay by default; the opt-in writable demo executes them only in an ephemeral rollback container", 1),
        ("Route every session through the administrator review queue and publish only after approval.",
         "Route legacy/practice sessions through the administrator review queue; publish FIXED Test as AI-official V1 and use the separate review-case workflow for disputed AI-official results.", 1),
        ("DML/DDL knowledge is assessed through MCQ and essay items and is never executed.",
         "DML/DDL may execute only in the opt-in writable demo inside the disposable container and are always rolled back; grading remains read-only.", 1),
    ])
    set_row(find_table(root, "FR ID"), "FR-10", [
        "FR-10", "Rubric-Guided Essay Scoring",
        "System evaluates technical written explanations against administrator rubrics with LLM assistance, providing score breakdowns and constructive feedback. Legacy/practice submissions are reviewed by an administrator, who may adjust SQL/essay evidence and approve publication. FIXED Test publishes AI-official V1 without per-question administrator comments.",
        "DBCAS, LLM Provider, Administrator",
    ])
    set_row(find_table(root, "NFR ID"), "NFR-07", [
        "NFR-07", "Learner Privacy",
        "Learner names and identifying numbers are removed before text is sent to external LLM Provider APIs. FIXED Test publishes AI-official V1 at finalize; legacy/practice scores, provisional profiles and gap results remain withheld until administrator approval. Only published official evidence enters learner-facing cumulative profiles.",
        "Data sanitization gateway plus release-scoped read checks and immutable result versions.",
    ])
    risk = find_table(root, "Risk ID & Category")
    for row in risk.findall(q(W, "tr")):
        if row_values(row)[0].startswith("RSK-02"):
            set_cell(row.findall(q(W, "tc"))[3],
                     "• Use low temperature and strict JSON output.\n• Grade against detailed rubrics and retain evidence.\n• Review legacy/practice before publication; FIXED Test publishes AI-official V1 and disputes use a separate review case.")
    deliverables = find_table(root, "Deliverable Item")
    for row in deliverables.findall(q(W, "tr")):
        if row_values(row)[0] == "1":
            cells = row.findall(q(W, "tc"))
            set_cell(cells[2], "A runnable local Docker Compose demo featuring OAuth and email/password sign-in, role management, personalized practice, a default read-only SQL sandbox with opt-in ephemeral writable demo, competency charts, gap guidance, and administrator content/review portals.")
            set_cell(cells[3], "Local demo and setup guide. Public deployment URL: OWNER UNKNOWN — no live URL is verified.")


def correct_architecture(root):
    replace_required(root, [
        ("Version 1.2", "Version 1.3", 1),
        ("Date: November 8th, 2026", f"Date: {COVER_DATE}", 1),
        ("The following signatures are required for approval of this document.",
         "The following signatures are required for approval of this document. Approval status: UNKNOWN — owner must confirm; ver1.3 does not assert approval.", 1),
        ("from 1 to 20 (default 5)", f"({PRACTICE_LIMITS})", 2),
        ("every session requires administrator review and approval.",
         "server-created FIXED TEST publishes AI-official V1; legacy/practice requires administrator review and approval.", 1),
        ("The session, its frozen plan and standardized evidence are stored; the result appears only after administrator review and approval.",
         "The session, its frozen plan and standardized evidence are stored; FIXED Test publishes AI-official V1 at finalize, while legacy/practice appears after administrator review and approval.", 1),
        ("Scores every answer on submission and queues every submitted session for administrator review and approval.",
         "Scores every answer on submission and applies the release policy: FIXED Test publishes AI-official V1; legacy/practice enters administrator review.", 1),
        ("5. AI grading and evaluation finish first; the result remains provisional and hidden from the learner.",
         "5. For FIXED Test, AI grading and evaluation finish first and V1 becomes OFFICIAL at finalize; no per-question administrator comments are created.", 1),
        ("6. The session waits in pending_review; an administrator reviews every SQL/essay score, adjusts it if needed, and publishes. Feedback is shown only after approval.",
         "6. For legacy/practice, the session waits in pending_review; an administrator reviews required SQL/essay evidence, adjusts it if needed, and publishes. A separate seven-day review case may regrade an AI-official V1.", 1),
        ("Allows an administrator to review automated grades for every submitted SQL and essay answer, adjust scores if needed, and approve the session. Unpublished scores, provisional profiles and gap results stay hidden from the learner until approval and publication.",
         "Allows an administrator to review automated grades for legacy/practice SQL and essay evidence, adjust scores with a reason, and approve publication. AI-official FIXED Test V1 is published at finalize and has no per-question administrator comments; its separate review-case workflow can produce V2.", 1),
        ("Every session follows this path.",
         "This use case applies to legacy/practice sessions, not AI-official FIXED Test V1.", 1),
        ("Every result requires administrator review and approval: an administrator reviews every SQL and essay score before publication.",
         "FIXED Test publishes AI-official V1 at finalize without per-question administrator comments; legacy/practice requires administrator review before publication. A separate seven-day review case may lead to V2 after reanalysis.", 1),
        ("All design, implementation, testing, and documentation must finish within the 15-week Capstone 1 schedule (14 September 2026 -- 26 December 2026), ending with the capstone defense. Written reports are delivered in both PDF and Word (.docx) formats.",
         "All design, implementation, testing, and documentation must finish within the 15-week Capstone 1 schedule (14 September 2026 -- 26 December 2026), ending with the capstone defense. Written reports are delivered in PDF and Word (.docx). OTP is out of scope; password recovery uses reset links. Free/Pro is UI-only with no payment or backend plan.", 1),
        ("under a default read-only role and SELECT-only validation; the opt-in demo profile allows writable DDL/DML",
         "under a default read-only role and SELECT-only validation; the opt-in demo profile allows writable DDL/DML", 1),
        ("that runs with a read-only role, SELECT-only validation, no network access, a 256 MB memory limit, and a 3-second statement timeout, so it can never reach application data.",
         "that runs with a read-only role and SELECT-only validation by default; the opt-in writable demo is ephemeral and rolled back. It has no network access, a 256 MB memory limit, and a 3-second statement timeout, so it can never reach application data.", 1),
        ("runs read-only SELECT queries in a sandbox",
         "runs SQL in a sandbox (read-only by default; opt-in writable demo is rolled back)", 1),
        ("read-only SELECT queries and written answers",
         "SQL queries (read-only by default) and written answers", 1),
        ("The API validates that the statement is a single SELECT; DML/DDL and other statements are rejected before execution.",
         "By default the API validates a single SELECT and rejects DML/DDL. The opt-in writable demo accepts validated DDL/DML only in the disposable ephemeral container.", 1),
        ("The query runs in the isolated PostgreSQL 17 Docker sandbox under a read-only role, a 3-second statement timeout, and a 256 MB memory limit, inside a read-only transaction that is rolled back.",
         "The query runs in the isolated PostgreSQL 17 Docker sandbox under the default read-only role (or the opt-in demo writable role), with a 3-second statement timeout, a 256 MB memory limit, and a transaction that is rolled back.", 1),
        ("Runs learner SELECT queries inside the Docker sandbox in a read-only transaction with a timeout and rolls back after evaluation.",
         "Runs learner SQL inside the Docker sandbox: SELECT-only under the default read-only role, or validated DDL/DML in the opt-in ephemeral writable demo; every transaction is rolled back after evaluation.", 1),
        ("runs SELECT queries in the sandbox",
         "runs SQL in the sandbox (read-only by default; opt-in writable demo is rolled back)", 1),
        ("Sends DB requests to PostgreSQL, SELECT queries to the SQL Sandbox",
         "Sends DB requests to PostgreSQL and learner SQL to the SQL Sandbox (read-only by default; opt-in writable demo is rolled back)", 1),
        ("which executes learner SELECT queries in the isolated Docker sandbox",
         "which executes learner SQL in the isolated Docker sandbox (read-only by default; opt-in writable demo is rolled back)", 1),
    ])
    set_row(find_table(root, "UC12"), "Description", [
        "Description",
        "Allows learners to choose concepts, difficulty bands, an exact question count and source, then complete a learner-defined practice session whose complete plan is frozen before question one. Legacy practice is 1–13; typed single-type caps are MCQ 50 / SQL 5 / essay 10; mixed practice totals at most 25 with caps MCQ 20 / SQL 2 / essay 3; default 5.",
    ])
    set_row(find_table(root, "UC13"), "Description", [
        "Description", "Allows learners to solve SQL tasks in a safe environment: SELECT-only by default, with validated DDL/DML only in the opt-in ephemeral writable demo."
    ])
    set_row(find_table(root, "BC03"), "Description", [
        "Description",
        "The external LLM Provider is assistive only. Final competency scores are computed deterministically by DBCAS from predefined scoring rules, isolated SQL test suites, and evidence logs. FIXED Test publishes AI-official V1 at finalize without per-question administrator comments; legacy/practice requires administrator review before publication. A separate seven-day review case may lead to V2 after reanalysis.",
    ])
    containers = find_table(root, "Role")
    for row in containers.findall(q(W, "tr")):
        cells = row.findall(q(W, "tc"))
        if cells and text_of(cells[0]) == "Administrator":
            set_cell(cells[1], "Manages CLOs, concepts, prerequisites, the validated Question Bank, translations and rubrics. Manages accounts, reviews/approves legacy/practice results, reviews cohort analytics, and handles AI-official review cases; FIXED Test V1 has no per-question comments.")


def schema_type(column) -> str:
    kind = column["type"].lower()
    if kind == "array":
        return (column.get("udt") or "_text").lstrip("_").upper() + "[]"
    if kind in ("character varying", "character"):
        return f"VARCHAR({column['max_length']})" if column.get("max_length") else "VARCHAR"
    if kind == "timestamp with time zone":
        return "TIMESTAMPTZ"
    if kind == "timestamp without time zone":
        return "TIMESTAMP"
    if kind == "numeric":
        return f"NUMERIC({column['numeric_precision']},{column['numeric_scale']})"
    return {
        "integer": "INT", "bigint": "BIGINT", "boolean": "BOOLEAN", "text": "TEXT",
        "jsonb": "JSONB", "date": "DATE", "smallint": "SMALLINT",
    }.get(kind, kind.upper())


def normalize_database_dictionary(root):
    schema = json.loads((ROOT / "docs/diagrams/schema-028/schema-introspection.json").read_text(encoding="utf-8"))

    def key(value):
        return value.lower().replace("_", "").replace(" ", "")

    real = {key(table["table"]): table for table in schema["tables"]}
    current = None
    seen = set()
    columns = 0
    for element in root.find(q(W, "body")):
        if element.tag == q(W, "p"):
            style = element.find("w:pPr/w:pStyle", NS)
            if style is not None and style.get(q(W, "val")) == "Heading2":
                current = text_of(element)
        elif element.tag == q(W, "tbl"):
            rows = element.findall(q(W, "tr"))
            header = row_values(rows[0]) if rows else []
            if not header or header[0] != "Attributes" or not current:
                continue
            name = current.split(" ", 1)[1] if current.startswith("A.") else current
            table = real.get(key(name))
            if table is None:
                raise ValueError(f"dictionary heading is not in the current schema: {current}")
            seen.add(table["table"])
            by_name = {column["name"]: column for column in table["columns"]}
            for row in rows[1:]:
                cells = row.findall(q(W, "tc"))
                if not cells:
                    continue
                column = by_name.get(text_of(cells[0]))
                if column is None:
                    raise ValueError(f"dictionary column is not in the current schema: {name}.{text_of(cells[0])}")
                set_cell(cells[1], schema_type(column))
                set_cell(cells[2], "Yes" if column["nullable"] else "Not")
                columns += 1
            current = None
    expected_columns = sum(len(table["columns"]) for table in schema["tables"])
    if len(seen) != len(real) or columns != expected_columns:
        raise ValueError(f"dictionary mismatch: {len(seen)} tables / {columns} columns")


def correct_database(root):
    replace_required(root, [
        ("Version 1.2", "Version 1.3", 2),
        ("Date: November 8th, 2026", f"Date: {COVER_DATE}", 2),
        ("Approved by", "Approval status", 2),
        ("MSc. Huynh Duc Viet", "UNKNOWN — owner must confirm", 2),
    ])
    overview = find_table(root, "Table Name")
    set_row(overview, "GradeReview", [
        "GradeReview",
        "Human review decision for legacy/practice administrator approval: automated evidence, reviewer, approved score and comments. AI-official V1 has no per-question administrator comments.",
    ])
    set_row(overview, "ResultReleaseEvent", [
        "ResultReleaseEvent",
        "Immutable history of every release-status transition, including AI-official FIXED Test publication and legacy/practice review.",
    ])
    set_row(overview, "session_result_version", [
        "session_result_version",
        "Immutable V1/V2 result header. FIXED Test V1 is AI-official; a separate review case may create V2 after reanalysis.",
    ])
    for table in tables(root):
        headers = row_values(table.findall(q(W, "tr"))[0])
        table_labels = {row_values(row)[0] for row in table.findall(q(W, "tr")) if row_values(row)}
        if headers and headers[0] == "Attributes":
            for row in table.findall(q(W, "tr")):
                cells = row.findall(q(W, "tc"))
                if not cells:
                    continue
                name = text_of(cells[0])
                if name == "result_release_policy":
                    set_cell(cells[-1], "Historical/server-owned IMMEDIATE or HUMAN_VERIFIED policy; the current UI does not select it.")
                elif name == "comments" and "approved_score" in table_labels:
                    set_cell(cells[-1], "Reviewer comments for legacy/practice human verification; AI-official V1 has no per-question comments.")
                elif name == "reason" and "new_score" in table_labels:
                    set_cell(cells[-1], "Reason for a legacy/practice score edit; not an AI-official V1 per-question comment.")
    scope = next(
        p for p in root.xpath("./w:body/w:p", namespaces=NS)
        if text_of(p).startswith("To serve as a basis for implementing the database")
    )
    parent = scope.getparent()
    index = list(parent).index(scope) + 1
    for value in (
        "To keep the demo boundary explicit: OTP authentication is out of scope; password recovery uses single-use reset tokens and audit records.",
        "To keep commercial simulation out of persistence: Free/Pro is UI-only, with no payment route, backend plan, or stored subscription table.",
    ):
        cloned = copy.deepcopy(scope)
        set_text(cloned, value)
        parent.insert(index, cloned)
        index += 1
    normalize_database_dictionary(root)


def correct_srs(root, baseline: str):
    replace_required(root, [
        ("Version 1.2", "Version 1.3", 1),
        ("Date: November 8th, 2026", f"Date: {COVER_DATE}", 1),
        ("develop2 6421b5ad44a0eaaeb9be8d26068c8ca434ae5bb7", baseline, 1),
        ("Administrators curate the bank and review legacy/practice results.",
         "Administrators curate the bank and review legacy/practice results. FIXED Test publishes AI-official V1 at finalize; " + AI_OFFICIAL_NOTE + ".", 1),
        ("V1/V2 result versions are immutable; FIXED Test publishes AI-official V1 at finalize, while legacy/practice uses human review.",
         "V1/V2 result versions are immutable; FIXED Test publishes AI-official V1 at finalize, while legacy/practice uses human review. " + AI_OFFICIAL_NOTE + ".", 1),
        ("Broker #80 is closed/unmerged; docker.sock #66 is a known limitation.",
         "Broker #80 is merged but default-OFF; docker.sock #66 remains a known limitation until the separately reviewed B2 cutover, and writable broker execution remains future B3 work.", 1),
        ("State/script grading is not implemented; GRADING_STATE_MODE has no runtime consumer.",
         "Writable/state grading is opt-in and default-OFF; the demo path is ephemeral and rolled back, and grading remains read-only.", 1),
        ("NFR evidence is recorded against the frozen code and exact-head CI runs; it is not a product SLA.",
         "The counts below are historical freeze evidence from the cited commit and CI run. Phase 5 did not rerun full backend/frontend/browser suites; current-head gates remain owner-sequenced.", 1),
        ("This SRS is part of the in-place v1.2 revision and records the frozen demo baseline, not a production release.",
         "This SRS is a separate ver1.3 reconciliation of the v1.2 content. Source documents are preserved; owner approval and production release remain pending.", 1),
    ])
    boundary = find_table(root, "Boundary")
    set_row(boundary, "Version", ["Version", VISIBLE_VERSION])
    set_row(boundary, "Baseline", ["Baseline", baseline])
    functional = find_table(root, "Requirement")
    set_row(functional, "FR-P01", [
        "FR-P01",
        "List practice options and preview an exact count: " + PRACTICE_LIMITS + ".",
        "GET /practice/options; POST /practice/preview", "/assessments",
        "test_learner_practice.py; LearnerPages.test.jsx",
    ])
    set_row(functional, "FR-P02", [
        "FR-P02",
        "Start learner-defined FIXED or ADAPTIVE practice with a frozen plan; server-created FIXED TEST is a separate AI-official path.",
        "POST /practice/start", "/assessments; /exam/:id",
        "test_learner_practice.py; test_continuous_adaptive.py",
    ])
    set_row(functional, "FR-F03", [
        "FR-F03", "FIXED mode submits once and publishes AI-official V1 without per-question administrator comments.",
        "POST /paper/submit", "FixedPaperRunner.jsx",
        "test_fixed_paper_api.py; test_pr3b2_v1_official.py",
    ])
    nfr = find_table(root, "Implementation")
    set_row(nfr, "NFR-SEC-02", [
        "NFR-SEC-02",
        "Learner SQL cannot reach the application DB; default read-only/no network/rollback. Writable DDL/DML is opt-in, ephemeral-only, rolled back, and never used for grading.",
        "ephemeral_sandbox.py; sql_classifier.py", "test_sandbox_safety.py; test_sql_multistatement.py",
    ])
    set_row(nfr, "NFR-SEC-03", [
        "NFR-SEC-03",
        "AI prompts are sanitized; one generic OpenAI-compatible provider is configured by LLM_API_KEY/LLM_BASE_URL/LLM_MODEL. Provider privacy/ZDR is an operator gate, not an app-enforced vendor promise.",
        "llm/sanitize.py; config.py", "test_ai_pipeline_purity.py; test_llm_provider_config.py",
    ])
    set_row(nfr, "NFR-TEST-01", [
        "NFR-TEST-01",
        "Historical freeze evidence: backend 1913; frontend 459; browser 140 passed + 2 skipped. Current-head full suites were not rerun in Phase 5.",
        "Prior v1.2 SRS evidence", "run 45124260745 at 6421b5a",
    ])
    gates = find_table(root, "Gate")
    set_row(gates, "Backend tests", ["Backend tests", "Historical: 1913 passed", "Prior CI backend job, run 45124260745 at 6421b5a; not rerun in Phase 5"])
    set_row(gates, "Frontend tests", ["Frontend tests", "Historical: 459 passed", "Prior CI frontend-static job; not rerun in Phase 5"])
    set_row(gates, "Browser tests", ["Browser tests", "Historical: 140 passed + 2 skipped", "Prior 9 CI shards; not rerun in Phase 5"])
    roles = find_table(root, "Module")
    for row in roles.findall(q(W, "tr")):
        cells = row.findall(q(W, "tc"))
        if cells and text_of(cells[1]) == "Assessments and blueprints":
            for cell, value in zip(cells, ["Administrator", "AI candidates and course documents", "/admin/documents", "FR-AD04, FR-AD05"]):
                set_cell(cell, value)
    evidence = find_table_with_row(root, "NFR-OPS-01")
    for row in evidence.findall(q(W, "tr")):
        cells = row.findall(q(W, "tc"))
        if cells and text_of(cells[0]) == "NFR-OPS-01":
            set_cell(cells[2], "Historical backend 1913, frontend 459, browser 140 + 2 skipped on the prior freeze head; Phase 5 current-head full suites pending")
    limitations = find_table(root, "Area")
    set_row(limitations, "Sandbox", [
        "Sandbox",
        "Broker #80 is merged but default-OFF; docker.sock #66 remains until B2; writable broker execution is future B3",
        "config.py; docs/agent/STATUS.md",
    ])
    trace = find_table(root, "FR group")
    for row in trace.findall(q(W, "tr")):
        cells = row.findall(q(W, "tc"))
        if cells and text_of(cells[0]) == "FR-27 to FR-29":
            for cell, value in zip(cells, [
                "FR-AD04/FR-AD05", "GET/POST /admin/question-candidates; /admin/documents",
                "/admin/documents", "test_ai_admin.py; test_admin_documents.py",
            ]):
                set_cell(cell, value)
    control = find_table(root, "Artifact")
    set_row(control, "Frozen code", ["Documentation baseline", f"develop2 {baseline}; architecture freeze 69e1e2f; production HOLD"])
    set_row(control, "Verification", ["Verification", "Historical backend 1913; frontend 459; browser 140 + 2 skipped; Phase 5 current-head full suites pending"])
    set_row(control, "Documents", ["Documents", "Separate ver1.3 copies; sources preserved; common FITAI A4/Times New Roman/gray-table style; 67 tables / 561 columns / 122 FKs / 28 migrations"])
    set_row(control, "Audits", ["Audits", "ver1.3 package, fact and style audits are recorded alongside this file; full current-head CI remains owner-gated"])
    set_row(control, "Integrity", ["Integrity", "All four DOCX packages are opened with Word COM, fields refreshed, saved, reopened and rendered for visual inspection"])


def ensure_rpr(parent):
    rpr = parent.find(q(W, "rPr"))
    if rpr is None:
        rpr = etree.Element(q(W, "rPr"))
        parent.insert(0, rpr)
    return rpr


def set_font(rpr, size: int | None = None, color: str | None = None, bold: bool | None = None):
    fonts = rpr.find(q(W, "rFonts"))
    if fonts is None:
        fonts = etree.Element(q(W, "rFonts"))
        rpr.insert(0, fonts)
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(q(W, attr), "Times New Roman")
    for attr in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
        fonts.attrib.pop(q(W, attr), None)
    if size is not None:
        sz = rpr.find(q(W, "sz"))
        if sz is None:
            sz = etree.SubElement(rpr, q(W, "sz"))
        sz.set(q(W, "val"), str(size))
        szcs = rpr.find(q(W, "szCs"))
        if szcs is None:
            szcs = etree.SubElement(rpr, q(W, "szCs"))
        szcs.set(q(W, "val"), str(size))
    if color is not None:
        node = rpr.find(q(W, "color"))
        if node is None:
            node = etree.SubElement(rpr, q(W, "color"))
        node.set(q(W, "val"), color)
    if bold:
        if rpr.find(q(W, "b")) is None:
            etree.SubElement(rpr, q(W, "b"))


def normalize_styles(styles):
    default = styles.find("w:docDefaults/w:rPrDefault/w:rPr", NS)
    if default is None:
        raise ValueError("styles.xml has no docDefaults/rPrDefault")
    set_font(default, 26, "000000")
    for sid in ("Normal", "BodyText", "ListParagraph"):
        style = styles.xpath("./w:style[@w:styleId=$sid]", namespaces=NS, sid=sid)
        if style:
            set_font(ensure_rpr(style[0]), 26, "000000")
    for sid in ("Heading1", "Heading2", "Heading3"):
        style = styles.xpath("./w:style[@w:styleId=$sid]", namespaces=NS, sid=sid)
        if style:
            set_font(ensure_rpr(style[0]), 26, "000000", bold=True)
    caption = styles.xpath("./w:style[@w:styleId='Caption']", namespaces=NS)
    if caption:
        set_font(ensure_rpr(caption[0]), 18, "44546A")
        ppr = caption[0].find(q(W, "pPr"))
        if ppr is None:
            ppr = etree.SubElement(caption[0], q(W, "pPr"))
        spacing = ppr.find(q(W, "spacing"))
        if spacing is None:
            spacing = etree.SubElement(ppr, q(W, "spacing"))
        spacing.set(q(W, "after"), "200")
    return styles


def normalize_theme(data: bytes) -> bytes:
    root = parse(data)
    for latin in root.xpath(".//a:themeElements/a:fontScheme//a:latin", namespaces={"a": A}):
        latin.set("typeface", "Times New Roman")
    return serialize(root)


def normalize_geometry(root):
    for sect in root.xpath(".//w:sectPr", namespaces=NS):
        size = sect.find(q(W, "pgSz"))
        if size is None:
            size = etree.SubElement(sect, q(W, "pgSz"))
        landscape = int(size.get(q(W, "w"), "11907")) > int(size.get(q(W, "h"), "16840"))
        size.set(q(W, "w"), "16840" if landscape else "11907")
        size.set(q(W, "h"), "11907" if landscape else "16840")
        margins = sect.find(q(W, "pgMar"))
        if margins is None:
            margins = etree.SubElement(sect, q(W, "pgMar"))
        for attr, value in {"top": "1134", "right": "1134", "bottom": "1418", "left": "1701",
                            "header": "720", "footer": "720", "gutter": "0"}.items():
            margins.set(q(W, attr), value)


def normalize_tables(root, key: str):
    for table in tables(root):
        rows = table.findall(q(W, "tr"))
        if not rows:
            continue
        first = row_values(rows[0])
        is_header = bool(first) and first[0] not in {"Project acronym"} and "Signature" not in first
        for ri, row in enumerate(rows):
            for cell in row.findall(q(W, "tc")):
                tcpr = cell.find(q(W, "tcPr"))
                if tcpr is None:
                    tcpr = etree.Element(q(W, "tcPr"))
                    cell.insert(0, tcpr)
                if ri == 0 and is_header:
                    shd = tcpr.find(q(W, "shd"))
                    if shd is None:
                        shd = etree.SubElement(tcpr, q(W, "shd"))
                    shd.set(q(W, "val"), "clear")
                    shd.set(q(W, "fill"), "D9D9D9")
            for run in row.xpath(".//w:r", namespaces=NS):
                rpr = ensure_rpr(run)
                size = 18 if key == "SRS" else None
                set_font(rpr, size=size, color="000000", bold=(ri == 0 and is_header))


def normalize_document_runs(root, key: str):
    body_started = False
    for p in root.xpath("./w:body/w:p", namespaces=NS):
        style = p.find("w:pPr/w:pStyle", NS)
        sid = style.get(q(W, "val")) if style is not None else "Normal"
        if sid == "Heading1":
            body_started = True
        has_field = bool(p.xpath(".//w:fldChar|.//w:instrText", namespaces=NS))
        for run in p.xpath(".//w:r", namespaces=NS):
            rpr = ensure_rpr(run)
            if sid == "Caption":
                set_font(rpr, 18, "44546A")
            else:
                set_font(rpr)
                if body_started and not has_field and sid not in {"Heading1", "Heading2", "Heading3", "Title", "Subtitle"}:
                    sz = rpr.find(q(W, "sz"))
                    if sz is not None and int(sz.get(q(W, "val"), "26")) < 26:
                        sz.set(q(W, "val"), "26")
                        szcs = rpr.find(q(W, "szCs"))
                        if szcs is not None:
                            szcs.set(q(W, "val"), "26")


def normalize_header_footer(data: bytes, key: str, *, header: bool) -> bytes:
    root = parse(data)
    full = text_of(root)
    if header and full:
        if key == "SRS":
            set_text(root, f"{GROUP} | {PROJECT} | {DOCUMENTS[key]['header']}")
        elif key == "DatabaseDesign":
            set_text(root, f"{GROUP} | {PROJECT} | DATABASE DESIGN")
    if not header and full and "PAGE" in " ".join(root.xpath(".//w:instrText/text()", namespaces=NS)):
        nodes = root.xpath(".//w:t", namespaces=NS)
        if nodes and not text_of(root).startswith(GROUP):
            nodes[0].text = f"{GROUP} | Page "
            for node in nodes[1:]:
                node.text = ""
    for run in root.xpath(".//w:r", namespaces=NS):
        set_font(ensure_rpr(run))
    return serialize(root)


def normalize_settings(data: bytes) -> bytes:
    root = parse(data)
    update = root.find(q(W, "updateFields"))
    if update is None:
        update = etree.SubElement(root, q(W, "updateFields"))
    update.set(q(W, "val"), "true")
    return serialize(root)


def core_xml(title: str) -> bytes:
    return (
        f'<cp:coreProperties xmlns:cp="{CP}" xmlns:dc="{DC}" xmlns:dcterms="{DCTERMS}" '
        f'xmlns:xsi="{XSI}"><dc:title>{title}</dc:title><dc:subject>{GROUP} {PROJECT} {VERSION}</dc:subject>'
        f'<dc:creator>{CREATOR}</dc:creator><cp:keywords>{GROUP}; {PROJECT}; {VERSION}</cp:keywords>'
        f'<dc:description>Verified DBCAS {VERSION} deliverable; owner approval pending.</dc:description>'
        f'<cp:lastModifiedBy>{CREATOR}</cp:lastModifiedBy><cp:revision>13</cp:revision>'
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{TIMESTAMP}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{TIMESTAMP}</dcterms:modified>'
        '</cp:coreProperties>'
    ).encode()


def custom_xml() -> bytes:
    def prop(pid: int, name: str, value: str):
        return f'<property fmtid="{{D5CDD505-2E9C-101B-9397-08002B2CF9AE}}" pid="{pid}" name="{name}"><vt:lpwstr>{value}</vt:lpwstr></property>'
    return (
        f'<Properties xmlns="{CUSTOM}" xmlns:vt="{VT}">'
        + prop(2, "Version", VERSION) + prop(3, "Group", GROUP) + prop(4, "Project", PROJECT)
        + '</Properties>'
    ).encode()


def ensure_custom_property(parts: dict[str, bytes]):
    parts["docProps/custom.xml"] = custom_xml()
    rels = parse(parts["_rels/.rels"])
    if not any(rel.get("Type", "").endswith("/custom-properties") for rel in rels):
        used = {rel.get("Id") for rel in rels}
        number = 1
        while f"rId{number}" in used:
            number += 1
        etree.SubElement(rels, q(REL, "Relationship"), Id=f"rId{number}",
                         Type=R + "/custom-properties", Target="docProps/custom.xml")
    parts["_rels/.rels"] = serialize(rels)
    content = parse(parts["[Content_Types].xml"])
    if not any(node.get("PartName") == "/docProps/custom.xml" for node in content):
        etree.SubElement(content, q(CT, "Override"), PartName="/docProps/custom.xml",
                         ContentType="application/vnd.openxmlformats-officedocument.custom-properties+xml")
    parts["[Content_Types].xml"] = serialize(content)


def normalize_metadata(parts: dict[str, bytes], key: str):
    title = f"{PROJECT} {DOCUMENTS[key]['title']} — {VERSION}"
    parts["docProps/core.xml"] = core_xml(title)
    ensure_custom_property(parts)
    app = parse(parts["docProps/app.xml"])
    for hlinks in app.xpath("./*[local-name()='HLinks']"):
        app.remove(hlinks)
    company = app.find(q(EP, "Company"))
    if company is None:
        company = etree.SubElement(app, q(EP, "Company"))
    company.text = "Duy Tan University"
    titles = app.find(q(EP, "TitlesOfParts"))
    if titles is not None:
        values = titles.xpath(".//vt:lpstr", namespaces={"vt": VT})
        if values:
            values[0].text = title
    parts["docProps/app.xml"] = serialize(app)


def write_package(path: Path, parts: dict[str, bytes]):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in parts.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 25, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zout.writestr(info, data)
    temp.replace(path)


def read_package(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as zin:
        return {name: zin.read(name) for name in zin.namelist()}


def source_manifest() -> dict:
    sources = [SOURCE_DIR / item["source"] for item in DOCUMENTS.values()]
    sources += [
        ROOT.parent / "C1SE.70_ProposalDocument_DBCAS_ver1.2.txt",
        ROOT.parent / "C1SE.70_ArchitectureDesign_DBCAS_ver1.2.txt",
        ROOT.parent / "C1SE.70_DatabaseDesign_DBCAS_ver1.2.txt",
        ROOT.parent / "Software Requiremen Specification Template.docx",
    ]
    return {
        str(path.resolve()): {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in sources
    }


def build(output: Path, baseline: str):
    output = ensure_safe_output(output, label="ver1.3 output")
    protected_final = (ROOT.parent / "Documents" / "Final").resolve()
    if output == protected_final or protected_final in output.parents:
        raise ValueError("refusing to overwrite Documents/Final; choose Documents/Final-ver1.3")
    verification = output / "verification"
    verification.mkdir(parents=True, exist_ok=True)
    manifest = source_manifest()
    (verification / "build-baseline.txt").write_text(baseline + "\n", encoding="utf-8")
    manifest_path = verification / "source-manifest.json"
    if manifest_path.exists():
        if json.loads(manifest_path.read_text(encoding="utf-8")) != manifest:
            raise ValueError("a preserved source changed since the first ver1.3 build")
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for key, item in DOCUMENTS.items():
        parts = read_package(SOURCE_DIR / item["source"])
        document = parse(parts["word/document.xml"])
        if key == "ProposalDocument":
            correct_proposal(document)
        elif key == "ArchitectureDesign":
            correct_architecture(document)
        elif key == "DatabaseDesign":
            correct_database(document)
        else:
            correct_srs(document, baseline)
            add_srs_frontmatter(document)
            add_srs_cover_logo(parts, document)
        update_frontmatter_tables(document, key, item["filename"], baseline)
        if key != "SRS":
            add_revision_row(document, key)
        normalize_geometry(document)
        normalize_tables(document, key)
        normalize_document_runs(document, key)
        parts["word/document.xml"] = serialize(document)
        parts["word/styles.xml"] = serialize(normalize_styles(parse(parts["word/styles.xml"])))
        parts["word/theme/theme1.xml"] = normalize_theme(parts["word/theme/theme1.xml"])
        parts["word/settings.xml"] = normalize_settings(parts["word/settings.xml"])
        for name in list(parts):
            if name.startswith("word/header") and name.endswith(".xml"):
                parts[name] = normalize_header_footer(parts[name], key, header=True)
            elif name.startswith("word/footer") and name.endswith(".xml"):
                parts[name] = normalize_header_footer(parts[name], key, header=False)
        normalize_metadata(parts, key)
        destination = output / item["filename"]
        write_package(destination, parts)
        print(destination)


def metadata_only(output: Path):
    output = ensure_safe_output(output, label="ver1.3 output")
    for key, item in DOCUMENTS.items():
        path = output / item["filename"]
        parts = read_package(path)
        normalize_metadata(parts, key)
        parts["word/settings.xml"] = normalize_settings(parts["word/settings.xml"])
        write_package(path, parts)
        print(path)


def package_problems(path: Path) -> list[str]:
    problems = []
    try:
        with zipfile.ZipFile(path) as zin:
            if zin.testzip() is not None:
                problems.append("ZIP CRC failure")
            names = set(zin.namelist())
            for required in ("[Content_Types].xml", "_rels/.rels", "word/document.xml", "docProps/core.xml"):
                if required not in names:
                    problems.append(f"missing {required}")
            content = parse(zin.read("[Content_Types].xml"))
            defaults = {node.get("Extension"): node.get("ContentType") for node in content if node.tag == q(CT, "Default")}
            overrides = {node.get("PartName", "").lstrip("/"): node.get("ContentType") for node in content if node.tag == q(CT, "Override")}
            for name in names:
                if name.endswith(".xml") or name.endswith(".rels"):
                    try:
                        parse(zin.read(name))
                    except Exception as exc:
                        problems.append(f"XML {name}: {exc}")
                if name != "[Content_Types].xml" and name not in overrides and name.rsplit(".", 1)[-1] not in defaults:
                    problems.append(f"missing content type: {name}")
            for name in sorted(n for n in names if n.endswith(".rels")):
                root = parse(zin.read(name))
                if name == "_rels/.rels":
                    source = ""
                else:
                    directory, filename = posixpath.split(name)
                    source = posixpath.join(posixpath.dirname(directory), filename[:-5])
                base = posixpath.dirname(source)
                for rel in root:
                    if rel.get("TargetMode") == "External":
                        continue
                    target = rel.get("Target", "")
                    resolved = posixpath.normpath(posixpath.join(base, target)).lstrip("/")
                    if resolved not in names:
                        problems.append(f"missing relationship target {name}: {target}")
    except Exception as exc:
        problems.append(f"{type(exc).__name__}: {exc}")
    return problems


def audit(output: Path, baseline: str) -> int:
    output = ensure_safe_output(output, label="ver1.3 audit")
    verification = output / "verification"
    verification.mkdir(parents=True, exist_ok=True)
    assertions = []

    def check(doc: str, label: str, condition: bool, detail=""):
        assertions.append({"document": doc, "id": label, "status": "PASS" if condition else "FAIL", "detail": detail})

    preserved = json.loads((verification / "source-manifest.json").read_text(encoding="utf-8"))
    for name, expected in preserved.items():
        path = Path(name)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        check("sources", f"source unchanged: {path.name}", actual == expected["sha256"], actual)

    style = {}
    retired = [
        "1 to 20", "1–20", "41 tables", "66 tables", "27 migrations", "558 columns",
        "120 foreign keys", "158 indexes", "OpenRouter", "Every result requires administrator review",
        "every session requires administrator review", "DML/DDL are never executed",
        "DML and DDL are never executed", "State/script grading is not implemented",
        "Broker #80 is closed/unmerged", "Broker #80 is closed;",
        "1–13 legacy; 1–13 legacy", "default 5; default 5", "default 5 (default 5)",
    ]
    for key, item in DOCUMENTS.items():
        path = output / item["filename"]
        check(key, "exists", path.exists(), str(path))
        if not path.exists():
            continue
        problems = package_problems(path)
        check(key, "ZIP/OOXML package", not problems, "; ".join(problems))
        parts = read_package(path)
        root = parse(parts["word/document.xml"])
        visible = text_of(root)
        core = parse(parts["docProps/core.xml"])
        creator = core.findtext(q(DC, "creator"), default="")
        modifier = core.findtext(q(CP, "lastModifiedBy"), default="")
        check(key, "creator metadata", creator == CREATOR, creator)
        check(key, "lastModifiedBy metadata", modifier == CREATOR, modifier)
        custom = parse(parts["docProps/custom.xml"])
        props = {node.get("name"): "".join(node.itertext()) for node in custom}
        check(key, "ver1.3 metadata", props.get("Version") == VERSION and props.get("Group") == GROUP and props.get("Project") == PROJECT, str(props))
        check(key, "visible ver1.3 cover", "Version 1.3" in visible and f"Date: {COVER_DATE}" in visible)
        check(key, "owner approval unknown", "Approval status: UNKNOWN" in visible or "Approval status" in visible and "owner must confirm" in visible)
        check(key, "current counts", all(token in visible for token in ("67 tables", "561 columns", "122 foreign keys", "159 indexes", "28 migrations")))
        check(key, "no retired facts", not any(token.lower() in visible.lower() for token in retired),
              ", ".join(token for token in retired if token.lower() in visible.lower()))
        check(key, "release paths", "AI-official V1" in visible and "legacy/practice" in visible)
        check(key, "AI-official comment boundary", "no per-question administrator comments" in visible.lower())
        instructions = " ".join(parts["word/document.xml"].decode("utf-8", "ignore").split())
        check(key, "TOC field", "TOC" in instructions)
        if key != "SRS":
            check(key, "caption fields", "SEQ Figure" in instructions and "SEQ Table" in instructions)
        media = [name for name in parts if name.startswith("word/media/")]
        source_media = [name for name in read_package(SOURCE_DIR / item["source"]) if name.startswith("word/media/")]
        if key == "SRS":
            check(key, "no required SRS diagrams", "SEQ Figure" not in instructions, f"media {len(media)} vs source {len(source_media)}")
        else:
            check(key, "preserved media count", len(media) == len(source_media), f"{len(media)} vs source {len(source_media)}")
        sections = root.xpath(".//w:sectPr", namespaces=NS)
        geometry_ok = True
        for sect in sections:
            size = sect.find(q(W, "pgSz"))
            margins = sect.find(q(W, "pgMar"))
            landscape = int(size.get(q(W, "w"))) > int(size.get(q(W, "h")))
            expected_size = ("16840", "11907") if landscape else ("11907", "16840")
            geometry_ok &= (size.get(q(W, "w")), size.get(q(W, "h"))) == expected_size
            geometry_ok &= all(margins.get(q(W, attr)) == value for attr, value in
                               {"top": "1134", "right": "1134", "bottom": "1418", "left": "1701"}.items())
        check(key, "common A4 geometry", geometry_ok, f"{len(sections)} sections")
        styles = parse(parts["word/styles.xml"])
        default_rpr = styles.find("w:docDefaults/w:rPrDefault/w:rPr", NS)
        normal_styles = styles.xpath("./w:style[@w:styleId='Normal']/w:rPr", namespaces=NS)
        normal = normal_styles[0] if normal_styles else default_rpr
        fonts = normal.find(q(W, "rFonts")) if normal is not None else None
        if fonts is None:
            fonts = default_rpr.find(q(W, "rFonts"))
        size = normal.find(q(W, "sz")) if normal is not None else None
        if size is None:
            size = default_rpr.find(q(W, "sz"))
        check(key, "Times New Roman Normal", fonts is not None and fonts.get(q(W, "ascii")) == "Times New Roman"
              and size is not None and size.get(q(W, "val")) == "26")
        fills = root.xpath(".//w:tbl[1]/w:tr[1]/w:tc/w:tcPr/w:shd/@w:fill", namespaces=NS)
        style[key] = {
            "sections": len(sections), "media": len(media), "paragraphs": len(root.xpath(".//w:p", namespaces=NS)),
            "tables": len(tables(root)), "toc_fields": instructions.count("TOC"),
            "seq_figure_fields": instructions.count("SEQ Figure"), "seq_table_fields": instructions.count("SEQ Table"),
            "first_table_header_fills": fills,
        }
        if key in {"ProposalDocument", "ArchitectureDesign", "SRS"}:
            check(key, "legacy and typed practice limits", all(token in visible for token in
                  ("1–13 legacy", "MCQ 50", "SQL 5", "essay 10", "mixed total 25", "MCQ 20", "SQL 2", "essay 3")))
        if key == "SRS":
            check(key, "current documentation baseline", baseline in visible)
            check(key, "OTP out of scope", "OTP" in visible and "not adopted" in visible)
            check(key, "Free/Pro UI-only", "Free/Pro is UI-only" in visible)
            check(key, "generic provider", "OpenAI-compatible provider" in visible and "LLM_API_KEY" in visible)
            check(key, "historical test evidence labelled", "Historical freeze evidence" in visible and "not rerun in Phase 5" in visible)
    failed = [item for item in assertions if item["status"] == "FAIL"]
    report = {
        "baseline": baseline,
        "total": len(assertions),
        "passed": len(assertions) - len(failed),
        "failed": len(failed),
        "assertions": assertions,
    }
    (verification / "fact-audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (verification / "style-audit.json").write_text(json.dumps(style, indent=2) + "\n", encoding="utf-8")
    print(f"ver1.3 audit: {report['total']} assertions, {report['failed']} failures")
    for item in failed:
        print("FAIL:", item["document"], item["id"], item["detail"])
    return 1 if failed else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--audit-only", action="store_true")
    mode.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args(argv)
    baseline = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if args.audit_only:
        recorded = args.output / "verification" / "build-baseline.txt"
        if recorded.exists():
            baseline = recorded.read_text(encoding="utf-8").strip()
        return audit(args.output, baseline)
    if args.metadata_only:
        metadata_only(args.output)
        return 0
    build(args.output, baseline)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""Step 4 programmatic verification of the final v1.2 Word documents.

    python scripts/verify_docx.py

Asserts every real table, column, FK, Compose service and OpenAPI endpoint is
mentioned in the three documents, and that no retired statement remains.
"""
import json
import sys
from pathlib import Path
from extract_docx_inventory import extract

ROOT = Path(__file__).resolve().parents[1]
ACA = ROOT / "docs/academic"
INTRO = json.load(open(ROOT / "docs/qa/schema-introspection.json", encoding="utf-8"))
FACTS = json.load(open(ROOT / "docs/qa/project-facts.json", encoding="utf-8"))
CTX = json.load(open(ROOT / "docs/diagrams/generated/system-context-model.json", encoding="utf-8"))
MAN = json.load(open(ROOT / "docs/diagrams/generated/manifest.json", encoding="utf-8"))

FILES = [
    ACA / "C1SE.70_ProposalDocument_DBCAS_ver1.2.docx",
    ACA / "C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx",
    ACA / "C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx",
]
problems = []
counts = {}


def require(label, condition, detail=""):
    counts[label] = int(bool(condition))
    if not condition:
        problems.append(f"{label}: {detail}")


def main():
    texts = {}
    db_rows = 0
    for f in FILES:
        d = extract(f)
        t = "\n".join(p["text"] for p in d["paragraphs"])
        t += "\n" + "\n".join(" ".join(r) for tb in d["tables"] for r in tb)
        texts[f.name] = t
        if "DatabaseDesign" in f.name:
            db_rows = sum(1 for tb in d["tables"] for r in tb[1:]
                          if len(r) >= 2 and r[1] in (
                              "integer", "bigint", "smallint", "text", "jsonb", "boolean",
                              "numeric", "timestamp with time zone", "character varying",
                              "ARRAY", "USER-DEFINED", "date") or
                          (len(r) >= 2 and r[1].startswith(("integer", "bigint", "smallint",
                                                            "character varying", "numeric",
                                                            "timestamp", "jsonb", "text",
                                                            "boolean", "ARRAY", "date"))))
    alltext = "\n".join(texts.values())

    table_names = [t["table"] for t in INTRO["tables"]]
    col_names = {c["name"] for t in INTRO["tables"] for c in t["columns"]}
    fk_names = [f["constraint"] for f in INTRO["foreign_keys"]]
    services = FACTS["compose_services_all"]
    paths = FACTS["openapi_paths"]

    missing_tables = [n for n in table_names if n not in alltext]
    missing_cols = sorted(c for c in col_names if c not in alltext)
    missing_fks = [n for n in fk_names if n not in alltext]
    missing_services = [s for s in services if s not in alltext]
    missing_paths = [p for p in paths if p not in alltext]
    missing_nodes = [n["id"] for n in CTX["nodes"] if n["id"] not in alltext]
    missing_flows = [f["id"] for f in CTX["flows"] if f["id"] not in alltext]

    total_columns = sum(len(t["columns"]) for t in INTRO["tables"])
    require("data-dictionary column rows", db_rows >= total_columns,
            f"{db_rows} < {total_columns}")
    require("tables N/N", not missing_tables, f"missing={missing_tables}")
    require("columns N/N", not missing_cols, f"missing={missing_cols[:20]}")
    require("FK constraints N/N", not missing_fks, f"missing={missing_fks[:10]}")
    require("compose services N/N", not missing_services, f"missing={missing_services}")
    require("OpenAPI paths N/N", not missing_paths, f"missing={missing_paths[:10]}")
    require("context nodes N/N", not missing_nodes, f"missing={missing_nodes}")
    require("context flows N/N", not missing_flows, f"missing={missing_flows}")

    retired = ["36 tables", "10 MCQ / 2 SQL / 1 Essay", "10 MCQ / 2 SQL / 1 essay",
               "13 questions / 60 minutes", "13-question / 60-minute contract",
               "FORMAL session", "new formal definitions", "administrators configure assessments"]
    found_retired = [r for r in retired if r in alltext]
    require("no retired statements", not found_retired, f"found={found_retired}")
    require("41 tables stated", "41 bảng" in alltext or "41 tables" in alltext)
    require("59 FKs stated", "59 khóa ngoại" in alltext or "59 foreign keys" in alltext)
    require("19 migrations stated", "19 migration" in alltext)
    require("exact count stated", "question_count" in alltext and "1–20" in alltext)
    require("SQL from validated bank stated", "SQL luôn từ ngân hàng" in alltext)
    require("two result flows stated", "IMMEDIATE" in alltext and "HUMAN_VERIFIED" in alltext)
    require("two-AI pipeline stated", "Prompt Builder" in alltext and "Evaluator" in alltext)
    require("5-item Admin stated", "5 mục" in alltext or "5-item" in alltext)
    for n in MAN["legacy_tables"]:
        require(f"legacy {n} shown", "legacy/retired" in alltext and n in alltext)
    for f in FILES:
        t = texts[f.name]
        require(f"version 1.2 in {f.name[:24]}", "1.2" in t)
        require(f"date in {f.name[:24]}", "2026-11-08" in t)
        require(f"[CẦN NGƯỜI ĐIỀN] in {f.name[:24]}", "[CẦN NGƯỜI ĐIỀN]" in t)
        require(f"Vietnamese in {f.name[:24]}", "bảng" in t or "khóa ngoại" in t)

    # cross-document consistency: shared terms in all three
    shared = ["41 bảng", "59 khóa ngoại", "Prompt Builder", "Evaluator", "IMMEDIATE",
              "HUMAN_VERIFIED", "legacy/retired", "question_count"]
    for term in shared:
        present = [f.name.split("_")[-1] for f in FILES if term in texts[f.name]]
        require(f"term '{term}' in all 3", len(present) == 3, f"only in {present}")

    print(f"verify_docx: {len(counts)} assertions; "
          f"tables={len(table_names)}/{len(table_names) - len(missing_tables)}, "
          f"distinct_column_names={len(col_names)}/{len(col_names) - len(missing_cols)}, "
          f"fks={len(fk_names)}/{len(fk_names) - len(missing_fks)}, "
          f"services={len(services)}/{len(services) - len(missing_services)}, "
          f"endpoints={len(paths)}/{len(paths) - len(missing_paths)}, "
          f"context nodes={len(CTX['nodes'])}/{len(CTX['nodes']) - len(missing_nodes)}, "
          f"context flows={len(CTX['flows'])}/{len(CTX['flows']) - len(missing_flows)}")
    if problems:
        for p in problems:
            print("FAIL:", p)
        sys.exit(1)
    print("PASS: every real name is present and no retired statement remains")


if __name__ == "__main__":
    main()

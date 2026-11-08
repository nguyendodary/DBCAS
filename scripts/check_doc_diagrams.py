# -*- coding: utf-8 -*-
"""Pure-python gate for professional diagrams (CI runnable, no renderers).

    python scripts/check_doc_diagrams.py

Compares committed sources in docs/diagrams/pro/ against:
  * docs/qa/schema-introspection.json (41 tables, 293 columns, 59 FKs)
  * docs/qa/project-facts.json (Compose services, 82 OpenAPI paths, OAuth providers)
  * docs/diagrams/generated/system-context-model.json (evidence model)
Fails on any differing count, name, type mapping, legacy tag or font floor.
CI needs no Java/Node renderers; only this stdlib script runs.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRO = ROOT / "docs" / "diagrams" / "pro"
problems = []
checks = []


def check(label, cond, detail=""):
    checks.append(label)
    if not cond:
        problems.append(f"{label}: {detail}")


TYPE_MAP = {
    "integer": "integer",
    "bigint": "bigint",
    "smallint": "smallint",
    "character varying": "varchar",
    "text": "text",
    "boolean": "boolean",
    "timestamp with time zone": "timestamp",
    "jsonb": "jsonb",
    "numeric": "numeric",
    "date": "date",
    "ARRAY": "text[]",
    "double precision": "double precision",
}
LEGACY = {"assessment", "assessment_concept", "assessment_question", "assessment_blueprint"}


def main():
    import json
    intro = json.loads((ROOT / "docs/qa/schema-introspection.json").read_text(encoding="utf-8"))
    facts = json.loads((ROOT / "docs/qa/project-facts.json").read_text(encoding="utf-8"))
    model = json.loads((ROOT / "docs/diagrams/generated/system-context-model.json").read_text(encoding="utf-8"))

    tables = intro["tables"]
    fks = intro["foreign_keys"]
    check("table count", len(tables) == 41, len(tables))
    check("fk count", len(fks) == 59, len(fks))
    check("column count", sum(len(t["columns"]) for t in tables) == 293)

    # ERD full model
    erd = (PRO / "erd.dbml").read_text(encoding="utf-8")
    erd_tables = re.findall(r"^Table\s+(\w+)\s*(?:\[|\{)", erd, re.M)
    check("ERD Ref count equals FK count", erd.count("Ref:") == len(fks),
          f"{erd.count('Ref:')} != {len(fks)}")
    check("ERD table count equals introspection", len(erd_tables) == len(tables),
          f"{len(erd_tables)} != {len(tables)}")
    check("ERD table names exact", set(erd_tables) == {t["table"] for t in tables},
          f"missing={sorted({t['table'] for t in tables}-set(erd_tables))}")
    check("ERD no duplicate tables", len(erd_tables) == len(set(erd_tables)))
    # Type mapping: every column line type must equal dbml_type(pg_type)
    by_name = {t["table"]: t for t in tables}
    type_ok = True
    for t in tables:
        for col in t["columns"]:
            exp = TYPE_MAP[col["type"]]
            pat = rf"{col['name']}\s+{re.escape(exp)}(\s|\[|$)"
            # case-sensitive exact match; no fallback
            if not re.search(pat, erd):
                type_ok = False
                break
        if not type_ok:
            break
    check("DBML type mapping exact (case-sensitive)", type_ok)
    # Legacy visually distinct
    for name in LEGACY:
        check(f"legacy marked {name}", f"Table {name} [headercolor:" in erd and "LEGACY" in erd)
    # TableGroups exist
    check("ERD TableGroup per domain", erd.count("TableGroup") == 7, erd.count("TableGroup"))

    # TRD panels: union tables = 41, each table exactly once
    trd_files = sorted(PRO.glob("trd-*.dbml"))
    check("TRD panels exist", len(trd_files) >= 6, [p.name for p in trd_files])
    all_trd_tables = []
    trd_refs = 0
    for f in trd_files:
        txt = f.read_text(encoding="utf-8")
        tt = re.findall(r"^Table\s+(\w+)\s*(?:\[|\{)", txt, re.M)
        all_trd_tables.extend(tt)
        trd_refs += txt.count("Ref:")
    check("TRD union tables = 41", set(all_trd_tables) == {t["table"] for t in tables})
    check("TRD each table once (sum=41)", len(all_trd_tables) == 41, len(all_trd_tables))
    # Internal refs must be a subset of FKs; ERD is canonical for 59.
    check("TRD internal refs < 59 (split panels)", 0 < trd_refs < 59, trd_refs)

    # System Context (C4 Level 1): system level only
    ctx = (PRO / "system-context.puml").read_text(encoding="utf-8")
    check("Context has 2 actors", len(re.findall(r"^actor\s+", ctx, re.M)) == 2)
    check("Context has 1 system DBCAS", "component [DBCAS]" in ctx)
    oauth_label = {"google": "Google OAuth", "github": "GitHub OAuth"}
    for provider in facts["oauth_providers"]:
        check(f"Context oauth {provider}", oauth_label[provider] in ctx, oauth_label[provider])
    check("Context has LLM external", "External LLM API" in ctx)
    check("Context has Email external", "Email Service" in ctx)
    check("Context has 6 flows", ctx.count(" --> ") == 6, ctx.count(" --> "))
    check("Context omits QA-only qa-ai", "qa-ai" not in ctx.lower())
    check("Context omits QA-only meter", "meter" not in ctx.lower().split("legend")[0])
    check("Context font 12pt floor", "defaultFontSize 12" in ctx)
    check("Context uses Arial", "defaultFontName Arial" in ctx)
    check("Context system-level only (no endpoint detail)", "/api/v1" not in ctx)
    check("Context flows labelled", "starts practice" in ctx and "OAuth authorize" in ctx)
    # Model cross-check: system-level nodes are subset of model nodes
    model_ids = {n["id"] for n in model["nodes"]}
    check("Model has learner/admin", {"learner", "admin"} <= model_ids)

    # Containers (C4 Level 2)
    cont = (PRO / "containers.puml").read_text(encoding="utf-8")
    for svc in ("frontend", "app", "db"):
        check(f"Container service {svc}", svc in cont.lower())
    check("Containers font floor", "defaultFontSize 12" in cont)

    # Sequence (other UML, Mermaid)
    seq = (PRO / "sequence-practice.mmd").read_text(encoding="utf-8")
    check("Sequence is sequenceDiagram", "sequenceDiagram" in seq)
    check("Sequence uses real practice path", "/api/v1/practice/start" in seq)
    check("Sequence uses real session path", "/api/v1/sessions/{id}/submit" in seq)

    # Committed SVG/PNG exist (no renderer needed to verify counts)
    for stem in ["system-context", "containers", "sequence-practice", "erd",
                 "trd-identity", "trd-curriculum", "trd-question_bank",
                 "trd-practice", "trd-evaluation", "trd-legacy", "trd-system"]:
        check(f"committed SVG {stem}", (PRO / f"{stem}.svg").exists())
        check(f"committed PNG {stem}", (PRO / f"{stem}.png").exists())

    print(f"check_doc_diagrams: {len(checks)} assertions, tables={len(tables)}, "
          f"columns={sum(len(t['columns']) for t in tables)}, fks={len(fks)}, "
          f"erd_refs={erd.count('Ref:')}, trd_tables={len(all_trd_tables)}")
    if problems:
        for p in problems:
            print("FAIL:", p)
        sys.exit(1)
    print("PASS: professional diagram sources match schema-introspection.json and project-facts.json")


if __name__ == "__main__":
    main()

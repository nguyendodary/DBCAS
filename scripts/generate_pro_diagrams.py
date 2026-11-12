# -*- coding: utf-8 -*-
"""Generate professional diagram sources from repository facts.

Outputs committed sources:
  docs/diagrams/pro/system-context.puml
  docs/diagrams/pro/containers.puml
  docs/diagrams/pro/sequence-practice.mmd
  docs/diagrams/pro/erd.dbml          (41 tables, 59 refs)
  docs/diagrams/pro/trd-*.dbml        (41 tables split per domain)

Inputs:
  docs/qa/schema-introspection.json
  docs/qa/project-facts.json
  docs/diagrams/generated/system-context-model.json

Run: python scripts/generate_pro_diagrams.py
Renders are produced by scripts/prerender_diagrams.py (SVG + 300-dpi PNG).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRO = ROOT / "docs" / "diagrams" / "pro"
INTRO = json.loads((ROOT / "docs/qa/schema-introspection.json").read_text(encoding="utf-8"))
FACTS = json.loads((ROOT / "docs/qa/project-facts.json").read_text(encoding="utf-8"))
MODEL = json.loads((ROOT / "docs/diagrams/generated/system-context-model.json").read_text(encoding="utf-8"))

LEGACY = {"assessment", "assessment_concept", "assessment_question", "assessment_blueprint"}

# Postgres type -> DBML type (shared with check_doc_diagrams.py)
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

DOMAINS = {
    "identity": ["account", "account_identity", "account_role", "account_role_audit",
                 "role", "user_profile", "refresh_session", "login_throttle",
                 "oauth_handoff", "password_reset_token", "password_reset_audit"],
    "curriculum": ["course_learning_outcome", "concept", "concept_dependency",
                   "concept_competency", "clo_concept"],
    "question_bank": ["question", "mcq_option", "rubric", "sql_test_dataset",
                      "question_concept", "question_candidate", "question_translation"],
    "practice": ["assessment_session", "session_question_plan", "session_start_request",
                 "attempt", "selection_log", "adaptive_event"],
    "evaluation": ["evaluation_record", "grade_review", "grade_edit_audit",
                   "grading_job", "competency_gap", "result_release_event", "llm_cache"],
    "legacy": ["assessment", "assessment_blueprint", "assessment_concept", "assessment_question"],
    "system": ["system_setting"],
}


def dbml_type(pg_type):
    return TYPE_MAP[pg_type]


def pk_columns(table):
    for c in table["constraints"]:
        if c["type"] == "p":
            return set(c["columns"])
    return set()


def table_by_name():
    return {t["table"]: t for t in INTRO["tables"]}


def format_table(t):
    pks = pk_columns(t)
    lines = []
    name = t["table"]
    if name in LEGACY:
        lines.append(f"Table {name} [headercolor: #d3d3d3] {{")
        lines.append("  Note: 'LEGACY - historical exam rows only'")
    else:
        lines.append(f"Table {name} {{")
    for col in t["columns"]:
        pg = col["type"]
        dtype = dbml_type(pg)
        flags = []
        if col["name"] in pks:
            flags.append("pk")
        if not col["nullable"] and col["name"] not in pks:
            flags.append("not null")
        flag_txt = f" [{', '.join(flags)}]" if flags else ""
        lines.append(f"  {col['name']} {dtype}{flag_txt}")
    lines.append("}")
    return "\n".join(lines)


def format_ref(fk):
    src, dst = fk["source"], fk["destination"]
    cols, refs = fk["columns"], fk["reference_columns"]
    dl = fk["on_delete"].lower()
    ul = fk["on_update"].lower()
    if len(cols) == 1:
        line = f"Ref: {src}.{cols[0]} > {dst}.{refs[0]} [delete: {dl}, update: {ul}]"
    else:
        line = f"Ref: {src}.({', '.join(cols)}) > {dst}.({', '.join(refs)}) [delete: {dl}, update: {ul}]"
    return line


def generate_erd():
    tables = INTRO["tables"]
    parts = ["// Entity Relationship Diagram (crow's foot) - generated from schema-introspection.json",
             "// 41 tables, 293 columns, 59 FKs", ""]
    parts.append("\n\n".join(format_table(t) for t in tables))
    parts.append("")
    parts.append("// Foreign keys (59)")
    for fk in INTRO["foreign_keys"]:
        parts.append(format_ref(fk))
    # TableGroups per domain
    parts.append("")
    for dname, members in DOMAINS.items():
        parts.append(f"TableGroup {dname} {{")
        for m in members:
            parts.append(f"  {m}")
        parts.append("}")
    return "\n".join(parts) + "\n"


def generate_trd(domain, members):
    by_name = table_by_name()
    member_set = set(members)
    tables = [by_name[m] for m in members]
    parts = [f"// Table Relationship - {domain} domain (generated)",
             f"// Tables: {', '.join(members)}", ""]
    parts.append("\n\n".join(format_table(t) for t in tables))
    parts.append("")
    parts.append("// Internal FKs (both ends in this domain)")
    internal = [f for f in INTRO["foreign_keys"] if f["source"] in member_set and f["destination"] in member_set]
    for fk in internal:
        parts.append(format_ref(fk))
    cross = [f for f in INTRO["foreign_keys"] if f["source"] in member_set and f["destination"] not in member_set]
    if cross:
        parts.append("")
        parts.append("// Cross-domain FKs (source in this domain; see ERD for full refs)")
        for fk in cross:
            parts.append(f"// {fk['constraint']}: {fk['definition']}")
    return "\n".join(parts) + "\n"


def generate_system_context():
    # C4 Level 1 from Compose + facts only (system level; no QA-only/internal containers).
    # Actors from account_role (Learner/Administrator); externals from oauth_providers + LLM env + SMTP.
    domains_ok = set()
    for members in DOMAINS.values():
        domains_ok.update(members)
    assert domains_ok == {t["table"] for t in INTRO["tables"]}
    assert len(INTRO["foreign_keys"]) == 59
    return """@startuml system-context
title System Context Diagram (C4 Level 1) - DBCAS
skinparam defaultFontName Arial
skinparam defaultFontSize 12
skinparam dpi 300
skinparam actorStyle awesome
skinparam backgroundColor white
skinparam shadowing false

' Actors (Person) - from account_role values
actor "Learner" as learner
actor "Administrator" as admin

' System in scope (Software System) - from docker-compose.local.yml service app + frontend
component [DBCAS] as dbcas #dceaf7

' External systems - from config + routers + services (exact names)
component [External LLM API] as llm #f3e2ef
component [Google OAuth] as google #f3e2ef
component [GitHub OAuth] as github #f3e2ef
component [Email Service] as email #f3e2ef

learner --> dbcas : starts practice, views results
admin --> dbcas : curates questions, reviews grading
dbcas --> llm : prompts + evaluations
dbcas --> google : OAuth authorize + callback
dbcas --> github : OAuth authorize + callback
dbcas --> email : password-reset email via SMTP

legend bottom
  |= System |
  | Learner / Administrator = actor |
  | DBCAS = system in scope |
  | External System = external system |
  | Arrows = system-level flows (paths detailed in sequence diagram) |
endlegend

@enduml
"""


def generate_containers():
    return """@startuml containers
title Container Diagram (C4 Level 2) - DBCAS
skinparam defaultFontName Arial
skinparam defaultFontSize 12
skinparam dpi 300
skinparam backgroundColor white
skinparam shadowing false

actor "Learner" as learner
actor "Administrator" as admin

component [SPA Frontend (Nginx)] as frontend #dceaf7
component [FastAPI API (app)] as app #dceaf7
database [PostgreSQL 17 (db)] as db #fff8dc
component [Mailpit SMTP :1025] as mailpit #fdf1d6
component [SQL Sandbox (ephemeral, --network none)] as sandbox #e8e2f5
component [Prompt Builder] as prompt_builder #e8e2f5

component [External LLM API] as llm #f3e2ef
component [Google OAuth] as google #f3e2ef
component [GitHub OAuth] as github #f3e2ef
component [Email Service] as email #f3e2ef

learner --> frontend : HTTPS SPA
admin --> frontend : HTTPS admin SPA
frontend --> app : HTTP /api/v1 via proxy
app --> db : SQL read/write
app --> sandbox : SQL answers via socket
app --> prompt_builder : prompt for Evaluator
app --> llm : chat/completions
app --> google : OAuth redirect
app --> github : OAuth redirect
app --> mailpit : password-reset email

legend bottom
  |= Containers |
  | frontend / app / db / mailpit = Compose services |
  | sandbox / Prompt Builder = runtime components |
  | External systems = LLM, OAuth, Email |
endlegend

@enduml
"""


def generate_sequence():
    # Practice lifecycle from OpenAPI + services (EASY/MEDIUM/HARD, count 1-20).
    return """sequenceDiagram
    title Practice Session Lifecycle - DBCAS
    autonumber
    participant Learner
    participant Frontend as SPA (frontend)
    participant API as FastAPI (app)
    participant DB as PostgreSQL (db)
    participant Sandbox as SQL Sandbox
    participant LLM as External LLM API

    Learner->>Frontend: GET / (SPA)
    Frontend->>API: POST /api/v1/practice/start (1-20, default 5)
    API->>DB: INSERT assessment_session + plan (session_question_plan)
    DB-->>API: session_id + questions (MCQ/SQL/essay)
    API-->>Frontend: questions JSON
    Learner->>Frontend: answers (draft via /draft)
    Frontend->>API: POST /api/v1/sessions/{id}/submit
    API->>Sandbox: execute SQL (ephemeral container, --network none)
    Sandbox-->>API: result rows
    API->>DB: write attempt + evaluation_record
    API->>LLM: POST /evaluations/overall (Prompt Builder -> Evaluator)
    LLM-->>API: structured JSON (Evaluation)
    API->>DB: publish via result_release_event (IMMEDIATE / HUMAN_VERIFIED)
    API-->>Frontend: results + competency gaps
    Frontend-->>Learner: render exam / evaluations / history
"""


def main():
    PRO.mkdir(parents=True, exist_ok=True)
    (PRO / "system-context.puml").write_text(generate_system_context(), encoding="utf-8")
    (PRO / "containers.puml").write_text(generate_containers(), encoding="utf-8")
    (PRO / "sequence-practice.mmd").write_text(generate_sequence(), encoding="utf-8")
    (PRO / "erd.dbml").write_text(generate_erd(), encoding="utf-8")
    for dname, members in DOMAINS.items():
        (PRO / f"trd-{dname}.dbml").write_text(generate_trd(dname, members), encoding="utf-8")
    print(f"generated: system-context.puml, containers.puml, sequence-practice.mmd, erd.dbml, {len(DOMAINS)} trd-*.dbml -> {PRO}")


if __name__ == "__main__":
    main()

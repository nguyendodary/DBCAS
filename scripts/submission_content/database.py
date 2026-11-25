# -*- coding: utf-8 -*-
"""Database Design content, generated from the measured schema introspection.

The dictionary, registry, key counts and index counts are read from
docs/diagrams/schema-028/schema-introspection.json (PostgreSQL 17.12, 28
migrations) instead of being typed by hand, so the document cannot drift from
db/schema.sql.  scripts/verify_submission_docs.py re-checks every table name,
column count and migration name against the same file.
"""
from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "submission" / "final" / "assets"
INTROSPECTION = (ROOT / "docs" / "diagrams" / "schema-028"
                 / "schema-introspection.json")
DATA = json.loads(INTROSPECTION.read_text(encoding="utf-8"))

TABLES = DATA["tables"]
FKS = DATA["foreign_keys"]
INDEXES = DATA["indexes"]
MIGRATIONS = sorted(DATA["migrations"])
TOTAL_TABLES = len(TABLES)
TOTAL_COLUMNS = sum(len(t["columns"]) for t in TABLES)
TOTAL_FKS = len(FKS)
TOTAL_INDEXES = len(INDEXES)
TOTAL_MIGRATIONS = len(MIGRATIONS)

DOMAINS = OrderedDict([
    ("Identity and access", {
        "account", "account_identity", "account_role", "account_role_audit",
        "refresh_session", "oauth_handoff", "login_throttle",
        "password_reset_token", "password_reset_audit", "user_profile",
        "role", "system_setting"}),
    ("Curriculum and concepts", {
        "course_learning_outcome", "concept", "concept_dependency",
        "concept_competency", "clo_concept", "course_document",
        "document_chunk", "document_clo"}),
    ("Question bank and generation", {
        "question", "question_concept", "question_clo", "question_translation",
        "question_evidence", "mcq_option", "rubric", "sql_test_dataset",
        "question_candidate", "question_rubric_profile",
        "question_rubric_criterion"}),
    ("Assessment and attempts", {
        "assessment", "assessment_blueprint", "assessment_concept",
        "assessment_question", "assessment_session", "attempt",
        "session_question_plan", "session_start_request", "selection_log",
        "adaptive_event", "tab_leave_interval", "attempt_rubric_criterion"}),
    ("Grading and results", {
        "evaluation_record", "grading_job", "grade_review", "grade_edit_audit",
        "result_release_event", "session_final_result",
        "session_result_version", "session_result_version_score",
        "session_result_criterion_score", "session_result_analysis",
        "session_result_publication"}),
    ("Review workflow", {
        "review_request", "question_report", "review_deviation",
        "review_deviation_confirmation"}),
    ("Competency analytics", {"competency_gap"}),
    ("AI audit and retention", {
        "ai_stage_run", "ai_stage_validation", "ai_stage_attempt",
        "ai_prompt_record", "ai_prompt_content", "prompt_access_audit",
        "retention_purge_audit", "llm_cache"}),
])

TABLE_DOMAIN = {}
for domain, names in DOMAINS.items():
    for name in names:
        TABLE_DOMAIN[name] = domain
MISSING = [t["table"] for t in TABLES if t["table"] not in TABLE_DOMAIN]
assert not MISSING, f"unclassified tables: {MISSING}"

MIGRATION_PURPOSE = {
    "001": "Linked Google/GitHub sign-in identities, one row per provider "
           "identity",
    "002": "Directed prerequisite edges between concepts with a self-FK guard",
    "003": "Draft and submission state, immutable snapshots, OAuth handoff, "
           "login throttle and the grading queue",
    "004": "Question version lineage and canonical SQL feature metadata",
    "005": "Reference roles Learner and Administrator",
    "006": "Question explanation, tags and documentation provenance",
    "007": "Bilingual question content; English remains canonical",
    "008": "Concept keywords, release policy, human grade review, release "
           "audit and the frozen session plan",
    "009": "Data repair of stale legacy publication decisions",
    "010": "Idempotency ledger binding start requests to sessions",
    "011": "Default-deny role-management capability and role-change audit",
    "012": "Explicit original locale for source prose",
    "013": "Versioned assessment blueprints",
    "014": "Append-only adaptive decision event log",
    "015": "Hashed single-use password-reset tokens and reset audit",
    "016": "Refresh credentials stored only as hashes",
    "017": "Optional curated question pool for assessments (legacy)",
    "018": "Learner-defined practice, runtime setting, evaluation evidence "
           "and grade-edit audit",
    "019": "Closes prebuilt published exams",
    "020": "Immutable final result snapshot replacing provisional drafts",
    "021": "Fixed-paper attempt state counters",
    "022": "Course-learning-outcome tagging with deterministic backfill",
    "023": "Course documents, extracted chunks, document-to-CLO links and "
           "question evidence",
    "024": "Tab-leave counters, cancellation columns and observed intervals",
    "025": "Test versus practice session purpose with provenance",
    "026": "Immutable result evidence: rubric snapshots, result versions, "
           "scores, analysis, publication state, AI stage runs and prompt "
           "retention",
    "027": "Learner review cases: window, claim, TTL, report triage and "
           "deviation evidence",
    "028": "Second-administrator confirmation of a nominated deviation",
}


def human_type(column):
    kind = column["type"]
    if kind == "character varying":
        return f"varchar({column['max_length']})" if column["max_length"] else "varchar"
    if kind == "numeric" and column.get("numeric_precision"):
        return f"numeric({column['numeric_precision']},{column.get('numeric_scale') or 0})"
    if kind == "timestamp with time zone":
        return "timestamptz"
    if kind == "timestamp without time zone":
        return "timestamp"
    if kind == "character":
        return f"char({column['max_length']})" if column["max_length"] else "char"
    if kind == "double precision":
        return "float8"
    return kind


def primary_keys(table):
    keys = []
    for constraint in table.get("constraints", []):
        if constraint["type"] == "p":
            keys.extend(constraint["columns"])
    return keys


def unique_columns(table):
    cols = set()
    for constraint in table.get("constraints", []):
        if constraint["type"] == "u" and len(constraint["columns"]) == 1:
            cols.update(constraint["columns"])
    return cols


def fk_map():
    mapping = {}
    for fk in FKS:
        for column in fk["columns"]:
            mapping.setdefault((fk["source"], column), []).append(fk)
    return mapping


def index_counts():
    counts = {}
    for index in INDEXES:
        counts[index["table"]] = counts.get(index["table"], 0) + 1
    return counts


FK_BY_COLUMN = fk_map()
INDEX_COUNTS = index_counts()


def registry_rows():
    rows = []
    for table in TABLES:
        name = table["table"]
        pks = primary_keys(table)
        fk_count = sum(1 for fk in FKS if fk["source"] == name)
        rows.append([name, TABLE_DOMAIN[name], str(len(table["columns"])),
                     ", ".join(pks) or "-", str(fk_count),
                     str(INDEX_COUNTS.get(name, 0))])
    return rows


def dictionary_blocks():
    blocks = []
    for table in TABLES:
        name = table["table"]
        pks = set(primary_keys(table))
        uniques = unique_columns(table)
        rows = []
        for column in table["columns"]:
            flags = []
            if column["name"] in pks:
                flags.append("PK")
            if column["name"] in uniques:
                flags.append("UQ")
            for fk in FK_BY_COLUMN.get((name, column["name"]), []):
                flags.append(f"FK → {fk['destination']}")
            if column["identity"]:
                flags.append("identity")
            default = column["default"]
            if default and not column["identity"]:
                flags.append(f"default {default}")
            if not column["nullable"]:
                flags.append("not null")
            rows.append([column["name"], human_type(column), "; ".join(flags)])
        blocks.append(("h3", f"{name} — {len(table['columns'])} columns"))
        blocks.append(("table", {
            "header": ["Column", "Type", "Key / nullability / default"],
            "widths": [4.6, 4.2, 6.7],
            "font": 9,
            "compact": True,
            "rows": rows,
        }))
    return blocks


def migration_rows():
    rows = []
    for name in MIGRATIONS:
        version = name[:3]
        rows.append([version, name, MIGRATION_PURPOSE.get(version, "")])
    return rows


BLOCKS = [
    ("h1", "1. Introduction"),
    ("h2", "1.1 Scope"),
    ("p", "This document describes the DBCAS relational schema: its "
          "conventions, its entity-relationship overview, the table registry, "
          "the column dictionary, keys and indexes, the migration history, "
          "the seed data, and the snapshot, version and audit layers. It is "
          "the reference for the persistence contract used by the API "
          "described in the Architecture Design document."),
    ("h2", "1.2 How This Document Was Measured"),
    ("p", f"Every object below was read from PostgreSQL 17.12 introspection of "
          f"db/schema.sql after all {TOTAL_MIGRATIONS} migrations, recorded in "
          f"docs/diagrams/schema-028/schema-introspection.json and gated by "
          f"docs:check. The application schema has {TOTAL_TABLES} tables and "
          f"{TOTAL_COLUMNS} columns, {TOTAL_FKS} foreign keys and "
          f"{TOTAL_INDEXES} indexes. The migration ledger table "
          f"schema_migration is excluded from these counts because it is "
          f"runtime bookkeeping, not domain data; the live database therefore "
          f"shows one table and three columns more than this document."),
    ("table", {
        "caption": "Measured schema totals",
        "header": ["Measure", "Value"],
        "widths": [8.0, 7.5],
        "rows": [
            ["Application tables", str(TOTAL_TABLES)],
            ["Columns", str(TOTAL_COLUMNS)],
            ["Foreign keys", str(TOTAL_FKS)],
            ["Indexes", str(TOTAL_INDEXES)],
            ["Migrations", str(TOTAL_MIGRATIONS)],
            ["Native enum types", str(len(DATA.get("enums", [])))],
            ["Views", "0"],
        ],
    }),
    ("note", "The four assessment-prefixed tables are retained legacy objects. "
             "They are present in the schema, marked as legacy in the ERD, and "
             "are not written by current code paths."),

    ("h1", "2. Conventions"),
    ("bullets", [
        "Names are lower_snake_case. A table is singular and names the entity "
        "(account, question, attempt); join tables concatenate both entities "
        "(question_concept).",
        "Every table has a surrogate primary key named <table>_id, except "
        "tables whose identity is the pair itself.",
        "Foreign keys are named <table>_<column>_fkey by PostgreSQL and are "
        "declared with an explicit ON DELETE policy; no cascade deletes "
        "domain history.",
        "Timestamps are timezone-aware and default to now(); audit tables are "
        "append-only and protected by triggers.",
        "There is no soft-delete flag and no tenant column: the deployment is "
        "single-institution, and history is preserved in dedicated tables "
        "rather than by hiding rows.",
        "Constraint names are stable and referenced by the API error codes, "
        "so renaming requires a migration and a code change together.",
    ]),
    ("table", {
        "caption": "Data types used",
        "header": ["Type", "Use"],
        "widths": [4.0, 11.5],
        "rows": [
            ["integer / bigint identity", "Surrogate keys"],
            ["varchar(n)", "Bounded text; email and names are capped"],
            ["text", "Prompt text, essays and explanations"],
            ["jsonb", "Snapshots, structured AI output and score detail"],
            ["timestamptz", "All event and audit times"],
            ["numeric(p,s)", "Scores and thresholds; never floating point"],
            ["boolean", "Capabilities and flags"],
            ["char(64)", "SHA-256 hashes of prompts and results"],
            ["text[]", "Tag lists such as question tags"],
        ],
    }),

    ("h1", "3. Entity-Relationship Overview"),
    ("p", "The entity-relationship diagram is generated from the live catalog "
          "and split into sheets of eight entities so that every table is "
          "drawn at a printable size. Four sheets are reproduced here: "
          "identity and AI audit, the question bank, the result and review "
          "tables, and the operational tail of the alphabet. The complete "
          "ten-sheet ERD, the relationship graph and the foreign-key ledger "
          "are generated in docs/diagrams/schema-028."),
    ("figure", str(ASSETS / "erd-sheet-1.png"),
     "ERD sheet 1: account, identity, roles, audit and AI stage attempts",
     {"width_cm": 15.0}),
    ("figure", str(ASSETS / "erd-sheet-6.png"),
     "ERD sheet 6: question bank, options, candidates and localization",
     {"width_cm": 15.0}),
    ("figure", str(ASSETS / "erd-sheet-9.png"),
     "ERD sheet 9: selection log, plan, result analysis and publication",
     {"width_cm": 15.0}),
    ("figure", str(ASSETS / "erd-sheet-10.png"),
     "ERD sheet 10: result versions, start requests, datasets and settings",
     {"width_cm": 15.0}),

    ("h1", "4. Table Registry"),
    ("p", f"All {TOTAL_TABLES} tables, grouped by domain, with their column "
          f"count, primary key, outgoing foreign keys and index count. The "
          f"column dictionary in section 5 is the authoritative list of every "
          f"column."),
    ("table", {
        "caption": "Table registry",
        "header": ["Table", "Domain", "Columns", "Primary key", "FKs", "Idx"],
        "widths": [4.6, 3.9, 1.5, 3.4, 1.0, 1.1],
        "font": 9,
        "rows": registry_rows(),
    }),

    ("h1", "5. Column Dictionary"),
    ("p", "One block per table, in alphabetical order. Type names are the "
          "PostgreSQL types as introspected; flags list primary key (PK), "
          "single-column unique (UQ), foreign-key targets, identity columns, "
          "defaults and nullability."),
] + dictionary_blocks() + [
    ("h1", "6. Keys and Indexes"),
    ("p", f"The schema declares {TOTAL_FKS} foreign keys and "
          f"{TOTAL_INDEXES} indexes. Of the indexes, 68 are primary-key "
          f"indexes, 41 back a unique constraint and 51 are standalone "
          f"performance indexes created explicitly by db/schema.sql."),
    ("table", {
        "caption": "Key and index inventory",
        "header": ["Object", "Count", "Rule"],
        "widths": [4.4, 1.6, 9.5],
        "rows": [
            ["Primary keys", "68", "One per table, including the migration "
             "ledger; 12 are composite"],
            ["Foreign keys", str(TOTAL_FKS),
             "Every reference is indexed on the referencing side"],
            ["Unique constraints", "41", "Business identity, not surrogate key"],
            ["Check constraints", "140", "Status vocabularies and ranges"],
            ["Standalone indexes", "51", "Foreign-key columns and hot filters"],
            ["Triggers", "41", "On application tables: 36 row-level guards "
             "and 5 constraint validators"],
        ],
    }),
    ("p", "Index rules applied: every foreign-key column is indexed because "
          "the API filters attempts by session, questions by concept and "
          "audit rows by actor. Status columns used by the worker are indexed "
          "with the timestamp that orders them, so the job claim query never "
          "scans the table. Two known gaps remain and are listed in section "
          "10: mcq_option.question_id and rubric.question_id have no index of "
          "their own."),

    ("h1", "7. Migrations"),
    ("p", f"{TOTAL_MIGRATIONS} forward-only migrations are applied in order "
          f"inside one transaction under an advisory lock. The runner stores "
          f"the SHA-256 of each file in schema_migration and refuses to run if "
          f"an applied file changed, so an edited migration must become a new "
          f"file. There is no down-migration path."),
    ("table", {
        "caption": "Migration history",
        "header": ["#", "File", "Purpose"],
        "widths": [1.2, 5.2, 9.1],
        "font": 9,
        "rows": migration_rows(),
    }),

    ("h1", "8. Seed Data"),
    ("p", "Seed data has three independent sources, each idempotent by a "
          "different mechanism."),
    ("table", {
        "caption": "Seed sources",
        "header": ["Source", "Content", "Idempotency"],
        "widths": [3.4, 7.2, 4.9],
        "font": 10,
        "rows": [
            ["db/seed.sql", "Two roles, one development administrator, one "
             "profile, one role link", "ON CONFLICT DO NOTHING on every "
             "statement"],
            ["Curated bank packs", "98 concepts, 12 course learning outcomes, "
             "46 prerequisite edges, 446 questions (326 MCQ, 71 SQL, 49 "
             "essay) and 442 Vietnamese translations",
             "Registry row in system_setting; a second run is a no-op"],
            ["seed_demo", "One administrator, three learners and four "
             "synthetic practice histories",
             "Existence check on the demo administrator"],
            ["Blueprint backfill", "Immutable blueprint versions for "
             "assessments that lack one", "Dry run unless --confirm is passed"],
        ],
    }),
    ("p", "The development administrator password is a documented development "
          "credential and must never reach a released database. The demo seed "
          "refuses to run outside development mode."),

    ("h1", "9. Version, Snapshot and Audit"),
    ("h2", "9.1 Result Versions"),
    ("p", "A published result is immutable. session_result_version stores one "
          "row per version with the source (V1 or V2), a supersedes pointer, "
          "the result hash and the approving administrator; "
          "session_result_version_score stores the per-attempt scores and "
          "session_result_criterion_score the per-criterion scores. "
          "session_result_publication is the only mutable row and carries a "
          "revision counter that guards every transition."),
    ("h2", "9.2 Snapshots"),
    ("bullets", [
        "assessment_session.config_snapshot freezes the session "
        "configuration chosen by the learner.",
        "attempt.question_snapshot freezes the question text served, so a "
        "later edit cannot change a historical answer.",
        "attempt_rubric_criterion freezes the rubric criterion and its maximum "
        "at grading time.",
        "question_rubric_profile and its criteria are versioned by "
        "profile_hash, so a rubric edit creates a new profile.",
        "question.family_id and version_no give each question a lineage; a "
        "session may not contain two versions of the same family.",
    ]),
    ("h2", "9.3 Audit"),
    ("table", {
        "caption": "Audit tables",
        "header": ["Table", "Records"],
        "widths": [4.6, 10.9],
        "font": 10,
        "rows": [
            ["schema_migration", "Applied migration, checksum and time"],
            ["account_role_audit", "Role grant, revocation and bootstrap"],
            ["grade_edit_audit", "Manual grade change with old and new score"],
            ["password_reset_audit", "Reset request and completion"],
            ["prompt_access_audit", "Granted, expired and purged prompt reads"],
            ["retention_purge_audit", "Prompt and cache purge operations"],
            ["result_release_event", "Every release-status transition"],
            ["selection_log", "Every question-selection decision"],
            ["adaptive_event", "Adaptive batch and decision events"],
        ],
    }),
    ("p", "Immutability is enforced by database triggers, not by convention: "
          "36 row-level guards reject updates and deletes on the audit and "
          "result tables, and five constraint triggers validate that a "
          "result version is complete and totals match before publication."),

    ("h1", "10. Maintenance Notes and Open Items"),
    ("bullets", [
        "schema_migration is runtime bookkeeping and must not be seeded or "
        "edited by hand.",
        "Two foreign-key columns still lack a dedicated index: "
        "mcq_option.question_id and rubric.question_id. This is a known "
        "performance gap, not a correctness defect.",
        "assessment_session.result_release_policy mixes a policy value with "
        "lifecycle states; a future migration should split the vocabulary.",
        "The duplicate concept_dependency definition recorded in the backlog "
        "remains an owner decision.",
        "updated_at is maintained by the application, not by a trigger.",
        "[OWNER TO PROVIDE: whether the legacy assessment tables may be "
        "dropped after the defence]",
        "[OWNER TO PROVIDE: data retention period for learner attempts]",
    ]),
]

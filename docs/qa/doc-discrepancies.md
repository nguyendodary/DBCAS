# Word-document discrepancy list — before editing (2026-11-07)

Sources of truth used for this list (all derived, not recalled):

- `docs/qa/schema-introspection.json` — real PostgreSQL 17 introspection of
  `db/schema.sql`: **41 tables, 293 columns, 59 foreign keys, 87 indexes,
  0 enum types, 19 migration files**.
- `docs/diagrams/diagram-inventory.json` — the same counts/names, used by
  `diagrams:check`.
- `docker-compose.local.yml`, `docker-compose.qa.yml`,
  `docker-compose.real-qa.yml`, `backend/app/routers/*`, `app.openapi()`
  (**82 paths / 93 operations**), `frontend/src/App.jsx` (**23 routes**),
  `frontend/src/components/Layout.jsx` (5-item Admin nav),
  `backend/app/services/prompt_builder.py`, `evaluation_pipeline.py`,
  `practice_generation.py`, `practice_selection.py`,
  `db/migrations/018*` and `019*`, `docs/qa/task-audit.md`.
- `_review/docx-work/before.json` — full text/table/image extraction of the
  four `ver1.1.docx` files (originals backed up to `docs/_backup-docx-20261107/`,
  which is git-ignored per CONTRIBUTING rule 3).

## Counts by type (distinct discrepancy items)

| Type | Items |
| --- | --- |
| wrong | 5 |
| missing | 9 |
| extra | 4 |
| outdated | 4 |
| **Total** | **22** |

## Discrepancy table

| Document | Section / Diagram | What the doc says | What the project really has | Type | Fix |
| --- | --- | --- | --- | --- | --- |
| Proposal | §Data & Storage Tier, FR/NFR, Table 6 | "PostgreSQL 17 database (36 tables)" | 41 tables / 293 columns / 59 FKs | wrong | Replace every "36 tables" with 41; add full data dictionary |
| Architecture | §1, §2, §4, §7, ERD text (14 occurrences) | "36 tables" | 41 tables | wrong | Replace all occurrences; regenerate ERD/TRD |
| Database | §1 Table 1 "Table Overview" | "36 tables" | 41 tables | wrong | Regenerate table overview from introspection |
| Proposal | Table 6, FR08–FR16, §scope | "New formal: 13 questions / 60 minutes (10 MCQ / 2 SQL / 1 Essay)", "10/2/1 for new standard definitions" (9 occurrences) | No formal/prebuilt exams; learner-defined practice with `question_count` 1–20 (default 5), balanced `mcq`/`sql`/`essay` targets | extra | Remove the fixed 10/2/1 contract; describe learner-defined exact count |
| Architecture | §4.1, §6, use cases (6 occurrences of 10/2/1, 16 of 13-q/60-min) | "standard 13-question / 60-minute contract (10 MCQ / 2 SQL / 1 essay)" | No 13-question/60-minute contract; practice expiry is 30 minutes, count is learner-chosen | extra | Remove contract; state real session rules |
| Database | §3, §5 | 10/2/1 mix and 60-minute formal contract | Learner-defined count, 30-minute session | extra | Correct to real behaviour |
| Proposal / Architecture / Database / UserStories | FR, use cases, flows (108 occurrences) | "FORMAL" vs "PRACTICE" session types | Only learner-defined practice sessions exist; `assessment_session.assessment_id` is nullable since migration 018 | extra | Replace with the single learner-defined practice concept |
| Proposal | §FR, Table 7, Table 11 (7 occurrences) | "administrators configure assessments with target concepts … create exams" | No exam creation; Admin has exactly 5 screens: Cohort, Grading, Accounts, Bank/CLO, System; only a global `result_flow` setting | extra | Remove exam-creation use cases; add 5-item Admin |
| Architecture / Database | §3, §4, §7 (23 occurrences) | `AssessmentBlueprint` / blueprints as active definitions | Blueprints and prebuilt exams are retired; migration 019 sets all published exams `closed`; exam tables are kept only for historical rows | outdated | Mark as legacy/retired, keep in ERD |
| Proposal | Figure 12.1 System Context Diagram | 6 nodes / 21 flows, actor+external-system set frozen at v1.1 | Real Compose services: `frontend`, `app`, `db`, `mailpit`, `init`, `executor-image` (+ `qa-ai`, real-qa meter); external: LLM provider, Google/GitHub OAuth, Mailpit, Docker sandbox; actors Learner/Admin | wrong | Regenerate from Compose/OpenAPI with labeled directed flows |
| Architecture | Figure 7 ERD, Figure 8 Table Relationship Diagram (9 images) | ERD of "36 tables"; TRD "predates the later security, release and evidence extensions" | 41 tables, 59 FKs, all columns/types/nullability from introspection | wrong | Regenerate both diagrams from `schema-introspection.json` |
| Database | Figure 1 ERD, Figure 2 Table Relationship Diagram (4 images) | Old ERD/TRD | Same as above | wrong | Replace with regenerated high-resolution figures |
| All three | §ERD / §Table overview | No legacy/retired note | `assessment`, `assessment_concept`, `assessment_question`, `assessment_blueprint` exist only for historical exam data; no API creates them; migration 019 closes published exams | missing | Add explicit legacy section + mark legacy entities in ERD |
| All three | Migration list | Lists migrations up to 017 (validator hard-coded 17) | 19 migrations (018 learner-practice evaluations, 019 archive prebuilt exams) | missing | Regenerate migration list; `diagrams:check` now derives 19 |
| Proposal / Architecture | §FR / §AI | No exact-count guarantee, no "SQL always from validated bank", no `generation_diagnostics` reason codes | `ai_type_targets`, `mixed_plan`, exact per-type counts, `bank_mixed`, reason codes (`mcq_options`, `schema`, `duplicate`, …) | missing | Add verified FR/NFR + traceability table |
| Architecture | §AI pipeline | LLM Provider + Evaluator | Two-AI pipeline: Prompt Builder (local/template fallback, `prompt_hash`, `builder_fallback`) → Evaluator (external LLM, `evaluator_fallback`, rule fallback); SQL executed in Docker sandbox, never by AI | missing | Add pipeline description and both fallbacks |
| Architecture | §result release | Release policy per exam | One global `system_setting.result_flow`: `IMMEDIATE` (Tự động) / `HUMAN_VERIFIED` (Admin duyệt) | missing | Correct to a single setting |
| Proposal | §FR table | FR01–FR16 with exam-oriented items, no traceability | FRs must map to working features | missing | Add FR → feature → screen/API → test traceability table |
| Database | §3 data dictionary | 41 entity tables but no complete column/type/null/default/constraint dictionary | 293 columns, 59 FKs, 87 indexes | missing | Generate data-dictionary tables from introspection (all 41 tables) |
| Proposal / Architecture / Database | §risks / §constraints | No local-only scope, no 2-call reserve, no sandbox limits | Local-only Docker Compose; no real users; 2 remaining LLM calls | missing | Add honest constraints/limitations |
| All three | Cover / revision history | v1.1, fixed 2026 dates, no approver field | Current reconciliation | outdated | v1.2, `[CẦN NGƯỜI ĐIỀN]` approver/date, honest version history |
| All three | Whole document | English body | Deliverables must be Vietnamese, formal | wrong | Add Vietnamese v1.2 content (corrigendum, FR, data dictionary, captions); see limitations |
| All three | TOC / list of figures / list of tables | Reflects v1.1 figures and sections | New figures/sections | outdated | Update fields after editing |
| User Stories (4th doc, out of scope) | use cases | FORMAL/PRACTICE and 13-question contract | Learner-defined practice | extra | Note: not in this task's three-document scope; flagged for the team |

## What Step 1 already fixed

- `docs/diagrams/schema-catalog.json`, `physical-schema-relationships.json`,
  `physical-schema.dot` and all committed SVGs were regenerated from a real
  PostgreSQL introspection of `db/schema.sql` (41 tables / 59 FKs / 19
  migrations). `npm run diagrams:check` is green.
- `scripts/introspect_schema.py` is the new single source of truth; it writes
  `docs/qa/schema-introspection.json` and `docs/diagrams/diagram-inventory.json`.
- `scripts/validate_diagrams.py` no longer hard-codes 38 tables / 54 FKs /
  17 migrations: it anchors counts and names to the introspection inventory and
  uses the same CRLF-normalised digest as the generator.

## Legacy / retired tables (explicit, not hidden)

These tables are present in `db/schema.sql` and therefore **must** appear in the
ERD. They are retained solely to preserve historical prebuilt-exam rows and
FKs; no current API creates or starts them:

| Table | Why it is legacy |
| --- | --- |
| `assessment` | Prebuilt exam definitions; migration 019 sets every published exam to `closed`; `seed_demo.py` seeds 0 exams |
| `assessment_concept` | Exam target-concept weights of the retired exam definitions |
| `assessment_question` | Curated exam question pool (migration 017); unused by learner-defined practice |
| `assessment_blueprint` | Adaptive blueprint of retired formal definitions; `assessment_session.assessment_id` is now nullable (migration 018) |

Tables that are **still active** and must not be labelled legacy:
`selection_log`, `adaptive_event`, `result_release_event`, `grade_review`,
`grade_edit_audit`, `evaluation_record`, `system_setting`,
`session_start_request`, `session_question_plan`, `sql_test_dataset`,
`llm_cache`, `question`, `mcq_option`, `rubric`, `attempt`, `evidence`, etc.

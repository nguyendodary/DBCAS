# CHANGELOG — in-place revision

Ngày: 2026-11-23. Baseline code: `develop2` `6421b5ad44a0eaaeb9be8d26068c8ca434ae5bb7`.
Covers, styles, page setup, headers/footers and table styles are unchanged for Proposal/Architecture/Database.
SRS is new (no DBCAS SRS existed); it uses the FITAI cover + root SRS structure.

## 1. Proposal

| Before | After | Evidence |
|---|---|---|
| `1–20, default 5` (2×), `1–20 questions`, `from 1 to 20` | `1–13 legacy; 25 mixed / 50 single-type; default 5` | `practice_config.py:4-20` |
| `Every submitted session ... reviewed and approved by an administrator before ... published` | FIXED Test publishes AI-official V1; legacy/practice reviewed | `assessment_lifecycle.py:233-238`; `result_version.py` |
| `Every submission is reviewed by an administrator ... before it is published` | legacy/practice reviewed; FIXED V1 AI-official | same |
| `Learner SQL execution is deliberately read-only ... DML/DDL ... never executed` | default read-only; opt-in writable demo, rollback; Free/Pro UI note | `docker-compose.demo-writable.yml`; `freePro.jsx` |
| `RAG-Based Study Resources ... outside scope` | long-term paths outside; admin document grounding implemented | `document_generation.py`; `/admin/documents` |
| `review SQL and essay grades for every submission` | legacy/practice only; FIXED V1 AI-official | `grading_review.py` |
| `mandatory AI-then-administrator review workflow` | AI-official FIXED + human-verified LEGACY | `result_version.py`; `grading_review.py` |
| `Administrators ... review every submission` (3×) | review legacy/practice submissions | `grading_review.py` |
| `Every submission is reviewed and approved ...` | conditional release wording | same |
| `(41 tables)`, `41 tables` | `(67 tables)`, `67 tables` + 561/122/159/28 in data-tier text | `db/schema.sql` |
| `every query executes inside a read-only transaction` | default read-only; opt-in writable rollback | `ephemeral_sandbox.py`; `sanitizer` |
| `results are published only after mandatory administrator review` | FIXED V1 AI-official; legacy/practice review | `result_version.py` |
| `Every result is published only after ...` | conditional release | same |
| `An administrator ... approves every result` | approves legacy/practice; FIXED V1 AI-official | `grading_review.py` |
| `Every submission waits in an administrator review queue` | legacy/practice queue; FIXED V1 AI-official | same |
| `mandatory two-stage result workflow ...` | conditional release workflow | same |
| `runs read-only learner SQL (SELECT statements only)` | default read-only; opt-in writable demo | `sql_service.py`; `sandbox_runner.py` |
| `Every submission is reviewed by an administrator` (2×) | legacy/practice reviewed; FIXED V1 AI-official | same |
| `accepts SELECT statements only` (2×) | default SELECT; opt-in writable DDL/DML | `sql_classifier.py` |
| `The sandbox accepts read-only SELECT ... DML/DDL assessed ...` | default read-only; demo writable rollback; grading read-only | `sql_grading.py` |
| `mandatory review and approval of results.` | review legacy/practice; FIXED V1 AI-official | `grading_review.py` |

Table 9/10/11/12/13/14 cells were edited in place (practice limits, review queue, SELECT-only, mandatory review). No row/column added.

## 2. Architecture

| Before | After | Evidence |
|---|---|---|
| `41 tables` (8×) | `67 tables` (plus 561/122/159/28 in DB sentence) | `db/schema.sql` |
| `reviews and approves every result` | reviews legacy/practice; FIXED V1 AI-official | `result_version.py` |
| `under a read-only role, SELECT-only validation` | default read-only; opt-in writable demo | `ephemeral_sandbox.py` |
| `human review and publication` | AI-official FIXED + human-verified LEGACY | `result_version.py`; `grading_review.py` |
| `enforces mandatory administrator review before publication` | FIXED V1 AI-official; LEGACY review | same |
| `reviews every submission` (2×) | legacy/practice submissions | same |
| `mandatory administrator review` | conditional release | same |
| `Every new session uses mandatory AI-then-admin review` | FIXED V1 AI-official; legacy/practice review | same |
| `every result publication requires administrator approval` | legacy/practice approval; FIXED V1 AI-official | same |
| `accepts SELECT only` (2×), `Learner execution accepts SELECT only` (2×) | default SELECT; opt-in writable DDL/DML | `sql_classifier.py`; `sql_grading.py` |
| `mandatory review and approval` / `Enforces mandatory review and approval` | conditional release review | `grading_review.py` |
| `reviews every submission, and approves official results` | legacy/practice; FIXED V1 AI-official | same |
| `Learner SQL ... read-only role, SELECT-only ...` | default read-only; opt-in writable demo | `ephemeral_sandbox.py` |

## 3. Database

| Before | After | Evidence |
|---|---|---|
| `41 tables` (2×) | `67 tables`, 561 columns, 122 FKs, 159 indexes, 28 migrations | `db/schema.sql`; introspection |
| Table 1: 41 rows | 67 rows (26 new rows cloned) | `schema-introspection.json` |
| 41 table sections / stale column lists | 67 sections; all 67 column lists refreshed to 561 columns; Appendix A.1–A.26 added by cloning an existing heading/lead/caption/table | `db/schema.sql` |
| `all 67 tables appear in Figure 2` | 41-card core in Figure 2; remaining 26 in Appendix A | diagram scope |
| GradeReview "mandatory administrator approval" | legacy/practice administrator approval | `grading_review.py` |

Appendix A tables: `ai_prompt_content`, `ai_prompt_record`, `ai_stage_attempt`, `ai_stage_run`, `ai_stage_validation`, `attempt_rubric_criterion`, `course_document`, `document_chunk`, `document_clo`, `prompt_access_audit`, `question_clo`, `question_evidence`, `question_report`, `question_rubric_criterion`, `question_rubric_profile`, `retention_purge_audit`, `review_deviation`, `review_deviation_confirmation`, `review_request`, `session_final_result`, `session_result_analysis`, `session_result_criterion_score`, `session_result_publication`, `session_result_version`, `session_result_version_score`, `tab_leave_interval`.

## 4. Diagrams (6 changed)

| Figure | Before → after | Source edited |
|---|---|---|
| Proposal Fig 3 (logical) | `41 tables` → `67 tables` | `docs/diagrams/rebuild/logical/logical.svg` |
| Proposal Fig 4 (pipeline) | `1–20` → `1–13 legacy /25 mixed/50 single`; `count 1–20` → `1–13 legacy`; grounding/release note | `docs/diagrams/rebuild/pipeline/pipeline.svg` |
| Architecture Fig 1 (use case) | `UC12: 1–20` → `1–13 legacy · 25/50 typed` | `docs/diagrams/rebuild/use-case/use-case.svg` |
| Architecture Fig 3 (container) | `(41 tables)` → `(67 tables)`; `[read-only transaction]` → `[default read-only]` | `docs/diagrams/rebuild/container/container.svg` |
| Architecture Fig 4a | `(41 tables)` → `(67 tables)` | `component-08a.svg` |
| Architecture Fig 4b | `(41 tables)` → `(67 tables)` | `component-08b.svg` |

Pixels and display size preserved. Before/after images: `before-after/diagrams/`.

**Not changed (OWNER-DECISION):** Architecture Fig 7/8 and Database Fig 1/2 still show the 41-card core and legend `41/293/59/19`. Adding 26 cards needs new layout/pages; the owner prohibited diagram rebuilds without approval.

## 5. SRS

New `SRS.docx` from:
- FITAI cover page copied as-is; only title/project/team/mentor text changed in existing runs.
- Root SRS section structure: Introduction, Project overview, Functional requirements, Use cases, NFRs, Data/release, Constraints, Traceability.
- Facts from schema/routes/tests; no diagrams added (the root SRS diagrams were Student Management, not DBCAS).
- 4 pages.

## 6. Verification

- Fact audit: **76 assertions, 76 passed, 0 failed** (`fact-audit.json`/`.md`).
- Style audit: C14N styles/theme/settings/numbering all **equal**; page setup/header/footer equal; cover paragraphs/tables equal for Proposal/Architecture/Database (`style-audit.json`/`.md`).
- Visual pairs: `before-after/pages/` (16 pairs) and `before-after/diagrams/` (6 pairs); no overflow/overlap found in edited text/table/diagram pages.
- Page counts (Word): Proposal 59→60 (+1), Architecture 70→70 (0), Database 40→63 (+23 due 26 appendix tables and full column lists); SRS 4 (new). LibreOffice preview: 62/70/79/4.
- All four `.docx` open with python-docx and convert with LibreOffice headless; PDFs in `after/`.

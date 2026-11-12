# Document discrepancies v3 — the three active v1.2 Word documents

Scope: full factual audit of the three active files in `docs/academic/`:

- `C1SE.70_ProposalDocument_DBCAS_ver1.2.docx`
- `C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx`
- `C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx`

Audited against the shipped project, not against the earlier v1.1 text:

| Evidence | Verified facts |
| --- | --- |
| `docs/qa/schema-introspection.json` (PostgreSQL 17.11) | **41 tables, 293 columns, 59 FKs, 87 indexes, 0 enums, 19 migrations** |
| `db/schema.sql` + `db/migrations/001–019` | 41-table DDL; migration 018 makes `assessment_session.assessment_id` nullable; migration 019 closes published `assessment` rows; `system_setting` holds the single global `result_flow` |
| `docs/qa/project-facts.json` | Compose 6 + `qa-ai`; OpenAPI **82 paths / 93 operations**; **23** frontend routes; Admin nav **5**; OAuth `[github, google]`; SMTP `mailpit:1025`; sandbox `dbcas-sql-ephemeral:local`, `--network none`, 256 MB, 1 CPU; count 1–20 default 5 |
| `docker-compose*.yml` | local: `mailpit`, `db`, `executor-image`, `init`, `app`, `frontend`; base: `db`, `mailpit`, `sandbox`; release: `db`, `sandbox`, `migrate`, `backend`, `worker` (optional profile), `frontend` |
| `backend/app/routers/*.py` + `services/*.py` | 7 router files; `practice_service` (30-min expiry, hard-coded 70% practice target), `practice_bank`/`practice_selection` (widening with disclosure), `refresh_tokens` (hashed refresh-session families, server-side logout), `system_settings` (only `result_flow` writable), `grading_review` (self-review forbidden) |
| `frontend/src/App.jsx`, `components/Layout.jsx`, `package.json` | 23 routes; Admin nav = Cohort, Grading, Accounts, Question Bank, System; React 19.3.0, Vite 8.3.1, Tailwind 4.3.3, Chart.js 4.5.1, i18next 26.4.3 |
| `backend/Dockerfile`, `frontend/Dockerfile`, local `git --version` | Python 3.13, `nginx:1.29-alpine`, Docker CLI 29, Git 2.54.0 |

Summary of distinct items (a recurring claim is one item; all occurrences in
the named sections are fixed):

| Type | Items |
| --- | ---: |
| Wrong fact | 18 |
| Missing content | 1 |
| Extra/redundant content | 3 |
| Outdated version/date/terminology | 7 |
| **Total** | **29** |

Status: all 29 items below were fixed in place on 2026-11-09 with the
run-preserving editor; the verification counts are in the final section.

## Discrepancies and fixes

| # | Type | Document | Section | Says | Reality | Fix |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Wrong | Proposal | §7.2 FR-15 | AI-source MCQ/essay items "must pass automated checks and Administrator approval before entering the plan." | The AI-source path validates generated items automatically and serves them in the same session (`practice_generation.validate_generated`, `practice_bank._persist` creates `status="draft"` and serves it). Administrator approval applies to `question_candidate` → validated bank, not to per-session AI-source items. | State automated validation for AI-source items; state Administrator approval only for candidates promoted into the validated bank. |
| 2 | Wrong | Proposal | §6.2, §4.5, §7.1, §7.2, §12.3; Architecture QA07 / RSK-06 | "Every selected concept is covered" and "every item stays inside the selected difficulty bands." | `practice_selection.Catalog._plan` balances concepts/bands but widens to related concepts/bands when exact capacity is short, and `disclosure()` reports the widening. With count < selected concepts, every concept cannot be covered. | Say the plan is spread across the selected concepts/bands as far as the exact count allows; any widening to related concepts/bands is disclosed and logged. |
| 3 | Wrong | Proposal | §7.1, §8, §12.1, §12.4, §12.5 | Administrators configure "competency benchmarks"; concepts are compared with "administrator benchmarks"/"administrator-set passing expectation". | Current learner-defined practice snapshots a hard-coded **70%** target per selected concept in `practice_service.py` (`"target_pct": "70"`). There is no admin endpoint/UI to set per-concept targets. Administrators configure essay rubrics and the global result flow; `assessment_concept.target_pct` belongs to legacy assessments. | Replace with "the platform's 70% passing target" and limit Administrator configuration to rubrics and the global result flow. |
| 4 | Wrong | Architecture | Table 1 Actor, UC05, UC11, UC17 | Administrator "sets the passing benchmark per concept"; concepts are compared with "administrator-set passing expectation"; "Administrators cannot take practice sessions." | The 70% practice target is platform-fixed in the session snapshot; there is no per-concept admin benchmark control. `LearnerOnly` is a role-intersection guard, so an Administrator-only account cannot take practice but a legacy dual-role account holding `Learner` can. | Reword UC05 step 5 and UC11/UC17 to the platform 70% target; say "Administrator-only accounts cannot take practice sessions." |
| 5 | Wrong | Architecture | §3.2 UC09 (Table 19) | Precondition "Concepts and validated questions must exist"; step 3 says the administrator reviews "AI provider availability and retention limits"; step 6 says "Every change is recorded in the audit trail"; postcondition says "learners can take it once it is published." | `GET/PUT /api/v1/admin/system` only reads status (`result_flow`, evaluator/prompt-builder configured, fallback, database, pipeline) and writes `result_flow`. `system_setting` records only `updated_by`/`updated_at`, not an immutable audit trail. There is no publish step. | Precondition = active Administrator. Step 3 = read-only status, only result flow is writable. Step 6 = updated_by/updated_at. Postcondition = stored flow applies to subsequent publications; existing sessions keep their snapshot. |
| 6 | Wrong | Architecture | §3.2 UC03 (Table 13) | Logout only removes the JWT client-side; A1 says the JWT "is not revoked server-side and remains valid until its expiration." | `POST /api/v1/auth/logout` calls `refresh_tokens.revoke`, which revokes the refresh-token family and associated access tokens (`sid` is checked against `refresh_session`). | Logout revokes the refresh family and its access tokens server-side, then clears client state; the alternate flow becomes an idempotent missing/already-revoked token case. |
| 7 | Wrong | Proposal | §12.2 Data & Storage Tier | "Stateless JWT authentication removes the need for a separate session store." | `refresh_session` stores hashed refresh-token families with credential version, expiry, use and revocation; access tokens carry `sid` and are checked against it. | Describe short-lived access JWTs plus a PostgreSQL refresh-session table for rotation/revocation; there is no separate access-token session store, but auth is not fully stateless. |
| 8 | Wrong | Proposal; Architecture | Proposal §12.1; Architecture §4.1 | "Administrator accounts never take practice sessions: learner routes reject them even on a legacy dual-role account." | Backend `require_roles` uses set intersection; a legacy account holding both `Learner` and `Administrator` passes `LearnerOnly`. The UI guard also checks the Learner role. Only Administrator-only accounts are rejected. | Say "Administrator-only accounts cannot take practice sessions" and drop the dual-role rejection claim. |
| 9 | Wrong | Architecture | §7 ERD prose | "records one Attempt per served question, one SelectionLog entry where a fallback was used." | `personalized_assessment.serve_planned` writes one `selection_log` row **per served question**, with `is_fallback` marking substitutions. | Say "one SelectionLog entry per served question (`is_fallback` marks fallback items)." |
| 10 | Extra | Architecture | Table 51 Component Responsibilities | Row "Personalized Assessment Service" duplicates the Practice Service description; the "Question Serving" component named in the §4.2 prose has no row. | Real Question Serving path: `personalized_assessment.serve_planned` serves the frozen plan in order, persists drafts and writes `selection_log`. | Relabel the duplicate row "Question Serving" and describe planned delivery, draft persistence and SelectionLog audit. |
| 11 | Wrong | Architecture | Table 52 Module View | Practice Module cites "(FR-06, FR-07)"; Result Release cites only "(FR-11)". | FR-06 is Result Flow & System Settings; FR-07 is the practice interface; FR-10 covers rubric/human-verified essay scoring; FR-11 is Evidence Storage. The Practice Module does not own the global result flow. | Practice Module: FR-07, FR-15. Result Release: FR-06, FR-10, FR-11. |
| 12 | Outdated | Architecture | Table 53 Allocation View | "Learners take assessments and view results." | Learners take learner-defined **practice sessions**; `assessment_session` stores practice runs. | "Learners take practice sessions and view results." |
| 13 | Outdated | Architecture | Table 6 E01 (Administrator entity) | Administrator manages "assessment configuration and result-release policy". | No exam/assessment builder exists in the current API/UI. The Administrator manages CLOs, concepts, question bank, translations, rubrics, accounts/roles, system settings and the global result flow. | Replace with "system settings and the global result flow". |
| 14 | Wrong | Architecture | §7 SelectionLog / Table 54 | `SelectionLog` described as a fallback-only audit in §7 (the Table 54 row is broader). | One row per served item; `is_fallback` is a flag, not the row's reason for existing. | Align §7 with the one-row-per-served-item behavior (Table 54 already says "every question-plan selection decision"). |
| 15 | Extra | Architecture | Table 51 Component Responsibilities | Two rows are labelled "Database (PostgreSQL 17)"; one says "Stores all system data" and the second "Stores all system data (41 tables)." | An application database and a separate SQL sandbox database are distinct components. | Label the first "Application Database (PostgreSQL 17)"; label the second "SQL Sandbox Database (PostgreSQL 17)" with "runs learner SELECT queries in isolation; never stores application data." |
| 16 | Extra | Architecture | Table 51 Component Responsibilities | Practice Service cell contains a second paragraph: "Drafts and validates AI question candidates ahead of time." | AI-source items are generated/validated at session start; administrator candidate review is a separate Question Bank path. | Replace with "Generates and validates AI MCQ/essay items at session start; SQL items always come from the validated bank." |
| 17 | Wrong | Architecture | §3.3 QA11 | "Timer, progress indicator, and 10/5-minute warnings are always visible." | The timer is persistent; the 10- and 5-minute warning banners appear only at those thresholds (`ExamPage.jsx` checks `seconds <= 600` / `<= 300`). | "The timer and progress indicator are always visible; warnings appear at 10 and 5 minutes." |
| 18 | Wrong | Architecture | §3.5 BC03 | "Assessments can require HUMAN_VERIFIED release." | The result flow is one global `system_setting.result_flow` value applied to every session, not a per-assessment option. | "The global result flow can require HUMAN_VERIFIED release." |
| 19 | Wrong | Proposal | §13 RSK-02 | "Route assessments configured for human-verified release through an administrator review queue." | Same global result flow; no per-assessment policy. | "Route sessions through the global HUMAN_VERIFIED review queue." |
| 20 | Wrong | Database | Table 1 Overview, AssessmentConcept | "Junction table holding the target concepts of an assessment ... passing benchmark used for gap detection (FR-06, FR-14)." | `assessment_concept` is one of the four **legacy** tables (migration 019 closes published assessments). Current practice stores a 70% target in `assessment_session.config_snapshot`. | Mark the row Legacy and remove active FR-06/FR-14 claims; point current targets to the session snapshot. |
| 21 | Wrong | Database | Table 1 Overview, Assessment | Legacy assessment row cites "(FR-06 legacy)". | FR-06 is Result Flow & System Settings in the current FR set; the legacy assessment table is not an FR-06 implementation. | Remove "(FR-06 legacy)" and keep the migration-019 legacy note. |
| 22 | Wrong | Database | Table 1 Overview, CompetencyGap | "The ranked study list is derived from ConceptCompetency, Concept, and AssessmentConcept records." | For learner-defined practice, targets come from `assessment_session.config_snapshot.concepts[].target_pct` (70%); `assessment_concept` is legacy. | Say targets come from the session's frozen concept targets (70% for practice), with legacy assessment targets only for historical rows. |
| 23 | Outdated | Database | Table 1 Overview, AssessmentSession | "frozen assessment configuration and concept targets". | The row is one learner's practice run; the snapshot is a practice configuration. | "frozen practice configuration and concept targets". |
| 24 | Outdated | Database | Second cover page | Date "October 30th, 2026" on the duplicate inner cover while the document is v1.2 dated November 8th, 2026. | First cover and DOCUMENT INFORMATION say 08/11/2026. | Change the inner-cover date to "November 8th, 2026". |
| 25 | Outdated | Proposal; Database | Proposal Table 12; Database Hardware and Software Requirements | "PostgreSQL 17 (LTS)". | PostgreSQL does not publish LTS releases; the tested server is PostgreSQL 17.11 (Debian 17.11-1.pgdg13+2). | "PostgreSQL 17". |
| 26 | Outdated | Proposal; Database | Proposal Table 12; Database Hardware and Software Requirements | "Git 2.55+". | `git --version` on the verified build host is `2.54.0.windows.1`; no repository evidence requires 2.55. | "Git 2.54+". |
| 27 | Outdated | Proposal | Table 12 Technology Stack | "i18next 26.4". | `frontend/package.json` pins `i18next` 26.4.3. | "i18next 26.4.3". |
| 28 | Missing | Architecture | §4.1 Container prose, Table 50; §6 Allocation prose, Table 53 | OAuth providers are named, but the external Email Service/SMTP dependency is absent even though the context diagram and password-reset flow use it. | `backend/app/services/mail.py` sends only password-reset mail; local/base Compose runs `mailpit` (SMTP 1025), release uses an external SMTP relay. | Add the external Email Service (SMTP; Mailpit in development) to the container/allocation prose and note it is not an application container. |
| 29 | Wrong | Proposal; Architecture | Proposal §4.5, §7.2 FR-15, §12.3; Architecture §3.2 UC10 | "Serves only validated questions" / "so that only validated items are served." | AI-source generated items are persisted with `Question.status = "draft"` (`practice_bank._persist`) and served in the same session after automatic content validation; only bank candidates require Administrator approval into `status = "validated"`. | Say "content-validated items (approved bank or auto-validated AI-source items)" and scope Administrator approval to candidates entering the validated bank. |

## Notes on what was checked and not changed

- Data dictionary: all **41 sections / 293 columns** were compared against
  `schema-introspection.json` (names, types, nullability, PK/FK cells,
  defaults). The six-column data tables match; only the Table 1 prose rows
  above were wrong.
- Table Overview has 41 rows and all 41 table names.
- Counts 41/293/59/87/19 were verified; the documents do not state 293/59/87/19
  anywhere, so no count was inserted (not a claim).
- No approver name, signature or date was invented. `[CẦN NGƯỜI ĐIỀN]`
  placeholders remain.
- No image was replaced. Figure captions and their SEQ fields are unchanged.
- TOC / list-of-figures / list-of-tables fields were not edited by the text
  editor; they are updated only if Word COM is run (see final verification).
- The pending TRD panel split is not recorded as a document fact; the figure
  caption stays unchanged until the owner decides.

## Verification (measured 2026-11-09)

Edits applied: **65 run-preserving text replacements** (25 Proposal,
31 Architecture including two targeted Database-label renames, 9 Database).
Only `word/document.xml` differs in each package; every other part is
byte-identical (styles, numbering, headers, footers, media, relationships,
field instructions).

| Check | Result |
| --- | --- |
| `scripts/verify_docx.py` | **41 assertions, 0 failures**; Database Design **41 sections / 293 columns**; PASS |
| `backend/.venv/Scripts/python.exe scripts/check_docs.py` | **46 assertions, 0 failures**; tables=**41**, columns=**293**, FKs=**59**, indexes=**87**, migrations=**19**, services=6/7, OpenAPI paths=**82**, operations=**93**, frontend routes=**23**, context nodes=**15**, context flows=**23**; PASS |
| `scripts/verify_word.py --ci --no-pdf` | **3 documents, 0 failed**; format diffs 0, run issues 0, new Vietnamese words 0, diagram issues 0, data mismatches 0; all PASS |
| Package structure | 34/33/48 parts, 0 added/removed; only `word/document.xml` changed; media 5/9/4 unchanged; fields 243/246/399, runs 1615/2211/3386, tables 21/58/46, sections 2/10/7 unchanged |
| Paragraph/table/image inventory | Proposal 913/21/5; Architecture 1363/58/9; Database 1995/46/4 — unchanged |
| Wrong-claim scan | 0 remaining matches for the 29 fixed phrases/groups (administrator benchmarks, every selected concept, dual-role, Stateless JWT, one SelectionLog fallback, Learners take assessments, October 30, LTS, Git 2.55, Personalised Assessment Service, FR-06 legacy, adaptive cap, only validated questions, etc.) |

Not verified: **Word COM was not run** (Word COM unavailable on this host,
reported as SKIP by `verify_word.py`); **LibreOffice/PyMuPDF page rendering
was not run**. Page numbers in `docProps/app.xml` remain the previous values
(59/65/36) and are not a live page-count measurement. TOC / list-of-figures /
list-of-tables fields were not refreshed; they still point at the existing
headings and captions and should be updated by Word COM on a host where it
is available.

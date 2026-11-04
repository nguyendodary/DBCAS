# Engineering task audit — 2026-11-04

Scope: the 45 engineering/QA/content titles supplied in the current instruction;
Jira statuses were not supplied and are recorded as **Unknown**. Product rules:
learner-defined practice, no prebuilt exams, automatic/admin-approved release,
Prompt Builder → Evaluator. Historical evidence alone does not close a task.

Baseline at `98e227b`: clean `develop2`, recovery/pull completed in its existing
worktree. The independent dirty `DBCAS` main checkout is untouched. Frontend
`npm ci`: exit 0; Vitest **344/344**, 39 files, **109.02s**; build exit 0,
**1.02s**; npm audit **0 vulnerabilities**. Backend lint/build exit 0; full
backend **1258/1258**, **757.49s**, 0 failures/skips, 1 dependency warning.
Full Chromium baseline **55/55**, **1774.01s**, 0 failed/skipped/flaky/retries; desktop/390px included. Launcher **7/7**; inventory/OpenAPI checks pass. Starting-HEAD CI:
successful [41694671249](https://github.com/nguyendodary/DBCAS/actions/runs/41694671249).

| Task | Jira status | Verified result before | Fix/change | Evidence (test name/screenshot) | Final result |
| --- | --- | --- | --- | --- | --- |
| 1.3 Architecture/API: runtime contract, schemas, guards/errors | Unknown | Baseline pending | Pending verification | `tests/dn/test_openapi_contract.py` | Still failing |
| 1.4 Database: safe migrations, constraints, indexes/idempotent seed | Unknown | Baseline pending | Pending verification | `tests/test_migrations.py` | Still failing |
| 1.5 Environment: fresh clone and one-command startup | Unknown | Historical evidence only | Pending current-clone verification | `scripts/local.test.mjs` | Still failing |
| 1.6 Learner UI: working learner journeys | Unknown | 344 UI tests pass; browser pending | Pending verification | `LearnerPages.test.jsx` | Still failing |
| 1.7 Admin UI: working administrator journeys | Unknown | 344 UI tests pass; browser pending | Pending verification | `AdminManagePages.test.jsx` | Still failing |
| 1.8 Automated question validation checklist | Unknown | 27 core questions lacked references/explanations; bad primary SQL allowed | Shared schema/language/duplicate/docs/SQL validator and CI command | `test_all_source_questions_pass_the_shared_validator`, `test_every_source_sql_has_nonempty_primary_and_executes_repeatably` (41/41 targeted) | Fixed |
| 2.1 Authentication/RBAC API | Unknown | Baseline pending | Pending verification | `tests/test_rbac.py` | Still failing |
| 2.2 Question bank and learner-defined practice API | Unknown | Sparse requests rejected, unseeded random selection | Exact-count implementation needed | `test_bank_shortfall_is_explicit_and_scope_not_widened` | Still failing |
| 2.3 MCQ saving, grading and submission | Unknown | Baseline pending | Pending verification | `tests/test_grading_service.py` | Still failing |
| 2.4 Home/authentication frontend | Unknown | UI suite passes; browser pending | Pending verification | `AuthPages.test.jsx` | Still failing |
| 2.5 Learner test-taking frontend | Unknown | UI suite passes; browser pending | Pending verification | `ExamPersistence.test.jsx` | Still failing |
| 2.6 Question/concept/CLO management; no exam parts | Unknown | UI suite passes; API/browser pending | Pending verification | `CurriculumEditing.test.jsx` | Still failing |
| 2.7 Correct MCQ content/answers | Unknown | Ambiguous/incorrect PG claims | Reviewed definitions, explicit before/fix manifest and factual SQL checks | `test_reviewed_postgres_semantics.py` (14), `bank-validation.md` (98 changes) | Fixed |
| 2.8 Question classification | Unknown | Coverage holes; metadata review pending | Pending validation | `bank-validation.md` | Still failing |
| 2.9 Automated tests and fixtures | Unknown | Existing deterministic suites executing | Add new requirement regressions | Baseline logs | Still failing |
| 2.10 Functional testing | Unknown | Current browser baseline pending | Pending verification | Browser suite | Still failing |
| 3.1 Isolated Docker SQL sandbox | Unknown | Baseline pending | Pending verification | `tests/dn/test_ephemeral_sandbox.py` | Still failing |
| 3.2 SQL comparison/grading | Unknown | Baseline pending | Pending verification | `tests/test_sql_release.py` | Still failing |
| 3.3 Prompt Builder → Evaluator essay grading | Unknown | Deterministic baseline pending; new key unused | Metered live gate needed | Pipeline tests | Still failing |
| 3.4 Learner attempt/result API | Unknown | Baseline pending | Pending verification | `tests/test_learner_practice.py` | Still failing |
| 3.5 AI-result/review frontend | Unknown | UI suite passes; browser pending | Pending verification | `PracticeEvaluation.test.jsx` | Still failing |
| 3.6 Execute every SQL question | Unknown | 67 execute; pg-s056 primary empty, pg-s053 semantic initials bug | Corrected references and data; actual double execution gate | `test_every_source_sql_has_nonempty_primary_and_executes_repeatably`, initials/orphan regressions | Fixed |
| 3.7 Essay sample answers/rubrics | Unknown | Two missing answers, retired rubric gaps, inaccurate prose | Corrected reviewed samples and canonical four-level rubric; old history fixtures preserved | `test_question_validator.py`, `test_localized_bank_sandbox.py` (162/162 combined) | Fixed |
| 3.8 Automated API suite | Unknown | Backend baseline running | Pending verification | Backend suite | Still failing |
| 3.9 SQL + AI flows | Unknown | Baseline pending; live not started | Pending verification | Browser/provider suites | Still failing |
| 3.18 Updated cases/test data | Unknown | Old tests assert superseded shortfall behavior | Preserve protections and add new assertions | Count matrix pending | Still failing |
| 4.1 Competency algorithm | Unknown | Baseline pending | Independent arithmetic check needed | Competency tests | Still failing |
| 4.2 Skill-gap/statistics APIs | Unknown | Baseline pending | Pending verification | `tests/dn/test_statistics_api.py` | Still failing |
| 4.3 Learner competency UI | Unknown | UI suite passes; browser pending | Pending verification | `CumulativeRace.test.jsx` | Still failing |
| 4.4 Ranking/settings frontend | Unknown | UI suite passes; browser pending | Pending verification | Learner browser scenarios | Still failing |
| 4.5 Admin dashboard/CLO/learner management | Unknown | UI suite passes; browser/API pending | Pending verification | Admin browser scenarios | Still failing |
| 4.6 Admin reports/settings | Unknown | UI suite passes; browser/API pending | Pending verification | Admin browser scenarios | Still failing |
| 4.7 Question-bank coverage | Unknown | 442 source questions/80 concepts; default seed only 24/15 | Derive quota from max 20 | `bank-validation.md` | Still failing |
| 4.8 Revalidate edited questions | Unknown | Baseline pending | Pending verification | `tests/test_bank_release.py` | Still failing |
| 4.9 Competency/dashboard tests | Unknown | Baseline pending | Manual/API/DB/UI agreement needed | Arithmetic evidence pending | Still failing |
| 4.10 Responsive/UI tests | Unknown | Unit pass; current 390px browser pending | Pending verification | Browser screenshots pending | Still failing |
| 4.12 Lint/format/CI | Unknown | Backend lint passes; no frontend lint/format command | Add reproducible enforcement | CI configuration | Still failing |
| 5.1 Skill-gap suggestions | Unknown | Baseline pending | Pending verification | Guidance tests | Still failing |
| 5.2 Whole-system integration | Unknown | Current browser baseline pending | Pending verification | Three repeated scenarios pending | Still failing |
| 5.3 Learner UX polish | Unknown | Count limits duplicated and count hidden | Use API count configuration/presets | Learner setup tests pending | Still failing |
| 5.4 Admin UX polish | Unknown | UI suite passes; browser pending | Pending verification | Admin browser scenarios | Still failing |
| 5.5 Final question-bank validation | Unknown | Missing shared complete bank gate | Validator/CI needed | `bank-validation.md` | Still failing |
| 5.6 Integration/error scenarios | Unknown | Existing baseline pending | Expand all generation failure modes | Count matrix pending | Still failing |
| 5.7 Performance/resource limits | Unknown | Current measurements pending | Controlled concurrency/load gate | Load evidence pending | Still failing |
| 5.8 Final regression/retesting | Unknown | Baseline only; implementation not started | Full final gate pending | Gate below | Still failing |

Excluded: 1.1, 1.2, 1.9, 1.10; 2.11; 3.10–3.17; 4.11, 4.13–4.15;
5.9–5.16 (**25 IDs**), plus deliverables exclusively consisting of documents,
slides, minutes, backlog updates or reflections. No engineering title excluded.

## Issues and retests

| # | Flow | What happened | Expected | Severity | Status | Commit |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Bank practice | Sparse matching pool returns 422 | Exactly requested count with disclosed widening | High | Reproduced by existing named test; fix pending | — |
| 2 | AI generation | Short/invalid batch has no validated template recovery | Bounded regeneration and exact validated fallback | High | Implementation inspected; regression pending | — |
| 3 | Generation validation | Empty/non-repeatable/duplicate generated questions not rejected | Shared bank/AI validation | High | Implementation inspected; regression pending | — |
| 4 | Bank content | Incorrect lock/FOUND/array/CTE claims, empty primary SQL, initials bug | Correct documented content and executable fixtures | High | Fixed; 162/162 plus final 41/41 retest; see bank audit | — |
| 5 | Setup | Count constants repeated in API/UI, no frontend lint/format gate | Central configuration and enforced checks | Medium | Inspected; change pending | — |

## Execution sequence

- [x] Execute and record untouched backend/frontend/browser baselines.
- [x] Correct 98 reviewed source definitions; strict content 442/442, localization 442/442, SQL 67/67, final semantic/content regressions 41/41. Coverage/seed still pending.
- [ ] Central count configuration, deterministic widening, bounded AI recovery;
  named red/green regressions and exact matrix; commit/push each verified step.
- [ ] Reverify Sprints 1–5 in order with API/browser/data evidence, update handover.
- [ ] Metered live scenarios (new key; 80 maximum), three fake repeats, 390px,
  independent arithmetic, controlled load/security, no-env fresh clone.
- [ ] Full final stability gate and pushed-HEAD CI; disclose any failed criterion.

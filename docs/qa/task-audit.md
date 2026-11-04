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
| 1.3 API: every success body/redirect and auth/error contract described | Unknown | 21 operations lacked success bodies; redirects said 200; login 401 absent (red test) | Typed responses; real 302 redirects; public-auth error envelopes | `test_every_json_success_has_a_schema_and_oauth_redirects_are_documented` 3/3; affected API suite 156/156 | Fixed |
| 1.4 Database: safe migrations, constraints, indexes/idempotent seed | Unknown | Existing migrations pass baseline; default seed stops at 24 | Complete additive seed; exact prior-content review, stable unused IDs and used-question versions | Migration baseline; `test_complete_corpus.py`, `test_demo_seed.py` (11/11) | Fixed |
| 1.5 Environment: no-env clone installs, seeds and starts in one command | Unknown | Current-clone verification absent | New remote clone, npm ci at root/UI, npm start, browser fallback probe | `scripts/local.test.mjs` 7/7; fresh browser: 4 logins, 5482 questions/80 concepts, SQL/fallback/390px, no page errors | Verified OK |
| 1.6 Learner UI: setup, answer/save/reload, submit and results | Unknown | Baseline 55/55 real Chromium; sparse bank/count failures | Exact-count setup and bounded recovery | `bank practice shows 0/1/3 attempt evidence and cumulative trend`; fake Chromium 13/13; full UI 345/345 | Fixed |
| 1.7 Admin UI: accounts, curriculum, bank and reviewed release persist | Unknown | Baseline real browser admin authoring/provisioning journey passes | No UI change required; schema gap fixed under 1.3 | `admin completes provisioning, curriculum, human AI review, activation and analytics`; baseline 55/55; fake Flow 2 passes | Verified OK |
| 1.8 Automated question validation checklist | Unknown | 27 core questions lacked references/explanations; bad primary SQL allowed | Shared schema/language/duplicate/docs/SQL validator and CI command | `test_all_source_questions_pass_the_shared_validator`, `test_every_source_sql_has_nonempty_primary_and_executes_repeatably` (41/41 targeted) | Fixed |
| 2.1 Authentication/RBAC: learner/admin/disabled accounts and refresh reuse | Unknown | Baseline full backend passes; current role/refresh API checks now executed | No auth change required | `test_self_registration_never_grants_admin`, `test_admin_endpoint_forbidden_for_learner`; auth/RBAC/refresh within 158/158 | Verified OK |
| 2.2 Question bank/practice API: exact count, scope, uniqueness/idempotency | Unknown | Sparse requests rejected; insufficient AI batches failed | Central limits, deterministic widening, validated bank/template recovery | `test_bank_shortfall_widens_deterministically_to_exact_count_and_discloses`; API subset 107/107; matrix 2,268,700 | Fixed |
| 2.3 MCQ: correct answer, autosave/reload and duplicate-safe submission | Unknown | Baseline MCQ/draft tests pass | No grading change required | `test_grading.py`, `test_draft_lifecycle.py` within 158/158; Chromium two-tab/double-submit scenario passes | Verified OK |
| 2.4 Home/auth frontend: sign-in, redirects, session recovery | Unknown | Baseline full UI and 55 Chromium cases pass | No authentication UI change required | `AuthPages.test.jsx`; fresh clone 4 real-browser logins; expired-two-tabs-restored.png | Verified OK |
| 2.5 Learner flow: select, save, refresh, finish and see released results | Unknown | Baseline browser passes; count setup lacks central bounds | Exact-count setup, persisted fallback notices and guarded retry | `ExamPersistence.test.jsx`; fake Chromium 13/13 with both release flows and reload | Fixed |
| 2.6 Admin management: persist bank/concept/CLO edits and permission boundaries | Unknown | Baseline authoring/curriculum browser journey passes | No exam-part surface; retain learner-defined practice product decision | `test_admin_questions.py`, `test_admin_curriculum.py` within 158/158; named admin authoring Chromium journey | Verified OK |
| 2.7 Correct MCQ content/answers | Unknown | Ambiguous/incorrect PG claims | Reviewed definitions, explicit before/fix manifest and factual SQL checks | `test_reviewed_postgres_semantics.py` (14), `bank-validation.md` (184 reviewed definitions) | Fixed |
| 2.8 Classification: confirmed concept/CLO/type/difficulty are valid and usable | Unknown | Sparse concept/type/difficulty coverage; aliases unmapped | Confirmed source mappings, 720 filled cells; scope validator | `test_all_concept_difficulty_type_cells_have_derived_capacity`; `test_common_validator_rejects_invalid_content`; coverage table | Fixed |
| 2.9 Cases/fixtures: deterministic valid and invalid requests across APIs | Unknown | Baseline 1258 tests; old generation shortfall fixtures | Preserve history fixtures; real typed fake provider and exact-count regressions | API 107/107; typed HTTP provider 4/4; matrix 2,268,700 cases | Fixed |
| 2.10 Functional tests: learner then admin persist real user actions | Unknown | Baseline 55/55 real Chromium executed | Extend generation fallback, timeout, retry and mixed types | Fake Chromium 13/13, 369.919s; default Chromium baseline 55/55, 1774.01s | Verified OK |
| 3.1 Isolated Docker SQL sandbox | Unknown | Baseline pending | Pending verification | `tests/dn/test_ephemeral_sandbox.py` | Still failing |
| 3.2 SQL comparison/grading | Unknown | Baseline pending | Pending verification | `tests/test_sql_release.py` | Still failing |
| 3.3 Prompt Builder → Evaluator essay grading | Unknown | Deterministic baseline pending; new key unused | Metered live gate needed | Pipeline tests | Still failing |
| 3.4 Learner attempt/result API | Unknown | Baseline pending | Pending verification | `tests/test_learner_practice.py` | Still failing |
| 3.5 AI-result/review frontend | Unknown | UI suite passes; browser pending | Pending verification | `PracticeEvaluation.test.jsx` | Still failing |
| 3.6 Execute every SQL question | Unknown | 67 execute; pg-s056 primary empty, pg-s053 semantic initials bug | Corrected references and data; actual double execution gate | `test_every_source_sql_has_nonempty_primary_and_executes_repeatably`, initials/orphan regressions | Fixed |
| 3.7 Essay sample answers/rubrics | Unknown | Two missing answers, retired rubric gaps, inaccurate prose | Corrected reviewed samples and canonical four-level rubric; old history fixtures preserved | `test_question_validator.py`, `test_localized_bank_sandbox.py` (162/162 combined) | Fixed |
| 3.8 Automated API suite | Unknown | Backend baseline running | Pending verification | Backend suite | Still failing |
| 3.9 SQL + AI flows | Unknown | Baseline pending; live not started | Pending verification | Browser/provider suites | Still failing |
| 3.18 Updated cases/test data: all failure modes deterministic | Unknown | Old assertions require a shortfall error | Exact-count regressions retain no-invalid-persistence/cache protections; typed HTTP fixtures | `test_every_generation_failure_preserves_exact_count_and_valid_content`; provider contract 4/4 | Fixed |
| 4.1 Competency algorithm | Unknown | Baseline pending | Independent arithmetic check needed | Competency tests | Still failing |
| 4.2 Skill-gap/statistics APIs | Unknown | Baseline pending | Pending verification | `tests/dn/test_statistics_api.py` | Still failing |
| 4.3 Learner competency UI | Unknown | UI suite passes; browser pending | Pending verification | `CumulativeRace.test.jsx` | Still failing |
| 4.4 Ranking/settings frontend | Unknown | UI suite passes; browser pending | Pending verification | Learner browser scenarios | Still failing |
| 4.5 Admin dashboard/CLO/learner management | Unknown | UI suite passes; browser/API pending | Pending verification | Admin browser scenarios | Still failing |
| 4.6 Admin reports/settings | Unknown | UI suite passes; browser/API pending | Pending verification | Admin browser scenarios | Still failing |
| 4.7 Bank coverage: seven valid unique cases per concept/difficulty/type | Unknown | Source capacity sparse; stronger case review finds repeated worked outputs | Raw quota/seed fixed; worked-case diversity correction pending | Raw 720 cells pass; new distinct-worked-results regression red | Still failing |
| 4.8 Revalidate edited questions | Unknown | Baseline pending | Pending verification | `tests/test_bank_release.py` | Still failing |
| 4.9 Competency/dashboard tests | Unknown | Baseline pending | Manual/API/DB/UI agreement needed | Arithmetic evidence pending | Still failing |
| 4.10 Responsive/UI tests | Unknown | Unit pass; current 390px browser pending | Pending verification | Browser screenshots pending | Still failing |
| 4.12 Lint/format/CI | Unknown | Backend lint passes; no frontend lint/format command | Add reproducible enforcement | CI configuration | Still failing |
| 5.1 Skill-gap suggestions | Unknown | Baseline pending | Pending verification | Guidance tests | Still failing |
| 5.2 Whole-system integration | Unknown | Current browser baseline pending | Pending verification | Three repeated scenarios pending | Still failing |
| 5.3 Learner UX: visible count, preserved retry/loading, 390px | Unknown | Count bounds duplicated and count hidden | API-driven presets, search/bounded chips, guarded retry preserves setup | `LearnerPages.test.jsx`; full UI 345/345; fake browser 13/13 and mobile-setup.png | Fixed |
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
| 1 | Bank practice | Sparse matching pool returns 422 | Exactly requested count with disclosed widening | High | Fixed; API and exhaustive matrix retested | — |
| 2 | AI generation | Short/invalid batch has no validated template recovery | Bounded regeneration and exact validated fallback | High | Fixed; every required failure mode retested through API/DB | — |
| 3 | Generation validation | Empty/non-repeatable/duplicate generated questions not rejected | Shared bank/AI validation | High | Fixed; schema/scope/SQL/content regressions pass | — |
| 4 | Bank content | Incorrect lock/FOUND/array/CTE claims, empty primary SQL, initials bug | Correct documented content and executable fixtures | High | Fixed; 162/162 plus final 41/41 retest; see bank audit | — |
| 5 | Setup | Count constants repeated in API/UI, no frontend lint/format gate | Central configuration and enforced checks | Medium | Inspected; change pending | — |
| 6 | SQL edge data | 30 served edge fixtures had empty expected grids | Every served fixture nonempty; retain empty-input regression coverage | High | Fixed; strict source/SQL/upgrade 57/57, 422.45s | `3e6d3e2` |
| 7 | Bank upgrades | Subsequent registered revisions could create copies instead of safely updating/versioning | Match the recorded prior content hash and preserve owner edits/status/history | High | Fixed; three registry revision regressions pass within 57/57 | `3e6d3e2` |
| 8 | Large bank / CI fake QA | 20-second API response waits fail in 9 repeated browser cases | Selected-content validation and bounded response time | High | Metadata selector implemented; local scenario passes; full fake QA retest pending | Pending count commit |

## Execution sequence

- [x] Execute and record untouched backend/frontend/browser baselines.
- [x] Correct 98 reviewed source definitions; strict content 442/442, localization 442/442, SQL 67/67, final semantic/content regressions 41/41. Coverage/seed still pending.
- [ ] Central count configuration, deterministic widening, bounded AI recovery;
  named red/green regressions and exact matrix; commit/push each verified step.
- [ ] Reverify Sprints 1–5 in order with API/browser/data evidence, update handover.
- [ ] Metered live scenarios (new key; 80 maximum), three fake repeats, 390px,
  independent arithmetic, controlled load/security, no-env fresh clone.
- [ ] Full final stability gate and pushed-HEAD CI; disclose any failed criterion.

Phase 1 bank milestone: `b3bb04e` source corrections pushed; 5,482 static-valid questions, 80 concepts, all 720 capacity cells >=7. Full content/SQL gate 41/41 (436.78s); safe seed/coverage gate 11/11 (56.32s). Count behavior and final full-system gate still pending.

Bank follow-up: DB-2NF declared id alone unique despite the stated composite key; 63 variants corrected, real grids regenerated; `test_second_normal_form_fixture_really_has_a_composite_key` plus complete-corpus suite **25/25, 7.58s**. Reference context guard red **11/11** then shared-validator/OpenAPI subset **41/41, 25.02s**. Full SQL execution gate remains due again on final code.

Exact-count milestone: production selector and recovery matrix **2,268,700/2,268,700**, 171.881s (pytest 172.10s): 3,241 concept scopes x 7 difficulty subsets x 20 counts x 5 modes (bank; AI normal/failure/invalid/timeout). Full source validation precedes selection; real SQL execution is a separate whole-corpus gate. Required detailed failure modes also run through the real API/DB/sandbox. Current commit subset **107/107, 67.19s**, HTTP fake-provider contracts **4/4, 3.15s**. Full UI **345/345, 128.25s**, production build 778ms. Latest real Chromium fake scenario **13/13, 369.919s**, no skips/flakes/retries; earlier failures retained. Source/difficulty OpenAPI enums were missing (named contract red), now exported and checked against runtime. Final complete backend/three browser repeats remain required.

Sprint 1/2 targeted rerun: **158/158, 123.29s**, auth/RBAC/refresh/migrations/init/question and curriculum APIs/MCQ grading/drafts/content metadata. A command initially referenced a nonexistent refresh test path and executed no tests (exit 4); corrected command executed the full listed files. Response-contract gate **156/156, 110.51s**, covering practice, grading review, OAuth, password reset, readiness and translation preparation; final all-operation contract probe **3/3, 0.97s**. Runtime has 93 operations across 82 paths; generated OpenAPI and inventory regenerated.

Sprint 1 complete on current milestone evidence: fresh browser probe succeeded with all 4 demo accounts, 5,482 questions/80 concepts, saved history, real SQL, no-key generation/evaluation fallback, arithmetic and 390px bounds; zero page errors. Evidence JSON/screenshots: `_review/audit-20261104/fresh-*`. Final full regression and clone fast-forward remain scheduled after later sprint fixes.

Sprint 2 complete on the named API/UI/browser milestone evidence above; final full suites still required after subsequent sprint changes. Rejected generation content remains absent from persisted questions and caches; old historical attempts are immutable. Latest product decision supersedes the former shortfall-error assertions without removing safety coverage.

Sprint 3 live/SQL evidence: **257 pass / 2 Docker CLI failures**, 540.20s; all 1747 SQL questions/3494 fixtures executed twice with zero content mismatches. Full isolated sandbox/protocol retest **10/10, 31.44s**; initial daemon cause remains unconfirmed and final serial/resource gate is still required. Provider compatibility red 2/2 then **83/83**, 26.76s; recovery/meter/provider **59/59**, 24.48s. New job meter cap80, restart/key-match/concurrency/privacy tests; no-key real gate skips automatically.

Live run1 failed evaluator404; run2 per-attempt evaluation passed, overall timeout; run3 generation-only **1/1**, 8.632s, valid Vietnamese SELECT-column-order MCQ, exact1/no fallback; run4 generation3 used validated bank fallback. Source key/model retained. Optional seed plus strict provider routing caused404; disabled mandatory reasoning caused400. Adapter fix preserves strict schema and existing wire limits. Reference: https://openrouter.ai/docs/guides/routing/provider-selection and https://openrouter.ai/docs/guides/best-practices/reasoning-tokens .

Content review reopened worked-case diversity: **137/240** native concept/difficulty cells have fewer than seven distinct worked grids despite distinct prompts. `test_each_case_cell_has_distinct_worked_results_and_grounded_answers` added before repair; full pre-change native definitions saved locally and reproducible from committed generator. Coverage task4.7 remains open until this stronger gate passes.

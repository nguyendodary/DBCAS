# Engineering task audit — 2026-11-05

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
| 3.1 SQL sandbox: offline limits, timeout, isolation and cleanup | Unknown | Baseline passes; later 2 Docker CLI errors during parallel startup | Isolated retest; limits unchanged; serial final resource gate due | `test_offline_container_limits_typed_execution_and_cleanup`, sandbox/protocol 10/10 | Verified OK |
| 3.2 SQL grading: typed comparison, limits and stable fixtures | Unknown | Full baseline passes; content issues tracked separately | No comparison change needed | `test_real_postgresql_values_survive_wire_comparison`, `test_real_boolean_and_text_never_equal_numbers`; SQL/content/pipeline group 257 pass/2 unrelated Docker errors | Verified OK |
| 3.3 Essay AI: Prompt Builder → Evaluator, safe failure and caching | Unknown | Live404 from optional seed routing; disabled mandatory reasoning rejected | Scoped provider compatibility and durable 80-call meter, strict schemas retained | Provider/pipeline/meter 83/83; real full run5 1/1, 126.438s | Fixed |
| 3.4 Attempt/result API: frozen scope, release, review and caching | Unknown | Baseline passes; count shortage fixed under2.2 | Existing ownership/release/history guarantees retained | `test_flow_one_waits_for_evaluation_then_releases_and_cache`, `test_flow_two_sql_edit_reason_audit_and_approve`; contracts/API156/156 | Verified OK |
| 3.5 AI result UI: pending/error/approval and reviewed visibility | Unknown | Full UI and fake browser pass | No product change needed; returning-learner browser login helper corrected | `PracticeEvaluation.test.jsx`; current UI347/347; fake13/13 and real full run5 | Verified OK |
| 3.6 Execute every SQL question | Unknown | 67 execute; pg-s056 primary empty, pg-s053 semantic initials bug | Corrected references and data; actual double execution gate | `test_every_source_sql_has_nonempty_primary_and_executes_repeatably`, initials/orphan regressions | Fixed |
| 3.7 Essay sample answers/rubrics | Unknown | Two missing answers, retired rubric gaps, inaccurate prose | Corrected reviewed samples and canonical four-level rubric; old history fixtures preserved | `test_question_validator.py`, `test_localized_bank_sandbox.py` (162/162 combined) | Fixed |
| 3.8 API suite: real DB, authorization and deterministic providers | Unknown | Baseline1258/1258; current backend CI green at9e24edd | Named recovery, contracts and publication regressions added | Current API116/116, contracts156/156, statistics/security150/150; final whole suite due | Verified OK |
| 3.9 SQL + AI flows: learner then admin review/release | Unknown | Live404/timeout and invalid mixed generation rejected | Provider/prompt repair; invalid content uses validated recovery | Fake13/13; full real run5 1/1; actual SQL/admin reason/approve and hidden-score checks | Fixed |
| 3.18 Updated cases/test data: all failure modes deterministic | Unknown | Old assertions require a shortfall error | Exact-count regressions retain no-invalid-persistence/cache protections; typed HTTP fixtures | `test_every_generation_failure_preserves_exact_count_and_valid_content`; provider contract 4/4 | Fixed |
| 4.1 Competency: weighted points/CLOs and rounding | Unknown | Baseline algorithms pass | Independent DB/API/UI arithmetic confirms formula | `test_points_weighted_dimensions_and_no_duplicate_contributions`; current150/150; manual CLO25%, cumulative1.47% | Verified OK |
| 4.2 Statistics/gaps: owned, published evidence and bounds | Unknown | Current API150/150 passes | No change needed | `test_learner_dashboard_is_owned_and_only_published_formal`, `test_unassessed_learner_has_no_invented_zero` | Verified OK |
| 4.3 Learner analysis: 0/1/3 attempts, pending and accurate charts | Unknown | UI passes; current fake/real browser agree | No product change needed | `CumulativeRace.test.jsx`; UI347/347; fake13/13, real run5 and numerical screenshots | Verified OK |
| 4.4 Own ranking and persistent learner preferences | Unknown | Ranking privacy/ties and settings controls pass | No change needed | `test_learner_rank_never_exposes_another_learner_or_accepts_an_identity_override`; `StatisticsPanel`, `SettingsPage`, language/theme tests; Chromium baseline55/55 | Verified OK |
| 4.5 Admin dashboard/CLO/accounts: persist real edits with RBAC | Unknown | API158/158, statistics150/150; current admin journey passes | No change needed beyond cited bank publication fix | `admin completes provisioning, curriculum, human AI review, activation and analytics` targeted24.1s; UI347/347 | Verified OK |
| 4.6 Admin reports/settings: actual export, safe cells, frozen policy | Unknown | API/UI and browser settings pass | No change needed | `uses the administrator assessment filter and exports an actual named ranking`, `keeps missing evidence distinct from zero and escapes spreadsheet formulas`; fake Flow2/system setting | Verified OK |
| 4.7 Bank: seven valid unique cases per concept/difficulty/type | Unknown | Sparse source; 137/240 native scopes lacked seven distinct worked grids | Case-v2 boundaries/cardinalities; all 240 scopes have seven real grids, grounding 720 type cells | `test_each_case_cell_has_distinct_worked_results_and_grounded_answers`; full strict bank/SQL/seed/history 73/73 | Fixed |
| 4.8 Publication: edited content must pass common validation again | Unknown | 6 red cases: missing refs/explanation/sample, empty SQL and context-dependent SQL accepted | Common gate and double execution; citation editor; edits still demote to draft | `test_publication_rejects_every_common_content_contract_violation`, `test_edit_demotes_and_cannot_bypass_the_common_revalidation_gate`; API116/116, UI347/347, targeted admin browser | Fixed |
| 4.9 Score/dashboard regressions and independent arithmetic | Unknown | Current150/150 passes | DB/API/learner/admin cross-check added | `test_rounding_ranks_and_invalid_evidence`; .25/1=25%, .25/17=1.47%; `numerical-verification.json` | Verified OK |
| 4.10 Responsive UI: desktop/390px, accessibility and values | Unknown | Baseline55/55, current fake13/13 and real full scenario pass | Citation editor and count layout included in current UI347/347 | `390px mobile learner setup, attempt and evaluation fit the viewport`; numerical desktop/admin390 screenshots; final whole-browser repeat due | Verified OK |
| 4.12 Lint/format/CI: enforced stack and dependency gates | Unknown | No frontend lint/format command; installed pip has2 unique advisories | Pinned ESLint10/Prettier, patched glob dependency, reviewed unused bindings, pip26.3; CI gates added | npm ci0; lint0/format0; UI347/347,53.44s/build619ms; Python38packages/0advisories, npm frontend0; pushed-HEAD CI still due | Fixed |
| 5.1 Suggestions: prioritize measured weak skills without invented gaps | Unknown | Current guidance/statistics150/150 passes; running learner UI shows suggestions | No change needed | `test_guidance.py`, `test_competency_gaps.py`; fake full journey and real run5 | Verified OK |
| 5.2 Whole-system integration | Unknown | Stale fixtures and full-endpoint URL duplication broke current real integration | Reviewed fixture migration and endpoint composition repair | Production app13/13,320.910s; fake39/39,1130.341s; current live7 1/1,130.612s with no fallback | Fixed |
| 5.3 Learner UX: visible count, preserved retry/loading, 390px | Unknown | Count bounds duplicated and count hidden | API-driven presets, search/bounded chips, guarded retry preserves setup | `LearnerPages.test.jsx`; full UI 345/345; fake browser 13/13 and mobile-setup.png | Fixed |
| 5.4 Admin UX: focused navigation, actionable review, persisted edits | Unknown | Current fake navigation/review and targeted authoring pass | Added required citation editing/help; preserved metadata | `Admin navigation has five focused screens and no exam creation surface`; `QuestionAuthoring` UI tests, fake13/13, targeted admin journey | Fixed |
| 5.5 Final bank: every source valid with executable stable SQL | Unknown | Sparse source had factual/fixture errors and incomplete default seed | Complete validator/seed, distinct worked cases and official refs | Bank73/73; 5482static-valid,1747SQL/6988actual executions; current full-run bank cases pass | Fixed |
| 5.6 Integration/error scenarios | Unknown | Obsolete supplementary browser fixtures; required count failure modes already pass | Migrate fixtures to learner-defined practice; retain strict assertions and reviewed authoring metadata | API107/107 and matrix2268700/2268700; production application13/13,320.910s includes unavailable AI, early finish, stale revision and RBAC | Fixed |
| 5.7 Performance/resource limits: bounded SQL and concurrent durable work | Unknown |8-user load exposed retry-budget loss and evaluation starvation | Capacity admission and eligible-row selection; reproducible CI load gate | Native13/13, API65/65;8x20/259HTTP/42.186s, SQLpeak4/providerpeak2, timeout3025ms and size rejections | Fixed |
| 5.8 Final regression/retesting | Unknown | Inherited fixtures/transport issues and live generation acceptance failure | Connection, fixture and endpoint repairs; strict tests retained | App13/13 plus original-deadline1/1; fake39/39; smoke3/3; provider146/146; live7 passes/run8 fails; final pushed-HEAD CI link in final-status | Still failing |

Excluded: 1.1, 1.2, 1.9, 1.10; 2.11; 3.10–3.17; 4.11, 4.13–4.15;
5.9–5.16 (**25 IDs**), plus deliverables exclusively consisting of documents,
slides, minutes, backlog updates or reflections. No engineering title excluded.

## Issues and retests

| # | Flow | What happened | Expected | Severity | Status | Commit |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Bank practice | Sparse matching pool returns 422 | Exactly requested count with disclosed widening | High | Fixed; API and exhaustive matrix retested | `0c16327` |
| 2 | AI generation | Short/invalid batch has no validated template recovery | Bounded regeneration and exact validated fallback | High | Fixed; every required failure mode retested through API/DB | `0c16327` |
| 3 | Generation validation | Empty/non-repeatable/duplicate generated questions not rejected | Shared bank/AI validation | High | Fixed; schema/scope/SQL/content regressions pass | `98e227b`, `0c16327` |
| 4 | Bank content | Incorrect lock/FOUND/array/CTE claims, empty primary SQL, initials bug | Correct documented content and executable fixtures | High | Fixed; 162/162 plus final 41/41 retest; see bank audit | `b3bb04e` |
| 5 | Setup | Count constants repeated in API/UI, no frontend lint/format gate | Central configuration and enforced checks | Medium | Fixed; central limits/matrix and enforced frontend checks pass | `0c16327`, `7d6a047` |
| 6 | SQL edge data | 30 served edge fixtures had empty expected grids | Every served fixture nonempty; retain empty-input regression coverage | High | Fixed; strict source/SQL/upgrade 57/57, 422.45s | `3e6d3e2` |
| 7 | Bank upgrades | Subsequent registered revisions could create copies instead of safely updating/versioning | Match the recorded prior content hash and preserve owner edits/status/history | High | Fixed; three registry revision regressions pass within 57/57 | `3e6d3e2` |
| 8 | Large bank / CI fake QA | 20-second API response waits fail in 9 repeated browser cases | Selected-content validation and bounded response time | High | Fixed; final fake39/39 over3 consecutive repeats,1130.341s,0 retries | `0c16327` |
| 9 | Admin publication | Incomplete/unsafe questions could become validated | Apply the common content and executable SQL gate | High | Fixed; 6 regressions, API116/116, UI347/347 and admin browser retested | `cd220da` |
| 10 | Native content | 137/240 scopes reused worked results despite changed prompts | Seven relevant distinct cases in every scope | High | Fixed;73/73 bank/SQL/history and2268700 matrix retested | `f2351d1` |
| 11 | SQL connection | One full-suite connection timed out before SQL; no bounded reconnect | Recover once before SQL inside the original connection budget | Medium | Fixed; bounded reconnect and full backend1393/1393 verified | `4e6f9d5`, `3b3994f` |
| 12 | Concurrent SQL grading | Capacity waits consumed the sole grading try and permanently failed saved answers | Reserve existing capacity before committing a job claim | High | Fixed; admission/native/API tests and8 concurrent maximum-size attempts retested | `c79e0c6` |
| 13 | Evaluation queue | An old failed SQL row blocked unrelated learners until UI fallback | Select eligible jobs using frozen question types | High | Fixed; two red regressions, native13/13 andAPI65/65; load8/8 published | `c79e0c6` |
| 14 | SQL connection transport | Full backend r2 had1382pass/1fail: pre-SQL OperationalError during whole-bank execution | One classified transient reconnect within original budget, no SQL replay | Medium | Fixed;27/27 connection/native/protocol and full backend1393/1393 pass | `3b3994f` |
| 15 | Browser authoring/application fixtures | Default supervisor copied incomplete archived content; supplementary tests used retired exam routes and wrong new-context locale | Author reviewed complete copies; exercise current practice contracts without modifying archived definitions | QA | Fixed; production application13/13,320.910s, no skips/retries/flaky; supervisor identical fixture1/1,67.803s | `5b67ca0` |
| 16 | Configured live endpoint | A full chat-completions URL receives a second appended chat path; live6 and one diagnostic return404 | Accept API base or full endpoint; preserve query/model/schema and one wire request | Medium | Fixed;10red/4pass then146/146 and full live7 1/1; configuration unchanged | `d4a541c` |
| 17 | Real generation stability | Second final live run falls back at third-attempt generation despite HTTP200; strict full-run assertion fails | Consecutive full real runs accept valid generated batches without fallback | High / acceptance | OPEN; run7 passes130.612s, run8 fails110.990s; session20 exact3 safe bank fallback.70/80 used;10 left cannot cover16-call full run | Unresolved provider acceptance |

2026-11-05 live run8: **0pass/1fail,110.990s**, failure at strict generated
source no-fallback assertion; extraction/validation reason not retained after
container cleanup, so no specific invalid field is asserted. Read-only session20
has3 exact bank-origin questions at tier0 with disclosed fallback. First two
attempts/evaluations pass; invalid/unaccepted AI content does not enter the saved
attempt. Twelve wire requests, **70/80 total,10remaining**. Further live calls
stopped because a complete passing scenario used16. Final task5.8/overall live
stability remains failing; other final offline/clone/CI checks continue.

2026-11-05 clean-clone final refresh (`e3d5034`): no.env before startup; root/UI
npm ci40s/17s succeed; one npm start builds/seeds/health-checks. Browser **4/4
demo logins**,5482questions/80concepts, saved history, real SQL and explicit
no-key generation/evaluation fallback;390px and0 page errors. Independent
released score **1.14/7=16.29%** matches. `_review/audit-20261105/fresh-probe.json`
and `fresh-*.png`. Task1.5 final refresh verified; no live requests,70/80 unchanged.

2026-11-05 final smoke **3/3,205.638s**, zero failed/skipped/flaky/retries/global
errors, including13-question learner/admin grading/publication/competency and
real Mailpit password reset. JSON/log `_review/audit-20261105/smoke-three-*`;
owned new clone project stopped with volumes preserved. No provider calls.

2026-11-05 live run7 at `d4a541c`: **1/1,130.612s**, zero failed/skipped/flaky/
retries; validated generated mixed batch, no evaluator fallback, three attempts,
automatic/admin approval, SQL/write rejection, score reason/audit, independent
arithmetic, cached reread and390px pass. Endpoint repair146/146 and live pass
close issue16/task3.3; task5.2 whole integration is now verified. Meter16 new
requests, **58/80 total,22remaining**; previous failed6/diagnostic retained.
Report/screenshots `_review/audit-20261105/real-run7-*`; second final live run8
and final clone/smoke/current-HEAD CI still required for task5.8.

2026-11-05 full backend: **1393/1393,769.93s**, zero failed/skipped, one
Starlette/httpx deprecation warning. CI backend job at `5b67ca0` succeeds in
run41941974331, including whole-corpus repeated SQL execution, count matrix,
connection/native/resource regressions, all API/security/history/provider tests.
Installed dependency audit, lint/build, pip check, OpenAPI, static5482/0invalid,
Compose configuration and production image build also pass. Exact log retained
at `_review/audit-20261105/ci-backend-5b67ca0.log`; final frontend gate remains open.

2026-11-05 fake-provider gate: **39/39 (13 x3 consecutive repeats),1130.341s**,
zero failures/skips/flaky/retries/global errors. Both release policies,
0/1/3 numerical evidence, expired two-tab refresh, duplicate submission, delayed
module/provider, generation outage/timeout/exact fallback and390px pass.
`_review/audit-20261105/fake-three-results.json`; raw log retained. Audit project
restored and fake service removed with data preserved. Real requests unchanged
40/80; full live repeats, final clone/smoke and pushed-HEAD frontend CI pending.

## Historical milestone notes

Publication milestone: six initial red regressions, then affected API **116/116, 50.72s** and competency/statistics/history-security **150/150, 84.96s**. Full frontend **347/347, 57.79s**, build781ms, backend lint/build and OpenAPI/inventory pass. Targeted browser3/4 passed; lifecycle fixture fixes retested concept-authoring1/1 (27.4s). Archived old question fixtures remain intact; newly authored fixtures use reviewed source refs/explanations. Final full browser/CI gate remains open.

Quality milestone: pinned lint/format checks run locally and in CI. Initial lint44 issues corrected without suppressions; no test removed. Formatter review111 equivalent syntax trees +14 reviewed unused-binding changes,0 unexpected changes; current UI347/347 (53.44s), build619ms. Fresh npm ci9s, frontend audit0; Python38installed packages/0advisories after pip26.3 (two unique earlier advisories). Root2low/0high-critical: KaTeX prototype-pollution prerequisite in isolated diagram tooling; renderer upgrade requires compatibility review. Current full backend run has two early historical-fixture failures, report/fix pending; final gate open.

Completed full backend run **1366pass/7fail,1320.82s**: six stale publication fixtures and one pre-SQL connection timeout. Fixture repairs preserve every original assertion, reconstruct registered archived definitions directly as historical DB state, add required reviewed metadata to newly published fixtures and replace the new integration fixture's empty SQL edge with NULL/zero boundaries. Empty-input SQL grading tests remain unchanged. Affected publication/upgrade/integration/SQL/concurrency group **104/104,60.07s**. Generated UI inventory retains23 routes; only source fingerprint and formatted line numbers changed. Reconnect3 red/3 pass before fix, bounded retry regression now green within104; final full rerun remains due.

Sprint5 concurrency milestone: load first exposed `sandbox_busy` exhausting queued grading, then a failed SQL evaluation poisoning the queue. Two scheduling regressions red2/2; final native/admission/protocol **13/13,39.91s**, API/pipeline/statistics/provider **65/65,51.89s**. Capacity is reserved before the claim commits; no limits/retry counts increased. Worker skips ungradable rows using frozen types. Final controlled load **8 learners x20 questions**,5563 versioned bank rows/80 concepts, **259 HTTP requests,42.186s**,8 exact/duplicate-safe/published attempts and8 cross-learner404s, zero unexpected errors/backpressure on this run. Fake HTTP provider10calls,peak2; SQL peak4. Start16requests mean2549.58ms/p953506.86; submit48 mean2240.56/p957795.76; SQL8 mean3642.63/p956686.41; evaluation74 mean50.48/p9591.62; statistics8 mean39.87/p9560.81; full bank listing1737.39ms. Statement timeout3025ms wall measurement; cell/row limits rejected; offline limits unchanged. Published60session/583attempt row hashes preserved across upgrade. Earlier failures, wrong load-client refresh body and helper WSL group forwarding fixed and retained in local evidence; no real-provider requests. Current source CI backend green at4e6f9d5, frontend54/55: one remaining newly authored browser fixture lacks metadata; fix pending.

## Execution sequence

- [x] Execute and record untouched backend/frontend/browser baselines.
- [x] Correct 98 reviewed source definitions; strict content 442/442, localization 442/442, SQL 67/67, final semantic/content regressions 41/41. Coverage/seed still pending.
- [x] Central count configuration, deterministic widening, bounded AI recovery;
  named red/green regressions and exact matrix; commit/push each verified step.
- [x] Reverify Sprints 1–4 in order with API/browser/data evidence, update handover.
- [ ] Finish Sprint5 integration and final regression; scheduling/load verified at `c79e0c6`.
- [x] Three fake repeats,390px, independent arithmetic, controlled load/security and final no-env clone/smoke.
- [ ] Consecutive full live acceptance: run7 passes/run8 fails;70/80 used,10left; no further full run fits.
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

Case-v2 bank regression **73/73, 411.91s**; seven distinct worked grids for each of 240 scopes and real answer grounding for all formats. Authoring manifest **11546 executions / 547.361s**; strict independent execution 1747 SQL x 2 fixtures x 2 checks = **6988**, all pass. Every changed native ID has a before-hash/source commit, issue, fix and official documentation reference in the structured change ledger. Current SQL/content/history gate is green; case-v2 matrix **2268700/2268700**, 151.352s, zero failures.

Live run5: complete real scenario **1/1, 126.438s**, zero failed/skipped/flaky/retries: 0/1/3 overall evaluations, automatic and approved release, required score-edit reason, SQL run, cached reread, validated mixed AI batch and 390px. Earlier run1/2/4 failures retained. Total actual calls **40/80**, remaining40. Two further full real runs fit the budget if no extra calls are needed; reserve them for final code.

Independent numerical check (learner9, sessions11/12/13): CLO PGX-FUNC **0.25/1 x100=25.00%**; pooled cumulative **0.25/17 x100=1.47%**. Read-only PostgreSQL aggregates, learner/admin statistics APIs, overall API and both browser screens agree; desktop/390px, zero page errors. Evidence `_review/audit-20261104/numerical-*`; weighted-dimension regressions remain in `test_competency_dimensions.py`.

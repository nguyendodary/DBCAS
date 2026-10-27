# DBCAS first-time-user acceptance — final evidence report

Completed: 2026-10-26T14:20:43.803248+07:00

## A. Executive verdict

**FULL FIRST-TIME-USER E2E ACCEPTANCE PASS**

All eight final browser gates completed with the required case counts, exit 0, no failed/flaky/skipped cases, and no global setup/teardown errors. The unchanged backend pass was recovered. A WebKit Help-focus defect required a small client fix, one regression test, and renewed frontend/build and browser verification. No implementation was restarted.

Browser runs used the Vite E2E frontend on 127.0.0.1:5174 and an isolated API on 127.0.0.1:8100. The production frontend build was checked separately.

## B. Help Guide

The Help control is in the upper-right utility group on desktop login/registration, learner and administrator workspaces and the exam. On mobile it remains in the responsive header/control row. Saved Firefox desktop-dashboard and 390 px exam screenshots were visually checked for placement and spacing. EN/VI content covers onboarding, Practice/Formal, question types, SQL sandbox, AI/essay processing, release states, results, language/theme, accessibility and troubleshooting. Route hints and role-specific Learner/Administrator sections are verified; the public guide contains both.

The drawer stays closed until requested. Evidence covers named modal semantics, background inertness, scroll lock, Escape/close/backdrop actions, focus restoration, section-heading focus and keyboard focus trapping. The 8 HelpGuide unit tests passed inside the 275-test frontend suite. Browser axe checks using wcag2a/wcag2aa tags pass on desktop, 390 px mobile and in the exam. Workspace tours cover EN/VI, light/dark themes and widths 390/768/1024/1440 px. In-exam Help preserves answers and the running countdown.

## C. First-time-user journeys

Each release browser ran the same 49-case suite, including UI registration/login; Help discovery and EN/VI switching; skill and EASY/MEDIUM/HARD selection; Practice/Formal; MCQ, executable SQL and essay; saved-answer navigation, drafts and refresh/resume; network recovery and duplicate submission; submission, history and cumulative competency.

The formal immediate journey completes 13 questions (10 MCQ, 2 SQL, 1 essay). The controlled-provider human-review journey verifies auto_grading → grading_failed → retry → pending_review → human-adjusted score → publication and released competency. SQL syntax errors, restricted DELETE and bounded execution timeout are exercised. Practice results remain outside official cumulative competency.

Each 10-case application suite separately uses app.main without dependency overrides or /__test routes. It verifies authentication, role promotion/revocation with immediate token enforcement, authorization and cross-user boundaries, strict difficulty, persisted drafts, unavailable AI, manual correction/publication, stale publication revision rejection, idempotency, cumulative evidence and responsive routes. Browser-level redirects require their final destination; API role checks continue to require 403, and unrelated-learner evidence access requires 404.

## D. Blueprint coverage

**All 49 approved blueprint scopes were started in Formal mode through the visible learner UI in each of the four release browsers** (196 verified scope starts). Per-browser HTTP diagnostics independently record 49 successful UI starts (201) and 49 successful UI finishes (200): assessment 2 = 4, assessment 3 = 6, assessment 4 = 9, assessment 6 = 30.

The test asserts distinct session IDs, scope/concept coverage, approved version 1, difficulty bounds, expected MCQ/SQL/essay mix, no duplicate question families, and idempotent resume. This is UI execution, supplemented by sanitized assembly inspection. These 49 scope sessions intentionally finish with zero answers; they do not claim 49 fully answered/graded exams. Full completion and grading are exercised by the separate journeys above. Imported blueprint approved_by remains NULL; no human/instructor content approval is claimed.

## E. Test results

| Gate | Result | Evidence |
|---|---|---|
| Backend full suite | 1,039 passed; 1 existing deprecation warning | [Recovered log](../../_review/remediation/final-backend-pytest.log) |
| Frontend full suite | 275 passed in 34 files, including 8 Help tests; exit 0 | [Final log](../../_review/remediation/resume-20261026/frontend-unit-after-focus-fix.log) |
| Production build | PASS; exit 0 | [Final log](../../_review/remediation/resume-20261026/frontend-build-after-focus-fix.log) |
| Chromium release | 49/49 PASS; exit 0; 0 skip | [Log](../../_review/remediation/resume-20261026/release-chromium-cffe4980e6/run.log), [JSON](../../_review/remediation/resume-20261026/release-chromium-cffe4980e6/browser-results-chromium.json) |
| Firefox release | 49/49 PASS; exit 0; 0 skip | [Log](../../_review/remediation/resume-20261026/release-firefox-cffe4980e6/run.log), [JSON](../../_review/remediation/resume-20261026/release-firefox-cffe4980e6/browser-results-firefox.json) |
| WebKit release | 49/49 PASS; exit 0; 0 skip | [Log](../../_review/remediation/resume-20261026/release-webkit-cffe4980e6/run.log), [JSON](../../_review/remediation/resume-20261026/release-webkit-cffe4980e6/browser-results-webkit.json) |
| Edge release | 49/49 PASS; exit 0; 0 skip | [Log](../../_review/remediation/resume-20261026/release-msedge/run.log), [JSON](../../_review/remediation/resume-20261026/release-msedge/browser-results-msedge.json) |
| Chromium application | 10/10 PASS; exit 0; 0 skip | [Log](../../_review/remediation/resume-20261026/application-chromium-b872116bd2/run.log), [JSON](../../_review/remediation/resume-20261026/application-chromium-b872116bd2/browser-results-chromium.json) |
| Firefox application | 10/10 PASS; exit 0; 0 skip | [Log](../../_review/remediation/resume-20261026/application-firefox/run.log), [JSON](../../_review/remediation/resume-20261026/application-firefox/browser-results-firefox.json) |
| WebKit application | 10/10 PASS; exit 0; 0 skip | [Log](../../_review/remediation/resume-20261026/application-webkit/run.log), [JSON](../../_review/remediation/resume-20261026/application-webkit/browser-results-webkit.json) |
| Edge application | 10/10 PASS; exit 0; 0 skip | [Log](../../_review/remediation/resume-20261026/application-msedge-b872116bd2/run.log), [JSON](../../_review/remediation/resume-20261026/application-msedge-b872116bd2/browser-results-msedge.json) |

All browser gates: HEAD `7ccdc44d761e56da935825313e95d2cdb1262366` with the preserved uncommitted source. Exact per-gate source SHA-256 and per-file hashes are recorded in [gate-matrix.json](../../_review/remediation/resume-20261026/gate-matrix.json) and each gate's source-before/source-after manifests. Every final gate has an unchanged source fingerprint across its run. The backend application/test source predates its recovered full-suite pass. The frontend full suite and production build were rerun after the Help focus fix. After all four release passes, the only further source change was frontend/e2e-application/application.spec.js, which is outside the release testDir, Vitest include and production entrypoint. Every other captured source file matches byte for byte; [input-equivalence evidence](../../_review/remediation/resume-20261026/gate-input-equivalence.json) verifies this against the final tree. Those completed gates were retained, and all four application suites ran the updated application test. No separate database/security subset rerun was necessary for these frontend/test-only changes.

### Per-gate database identities

| Gate | Disposable database container | Test-run UUID | Isolation evidence |
|---|---|---|---|
| release-chromium | `dbcas-test-35ad20c6` / `dbcas_test` | `2499f680dd454863a1a6356d63f6e540` | [Proof](../../_review/remediation/resume-20261026/release-chromium-cffe4980e6/database-isolation.json) |
| release-firefox | `dbcas-test-f5871db5` / `dbcas_test` | `5b23f2403c6449c7b80f040c11b74b4d` | [Proof](../../_review/remediation/resume-20261026/release-firefox-cffe4980e6/database-isolation.json) |
| release-webkit | `dbcas-test-a402f99b` / `dbcas_test` | `291e966427bd45709d69394395517631` | [Proof](../../_review/remediation/resume-20261026/release-webkit-cffe4980e6/database-isolation.json) |
| release-msedge | `dbcas-test-801e24a5` / `dbcas_test` | `15e3a7bf70f148ce8c5f154e511cbcdf` | [Proof](../../_review/remediation/resume-20261026/release-msedge/database-isolation.json) |
| application-chromium | `dbcas-test-cc3c9088` / `dbcas_test` | `9cbb02cfbd814a05a5cdf9e605d23773` | [Proof](../../_review/remediation/resume-20261026/application-chromium-b872116bd2/database-isolation.json) |
| application-firefox | `dbcas-test-97b7a95c` / `dbcas_test` | `fd00bffa7988493abe7f0fa20afb9360` | [Proof](../../_review/remediation/resume-20261026/application-firefox/database-isolation.json) |
| application-webkit | `dbcas-test-f8529719` / `dbcas_test` | `25bb94c2b572408d99686daf7dc1e2ee` | [Proof](../../_review/remediation/resume-20261026/application-webkit/database-isolation.json) |
| application-msedge | `dbcas-test-a263fd8c` / `dbcas_test` | `97ff5698250b469dbf64228d2689e759` | [Proof](../../_review/remediation/resume-20261026/application-msedge-b872116bd2/database-isolation.json) |

All eight databases run PostgreSQL 17 in ownership-labelled tmpfs containers with no persistent mounts. Before mutating E2E, the live API writes a probe that is observed in its disposable database and absent from persistent development. The sandbox is separately owned and disposable. Gate launches were sequential.

## F. Confirmed defects and regression outcomes

1. Prior implementation fixed Practice sessions entering official cumulative competency. Legacy sessions without an assembly_mode retain formal behavior. Regression: the recovered full backend suite and final practice/browser journeys pass.
2. Prior implementation removed Help's entrance opacity fade after an axe contrast finding. Unit and final browser checks verify opacity 1 and clean axe results.
3. Earlier test assumptions were adapted to the expanded bank (multiple Start controls, duplicated text, target ordering, assessment rule selection and asynchronous redirects). Final role destination and API authorization assertions remain explicit.
4. The recovered Firefox run passed 49 test cases but failed global teardown; its original OS exit code was not retained, and .last-run.json reports failed. It was never accepted as a passed gate. The existing ownership-checked cleanup succeeded on replay (exit 0); original subprocess stderr was not exposed, so the precise original cause is unconfirmed. Both disposable databases were archived before replay. The full Firefox rerun then passed with a captured exit 0 and no global errors. [Recovered run](../../_review/remediation/resume-20261026/release-firefox-recovered/run-recovered.log), [cleanup replay](../../_review/remediation/resume-20261026/cleanup-reproduction.json).
5. **WebKit Help focus restoration:** pointer activation did not focus the button, so the drawer captured the previous element and failed to restore the invoker. HelpButton now explicitly focuses its own trigger before opening. A new pointer-activation unit regression failed before the fix (7 pass / 1 fail), then all 8 Help tests passed. The original WebKit failure assertion was retained; the failed run was archived and stopped, with its 7 completed passes, 1 failure and 41 incomplete cases kept separate from full-gate results.
6. **Registration-to-login test timing:** WebKit's trace showed the URL changing before the Login component mounted; automation filled the outgoing registration field, then native validation blocked login with an empty email. No login request was sent. The E2E case now waits for the visible Sign in heading and requires HTTP 200 from the login request before requiring the exact dashboard destination. No authentication implementation was changed.
7. **Preserved WebKit diagnostic:** the 49-scope test recorded an access-control page-error message for GET /api/v1/sessions. Its diagnostics also record 49 successful GET responses (all 200), no failed requests, no console errors and all 49 completed UI scope assertions. No request failure or functional defect was demonstrated by that record. The message is retained in journey-evidence.json; its precise browser origin is not proven, and no assertion was relaxed or error filtered in response to it.
8. **Application-test Practice/official mismatch:** the old helper deliberately selected Practice while expecting its results to enter official competency. The application correctly returned zero. The fixture now preserves its publication-required Easy pool and adds a feasible Medium Formal pool. The journey requires zero official contribution after three completed Practice sessions, then completes all 13 Formal questions (10 MCQ, 2 SQL, 1 essay), checks withheld evidence and unavailable AI, publishes human-verified results, and requires exactly one official contributing session with the precisely pooled Formal score. No product scoring or authorization implementation was changed for this test correction.
9. **Edge setup isolation check:** the first Edge application attempt stopped before any test ran because the probe query did not confirm its account in the disposable database. Its containers had already been cleaned up when inspected, so the failed probe's exact cause remains unconfirmed. An immediate read-only audit showed every persistent table unchanged. The retry used a fresh owned database and the unchanged strict isolation guard; only the subsequent complete 10-test, exit-0 run is accepted. The original zero-test setup failure remains in gate-matrix.json and its run log.

The earlier Chromium 48/49 result and 16/16 targeted rerun are preserved but are not used as proof of a full pass. After the shared Help fix, all four full release gates and all four application gates were verified against the same application inputs. Later application-test-only edits are explicitly accounted for by the input-equivalence evidence. Earlier full Firefox/Chromium passes on the preceding Help source remain historical evidence.

## G. Persistent database integrity

Persistent development: `dbcas-db`, database `dbcas`, PostgreSQL 17.11, system identifier `7691984040786436134`, volume `dbcas_db-data`. All **34 table counts and hashes** match the initial, pre-E2E, before-remaining-gates and resumed captures. Both historical fingerprint formats were reproduced: SQL composite-row string aggregation and canonical JSON-row hashing. The 13 migration ledger rows (001–013) are unchanged, including checksums.

Preserved: **713 questions, 713 translations, 49 blueprints, 18 historical sessions, 109 historical attempts**. Persistent access during continuation used read-only transactions. No migrations or content/historical edits were applied to persistent development. No Docker volumes were deleted. See [final integrity audit](../../_review/remediation/resume-20261026/integrity-final.json).

## H. Git and scope limitations

HEAD: `7ccdc44d761e56da935825313e95d2cdb1262366`. Working tree: **19 modified tracked files and 9 untracked files**, preserved. [Final status](../../_review/remediation/resume-20261026/git-status-final.txt). No commit or push. No academic documentation or AI/OAuth configuration was changed.

Controlled release grading verifies application state and scoring paths at the provider HTTP boundary. Application gates verify the real unavailable-provider/manual-review path. Live external AI provider success and completed external OAuth sign-in are outside these results; OAuth state/callback safety is tested. Automated accessibility checks do not constitute a manual screen-reader audit.

Machine-readable browser journey evidence: [journey-evidence.json](../../_review/remediation/resume-20261026/journey-evidence.json).

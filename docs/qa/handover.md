# Active handover - 2026-11-04

- Branch `develop2`, HEAD `0df6bf9`, pushed. New commits: `d9bbbd0` recovery baseline, `b3bb04e` source corrections, `0df6bf9` complete balanced bank/safe seed. Independent dirty main checkout untouched.
- Baseline executed before application edits: backend lint/build OK, **1258/1258**, 757.49s; frontend ci/build OK, **344/344**, 109.02s; Chromium **55/55**, 1774.01s, 0 skipped/failed/flaky/retries, desktop/390px. Launcher **7/7**. Baseline CI green.
- Bank: **5,482 = 2,006 MCQ / 1,747 SQL / 1,729 essay**, 80 concepts; all 720 cells meet derived quota 7. **121** reviewed prior definitions now retained. A stricter review found 30 empty legacy edge outputs (red gate 30 invalid); every served fixture now must be nonempty. Added qualifying boundary rows while retaining negative cases; original empty-input cases remain separate tests. Repair tool executed **120** queries; expected-grid manifest now records **6,056 actual PG executions / 292.263s**, with identical pairs reused. Strict bank/upgrade regression **57/57, 422.45s**; earlier source SQL gate **41/41**, 436.78s and seed gate **11/11**, 56.32s preceded this tightening.
- Uncommitted count milestone: central bounds 1/default5/max20 exposed by API and UI presets; deterministic balance/widening, two bounded generation attempts, strict shared validation, partial-batch duplicate protection, bank then validated template recovery and persisted Vietnamese notices. Matrix **2,268,700/2,268,700**, 186.28s. API recovery **48/48**, 58.03s, then 3/3 whitespace-config checks; strict-edge recovery **52/52, 53.54s**. UI targeted **43/43**, 12.91s, build 1.14s. Runtime OpenAPI/inventory checks pass.
- Isolated current stack `dbcas-audit-20261104`: ports 18780/18700/18725/11725, no real-provider access. Running API confirms 80 concepts and central limits. Learner real Chromium scenario **1/1**, 1.3min: 0/1/3 attempts, saved drafts/reload and API/UI arithmetic. Stack image predates the final strict-edge edits; rebuild/upgrade and prove history preservation next. Original `dbcas-local` and `dbcas-cont-fresh` untouched.
- Official PG 18.6 docs reviewed; sandbox PG17. No network restrictions for official docs. Newer source revisions now match registered prior content hashes, preserving owner edits/status and versioning referenced rows; registry revision regressions pass.
- New-key budget: **0/80 actual provider calls**, no token/latency usage yet. Newer key remains privately in separate main .env; not copied/logged. Both .env files ignored. Fresh 80-call ledger/meter still needs activation; old key ledger is separate.
- Security baseline: frontend 0; root 2 low/0 high-critical. Python app dependencies clean; installed pip 26.1.1 has two advisories requiring upgrade. Frontend lint/format CI remains to implement.
- Next: commit/push the verified strict bank/upgrade correction separately; retest and commit/push count implementation. Then verify all 45 sprint titles in order, complete fake-provider browser repeats and metered live scenario, performance/concurrency/security, fresh clone without .env, full final suites and pushed-HEAD CI. No final completion claimed.

Previous handover evidence follows unchanged.

# QA continuation — 2026-11-04

## Current instruction and active work

Branch/worktree: `develop2`, `_worktrees/dbcas-dn-20261101`; starting commit
`98e227b`, clean and synchronized. Its CI [41694671249](https://github.com/nguyendodary/DBCAS/actions/runs/41694671249)
was verified successful. Original dirty main checkout remains untouched.

Current user scope supersedes older notes: **45 tasks regardless of Jira status**,
exact count with disclosed widening and validated templates, complete bank audit,
and a **fresh 80-request ledger for the new key**. The prior-count blocker and
59-call policy below belong to the previous key/job and no longer block this job.
The newer main-checkout `.env` differs from the worktree's older credentials;
use its existing key/model privately. `.env` is ignored and untracked.

Current job real requests: **0 / 80**, tokens **0**, remaining **80**. Do not enable
a provider until the fresh ledger reserves each wire request including retries.

Baseline frontend: `npm ci` exit 0; **344/344**, 39 files, **109.02s**, build exit 0
(1.02s); npm audit **0 vulnerabilities**. Backend lint/build exit 0; full backend **1258/1258**, **757.49s**, 0 failures/skips,
1 dependency deprecation warning; full Chromium baseline running. Logs: `_review/audit-20261104/`.
Official PostgreSQL stable docs verified as **18.6**; 123/125 existing source URLs
fetched, two stale paths identified. **442 questions / 80 concepts** inventoried;
content and count defects recorded before changes in the two audit files.

Next: finish untouched backend then browser baseline, correct bank and execute
every SQL item, implement shared validation/count recovery, then sprint audit and
full gates. Keep only `task-audit.md`, `bank-validation.md`, and this handover as
new concise QA evidence. Browser runtime discovery returned no supported in-app
execution tool; use the existing real Chromium Playwright runner.

---

## Resume from here (latest state)

Work only on `develop2` in `_worktrees/dbcas-dn-20261101`. Last UI change:
**`b15a28f`**; backend field guard `dabda62` and the subsequent cache-validation fix follow green CI `e729f87`. Do not redo
completed flows unless their code changes. The original dirty `DBCAS` main
checkout and its independent work have not been modified.

**DONE — previous agent:** practice/approval/evaluation architecture, five Admin
screens, privacy, charts, persistence, auth/race recovery; see `docs/final-status.md`
and green starting-HEAD CI `41582152378` (`f14bd6d`). These were fake-provider gates.

**DONE — continuation:**

- `4188a8b`: finish the inherited generation failure/retry change; 503/code/no
  fabricated session, matching-bank fallback, identical retry request ID; fixed
  screenshot timing and independent HTTP transaction regression.
- `7e79072`: opt-in live three-run scenario and atomic request ledger capped at
  59 including retries/timeouts; **10/10 deterministic tests**. The normal suite
  still forbids provider networking. [Runbook](real-provider-runbook.md).
- `af2bce0`: bounded JSON-line SQL bridge; deterministic EOF regression red then
  green, CRLF/boundary/isolation/cleanup checks retained (**10/10** targeted).
- `b15a28f`: prioritize current-answer submission; whole-practice finish remains
  secondary during an active question. Before/after screenshots are in the report.
- Latest AI guard: reject SQL fixtures attached to MCQ/essay questions rather
  than discarding them; require null fixtures/quoted aliases in the prompt.
  Six added cases cover validation plus bank fallback/503 with no invalid
  question persistence; **52/52 targeted pass**, 26.48s. Final CI must verify.
- Cache follow-up: schema-valid/domain-invalid generation previously entered
  cache before being rejected, preventing same-ID retry from recovering. A real
  `LLMService` + fake provider/cache regression was red; the domain validator now
  runs before cache storage, with its parsed result reused. **53/53 targeted
  pass**, 29.60s; invalid cache/session/question counts stay zero, retry makes
  exactly a second provider call and replay makes none. Final CI must verify.

| Verified local gate | Evidence |
| --- | --- |
| Backend lint/build/pip check; **1257/1257**, 0 failed/skipped, 728.26s | `_review/continuation-backend-fixture-guard-full.log`; field guard included, before cache follow-up |
| Frontend npm ci/build; **344/344**, 39 files, 105.97s; audit **0 total/high/critical** | `_review/continuation-frontend-ci-fix-full.log`, build/audit logs; runtime UI source `b15a28f` |
| Local normal browser **55/55**, 1623.34s, 0 failed/skipped/flaky, retries=0 | `_review/continuation-regression/browser-results-chromium.json`; before final fixture-type guard |
| Green CI `e729f87`: **1251 backend / 344 UI / 55 browser / 3 smoke / 33 fake**, 0 browser failed/skipped/flaky | [41665844483](https://github.com/nguyendodary/DBCAS/actions/runs/41665844483); final CI rechecks after the guard |
| Remote clone started with no `.env`, 4 healthy services, init/executor exit 0 | `continuation-20261103/gate-results.json`; clone source `b15a28f` |
| Four demo UI logins, no-key AI→bank fallback, SQL, rule evaluation, **1/11 = 9.09%**, 390px, **0 page errors** | [Fresh proof](continuation-20261103/fresh-probe.json), screenshots in report |
| Launcher **7/7**, OpenAPI and inventory current | `_review/continuation-launcher.log`; contract/inventory commands passed |

**IN PROGRESS:** verify the final HEAD's GitHub Actions run before final response.
This evidence-only push triggers the existing unchanged full workflow. Read its
actual counts (backend, frontend, 55 regression browser cases, 3 smoke repeats,
11 fake-provider cases × 3). Do not claim a pending run is green. Use
`gh run list --branch develop2 --limit 1 --json headSha,status,conclusion,databaseId`
and the matching run's logs. [Branch checks](https://github.com/nguyendodary/DBCAS/actions?query=branch%3Adevelop2).

CI `41663589531` confirmed backend success but found one frontend test race
(343/344): the Dashboard cost-guard assertion preceded React initialization.
The follow-up test/CI commit controls the initial session response inside `act`,
retains `include_explanations=false`, adds one-call/rendered-guidance checks,
and guards cleanup when failure precedes `.env` creation. Dashboard **25/25**
(6.34s), full UI **344/344** (105.97s); no timeout/assertion weakened. Normal
browser regression also completed **55/55** against that application code:
`_review/continuation-browser-full.log`, output `_review/continuation-regression/`,
manifest `_review/continuation-release-containers.json`, Mailpit 18625/SMTP 11625.
Its owned disposable containers were cleaned by the test harness.

**NOT STARTED / blocked prerequisite:** real-provider three-run acceptance.
Continuation used **0 real calls / 0 tokens**. Prior actual request/retry count
is unknown; 27 cache rows are not a counter. User clarification is pending.
Do not spend until reconciled; authorization already exists within the <60 cap.
Opt-in gate correctly skipped 3 cases when not activated. No live-quality acceptance,
latency distribution, failure rate or prior token total can be claimed.

The matching prior session's public notes independently confirm the same
unbounded-call-accounting condition and that it stopped the real stack. The
unrelated session with a different cwd was not inspected. Offline cached-batch
review now found 3/3 reference SQL syntax errors, a duplicate-primary-key fixture,
and SQL fixtures discarded by non-SQL generation. The batch was rejected for type
labels; the latest guard closes the discarded-field issue as well. Do not call
the provider to retest it until the total request count can be established.

**Known limits:** initial native Windows run had 1242 pass / 2 fail; later serial
1251/1251 passed. Exact cause of earlier Docker-start/fixture transients remains
unconfirmed; no deadline/assertion was relaxed. Initial and diagnostic logs stay
local. Only owned temporary resources were stopped/cleaned after ownership checks.

Updated fallback preview remains running at **http://localhost:18680**
(`dbcas-cont-fresh`); API 18600, Mailpit 18625. The original 18080 stack was left
untouched. `.env` is ignored/untracked, and known-key/pattern scans of staged and
working diffs plus all Git history were clean before each push.

Detailed issue/commit table, arithmetic and screenshots:
[continuation report](continuation-20261103/README.md).

## Historical recovery notes (superseded by the state above)

## Recovered state

- Working tree: `_worktrees/dbcas-dn-20261101`, branch `develop2`, starting HEAD `f14bd6d`.
- Ran fetch, checkout and pull/rebase. Reviewed all seven inherited modified files; temporarily stashed those files to permit pull, then restored them. Remote was already current. No inherited work discarded. The separate dirty `DBCAS` main checkout is untouched.
- Read `AGENTS.md`, `CONTRIBUTING.md`, the last 40 commits, `docs/final-status.md`, `docs/qa/browser-qa.md`, and the existing browser QA plan. Neither `real-key-qa-brief.md` nor an earlier handover exists in this tree.

## DONE with existing evidence (previous agent)

| Work | Evidence | Limits |
| --- | --- | --- |
| Practice setup, immediate/review release, five Admin screens, mobile, autosave, double submit, timeout and two tabs | `docs/final-status.md`, `docs/qa/browser-qa.md`, `docs/qa/final-20261103/`; code through `853c275` | Historical fake-provider evidence, not real-key acceptance |
| Historical full gates | At `853c275`: backend 1228 pass; UI 340 pass; browser 55 pass; fake HTTP 30 pass; local scenario 3 pass; fresh checkout; CI run 41510594920 | Later commits require targeted verification and final current-code gates |
| Proxy readiness | `438e68d`, 7 launcher tests and recorded 502→200 reproduction | Do not infer every older CI login failure has the same cause |
| Polling retry, generated type validation, pending cohort exclusion | `c78a92d`, `0f3f153`, `6b6b8d6`, `f14bd6d` | Review current local results before claiming acceptance |

## IN PROGRESS inherited from previous agent

- Seven-file change: generation/provider failure with insufficient bank must return `generation_unavailable`, explain recovery, and offer **Thử lại**; never fabricate a template batch as though it came from AI. Backend and UI regressions added. Fake release provider gained the practice-generation protocol. Browser regression also checks cohort unchanged while review is pending and +1 after approval.
- Completed: rebuilt current changes, **11/11 browser scenarios pass**, 0 failed/skipped/flaky, retries=0, 336.65s. Inherited failing result preserved as `_review/continuation-inherited-browser-results.json`; precise original runtime/build cause unconfirmed. No additional product defect inferred from that old result.
- Strengthened new HTTP regression to assert 503/code/no session, releasing the direct-call transaction first (2/2 pass, 1.99s). Strengthened browser retry to check identical request, no fallback and visible recovered question (1/1 pass, 10.0s). Initial screenshot was a skeleton; corrected capture is in the report.
- Detailed issues, screenshots, hand arithmetic and gates: [continuation-20261103/README.md](continuation-20261103/README.md). Inherited work committed and pushed as **`4188a8b`**; real-call accounting remains unresolved.

## NOT STARTED / not yet verified in this continuation

- Local `.env` has a key; host `openrouter.ai`, configured route `openrouter/free`. `.env` is ignored and untracked. Running app deliberately points at loopback port 1. Its DB has **27 cached responses** with that route (26 `gap_explain`, 1 `practice_generation`), plus 43 explicitly fake-provider cache rows. Prior request/retry count remains **unverified**, and cannot be inferred from cache rows. No prior real-call ledger found in QA docs or saved local logs. Clarification requested; no dependent real calls until reconciled. Current continuation real calls: **0**. Hard total cap: **under 60**.
- Finish inherited generation retry and run only affected/unverified flows; log new defects with screenshots.
- Add opt-in real-provider tests (skip without key), retain deterministic equivalents, then three consecutive real-key scenarios if credentials and budget permit.
- Current-code backend lint/build/tests; frontend npm ci/tests/build/audit; browser 0 failed/flaky; fresh clone without `.env`; CI and pushed-HEAD verification.

## Execution steps

1. Diagnose the existing generation-retry browser failure; inspect provider contract and screenshots. Run targeted API/UI/browser tests, fix only evidenced defects, update this note, commit and push.
2. Establish credentials/call ledger from safe metadata. Use existing user flows and 3–5 questions, caching enabled; record call count/tokens/latencies without request secrets. If no key, state that real acceptance remains unavailable while finishing independent work.
3. Run remaining browser paths and hand-check published scores/dimensions/ranking. Record arithmetic and each screen's evidence.
4. Run final gates once on final code, repeat only if dependencies change or a failure requires it. Verify `.env` ignored and scan staged diff/history for secrets before every push.

## Open issues and environment

- Browser plugin instructions were read; the required `node_repl` execution tool is absent after both discovery attempts. Use the available Playwright browser tools as the fallback for interactive inspection; existing Playwright test runner remains available for regression.
- Docker access requires execution outside the sandbox; read-only `docker ps` succeeded with approval. Several unrelated stacks exist; operate only on the explicitly local DBCAS QA project.
- Git commit identity and staged diff must be checked for each commit per `AGENTS.md`. User-requested `<Area>: <description>` commit format takes precedence over the repository's generic Conventional Commits convention.

## Continuation evidence

- `backend/tests/test_learner_practice.py`: **25 passed**, 0 failed, 1 dependency deprecation warning, 22.26s (`_review/continuation-practice-api.log`).
- `LearnerPages.test.jsx` + `PracticeEvaluation.test.jsx`: **31 passed**, 2 files, 10.86s (`_review/continuation-targeted-ui.log`).
- Starting HEAD `f14bd6d` has successful CI [41582152378](https://github.com/nguyendodary/DBCAS/actions/runs/41582152378), verified via GitHub CLI. This supersedes the older CI status in final-status.md.
- Rebuilding current changes in isolated project `dbcas-cont-qa` (ports 18480/18400/18425/11425/18499), with real provider disabled. The initial launcher invocation refused a real key because PowerShell removed an empty environment override; corrected using a whitespace key (disabled by `.trim()`). No request was sent by that refused invocation.
- Full frontend: npm ci/build passed; **344/344**, 39 suites, 143.63s, audit 0 total/high/critical. Backend lint/build/pip check passed. Targeted results above precede the final full backend gate.
- Next: finish opt-in real-provider request ledger and scenario (never weaken the automated suite's no-network guard), run full backend/current CI gates, and verify a fresh clone. Do not enable real calls without a verified prior count.
- Opt-in request ledger and three-run scenario implemented; [runbook](real-provider-runbook.md). Deterministic meter tests: **10/10**, 2.76s, covering successful/failed HTTP, timeout, crash persistence, concurrency and cap. Opt-in browser gate: **3 skipped** because activation is absent, as intended. The runner's missing-history guard was exercised and refused before starting anything. Live orchestration and content remain unverified; 0 continuation requests.

## Current in-progress gate investigation (after `7e79072`, pushed)

- Full native Windows backend run `_review/continuation-backend-full.log`: **1242 pass / 2 fail**, 765.01s; do not count it as acceptance. Failures: offline-container execution and bilingual bank import. Standalone bank import passed 1/1 in 68.42s; precise transient cause unconfirmed.
- Added `dn/test_sandbox_protocol.py`. A real pipe kept open reproduces EOF dependence deterministically (red 1/1, 1.61s). Two uncommitted product lines now send/read a bounded JSON line, preserving the 100000-byte payload limit; frame tests pass in the targeted run. Added CRLF/limit boundary coverage after that run.
- Targeted real Docker tests still failed at **Docker start** (5 pass / 1 fail, 89.09s), so framing alone does not establish the original failure's cause or resolution. Inspect CLI error/timing using local-only `_review/sandbox_probe.py`; do not loosen timeout/resource/assertion limits to pass.
- After the idle owned QA stack was stopped, **10/10 protocol + real Docker sandbox tests pass**, 30.91s, including the new CRLF/byte-boundary tests. Diagnostic probe provisions, executes SELECT with two rows and cleans up in ~4s. No command/resource deadlines changed. Commit the framing fix and then run the full backend serially; keep the initial failures in the report.
- Stopped only the owned idle `dbcas-cont-qa` stack to avoid interference. Unrelated stacks and the original `dbcas-local` remain untouched. Removed two owned tmpfs containers from the interrupted test after receipt/label checks.
- Fresh remote clone exists at `_review/continuation-fresh-clone`, branch develop2 at `7e79072`, with **no .env** verified. Startup has not yet run. CI for `7e79072`: run **41655908179**, still pending when last checked.

## Latest gate state

- Framing fix committed/pushed as **`af2bce0`**. Final native backend: **1251/1251 pass**, 0 failed/skipped, 693.04s, one dependency warning (`_review/continuation-backend-final.log`). Lint/build/pip check passed again. Earlier failures are preserved, not counted as acceptance.
- Fresh clone fast-forwarded to `af2bce0`, still no `.env`; start/probe next, after final frontend change is pushed.
- One-line UX follow-up in `ExamPage.jsx`: header finish action uses `btnGhost` during an active question, prioritizing submit-current-answer. Full UI rerun: **344/344**, 39 files, 77.37s; build passed. No behavior/label/confirmation changed.
- Prepared `_review/continuation-fresh-probe.mjs`: four demo logins plus no-key AI→bank fallback, real SQL execution, rule evaluation, arithmetic and mobile bounds. Run only after isolated clone startup on ports 18680/18600/18625/11625, project `dbcas-cont-fresh`.
- CI application run `41658613899` is for `af2bce0`; the next push will supersede it. No real calls sent; prior-count clarification remains unanswered.

CI at `0df6bf9`: backend green, default browser 55/55 (25.8min), smoke 3/3 (5.2min); fake QA **9 failed / 6 passed / 18 not run**, three repeated failures each in two-tab, paused-provider and bank 0/1/3 scenarios. Logs include 20-second API response timeouts. Current metadata-only selection avoids the previous full-bank loading/validation path; current local 0/1/3 scenario passes. Retest full fake QA before closing.

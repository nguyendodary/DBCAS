# QA continuation — 2026-11-03

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

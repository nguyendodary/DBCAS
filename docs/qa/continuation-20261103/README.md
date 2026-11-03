# QA continuation: evidence and limitations

Scope: local `develop2`, starting at `f14bd6d`. Existing acceptance is in
[`final-status.md`](../../final-status.md); this report covers inherited work
finished after that commit. All screenshots use synthetic local accounts.

Final branch CI is authoritative for the final HEAD:
[![Local quality gate](https://github.com/nguyendodary/DBCAS/actions/workflows/dn-backend.yml/badge.svg?branch=develop2)](https://github.com/nguyendodary/DBCAS/actions?query=branch%3Adevelop2).
The local results below were measured; this documentation does not predeclare
the result of a workflow that is still running.

## Issues

| # | Flow / steps | Actual | Expected | Severity | Status / evidence |
| --- | --- | --- | --- | --- | --- |
| 30 | Learner: choose ER modeling, AI source, 5 questions; fail provider while bank has too few matching questions | Previous generation code silently invented trivial template MCQs | Use validated matching bank questions, or explain unavailability and allow retry with the same request ID | Medium | Fixed inherited change; API returns 503/`generation_unavailable`, no session created; browser retry recovers. [Failure](generation-unavailable.png), [recovered](generation-recovered.png). Commit recorded in handover |
| 31 | Capture recovery immediately after URL changes | First recovery screenshot showed only the loading skeleton | Evidence must show the recovered question | QA | Fixed browser assertion: verify response, same payload/request ID, no fallback and visible question before capture; targeted rerun 1/1 in 10.0s. [Before](recovery-skeleton-before.png), [after](generation-recovered.png) |
| 32 | New regression calls service directly, then HTTP with the same learner | Direct call's open transaction retained its advisory lock, blocking HTTP | End the direct transaction before testing the independent HTTP transaction | QA | Fixed fixture transaction; 2/2 configured/unconfigured variants pass in 1.99s. Interrupted diagnostic run is not counted as acceptance |
| 33 | Reconcile real-provider spending before continuation | 27 cached responses have the configured route, but no prior outbound request/retry ledger is available | Count every real request, including retries/timeouts; total strictly below 60 | Acceptance blocker | Open. User clarification requested; continuation sends 0 real requests. Cache rows are not a request counter |
| 34 | Windows SQL bridge receives a complete JSON request while its stdin writer remains open | Reader waits for EOF and does not execute the complete request | Execute a bounded complete frame without depending on EOF propagation | High | Pipe regression red before fix (1.61s); JSON-line framing fixes it. Protocol + real offline sandbox 10/10 pass in 30.91s; payload bound, CRLF, resource isolation and cleanup preserved |
| 35 | Initial native backend gate / concurrent Docker diagnostics | Docker exec/start timeout; bank import once rejected a SQL fixture | Stable final serial gate with unchanged deadlines/assertions | QA | Initial full gate: 1242 pass / 2 fail, 765.01s. Final serial gate: **1251/1251 pass**, 693.04s. Exact cause of the earlier Docker-start/fixture transient remains unconfirmed |
| 36 | During an active question, inspect the exam header and answer form | Finish-entire-practice and submit-current-answer buttons both use filled primary styling | Make the current answer the obvious next action | Low | Fixed `b15a28f`; confirmation/early finish stay available. [Before](generation-recovered.png), [after](fresh-answer-action.png) |

Commit mapping: **30–32 → `4188a8b`**; **33 → open, future ledger `7e79072`**;
**34 → `af2bce0`**; **35 → final serial evidence `b15a28f`**; **36 → `b15a28f`**.

The inherited browser failure (generic error instead of generation-specific text)
is preserved in `_review/continuation-inherited-browser-results.json`. A fresh
build with the inherited changes passed. The original failure's precise build/
runtime cause was not established; no extra product defect is claimed from it.

## Flows now verified

- Immediate: zero/one/three attempts, draft/reload, waiting state, per-question
  feedback, overall/trend, cache, history and arithmetic. [Zero](overall-0.png),
  [one](overall-1.png), [three](overall-3.png).
- Admin approval: all learner scores hidden before approval; cohort unchanged
  while pending; SQL SELECT runs, DELETE rejected; score edit requires a reason;
  audit persists; released cohort count increases by exactly one; learner updates
  automatically. [Review](admin-review.png), [released](approved-result.png).
- Five Admin screens, scoped hard AI generation, learner at 390px, bounded
  provider outage fallback, generation retry, stalled module recovery, double
  submit, two tabs, refresh while grading and genuinely expired authentication.
  [Mobile](mobile-evaluation.png).

The 11 browser scenarios used the deterministic HTTP provider: **11 passed,
0 failed/skipped/flaky, retries=0**, 336.65s. Screenshot synchronization was then
strengthened and the affected scenario passed again. These are not real-model
quality results.

## Independently checked arithmetic

| Evidence | Hand calculation | Displayed / asserted |
| --- | --- | --- |
| Bank attempts 1, 2, 3, each three questions | Each 1 / 11 × 100 = 9.0909…% | Each 9.09%; overall count 1/2/3, history length 1/2/3 |
| Three published bank attempts | (1 + 1 + 1) / (11 + 11 + 11) × 100 = 9.0909…% | 9.09% |
| Approved score after edit | 1.25 / 11 × 100 = 11.3636…% | 11.36%; approved banner and adjustment notice |
| Approved BENCH-SQL CLO | 0.25 / 6 × 100 = 4.1666…% | 4.17% |
| Approved Performance topic | 1 / 5 × 100 = 20% | 20.00% |
| Mobile generated practice | 3 / 3 × 100 = 100% | 100.00%; easy 2/2, hard 1/1 |
| Fresh no-key bank fallback | 1 / 11 × 100 = 9.0909…%; design CLO 1/6 × 100 = 16.6666…% | 9.09%; CLO 16.67%; SQL CLO 0/5 = 0% |

Totals above come from answer evidence, then are checked against history and UI.
The fake provider's generation templates are intentionally trivial fixtures;
their 100% is not evidence of educational quality or real difficulty calibration.

## Gate status

- Backend lint/build/pip check: passed. Final full backend on `af2bce0`:
  **1251/1251 pass**, 0 failed/skipped, 693.04s; one dependency deprecation warning.
  Practice API: 25/25; added HTTP assertions: 2/2 (the same configured/unconfigured
  test cases, not two additional cases).
- Frontend `npm ci`: 164 packages, audit 165; tests **344/344**, 39 files, 77.37s
  after the button styling follow-up (earlier run 143.63s);
  build passed; audit **0 vulnerabilities**, including 0 high/critical.
- Fresh remote clone (`b15a28f`) had no `.env` before a single `npm start`: **4
  healthy services**, init/executor exit 0; initial seed **0 exams / 24 questions /
  15 concepts / 2 CLOs / 4 accounts / 4 historical sessions**. Four demo logins and
  a new three-question practice with no-key generation/evaluation fallbacks pass;
  actual SQL executes, score 1/11 = 9.09%, 390px fits, 0 page errors.
  [Probe](fresh-probe.json), [answer action](fresh-answer-action.png),
  [mobile result](fresh-fallback-mobile.png), [system status](fresh-admin-system.png).
- Final HEAD CI runs **55 regression browser cases**, **3 smoke repeats**, and
  **11 HTTP-fake scenarios × 3**, all with retries=0, plus backend/frontend gates.
  Its outcome is linked above and must be checked before claiming completion.
  Starting HEAD CI was green at
  [41582152378](https://github.com/nguyendodary/DBCAS/actions/runs/41582152378).
- `.env` ignored/untracked; known-key and key-pattern scans of working diff,
  staged diff and all Git history found 0 occurrences before pushing handover.

The initial native backend gate and diagnostic failures remain recorded locally;
they are not accepted as a green run. The independent EOF regression is fixed,
but this alone does not prove the cause of every observed Docker CLI timeout.
Only the owned idle QA stack was stopped before serial verification; no timeout,
resource limit, expected count or assertion was loosened.

## Real provider

Local credentials exist, host `openrouter.ai`, route `openrouter/free`; no key is
printed or stored here. Continuation usage: **0 calls / 0 tokens / no measured
latency**. Prior total usage, retries and failure rate are unknown. The 27 cache
rows (26 gap explanations, 1 generation) establish stored responses only.

Real three-run acceptance and real question/evaluation quality remain unverified
until the previous request count can be reconciled. Continue independent local
gates without spending against an unknown total.

Latest fallback preview: http://localhost:18680. Original main checkout and
18080 stack were preserved. Raw test traces/auth state remain local under
ignored `_review/`; `.env` and credentials are not committed.

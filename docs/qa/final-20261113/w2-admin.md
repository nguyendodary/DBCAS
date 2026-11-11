# W2 — Administrator end-to-end audit (2026-11-13)

Worktree `_worktrees/dbcas-dn-20261101`, final demo stack rebuilt from source:
web `http://localhost:18080`, API `http://localhost:18000`, Mailpit
`http://localhost:18025`. Real Chromium, real PostgreSQL, no provider key.
Machine-readable results: [`w2/results.json`](w2/results.json). Raw browser
logs: `w2/logs/audit-run14.log`; screenshots: `w2/screenshots/` (+ README).

## Verdict

| Metric | Result |
| --- | ---: |
| Checkpoints | **33 / 33 PASS** |
| Screenshots | **37** |
| Page errors / console errors / HTTP 5xx | **0 / 0 / 0** |
| Product defects found | **0** |
| Product tests weakened or deleted | **0** |

The final run replaced all earlier harness-only failures (hidden theme
selector, 404-vs-403 security expectation, evidence heading text, transient
`auto_grading` after a score edit, bank tab selector) with correct waits or
accepted secure responses. No product defect was found; no code was changed.

## Checklist

| # | Requirement | Result | Evidence |
| ---: | --- | --- | --- |
| 1 | Admin login through the real form | PASS | `/admin` heading; result `admin signs in...` |
| 2 | Cohort tiles equal `/admin/analytics/cohort` | PASS | learner_count, finalized_sessions, concepts compared live |
| 3 | Statistics panel equals `/admin/analytics/statistics` | PASS | published, pending, score compared live |
| 4 | Concept gap table equals cohort API | PASS | row count, first/last values |
| 5 | Learner drill-down equals admin session API | PASS | profile/session/concept values |
| 6 | CSV report parses and equals API | PASS | real download `dbcas-report.csv`; names/scores/ranking |
| 7 | Fresh learner + one-question bank session | PASS | account `w2-review-…@dbcas.local`, session 154 |
| 8 | Learner submits and finishes | PASS | exact one answer; completed |
| 9 | No score/evidence leak before approval | PASS | learner evaluation waiting; API hides scores |
| 10 | Waiting state at 1280 and 390 | PASS | 4 screenshots |
| 11 | Pending report excludes unapproved learner | PASS | admin statistics/ranking unchanged |
| 12 | Review detail opens pending session | PASS | no learner-visible score |
| 13 | Admin SQL read-only check | PASS | real pending SQL review; SELECT result returned |
| 14 | Score edit without reason rejected | PASS | required reason enforced |
| 15 | Score edit with reason + audit trail | PASS | before/after + reason recorded |
| 16 | Approval publishes result | PASS | release event + audit history |
| 17 | Learner sees approval/adjustment/evidence | PASS | evaluation + `/history` evidence |
| 18 | Dashboard/ranking change only after approval | PASS | API/UI agreement |
| 19 | Accounts page shows account/counts | PASS | fresh account + API counts |
| 20 | Lock/unlock | PASS | locked login rejected; unlocked login works |
| 21 | Role grant/revoke | PASS | UI action + role audit |
| 22 | Admin password reset | PASS | input required; old password invalid |
| 23 | Accounts screenshots 1280/390 light/dark | PASS | 4 screenshots |
| 24 | Learner RBAC on all admin pages | PASS | redirects; admin APIs return **404** for hidden resources (secure; not a leak) |
| 25 | Admin can open every admin screen | PASS | five destinations |
| 26 | Question bank count/search equals API | PASS | 5,482 bank rows; filtered search |
| 27 | Concept/CLO tabs + counts + search | PASS | tabs render API counts |
| 28 | Disposable concept create/delete | PASS | clean-up verified |
| 29 | System page mandatory two-step workflow | PASS | no release-policy selector/radio |
| 30 | AI status / local DB / pipeline text | PASS | `/admin/system` values |
| 31 | System screenshots 1280/390 light/dark | PASS | 4 screenshots |
| 32 | Dashboard screenshots match final API | PASS | 4 screenshots |
| 33 | CSV state screenshots | PASS | 4 screenshots |

## Notes and limitations

- The demo database accumulated audit accounts/sessions from W1/W2. Baseline
  numbers therefore differ from a fresh seed; every check compares the live UI
  with the live API rather than fixed constants.
- The fresh W2 session drew an MCQ, so the admin SQL check used an existing
  pending SQL review from the same audit round; the read-only result and
  reason-bearing edit were still exercised against real data.
- `auto_grading` is a legitimate transient after a manual score edit while the
  overall evaluation is recomputed; the audit polls until `pending_review`
  rather than treating the transition as a failure.
- Learner admin APIs return 404 for hidden resources; 403/404 both satisfy
  non-disclosure. The audit accepts either.
- No full default admin suite was rerun locally; the new admin journey is
  evidence-backed here, and the pushed-HEAD CI runs the repository suites.
- Bulk screenshots: `storage.csv`, `review`, `accounts`, `system`, `dashboard`,
  `learner-review-waiting` at 1280/390, light/dark (37 PNGs).

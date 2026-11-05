# Active handover - 2026-11-04

## Recovery checkpoint - 2026-11-05

Recovered existing worktree on `develop2` at pushed `c79e0c6`. Fetch succeeded;
checkout confirmed. Rebase pull refused because the prior agent's six test files
are uncommitted; preserve/review them, commit the verified item, then rebase pull.
No reset/clean or changes to other worktrees. No `brief-*.md` files are present.

| Part | Status | Evidence / next action |
| --- | --- | --- |
| PostgreSQL bank audit and new questions | DONE+verified | `f2351d1`, bank 73/73; 5482 questions, 6988 SQL executions; `bank-validation.md` |
| Exact-count guarantee | DONE+verified | `0c16327`, `test_exact_count_exhaustive_concept_difficulty_count_source_matrix`: 2268700/2268700 |
| Sprint 1-4 engineering checks | DONE+verified | Per-task evidence in `task-audit.md`; later final gate is separate |
| Sprint 5 load and scheduling | DONE+verified | `c79e0c6`, native13/13, API65/65, `practice-load-results.json`: 8x20,259HTTP,42.186s |
| Full browser E2E and final regression | IN PROGRESS | Prior supplementary application run failed obsolete expectations; reviewed fixture repairs pending. Default55, fake3 repeats, live2 repeats and smoke3 remain |
| Stability gate and clean-clone final check | IN PROGRESS | Prior full backend r2:1382pass/1fail,1298.97s; pre-SQL OperationalError in whole-bank execution. Transport regressions written but implementation pending |

Per-Jira status checkpoint (the named tests, screenshots and detailed evidence
for every row are retained in `task-audit.md`; Jira server status is Unknown).

| Jira task(s) | Status | Evidence |
| --- | --- | --- |
| 1.3 | DONE+verified | response-contract 156/156, `86166ab` |
| 1.4 | DONE+verified | seed/migration11/11, `0df6bf9` |
| 1.5 | DONE+verified | fresh browser four logins, launcher7/7; final clone refresh due |
| 1.6 | DONE+verified | fake13/13, exact-count107/107 |
| 1.7 | DONE+verified | admin authoring Chromium journey |
| 1.8 | DONE+verified | strict validator41/41, `b3bb04e` |
| 2.1 | DONE+verified | auth/RBAC/refresh within158/158 |
| 2.2 | DONE+verified | exact-count matrix2268700/2268700 |
| 2.3 | DONE+verified | grading/draft lifecycle within158/158 |
| 2.4 | DONE+verified | AuthPages; fresh browser four logins |
| 2.5 | DONE+verified | ExamPersistence; fake13/13 |
| 2.6 | DONE+verified | admin questions/curriculum within158/158 |
| 2.7 | DONE+verified | PostgreSQL semantics14; bank change ledger |
| 2.8 | DONE+verified | 720 coverage cells; source classification validator |
| 2.9 | DONE+verified | API107/107, HTTP provider4/4, count matrix |
| 2.10 | DONE+verified | fake13/13 and baseline Chromium55/55 |
| 3.1 | DONE+verified | sandbox native/protocol repeats10/10; final serial gate due |
| 3.2 | DONE+verified | real typed wire/comparison tests |
| 3.3 | DONE+verified | provider83/83, live full run5 1/1 |
| 3.4 | DONE+verified | both release flows; contracts156/156 |
| 3.5 | DONE+verified | UI347/347, fake13/13, live run5 |
| 3.6 | DONE+verified | bank73/73, all1747SQL x4; final transport retest due |
| 3.7 | DONE+verified | validator/localization162/162 |
| 3.8 | DONE+verified | API116/116, contracts156/156 |
| 3.9 | DONE+verified | Sprint3 API/UI/browser milestone in task audit |
| 3.18 | DONE+verified | generation failure modes; API107/107 and provider4/4 |
| 4.1 | DONE+verified | competency/statistics150/150 |
| 4.2 | DONE+verified | frozen published evidence/privacy regressions |
| 4.3 | DONE+verified | CumulativeRace; numerical .25/1 and .25/17 cross-check |
| 4.4 | DONE+verified | rank privacy/settings/language/theme tests |
| 4.5 | DONE+verified | API158/158, statistics150/150, admin browser |
| 4.6 | DONE+verified | real ranking export, formula escaping, frozen policy |
| 4.7 | DONE+verified | distinct worked grids; bank73/73, `f2351d1` |
| 4.8 | DONE+verified | six red-to-green publication regressions, `cd220da` |
| 4.9 | DONE+verified | arithmetic DB/API/learner/admin numerical screenshots |
| 4.10 | DONE+verified | desktop/390px fake13/13 and live run5 |
| 4.12 | DONE+verified | lint/format0, UI347/347, audited deps; final CI due |
| 5.1 | DONE+verified | guidance/competency150/150 and live run5 |
| 5.2 | IN PROGRESS | consecutive full fake/live scenarios pending |
| 5.3 | DONE+verified | LearnerPages, fake13/13 and mobile-setup.png |
| 5.4 | DONE+verified | authoring UI, fake13/13, targeted admin journey |
| 5.5 | DONE+verified | source bank73/73, all5482 validated |
| 5.6 | IN PROGRESS | count failure modes107/107 and matrix already verified; final browser errors pending |
| 5.7 | DONE+verified | `c79e0c6`, 8x20 controlled load, SQLpeak4/providerpeak2 |
| 5.8 | IN PROGRESS | full final backend/browser/CI gate pending |

Resume sequence: fix the already-red bounded pre-SQL transport regressions;
verify and commit/push that item; finish existing supplementary browser fixture
repairs and default browser; final serial backend; fake3 and live2; smoke3,
fresh-clone fast-forward and pushed-HEAD CI. Reuse unchanged bank/count evidence.
Ledger `_review/real-provider-20261104/ledger.json` is present and explicit:
40/80 requests used,40 remain. No live requests during recovery. Key/model stay
private in child environments; real tests auto-skip without a key.

2026-11-05 transport item complete: the prior red4/pass10 identified additional
pre-SQL reset/closed/startup connection failures outside the timeout-only
reconnect. The existing single reconnect now classifies those transient failures;
authentication/configuration/unknown failures still never retry. Two further
regressions prove transport exhaustion stops at two attempts and small budgets
remain single-attempt. Connection/native/protocol **27/27,38.52s**, lint/build
pass; `_review/audit-20261104/transport-native-final.{log,xml}`. An initial command
used a nonexistent protocol filename and ran no tests; corrected before this gate.
Full final serial backend and browser gates remain open; live meter unchanged40/80.

- Branch `develop2`; latest pushed `27377ff`. Independent dirty main checkout and original local stacks untouched. Publication/editor, frontend quality and fixture/inventory milestones pushed.
- Untouched baseline: backend lint/build OK, **1258/1258, 757.49s**; frontend npm ci/build OK, **344/344, 109.02s**; Chromium **55/55, 1774.01s**, zero failures/skips/flaky/retries; launcher **7/7**. Starting CI green.
- Bank **5482 = 2006 MCQ / 1747 SQL / 1729 essay**, 80 concepts, 720 cells at least7. Original442 audited,121 corrected; all5040 native definitions reviewed/revised. Complete5161-ID change ledger and185 preserved definitions; other native before versions reproducible from `9e24edd`. Official PostgreSQL18.6 references; sandboxPG17.
- Latest bank/SQL/seed/history **73/73, 411.91s**: 1747SQL x2fixtures x2executions = **6988**, no empty/mismatching/nondeterministic outputs. Seven distinct worked grids in each240 concept/difficulty scopes. Authoring manifest **11546 executions / 547.361s**.
- Central count1/default5/max20, deterministic balance/disclosed widening, two bounded AI attempts, validated bank/template recovery. Current matrix **2268700/2268700, 151.352s**. Count API/provider/statistics/contracts **107/107,67.19s**, all required malformed/failure modes covered.
- Sprint1/2: auth/RBAC/refresh/migration/init/MCQ/drafts/curriculum API **158/158,123.29s**; contracts **156/156,110.51s** plus schema probe **3/3,.97s**. Fixed21 missing response bodies,302 and public-auth errors;93operations/82paths.
- Sprint3: SQL/content/pipeline group **257pass/2 Docker CLI failures,540.20s** during concurrent startup; isolated sandbox/protocol **10/10,31.44s**. Exact daemon cause unconfirmed; final serial resource gate due. Provider/meter **83/83,26.76s**, later recovery/meter/provider **59/59,24.48s**. Backend CI at9e24edd green.
- Fresh-key meter **40/80 actual requests;40remaining**. Read `_review/real-provider-20261104/ledger.json` before live work. Older ledger preserved separately. Key/model loaded privately into child environments; neither.env modified. Live project `dbcas-real-qa-20261104` currently provider-disabled. Reserve remaining budget for two final full live runs (~16calls each).
- Live run5 full scenario **1/1,126.438s**, zero failures/skips/flaky/retries: validated mixed generation,0/1/3 overall,both release flows,SQL/reason/approval,caching,390px. Generation-only run3 **1/1,8.632s**. Failed real runs1/2/4 retained; routing seed/mandatory reasoning fixed, strict validation retained. Final usage statistics must come from ledger.
- Manual numerical proof: PGX-FUNC **.25/1=25.00%**, cumulative **.25/17=1.47%**; DB,learner/admin APIs and both UI screens agree,desktop/390px,no page errors (`numerical-*`). Current competency/statistics/guidance/history-security/publication **150/150,84.96s**.
- Publication: six initial red cases now pass; common validator and double SQL execution before publishing. Citation editor preserves metadata/explicit clear. Affected API **116/116,50.72s**; UI **347/347,57.79s**,build781ms; lint/build/OpenAPI/inventory pass. Targeted browser3pass/1fixture failure, concept-authoring retest **1/1,27.4s** after honoring delivery/evaluation lifecycle. Failed fixture probes retained.
- Fake browser latest full **13/13,369.919s**, no failures/skips/flaky/retries. Three final consecutive fake runs,default55,smoke3 due. Previous CI default52/55 exposed obsolete authoring/scope/shortfall fixtures; targeted repairs verified, final pushed-HEAD CI must be green.
- Fresh remote clone at0c16327 initially without.env: npm ci/root+UI/npm start succeeded; full bank,four demo logins/history,SQL/no-key AI fallback,390px/no page errors. Owned fresh project stopped,history volumes retained. Recheck final code after fast-forward.
- Quality: frontend npm ci exit0 (9s), lint0/format0, **347/347,53.44s**, build619ms. Formatter review:111 equivalent syntax trees,14 reviewed unused-binding cleanups,0 unexpected changes. ESLint10 handles JSX directly; patched minimatch11.0.4 pin avoids a newly found glob DoS advisory. No tests removed.
- Security: installed Python38 packages/0 advisories after pip26.3 upgrade; pip check OK; frontend0 vulnerabilities. Root2low/0high-critical are isolated Mermaid tooling/KaTeX; upgrading needs renderer compatibility review. Docker/CI pin pip26.3; CI adds installed-dependency audit and frontend lint/format.
- Full regression after publication: **1366pass/7fail,1320.82s**. Six fixtures lacked required content or tried to republish archived incomplete rows; one shared-sandbox connection timed out before SQL. Fixture repair retains all assertions and archived definitions; current affected group **104/104,60.07s**, including the separate bounded reconnect regression. Route inventory updated for formatting-only hash/line changes (23UI/93API routes unchanged).
- Reconnect regression red3/pass3 before repair; current code passes timeout recovery, exhaustion within original5s budget, small budget, authentication no-retry and no SQL replay. Affected104/104 includes6 new connection regressions. Patched offline image pip26.3: native sandbox/protocol **10/10,73.66s**, actual36 installed packages/0 advisories. No execution/resource limit raised.
- Sprint4 milestone verified using current API150/150, UI347/347, targeted admin authoring, fake13/13, real full run5 and independent numerical proof; see task rows. Final full CI/browser gate remains open. Sprint5 controlled load and repeated regression next.
- Sandbox fix `4e6f9d5` pushed; native/protocol repeats10/10 each (73.66s incl rebuild,30.61s,30.75s),0 failures/retries. CI backend green at4e6f9d5; frontend54/55, remaining supervisor authoring fixture lacks reviewed refs/explanation.
- New load-discovered fixes ready: SQL capacity admission before durable claim; evaluation worker skips old ungradable SQL using frozen types. Red2/2; native/admission/protocol13/13 (39.91s), affected API/provider/statistics65/65 (51.89s). No resource/execution limit or provider retry budget increased.
- Controlled load final:8learners x20questions,5563 versioned bank rows/80concepts,259HTTP/42.186s,8exact/duplicate-safe published attempts,8owned-data denials,0unexpected errors. Fake provider10calls/peak2;SQLpeak4;timeout3025ms,cells/rows rejected. Full published-row hashes preserved:60sessions/583attempts. Full timings in `practice-load-results.json`; failed exploratory runs retained. New-key budget40/80 unchanged.
- Next: push scheduling/load milestone; finish browser fixture recovery (including supplementary application-entrypoint scenarios that still refer to retired exams), then full backend/default browser, three fake repeats, two live repeats, final fresh clone and pushed-HEAD CI. Gate remains open.

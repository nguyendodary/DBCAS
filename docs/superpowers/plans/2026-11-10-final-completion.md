# Final completion implementation plan

> Execution: the owner explicitly requested one sole-writer run. Implement and
> review each task in this session; do not delegate or request plan approval.

**Goal:** finish the remaining recovery, visual verification, documentation and
demo gates on `develop2`, preserving verified code and evidence.

**Architecture:** retain the existing FastAPI/PostgreSQL/React architecture and
mandatory administrator release contract unless the owner corrects it. Use
the green pushed-source CI for unchanged long suites and isolated local
projects for reset/start checks, preserving the existing healthy demo stack.

**Tech stack:** Python/FastAPI, PostgreSQL, React/Vite, Playwright, Docker
Compose, existing Word/diagram verification scripts.

**Spec:** the owner's “FINISH EVERYTHING” request; `docs/qa/handover.md`;
`docs/qa/final-ui/light-theme-spec.md`.

## Global constraints

- Branch only `develop2`; one writer; no force push or destructive Git recovery.
- Preserve valid changes, the main-worktree stash and the healthy local stack.
- Commit and push each finished item; review staged diff and team identity.
- Never weaken assertions, retries or timeouts to obtain passing tests.
- At most two real LLM calls total; read the ledger first; never expose a key.
- Preserve existing Word formatting, names, dates and approved diagrams.

## Review focus

- Interrupted sessions can leave live services without an active writer: check
  session outcome, process ancestry and file state before edits.
- Later CSS can invalidate earlier screenshots: refresh both themes and widths,
  check opaque dark fields, media visibility, overflow and Vietnamese wrapping.
- A pending review must not expose scores: retain the existing browser and
  backend assertions that exercise pending and approved results.
- A successful fallback does not prove real-model quality: report the rejected
  key and retain the request cap without inventing successful output.
- Resetting the prepared demo would erase evidence: run reset/start in a fresh
  isolated project and verify readiness plus both requested demo logins.

## Task 1: Recovery and W5 evidence

**Files:** `docs/qa/handover.md`, `docs/qa/final-ui/screenshots.md`.
**Interfaces:** consumes current Git/process state and CI 42825915679; produces
a clean checkpoint with the exact source hash and test numbers.

- [x] Confirm the old project session is interrupted and no other session runs.
- [x] Fetch/check out `develop2`; inspect stash, history, pending diff and identity.
- [x] Run fsck and recent-file byte/JSON/YAML/Python parsing checks.
- [x] Read the pushed-source CI logs; record 1455 backend, 351 unit, 55 browser,
  39 fake-provider and 3 clean-checkout smoke passes.
- [x] Commit/push the valid wording and recovery checkpoint; pull with rebase.

## Task 2: W4 visual evidence and quick W1–W3 checks

**Files:** `docs/qa/final-ui/{light,dark}/`, `screenshots.md`, `index.md`,
`docs/qa/handover.md`; change UI source/tests only for a reproduced defect.
**Interfaces:** consumes current seeded local API and UI; produces final-theme
captures, measured overflow/font/chart results and written visual findings.

- [x] Run `npm run ui:contrast` once and save the actual counts (186/186; repeat only after CSS fixes).
- [x] Capture every learner/admin/auth screen at 1280/390 in both themes (102 images).
- [x] View each capture and describe actual layout, text, chart and field state.
- [x] Check the SQL workspace at 390/768/1280/1920, Vietnamese text and fonts.
- [x] If a defect appears, reproduce it with a meaningful regression test,
  implement the smallest fix, and run only the affected checks.
- [x] Update the handover, commit and push W4 evidence/fixes.

## Task 3: W6–W8 and isolated demo

**Files:** `docs/qa/{ai-pipeline-audit,cleanup-report,handover,task-audit}.md`,
`docs/academic/*ver1.2.docx` only if a measured error exists, `docs/deliverables/`,
`README.md`, `docs/{README,final-status}.md`, `docs/demo/demo-script.md`.
**Interfaces:** consumes existing request ledger, current schema/Compose/OpenAPI
and routes; produces an honest final audit and reproducible demo evidence.

- [ ] Reconcile the real-call ledger and unchanged purity/fallback evidence;
  use at most one remaining request only if a valid final live check is possible.
- [ ] Recheck cleanup references; preserve every retained item with a live use.
- [ ] Audit Word text/structure against the final project; open without repair;
  run `npm run docs:check` and `npm run docs:verify-word` once.
- [ ] For an architecture delta, rebuild affected diagrams and obtain owner
  approval before Word insertion; otherwise preserve diagrams.
- [ ] Fresh clone without `.env`; isolated `npm run reset` then `npm start`;
  readiness and learner/admin logins; preserve the healthy original stack.
- [ ] Update current docs and handover; commit/push each completed item.

## Task 4: Final verification and report

**Files:** current status/evidence documents only.
**Interfaces:** consumes all gate outputs and pushed HEAD; produces the owner's
requested recovery table, screenshot links, gate numbers and limitations.

- [ ] Confirm clean Git state and remote agreement; inspect new commit log.
- [ ] Confirm green CI on the final pushed HEAD; reuse unchanged-code gate
  evidence, explicitly identifying its source commit.
- [ ] Report unverified live quality and human-authored academic items honestly.

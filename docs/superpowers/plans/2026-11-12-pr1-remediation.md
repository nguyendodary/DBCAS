# PR #1 Remediation Implementation Plan

> Execution: implement in this session, one task/commit at a time; stop for independent re-review. The owner explicitly authorized execution, branch synchronization and pushes. Do not merge.

**Goal:** Address findings F1–F10 without rewriting shared history or disrupting the existing demo stack.

**Architecture:** Keep the deployed application and migration contract intact. Add a shared demo-credential policy, a dependency-free tree/index secret scanner, narrowly scoped artifact cleanup and migration regression coverage. Mirror integration commits onto develop2 with cherry-pick.

**Tech Stack:** Python/FastAPI/PostgreSQL 17, React/Vite, Node 24, GitHub Actions.

**Spec:** Owner's remediation request; `docs/qa/pr1-review-20261114.md` (independent uncommitted review).

## Global constraints

- Author changes on integration/develop2-to-main-20261114; cherry-pick onto develop2; push after each small commit.
- Never modify main/master/develop, force-push, rewrite history or merge PR #1.
- Never output credential/JWT values or resolved Compose environments. Rotation writes only the ignored .env.
- Leave dbcas-local containers running. Distinguish configuration-key rotation from activation in already running processes.
- Preserve applied migration SQL, legacy rows, curated referenced screenshots and academic verification fixtures.
- Use the existing team identity, Conventional Commits and attribution hook; inspect staged changes before every commit.

## Review focus

- Archive members and staged blobs must be scanned, not just working-tree text; an unapproved fixture cannot bypass scanning.
- Any active or disabled account with a public demo credential must prevent staging/production startup; development retains demo behavior.
- A saved .env key is not a live-container restart; report expiry/revocation/signature state truthfully.
- Migration 019 changes only published assessment statuses; drafts/closed rows and historical sessions/attempts survive repeated execution.
- Both branches must end with identical trees; CI evidence must identify the exact final integration head.

## Tasks

### 1. Exposure response and artifact cleanup (F1/F4)

- [ ] Decode only iat/exp into anonymous T01–T12 rows; inspect live signature/refresh-record status without outputting tokens.
- [ ] Replace JWT_SECRET in ignored .env with a fresh cryptographic value; confirm captured signatures reject the new key. Do not restart services.
- [ ] Inventory the 123 raw files, 62 logs and PPTX; find documentation/CI/npm references, preserve curated linked images and fix links.
- [ ] git rm raw/log files; move referenced slides under docs/academic/support; add narrow output/archive ignore rules and a redacted retention note.
- [ ] Commit/push; preserve original review as untracked historical evidence.

### 2. Secret scanning and CI coverage (F1/F3)

- [ ] Add `scripts/scan_secrets.py` with whole-tree and --staged modes, ZIP member scanning and paths-only failures.
- [ ] Add exact path/rule/value-digest allowlisting only for provably fake fixtures; test detection, archive coverage and allowlist boundaries.
- [ ] Wire `npm run secrets:scan`, a pre-commit hook and an Actions secrets job; keep all existing jobs and add main branch targets.
- [ ] Commit/push; apply main protection only after read-only admin confirmation, requiring all jobs plus one review, no force-push.

### 3. Deployment guard (F2)

- [ ] Centralize known public demo credentials; use the policy in Settings, account startup validation and initial-admin bootstrap.
- [ ] Add parameterized staging/production and development tests, including demo-database promotion, disabled accounts and unsafe config fields.
- [ ] Run backend lint and touched auth/config/initialization/bootstrap tests; commit/push.

### 4. Migration rollout and remaining hygiene (F5–F10)

- [ ] Add a seeded pre-019 PostgreSQL migration regression: status-only changes, complete row fingerprints, second application empty and direct SQL rerun unchanged.
- [ ] Document withdrawal of published prebuilt exams, backups using pg_dump --format=custom and code-revert/data-restore distinction.
- [ ] Make README suitable for an ordinary main clone; restore the three lost main spacing changes.
- [ ] Remove literal database-credential fallbacks and update the vulnerable documentation dependency without weakening figure checks.
- [ ] Run touched backend checks, frontend tests/build/lint, docs:check, docs:verify-word and env:check; inspect generated changes; commit/push.

### 5. Synchronization and final evidence

- [ ] Record remediation evidence and recommended protection settings in docs/qa; update PR description, preserving existing context.
- [ ] Cherry-pick each author commit onto develop2 in order and push each; return to integration.
- [ ] Run the complete-tree secret gate with zero findings and wait for all unchanged CI jobs on the final integration head.
- [ ] Confirm MERGEABLE, identical remote trees, unchanged main, running demo health and no secrets staged/tracked.
- [ ] Report commits, exact removed bytes/counts, anonymous claim table, rotation activation limits, real gate numbers/run URL and final SHA; stop.

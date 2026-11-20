# 07 — UNKNOWNs Requiring Owner Confirmation

Every item below is marked **UNKNOWN — owner must confirm**. None was inferred
from production access; no production system or real student data was used in
this audit.

## Product and grading

| ID | Item | Why it is unknown | Decision needed |
| --- | --- | --- | --- |
| U1 | Are DDL/DML exercises actually required for grading, or only for the editor "Run" button? | The repository cannot express a product requirement; current questions all use result-based `SELECT` grading. | If editor-only, `state`/`script` grading can be deferred. |
| U2 | What grading semantics should a writable exercise use: final result, final state, or per-statement command tags? | `sql_test_dataset` has only `setup_sql` and `expected_result` (`db/schema.sql:165-171`). | Choose default `result` vs `state`; decide whether `script` is worth implementing. |
| U3 | Should a learner's script be allowed to replace or alter fixture tables, or only write to separate output tables? | Affects the grading-integrity checks in `04-target-design.md` §7.1. | Define protected objects and whether catalog verification is required. |
| U4 | Are high-stakes assessments allowed to use writable questions? | Changes the acceptable risk and whether manual review is required. | Approve/reject writable questions for graded exams. |
| U5 | Which DDL/DML statements must be supported in v1? | The policy matrix is a proposal, not a curriculum decision. | Confirm at minimum `CREATE TABLE`, `INSERT`, `UPDATE`, `DELETE`, limited `ALTER`; decide on views/indexes/sequences. |

## Deployment and operations

| ID | Item | Why it is unknown | Decision needed |
| --- | --- | --- | --- |
| U6 | Can staging/production provide a Docker socket, sidecar, or equivalent for ephemeral containers? | `docker-compose.release.yml:42-56` has no socket mount; DN/local do (`docker-compose.dn.yml:51`, `docker-compose.local.yml:84`). | Choose the production execution substrate before Phase 2. |
| U7 | What is the actual production `SANDBOX_MODE` (`shared` or `ephemeral`)? | No production config was accessed; config allows both and has no guard (`backend/app/config.py:196-230`). | Confirm current value and whether shared mode is in use. |
| U8 | Are app DB and sandbox DB on distinct PostgreSQL servers in production? | The guard at `config.py:220-221` enforces it, but production values were not inspected. | Confirm; the writable design assumes distinct servers. |
| U9 | Production DB size, question count, and peak concurrent SQL runs. | Local synthetic counts are 5,560 questions / 880 attempts (`02-measurements.md` §11), not production. | Capacity-plan `sandbox_busy` thresholds and rate limits. |
| U10 | Is the SQLite/Docker socket group and UID mapping available for the ephemeral runner in production? | Local/DN use `group_add` with a local GID; release does not. | Confirm UID/GID and daemon access policy. |

## Security and policy

| ID | Item | Why it is unknown | Decision needed |
| --- | --- | --- | --- |
| U11 | Is a cluster-wide `learner_rw` role acceptable in shared dev mode, or must development also use ephemeral? | Shared mode has a larger blast radius even in development. | Confirm the development-only flag policy. |
| U12 | Should `pg_*` helper functions (`pg_typeof`, `pg_size_pretty`, etc.) be selectively allowed? | Current deny-list blocks the whole prefix (`sql_validator.py:98-109`). | Decide trade-off between compatibility and information leakage. |
| U13 | Are `random()`, `now()`, and `current_timestamp` acceptable in graded answers? | They are non-deterministic and can make result comparison flaky. | Decide whether to block them in grading mode. |
| U14 | What SQL text retention is allowed in logs/audit? | The design proposes storing a hash, not SQL text (`04-target-design.md` §10). | Privacy owner must approve or reject text retention. |
| U15 | Is 512 MB / 256 PID / 60 s acceptable for writable containers? | Local ephemeral measurements used 256 MB / 128 PID / 45 s (`02-measurements.md` §4). | Ops must approve limits after the Phase 2 benchmark. |
| U16 | Does the existing sandbox volume have leftover `ds_*` schemas or widened `public` grants? | Shared-mode `cleanup_datasets()` is not wired to startup (`01-current-state.md` G7). | Inspect before enabling shared writable mode; ephemeral avoids the issue. |

## Verification and evidence

| ID | Item | Why it is unknown | Decision needed |
| --- | --- | --- | --- |
| U17 | Production first-load and query latency. | Only local measurements exist (`02-measurements.md`). | Do not treat local numbers as SLAs; re-measure in staging. |
| U18 | Which CI checks are required for the eventual code PRs. | `dn-backend.yml:2-3` documents required checks on `main`; this docs-only PR skips most jobs by design. | Confirm branch-protection rules before merging implementation PRs. |
| U19 | Whether the 3× QA/smoke repeats in CI are deliberate flake detection. | `.github/workflows/dn-backend.yml:208-267` shows three QA legs and three smoke legs; only `qa-1` has a different load. | Owner must confirm before reducing the matrix (`05-bloat-candidates.md` #3). |
| U20 | Whether the redundant shared `sandbox` service in DN Compose can be removed. | Ephemeral mode does not use it, but removing it changes `depends_on` and readiness. | Compose owner must approve; do not bundle with the sandbox rollout. |

## Explicitly not claimed

- No statement in this document set asserts a production fact.
- No statement asserts that writable SQL is currently enabled or approved.
- No statement asserts that local measurements are representative of
  production load.
- No claim is made that `docs/pending-readiness-edits` or `docs/qa/**` were
  reviewed or modified; both were left untouched.

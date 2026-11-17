# PR 3A -- Authoritative Database Foundation Specification

## 1. Baseline and scope

- Target baseline: `origin/develop2` at
  `7176d588f11fea13945708cbdcb8cbe1a1bd9b81`.
- Implementation branch: `feat/pr3a-db-foundation`.
- Migration owned by PR 3A: `026_pr3a_database_foundation.sql`.
- Later migrations remain owned by later PRs:
  - 027: review request lifecycle, draft revisions, confirmation.
  - 028: reports, corrections, regrades.
  - 029: v2 review link and publication enablement.
- The eight approved product-owner decisions are unchanged.

This document consolidates the original architecture report, Addenda 1-3, and
the Final Technical Readiness Gate. Where those documents conflict, this file is
authoritative for PR 3A.

## 2. Contradictions resolved

1. **v2 scope regex.** The only permitted expression is
   `^v2:[1-9][0-9]*$`. The earlier `LIKE 'v2:%'` form and the malformed
   `^v2:1-9*$` form are removed. Migration 026 uses the exact regex in the
   `scope_key` check and in the `run_mode` check.
2. **Mutable status on immutable versions.** `session_result_version` contains
   only immutable result evidence. Mutable state lives in
   `session_result_publication`, which has its own `session_id` and composite
   FK to `(session_id, result_version_id)`.
3. **AI uniqueness.** Every AI run identity and active-run rule includes
   `session_id`: `UNIQUE (session_id, scope_key, stage, execution_run_no)` and
   a partial unique index on `(session_id, scope_key, stage)` for active states.
4. **AI ordering.** AI2 cannot be inserted or set to `PROCESSING` unless an
   immutable `ai_stage_validation` row proves that the same-session,
   same-scope AI1 run is `COMPLETED`, `VALID`, and hash-consistent.
5. **Result completeness.** Every version must have exactly one score row per
   required attempt and exactly one criterion row per required essay criterion.
   Counts and totals alone are insufficient; frozen plan identity is compared
   by exact `(session_id, seq_no, question_id)` tuples in both directions.
6. **Attempt freeze.** Only structural attempt changes are frozen after a
   result version exists. Draft, score, submission, and other non-structural
   updates remain allowed, and legacy sessions without a result version are
   unaffected.
7. **Deferred validation.** Totals and completeness are implemented as complete
   PostgreSQL functions with deferred constraint triggers. No placeholder
   comments remain.
8. **DDL validity.** All partial uniqueness uses `CREATE UNIQUE INDEX`; all
   composite FKs reference declared UNIQUE keys; creation order avoids forward
   references.

## 3. Migration 026 implementation summary

### Tables created

- `question_rubric_profile`, `question_rubric_criterion`,
  `attempt_rubric_criterion`
- `session_result_version`, `session_result_version_score`,
  `session_result_criterion_score`
- `session_result_publication`, `session_result_analysis`
- `ai_stage_run`, `ai_stage_validation`, `ai_stage_attempt`
- `ai_prompt_record`, `ai_prompt_content`
- `retention_purge_audit`, `prompt_access_audit`

### Tables altered

- `attempt`: `UNIQUE (session_id, attempt_id)`
- `assessment_session`: `review_policy`, `current_result_version_id`, composite
  deferred FK to the result version
- `session_start_request`: `request_hash`
- `llm_cache`: `expires_at`, backfill, `NOT NULL`, index

### Trigger categories

- Immutable evidence triggers on result versions, scores, criteria, rubric
  snapshots, AI validation, analysis, and audit tables.
- Rubric profile status transition: `active -> retired` only.
- Narrow structural attempt freeze after result-version creation.
- AI2 ordering validation against immutable AI1 validation.
- Publication transition trigger with `state_revision` increments.
- Deferred current-pointer check: pointer must reference an `OFFICIAL` version.
- Deferred totals and completeness checks for every version.

## 4. Actual verification results

Verification used a disposable PostgreSQL 18.4 UTF8 cluster initialized in
`C:\Users\kudot\AppData\Local\Temp\opencode\pg-pr3a-utf8-6c1f2c367cae`, port
55440, trust auth, with a dedicated database `dbcas_pr3a_test`. Docker was
unavailable in this environment, so the repository's Docker-based pytest suite
could not be started. No shared or production database was used.

| Check | Result |
|---|---|
| Apply `db/schema.sql` then migrations 001-026 via `app.migrate` | PASS |
| Re-run `app.migrate` (already current) | PASS |
| Direct re-run of migration 026 SQL | PASS after adding `DROP TRIGGER IF EXISTS` before deferred triggers |
| Migration text audit (regex, no `count()`, no `LIKE 'v2:%'`) | PASS |
| Schema shape and session-scoped active index | PASS |
| AI run uniqueness, regex, and AI2 ordering | PASS |
| Complete result, publication transition, and narrow attempt freeze | PASS |
| Deferred completeness rejects missing criterion and swapped plan identity | PASS |
| Legacy attempt insert/update/delete remains allowed | PASS |
| SQLAlchemy models import and register 63 tables | PASS |
| Existing legacy migration tests run directly against the isolated DSN | PASS |
| `scripts/validate_diagrams.py` after regenerating catalog, FK ledger, and DOT | PASS |
| `py -3 -m compileall` on changed Python files | PASS |

Existing tests were updated only where migration 026 adds rows/columns:
migration lists now include 026, `schema_migration` count is 26, and row
fingerprints exclude the additive `review_policy` and
`current_result_version_id` columns.

Standalone runner used:

```
PR3A_TEST_DSN=postgresql://postgres@127.0.0.1:55440/dbcas_pr3a_test py -3 scripts/verify_pr3a_schema.py
```

Output:

```
PASS: migration text audit
PASS: schema shape and session-scoped index
PASS: AI run uniqueness, regex, and AI2 ordering
PASS: complete result, publication transition, and attempt freeze
PASS: deferred completeness rejects missing criterion and plan identity mismatch
PASS: legacy non-structural and structural attempt operations
PASS: 6 PR 3A schema checks
```

## 5. Technical gates

| Gate | Result |
|---|---|
| Session-scoped AI identity and active-run uniqueness | PASS |
| Exact `v2` scope regex | PASS |
| Publication session ownership and composite FK | PASS |
| AI2 ordering after immutable AI1 validation | PASS |
| Exact attempt/plan tuple completeness | PASS |
| Essay criterion completeness | PASS |
| Narrow structural attempt freeze | PASS |
| Complete deferred validation | PASS |
| Valid PostgreSQL partial indexes and composite FKs | PASS |
| Migration 026 ownership and creation order | PASS |
| Docker-based repository pytest suite | NOT RUN (Docker unavailable) |
| PostgreSQL 17 verification | NOT RUN (only isolated PG18.4 available) |
| Python diagram catalog validator | PASS |
| `npm run diagrams:check` | NOT PASS in this environment: Mermaid CLI module missing; the Python validator passed |

## 6. Remaining risks

- Verification used PostgreSQL 18.4, while the repository test harness pins
  PostgreSQL 17. The migration uses standard PostgreSQL features available in
  both versions, but a PG17 CI run is still required before merge.
- Docker was unavailable, so `backend/tests/conftest.py` could not provision
  its standard disposable PG17 container. The added pytest wrapper
  `backend/tests/test_migrations_026.py` must run in CI.
- SQLAlchemy models declare the main constraints and composite FKs; DDL-only
  partial indexes and triggers remain the migration's responsibility, matching
  existing repository convention.
- No application code reads or writes the new tables in PR 3A. This is
  intentional; later PRs add services and APIs.

## 7. Merge readiness

PR 3A database foundation is implementation-complete and verified against the
available isolated PostgreSQL instance. Merge readiness is conditional on the
PG17 Docker CI run passing. No commit, push, PR, deployment, or shared-database
migration was performed by this work.

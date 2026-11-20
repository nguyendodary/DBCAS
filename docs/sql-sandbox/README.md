# SQL Sandbox — Audit and Multi-Statement DDL/DML Design

Status: **analysis only**. No application code, migrations, seed data, Compose
files, or `docs/qa/**` are changed by this branch. Production remains **HOLD**.

Baseline: `origin/develop2` at `955abd075928bc3c3d738a20cd942dfc7bb256c8`.
Branch: `docs/sql-sandbox-design`.

## Why this exists

DBCAS currently executes learner SQL through a deliberately narrow path: one
read-only `SELECT`-shaped statement, in a separate PostgreSQL sandbox, as a
`learner_ro` role that has `SELECT` only and `default_transaction_read_only=on`.
That is the correct default for today's auto-graded `SELECT` exercises, but it
cannot express common SQL teaching tasks such as:

- a script with several `SELECT` statements (setup + answer + verification);
- `CREATE TABLE` / `INSERT` / `UPDATE` / `DELETE` exercises;
- `ALTER TABLE`, constraints, indexes, and other schema-change exercises.

This document set audits the current state, measures the relevant paths, and
proposes a design that adds multi-statement DDL/DML **without weakening the
existing isolation guarantees**.

## Recommendation in one paragraph

Keep the current SELECT-only path as the default. Add a second, explicitly
opted-in execution mode for writable scripts: a per-execution private schema
inside a disposable, network-less PostgreSQL container (`SANDBOX_MODE=ephemeral`),
a new `learner_rw` role whose only privileges are inside that schema, an AST
allow-list that rejects transaction control, `COPY`, `DO`, `CALL`, extensions,
foreign objects, roles/grants, and catalog access, and a runner that executes
the whole script in one transaction and always rolls it back. Grading gains a
`state` mode that runs a trusted verifier inside the same transaction. Shared
mode may support writable scripts in development only; staging/production must
refuse writable mode unless `SANDBOX_MODE=ephemeral`.

## Documents

| File | Contents |
| --- | --- |
| [`01-current-state.md`](01-current-state.md) | Enforcement layers, execution paths, grading, Compose/CI facts, and gaps. |
| [`02-measurements.md`](02-measurements.md) | Measured latency, startup, seed, memory, image, bundle, and CI numbers. |
| [`03-options-and-recommendation.md`](03-options-and-recommendation.md) | Options considered, comparison matrix, and the recommendation. |
| [`04-target-design.md`](04-target-design.md) | Role model, policy matrix, runner protocol, error model, grading, API/UI, limits. |
| [`05-bloat-candidates.md`](05-bloat-candidates.md) | Top five cost/bloat candidates with evidence and estimated impact. |
| [`06-delivery-plan.md`](06-delivery-plan.md) | Phases, tests, rollout, rollback, and risk register. |
| [`07-unknowns.md`](07-unknowns.md) | Items that require an owner decision or production access. |

## Evidence conventions

- `path:line` refers to the repository at the baseline commit above.
- "Measured" means a command was run in this audit against the local synthetic
  stack; the exact command and conditions are in `02-measurements.md`.
- "UNKNOWN — owner must confirm" means the fact cannot be established from the
  repository or local synthetic data. These are collected in `07-unknowns.md`.
- No production system, production data, or real student data was accessed.

## What this branch deliberately does not do

- No merge to `develop2` or `main`.
- No change to `main`, production, `docs/qa/**`, application code, migrations,
  seed data, or Compose.
- No claim that writable SQL is approved for production. The design includes a
  feature gate and a startup refusal until the owner signs off.

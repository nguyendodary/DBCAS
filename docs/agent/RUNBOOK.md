# Agent runbook

Commands are from the repository root unless noted. They are documented by the linked
repository files; a documented command is not evidence that it passed on your commit.
Use synthetic data only.

## Build, test, E2E and demo seed

Prepare Python 3.13 and the backend virtual environment as in [README](../../README.md).

```bash
python backend/manage.py lint
python backend/manage.py build
python backend/manage.py test
npm --prefix frontend ci
npm --prefix frontend test
npm --prefix frontend run build
npm --prefix frontend run test:e2e
npm run docs:check
npm run secrets:scan
```

Sources: [backend commands](../../backend/manage.py), [frontend scripts](../../frontend/package.json),
[root scripts](../../package.json), and [README](../../README.md). Backend and E2E tests need
their documented Docker/test environment. Run Docker-dependent gates sequentially ([README](../../README.md)).

`npm start` starts the local stack; its init service runs the demo seed
([local Compose](../../docker-compose.local.yml), [launcher](../../scripts/local.mjs)).
`npm run stop` stops it. Do not run `npm run reset` without explicit approval: it removes local volumes
([README](../../README.md)).

## Worktrees

```bash
git worktree list --porcelain
git -C "<worktree>" status --short --untracked-files=all --ignored
```

Inspect tracked, untracked **and ignored** files, save any unique work, and confirm the
branch/remote state before `git worktree remove "<worktree>"`. Never force-remove an
unsaved worktree. On Windows, a locked directory may refuse removal; close the owning
process and report the refusal rather than deleting around it. Worktree command syntax:
**UNVERIFIED — owner must confirm** for the local Git version.

## Failed smoke seed

The [workflow](../../.github/workflows/dn-backend.yml) collects `seed-init-smoke-N`
before teardown, including init state/log and database health/log
([collector](../../scripts/collect_seed_diagnostics.sh), [#63](https://github.com/nguyendodary/DBCAS/pull/63)).

```bash
gh run download <run-id> --name seed-init-smoke-1 --dir <evidence-directory>
gh run view <run-id> --log-failed
```

Choose the actual smoke shard number. Preserve the run ID, head SHA, artifact and
failed log; inspect init exit/state and timestamps alongside database health and log.
Do not infer a root cause from duration alone. Review diagnostics before sharing.

## Docker readiness and flaky signals

For the 15-second `docker info` failure, preserve the exact-head job log and classify
the failure using [#67](https://github.com/nguyendodary/DBCAS/issues/67); the probe is in
[conftest.py](../../backend/tests/conftest.py). For container-create timeouts see
[#55](https://github.com/nguyendodary/DBCAS/issues/55). Do not assume they share a cause.
If demo-seed or readiness fails again, save diagnostics and stop. Follow the rerun
restriction in [AGENTS.md](../../AGENTS.md).

On Windows, verify the exact bytes, line endings and syntax of generated scripts before
executing them; a newline-in-script incident was reported but its log is
**UNKNOWN — owner must confirm**. See the Windows wrapper note in
[ephemeral_sandbox.py](../../backend/app/services/ephemeral_sandbox.py).

# Phase 6 — final gates (2026-11-25)

Application commit `253f272`; documentation/tooling commits through `d6df804`.
Every result below cites a saved log and metadata with an explicitly captured
child exit code unless the older limitation is named. No gate was weakened, no
test was skipped or removed to force a pass, and no CI run was retried blindly.

## Browser and stack gates

| Gate | Command | Result | Evidence |
|---|---|---|---|
| Local stack | `npm start`, isolated worktree, project `dbcas-baseline-local` | PASS, healthy, exit 0 | [log](baseline-local-stack.log), [meta](baseline-local-stack.meta) |
| E2E localization | `npm --prefix frontend run test:e2e -- e2e/localization.spec.js` | PASS, 11 tests, exit 0 | [log](baseline-e2e-1-localization.log), [meta](baseline-e2e-1-localization.meta) |
| E2E rest 1/2 | 18 rest specs, `--shard=1/2` | PASS, 36 passed / 2 skipped, exit 0 | [log](baseline-e2e-2-rest.log), [meta](baseline-e2e-2-rest.meta) |
| E2E rest 2/2 | Same specs, `--shard=2/2` | PASS, 36 passed, exit 0; isolation proof preserved | [log](baseline-e2e-2-rest-shard2.log), [meta](baseline-e2e-2-rest-shard2.meta) |
| Practice | `npm --prefix frontend run test:practice` | PASS, 12 passed / 2 provider-only skipped, exit 0 | [log](baseline-practice.log), [meta](baseline-practice.meta) |
| Local smoke | `npm --prefix frontend run test:local` in `frontend/` | PASS, 3 repeats, exit 0 | [log](baseline-local-smoke.log), [meta](baseline-local-smoke.meta) |
| QA | `node scripts/browser-qa.mjs 3`, fake provider | PASS, 54 tests across 3 runs, exit 0 | [log](baseline-qa.log), [meta](baseline-qa.meta) |

The first shard-2 launch was terminated by a harness timeout before any test
ran and is retained separately as
[aborted evidence](baseline-e2e-2-rest-shard2-attempt1-aborted.meta), not as a
result.

After all browser gates, the QA stack was stopped with
`docker compose -p dbcas-baseline-local -f docker-compose.local.yml down`
(no `--volumes`, no `--remove-orphans`), exit 0. Its named volume
`dbcas-baseline-local_local-data` remains. The separate
`dbcas-baseline-recovery` Mailpit and the pre-existing `dbcas` stack were not
stopped; ports 18000/18025/18080/11025 are free again. Evidence:
[log](final-qa-stack-down.log), [meta](final-qa-stack-down.meta).

## Static, contract and security gates

| Gate | Command | Result | Evidence |
|---|---|---|---|
| Backend lint | `python -m ruff check app tests manage.py` from `backend/` | PASS, exit 0 | [log](baseline-backend-lint.log), [exit](baseline-backend-lint.exit) |
| Backend full test | `python -u -m pytest -q --color=no` from `backend/` | 1940 passed / 7 skipped; child exit code not captured | [log](baseline-backend-pytest.log), [meta](baseline-backend-pytest.meta), [limitation](baseline-v2.md) |
| Frontend lint | `npm --prefix frontend run lint` | PASS, exit 0 | [log](baseline-frontend-lint.log), [meta](baseline-frontend-lint.meta) |
| Frontend unit | `npm --prefix frontend test -- --maxWorkers=2` | PASS, 54 files / 463 tests, exit 0 | [log](baseline-frontend-unit.log), [meta](baseline-frontend-unit.meta) |
| Frontend format | `npm --prefix frontend run format:check` | PASS after exact-byte CRLF normalization, exit 0 | [log](baseline-frontend-format-after-lf.log), [meta](baseline-frontend-format-after-lf.meta) |
| Frontend build | `npm --prefix frontend run build` | PASS, exit 0 | [log](final-frontend-build.log), [meta](final-frontend-build.meta) |
| E2E shard assignment | `bash scripts/e2e-shards.sh check` | PASS: 25 specs assigned exactly once (1 localization, 18 rest, 4 QA, 1 smoke, 1 manual), exit 0 | [log](final-e2e-shards.log), [meta](final-e2e-shards.meta) |
| Browser/provider config tests | `node --test scripts/browser_config.test.mjs scripts/provider_control.test.mjs` | PASS, 3/3, exit 0 | [log](final-browser-config-tests.log), [meta](final-browser-config-tests.meta) |
| Launcher local unit tests | `npm run test:local` | PASS, 11/11, exit 0 | [log](baseline-local-scripts.log), [meta](baseline-local-scripts.meta) |
| Frontend security unit | `node --test scripts/frontend_security_audit.test.mjs` | PASS, 31/31, exit 0 | [log](final-frontend-security.log), [meta](final-frontend-security.meta) |
| Frontend security audit | `node scripts/frontend_security_audit.mjs` | PASS, 0 high/critical advisories, exit 0 | [log](final-frontend-audit.log), [meta](final-frontend-audit.meta) |
| Dependency audit | `npm audit --audit-level=high` | PASS, 0 vulnerabilities, exit 0 | [log](final-npm-audit.log), [meta](final-npm-audit.meta) |
| Docs | `npm run docs:check` re-run after the collector change | PASS, exit 0 | [log](final-docs-check.log), [meta](final-docs-check.meta) |
| OpenAPI | `python scripts/export_openapi.py --check` | PASS, exit 0 | [log](baseline-openapi-check.log), [meta](baseline-openapi-check.meta) |
| Environment inventory | `npm run env:check` | PASS, names/syntax only, exit 0 | [log](baseline-env-check.log), [meta](baseline-env-check.meta) |
| Route inventory | `npm run inventory:check` | PASS, exit 0 | [log](baseline-inventory-check.log), [meta](baseline-inventory-check.meta) |
| Provider | `npm run llm:check` | PASS, HTTP 200 models/chat, exit 0, no key printed | [log](baseline-provider-check.log), [meta](baseline-provider-check.meta) |
| Contrast | `npm run ui:contrast` | PASS, 186 pairs, exit 0 | [log](final-ui-contrast.log), [meta](final-ui-contrast.meta) |
| Secrets tree | `npm run secrets:scan` re-run after new scripts/logs | PASS, 3083 files / 0 findings, exit 0 | [log](final-secrets-tree.log), [meta](final-secrets-tree.meta) |
| Secrets history | Real-key pattern across reachable commits | PASS, 1042 commits / 0 matching commits; matched lines not printed | [log](baseline-secrets-history.log), [meta](baseline-secrets-history.meta) |
| Whitespace | `git diff --check` | PASS, no output | Recorded in this file's command log |

## CI and owner gates

The exact-commit CI run for `d6df804` is run `45597486074`. Two earlier runs
were superseded by later pushes and were not retried. The first `gh run watch`
ended with exit 1 because of a proven GitHub API network read timeout while the
run was still `pending`; its own output is preserved in
[final-ci-watch.log](final-ci-watch.log) and
[metadata](final-ci-watch.meta). The workflow uses a per-branch concurrency
group with `cancel-in-progress: false` for pushes, so this run waited behind
the still-running `2c3a582` run. Exactly one deliberate watch re-attempt was
started and is recorded in [final-ci-watch-attempt2.log](final-ci-watch-attempt2.log),
but it also exited in 11 seconds with `error connecting to api.github.com`. No
CI job was manually rerun. A direct read at that point showed the run genuinely
`in_progress` with `changes`, `frontend-static` and `secrets` already successful
and backend, three E2E shards, three QA shards and three smoke shards still
running. No further watch retry was attempted. A single later status check recorded
**conclusion `success`** for run `45597486074` on `d6df804`: all 14 jobs were
successful (`changes`, `frontend-static`, `backend`, `secrets`,
`frontend-local`, E2E localization, E2E rest 1/2 and 2/2, QA-1/2/3, and smoke
1/2/3). Evidence: [CI conclusion](final-ci-conclusion.log),
[metadata](final-ci-conclusion.meta). This is exact-commit CI evidence; it is
not copied into STATUS or BACKLOG.

- D1: no cleanup file deletion performed; only the proposal exists.
- D3: no `develop2 → main` merge or PR; `main` remains `e7e432c`.
- D4: no image snapshot, approved academic DOCX, product copy or UI behavior
  changed; two stale-copy findings are recorded in [ui-review](ui-review.md).

Production remains **HOLD**. The only unresolved test evidence limitation is
the old PowerShell wrapper's missing pytest child exit code; the full pytest
output has no failures or errors and is not represented as an observed zero.

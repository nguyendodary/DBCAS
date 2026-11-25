# Phase B — local baseline (complete with one captured limitation)

Started 2026-11-25 on `develop2`. The application run started at `253f272`;
subsequent commits changed only `docs/agent/**` and the narrow documentation
collector outside the application runtime. Browser and QA work used the
isolated worktree at the same application commit. Docker-using commands were
run sequentially. This is the final Phase B record with the pytest exit-code
limitation below preserved.

| Gate | Command | Observed result | Evidence |
|---|---|---|---|
| Backend lint | `.venv\Scripts\python.exe -m ruff check app tests manage.py` from `backend/` | PASS, exit 0 | [log](baseline-backend-lint.log), [exit](baseline-backend-lint.exit) |
| Backend full test | `.venv\Scripts\python.exe -u -m pytest -q --color=no` from `backend/` | Summary: **1940 passed, 7 skipped, 1 warning**, 1438.70 s. The child exit code was not captured; see limitation below. | [stdout](baseline-backend-pytest.log), [stderr](baseline-backend-pytest.stderr.log), [metadata](baseline-backend-pytest.meta) |
| Frontend lint | `npm --prefix frontend run lint` | PASS, exit 0 | [log](baseline-frontend-lint.log), [metadata](baseline-frontend-lint.meta) |
| Frontend unit | `npm --prefix frontend test -- --maxWorkers=2` | PASS, 54 files / 463 tests, exit 0 | [log](baseline-frontend-unit.log), [metadata](baseline-frontend-unit.meta) |
| Frontend format | `npm --prefix frontend run format:check` | Initial run FAIL, exit 1: six checkout files had CRLF. After preserving their exact bytes and normalizing them to the unchanged Git LF content, the same command PASS, exit 0. | [first log](baseline-frontend-format.log), [first exit](baseline-frontend-format.meta), [byte comparison and backups](baseline-format-line-endings.log), [passing log](baseline-frontend-format-after-lf.log), [passing exit](baseline-frontend-format-after-lf.meta) |
| E2E localization shard | `npm --prefix frontend run test:e2e -- e2e/localization.spec.js` | PASS, 11 tests, 13.5 min, exit 0 | [log](baseline-e2e-1-localization.log), [metadata](baseline-e2e-1-localization.meta) |
| E2E rest, shard 1/2 | `npm --prefix frontend run test:e2e -- <18 rest specs> --shard=1/2` | PASS: 36 passed, 2 skipped, 9.8 min, exit 0 | [log](baseline-e2e-2-rest.log), [metadata](baseline-e2e-2-rest.meta) |
| E2E rest, shard 2/2 | Same 18 specs with `--shard=2/2`, application commit `253f272` | PASS: 36 passed, 8.4 min, exit 0. Isolation proof preserved under the isolated worktree's `_review/saved-proofs/e2e-2-rest-shard2.json`. | [log](baseline-e2e-2-rest-shard2.log), [metadata](baseline-e2e-2-rest-shard2.meta), [aborted attempt](baseline-e2e-2-rest-shard2-attempt1-aborted.meta) |
| Local stack for practice/local/QA/smoke | `npm start` in isolated worktree, project `dbcas-baseline-local`, example-based `.env`, no real key passed | PASS: all services healthy and readiness succeeded, exit 0, 337.7 s | [log](baseline-local-stack.log), [metadata](baseline-local-stack.meta) |
| Practice | `npm --prefix frontend run test:practice` in isolated worktree | PASS: 12 passed, 2 provider-only skipped, 2.9 min, exit 0 | [log](baseline-practice.log), [metadata](baseline-practice.meta) |
| Local smoke | `npm --prefix frontend run test:local` in isolated worktree | PASS: 3 passed with 3 repeats, 4.5 min, exit 0 | [log](baseline-local-smoke.log), [metadata](baseline-local-smoke.meta) |
| QA | `node scripts/browser-qa.mjs 3` in isolated worktree, fake provider, native Docker CLI removed from child PATH | PASS: 54 tests across 3 consecutive runs, 19.7 min, exit 0 | [log](baseline-qa.log), [metadata](baseline-qa.meta) |
| Launcher local unit tests | `npm run test:local` from repository root | PASS: 11/11 tests, exit 0 | [log](baseline-local-scripts.log), [metadata](baseline-local-scripts.meta) |
| Docs gate | `npm run docs:check` | PASS, exit 0 | [log](baseline-docs-check.log), [metadata](baseline-docs-check.meta) |
| OpenAPI contract | `backend\.venv\Scripts\python.exe scripts\export_openapi.py --check` | PASS, exit 0 | [log](baseline-openapi-check.log), [metadata](baseline-openapi-check.meta) |
| Environment inventory | `npm run env:check` | PASS, exit 0; names/syntax only, no full key printed | [log](baseline-env-check.log), [metadata](baseline-env-check.meta) |
| Route inventory | `npm run inventory:check` | PASS, both generated inventories match sources, exit 0 | [log](baseline-inventory-check.log), [metadata](baseline-inventory-check.meta) |
| Provider check | `npm run llm:check` | PASS: generic provider, HTTP 200 models and chat, exit 0; no key printed | [log](baseline-provider-check.log), [metadata](baseline-provider-check.meta) |
| Secrets tree scan | `npm run secrets:scan` | PASS: 3050 files, 0 findings, exit 0 | [log](baseline-secrets-tree.log), [metadata](baseline-secrets-tree.meta) |
| Secrets history scan | Real-key pattern across all reachable commits | PASS: 1042 commits scanned, 0 matching commits; matching lines were not printed | [log](baseline-secrets-history.log), [metadata](baseline-secrets-history.meta) |

The browser evidence was kept under the isolated recovery worktree's `_review`
directory. The second shard's disposable-database isolation proof was copied to
`_review/saved-proofs/e2e-2-rest-shard2.json` before any subsequent Docker gate.
The first shard-2 launch was terminated by a harness configuration timeout after
one second, before any test ran; it is retained as
[aborted evidence](baseline-e2e-2-rest-shard2-attempt1-aborted.meta) and is not a
test result.

## Captured limitation

The PowerShell background wrapper's `Process.ExitCode` was null after
`WaitForExit`. Its own shell returned zero, but that is **not** evidence of the
pytest child's exit code. The complete pytest output reports no failures or
errors and gives the counts above; the unobserved child exit remains a limitation
of this run rather than being silently recorded as zero. The seven skips are
pytest's reported result; no test was removed or newly skipped by this task.

No pre-existing Docker container was stopped as part of the baseline run.
The pytest-owned disposable containers are no longer running. Existing dev
services and the five older standalone test containers remained running.

The six format failures were caused solely by checkout line endings: each
original file normalized to the exact Git blob and to Prettier's output.
Original CRLF bytes and hashes were saved outside the checkout under
`_worktrees/recovery-baseline-20261125/format-crlf-originals/`. After the
repair, `git diff --exit-code -- frontend` returned 0; no test expectation or
product logic was changed.

For browser tests, the separate Compose project `dbcas-baseline-recovery` has
its own Mailpit on ports 18825/11825; its [startup log](baseline-e2e-mailpit.log)
and [exit status](baseline-e2e-mailpit.meta) are recorded. The existing `dbcas`
project is not used by these E2E shards. Test output, manifests and isolation
proofs are placed beneath the isolated recovery worktree's parent directory.
The first shard's proof was copied to `_review/saved-proofs/e2e-1-localization.json`
within that isolated parent before starting the next shard.

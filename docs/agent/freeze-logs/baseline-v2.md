# Phase B — local baseline (in progress)

Started 2026-11-25 on `develop2`. The backend run started at `253f272`;
subsequent commits through this checkpoint change only `docs/agent/**`.
Browser work will use the isolated worktree at the same application commit.
Commands that use Docker are run sequentially. This is a partial record, not
the final Phase B result.

| Gate | Command | Observed result | Evidence |
|---|---|---|---|
| Backend lint | `.venv\Scripts\python.exe -m ruff check app tests manage.py` from `backend/` | PASS, exit 0 | [log](baseline-backend-lint.log), [exit](baseline-backend-lint.exit) |
| Backend full test | `.venv\Scripts\python.exe -u -m pytest -q --color=no` from `backend/` | Summary: **1940 passed, 7 skipped, 1 warning**, 1438.70 s. The child exit code was not captured; see limitation below. | [stdout](baseline-backend-pytest.log), [stderr](baseline-backend-pytest.stderr.log), [metadata](baseline-backend-pytest.meta) |
| Frontend lint | `npm --prefix frontend run lint` | PASS, exit 0 | [log](baseline-frontend-lint.log), [metadata](baseline-frontend-lint.meta) |
| Frontend unit | `npm --prefix frontend test -- --maxWorkers=2` | PASS, 54 files / 463 tests, exit 0 | [log](baseline-frontend-unit.log), [metadata](baseline-frontend-unit.meta) |
| Frontend format | `npm --prefix frontend run format:check` | Initial run FAIL, exit 1: six checkout files had CRLF. After preserving their exact bytes and normalizing them to the unchanged Git LF content, the same command PASS, exit 0. | [first log](baseline-frontend-format.log), [first exit](baseline-frontend-format.meta), [byte comparison and backups](baseline-format-line-endings.log), [passing log](baseline-frontend-format-after-lf.log), [passing exit](baseline-frontend-format-after-lf.meta) |
| E2E localization shard | `npm --prefix frontend run test:e2e -- e2e/localization.spec.js` | PASS, 11 tests, 13.5 min, exit 0 | [log](baseline-e2e-1-localization.log), [metadata](baseline-e2e-1-localization.meta) |
| E2E rest, shard 1/2 | `npm --prefix frontend run test:e2e -- <18 rest specs> --shard=1/2` | Running on isolated worktree | [metadata](baseline-e2e-2-rest.meta); live output is on disk |
| E2E rest, shard 2/2; practice, local, QA, smoke | Owner-specified commands | Pending | To be recorded |
| Docs, OpenAPI, environment, inventory, provider, secrets tree/history | Owner-specified commands | Pending | To be recorded |

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

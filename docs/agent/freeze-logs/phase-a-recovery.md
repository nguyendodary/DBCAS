# Phase A — recovery and coordination (2026-11-25)

## Checkout and previous work

- `git fetch origin` and `git pull --ff-only` completed. At recovery both
  `develop2` and `origin/develop2` were `ee19cd2`, with a clean worktree.
- Local `main` and `origin/main` were both `e7e432ce`; neither was changed.
- The existing `stash@{0}` belongs to an earlier main-worktree preservation;
  it was not applied or dropped. There was one registered worktree.
- `7c262ad`, `6f60f69`, and `638144e` modify only `frontend/e2e/**`.
  `ee19cd2` adds only `docs/agent/freeze-logs/ci-spec-fix.md`, outside that
  directory. The previous session stopped at this exact Phase A.4 condition.
  The renewed recovery request names all four commits, directs verification,
  and lists D1, D3, and D4 as owner gates; the documentation-only exception is
  recorded here and is not represented as an E2E file.
- The earlier `e2e-edits-pre-kill.patch` and `_patch_group*.patch` were not
  found at the inspected locations. `e2e-edits-recreated.patch` was regenerated
  using `git diff --binary 2eea105..ee19cd2 -- frontend/e2e`; `git apply
  --check --reverse` succeeded against the recovered checkout. This proves the
  recreated diff matches the current E2E files, not that a missing backup was
  independently compared. The exact patch contains blank context lines whose
  required leading spaces are reported by `git diff --check` when the patch
  itself is added; the other staged files pass the whitespace check.

## Processes, ports and containers

- PIDs 9588 and 18640 were absent. The previous session reports PID 18640 was
  stopped after identity verification and PID 9588 exited on its own.
- No matching process had a working directory inside `DBCAS`, and no listener
  or connection was found on 8100, 8101, 5174, or 18000–18999. The Playwright
  MCP and current Codex processes were kept running.
- The previous session stopped the `dbcas-local` Compose project without
  `--volumes`. At recovery `dbcas` had three running services. Five other
  running PostgreSQL/test containers had no Compose project label; their
  ownership was not inferred and they were left untouched.
- `gh run view 45563628373` reports success for exact commit `ee19cd2`,
  including backend, frontend-static, secrets, changes, frontend-local, and
  all listed E2E, QA, and smoke shards. This is CI evidence for that commit;
  it is not a substitute for the separately requested local Phase B baseline.

## Next

Run Phase B sequentially and save each command's output and exit status.
Do not alter the committed E2E specifications merely to repeat their prior fix.

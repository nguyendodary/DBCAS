# Recovery progress

Last updated: 2026-11-25. Project checkout: `develop2`.

| Phase | Status | Evidence or next action |
|---|---|---|
| A | Recovery and inventory complete; previous A.4 scope exception recorded | [phase-a-recovery.md](phase-a-recovery.md) |
| B | Pending | Run the local baseline sequentially; record results in `baseline-v2.md` and individual logs. |
| 0 | Pending | Survey the workspace and branches; write `phase0-survey.md`. |
| 3 | Pending | Prepare `cleanup-proposal.md`; deletion remains gated by D1. |
| 4 | Pending | Review the real UI; record `ui-review.md`; snapshot and out-of-scope product changes remain gated by D4. |
| 5 | Pending | Read the source Word templates, create `ver1.3` outputs, render and verify. |
| 6 | Pending | Run final gates and real-stack E2E after the preceding work. |
| 7 | Pending | Follow branch protection; owner review remains gated by D3. |

## Next commands

From `DBCAS/backend`: `.\.venv\Scripts\python.exe -m ruff check app tests manage.py`,
then `.\.venv\Scripts\python.exe -m pytest -q`, with output and exit status
saved under `docs/agent/freeze-logs/`. Continue with the remaining Phase B
commands in the owner specification, one stack-using gate at a time.

Never print secrets or commit `.env`; do not modify `docs/qa/**`, applied
migrations, validators or scoring schema; do not add dependencies, relax or
delete tests, force-push, rebase published history, or delete remote refs.
Do not delete files or directories before owner approval. No changes to `main`
are authorized before the release gate.

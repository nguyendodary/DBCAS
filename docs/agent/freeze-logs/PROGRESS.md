# Recovery progress

Last updated: 2026-11-25. Project checkout: `develop2`.

| Phase | Status | Evidence or next action |
|---|---|---|
| A | Recovery and inventory complete; previous A.4 scope exception recorded | [phase-a-recovery.md](phase-a-recovery.md) |
| B | Running | [baseline-v2.md](baseline-v2.md) records completed checks and limitations; E2E localization shard is running, PID 22388. |
| 0 | Inventory recorded; detailed review incomplete | [phase0-survey.md](phase0-survey.md) records all branches; 246 paths in a large historical sync differ from the baseline and need review. |
| 3 | Proposal ready; D1 pending | [cleanup-proposal.md](cleanup-proposal.md); item 1 is the only proposed deletion. |
| 4 | Pending | Review the real UI; record `ui-review.md`; snapshot and out-of-scope product changes remain gated by D4. |
| 5 | Template analysis started | [doc-style-spec.md](doc-style-spec.md) records measured FITAI styles; four `ver1.3` outputs and full render verification remain pending. |
| 6 | Pending | Run final gates and real-stack E2E after the preceding work. |
| 7 | Pending | Follow branch protection; owner review remains gated by D3. |

## Next commands

Check `baseline-e2e-1-localization.meta` and its recorded PID before starting
any other Docker-using gate. After that shard finishes, run the two remaining
E2E shards, practice, local, QA, smoke, and the remaining documentation,
provider and secret gates. Keep Docker-using gates sequential and preserve logs.

An isolated, detached worktree at
`_worktrees/recovery-baseline-20261125/DBCAS` points at `253f272`. It reuses
the existing dependency directories through junctions and has its own ignored
example-based `.env`; browser and QA evidence must use this isolated tree so
existing `_review` evidence is not overwritten. The workspace and branch
inventory is recorded; see the Phase 0 report before treating its large
historical synchronization diff as semantically reviewed.

Never print secrets or commit `.env`; do not modify `docs/qa/**`, applied
migrations, validators or scoring schema; do not add dependencies, relax or
delete tests, force-push, rebase published history, or delete remote refs.
Do not delete files or directories before owner approval. No changes to `main`
are authorized before the release gate.

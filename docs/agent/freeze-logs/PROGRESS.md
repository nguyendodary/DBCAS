# Recovery progress

Last updated: 2026-11-25. Project checkout: `develop2`.

| Phase | Status | Evidence or next action |
|---|---|---|
| A | Recovery and inventory complete; previous A.4 scope exception recorded | [phase-a-recovery.md](phase-a-recovery.md) |
| B | Complete with one limitation | [baseline-v2.md](baseline-v2.md): all gates passed with recorded exit codes except the old pytest child exit-code capture limitation; E2E 11+36+36, practice 12/2 skipped, local smoke 3/3, QA 54/54, all static/provider/secret gates green. |
| 0 | Review complete with stated limitation | [phase0-survey.md](phase0-survey.md) records all branches; [phase0-large-sync-review.md](phase0-large-sync-review.md) disposes of all 236 remaining paths with no import candidate, while preserving the binary/generated-file limitation. |
| 3 | Proposal ready; D1 pending | [cleanup-proposal.md](cleanup-proposal.md); item 1 is the only proposed deletion. |
| 4 | Pending | Review the real UI; record `ui-review.md`; snapshot and out-of-scope product changes remain gated by D4. |
| 5 | Template analysis started | [doc-style-spec.md](doc-style-spec.md) records measured FITAI styles; [collector discrepancy](doc-facts-discrepancy.md) and four verified `ver1.3` outputs remain. |
| 6 | Pending | Run final gates and real-stack E2E after the preceding work. |
| 7 | Pending | Follow branch protection; owner review remains gated by D3. |

## Next commands

Phase B is recorded; do not rerun its green gates. Next: review the real UI and
write `ui-review.md` without product changes (D4), finish the four verified
`ver1.3` Word files and the narrow collector correction, then run the Phase 6
final gates. Keep Docker-using gates sequential and preserve logs. The
interrupted first shard-2 launch remains retained as `*-attempt1-aborted.*` and
is not evidence.

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

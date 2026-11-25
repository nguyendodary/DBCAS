# Recovery progress

Last updated: 2026-11-25. Project checkout: `develop2`.

| Phase | Status | Evidence or next action |
|---|---|---|
| A | Recovery and inventory complete; previous A.4 scope exception recorded | [phase-a-recovery.md](phase-a-recovery.md) |
| B | Complete with one limitation | [baseline-v2.md](baseline-v2.md): all gates passed with recorded exit codes except the old pytest child exit-code capture limitation; E2E 11+36+36, practice 12/2 skipped, local smoke 3/3, QA 54/54, all static/provider/secret gates green. |
| 0 | Review complete with stated limitation | [phase0-survey.md](phase0-survey.md) records all branches; [phase0-large-sync-review.md](phase0-large-sync-review.md) disposes of all 236 remaining paths with no import candidate, while preserving the binary/generated-file limitation. |
| 3 | Proposal ready; D1 pending | [cleanup-proposal.md](cleanup-proposal.md); item 1 is the only proposed deletion. |
| 4 | Review complete; no product change | [ui-review.md](ui-review.md) records desktop/mobile/admin evidence and two D4-gated copy findings; no image snapshot, translation or behavior was edited. |
| 5 | Generation and verification complete; approval gated | [doc-verify.md](doc-verify.md) records four hashes, 79/79 audit assertions, Word/PDF page parity (61/78/72/9) and the narrow collector fix. DOCX remain outside Git pending owner approval. |
| 6 | Complete | [final-gates-v2.md](final-gates-v2.md) records all local gates, QA-stack teardown and exact-commit CI run `45597486074` **success** (12/12 jobs); two watch attempts only failed on GitHub API connectivity. |
| 7 | Gates verified; no merge | [phase7-branch-gates.md](phase7-branch-gates.md): `main` unchanged, no open PR, no branch protection/ruleset bypass, D1/D3/D4 still owner-gated. |

## Next commands

All recovery phases are complete. Do not rerun green gates. Remaining actions
are owner decisions only: D1 cleanup deletion, D3 `develop2 → main` promotion,
and D4 approval of the two stale-copy corrections and the four external
`ver1.3` DOCX. The interrupted first shard-2 launch remains retained as
`*-attempt1-aborted.*` and is not evidence. Production stays **HOLD**.

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

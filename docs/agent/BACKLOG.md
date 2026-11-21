# Ordered backlog

Priorities and owners live here; the current snapshot is in [STATUS](STATUS.md).

## Waiting for owner

1. **(a) Broker UNKNOWNs:** answer the open questions in the [broker design](../sql-sandbox/broker/README.md) and [SQL sandbox UNKNOWNs](../sql-sandbox/07-unknowns.md) before PR-B writable execution. [#66](https://github.com/nguyendodary/DBCAS/issues/66) tracks the decision; [#69](https://github.com/nguyendodary/DBCAS/pull/69) is merged documentation only, **not owner-approved**. Review [owner decisions](../analysis/owner-decisions.md) and approve or amend the five assumed defaults before [#76](https://github.com/nguyendodary/DBCAS/pull/76) is merged.
2. **(b) Readiness edits:** decide on the local branch `docs/pending-readiness-edits` (head `8bc95fb7ab423cba8583f092d64362cd6001838c`); integrate selectively, do not merge as-is (stale baseline `37a384a`).
3. **(c) Local Docker inventory:** identify the local `dbcas-*` containers and volumes before any local Docker test; never delete or prune them blindly. Local inventory logs: `_review/merge-20261121/docker-containers-before.log` and `_review/merge-20261121/docker-volumes-before.log`.
4. **(d) Production gates (unchanged):** account-level OpenRouter ZDR and logging settings ([deployment guide](../deployment-and-readiness.md)); Vietnamese rubric quality evaluation ([activation readiness](../activation-readiness-20261025.md)); gateway, rollback and monitoring rehearsal ([deployment guide](../deployment-and-readiness.md)). Phase 6 planning documents are not done. **UNKNOWN — owner must confirm**.

## Needs owner

5. [#67](https://github.com/nguyendodary/DBCAS/issues/67): Docker readiness timeout — fix merged in [#70](https://github.com/nguyendodary/DBCAS/pull/70); issue open for the owner to close after observing CI.
6. [#71](https://github.com/nguyendodary/DBCAS/issues/71): qa-1 `sandbox_busy` 503 on concurrent SQL load — flaky under load, cause **UNKNOWN — owner must confirm**; CI was red on attempt 1 and green on attempt 2 of [run 44792968574](https://github.com/nguyendodary/DBCAS/actions/runs/44792968574). Phase B analysis: `docs/analysis/qa1-sandbox-busy.md`.
7. [#55](https://github.com/nguyendodary/DBCAS/issues/55): Docker container-create timeouts.
8. Prioritize [bloat follow-ups](../sql-sandbox/05-bloat-candidates.md).
9. Inventory and approve cleanup of stale local images ([bloat candidates](../sql-sandbox/05-bloat-candidates.md)); do not prune blindly.
10. [#75](https://github.com/nguyendodary/DBCAS/pull/75): diagnostics-only PR is green after regenerating the route inventory. Collect the `sandbox_busy rejection` fields on the next #71 occurrence; see [STATUS](STATUS.md). May merge after owner review.
11. [#76](https://github.com/nguyendodary/DBCAS/pull/76): default-off broker skeleton is green after documenting `SANDBOX_BROKER*` in `.env.example` and regenerating the route inventory. Keep the flag OFF and production **HOLD** until the owner approves the assumptions in [owner decisions](../analysis/owner-decisions.md).
12. Owner actions still pending: approve or amend the assumed defaults (channel, TTL 300 s, 30-day audit, `SANDBOX_BROKER`/`BROKER_ENABLED` naming) before #76 merges; identify local `dbcas-*` containers and volumes before any local Docker test; decide on local branch `docs/pending-readiness-edits` (do not merge as-is).

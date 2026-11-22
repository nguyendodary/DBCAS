# Ordered backlog

Priorities and owners live here; the current snapshot is in [STATUS](STATUS.md).

## Waiting for owner

1. **(a) Broker UNKNOWNs:** answer the remaining open questions in the [broker design](../sql-sandbox/broker/README.md) and [SQL sandbox UNKNOWNs](../sql-sandbox/07-unknowns.md) before PR-B writable execution. [#66](https://github.com/nguyendodary/DBCAS/issues/66) tracks the decision; [#69](https://github.com/nguyendodary/DBCAS/pull/69) is merged documentation only. The five B1 defaults are **approved by owner** ([owner decisions](../analysis/owner-decisions.md#owner-decisions--approved-2026-11-21-verbatim)); everything else stays **UNKNOWN — owner must confirm**.
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
11. [#76](https://github.com/nguyendodary/DBCAS/pull/76): merged as `50f5724`; five defaults approved by owner; flag stays OFF by default.
12. [#80](https://github.com/nguyendodary/DBCAS/pull/80): **closed for the demo scope**, not merged; branch/worktree kept. Broker stays OFF; #66 `docker.sock` is an accepted demo limitation.
13. [#89](https://github.com/nguyendodary/DBCAS/pull/89): seed snapshot — **skipped by owner**, do not merge. [#90](https://github.com/nguyendodary/DBCAS/pull/90): opt-in writable SQL — **merged as `986f992`**; flags OFF. [#91](https://github.com/nguyendodary/DBCAS/pull/91): runbook merged as `b54e0b6`.
14. [#93](https://github.com/nguyendodary/DBCAS/pull/93): Free/Pro **UI-only** simulation (`VITE_DEMO_FREE_PRO=false` by default, `DBCAS_DEMO_PROFILE=free-pro`); no backend route, migration or payment. Awaiting owner review.
15. **Demo rehearsal:** 3 full CI runs green on `78c340b` (PR #92, closed); owner applies `demo-v1` after the selected PRs merge ([runbook](../demo/README.md)).
16. Remaining work in order: **B3** split the broker into its own service and remove the Docker CLI/socket from the API image/Compose (this is what closes [#66](https://github.com/nguyendodary/DBCAS/issues/66), which stays **open**), then warm pool, state grading, frontend.
17. Owner actions still pending: U6/U7/U8/U10 substrate, issuer/rotation, image digest, limits, U18 required checks, local `dbcas-*` inventory, `docs/pending-readiness-edits` (do not merge as-is), OTP vs reset-link ([#25](https://github.com/nguyendodary/DBCAS/pull/25)). Remaining [owner decisions](../analysis/owner-decisions.md) items are **UNKNOWN — owner must confirm**.

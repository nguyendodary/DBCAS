# Ordered backlog

Priorities and owners live here; the current snapshot is in [STATUS](STATUS.md).

## Packaging recovery (2026-11-25) — complete

- The sequential [Phase B baseline](freeze-logs/baseline-v2.md) and
  [final gates](freeze-logs/final-gates-v2.md) are recorded with saved logs and
  exit codes; exact-commit CI run `45597486074` was `success` (14/14 jobs). The
  historical pytest child exit-code capture limitation remains documented.
- The workspace/branch survey and the
  [detailed sync review](freeze-logs/phase0-large-sync-review.md) are complete;
  all 236 remaining paths were dispositioned with the stated binary/generated
  limitation and no import candidate.
- The [real UI review](freeze-logs/ui-review.md) is complete. Two stale-copy
  items await the D4 decision; no product copy, image snapshot or behavior was
  changed.
- The `ver1.3` set is **five** documents (Proposal, Architecture, Database,
  Code Standards, Technical Report) under `docs/submission/final`.
  [Verification](freeze-logs/doc-verify.md) records 62/79/75/14/15 pages, 148 XML
  assertions / 0 failures, 67-table traceability, the measured
  [FITAI specification](freeze-logs/doc-style-spec.md), 0 near-empty and 0
  overflow PDF pages, and 0 TOC/list page mismatches. `npm run docs:verify-word`
  is the gate.
- 2026-11-26 baseline replacement: the condensed generated set was rejected and
  archived to `Archive/rejected-final-20261126/` (49 files + `MANIFEST.sha256`).
  The owner set was rebuilt by **in-place revision** of the content-complete
  `Documents/Final-ver1.3` Proposal/Architecture/Database and the best surviving
  DBCAS Code Standards/Technical Report. The 13-page ERD/ledger set was rebuilt
  from introspection (67/561/122; 58 intra-domain + 64 cross-domain FKs), the
  Gantt from Table 13, and a legible layering figure was added to Code Standards.
  Evidence: [baseline-selection.md](freeze-logs/baseline-selection.md),
  [doc-verify.md](freeze-logs/doc-verify.md), `verification/proposal-sections.md`.
  Ten owner facts remain O1–O10 in Appendix A of every document.
- The stale practice count in `scripts/doc_facts.py` was corrected from
  `public_config()` and verified against the current public configuration
  without changing validators or application validation.
- Await the owner gates: D1 deletion of item 1 in the
  [cleanup proposal](freeze-logs/cleanup-proposal.md), D3 `develop2 → main`
  promotion, and D4 approval of external documents and the two copy fixes.
  No deletion, merge, remote ref change or product snapshot change was made.

## Accepted freeze work (2026-11-24)

T1–T8 are accepted architecture-freeze changes, one commit each (`efb15e1`,
`59a41df`, `39f1d36`, `25ac1b3`, `2b0641a`, `ac74ed1`, `3a16152`, `974b92b`):
upload-limit alignment, full i18n, AI adaptive mode 2, AI candidate queue,
mixed AI question types, mode UI + AI badge, DML state grading, and default
Free/Pro UI gating. T9 records the freeze and verification in
[ARCHITECTURE_FREEZE.md](../ARCHITECTURE_FREEZE.md). No further feature is
accepted after the freeze commit.

## Owner-approved configuration change (2026-11-24)

After the freeze, the owner approved a configuration-only change so any
OpenAI-compatible LLM provider can be selected by editing `.env` alone. It
removes `OPENROUTER_*` and vendor-only guards/parameters, keeps one `LLM_*`
block, adds `npm run llm:check`, and retries optional request fields once
without them on 400/422. No generation logic, validator, grading, migration or
UI changed; see section 7.2 of [ARCHITECTURE_FREEZE.md](../ARCHITECTURE_FREEZE.md).

## Code freeze (2026-11-23)

`develop2` `333e8c4518c217eae1d1aaf65813bdb84b4e050b` is frozen: no further feature, table, migration, route or flag work for the synthetic demo submission. Phase B fixes #96, #97, #98 and #101-#105 are merged; [#107](https://github.com/nguyendodary/DBCAS/pull/107) tooling, [#100](https://github.com/nguyendodary/DBCAS/pull/100) submission documents, [#108](https://github.com/nguyendodary/DBCAS/pull/108) status snapshot and [#109](https://github.com/nguyendodary/DBCAS/pull/109) test-only flake fix are merged. The earlier 3x on `14ffdead` failed attempt 3 in `test_capability_peer_identity_and_replay` (base64url padding-only forgery); #109 makes the forgery deterministic with no production change. New 3x on `333e8c45`: [run `45192055379`](https://github.com/nguyendodary/DBCAS/actions/runs/45192055379) attempts 1-3 green, backend 1914. This docs-only snapshot is the last change before the 2026-11-24, owner-requested branch-integration pass: `feat/broker-runtime` (#80) was merged with fixes behind default-OFF `SANDBOX_BROKER`; three superseded branches were merged for history only. No new feature, table, migration, route or flag work was added. Production remains **HOLD**.

## Waiting for owner

1. **(a) Broker UNKNOWNs:** answer the remaining open questions in the [broker design](../sql-sandbox/broker/README.md) and [SQL sandbox UNKNOWNs](../sql-sandbox/07-unknowns.md) before PR-B writable execution. [#66](https://github.com/nguyendodary/DBCAS/issues/66) tracks the decision; [#69](https://github.com/nguyendodary/DBCAS/pull/69) is merged documentation only. The five B1 defaults are **approved by owner** ([owner decisions](../analysis/owner-decisions.md#owner-decisions--approved-2026-11-21-verbatim)); everything else stays **UNKNOWN — owner must confirm**.
2. **(b) Readiness edits:** decide on the local branch `docs/pending-readiness-edits` (head `8bc95fb7ab423cba8583f092d64362cd6001838c`); integrate selectively, do not merge as-is (stale baseline `37a384a`).
3. **(c) Local Docker inventory:** identify the local `dbcas-*` containers and volumes before any local Docker test; never delete or prune them blindly. Local inventory logs: `_review/merge-20261121/docker-containers-before.log` and `_review/merge-20261121/docker-volumes-before.log`.
4. **(d) Production gates (unchanged):** account-level provider ZDR and logging settings, now an operator decision outside the app ([deployment guide](../deployment-and-readiness.md)); Vietnamese rubric quality evaluation ([activation readiness](../activation-readiness-20261025.md)); gateway, rollback and monitoring rehearsal ([deployment guide](../deployment-and-readiness.md)). Phase 6 planning documents are not done. **UNKNOWN — owner must confirm**.

## Needs owner

5. [#67](https://github.com/nguyendodary/DBCAS/issues/67): Docker readiness timeout — fix merged in [#70](https://github.com/nguyendodary/DBCAS/pull/70); issue open for the owner to close after observing CI.
6. [#71](https://github.com/nguyendodary/DBCAS/issues/71): qa-1 `sandbox_busy` 503 on concurrent SQL load — flaky under load, cause **UNKNOWN — owner must confirm**; CI was red on attempt 1 and green on attempt 2 of [run 44792968574](https://github.com/nguyendodary/DBCAS/actions/runs/44792968574). Phase B analysis: `docs/analysis/qa1-sandbox-busy.md`.
7. [#55](https://github.com/nguyendodary/DBCAS/issues/55): Docker container-create timeouts.
8. Prioritize [bloat follow-ups](../sql-sandbox/05-bloat-candidates.md).
9. Inventory and approve cleanup of stale local images ([bloat candidates](../sql-sandbox/05-bloat-candidates.md)); do not prune blindly.
10. [#75](https://github.com/nguyendodary/DBCAS/pull/75): diagnostics-only PR is green after regenerating the route inventory. Collect the `sandbox_busy rejection` fields on the next #71 occurrence; see [STATUS](STATUS.md). May merge after owner review.
11. [#76](https://github.com/nguyendodary/DBCAS/pull/76): merged as `50f5724`; five defaults approved by owner; flag stays OFF by default.
12. [#80](https://github.com/nguyendodary/DBCAS/pull/80): closed for the demo scope, then merged on explicit owner request as part of the branch-integration pass; constrained runtime stays behind default-OFF `SANDBOX_BROKER`. #66 `docker.sock` remains a known limitation until the separately reviewed B2 cutover; writable execution through the broker is B3 and is not part of this merge.
13. [#89](https://github.com/nguyendodary/DBCAS/pull/89): seed snapshot — **skipped by owner**; its versioned snapshot path was replaced by [#111](https://github.com/nguyendodary/DBCAS/pull/111), so the stale branch was merged for history only. `docs/submission-final` (#99) was likewise superseded by [#100](https://github.com/nguyendodary/DBCAS/pull/100) and merged for history only. [#90](https://github.com/nguyendodary/DBCAS/pull/90): opt-in writable SQL — **merged as `986f992`**; flags OFF. [#91](https://github.com/nguyendodary/DBCAS/pull/91): runbook merged as `b54e0b6`.
14. [#93](https://github.com/nguyendodary/DBCAS/pull/93): Free/Pro **UI-only** simulation — **merged as `a9a3e25`**; `VITE_DEMO_FREE_PRO=false` by default, no backend route/migration/payment.
15. **Demo flake/tag:** [#94](https://github.com/nguyendodary/DBCAS/issues/94) `practice-flows` heading timeout — **UNKNOWN — owner must confirm**. Rehearsal: 3 full CI runs green on `78c340b` (PR #92 closed; `demo/rehearsal` merged for history only on 2026-11-24). Owner steps: enable `DBCAS_DEMO_PROFILE=writable,free-pro`, rehearse once, offline QA AI fallback, then `demo-v1` ([runbook](../demo/README.md)).
16. Remaining work in order: **B2 cutover** split the broker into its own service and remove the Docker CLI/socket from the API image/Compose (this is what closes [#66](https://github.com/nguyendodary/DBCAS/issues/66), which stays **open**); then **B3** writable execution after owner security approval; then warm pool, state grading, frontend.
17. Owner actions still pending: U6/U7/U8/U10 substrate, issuer/rotation, image digest, limits, U18 required checks, local `dbcas-*` inventory, `docs/pending-readiness-edits` (do not merge as-is), OTP vs reset-link ([#25](https://github.com/nguyendodary/DBCAS/pull/25)). Remaining [owner decisions](../analysis/owner-decisions.md) items are **UNKNOWN — owner must confirm**.
18. **Final release (owner-gated):** handover docs and the local tag `arch-freeze-v1.2` are ready; the annotated `v1.0-final` tag and the `develop2 -> main` PR are still not created. After owner approval, push the branch and tag, open the PR, update the Word TOC fields in the four `.docx` files, and rehearse the demo once with `DBCAS_DEMO_PROFILE=writable,free-pro`. Production stays **HOLD**.
19. **Branch cleanup (2026-11-24):** `feat/broker-runtime` merged with fixes as `23d4d65`; `demo/rehearsal` and `docs/submission-final` recorded as `aceb0d0` and `e541495`; `feat/demo-seed-snapshot` was already an ancestor of `develop2`. All four branches were deleted locally and on `origin`, and the broker worktree was removed. No new feature, table, migration, route or flag work was introduced by the integration.

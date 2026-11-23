# Status snapshot

Date: 2026-11-23. Overwrite this snapshot when state changes; do not treat it as CI evidence.

Last verified: `develop2` [69e1e2f1273dc1870df71ad4f17936dfacdf5953](https://github.com/nguyendodary/DBCAS/commit/69e1e2f1273dc1870df71ad4f17936dfacdf5953) as of 2026-11-23; do not chase later SHAs. **Code freeze: no further feature work.** `main` [e7e432cefc2e21706ddfec96cfb8fa8b3b32b858](https://github.com/nguyendodary/DBCAS/commit/e7e432cefc2e21706ddfec96cfb8fa8b3b32b858), unchanged.

Production: **HOLD**; release prerequisites are in [BACKLOG](BACKLOG.md).

## Last done

- [#96](https://github.com/nguyendodary/DBCAS/pull/96): freeze decisions and bloat register â€” merge `598e409c02a8630778ab3db5dd89430e6d50fee8`.
- [#97](https://github.com/nguyendodary/DBCAS/pull/97): aligned demo runbook and README â€” merge `187c7e07f17363c02aa57b74c5580cdc796e6b07`.
- [#98](https://github.com/nguyendodary/DBCAS/pull/98): pytest moved to development requirements â€” merge `e742f245d1468bfe88ed6740c58f212606074812`.
- [#101](https://github.com/nguyendodary/DBCAS/pull/101): mapped `session_start_request.request_hash` in the ORM â€” merge `ad774362456d55580bd467e12ffd3f06efbacd28`.
- [#102](https://github.com/nguyendodary/DBCAS/pull/102): bulk-loaded locked adaptive questions â€” merge `c9dbd8f5ef9847748a04d49b9d093e77b6414b54`.
- [#103](https://github.com/nguyendodary/DBCAS/pull/103): deferred background media and shrank the hero assets â€” merge `94885c9a267bf1b6ec337be09d8e534715368ab4`.
- [#104](https://github.com/nguyendodary/DBCAS/pull/104): shared and validated demo Compose profile selection â€” merge `29a68ad873377587f41c1c47f6d112c8fb483324`.
- [#105](https://github.com/nguyendodary/DBCAS/pull/105): grading-job latency and status diagnostics â€” merge `69e1e2f1273dc1870df71ad4f17936dfacdf5953`.
- Final verification: full CI run `45124260745 (attempt 1)`, rerun `45124260745 (attempt 2)`, rerun `45124260745 (attempt 3)` on `69e1e2f1273dc1870df71ad4f17936dfacdf5953`.

## In progress and next

- Documents: Phase C in-place revision on `docs/revise-existing-in-place` head `d913b4dacdf6dfbcecf1b499c073a473b44124ce`; [#100](https://github.com/nguyendodary/DBCAS/pull/100) is open, CI-green, and **not merged** pending the owner's `OK merge #100`. Fact audit 94/94; `npm run docs:check` passes.
- Proposed annotated tag `v1.0-final` on the final freeze record (not created).
- Proposed `develop2 -> main` PR after Phase C (not created). `main` stays unchanged.

## Blockers and risks

- [#71](https://github.com/nguyendodary/DBCAS/issues/71): qa-1 `sandbox_busy` remains **UNKNOWN â€” owner must confirm**; diagnostics only.
- [#94](https://github.com/nguyendodary/DBCAS/issues/94): result-heading timeout remains **UNKNOWN â€” owner must confirm**; #105 adds job status/latency logging.
- [#55](https://github.com/nguyendodary/DBCAS/issues/55): Docker container-create timeouts; open.
- Broker [#80](https://github.com/nguyendodary/DBCAS/pull/80) is closed; `docker.sock` [#66](https://github.com/nguyendodary/DBCAS/issues/66) remains a known limitation; broker stays OFF.
- SQL-run rate limiting is **not implemented**; per-execution limits and two-slot admission remain the guard.
- Cold seed remains about three minutes; no safe in-seed parallelism was found without changing validation semantics.
- Owner decisions remain: DB release default `IMMEDIATE` vs API `HUMAN_VERIFIED`; duplicate `concept_dependency` DDL; OTP [#25](https://github.com/nguyendodary/DBCAS/pull/25); local `dbcas-*` inventory; production substrate and release gates.




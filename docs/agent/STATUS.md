# Status snapshot

Date: 2026-11-25. Overwrite this snapshot when state changes; do not treat it as CI evidence.

Baseline: `develop2` architecture-freeze work through `974b92b` (T1–T8), after the earlier integration pass at `e541495`; final freeze commit and verified results are recorded in [ARCHITECTURE_FREEZE.md](../ARCHITECTURE_FREEZE.md). **Architecture freeze: no new feature, table, migration, route or flag work after the accepted T1–T9 set** (code freeze [`69e1e2f`](https://github.com/nguyendodary/DBCAS/commit/69e1e2f1273dc1870df71ad4f17936dfacdf5953)); the integration only lands work already prepared on stale branches. Handover docs and the local tag `arch-freeze-v1.2` were added on 2026-11-25; nothing was pushed. `main` [e7e432cefc2e21706ddfec96cfb8fa8b3b32b858](https://github.com/nguyendodary/DBCAS/commit/e7e432cefc2e21706ddfec96cfb8fa8b3b32b858), unchanged.

Production: **HOLD**; release prerequisites are in [BACKLOG](BACKLOG.md).

## Last done

- Handover (2026-11-25): [release notes v1.1](../RELEASE_NOTES_v1.1.md), [submission summary](../submission-pack/SUMMARY.md), [demo checklist](../submission-pack/DEMO_CHECKLIST.md), README Windows Docker GID fallback, and [handover gates](freeze-logs/handover-gates.md); clean-clone `npm start` verified with fake keys; local tag `arch-freeze-v1.2` (not pushed). `main` unchanged.
- [#96](https://github.com/nguyendodary/DBCAS/pull/96): freeze decisions and bloat register — merge `598e409c02a8630778ab3db5dd89430e6d50fee8`.
- [#97](https://github.com/nguyendodary/DBCAS/pull/97): aligned demo runbook and README — merge `187c7e07f17363c02aa57b74c5580cdc796e6b07`.
- [#98](https://github.com/nguyendodary/DBCAS/pull/98): pytest moved to development requirements — merge `e742f245d1468bfe88ed6740c58f212606074812`.
- [#101](https://github.com/nguyendodary/DBCAS/pull/101): mapped `session_start_request.request_hash` in the ORM — merge `ad774362456d55580bd467e12ffd3f06efbacd28`.
- [#102](https://github.com/nguyendodary/DBCAS/pull/102): bulk-loaded locked adaptive questions — merge `c9dbd8f5ef9847748a04d49b9d093e77b6414b54`.
- [#103](https://github.com/nguyendodary/DBCAS/pull/103): deferred background media and shrank the hero assets — merge `94885c9a267bf1b6ec337be09d8e534715368ab4`.
- [#104](https://github.com/nguyendodary/DBCAS/pull/104): shared and validated demo Compose profile selection — merge `29a68ad873377587f41c1c47f6d112c8fb483324`.
- [#105](https://github.com/nguyendodary/DBCAS/pull/105): grading-job latency and status diagnostics — merge `69e1e2f1273dc1870df71ad4f17936dfacdf5953`.
- [#107](https://github.com/nguyendodary/DBCAS/pull/107): finalized the `.docx` toolkit, diagram checks and `docs/qa/**` write guard — merge `3bccbd6ac027fe26d9c05de1424c847766792d0c`; exact-commit CI [run `45165843463`](https://github.com/nguyendodary/DBCAS/actions/runs/45165843463) green.
- [#100](https://github.com/nguyendodary/DBCAS/pull/100): revised the submission documents in place (ERD 2 pages, TRD 11 pages / 67 cards, SRS 7 pages) — merge `aac18c915f50489b8512da8a24b2cf8488e64850`; exact-commit CI [run `45170482066`](https://github.com/nguyendodary/DBCAS/actions/runs/45170482066) green.
- [#108](https://github.com/nguyendodary/DBCAS/pull/108): final STATUS/BACKLOG snapshot — merge `14ffdead4942cfdff7f98eb38c2e173d10961556`; PR CI [run `45173141472`](https://github.com/nguyendodary/DBCAS/actions/runs/45173141472) green (docs-only jobs skipped).
- [#109](https://github.com/nguyendodary/DBCAS/pull/109): test-only capability-forgery fix — merge `333e8c4518c217eae1d1aaf65813bdb84b4e050b`; exact-commit CI [run `45188946962`](https://github.com/nguyendodary/DBCAS/actions/runs/45188946962) green, backend 1914.
- Earlier 3x on `14ffdead`: run [`45173345463`](https://github.com/nguyendodary/DBCAS/actions/runs/45173345463) attempts 1-2 green; attempt 3 failed in `test_capability_peer_identity_and_replay` because the old `xy` forgery changed only base64url padding bits (~1/1024). #109 makes the forgery deterministic; no production change.
- New 3x on `333e8c45`: run [`45192055379`](https://github.com/nguyendodary/DBCAS/actions/runs/45192055379) attempts 1-3 green; backend 1914, frontend 459, all browser shards green.
- Submission package: `Architecture.docx` (77 pages), `Database.docx` (70), `Proposal.docx` (60), `SRS.docx` (7); fact audit 94/94; style/cover audit unchanged.
- Branch integration (2026-11-24, owner request): `feat/broker-runtime` merged as `23d4d65`; `demo/rehearsal` and `docs/submission-final` recorded as `aceb0d0` and `e541495`; `feat/demo-seed-snapshot` was already an ancestor of `develop2`. All four branches were deleted locally and on `origin`, and the broker worktree was removed.
- Accepted freeze work T1–T8 (one commit each): `efb15e1` upload limit, `59a41df` i18n, `39f1d36` AI adaptive questions, `25ac1b3` AI candidates, `2b0641a` mixed AI types, `ac74ed1` mode UI, `3a16152` DML state grading, `974b92b` Free/Pro demo gating. T9 is documentation/freeze verification.
- Post-freeze owner-approved fixes: `27c3e14` ephemeral exec + writable job, `3aec0b8` grade-visibility test, `ab06d14` final all-green suite. Model trials are recorded in `freeze-logs/model-trials.md` (uncommitted running log).
- Owner-approved configuration change (2026-11-24): one generic `openai_compatible` LLM provider configured only by `LLM_API_KEY`/`LLM_BASE_URL`/`LLM_MODEL`; all `OPENROUTER_*` settings and OpenRouter-only guards/parameters removed, replaced by generic HTTPS + explicit-model release checks. `npm run llm:check` added. Details in `freeze-logs/llm-provider-notes.md`, `freeze-logs/llm-check-results.md` and section 7.2 of [ARCHITECTURE_FREEZE.md](../ARCHITECTURE_FREEZE.md).

## In progress and next

- Local freeze tags `arch-freeze-v1`, `arch-freeze-v1.1` and `arch-freeze-v1.2` exist; none is pushed. The annotated `v1.0-final` tag is still not created.
- `develop2 -> main` PR remains owner-gated and not created; `main` stays unchanged.
- Branch integration (2026-11-24, explicit owner request): `feat/broker-runtime` (#80) merged with fixes; the constrained runtime stays behind default-OFF `SANDBOX_BROKER`; the API keeps its existing Docker CLI/socket until a separately reviewed cutover, and B3 writable execution plus a standalone broker service remain future work. `demo/rehearsal` (#92), `feat/demo-seed-snapshot` (#89) and `docs/submission-final` (#99) were superseded by later `develop2` work (#90, #100, #111) and merged for history only.

## Blockers and risks

- [#71](https://github.com/nguyendodary/DBCAS/issues/71): qa-1 `sandbox_busy` remains **UNKNOWN — owner must confirm**; diagnostics only.
- [#94](https://github.com/nguyendodary/DBCAS/issues/94): result-heading timeout remains **UNKNOWN — owner must confirm**; #105 adds job status/latency logging.
- [#55](https://github.com/nguyendodary/DBCAS/issues/55): Docker container-create timeouts; open.
- Broker [#80](https://github.com/nguyendodary/DBCAS/pull/80) is merged but its flag stays OFF; the real-runtime gaps in [validation](../analysis/broker-validation.md) remain, and `docker.sock` [#66](https://github.com/nguyendodary/DBCAS/issues/66) is still a known limitation until the separately reviewed B2 cutover; writable execution through the broker is B3 and is not part of this merge.
- SQL-run rate limiting is **not implemented**; per-execution limits and two-slot admission remain the guard.
- Cold seed remains about three minutes; no safe in-seed parallelism was found without changing validation semantics.
- Free/Pro is **UI-only** (`VITE_DEMO_FREE_PRO=true` demo default, plan stored in `dbcas_demo_plan`); no backend payment route or migration. Free locks Mode 2; Pro unlocks it.
- No provider-level ZDR/logging approval for real data remains in the app (vendor-only flags removed); provider privacy is an operator decision. **Production stays HOLD**.
- Owner decisions remain: DB release default `IMMEDIATE` vs API `HUMAN_VERIFIED`; duplicate `concept_dependency` DDL; OTP [#25](https://github.com/nguyendodary/DBCAS/pull/25); local `dbcas-*` inventory; production substrate and release gates.

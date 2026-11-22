# Status snapshot

Date: 2026-11-22. Overwrite this snapshot when state changes; do not treat it as CI evidence.

Last verified: `develop2` [7fa2aa88e79e0a04ac07947f37ef380c7c98b5cf](https://github.com/nguyendodary/DBCAS/commit/7fa2aa88e79e0a04ac07947f37ef380c7c98b5cf) as of 2026-11-22; update after the next merge. `main` [e7e432cefc2e21706ddfec96cfb8fa8b3b32b858](https://github.com/nguyendodary/DBCAS/commit/e7e432cefc2e21706ddfec96cfb8fa8b3b32b858), unchanged.

Production: **HOLD**; release prerequisites are in [BACKLOG](BACKLOG.md).

## Last done

- [#60](https://github.com/nguyendodary/DBCAS/pull/60): retired withdrawn audit exception — merge `06dffe21231a515969eee8ccc04081fb9ff5aa4e`.
- [#61](https://github.com/nguyendodary/DBCAS/pull/61): pinned approved OpenRouter release routing — merge `2edc1dded5d654e9e6e3ca397d5e329bc3b480e1`.
- [#62](https://github.com/nguyendodary/DBCAS/pull/62): recover interrupted v2 regrade analysis — merge `955abd075928bc3c3d738a20cd942dfc7bb256c8`.
- [#63](https://github.com/nguyendodary/DBCAS/pull/63): collect demo-seed diagnostics — merge `5919ce2be21f130d2ccd6d989b4703411826817b`.
- [#64](https://github.com/nguyendodary/DBCAS/pull/64): SQL sandbox audit and design — merge `a43ff087087df3fe184970e20a211e8e9754b49c`.
- [#65](https://github.com/nguyendodary/DBCAS/pull/65): AST classification and opt-in read-only scripts — merge `ab5d9629ff5f2bed0325e72867b238343880f630`.
- [#68](https://github.com/nguyendodary/DBCAS/pull/68): agent knowledge base — merge `a42513509c52dd8818d191bb85688a97892c306b`.
- [#69](https://github.com/nguyendodary/DBCAS/pull/69): SQL sandbox executor broker design, merged as documentation only and **not owner-approved** — merge `10c29586b569d5fd8068cc477aef682dca113be9`.
- [#70](https://github.com/nguyendodary/DBCAS/pull/70): retry the Docker readiness probe — merge `06ac8a254265a9f539697d887d7fc58cca59dcc3`.
- [#72](https://github.com/nguyendodary/DBCAS/pull/72): refreshed STATUS and BACKLOG — merge `a343ab086a536aebe78e256af118c2a2e1975230`.
- [#73](https://github.com/nguyendodary/DBCAS/pull/73): refreshed STATUS and BACKLOG after #72 — merge `5ac5f7e89731a74957d895a2a1bd0f7645f97edc`.
- [#74](https://github.com/nguyendodary/DBCAS/pull/74): qa-1 `sandbox_busy` analysis and owner decision sheet — merge `117a89afe76daa49d5ddee51599682e08ab1cd5d`.
- [#75](https://github.com/nguyendodary/DBCAS/pull/75): qa-1 `sandbox_busy` rejection diagnostics — merge `9a882b10e42cd5ff8d141a21c80234a096eb44c7`.
- [#79](https://github.com/nguyendodary/DBCAS/pull/79): owner-approved defaults recorded — merge `9d3b1326384541fe9089d724f3ec49e8480ae89d`.
- [#76](https://github.com/nguyendodary/DBCAS/pull/76): default-off broker skeleton — merge `50f5724c2f01fa18131e0ec58bf68982c290f059`.
- [#78](https://github.com/nguyendodary/DBCAS/pull/78): PR-B2 design documentation — merge `ea9a29b1c0d22f10a55688ea1c0ffc1007071ec3`.
- [#82](https://github.com/nguyendodary/DBCAS/pull/82): broker CI validation record — merge `ccf992430b74ac1b1596e0bdee3fb217280d147c`.
- [#86](https://github.com/nguyendodary/DBCAS/pull/86): practice grid navigation, bank-list payload trimming and E2E — merge `7fa2aa88e79e0a04ac07947f37ef380c7c98b5cf`.

CI on `10c29586`: [run 44792968574 attempt 1](https://github.com/nguyendodary/DBCAS/actions/runs/44792968574/attempts/1) was red (qa-1 `sandbox_busy`, [#71](https://github.com/nguyendodary/DBCAS/issues/71)); the single authorized [attempt 2](https://github.com/nguyendodary/DBCAS/actions/runs/44792968574/attempts/2) was green (14/14).
CI on `a343ab0`: [run 44857868535](https://github.com/nguyendodary/DBCAS/actions/runs/44857868535) passed all jobs, including qa-1, qa-2 and qa-3.
CI on `5ac5f7e`: [run 44862121405](https://github.com/nguyendodary/DBCAS/actions/runs/44862121405) passed all jobs; backend 1870 passed, frontend 455/455.
CI on `117a89a`: [run 44864055440](https://github.com/nguyendodary/DBCAS/actions/runs/44864055440) passed all jobs.

## In progress and next

- Free/Pro and cost reporting: design in [free-pro-design](../analysis/free-pro-design.md) — **awaiting owner decisions** on plan names, price/free quota, demo vs real payment, report audience and retention.
- [#80](https://github.com/nguyendodary/DBCAS/pull/80): broker runtime behind default-OFF `SANDBOX_BROKER` (head `5807094`) — **OPEN, NOT MERGED**, awaiting two owner decisions: qa-1 `sandbox_busy`/503 policy and the p50 latency target. See [validation record](../analysis/broker-validation.md).
- Next: [BACKLOG](BACKLOG.md).

## Blockers and risks

- [#66](https://github.com/nguyendodary/DBCAS/issues/66): API mounts `docker.sock`; the broker design in [#69](https://github.com/nguyendodary/DBCAS/pull/69) is documentation only and not owner-approved, so writable execution remains blocked.
- [#67](https://github.com/nguyendodary/DBCAS/issues/67): Docker readiness timeout; fix merged in [#70](https://github.com/nguyendodary/DBCAS/pull/70), issue open for the owner to close after observing CI.
- [#71](https://github.com/nguyendodary/DBCAS/issues/71): qa-1 `sandbox_busy` under load — flaky, cause **UNKNOWN — owner must confirm**. Diagnostics collection plan: fix the #75 inventory drift, merge diagnostics, then read the `sandbox_busy rejection` fields described in [the analysis](../analysis/qa1-sandbox-busy.md) from the next failed qa-1 log.
- Owner actions pending: identify local `dbcas-*` containers and volumes; decide on local branch `docs/pending-readiness-edits`. The five B1 defaults were approved on 2026-11-21; all other items in [owner decisions](../analysis/owner-decisions.md) remain **UNKNOWN — owner must confirm**.
- [#55](https://github.com/nguyendodary/DBCAS/issues/55): Docker container-create timeouts; open.
- Local Docker/WSL verification was skipped by owner decision; local `dbcas-*` containers/volumes are unidentified and must not be touched.
- Production substrate, release gates and owners: **UNKNOWN — owner must confirm**; see [BACKLOG](BACKLOG.md).

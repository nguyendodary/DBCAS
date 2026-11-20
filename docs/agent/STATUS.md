# Status snapshot

Date: 2026-11-20. Overwrite this snapshot when state changes; do not treat it as CI evidence.

Last verified: `develop2` [ab5d9629ff5f2bed0325e72867b238343880f630](https://github.com/nguyendodary/DBCAS/commit/ab5d9629ff5f2bed0325e72867b238343880f630); `main` [e7e432cefc2e21706ddfec96cfb8fa8b3b32b858](https://github.com/nguyendodary/DBCAS/commit/e7e432cefc2e21706ddfec96cfb8fa8b3b32b858). These SHAs are **as of the base of this PR; update after merge**.

Production: **HOLD**; release prerequisites are in [BACKLOG](BACKLOG.md).

## Last done

- [#60](https://github.com/nguyendodary/DBCAS/pull/60): retired withdrawn audit exception — merge `06dffe21231a515969eee8ccc04081fb9ff5aa4e`.
- [#61](https://github.com/nguyendodary/DBCAS/pull/61): pinned approved OpenRouter release routing — merge `2edc1dded5d654e9e6e3ca397d5e329bc3b480e1`.
- [#62](https://github.com/nguyendodary/DBCAS/pull/62): recover interrupted v2 regrade analysis — merge `955abd075928bc3c3d738a20cd942dfc7bb256c8`.
- [#63](https://github.com/nguyendodary/DBCAS/pull/63): collect demo-seed diagnostics — merge `5919ce2be21f130d2ccd6d989b4703411826817b`.
- [#64](https://github.com/nguyendodary/DBCAS/pull/64): SQL sandbox audit and design — merge `a43ff087087df3fe184970e20a211e8e9754b49c`.
- [#65](https://github.com/nguyendodary/DBCAS/pull/65): AST classification and opt-in read-only scripts — merge `ab5d9629ff5f2bed0325e72867b238343880f630`.

## In progress and next

- Agent knowledge base [#68](https://github.com/nguyendodary/DBCAS/pull/68) (this PR).
- Broker PR-A [#69](https://github.com/nguyendodary/DBCAS/pull/69); readiness fix [#70](https://github.com/nguyendodary/DBCAS/pull/70).
- Next: [broker and readiness queue](BACKLOG.md); resolve [owner decisions](BACKLOG.md).

## Blockers and risks

- Demo-seed CI failure cause is undetermined; use [RUNBOOK](RUNBOOK.md) and [#63](https://github.com/nguyendodary/DBCAS/pull/63).
- API Docker socket access: [#66](https://github.com/nguyendodary/DBCAS/issues/66); Docker readiness timeout: [#67](https://github.com/nguyendodary/DBCAS/issues/67).
- Production substrate, release gates and owners: **UNKNOWN — owner must confirm**; see [BACKLOG](BACKLOG.md).

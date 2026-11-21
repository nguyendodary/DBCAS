# PR-B2 design: move ephemeral execution to the broker

**Status: DESIGN ONLY.** This document changes no code, flag, test, Compose file or CI workflow; production remains **HOLD**. It is based on `develop2` [`dbfaeb3`](https://github.com/nguyendodary/DBCAS/commit/dbfaeb3c21cc4c923ce9de24fdfb7e0850c93d03). The B1 skeleton is PR [#76](https://github.com/nguyendodary/DBCAS/pull/76) (head `9486c6e`), which is **open, not merged and not owner-approved**. Every statement that depends on an unapproved default is explicitly marked **ASSUMES owner approval of <default>**.

## 1. Scope and starting point

- B1 supplies a fixed-operation, capability-scoped, default-OFF skeleton with a stub runtime; it deliberately does **not** migrate execution ([owner-decisions.md](owner-decisions.md#L3-L9), [broker README](../sql-sandbox/broker/README.md#L163-L170)).
- Today ephemeral execution lives in the API process: `build_sandbox_runner()` returns `EphemeralSandboxRunner` when `SANDBOX_MODE=ephemeral` ([sandbox_runner.py](../../backend/app/services/sandbox_runner.py#L642-L646)), wired through `get_sandbox_runner()` ([deps.py](../../backend/app/deps.py#L89-L95)). The runner calls the Docker CLI via `subprocess.run` ([ephemeral_sandbox.py](../../backend/app/services/ephemeral_sandbox.py#L25), [ephemeral_sandbox.py](../../backend/app/services/ephemeral_sandbox.py#L64)).
- The API image copies the Docker CLI binary ([Dockerfile](../../backend/Dockerfile#L1-L3)) and local/DN Compose mount the daemon socket into init/app with a group id ([docker-compose.local.yml](../../docker-compose.local.yml#L72-L85), [docker-compose.dn.yml](../../docker-compose.dn.yml#L51-L82)). Release Compose has no socket mount ([broker README](../sql-sandbox/broker/README.md#L10-L17)).
- **ASSUMES owner approval of the B1 defaults in [owner-decisions.md](owner-decisions.md#L15-L19)**; without that approval B2 has no accepted contract to build on.

## 2. Step order — cutover that never leaves dev/CI broken

Each step is its own reviewable PR with exact-head CI evidence; no step removes a working path before its replacement is green.

1. **Baseline and gates:** record green backend/frontend/E2E on the pre-change commit and capture one `sandbox_busy rejection` log if #71 recurs ([STATUS](../agent/STATUS.md#L38-L44)); local Docker is unavailable so dev parity is proven in CI.
2. **Broker runtime alongside the API, flag OFF:** add a broker process/container that owns the runtime, with **no new `docker.sock` mount in this docs PR**. The runtime substrate is **UNKNOWN — owner must confirm** (sidecar socket vs rootless Podman/Docker; [broker README](../sql-sandbox/broker/README.md#L201-L205)). **ASSUMES owner approval of channel `unix` for local/CI and `mtls` for staging/production** ([owner-decisions.md](owner-decisions.md#L15)).
3. **Dual path:** with `SANDBOX_BROKER=false` the existing API CLI path stays byte-identical; with it ON, `EphemeralSandboxRunner` delegates create/run/destroy to the broker over the fixed RPC ([broker README](../sql-sandbox/broker/README.md#L102-L108)). The old path is retained through every intermediate CI run.
4. **CI-first enablement:** enable the flag only in the CI override/environment first, run the parity matrix (Windows/WSL dev parity documented in [RUNBOOK](../agent/RUNBOOK.md#L69-L72) and in CI), then keep dev default OFF. **ASSUMES owner approval of `BROKER_ENABLED=false`/`SANDBOX_BROKER=false`** ([owner-decisions.md](owner-decisions.md#L18)).
5. **Remove API privileges per stack, after green dual path:** separate PRs for `docker-compose.local.yml` and `docker-compose.dn.yml` remove the socket mounts and group_add from the **API/init services only**, then a separate image PR removes the Docker CLI from [backend/Dockerfile](../../backend/Dockerfile#L1-L3); never remove the broker's own runtime access in the same step ([broker README](../sql-sandbox/broker/README.md#L147-L155)).
6. **Release stack:** staging/production still have no socket mount ([broker README](../sql-sandbox/broker/README.md#L15)); production substrate and sign-off are **UNKNOWN — owner must confirm** and must not be assumed from local/DN ([owner-decisions.md](owner-decisions.md#L23-L25)).

## 3. Flag rollout and parity

- Default OFF everywhere; turn ON in CI/test first, then optionally in a controlled dev cohort, never in production without the owner decision ([owner-decisions.md](owner-decisions.md#L18), [STATUS](../agent/STATUS.md#L33)).
- Windows/WSL: the current CLI wrapper uses `wsl.exe -e docker` and generated-script byte/line-ending checks are required ([RUNBOOK](../agent/RUNBOOK.md#L69-L72), [ephemeral_sandbox.py](../../backend/app/services/ephemeral_sandbox.py#L25)). B2 must prove the same authorization, template, lifecycle and failure contract in local Windows/WSL and CI; differences need explicit parity tests and owner approval ([broker README](../sql-sandbox/broker/README.md#L64-L66)).
- Parity evidence = identical route inventory, identical `sandbox_busy` contract and identical audit redaction in both paths; the inventory generator is static AST only ([README note](../sql-sandbox/broker/README.md#L157-L177)).

## 4. Tests required before each cutover

- Container escape probes, cross-user lease isolation, resource abuse, no socket/CLI/capability left in API/init, reaper and crash recovery, dev/WSL and CI parity ([broker README](../sql-sandbox/broker/README.md#L165-L168)).
- Allow-list enforcement for image/limits/template and fail-closed startup validation (B1 contract tests already cover the schema shape in PR #76).
- Regression: backend, frontend and E2E suites stay green; keep 455/455 frontend and the backend count at or above the current baseline, citing exact-head logs ([STATUS](../agent/STATUS.md#L26-L28)).
- No test threshold, concurrency limit or CI workflow is weakened in this design.

## 5. #71 capacity findings the broker must handle

- The current executor has **two process-local slots** ([ephemeral_sandbox.py](../../backend/app/services/ephemeral_sandbox.py#L20-L21)) and the API runs **two Uvicorn workers**, giving four slots with no shared fairness; `sandbox_busy` is raised after a 5 s local acquire ([ephemeral_sandbox.py](../../backend/app/services/ephemeral_sandbox.py#L97-L99), [qa1 analysis](qa1-sandbox-busy.md#L15-L18)).
- Submit grading and maintenance grading share those slots ([qa1 analysis](qa1-sandbox-busy.md#L28-L32), [qa1 analysis](qa1-sandbox-busy.md#L138-L144)).
- Therefore B2 must provide **process-shared bounded admission** and **separate grading capacity**, not merely move the same semaphore behind an RPC ([qa1 analysis](qa1-sandbox-busy.md#L163-L174)). **ASSUMES owner approval of the process-shared admission option**; the exact queue size and deadlines remain **UNKNOWN — owner must confirm** ([owner-decisions.md](owner-decisions.md#L26-L28)).
- Before changing capacity, read the diagnostics merged in #75: `worker_pid`, `slot_count`, `available_slots`, `wait_ms`, `operation`, `active_holders{purpose,held_ms}` ([sandbox_diagnostics.py](../../backend/app/services/sandbox_diagnostics.py#L61-L75)) — group rejections by worker and holder purpose to decide whether skew or grading contention dominates ([qa1 analysis](qa1-sandbox-busy.md#L132-L154)). Do not raise the 2-slot default or loosen the test until that data exists ([qa1 analysis](qa1-sandbox-busy.md#L180-L182)).

## 6. Rollback

- Before privilege removal: set `SANDBOX_BROKER=false` to restore the byte-identical existing path ([owner-decisions.md](owner-decisions.md#L18)).
- After privilege removal: revert the cutover commits, stop new admission, drain/expire owned leases and remove only broker-owned executors; if no safe prior path exists, fail closed rather than restoring API socket access ([broker README](../sql-sandbox/broker/README.md#L179-L187)). Rollback must never reintroduce `docker.sock` to the API ([broker README](../sql-sandbox/broker/README.md#L183-L185)).

## 7. Risk register (design judgments; measurements are UNKNOWN)

| Risk | Mitigation / evidence needed |
| --- | --- |
| API or issuer compromised | Narrow capabilities and independent issuer; forged/replayed tests; residual blast radius is **UNKNOWN — owner must confirm** ([broker README](../sql-sandbox/broker/README.md#L189-L192)) |
| Broker/runtime escape | Fixed digest/template, least privilege, rootless/stronger runtime evaluation, escape probes and security review ([broker README](../sql-sandbox/broker/README.md#L192-L193)) |
| Cross-user state leakage | Opaque owned leases, no reuse of used executors, adversarial isolation tests ([broker README](../sql-sandbox/broker/README.md#L193-L194)) |
| Crash, orphan or partial create | Durable labels/state, watchdog and reaper; kill/restart and daemon-failure tests ([broker README](../sql-sandbox/broker/README.md#L194-L195)) |
| Exhaustion or queue starvation | Bounded resources, per-subject/global quotas and load tests; owner approves limits ([broker README](../sql-sandbox/broker/README.md#L195-L196)) |
| Platform drift | Contract and isolation tests in local Windows/WSL and CI; production substrate approval ([broker README](../sql-sandbox/broker/README.md#L197-L198)) |

## 8. UNKNOWNs for the owner (must be answered before implementation)

- Production execution substrate and security sign-off, including U6/U7/U10 and the #66 decision ([broker README](../sql-sandbox/broker/README.md#L201-L203)).
- Rootless runtime support, capability issuer, key rotation, approved image digest, limits and audit retention ([broker README](../sql-sandbox/broker/README.md#L204-L205)).
- Windows/WSL and CI parity, required checks, queue capacity, timeout budgets and performance targets ([broker README](../sql-sandbox/broker/README.md#L206-L207), [owner-decisions.md](owner-decisions.md#L26-L28)).
- Product/grading semantics U1–U5, U12, U13, U16; these block B3/B5, not B2 ([owner-decisions.md](owner-decisions.md#L29-L30)).
- Exact values behind B1 defaults: channel, TTL 300 s, peer `dbcas-api`, 30-day audit retention, and the `SANDBOX_BROKER` vs `BROKER_ENABLED` name ([owner-decisions.md](owner-decisions.md#L15-L19), [BACKLOG](../agent/BACKLOG.md#L7)).

## 9. Sections to read first

- [broker README](../sql-sandbox/broker/README.md#L110-L155) — executor policy, lifecycle and cutover conditions.
- [broker README](../sql-sandbox/broker/README.md#L157-L177) — B1–B6 plan and validation.
- [qa1 analysis](qa1-sandbox-busy.md#L156-L182) — capacity options and recommendation.
- [owner decisions](owner-decisions.md#L11-L19) — blocking B1 defaults that B2 inherits.

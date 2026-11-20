# Executor broker: design proposal for #66

**Status:** PR-A is design only; no broker, writable execution, deployment or flag
change is implemented here. Production remains HOLD. This proposal addresses the
design portion of [#66](https://github.com/nguyendodary/DBCAS/issues/66); the issue
remains open until its implementation and acceptance criteria are met.

## Current state and trust boundaries

At [base ab5d962](https://github.com/nguyendodary/DBCAS/commit/ab5d9629ff5f2bed0325e72867b238343880f630),
[backend/Dockerfile](../../../backend/Dockerfile) copies the Docker CLI into the API
image, whose process runs as UID 10001. [Local Compose](../../../docker-compose.local.yml)
mounts the daemon socket into both init and app and adds the configured Docker GID;
[DN Compose](../../../docker-compose.dn.yml) does likewise for init and backend.
[Release Compose](../../../docker-compose.release.yml) has no socket mount.
See the audit in [#66](https://github.com/nguyendodary/DBCAS/issues/66) and
[#65](https://github.com/nguyendodary/DBCAS/pull/65).

[EphemeralSandboxRunner](../../../backend/app/services/ephemeral_sandbox.py) calls
the Docker CLI to inspect an image label, create/start an executor, invoke the
trusted [JSON bridge](../../../backend/app/sandbox_job.py) with `docker exec -i`,
and inspect/remove its own labeled container. Its present template uses no network,
read-only root, UID 10001, all capabilities dropped, no-new-privileges, 256 MB,
1 CPU and 128 PIDs, with tmpfs and an in-container watchdog. These are current
settings, not proof of an escape-free boundary.

1. **Learner to API:** SQL and other learner input are untrusted. The existing
   classifier and runner constrain SQL; an API authentication or validation bug
   remains possible ([#65](https://github.com/nguyendodary/DBCAS/pull/65)).
2. **API to daemon today:** an attacker who compromises a socket-enabled API
   process can speak to the Docker daemon, create privileged or host-mounted
   containers and potentially control the daemon host. The non-root API UID does
   not remove daemon authority ([#66](https://github.com/nguyendodary/DBCAS/issues/66)).
3. **Student executor to host:** the current create arguments do not mount the
   socket and use `--network none`; a compromised executor can access its own
   process, local data and permitted resources and may attempt kernel/runtime
   escape or resource exhaustion. Containers share a kernel; host escape is a
   threat to test, not a demonstrated finding (current
   [executor](../../../backend/app/services/ephemeral_sandbox.py)).
4. **Proposed API to broker to runtime:** the broker is a privileged trust
   boundary. Compromise of the broker or of its runtime still threatens the host.
   A compromised API may submit any operation its own credentials authorize;
   a narrow RPC and quotas reduce that authority, not eliminate it.

## Options

The qualitative assessments below are design judgments, not measured guarantees;
actual latency, operations and cost are **UNKNOWN — owner must confirm**.
[PR #64's options](../03-options-and-recommendation.md) and
[measurements](../02-measurements.md) compare shared schemas and ephemeral containers.

| Option | Security | Latency | Operations | Windows / WSL dev parity | CI parity | Cost |
| --- | --- | --- | --- | --- | --- | --- |
| A. Fixed-operation broker + container runtime | Narrow application authority; broker/runtime remain privileged | RPC plus container startup; warm pool may help | Broker, identity, cleanup, quotas | UNKNOWN; prove on WSL | Requires same contract and escape tests | Additional service; UNKNOWN |
| B. Docker socket proxy with endpoint filters | Reduces endpoints but allowed create/exec parameters may still be too broad; not a semantic policy | Proxy hop | Proxy policy must track Docker API | UNKNOWN | Requires equivalent proxy setup | Additional proxy; UNKNOWN |
| C. Rootless Docker/Podman under broker | Additional host privilege reduction; kernel/runtime and broker risks remain | UNKNOWN | UID mapping, storage and runtime support | UNKNOWN | UNKNOWN | Integration/operations cost UNKNOWN |
| D. gVisor/Firecracker-style isolation | Potentially stronger executor boundary; does not replace broker authorization | Startup/compatibility UNKNOWN | Runtime, kernel and image compatibility | UNKNOWN | UNKNOWN | Resource and integration cost UNKNOWN |
| E. Database/schema per attempt, no container | Shared DB process/cluster increases cross-tenant and resource blast radius; per-DB isolation varies | Shared-schema baseline in [measurements](../02-measurements.md); other cases UNKNOWN | Roles, grants, cleanup, quotas | Fits existing PostgreSQL tooling; parity UNKNOWN | Needs isolation and recovery tests | Lower container overhead is a hypothesis |

**Recommendation:** A, with C as a preferred defense-in-depth substrate if proved
available, and evaluate D for the production threat model. B alone exposes a
general Docker-shaped interface rather than validating an entire operation.
E remains a development-only writable alternative under [the existing design](../03-options-and-recommendation.md),
not the staging/production writable boundary. Local development and CI must
exercise the same authorization, template, lifecycle and failure contract;
differences in transport/runtime require explicit parity tests and owner approval.

## Proposed protocol and authority

The API uses a local authenticated channel: mutually authenticated TLS with
short-lived service identities, or a Unix socket with checked peer credentials
when the platform supports it. An independent trusted issuer signs short-lived,
audience-bound capabilities with issuer, subject, permitted operation/mode,
dataset, expiry and unique request ID. The broker verifies both channel identity
and capability, prevents replay except exact idempotent retransmissions, and owns
lease-to-requester authorization. If the
API can mint arbitrary learner identities, those identities are not trustworthy
after API compromise; deployment must establish the issuer boundary or explicitly
accept that residual risk. Issuer, key rotation and socket support are owner decisions.

Illustrative request, not an implemented interface:

```json
{
  "version": 1, "operation": "run", "request_id": "<unique-id>",
  "dataset_id": "<approved-id>", "dataset_digest": "<immutable-digest>",
  "script": "<bounded-untrusted-sql>", "script_hash": "<digest>",
  "mode": "read_only", "limits": {"wall_ms": 5000}, "ttl_seconds": 45,
  "requester": "<pseudonymous-subject>", "capability": "<signed-capability>"
}
```

The broker verifies the digest of the bounded SQL payload, retrieves only the
approved dataset through a fixed trusted source, verifies its digest, clamps
requested limits to server policy, and rejects unknown fields, modes, expired
tokens and duplicate IDs with different payloads. It never accepts an image, Docker command, environment,
host path, mount, network, privileged option or arbitrary URL from the API.
Errors and results are bounded and sanitized; no daemon response is forwarded raw.
The precise capability format and trusted dataset access are **UNKNOWN — owner
must confirm**.

Expose only fixed `create`, `run`/exec, `inspect` and `destroy` operations on
broker-owned opaque leases. Each operation checks the lease, subject, capability,
deadline and state. Retries use the same idempotency ID: duplicate creates return
the existing lease or a definite conflict, and destroy is idempotent. A timeout
does not imply the runtime did nothing; the broker reconciles by labels.
No caller can operate on another caller's lease. The broker never exposes raw
Docker API access.

## Executor policy and lifecycle

- The broker alone selects an immutable, allow-listed executor image digest with
  protocol label `com.dbcas.sandbox-protocol=1`, a fixed entrypoint, fixed tmpfs
  mounts and no host binds or socket. The label is an additional check, not a
  substitute for the digest.
- Proposed maximum template: `--network none`, read-only root filesystem, UID
  10001:10001, `--cap-drop ALL`, `no-new-privileges`, 512 MB memory, 1 CPU
  and 128 PIDs. The current 256 MB limit is documented above; 512 MB is a
  proposed ceiling pending [U15](../07-unknowns.md), benchmark and approval.
- The broker validates read-only/writable policy independently of caller input;
  writable attempts use isolated ephemeral execution, schema/role restrictions,
  a bounded transaction and cleanup as proposed in [target design](../04-target-design.md).
  Trusted verifier access is distinct from learner SQL.
- A broker-owned watchdog enforces TTL and operation deadlines; an independent
  startup and periodic reaper inspects broker ownership labels, reconciles durable
  lease state, and removes expired/orphaned executors. It must not remove foreign
  containers. Runtime unavailability raises an alert and keeps leases non-reusable.
- Broker admission uses a bounded global queue, per-subject quotas and a bounded
  pool; reject or time out explicitly when full. Queue wait, operation and total
  lifetime have independent deadlines. Exact queue size and timeouts are
  **UNKNOWN — owner must confirm** after load tests; a request cannot extend TTL.
- Warm executors and templates are broker-owned. Never transfer a used instance
  to another learner; destroy it, including on failed cleanup. Warm-pool isolation,
  reset semantics and capacity require dedicated tests before enabling.
- Audit records include correlation ID, pseudonymous requester, dataset/digest,
  operation/mode, policy version, timing and result class. Do not log SQL,
  credentials or raw data by default; retention is an owner decision
  ([U14](../07-unknowns.md)).

On invalid auth, policy, protocol or dataset, fail closed. On queue exhaustion
return a bounded busy response. On crash, timeout, cancellation or partial create,
return a sanitized unavailable result and reconcile; never reuse uncertain state.
If the daemon, identity verifier, audit sink or reaper is unavailable, stop
admitting new writable work; alert operators. Define durable audit buffering and
recovery before rollout, without silently losing security events.

After cutover, remove the Docker CLI from the API image and socket mounts and
daemon group access from API/init services in every stack; verify effective
capabilities as well as file configuration. Do not restore direct API access as
a fallback. `SANDBOX_MODE=ephemeral` selects the broker-backed path after
cutover; `SANDBOX_MULTI_STATEMENT`, `SANDBOX_WRITABLE` and `GRADING_STATE_MODE`
remain OFF by default. A release writable request additionally requires ephemeral
mode, security review and explicit owner approval. The current configuration guard
alone is not broker approval ([configuration](../../../backend/app/config.py),
[#65](https://github.com/nguyendodary/DBCAS/pull/65)).

## Migration and validation

Each PR is separately reviewable, disabled by default where applicable, and must
record exact commit, command, logs, runtime and test results. Synthetic data only.
No PR below authorizes staging/production rollout.

| PR | Scope | Required tests before review |
| --- | --- | --- |
| B1 | Broker skeleton behind a flag; fixed schema/auth, no executor migration | Invalid/expired/replayed capability, peer identity, schema/limits rejection, quota and timeout tests; existing path unchanged |
| B2 | Move existing ephemeral execution and cleanup to broker; remove API CLI/socket access at cutover | Container escape probes, cross-user lease isolation, resource abuse, no socket/CLI/capability in API/init, reaper and crash recovery; dev/WSL and CI parity |
| B3 | Opt-in writable ephemeral mode after security approval | AST and role bypass probes, rollback/cleanup, resource exhaustion, cross-user isolation, failure and crash recovery |
| B4 | Broker-owned warm pool | Cross-user residue, stale leases, pool exhaustion, reaper/restart and no reuse after uncertainty |
| B5 | State grading and trusted verifier | Tamper/isolation probes, result vs state semantics, transactional rollback, verifier boundary and recovery |
| B6 | Frontend | Feature-off compatibility, enabled UI/error states, accessibility and end-to-end isolation |

Every implementation PR runs the affected security tests plus backend, frontend
and E2E regressions. [#65](https://github.com/nguyendodary/DBCAS/pull/65)
reports 1,867 backend and 455 frontend tests on its local work; these are historical
comparison points, not results for future commits. The E2E suite and its CI shards
are defined in the [workflow](../../../.github/workflows/dn-backend.yml). Record
actual counts and exact-head logs; do not assume they pass.

## Rollback and risks

Disable the new feature flags, stop new broker admission, drain or expire active
leases, reconcile and remove only broker-owned executors, and return to the
previous approved read-only shared path where available. A rollback must not
reintroduce socket access to API/init; if no safe prior path exists, fail closed.
Validate this with synthetic data, recovery tests and a documented operator
rehearsal before any rollout. Data/schema rollback for future migrations needs
its own approved plan; this design adds none.

| Risk | Mitigation / evidence needed |
| --- | --- |
| API or token issuer compromised | Narrow scoped capabilities, independent issuer and quotas; test forged/replayed requests and residual blast radius |
| Broker/runtime escape | Fixed digest/template, least privilege, evaluate rootless/stronger runtime, escape probes and security review |
| Cross-user state leakage | Opaque owned leases, no reuse of used executors, adversarial isolation tests |
| Crash, orphan or partial create | Durable labels/state, watchdog and reaper; kill/restart and daemon failure tests |
| Exhaustion or queue starvation | Bounded resources, per-subject/global quotas and load tests; owner approves limits |
| Audit or key service unavailable | Fail closed for writable work, alert, tested recovery and rotation |
| Platform drift | Contract and isolation tests in local Windows/WSL and CI; production substrate approval |

## Owner decisions

- **UNKNOWN — owner must confirm:** production execution substrate and security
  sign-off, including U6/U7/U10 and the broker decision in
  [#66](https://github.com/nguyendodary/DBCAS/issues/66).
- **UNKNOWN — owner must confirm:** rootless runtime support, identity issuer,
  key rotation, approved image digest, limits and audit retention.
- **UNKNOWN — owner must confirm:** Windows/WSL and CI parity, required checks,
  queue capacity, timeout budgets and performance targets.
- **UNKNOWN — owner must confirm:** product and grading semantics in
  [the existing unknowns](../07-unknowns.md).

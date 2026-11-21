# QA-1 `sandbox_busy`: analysis of issue #71

**Status:** analysis only, as of 2026-11-21. This document changes no code, test,
limit, flag or CI configuration; production remains **HOLD**. It examines
`develop2` at [`a343ab0`](https://github.com/nguyendodary/DBCAS/commit/a343ab086a536aebe78e256af118c2a2e1975230).
The sandbox, grading, worker, route and load-test files cited below are identical
to the failing commit [`10c2958`](https://github.com/nguyendodary/DBCAS/commit/10c29586b569d5fd8068cc477aef682dca113be9)
and to the earlier [`ab5d962`](https://github.com/nguyendodary/DBCAS/commit/ab5d9629ff5f2bed0325e72867b238343880f630)
(`git diff --stat` is empty for those paths between each pair).

## Short answer

- The 503 is deliberate bounded backpressure: the route maps any `SandboxError`
  to HTTP 503 with the error code, including `sandbox_busy` ([practice.py](../../backend/app/routers/practice.py#L182-L183)).
- Capacity is a **two-slot semaphore local to each Python process**
  ([ephemeral_sandbox.py](../../backend/app/services/ephemeral_sandbox.py#L19)).
  The API image runs **two Uvicorn workers** ([Dockerfile](../../backend/Dockerfile#L14)),
  so the container has at most four slots, but no shared fairness between them.
- Every `/sql-run` creates, starts, readiness-checks, executes in and removes a
  container. The slot is held for that whole span ([ephemeral_sandbox.py](../../backend/app/services/ephemeral_sandbox.py#L84-L114),
  [execute](../../backend/app/services/ephemeral_sandbox.py#L150-L165)) and is
  released only in cleanup ([ephemeral_sandbox.py](../../backend/app/services/ephemeral_sandbox.py#L69-L82)).
- The QA load permits four concurrent SQL runs ([practice_load.py](../../backend/tests/practice_load.py#L157)).
  Each learner owns a separate HTTP client ([practice_load.py](../../backend/tests/practice_load.py#L119-L124)),
  so the operating system can place several of the four concurrent connections
  on the same Uvicorn worker. A four-request burst on one worker is two requests
  beyond its two slots.
- SQL grading on submit also uses those same slots: `submit()` calls
  `grade_attempt()` synchronously ([assessment_lifecycle.py](../../backend/app/services/assessment_lifecycle.py#L166-L175)),
  and SQL grading provisions, executes and drops one container per dataset,
  sequentially ([sql_grading.py](../../backend/app/services/sql_grading.py#L46-L52),
  [#L81-L83](../../backend/app/services/sql_grading.py#L81-L83)).
- The exact request rejected in the failing run cannot be identified from the
  logs: neither Uvicorn worker identity nor slot-wait time is recorded. Root
  cause therefore remains **UNKNOWN — owner must confirm** the discriminating
  observation in "Hypotheses" below. The mechanism is consistent with local
  admission skew and grading interference; it is not evidence of a production
  incident.

## Observed evidence

| Run | Commit | qa-1 result | `concurrent_sql`: attempts / success / 503 | p50 / p95 (ms) | Peak in flight |
| --- | --- | --- | --- | --- | --- |
| [#65 merge, run 44750054203](https://github.com/nguyendodary/DBCAS/actions/runs/44750054203) | `ab5d962` | success | 8 / 8 / 0 | 3135.52 / 6358.04 | 4 |
| [#69 merge, run 44792968574 attempt 1](https://github.com/nguyendodary/DBCAS/actions/runs/44792968574/attempts/1) | `10c2958` | **failure** | 10 samples: 7 / 3 | 5050.84 / 7291.09 | 4 |
| [#69 merge, run 44792968574 attempt 2](https://github.com/nguyendodary/DBCAS/actions/runs/44792968574/attempts/2) | `10c2958` | success | 8 / 8 / 0 | 2581.76 / 5663.34 | 4 |
| [#72 merge, run 44857868535](https://github.com/nguyendodary/DBCAS/actions/runs/44857868535) | `a343ab0` | success | 8 / 8 / 0 | 5774.24 / 7099.21 | 4 |

The failing attempt is the qa-1 job [136485291299](https://github.com/nguyendodary/DBCAS/actions/runs/44792968574/job/136485291299);
attempt 2 is [136676896504](https://github.com/nguyendodary/DBCAS/actions/runs/44792968574/job/136676896504);
the #65 and #72 jobs are [136335460256](https://github.com/nguyendodary/DBCAS/actions/runs/44750054203/job/136335460256)
and [136704274001](https://github.com/nguyendodary/DBCAS/actions/runs/44857868535/job/136704274001).
Values are the load report's phase samples, which include retries; percentiles
are calculated per HTTP sample, not per logical request ([release_load.py](../../backend/tests/release_load.py#L19-L23)).

Details of the failing attempt:

- The same job reported 18/18 browser tests passed; the subsequent load phase
  failed with `concurrent_sql: HTTP 503 (sandbox_busy)` and exited 1.
- The phase recorded three 503 samples under a client policy that allows three
  attempts with 0.25 s and 0.5 s sleeps ([practice_load.py](../../backend/tests/practice_load.py#L80-L89)),
  so at least one logical SQL request was rejected on every attempt. The report
  does not say which learner or connection.
- A fourth 503 occurred in the `sql_row_limit` measurement; its one allowed
  retry succeeded, and it did not cause the job failure. The #72 run likewise
  had one retried `sql_timeout` 503. Backpressure is not unique to the
  `concurrent_sql` assertion.
- During the final load window, the memory artifact samples three SQL executor
  containers at 18:39:06.959Z and again at 18:39:15.377Z; the API container is
  about 614–625 MiB and each executor about 52–99 MiB of its 256 MiB limit
  ([artifact 14657913864](https://github.com/nguyendodary/DBCAS/actions/runs/44792968574/artifacts/14657913864)).
  That is at least three of the four cluster-wide slots in use, but it does not
  reveal their worker distribution.
- The Docker-events artifact stops before the final burst: its last SQL event is
  at 18:37:38 and its last event at 18:38:47
  ([artifact 14657868981](https://github.com/nguyendodary/DBCAS/actions/runs/44792968574/artifacts/14657868981)).
  Its container lifetimes of 2.2–3.1 s describe earlier phases, not the failed
  interval. Host CPU and Docker-daemon state at failure are **UNKNOWN — owner
  must confirm**.

The failing attempt was also slower in non-SQL phases: login p50 620.67 ms versus
466.72 ms on attempt 2 and 477.78 ms on #72; `duplicate_start` p50 2355.26 ms
versus 1214.32 ms and 1782.22 ms. That correlates with general runner/daemon
slowness, but #72 was green with a higher `concurrent_sql` p50 (5774.24 ms), so
slowness alone does not decide the outcome.

## Request path and capacity

Ephemeral mode is selected by `SANDBOX_MODE: ephemeral` in local Compose
([docker-compose.local.yml](../../docker-compose.local.yml#L38)); QA uses that
stack. The route provisions a dataset, executes the learner SQL, and always
drops the dataset ([practice.py](../../backend/app/routers/practice.py#L178-L183)).
`provision_dataset()` calls `_create()`, which acquires `_SLOTS` with a
**five-second timeout** and raises `sandbox_busy` when it expires
([ephemeral_sandbox.py](../../backend/app/services/ephemeral_sandbox.py#L84-L87)).
The slot is released in `_cleanup()`, including when create/start/readiness
fails ([ephemeral_sandbox.py](../../backend/app/services/ephemeral_sandbox.py#L106-L114)).

`_SLOTS` is module-level state, so each Uvicorn worker has its own two slots; a
release in one worker cannot admit a waiter in the other. The two grading paths
also consume these slots:

- A SQL submission grades synchronously in the request thread. It provisions
  and drops a container per dataset ([sql_grading.py](../../backend/app/services/sql_grading.py#L46-L52)).
  If admission fails, `submit()` stores the answer as pending and enqueues a job
  instead of failing the request ([assessment_lifecycle.py](../../backend/app/services/assessment_lifecycle.py#L166-L175)).
- Each worker's lifespan starts a maintenance thread ([main.py](../../backend/app/main.py#L31-L35)).
  That thread processes up to ten grading jobs per tick, then waits five seconds
  ([worker.py](../../backend/app/worker.py#L38-L40), [worker.py](../../backend/app/worker.py#L49-L56),
  [config.py](../../backend/app/config.py#L140)). A SQL job takes one slot
  non-blockingly for the whole job; if no slot is free it rolls back and leaves
  the job queued ([grading_jobs.py](../../backend/app/services/grading_jobs.py#L22-L27)).
  It cannot itself raise `sandbox_busy`, but it can hold a slot while a run request
  waits.

Why a four-request burst can exceed five seconds on one worker: with two local
slots and an observed container cycle of roughly 2.2–3.1 s, the second queued
request can wait almost two cycles. A burst of four on one worker can therefore
need about 6 s for its last request, beyond the 5 s admission timeout. The
failure's `concurrent_sql` p50 of 5050.84 ms sits at that timeout, which is
consistent with admission wait dominating the sample; it is not proof, because
the report aggregates successes and 503s together.

The load's client design makes an uneven burst possible: every learner creates
its own `httpx.AsyncClient` ([practice_load.py](../../backend/tests/practice_load.py#L119-L124)),
so each learner's requests use that client's connection, and the application
does not redistribute a request to the other worker. Exact connection-to-worker
assignment is **UNKNOWN — owner must confirm**.

## Hypotheses, ranked

1. **Local admission skew and starvation (most consistent).** Four concurrent
   connections can put more than two requests on one worker. Two run, the rest
   wait; with ~3 s cycles the last waiter reaches or passes the 5 s timeout, and
   a retry can land behind a fresh pair. Discriminating observation: log the
   Uvicorn worker PID and slot-wait milliseconds for each `/sql-run`, then check
   whether 503s cluster on one PID while its two slots are continuously held.
2. **Grading shares the same slots (also plausible).** Synchronous submit
   grading and the per-worker maintenance thread can hold a worker's slots while
   other learners run SQL. The failing attempt's `duplicate_submission` p95 is
   10662.7 ms, versus 8089.3 ms on attempt 2 and 7368.96 ms on #65, which is
   consistent with grading waits but not conclusive. Discriminating observation:
   tag each lease/container as `run` or `grade` and measure overlap; repeat with
   grading forced to a separate capacity.
3. **Host or Docker-daemon contention (cannot exclude).** The whole failing
   attempt was slower, and each container start and readiness check adds to slot
   occupancy. Discriminating observation: per-operation timings for create,
   start, `pg_isready`, exec and remove, plus runner CPU/load and daemon
   statistics. No such data was retained for the failed interval.
4. **Slot-accounting defect or leak (no evidence).** Code review shows release in
   `_cleanup()`'s `finally`, and `_create()` calls `_cleanup()` on any failure,
   so a leak is not apparent. Discriminating observation: count acquire/release
   pairs and expose the semaphore value; a `BoundedSemaphore` over-release would
   also raise rather than pass silently.

## Options and recommendation

No option is implemented here.

- **Instrument first (recommended).** Record worker PID, purpose, slot-wait ms
  and outcome on every admission. This distinguishes hypotheses 1 and 2 without
  changing limits or expectations.
- **Process-shared admission.** Replace the per-worker semaphore with a global
  bounded queue (file/DB lock or the broker in [#66](https://github.com/nguyendodary/DBCAS/issues/66)).
  This removes cross-worker unfairness but adds a shared failure point and needs
  the broker decisions in [owner-decisions.md](owner-decisions.md).
- **Increase slots or timeout.** Only after measuring host headroom and the
  product latency target; more 256 MiB / 1 CPU containers increase daemon and
  host load, and a longer timeout increases worst-case response time. Production
  limits and peak concurrency are **UNKNOWN — owner must confirm**
  ([U9/U15](../sql-sandbox/07-unknowns.md#deployment-and-operations)).
- **Separate grading capacity.** Give grading its own slot pool or always enqueue
  SQL grading, so submit-time grading cannot starve interactive runs. This
  changes product latency semantics and needs owner approval.
- **Loosen the test.** Treating a bounded 503 as acceptable would hide the
  capacity signal. If the product accepts backpressure for `concurrent_sql`,
  the assertion and retry policy need an explicit owner decision, not a silent
  test edit.

Recommendation: instrument and reproduce first; then choose process-shared
admission or separated grading capacity. Do not raise limits or weaken the test
until the worker/slot-wait data identifies which capacity is actually exhausted.
Issue [#71](https://github.com/nguyendodary/DBCAS/issues/71) remains open.

## Not claimed

- No production occurrence, impact or SLA is asserted; no production system was
  accessed.
- No memory exhaustion is claimed: the samples show ample host memory, although
  host CPU and daemon load are unknown.
- No learner-specific or worker-specific rejection is identified; the aggregate
  report cannot support that claim.
- No change to `docs/qa/**`, `docs/pending-readiness-edits`, issue state, flags
  or CI is made by this analysis.

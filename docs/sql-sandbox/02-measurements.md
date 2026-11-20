# 02 — Measurements

All numbers below were measured in this audit on **local synthetic data**.
No production system or real student data was accessed.

## 0. Environment and caveats

- Host: Windows, repository at `C:\Users\kudot\Downloads\proposal test\DBCAS`.
- Docker: WSL2 backend, reached with `wsl.exe -e docker` because the Windows
  Docker CLI points at an unreachable `127.0.0.1:2375`.
- Local stack: `dbcas-local-*` (Compose project `dbcas-local`), plus the older
  `dbcas-db` / `dbcas-sandbox` / `dbcas-mailpit` containers.
- The local containers were restarting every few minutes during the audit
  (observed `Up 6 seconds` with `Created 6 days ago`). Each measurement was
  repeated; the tables report the distribution, not a single sample. Treat
  these as **indicative local numbers**, not SLAs.
- "p50/p95" use linear interpolation over sorted samples.

## 1. Application database query latency

Method: a psycopg 3.3.6 script executed inside `dbcas-local-app-1` against
`DATABASE_URL` (`dbcas-local-db-1`, 5,560 questions, 880 attempts, 242
sessions, 3,494 SQL datasets). Three warm-up executions, then `N=30` per query.
The connection is reused; `statement_timeout=3000`.

| Query | N | min ms | p50 ms | p95 ms | max ms | mean ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `SELECT count(*) FROM question` | 30 | 0.447 | 0.486 | 0.581 | 0.804 | 0.505 |
| concept/question join + `GROUP BY` + `LIMIT 10` | 30 | 1.189 | 1.365 | 1.640 | 1.979 | 1.377 |
| `row_number() OVER (PARTITION BY question_type …)` + `LIMIT 50` | 30 | 3.584 | 4.369 | 5.150 | 5.982 | 4.371 |
| `attempt` ⋈ `assessment_session` + `LIMIT 50` | 30 | 0.201 | 0.248 | 0.363 | 0.838 | 0.273 |
| **connect + `SELECT 1` + close** | 30 | 7.284 | 7.645 | 8.802 | 9.937 | 7.833 |

Interpretation: the app DB is not the bottleneck for the sandbox feature. A
new connection costs about 7.6 ms p50 locally; query execution is sub-5 ms for
the shapes above.

## 2. Sandbox database query latency

Method: `psql -X -q -A -t` inside `dbcas-sandbox` with `\timing on`; 30
executions of each query after a warm-up. These are server-side execution
times, not client round trips.

| Query | N | min ms | p50 ms | p95 ms | max ms | mean ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `count/sum/avg` over `generate_series(1,10000)` | 30 | 1.084 | 1.244 | 1.679 | 2.588 | 1.333 |
| `g % 100` group + order + `LIMIT 20` over 20,000 rows | 30 | 3.256 | 3.570 | 4.562 | 8.170 | 3.830 |

## 3. Shared runner: provision + execute + drop

Method: a script executed inside a throwaway `dbcas-sql-ephemeral:local`
container attached to `dbcas_sandbox-net`, using the real `SandboxRunner` and
the real `dbcas-sandbox` server. Setup creates a 3-row `sales` table; the
learner query is a `GROUP BY`. `N=12`; each iteration provisions a fresh
schema, executes, then drops it.

| Phase | N | min ms | p50 ms | p95 ms | max ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| provision + execute + drop | 12 | 53.84 | **56.54** | 109.71 | 144.81 |
| execute only | 12 | 17.60 | **19.92** | 25.51 | 27.28 |

Interpretation: the shared path is cheap. The cost is dominated by schema
provisioning and connection setup, not by the query.

## 4. Ephemeral runner: container per dataset

Method: the real `EphemeralSandboxRunner` inside `dbcas-local-app-1`, three
iterations, same 3-row `sales` setup and `GROUP BY` query. Each iteration
creates a container, provisions the dataset, executes, and drops the lease.

| Iteration | provision ms | execute ms | drop ms | total ms | success |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 2,207.2 | 449.6 | 197.1 | **2,853.8** | yes |
| 1 | 1,894.4 | 435.9 | 193.5 | **2,523.8** | yes |
| 2 | 1,695.7 | 422.4 | 162.6 | **2,280.7** | yes |

Interpretation: ephemeral isolation costs roughly **2.3–2.9 s per dataset**,
mostly container start and `pg_isready` polling (`ephemeral_sandbox.py:83-114`).
This is acceptable for submit-time grading but noticeable for an interactive
"Run" button. A warm pool or per-attempt container reuse is the obvious
optimization; it is not implemented today.

## 5. Service startup

Warm start (existing volumes, container restart):

| Service | Evidence | Approximate ready time |
| --- | --- | --- |
| `dbcas-db` | `StartedAt 2026-11-20T10:39:05.449Z`; ready log `10:39:06.190Z` | **0.74 s** |
| `dbcas-sandbox` | `StartedAt 2026-11-20T10:39:05.437Z`; ready log `10:39:06.142Z` | **0.71 s** |
| `dbcas-local-app-1` | startup log `10:37:00.966` → application ready `10:37:04.5` | **~3.5 s** |
| `dbcas-local-app-1` (second restart) | `10:37:54.5` → `10:37:59.47` | **~5.0 s** |
| `dbcas-local-frontend-1` | nginx "ready for start up" → worker start | **< 0.2 s** after entrypoint |
| `dbcas-local-mailpit-1` | mailpit start logs | **< 0.2 s** |

Cold start (first initialization of a volume):

| Service | Evidence | Approximate time |
| --- | --- | --- |
| `dbcas-local-db-1` | initdb start `2026-11-09T16:18:22.93Z` → ready `16:18:23.85Z` | **~0.9 s** (initdb only; schema/seed run separately) |
| `dbcas-sandbox` | first boot `2026-10-03T13:29:08.156Z` → ready `13:29:09.369Z` | **~1.2 s**, including the learner-role init script (`13:29:09.169` → `13:29:09.327`) |
| `dbcas-local-app-1` | first start `2026-11-14T00:39:33.97Z` → two workers ready `00:39:36.73Z` | **~2.8 s** after Uvicorn starts |
| `dbcas-local-frontend-1` | first start `2026-11-14T00:39:39.61Z` → nginx worker `00:39:39.73Z` | **~0.12 s** |

The expensive cold start is the **init/seed** service, not the servers.

## 6. Seed / init time

CI artifacts from `dn-backend.yml` smoke shards:

| Run | Artifact | Init start | Init finish | Duration | Result |
| --- | --- | --- | --- | ---: | --- |
| `44706644787` (`955abd0`) | `seed-init-smoke-1/init-state.json` | `2026-11-20T08:59:02.161Z` | `2026-11-20T09:01:26.182Z` | **144.0 s** | exit 0 |
| `44701525065` (`5919ce2`) | `seed-init-smoke-1/init-state.json` | `2026-11-20T08:20:40.618Z` | `2026-11-20T08:22:42.537Z` | **121.9 s** | exit 0 |

Local `dbcas-local-init-1` on 2026-11-14 ran `00:39:27.76` → `00:39:32.80`
(**5.0 s**) but logged "Existing local data preserved", so it did not seed.

`backend/app/seed_demo.py` creates 4 history sessions × 13 questions and runs
SQL through the sandbox; that explains the ~2-minute cold seed. This cost is
paid **per CI shard** (see §10).

## 7. Container memory

`docker stats --no-stream` during the audit:

| Container | Memory | Limit | PIDs |
| --- | ---: | ---: | ---: |
| `dbcas-local-frontend-1` | 9.97–10.88 MiB | 7.755 GiB | 9 |
| `dbcas-local-app-1` | 241–257.5 MiB | 7.755 GiB | 10 |
| `dbcas-local-db-1` | 51.3–57.0 MiB | 7.755 GiB | 8 |
| `dbcas-local-mailpit-1` | 5.0 MiB | 128 MiB | 9 |
| `dbcas-mailpit` | 16.7–17.0 MiB | 7.755 GiB | 9 |
| `dbcas-sandbox` | 24.7–26.4 MiB | 256 MiB | 6 |
| `dbcas-db` | 27.9–31.1 MiB | 7.755 GiB | 6 |

The sandbox's 256 MB limit is comfortable for SELECT workloads. Writable DDL/DML
with larger intermediate results needs a higher limit or strict row/byte caps;
see `04-target-design.md` §8.

## 8. Image sizes

`docker images` on the audit host:

| Image | Size |
| --- | ---: |
| `dbcas-sql-ephemeral:local` (executor) | **899 MB** |
| `dbcas-local-api:local` (API) | **423 MB** |
| `dbcas-local-web:local` / frontend images | **129 MB** |
| `postgres:17` base | pulled separately; the executor adds Python, venv, and app code |

The API image contains a **44.3 MB** Docker CLI binary
(`/usr/local/bin/docker`, measured inside the image) and **129 MB** of Python
site-packages. The executor adds a full Python venv on top of `postgres:17`.

## 9. Frontend bundle and first load

`frontend/dist` build output (not tracked by git; generated by Vite):

| Metric | Value |
| --- | ---: |
| Files in `dist` | 41 |
| Total size | **17,756 KB (17.3 MiB)** |
| JS files / raw / gzip | 21 / **954.2 KB** / **296.8 KB** |
| CSS files / raw / gzip | 1 / **126.5 KB** / **26.8 KB** |
| Entry JS `index-*.js` | **316.7 KB** raw / **94.5 KB** gzip |
| Shared UI `ui-*.js` | **280.4 KB** raw / **89.3 KB** gzip |
| Largest route chunk `CompetencyCharts-*.js` | 181.2 KB raw / 62.3 KB gzip |

Largest media assets in `frontend/dist/assets` (copied from
`frontend/src/assets`):

| Asset | Size |
| --- | ---: |
| `hinhnen_Home-*.mp4` | **9.41 MB** |
| `video1-*.mp4` | **3.90 MB** |
| `hinhnen-*.png` | **1.88 MB** |
| `nen1-*.jpg` | 0.40 MB |
| `hinhnen_Home-*.jpg` | 0.27 MB |
| `SQL-*.jpg` | 0.27 MB |

Playwright first-load against `http://127.0.0.1:18080/` (Chromium, local
network, 3 runs, after `load` + 800 ms settle):

| Run | Wall ms | DOMContentLoaded ms | Load ms | Resources | Transfer KB |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 908 | 91 | 91 | 10 | 1,174 |
| 1 | 891 | 75 | 76 | 10 | 1,174 |
| 2 | 873 | 65 | 65 | 10 | 1,174 |

The initial document load is fast because the 15 MB of media is not on the
critical path. The media still dominates the **image and repository** size,
not the first paint.

## 10. CI duration

Run `44706644787` on `955abd0` (successful `develop2` push):

| Job | Duration |
| --- | ---: |
| `changes` | 0.2 min |
| `secrets` | 0.6 min |
| `backend` | **22.8 min** |
| `frontend-static` | 1.9 min |
| `frontend-shard` e2e-1 (localization) | 13.3 min |
| `frontend-shard` e2e-2 (rest 1/2) | 10.1 min |
| `frontend-shard` e2e-3 (rest 2/2) | 7.6 min |
| `frontend-shard` qa-1 (load=1) | 10.8 min |
| `frontend-shard` qa-2 (load=0) | 10.6 min |
| `frontend-shard` qa-3 (load=0) | 9.6 min |
| `frontend-shard` smoke-1 | 5.5 min |
| `frontend-shard` smoke-2 | 4.4 min |
| `frontend-shard` smoke-3 | 4.4 min |
| `frontend-local` (fan-in) | 0.2 min |

Total frontend-shard machine time: **76.3 min** across 9 legs. Wall clock is
dominated by `backend` (22.8 min). Every leg starts a full Compose stack and
seeds the demo database (~2 min), which is the main duplicated cost.

## 11. Local database shape (synthetic)

`dbcas-local-db-1`, `public` tables with non-zero rows at audit time:

| Table | Rows | Total size |
| --- | ---: | ---: |
| `question` | 5,560 | 17.1 MB |
| `mcq_option` | 8,188 | 1.56 MB |
| `rubric` | 7,052 | 1.74 MB |
| `sql_test_dataset` | 3,494 | 3.03 MB |
| `attempt` | 880 | 3.28 MB |
| `assessment_session` | 242 | 6.39 MB |
| `session_question_plan` | 880 | 205 KB |
| `selection_log` | 880 | 1.30 MB |
| `evaluation_record` | 279 | 590 KB |
| `grading_job` | 171 | 156 KB |
| `llm_cache` | 150 | 532 KB |
| `account` | 200 | 172 KB |
| `concept` | 80 | 115 KB |
| `question_concept` | 5,614 | 598 KB |

Empty local tables include `assessment`, `assessment_blueprint`,
`assessment_concept`, `assessment_question`, `grade_review`,
`login_throttle`, `oauth_handoff`, `question_candidate`, and
`account_identity`. Empty locally does **not** mean unused: several are
exercised by tests or by admin-only flows. See `05-bloat-candidates.md` for the
ones with enough evidence to act on.

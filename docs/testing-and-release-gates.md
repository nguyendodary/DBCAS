# Testing and release gates

Run from the stated directory with Docker available. Containers created by
tests use disposable data; never point a test at the developer/production DB.
The backend suite requires real PostgreSQL and the real sandbox image. A
missing Docker dependency fails the gate instead of silently skipping it.

## Full automated and static checks

From the repository root in the frontend terminal:

```powershell
cd frontend
npm ci
npm test
npm run build
npm audit
```

From the repository root in the backend terminal:

```powershell
cd backend
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m compileall -q app/
.venv/Scripts/python.exe -c "from app.main import app"
.venv/Scripts/python.exe -m pip check
```

From the repository root:

```powershell
docker compose config -q
docker compose --env-file deploy/release.env.example -f docker-compose.release.yml config --no-env-resolution -q
```

Use `.venv/bin/python` on POSIX. For Python dependency advisory scanning,
install/run `pip-audit` in the development environment; do not add it to
production runtime requirements. Record versions and the scan date. Do not
run blind forced dependency upgrades. A clean scan is not a security proof.

The test bootstrap explicitly blanks local AI credentials. A live provider
transport is forbidden: integration tests use the real LLM service, cache,
JSON/schema/domain validation with `httpx.MockTransport`. Never export a
paid key into an automated test environment or enable the live essay worker.

## Migration and real sandbox gates

Run `py -3.13 db/validate_question_localization.py` to check Vietnamese
coverage, stable MCQ labels, rubric levels, likely English prose and protected
technical tokens. A release requires the expected 441 question sources and
complete Vietnamese coverage.

`tests/test_migrations.py` covers fresh, pre-OAuth, post-OAuth without the
prerequisite graph, and current schemas in isolated namespaces. It verifies
data retention, repeated migration safety, constraints and final column
shape. The migration runner verifies checksums and serializes upgrades.

Sandbox suites cover PostgreSQL execution, rollback/cleanup, SELECT/JOIN/
GROUP/HAVING/subqueries, timeout, row/byte/cell bounds, dynamic SQL/catalog
rejection, unsafe setup rejection and typed numeric/boolean/null/text
semantics. Do not replace these with Python-literal comparator tests alone.
The sandbox test container has the release 256 MB/one-CPU resource limits.

## True browser journeys and accessibility

```powershell
cd frontend
npx playwright install chromium
npm run test:e2e
```

Install Firefox/WebKit with `npx playwright install firefox webkit`. On
PowerShell select a browser using `$env:DBCAS_BROWSER='firefox'` (or `webkit`,
`msedge`, `chromium`), then run the same complete gate. Edge uses an already
installed, separate headless browser profile. Every run creates fresh test
data; reports/screenshots are separated by engine. WebKit compatibility
does not establish a test on branded Safari or an Apple device. POSIX uses
`DBCAS_BROWSER=firefox npm run test:e2e`. Restore/clear the variable afterward.

Playwright starts Vite at `127.0.0.1:5174` and a real API at
`127.0.0.1:8100`. The test launcher creates labeled disposable app/sandbox
containers, migrates the schema, imports the academic pack and provisions
test-only identities. Test fixture endpoints exist in `tests/release_server.py`
only, are not copied into production images, and never serve on port 8000.
OAuth is disabled there; AI uses the real service with mocked HTTP transport.
It does not use the developer `.env` database or live provider configuration.
The browser fixture API uses one worker on Windows and two on Linux; Playwright
itself runs one test worker per engine. Two-worker native Windows API runs encountered
intermittent request stalls; retain those failed runs rather than presenting
them as passed. The separate network load gate and Linux release image smoke
both exercise two workers. Browser success alone is not proof of every
platform/worker combination.

Navigation-cancelled speculative requests are recorded separately from actual
failed requests; they are never silently counted as successful responses.
Dashboard checks also require both chart canvases to render. Runtime errors,
console errors, actual failed requests and repeated-request loops fail the gate.
Readiness uses visible content, resolved skeletons, error checks and rendered
charts instead of waiting for all speculative network activity to become idle.
Run full backend and browser gates sequentially on constrained local Docker/WSL
environments; retain dependency timeout failures and rerun complete gates after
the environment is stable. Do not silently retry or skip failed tests.

Journeys cover registration/login, all 13 adaptive questions, server drafts
and refresh/resume, actual SQL runs, essay grading, a committed answer whose
browser response is lost, manual finish, server timeout, evidence/history/
dashboard/guidance, admin provisioning, CRUD and mapping preservation,
explicit AI review, validation/activation, candidates and analytics. RBAC
checks include browser guards and real API ownership rejection.

Critical routes are checked at 390, 768, 1024 and 1440 px with axe and
viewport-overflow assertions. Reduced motion and viewport dialogs are
exercised. Screenshots and JSON results go to the workspace's sibling
`_review/remediation` directory, outside the repository. Test traces are
disabled to avoid storing authorization headers. Automated axe checks are
not WCAG certification; inspect screenshots and keyboard behavior manually.

The test cleanup verifies recorded container ownership labels before removing
only those test containers. Test data uses tmpfs; no developer Docker volume
is removed. Windows process termination can bypass Python atexit, so the
browser gate also has explicit ownership-checked cleanup.

## 100-learner load gate

In a terminal, with no browser gate running on these ports:

```powershell
cd backend
.venv/Scripts/python.exe tests/release_server.py --workers 2
```

After `/health` is ready, run in another terminal:

```powershell
cd backend
.venv/Scripts/python.exe tests/release_load.py
.venv/Scripts/python.exe tests/release_load.py --profile normal --output ../../_review/remediation/load-results-normal.json
.venv/Scripts/python.exe tests/release_sql_load.py
```

The load script refuses the normal application port and prepares exactly
100 test learners/sessions. It uses real network requests for authentication
validation, assessment list, state, draft, atomic answer submission, finish,
and competency reads. Authentication validation is JWT `/me`, not a test
that removes bcrypt cost from the actual login flow. Record request count,
success/failure, p50/p95/p99, mean and resource observations. The synchronized
burst intentionally measures 100 simultaneous requests; preserve failures
and earlier measurements when optimizing. Do not call a live provider.

The separate `normal` profile staggers 100 active learner identities at 20
requests/second and records peak in-flight requests. Arrival delay is excluded
from request latency. Report this explicit workload alongside the burst,
never as 100 simultaneous HTTP requests. SQL load uses four concurrent
learners for three rounds, against the same resource-limited real sandbox.
Verification probes and the test Vite proxy avoid reusing stale sockets.
These test transport settings do not change production assessment behavior.

After building both release images, run `python tests/release_images.py` from
the backend virtual environment. This exercises Python 3.13 migrations,
production configuration rejection, dependency readiness, registration,
actual Nginx proxy/security headers and a Chromium page/font timing check.
It creates only labeled test containers with tmpfs data and owned networks,
then removes those resources. It reserves three nonoverlapping /28 subnets
under `10.231.240.0/24`; check local routes before running and refuse overlaps.
On Windows, it invokes a WSL-backed Docker executable directly to preserve
JSON environment values through batch-wrapper quoting. Never substitute
developer credentials. The release stack itself keeps ordinary Docker/Compose
commands. A local image test does not deploy externally or verify public TLS.

`.github/workflows/release-gate.yml` configures the full backend/frontend and
Chromium/Firefox/WebKit browser gates on Python 3.13/Node 24, without live provider keys. It has not
run remotely while these commits remain unpushed. Load/image measurements
remain explicit local gates; preserve their reports for review.

Run SQL at separately bounded concurrency appropriate for the 256 MB sandbox;
do not launch 100 unrestricted SQL executions as a substitute for its safety
limits. Stop only the test launcher/process tree you started, then run
`python tests/cleanup_release.py`. Leave user review servers and databases
running. Do not prune Docker or delete volumes.

## Human release checks

`tests/test_readiness.py` checks a real PostgreSQL statement cancellation
and a local TCP server that accepts a connection but never authenticates.
The latter must return a safe 503 within the connection deadline, while
liveness remains available. Invalid/unbounded timeout settings are rejected.

After OAuth security changes, the owner signs in with both configured
providers and reports success/error codes; never request credentials.
Automated mocked provider tests and successful start redirects cannot prove
live consent/callback readiness. Retain the full release report, requirement
matrix, findings tracker, exact suite counts, build output, migration matrix,
load timings, browser screenshots and unresolved formal-document conflicts.

Proposal §6.2 practical DML/DDL conflicts with the read-only SQL acceptance
criteria/security architecture. The owner selected read-only execution with
DML/DDL knowledge assessed through MCQ/essay on 11 October 2026; see
requirements-decisions.md. Keep the safer sandbox rule; shared-database learner
mutations are never enabled. The supplementary bank regression verifies that
its learner reference queries remain SELECT.

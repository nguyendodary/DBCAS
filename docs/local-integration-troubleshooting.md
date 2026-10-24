# Local Docker / WSL integration troubleshooting

Run the full backend suite and browser suites sequentially. The documented
backend command remains `.venv/Scripts/python.exe -m pytest -q` from `backend`.
The standard browser command remains `npm --prefix frontend run test:e2e` from
the repository root. The Playwright configuration uses one worker and zero
retries; do not use a passing retry to erase a recurring failure.

## Diagnose the transport before changing services

1. Inspect `docker context ls`, `docker info`, `wsl --list --verbose` and WSL
   guest execution separately. A running distribution/service or an accepted
   TCP connection is not proof that the guest command or Docker HTTP API works.
2. Inspect host RAM/disk, known service ports, container state/restart/OOM flags
   and relevant daemon logs. Distinguish unavailable diagnostics from a healthy
   result. Do not classify a failure as OOM without evidence.
3. Windows localhost forwarding and the WSL private interface are different
   paths. For Docker hosted in WSL, set `DBCAS_TEST_DOCKER_HOST` to the currently
   verified WSL private address **for that test process only** when necessary.
   This controls disposable published database ports, not the Docker daemon's
   listen address. Never expose an unauthenticated Docker socket to fix a test.
4. Verify that the selected database is disposable before tests. Never point a
   test fixture at the development database. Keep live AI credentials disabled;
   the test bootstrap and mock-transport guard enforce that requirement.

Example (replace the address after discovering/verifying it):

```powershell
$env:DBCAS_TEST_DOCKER_HOST='<verified-WSL-private-address>'
cd backend
.venv/Scripts/python.exe -m pytest -q
```

After that process exits, run Chromium release E2E, then the documented supported
browser engines one at a time using `DBCAS_BROWSER=firefox`, `webkit` or `msedge`.
Use separate `DBCAS_E2E_OUTPUT` / `DBCAS_TEST_MANIFEST` paths to preserve previous
diagnostics. Keep the existing one-worker setting. Readiness polls must check
actual TCP authentication/queries, not wait a fixed extra sleep.

## Disposable-container ownership and bounded failure

The harness records a run ID and intended names under
`../_review/docker-tests/<run-id>.json` before asking Docker to create a
container. Create and start are separate bounded commands, so a failed start or
ambiguous create timeout already has cleanup ownership. Docker stderr is retained
in the test error. No startup failure is silently retried. Disposable database
storage is tmpfs; the sandbox keeps its 256 MB / one-CPU / PID limits. Successful
TCP readiness must also report PostgreSQL major version 17.

The schema is loaded through that verified disposable PostgreSQL connection,
with a statement timeout and errors propagated. This executes the complete
`db/schema.sql`; it avoids Docker's separate `exec -i` stdin/attach stream, which
timed out during a Windows/WSL browser bootstrap even after TCP readiness passed.
It does not change the development database or reduce schema assertions.

Cleanup inspects the actual container, verifies `dbcas.test-run`, and refuses
unexpected bind/volume mounts before removing the container. It never requests
volume removal. Failed ownership inspection or cleanup is reported explicitly,
with the receipt retained for later investigation. A missing container is safe
to leave absent. For an older orphan, also verify its purpose and that its owning
test process has completed before removal. Never remove unrelated containers or
run global pruning.

Pure ownership/command unit checks can run without a daemon:

```powershell
cd backend
.venv/Scripts/python.exe -m pytest --noconftest -q tests/test_docker_runtime.py
```

That command tests mocked command behavior only. It is **not** the full backend
release gate and does not justify skipping PostgreSQL, sandbox or security tests.

## If WSL control or forwarding remains unavailable

Retain the exact timeouts, Docker errors, run receipts and browser diagnostics.
Do not reset distributions, delete volumes, kill broad processes or stop unrelated
workloads. A host-wide WSL/service restart requires a separate maintenance
decision because it can interrupt every running Linux project. The agent must
report that boundary rather than execute it automatically. Inspect successful
subsequent runs for stability; do not claim the underlying intermittent cause
resolved merely because the API temporarily answered.

See [current remediation results](docker-stabilization-acceptance-20261023.md).

# Bug A — ephemeral SQL executor "invalid response" (2026-11-24)

Owner-requested investigation and fix. No architecture or security changes:
`--network none`, read-only rootfs, dropped capabilities and all resource limits
in `EphemeralSandboxRunner._create` are untouched.

## 1. Manual reproduction (exact executor commands on this host)

Python `subprocess` against `C:\Users\kudot\docker-cli\docker\docker.EXE`
(`shutil.which("docker")`), container created exactly as `_create` does from
`dbcas-sql-ephemeral:local`, payload a single JSON line on stdin.

| Command | Exit code | stdout | stderr |
|---|---|---|---|
| `docker create ...` | 0 | container id | empty |
| `docker start <name>` | 0 | container name | empty |
| `docker exec <name> pg_isready ...` | 0 | empty (normally prints a status line) | empty |
| `docker exec -i <name> /opt/runner/bin/python -m app.sandbox_job` | 0 | **empty** | empty |
| `docker exec -i <name> /bin/cat` | 0 | **empty** | empty |
| `docker exec -i <name> python -c "print('PYOK', ...)"` | 0 | **empty** | empty |
| `docker exec -t <name> echo HI123` | 0 | empty | empty |
| `wsl.exe -e docker exec -i <name> echo HI789` | 0 | `HI789\n` | empty |

`docker logs <name>` showed a healthy PostgreSQL startup, so the container was
running; every native `docker exec` attach stream was silently discarded.

## 2. Root causes (two independent defects)

- **(d) Windows/Docker Desktop CLI difference.** The native `.EXE` shim runs
  non-attach commands (`ps`, `inspect`, `logs`, `create`) correctly but drops
  all `docker exec` stdout/stderr. The repo already had a Windows WSL workaround
  in `docker_cli()` but only for `.cmd` wrappers. Fixed by preferring
  `wsl.exe -e docker` on Windows when its CLI reports a live server, with the
  native path kept as fallback.
- **Executor Settings rejected the writable demo profile.** With the stream
  restored, the container's real stderr became visible:
  `pydantic_core.ValidationError: Value error, SANDBOX_WRITABLE requires
  SANDBOX_MODE=ephemeral in every deployment mode` at `sandbox_job.py:20`.
  The trusted in-container job built `Settings` without `sandbox_mode`, so it
  defaulted to `shared` and failed before reading the payload. Fixed by passing
  `sandbox_mode="ephemeral"` — the job only ever runs inside that container.

The other candidates were ruled out: stdin was delivered (`/bin/cat` also
returned nothing); image and entrypoint were correct (`is_ready()` true, normal
Postgres logs); the container stayed alive for its 45 s watchdog.

## 3. Shared-sandbox `dataset_setup_failed (UndefinedObject)`

Reproduced with a writable shared runner against the legacy sandbox at
`localhost:5434`: `GRANT ... TO learner_rw` raises
`psycopg.errors.UndefinedObject`. **Missing object: role `learner_rw`.**
`dbcas_dataset_setup` and `learner_ro` exist there; `learner_rw` is created by
`sandbox/init/00-learner-role.sh` only when `SANDBOX_WRITABLE_PASSWORD` is set,
and the legacy SELECT-only sandbox was started without it. The app itself
cannot hit this combination (`config._deployment_safety` forbids
`sandbox_writable` with `sandbox_mode=shared`). The generic error was replaced
with one that names `learner_rw` and points at the ephemeral profile, so the
misconfiguration is identifiable instead of opaque.

## 4. Evidence after the fix

- `tests/dn/test_ephemeral_sandbox.py`: originally 4 failures; now **5 passed**
  (the 4 regressions plus a new writable UPDATE/DELETE rollback test that
  exercises the fixed in-container Settings).
- `tests/test_sandbox_transport_fix.py`: **4 passed** (CLI selection cached WSL
  choice, native and `.cmd` fallbacks, explicit missing-role error).
- Real grading trial through the fixed ephemeral sandbox (fresh dataset each
  time, reference answer graded by `app.services.sql_grading.grade_sql`):

| Statement | Executed | Rolled back | Resulting table state | Score | Grader |
|---|---|---|---|---|---|
| `UPDATE dml_items SET name='gamma' WHERE id=2;` | yes | yes | `[[1,'alpha'],[2,'gamma'],[3,'gamma']]` | 5.00/5.00 | `sql_semantic` |
| `DELETE FROM dml_items WHERE id=2;` | yes | yes | `[[1,'alpha'],[3,'gamma']]` | 5.00/5.00 | `sql_semantic` |

No security setting was relaxed and no new dependency was added.

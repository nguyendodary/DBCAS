# .env single-source audit — 2026-11-14

## Root cause

The demo stack does not read `DBCAS/.env`. `npm start` runs from
`_worktrees/dbcas-dn-20261101`; `scripts/local.mjs` reads only
`<that root>/.env`, and `docker-compose.local.yml` declares `env_file: .env`
relative to the same directory. The running containers confirm it:

| Path | Used by | Evidence |
| --- | --- | --- |
| `_worktrees/dbcas-dn-20261101/.env` | **Active demo stack** `dbcas-local` (`app`, `init`, Compose substitution) | `scripts/local.mjs` reads `<root>/.env`; `docker-compose.local.yml` has `env_file: .env`; container label `com.docker.compose.project.working_dir` = the worktree; project name `dbcas-local` |
| `DBCAS/.env` | Only the older 3-container `dbcas` project (`db`, `mailpit`, `sandbox`); **not** the app/frontend | `docker compose ls` shows project `dbcas` with `DBCAS/docker-compose.yml`; that file has no `app`/`frontend` service |
| `_worktrees/dbcas-dn-20261101/_review/*/fresh-clone/.env` | Disposable QA clones only | Each is 251 B with blank AI values; their own Compose project labels point into `_review/.../fresh-clone` |
| `_trash-20261113/.../.env` | Quarantined old clones; not running | Outside any active Compose working directory |
| `DBCAS-frontend-src/.env.example` | Historical source snapshot only | No live process or Compose file references it |

Newest owner values by modification time, names only:

| File | Last modified | AI key | Model |
| --- | --- | --- | --- |
| `DBCAS/.env` | 2026-11-11 13:06 | `sk-...95bd` (newest) | `openrouter/free` |
| `_worktrees/dbcas-dn-20261101/.env` | 2026-11-03 10:02 (before fix) | `sk-...e664` (older) | `openrouter/free` |

The older worktree key explains the “key not working” report: the app was
running with a key that was two revisions behind the owner's newest one.

## Fix

- Copied only `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` from `DBCAS/.env`
  into the ignored worktree `.env`; no value was printed or committed.
  Backup: `_review/env-20261114/.env.before-20261114` (ignored).
- `npm start` now prints the exact `.env` path and `key set (sk-...last4) /
  model set / base URL set` before Docker starts.
- `npm run env:check` reports AI variable names, missing/empty names, masked
  key and syntax checks without values.
- A linked worktree with no `.env` now fails with a clear message instead of
  silently creating a second environment. A fresh clone still gets the
  documented no-`.env` demo defaults.
- README top section states the single `.env` location and warns that the
  `DBCAS/` main checkout is not used.

## Live builder → evaluator check

Env: `_worktrees/dbcas-dn-20261101/.env`; key `sk-...95bd`; model
`openrouter/free`. Full secret-free ledger:
[`live-request-ledger.json`](live-request-ledger.json).

| # | Check | HTTP | Model accepted | Tokens | Latency | Fallback |
| --- | --- | ---: | --- | --- | ---: | --- |
| 1 | Evaluator | 200 | yes | 919 + 462 = 1381 | ≤17.75 s | no |
| 2 | Generation attempt 1 | 400 | no | — | 0.24 s | yes (client retry) |
| 3 | Generation attempt 2 | 200 | yes | 341 + 2183 = 2524 | ≤26.6 s | yes (strict validation: `timeout`) |

The round was authorized for **2** new HTTP requests. The client's built-in
retry on the first generation rejection made **3** requests; this is recorded
as an overrun and no fourth request was made. No 403 occurred. The evaluator
used the real model with `evaluator_fallback=false`; generation transport was
accepted on the retry but yielded no usable validated question, so the
application uses the validated bank/template fallback. Builder purity and
wire-prompt equality passed.

## All `.env` files found (values never read into output)

| Path | Size | Last modified | Git | Variable names |
| --- | ---: | --- | --- | --- |
| `_worktrees/dbcas-dn-20261101/.env` | 3928 | 2026-11-11 12:40 | ignored | ACCESS_SESSION_MAX_MINUTES, ACCESS_TOKEN_EXPIRE_MINUTES, CORS_ORIGINS, DATABASE_CONNECT_TIMEOUT_SECONDS, DATABASE_MAX_OVERFLOW, DATABASE_POOL_SIZE, DATABASE_POOL_TIMEOUT_SECONDS, DATABASE_URL, DEPLOYMENT_MODE, DN_API_PORT, DN_DB_PORT, DN_DOCKER_GID, DN_SANDBOX_PORT, FRONTEND_URL, GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GITHUB_REDIRECT_URI, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, GRADING_JOB_MAX_ATTEMPTS, GRADING_JOB_RETRY_SECONDS, JWT_ALGORITHM, JWT_SECRET, LLM_API_KEY, LLM_BACKOFF_SECONDS, LLM_BASE_URL, LLM_MAX_RETRIES, LLM_MODEL, LLM_SEED, LLM_TEMPERATURE, LLM_TIMEOUT_SECONDS, MAILPIT_SMTP_PORT, MAILPIT_UI_PORT, OAUTH_HANDOFF_TTL_SECONDS, OAUTH_STATE_TTL_SECONDS, PASSWORD_RESET_CONFIRM_RATE_LIMIT_ATTEMPTS, PASSWORD_RESET_IP_RATE_LIMIT_ATTEMPTS, PASSWORD_RESET_RATE_LIMIT_ATTEMPTS, PASSWORD_RESET_RATE_LIMIT_WINDOW_SECONDS, PASSWORD_RESET_TOKEN_TTL_MINUTES, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_PORT, POSTGRES_USER, READINESS_DATABASE_TIMEOUT_SECONDS, SANDBOX_ADMIN_URL, SANDBOX_CONNECT_TIMEOUT_SECONDS, SANDBOX_LEARNER_PASSWORD, SANDBOX_MAX_CELL_BYTES, SANDBOX_MAX_RESULT_BYTES, SANDBOX_MAX_ROWS, SANDBOX_MAX_SETUP_BYTES, SANDBOX_MAX_SQL_BYTES, SANDBOX_PORT, SANDBOX_POSTGRES_PASSWORD, SANDBOX_STATEMENT_TIMEOUT_MS, SANDBOX_URL, SESSION_SWEEP_SECONDS, SMTP_FROM, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_SSL, SMTP_STARTTLS, SMTP_TIMEOUT_SECONDS, SMTP_USERNAME |
| `DBCAS/.env` | 2272 | 2026-11-11 06:06 | ignored | ACCESS_TOKEN_EXPIRE_MINUTES, DATABASE_URL, FRONTEND_URL, GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GITHUB_REDIRECT_URI, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, JWT_ALGORITHM, JWT_SECRET, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, MAILPIT_SMTP_PORT, MAILPIT_UI_PORT, OAUTH_HANDOFF_TTL_SECONDS, OAUTH_STATE_TTL_SECONDS, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_PORT, POSTGRES_USER, SANDBOX_ADMIN_URL, SANDBOX_CONNECT_TIMEOUT_SECONDS, SANDBOX_LEARNER_PASSWORD, SANDBOX_MAX_ROWS, SANDBOX_MAX_SQL_BYTES, SANDBOX_PORT, SANDBOX_POSTGRES_PASSWORD, SANDBOX_STATEMENT_TIMEOUT_MS, SANDBOX_URL, SMTP_FROM, SMTP_HOST, SMTP_PORT |
| `_worktrees/dbcas-dn-20261101/_review/finish-20261110/fresh-clone/.env` | 251 | 2026-11-10 15:03 | ignored | JWT_SECRET, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER |
| `_worktrees/dbcas-dn-20261101/_review/oauth-20261112/fresh-clone/.env` | 251 | 2026-11-11 03:39 | ignored | JWT_SECRET, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER |
| `_worktrees/dbcas-dn-20261101/_review/qa/fresh-audit/.env` | 251 | 2026-11-02 08:50 | ignored | JWT_SECRET, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER |
| `_worktrees/dbcas-dn-20261101/_review/qa/fresh-clone/.env` | 251 | 2026-11-02 08:06 | ignored | JWT_SECRET, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER |
| `_trash-20261113/worktree/_review/audit-20261108/fresh-clone/.env` | 251 | 2026-11-07 12:42 | outside git | JWT_SECRET, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER |
| `_trash-20261113/worktree/_review/audit-fresh-20261104/.env` | 251 | 2026-11-04 10:49 | outside git | JWT_SECRET, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER |
| `_trash-20261113/worktree/_review/continuation-fresh-clone/.env` | 251 | 2026-11-03 15:10 | outside git | JWT_SECRET, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER |
| `_trash-20261113/worktree/_review/final-clean-20261102/.env` | 251 | 2026-11-02 01:54 | outside git | JWT_SECRET, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER |
| `_trash-20261113/worktree/_review/final-clone-20261103/.env` | 251 | 2026-11-02 19:30 | outside git | JWT_SECRET, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER |
| `_trash-20261113/worktree/_review/fresh-clone-20261103/.env` | 251 | 2026-11-02 17:42 | outside git | JWT_SECRET, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER |
| `_trash-20261113/worktree/_review/fresh-final-20261105/.env` | 251 | 2026-11-05 01:13 | outside git | JWT_SECRET, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER |
| `_trash-20261113/worktree/_review/fresh-local-20261102/.env` | 251 | 2026-11-01 20:32 | outside git | JWT_SECRET, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER |
| `_trash-20261113/worktree/_review/readiness-clean-clone/.env` | 251 | 2026-11-03 01:26 | outside git | JWT_SECRET, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER |

All 27 `.env*` files found include 13 `.env.example` files. Every example has
the same name schema as its adjacent environment (worktree example: 71 names;
main checkout example: 34 names); no example holds a value. None is tracked:
the worktree and main checkout files are matched by `.gitignore:20`.

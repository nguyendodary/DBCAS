# Handover gates — Architecture Freeze v1.1 (2026-11-25)

Re-run before the local handover tag. Code HEAD for the gate run:
`c31b2c3` (`develop2`). This log and the `STATUS`/`BACKLOG` update are the only
changes after that commit; no application code, validator, schema, migration or
`docs/qa/**` file was touched.

Environment: Windows, Node `v24.16.0`, Docker `29.8.1` (native and WSL2 both
report the same engine), Python `3.14.5` in `backend\.venv`, PostgreSQL 17 in
Docker, WSL2 `Ubuntu-24.04` available.

## Automated gates

| Gate | Command | Result |
|---|---|---|
| Backend lint | `.\.venv\Scripts\python.exe -m ruff check app tests manage.py` (from `backend/`) | `All checks passed!` |
| Backend full test | `.\.venv\Scripts\python.exe -m pytest -q` (from `backend/`) | **1940 passed, 7 skipped, 1 warning in 1473.97s (24:33)** |
| Frontend lint | `npm --prefix frontend run lint` | PASS — ESLint `--max-warnings=0` |
| Frontend unit test | `npm --prefix frontend test -- --maxWorkers=2` | **54 files / 463 tests passed** in 115.20s |
| Docs gate | `backend\.venv\Scripts\python.exe scripts\check_docs.py` | PASS — 48 assertions, 67 tables, 561 columns, 122 FKs, 159 indexes, 28 migrations, 106 API paths / 118 operations, 24 frontend routes |
| OpenAPI contract | `backend\.venv\Scripts\python.exe scripts\export_openapi.py --check` | `OpenAPI matches the runtime contract` |
| Environment inventory | `npm run env:check` | PASS — AI names present, key syntactically valid, HTTPS base URL; values masked |
| Route inventory | `npm run inventory:check` | `OK: api-routes.json and frontend-routes.json match their sources` |

Expected warnings, not failures:

- `Unknown LLM_PROVIDER=Mistral; using openai_compatible` — the configured label
  is not a known alias, so the documented fallback applies; the key and base URL
  are valid.
- `JWT_SECRET is the development default` — expected on the local demo `.env`;
  staging/production reject the documented demo secrets.

The backend warning is the Starlette/httpx deprecation notice; it is unchanged
and does not affect the result.

## Security and merge checks

| Check | Result |
|---|---|
| `npm run secrets:scan` (current tree) | `Secret scan: 2969 files; 0 findings; mode=tree.` |
| Full Git history blob scan (8038 blobs, all refs) | 16 matches, all fixture/placeholder values (mock/QA/test tokens, a short provider-key-shaped value used to test masking, a template placeholder); **0 real keys** |
| Tracked `.env*` | Only `.env.example`; `.env`, `.demo-seed.sql`, `node_modules/`, `dist/`, `.venv/` are ignored |
| Merge test `develop2 -> main` | `git merge-tree --write-tree --name-only --messages main develop2` exit 0, no conflicts; `main` remains `e7e432c` |
| Old tags | `arch-freeze-v1` = `38f8e06`; `arch-freeze-v1.1` = `696cdf9`; neither was moved |

## Clean-clone README test

A separate clone of `develop2` was created in the temp directory with a fake
`.env` (fake LLM key/base/model, random-looking DB/JWT values) on ports
18100/18180/18125/11125.

1. First `npm start` stopped at `Không đọc được group Docker socket` because the
   native Windows Docker CLI returned no stdout for the socket-group probe.
2. The WSL probe returned GID `988`; setting `LOCAL_DOCKER_GID=988` and re-running
   `npm start` built the images, seeded the demo and reached readiness.
3. `/readiness` returned `database: true` and `sandbox: true`.
4. Admin login returned a token; `GET /api/v1/admin/accounts` returned 4 accounts.
5. Mailpit answered HTTP 200 at `http://localhost:18125`.
6. `npm run stop` stopped every service cleanly.

The README now documents the `LOCAL_DOCKER_GID` fallback (commit `7dee2fc`).
No application or Compose change was made.

## Handover commits

| Commit | Purpose |
|---|---|
| `1e5736e` | `docs(release): add v1.1 release notes` |
| `7dee2fc` | `docs(readme): document Windows Docker socket group fallback` |
| `53b6d4f` | `docs(submission): add handover summary` |
| `c31b2c3` | `docs(submission): add defense demo checklist` |
| this commit | `docs(agent): record v1.1 handover gates` |

Local tag after this commit: **`arch-freeze-v1.2`**. It is not pushed.

## Result

All automated gates pass on the real tree with Docker and WSL2 available. The
manual E2E evidence (Mode 2, admin queue, vi/en, key-off fallback, DML) was not
re-run in this pass; its measured results remain in
[`final-gates.md`](final-gates.md), [`ai-dml-verification.md`](ai-dml-verification.md)
and [`prompt-contract-fix.md`](prompt-contract-fix.md). Production remains
**HOLD**; nothing was pushed or merged.

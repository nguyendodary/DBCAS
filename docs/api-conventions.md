# DBCAS API Conventions

Source of truth for how the backend exposes HTTP APIs. Derived from the
Architecture document (module view: Controllers → Services → Repositories).
All domain rules come from the project use cases — do not invent endpoints.

## Base

- Prefix: `/api/v1`. Health check (infra, no auth): `GET /health`.
- JSON only (`application/json`). HTTPS terminates in front of the API.
- Auth: `Authorization: Bearer <JWT>` — access token from `POST /api/v1/auth/login`.
- Roles: `Learner`, `Administrator` (seeded in `db/seed.sql`). Role checks
  run through `require_roles(...)` dependencies — never hand-check strings
  inside handlers.

## Layers (backend/app)

| Layer | Files | Rule |
|---|---|---|
| Controllers | `routers/` | validate input, call services, map responses — no business logic |
| Services | `services/` | use-case rules (auth, grading, sessions…); call repositories |
| Repositories | `repositories.py` | all SQLAlchemy access; services never write queries |
| Models | `models.py` | mirror `db/schema.sql` names exactly |
| DTOs | `schemas.py` | pydantic request/response; field-level validation |

## Status codes

| Code | When |
|---|---|
| 200 | success |
| 201 | resource created |
| 401 | missing/invalid/expired token, bad credentials, inactive account |
| 403 | authenticated but wrong role, or login into a `disabled` account |
| 404 | resource not found (also used for other people's sessions — do not leak existence) |
| 409 | state conflict (duplicate email, already-submitted answer, closed/expired session) |
| 422 | request validation failed |

## Error format — always

```json
{ "error": { "code": "snake_case_code", "message": "Human readable", "details": [] } }
```

`code` is stable and machine-readable; `details` is optional (e.g. field
errors for 422). Handled by `AppError` + handlers in `errors.py` — raise
`AppError(status, code, message)` from services, never return ad-hoc JSON.

## Implemented endpoints (Sprint 1–2, DN scope)

| Method & path | Role | Use case |
|---|---|---|
| `POST /api/v1/auth/register` | public | UC01 — learner self-registration (always Learner role) |
| `POST /api/v1/auth/login` | public | UC02 — credentials + `status=active` → JWT |
| `GET  /api/v1/auth/me` | any authenticated | current account + roles |
| `POST /api/v1/admin/accounts` | Administrator | UC04 — provision account, starts `disabled` |
| `POST /api/v1/sessions/{id}/answers` | Learner (owner) | UC15/16 — submit answer; MCQ graded by key, SQL graded semantically in the sandbox |
| `POST /api/v1/sessions/{id}/sql-run` | Learner (owner) | UC13 — run learner SQL in the sandbox on the question's primary dataset |

`sql-run` executes the query in the isolated sandbox and returns a sanitized
`{success, columns, rows, row_count, execution_time_ms, error_type,
error_message}` payload — failures (syntax error, timeout, prohibited
statement, result too large) are data, not HTTP errors. It never touches the
system database and never exposes container details.

`/answers` accepts `selected_option_id` (MCQ) or `sql_answer` (SQL). SQL
submissions are executed read-only against every `sql_test_dataset` of the
question — edge cases included — and compared semantically to each stored
`expected_result` (`{columns, rows, ordered?, check_columns?}`): row order is
insensitive unless `ordered` is set, duplicates count, numbers compare by
value, and required concept tags (`question_concept.is_required`) are
verified on the query AST. Score = `points × passed_datasets / total`; a
missing required technique scores 0. Evidence is stored in
`attempt.grading_detail` without exposing expected rows or setup SQL.

Unimplemented module endpoints (question bank, adaptive selection, essay
grading, competency, analytics) belong to other backlog items — see the
Architecture document for the module map.

## Request rules worth remembering

- Registration password: ≥8 chars, ≤72 bytes (bcrypt limit), confirmation
  must match. Administrator role can never be self-registered (UC01/UC04).
- Answer key is never returned to learners: `mcq_option.is_correct` is used
  server-side only; grading evidence lives in `attempt.grading_detail`.
- Logout is client-side (UC03): stateless JWT, no server revocation.

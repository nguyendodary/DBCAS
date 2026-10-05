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

## Implemented endpoints

| Method & path | Role | Use case |
|---|---|---|
| `POST /api/v1/auth/register` | public | UC01 — learner self-registration (always Learner role) |
| `POST /api/v1/auth/login` | public | UC02 — credentials + `status=active` → JWT |
| `GET  /api/v1/auth/me` | any authenticated | current account + roles |
| `GET  /api/v1/concepts/graph` | any authenticated | DBCAS-26 — prerequisite skill graph |
| `GET  /api/v1/assessments` | Learner | UC12 — active assessments the learner may start |
| `POST /api/v1/assessments/{id}/sessions` | Learner | UC12 — start or resume an adaptive session |
| `GET  /api/v1/sessions` | Learner (owner) | UC18 — own session history, newest first |
| `GET  /api/v1/sessions/{id}` | Learner (owner) | UC12 — live state: countdown, progress, pending question |
| `POST /api/v1/sessions/{id}/serve-next` | Learner (owner) | FR-15 — pending question or adaptive next pick (audited in `selection_log`) |
| `POST /api/v1/sessions/{id}/finish` | Learner (owner) | UC12 — finalize + deterministic competency/gap recompute |
| `GET  /api/v1/sessions/{id}/evidence` | Learner (owner) | UC18 — per-question evidence; answer keys revealed only post-finalization |
| `POST /api/v1/sessions/{id}/answers` | Learner (owner) | UC15/16 — submit answer; MCQ by key, SQL semantically in sandbox, essay by 4-level LLM rubric |
| `POST /api/v1/sessions/{id}/sql-run` | Learner (owner) | UC13 — run learner SQL in the sandbox on the question's primary dataset |
| `GET  /api/v1/sessions/{id}/competency` | Learner (owner) | UC16 — per-concept competency profile |
| `GET  /api/v1/sessions/{id}/gaps` | Learner (owner) | UC17 — skill gaps ranked by shortfall |
| `GET  /api/v1/sessions/{id}/guidance` | Learner (owner) | DBCAS-27 — prerequisite-aware ranked study guidance |
| `POST /api/v1/admin/accounts` | Administrator | UC04 — provision account, starts `disabled` |
| `GET  /api/v1/admin/accounts` | Administrator | account roster |
| `PATCH /api/v1/admin/accounts/{id}` | Administrator | UC04 — activate verified / disable account |
| `GET|POST /api/v1/admin/concepts`, `PATCH|DELETE /api/v1/admin/concepts/{id}` | Administrator | UC05 — concept model CRUD |
| `PUT /api/v1/admin/concepts/{id}/prerequisites` | Administrator | UC05 — replace a concept's prerequisite set (cycle-safe) |
| `GET|POST /api/v1/admin/clos`, `PATCH|DELETE /api/v1/admin/clos/{id}` | Administrator | UC05 — CLO CRUD |
| `PUT /api/v1/admin/clos/{id}/concepts` | Administrator | UC05 — replace the confirmed concept set |
| `POST /api/v1/admin/clos/{id}/ai-suggest` | Administrator | UC06 — AI concept links, stored pending |
| `POST /api/v1/admin/clos/{clo}/concepts/{cid}/confirm` · `DELETE …/concepts/{cid}` | Administrator | UC06 — confirm/reject one pending link |
| `GET|POST /api/v1/admin/questions`, `GET|PUT /api/v1/admin/questions/{id}` | Administrator | UC07 — question bank CRUD |
| `PATCH|DELETE /api/v1/admin/questions/{id}` | Administrator | UC07 — status transition / delete (guarded by references) |
| `POST /api/v1/admin/questions/{id}/ai-tags` | Administrator | UC08 — AI tag + difficulty + criteria suggestion, stored pending |
| `POST /api/v1/admin/questions/{qid}/tags/{cid}/confirm` · `DELETE …/tags/{cid}` | Administrator | UC08 — confirm/reject a pending tag |
| `GET|POST /api/v1/admin/question-candidates…` | Administrator | UC10 — queue, generate, validate, approve, reject |
| `GET|POST /api/v1/admin/assessments`, `GET|PUT|PATCH|DELETE /api/v1/admin/assessments/{id}` | Administrator | UC09 — adaptive assessment configuration + lifecycle |
| `GET /api/v1/admin/analytics/cohort` | Administrator | UC20 — class-wide competency + below-benchmark prevalence |
| `GET /api/v1/admin/learners` | Administrator | learner roster with activity counts |
| `GET /api/v1/admin/learners/{id}/sessions` | Administrator | learner session drill-down |
| `GET /api/v1/admin/sessions/{id}/competency` | Administrator | per-session competency profile |

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

Essay submissions (`essay_answer`) are sanitized (learner name/email and
student-number-like digits are redacted) before the external LLM provider
sees them, then graded against the question's four-level `rubric` rows.
The provider's score is validated and clamped into the selected level's
`min_score`–`max_score` band; malformed provider output returns `502
llm_invalid_response` and leaves the attempt unsubmitted for a safe retry.
An unconfigured provider returns `503 llm_not_configured`.

Every response also carries `X-Content-Type-Options: nosniff` and
`X-Frame-Options: DENY`; `/api/*` responses are `Cache-Control: no-store`.

## Request rules worth remembering

- Registration password: ≥8 chars, ≤72 bytes (bcrypt limit), confirmation
  must match. Administrator role can never be self-registered (UC01/UC04).
- Answer key is never returned to learners: `mcq_option.is_correct` is used
  server-side only; grading evidence lives in `attempt.grading_detail`.
- Logout is client-side (UC03): stateless JWT, no server revocation.

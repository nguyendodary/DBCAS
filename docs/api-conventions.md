# DBCAS API Conventions

The [supervisor API extension](supervisor-implementation.md#api-contract)
documents optional personalized start bodies, explicit topic practice,
publication guards, grading review/retry APIs and cumulative profiles. Existing
bodyless starts and the `/api/v1` prefix remain supported. A 409
`results_pending` response contains safe release-state details and no grades.

Source of truth for how the backend exposes HTTP APIs. Derived from the
Architecture document (module view: Controllers → Services → Repositories).
All domain rules come from the project use cases — do not invent endpoints.

## Base

- Prefix: `/api/v1`. Process liveness: `GET /health`; dependency readiness:
  `GET /readiness` (200/503 with safe dependency booleans).
- JSON only (`application/json`). HTTPS terminates in front of the API.
- Auth: `Authorization: Bearer <JWT>` — access token from `POST /api/v1/auth/login`.
- Roles: `Learner`, `Administrator` (fresh DDL and additive migration 005).
  Role checks run through `require_roles(...)` dependencies. Administrator
  does not imply permission to assign roles: role operations also require the
  database-backed `can_manage_roles` capability.

## Layers (backend/app)

| Layer | Files | Rule |
|---|---|---|
| Controllers | `routers/` | validate input, call services, map responses — no business logic |
| Services | `services/` | use-case rules (auth, grading, sessions…); call repositories |
| Repositories | `repositories.py` | SQLAlchemy queries, inserts and deletes; services own domain updates to loaded entities and commit/rollback boundaries |
| Models | `models.py` | corresponding access types/principal constraints; DDL/migrations are persistence authority |
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
| 429 | login throttled; `Retry-After` is provided |
| 500 | safe database/internal failure envelope |
| 502/503/504 | controlled provider/grading infrastructure failure |

## API error envelope

```json
{ "error": { "code": "snake_case_code", "message": "Human readable", "details": [] } }
```

`code` is stable and machine-readable; `details` is optional (e.g. field
errors for 422). Handled by `AppError` + handlers in `errors.py` — raise
`AppError(status, code, message)` from services, never return ad-hoc JSON.
Expected database/provider/configuration failures and unhandled internal
faults use safe JSON handlers. Infrastructure failures before the app or at
a reverse proxy can have a proxy response; this contract cannot govern them.

## Implemented endpoints

| Method & path | Role | Use case |
|---|---|---|
| `POST /api/v1/auth/register` | public | UC01 — learner self-registration (always Learner role) |
| `POST /api/v1/auth/login` | public | UC02 — credentials + `status=active` → JWT |
| `GET  /api/v1/auth/me` | any authenticated | current account + roles |
| `POST /api/v1/auth/renew` | any authenticated | bounded renewal retaining original login time |
| `GET /api/v1/auth/oauth/providers` | public | enabled provider configuration flags |
| `GET /api/v1/auth/oauth/{provider}/start`, `GET …/callback`, `POST …/complete` | public | backend code exchange, state/PKCE, verified-email linking and one-time handoff |
| `GET  /api/v1/concepts/graph` | any authenticated | DBCAS-26 — prerequisite skill graph |
| `GET  /api/v1/assessments` | Learner | UC12 — active assessments the learner may start |
| `POST /api/v1/assessments/{id}/sessions` | Learner | UC12 — start or resume an adaptive session |
| `GET  /api/v1/sessions` | Learner (owner) | UC18 — own session history, newest first |
| `GET  /api/v1/sessions/{id}` | Learner (owner) | UC12 — live state: countdown, progress, pending question |
| `POST /api/v1/sessions/{id}/serve-next` | Learner (owner) | FR-15 — pending question or adaptive next pick (audited in `selection_log`) |
| `POST /api/v1/sessions/{id}/finish` | Learner (owner) | UC12 — finalize + deterministic competency/gap recompute |
| `GET  /api/v1/sessions/{id}/evidence` | Learner (owner) | UC18 — per-question evidence; answer keys revealed only post-finalization |
| `POST /api/v1/sessions/{id}/answers` | Learner (owner) | UC15/16 — submit answer; MCQ by key, SQL semantically in sandbox, essay by 4-level LLM rubric |
| `PUT /api/v1/sessions/{id}/draft`, `GET …/draft?question_id={qid}` | Learner (owner) | revision-controlled durable ungraded current answer |
| `POST /api/v1/sessions/{id}/submit` | Learner (owner) | idempotent answer + authoritative next state in one transaction; preferred SPA endpoint |
| `POST /api/v1/sessions/{id}/sql-run` | Learner (owner) | UC13 — run learner SQL in the sandbox on the question's primary dataset |
| `GET  /api/v1/sessions/{id}/competency` | Learner (owner) | UC16 — per-concept competency profile |
| `GET  /api/v1/sessions/{id}/gaps` | Learner (owner) | UC17 — skill gaps ranked by shortfall |
| `GET  /api/v1/sessions/{id}/guidance` | Learner (owner) | DBCAS-27 — prerequisite-aware ranked study guidance |
| `POST /api/v1/admin/accounts` | Role manager | UC04 — provision Administrator account, starts `disabled` |
| `GET  /api/v1/admin/accounts` | Administrator | account roster |
| `PATCH /api/v1/admin/accounts/{id}` | Administrator (role manager for Administrator targets) | UC04 — activate a verified account; disabling an Administrator additionally requires `can_manage_roles` |
| `GET /api/v1/admin/role-management/capability` | Administrator | current operator's role-assignment capability only |
| `PATCH /api/v1/admin/accounts/{id}/role` | Role manager | grant/revoke Administrator with `role` + `expected_role`; serialized, audited, conflict-safe |
| `GET /api/v1/admin/accounts/role-audit` | Role manager | immutable role assignment/bootstrap audit history |
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
| `POST /api/v1/admin/questions/{id}/ai-review` | Administrator | explicit approval/rejection of AI difficulty/criteria |
| `GET|POST /api/v1/admin/question-candidates…` | Administrator | UC10 — queue, generate, validate, approve, reject |
| `GET|POST /api/v1/admin/assessments`, `GET|PUT|PATCH|DELETE /api/v1/admin/assessments/{id}` | Administrator | UC09 — adaptive assessment configuration + lifecycle |
| `GET /api/v1/admin/analytics/cohort?assessment_id={id}` | Administrator | UC11 — class-wide competency + below-benchmark prevalence and trend |
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
insensitive unless `ordered` is set, duplicates count, PostgreSQL numeric
values compare by value (1, 1.0 and 1.00), booleans are distinct from numbers,
NULL is distinct, and text whitespace remains significant. Numeric wire
strings carry PostgreSQL type metadata. Required confirmed concept tags
(`question_concept.is_required`) are
verified on the query AST. Score = `points × passed_datasets / total`; a
missing required technique scores 0. Evidence is stored in
`attempt.grading_detail` without exposing expected rows or setup SQL.

Essay submissions (`essay_answer`) are sanitized (learner name/email and
known student identifiers and labelled PII are redacted with token boundaries) before the external LLM provider
sees them, then graded against the question's four-level `rubric` rows.
The provider's score must be finite and inside the selected canonical level's
`min_score`–`max_score` band; no clamping or invented score is permitted. Explanation,
feedback, matched criteria, missing concepts and supported evidence citations are required.
Malformed/domain-invalid provider output returns `502
llm_invalid_response` and leaves the attempt unsubmitted for a safe retry.
Provider outages/unconfigured grading persist a submitted answer as explicitly
pending with a bounded grading job and null score; an external-call-enabled
worker is required for essay retries. The standalone AI endpoints return safe
503 configuration errors. Invalid output never reaches the cache.

Every response also carries `X-Content-Type-Options: nosniff` and
`X-Frame-Options: DENY`; `/api/*` responses are `Cache-Control: no-store`.

## Request rules worth remembering

- Registration password: ≥8 chars, ≤72 bytes (bcrypt limit), confirmation
  must match. Registration always creates Learner; supplied role/capability
  fields are ignored. Administrator assignment is restricted to role managers.
- Answer keys/expected results are withheld during the live session; permitted
  MCQ keys and grading evidence are revealed only after finalization.
- Logout is client-side (UC03): stateless JWT, no server revocation.

## Persistence and display contracts

Question metadata on `PUT /admin/questions/{id}` distinguishes omission from
an explicit value: omitted `tags` or `source_refs` preserves that field,
including when an edit creates a new question version. A provided list replaces
it; `[]` intentionally clears it, while `null` is invalid. On creation, omission
still produces empty lists. The admin editor retains and sends existing
metadata without offering a clearing control. Historical evidence is unchanged.

Question: `source=bank|ai_generated`, `status=draft|validated|retired`.
Assessment: `draft|published|closed`; Session: `in_progress|completed|timed_out`.
AI mappings: `pending|confirmed|rejected`; candidate validation: `pending|validated|rejected`
with `promoted_question_id` denoting approval. Legacy active/rejected aliases
are normalized on input/upgrade, not new persistence states.

Drafts are distinct from submitted answers. Writes target the currently
served unsubmitted item; reads require an item actually served in the owned
session. The database clock owns expiry/finalization; timeout/manual finish
uses saved nonempty drafts and is idempotent. Snapshots preserve assessment
targets/config, prompt, options, points, rubrics, datasets and confirmed tags.
Used content edits create versions, preserving prior reports.

Competency uses submitted graded immutable evidence with confirmed tags;
pending/rejected tags contribute zero. Gap means competency strictly below
target. Guidance order is shortfall DESC, then concept ID; prerequisite
readiness and LLM explanations cannot reorder it. Changed context clears
stale explanations.

Guidance reasons use `reason_code: "below_benchmark"` and typed
`reason_params: { shortfall, target }` (Decimal values serialized as numeric
strings, never locale-formatted). Clients localize the reason and format the
numbers/percentage. The existing prerequisite `status` and `concept_name`
fields supply preparation/unassessed details; below-target prerequisites
take precedence over unassessed ones in that explanation. These presentation
changes do not alter readiness, ranking, scoring or persistence.

The former dynamically generated English `reason` field is removed. The
repository's dashboard and tests are migrated together; no external public
client compatibility requirement is documented. Deploy API and frontend
together. English question content remains canonical. `question_translation`
stores display prose by locale; it does not store SQL, expected results,
identifiers, answer keys, source references, concept codes or difficulty data.

Localization boundary audit:

- Competency/gap/dashboard summaries are numeric data or enum codes; the
  client supplies labels. Guidance benchmark and prerequisite sentences are
  system UI text and now use the structured contract above.
- The frontend sends its selected locale in `Accept-Language` when starting an
  assessment. The server pins that locale to the session; question snapshots
  capture the display text and historical evidence keeps it. Existing
  snapshots remain unchanged and default to English.
- English question text remains canonical. Vietnamese prompts, explanations,
  option text and learner-facing rubric wording are stored against the same
  question. SQL, identifiers, datasets, expected rows, tags, source references
  and scoring contracts remain canonical.
- Essay grading keeps its English rubric bands and score boundaries. For a
  Vietnamese session, only learner-facing provider narratives are requested
  in Vietnamese; stored band names and score validation remain unchanged.
- Missing or stale translations fall back to English and are exposed as
  untranslated in the admin bank. The source-pack validator reports missing
  locales before a complete bank release.
- OAuth errors, API/validation errors and assessment statuses already map
  stable codes to frontend catalogs, with localized unknown-code fallbacks.
- SQL failure codes map to localized guidance. Only sanitized syntax/schema
  diagnostics remain technical text; no arbitrary server exception is shown.
- Admin AI review preserves provider payloads. Candidate check codes and
  pass/fail states are localized; the detailed JSON is technical diagnostic
  data, not a source of UI labels.

History/analytics include server-computed summaries and daily trends. Category
charts show a labelled display mean of assessed concept percentages; the
formal documents specify visualization but no new category scoring formula.
Official competency remains per concept. Unbenchmarked concepts are not
counted as meeting a target, and pending grades prevent a final overall result.

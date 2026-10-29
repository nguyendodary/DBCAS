# Formal adaptive delivery — 29 October 2026

## Why this change exists

The personalized selector introduced on 18 October assembled the entire formal
question plan before question one and clamped every question to the single
selected difficulty band. A read-only audit of the real bank explains why the
demo failed: no single-concept pool satisfies the full 10 MCQ / 2 SQL / 1 essay
mix inside one band, so any one-skill formal start — Easy, Medium or Hard —
could only end in `insufficient_question_pool`. The error was accurate about
the frozen-plan rule; the frozen-plan rule was wrong. The earlier successful
13-question benchmark ran through a different configuration path and never
exercised the selector, so its success did not prove the selector worked.

## Current formal behavior (source of truth)

Implemented in `backend/app/services/formal_adaptive.py`, reached from
`POST /api/v1/assessments/{id}/sessions` whenever the body requests
`mode: "FORMAL"`. Practice and the original body-less adaptive start are
unchanged.

- **Scope.** The learner selects one skill, several skills, or every concept of
  a published assessment (`all_concepts`). The server validates every ID
  against the published targets, rejects duplicates and mixed scope requests,
  and keeps UUID request idempotency plus the transactional start locks.
  Selected skills are honoured exactly; no unrelated skill is added.
- **Named bands are a starting point, not a cap.** EASY = 1–2, MEDIUM = 3,
  HARD = 4–5 choose the opening band. After each answered question the band
  moves at most one step, driven by the last three graded answers: three
  mastered raises one band, three missed lowers one band, anything else
  maintains. Movement is clamped to the assessment's administrator-configured
  difficulty range, and the reason is recorded.
- **Mandatory opening.** Questions 1–3 are validated approved-bank MCQs at
  difficulty 1–2 inside the selected scope. This is the same basic-evidence
  opener the original engine used.
- **Phase order.** The configured type mix is served in strict MCQ → SQL →
  essay phases (currently 13 questions = 10 MCQ + 2 SQL + 1 essay in 60
  minutes; historical published configurations keep their captured limits).
  A phase is never substituted with another type; theory-only contracts that
  contain no SQL are never forced to run SQL.
- **Question source modes.** `BANK` (default) serves validated bank questions
  only. `AI` keeps the three bank openers and generates every later question
  at the adaptive target, validates it before presentation (including sandbox
  execution for SQL references), stores it outside the approved bank with
  provenance, and stops explicitly with an audited notice if a generated
  question fails validation. AI mode requires a configured provider and a
  schema that can persist session-scoped generated questions; where either is
  missing it fails closed (503) and the learner is directed to bank mode. It
  is not available on the current persistent development schema.
- **Honest shortage handling.** Before a session row exists, a preflight
  compares the complete mandatory mix against distinct eligible version
  families inside the scope: per-type availability, the three basic opening
  MCQs, and any selected skill with no approved question at all. A genuine
  shortage returns an accurate `formal_bank_insufficient` error with the
  concrete counts and options; the requested 13 is never silently reduced,
  the band is never used as a hidden relaxation, and no question, answer or
  approval is fabricated. Mid-session bank changes stop delivery with a
  durable `adaptive_event` notice instead of substituting.
- **Auditability.** Every served question keeps its `selection_log` decision
  (phase, band, band reason, target and served difficulty, source mode,
  concept reason); every stop decision is an `adaptive_event` row.

## Related guards added with the selector

- `LearnerOnly` is now a true role guard: an Administrator account attempting
  to start, serve or submit an assessment receives `403 admin_cannot_learn`,
  even on a legacy dual-role account. Learners remain unable to see unpublished
  scores, provisional profiles or gap results; both release policies are intact.
- Human-verified review gained `POST /api/v1/admin/grading-reviews/{session_id}`
  `/attempts/{attempt_id}/sql-run`: the reviewing Administrator re-executes the
  stored SQL answer in the isolated read-only sandbox (provisioned primary
  dataset, dropped afterwards). It is allowed only after submission, only for
  `HUMAN_VERIFIED` sessions, never on the reviewer's own session, and the
  execution result is review evidence, not a silent regrade.

## Verification performed on 29 October

All gates ran against disposable PostgreSQL 17 containers or the disposable
demo database; the persistent academic database and its question content were
not modified, and no migration was applied.

- `backend/tests/test_formal_band_policy.py` — 10 passed (±1 band policy,
  clamping, insufficient-evidence maintenance).
- `backend/tests/test_formal_ai_adaptive.py` — 6 passed (AI gating, fail-closed
  behaviour, provenance isolation).
- `backend/tests/test_assessment_blueprints.py` — 12 passed (adaptive formal
  start replaces frozen blueprint scheduling; shortage creates no session).
- Regression: `test_adaptive_engine`, `test_grading`,
  `test_supervisor_completion` — 56 passed;
  `test_supervisor_requirements`, `test_rbac`, `test_final_acceptance` — 92
  passed; `frontend/src/test/LearnerPages.test.jsx` — 16 passed.
- Live demo-data verification (`_review/personalized-assessment-20261029/`):
  13/13 checks passed on the disposable demo database — one-skill starts at
  each named band serve a full 13 in strict MCQ → SQL → essay order with at
  most one band step and basic openers; all-concepts and multi-skill scopes
  start with the exact selected scope recorded; a genuinely short bank
  (skill with no approved SQL) returns `formal_bank_insufficient` with
  per-type counts; `IMMEDIATE` and `HUMAN_VERIFIED` policies are carried into
  sessions; AI mode fails closed without provider/schema support.

## Status and boundaries

The implementation lives in the current working tree and is pending its own
code commit by the repository owner; this document records verified workspace
behaviour, not GitHub history. The 29 October academic analysis remains open:
the per-area theory mix (10/0/3 blueprints versus the 10/2/1 assessment
contract) and blueprint approval provenance are decisions reserved to the
project owner and are unaffected by this delivery-policy change. Historical
frozen-plan documents and dated test records above keep their original wording
as execution history; this file is the current-state reference for formal
delivery.

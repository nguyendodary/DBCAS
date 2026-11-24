# Bug B — `is_correct` null / `ability` flat (2026-11-24)

Owner-requested investigation. **Conclusion: not an adaptive or grading bug.**
Both observations came from the frozen release policy and from answering
without knowing the answer key. No production code was changed for this bug; a
regression test documents the correct observation path.

## 1. Actual grading flow (from code)

- MCQ: `POST /sessions/{id}/submit` → `grading_service.submit_answer` →
  `assessment_lifecycle.submit` → `grade_attempt` → `score_mcq` **synchronously**.
  Score and `grading_detail.is_correct` are persisted on the Attempt at submit.
- SQL: same synchronous path via `grade_sql`; on `SandboxError`/`LLMError` the
  answer is persisted with `grading_detail.status="pending"` and
  `repo.enqueue_grading(attempt)`; `app.worker` / `grading_jobs.process_one`
  retries it later.
- Essay: graded synchronously when an LLM is configured; otherwise queued for
  the maintainer worker or left `awaiting_instructor` (`AUTO_GRADE_ESSAYS=false`).
- FIXED papers are the exception: drafts are graded in `finalize`, not per-question.
- `assessment_lifecycle.result_for()` deliberately returns `score=None` and
  `is_correct=None` whenever `result_release_policy == "HUMAN_VERIFIED"` and
  `release_status != "published"`. Mode 2 sessions use HUMAN_VERIFIED, so the
  submit response always shows null — by design, not a missing grade.
- Adaptive difficulty uses `ai_adaptive._correct(attempt)` on the persisted
  answer (MCQ compares `selected_option_id` to the snapshot answer key; other
  types compare score/points) and `progress()` reports
  `ability = _level_for(...)`, based on the last answered attempt. It does not
  depend on the release policy.

## 2. Controlled E2E (session 13, 3 MCQ, EASY band)

The correct option was looked up through the existing admin question-detail
endpoint before each submit, so the intended answers were genuinely known.

| Seq | Intended | Selected | Submit response `is_correct` | Ability after | Persisted score | Persisted `is_correct` |
|---|---|---|---|---|---|---|
| 1 | correct | correct option | null | 2.0 | 1.00 | true |
| 2 | wrong | wrong option | null | 1.0 | 0.00 | false |
| 3 | correct | correct option | null | 2.0 | 1.00 | true |

After `finish`: `status=completed`, `release_status=provisional_ai`,
`result_release_policy=HUMAN_VERIFIED`, `adaptive_progress.ability=2.0`.
`GET /api/v1/sessions/13/evidence` (learner token) returned score and
`grading_detail.is_correct` for all three items — the correct place to observe
grades while the result is provisional.

The earlier "ability always 1" observation came from choosing arbitrary MCQ
options (all wrong in that run) and from reading `is_correct` in the submit
response, which is hidden by design.

## 3. Regression test

`tests/test_ai_adaptive_practice.py::test_ability_moves_both_ways_and_grade_is_hidden_until_evidence`
(added in the Bug B commit) proves: EASY band difficulty 1 → 2 after a correct
answer → 1 after a wrong answer; submit response hides score/is_correct while
the Attempt rows hold `[1.00, 0.00, 1.00]` and `[true, false, true]`; session is
still unpublished. Result: **7 passed** in that module.

## 4. Correct way to observe

1. Submit answers; ignore hidden `is_correct`/`score` in the submit response.
2. Call `finish` and poll `GET /api/v1/sessions/{id}` until `status=completed`
   (retry jobs may still be pending for SQL/essay).
3. Read `GET /api/v1/sessions/{id}/evidence` with the learner token; or inspect
   `adaptive_progress.ability` in the session state to see difficulty up/down.

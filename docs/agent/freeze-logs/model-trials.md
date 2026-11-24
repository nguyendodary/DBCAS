# LLM model trials and Mode 2 E2E — 2026-11-24

Owner-requested verification. No application code was changed; only `LLM_MODEL`
(and, where needed, `OPENROUTER_MODEL`) in the local `.env` was changed per
trial. `.env` is not committed and no API key value is printed anywhere in this
report or in the logs. All trials use the project's own provider
(`app.services.llm.build_llm_service`) and validators
(`app.services.practice_generation.validate_generated`).

## Model existence (GET https://openrouter.ai/api/v1/models, HTTP 200, 438 ids)

| Model | Exists |
|---|---|
| `inclusionai/ling-3.2-flash:free` | exists |
| `recursive/flint-v1.0:free` | exists |
| `liquid/lfm-3-1.7b:free` | exists |
| `openrouter/free` | exists |

"Exists" means the id is returned by `/models`; it does not guarantee that a
chat-completion request will succeed. That is tested below.

## Trial 1 — `inclusionai/ling-3.2-flash:free`

### Direct generation (5 requests through the project provider)

| Case | HTTP | Time (s) | Valid JSON | Passed `validate_generated` |
|---|---|---|---|---|
| MCQ vi | 200 | 31.12 | yes | no (`generation_content`) |
| SQL SELECT vi | 429 | 0.61 | no | no (`llm_rate_limited`) |
| SQL DML vi | 429 | 0.96 | no | no (`llm_rate_limited`) |
| Essay vi | 429 | 0.77 | no | no (`llm_rate_limited`) |
| MCQ en | 429 | 0.78 | no | no (`llm_rate_limited`) |

429 rate 4/5 = 80%. JSON valid 1/5. Validation passed 0/5.

### Mode 2 E2E (mix 2 MCQ + 2 SQL + 2 essay, session 9)

| Question | Type | Source | Difficulty | Transition latency | Submit | `is_correct` | Ability |
|---|---|---|---|---|---|---|---|
| 1 | mcq | bank | 2 | 12 ms | 200 | null | 1 |
| 2 | sql | bank | 2 | 10 ms | 200 | null | 1 |
| 3 | essay | bank | 2 | 11 ms | 200 | null | 1 |
| 4 | mcq | bank | 2 | 12 ms | 200 | null | 1 |
| 5 | sql | bank | 2 | 13 ms | 200 | null | 1 |
| 6 | essay | bank | 2 | 13 ms | 200 | null | 1 |

AI questions 0 / bank 6. Final `ai_generated_count` 0. Average transition
11.8 ms — no AI call is made, so no prefetch benefit is observable. Answers
were deliberately first/last MCQ option, `SELECT 1;` vs `UPDATE ...;`, and
short vs detailed essay; `is_correct` stayed null and `adaptive_progress.ability`
stayed at 1, so no up/down difficulty step could be confirmed. This is a
grading-visibility limitation of the running stack, not a model result (the
same behaviour occurs with every model tried).

### Admin candidate check

Logged in as `admin@dbcas.local`. All five candidate status filters returned
HTTP 200 with `[]`. With 0 AI questions served, there was no candidate to
approve or reject; the approve/reject path cannot be exercised for this model.

### SQL UPDATE / DELETE execution

- Shared-sandbox path: `dataset_setup_failed` / `Could not prepare the SQL test dataset` (host `UndefinedObject`).
- Ephemeral (writable demo) path, verbatim for both UPDATE and DELETE:
  `sandbox_unavailable: SQL executor returned an invalid response` — the known
  host `docker exec` limitation recorded in `pytest-environment-limitation.log`.
- No grade could be produced because neither statement executed.

## Trial 2 — `recursive/flint-v1.0:free`

### Direct generation (5 requests through the project provider)

| Case | HTTP | Time (s) | Valid JSON | Passed validation |
|---|---|---|---|---|
| MCQ vi | 404 | 1.13 | no | no (`llm_provider_error`) |
| SQL SELECT vi | 404 | 0.55 | no | no |
| SQL DML vi | 404 | 0.55 | no | no |
| Essay vi | 404 | 0.59 | no | no |
| MCQ en | 404 | 0.59 | no | no |

The id is listed by `/models` but every chat-completion call returns
`The AI grading service rejected the request (HTTP 404)`. 429 rate 0/5 but
every request failed for a different reason; JSON valid 0/5; validation 0/5.

### Mode 2 E2E (session 10)

AI questions 0 / bank 6; `ai_generated_count` 0. Transition latencies
17, 11, 12, 13, 11, 18 ms (mean 13.7 ms). Submits HTTP 200, `is_correct`
null and ability stayed 1 for all six (same grading-visibility limitation as
trial 1). Intentionally wrong/right answers gave no observable difficulty step.

### Admin candidate check

All five candidate status filters: HTTP 200, `[]`. No candidate to approve or
reject.

### SQL UPDATE / DELETE execution

Re-running the same host trial produced the same verbatim result for both
statements: `sandbox_unavailable: SQL executor returned an invalid response`.
No grade produced. This result is model-independent.

## Trial 3 — `liquid/lfm-3-1.7b:free`

### Direct generation (5 requests through the project provider)

| Case | HTTP | Time (s) | Valid JSON | Passed validation |
|---|---|---|---|---|
| MCQ vi | 200 | 35.22 | no | no (`llm_invalid_response`, output budget exhausted) |
| SQL SELECT vi | 200 | 20.05 | no | no (output budget exhausted) |
| SQL DML vi | 200 | 21.32 | no | no (output budget exhausted) |
| Essay vi | 200 | 33.66 | no | no (output budget exhausted) |
| MCQ en | 200 | 17.93 | yes | no (`generation_type_fields`) |

429 rate 0/5. JSON valid 1/5. Validation passed 0/5. Latency 17.9–35.2 s,
well above the app's 10 s `AI_PRACTICE_TIMEOUT_SECONDS` budget.

### Mode 2 E2E (session 11)

AI questions 0 / bank 6; `ai_generated_count` 0. Transition latencies
13, 11, 12, 12, 11, 11 ms (mean 11.7 ms). The app log shows AI was attempted
and then fell back for each slot with reasons `GenerationRejected`,
`llm_invalid_response` ("AI response exhausted its output budget before
completion"), `generation_deadline` and `llm_rate_limited`; prefetch workers
also skipped. Submits HTTP 200, `is_correct` null, ability stayed 1 — no
observable difficulty step (same stack-level grading limitation).

### Admin candidate check

All five filters: HTTP 200, `[]`. No candidate to approve or reject.

### SQL UPDATE / DELETE execution

Same verbatim host error for both statements:
`sandbox_unavailable: SQL executor returned an invalid response`. No grade.

## Trial 4 — `openrouter/free`

### Direct generation (5 requests through the project provider)

| Case | HTTP | Time (s) | Valid JSON | Passed validation |
|---|---|---|---|---|
| MCQ vi | 200 | 21.56 | yes | no (`generation_content`) |
| SQL SELECT vi | 200 | 8.59 | yes | no (`generation_sql_fixture`) |
| SQL DML vi | 200 | 31.43 | yes | no (`generation_sql_fixture`) |
| Essay vi | 200 | 28.58 | yes | no (`generation_content`) |
| MCQ en | 200 | 20.85 | no | no (`llm_invalid_response`, output budget exhausted) |

429 rate 0/5. JSON valid 4/5 (best of the four). Validation passed 0/5.
Latency 8.6–31.4 s, again far above the app's 10 s generation budget.

### Mode 2 E2E (session 12)

AI questions 0 / bank 6; `ai_generated_count` 0. Transition latencies
15, 13, 12, 12, 13, 13 ms (mean 13.0 ms). Submits HTTP 200, `is_correct`
null, ability stayed 1 — same grading-visibility limitation.

### Admin candidate check

All five filters: HTTP 200, `[]`. No candidate to approve or reject.

### SQL UPDATE / DELETE execution

Same verbatim host error for both statements:
`sandbox_unavailable: SQL executor returned an invalid response`. No grade.

## Summary

| Model | Exists | 429 rate (direct) | Valid JSON | AI / bank (E2E) | Avg transition latency | DML runs | Conclusion |
|---|---|---|---|---|---|---|---|
| `inclusionai/ling-3.2-flash:free` | yes | 4/5 = 80% | 1/5 | 0 / 6 | 11.8 ms | no | **not usable** |
| `recursive/flint-v1.0:free` | yes | 0/5 (but 404 on 5/5) | 0/5 | 0 / 6 | 13.7 ms | no | **not usable** |
| `liquid/lfm-3-1.7b:free` | yes | 0/5 | 1/5 | 0 / 6 | 11.7 ms | no | **not usable** |
| `openrouter/free` | yes | 0/5 | 4/5 | 0 / 6 | 13.0 ms | no | **not usable** |

All four ids exist in `/models`, but none produced a single AI-served question
in six E2E questions. Failure modes differ: rate limiting (model 1), no
inference endpoint (model 2), output-budget truncation / deadline (model 3),
and syntactically valid JSON that fails the project's content and fixture
validators (model 4). Even the best raw JSON rate (4/5 for `openrouter/free`)
yielded 0 validated questions, and its 8.6–31.4 s latency exceeds the frozen
10 s `AI_PRACTICE_TIMEOUT_SECONDS`.

Cross-cutting observations that are **not** model results:
- With 0 AI questions served, the `question_candidate` queue stayed empty for
  every model, so no browser approve/reject could be performed. That path is
  covered by the T4 automated test in `test_ai_adaptive_practice.py`.
- Deliberate wrong/right answers did not change `adaptive_progress.ability`
  (stayed 1) and `is_correct` stayed null, so no up/down difficulty step could
  be confirmed for any model. This is a grading-visibility limitation of the
  running stack, not a provider result.
- Real UPDATE and DELETE could not be graded on this host: the writable
  sandbox returned verbatim
  `sandbox_unavailable: SQL executor returned an invalid response` for both
  statements in every trial, the same documented `docker exec` limitation as
  `pytest-environment-limitation.log`.

## Recommendation

**TẤT CẢ ĐỀU KHÔNG ĐẠT.** No model in this list can be recommended for Mode 2.
The acceptance bar was not lowered: a usable model must return valid JSON, pass
`validate_generated` for MCQ / SQL SELECT / SQL DML / essay in both locales,
serve AI questions inside the frozen 10 s budget, and survive the 6-question
E2E with a non-empty candidate queue. None did.

Keep the frozen configuration as-is (`LLM_MODEL` restored to the original
value) and keep Mode 2 on its documented reviewed-bank fallback for the demo.
Any future model change is a new owner-approved decision after the freeze, not
a substitution made to make this trial look successful.

## Mode 2 E2E trials

Pending.

## SQL UPDATE / DELETE execution trials

Pending.

## Summary and recommendation

Pending.

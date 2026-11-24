# Mode 2 LLM re-test — new model `deepseek/deepseek-v4.1-flash-free` (2026-11-24, fourth run)

Owner-requested re-test after another model change in `.env`. Current
configuration was used unchanged: `LLM_MODEL=deepseek/deepseek-v4.1-flash-free`,
`LLM_BASE_URL=https://api.orcarouter.ai/v1`, `LLM_PROVIDER=openrouter`,
`LLM_TIMEOUT_SECONDS=90`, `AI_PRACTICE_TIMEOUT_SECONDS=10`. No key was printed,
no code or LLM setting was changed, and nothing was committed. All earlier
sections of this report are preserved below.

## 1. Direct generation trials (5 requests)

| # | Case | HTTP status | Response time | Valid JSON | `validate_generated` | Error |
|---|---|---|---|---|---|---|
| 1 | MCQ Vietnamese | 200 | 10.896 s | yes | no | `GenerationRejected: generation_content` |
| 2 | SQL SELECT | none (timeout) | 30.423 s | no | not reached | `llm_timeout` — AI grading service timed out |
| 3 | SQL DML | none (timeout) | 30.494 s | no | not reached | `llm_timeout` |
| 4 | Essay | 200 | 24.814 s | yes | no | `GenerationRejected: generation_content` |
| 5 | MCQ English | 200 | 11.090 s | yes | no | `GenerationRejected: generation_content` |

- HTTP 429 in direct trials: 0/5 (the failure mode changed from the previous
  models' 429/404 to slow responses and content rejection).
- HTTP 200: 3/5. Valid JSON: 3/5. Validated questions: **0/5**.
- Mean response time across all 5: 21.5 s; across the three HTTP 200 cases:
  15.6 s. Every successful response exceeded the app's 10 s practice budget.
- The model exists on the configured base URL (`/models`, 215 ids). Published
  unit prices are `prompt=0`, `completion=0` (free tier).

## 2. Mode 2 E2E (8 questions per run, mix MCQ 4 + SQL 2 + essay 2)

Locale was controlled with the `Accept-Language` header used by
`routers/practice.py`.

### Vietnamese (`Accept-Language: vi`, session 18)

| Seq | Type | Source | Content locale | Transition | Intended | Ability after |
|---|---|---|---|---|---|---|
| 1 | mcq | bank | vi | 2040 ms | correct | 2.0 |
| 2 | sql | bank | vi | 2063 ms | probe | 1.0 |
| 3 | essay | bank | vi | 2042 ms | complete | 1.0 |
| 4 | mcq | bank | vi | 2078 ms | wrong | 1.0 |
| 5 | sql | bank | vi | 2044 ms | probe | 1.0 |
| 6 | essay | bank | vi | 2083 ms | complete | 1.0 |
| 7 | mcq | bank | vi | 2057 ms | correct | 2.0 |
| 8 | mcq | bank | vi | 2066 ms | wrong | 1.0 |

AI 0 / bank 8; mean transition 2059 ms; all 8 contents Vietnamese; final
ability 1.0; status `completed`; `ai_generated_count` 0.

### English (`Accept-Language: en`, session 19)

| Seq | Type | Source | Content locale | Transition | Intended | Ability after |
|---|---|---|---|---|---|---|
| 1 | mcq | bank | en | 2063 ms | correct | 2.0 |
| 2 | sql | bank | vi | 2057 ms | probe | 1.0 |
| 3 | essay | bank | en | 2061 ms | complete | 1.0 |
| 4 | mcq | bank | vi | 2060 ms | wrong | 1.0 |
| 5 | sql | bank | vi | 2052 ms | probe | 1.0 |
| 6 | essay | bank | vi | 2043 ms | complete | 1.0 |
| 7 | mcq | bank | vi | 2041 ms | correct | 2.0 |
| 8 | mcq | bank | vi | 2085 ms | wrong | 1.0 |

AI 0 / bank 8; mean transition 2058 ms; **only 2 of 8 contents English, 6
Vietnamese** — the English session was not fully localized. Because no AI
question was served, this is a bank-translation gap, not a model translation.
Final ability 1.0; status `completed`.

### Ability and difficulty

Both runs show the documented pattern: correct MCQ → ability 2.0, wrong answer
→ 1.0 (`2→1→1→1→1→1→2→1`). Served question difficulty stayed at 2 since the
bank fallback had no AI-generated level-matched item. All 16 submits returned
HTTP 200; `is_correct` stayed null in submit responses as required by the
HUMAN_VERIFIED release rule (`bug-b-grade-visibility.md`).

App logs show every E2E generation attempt fell back with
`reason=llm_rate_limited detail=AI grading is rate-limited` — so although the
direct trial saw 0% 429, the E2E phase was effectively 100% rate-limited after
the direct calls consumed the free-tier quota. `generation_fallback` stayed
`false` despite 0 AI questions; the authoritative fields are `source` and
`ai_generated_count`.

## 3. Admin candidate verification

| Check | Result |
|---|---|
| AI-generated questions in `question_candidate` | None — 0 AI questions served |
| `GET /admin/question-candidates` (all/pending/validated/approved/rejected) | HTTP 200, `[]` for every filter |
| Approve 1 candidate | **Skipped** — no candidate existed; endpoint not called |
| Reject 1 candidate | **Skipped** — no candidate existed; endpoint not called |
| State after | Queues still empty; no candidate IDs to report |

Blocked by upstream generation failures, not by the candidate workflow. That
path is covered by the T4 automated test.

## 4. SQL DML trial

No AI-generated SQL DML question was produced, so the "use a genuinely
AI-generated question" requirement could not be met. Safe supplementary check
on the disposable writable sandbox (fresh schema, always rolled back, no
production data):

| Statement | Executed | Rolled back | Resulting table state | Score | Grader |
|---|---|---|---|---|---|
| `UPDATE dml_items SET name='gamma' WHERE id=2;` | yes | yes | `[[1,'alpha'],[2,'gamma'],[3,'gamma']]` | 5.00/5.00 | `sql_semantic` |
| `DELETE FROM dml_items WHERE id=2;` | yes | yes | `[[1,'alpha'],[3,'gamma']]` | 5.00/5.00 | `sql_semantic` |

Source: reviewed bank fixture `db/dml_practice_pack.json`, **not** an AI
question; the AI-specific DML sub-item remains blocked.

## 5. Comparison with the previous model (`google/gemma-4-31b-it:free`)

| Metric | Previous model (`gemma-4-31b-it:free`) | New model (`deepseek-v4.1-flash-free`) |
|---|---|---|
| Base URL | openrouter.ai | api.orcarouter.ai |
| Exists in `/models` | yes | yes (215 ids) |
| Direct 429 rate | 0% (100% 404) | 0% in direct, ~100% in E2E logs |
| Direct HTTP status | 404 on 5/5 | 200 on 3/5, timeout on 2/5 |
| Successful generations | 0/5 | 3/5 returned JSON but 0 usable |
| Valid JSON | 0/5 | 3/5 |
| `validate_generated` | 0/5 (not reached) | 0/5 (`generation_content`) |
| Direct response time | 0.53–1.12 s | 10.9–30.5 s (mean 21.5 s) |
| E2E AI / bank | 0 / 16 | 0 / 16 |
| E2E avg transition | 2038 ms (vi), 2045 ms (en) | 2059 ms (vi), 2058 ms (en) |
| Ability up/down | observed | observed |
| English content coverage | 2/8 en, 6/8 vi | 2/8 en, 6/8 vi |
| Admin | empty / skipped / skipped | empty / skipped / skipped |
| SQL DML | bank fixture, 5.00/5.00 | bank fixture, 5.00/5.00 |
| Cost per session | N/A (free tier 0/0, not assumed) | N/A (free tier 0/0, not assumed) |

This model is the first to return usable JSON, but content validation rejected
every object, SQL requests timed out, and the E2E phase was rate-limited — so
no AI question was ever served.

## 6. Conclusion

**The new model does not meet the Mode 2 requirement.**

- Met: reviewed-bank fallback kept all 16 E2E submits working; ability rises and
  falls correctly; disposable UPDATE/DELETE grading works (5.00/5.00); admin
  reads return cleanly; some responses arrive as valid JSON.
- Not met: 0/5 questions passed `validate_generated`; 2/5 direct requests timed
  out at 30 s; 0 AI questions in 16 E2E questions; no candidate to
  approve/reject; DML with an AI-generated question impossible; English session
  only 2/8 in English.
- Concrete causes: (1) generated objects fail the project's content validator
  (`generation_content`) for MCQ (vi and en) and essay; (2) both SQL requests
  exceed the 30 s provider call budget; (3) the free-tier quota was exhausted
  during testing, so all E2E attempts fell back with `llm_rate_limited`.
- **Timeout recommendation (not applied):** successful responses took 10.9–24.8
  s, all above the frozen `AI_PRACTICE_TIMEOUT_SECONDS=10`. If a model with
  passing validation is chosen, set it to at least **30 s** (e.g. 30–35 s) so
  generation is not cut off; also raise `LLM_TIMEOUT_SECONDS` above the SQL
  request latency. This alone will not fix the current content-validation or
  rate-limit failures. No timeout was changed.

## 7. Completion status and final state

- **Ran:** 5 direct requests; two 8-question Mode 2 E2E sessions (vi and en)
  with per-submit ability and content-language observation; admin queue reads;
  disposable sandbox UPDATE/DELETE grading; `/models` existence and pricing
  lookup; app-log fallback diagnosis.
- **Not run / blocked:** admin approve 1 and reject 1 (no candidate); DML using
  an AI-generated question (none generated); numeric cost estimate (N/A by rule).
- **Skipped:** no config, key, code or commit changes.
- **Final state:** `.env` SHA-256 unchanged from the start of this re-test
  (`FEB755DBFF102C9C4887E7AF7C422814A88B468297667B8E6EE13A33B2E31E61`). Git
  status: only `docs/agent/freeze-logs/model-trials.md` is modified relative to
  `ab06d14`; all earlier report sections are retained verbatim below. No commit
  was made.

---

# Previous report — third run (`google/gemma-4-31b-it:free`)

The content below is preserved from the previous run.

# Mode 2 LLM re-test — new model `google/gemma-4-31b-it:free` (2026-11-24, third run)

Owner-requested re-test after the model change in `.env`. Current configuration
was used unchanged: `LLM_MODEL=google/gemma-4-31b-it:free`,
`LLM_BASE_URL=https://openrouter.ai/api/v1`, `LLM_PROVIDER=openrouter`,
`LLM_TIMEOUT_SECONDS=90`, `AI_PRACTICE_TIMEOUT_SECONDS=10`. No key was printed,
no code or LLM setting was changed, and nothing was committed. The earlier
sections of this report are preserved below.

## 1. Direct generation trials (5 requests)

| # | Case | HTTP status | Response time | Valid JSON | `validate_generated` | Error |
|---|---|---|---|---|---|---|
| 1 | MCQ Vietnamese | 404 | 1.116 s | no | not reached | `llm_provider_error` — request rejected (HTTP 404) |
| 2 | MCQ English | 404 | 0.527 s | no | not reached | `llm_provider_error` |
| 3 | SQL SELECT | 404 | 0.599 s | no | not reached | `llm_provider_error` |
| 4 | SQL DML | 404 | 0.569 s | no | not reached | `llm_provider_error` |
| 5 | Essay | 404 | 0.547 s | no | not reached | `llm_provider_error` |

Successful generations 0/5. Valid JSON 0/5. Validated questions 0/5.
The id **exists** in `GET /models` (438 ids), but no chat-completion request can
be served — the same failure mode as `recursive/flint-v1.0:free` in the earlier
trial. Published unit prices: `prompt=0`, `completion=0` (free tier).

## 2. Mode 2 E2E (8 questions per run, mix MCQ 4 + SQL 2 + essay 2)

Locale was controlled with the `Accept-Language` header used by
`routers/practice.py`.

### Vietnamese (`Accept-Language: vi`, session 16)

| Seq | Type | Source | Content locale | Transition | Intended | Ability after |
|---|---|---|---|---|---|---|
| 1 | mcq | bank | vi | 2036 ms | correct | 2.0 |
| 2 | sql | bank | vi | 2031 ms | probe | 1.0 |
| 3 | essay | bank | vi | 2039 ms | complete | 1.0 |
| 4 | mcq | bank | vi | 2031 ms | wrong | 1.0 |
| 5 | sql | bank | vi | 2038 ms | probe | 1.0 |
| 6 | essay | bank | vi | 2036 ms | complete | 1.0 |
| 7 | mcq | bank | vi | 2045 ms | correct | 2.0 |
| 8 | mcq | bank | vi | 2045 ms | wrong | 1.0 |

AI 0 / bank 8; mean transition 2038 ms; all 8 contents in Vietnamese; final
ability 1.0, status `completed`, `ai_generated_count` 0.

### English (`Accept-Language: en`, session 17)

| Seq | Type | Source | Content locale | Transition | Intended | Ability after |
|---|---|---|---|---|---|---|
| 1 | mcq | bank | en | 2052 ms | correct | 2.0 |
| 2 | sql | bank | vi | 2050 ms | probe | 1.0 |
| 3 | essay | bank | en | 2034 ms | complete | 1.0 |
| 4 | mcq | bank | vi | 2037 ms | wrong | 1.0 |
| 5 | sql | bank | vi | 2046 ms | probe | 1.0 |
| 6 | essay | bank | vi | 2038 ms | complete | 1.0 |
| 7 | mcq | bank | vi | 2045 ms | correct | 2.0 |
| 8 | mcq | bank | vi | 2055 ms | wrong | 1.0 |

AI 0 / bank 8; mean transition 2045 ms; **only 2 of 8 contents were English, 6
were Vietnamese** — the English session was not fully localized. This comes
from missing bank translations (no AI questions were generated), not from the
model. Final ability 1.0, status `completed`.

### Ability and difficulty

Both runs show the documented pattern: correct MCQ → ability 2.0, wrong answer
→ 1.0 (`2→1→1→1→1→1→2→1`). Served question difficulty stayed at 2 because the
bank fallback had no AI-generated, level-matched question. All 16 submits
returned HTTP 200; `is_correct` remained null in submit responses as required by
the HUMAN_VERIFIED release rule (see `bug-b-grade-visibility.md`).

Note: `generation_fallback` stayed `false` even with `ai_generated_count=0` and
all sources `bank`; the authoritative indicators are `source` and
`ai_generated_count`, not that flag.

## 3. Admin candidate verification

| Check | Result |
|---|---|
| AI-generated questions in `question_candidate` | None — 0 AI questions served in either run |
| `GET /admin/question-candidates` (all/pending/validated/approved/rejected) | HTTP 200, `[]` for every filter |
| Approve 1 candidate | **Skipped** — no candidate existed; endpoint not called |
| Reject 1 candidate | **Skipped** — no candidate existed; endpoint not called |
| State after | Queues still empty; no candidate IDs to report |

Blocked by the upstream HTTP 404s, not by a candidate-workflow defect. The
approve/reject path is covered by the T4 automated test.

## 4. SQL DML trial

No AI-generated SQL DML question was produced, so the "use a genuinely
AI-generated question" requirement could not be satisfied. As a safe
supplementary check, the reviewed disposable DML fixture was executed in the
writable ephemeral sandbox (fresh schema, always rolled back, no production
data):

| Statement | Executed | Rolled back | Resulting table state | Score | Grader |
|---|---|---|---|---|---|
| `UPDATE dml_items SET name='gamma' WHERE id=2;` | yes | yes | `[[1,'alpha'],[2,'gamma'],[3,'gamma']]` | 5.00/5.00 | `sql_semantic` |
| `DELETE FROM dml_items WHERE id=2;` | yes | yes | `[[1,'alpha'],[3,'gamma']]` | 5.00/5.00 | `sql_semantic` |

Source: `db/dml_practice_pack.json` (reviewed bank), **not** an AI question. The
AI-specific DML sub-item remains blocked.

## 5. Comparison with the previous model (`dots-studio/dots-3-note-preview:free`)

| Metric | Previous model | New model (`gemma-4-31b-it:free`) |
|---|---|---|
| Exists in `/models` | yes | yes |
| Direct HTTP status | 429 on 5/5 | 404 on 5/5 |
| 429 rate | 100% | 0% (replaced by 100% 404) |
| Successful generations | 0/5 | 0/5 |
| Valid JSON | 0/5 | 0/5 |
| `validate_generated` | 0/5 (not reached) | 0/5 (not reached) |
| E2E AI / bank | 0 / 16 | 0 / 16 |
| E2E avg transition | 2046 ms (vi), 2041 ms (en) | 2038 ms (vi), 2045 ms (en) |
| Ability up/down | 2→1, 1→2 observed | 2→1, 1→2 observed |
| English content coverage | 3/8 en, 5/8 vi | 2/8 en, 6/8 vi |
| Admin queue / approve / reject | empty / skipped / skipped | empty / skipped / skipped |
| SQL DML | bank fixture, 5.00/5.00 | bank fixture, 5.00/5.00 |
| Cost per session | N/A (free tier 0/0 published, not assumed) | N/A (same) |

The failure mode changed (rate limiting → unusable endpoint), but every
acceptance-relevant outcome is unchanged: no AI question was ever generated or
served.

## 6. Conclusion

**The new model does not meet the Mode 2 requirement.**

- Met: the reviewed-bank fallback keeps all 16 E2E submits working; ability
  moves correctly on wrong/correct answers; disposable UPDATE/DELETE grading
  works (5.00/5.00); admin reads return cleanly.
- Not met: 0/5 direct generations; 0 AI questions in 16 E2E questions; no
  candidate to approve/reject; DML with an AI-generated question impossible;
  English session not fully localized.
- Cause: the model id is listed by OpenRouter but every chat-completion request
  is rejected with HTTP 404, so the project's provider never receives a
  completion to parse or validate.
- Do **not** change `AI_PRACTICE_TIMEOUT_SECONDS`: failures arrive in 0.5–1.1 s
  as 404 responses, not timeouts; a longer budget would not help. Use a model
  with a working chat endpoint and available quota, then re-run these gates.
  Standards were not lowered.

## 7. Completion status and final state

- **Ran:** 5 direct requests; two 8-question Mode 2 E2E sessions (vi and en)
  with per-submit ability observation and content-language checks; admin queue
  reads; disposable sandbox UPDATE/DELETE grading; `/models` existence and
  pricing lookup.
- **Not run / blocked:** admin approve 1 and reject 1 (no candidate); DML using
  an AI-generated question (none generated); numeric cost estimate (N/A by rule).
- **Skipped:** no config, key, code or commit changes.
- **Final state:** `.env` SHA-256 unchanged from the start of this re-test
  (`7D86FFC1E2A6CF9F1036E2F1580F40CFFEBFAD7B7BCC6FFAAFDD8D7A17209E15`). Git
  status: only `docs/agent/freeze-logs/model-trials.md` is modified relative to
  `ab06d14`; all earlier report sections are retained verbatim below. No commit
  was made.

---

# Previous report — second run (`dots-studio/dots-3-note-preview:free`)

The content below is preserved from the previous run.

# Current LLM configuration — Mode 2 verification (2026-11-24, second run)

Owner-requested verification against the **current, unchanged** `.env`. No
application code was changed, no LLM setting was changed, no key was requested
or printed, and nothing was committed. All calls go through the project's own
provider (`app.services.llm.build_llm_service`) and validator
(`app.services.practice_generation.validate_generated`).

Configuration read from `.env` (values that are not secret):
`LLM_MODEL=dots-studio/dots-3-note-preview:free`,
`LLM_BASE_URL=https://openrouter.ai/api/v1`, `LLM_PROVIDER=openrouter`,
`LLM_TIMEOUT_SECONDS=90`, `AI_PRACTICE_TIMEOUT_SECONDS=10`,
`AI_PRACTICE_PREFETCH=true`. Key presence: configured (value never printed).

## 1. Direct generation trials (5 requests)

| # | Case | HTTP status | Response time | Valid JSON | `validate_generated` | Error |
|---|---|---|---|---|---|---|
| 1 | MCQ Vietnamese | 429 | 1.303 s | no | not reached | `llm_rate_limited` — AI grading is rate-limited |
| 2 | MCQ English | 429 | 0.580 s | no | not reached | `llm_rate_limited` |
| 3 | SQL SELECT | 429 | 0.655 s | no | not reached | `llm_rate_limited` |
| 4 | SQL DML | 429 | 0.855 s | no | not reached | `llm_rate_limited` |
| 5 | Essay | 429 | 0.542 s | no | not reached | `llm_rate_limited` |

429 rate: 5/5 = 100%. Valid JSON: 0/5. Validated questions: 0/5.

## 2. Mode 2 E2E (8 questions per run, mix MCQ 4 + SQL 2 + essay 2)

Locale was set with the `Accept-Language` header, which is what
`routers/practice.py` uses to populate `session.locale`.

### Vietnamese (`Accept-Language: vi`, session 14)

| Seq | Type | Source | Content locale | Transition | Intended answer | Ability after |
|---|---|---|---|---|---|---|
| 1 | mcq | bank | vi | 2047 ms | correct | 2.0 |
| 2 | sql | bank | vi | 2048 ms | probe `SELECT 1;` | 1.0 |
| 3 | essay | bank | vi | 2039 ms | complete | 1.0 |
| 4 | mcq | bank | vi | 2064 ms | wrong | 1.0 |
| 5 | sql | bank | vi | 2045 ms | probe | 1.0 |
| 6 | essay | bank | vi | 2042 ms | complete | 1.0 |
| 7 | mcq | bank | vi | 2032 ms | correct | 2.0 |
| 8 | mcq | bank | vi | 2054 ms | wrong | 1.0 |

Start locale `vi`; `ai_generated_count` 0; `generation_fallback` false (that flag
is not a per-question AI indicator — the `source` fields and `ai_generated_count`
are authoritative). Final status `completed`, ability 1.0.

### English (`Accept-Language: en`, session 15)

| Seq | Type | Source | Content locale | Transition | Intended answer | Ability after |
|---|---|---|---|---|---|---|
| 1 | mcq | bank | en | 2015 ms | correct | 2.0 |
| 2 | sql | bank | vi | 2036 ms | probe | 1.0 |
| 3 | essay | bank | en | 2039 ms | complete | 1.0 |
| 4 | mcq | bank | vi | 2036 ms | wrong | 1.0 |
| 5 | sql | bank | vi | 2042 ms | probe | 1.0 |
| 6 | essay | bank | vi | 2058 ms | complete | 1.0 |
| 7 | mcq | bank | vi | 2061 ms | correct | 2.0 |
| 8 | mcq | bank | vi | 2044 ms | wrong | 1.0 |

Start locale `en`; `ai_generated_count` 0. Final status `completed`, ability 1.0.
**Finding:** 5 of 8 questions in the English session were served with `vi`
content from the bank (missing English translations), so the session was not
fully English.

### E2E summary

| Run | AI questions | Bank questions | Avg transition | Ability path | Difficulty observation |
|---|---|---|---|---|---|
| Vietnamese (session 14) | 0 | 8 | 2046 ms | 2→1→1→1→1→1→2→1 | ability rises on correct, falls on wrong; served bank questions stayed at difficulty 2 |
| English (session 15) | 0 | 8 | 2041 ms | 2→1→1→1→1→1→2→1 | same; no AI question available to generate a level-matched item |

Ability was observed exactly as documented in `bug-b-grade-visibility.md`:
`adaptive_progress.ability` from `GET /sessions/{id}` after each submit, with
answer keys looked up through the admin question-detail endpoint. All 16 submits
returned HTTP 200; `is_correct` stayed null in submit responses because of the
HUMAN_VERIFIED release rule (expected, see that log).

## 3. Admin candidate verification

| Check | Result |
|---|---|
| AI question present in `question_candidate` | **No** — 0 AI questions were generated, so none could be queued |
| `GET /admin/question-candidates` (all, pending, validated, approved, rejected) | HTTP 200, each returned `[]` |
| Approve 1 candidate | **Skipped** — no candidate exists; approve endpoint was not called |
| Reject 1 candidate | **Skipped** — no candidate exists; reject endpoint was not called |
| State after | Queues unchanged, still empty; no candidate IDs to report |

This sub-item is blocked by the upstream 429s, not by a candidate-workflow error.
The approve/reject path itself is covered by the T4 automated test
(`backend/tests/test_ai_adaptive_practice.py`).

## 4. SQL DML trial

No AI-generated SQL DML question was produced in either E2E run, so the
"use the AI-generated question" requirement could not be met. As a safe
supplementary check, the project's disposable DML fixture was executed in the
writable ephemeral sandbox (`dml_items`, fresh schema, always rolled back; no
production data touched):

| Statement | Executed | Rolled back | Resulting table state | Score | Grader |
|---|---|---|---|---|---|
| `UPDATE dml_items SET name='gamma' WHERE id=2;` | yes | yes | `[[1,'alpha'],[2,'gamma'],[3,'gamma']]` | 5.00/5.00 | `sql_semantic` |
| `DELETE FROM dml_items WHERE id=2;` | yes | yes | `[[1,'alpha'],[3,'gamma']]` | 5.00/5.00 | `sql_semantic` |

Source of these fixtures: reviewed demo bank (`db/dml_practice_pack.json`),
**not** an AI-generated question. This sub-item is therefore reported as
partially covered, with the AI-specific part blocked.

## 5. Cost estimate

`GET /models` reports published unit prices `prompt=0`, `completion=0` for this
free-tier model. Per the instruction not to assume zero cost, and because no
reliable paid-tier price exists for this model, the estimated monetary cost per
session is **N/A**. No token-usage-based figure is claimed. The practical
constraint observed was rate limiting (HTTP 429), not price.

## 6. Summary table

| Item | Result |
|---|---|
| HTTP status (direct) | 429 on all 5 requests |
| Response time (direct) | 0.542–1.303 s |
| Valid JSON (direct) | 0/5 |
| `validate_generated` (direct) | 0/5 (not reached) |
| E2E Vietnamese | 8 questions, 0 AI / 8 bank, 2046 ms avg |
| E2E English | 8 questions, 0 AI / 8 bank, 2041 ms avg; 5 questions served in vi |
| AI/bank ratio | 0/16 AI, 16/16 bank across both runs |
| Transition latency | ~2.04 s in both runs (429 retry/backoff before fallback) |
| Difficulty / ability | Ability 2→1 (wrong), 1→2 (correct) in both runs; served difficulty unchanged at 2 |
| Admin | Queue empty; approve/reject skipped (no candidate) |
| SQL DML | Bank fixture UPDATE/DELETE both graded 5.00/5.00; AI-question DML blocked |
| Cost per session | N/A (free-tier published price 0/0; not assumed as zero) |
| Errors | 5× `llm_rate_limited` (HTTP 429) |

## 7. Recommendation

**The current model does not meet the Mode 2 requirement.** It produced no
valid JSON, no validated question, and zero AI-served questions in 16 E2E
questions; the admin candidate path could not be exercised. Failure criteria:
100% HTTP 429 on direct generation, 0 AI questions in both E2E sessions, no
candidate to review.

Do **not** change `AI_PRACTICE_TIMEOUT_SECONDS`: the failures are rate-limit
rejections in ~0.5–1.3 s, not slow responses, so a larger timeout would not help.
Improvements: use a provider plan/model with available quota (or wait for the
free-tier quota window to reset) and re-run the same gates; keep the reviewed-bank
fallback so learners are unaffected. Standards were not lowered.

## 8. Completion status and final state

- **Ran:** 5 direct generation requests; two 8-question Mode 2 E2E sessions (vi
  and en) with ability observation; admin candidate queue reads; disposable
  sandbox UPDATE/DELETE grading; published-price lookup.
- **Not run / blocked:** admin approve 1 and reject 1 (no candidate existed);
  DML using an AI-generated question (no AI question existed); numeric cost
  estimate (N/A by rule).
- **Skipped:** no LLM configuration change, no API key request, no app code
  change, no commit.
- **Final state:** `.env` SHA-256 unchanged
  (`FF1D8B8393B3DDD57D27A5F84331E10EE3299990C5AE9C8D76AD1397220AB46F` before
  and after); Git tree has only this report file modified relative to `ab06d14`;
  no commit was made.

---

# Appendix — earlier four-model trials (previous task, committed at `44bd175`)

The content below is retained from the previous owner-requested trial and is
not part of the current-config results above.

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

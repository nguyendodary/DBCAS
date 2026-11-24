# Mode 2 verification with the current `.env` provider (2026-11-24)

Owner-requested verification. No application code changed, `.env` not committed
or edited, no API key printed. Configuration read from `.env`:
`LLM_MODEL=deepseek-v4-1-flash-1017`, `LLM_BASE_URL=https://api.mistral.ai/v1`,
`LLM_PROVIDER=Mistral` (reported as unknown and normalized to
`openai_compatible` with a warning), `AI_PRACTICE_TIMEOUT_SECONDS=10`.
`.env` SHA-256 at start and end: `2FC8D20C1C591559DCA07CCA50607C417EC93342F869B507DFB82D338FC91D26`.

## 1. Direct generation — 5 types x 3 repetitions through the project provider

Calls used `LLMService.generate_structured` with the project's
`GeneratedQuestion` JSON schema and the real `ai_practice` prompt, then
`validate_generated`. Every call first received HTTP 422 on the optional fields
(`max_tokens,response_format,seed`) and succeeded on the single generic retry
without them — the retry worked, but the returned object never matched the
project schema. "JSON" below means the HTTP response parsed as JSON; none of the
objects passed the project's schema/`validate_generated`.

| Case | Rep | HTTP | Time (s) | JSON parsed | Passed validate | Specific reason | Rejected content (short) |
|---|---|---|---|---|---|---|---|
| MCQ vi | 1 | 200 (after 422) | 3.060 | yes | no | `llm_invalid_response` — invalid field at root `response` | `question:` "Câu lệnh SQL nào ... thêm bản ghi mới?"; options are strings |
| MCQ vi | 2 | 200 | 3.448 | yes | no | same | same shape: `question` instead of `prompt`, string options |
| MCQ vi | 3 | 200 | 3.355 | yes | no | same | same shape |
| MCQ en | 1 | 200 | 2.314 | yes | no | same | `question:` "Which SQL statement is used to add a new row ...?"; string options |
| MCQ en | 2 | 200 | 2.834 | yes | no | same | same shape |
| MCQ en | 3 | 200 | 3.422 | yes | no | same | same shape |
| SQL SELECT | 1 | 200 | 3.950 | yes | no | same | `question:` "Cho bảng products ... hãy viết một câu lệnh SQL"; no `prompt` |
| SQL SELECT | 2 | 200 | 3.717 | yes | no | same | same shape; setup_sql/edge_setup_sql/tables present |
| SQL SELECT | 3 | 200 | 3.623 | yes | no | same | same shape |
| SQL DML | 1 | 200 | 7.878 | yes | no | same | `question:` "Cho bảng products (product_id, product_name, ...)"; no `prompt` |
| SQL DML | 2 | 200 | 4.790 | yes | no | same | same shape |
| SQL DML | 3 | 200 | 5.187 | yes | no | same | same shape |
| Essay | 1 | 200 | 4.508 | yes | no | same | `question:` "Cho bảng nhan_vien (ma_nv, ho_ten, luong, ...)"; no `prompt` |
| Essay | 2 | 200 | 4.710 | yes | no | same | same shape |
| Essay | 3 | 200 | 4.909 | yes | no | same | same shape |

Timing: min 2.314 s, median 3.717 s, mean 4.11 s, max 7.878 s.
Successful generations: 0/15. Valid JSON (schema-valid): 0/15. `validate_generated`: 0/15.
All 15 responses were HTTP 200 after the optional-field retry, so 429 was **not**
the cause in the direct phase.

### Prompt vs validator — concrete diagnosis (no validator change)

A separate diagnostic captured the raw generated objects for all five cases.
Every object had:

- extra key `question` and **missing required key `prompt`** (root schema has
  `additionalProperties: false` and `prompt` required);
- MCQ `options` as a list of **strings**, while `GeneratedOption` requires
  `{text, correct}` objects.

| Case | Extra keys vs schema | Missing required keys | `options` element type |
|---|---|---|---|
| MCQ vi | `question` | `prompt` (plus type-specific `options`/`rubrics`/`setup_sql`) | `str` |
| MCQ en | `question` | `prompt` | `str` |
| SQL SELECT | `question` | `prompt`, `options`, `rubrics` | n/a |
| SQL DML | `question` | `prompt`, `options`, `rubrics` | n/a |
| Essay | `question` | `prompt`, `options`, `setup_sql`, `edge_setup_sql`, `tables` | n/a |

Evidence excerpt (MCQ vi, shortened):
`{"concept_ids":[16],"question_type":"mcq","difficulty_level":2,"question":"Câu lệnh SQL nào ... thêm bản ghi mới vào bảng?","options":["INSERT INTO","UPDATE","DELETE FROM","SELECT"], ...}`

The generation prompt (`app/services/ai_adaptive.py::_prompt`) says "Return one
JSON object with concept_ids ..., question_type ..., difficulty_level ..., a
non-empty explanation, source_refs, reference_answer and points" and asks for
"exactly four options", but it **never names the required field `prompt`** nor
the `{text, correct}` option shape. The model therefore used the natural word
`question` and plain option strings. The validator is behaving correctly: it
enforces the documented strict schema; the defect is in the **prompt/schema
contract**, not in over-strict validation. No validator or prompt code was
changed in this task, as required.

## 2. Mode 2 E2E (mix MCQ 4 + SQL 2 + essay 2, 8 questions per run)

### Vietnamese (`Accept-Language: vi`, session 20)

| Seq | Type | Source | Content locale | Transition | Intended | Ability after |
|---|---|---|---|---|---|---|
| 1 | mcq | bank | vi | 2083 ms | correct | 2.0 |
| 2 | sql | bank | vi | 2073 ms | probe | 1.0 |
| 3 | essay | bank | vi | 2073 ms | complete | 1.0 |
| 4 | mcq | bank | vi | 2033 ms | wrong | 1.0 |
| 5 | sql | bank | vi | 2027 ms | probe | 1.0 |
| 6 | essay | bank | vi | 2053 ms | complete | 1.0 |
| 7 | mcq | bank | vi | 2037 ms | correct | 2.0 |
| 8 | mcq | bank | vi | 2062 ms | wrong | 1.0 |

AI 0 / bank 8; mean transition 2055 ms; ability path `2→1→1→1→1→1→2→1`
(up on correct MCQ, down on wrong MCQ).

### English (`Accept-Language: en`, session 21)

| Seq | Type | Source | Content locale | Transition | Intended | Ability after |
|---|---|---|---|---|---|---|
| 1 | mcq | bank | en | 2054 ms | correct | 2.0 |
| 2 | sql | bank | vi | 2053 ms | probe | 1.0 |
| 3 | essay | bank | en | 2052 ms | complete | 1.0 |
| 4 | mcq | bank | vi | 2025 ms | wrong | 1.0 |
| 5 | sql | bank | vi | 2041 ms | probe | 1.0 |
| 6 | essay | bank | vi | 2046 ms | complete | 1.0 |
| 7 | mcq | bank | vi | 2088 ms | correct | 2.0 |
| 8 | mcq | bank | vi | 2076 ms | wrong | 1.0 |

AI 0 / bank 8; mean transition 2054 ms; same ability path. **Only 2 of 8
contents were English; 6 were Vietnamese bank items** — a bank-translation gap,
not a model translation failure (no AI item was served).

App logs show each E2E generation attempt fell back with
`reason=llm_rate_limited detail=AI grading is rate-limited` after the direct
trials consumed the free-tier quota. `generation_fallback` stayed `false`;
`source` and `ai_generated_count` are authoritative.

## 3. Admin candidate verification

| Check | Result |
|---|---|
| AI-generated questions in `question_candidate` | none — 0 AI questions served |
| `GET /admin/question-candidates` all/pending/validated/approved/rejected | HTTP 200, `[]` in every filter |
| Approve 1 candidate | **not run** — no candidate existed; endpoint not called |
| Reject 1 candidate | **not run** — no candidate existed; endpoint not called |
| State after | queues still empty; no candidate IDs |

This item is blocked by the upstream schema failures and 429s, not by the
candidate workflow (which remains covered by T4 automated tests).

## 4. SQL UPDATE / DELETE

No AI-generated SQL DML question was ever served, so an UPDATE/DELETE **from an
AI question could not be executed**. As a clearly-labelled supplementary check
using the reviewed demo fixture in the disposable writable sandbox (fresh
schema, always rolled back, no production data):

| Statement | Executed | Rolled back | Grade | Grader |
|---|---|---|---|---|
| `UPDATE dml_items SET name='gamma' WHERE id=2;` | yes | yes | 5.00/5.00 | `sql_semantic` |
| `DELETE FROM dml_items WHERE id=2;` | yes | yes | 5.00/5.00 | `sql_semantic` |

Source: `db/dml_practice_pack.json`, **not** AI-generated. The AI-specific DML
requirement remains unmet.

## 5. Tokens and estimated cost

Direct 15-call token usage from provider `usage` (measured, not estimated):

| Case | Prompt tokens | Completion tokens | Total tokens (min–max) |
|---|---|---|---|
| MCQ vi | 126 | 184–186 | 310–312 |
| MCQ en | 126 | 195–200 | 321–326 |
| SQL SELECT | 187 | 298–538 | 485–725 |
| SQL DML | 191 | 651–707 | 842–898 |
| Essay | 130 | 718–843 | 848–973 |
| **Total (15 calls)** | — | — | **9,082** |

Per E2E session tokens: **N/A** — the application API does not expose provider
`usage` per served question, so no per-session token figure can be claimed
without inventing data. The free-tier quota was consumed during testing, which
is why E2E attempts returned 429.

Cost per session: **N/A**. `GET https://api.mistral.ai/v1/models` returns no
`pricing` object for `deepseek-v4-1-flash-1017` (`pricing: {}`); there is no
reliable price data to multiply by the measured tokens. Zero is not assumed.

## 6. Conclusion and timeout proposal

Met: generic provider call works (HTTP 200 after the optional-field retry),
bank fallback keeps both E2E sessions functional, ability moves up/down
correctly, disposable DML grading works with the reviewed fixture.

Not met: 0/15 direct generations pass schema or `validate_generated`; 0 AI
questions in 16 E2E questions; no admin candidate to approve/reject; no
AI-generated UPDATE/DELETE; English session only 2/8 in English.

Timeout proposal (**not applied**): measured direct latency is 2.3–7.9 s (mean
4.1 s); the app's 10 s `AI_PRACTICE_TIMEOUT_SECONDS` already covers these calls.
A value of **15 s** would leave headroom for a 422 optional-field retry plus a
slow SQL/essay response, but raising it will not fix the real blockers: the
prompt/schema field mismatch and the free-tier 429s. No timeout was changed.

Failure priority: (1) generation prompt does not instruct the model to emit the
required `prompt` field and `{text, correct}` option objects — fix belongs in
the prompt contract, not in the validator; (2) the configured free-tier quota
is exhausted after a handful of calls. The validator correctly rejected every
malformed object and was not loosened.

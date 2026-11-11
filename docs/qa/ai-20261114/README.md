# New AI model validation — 2026-11-14

## Configuration loaded by the application

`npm start` reads `_worktrees/dbcas-dn-20261101/.env` (the same file the
Compose app uses). No value below is a key.

| Item | Verified value |
| --- | --- |
| Model | `baidu/ernie-5.5-flash-preview:free` |
| Base host | `openrouter.ai` |
| API key | present, `sk-...95bd` (masked) |
| Practice generation timeout | 90 s provider budget, 0 retries |
| Generation validation deadline | 120 s |
| Key quota endpoint | HTTP 200: usage `0`, limit `50`, remaining `50`, free tier |

The backend `Settings` loaded from the same file reports the model above, and
the app container was restarted after the change. No older model is referenced
by the resolved configuration.

## Root causes found and fixed

1. **HTTP 400 on the first generation request.** The model mandates reasoning.
   Sending `reasoning: {"enabled": false}` returns
   `400 Reasoning is mandatory for this endpoint and cannot be disabled`.
   Fixed by requesting `reasoning: {"effort": "minimal"}` up front for
   OpenRouter. The old protocol-retry path was removed, so generation never
   spends a second call to discover this.
2. **HTTP 200 but strict validation failed.** The old 24 s validation deadline
   expired while the model was still producing the answer. A one-question
   request took 29.35 s. Fixed by raising the bounded provider timeout to 90 s
   and the generation deadline to 120 s. Practice generation remains
   `max_retries=0`; `generate_entries` still allows at most two attempts.
3. **Live verifier could overrun.** `scripts/verify_live_ai.py` previously set
   `max_retries=1` and a five-call ledger. It now uses `max_retries=0`, a
   hard two-request transport cap, and a 90 s timeout; `test_live_ai_budget.py`
   proves the third request cannot reach the transport.

## Real requests (no mocks)

The key quota endpoint was queried once (HTTP 200, no model tokens). Model
requests are listed below; the exact raw prompts/responses are not stored.

| # | Check | HTTP | Model confirmed | Tokens (prompt/completion/total) | Latency | Result |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 1 | Connectivity, reasoning disabled | 400 | — | — | 0.88 s | expected fix trigger |
| 2 | Connectivity, reasoning minimal | 200 | `baidu/ernie-5.5-flash-preview:free` | 35 / 36 / 71 | 1.67 s | JSON `{"ok":true}` |
| 3 | Direct generation, old 24 s deadline | 200 | confirmed | 318 / 1469 / 1787 | 29.35 s | deadline; 0 generated |
| 4 | Direct generation, new deadline | 200 | confirmed | 318 / 1314 / 1632 | 36.67 s | **1 MCQ, diagnostics empty** |
| 5 | App API, 3 questions, old 120 s deadline | 200 | confirmed | not retained | 127.35 s | deadline; bank fallback |
| 6-9 | App API, rate-limit window | 429 ×4 | — | — | 0.5–2.0 s | stopped after two attempts |
| 10 | Error-body probe | 200 | confirmed | not retained | <2 s | rate limit reset |
| 11 | App API, 1 question, fresh account | 200 | confirmed | not retained at API layer | 31.28 s | **1/1 AI MCQ, no fallback** |
| 12 | App API, 2 questions, fresh account | 200 | confirmed | not retained at API layer | 32.86 s | **1 AI MCQ + bank SQL, exact count** |

Total model HTTP requests: **12** (7 × HTTP 200, 1 × HTTP 400, 4 × HTTP 429).
Successful AI generation: **3 runs** (direct post-fix, app 1-question, app
2-question). No quota was purchased or increased.

## Generation evidence

Session **197**, app API (`POST /api/v1/practice/start`):

```json
{
  "http": 200,
  "question_source": "ai",
  "ai_generated_count": 1,
  "bank_mixed": false,
  "template_fallback": false,
  "generation_fallback": false,
  "generation_diagnostics": [],
  "max_questions": 1,
  "current_question_type": "mcq"
}
```

The question was returned and persisted (`GET /sessions/197` returned the same
`question_id 5532`). Content inspected from the application database:

- Prompt: PostgreSQL default output label for an unlabeled select-list
  expression such as `SELECT 2 + 2;`
- Reference answer: `?column?`
- Options: `NULL`, `?column?`, `expr`, `unnamed`
- Explanation and official PostgreSQL documentation reference present.

Session **198**, count 2: `ai_generated_count=1`, `bank_mixed=true`,
`template_fallback=false`, `generation_diagnostics=[]`. The single AI MCQ plus
the validated bank SQL gives exactly the requested two questions. The existing
`generation_fallback` flag is true for mixed bank SQL by design, not because
AI generation failed.

## Validation and fallback tests

- `backend/tests/dn/test_practice_recovery.py` duplicate/malformed/recovery
  selection: **24/24 passed**.
- AI/LLM/provider targeted suites: **127/127 passed**.
- The provider regression now asserts minimal reasoning is sent on the first
  call, a protocol 400 is never retried at budget zero, and one generation
  invocation maps to one HTTP request.
- Invalid responses still fail closed; duplicates are removed; templates are
  used only when generation/validation genuinely fails.

## Rate limiting and remaining limitation

The free model returned HTTP 429 after the early burst; two app retries were
stopped and no further calls were made until the window reset. The final
1-question and 2-question app runs then succeeded.

Count 3 (two AI questions + bank SQL) exceeded the 120 s deadline in this
environment and correctly fell back to the bank. The UI's HTTP client has a
60 s timeout, so count 3 is not claimed as successful for the real model. This
is a performance limitation of the free model, not a silent fallback: the
response field `generation_fallback=true` and diagnostics `timeout` expose it.

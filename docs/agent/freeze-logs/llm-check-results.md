# `npm run llm:check` results (2026-11-24)

No API key or secret value is printed in this log. `.env` was not modified by
the command; temporary trials below used process-environment overrides only.

## Current `.env` (Mistral base URL)

Verbatim output (base URL and model are not secrets; key is never shown):

```
llm:check (values from .env unless overridden by environment)
provider: openai_compatible (unknown value, warning)
base URL: https://api.mistral.ai/v1
model: deepseek-v4-1-flash-1017
GET /models: HTTP 200 in 666 ms; 63 model(s)
POST /chat/completions: HTTP 200 in 953 ms; JSON hợp lệ: có
result: PASS
```

The configured `LLM_PROVIDER` value is not a known alias, so it was reported as
`openai_compatible (unknown value, warning)` — the configured value itself was
not changed. The minimal chat request returned valid JSON `{"ok":true}`.

## Temporary provider 1 — local fake OpenAI-compatible server

Overrides used (no `.env` write): `LLM_BASE_URL=http://127.0.0.1:8765/v1`,
`LLM_API_KEY=<temporary-fake-key>`, `LLM_MODEL=fake-model-1`,
`LLM_PROVIDER=Mistral`.

```
provider: openai_compatible (unknown value, warning)
base URL: http://127.0.0.1:8765/v1
model: fake-model-1
GET /models: HTTP 200 in 33 ms; 1 model(s)
POST /chat/completions: HTTP 200 in 4 ms; JSON hợp lệ: có
result: PASS
```

Clear recognition of the unknown provider name plus a working generic
chat-completions call. The local fake server was stopped after the trial.

## Temporary provider 2 — wrong base URL

Override: `LLM_BASE_URL=http://127.0.0.1:9/v1` (other values unchanged).

```
base URL: http://127.0.0.1:9/v1
model: fake-model-1
GET /models: ERROR fetch failed
result: FAIL - không gọi được endpoint models; kiểm tra LLM_BASE_URL và mạng.
```

Exit code 1. No key, prompt or credential appears in the message. The
reviewed-bank fallback is a separate application path: it is covered by
`tests/test_ai_adaptive_practice.py::test_ai_adaptive_falls_back_to_bank_without_exposing_the_error`
and by the earlier key-off E2E in `fallback-check.log`; this check itself only
reports provider reachability and never changes a configuration value.

## Admin System status after rebuilding the stack

`GET /api/v1/admin/system` → HTTP 200:

```
{"evaluator_configured":true,"prompt_builder_configured":false,
 "fallback_available":true,"mode":"local","database":"PostgreSQL 17",
 "pipeline":"Prompt Builder → Evaluator → Admin review"}
```

Admin → System page showed: `Prompt builder: Template fallback ready` and
`Evaluator: API configured · falls back on error` — correct with the new
generic provider configuration.

# Mistral API notes (official documentation, read 2026-11-24)

Sources read: https://mistral.ai/ , https://docs.mistral.ai/api/ ,
https://docs.mistral.ai/api/endpoint/models , https://docs.mistral.ai/resources/error-glossary
and the Mistral "Error glossary" search result. Only documented facts are
recorded here; nothing is inferred.

## Mistral AI (homepage)

The site presents Mistral as a sovereign-AI company with open-weight frontier
models, Studio (developer console/API), Vibe, Inference and Compute products.
It offers an OpenAI-compatible chat endpoint.

## Base URL and authentication

- Base URL used in the official curl examples: `https://api.mistral.ai/v1`.
- Authentication header: `Authorization: Bearer $MISTRAL_API_KEY`.
- Content-Type: `application/json`.

## Endpoints

- Chat completions: `POST /v1/chat/completions`. The docs call it "the standard
  OpenAI-compatible chat endpoint"; a basic completion returns `choices[]`
  with a `message` object.
- List models: `GET /v1/models`, authenticated with the same Bearer header.
  Response body contains `data` (array of model cards with `id`) and
  `object: "list"`.
- Retrieve one model: `GET /v1/models/{model_id}`.

## JSON mode

- Request field `response_format` accepts `{"type": "text"}` by default,
  `{"type": "json_object"}` to guarantee JSON output, and `{"type": "json_schema"}`
  to follow a supplied schema.
- The docs state: when using JSON mode you MUST also instruct the model to
  produce JSON in a system or user message.

## Parameters that differ from OpenAI (as documented by Mistral)

- Mistral documents `random_seed` for deterministic sampling; the OpenAI-style
  `seed` parameter is not listed on the Mistral chat page.
- Mistral documents `reasoning_effort` with values
  `none | minimal | low | medium | high | xhigh`, and a separate `prompt_mode`
  value `"reasoning"`.
- Additional Mistral-specific chat fields listed: `safe_prompt` (default false),
  `service_tier` (`auto | standard_only`), `prediction`, `prompt_cache_key`,
  `min_tokens`, `repetition_penalty`, `top_k`, `guardrails`.
- The OpenAI reference implementation in this project currently sends
  `seed` and `reasoning: {"effort": "minimal"}` plus routing fields; these are
  the parameters most likely to need the 400/422 retry-without-optional-fields
  behaviour for a Mistral base URL.

## Error format

- General error body documented as:
  `{"object": "error", "message": "...", "type": "invalid_request_error",
  "param": "model", "code": "unknown_model"}`.
- 400 = malformed request or a value the model/endpoint does not accept
  (the `message` field describes the problem); unknown model returns 400 with
  code `1500`, not 404.
- 422 = well-formed JSON but a field is missing or has an invalid/unsupported
  value; `detail` is a list whose items contain `loc` and `msg`. The glossary
  explicitly mentions an OpenAI client sending an unsupported field such as
  `store` producing `Extra inputs are not permitted`.
- 401 = missing/invalid key; body example `{"detail": "Invalid API Key"}`.
- 429 = rate limit or out of capacity (codes `1300`, `3505`, `3801`).
- The docs state the OpenAI-compatible endpoint wraps errors in an `error`
  object, as OpenAI clients expect.

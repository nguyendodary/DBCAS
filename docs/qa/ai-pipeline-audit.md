# AI pipeline audit — Prompt Builder (AI #1) and Evaluator (AI #2)

Date: 2026-11-10. Branch: `develop2`, worktree
`_worktrees/dbcas-dn-20261101`. Scope: backend AI modules, `ai/`, new
tests, this report. No commit, no network/LLM call, no real key was used.

## What was wrong

1. **Builder fallback was silent.** `build_prompt` caught every model or
   validation error but logged only `status=inference_or_validation_failed`;
   there was no stable reason code, so a fallback could not be diagnosed.
2. **Builder validation proved data/schema integrity, not prompt purity.**
   It rejected changed data/schema, but a model could add an Evaluation-like
   object, copy an answer into an instruction section, prepend prose, or add
   an extra section and still pass. That is the path where AI #1 could grade
   or write feedback instead of only building a prompt.
3. **The exposed `prompt_hash` could differ from the wire prompt.**
   `evaluate()` built the prompt, but `LLMService.generate_structured()`
   sanitized every message again at transport time. If a learner answer
   contained an email/phone/labelled id, the Evaluator received sanitized
   text while `prompt_hash` identified the unsanitized built prompt.
4. **Evaluator fallback logged no reason.** Provider timeout, invalid JSON,
   schema failure and rule fallback all produced one status string.
5. **No test proved the exact prompt/hash contract.** Existing tests proved
   template contents and fallback booleans, but not “Evaluator message hash
   == returned prompt_hash”, nor “a model that outputs a grade is rejected”.

## What changed

| File | Change | Evidence |
| --- | --- | --- |
| `backend/app/services/prompt_builder.py` | Added `OUTPUT_FIELDS`/`_OUTPUT_FIELD_RE` and feedback markers; `_sections` enforces no preamble, fixed order, all five sections; `validate_prompt` now rejects `prompt_output_leak`, `prompt_feedback_leak`, `prompt_answer_leak` and extra instruction headers; `PromptResult.reason_code` and `_failure_reason`; builder log now emits `reason=`. | validation `92-120`; result/reason `123-140`; build/log `154-170` |
| `backend/app/services/evaluation_pipeline.py` | Added `sanitize_data` before build; `evaluate` now hashes exactly the sanitized prompt and calls the provider with `sanitize_messages=False`; added secret-free `failure_reason` and evaluator `reason=` log. | `16-37`, `127-157` |
| `backend/app/services/llm/service.py` | `generate_structured(..., sanitize_messages=True)`; evaluator opts out only after pre-sanitizing, so wire prompt == hash. Default path for essays/admin is unchanged. | `98-122`; cache/validation still `127-148` |
| `backend/tests/test_ai_pipeline_purity.py` | New: builder purity, output/feedback/answer injection rejection, reason codes, timeout, no mutation, model-returns-grade rejection, practice essay cannot reach old grader. | 15 tests |
| `backend/tests/test_ai_prompt_hash.py` | New: exact prompt/hash match, model-builder prompt, builder fallback, real `LLMService` wire + PII redaction, cache, 429/500/503 retry, timeout fallback, invalid output not cached. | 10 tests |

Builder purity boundary in one sentence: AI #1 may format the five fixed
sections and serialize the exact finished-attempt data; data/schema are
compared byte-for-byte, output-only keys and copied answers outside `DỮ LIỆU`
are rejected, and the deterministic template is used on any failure.

No other path lets the local model produce grades/feedback. The old
essay-only grader is still reachable only for formal assessment sessions and
is explicitly blocked for learner-defined practice at
`backend/app/services/assessment_lifecycle.py:112-114`; a new test proves
`grade_essay` is never called for a practice essay.

## Tests (real commands and counts)

Run from the repo root with the repo venv:

```bash
backend/.venv/Scripts/python.exe -m pytest \
  backend/tests/test_ai_pipeline_purity.py \
  backend/tests/test_ai_prompt_hash.py \
  backend/tests/test_two_ai_pipeline.py \
  backend/tests/test_llm.py \
  backend/tests/test_llm_release.py -q
# 141 passed in 18.91s
```

Evaluation-service and grading support suites:

```bash
backend/.venv/Scripts/python.exe -m pytest \
  backend/tests/test_learner_practice.py \
  backend/tests/test_ai_numeric_precision.py \
  backend/tests/test_optional_essay.py -q
# 41 passed in 44.91s
```

`backend/tests/test_essay_grading.py` is **pre-existing red** on this branch:
`4 failed, 21 passed in 12.19s` before and after this change. The four
failures are stale endpoint expectations from the mandatory-review round
(`TestEndpoint.test_complete_answer`, `test_malformed_llm_response`,
`test_invalid_rubric_level`, `test_failed_grade_leaves_attempt_pending`);
they are unrelated to this patch and were not weakened or deleted.

`ruff check` on all changed backend files: **PASS**. `py_compile` on the
changed backend files plus `ai/pipeline.py` and `ai/infer.py`: **PASS**.
`ai/pipeline.py` imports successfully with the backend venv.

## Dead AI code review

| Item | Evidence | Action |
| --- | --- | --- |
| `backend/app/services/essay_grading.py` and `AUTO_GRADE_ESSAYS` worker path | Live for formal assessment: `assessment_lifecycle.py:100,118`; `docker-compose.local.yml:41`; `worker.py:22`; 25 tests. Practice essays are blocked before the grader (`assessment_lifecycle.py:112-114`). | **Keep** — not dead. New test proves practice cannot reach it. |
| `backend/app/services/llm/provider.py` (`LLMProvider`, `ChatCompletionsProvider`) | Used by evaluation, essay, practice generation, admin curation, competency guidance and translation; constructed by `build_llm_service` in `deps.py:104-106` and `worker.py:28,34`. Exactly one provider client exists. | **Keep** — live and only provider. |
| `ai/pipeline.py`, `ai/infer.py`, `ai/Dockerfile`, `scripts/ai.mjs` | Documented and wired: `package.json:8` (`ai:train`), `docs/ai-pipeline.md:28,38,46-47`, `scripts/ai.mjs:21-22`, `prompt_builder.py:143-151` local inference. | **Keep** — optional training is documented and runnable by the documented Docker command. |
| `ai/output/*` | Generated, git-ignored training output; no tracked source imports it; docs only name the path. | **No removal** — not tracked; deleting would destroy local evidence. |
| `_content/expansion-20261024/evidence/existing_prompts.tsv` | Historical content-expansion inventory, not an AI prompt/training artifact and not referenced by the AI pipeline. | **Leave untouched** — out of AI scope. |
| Duplicate/old prompt builders or alternate providers | Search found one builder (`prompt_builder.py`), one provider (`llm/provider.py`) and one evaluator (`evaluation_pipeline.py`). | **None removed** — no unused provider or duplicate builder to delete. |

## Live check (2026-11-10, 1 real call)

One real provider request was made from the rebuilt local app container for
session #6 (`learner_id=2`, 1 submitted attempt): `data_for` → template builder
→ Evaluator. The builder hash and the evaluator log hash are the **same**
(`bcbd4247…c521ee`), so the Evaluator received exactly the built prompt.

The provider rejected the configured key (`reason=llm_auth_failed`); the
Evaluator fell back to the rule evaluation and returned 5 question comments.
No secret, prompt or answer was printed. This proves the live timeout/error
fallback path and the hash contract, but **not** real-model quality. The
remaining reserve was not used (1 of the 2 calls this round consumed).

## Remaining unverified

- Real-model output quality remains unverified because the configured key was
  rejected; the rule fallback is the verified path. All deterministic evaluator
  tests use `httpx.MockTransport`.
- Local LoRA prompt quality was not measured. `npm run ai:train -- --smoke`
  was **not** executed because its Docker build would download dependencies
  (network is forbidden here); only compile/import checks were run.
- The full backend suite and browser suite were not run (targeted tests only,
  as required).
- The four pre-existing `test_essay_grading.py` endpoint failures above still
  need a separate decision by the owning workstream.

# Optional question translation drafts

The manual reviewed-translation workflow remains available. Machine preparation
is a separate **opt-in**, disabled by default (`QUESTION_TRANSLATION_ENABLED=false`).
Existing grading credentials do not enable it. An operator must explicitly opt
in and configure the existing provider's `LLM_BASE_URL`, `LLM_API_KEY` and
`LLM_MODEL`; no new paid SDK or dependency is required. This task enables no live
provider and claims no live translation verification.

## Administrator workflow

1. Enter the original once. Correct its detected language if necessary.
2. Open **Optional reviewed translation**. When the opt-in and provider
   configuration are available, **Prepare translation draft** appears for a
   missing translation. Preparation is an explicit request, not an automatic
   provider call on typing or saving.
3. Inspect/correct the returned prompt, options, explanation and rubric prose.
   The review checkbox remains unchecked. Existing manually entered or reviewed
   translations are not automatically overwritten.
4. Confirm review against the original and grading criteria, then use the normal
   save workflow. Only that authenticated Administrator save persists the
   translation under the existing question-translation contract.

Saving the original is available during preparation and after failures. A draft
is held in the editor only; unchecked text is not saved and is lost when the
editor closes. A response arriving after newer source/manual edits is discarded.
Closing the editor aborts the client request, although an already-running bounded
provider call can still finish server-side. The draft endpoint never saves a
question, translation, score or assessment snapshot. Existing stale-hash and
question-version rules continue to apply after a reviewed save.

## API

Both endpoints require an active Administrator, using current database roles.
Anonymous and Learner requests return 401/403.

- `GET /api/v1/admin/question-translation/capability` returns
  `{"available": false}` unless both the separate opt-in and provider settings
  are present. It exposes no credentials and makes no provider call.
- `POST /api/v1/admin/question-translation/draft` accepts the existing
  `QuestionUpsertRequest`. Its `original_locale` determines the other language.
  Supplied translations, grading keys, score boundaries and dataset values are
  not generation outputs. A successful response has `status: "draft"`, the
  source fingerprint and a `translation` object matching the existing display
  translation fields. It cannot return an approved status.

The service sends only prose fields and opaque markers. SQL definitions are
parsed locally for protected identifiers; no SQL is executed for translation.
Reference SQL/dataset contents and correct-answer associations are not sent to
the provider. Code fences, inline backticks, delimited math, recognized formulas,
numbers, uppercase technical text and known SQL identifiers are masked and
restored verbatim. Missing, changed or reordered markers fail validation.
Technical-only answers remain exact. Option/rubric keys cannot change; duplicate
translated options and incomplete rubric/option coverage are rejected.

This protection is deliberately conservative. Use backticks/code fences for
technical text and `$...$`, `$$...$$`, `\(...\)` or `\[...\]` for math. Unmarked
technical terms and natural-language rubric equivalence cannot be proven by a
generic model. Human review remains mandatory before official use; machine
output is never silently approved or treated as historical evidence.

## Cost, outages and quotas

Each request makes at most one provider attempt, with a 1-30 second configured
timeout and 4096 output-token cap. Prose input is limited to 16 KB; the complete
request is limited to 128 KB. Drafts use no database LLM cache. The per-process
budget allows two requests per administrator per minute and twenty total per
hour, including failed attempts. Quota rejection returns 429 plus `Retry-After`.
Multiple API workers multiply this process budget and restarts reset it:
configure provider-side account quotas before enabling this optional feature.
These bounds are not a global billing guarantee.

Unavailable configuration returns 503 `translation_not_configured`. Provider
outages/quota errors retain the existing normalized LLM error contract. Invalid
structured output or damaged technical markers return a controlled error; the
original and manual translation controls remain usable. There are no automatic
generation retries, live calls in automated tests, or AI-generated fake fallback
translations.

## Traceability addendum to the retained diagrams

The ten reviewed diagrams and their 51-flow context baseline are unchanged.
This optional task was added after that dated review. The following conditional
exchanges document its detail without relabeling or removing existing flows:

| Source | Destination | Exchange | Evidence |
|---|---|---|---|
| Administrator | DBCAS | Explicit draft preparation request | `routers/admin.py:prepare_question_translation` |
| DBCAS | Existing optional LLM provider | Masked EN/VI prose and strict output schema | `services/question_translation.py:prepare`, existing `LLMService` |
| Existing optional LLM provider | DBCAS | Unreviewed structured prose, validated before return | Same service; token and translation-coverage checks |
| DBCAS | Administrator | Draft or actionable error; no question persistence | Draft-only response schema and authoring UI |
| Administrator | DBCAS | Reviewed question save | Existing question update/translation workflow, not implied by generation |

No new actor, database, deployment service or migration is introduced. The
external interaction uses the existing provider adapter and API process; no
translation worker is invented. See the
[blocker-remediation acceptance report](docker-stabilization-acceptance-20261023.md)
for actual mock, database, browser and release-gate results.

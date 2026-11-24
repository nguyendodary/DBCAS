# Prompt contract fix for Mode 2 generation (2026-11-24)

Owner-requested, prompt-only fix after `model-trials-mistral.md` showed 15/15
generations rejected because the model used `question` instead of `prompt` and
string options instead of `{text, correct}` objects. No validator, schema,
grading, UI or `.env` change; no key printed; `.env` unchanged.

## What changed

`app/services/ai_adaptive.py::_prompt` now:

- generates a complete example from `GeneratedQuestion.model_json_schema()`
  (`_example_question`): keys come directly from the schema `properties` and
  nested `$defs`, so the prompt cannot drift from what the validator enforces;
- states the output language explicitly from the learner's `Accept-Language`
  (`vi` → Vietnamese, `en` → English) and asks for all question/answer text in
  that language;
- names the required key `prompt` and forbids `question` and extra keys
  (`additionalProperties=false`);
- gives per-type guidance: MCQ four `{text, correct}` options with exactly one
  correct; SQL `setup_sql`/`edge_setup_sql`/`tables` consistent with a
  deterministic reference; essay null seed fields and four continuous rubrics;
- uses a verified versioned doc URL `https://www.postgresql.org/docs/18/sql-insert.html`
  in the example and requires versioned official URLs in `source_refs`.

A second refinement (same prompt-only scope) fixed the remaining prompt-content
causes: unversioned doc URL, non-null essay `setup_sql`, and seed/reference
mismatch for SQL.

## 1. Direct trials — 5 types x 3 repetitions (before → after)

| Case | Before (validated) | After (validated) | After failure reasons |
|---|---|---|---|
| MCQ vi | 0/3 | 3/3 | — |
| MCQ en | 0/3 | 3/3 | — |
| SQL SELECT | 0/3 | 3/3 | — |
| SQL DML | 0/3 | 1/3 | 2× `generation_sql_syntax` / `reference_answer` |
| Essay | 0/3 | 3/3 | — |
| **Total** | **0/15** | **13/15** | 2 remaining |

First refinement: 14/15 schema-valid but still 0/15 validated (8× `source_refs`
unversioned URL, 3× `generation_sql_execution` empty/nondeterministic,
3× `generation_type_fields` setup_sql on essay, 1× `concept_ids[]` type).
Second refinement removed all of those.

Remaining two failures, with shortened generated content:

| Case | Reason | Evidence |
|---|---|---|
| SQL DML #1 | `generation_sql_syntax` (`reference_answer`) | `UPDATE inventory SET price = price * 1.10 WHERE quantity < 10 AND price < 100 RETURNING product_id, ...` — malformed `RETURNING` list |
| SQL DML #2 | `generation_sql_syntax` (`reference_answer`) | same shape, `WHERE quantity < 20 ... RETURNING product_id, ...` |

The validator correctly rejected these; it was **not** loosened.

After-run latency: min 2.15 s, mean 3.83 s, max 9.01 s (one SQL SELECT call).
After-run tokens (provider `usage`): total **13,859** across 15 calls
(MCQ vi 2,047; MCQ en 1,810; SQL SELECT 2,617; SQL DML 2,917; essay 4,468).
Cost per session: N/A — no reliable published price for this model.

## 2. Mode 2 E2E after the fix

| Run | Session | Served source | Content locale | Transition | Ability path |
|---|---|---|---|---|---|
| Vietnamese | 22 | 8/8 `ai_generated` | 8/8 vi | ~2040 ms | 2→1→1→1→1→1→2→1 |
| English | 23 | 8/8 `ai_generated` | 8/8 en | ~2045 ms | 2→1→1→1→1→1→2→1 |

Difficulty varied between 1 and 2 as ability rose/fell. Note the session field
`ai_generated_count` stayed 0; the authoritative per-question `source` values
are `ai_generated`. No bank fallback occurred in either run.

## 3. Admin candidate queue

Before E2E: empty. After the two AI sessions: **16 candidates**
(10 pending, 6 validated at first read).

| Action | Result |
|---|---|
| Reject candidate 16 | HTTP 200 → `rejected` |
| Approve candidate 11 | 409 `candidate_checks_changed` (stale checks) |
| Revalidate candidate 11 | returned `pending` (duplicate check failed) |
| Approve candidate 6 after revalidation | HTTP 200 → `approved`, `promoted_question_id=4063` |
| Final counts | approved 1, rejected 1, pending 11, validated 4 |

## 4. Tests and gates

- `tests/test_ai_adaptive_practice.py`: 14 passed, including 6 new prompt tests
  (all kinds × vi/en, example parsed from the prompt and checked against the
  strict schema) and a legacy-contract test proving `question`/string options
  are still rejected (`generation_schema`, bank fallback, fallback log).
- Related LLM config tests: 26 passed earlier in this branch.
- Full backend suite: 1935 passed, 7 skipped; ruff and docs:check pass.
- No validator or schema file was touched. .env SHA-256 unchanged
  (`2FC8D20C1C591559DCA07CCA50607C417EC93342F869B507DFB82D338FC91D26`).

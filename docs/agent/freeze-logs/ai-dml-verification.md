# AI-generated DML verification and DML rotation fix (2026-11-25)

Owner-approved change (phương án 4). Scope: `backend/app/services/ai_adaptive.py`
(`_prompt`, `_example_question`, target selection, wrong-kind rejection), directly
related tests, and this report. No validator, schema, grading, UI, migration,
`.env`, dependency or `docs/qa/**` change. No key printed.

## Files changed

- `backend/app/services/ai_adaptive.py`
- `backend/tests/test_ai_adaptive_practice.py`
- this report

## Prompt change

For SQL turns, the prompt now carries a deterministic target from a rotation:
**INSERT → UPDATE → DELETE → INSERT …**, derived from the number of DML
questions already served **in the current session** (only `question_type=sql`
snapshots count — an earlier draft incorrectly counted MCQ reference text such
as "UPDATE" and was corrected). The prompt says a SELECT is still allowed, but
any DML must use the target verb; UPDATE/DELETE additionally require an explicit
WHERE, no RETURNING, and seeds with at least one matching and one non-matching
row. The schema-derived example uses the matching INSERT/UPDATE/DELETE reference.
If the AI returns a DML verb other than the target, `_generate_one` rejects it
with `dml_kind_mismatch`, logs the reason in the fallback log and uses the
existing reviewed-bank fallback. Prefetch keys include the target verb so a
stale item cannot bypass the check. Validator and grading are unchanged.

## Rotation tests

- `test_dml_rotation_is_deterministic` — INSERT → UPDATE → DELETE → INSERT → UPDATE.
- `test_prompt_carries_dml_target_and_matching_example` (3 targets) — prompt names
  the target, forbids RETURNING for UPDATE/DELETE, and the embedded example has
  the matching verb.
- `test_wrong_dml_kind_is_rejected_and_falls_back_to_bank` — an INSERT response
  under an UPDATE target is rejected (`dml_kind_mismatch` in the log), the
  learner receives a bank question, and `is_fallback` is true.
- All 19 tests in `test_ai_adaptive_practice.py` pass; ruff passes.

## E2E evidence

Four mixed Mode 2 sessions (vi → en → vi → en), 8 questions each with mix
MCQ 4 + SQL 2 + essay 2, plus two SQL-only sessions (vi, en) to reach the third
DML slot (mixed mode caps SQL at 2). All SQL questions served in these six
sessions were `ai_generated` and matched the rotation target:

| Session | Language | DML verbs served | Scores (grader `sql_semantic`) |
|---|---|---|---|
| 31 | vi | INSERT, UPDATE | 1.00 correct; 0.00 wrong |
| 32 | en | INSERT, UPDATE | 0.00; 0.00 (wrong seeded answers) |
| 33 | vi | INSERT, UPDATE | 0.00; 0.00 |
| 34 | en | INSERT, UPDATE | 0.00; 0.00 |
| 39 | vi | INSERT, UPDATE, DELETE | 1.00 correct, 0.00 wrong, 1.00 correct |
| 40 | en | INSERT, UPDATE, DELETE | 1.00 correct, 0.00 wrong, 1.00 correct |

Totals: INSERT 6, UPDATE 6, DELETE 2 served; 14/14 were AI-generated with the
correct target verb; no SQL question fell back to bank in these six sessions.

### Validate rate by DML type

Among **served** questions: INSERT 6/6, UPDATE 6/6, DELETE 2/2 (100% of served
items passed generation + validation). The number of rejected generation calls
is not available from this run because the app container log was replaced by
`npm start`; the last measured direct-trial DML rate before the fix was 1/3
(`prompt-contract-fix.md`). No wrong-kind rejection was observed among served
items; the dedicated test proves that path works.

### Correct / wrong answers and grader

For sessions 39/40 (SQL-only), each verb got a correct answer (the AI reference
itself) and an intentionally wrong answer of the same verb with a `WHERE 1=0`
(or DEFAULT VALUES for INSERT) mutation:

| Verb | Correct answer | Wrong answer |
|---|---|---|
| INSERT | score 1.00, status `correct` | score 0.00, status `incorrect` |
| UPDATE | score 1.00, status `correct` | score 0.00, status `error` |
| DELETE | score 1.00, status `correct` | score 0.00, status `incorrect` |

In the earlier mixed run, the intentionally wrong `UPDATE practice_rows ...`
against a different table produced verbatim: score `0.00`, grader `sql_semantic`,
status `error`, `error_type: schema_error`. This is a **database rejection of
the deliberately invalid answer**, not an internal grading fault; the validator
and grader were not changed.

### Rollback

Every DML reference from sessions 39/40 was re-executed in a fresh disposable
writable sandbox with the project's `execute_writable_script`:
`success: true`, `rolled_back: true`, `error_type: null` for all 6 statements.
The same check for the mixed sessions' 8 AI DML items also returned
`rolled_back: true`.

## Remaining limitations

- Only 2 DELETE questions were served (one per locale); the mixed mode's SQL
  cap of 2 prevented a third DML slot, so SQL-only sessions supplied it.
- Per-call token usage for the E2E sessions is not exposed by the application
  API; token/cost totals are recorded as N/A in the packaging log.
- No grading or validator change was made to improve these results.

## Token and cost (packaging step 2)

The application API does not expose provider `usage` per served question, so
per-session token totals for the six E2E sessions are **N/A** (not invented).
The provider did return `usage` in the direct trials: 13,859 total tokens across
15 calls before this rotation change (`prompt-contract-fix.md`); that figure is
not attributable to the E2E sessions above.

Estimated cost per session: **N/A**. The configured Mistral `/models` response
has no reliable `pricing` field for `deepseek-v4-1-flash-1017`. Zero is not
assumed.

# Phase 5 — practice-limit source discrepancy

Observed 2026-11-25 while inspecting the Word sources. This is a documentation
fact-collector issue; no application validator or scoring behavior was changed.

`scripts/doc_facts.py:86` hard-codes `question_count.max` to 20. The current
source of truth is `backend/app/services/practice_config.py`: legacy practice
has `MIN_QUESTIONS = 1`, `DEFAULT_QUESTIONS = 5`, and
`LEGACY_MAX_QUESTIONS = MAX_QUESTIONS = 13`. `public_config()` also reports
typed-practice limits: single-type MCQ 50, SQL 5, essay 10; mixed MCQ 20,
SQL 2, essay 3, total 25. The applicable rules vary by practice style and
source; `backend/app/services/practice_service.py` defines those branches.
The value 20 is therefore not a correct universal question-count maximum.

The collector's other fields must still be checked against current code before
use. The new Word documents must describe the relevant legacy and typed rules
separately and must not copy the hard-coded number as a universal limit.

## Planned narrow correction

1. Change the collector's existing `question_count` values to derive from
   `public_config()` while retaining its existing `min`, `max`, `default`
   output keys; read typed limits from the same configuration when needed.
2. Verify a generated facts file against the current public configuration in
   an isolated path outside `docs/qa/**`, without adding a dependency or
   changing application validation.
3. Record the command, result, and commit before relying on the generated data.

The E2E baseline currently in progress remains pinned to application commit
`253f272`. The proposed collector correction has not yet been made.

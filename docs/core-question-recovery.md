# Core question recovery and legacy Essay retirement

On 2026-10-15, four core records were recovered from the development
database after repository history, refs and fixtures did not contain them.
Eighteen immutable attempt snapshots corroborated their identities. The
recovery commit `6233e7c` contains their original English content, answers,
fixtures, mappings, points and rubrics, with separate Vietnamese translations.

| Existing ID | Source key | Type | Concept | Snapshots |
| --- | --- | --- | --- | --- |
| 2 | legacy-mcq-select-filter | MCQ | SELECT | 7 |
| 3 | legacy-mcq-inner-join | MCQ | JOIN | 5 |
| 4 | legacy-sql-customer-names | SQL | SELECT | 4 |
| 5 | legacy-essay-index-read-write | Essay | IDX | 2 |

## Essay ID 5

The historical rubric is unchanged: Missing 0, Partial 1–3, Complete 4–5.
The proposed four-band repair in pack 1.2 changed scoring semantics and was
never applied to the development database. Pack 1.3 restores the exact
historical source and Vietnamese presentation, and marks it `retired` for
future selection. The current grader still requires four canonical bands;
it does not normalize or regrade the legacy rubric. Saved snapshots and
evidence remain unchanged.

Read-only audit before retirement found published assessment 2
(`PostgreSQL Foundations`) targeting IDX, JOIN and SELECT with two Essay
slots. ID 5 was its only stored IDX Essay. It appeared in two attempts
across six finalized sessions: one scored 2, one unsubmitted. Both attempts
have three-band snapshots. The adaptive engine already excludes ID 5 because
its old rubric fails the current four-band validator. The published
assessment's two-Essay target is already short; that pre-existing
configuration issue is not changed by retiring ID 5.

## Distinct successor

The versioned core pack adds `essay-index-workload-tradeoff`, a new IDX Essay
on selective B-tree lookups versus INSERT/UPDATE index maintenance and when
the index may not be worthwhile. It has its own question ID, naturally
authored English and Vietnamese prompts, and the existing four-band rubric
contract. Provenance is the owner-directed legacy resolution and this
versioned pack; the content is original, not copied from PostgreSQL docs.

The importer creates and validates the successor before retiring an existing
ID 5. It matches canonical content by prompt, preserves the old ID and rubric,
does not rewrite attempts, and does not reactivate a retired record on repeat
imports. New installations create the historical item already retired.

The packs contain 442 stored questions: 441 active and one retired. Core has
27 rows, including both Essay items; PostgreSQL has 415. Each stored item has
an English canonical source and a Vietnamese display translation.

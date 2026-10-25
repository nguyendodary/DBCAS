# pg-m089 reconciliation and assessment 2 coverage audit

Date: 2026-10-15. Starting HEAD: `f6587144da1ce5a1f7ece33e09ede23220941235`.
The initial development audit preceded mutations. Disposable verification preceded
the guarded current-row correction. No historical publication was changed.

## pg-m089: proven stale canonical content (case A)

The source is `db/postgres_knowledge_pack.json`, key `pg-m089`, pack version
1.0; its reviewed correction is commit `988c2b1`. The database has no separate
pack-code column: exact prompt, canonical fields, concept mapping and source
references identify development question **119**. Its entire typed payload
matched the historical Git blob `988c2b1^:db/postgres_knowledge_pack.json`.
There were no owner-only content differences, ID collisions or translations.

- Type: MCQ; concept: `PG-TYPE-JSON`; difficulty: 4; maximum: 1 point.
- Prompt: "Querying jsonb_path_ops vs jsonb_ops GIN indexes differ mainly in:"
- Lifecycle: validated; version **1 → 2**; same question identity.
- Option C remains correct, with option ID **417**. IDs A/B/D remain
  **415/416/418**; all labels and correctness flags are unchanged.
- Only C's prose and the explanation changed. C formerly said only `@>`
  containment queries were indexed. Current prose includes `@>`, `@?`, `@@`
  and excludes key-existence operators.
- Both original PostgreSQL 18 source references (JSON Types and Index Types),
  their section/title/version/retrieval metadata, tags, points and mapping
  remain unchanged. The factual correction agrees with the
  [PostgreSQL 18 JSON indexing documentation](https://www.postgresql.org/docs/18/datatype-json.html#JSON-INDEXING).
- Created: `2026-10-13 14:06:57.565326+00`; old updated timestamp:
  `2026-10-13 14:06:57.600186+00`; correction timestamp:
  `2026-10-15 11:47:44.043841+00`.

Before correction, question 119 had **zero attempts, selection logs,
candidate references and family descendants**. No historical snapshot contains
it. Published assessment 6 targets its concept dynamically (difficulty 1–5);
there is no fixed question roster to rewrite. Neither assessment 6 nor any
session/configuration was updated.

| Fingerprint | SHA-256 |
| --- | --- |
| Historical EN source | `ae2d8ad7034274f898c926762e47a24716bcd89f5e2cad1ff0aa6efae7f76945` |
| Corrected EN source / VI source_hash | `2d57baeb1d6d96e380f686574ce022e3dae97011c2390b4ad36ed37312681f93` |
| Normalized VI display payload | `e9ffa55c3983ccaca17b12a929cc20a7bed5d65d2e240fbfaba59d3b96c736ef` |

The VI prompt is "Chỉ mục GIN dùng jsonb_path_ops khác jsonb_ops chủ yếu ở
điểm nào?" Its options/explanation come from the existing reviewed translation
manifest. No translation was regenerated for this task.

## Guarded import and parity

`db/pg_m089_reconciliation.json` records the exact historical source from Git,
the reviewed correction, and expected version. It is not a database dump.
`python -m app.reconcile_bank` is read-only preflight. It compares every current
canonical question, lifecycle and normalized translation; unknown changes,
duplicates, missing/extra questions or owner translation differences stop an
apply. Three initial translation flags were only trailing whitespace already
stripped by the normal importer; preflight now uses that same normalization.

`python -m app.reconcile_bank --apply --admin-email <existing-admin>` requires
an Administrator. Under the ordinary question lock it rechecks the exact old
unreferenced version, changes only the reviewed prose, increments the version,
and uses the existing validated pack import for translations. Referenced or
modified old rows are refused. The general admin editing/version rules are
unchanged. Import remains additive/per-record, so interrupted imports are
resumable rather than promising a single transaction across the whole bank.

Dry-run showed **one correction, 327 missing translations, 115 matching
translations, no missing/extra questions, and no unresolved conflicts**.
After apply and a second apply:

| Check | Result |
| --- | ---: |
| Stored / active / retired | 442 / 441 / 1 |
| Current canonical matches | 442 |
| Current VI matches | 442 |
| Missing / stale / duplicate translations | 0 / 0 / 0 |
| Extra questions / content conflicts | 0 / 0 |
| Second-import material changes | 0 |

The ordinary translation upsert now skips identical content/fingerprints,
including timestamps. Questions and translations have identical full-row
hashes before/after the second import: respectively
`2e9079bce74d1c7587798f472cc1d15b` and
`a760e101d0ecbc806784db7acf69cecc`.
MCQ ORM loading now orders by stable option ID, matching existing admin DTO
ordering; changing option C's text cannot reorder future displayed options.
Saved snapshot option order is not rewritten.

## Historical and unrelated-data safety

The following before/after ordered full-row MD5 hashes match:

| Records | Count | Hash |
| --- | ---: | --- |
| Attempts, including scores/snapshots/grading detail | 96 | `699bc1e1d2f9f39055f32a7b1de4353a` |
| Sessions, including configuration snapshots | 17 | `8fcadd229696aa5f3281a8603ba8c2d2` |
| Assessments | 5 | `299153ecafa193402f4c29832b665349` |
| Assessment targets | 100 | `c28bfaedd8f7c50adf55f64cce410c5c` |
| Selection logs | 96 | `e67653d71941b5b0afb3299da0f4300d` |
| Questions other than 119 | 441 | `02f88203ef65236484a3278d9d8b114f` |
| Options other than question 119 | 1288 | `2cf97919ca3689b5ddef90f28a6d3f46` |
| Rubrics | 195 | `f7ff7d8e547beeb0ab2a6171801c2cc8` |
| Question/concept mappings | 496 | `6bc2971b3e5e347db34e24f7c1aab330` |

## Assessment 2: exact shortage and classification

`PostgreSQL Foundations` remains **published**, version 1, created
`2026-10-10 06:10:53.249947+00`. Its configuration is 30 minutes, eight questions,
**4 MCQ / 2 SQL / 2 Essay**, targeting SELECT 40%, JOIN 30%, IDX 30%, all at
difficulty 1–3. Its six sessions are finalized. The earliest saved session
configuration is marked `legacy_backfill`; no separate publication-time
candidate-pool snapshot exists, so the complete original pool cannot be
claimed from current rows alone.

Surviving question creation timestamps and actual attempts corroborate
questions 2/3 (MCQ), 4 (SQL), 5 (Essay) around publication. The earliest
selection log explicitly records `opening_fallback_no_mcq`, then
`mcq_unavailable`; this was already an undersupplied historical bank. The
recorded old Essay count was one for a quota of two: **one missing Essay**,
not two missing items. With today's four-band grader and before the successor,
the old three-band item contributed zero compatible Essays (a deficit of two).

Current exact legacy targets yield **2 MCQ / 1 SQL / 1 Essay**. ID 5 is retired
and ineligible; ID 450 is the one valid IDX Essay. Against the old requested
mix, deficits are **2 MCQ / 1 SQL / 1 Essay**, plus only two basic MCQs for the
current three-question opening. This is **B: current coverage shortage for
the exact legacy target pool**. There is also an old/current configuration
mismatch: the supported formal contract is 60 minutes, 10/2/1. Its rejection
of the old mix is intentional, not an incorrect validator to relax.

## Owner-selected forward path

The owner selected the current formal contract. No extra questions are needed:
`db/assessment_templates/postgres_foundations_current.json` expresses the same
SELECT/JOIN/indexing objectives using current bank topic codes
`PG-SELECT-LIST`, `PG-JOIN-TYPES`, and existing `IDX`, preserving target
percentages 40/30/30 and difficulty range 1–3. This is a distinct future
template, not an alias migration or a revision of assessment 2.

Its eligible pool is **14 MCQ / 18 SQL / 2 Essay**, covers all three targets,
and satisfies basic-opening coverage. ID 450 remains validated, confirmed IDX,
five points, difficulty 3, four canonical bands, current EN/VI, and selectable.
ID 5 remains excluded. Simulated all-correct and all-incorrect 13-item adaptive
journeys each select 10/2/1 and include the IDX successor.

The template was created/published only in disposable databases through normal
services and browser/API flows. Temporary assessments were deleted through the
supported service/API. No new assessment or question was added to development;
all five existing assessment rows and all historical snapshots remain intact.

## Verification

Tests run locally on Windows with Python 3.14.5 and disposable PostgreSQL
containers hosted in WSL. No owner environment files were changed, and no
live provider calls were made. Browser verification selected seven relevant
flows per browser: EN/VI PostgreSQL filter and formal publish validation,
EN/VI learner content/history/locale lock, EN/VI legacy/successor review, and
the complete admin curation/assessment-creation workflow. The 19 unrelated
responsive/release cases were not selected in this task.

| Gate | Result |
| --- | --- |
| Backend full suite | 840 passed, 0 failed/skipped; one Starlette warning |
| Assessment/admin/adaptive/lifecycle/bank regression group | 85 tests included in the passing full suite |
| SQL sandbox references | 67 questions / 134 fixtures passed in full suite; mutation guards unchanged |
| Active Essay rubric contracts | 48/48 passed; historical three-band item remains retired |
| Frontend full suite | 178 passed in 24 files |
| Reconciliation and future-coverage focused suite | 11 passed |
| Extended all-correct/all-incorrect future-selection regression | 1 passed, 10 deselected |
| Source localization/integrity validator | 442/442, exit 0, no missing/duplicate keys or English-prose flags |
| Development preflight and source parity | 442 canonical and 442 VI matches; no conflicts, extras, missing or stale rows |
| Development second import | Passed; zero question/translation row changes, including timestamps |
| Chromium | 7/7 targeted flows passed |
| Firefox | 6 initially passed; one synchronization failure corrected; affected case then passed (7 unique flows covered) |
| WebKit | 7/7 targeted flows passed |
| Build | Passed |
| npm audit | Zero vulnerabilities |
| pip check / pip-audit | No broken requirements / no known vulnerabilities |
| Compose configuration / diff check | Passed |
| UI i18n parity | 819 EN / 819 VI, zero differences |

Initial failures are retained here: the first focused backend run had ten
passes and one failure exposing unstable ORM option order after updating C.
Stable option-ID ordering fixed it; all eleven then passed. Browser collection
initially rejected a test import of the application i18n module because Node
requires JSON import attributes; direct catalog reads fixed collection. The
Firefox admin test advanced before its save/tag-confirmation requests had
settled; explicit completion assertions fixed the affected flow. No automatic
retry was used. Existing Starlette deprecation and NO_COLOR/FORCE_COLOR
warnings remain.

No P0/P1 reconciliation or current-template coverage issue remains. Assessment
2 intentionally retains its historical unsupported configuration (P2 review
context); use a distinct future assessment under the approved formal contract.
P3: the existing Starlette test-client deprecation warning remains.

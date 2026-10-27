# DBCAS embedded-figure correction ledger - 27 October 2026

Targeted correction of the diagrams embedded in the four active `*_ver1.2.docx`
deliverables, plus one follow-up prose cell that contradicted a corrected diagram. No
application code, migration, test, database record or diagram source model was changed.

Method: each embedded PNG was compared against the repo `.dot` / JSON diagram models,
`docs/diagrams/schema-catalog.json` and the current backend services. A figure was
changed only when it **asserts something the code contradicts**. Omissions already
bridged by explicit prose were not treated as staleness.

Rendering: the original matplotlib-produced PNGs were edited pixel-in-place
(`_docread/patch_trd_20261027.py`, `patch_comp_20261027.py`, `patch_log_20261027.py`)
and installed by replacing only the matching `word/media/*` member
(`_docread/install_media_20261027.py`). Dimensions are unchanged, so every
`wp:extent` / caption / paragraph / relationship entry stays valid. Re-typesetting was
rejected: the figure font is not DejaVu Sans and no installed family reproduced the
measured glyph metrics, so a redraw would have broken visual continuity.

## Classification of every embedded figure

| Placement | Figure | sha (before) | Class | Action |
|---|---|---|---|---|
| Proposal Fig 1 | Sprint roadmap | `ca2518ad1f51` | UNCHANGED | none |
| Proposal Fig 2 | System Context | `2794fabf0d75` | UNCHANGED | none (protected) |
| Proposal Fig 3 | Logical architecture view | `fa0e6f217935` | MINOR CORRECTION | patched |
| Proposal Fig 4 | Assessment / evaluation pipeline | `ef593781ce8c` | UNCHANGED | none |
| Architecture Fig 1 | Use Case | `081cc67a9e34` | UNCHANGED | none |
| Architecture Fig 2 | System Context | `2794fabf0d75` | UNCHANGED | none (protected) |
| Architecture Fig 3 | Container | `040acf4a4581` | UNCHANGED | none |
| Architecture Fig 4 | Component view | `09b28ece8b06` | MATERIAL UPDATE | patched |
| Architecture Fig 5 | Module / service view | `799e9149e945` | UNCHANGED | none |
| Architecture Fig 6 | Allocation | `1918f7591e4f` | UNCHANGED | none |
| Architecture Fig 7 | Conceptual ERD | `0e35cb0e44ac` | UNCHANGED | none |
| Architecture Fig 8 | Physical database relationship view (TRD) | `618b2479a1d6` | MINOR CORRECTION | patched |
| Database Fig 1 | Conceptual ERD | `0e35cb0e44ac` | UNCHANGED | none |
| Database Fig 2 | Physical database relationship view (TRD) | `618b2479a1d6` | MINOR CORRECTION | patched (identical bytes to Architecture Fig 8) |
| cover pages | institutional logos | `7610f45c2c7c`, `12c89edc68a3` | not diagrams | none |

10 of 10 non-updated diagram placements stayed byte-identical; 4 placements across
3 unique images were corrected; 0 placements were left unmatched.

## Corrections applied

### Component view - `09b28ece8b06` -> `bec2ecc8e6c0` (Architecture Fig 4)

Three false dependency claims removed, no other pixel touched:

| Region | Before | After | Evidence |
|---|---|---|---|
| Curriculum Service | `CLO / concept rules, mapping confirmation` / `uses LLM Gateway` | `CLO / concept rules, mapping confirmation` | `docs/diagrams/components.json` `caption_corrections[2]`: curriculum/question services do not call the LLM directly. `backend/app/services/curriculum_service.py` contains no `llm` / `gateway` / `ai_admin` reference at all |
| Question Bank Service | `Validated bank curation, tag confirmation` / `uses LLM Gateway` | `Validated bank curation, tag confirmation` | same correction; `backend/app/services/question_service.py` contains no LLM or gateway reference |
| Adaptive Engine Service | `Next-question selection, candidate generation and checks` / `uses LLM Gateway, Sandbox Runner` | `Next-question selection` (re-centred) | `caption_corrections[1]` (generation and SQL checks belong to `ai_admin_service`) and `[3]` (no LLM or SandboxRunner dependency); `backend/app/services/adaptive_engine.py` has zero matches for `llm`, `sandbox` or `generat` |

Competency & Gap Service and Grading Service keep their `uses LLM Gateway` text -
both are true (`competency_gap.py`, essay grading). Box borders, connectors, band
grouping, colours and the italic dependency style are unchanged.

### Logical architecture view - `fa0e6f217935` -> `bdb30a4e15d4` (Proposal Fig 3)

Adaptive Engine subtitle `Concept + Difficulty + Type · Gen/Validate (FR-15)` ->
`Concept + Difficulty + Type (FR-15)`, re-centred on the box axis (interior centre
1599.5 px, subtitle centre 1599.5 px).

`docs/diagrams/logical-architecture.json` `caption_corrections[3]`: "Generation belongs
to administrator AI assistance; legacy adaptive engine selects validated bank records."
The retained `Concept + Difficulty + Type` is still accurate - `adaptive_engine._pick`
selects on `concept_id` performance, `min_difficulty`/`max_difficulty` and
`question_type` quotas.

### Physical database relationship view - `618b2479a1d6` -> `c2b308b1e5e0` (Architecture Fig 8, Database Fig 2)

`ConceptCompetency.points_earned` and `ConceptCompetency.points_possible` shown as
`numeric(6,2)`; `schema-catalog.json` declares `numeric(10,2)` for both, which
`db/migrations/008_personalization_and_verified_results.sql:15` applies over the
`NUMERIC(6,2)` baseline at `db/schema.sql:227` (replayed at `db/schema.sql:506`). Both
cells re-typeset by glyph splice from the same PNG (`QuestionCandidate.question_type`
`varchar(10)` digits), right-alignment preserved. The neighbouring
`competency_pct numeric(5,2)` is correct and untouched. The whole figure was otherwise
machine-verified: 21 entities and 137 drawn attribute rows transcribed from 2x tiles
and diffed against the catalog - these two cells were the only discrepancies.

## Reviewed and deliberately left alone

* **System Context** (both documents) - accurate; protected by the task brief.
* **Container, Allocation, Use Case, Module view, Pipeline, Sprint roadmap** - every
  assertion still matches the code; later tables are covered by explicit prose.
* **Conceptual ERD** - depicts the core model only; `Database P70` and
  `Architecture P231` state that later-migration tables are documented in prose.
* **`Controller / Service / Repository [Container: ...]` band labels** in the Component
  view - classified `KEEP ORIGINAL / REPORT LIMITATION`. The word `Container` is a
  notation imprecision, already resolved by the section 4.2 prose ("It follows a
  three-layer architecture of Controller, Service, and Repository layers") and
  `components.json` `caption_corrections[0]`. A clean raster edit is impossible: the
  connector lines pass through the glyphs (`Service` band at x 569..571 inside the "c";
  `Repository` band at x 594..595 inside the "y" of "SQLAlchemy"), so any erase-and-shift
  would either jog a connector or clip a letter. Preserving fidelity wins over the edit.
* **`Stateless JWT (no session store)`** - true; no auth-session table exists in the catalog.
* **`60 minutes / 13 questions`** - true baseline defaults; prose qualifies them.

## Validation

* All four documents reopen in Word with no repair prompt: Proposal 58 pp / 5 shapes,
  Architecture 62 pp / 9, User Stories 24 pp / 1, Database 33 pp / 2; 0 degenerate shapes.
* Page counts and every caption number unchanged; PDF text layer identical page-for-page
  before and after; the only pixel differences in the whole document set are the four
  figure pages (Proposal 47, Architecture 47 and 58, Database 14).
* Non-media zip members are byte-identical, so `document.xml`, relationships,
  `[Content_Types].xml` and all extents are untouched.
* After the follow-up Table 48 cell edit the Architecture document still renders 62
  pages with 9 shapes and 0 degenerate; exactly one zip part moved
  (`word/document.xml`), all 9 media parts stayed byte-identical to the patched figures,
  and the only text or pixel difference across the document is page 49 - the two lines
  of that one bullet. TOF/TOC page references are unchanged.
* `npm run diagrams:check` - PASS (10 models, 34 tables, 49 FKs, 14 migration fingerprints).
* `npm run inventory:check` - PASS.
* The four untouched originals (`ver1.5`, `ver1.3`, `ver1.4`, `ver1.4`) are unchanged.
* `git status` in `DBCAS` was clean before and after: no application, test or migration file moved.

## Reported and then corrected as a follow-up (prose, one table cell)

* Architecture section 4.2, `Table 48. Responsibilities of Component Diagram`, Adaptive
  Engine Service row still read "Drafts and validates AI question candidates ahead of
  time." after the figure pass - it contradicted the corrected Component figure and the
  code (`caption_corrections[1]`). Corrected in the same document on 27 October:

  | | |
  |---|---|
  | Before | `Drafts and validates AI question candidates ahead of time.` |
  | After | `Applies deterministic difficulty, weak-concept and mix-quota rules; logs each decision to SelectionLog.` |

  The first bullet of the same cell ("Serves the next question from the frozen session
  plan, which was assembled from the learner's chosen skills, difficulty band, and the
  validated bank.") was already accurate and is unchanged.

  Evidence for every clause of the replacement:

  | Clause | Source |
  |---|---|
  | deterministic | `adaptive_engine.py` module docstring: "Adaptive policy - fully deterministic, mirroring the documented flow" |
  | difficulty rule | `OPENING_SIZE = 3`; `phase` is `"opening"` below it and `"adaptive"` from question four; `opening_correct >= OPENING_SIZE` raises, `== OPENING_SIZE - 1` holds medium, otherwise basic in weak concepts (`adaptive_engine.py:65,265,271,296-305`) |
  | weak-concept rule | `_weakest_concept` and `_concept_perf` drive misses towards weak or still-uncovered target concepts |
  | mix-quota rule | `QUOTA_PRESSURE_THRESHOLD = Decimal("0.5")` - a sql or essay type is picked once `need_type / slots_left >= 0.5` (`adaptive_engine.py:26,67`) |
  | logs each decision | `_serve` calls `repo.create_selection_log(...)` once per served question with `decision_detail` and `is_fallback` (`adaptive_engine.py:486-492`); docstring: "persists the next Attempt plus one ``selection_log`` audit row" |
  | SelectionLog | `Table 18. Database Design (SelectionLog)` in the Database Design document; FR-15 |
  | not a generator | `_serve` re-checks `question.status != "validated"` and raises `question_bank_changed`; only `status='validated'` confirmed-tag questions enter `_eligible_pool`, so AI drafts can never be served (NFR-09). `backend/tests/test_adaptive_engine.py::test_no_servable_questions_rejected_as_configuration` asserts an unconfirmed AI tag and a `draft` question are both unservable (`assessment_bank_incomplete`, 422) |
  | no LLM/sandbox role | `adaptive_engine.py` has zero matches for `llm`, `sandbox` or `generat`; drafting belongs to `ai_admin_service` / `governed_generation` |

  Tests consulted: `backend/tests/test_adaptive_engine.py` (19 tests, "start/resume,
  sanitized serving, the opening-three-basic-MCQs phase, adaptive difficulty/concept
  selection driven by accumulated evidence, the configured question-mix quota pressure,
  selection_log auditing, max-question and pool-exhaustion termination, finish/timeout
  finalization with deterministic competency recompute, and the per-question evidence
  record") and `backend/tests/test_batch_adaptive.py` (7 tests) for the batch path that
  `serve_next` dispatches to at `adaptive_engine.py:444`. Neither suite was executed -
  this is a documentation change verified by reading the implementation and the tests.

  Layout preservation: the replacement was length-matched to the cell. The
  responsibilities column wraps at ~58 characters, and the original bullet already
  occupied two lines; the 103-character replacement also occupies exactly two lines.
  Word renders 62 pages before and after, every page of the PDF text layer is identical
  except page 49, and the only pixel difference in the whole document is those two
  lines. The longer first draft of this sentence (227 characters, five lines) pushed the
  document to 63 pages and was rejected for that reason.

## Artefacts

Patch and install scripts plus before/after crops live outside the repository in
`_docread/` (`patch_trd_20261027.py`, `patch_comp_20261027.py`, `patch_log_20261027.py`,
`install_media_20261027.py`, `patch_table48_20261027.py`,
`render_20261027/cmp_*.png`, `render_20261027/final_media_verification.txt`).
Pre-edit snapshots of the v1.2 documents are kept in `_docread/pre_media_backup_20261027/`
(before the figure pass) and `_docread/prose_backup_20261027/` (before the Table 48
cell); earlier renders are in `render_20261027/pdf_pre_media/` and
`render_20261027/pdf_pre_prose/`.
`DBCAS/docs/diagrams/originals/` is intentionally left as the untouched extraction of
the pre-correction figures.

# DBCAS embedded-figure correction ledger - 27 October 2026

Targeted correction of the diagrams embedded in the four active `*_ver1.2.docx`
deliverables. Scope is figures only: no prose, no table text, no application code,
no migration, no test, no diagram source model was changed.

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
* `npm run diagrams:check` - PASS (10 models, 34 tables, 49 FKs, 14 migration fingerprints).
* `npm run inventory:check` - PASS.
* The four untouched originals (`ver1.5`, `ver1.3`, `ver1.4`, `ver1.4`) are unchanged.
* `git status` in `DBCAS` was clean before and after: no application, test or migration file moved.

## Reported but deliberately not changed (outside figure scope)

* Architecture section 4.2, `Table 48. Responsibilities of Component Diagram`, Adaptive
  Engine Service row still reads "Drafts and validates AI question candidates ahead of
  time." That sentence contradicts the corrected Component figure and the code
  (`caption_corrections[1]`). It is table prose, not a diagram, so this pass left it
  alone - it needs an owner-visible prose edit in the next documentation pass.
* The Component figure's three `[Container: ...]` band labels (see above).

## Artefacts

Patch and install scripts plus before/after crops live outside the repository in
`_docread/` (`patch_*_20261027.py`, `install_media_20261027.py`,
`render_20261027/cmp_*.png`, `render_20261027/final_media_verification.txt`).
`DBCAS/docs/diagrams/originals/` is intentionally left as the untouched extraction of
the pre-correction figures.

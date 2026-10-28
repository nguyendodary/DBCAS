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
ruled out here on the belief that the figure font was not DejaVu Sans and that no
installed family reproduced the measured glyph metrics. **That belief was wrong** - see
*Two-diagram typography remediation* at the end of this ledger: the figures are DejaVu
Sans at integer pixel sizes (normalised cross-correlation 0.9999-1.0000 on complete
lines), and the two defective diagrams have since been re-typeset in place.

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

The `UNCHANGED` classifications for Architecture Fig 3 and Fig 6 were correct for this
pass and were superseded the next morning; see *Two-diagram typography remediation*.

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

---

# Follow-up pass - 28 October 2026: revision history, pagination and visual QA

Scope was formatting and rendering only. No diagram was regenerated, no application
code, test, migration or database record was touched, and no figure that was already
correct had its image modified.

## Revision history normalisation

Every revision-history row in all four `*_ver1.2.docx` now carries exactly `Update` in
the Comment / Description-of-change column (3 rows per document, versions 1.0 / 1.1 /
1.2). Version numbers, verified dates and author/reviewer fields were preserved; no row
was added or removed. Displayed version and filename tag remain `ver1.2` in all four.
Before the pass the cells read `Init` on every 1.0 row, `Update` on every 1.1 row, and a
long reconciliation paragraph on every 1.2 row; only the 1.0 and 1.2 cells changed.

## Caption fields

Three Architecture captions had the `SEQ Table` field placed *after* the number text
instead of between `Table` and `.`, producing `Table . <title><n>` renderings
(`Table . Operational Use Cases: Roles13`, `…Session21`, `…Feedback24`). The field was
relocated and the italic title run restored in `word/document.xml`; only that one zip
part moved and the other 32 parts stayed byte-identical. Detector:
`_docread/scan_lists_20261028.py`, 3 -> 0 malformed captions, all four documents clean.

## Field refresh

The cached TOC / LOT / LOF page numbers were materially stale - inherited from the
untouched originals, not caused by any edit in this pass. Before the refresh:
Proposal 44 of 57 entries drifted; Architecture 29 drifted and 42 had stale titles;
User Stories 7; Database 47. A controlled copy was refreshed in Word
(`_docread/refresh_controlled_20261028.py` - fields, all TOCs and TOFs, header/footer
fields, `Repaginate()`), which changed no page count (57 / 62 / 23 / 33 before and
after) and no media byte. Only `word/document.xml` and `docProps/app.xml` were spliced
back into the deliverables (`_docread/promote_refresh_20261028.py`), after confirming
rIds, style ids, numbering ids, `sectPr` counts and `pgNumType` were unchanged.

Result: 224 of 224 cached list entries now match the rendered document exactly
(`_docread/cached_vs_actual_20261028.py`: 57 / 76 / 10 / 81, page-drift 0, title-stale 0)
and 224 of 224 entries land on the displayed page their list declares
(`_docread/toc_check_20261028.py`, ok=224 mismatch=0 notfound=0).

## Pagination verification

| Document | Physical | Numbered | Front matter | Sections | Displayed 1..N contiguous | Duplicates | Near-empty pages |
|---|---|---|---|---|---|---|---|
| Proposal | 57 | 49 | p1-8 | 2 | yes | none | none |
| Architecture | 62 | 54 | p1-8 | 10 (3 landscape) | yes | none | none |
| User Stories | 23 | 17 | p1-6 | 2 | yes | none | none |
| Database | 33 | 26 | p1-7 | 7 (1 landscape) | yes | none | none |

Numbering is arabic decimal throughout - no `pgNumType w:fmt` is set to roman anywhere.
Each document restarts at 1 exactly once, in the section where the body begins
(Proposal sect2, Architecture sect4, User Stories sect2, Database sect5). Headers and
footers use only the `PAGE` field; there is no `NUMPAGES` / `SECTIONPAGES` anywhere, so
no "page X of Y" total can go stale. `docProps/app.xml` `<Pages>` matches the physical
count in all four.

## Sprint roadmap header rule - corrected in place

Proposal Figure 1 (`word/media/image2.png`, 4712x3497) had the header row's bottom rule
drawn across the last wrapped subtitle line of four sprint cells, so `Design`, `Engine`,
`Dashboards` and `Remediation & Final Delivery` read as struck through, and the
`MIDTERM REVIEW` gate's date line was likewise crossed.

The rule was a straight 5-row band at y 508-512 with 15 rows of empty whitespace beneath
it, so `_docread/patch_roadmap_20261028.py` applies a pure permutation of three existing
5-row bands - no pixel is invented and no glyph is redrawn:

| Rows | Before | After |
|---|---|---|
| 508-512 | the rule | old 513-517 (surviving glyph bottoms) |
| 513-517 | glyph bottoms | old 518-522 (whitespace) |
| 518-522 | whitespace | old 508-512 (the rule, now clear of every glyph) |

Verified: dimensions unchanged, all changed pixels confined to rows 508-522, the
full-width rule now sits at 518-522 with five whitespace rows above it, one zip part
changed and 33 byte-identical, `ca2518ad1f51` -> `46ed48ce323a`. Re-render confirms the
strike-through is gone and the document is still 57 pages with identical list entries.

## Reviewed and reported rather than forced

* **Container diagram** (Architecture Fig 3, `040acf4a4581`) and **Allocation view**
  (Architecture Fig 6, `1918f7591e4f`) - the label text in several shapes is typeset on
  a line pitch smaller than the glyph height, so adjacent lines shear each other: in
  `Web Application` the first line loses its ascenders and the third loses its lower
  half; in the Allocation `Application Server` and `SQL Sandbox` shapes the third line
  is sheared flat across. In the Container figure `SQL Execution Sandbox`'s second line
  also runs past the cylinder's right edge. Both images were byte-identical to the
  untouched originals, so this was inherited, not introduced here. Reported at the time
  as unfixable because re-typesetting was thought to break visual continuity; that
  conclusion was reversed on 28 October - see *Two-diagram typography remediation*.
* **Milestone hexagons** in the sprint roadmap (`MIDTERM REVIEW`, `FINAL CAPSTONE
  DEFENSE`) are narrower than their four-line labels, so the slanted edges nick the
  first and last characters of the outer lines. All text remains legible; clearing it
  would need the hexagons enlarged into the swimlane rules and the dashed sprint
  separators, so it is reported rather than forced.
* **One text overhang** in the whole document set: Proposal p18, the justified line
  ending `…the SMART (Specific,` - the trailing comma's ink reaches x 541.0 pt against a
  538.3 pt column, a 2.7 pt (0.95 mm) hanging-punctuation overshoot. It is inside the
  printable area (54 pt of margin remain) and is normal justification behaviour, so it
  was left alone. No table or figure crosses a margin in any of the four documents.

## Visual QA coverage

All 14 figure placements were inspected at native resolution against the 17 defect
classes (geometry from `w:pgSz` / `w:pgMar`: 595x842 pt, margins L 99 / R 57 pt;
landscape sections 842x595). `_docread/figure_metrics_20261028.py` reports every
placement inside its column with the native aspect ratio preserved and no Word-side
cropping; `_docread/qa_20261028/` holds the page renders and the native crops. Clean:
Use Case, System Context (both documents), Component, Module view, Conceptual ERD (both
placements), Physical TRD (both placements), logical architecture view, assessment
pipeline. The OAuth identity providers are absent from the System Context figure by
design and both documents say so in prose beside it.

## Artefacts for this pass

`_docread/pre_roadmap_backup_20261028/` holds the pre-correction Proposal plus its
SHA-256; earlier snapshots are in `pre_format_backup_20261028/`,
`pre_caption_backup_20261028/` and `pre_refresh_backup_20261028/`. Final renders are in
`_docread/render_20261028_final/`. The four deliverables live outside this repository,
so only this ledger is committed.

---

## Two-diagram typography remediation - 28 October 2026

Architecture **Figure 3 Container** (`040acf4a4581`) and **Figure 6 Allocation**
(`1918f7591e4f`) were the last two materially defective diagrams. Both are now repaired
in place; every other figure, every word of prose and both documents' structure are
untouched.

### Root cause

Not "tight leading" in the typographic sense. The generator drew **each label line
inside its own opaque rectangle filled with the shape's own colour**, and those
rectangles overlap, so a later line's background deletes whole scan rows of its
neighbours. That is why the damage is one-sided per line - a sheared ascender row on one
line and a sheared descender row on the next - and why no amount of leading adjustment in
the source model would have shown up in the raster.

Three further defects share the same origin:

* each line's font size was auto-fitted independently, so one block mixes 17, 18 and 23 px;
* the `API Application` tag line was drawn twice at two sizes without clearing, leaving
  visible double rendering (`[Cont**Container: FastAPI 0.141, Python 3.13**]`);
* in the Allocation view the tag lines are wider than their shapes, so their background
  rectangles erased the right border stroke and painted shape-grey onto the white page.

### Font identity

The earlier rejection in this ledger rested on a bad measurement. Re-fitted against the
raster with a free x-offset search, **DejaVu Sans / DejaVu Sans-Bold at integer pixel
sizes** reproduce complete, undamaged lines at normalised cross-correlation
0.9999-1.0000. The font was never the problem; the identification search had been
anchored on a left column taken from a differently-thresholded measurement.

### Method

`_docread/typo_repair_20261028.py` re-typesets the seven affected label blocks
(28 lines) into the existing rasters at unchanged dimensions:

1. each line's original size and baseline are recovered by an **erasure test** - a
   placement is feasible only when its rendered ink box *contains* every surviving ink
   row and the missing rows are contiguous at one end. Ink-box containment discriminates
   far better than cosine similarity on partial data.
2. an integer DP over baselines re-spaces the block so no two ink boxes share a row,
   preferring the identified placement and penalising any lost row. Every chosen baseline
   is within 4 px of the identified original.
3. the block is wiped only where the old glyph alpha sits, then repainted anti-aliased in
   the shape's own white and clipped to the shape interior, established geometrically as
   the largest fill component, hole-filled and eroded three pixels.
4. two Allocation tag lines are shifted 8 px and pulled inside their shapes; their border
   strokes are rebuilt by copying clean donor rows (Application Server col 783, 23 rows
   865-887; SQL Sandbox col 809, 24 rows 1103-1126). The donor rule takes the *smallest*
   edge value that recurs, because label bleed can only push an edge outward.

No `.dot` source, diagram model, generator or application file was changed, and no
generic Graphviz rendering was substituted.

### Verification

* `_docread/typo_verify_20261028.py` - every planned box row carries ink, no ink sits
  outside the union of the boxes, each ink row belongs to exactly one line, all ink is
  inside its shape, both restored border strokes are continuous, the page outside them is
  white. **ALL HARD CHECKS PASS**, 0 warnings.
* `_docread/typo_qa_20261028.py` - changed pixels 38,065 / 2,047,592 (1.86 %) for
  `image4` and 16,952 / 1,707,673 (0.99 %) for `image7`, **0 of them outside the seven
  label blocks**. Connectors, arrows, colours and composition are untouched.
* `_docread/typo_install_20261028.py` - 2 of 33 zip parts replaced, part order preserved,
  `word/document.xml` and the other 7 media members byte-identical.
* `_docread/typo_integrity_20261028.py` - XML well-formed, the other three deliverables
  untouched. **INTEGRITY: PASS**.
* `_docread/typo_indoc_diff_20261028.py` - Word-rendered PDFs before and after, all 62
  pages at 150 dpi: **60 pages pixel-identical**; page 44 differs only inside
  x[308,803] y[488,1030] and page 54 only inside x[546,741] y[849,1006], both strictly
  within their figure rectangles. Placements are unchanged (Fig 3 412.5x405.0 pt at
  113,130; Fig 6 330.0x318.0 pt at 154,197) and both documents are 62 pages.
* `_docread/typo_indoc_blocks_20261028.py` writes BEFORE | AFTER crops of each of the
  seven blocks from the in-document render at native and 2x scale
  (`_docread/typo_qa/indoc_*.png`).
* `_docread/toc_check_20261028.py` against the post-repair render: **224 entries ok, 0
  mismatch, 0 notfound**. `_docread/cached_vs_actual_20261028.py`: **224 cached entries
  all same, 0 page drift, 0 stale titles** - the field results cached in the DOCX still
  agree with a fresh Word refresh, so no F9 is required.
* Revision History comments remain exactly `Update` in all four documents and the
  Architecture footer numbering stays contiguous 1..54.

### Limitation

Word's PDF export re-encodes the embedded PNGs and resamples Figure 6 to 916x883
(~200 ppi at the placed size); the DOCX itself keeps the full 1331x1283 raster, so the
downsampling is an artefact of the export, not of the document.

### Artefacts for this pass

`_docread/pre_typography_backup_20261028/` holds the untouched Architecture document and
both original PNGs with their SHA-256; `_docread/new_typo/` the two repaired PNGs
(`1ea5eddafc7411cc`, `03e844fad662ff85`); `_docread/typo_qa/` the crops and side-by-side
comparisons; `_docread/render_typo_20261028/` the before and after Word renders. Nothing
was pushed and no tag was created.

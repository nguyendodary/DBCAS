# Table Relationship Diagram (TRD) — Stage A clone + Stage B content delta

**Workstream:** W3b · **Figure:** Architecture Fig 8 = Database Fig 2
**Original:** `docs/qa/diagram-originals/ArchitectureDesign_ver1.1_image9.png`
(3440 × 2080; identical `DatabaseDesign_ver1.1_image4.png`; caption
“Table Relationship Diagram”).
**Branch/worktree:** `develop2`, `_worktrees/dbcas-dn-20261101`. No commit,
no push, no `.docx` change, no secret in any output.

**Status: Stage A PASS; Stage B PASS on 5 consecutive pages.**
The old single-page 41-card v1.2 claim is **not** repeated: the full
41-table / 293-column schema is split across five legible landscape pages.
Each page is 3440 × 2080, same card grammar as the v1.1 original.

---

## 1. Stage A — measured clone of the original 21-card page

### Method

1. `scripts/trace_trd_w3b.py` measured the original from pixels only:
   21 full card rectangles (white body + `#E8E8E8` header band, border
   found from the closed card outline), 21 header title bands, all body
   text rows, the 2 px light row separators, the rounded legend frame,
   legend text/symbols, and the crow’s-foot network outside cards/legend.
   Outputs: `trace.json`, `trace_markers.png` (every detected element drawn
   over the original; viewed).
2. `scripts/build_trd_stage_a_w3b.py` built the clone with no layout
   engine: measured card boxes, measured row baselines, original anchors
   (name left, `[PK]/[FK]` right, type right), Arial sizes calibrated to
   the original (title 34, name 26, marker 20, type 24, legend 30), and
   the traced orthogonal + diagonal connector pieces.
3. Rule-8 checker (`scripts/check_diagram_geometry.py`) was run on a
   deliberately broken copy first, then on the real clone.

### Stage A evidence

| Item | Result |
| --- | --- |
| Canvas | 3440 × 2080, exactly the original |
| Cards | 21, exactly once; 6 columns (4/4/4/3/3/3) |
| Card grammar | grey header, centered bold title, one row per column, name / `[PK]`/`[FK]`/`[PK, FK]` / type, PK bold + underlined, light row separators |
| Text elements | 345 |
| Connector pieces | 128 (`h` + `v` + short diagonal crow’s-foot prongs) |
| Legend | frame + `name = primary key`, `[FK] = foreign key`, one/many symbols |
| Checker, deliberately broken | **FAIL, exit 1, 896 problems** (`checker-a-broken.txt`) |
| Checker, real clone | **PASS, exit 0** — 345 labels exactly match; 556 line segments / 361 shapes, each exactly once; 0 text/text or text/line intersections (`checker-a-pass.txt`) |
| Deliverables | `trd-original-style.svg/.drawio/.png`, `trd-original-style-broken.svg`, `spec-stage-a.json`, `text-content-stage-a.json`, `trace.json` |

### Region-by-region description (all 12 4×3 tiles + full render viewed)

The region contact sheet is
`docs/qa/rebuild-preview/trd/stage-a/regions-contact-sheet.png`.

- **r11 — top-left (Role, AccountRole top):** Role card at 111,95 with
  `role_id` `[PK]` `int`, `role_name` `varchar(50)`, `description` `text`;
  plain border; one-tick connector leaving `role_id` to the right. Below it
  AccountRole starts with `account_id` and `role_id` both `[PK, FK]`,
  bold/underlined, with the two crow’s feet on the right edge.
- **r12 — top, second column (Account):** Account card at 665,95:
  `account_id [PK] int`, `email varchar(255)`, `password_hash varchar(255)`,
  `status varchar(20)`, `created_at timestamptz`; two connectors enter/leave
  its top-row and left/right edges.
- **r13 — top, third column (Concept/Question top):** Concept card with six
  rows, Question card with eleven rows; the top-row horizontal stub from
  Concept to the right bus, and the `question_id` connector with one tick.
- **r14 — top-right (MCQOption/Attempt top):** MCQOption five rows and
  Attempt eleven rows; crow’s feet on the left edges at the FK rows,
  one-tick marks on the right; the top bus passes above the cards.
- **r21 — middle-left (UserProfile/CLO):** UserProfile six rows, CLO seven
  rows; UserProfile’s `account_id [FK]` crow’s foot and CLO’s `created_by
  [FK]` crow’s foot face the 106 px gap; `clo_id` connector exits right.
- **r22 — middle (QuestionConcept/SelectionLog):** QuestionConcept’s two
  `[PK, FK]` rows (`question_id`, `concept_id`) with crow’s feet on the
  right; SelectionLog with `log_id [PK]`, `session_id [FK]`,
  `question_id [FK]` and its connectors.
- **r23 — middle-right (QuestionCandidate/AssessmentSession):** candidate
  card (`concept_id`, `promoted_question_id` FK rows) and AssessmentSession
  (`assessment_id`, `learner_id` FK rows), both with crow’s feet at the
  card edges and one-tick marks where they are referenced.
- **r24 — right-middle (Rubric/ConceptCompetency):** Rubric six rows and
  ConceptCompetency eight rows; rubric `question_id [FK]` and competency
  `session_id`/`concept_id` crow’s feet, one ticks on the parent side.
- **r31 — bottom-left (LLMCache/Assessment):** LLMCache six rows; Assessment
  eleven rows with `created_by [FK]`; the long left-hand connector down to
  Assessment’s `created_by` row is present, and the Assessment card is
  **solid** in Stage A (legacy styling belongs to Stage B only).
- **r32 — bottom-middle (AssessmentConcept):** five rows, `assessment_id`
  and `concept_id` both `[PK, FK]`, crow’s feet left, crow’s foot/one tick
  right; the surrounding Assessment/Question buses cross the gap.
- **r33 — bottom-right (legend):** rounded frame, `name` bold/underlined,
  `[FK]`, one-tick and crow’s-foot symbols, all four labels; the clone’s
  legend is the original legend, not a new key.
- **r34 — bottom far right (CompetencyGap):** six rows, `session_id` and
  `concept_id` FK rows with crow’s feet; `llm_explanation`/`status`/
  `created_at` intact; bottom border and shadow match the original card.

### Honest Stage A differences (overlay viewed)

- Arial-as-rendered-by-Chrome vs the original font: right edges differ by
  roughly 2–6 px on long labels; baselines are within 0–2 px.
- Card border/shadow: original has a 2 px dark border with a thin grey
  shadow; the clone uses a 2.5 px border and a 3 px grey offset rectangle.
- Row separators: original is a 2 px `#DCDCDC` band; clone draws the same
  2 px colour at the measured row boundary.
- Connectors are emitted as the measured orthogonal/diagonal pieces, so
  the geometry follows the original route; they are not re-routed through a
  layout engine.
- Legend font was calibrated to 30 px (the original’s legend text is larger
  than the card body text); the `many` symbol is drawn as the original’s
  left-to-right crow’s foot.

---

## 2. Stage B — verified content delta on 5 consecutive pages

Source of truth: `docs/qa/schema-introspection.json` and
`db/schema.sql`; content checked against
`docs/qa/content-delta-verified.md` §9. The master task rule overrides the
old “pending panel decision”: split into legible consecutive pages, keep
every column, every FK, legacy marking, and the 41/293/59/19 counts.

### Page grid (deterministic, no auto-layout)

- 5 pages, 3440 × 2080 landscape, white background.
- 4 card columns; card width 810; column gaps 40; row gap 40.
- Top stub band 160 px (first glyph top is 29 px, ≥ 20 px from the canvas
  edge; the first drawn stroke is at y=20, so no text or line touches y=0).
- Page row heights (px per column row) chosen so the last card ends at
  1944 / 1944 / 1998 / 2022 / 2028, not a single tall blank band:
  P1 78, P2 78, P3 66, P4 62, P5 70.
- Card grammar is the original: grey header, bold title, one row per real
  column in real order, name / `[PK]`/`[FK]`/`[PK, FK]` / compact type +
  `NULL`/`NOT NULL`; PK rows bold + underlined.
- Fonts are never smaller than the original: title 38 (orig. 34), name 32
  (orig. 26), type 24 (orig. 24), marker 22 (orig. 20).
- Legacy cards (`assessment`, `assessment_concept`, `assessment_question`,
  `assessment_blueprint`) are dashed and carry a `LEGACY` tag.
- Legend on every page: PK/FK grammar, one/many symbols, legacy rule, and
  `41 tables · 293 columns · 59 FKs · 19 migrations`; page n of 5.

### Captions (proposed; existing caption format per document)

Architecture Design (existing format `Figure 8. …`):

- `Figure 8. Table Relationship Diagram (1/5)`
- `Figure 8. Table Relationship Diagram (2/5)`
- `Figure 8. Table Relationship Diagram (3/5)`
- `Figure 8. Table Relationship Diagram (4/5)`
- `Figure 8. Table Relationship Diagram (5/5)`

Database Design (existing format `Figure 2: …`):

- `Figure 2: Table Relationship Diagram (1/5)`
- `Figure 2: Table Relationship Diagram (2/5)`
- `Figure 2: Table Relationship Diagram (3/5)`
- `Figure 2: Table Relationship Diagram (4/5)`
- `Figure 2: Table Relationship Diagram (5/5)`

### Page contents and counts

| Page | Table range (reading order) | Tables | Columns | Same-page FK connectors | Cross-page stubs out / in | Checker |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | account → assessment_question | 10 | 52 | 8 | 2 / 12 | PASS |
| 2 | password_reset_token → system_setting | 11 | 63 | 7 | 7 / 2 | PASS |
| 3 | question → competency_gap | 7 | 57 | 6 | 4 / 6 | PASS |
| 4 | assessment_session → result_release_event | 7 | 60 | 6 | 8 / 6 | PASS |
| 5 | assessment → concept_competency | 6 | 61 | 2 | 9 / 4 | PASS |
| **Total** |  | **41** | **293** | **29** | **30 / 30** |  |

Exact page order:

1. `account, account_identity, account_role_audit, user_profile,
   refresh_session, oauth_handoff, role, account_role, login_throttle,
   assessment_question`
2. `concept, question_candidate, course_learning_outcome, clo_concept,
   question_concept, password_reset_token, llm_cache, assessment_concept,
   concept_dependency, password_reset_audit, system_setting`
3. `question, question_translation, mcq_option, rubric, selection_log,
   sql_test_dataset, competency_gap`
4. `assessment_session, attempt, session_question_plan,
   session_start_request, adaptive_event, evaluation_record,
   result_release_event`
5. `assessment, assessment_blueprint, grade_review, grading_job,
   grade_edit_audit, concept_competency`

### Every FK is represented

- 59 FKs total = **29 same-page crow’s-foot connectors** + **30 cross-page
  FKs**, each cross-page FK drawn in **both directions** = **60 labelled
  page-edge stubs**.
- Same-page connectors are not text arrows: `scripts/verify_trd_stage_b_w3b.py`
  checks a three-prong crow’s foot touching the source card edge at the FK
  row and a one-tick at the destination row for every same-page FK.
- Cross-page stubs say `→ target(columns) · pN` on the source page and
  `← source(columns) · pN` on the target page; the verifier finds both
  labels for every cross-page FK. No FK is left as an unlabelled arrow.

### Cross-page FK stubs (30 FKs; 60 stubs)

| # | Source page → target page | FK |
| ---: | --- | --- |
| 1 | p5 → p1 | `assessment.created_by` → `account.account_id` |
| 2 | p5 → p1 | `assessment_blueprint.approved_by` → `account.account_id` |
| 3 | p2 → p5 | `assessment_concept.assessment_id` → `assessment.assessment_id` |
| 4 | p1 → p5 | `assessment_question.assessment_id` → `assessment.assessment_id` |
| 5 | p1 → p3 | `assessment_question.question_id` → `question.question_id` |
| 6 | p4 → p5 | `assessment_session.assessment_id` → `assessment.assessment_id` |
| 7 | p4 → p5 | `assessment_session.blueprint_id` → `assessment_blueprint.blueprint_id` |
| 8 | p4 → p1 | `assessment_session.learner_id` → `account.account_id` |
| 9 | p4 → p3 | `attempt.question_id` → `question.question_id` |
| 10 | p4 → p3 | `attempt.selected_option_id` → `mcq_option.option_id` |
| 11 | p3 → p2 | `competency_gap.concept_id` → `concept.concept_id` |
| 12 | p3 → p4 | `competency_gap.session_id` → `assessment_session.session_id` |
| 13 | p5 → p2 | `concept_competency.concept_id` → `concept.concept_id` |
| 14 | p5 → p4 | `concept_competency.session_id` → `assessment_session.session_id` |
| 15 | p2 → p1 | `course_learning_outcome.created_by` → `account.account_id` |
| 16 | p4 → p1 | `evaluation_record.learner_id` → `account.account_id` |
| 17 | p5 → p4 | `grade_edit_audit.attempt_id` → `attempt.attempt_id` |
| 18 | p5 → p1 | `grade_edit_audit.reviewer_id` → `account.account_id` |
| 19 | p5 → p4 | `grade_review.attempt_id` → `attempt.attempt_id` |
| 20 | p5 → p1 | `grade_review.reviewer_id` → `account.account_id` |
| 21 | p5 → p4 | `grading_job.attempt_id` → `attempt.attempt_id` |
| 22 | p2 → p1 | `password_reset_audit.account_id` → `account.account_id` |
| 23 | p2 → p1 | `password_reset_token.account_id` → `account.account_id` |
| 24 | p3 → p1 | `question.created_by` → `account.account_id` |
| 25 | p2 → p3 | `question_candidate.promoted_question_id` → `question.question_id` |
| 26 | p2 → p3 | `question_concept.question_id` → `question.question_id` |
| 27 | p4 → p1 | `result_release_event.reviewer_id` → `account.account_id` |
| 28 | p3 → p4 | `selection_log.session_id` → `assessment_session.session_id` |
| 29 | p4 → p3 | `session_question_plan.question_id` → `question.question_id` |
| 30 | p2 → p1 | `system_setting.updated_by` → `account.account_id` |

The same list is machine-readable in
`docs/diagrams/rebuild/trd/cross-page-fks.json`.

### Checker numbers (rule 8, every final page)

Deliberately broken page: `trd-1-broken.svg` → **FAIL exit 1, 549
problems** (`checker-b-broken.txt`). Final pages:

| Page | Labels expected | SVG text | SVG line segments | SVG shapes | Result |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 157 | 157 | 266 | 170 | PASS |
| 2 | 178 | 178 | 309 | 204 | PASS |
| 3 | 158 | 158 | 237 | 168 | PASS |
| 4 | 174 | 174 | 260 | 191 | PASS |
| 5 | 170 | 170 | 229 | 169 | PASS |

Every page: no text/text intersection, no text/foreign-segment intersection,
no label-set mismatch, no duplicate element. Separate verifier
`scripts/verify_trd_stage_b_w3b.py`: **PASS** — 41 cards exactly once,
293/293 column rows match real order/type/nullability/PK-FK, 29 same-page
crow’s-foot connectors + 30 cross-page FKs with 60 stubs, no segment
midpoint inside a card, no text outside the canvas or overlapping.

### Legibility (honest)

Each page is 3440 × 2080. At the width used in the Word documents
(about 9.5 in for a landscape full-width figure) the 32 px card names
render at about 6.3 pt; on screen at 100% they are comfortably legible,
and on A3/landscape print they are readable but small. The full 293
columns are present; no card says “+N more”. This is why the figure is
five pages rather than one: one 3440 × 2080 page at original density
cannot hold 41 full-column cards legibly, which is also what
`content-delta-verified.md` §9 records. The 5-page split is a proposed
caption change only; no `.docx` was edited and no “full schema on one
page” claim is made.

### Visual review (full pages and thirds)

- **Page 1:** top third is the 160 px stub band (first glyph at y=29, no
  clipping) followed by account / account_identity / account_role_audit /
  user_profile; middle third is refresh_session / oauth_handoff / role /
  account_role; bottom third is login_throttle / assessment_question and
  the legend. Card bottoms reach y=1944; the 40 px row gaps carry the
  crow’s-foot connectors.
- **Page 2:** top third concept / question_candidate /
  course_learning_outcome / clo_concept; middle third question_concept /
  password_reset_token / llm_cache / assessment_concept; bottom third
  concept_dependency / password_reset_audit / system_setting + legend.
  Card bottoms 1944.
- **Page 3:** question fills the top row with question_translation /
  mcq_option / rubric; bottom row selection_log / sql_test_dataset /
  competency_gap + legend; card bottoms 1998.
- **Page 4:** assessment_session / attempt / session_question_plan /
  session_start_request on top, adaptive_event / evaluation_record /
  result_release_event below + legend; 6 same-page crow’s-foot connectors
  are visible between the cards (session/attempt cluster); bottoms 2022.
- **Page 5:** assessment / assessment_blueprint / grade_review /
  grading_job on top, grade_edit_audit / concept_competency below + legend;
  the two legacy assessment cards are dashed and tagged; bottoms 2028.

### Final vs original comparison (layout grammar, not identical canvas)

Kept from the original: the card grid grammar, grey header band, centered
bold table title, one row per column, name / `[PK]`/`[FK]`/`[PK, FK]` /
type anchors, PK underline, light row separators, crow’s-foot / one-tick
notation, rounded legend frame, white background, landscape orientation.
Changed because the content cannot fit one page: 21 cards → 41 cards on
5 pages; 6 original columns → 4 wider columns per page; row heights
62–78 px; fonts enlarged (32/24/22 vs 26/24/20) so the denser cards stay
readable. The original single-page canvas is still exactly reproduced by
Stage A (`trd-original-style.*`).

## 3. Outputs

`docs/diagrams/rebuild/trd/`:

- `trd-original-style.svg/.drawio/.png`, `trd-original-style-broken.svg`
- `trd-1.svg/.drawio/.png` … `trd-5.svg/.drawio/.png`, `trd-1-broken.svg`
- `spec.json` (5-page Stage B), `spec-stage-a.json` (Stage A)
- `text-content.json` (Stage B, per page), `text-content-p1..p5.json`,
  `text-content-stage-a.json`
- `cross-page-fks.json`, `legend.json`, `legend.svg`
- `trace.json`, `trace_markers.png`

`docs/qa/rebuild-preview/trd/`:

- `report.md` (this file), `index.md`
- `stage-a/{original,clone,final,side-by-side,overlay,diff}.png`,
  `stage-a/regions/` + `regions-contact-sheet.png`
- `stage-b/page-1..5/{clone.png,regions/}`, `final-contact-sheet.png`
- `stage-b/original.png`, `side-by-side-original-page1.png`,
  `overlay-original-page1.png`, `diff-original-page1.png`
- `checker-a-pass.txt`, `checker-a-broken.txt`, `checker-b-1..5.txt`,
  `checker-b-broken.txt`

## 4. Blockers / limitations

- draw.io CLI is not available on this machine; `.drawio` files are
  hand-authored mxGraph with explicit geometry/waypoints (stated, not
  hidden).
- Stage A cannot be byte-identical: Arial-vs-original glyph metrics and
  anti-aliasing leave 2–6 px fringes on long labels (overlay viewed).
- Stage B is a layout proposal: captions `(1/5)`…`(5/5)` must be accepted
  by the owner before any `.docx` media replacement. No `.docx` was
  touched.
- The 30 cross-page FKs are intentionally listed in both directions; this
  is 60 stub labels, not 60 distinct FKs.

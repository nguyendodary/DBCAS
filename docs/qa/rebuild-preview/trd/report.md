# Table Relationship Diagram (TRD) — Stage A clone + Stage B F6 redo

**Workstream:** W3b · **Figure:** Architecture Fig 8 = Database Fig 2
**Original:** `docs/qa/diagram-originals/ArchitectureDesign_ver1.1_image9.png`
(3440 × 2080; identical `DatabaseDesign_ver1.1_image4.png`; caption
“Table Relationship Diagram”).
**Branch/worktree:** `develop2`, `_worktrees/dbcas-dn-20261101`. No commit,
no push, no `.docx` change, no secret in any output.

**Status: Stage A PASS; Stage B F6 redo PASS on 5 consecutive pages.**
The owner-rejected top stub bar and page-edge buses are gone. Every
cross-page FK is a labelled stub inside the owning column row (`to <table>
(pN)` on the source row, `from <table> (pM)` on the target row); every
same-page FK is one orthogonal crow's-foot connector routed only in the
free 55 px column gutters / 60 px row gaps. The full 41-table / 293-column
schema is split across five legible landscape pages, all columns present.

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

## 2. Stage B — owner fix round (F6): stubs on the owning column row

Source of truth: `docs/qa/schema-introspection.json` and `db/schema.sql`;
content checked against `docs/qa/content-delta-verified.md` §9. The page
split and reading order are unchanged from the approved five-page proposal.

### 2.1 What changed in this redo

The rejected version drew 60 cross-page stubs in a 160 px band at the top
of every page, with long page-edge buses. The redo removes that band
entirely:

- **No top stub band.** Cards start at y=42. The first text ink is at
  y=65 (page 5: y=57, the LEGACY tag); there is no stub band or extra line
  above the cards (only the card top borders themselves).
- **Stubs are in the owning column's row.** Each cross-page FK contributes
  exactly one source stub `to <table> (p<N>)` and one target stub
  `from <table> (p<M>)`. The text is placed in the same card row as the FK
  column: inline immediately to the right of the column name when it fits,
  otherwise in a block immediately under that column name. It is never a
  detached top block. 30 cross-page FKs → 60 stubs (30 pairs).
- **Real connectors for all 29 same-page FKs.** Source anchor is a
  three-prong crow's foot on the FK column row edge; destination anchor is
  a perpendicular one-bar 10 px outside the referenced column row edge.
  Every route is orthogonal and uses only the 55 px column gutters and the
  60 px row gaps. No connector segment enters any card or any text bbox.
- **Same card grammar and full columns.** Grey header, bold centred table
  name, one row per real column in schema order, name / `[PK]` / `[FK]` /
  `[PK, FK]` / compact type + `NOT NULL`/`NULL`; PK names bold and
  underlined. No card uses “+N more”; no column is dropped.
- **Legacy cards** (`assessment`, `assessment_concept`,
  `assessment_question`, `assessment_blueprint`) keep the dashed border and
  the red `LEGACY` tag.

### 2.2 Page grid (deterministic, no layout engine)

- 5 pages, 3440 × 2080 landscape, white background.
- 4 card columns at x = 40 / 890 / 1740 / 2590; card width 795; column
  gutters 55 px; row gap 60 px; top margin 42 px.
- Base body row heights 72 / 70 / 62 / 58 / 64 px for pages 1–5. Rows that
  carry stubs grow to fit the stub block; cards in the same grid row share
  the row top, not necessarily the row bottom.
- Card grammar: title 38 px bold, column name 32 px, marker 22 px bold,
  compact type 24 px, stub 24 px. All fonts are at least the original card
  fonts (title 34, name 26, marker 20, type 24).
- Legend on every page: PK/FK grammar, one/many symbols, legacy rule, and
  `41 tables · 293 columns · 59 FKs · 19 migrations`, plus page n of 5.

### 2.3 Captions (proposed; existing caption format per document)

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

### 2.4 Page contents and counts

| Page | Table range (reading order) | Tables | Columns | Same-page FK connectors | Cross-page stubs out / in | Checker labels | Segments | Shapes | Result |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | account → assessment_question | 10 | 52 | 8 | 2 / 12 | 157 | 263 | 167 | PASS |
| 2 | password_reset_token → system_setting | 11 | 63 | 7 | 7 / 2 | 178 | 281 | 176 | PASS |
| 3 | question → competency_gap | 7 | 57 | 6 | 4 / 6 | 158 | 212 | 143 | PASS |
| 4 | assessment_session → result_release_event | 7 | 60 | 6 | 8 / 6 | 174 | 218 | 149 | PASS |
| 5 | assessment → concept_competency | 6 | 61 | 2 | 9 / 4 | 170 | 170 | 110 | PASS |
| **Total** |  | **41** | **293** | **29** | **30 / 30** |  |  |  |  |

Exact page order (unchanged from the approved split):

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

### 2.5 The 59/59 proof

`scripts/verify_trd_stage_b_f6.py` reads `spec.json` and
`schema-introspection.json` and checks geometry, not prose. Output saved as
`docs/qa/rebuild-preview/trd/verify-stage-b.txt`:

```
tables 41, columns 293, FKs 59, migrations 19
pages 5, same-page FK connectors 29, cross-page FKs 30, stubs 60
FKs drawn exactly once: 59/59 (29 connectors + 30 stub pairs)
RESULT: PASS
all 41 cards exactly once; 293/293 rows match real order/type/nullability/PK-FK;
every same-page FK has exactly one orthogonal crow-foot connector with a one bar
and no card/text crossing; every cross-page FK has exactly one to/from stub pair on
the correct columns; no dangling connector endpoint.
```

What the verifier proves:

1. 41 cards exactly once, 293/293 rows match the introspection in order,
   type, nullability and PK/FK marker; all four legacy cards are dashed and
   tagged.
2. Every same-page FK has exactly one connector (constraint name matched);
   the source anchor is on the source card boundary inside the FK column's
   row band; the destination anchor is on the destination card boundary
   inside the referenced column's row band.
3. The crow's foot is a real three-prong mark at the source edge (apex
   10–55 px outside, prongs to y−14 / y / y+14); the one side is a vertical
   bar 10 px outside the destination edge, centred on the anchor row.
4. Every connector segment is present in the emitted page; the non-bar
   segments form one connected path from the source edge to the destination
   edge; every non-bar endpoint is shared by another segment or lies on one
   of the two connector cards; no dangling endpoint.
5. No segment midpoint or interior part lies inside **any** card, and no
   segment intersects **any** text bbox (strict, no checker exemption).
6. Every cross-page FK has exactly one `to <table> (p<N>)` stub on the
   source row and exactly one `from <table> (p<M>)` on the target row, with
   the exact text, the correct table/column, and a bbox inside that column
   row band. Inline stubs overlap the name line and sit to its right; block
   stubs start directly below the name.
7. 29 connectors + 30 stub pairs = 59 FKs, each represented exactly once;
   the cross ledger has 30 entries.

Negative test: a deliberately broken spec (one out-stub deleted and a
segment pushed through the account card) makes the verifier **FAIL exit 1,
7 problems, 58/59** — saved as `verify-stage-b-broken.txt`. The broken
spec is a temporary copy under the system temp dir, not part of the repo.

### 2.6 Cross-page FK stubs (30 FKs; 60 stubs)

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

Machine-readable copy: `docs/diagrams/rebuild/trd/cross-page-fks.json`.

### 2.7 Rule-8 checker numbers

Deliberately broken copy of every page (`trd-N-broken.svg`) is run first
and must FAIL; the real page must PASS. All broken copies are the same
text-pile defect used by the established gate (`make_broken_svg_w3b.py`).

| Page | Labels | Segments | Shapes | Real result | Broken result |
| ---: | ---: | ---: | ---: | --- | --- |
| 1 | 157 | 263 | 167 | PASS exit 0 | FAIL exit 1, 525 problems |
| 2 | 178 | 281 | 176 | PASS exit 0 | FAIL exit 1, 625 problems |
| 3 | 158 | 212 | 143 | PASS exit 0 | FAIL exit 1, 490 problems |
| 4 | 174 | 218 | 149 | PASS exit 0 | FAIL exit 1, 562 problems |
| 5 | 170 | 170 | 110 | PASS exit 0 | FAIL exit 1, 559 problems |

Evidence: `checker-b-1.txt`…`checker-b-5.txt` and
`checker-b-1-broken.txt`…`checker-b-5-broken.txt`. Every page has zero
text/text intersections, zero text/foreign-segment intersections, the exact
label multiset, and each element exactly once.

### 2.8 Visual review — full pages and 12 regions per page

All five full pages and every one of the 60 4×3 region tiles were viewed
(`docs/qa/rebuild-preview/trd/stage-b/page-N/clone.png` and `regions/`).
The region contact sheets are `stage-b/page-N/regions-contact-sheet.png`.

**Page 1 (10 cards, 52 columns, 8 connectors, 14 stubs).**
r11 top-left: `account` header and `account_id` at the top of its tall row;
12 green `from …` labels sit directly under `account_id` in two columns,
then `email`, `password_hash`, `password_set`, `password_changed_at`,
`status`, `can_manage_roles`, `created_at`; the right gutter carries the
seven-connector fan with a bar at each destination row. r12:
`account_identity` full card, `account_id [FK]` with the crow's foot at the
left edge and the vertical gutters outside. r13: `account_role_audit`,
`actor_account_id`/`target_account_id` each with a left-edge crow's foot;
`audit_id` PK and the remaining columns intact. r14: `user_profile`,
`account_id [FK]` crow's foot; all six columns. r21: bottom of `account`,
`refresh_session` with `account_id [FK]` crow's foot and the left-margin
self-column run. r22: `oauth_handoff`, its `account_id` crow's foot, and
the horizontal lanes in the row gap above. r23: `role`, `role_id [PK]`;
the `account_role.role_id` connector enters its right edge. r24:
`account_role` with both `[PK, FK]` rows and two left-edge crow's feet.
r31: `login_throttle` full card. r32: dashed `assessment_question` with
`to assessment (p5)` under `assessment_id` and `to question (p3)` inline
next to `question_id`. r33: empty card slot, only the right-hand connector
lane visible. r34: legend, counts line and `Page 1 of 5`.

**Page 2 (11 cards, 63 columns, 7 connectors, 9 stubs).**
r11: `concept` with `from competency_gap (p3)` and
`from concept_competency (p5)` directly under the `concept_id` name; nine
columns through `learning_objectives`. r12: `question_candidate`;
`concept_id [FK]` crow's foot left, `promoted_question_id [FK]` with
`to question (p3)` below. r13: `course_learning_outcome`;
`created_by` with `to account (p1)` inline before `[FK]`. r14:
`clo_concept`, both `[PK, FK]` rows and left-edge crow's feet. r21:
`question_concept`, `question_id` with `to question (p3)` inline and
`concept_id` crow's foot. r22: `password_reset_token`, `account_id` with
`to account (p1)` inline. r23: `llm_cache`, six columns, right-hand lanes.
r24: dashed `assessment_concept`, `assessment_id` with
`to assessment (p5)` below and `concept_id` crow's foot. r31:
`concept_dependency`; the long `prerequisite_concept_id [PK, FK]` row
keeps a clear gap before its marker. r32: `password_reset_audit`,
`account_id` with `to account (p1)` inline. r33: `system_setting`,
`updated_by` with `to account (p1)` inline. r34: legend.

**Page 3 (7 cards, 57 columns, 6 connectors, 10 stubs).**
r11: `question`; `question_id` carries five `from …` labels
(assessment_question p1, attempt p4, question_candidate p2, question_concept
p2, session_question_plan p4) under the name; `question_type`…`status` intact.
r12: `question_translation`; `question_id [PK, FK]` crow's foot left.
r13: `mcq_option`; `from attempt (p4)` inline on the `option_id` line.
r14: `rubric`; `question_id [FK]` crow's foot. r21: lower `question`,
`created_by` with `to account (p1)` inline, `family_id` self-FK crow's
foot at the left edge. r22–r24: blank white area between the tall
`question` card and the second row; only card borders / a connector lane
are visible. r31: `selection_log`, `session_id` with
`to assessment_session (p4)` and `question_id [FK]`. r32:
`sql_test_dataset`, `question_id [FK]`. r33: `competency_gap`,
`session_id` `to assessment_session (p4)` and `concept_id`
`to concept (p2)`. r34: legend.

**Page 4 (7 cards, 60 columns, 6 connectors, 14 stubs).**
r11: `assessment_session`; `session_id` has three `from …` labels,
`assessment_id` `to assessment (p5)`, `learner_id` `to account (p1)`;
`status`…`published_at` intact. r12: `attempt`; `attempt_id` has three
`from …` labels under it, `question_id` `to question (p3)` inline,
`selected_option_id` `to mcq_option (p3)` under it. r13: `session_question_plan`,
`question_id` `to question (p3)`. r14: `session_start_request`; composite
FK anchored at `session_id` (leading column), crow's foot at its left edge.
r21: bottom of `assessment_session` with `blueprint_id`
`to assessment_blueprint (p5)`, then `adaptive_event`. r22: lower
`attempt` rows, `evaluation_record` with `learner_id to account (p1)`.
r23: empty slot / `result_release_event` top. r24: legend. r31:
`adaptive_event` full card. r32: `evaluation_record` full card with
`learner_id to account (p1)`. r33: `result_release_event` with
`reviewer_id to account (p1)`. r34: legend, counts and `Page 4 of 5`.

**Page 5 (6 cards, 61 columns, 2 connectors, 13 stubs).**
r11: dashed `assessment` (`LEGACY`), `assessment_id` with three
`from …` labels (assessment_concept p2, assessment_question p1,
assessment_session p4), `created_by to account (p1)`, `family_id` self-FK
crow's foot, all 14 columns. r12: dashed `assessment_blueprint` (`LEGACY`),
`blueprint_id` with `from assessment_session (p4)`, `assessment_id [FK]`
crow's foot, all 16 columns through `created_at`. r13: `grade_review`,
`attempt_id to attempt (p4)`, `reviewer_id to account (p1)`. r14:
`grading_job`, `attempt_id to attempt (p4)`. r21: lower `assessment`
(`family_id` self-FK and dashed border). r22: lower `assessment_blueprint`
(`approved_by to account (p1)`). r23: empty white area right of the two
bottom cards. r24: legend. r31: `grade_edit_audit`, `attempt_id` and
`reviewer_id` stubs. r32: `concept_competency`, `session_id
to assessment_session (p4)` and `concept_id to concept (p2)`. r33/r34:
empty white / legend.

### 2.9 Page-1 comparison with the original (layout grammar, not identity)

`stage-b/original.png`, `side-by-side-original-page1.png`,
`overlay-original-page1.png` (red = original only, blue = new only),
`diff-original-page1.png`. Measured overlay: 682,333 changed pixels,
394,965 original-only, 287,368 new-only. This is not a clone claim: the
original is 21 cards on one 3440 × 2080 page; page 1 of the redo is 10
cards with the full 52-column content and 14 stubs. The unchanged grammar is
the grey header band, centred bold table name, one row per column with
name / marker / type, PK underline, light row separators, crow's-foot /
one-bar notation and the white landscape canvas. The change is the required
five-page content split, wider cards (795 px), larger fonts (38/32/24/22)
and the new in-row stubs.

### 2.10 Legibility and honest remaining differences

- Each page is 3440 × 2080. At the 9.5 in Word landscape figure width the
  32 px card names render at about 6.3 pt; on screen at 100% they are
  comfortably legible, and A3 landscape print is readable but small.
  The 24 px stub text is about 4.7 pt at 9.5 in — it is intended for the
  full-page/A3 view; it is deliberately smaller than the column text so it
  does not compete with the schema. No text was shrunk below the original
  card fonts.
- The 293 columns are all present, in schema order, with no “+N more”.
- The five-page split and the `(1/5)`…`(5/5)` captions are still a proposal;
  no `.docx` was edited.
- Some connect bundles are dense where many FKs converge on one column:
  `account.account_id` (7 same-page connectors + 12 incoming stubs),
  `question.question_id` (6 connectors + 5 incoming stubs) and
  `assessment_session.session_id` (4 connectors + 3 incoming stubs). The
  bundles are in the gutters, never in a card; the verifier checks every
  segment against every card and every text bbox.
- The composite FK `session_start_request(session_id, learner_id)` is drawn
  once, anchored at its leading column `session_id` on both cards; both
  columns keep their `[PK, FK]` markers.
- `draw.io` CLI is not available on this machine; the `.drawio` files are
  hand-authored mxGraph with explicit card rectangles, row texts, stub
  labels, legend and connector segments.
- There is unavoidable white space on pages 3–5 where a tall card (e.g.
  `question`, `attempt`, `assessment_blueprint`) leaves short cards in the
  other columns; the grid is deterministic and no card was stretched.

## 3. Outputs

`docs/diagrams/rebuild/trd/`:

- `trd-1.svg/.drawio/.png` … `trd-5.svg/.drawio/.png`
- `trd-1-broken.svg` … `trd-5-broken.svg`
- `spec.json` (5-page F6 layout with `connectors` + `stubs`),
  `spec-stage-a.json`
- `text-content.json`, `text-content-p1..p5.json`, `text-content-stage-a.json`
- `cross-page-fks.json`, `legend.json`, `legend.svg`
- `trace.json`, `trace_markers.png`

`docs/qa/rebuild-preview/trd/`:

- `report.md` (this file), `index.md`
- `stage-a/{original,clone,final,side-by-side,overlay,diff}.png`,
  `stage-a/regions/` + `regions-contact-sheet.png`
- `stage-b/page-1..5/{clone.png,regions/,regions-contact-sheet.png}`,
  `final-contact-sheet.png`
- `stage-b/original.png`, `side-by-side-original-page1.png`,
  `overlay-original-page1.png`, `diff-original-page1.png`
- `checker-b-1..5.txt`, `checker-b-1..5-broken.txt`,
  `verify-stage-b.txt`, `verify-stage-b-broken.txt`

## 4. Files changed in this redo

- New: `scripts/trd_common_f6.py`, `scripts/build_trd_stage_b_f6.py`,
  `scripts/verify_trd_stage_b_f6.py`, `scripts/make_trd_previews_f6.py`,
  `scripts/make_trd_final_f6.py`.
- Regenerated: the five `trd-N.svg/.drawio/.png`, five broken SVGs,
  `spec.json`, `text-content*.json`, `cross-page-fks.json`; the whole
  `docs/qa/rebuild-preview/trd/stage-b/` evidence tree; `report.md`,
  `index.md`.
- Untouched: `docs/qa/handover.md`, every `.docx`, application code,
  User Story, other figures’ files.

## 5. Blockers / limitations

- draw.io CLI is not available; `.drawio` files are hand-authored mxGraph.
- The five-page split and the `(1/5)`…`(5/5)` captions must be accepted by
  the owner before any `.docx` media replacement. No `.docx` was touched.
- The 30 cross-page FKs are listed in both directions (60 stub labels);
  that is 30 FKs, not 60 distinct relationships.

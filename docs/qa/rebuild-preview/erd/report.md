# Chen ERD rebuild — W3a (Stage A clone + Stage B content delta)

Figure: `docs/qa/diagram-originals/ArchitectureDesign_ver1.1_image8.png`
(3251 × 1677; identical to `DatabaseDesign_ver1.1_image3.png`).

- **Stage A: COMPLETE** — pixel-traced clone, same canvas, 17 entities /
  24 diamonds / 17 key ellipses, checker PASS, broken checker FAIL.
- **Stage B: COMPLETE** — verified content delta applied
  (`docs/qa/content-delta-verified.md` §8), 16 entities (12 core + 4 legacy),
  16 keys, 20 FK-backed diamonds, checker PASS, broken checker FAIL.

No commit was made (the main agent commits). No shared script was edited;
the tracer/builder copies are `scripts/trace_erd_w3a.py`,
`scripts/build_erd_w3a.py`, `scripts/build_erd_stage_b_w3a.py`.

## Stage A — clone (no content change)

### Method

1. `scripts/trace_erd_w3a.py` detects the **closed white regions** behind
   every white-filled shape (the stock fill tracer finds none on this
   black-and-white line art), classifies them by size/fill ratio into
   entity rectangles (380 × 95 inner), relationship diamonds
   (143 × 70 inner) and key ellipses (201 × 54 inner), reconstructs the
   outer stroke bbox, and reads each label from the ink inside its shape.
   Diamond/ellipse stroke rings are cut before text detection so labels
   that touch their outline (`promoted to`) are not lost.
2. Free cardinality labels (`1`, `N`, `M`) are grouped from glyph
   components outside shapes; legend text is measured separately.
3. The orthogonal connector network is traced from dark horizontal /
   vertical runs after masking every shape and label; anti-aliased double
   rows are merged into one centre-line.
4. `scripts/build_erd_w3a.py` emits SVG / hand-authored mxGraph `.drawio` /
   `spec.json` / `text-content.json`; Arial sizes and per-label
   letter-spacing are calibrated so the checker's ink bboxes equal the
   measured bboxes. Chrome renders the PNG at exactly 3251 × 1677.
5. Outputs were viewed full-size and in 3 × 3 region tiles; the trace
   marker overlay (`stage-a/trace_markers-stage-a.png`) was viewed to
   confirm every shape and label is detected once.

### Counts (Stage A)

| Item | Count |
| --- | --- |
| Entities | 17 |
| Relationship diamonds | 24 |
| Key ellipses | 17 |
| Cardinality labels | 48 |
| Legend text labels | 6 |
| Text labels total | 112 |
| Shapes (incl. legend + 3 legend icons) | 62 |
| Connector centre-line segments | 120 |

### Checker (Stage A)

- PASS: `docs/qa/rebuild-preview/erd/stage-a/checker-pass.txt`
  — 112 text labels, 67 distinct labels exactly match, **312 elements each
  exactly once**, no text/text or text/segment intersection.
- Deliberately broken (`make_broken_svg.py`, all labels piled):
  `stage-a/checker-broken.txt` — **FAIL, 254 problems**.
- Canvas of `erd-stage-a.svg/.png`: **3251 × 1677**.

### Region descriptions (Stage A, all viewed)

- **r11 top-left** — Role box with bold title, `assigned` diamond and `N`
  cardinality to Account; `role id` key ellipse under Role; `defines`
  diamond on the Account→CLO elbow; CLO top and `clo id` at the lower
  edge.
- **r12 top-middle** — `account id` key above Account; Account right half;
  `has` diamond with `1` to UserProfile; UserProfile box and `user id`
  key; `authors` diamond on the long horizontal line; `candidate id` key.
- **r13 top-right** — `rubric id` key, Rubric box, `graded by` diamond with
  `N`/`1`, Question top; `tested by` and SQLTestDataset top-right corner.
- **r21 middle-left** — CLO box and `clo id`; `assessment id` key;
  `maps to` diamond and the `M` run down to Concept; `concept id` key;
  Concept left edge.
- **r22 middle-middle** — Assessment box; `takes`, `seeds` and
  `instantiates` diamonds with their cardinalities; QuestionCandidate box
  and `candidate id`; `tagged with` diamond on the long Concept–Question
  line; `session id` key and AssessmentSession box; `logs` diamond edge.
- **r23 middle-right** — Question box; `tested by`/`chosen in` diamonds;
  SQLTestDataset and `dataset id`; `offers` diamond; SelectionLog with
  `log id`; `option id`; MCQOption; `answered in` diamond.
- **r31 bottom-left** — LLMCache box and `cache id`; legend top-left
  corner and Entity swatch.
- **r32 bottom-middle** — ConceptCompetency with `competency id`;
  `measured by`, `yields`, `diagnosed in` and `flags` diamonds;
  CompetencyGap with `gap id`; legend Relationship/Key attribute swatches.
- **r33 bottom-right** — `records` diamond and `N` into Attempt;
  `selected in` diamond; Attempt with `attempt id`; legend right end and
  the full `1 = one, N / M = many (M : N = many-to-many)` note.

### Honest differences (Stage A, all viewed in `stage-a/overlay.png`)

1. Arial-as-rendered-by-Chrome differs from the original raster: text
   ink widths are matched by per-label spacing, but glyph shapes still
   show 1–4 px red/blue fringes; the legend note is letter-spaced across
   the same 1788–2365 extent, so individual glyph positions differ.
2. Diamond/ellipse strokes are 1 px thinner/thicker than the original in
   places; entity borders reproduce the original 4 px exactly.
3. Connectors are emitted as clean 4 px centre-lines. The original has
   anti-aliased 4–5 px strokes and hand-drawn 1–2 px jogs at some elbows;
   a few junction pixels therefore show red/blue fringes.
4. Key underlines are separate 2 px segments placed 3 px below the
   measured ink bottom; thickness/position match within ~1 px.
5. The legend note was split into a bold `1 = one, N / M = many` and a
   regular `(M : N = many-to-many)` label, exactly as in the original.
6. No element is duplicated; every label is an individual `<text>`.

### Stage A deliverables

`docs/diagrams/rebuild/erd/stage-a/`: `erd-stage-a.svg`,
`erd-stage-a.drawio`, `erd-stage-a.png`, `erd-stage-a-broken.svg`,
`spec-stage-a.json`, `text-content-stage-a.json`, `trace-stage-a.json`,
`trace_markers-stage-a.png`.
Evidence: `docs/qa/rebuild-preview/erd/stage-a/`.

## Stage B — verified content delta

Source of truth: **`docs/qa/content-delta-verified.md` §8** (not the older
`content-delta.md`). 15 FK-backed relations among the 12 core entities are
kept; the five legacy relations are added only where a real FK connects a
legacy entity. `pools` and `versions` are **not** drawn between
AssessmentQuestion and AssessmentBlueprint (no such FK).

### Counts (Stage B)

| Item | Count |
| --- | --- |
| Entities | 16 = 12 core + 4 legacy dashed |
| Key ellipses | 16 |
| Relationship diamonds | 20 = 15 core + 5 legacy |
| Cardinality labels | 40 (2 per diamond) |
| LEGACY tags | 4 |
| Legend text labels | 7 |
| Text labels total | 103 |
| Shapes (incl. legend + 4 legend icons) | 57 |
| Connector polylines | 40 (2 per diamond) |

### Entities

Core: `Role`, `Account`, `UserProfile`, `SystemSetting`,
`CourseLearningOutcome`, `Concept`, `Question`, `MCQOption`,
`AssessmentSession`, `Attempt`, `ConceptCompetency`, `CompetencyGap`.

Legacy (dashed, `LEGACY` tag): `Assessment`, `AssessmentConcept`,
`AssessmentQuestion`, `AssessmentBlueprint`.

Removed from the ERD (remain in TRD): `Rubric`, `QuestionCandidate`,
`SQLTestDataset`, `SelectionLog`, `LLMCache`.

### Core diamonds (15, exact labels from §8)

1. `assigned` — Account M:N Role (`account_role`)
2. `has` — Account 1:1 UserProfile (`user_profile.account_id`)
3. `defines` — Account 1:N CourseLearningOutcome (`created_by`)
4. `takes` — Account 1:N AssessmentSession (`learner_id`)
5. `tagged with` — Question M:N Concept (`question_concept`)
6. `offers` — Question 1:N MCQOption (`mcq_option.question_id`)
7. `selected in` — Attempt N:1 MCQOption (`selected_option_id`)
8. `records` — AssessmentSession 1:N Attempt (`attempt.session_id`)
9. `yields` — AssessmentSession 1:N ConceptCompetency (`session_id`)
10. `measured by` — Concept 1:N ConceptCompetency (`concept_id`)
11. `diagnosed` — AssessmentSession 1:N CompetencyGap (`session_id`)
12. `targets` — Concept 1:N CompetencyGap (`concept_id`)
13. `versions` — Question 1:N Question (`question.family_id` self-FK)
14. `updates` — Account 1:N SystemSetting (`updated_by`, nullable)
15. `requires` — Concept M:N Concept (`concept_dependency`)

### Legacy diamonds (5)

- `targets` — Assessment 1:N AssessmentConcept (`assessment_concept.assessment_id`)
- `pools` — Assessment 1:N AssessmentQuestion (`assessment_question.assessment_id`)
- `versions` — Assessment 1:N AssessmentBlueprint (`assessment_blueprint.assessment_id`)
- `instantiates` — AssessmentSession N:1 Assessment (`assessment_session.assessment_id`, nullable)
- `uses` — AssessmentSession N:1 AssessmentBlueprint (`assessment_session.blueprint_id`, nullable)

### Key ellipses (16)

`role_id`, `account_id`, `user_id`, `setting_key`, `clo_id`,
`assessment_id`, `assessment_id, concept_id`, `question_id`,
`assessment_id, question_id`, `concept_id`, `session_id`, `option_id`,
`blueprint_id`, `attempt_id`, `competency_id`, `gap_id`.

### Checker (Stage B)

- PASS: `docs/qa/rebuild-preview/erd/checker-final.txt`
  — 103 text labels, **61 distinct labels exactly match**, **262 elements
  each exactly once**, no text/text or text/segment intersection.
- Deliberately broken: `checker-stage-b-broken.txt` — **FAIL, 302 problems**.
- Final canvas **3251 × 1677** (`final.png`), same as the original.

### Region descriptions (Stage B, all viewed in `regions-final/`)

- **r11 top-left** — Role and Account with `assigned` M:N; `defines`
  elbow down to CourseLearningOutcome; `role_id` key; `clo_id` at the
  lower edge.
- **r12 top-middle** — `account_id`; Account–`has`–UserProfile 1:1;
  `user_id`; the `updates` diamond and its line routed below the key
  ellipse into SystemSetting; composite `assessment_id, concept_id` key
  above AssessmentConcept.
- **r13 top-right** — SystemSetting and `setting_key`; the core `versions`
  self-FK is a true self-loop on **Question's right side** (diamond at
  x≈2680, y≈560): one branch leaves Question at y=535, the other leaves
  Question's bottom-right at y=613 and loops below the diamond at y=630;
  `1`/`N` sit on the two branches. No connector runs from SystemSetting
  to the `versions` diamond.
- **r21 middle-left** — CourseLearningOutcome; `concept_id`; the stacked
  `uses` (Session→Blueprint) and `versions` (Assessment→Blueprint)
  diamonds; the `versions` line is routed at x=620 so it does not cross
  the `concept_id` ellipse; `1`/`N` labels at Blueprint.
- **r22 middle-middle** — Assessment (dashed, LEGACY); `takes` and
  `instantiates`; AssessmentSession and `session_id`; `tagged with`;
  `pools`; the legacy `targets` diamond at far right of AssessmentConcept;
  `assessment_id, concept_id` key. Every cardinality is individually
  visible.
- **r23 middle-right** — Question; `offers`; AssessmentQuestion (dashed,
  LEGACY) and its composite `assessment_id, question_id` key; `option_id`;
  MCQOption; `selected in`; the empty original SQLTestDataset slot is
  unused (white space).
- **r31 bottom-left** — AssessmentBlueprint (dashed, LEGACY);
  `blueprint_id`; its two incoming lines labelled `1` and `N`; legend
  left end with Entity swatch.
- **r32 bottom-middle** — ConceptCompetency and `competency_id`;
  `measured by`, `yields`, core `targets`; CompetencyGap and `gap_id`;
  `diagnosed`; legend Relationship/Key attribute swatches.
- **r33 bottom-right** — `records` into Attempt; `selected in`;
  Attempt and `attempt_id`; legend right end with the new dashed
  **“Legacy table (historical rows only)”** entry.

### Added / removed elements vs the original

Added entities: `SystemSetting` (core), `AssessmentConcept`,
`AssessmentQuestion`, `AssessmentBlueprint` (legacy, dashed + LEGACY tag).

Removed entities: `Rubric`, `QuestionCandidate`, `SQLTestDataset`,
`SelectionLog`, `LLMCache` (TRD-only; not core).

Added diamonds: `updates`, `requires`, core `versions` self-FK,
legacy `targets`, `pools`, legacy `versions`, `uses`.

Removed/renamed diamonds: `graded by`, `authors`, `configures`,
`promoted to`, `seeds`, `maps to`, `chosen in`, `logs`, `answered in`,
`tested by` are gone (5 dropped entities / not in §8). `flags` became
`diagnosed`; `diagnosed in` became core `targets`; `instantiates` now
connects AssessmentSession–Assessment; legacy `targets` was moved to the
right of AssessmentConcept so it no longer collides with `takes`.

The excluded verbs are still real schema facts in some cases (e.g.
`question.created_by` supports the old `authors` idea, `clo_concept`
supports `maps to`, `assessment.created_by` supports `configures`), but
W4's verified §8 fixes the Stage B core set at the 15 relations listed
above; they remain TRD/data-dictionary relationships and are deliberately
not drawn here to keep the Chen subset at the verified scope.

Added keys: `setting_key`, `assessment_id, concept_id`,
`assessment_id, question_id`, `blueprint_id`.
Removed keys: `rubric id`, `candidate id`, `dataset id`, `log id`,
`cache id` (their entities left the ERD).

Legend: original four entries kept; new dashed swatch + “Legacy table
(historical rows only)” added; box widened from x760–2490 to x560–3000
(still inside the same canvas).

### Honest differences (Stage B)

1. **Not a clone**: this stage intentionally changes content; entity /
   diamond / key positions were chosen to keep the original slots and
   canvas, not to be pixel-identical.
2. **Composite keys** `assessment_id, concept_id` and
   `assessment_id, question_id` do not fit the original 201 × 54 ellipse
   at a legible size, so they use 320 × 64 ellipses. This is the only
   shape-size change; documented here rather than shrinking the text.
3. **Legend is wider** (560–3000) to fit the legacy entry without
   shrinking any original label.
4. **20 diamonds, not 12**: the verified delta itself lists 15 core
   relations; adding the five connected legacy relations gives 20. The
   task allowed an honest adjustment; the exact set and FK evidence are
   listed above. No `pools`/`versions` edge exists between
   AssessmentQuestion and AssessmentBlueprint.
5. **Duplicate labels are intentional**: `targets` (core + legacy) and
   `versions` (core self-FK + legacy) appear twice on different diamonds,
   each with its own cardinalities. The checker treats them as a multiset;
   no geometry is duplicated.
6. Connectors were re-routed around key ellipses and boxes (e.g.
   `updates` leaves Account's right border, runs below `UserProfile` and
   `user_id`, then enters the diamond from the left so it cannot read as
   UserProfile→SystemSetting; legacy `versions` at x=620; `targets` to the
   right of AssessmentConcept); their lengths differ from the original
   corresponding lines because the content changed.
7. The core `versions` self-FK is a real two-branch loop attached twice to
   Question's right side, not a diamond on the SystemSetting–Question
   vertical. The `updates` diamond is fed from Account only; its `1` is at
   the Account branch and its `N` at SystemSetting.
8. Nullable legacy FKs (`instantiates`, `uses`) and `updates` are shown
   with `1`/`N` as the verified delta specifies; the underlying columns
   are nullable, which is a TRD-level fact, not a different cardinality.
9. Same Arial family/sizes as Stage A; no auto-layout; every label is an
   individual `<text>`; no duplicate element.

### Blockers

None. `draw.io` CLI is unavailable on this machine, so `erd.drawio` is
hand-authored mxGraph (as in the other rebuilt figures). The Stage A
clone and Stage B final both pass the shared rule-8 checker; the broken
copies fail it as required.

## Final deliverables

- `docs/diagrams/rebuild/erd/erd.svg`, `erd.drawio`, `erd.png`
  (3251 × 1677), `erd-broken.svg`, `spec.json`, `text-content.json`,
  `trace-stage-b.json`.
- Stage A preserved in `docs/diagrams/rebuild/erd/stage-a/`.
- Evidence: `docs/qa/rebuild-preview/erd/final.png`,
  `side-by-side-final.png`, `overlay-final.png`, `diff-final.png`,
  `regions-final/r11..r33.png`, `checker-final.txt`,
  `checker-stage-b-broken.txt`, `inventory-stage-b.md`.
- Stage A evidence: `docs/qa/rebuild-preview/erd/stage-a/` (clone,
  side-by-side, overlay, 9 regions, checker PASS, broken FAIL, inventory).

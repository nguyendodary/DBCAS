# Chen ERD rebuild — figure 09 (owner fix round F5)

Figure: `docs/qa/diagram-originals/ArchitectureDesign_ver1.1_image8.png`
(3251 × 1677; identical to `DatabaseDesign_ver1.1_image3.png`).

**Status: Stage B REDONE in the owner fix round (F5) — COMPLETE.**
The previous Stage B was rejected: it dropped five original entities and
nine original relationships, and the owner requires the complete Stage A
layout restored. This round keeps the **complete Stage A clone verbatim**
and adds only free-space content. No commit was made (the main agent
commits). No shared script was edited; the F5 copies are
`scripts/build_erd_f5.py`, `scripts/check_erd_delta_f5.py`,
`scripts/make_erd_previews_f5.py`.

- Stage A clone preserved: **17/17 entities, 17/17 key ellipses, 24/24
  diamonds, 120/120 connector segments, 112/112 labels** with identical
  name and exact bbox — proved in
  `docs/qa/rebuild-preview/erd/delta-f5.txt`.
- Final: **21 entities, 21 keys, 28 diamonds, 56 cardinalities, 4 LEGACY
  tags**, canvas **4300 × 1677** (original 3251 × 1677 + 1049 px of free
  right column).
- Rule-8 checker: **PASS** (139 labels, 83 distinct, 388 elements each
  exactly once, 3208 line segments, 249 shape elements). Broken copy:
  **FAIL 295 problems**.
- Relationship evidence table: **`docs/qa/erd-evidence.md`** (24 kept,
  0 removed, 4 added; every kept/added row has an exact FK).

## Stage A — clone (unchanged base)

All Stage A geometry is reused byte-for-byte from
`docs/diagrams/rebuild/erd/stage-a/spec-stage-a.json`. The tracer measured
the original black-and-white line art (closed white regions → entity
380 × 95 inner, diamond 143 × 70, key 201 × 54) and the orthogonal
connector network. Arial sizes/letter-spacing were calibrated so the
checker's ink bboxes equal the measured bboxes. Counts and method details
are unchanged from the Stage A report: 17 entities, 24 diamonds, 17 keys,
48 cardinalities, 6 legend labels, 112 texts, 62 shapes, 120 connector
segments, canvas 3251 × 1677.

Stage A region descriptions and honest differences remain valid; they are
not repeated here. Stage A files are untouched in
`docs/diagrams/rebuild/erd/stage-a/`.

## Final — owner fix round F5

### Method

1. Load `stage-a/spec-stage-a.json` and copy all shapes, lines and texts
   without modification (except the legend frame, which is extended to the
   right, and the Assessment entity, whose stroke becomes dashed).
2. Append three new entity boxes in a new free right column (x = 3600…3988):
   `SystemSetting`, `AssessmentQuestion`, `AssessmentBlueprint`.
   `AssessmentConcept` is placed in the free space below `Concept`
   (x = 700…1000, y = 1000…1103), immediately below-left of the retained
   `targets` diamond, and is joined to that diamond by a short labelled
   junction association (no second diamond). Append the four key ellipses
   and four `LEGACY` tags (Assessment is the fourth legacy tag).
3. Append four FK-backed diamonds: `updates` (Account–SystemSetting),
   `pools` (Assessment–AssessmentQuestion), `versions`
   (Assessment–AssessmentBlueprint), `uses` (AssessmentSession–
   AssessmentBlueprint). No `requires`, no core `versions` self-FK, no
   duplicate `targets`, no `holds`.
4. Route each new diamond with orthogonal polyline branches; route the
   `targets`↔AssessmentConcept junction association in free space; new
   labels are planned with the same Arial calibration as Stage A. Render
   with headless Chrome at exactly 4300 × 1677.
5. Check with the shared rule-8 checker and the F5 delta/layout checker;
   view the full image and all 15 region crops.

### Counts (final)

| Item | Count |
| --- | --- |
| Entities | 21 = 17 original + 4 (SystemSetting + 3 legacy) |
| Key ellipses | 21 = 17 original + 4 |
| Relationship diamonds | 28 = 24 original + 4 added |
| Cardinality labels | 56 (2 per diamond; 48 original + 8 new) |
| LEGACY tags | 4 (Assessment, AssessmentConcept, AssessmentQuestion, AssessmentBlueprint) |
| Dashed entities | 4 |
| Legend entries | 5 (4 original + “Legacy table (historical rows only)”) |
| Text labels | 139 = 112 original + 27 new |
| Shapes | 75 = 62 original + 13 new (4 entities, 4 ellipses, 4 diamonds, 1 legend swatch) |
| Connector polylines | 133 = 120 original + 13 new (2 branches × 4 diamonds + 4 key leaders + 1 junction association) |
| Connector segments | 152 = 120 original + 32 new |
| Canvas | **4300 × 1677** (grow right only) |

### Additions (exact)

Entities: `SystemSetting`, `AssessmentQuestion`, `AssessmentBlueprint` in
the free right column; `AssessmentConcept` below `Concept`, beside the
retained `targets` diamond.

Keys: `setting_key`, `assessment_id, concept_id`,
`assessment_id, question_id`, `blueprint_id`.

Diamonds, with FK evidence (full derivation in `docs/qa/erd-evidence.md`):

| Diamond | Relationship | FK |
| --- | --- | --- |
| `updates` | Account 1:N SystemSetting | `system_setting.updated_by → account.account_id` (nullable) |
| `pools` | Assessment 1:N AssessmentQuestion | `assessment_question.assessment_id → assessment.assessment_id` |
| `versions` | Assessment 1:N AssessmentBlueprint | `assessment_blueprint.assessment_id → assessment.assessment_id` |
| `uses` | AssessmentSession N:1 AssessmentBlueprint | `assessment_session.blueprint_id → assessment_blueprint.blueprint_id` (nullable) |

`AssessmentConcept` is the legacy junction table behind the **retained
original `targets` diamond** (`assessment_concept.assessment_id` +
`concept_id`). It is drawn as a dashed table with its composite key and
`LEGACY` tag below `Concept`, and a short orthogonal association joins its
top border to the left vertex of the existing `targets` diamond. The
association is annotated `assessment_concept` / `junction`; this is a table
annotation, not a new relationship verb, and no duplicate `targets` (or
invented `holds`) diamond was added. `LLMCache` remains the one table in
the original that has no relationship.

### Removals (0)

**No original entity, key, diamond, label or connector was removed or
moved.** The five entities and nine relationships removed in the rejected
Stage B are restored in their Stage A slots:

- Entities: `Rubric`, `QuestionCandidate`, `SQLTestDataset`,
  `SelectionLog`, `LLMCache`.
- Relationships: `graded by`, `tested by`, `authors`, `promoted to`,
  `seeds`, `maps to`, `chosen in`, `logs`, `answered in`.

Proof for every one: exact FK in `docs/qa/erd-evidence.md`, plus the
120/120 segment and 17/17 bbox proof in `delta-f5.txt`.

### Checker numbers

- Rule-8 PASS (`checker-final.txt`, identical to `checker-f5.txt`): 139
  text labels, 83 distinct labels exactly match, 388 elements each exactly
  once, no text/text or text/segment intersection. SVG: 139 text elements,
  3208 line segments, 249 shape elements.
- Deliberately broken (`checker-final-broken.txt`, identical to
  `checker-f5-broken.txt`): 139 labels piled — **FAIL 295 problems**.
- F5 delta/layout checker (`delta-final.txt`, identical to `delta-f5.txt`):
  PASS — 17/17 entities exact, 17/17 keys exact, 24/24 diamonds exact,
  112/112 labels byte-identical, 120/120 connector segments present,
  0 duplicates, 0 moved/removed, every segment orthogonal, no segment
  through an entity box, no dangling endpoints, 21/21 entities have their
  key ellipse and key label.

### Stage A → final bbox proof (all 17 exact)

The full list is printed in `delta-f5.txt`; the exact slots are:

`Role 267,126,655,229`; `Account 907,126,1295,229`;
`UserProfile 1547,126,1934,229`; `Rubric 2187,126,2574,229`;
`CourseLearningOutcome 267,510,655,613`;
`Assessment 907,510,1295,613`; `QuestionCandidate 1547,510,1934,613`;
`Question 2187,510,2574,613`; `Concept 907,894,1295,997`;
`AssessmentSession 1547,894,1934,997`;
`SelectionLog 2187,894,2574,997`; `MCQOption 2827,894,3214,997`;
`LLMCache 267,1278,655,1381`;
`ConceptCompetency 907,1278,1295,1381`;
`CompetencyGap 1547,1278,1934,1381`; `Attempt 2827,1278,3214,1381`;
`SQLTestDataset 2827,510,3214,613`.

The final is a wider canvas (4300 px), so a fit-to-window view shrinks all
elements uniformly; that is not a layout change. `side-by-side-left-final.png`
shows the Stage A clone and the final left 3251 px side by side at 1:1, and
`overlay-stage-a-final.png` is black wherever they match (red is only the
new dashed Assessment border/tag and a few anti-aliasing fringes).

### Region descriptions (all viewed in `regions-final/`)

- **r11 top-left** — Role, `assigned` M:N to Account, `role id`; `defines`
  on the Account→CLO elbow; CLO top edge and `clo id`; Account's left half.
- **r12 top-midleft** — `account id`, Account, `has` 1:1 UserProfile,
  `user id`, `authors`, `candidate id`; the new `updates` route leaves
  Account's right edge, rises to the free top margin (y = 20) and runs
  right; its `1` sits at the top bend.
- **r13 top-midright** — `rubric id`, Rubric, `graded by` with N/1,
  Question top, `tested by` → SQLTestDataset top; the new `updates`
  diamond at x = 2987 enters from the left and leaves right to
  SystemSetting.
- **r14 top-right** — SystemSetting with `setting_key`; the `updates` `N`
  at its left edge. No legacy table sits in this corner now; the
  AssessmentConcept junction is drawn beside the retained `targets`
  diamond (r21).
- **r21 mid-left** — CLO, `clo id`, `maps to`, `assessment id`,
  Assessment (dashed, `LEGACY`), `targets`, Concept, `concept id`.
  AssessmentConcept (dashed, `LEGACY`) sits below `Concept` with its
  composite `assessment_id, concept_id` key; a short orthogonal association
  rises from its top border to the free left vertex of the retained
  `targets` diamond. The two new legacy source routes leave Assessment's
  left edge (y = 600/608) and run down the free channel x = 671/683,
  crossing the existing `maps to` stub orthogonally at y = 752.
- **r22 mid-midleft** — `takes`, `seeds`, `instantiates`, `tagged with`,
  QuestionCandidate, `candidate id`, Concept, `session id`,
  AssessmentSession, `logs`. All original routing unchanged.
- **r23 mid-midright** — Question, `tested by`, `chosen in`, `offers`,
  SelectionLog, MCQOption, `option id`, `answered in`. The `uses` route
  passes horizontally at y = 888, 4 px above the SelectionLog/MCQOption
  top border (no box/text intersection).
- **r24 mid-right** — `pools` with N into AssessmentQuestion; `versions`
  below it; `uses` at the far right; the three right-column keys. Every
  cardinality is individually visible.
- **r31 bottom-left** — LLMCache and `cache id`; the two legacy source
  routes descend x = 671/683 and turn right at y = 1498/1506; legend left
  end with Entity swatch.
- **r32 bottom-midleft** — ConceptCompetency, `competency id`,
  `measured by`/`yields`, CompetencyGap, `gap id`, `flags`/`diagnosed in`.
  The pools/versions/uses bottom corridors run at y = 1498/1506/1514, all
  above the legend and below the key ellipses.
- **r33 bottom-midright** — `records` into Attempt, `selected in`,
  Attempt and `attempt id`; the legend tail with the new dashed
  **“Legacy table (historical rows only)”** entry.
- **r34 bottom-right** — `versions` and `uses` diamonds with `N`/`1`,
  AssessmentBlueprint (dashed) and `blueprint_id`; both routes enter the
  blueprint cleanly from left/right; `LEGACY` tag inside the box.
- **r_new_column** — the free right column: SystemSetting/`setting_key`,
  AssessmentQuestion/composite key, AssessmentBlueprint/`blueprint_id`,
  diamonds `pools`/`versions`/`uses`, three LEGACY tags. AssessmentConcept
  is intentionally in r21 beside the `targets` diamond, not here. No box,
  text or key overlaps.
- **r_legend** — the full legend: Entity, Relationship, Key attribute,
  `1 = one, N / M = many`, `(M : N = many-to-many)`, and the new dashed
  legacy entry.
- **r_junction** — close crop of the `targets`–AssessmentConcept
  association: the retained `targets` diamond at top right, the short
  `assessment_concept` / `junction` annotation, the orthogonal line down
  its left vertex then to the AssessmentConcept box top, and the composite
  key below the box. No floating entity.

### Shared figure-gate note

`scripts/check_rebuild_figures.py` currently asserts `final.png` canvas ==
`original.png` canvas for every figure. The owner explicitly allows this
figure to grow right/bottom, and the final is intentionally
**4300 × 1677** vs the original 3251 × 1677, so the shared gate reports
`erd: canvas (4300, 1677) != original (3251, 1677)`. The F5 work did not
edit that shared script (per the round rules). It needs a one-line ERD
exception (or a per-figure expected canvas) in the main agent's gate
update. Every figure-specific gate is green:
`checker-final.txt` PASS, `checker-final-broken.txt` FAIL, `delta-final.txt`
PASS.

### Honest remaining differences

1. The canvas is wider (4300 vs 3251) because the four additions use a new
   free right column. The original 3251 × 1677 region is geometrically
   identical; when the image is scaled to fit a screen the original
   elements look smaller, but their bboxes are unchanged.
2. Assessment's stroke is dashed and it carries a `LEGACY` tag; bbox,
   title text and all its original connectors are untouched.
3. The legend frame is extended right from x = 2490 to x = 3060; left,
   top, height and every original legend item are unchanged.
4. The two new legacy routes (pools/versions) cross the existing `maps to`
   stub at y = 752; the `uses` route crosses three original vertical stubs
   at y = 888 (x ≈ 2060/2156/2236). The AssessmentConcept junction
   association crosses the short `concept id` key leader at x ≈ 900,
   y ≈ 945. These are orthogonal line-line crossings only; no line goes
   through a box and no text is touched.
5. `updates` uses the free top margin (y = 20), above the account/rubric
   key ellipses; the nullable `system_setting.updated_by` is drawn 1:N as
   the owner specified.
6. Arial/Chrome ink differs from the original raster by antialiasing.
   Against the Stage A clone, only 1,922 of 242,538 ink pixels are
   Stage-A-only (the dashed Assessment border/tag and fringes); all new
   ink is in the additions.
7. `AssessmentConcept` is no longer floating: it sits below `Concept` and
   is joined to the retained `targets` diamond by a short orthogonal
   junction association. This is a table annotation, not a second
   relationship: its `assessment_concept.assessment_id` / `concept_id`
   FKs are the same junction already represented by `targets`. No new
   relationship verb was invented.
8. New labels use the same Arial family/sizes and individual `<text>`
   elements; no label was shrunk. The broken copy piles every label and
   fails 295 problems as required.

### Deliverables

`docs/diagrams/rebuild/erd/`: `erd.svg`, `erd.png` (4300 × 1677),
`erd.drawio`, `erd-broken.svg`, `spec.json`, `text-content.json`,
`trace.json`; Stage A preserved in `stage-a/`.

Evidence: `final.png`, `side-by-side-final.png`,
`side-by-side-left-final.png`, `side-by-side-stage-a-final.png`,
`overlay-final.png`, `overlay-stage-a-final.png`,
`bboxes-stage-a-on-final.png` (green = exact Stage A entity bboxes),
`diff-final.png` (Stage A clone → final difference), `regions-final/`
(15 crops), `checker-f5.txt`, `checker-f5-broken.txt`, `delta-f5.txt`, and
`docs/qa/erd-evidence.md`.

Old Stage B evidence files are kept with a `rejected-stage-b-` prefix
(`rejected-stage-b-checker.txt`, `rejected-stage-b-checker-broken.txt`,
`rejected-stage-b-delta.txt`, `rejected-stage-b-inventory.md`) so the
current gates are unambiguous: `checker-final.txt`,
`checker-final-broken.txt`, `delta-final.txt` (also mirrored as
`checker-f5.txt`, `checker-f5-broken.txt`, `delta-f5.txt`).

### Files changed in this round

- Replaced: `docs/diagrams/rebuild/erd/erd.svg`, `erd.png`, `erd.drawio`,
  `erd-broken.svg`, `spec.json`, `text-content.json`;
  `docs/qa/rebuild-preview/erd/{final.png,side-by-side-final.png,
  overlay-final.png,diff-final.png,regions-final/*,report.md}`.
- Added: `docs/diagrams/rebuild/erd/trace.json`;
  `docs/qa/rebuild-preview/erd/{side-by-side-left-final.png,
  side-by-side-stage-a-final.png,overlay-stage-a-final.png,
  checker-f5.txt,checker-f5-broken.txt,delta-f5.txt}`;
  `docs/qa/erd-evidence.md`; `scripts/build_erd_f5.py`,
  `scripts/check_erd_delta_f5.py`, `scripts/make_erd_previews_f5.py`.
- Not touched: `docs/qa/handover.md`, any `.docx`, application code,
  User Story, Stage A files, other figures, shared scripts.

## Previous Stage B (rejected — historical)

The earlier Stage B used `content-delta-verified.md` §8 to remove
`Rubric`, `QuestionCandidate`, `SQLTestDataset`, `SelectionLog` and
`LLMCache`, move/re-point diamonds, and add `requires`/core `versions`.
That output is superseded by this F5 redo; its old files were overwritten.
The previous report text is retained in git history only.

# Use Case Diagram — Stage A clone + Stage B content delta

**Status: Stage A PASS, Stage B PASS, owner-fix F1 PASS (right margin). No
`.docx` touched; no commit from W1.**
Figure: `ArchitectureDesign_ver1.1_image2.png` (3000 × 3300 source; final is
now 3120 × 3300 after the owner-requested right margin), caption
“DBCAS Use Case Diagram” / Architecture Figure 1. Final files:
`docs/diagrams/rebuild/use-case/` and `docs/qa/rebuild-preview/use-case/`.

## Stage A — clone only

### Pipeline (dedicated W1 tracer; shared scripts untouched)

1. `scripts/trace_figure_w1.py` — a copy of the shared tracer with the three
   known defects fixed:
   - **adaptive per-fill dilation** for the thick ellipse rings: each ring is
     measured at the top/bottom centre (5 px here), the fill mask is dilated by
     ring+2 and restricted to pixels near the fill or the measured stroke; the
     old fixed 6/16 px dilation welded the rings into the association network.
   - **fused-structure decomposition**: the frame + 16 fan lines + 2 actors
     arrive as ONE 126 636 px component. It is decomposed by measured topology:
     the frame from full-width/height runs, each fan line from its own clean
     component between frame and ellipse (PCA fit + measured hub), the four
     elbow trunks from axis runs, and each actor as head circle + body + arms +
     legs. No global skeleton split, no auto layout.
   - **title-glyph blobs are text, not shapes**: fills smaller than an ellipse
     are rejected; the title is one same-baseline band (“DBCAS Use Case
     Diagram”), not two word fragments.
2. `text-content.json` — all strings transcribed from 2× crops (every ellipse,
   both actors, title, subtitle, note). **23 logical labels; 26 Stage A text
   bands** because UC08, UC10 and UC18 wrap onto two lines.
3. `text-fixes.json` — no splits/replaces/nudges were needed; spacing was never
   shrunk and no labels were merged.
4. `make_font_plan.py` → `font-plan.json` (width-driven Arial; title/subtitle/
   UC02/UC03 bold), then `calibrate_letter_spacing.py` → `letter-spacing.json`
   measured from the real Chrome renderer.
5. `build_figure_w1.py` → `use-case.svg`, `use-case.drawio`, `spec.json`, PNG
   at exactly 3000 × 3300. The W1 builder applies the measured label gap only
   to the boundary top edge (the shared builder would have gapped the bottom
   too) and emits the actor head/limbs with measured stroke colour/width.
6. `make_figure_inventory_w1.py` → `inventory.md` (Stage B: 19 shapes + 21
   lines + 20 arrowheads + 2 actor stick figures + 27 texts = **89 elements**);
   `inventory-stage-a.md` is the Stage A inventory (26 texts = **88 elements**).

### Stage A element counts

- **19 shapes exactly: 1 system boundary + 18 ellipses.** No title-glyph
  shape, no duplicate boundary, no actor emitted as a shape.
- **21 lines, 20 arrowheads** (16 fan associations + 4 elbow trunk lines).
- **2 actor stick figures** (head circle + body + arm + 2 legs each).
- **26 text bands = 23 logical labels** (3 wrapped UC labels).
- Boundary: bbox 352.5,272.5 → 2647.5,3057.5, stroke 6, top label gap
  1069→1931, bottom continuous.

### Rule 8 — deliberately broken first, then the real build

- `make_broken_svg.py` piles all 26 labels → `checker-broken.txt`:
  **FAIL, exit 1, 113 problems**.
- Real Stage A build → `checker-pass-stage-a.txt` (run on
  `use-case-stage-a.svg`): **PASS, exit 0**, 26 labels exactly match,
  101 elements each exactly once.

### Rule 1 — full clone and all 9 region tiles viewed (Stage A)

- **r11 top-left** — blank margin; boundary top-left corner; the outer trunk
  vertical at x≈294 crossing the boundary; the UC02/UC03 horizontal trunk
  lines; UC01 ellipse top-left with its arrow.
- **r12 top-middle** — one-line bold title; “DBCAS system” at the boundary
  label gap; UC02 Login and UC03 Logout ellipses with arrows entering from both
  sides; top edges of UC01/UC04.
- **r13 top-right** — boundary top-right corner and right vertical; trunk
  lines at y≈480/700 crossing the boundary; UC04 right edge with arrow.
- **r21 middle-left** — Learner actor (head, body, arm, legs), label; fan lines
  from the arm hub; boundary and trunk verticals; UC12/13/14/15 arrow tips.
- **r22 middle-middle** — white space between the two ellipse columns; clean
  ellipse edges; no duplicated labels.
- **r23 middle-right** — Administrator actor, label, fan lines to UC05–UC08;
  the UC11 line is opened at the “Administrator” label (rule 8).
- **r31 bottom-left** — boundary bottom-left corner; UC16/17/18 arrow tips;
  start of the bottom note; bottom border continuous.
- **r32 bottom-middle** — UC16/17/18 and UC09/10/11 bottoms; full bottom note;
  bottom border continuous.
- **r33 bottom-right** — bottom-right corner; UC09/10/11 right edges and
  arrows; end of the note.
- Full `clone.png`, `side-by-side.png`, `overlay.png` viewed. The overlay is
  black where both agree; red = original only, blue = clone only.

### Honest Stage A differences

1. **Glyph metrics** — Arial as rendered by Chrome differs from the original
   font; right edges and word positions differ by roughly 1–4 px (red/blue
   fringes). Letter-spacing makes the total band width match, but the residual
   is distributed between words.
2. **Association lines** — drawn from the measured hub to the ellipse’s
   measured centre height; the original’s anti-aliased lines differ by 1–2 px
   in slope. Arrowhead polygons are 15 × 15 px approximations.
3. **Rule-8 cut** — the UC11 fan line is opened around the “Administrator”
   label because the original line passes behind the ‘A’; the clone has a small
   gap where the original is continuous (required by rule 8).
4. **Actor legs** — measured diagonal components are joined at the hip and
   extended 6 px to the measured AA end; tips differ by 1–2 px.
5. **Ellipse path** — the SVG path is the measured ring centreline (fill bbox
   expanded by ring/2+0.5, i.e. 3 px); the original fill/ring AA fringe is
   ±1 px.
6. **Boundary gap** — top gap measured 1069→1931; bottom border is continuous
   (a first build wrongly repeated the gap on the bottom; fixed and re-checked).

## Stage B — verified content delta only

Applied `docs/qa/content-delta-verified.md` §1. **No UC19/UC20 added; 18 use
cases kept** (the evidence-based UC19/UC20 proposal is in the section below,
still not added).

| Band | Stage A | Stage B |
| --- | --- | --- |
| UC09 | `UC09 Configure adaptive assessments` | `UC09 Configure result flow and settings` |
| UC12 | `UC12 Take timed adaptive assessment` | `UC12 Take personalized practice session` |
| UC18 | `UC18 Review assessment history and` / `evidence` | `UC18 Review practice history and` / `evidence` |
| bottom note | one line | unchanged first line + `UC12: 1–20 questions (default 5) · 30-minute expiry.` as a second line |

- **27 text bands = 23 logical labels** (3 wrapped UC labels; the note now has
  two lines). No label was shrunk or merged: font sizes stay 36/37 px, and the
  changed bands got wider measured boxes where the new wording is longer.
- Stage B checker `checker-pass-stage-b.txt`: **PASS, exit 0, 27 labels,
  102 elements**; broken build `checker-broken-stage-b.txt`: **FAIL, exit 1,
  120 problems**.
- Stage A → B delta `checker-stage-b-delta.txt`: **PASS** — canvas, 19 shapes,
  21 lines, 20 arrowheads and 2 sticks identical; only X007/X019/X023 changed
  and X027 (practice note) added; all other text entries byte-identical.
- Stage B images: `final.png` (3000 × 3300), `side-by-side-final.png`,
  `overlay-final.png` (red = original only, blue = clone only), `diff.png`
  (amplified absolute difference), `regions-final/` — all 9 tiles viewed. The
  only visible Stage B changes are the three renamed ellipses and the second
  note line; everything else matches Stage A.

## Owner fix 2026-11-09 — Administrator label right margin

Owner report: the Administrator label is cut at the right canvas edge and the
actor sits further right than the original. Fix applied: **canvas widened on
the right only, 3000 × 3300 → 3120 × 3300 (+120 px); no element moved.**

### What the pixels actually measured

| Item (original vs Stage B/F1) | Original | Stage B / F1 |
| --- | --- | --- |
| Administrator label band X014 | rendered ink right edge **2974**, left 2717 | right edge **2974**, left 2717 (identical) |
| Label right margin to canvas | **26 px** (3000 − 2974) | **146 px** (3120 − 2974) |
| Actor head top arc, y = 1551 | x 2835–2855, centre **2845.0** | x 2836–2853, centre **2844.5** |
| Actor stick K02 bbox / circle | — | [2808, 1548, 2881, 1621] / [2845.0, 1585.0, 32.6] (traced from the original) |

The trace is right: the actor was **not** displaced (0.5 px difference in the
rendered head arc is antialiasing). The real defect is the near-zero right
margin: the source itself ends the label only 26 px from the canvas edge, and
the 1:1 side-by-side put the panel border immediately after it, so the regular
Arial final looked clipped. Adding 120 px of white canvas on the right keeps
the actor and label at their measured, original coordinates and gives the full
word 146 px of clear space (4.7 % of the new width, versus 0.9 % before).

### Verification

- **Rule-8 checker — PASS, exit 0**: `checker-pass-f1.txt`, 27 labels exactly
  match `text-content.json`, 102 elements each exactly once, no text/text or
  text/foreign-segment intersection (`use-case.svg`, 3120 × 3300).
- **Deliberately broken — FAIL, exit 1, 120 problems**:
  `use-case-broken-f1.svg` → `checker-broken-f1.txt` (same 120 as Stage B).
- **F1 delta — PASS**: `checker-f1-delta.txt`. Canvas 3000 × 3300 → 3120 ×
  3300 (height unchanged); shapes 19 = 19, lines 21 = 21, sticks 2 = 2,
  dashes 0 = 0; **all 27 texts byte-identical** (content, x, y, size, weight,
  letter-spacing, measured band, host). This is stricter than "only the
  actor/label/margin changed": the actor and label did not change either.
  Administrator label measured [2717, 1885, 2975, 1914], right margin 145 px
  by the spec band / 146 px by rendered ink. Pixel proof: the 3000 × 3300
  content region of the new `use-case.png` is **byte-for-byte pixel-identical**
  to Stage B (`use-case-stage-b.png`): 0 differing pixels, max channel
  difference 0; the new x = 3000–3119 band is pure white (255,255,255).
- **Figure gate**: the use-case row passes (final 3120 × 3300 equals the
  padded comparison original). A full shared-worktree run at the end of this
  task reported one **unrelated** problem from F3's in-progress ERD work:
  `erd: canvas (4300, 1677) != original (3251, 1677)`; no use-case problem was
  listed. For the 1:1 comparison the untouched original is padded with white
  on the right to the new canvas (`original.png`, 3120 × 3300); the
  byte-identical raw source is kept as `original-source.png` and at
  `docs/qa/diagram-originals/ArchitectureDesign_ver1.1_image2.png`. The
  Stage A clone (`clone.png`, `use-case-stage-a.svg`, `spec-stage-a.json`,
  `trace-stage-a.json`) is untouched.

### New final images and regions VIEWED

- `final.png` (3120 × 3300) — full diagram viewed. Title centred at the same
  place; boundary 352.5 → 2647.5; 18 ellipses and both actors unchanged; the
  only eye-visible change is a 120 px white band on the right. “Administrator”
  is complete, ending at x = 2974 with 146 px of white before the edge.
- `r13.png` (top-right, x 2080–3120, y 0–1100) — blank top margin; the
  boundary top-right corner at (2647.5, 272.5) and its right vertical; the
  UC02/UC03 horizontal trunk lines at y ≈ 480/700 crossing the boundary; the
  UC04 ellipse right edge and arrow at the bottom-left of the tile; 473 px of
  clean white canvas to the right of the boundary.
- `r23.png` (middle-right, x 2080–3120, y 1100–2200) — UC05/UC06/UC07/UC08
  right edges and arrows; the Administrator head, body, arms and legs; fan
  lines converging at the left hand; the complete “Administrator” label
  (2717–2974) centred under the actor; 146 px of white margin to the canvas
  edge. No clipped glyph.
- `r33.png` (bottom-right, x 2080–3120, y 2200–3300) — UC09/UC10/UC11 right
  edges and arrows; the bottom-right boundary corner (2647.5, 3057.5); the end
  of the bottom note (“UC12.”); continuous white margin on the right.
- `right-edge-final.png` — raw original crop (x 2550–3000) | final crop
  (x 2550–3120), y 1400–2020, 1:1. Both labels end at the same absolute
  x = 2974; the raw original shows only 26 px to its panel edge, while the
  final shows 146 px of white margin and the complete final “r”. The only
  visible difference is the source's heavier Administrator glyphs versus Arial
  regular (pre-existing; not changed here).
- `side-by-side-final.png` (6264 × 3300) — padded original | final at 1:1;
  every ellipse, line, arrow and actor aligns; only the three Stage B renamed
  labels and the second note line differ; the right margin is now present in
  the final panel.
- `overlay-final.png` (3120 × 3300) — black where both images agree; red =
  original only, blue = final only. Text shows the usual 1–4 px red/blue glyph
  fringes; UC12, UC09, UC18 and the second note line show the Stage B content
  delta; the Administrator label shows the bold-vs-regular outline difference.
  The right 120 px band is white (no ink in either image).
- `diff.png` (3120 × 3300, 3 × Σ|RGB difference|) — black background with
  grey/white glyph outlines; strong white at UC12, UC09, UC18 and the second
  note line; the new right margin is pure black (zero difference).
- Overlay counts: **108,698 changed pixels** (original-only 44,222, final-only
  64,476) out of 10,296,000; diff nonzero 263,748 px, mean 5.84, max 255 —
  identical content-difference numbers to Stage B because no element moved
  (the extra 120 px column is zero-difference).

### Word width / ratio

The v1.2 Architecture `.docx` stores this figure at **5,580,000 × 6,138,000
EMU = 6.1024 × 6.7126 in** (6.10 × 6.71 in). The new canvas is 3120 × 3300,
ratio **0.9455** (was 0.9091). At the same 6.10 in width the new image is
**6.452 in** high (5,899,638 EMU), so **the width still matches 6.10 in but
the width:height ratio no longer matches 6.10:6.71**; content at that width
prints at **96.15 %** of the old scale, and keeping the stored 6.10 × 6.71
frame would stretch it vertically by about 4.0 %. No `.docx` was touched. If the exact 6.10 × 6.71 frame is mandatory, the alternatives are
(a) add 132 px of bottom canvas (3120 × 3432 keeps the ratio) or (b) keep
3000 × 3300 and move the actor + label left, which would move the traced
actor away from the original position.

### Honest remaining differences

1. The 120 px right margin is new white canvas; the source original keeps its
   26 px margin. The raw source is preserved as `original-source.png`.
2. The source “Administrator” is drawn with heavier glyphs than Arial regular
   (pre-existing Stage A font substitution); rendered right edge differs by
   1 px (2974 vs 2973 at threshold < 100), head centre by 0.5 px.
3. Aspect ratio/Word height as stated above.
4. No UC19/UC20 was added to the figure; the evidence-based proposal is below.

## UC19/UC20 analysis (owner question — NOT added to the figure)

Inspected: `frontend/src/components/Layout.jsx` (admin nav),
`frontend/src/App.jsx` routes, `frontend/src/pages/admin/` (all six screens),
`frontend/src/i18n/vi.json`, and the matching backend routers.

- **“Hệ thống” — `/admin/system`** (`App.jsx:114`, `Layout.jsx:23`, vi label
  “Hệ thống”) is `AdminSystemPage.jsx`. Its only editable capability is the
  global `result_flow` radio (`IMMEDIATE` / `HUMAN_VERIFIED`), saved with
  `PUT /api/v1/admin/system` (`backend/app/routers/practice.py:78-87`,
  `backend/app/services/system_settings.py`). That is exactly **UC09
  “Configure result flow and settings”**, which is already in the figure.
  The other two cards (AI status, basic information) are read-only status.
  **UC09 covers “Hệ thống”; a separate system-settings UC would duplicate it.**
- **“Duyệt bài” — `/admin/grading`** (`App.jsx:116-117`, `Layout.jsx:20`, vi
  label “Duyệt bài”) is `AdminGradingPage.jsx`: queue
  (`GET /admin/grading-reviews`), detail, per-attempt score/comment approval,
  publish/duyệt, retry failed grading, SELECT-only SQL verification, AI
  evaluation panel, audit trail and score-edit history
  (`backend/app/routers/admin.py:64-96`, `practice.py:123`). **None of UC09,
  UC10 or UC11 covers this.** UC10 is explicitly the AI question-candidate
  pipeline (`admin.py` section “UC10 — AI question candidates”, endpoints
  `/question-candidates*`); UC11 is explicitly cohort analytics and learner
  drill-down (`admin.py` section “UC11 — cohort analytics & learner
  drill-down (DBCAS-25)”, `/analytics/*`); UC15 is the learner receiving
  results, not the administrator reviewing and releasing them.

**Proposed exact labels (from `docs/qa/content-delta-verified.md`, not yet in
the figure):**

- `UC19 Manage interface preferences` — learner `/settings` page
  (`App.jsx:105`, `Layout.jsx:15`, `SettingsPage.jsx`); language and theme are
  real, persisted browser preferences. This is the only other verified
  capability still absent from the figure; it is not an Admin-nav item.
- `UC20 Review and publish human-verified results` — the “Duyệt bài” gap
  above (`grading_review.py`, `/api/v1/admin/grading-reviews`).

If the owner only wants the two Admin-nav items resolved, add **UC20 only**:
“Duyệt bài” is the real gap, while “Hệ thống” is already UC09. Add UC19 as
well only if the baseline is allowed to grow by both verified extensions.
Nothing was added to the SVG/PNG/drawio in this round.

## Deliverables

`docs/diagrams/rebuild/use-case/`: `use-case.svg`, `use-case.drawio`,
`use-case.png` (3120 × 3300), `use-case-broken.svg`,
`use-case-broken-f1.svg`, `use-case-stage-a.svg`, `use-case-stage-b.svg`,
`use-case-stage-b.png`, `spec.json`, `spec-stage-a.json`, `spec-stage-b.json`,
`trace.json`, `trace-stage-a.json`, `trace-stage-b.json`,
`text-content.json`, `text-content-stage-a.json`, `text-fixes.json`,
`font-plan.json`, `font-plan-stage-a.json`, `letter-spacing.json`,
`letter-spacing-stage-a.json`, `inventory.md`, `inventory-stage-a.md`,
`trace_markers.png`.

`docs/qa/rebuild-preview/use-case/`: `original.png` (padded comparison
canvas), `original-source.png` (raw 3000 × 3300), `clone.png`,
`side-by-side.png`, `overlay.png`, `regions/` (Stage A);
`final.png` (3120 × 3300), `side-by-side-final.png`, `overlay-final.png`,
`diff.png`, `regions-final/`, `right-edge-final.png` (F1); `checker-pass.txt`,
`checker-pass-stage-a.txt`, `checker-pass-stage-b.txt`,
`checker-pass-f1.txt`, `checker-broken.txt` (Stage A),
`checker-broken-stage-b.txt`, `checker-broken-f1.txt`,
`checker-stage-b-delta.txt`, `checker-f1-delta.txt`.
Helper scripts: `scripts/make_use_case_f1_previews.py`,
`scripts/check_use_case_f1_delta.py` (shared scripts untouched).

## Logic-alignment update — 2026-11-09

The mandatory-review decision removed the administrator's result-flow choice.
UC09 is now **“Review and approve results”** (was “Configure result flow and
settings”). Coordinates and all other labels are unchanged. The new render is
in `final.png`; the rule-8 checker is **PASS 27 labels / 102 elements**, the
deliberately broken copy **FAIL 123**, and the word/flow only difference is
recorded in `overlay-final.png`/`diff.png`.

# Container Diagram — Stage A clone + Stage B content delta (Round 1 REDO, figure 3)

**Owner-fix round F2 (2026-11-09): PASS — canvas now 1780 × 1645. See the
"F2 owner fix" section at the bottom; the Stage A/B sections are the
historical record.**

**Status: Stage A (clone only) PASS, Stage B content delta PASS.**
Figure: `ArchitectureDesign_ver1.1_image4.png` (1444 × 1418) →
`docs/diagrams/rebuild/container/`.

## Pipeline

1. `scripts/trace_figure.py` — pixel measurement of the original →
   `trace.json` (**9 shapes**: dashed system boundary + 8 boxes
   (6 rounded, 2 database cylinders with measured silhouette outline + lid
   ellipse), **4 dash runs** (41/42/47/47 dashes, on≈12 off≈12),
   **7 lines** with sampled stroke colour + width, **7 arrowheads**,
   **47 text bands** with ink colours) + `trace_markers.png` (verification
   overlay of every detected element, viewed).
2. `text-content.json` — all 47 strings read from 2x crops of the original
   (every box and every line label viewed while transcribing); explicit
   `free_ids`/`box_ids` keep the string↔bbox mapping stable.
3. `text-fixes.json` — the original's own text-frame defects, fixed with
   spacing only (owner rule: never shrink/merge — enlarge spacing):
   - **splits**: 3 merged line pairs (a descender touched the next row's
     ascender → Learner/Sandbox/LLM line 3|4 split at y 116/1261/1262);
   - **replaces**: API Application line 3 (its middle was fused into two
     wrong bands) rebuilt as one band; line 4 re-based below it;
   - **nudges**: 2 inherited line-through-label grazes shifted (+6 px
     "views competency profile", +14 px "candidate requests [HTTPS/REST]")
     and inherited frame overlaps resolved down the stack (≤10 px each,
     total 14 labels, applied by `scripts/resolve_text_spacing.py` on the
     *rendered* geometry until 0 overlaps remained).
4. `scripts/make_font_plan.py` — width-driven Arial calibration; a bold
   list forces the 8 box titles + the boundary label bold, everything else
   regular (matches the original); occluded lines (top clipped by the
   original's overlapping text frames) get `anchor=bottom` so the full line
   renders at the original baseline.
5. `scripts/build_figure.py` → `container.svg`, `container.drawio`
   (hand-authored mxGraph; draw.io CLI unavailable), `spec.json`; PNG
   rendered with headless Chrome at exactly 1444 × 1418.
6. `scripts/calibrate_letter_spacing.py` → `letter-spacing.json` —
   residual width steps (integer font sizes) corrected with letter-spacing
   measured from the real renderer; rebuild once more with the calibration.
7. `scripts/make_figure_inventory.py` → `inventory.md` — every element
   listed exactly once (**74 elements**: 9 shapes + 4 dash runs + 7 lines +
   7 arrowheads + 47 texts).
8. Rule-8 line/text cut: the tracer opens lines at the measured ink boxes,
   then `build_figure.py` repeats the cut against the **rendered**
   font-metric boxes (exactly what the checker computes) so no segment can
   cross a label — 1 extra segment opened on this figure (the
   `[read-only transaction]` corner of L08's tail).

## Rule 8 — checker (deliberately broken first, then the real build)

- `make_broken_svg.py` piles all 47 labels on top of each other →
  `checker-broken.txt`: **FAIL, exit 1, 163 problems** (text/text +
  text/segment) — the gate can fail.
- Real build → `checker-pass.txt`: **PASS, exit 0**:
  34→47 labels exactly match the expected list (46 distinct — "[Person]"
  appears twice), no text/text intersection, no text/foreign-segment
  intersection (0 own-line exemptions), 251 elements each exactly once.

## Rule 1 — region-by-region description (all 9 tiles + full render viewed)

- **r11 top-left** — dashed boundary top-left corner; bold "DBCAS System
  [Software System]" just inside the top border; Learner box's right half
  (title/[Person]/"Undergraduate student taking"/"database assessments");
  left dashed border continuous from the corner down.
- **r12 top-middle** — Learner and Administrator box halves with all four
  lines each; both association lines descending to Web Application with
  "Takes assessments, / views competency profile" and "Manages CLOs, bank,
  rubrics; / reviews…" labels; top dashed border crossing behind; Web
  Application box with its four lines (the line-3/4 gap visible as in the
  original, full text now readable).
- **r13 top-right** — Administrator box right half (4 lines); label tails
  "…s CLOs, bank, rubrics;" / "…ews analytics"; boundary top-right corner
  turning into the right dashed border.
- **r21 middle-left** — left dashed border running down; right edge of the
  Web Application box and the "[" of its Container line at the tile edge.
- **r22 middle-middle** — "Delivers to user's / web browser" beside the
  vertical arrow; Single Page Application box (4 lines); "Makes API calls /
  [JSON/HTTPS + JWT]"; API Application box top with its title + Container
  line.
- **r23 middle-right** — right dashed border; the LLM box's top-left corner
  at the bottom (LLM sits outside the boundary, as in the original).
- **r31 bottom-left** — left border's bottom corner; the Database cylinder
  (cap curve, lid ellipse, body) with "Database / [Container: PostgreSQL 17]
  / Users, CLOs, concepts, question bank, / attempts, evidence, cached LLM
  responses"; the API→Database arrow landing on the cap with its
  arrowhead; bottom dashed border turning at the corner.
- **r32 bottom-middle** — API Application box bottom; three arrow labels
  "Reads from and / writes to [SQL]", "Executes learner SQL /
  [read-only transaction]"; SQL Execution Sandbox cylinder with its four
  lines; Database cylinder's right edge; bottom dashed border.
- **r33 bottom-right** — the API→LLM arrow crossing the right dashed
  border (LLM Provider API is external — outside the boundary, correct);
  labels "Sanitized prompts / / candidate requests [HTTPS/REST]"; gray
  rounded LLM Provider API box (4 lines); boundary's right/bottom-right
  corner.

## Proof images (`docs/qa/rebuild-preview/container/`)

- `original.png`, `clone.png` — same canvas/origin, both 1444 × 1418
- `side-by-side.png` — original | clone at 1:1
- `overlay.png` — black = ink in both, **red = original only**,
  **blue = clone only**
- `regions/r11..r33.png` — 3×3 tiles of the clone (all viewed above)
- `checker-broken.txt` (FAIL 163), `checker-pass.txt` (PASS)
- `calibrate.txt` — letter-spacing calibration measurement
- `trace.json`/`text-fixes.json` live with the figure in
  `docs/diagrams/rebuild/container/`

## Honest differences (overlay, all viewed)

1. **Glyph metrics**: Arial-as-rendered-by-Chrome differs from the
   original's font → right edges ±2–5 px on most labels (red/blue
   fringes); top-left anchors match within 0–1 px.
2. **Occluded lines revealed**: where the original's overlapping text
   frames hide the top of a line ("Delivers static content and the",
   "Learner Assessment Portal, Administrator", "Authentication, …"), the
   clone draws the full line at the original baseline (blue above red) —
   content readable, geometry per the baseline.
3. **Two intentional label shifts** (checker-required spacing): "views
   competency profile" +6 px, "candidate requests [HTTPS/REST]" +14 px
   right of the original (they grazed their own flow line).
4. **14 box labels nudged ≤10 px vertically** (spacing-only, rule 7) so no
   two labels intersect — all listed in `text-fixes.json`.
5. **Dash phase**: dashes are emitted on a uniform on/off=12/12 grid from
   the measured span; the original's runs vary ±1 px, so dashed borders
   alternate red/blue fringes after the first few dashes.
6. Border strokes: original ~2 px AA strokes vs the clone's crisp 2 px
   (blue/red 1 px fringes at box outlines).

## Deliverables

`docs/diagrams/rebuild/container/`: `container.svg`, `container.drawio`,
`container.png`, `container-broken.svg`, `spec.json`, `trace.json`,
`text-content.json`, `text-fixes.json`, `font-plan.json`,
`letter-spacing.json`, `inventory.md`.

## Stage B — verified content delta (2026-11-09)

**Status: PASS.** Applied `docs/qa/content-delta-verified.md` §2; no
Email/OAuth box was added (pending owner decision, see below).

| Band | Stage A | Stage B |
| --- | --- | --- |
| Learner body | `Undergraduate student taking` / `database assessments` | `Undergraduate student taking` / `database practice` |
| Administrator body | `...curates content and configures assessments` | `...curates content and maintains system settings` |
| Web Application tag | `[Container: React 19.3, Vite 8]` | `[Container: Nginx 1.29]` |
| Web Application body | `...single-page application bundle` | `...SPA bundle` |
| SPA tag | `[Container: React, Tailwind CSS 4, Chart.js 4.5]` | two lines: `[Container: React 19.3, Vite 8.3.1,` / `Tailwind CSS 4.3.3, Chart.js 4.5.1]` |
| SPA body | `Learner Assessment Portal, Administrator` / `Management Portal, SQL editor, radar/bar charts` | `Learner and Administrator portals,` / `SQL editor, radar and bar charts` |
| API tag | `[Container: FastAPI 0.141, Python 3.13]` | `[Container: FastAPI 0.141.1, Python 3.13]` |
| API body | `...assessment sessions,` / `grading, adaptive selection, ...` | `Authentication, practice sessions, plan assembly,` / `grading, competency and gap engines` |
| Database body | `...attempts, evidence, cached LLM responses` | `...sessions, evidence, cached LLM responses` + `(41 tables)` |
| Flow label | `Takes assessments,` | `Takes practice sessions,` |

- **49 text bands** (47 + SPA tag line 2 + `(41 tables)`); 48 distinct strings
  because `[Person]` appears twice. The exact versions/wording concatenate
  correctly across the wrapped bands (checked).
- Stage B checker `checker-pass-stage-b.txt`: **PASS, exit 0, 49 labels,
  253 elements**; broken build `checker-broken-stage-b.txt`: **FAIL, exit 1,
  160 problems**.
- Stage A → B delta `checker-stage-b-delta.txt`: **PASS** — canvas, 9 shapes,
  4 dash runs, 10 lines and all arrowheads identical; only the 13 changed
  labels plus the 2 added bands differ; all other text entries byte-identical.
  This also proves no Email/OAuth box was invented.
- **SPA box layout**: the exact version string is 655 px at the original
  21 px size and cannot fit one 482 px line. It is split over two lines at the
  same font size (never shrunk); the box’s five lines are 1–2 px apart and the
  title sits 2 px inside the top border. The checker confirms no text/text
  intersection. This is the only geometry consequence of the delta.
- Stage B images: `final.png`, `side-by-side-final.png`, `overlay-final.png`,
  `diff.png`, `regions-final/`. All 9 Stage B tiles viewed:
  r11 Learner box/boundary; r12 both person boxes + Web Application;
  r13 Administrator/boundary; r21 left border + box edges; r22 SPA box
  (5-line text) + API top; r23 right border + LLM top; r31 Database cylinder
  with `(41 tables)`; r32 SQL Sandbox; r33 LLM Provider API. No duplicated
  labels, no clipping, no text crossing a line.
- **Pending owner decision — Email/OAuth:** not added. The original 8-box
  composition has no free block inside the boundary; adding
  `Email Service` and `OAuth Identity Providers` would either move existing
  boxes or place new external boxes in the right-hand margin, changing the
  original composition. Per the verified delta’s fallback, they remain
  context-level dependencies for the owner to decide. No Mailpit box was
  invented inside the boundary.
- Stage A was re-verified after the delta by rebuilding the saved Stage A
  spec: `checker-pass-stage-a.txt` **PASS, 47 labels, 251 elements**;
  Stage A artifacts are preserved as `*-stage-a.*` and `regions-stage-a/`.
- Stage B deliverables: `container.svg`, `container.drawio`,
  `container.png` (1444 × 1418), `container-broken.svg`, `spec.json`,
  `trace.json`, `text-content.json`, `font-plan.json`, `letter-spacing.json`,
  `inventory.md`; preview `final.png`, `side-by-side-final.png`,
  `overlay-final.png`, `diff.png`, `regions-final/`,
  `checker-pass-stage-b.txt`, `checker-broken-stage-b.txt`,
  `checker-stage-b-delta.txt`.


---

## F2 owner fix (2026-11-09) — collisions, weights, OAuth/Email

**Status: PASS.** Canvas **1780 × 1645** (was 1444 × 1418). Figure:
`docs/diagrams/rebuild/container/container.svg` / `.png` / `.drawio`.

### What changed (owner's three items)

**(a) Box text collisions.** Every label inside the six rounded boxes and the
two cylinders was re-laid out with one uniform ink gap and clear borders; no
font was shrunk. Rounded boxes use 14 px top/bottom padding and a 7 px gap
between ink boxes; the cylinders keep their measured 147 px body and use a
26 px lid clearance / 4 px ink gaps / 8 px bottom clearance. Boxes grow
downwards only, so every top-left anchor is unchanged:

| Box | old height | new height |
| --- | --- | --- |
| Learner | 110 | 122 |
| Administrator | 110 | 123 |
| Web Application | 107 | 124 |
| Single Page Application | 104 | 153 |
| API Application | 106 | 127 |
| LLM Provider API | 107 | 123 |
| Database / SQL Sandbox cylinders | 147 | 147 (unchanged) |

The smallest text-to-border margin is now 7 px (checked by the delta gate),
versus the previous 2 px (`Administrator`, `Single Page Application`).

**(b) Restored weights (measured from the original crop).**
- LLM Provider API border: original rows at the top edge read
  `255, 146, 107, 143, 153` (stroke `#6B6B6B` over fill `#999999`), i.e.
  **1.95 px coverage ≈ 2 px**, not the 7 px stub. Final: 2 px `#6B6B6B`
  (crisp rows `107, 107`). The new OAuth/Email boxes use the same 2 px
  `#6B6B6B` border.
- `Sanitized prompts /`: restored to **20 px regular `#222222`** (the
  original cap height is 13 px; Arial 20 px has a 14 px cap, so still above
  the original). It now matches `candidate requests [HTTPS/REST]`
  (20 px regular `#222222`): PNG stem-run median/p75 are 2/2 px for both and
  the mean is 2.20 vs 2.29 px.
- API→LLM flow line: 2.5 px black → **2 px `#444444`**, matching the other
  flow lines. The two web-tier vertical lines were also restored from
  2.5/4 px `#7D7D7D` to their measured **2 px `#444444`**.

**(c) New external boxes and edges.** `OAuth Providers`
(1069,1480)-(1403,1610) and `Email Service` (1420,1480)-(1754,1610), both in
the LLM Provider API style (334 × 130, radius 22, `#999999` fill,
`#6B6B6B` 2 px border, white bold 25 px title, 20/19 px body). Two labelled
orthogonal edges leave the API Application right edge (981,950/970):

- `OAuth sign-in [HTTPS]` → OAuth Providers top (1236,1480), via the
  x=1038 lane and y=1385 bus;
- `Password-reset email [SMTP]` → Email Service top (1587,1480), via the
  x=1052 lane and y=1355 bus.

The lanes run in the 1025–1069 corridor outside the system boundary and left
of the LLM box; the buses run below the LLM box. **Pixel scan of the LLM
interior (x 1072–1400, y 1192–1309) after rendering: 0 pixels darker than
90** — no OAuth/Email route passes through the LLM box (the only dark pixels
near its top are the pre-existing API→LLM arrowhead at x 1164–1177).

### Checker / proof evidence

- `checker-pass-fix.txt`: **PASS, exit 0** — 59 text bands (56 distinct
  strings; `[Person]` ×2, `[External Software System]` ×3), **0** text/text
  intersections, **0** text/foreign-segment intersections, 269 elements each
  exactly once. Expected list: 59 = 1 title + 16 flow labels + 42 box texts.
- `checker-broken-fix.txt`: **FAIL, exit 1, 193 problems** on the
  deliberately piled-label SVG (59 labels) — the gate can fail.
- `checker-delta-fix.txt`: **PASS** — Stage B boundary, both cylinders, 4
  dash runs, every old arrow tip, and 14 of the 15 old free labels (the
  DBCAS title + 13 flow labels) are identical; only `Sanitized prompts /`
  changed weight. Every other box label keeps its content/weight/size/host
  and moves only vertically, with x drift 0 px. Old shapes only grow
  downwards (x0/y0/x1 identical); new shapes live below the old canvas.
- Elements: 11 shapes + 4 dash runs + 12 lines + 9 arrowheads + 59 texts =
  **98 elements**, each once (`inventory.md`).

### Rule 1 — every region viewed and described

`final.png` (1780 × 1645) and all nine 3×3 tiles
(`regions-final/r11..r33.png`, each 593 × 548) plus two focused crops were
viewed:

- **r11 top-left** — blank upper-left; Learner box right half with
  `Learner` / `[Person]` / `Undergraduate student taking` /
  `database practice`; dashed boundary top-left corner and
  `DBCAS System [Software System]`; the Learner→Web Application line leaves
  the box at the tile's bottom-right.
- **r12 top-middle** — Administrator box (4 readable lines), both person
  flow labels (`Takes practice sessions, views competency profile`;
  `Manages CLOs, bank, rubrics; reviews analytics`), the boundary top border,
  the Web Application box with its 4 evenly spaced lines, and the start of
  `Delivers to user's`.
- **r13 top-right** — empty right margin; boundary top border and the top of
  the right dashed border only.
- **r21 middle-left** — left dashed border running down; left slivers of the
  SPA and API boxes; otherwise blank.
- **r22 middle-middle** — full Single Page Application box (5 lines,
  including the two-line container tag), `Makes API calls` /
  `[JSON/HTTPS + JWT]`, the 4-line API Application box, the right boundary
  border, the start of the Sanitized label, and the two new vertical edge
  lanes at the far right.
- **r23 middle-right** — right margin; tail of `Sanitized prompts /`; LLM
  Provider API top-left corner; boundary right border; no clipping.
- **r31 bottom-left** — Database cylinder with `Database` /
  `[Container: PostgreSQL 17]` / two body lines / `(41 tables)`, the
  API→Database arrowhead, boundary bottom-left corner and bottom border.
- **r32 bottom-middle** — SQL Execution Sandbox cylinder (4 lines), left part
  of the LLM box, `OAuth sign-in [HTTPS]` above its bus, the OAuth box's left
  half, and the boundary bottom/right corner.
- **r33 bottom-right** — right part of the LLM box,
  `Password-reset email [SMTP]` above its bus, both new external boxes with
  all four lines, and the two arrowheads landing on their top borders.
- **r_extra_external** (`1020,1180`–`1780,1645`) — LLM bottom, both labelled
  buses, both new boxes; labels sit 4 px above their own line and never touch
  a glyph or a border.
- **r_extra_flow** (`40,190`–`900,620`) — boundary title, both person-flow
  labels and the Web Application box: the even line spacing and 14 px
  padding are visible, with no text touching a border.

### Honest remaining differences

1. Box heights grow downwards (table above); dependent flow-line sources move
   with the new bottom edges. Nothing else moved.
2. Arial glyph metrics differ from the original's wider font; box text is
   re-centred on the original ink-left anchors and may be a few px narrower.
3. The two new edges cross the existing API→LLM diagonal and the boundary
   right border (external connection) — line/line and line/border crossings
   only; no box or text is crossed.
4. The new external boxes sit in the added right/bottom area; the canvas is
   336 px wider (1444→1780) and 227 px taller (1418→1645).
5. Dash phase and glyph AA fringes remain as documented for Stage A/B.
6. draw.io CLI is unavailable on this machine; the `.drawio` is hand-authored
   mxGraph with the same orthogonal waypoints.

### Files changed

- `docs/diagrams/rebuild/container/`: `container.svg`, `container.png`,
  `container.drawio`, `container-broken.svg`, `spec.json`, `trace.json`,
  `text-content.json`, `font-plan.json`, `letter-spacing.json`,
  `inventory.md`.
- `docs/qa/rebuild-preview/container/`: `final.png`,
  `side-by-side-final.png`, `overlay-final.png`, `diff.png`,
  `regions-final/` (9 tiles + 2 focused crops), `checker-pass-fix.txt`,
  `checker-broken-fix.txt`, `checker-delta-fix.txt`, this report.
- Scripts (new, F2-only): `scripts/build_container_fix_f2.py`,
  `scripts/f2_layout_common.py`, `scripts/calibrate_letter_spacing_f2.py`,
  `scripts/check_container_fix_delta_f2.py`,
  `scripts/make_f2_previews_f2.py`.

**Fit check:** yes — both new external boxes fit entirely in the enlarged
canvas: their top edge is y=1480, i.e. 62 px below the old canvas height
(1418), and the Email box extends to x=1754 (old width 1444), so they use
only the added bottom/right area. No existing node was moved or resized
horizontally to make room; the only existing geometry changes are the
owner-requested downward box growth and the dependent line sources.

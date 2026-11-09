# Container Diagram — Stage A clone report (Round 1 REDO, figure 3)

**Status: Stage A (clone only) complete — no content delta applied.**
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

# Module View — Stage A clone report (figure 5) + Stage B content delta

**Status: Stage A (clone only) GREEN. Stage B content delta applied below.**
Figure: `ArchitectureDesign_ver1.1_image6.png` (3300 × 2050) →
`docs/diagrams/rebuild/module/`.

## Pipeline (Stage A)

1. `scripts/trace_figure_w2a.py` (copy of `trace_figure.py`, white-rect
   extension; the shared tracer was not edited) — pixel measurement of the
   original → `trace.json`:
   - **30 shapes**: 6 functional-module panels (`#F4F9FD`, blue border,
     r≈16), 3 top bars (`#E5F3FF`, r≈14), 3 shared-dependency cards
     (green `#E4F5E9`, lavender `#EFEAFF`, peach `#FFF0E9`), and the
     **18 white sub-boxes** (`#FFFFFF`, stroke `#8B9DAD`, ~3 px) found by
     run-based rectangle detection (vertical stroke pair + top/bottom
     bands, validated on all four edges and the white interior perimeter);
   - **14 lines / arrowheads**: 2 pipeline arrows + 12 sub-box arrows,
     measured from their own `#536577` shaft+triangle pixels (thin shaft,
     solid head, measured head length/half-width);
   - **60 text bands** with ink colours (`#173D65` body, `#536577` caption).
   - `trace_markers.png` — every detected element drawn over a copy of the
     original (viewed; all 30 boxes, 14 arrows, 60 bands marked once).
2. `text-content.json` — all 60 strings read from ≥2× crops (top bars at
   2×, every sub-box and dependency card viewed, caption read verbatim).
   `free_ids`/`box_ids` keep string↔bbox mapping stable. The original
   wraps the 3 top bars and 13 sub-box labels at line breaks; every visual
   line is its own label (concatenating them with a space gives the exact
   delta string).
3. `text-fixes.json` — **no fixes needed**: all 60 labels were recovered
   as separate bands, so no splits, replacements or nudges. The rule-8
   checker found 0 text/text overlaps and 0 text/segment crossings.
4. `scripts/make_font_plan_w2a.py` — width-driven Arial calibration with
   per-id bold list (`bold_ids`; panel titles 51 px, top bars 39–45 px,
   dependency titles 48–50 px, sub-box text 34–35 px, caption 36 px,
   title 76 px, section headings 54 px). No size is below the original's
   measured ink height/width fit.
5. `scripts/build_figure_w2a.py` → `module.svg`, `module.drawio`
   (hand-authored mxGraph, orthogonal edges + waypoints; draw.io CLI not
   available on this machine), `spec.json`; PNG rendered with headless
   Chrome at exactly 3300 × 2050.
6. `scripts/calibrate_letter_spacing.py` → `letter-spacing.json`:
   residuals of the integer-size width fit corrected from the real Chrome
   renderer (60/60 labels; `calibrate.txt`).
7. `scripts/make_figure_inventory.py` → `inventory.md` — every element
   exactly once (**118 elements**: 30 shapes + 14 lines + 14 arrowheads +
   60 texts).

## Rule 8 — checker (deliberately broken first, then the real build)

- `make_broken_svg.py` piles all 60 labels on top of each other →
  `checker-broken.txt`: **FAIL, exit 1, 283 problems** (text/text +
  text/segment) — the gate can fail.
- Real build → `checker-pass.txt`: **PASS, exit 0**:
  60 labels exactly match the expected list (39 distinct strings:
  `Curriculum` ×3, `Controller` ×5, …), no text/text intersection, no
  text/foreign-segment intersection (0 own-line exemptions),
  **119 elements each exactly once** (30 rects + background rect +
  14 arrow polygons + 14 polylines + 60 texts; the inventory lists the
  118 measured elements).

## Rule 1 — region-by-region description (all 9 tiles + full render viewed)

- **r11 top-left** — white margin; the “Web UI · Learner and Administrator
  portals” bar (light-blue fill, blue border) with the pipeline arrow
  leaving its right edge; top of the Identity & Access panel with its
  bold title and the first text lines of Auth / Auth Service / Account.
- **r12 top-middle** — centred bold title “DBCAS MODULE VIEW”; the “API
  entry · FastAPI routing, JWT and validation” bar with incoming arrow
  from the left and outgoing arrow to the right; “FUNCTIONAL MODULES”
  heading; top of the Curriculum panel + bold title and three
  “Curriculum” line-1 labels.
- **r13 top-right** — incoming pipeline arrow; “Backend services ·
  Controllers → Services → Repositories” bar; Question Bank panel title;
  the tops of its three sub-boxes including the 3-line “Question /
  Candidate Controller”.
- **r21 middle-left** — bottom of the Identity sub-boxes and panel border;
  the Assessment panel with “Assessment Controller”, “Session + Adaptive
  Service” (3 lines) and “Assessment / Selection Repository” (3 lines),
  both internal arrows visible; panel bottom border.
- **r22 middle-middle** — bottom of the Curriculum sub-boxes; Grading
  panel title and its three boxes (“Attempt Controller”, “Grading
  Service”, “Attempt Repository”) with two arrows; panel bottom border.
- **r23 middle-right** — bottom of the Question Bank boxes (“Candidate
  Controller”, “Bank Service”, “Repository”); Competency panel with
  “Analytics Controller”, “Competency + Gap Service”, “Competency
  Repository” and two arrows.
- **r31 bottom-left** — bottom border of the Assessment panel; the green
  PostgreSQL 17 card with bold title and “Application data, evidence and
  LLMCache”; beginning of the grey footnote.
- **r32 bottom-middle** — “SHARED DEPENDENCIES” heading; the lavender LLM
  Gateway card (title + “Sanitized requests; provider-agnostic assistive
  calls”); middle of the footnote.
- **r33 bottom-right** — the peach SQL Sandbox card (“Isolated PostgreSQL;
  read-only, time and memory limits”); end of the footnote “…assessment
  workflow requires them.”

## Proof images (`docs/qa/rebuild-preview/module/`)

- `original.png`, `clone.png` — same canvas/origin, both 3300 × 2050
- `side-by-side.png` — original | clone at 1:1
- `overlay.png` / `diff.png` — black = ink in both, **red = original
  only**, **blue = clone only**
- `regions/r11..r33.png` — 3×3 tiles of the clone (all viewed above)
- `checker-broken.txt` (FAIL 283, exit 1), `checker-pass.txt` (PASS, exit 0)
- `calibrate.txt`, `trace-log*.txt`, `font-plan-log.txt`

## Honest differences (overlay, viewed)

1. **Glyph metrics**: Arial-as-rendered-by-Chrome vs the original's font —
   right edges ±1–4 px on most labels; top-left anchors within 0–1 px.
2. **Card borders**: clone draws one uniform 4 px stroke; the original's
   painted border is ~3 px + 1 px AA. Overlay shows a 1 px red/blue fringe
   on many card edges.
3. **Service-box bboxes**: several white sub-boxes land 1–2 px off the
   original outline (centreline vs outer-edge measurement); text inside is
   matched, and the internal spacing is unchanged.
4. **Corner radii**: panels r=16, top bars r=14, white sub-boxes r=7 from
   the measured arcs; corners show ≤2 px red/blue fringes.
5. **Arrowheads**: measured solid triangles redrawn as filled polygons at
   measured length/half-width; tip position ≤1 px.
6. **Fills**: medians sampled from pixels (`#F4F9FD`, `#E5F3FF`, `#E4F5E9`,
   `#EFEAFF`, `#FFF0E9`); AA boundaries differ by ≤2/255.
7. **PostgreSQL 17**: 1–2 px baseline/height fringe in the overlay (bbox
   includes the descender); the other two dependency titles match.
8. No legend in this figure; none added.

## Deliverables

`docs/diagrams/rebuild/module/`: `module.svg`, `module.drawio`,
`module.png`, `module-broken.svg`, `spec.json`, `trace.json`,
`text-content.json`, `text-fixes.json`, `font-plan.json`,
`letter-spacing.json`, `inventory.md`, `trace_markers.png`.

---

## Stage B — content delta (2026-11-09)

Input: `docs/qa/content-delta-verified.md` §4 (W9) + owner instruction.
Applied by `scripts/build_stage_b_w2a.py` from `delta-stage-b.json`
(same canvas, same shapes/lines/arrows, no auto-layout). **12 Stage A
text elements became 9 Stage B labels; 48 untouched labels are
byte-identical to the Stage A spec; canvas + all 30 shapes + 14
lines/arrowheads + 0 sticks are identical (checked in JSON).**

Exact final labels now on the figure:

- Card title `Practice`; boxes `Practice Controller` → `Practice Service`
  → `Session / Plan Repository` (the 3-line original blocks are replaced
  by one centred line and by the same 2-line grid used by the other
  cards, at the same 34 px size).
- `Grading Controller`; `Grading Service`; `Attempt / Evidence
  Repository` (line 1 is `Attempt / Evidence`, fitted inside the same
  card with -1.41 px tracking at the unchanged 34 px font size — no
  font shrink, no border touch).
- `Application data, evidence and LLM cache` (LLMCache → LLM cache).
- Footnote `Repositories persist application records. Services call the
  LLM Gateway or SQL Sandbox only when the workflow requires them.`
  (the word “assessment” removed).
- Everything else (3 top bars, Identity & Access, Curriculum, Question
  Bank, Competency, the other dependency text, headings, title) is
  unchanged and still carries the exact delta KEEP strings (the top bars
  keep the original's 2-line wrap; concatenating each pair with a space
  gives the exact label).

Rule 8 (Stage B): **PASS, exit 0**, 57 labels exactly match the Stage B
expected list, no text/text or text/foreign-segment intersection, 116
elements each exactly once (`checker-stage-b.txt`). Deliberately broken
copy (`module-stage-b-broken.svg`, 57 piled labels) → **FAIL, exit 1,
268 problems** (`checker-stage-b-broken.txt`).

Proof: `final.png` (3300 × 2050), `side-by-side.png`, `overlay.png`,
`diff.png` (red = Stage A/original only, blue = Stage B only — all
changed labels show as red old text + blue new text, everything else
black), `regions/` re-viewed (r21 Practice card, r22 Grading card,
r31/r32 dependency cards). Stage A evidence kept as `clone-stage-a.png`,
`side-by-side-stage-a.png`, `overlay-stage-a.png`,
`spec-stage-a.json`, `text-content-stage-a.json`,
`module-stage-a.png`, `checker-pass.txt`. `inventory-stage-b.md` lists
the 115 Stage B elements exactly once.


# Use Case Diagram — Stage A clone + Stage B content delta

**Status: Stage A PASS, Stage B PASS. No `.docx` touched; no commit from W1.**
Figure: `ArchitectureDesign_ver1.1_image2.png` (3000 × 3300), caption
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
cases kept.**

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

## Deliverables

`docs/diagrams/rebuild/use-case/`: `use-case.svg`, `use-case.drawio`,
`use-case.png` (3000 × 3300), `use-case-broken.svg`, `use-case-stage-a.svg`,
`spec.json`, `spec-stage-a.json`, `trace.json`, `trace-stage-a.json`,
`text-content.json`, `text-content-stage-a.json`, `text-fixes.json`,
`font-plan.json`, `font-plan-stage-a.json`, `letter-spacing.json`,
`letter-spacing-stage-a.json`, `inventory.md`, `inventory-stage-a.md`,
`trace_markers.png`.

`docs/qa/rebuild-preview/use-case/`: `original.png`, `clone.png`,
`side-by-side.png`, `overlay.png`, `regions/` (Stage A);
`final.png`, `side-by-side-final.png`, `overlay-final.png`, `diff.png`,
`regions-final/` (Stage B); `checker-pass-stage-a.txt`,
`checker-pass-stage-b.txt`, `checker-broken.txt` (Stage A),
`checker-broken-stage-b.txt`, `checker-stage-b-delta.txt`.

# Pipeline (Proposal Figure 4) — Stage A clone + Stage B content delta

Figure: `docs/qa/diagram-originals/ProposalDocument_ver1.1_image5.png`
(1342 × 762) → `docs/diagrams/rebuild/pipeline/`.
Stage A is the measured clone; Stage B applies only section 6 of
`docs/qa/content-delta-verified.md`. **Nothing was auto-laid-out**: every
box, arrow, dash run and text band in Stage A comes from pixels.

## Stage A — clone only

### Pipeline

1. `scripts/trace_figure_w2b.py` (copy of `trace_figure.py`, only the four
   pipeline-specific detector fixes: short arrows are line-like, text on a
   dashed row is not discarded, dash rows must have `abs(off-on) <= 2`, short
   Hough arms) → `trace-stage-a.json`. It measured 9 shapes (8 rounded boxes
   + stepped dashed boundary), 35 text bands, 6 dash runs and the horizontal
   feedback elbow, but the four short inter-box arrows are fused to the box
   border strokes and were not separable.
2. `scripts/supplement_pipeline_w2b.py` completes the measured trace:
   every arrow endpoint was read from row/column pixel runs
   (`BROKEN`-checked crops in `inspect/`), the eight box bboxes are drawn on
   the measured stroke centreline with radius 9, and the stepped dashed
   boundary is represented by its five measured runs (the PNG's top border
   really stops at x=407 and the right border starts at y=298 — it is not a
   full rectangle).
3. `text-content.json` — all 35 strings transcribed from 2×/4× crops
   (every box title, every body line, subtitle, footer, footnote viewed).
   `text-fixes.json` is empty: no merged line pairs and no inherited
   overlaps (0 nudges needed).
4. `make_font_plan.py` + `calibrate_letter_spacing.py` — title 31 bold,
   box titles 21–22 bold, body 16–17 regular, footer 20 bold; every
   rendered width matches its measured band (`letter-spacing-stage-a.json`).
5. `scripts/build_figure_w2b.py` → `pipeline-stage-a.svg`,
   `pipeline-stage-a.drawio`, `spec-stage-a.json`; PNG rendered by headless
   Chrome at exactly 1342 × 762.
6. `make_figure_inventory.py` → `inventory-stage-a.md`: **66 elements**
   (9 shapes + 6 dash runs + 8 lines + 8 arrowheads + 35 texts), each once.
7. Rule-8: `make_broken_svg.py` piles all 35 labels →
   `checker-broken.txt` **FAIL exit 1, 165 problems**; real build →
   `checker-pass.txt` **PASS exit 0** — 35/35 expected labels, 0 text/text,
   0 text/segment, 264 geometric elements each exactly once.

### Stage A regions actually viewed

- **r11 top-left** — title/subtitle left half; dashed top border ending at
  the entry arrow (x≈407); Opening box with title + both body lines; the
  boundary's left border continuous down.
- **r12 top-middle** — title/subtitle middle; dashed boundary rows; Evidence
  box with “Record result / update concept estimates”; Grade box right edge
  and its arrow; Adaptive box left edge.
- **r13 top-right** — title/subtitle right end; Adaptive + Next item boxes;
  the short Adaptive→Next arrow; boundary turning down at the right.
- **r21 middle-left** — left dashed border; bottoms of Opening/Grade boxes;
  Candidate preparation box top with its title and first body line.
- **r22 middle-middle** — the feedback elbow leaving Validated item bank
  (x≈670) at y≈384, running right to x≈933 and up into Adaptive selection;
  Validated item bank top/body.
- **r23 middle-right** — Next item→Complete assessment vertical arrow; the
  right dashed border and the short y≈294 connector back to the flow line.
- **r31 bottom-left** — Candidate preparation body/box bottom; bottom
  dashed border; “Target mix…” and footnote starts.
- **r32 bottom-middle** — Validated item bank bottom; “Repeat after each
  answer until cap or timer” sitting on the dashed bottom border with the
  original white gap (clone cuts the dashes there); footer text.
- **r33 bottom-right** — Complete assessment body/box bottom; right/bottom
  dashed corner; footer and footnote ends.

### Stage A honest differences (viewed on `overlay.png`)

1. Text right edges ±2–5 px (Arial as rendered by Chrome vs the original's
   font); left/top anchors match 0–1 px.
2. Dashes are emitted on the measured uniform on/off grid; the PNG's dash
   phase varies ±1 px, so long borders alternate red/blue after the first
   few dashes.
3. Box borders are drawn on the measured stroke centreline (2 px); the PNG
   has 2 px anti-aliased strokes → 1 px fringes.
4. Arrowheads are the measured triangle geometry (15 × 15); tips touch the
   target border exactly, AA edges differ by ≤1 px.
5. The entry arrow starts on the dashed border (the PNG has only a short
   tick + head), reproduced as measured.
6. Footer label sits on the dashed bottom border as in the PNG; the clone
   opens the dash run around it (the PNG also has a white gap there).

## Stage B — verified content delta (section 6)

**Status: complete.** Same canvas (1342 × 762), same 8 boxes, same arrows,
same dashed stepped boundary; only the text layer plus the feedback route
changed.

- Title → `Evidence-based Competency & Gap Evaluation Pipeline`; subtitle →
  `Complete practice plan frozen before question one • every served item
  comes from the plan`.
- Flow (W11 order) **Practice setup → Plan assembly & freeze → Serve
  planned item → Grade each answer → Record evidence → Complete session**;
  bottom row keeps `Candidate preparation` and `Validated item bank`.
- Exact section-6 body strings on the other 7 boxes; the Plan assembly &
  freeze body uses the corrected selector wording from
  `doc-discrepancies-v3` items 2/29: `Exact count · selected concepts
  spread as count allows · no repeated version families · SQL bank-only ·
  AI MCQ/essay` (same 16 px body size, same 4 lines). `Opening`, the 3-MCQ
  text, the adaptive selection text, the 13 cap, the 10/2/1 target mix and
  the “repeat after each answer…” label are gone.
- Footer → `Session length 1–20 (default 5) · 30-minute expiry · SQL always
  from the validated bank; AI fallback shows one bank_mixed notice.`
  (one 20 px bold line).
- Feedback: Validated item bank now feeds **Plan assembly & freeze** with a
  dashed orthogonal elbow (bank fallback); the old elbow into the
  adaptive-selection box is gone. Forward arrows are unchanged solid.
- Long new body lines are wrapped at spaces at the **same Stage A font
  sizes** (never smaller); titles stay 21–22 bold, body 16 regular.
  The wider “Serve the next item…” line made the bottom dash gap wider
  (measured/derived from its rendered bbox), exactly as the original gap
  mechanism works.
- `make_figure_inventory.py` → `inventory.md`: **71 elements** (9 + 6 + 8 +
  8 + 40), each once.
- Rule-8: `pipeline-broken.svg` → `checker-stage-b-broken.txt` **FAIL exit
  1, 205 problems**; real build → `checker-stage-b.txt` **PASS exit 0** —
  **40/40 labels** (title + 4 free + 35 box), 0 text/text, 0
  text/segment, **222 elements each exactly once**.

### Stage B regions viewed (`regions-final/`)

- **r11** — new title left, subtitle start; boundary top ending at the entry
  arrow; Practice setup (5 wrapped body lines, last “or AI” inside the
  box); Plan assembly & freeze title 2 lines.
- **r12** — title/subtitle middle; Plan assembly body (4 lines, corrected
  “selected concepts spread as count allows” wording), Serve
  planned item (3 lines), Grade each answer title/body.
- **r13** — title end; Grade each answer body; Record evidence title/body.
- **r21** — left border; bottoms of Practice setup/Plan assembly; dashed
  elbow vertical at x≈407; Candidate preparation title/body.
- **r22** — dashed elbow horizontal y≈384 from the bank to x≈407; Validated
  item bank title/body.
- **r23** — Record evidence→Complete session vertical arrow; right boundary
  and y≈294 connector.
- **r31** — Candidate preparation bottom; bottom dashed border; start of
  the wide “Serve the next item…” label; session-length footer; footnote.
- **r32** — Validated item bank bottom; middle of the repeat label with the
  dash gap; footer middle.
- **r33** — Complete session body (4 lines, “What to study next” quoted);
  dash/footer/footnote ends.

### Stage B honest differences / open points

1. Content delta wording is implemented verbatim; the implementation-only
   entity names in parentheses (`attempt`, `evaluation_record`) are not
   drawn because they are code references, not box labels.
2. The delta's “box 4 Grade each answer” + W11 order is implemented as
   Practice setup → Plan assembly → Serve → **Grade** → Record evidence;
   the physical boxes keep their Stage A positions.
3. The bank→plan feed is drawn dashed (“dashed fallback/feedback line” in
   the KEEP list); the Stage A elbow was solid. Orthogonal route, same
   arrowhead geometry.
4. “bank shortage is a hard stop” has no exact label in section 6; only the
   bank_mixed notice is drawn. Flagged for the main agent, not invented.
5. Wrapping changes line counts inside boxes; fonts/sizes are Stage A sizes
   or larger, spacing only. No boxes, arrows or boundary segments moved.
6. Same Arial/AA/dash-phase differences as Stage A remain.

## Proof files (`docs/qa/rebuild-preview/pipeline/`)

`original.png`, Stage A `clone.png` / `side-by-side.png` / `overlay.png` /
`diff.png` / `regions/`; Stage B `final.png` / `side-by-side-final.png` /
`overlay-final.png` / `diff-final.png` / `regions-final/`;
`checker-broken.txt` (165 FAIL), `checker-pass.txt` (Stage A PASS),
`checker-stage-b-broken.txt` (200 FAIL), `checker-stage-b.txt` (Stage B
PASS), `calibrate.txt`, `calibrate-stage-b.txt`, `font-plan-run*.txt`.

## Deliverables

`docs/diagrams/rebuild/pipeline/`: `pipeline.svg`, `pipeline.drawio`,
`pipeline.png`, `pipeline-broken.svg` (Stage B final); Stage A copies
`pipeline-stage-a.svg/.drawio/.png`, `pipeline-stage-a-broken.svg`,
`trace.json`, `trace-stage-a.json`, `text-content.json`,
`text-content-stage-a.json`, `text-fixes.json`, `font-plan.json`,
`font-plan-stage-a.json`, `letter-spacing.json`,
`letter-spacing-stage-a.json`, `inventory.md`, `inventory-stage-a.md`,
`spec.json`, `spec-stage-a.json`, `trace_markers.png`.

**Blockers:** draw.io CLI is not installed on this machine, so `.drawio` is
hand-authored mxGraph (orthogonal waypoints, dashed boundary/bank edge);
no `.docx` touched. The Stage B interpretation points above need the main
agent's review.

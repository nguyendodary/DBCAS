# Logical System Architecture — Stage A clone report (figure 6) + Stage B content delta

**Status: Stage A (clone only) GREEN. Stage B content delta applied below.**
Figure: `ProposalDocument_ver1.1_image4.png` (3200 × 3160) →
`docs/diagrams/rebuild/logical/`.

## Pipeline (Stage A)

1. `scripts/trace_figure_w2a.py` (copy of `trace_figure.py` + white-rect /
   connector / actor extension; shared tracer untouched) — pixel
   measurement of the original → `trace.json`:
   - **19 white rectangles** found from their own stroke runs (one pair of
     vertical bands + top/bottom bands, validated on all four edges and
     the white interior perimeter): 4 tier frames (8 px `#222222` border),
     4 tier tabs, 2 presentation portals, 6 Tier-2 service boxes,
     PostgreSQL's inner box, 2 sandbox/LLM boxes. Box corner radii
     10–12 px measured from the flat-run inset.
   - Frame top borders carry a measured **gap under each tab** (the tab is
     painted over the frame line in the original); `gaps` are stored on the
     frame shape so the emitted SVG splits the top edge exactly there.
   - **10 connector lines / 6 arrowheads**: 2 plain HTTPS lines
     (Tier 1→2), 4 Tier 2→3 segments (2 with measured solid arrowheads at
     PostgreSQL), 4 Tier 3→4 segments (2 with arrowheads at the bottom
     boxes), plus the 2 horizontal actor arrows; each tip is extended to
     the target border's measured outer edge.
   - **2 actor sticks**: head circle from the enclosed white disc
     (r=20 px), vertical body between the measured neck and hip rows, two
     arm lines and two leg lines from the measured joint rows — no Hough
     scribble.
   - **37 text bands** (title, subtitle, 4 tab labels, 4 portal texts,
     2 actor labels, 2 HTTPS labels, 12 Tier-2 texts, 2 Tier-3 connector
     labels, PostgreSQL title + 2 subtitle lines, 2 Tier-4 connector
     labels, 4 sandbox/LLM texts) with ink `#111111`.
   - `trace_markers.png` — every detected element drawn over a copy of the
     original (viewed).
2. `text-content.json` — all 37 strings read from ≥2× crops; 10 free +
   27 box labels, per-id bold list (title, tab labels, box titles).
3. `text-fixes.json` — no fixes needed (0 text/text overlaps, 0
   text/segment crossings after the frame-gap cut).
4. `scripts/make_font_plan_w2a.py` — width-driven Arial calibration with
   per-id bold: title 78 px, subtitle 42 px, tab labels 45–46 px, box
   titles 46 px, body 34 px, actor labels 36 px. No size below the
   original's measured ink fit.
5. `scripts/build_figure_w2a.py` → `logical.svg`, `logical.drawio`
   (hand-authored mxGraph; draw.io CLI unavailable), `spec.json`; PNG with
   headless Chrome at exactly 3200 × 3160.
6. `scripts/calibrate_letter_spacing.py` → `letter-spacing.json`
   (37/37 labels from the real renderer; `calibrate.txt`).
7. `scripts/make_figure_inventory_w2a.py` → `inventory.md` — every
   element exactly once (**74 elements**: 19 shapes + 10 lines +
   6 arrowheads + 2 sticks + 37 texts; the copy fixes the shared
   counter's arrow/stick tally).

## Rule 8 — checker (deliberately broken first, then the real build)

- `make_broken_svg.py` piles all 37 labels → `checker-broken.txt`:
  **FAIL, exit 1, 191 problems** — the gate can fail.
- Real build → `checker-pass.txt`: **PASS, exit 0**:
  37 labels exactly match the expected list (36 distinct strings —
  “HTTPS / REST” appears twice), no text/text intersection, no
  text/foreign-segment intersection (0 own-line exemptions),
  **105 elements each exactly once** (48 shape elements, 37 texts).

## Rule 1 — region-by-region description (all 9 tiles + full render viewed)

- **r11 top-left** — start of the bold title and the upright subtitle;
  Tier-1 frame top-left corner and the start of the Tier-1 tab; the
  Learner stick (circle head, body, two arms, two legs), the right-pointing
  actor arrow into the Learner box, the “Learner” label; the left part of
  the Learner Assessment Portal; the left “HTTPS / REST” label; the
  Tier-2 frame corner and tab start.
- **r12 top-middle** — end of the title and subtitle; the Tier-1 tab
  label; the right half of the Learner box and the left half of the
  Administrator box with their titles/subtitles; both HTTPS labels; the
  Tier-2 tab label.
- **r13 top-right** — title/subtitle tails; Tier-1 tab end; the
  Administrator box with its subtitle; the left-pointing actor arrow from
  the box to the Administrator stick; “Administrator” label; frame corner;
  Tier-2 tab end.
- **r21 middle-left** — Auth & Role Management and Automated Grading
  Engine boxes (titles + subtitles); Tier-2 frame bottom; the left
  connector crossing to Tier 3; “SQL / SQLAlchemy ORM”; the arrow into
  PostgreSQL.
- **r22 middle-middle** — Request Validation and Adaptive Engine boxes;
  the Tier-3 tab label; tails of the Tier-3 connector labels; PostgreSQL
  title.
- **r23 middle-right** — Assessment Session Service and Competency & Gap
  Engine boxes; right frame border; connector and “Evidence & Cached LLM
  Writes”; arrow into PostgreSQL.
- **r31 bottom-left** — bottom of PostgreSQL's box; Tier-3 frame bottom;
  Tier-4 frame top + tab start; “SQL Exec & Output Match”; arrow into the
  Docker SQL Sandbox box.
- **r32 bottom-middle** — PostgreSQL subtitle lines 1–2; Tier-4 tab label;
  the two Tier-4 connector labels; tops of the Docker and LLM boxes.
- **r33 bottom-right** — PostgreSQL subtitle tail; Tier-4 tab end; right
  frame border; “Prompts & Structured JSON”; arrow into the LLM Provider
  API box; its title/subtitle.

## Proof images (`docs/qa/rebuild-preview/logical/`)

- `original.png`, `clone.png` — same canvas/origin, both 3200 × 3160
- `side-by-side.png` — original | clone at 1:1
- `overlay.png` / `diff.png` — black = ink in both, **red = original
  only**, **blue = clone only**
- `regions/r11..r33.png` — 3×3 tiles of the clone (all viewed above)
- `checker-broken.txt` (FAIL 191, exit 1), `checker-pass.txt` (PASS, exit 0)
- `calibrate.txt`, `trace-log*.txt`, `font-plan-log.txt`

## Honest differences (overlay, viewed)

1. **Subtitle style**: the original subtitle is italic; the clone is
   upright (the rule-8 text metrics support regular/bold only). Width and
   position are matched (42 px); overlay shows red/blue glyph-shape
   fringes on that one line.
2. **Glyph metrics**: Arial vs the original's font — right edges ±1–4 px on
   most labels; tab labels up to ±8 px at the ends.
3. **Borders**: every box/frame is one 8 px `#222222` stroke at the measured
   centreline; overlay shows ≤1 px red/blue fringes (AA).
4. **Tab/frame junction**: the frame top edge is intentionally split under
   the tab (as in the original, where the tab covers the line); the tab's
   own border is complete.
5. **Actor sticks**: head circle r=20 px (measured from the white disc),
   body/arms/legs on the measured joint rows (neck 568, shoulder 595,
   hip 656, feet 710); stroke 4 px vs the original's 4–5 px — ≤2 px fringes.
6. **Connector tips**: arrowheads are solid polygons at measured
   length/half-width, extended to the target border's outer edge; ≤1 px.
7. **Text sizes**: 34–78 px from the width fit; letter-spacing calibration
   removes the integer-size step (residual ≤1 px).
8. No legend in this figure; none added.

## Deliverables

`docs/diagrams/rebuild/logical/`: `logical.svg`, `logical.drawio`,
`logical.png`, `logical-broken.svg`, `spec.json`, `trace.json`,
`text-content.json`, `text-fixes.json`, `font-plan.json`,
`letter-spacing.json`, `inventory.md`, `trace_markers.png`.

---

## Stage B — content delta (2026-11-09)

Input: `docs/qa/content-delta-verified.md` §5 (W10) + owner instruction.
Applied by `scripts/build_stage_b_w2a.py` from `delta-stage-b.json`
(same canvas, same shapes/lines/sticks, no auto-layout). **8 Stage A
labels changed + 1 subtitle line re-split; the other 28 labels are
byte-identical; canvas + 19 shapes + 10 lines/6 arrows + 2 actor sticks
are identical (checked in JSON).**

Exact final labels now on the figure:

- `Learner Practice Portal`; subtitle `Practice setup · Competency
  charts · SQL editor` (Exam UI removed).
- `Administrator Management Portal` — subtitle `CLOs & Concepts (FR-02)
  · Question Bank (FR-04) · Analytics & review` (one line, 34 px, -0.52 px
  tracking so it stays inside the same box — no font shrink).
- `Practice Session Service` — `Plan assembly · Frozen delivery · 30-min
  session`.
- `Practice Plan Assembly` — `Bank + AI selection · Validate · Freeze
  (FR-15)` (replaces `Adaptive Engine`).
- Tier-3 subtitle (exact 41-table string, kept on 2 lines, 34 px):
  `41 tables: Users & Roles | CLOs & Concept Model | Question Bank &
  Rubrics | Practice Sessions & Frozen Plans | Attempts & Evidence |
  Grading/Release Audit | Cached LLM Responses — short-lived JWT +
  refresh-session table` (W4 items 7/29: short-lived access JWT +
  PostgreSQL refresh-session table; line 2 is 1724 px inside the 2102 px
  inner box — no smaller font, no tracking, no overlap).
- Unchanged: title/subtitle, 4 tier titles, both actor labels, the 4
  remaining Tier-2 boxes + subtitles, PostgreSQL title, SQL / SQLAlchemy
  ORM, Evidence & Cached LLM Writes, SQL Exec & Output Match, Prompts &
  Structured JSON, Docker SQL Sandbox + subtitle, LLM Provider API + subtitle.
- Removed as live concepts: `Adaptive Engine`, `Exam UI`, `Assessment
  Session Service`, `Learner Assessment Portal`; the 6-service-box and
  4-tier abstractions are unchanged, no box added or moved.

Rule 8 (Stage B): **PASS, exit 0**, 37 labels exactly match the Stage B
expected list, no text/text or text/foreign-segment intersection,
**105 elements each exactly once** (`checker-stage-b.txt`). Deliberately
broken copy (`logical-stage-b-broken.svg`, 37 piled labels) → **FAIL,
exit 1, 192 problems** (`checker-stage-b-broken.txt`).

Proof: `final.png` (3200 × 3160), `side-by-side.png`, `overlay.png`,
`diff.png` (red = Stage A/original only, blue = Stage B only — the
changed portal/service labels show red old text + blue new text,
everything else black), `regions/` re-viewed (r11–r13 portals, r21–r23
service boxes, r31/r32 PostgreSQL).

**Cross-document consistency fix (W4 items 7/29):** the Tier-3 subtitle
phrase `Cached LLM Responses — Stateless JWT` was changed to
`Cached LLM Responses — short-lived JWT + refresh-session table`
(short-lived access JWT + PostgreSQL refresh-session table). Only that
one Stage B label (`X029-L2`) changed; all other 36 labels and all
shapes/lines/sticks are byte-identical. Checker re-run: **PASS, exit 0
(37 labels / 105 elements)**; broken copy **FAIL, exit 1, 192
problems**; `final.png`, side-by-side, overlay, diff and the 9 region
tiles re-rendered at 3200 × 3160. The line is 1724 px at 34 px, inside
the PostgreSQL box's 2102 px inner width, on the existing second
subtitle line — no font shrink, no extra line, no overlap.
 Stage A evidence kept as
`clone-stage-a.png`, `side-by-side-stage-a.png`, `overlay-stage-a.png`,
`logical-stage-a.png`, `spec-stage-a.json`,
`text-content-stage-a.json`, `checker-pass.txt`.
`inventory-stage-b.md` lists the 74 Stage B elements exactly once.


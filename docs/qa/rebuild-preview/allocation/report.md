# Allocation Diagram — Stage A clone + Stage B content delta

**Owner-fix round F2 (2026-11-09): PASS — canvas now 1725 × 1600. See the
"F2 owner fix" section at the bottom; the Stage A/B sections are the
historical record.**

**Status: Stage A PASS (re-verified), Stage B PASS.**
Figure: `ArchitectureDesign_ver1.1_image7.png` (1331 × 1283),
Architecture Figure 6. This report was missing after the first Stage A pass;
it is added here with the viewed evidence and the Stage B delta.

## Stage A — clone only

### Pipeline

1. `scripts/trace_figure.py` (shared Stage A tracer) → `trace.json`:
   **9 shapes** (1 dashed deployment boundary + 3 rounded nodes + 3 database
   cylinders + 1 ellipse + 1 person box), **4 dash runs**, **8 lines**,
   **7 arrowheads**, **39 text bands** with ink colours.
2. `text-content.json` — all 39 strings read from 2× crops (every box, both
   flow-label lines, boundary label).
3. `text-fixes.json` — one merged-line split (Application Server title line),
   two replace/add bands (the boundary label’s bold + regular runs), and 11
   spacing-only nudges; none shrink or merge text. The original’s clipped
   label background tabs are retained as measured bands, not merged.
4. `make_font_plan.py` + `calibrate_letter_spacing.py` → Arial weights/sizes
   and per-label spacing measured from the real Chrome renderer.
5. `build_figure.py` → `allocation.svg`, `allocation.drawio`, `spec.json`,
   PNG at exactly 1331 × 1283.
6. `make_figure_inventory.py` → `inventory.md` (Stage A; the W1 corrected
   inventory is `inventory.md` after Stage B; Stage A copy is
   `inventory-stage-a.md`).

### Stage A element counts

- **9 shapes**: boundary, Person box, User's Device, Internet ellipse, Web
  Server, Application Server, Database cylinder, SQL Sandbox cylinder,
  LLM Provider API.
- **8 lines / 7 arrowheads**, **4 dash runs** (boundary, on≈12/off≈12).
- **39 text bands**, 39 distinct strings.
- All 8 deployment nodes kept; `Learner / Administrator` stays one combined
  Person box (original style).

### Rule 8 — checker

- Stage A build `checker-pass-stage-a.txt` (run on `allocation-stage-a.svg`):
  **PASS, exit 0**, 39 labels exactly match, **203 elements** each exactly
  once.
- Deliberately broken build `checker-broken-stage-a.txt`: **FAIL, exit 1,
  87 problems**.

### Rule 1 — viewed images

`original.png`, `clone.png`, `side-by-side.png`, `overlay.png` and all nine
`regions/` tiles were viewed. Region descriptions:

- **r11 top-left** — blank margin; only the right edge of the Person box at
  the top-right of the tile.
- **r12 top-middle** — full `Learner / Administrator [Person]` box, `Uses`
  arrow, User's Device box with browser line, `HTTPS` arrow, Internet ellipse
  top.
- **r13 top-right** — blank (the diagram is centred/narrow).
- **r21 middle-left** — deployment boundary top-left corner and the
  `Docker-capable Host` / `[Deployment Node: …]` label; the top dashed border
  runs behind the label.
- **r22 middle-middle** — Internet bottom, `HTTPS` crossing the boundary,
  Web Server box (`Serves static content and the React + Vite single-page
  application`), `JSON / HTTPS (REST API calls)` label, Application Server top.
- **r23 middle-right** — blank margin.
- **r31 bottom-left** — Database cylinder (title, PostgreSQL tag, two body
  lines); dashed boundary bottom-left corner.
- **r32 bottom-middle** — Application Server bottom, `DB requests
  (SQL / SQLAlchemy)` and `Sandboxed SQL execution (read-only transaction)`
  labels, SQL Sandbox cylinder with four lines; dashed bottom border.
- **r33 bottom-right** — `Sanitized prompts / structured JSON (HTTPS)` label,
  LLM Provider API box; boundary right edge.

**Acceptability:** yes — an acceptable near-identical clone. Same canvas,
same node positions, same text bands, no duplicated elements; the overlay is
black on all geometry with red/blue glyph-metric fringes.

### Honest Stage A differences

1. **Glyph metrics** — Arial vs the original font; 1–4 px red/blue fringes on
   most labels, larger on the `Docker-capable Host` line because the bold and
   regular fragments have different metric widths.
2. **Text-frame artefacts revealed/cleaned** — the original’s Application
   Server tag has a white text-background tab after `3.13]` and the body line
   is partly overlapped by the tag frame. The clone draws the full, clean line;
   the white tab is not reproduced.
3. **Boundary label band** — the original `Docker-capable Host` /
   `[Deployment Node: …]` text sits on the dashed top border with a white
   background tab; the clone keeps the measured bands and the dashed border
   phase, so the line is interrupted in the same place.
4. **Dash phase** — uniform on/off grid from the measured span; original
   dashes vary ±1 px, giving alternating red/blue fringes after the first few.
5. **Borders** — original 2 px AA vs clone crisp 2 px; cylinder lid/body
   outlines follow the measured silhouettes.

## Stage B — verified content delta

Applied `docs/qa/content-delta-verified.md` §3. Only three labels change; no
node moved and no node was added.

| Band | Stage A | Stage B |
| --- | --- | --- |
| X020 | `Business logic, JWT / RBAC, grading,` | `Business logic: JWT / RBAC, grading,` |
| X021 | `adaptive selection, competency engine` | `practice plan assembly, competency engine` |
| X038 | `learner role, 256 MB, 3 s timeout` | `learner role; 256 MB, 3 s timeout` |

- **39 text bands** (unchanged count, all 39 distinct).
- Stage B checker `checker-pass-stage-b.txt`: **PASS, exit 0, 39 labels,
  203 elements**; broken build `checker-broken-stage-b.txt`: **FAIL, exit 1,
  87 problems**.
- Stage A → B delta `checker-stage-b-delta.txt`: **PASS** — canvas, 9 shapes,
  4 dash runs and 8 lines identical; only X020/X021/X038 differ; every other
  text entry byte-identical. `practice plan assembly` keeps the Stage A font
  size (18 px) and its wider band stays inside the Application Server box.
- Stage B images: `final.png`, `side-by-side-final.png`, `overlay-final.png`
  (red = original only, blue = clone only), `diff.png`, `regions-final/`.
  All 9 Stage B tiles viewed; the only visible changes are the three labels.
- **Pending owner decision — Email/OAuth:** not added. The 8-node layout has
  no free block without moving existing nodes; the verified delta allows
  keeping the production-view 8 nodes. No Mailpit box was invented.

## Deliverables

`docs/diagrams/rebuild/allocation/`: `allocation.svg`, `allocation.drawio`,
`allocation.png` (1331 × 1283), `allocation-broken.svg`,
`allocation-stage-a.svg`, `spec.json`, `spec-stage-a.json`, `trace.json`,
`trace-stage-a.json`, `text-content.json`, `text-content-stage-a.json`,
`text-fixes.json`, `font-plan.json`, `font-plan-stage-a.json`,
`letter-spacing.json`, `letter-spacing-stage-a.json`, `inventory.md`,
`inventory-stage-a.md`, `trace_markers.png`.

`docs/qa/rebuild-preview/allocation/`: `original.png`, `clone.png`,
`side-by-side.png`, `overlay.png`, `regions/` (Stage A);
`final.png`, `side-by-side-final.png`, `overlay-final.png`, `diff.png`,
`regions-final/` (Stage B); `checker-pass-stage-a.txt`,
`checker-pass-stage-b.txt`, `checker-broken-stage-a.txt`,
`checker-broken-stage-b.txt`, `checker-stage-b-delta.txt`.

---

## F2 owner fix (2026-11-09) — frame label, HTTPS routing, OAuth/Email

**Status: PASS.** Canvas **1725 × 1600** (was 1331 × 1283). Figure:
`docs/diagrams/rebuild/allocation/allocation.svg` / `.png` / `.drawio`.

### What changed (owner's three items)

**(a) Frame label restored to the measured original.** The original
`Docker-capable Host` cap height is 15 px (Arial bold 21 px), the bracket
cap is ~14 px (Arial regular 20 px), both sitting with their baseline at
y≈562 and the border at y=541. The old clone used 17 px bold / 20 px with
the text 7 px too high, so it touched the dashed border. Now:

- `Docker-capable Host` — 21 px bold, ink top y=547 (6 px below the border);
- `[Deployment Node: containerized` — 20 px regular, same baseline;
- `deployment, Docker Compose]` — 20 px regular, second line at ink top
  y=570 (5 px line gap, 27 px above the Web Server box).

The bracket is wrapped after `containerized` because the measured-size
single line is 596 px wide and covers the whole 807 px frame top; wrapping
is the only way to keep the original size and give the HTTPS line a clear
channel. The text is unchanged (the two runs concatenate with one space).

**(b) HTTPS line no longer through the title.** The old two segments
(`L07` + `L08`, split with a 30 px gap through the label band) were merged
into one continuous orthogonal edge
`(597,473) → (593,615)`, 2.5 px `#474747` — the measured original colour
and weight. It crosses the top border at x≈594 and passes **13 px to the
right of the wrapped label's first line** (which ends at x≈580); the
delta checker proves no frame-label bbox intersects the line. All other
nodes are untouched.

**(c) New external nodes and edges.** `OAuth Providers`
(900,1420)-(1291,1565) and `Email Service` (1308,1420)-(1699,1565):
391 × 145, radius 15, 2 px `#3F3494` border, `#6A5ACD` fill, white
23 px bold title + 18 px tag/body — the figure's own LLM Provider API
style (the Container uses its grey LLM style; the box construction and
type treatment are the same). Two labelled orthogonal edges leave the
Application Server right edge (791,890/910):

- `OAuth sign-in [HTTPS]` → OAuth Providers top (1095,1420), via the
  x=870 lane outside the boundary and the y=1380 bus;
- `Password-reset email [SMTP]` → Email Service top (1503,1420), via the
  x=880 lane and the y=1350 bus.

Both lanes run in the corridor between the boundary right edge (860) and
the LLM box (x=900); both buses run below the boundary (y≥1350 > 1229).
No route passes through a box; the only crossings are line/line with the
pre-existing Application Server→LLM edge and the dashed boundary border.

### Checker / proof evidence

- `checker-pass-fix.txt`: **PASS, exit 0** — 50 text bands (48 distinct
  strings; `[External Software System]` ×2), **0** text/text
  intersections, **0** text/foreign-segment intersections, 219 elements
  each exactly once. Expected list: 50 = 1 title + 15 flow labels +
  34 box texts.
- `checker-broken-fix.txt`: **FAIL, exit 1, 109 problems** on the
  deliberately piled-label SVG (50 labels).
- `checker-delta-fix.txt`: **PASS** — **all 9 original shapes are
  byte-identical**, 4 dash runs and lines L01–L06 identical; only X011
  (17→21 px bold), X010 split into X010+X040, and the 10 new labels differ;
  no font size decreased. The frame-label bboxes and the new labels are
  clear of their edges (checked).
- Elements: 11 shapes + 4 dash runs + 9 lines + 9 arrowheads + 50 texts =
  **83 elements**, each once (`inventory.md`).

### Rule 1 — every region viewed and described

`final.png` (1725 × 1600) and all nine 3×3 tiles
(`regions-final/r11..r33.png`, each 575 × 533) plus two focused crops were
viewed:

- **r11 top-left** — blank margin; right part of the Person box and the
  top of User's Device at the right edge; Internet top below.
- **r12 top-middle** — `Learner / Administrator [Person]` box,
  `Uses` arrow, User's Device (3 lines), `HTTPS`, Internet ellipse and
  the start of the second `HTTPS`; all text clear of borders.
- **r13 top-right** — empty right margin; no content.
- **r21 middle-left** — dashed boundary top-left corner and the restored
  frame label: bold `Docker-capable Host` + `[Deployment Node:
  containerized` on line 1, `deployment, Docker Compose]` on line 2;
  the boundary's top border runs above the text.
- **r22 middle-middle** — Internet bottom, `HTTPS` and the continuous
  line crossing the border clear of the label, Web Server (3 lines),
  `JSON / HTTPS (REST API calls)`, Application Server (4 lines),
  `Sanitized prompts / structured JSON (HTTPS)` and the boundary right
  border; the new edge lanes are visible at the far right.
- **r23 middle-right** — blank right margin; the two new vertical lanes
  at the bottom-left of the tile.
- **r31 bottom-left** — Database cylinder (title, PostgreSQL tag, two
  body lines), boundary bottom-left corner and bottom border; no text
  touches the cylinder.
- **r32 bottom-middle** — Sandbox cylinder, LLM Provider API left part,
  `OAuth sign-in [HTTPS]` above its bus, OAuth Providers box left half,
  boundary bottom/right corner.
- **r33 bottom-right** — LLM Provider API right part,
  `Password-reset email [SMTP]` above its bus, both new purple external
  boxes with all four lines and the two arrowheads on their top borders.
- **r_extra_external** (`850,1030`–`1725,1600`) — LLM bottom, both buses,
  both new boxes; labels sit 4 px above their own line, no glyph or
  border contact.
- **r_extra_frame** (`40,500`–`900,700`) — the restored frame label in
  full: title + wrapped bracket at original weight, the continuous HTTPS
  line 15 px to the right of line 1 and the arrow into Web Server.

### Honest remaining differences

1. The frame label is wrapped to two lines (one title + first bracket run
   on line 1, continuation on line 2). The single-line measured-size label
   covers the whole frame top and cannot coexist with the HTTPS line; this
   is the smallest layout change that satisfies (a) and (b) together.
2. The new external boxes use the Allocation LLM Provider API's purple
   style (so all three external nodes match); the Container equivalents use
   that figure's grey LLM style. Box construction/type sizes are identical.
3. The new edge lanes run just outside the boundary (x=870/880, 10/20 px
   from the border) and cross the existing Application Server→LLM diagonal
   (line/line) — no box or text is crossed.
4. Original dash phase, glyph AA fringes and the Arial-vs-original font
   metric differences remain as documented for Stage A/B.

### Files changed

- `docs/diagrams/rebuild/allocation/`: `allocation.svg`, `allocation.png`,
  `allocation.drawio`, `allocation-broken.svg`, `spec.json`, `trace.json`,
  `text-content.json`, `font-plan.json`, `letter-spacing.json`,
  `inventory.md`.
- `docs/qa/rebuild-preview/allocation/`: `final.png`,
  `side-by-side-final.png`, `overlay-final.png`, `diff.png`,
  `regions-final/` (9 tiles + 2 focused crops), `checker-pass-fix.txt`,
  `checker-broken-fix.txt`, `checker-delta-fix.txt`, this report.
- Scripts (new, F2-only): `scripts/build_allocation_fix_f2.py`,
  `scripts/f2_layout_common.py`, `scripts/calibrate_letter_spacing_f2.py`,
  `scripts/check_allocation_fix_delta_f2.py`,
  `scripts/make_f2_previews_f2.py`.

**Fit check:** yes — all nine original shapes are byte-identical in the
delta spec (no node moved), and both new nodes start at y=1420, i.e. below
the old canvas height (1283); the figure only grows right to 1725 and
bottom to 1600. Existing nodes were not moved to make room.

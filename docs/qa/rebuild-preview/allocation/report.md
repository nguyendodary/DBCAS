# Allocation Diagram — Stage A clone + Stage B content delta

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
3. `text-fixes.json` — one merged-line split and spacing-only nudges recorded
   by the Stage A pipeline; none shrink or merge text.
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

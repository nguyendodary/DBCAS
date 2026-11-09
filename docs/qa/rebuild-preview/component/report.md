# Component Diagram (Architecture Figure 4) — Stage A clone + Stage B delta

Figure: `docs/qa/diagram-originals/ArchitectureDesign_ver1.1_image5.png`
(2361 × 1423) → `docs/diagrams/rebuild/component/`.
Stage A is the pixel-measured clone; Stage B applies only section 7 of
`docs/qa/content-delta-verified.md`. No auto-layout was used.

## Stage A — clone only

### Pipeline

1. `scripts/trace_figure.py` → `trace-stage-a.json`: 26 boxes (21
   controllers/services/repositories + LLM Gateway, Database, Sandbox
   Runner, LLM Provider API, SQL Sandbox), 139 text bands, 24 measured
   flows and 23 arrows. The three dashed boundaries and two vertical dash
   sides were below the generic dash-cluster span; several flows were split
   at boundary crossings; SQL Sandbox was classified as a rounded rect.
2. `scripts/supplement_component_w2b.py` completes the trace from pixels:
   three dashed boundaries with measured bboxes and 12 measured dash runs
   (on 14 / off 15), 24 cleaned flow lines/arrowheads (endpoints from the
   tracer segments plus row/column scans), and the SQL Sandbox cylinder
   rebuilt from its fill silhouette (`cap_ry=9`).
3. `text-fixes.json` — 5 **splits** of merged line pairs (Attempt/Controller
   title, Candidate “reject AI question”/“candidates”, Grading “MCQ key
   check, SQL”/“result grading,”, Question Repository title
   “Repository”/“Question,”, and “MCQOption,”/“SQLTestDataset,”); 6
   **replaces** correcting the three bold+regular boundary captions whose
   bands had absorbed the dashed border/crossing lines (Controller, Service,
   Repository, `[Container: …]`); **63 spacing-only nudges** (60 from
   `resolve_text_spacing.py` + 3 manual: Attempt Repository stack up 4 px,
   SQL Sandbox title/container down 6 px to clear the lid arc). No text was
   shrunk or merged.
4. `scripts/make_font_plan_w2b.py` with per-id bold control (boundary names
   + all box titles bold; the detail lines “LLM Gateway” / “Sandbox Runner”
   stay regular). Sizes: controller/service titles 26–29 bold, bodies
   20–23, repository titles 27–29, bottoms 27–28; `letter-spacing-stage-a`
   calibrated against Chrome.
5. `scripts/build_figure_w2b.py` → `component-stage-a.svg`,
   `component-stage-a.drawio`, `spec-stage-a.json`; PNG rendered at exactly
   2361 × 1423.
6. `make_figure_inventory.py` → `inventory-stage-a.md`: **228 elements**
   (29 shapes + 12 dash runs + 24 lines + 24 arrowheads + 139 texts), each
   exactly once.
7. Rule-8: `component-broken.svg` → `checker-broken.txt` **FAIL exit 1,
   611 problems**; real build → `checker-pass.txt` **PASS exit 0** —
   **139/139 labels** (7 free + 132 box), 0 text/text, 0 text/segment,
   **719 geometric elements each exactly once**. Two extra line cuts on the
   SQL Sandbox lid/title were opened by the builder.

### Stage A regions viewed

- **r11 top-left** — Controller caption (bold + regular container text),
  Auth and Assessment Controller boxes with all six lines, both arrows
  leaving them, Service band caption below.
- **r12 top-middle** — Controller bottom dash row and Service top row;
  Curriculum, Question Bank and Analytics Controller boxes, all lines and
  their arrows; Service captions.
- **r13 top-right** — Attempt and Candidate Controller boxes, their arrows
  into Grading/Adaptive Engine, Controller boundary top-right corner.
- **r21 middle-left** — Auth Service and Assessment Session Service boxes
  with bodies; Repository caption; Account and Assessment Repository boxes;
  vertical flows crossing the Service/Repository bands.
- **r22 middle-middle** — Curriculum, Question Bank and Competency & Gap
  service boxes; the three repository boxes below; flows and boundary rows.
- **r23 middle-right** — Grading and Adaptive Engine service bodies;
  Attempt and Selection & Candidate repositories; right boundary and the
  three boundary rows.
- **r31 bottom-left** — LLM Gateway box and its arrow down to LLM Provider
  API; Repository fan-out arrow leaving Account Repository.
- **r32 bottom-middle** — Database cylinder with seven repo arrows entering
  the lid, the short “cache” arrow from LLM Gateway, Sandbox Runner edge,
  LLM Provider edge, SQL Sandbox lid.
- **r33 bottom-right** — Sandbox Runner body, arrow down to SQL Sandbox
  cylinder, SQL Sandbox title/container, right boundary corner.

### Stage A honest differences

1. 63 labels were moved 2–15 px (spacing only) so the rule-8 checker is
   clean; the largest chains are Grading/Adaptive bodies and
   Attempt/Selection repositories.
2. SQL Sandbox title/container moved +6 px down (it touched the lid arc in
   the PNG); Attempt Repository stack moved −4 px so “evidence)” stays
   inside its box.
3. Italic detail lines (“uses LLM Gateway”, “uses Sandbox Runner, LLM
   Gateway”, etc.) render regular: the builder/checker use upright Arial
   only.
4. Stage A width calibration chose regular 30 px for “Competency &”; the
   PNG is bold (Stage B renders it bold 28). All other titles are bold.
5. Dashes use the measured uniform 14/15 grid; PNG dash phase varies ±1 px
   → alternating red/blue fringes.
6. Cylinder outlines are sampled from the fill silhouette every 2 px; AA
   edges differ ≤1 px. Arrowheads are 15 × 15 measured triangles.
7. Text right edges ±2–5 px (Arial vs original font); all left/top anchors
   are within 0–1 px except the spacing nudges above.

## Stage B — verified 7/7/7 content delta (section 7)

**Status: complete.** Canvas, all 26 boxes, 3 dashed boundaries, 24 flows,
cream/dark colours and the bottom row are unchanged. Only labels changed.

- Controllers (7): Auth, **Practice**, Curriculum, Question Bank,
  Analytics, **Grading**, **Accounts** — exact section-7 body lines.
- Services (7): Auth, **Practice**, Curriculum, Question Bank,
  Competency & Gap, **Grading & Evaluation**, **Admin & Settings** — exact
  bodies.
- Repositories (7): Account, **Session & Plan**, Curriculum, Question,
  Competency, **Grading**, **Audit & Settings** — exact entity lists.
- Bottom: `LLM Gateway [Component: Python]` (“…LLM cache”), `Database
  [Container: PostgreSQL 17]` (“Stores all application data (41 tables)”),
  `Sandbox Runner [Component: Python, Docker]`, `LLM Provider API
  [External System]`, `SQL Sandbox [Container: Docker, PostgreSQL 17]`,
  `cache`.
- Removed as live labels: Assessment Controller, Assessment Session
  Service, Adaptive Engine Service, Assessment Repository, Attempt
  Repository, Selection & Candidate Repository (and the old Attempt/Grading
  controller names). No `Assessment*`/`Adaptive*`/`Selection*` title remains.
- Titles/body reflowed to 2–3 lines at the **same Stage A sizes** (never
  smaller); box geometry and every arrow/dash endpoint are byte-identical
  to Stage A.
- `inventory.md`: **201 elements** (29 shapes + 12 dash runs + 24 lines +
  24 arrowheads + 112 texts), each once.
- Rule-8: `component-broken.svg` → `checker-stage-b-broken.txt` **FAIL exit
  1, 546 problems**; real build → `checker-stage-b.txt` **PASS exit 0** —
  **112/112 labels** (7 free + 105 box; 85 distinct), 0 text/text, 0
  text/segment, **692 geometric elements each exactly once**.

### Stage B regions viewed (`regions-final/`)

- **r11** — Controller caption; Auth Controller (Register/login/logout,
  OAuth, password reset) and Practice Controller (Practice setup, start,
  serve, submit); arrows to Auth/Practice services.
- **r12** — Curriculum, Question Bank, Analytics controllers; bodies with
  prerequisites / candidates / cohort analytics; arrows down.
- **r13** — Grading and Accounts controllers; boundary corner; arrows to
  Grading & Evaluation and Admin & Settings services.
- **r21** — Auth/Practice service bodies; Repository caption; Account and
  Session & Plan repositories with their entity lists.
- **r22** — Curriculum/Question Bank/Competency & Gap services;
  Curriculum/Question/Competency repositories; all entity lines; two
  boundary rows.
- **r23** — Grading & Evaluation and Admin & Settings service bodies;
  Grading and Audit & Settings repositories; right boundary.
- **r31** — LLM Gateway body (“LLM cache”) and arrow to LLM Provider API.
- **r32** — Database cylinder with “(41 tables)”, seven fan-in arrows,
  cache arrow, neighbouring boxes.
- **r33** — Sandbox Runner → SQL Sandbox arrow; SQL Sandbox cylinder title
  and container line; boundary corner.

### Stage B honest differences / open points

1. “Accounts Controller” is used (the section-7 alternative
   “Accounts / Settings Controller” was not needed); settings endpoints are
   represented by Admin & Settings Service / Audit & Settings Repository.
2. Body lines are wrapped differently from the PNG because the new strings
   are shorter/longer, but fonts/sizes are Stage A or larger and the boxes
   are unchanged.
3. Inherited Stage A differences remain: SQL Sandbox +6 px title nudge,
   Attempt Repository −4 px stack, italic detail lines upright, dash phase,
   ±2–5 px text right edges.
4. No extra nodes were added; the delta has no Component ADD items.

## Proof files (`docs/qa/rebuild-preview/component/`)

`original.png`, Stage A `clone.png` / `side-by-side.png` / `overlay.png` /
`diff.png` / `regions/`; Stage B `final.png` / `side-by-side-final.png` /
`overlay-final.png` / `diff-final.png` / `regions-final/`;
`checker-broken.txt` (611 FAIL), `checker-pass.txt` (Stage A PASS),
`checker-stage-b-broken.txt` (546 FAIL), `checker-stage-b.txt` (Stage B
PASS), `calibrate.txt`, `calibrate-stage-b.txt`, `font-plan-run*.txt`,
`resolve-spacing-run1.txt`, `inspect/` crops.

## Deliverables

`docs/diagrams/rebuild/component/`: `component.svg`, `component.drawio`,
`component.png`, `component-broken.svg` (Stage B final);
`component-stage-a.svg/.drawio/.png`, `component-stage-a-broken.svg`,
`trace.json`, `trace-stage-a.json`, `text-content.json`,
`text-content-stage-a.json`, `text-fixes.json`, `font-plan.json`,
`font-plan-stage-a.json`, `letter-spacing.json`,
`letter-spacing-stage-a.json`, `inventory.md`, `inventory-stage-a.md`,
`spec.json`, `spec-stage-a.json`, `trace_markers.png`.

**Blockers:** draw.io CLI unavailable → hand-authored mxGraph; Stage B
reflow of long labels is spacing-only and should be reviewed. No `.docx`
touched. No secrets.

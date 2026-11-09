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

## F4 owner fix round (2026-11-09) — two-page split + Grading & Evaluation Service

The approved Stage B content is unchanged. The single 2361 x 1423 page is
re-laid out as **two horizontal pages, 08a (left columns) and 08b (right
columns)**, and the Grading & Evaluation Service box is enlarged/reflowed.
Pre-fix baseline: `spec-stage-b-prefix.json`, `final-prefix.png`. The old
single-page build files `component.svg/.drawio/.png` are retained unchanged
as that baseline; the F4 final is the `component-08a.*` + `component-08b.*`
pair and the preview `final-08a.png` / `final-08b.png`.

### Why the split (measured printed size)
The docx places this figure at **9.15 in** wide (`wp:extent` 8366760 EMU).
Pre-split: `pt = px / 2361 * 9.15 * 72`:

| px | pre-split pt | use |
| --- | --- | --- |
| 17 | **4.74** | `[Container: Docker, PostgreSQL 17]` |
| 20 | 5.58 | body text |
| 21 | 5.86 | repository lines |
| 22 | 6.14 | controller body |
| 23 | 6.40 | service body |
| 26-29 | 7.24-8.08 | titles |

Most body text was below 7 pt. Post-split, each page is **1400 x 980 px**
displayed at **9.15 x 6.41 in**, which fits the landscape text area
(9.52 x 6.69 in) with 0.28 in left for the caption:

| page | min px | pt = px/1400*9.15*72 |
| --- | --- | --- |
| 08a | 20 | **9.41** |
| 08b | 17 | **8.00** |

All text stays at its Stage B size; **nothing was shrunk**.

### Page layout
* **08a — left columns**: Controller/Service/Repository bands for Auth,
  Practice, Curriculum and Question Bank; bottom LLM Gateway, LLM Provider
  API and Database. 67 labels (7 free + 60 box; 50 distinct strings).
* **08b — right columns**: bands for Analytics/Competency & Gap, Grading,
  Accounts/Admin & Settings; bottom Sandbox Runner, SQL Sandbox and the
  **shared Database cylinder repeated** so the three right-hand repositories
  keep a visible sink. 54 labels (6 free + 48 box; 45 distinct strings).
  The caption/report states the Database is identical to 08a.
* Cards keep their exact width/height/style/text; only x/y translate. The
  three dashed bands are redrawn per page in the same 14/15 dash style.
* Connector semantics: **24/24 arrowheads preserved** (14 tips on 08a,
  10 on 08b); controller→service and service→repository arrows stay inside a
  column; 4 left repositories feed 08a's Database and 3 right repositories
  feed the repeated Database on 08b. The 2 extra polyline objects (25→27)
  are rule-8 cuts where a service→repository line crosses a band caption.

### Grading & Evaluation Service (S05) fix
Old: 262 x 167, **6** rendered lines (3 title + 3 body), title baselines
462/490/512, body 535/558/581, only 11 px top padding. New: **300 x 185**,
**5** lines — the two words "Evaluation" and "Service" are merged into one
line (same content), then the three body lines:

| line | content | size | baseline | ink bbox |
| --- | --- | --- | --- | --- |
| 1 | Grading & | 28 bold | 323 | 303-329 |
| 2 | Evaluation Service | 28 bold | 357 | 337-357 |
| 3 | MCQ key, SQL | 23 regular | 382 | 365-387 |
| 4 | sandbox, Prompt | 23 regular | 407 | 390-412 |
| 5 | Builder → Evaluator | 23 regular | 432 | 415-432 |

Box `[556,275,856,460]`: 28 px top/bottom padding, 25 px body baseline
grid, "Evaluation Service" 249 px ink in a 300 px box (25.5 px each side).
No line touches the border.

### Checkers (this round)
* `checker-08a.txt` — **PASS exit 0**, **67 labels**, **415 elements each
  exactly once**, 0 text/text, 0 text/segment.
* `checker-08a-broken.txt` — **FAIL exit 1, 343 problems**.
* `checker-08b.txt` — **PASS exit 0**, **54 labels**, **341 elements each
  exactly once**, 0 text/text, 0 text/segment.
* `checker-08b-broken.txt` — **FAIL exit 1, 286 problems**.
* `delta-split-f4.txt` (`scripts/check_f4_component_split.py`): **PASS** —
  26/26 card shapes kept with identical size/style (only the declared S05
  resize), 111/112 label ids kept (B047 merged into B040),
  24/24 arrowheads kept.
* Pixel proof: 08a prefix layout vs fixed layout = **0 different pixels**
  (pure re-layout); 08b differs only inside S05 (**27 012 px** on the final
  1400 x 980 canvases; see `overlay-final-08b.png`).
* The stock figure gate still sees `final.png` at 2361 x 1423; it is a
  contact sheet of 08a+08b at 0.84 scale, while the actual review pages are
  `final-08a.png` / `final-08b.png` at 1:1 (1400 x 980).

### F4 regions viewed — 08a (`regions-final/`, 3 x 3 tiles)
* **r11** — Controller caption; Auth Controller (2 title + 2 body lines);
  Practice Controller left edge; controller band top/bottom dash rows.
* **r12** — Practice and Curriculum controllers; both arrows crossing the
  two band boundaries into the Service row.
* **r13** — Question Bank Controller; band right edge and right dash column.
* **r21** — Auth Service; Repository caption; Account Repository; the
  service→repository arrow crossing both dashed rows.
* **r22** — Practice/Curriculum services and repositories; caption row
  visible between the arrows.
* **r23** — Question Bank Service and Question Repository; right band edge.
* **r31** — Account Repository bottom; LLM Gateway and LLM Provider API.
* **r32** — "cache" label above the Gateway→Database arrow; Database left
  half with the fan-in arrowheads.
* **r33** — Database right half, title/container/(41 tables), band corner.

### F4 regions viewed — 08b (`regions-final-08b/`, 3 x 3 tiles)
* **r11** — Controller caption; Analytics Controller; band top/left.
* **r12** — Grading Controller; both dashed rows; arrow into the Service row.
* **r13** — Accounts Controller; band right edge.
* **r21** — Competency & Gap Service; Repository caption; Competency
  Repository.
* **r22** — **Grading & Evaluation Service: five lines** (Grading & /
  Evaluation Service / MCQ key, SQL / sandbox, Prompt / Builder → Evaluator)
  with even padding; Grading Repository below; the rule-8 gap at the
  Repository caption is visible.
* **r23** — Admin & Settings Service; Audit & Settings Repository.
* **r31** — Sandbox Runner → SQL Sandbox arrow and the SQL Sandbox cylinder.
* **r32** — repeated Database left half with the three right-hand repository
  fan-in arrows.
* **r33** — repeated Database right half; band corner.

### Caption proposal
`docs/qa/rebuild-preview/component/caption-proposal.md`:
**Figure 4 (1/2). Component Diagram — controllers, services and repositories:
Auth, Practice, Curriculum and Question Bank.** and **Figure 4 (2/2).
Component Diagram — Analytics/Competency & Gap, Grading and
Accounts/Admin & Settings.** Each page 9.15 x 6.41 in. The 08b caption adds:
“Database repeated for connector context; identical to 4 (1/2).”

### Honest remaining differences
1. The two pages are a **re-layout**, not two crops: y positions are compacted
   so each page fits the 6.69 in landscape text height at 9.15 in width.
2. The shared Database cylinder is **repeated on 08b** (4 labels duplicated)
   to keep the three right-hand repository connectors visible; it is the same
   card and text, not a new component.
3. On 08b the Gateway→Database "cache" arrow is not present because the
   Gateway lives on 08a; the Database is the shared sink on both pages.
4. S05's title is 2 lines instead of 3 ("Evaluation" + "Service" merged into
   "Evaluation Service"); this is the 5-line reflow the owner asked for, and
   the words are unchanged.
5. Inherited Stage A/B differences remain: Arial vs the original font
   (right edges ±2–5 px), dash phase, AA fringes, and the SQL Sandbox +6 px
   title nudge. No new text was shrunk.
6. `final.png` is the 2361 x 1423 contact sheet for the existing gate; do not
   insert it into Word. Insert `final-08a.png` and `final-08b.png` at
   9.15 in wide each.

### Files changed
`docs/diagrams/rebuild/component/`: `component-08a.svg/.drawio/.png`,
`component-08b.svg/.drawio/.png`, `component-08a-prefix.svg/.png`,
`component-08b-prefix.svg/.png`, `spec-08a.json`, `spec-08b.json`,
`trace-08a.json`, `trace-08b.json`, `text-content-08a.json`,
`text-content-08b.json`, `font-plan-08a.json`, `font-plan-08b.json`,
`letter-spacing-08a.json`, `letter-spacing-08b.json`, `inventory-08a.md`
(126 elements), `inventory-08b.md` (103), `split.json`; retained evidence
`spec-stage-b-prefix.json`, `component-prefix.svg`.
`docs/qa/rebuild-preview/component/`: `final.png` (contact sheet),
`final-08a.png`, `final-08b.png`, `08a.png`, `08b.png` (same renders),
`side-by-side-final-08a/-08b.png`, `overlay-final{,-08a,-08b}.png`,
`diff-final{,-08a,-08b}.png`, `regions-final/` (9), `regions-final-08b/` (9),
`checker-08a.txt`, `checker-08a-broken.txt`, `checker-08b.txt`,
`checker-08b-broken.txt`, `checker-final-08a.txt`, `checker-final-08b.txt`,
`delta-split-f4.txt`, `caption-proposal.md`; retained `final-prefix.png`.
New scripts: `scripts/build_component_split_f4.py`,
`scripts/check_f4_component_split.py`,
`scripts/make_component_f4_previews.py`,
`scripts/make_figure_inventory_f4.py`.

## Logic-alignment update — 2026-11-09

The Admin & Settings Service line is now **“review & approval”** (was “global
result flow”). Page 08b geometry is unchanged. Rule-8 checker **PASS 54 labels
/ 341 elements**; deliberately broken copy **FAIL 289**; previews regenerated.

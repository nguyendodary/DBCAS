# Content delta — verified against the real project (W4 quick pass, 2026-11-09)

Scope: this file re-verifies `docs/qa/diagram-originals/content-delta.md`
row by row against the shipped project. It is the input for the diagram
Stage B agents. Where the earlier file is wrong, the wrong row is named
explicitly. Where the real project does not support a proposed change,
the change is marked **do not add**.

Evidence read for this pass:

| Evidence | Verified values |
| --- | --- |
| `docs/qa/schema-introspection.json` (PostgreSQL 17.11) | **41 tables, 293 columns, 59 FKs, 87 indexes, 0 enums, 19 migrations** |
| `db/schema.sql` + `db/migrations/001–019` | 41-table DDL; migration 018 makes `assessment_session.assessment_id` nullable; migration 019 closes published `assessment` rows |
| `docs/qa/project-facts.json` | Compose 6 + `qa-ai`; OpenAPI **82 paths / 93 operations**; **23** frontend routes; Admin nav **5**; OAuth `[github, google]`; SMTP `mailpit:1025`; sandbox `dbcas-sql-ephemeral:local`, `--network none`, 256 MB, 1 CPU; count 1–20 default 5 |
| `docker-compose*.yml` | local: `mailpit`, `db`, `executor-image`, `init`, `app`, `frontend`; base: `db`, `mailpit`, `sandbox`; release: `db`, `sandbox`, `migrate`, `backend`, `worker` (optional profile), `frontend` |
| `backend/app/routers/*.py` | `admin`, `assessments`, `auth`, `concepts`, `oauth`, `practice`, `sessions` (7 router files) |
| `backend/app/services/*.py` | `practice_service` (plan freeze + 30-min expiry + hard-coded 70% practice target), `practice_bank`, `practice_selection`, `practice_generation`, `session_service`, `adaptive_engine` (legacy/optional), `grading_service`, `grading_jobs`, `competency_service`, `cumulative_competency`, `guidance_service`, `prompt_builder`, `llm/`, `ephemeral_sandbox`, `mail`, `oauth`, `password_reset` |
| `frontend/src/App.jsx`, `components/Layout.jsx` | 23 routes; Admin nav = Cohort, Grading, Accounts, Question Bank, System |
| `docs/diagrams/rebuild/system-context/text-content.json` | owner-approved Stage B labels (34 labels) |
| Original PNGs in `docs/qa/diagram-originals/` | viewed: Use Case, Container, Component, Module, Allocation (Arch Figs 1, 3–6); Logical and Pipeline (Proposal Figs 3–4); ERD and TRD (Arch Figs 7–8) |
| v1.2 in-place redraws in `docs/qa/doc-v2-new-diagrams/` | viewed: Use Case, Container, Component, Module, Allocation, ERD, TRD |

General rule for the diagram agents: **the original PNG is the composition
template; the labels below are the content that must be true; do not copy
a label from the original when it is listed under CORRECT or REMOVE.**

## Summary of wrong or incomplete rows in `content-delta.md`

| # | Figure / row | Why it is wrong |
| --- | --- | --- |
| W1 | Context / Learner flows | Says "correct 2 labels" but lists up to 4 learner-label changes; owner-approved Stage B applied only **Practice requests** and **Result flow & settings**. Approved labels still read `MCQ / SQL / Conceptual answers` and `Assessment results`. |
| W2 | Context / Admin flows | Header says **8** admin flows; the original/approved figure has **7** (`CLOs & Concepts`, `Questions`, `Rubrics`, `Result flow & settings`, `Learner performance`, `Competency gap analytics`, `AI mapping suggestions`). |
| W3 | Context / Sandbox | Proposes "add 1 flow only". The sandbox is **internal** to DBCAS; a system-context flow to it would cross the system boundary. Stage B did not add it. Remove this row. |
| W4 | Context / summary | Says "added 2 boxes + **4** flows"; the OAuth + email rows justify **3** flows (`OAuth sign-in request`, `Identity assertion`, `Password-reset email`). |
| W5 | Use Case | Says only UC09/UC12 change; the real v1.2 figure also changes **UC18** from "Review assessment history and evidence" to "Review practice history and evidence". |
| W6 | Container | Says original version text contains "36 tables"; the original container PNG has no "36 tables" string (only "adaptive selection"). The 41-table text belongs to the redraw, not the original. |
| W7 | Container / Allocation | Lists `mailpit` in the real project but then says "keep 5–6 containers"/"keep 8 nodes" and adds no email node. Compose really has a Mailpit container (local/base), and release uses an external SMTP relay. Add one external Email Service node (and OAuth nodes) or state deliberately that this view is production-only. |
| W8 | Container labels | The v1.2 redraw labels the Nginx container `Web Application [Container: React 19.3, Vite 8]`; React/Vite is the SPA build, not the web server. See exact split below. |
| W9 | Module | Says "correct 1 module name"; the Practice card needs **4** label changes (module title + 3 inner boxes). |
| W10 | Logical | Gives no exact six Tier-2 labels. "Practice replaces Assessment/Adaptive" changes two boxes, but `Assessment Session Service` and `Adaptive Engine` must be replaced by practice/plan/release names; see exact list below. |
| W11 | Pipeline | Says "keep 8-box loop + fallback" and "correct counts/caps". The real flow has **no adaptive selection loop and no opening 3 MCQs**; the plan is frozen before question one. Keeping the loop preserves a false mechanism. Redraw the 8 boxes as practice setup → plan assembly/freeze → serve → grade → evidence → complete, with candidate preparation → validated bank feeding the plan. |
| W12 | ERD / diamonds | Says "12 diamonds" and includes **`pools`**, which is not an FK relationship between the two legacy entities shown in the earlier redraw. FK reality gives **15** relations among the chosen 12 core entities; `pools`/`versions` are valid only on `Assessment–AssessmentQuestion` / `Assessment–AssessmentBlueprint`, never `AssessmentQuestion–AssessmentBlueprint`. |
| W13 | TRD | Says "41 cards, PK/FK/type/null per card (**full schema**)". The existing v1.2 TRD shows a **subset** of columns per card with "+N more columns"; 293 columns on one 3440×2080 canvas is not full schema. Split/page count is **PENDING** owner decision. |

---

## 0. Context — Proposal Fig 2 = Architecture Fig 2 (already approved; do not silently change)

Status: **Stage B approved 2026-11-09**. Exact approved labels are in
`docs/diagrams/rebuild/system-context/text-content.json`. If the figure is
ever rebuilt again, these are the exact final labels:

**KEEP (system / boxes / legend)**
- Title: `DBCAS System Context Diagram`
- Ellipse: `DBCAS`
- Boxes: `Learner`, `Administrator`, `LLM Provider`, `OAuth Providers`, `Email Service`
- Legend: `System`, `Actor`, `Interaction`

**KEEP (24 approved flow labels, exact text)**
`Practice requests`; `CLOs & Concepts`; `MCQ / SQL / Conceptual answers`;
`Questions`; `View requests`; `Rubrics`; `Authentication requests`;
`Result flow & settings`; `Registration requests`; `Assessment results`;
`Learner performance`; `Competency profile & gaps`; `Competency gap analytics`;
`Study guidance`; `AI mapping suggestions`; `Gap explanation requests`;
`Essay evaluation requests`; `CLO/Concept mapping requests`;
`Mapping suggestions`; `Essay evaluation results`; `Gap explanations`;
`OAuth sign-in request`; `Identity assertion`; `Password-reset email`.

**CORRECT / OPEN (owner decision needed before any change)**
- `MCQ / SQL / Conceptual answers` → the real question types are **mcq, sql,
  essay** (`practice_config.QUESTION_TYPES`; `question.question_type` CHECK).
  A factually cleaner label is `MCQ / SQL / essay answers`. The approved
  Stage B did **not** apply this, so do not change it without the owner.
- `Assessment results` → current learner flow is practice
  (`/api/v1/practice/start`, `assessment_session` holds practice runs).
  A factually cleaner label is `Practice results`. Not applied in Stage B.
- `Assessment requests` was already renamed to `Practice requests`; do not
  reintroduce the old text.
- `Assessment configuration` was already renamed to `Result flow & settings`;
  do not reintroduce it.

**DO NOT ADD**
- No sandbox flow/box in the context view: `ephemeral_sandbox.py`,
  `dbcas-sql-ephemeral:local` and `--network none` are **inside** the DBCAS
  boundary. Sandbox belongs in Container/Component/Allocation, not Context.

**Wrong rows in the old file:** W1, W2, W3, W4.

---

## 1. Use Case — Architecture Fig 1

Original: 2 actors (`Learner`, `Administrator`), system boundary `DBCAS system`,
18 ellipses UC01–UC18, note at bottom. v1.2 already redrew it with the
corrections below.

**KEEP (exact labels)**
- Title: `DBCAS Use Case Diagram`
- Actors: `Learner`, `Administrator`
- System boundary: `DBCAS system`
- Note: `Learner registration is available before sign-in. UC13 and UC14 occur within UC12.`
- 18 baseline ellipses, in the original positions:
  `UC01 Register learner account`, `UC02 Login`, `UC03 Logout`,
  `UC04 Provision administrator accounts`, `UC05 Define CLOs and concept model`,
  `UC06 Review AI-suggested CLO mappings`, `UC07 Curate validated question bank`,
  `UC08 Review AI-recommended question tags`,
  `UC09 Configure result flow and settings`,
  `UC10 Oversee AI-generated question candidates`,
  `UC11 View learner and cohort analytics`,
  `UC12 Take personalized practice session`,
  `UC13 Write and run SQL`,
  `UC14 Answer MCQ and essay questions`,
  `UC15 Receive grading results and feedback`,
  `UC16 View competency profile`,
  `UC17 View competency gap explanations`,
  `UC18 Review practice history and evidence`

**CORRECT (old → new; all already reflected in the v1.2 figure except where noted)**
- `UC09 Configure adaptive assessments` → `UC09 Configure result flow and settings`
  — real admin screen is System settings with one global `result_flow`
  (`IMMEDIATE` / `HUMAN_VERIFIED`); there is no exam builder
  (`backend/app/services/system_settings.py`, `PUT /api/v1/admin/system`).
- `UC12 Take timed adaptive assessment` → `UC12 Take personalized practice session`
  — learner picks concepts, bands, count 1–20 (default 5), source bank/AI;
  plan frozen before question one; expires after 30 minutes
  (`practice_config.py`, `practice_service.py`).
- `UC18 Review assessment history and evidence` → `UC18 Review practice history and evidence`
  — this correction is **missing from content-delta.md** and is already in
  the v1.2 figure. Evidence: `/history` routes, `HistoryPage.jsx`,
  `assessment_session` now stores learner practice runs.
- Optional note under UC12: `1–20 questions (default 5) · 30-minute expiry`
  (do not replace the ellipse text with this long note; keep the short
  ellipse label and put the detail in the existing bottom note).

**ADD (pending owner decision only)**
- `UC19 Manage interface preferences` — real Settings page, language/theme
  stored in browser (`SettingsPage.jsx`, `i18n/index.js`).
- `UC20 Review and publish human-verified results` — real admin grading
  review/publish flow (`grading_review.py`, `/api/v1/admin/grading-reviews`).
  The v1.2 text says UC19/UC20 are extensions specified in §3.2 and the
  figure is the **baseline 18**. Do not add them unless the owner lifts the
  baseline limitation; the text already documents them.

**REMOVE / DO NOT KEEP**
- `Configure adaptive assessments`, `Take timed adaptive assessment`,
  `Review assessment history and evidence` (v1.1 wording).

**Wrong row:** W5 (UC18 correction omitted).

---

## 2. Container — Architecture Fig 3

Original: 2 person boxes, 3 application containers (`Web Application`,
`Single Page Application`, `API Application`), `Database`, `SQL Execution
Sandbox`, external `LLM Provider API`. v1.2 redraw kept the same 8 boxes but
still mislabels the Nginx container and omits Email/OAuth.

**KEEP (exact v1.2 labels that are already correct)**
- `Learner [Person]` — `Undergraduate student taking database practice`
- `Administrator [Person]` — `Faculty / course manager who curates content and maintains system settings`
- `Web Application` — `Delivers static content and the SPA bundle`
- `Single Page Application` — `Learner and Administrator portals, SQL editor, radar and bar charts`
- `API Application` — `Authentication, practice sessions, plan assembly, grading, competency and gap engines`
- `Database` — `Users, CLOs, concepts, question bank, sessions, evidence, cached LLM responses (41 tables)`
- `SQL Execution Sandbox` — `Isolated, read-only learner role, 3 s timeout, 256 MB memory limit`
- `LLM Provider API` — `Any compliant provider (REST); assistive tasks only`
- Flow labels: `Takes practice sessions, views competency profile`;
  `Manages CLOs, bank, rubrics; reviews analytics`; `Delivers to user's web browser`;
  `Makes API calls [JSON/HTTPS + JWT]`; `Reads from and writes to [SQL]`;
  `Executes learner SQL [read-only transaction]`;
  `Sanitized prompts / candidate requests [HTTPS/REST]`

**CORRECT (old → new)**
- `Web Application [Container: React 19.3, Vite 8]` → `Web Application [Container: Nginx 1.29]`
  — `frontend/Dockerfile` serves the built `dist` with `nginx:1.29-alpine`;
  the container maps `18080:8080` in local Compose.
- `Single Page Application [Container: React, Tailwind CSS 4, Chart.js 4.5]`
  → `Single Page Application [Container: React 19.3, Vite 8.3.1, Tailwind CSS 4.3.3, Chart.js 4.5.1]`
  — exact frontend versions from `frontend/package.json`.
- `API Application [Container: FastAPI 0.141.1, Python 3.13]` — correct;
  add `uvicorn` if a runtime tag is wanted (`backend/requirements.txt`).
- `Database [Container: PostgreSQL 17]` — correct; 41 tables.
- `SQL Execution Sandbox [Container: Docker, PostgreSQL 17]` — correct;
  sandbox image `dbcas-sql-ephemeral:local`, `--network none`, 256 MB.
- Any `36 tables` / `adaptive selection` text → `41 tables` / `practice plan assembly`.
  **The original container PNG has no "36 tables" string** (W6); only the
  adaptive-selection wording is original.

**ADD (evidence-backed; owner may choose production-only view)**
- `Email Service [External Software System]` — `Password-reset email (Mailpit v1.24 in development; SMTP relay in release)`.
  Local/base Compose: `mailpit` (SMTP 1025, UI 18025); `backend/app/services/mail.py`
  sends only password-reset mail. Release Compose has no Mailpit; it points
  at a real SMTP relay (`deploy/release.env.example`).
- `OAuth Identity Providers [External Software System]` — `Google and GitHub OAuth 2.0`.
  `backend/app/routers/oauth.py`, `services/oauth.py`; 2 providers in project-facts.
- If the owner insists on the original 8-box count, keep the two external
  systems out and state in the figure note that OAuth/SMTP are context-level
  dependencies; do **not** invent a Mailpit box inside the DBCAS boundary.

**REMOVE**
- The overlapping duplicate white title text visible in the original Web
  Application/SPA boxes (the clean v1.2 redraw already fixes it).
- No `assessment`/`adaptive` container.

**Wrong rows:** W6, W7, W8.

---

## 3. Allocation — Architecture Fig 6

Original: 8 nodes — `Learner / Administrator` (Person), `User's Device`,
`Internet`, `Web Server`, `Application Server`, `Database`, `SQL Sandbox`,
`LLM Provider API`. v1.2 already changed "adaptive selection" to "practice
plan assembly".

**KEEP (exact labels)**
- `Learner / Administrator [Person]`
- `User's Device` — `Laptop / desktop with modern browser (Chrome, Edge, Firefox, Safari)`
- `Internet`
- `Web Server [Container]` — `Serves static content and the React + Vite single-page application`
- `Application Server [Container: FastAPI, Python 3.13]` — `Business logic: JWT / RBAC, grading, practice plan assembly, competency engine`
- `Database [Container: PostgreSQL 17]` — `Application data, evidence, cached LLM responses`
- `SQL Sandbox [Container: Docker, PostgreSQL 17]` — `Isolated, network disabled, read-only learner role; 256 MB, 3 s timeout`
- `LLM Provider API [External service: provider-agnostic REST]` — `Essay scoring, CLO mapping, tag suggestions, gap explanations`
- Flow labels: `Uses`, `HTTPS`, `JSON / HTTPS (REST API calls)`, `DB requests (SQL / SQLAlchemy)`, `Sandboxed SQL execution (read-only transaction)`, `Sanitized prompts / structured JSON (HTTPS)`

**CORRECT**
- `adaptive selection` → `practice plan assembly` (done in v1.2; keep).
- `Learner / Administrator` is one combined Person box; that is original
  style and may stay.
- The old file says "same 8 (Compose)". That is wrong: **the 8 nodes are not
  the Compose service list** (Compose local has 6 services + `qa-ai`; base
  has 3; release has 6 including an optional worker). Say "same 8 deployment
  nodes", not "8 Compose".

**ADD (evidence-backed; same owner decision as Container)**
- `OAuth Identity Providers [External service: Google/GitHub]` connected to
  the browser/Application Server.
- `Email Service [External service: SMTP/Mailpit]` connected to the
  Application Server (password-reset mail only).
- Optional: `Background Worker` as a note inside `Application Server`
  (`backend/app/main.py` starts `maintenance_loop`; release also has an
  optional `worker` profile). Do not draw it as a new deployment host unless
  the owner wants the release topology.

**REMOVE**
- Any "adaptive selection" text.

**Wrong row:** W7 (Compose claim / missing email).

---

## 4. Module — Architecture Fig 5

Original: 3 top bars, 6 functional module cards, 3 shared dependencies.
v1.2 already redrew the Practice card; the old file only records "1 module
name", so its correction count is incomplete (W9).

**KEEP (exact v1.2 labels)**
- Title: `DBCAS MODULE VIEW`
- Top bars: `Web UI · Learner and Administrator portals`;
  `API entry · FastAPI routing, JWT and validation`;
  `Backend services · Controllers → Services → Repositories`
- Section label: `FUNCTIONAL MODULES`
- Cards:
  - `Identity & Access`: `Auth Controller` → `Auth Service` → `Account Repository`
  - `Curriculum`: `Curriculum Controller` → `Curriculum Service` → `Curriculum Repository`
  - `Question Bank`: `Question / Candidate Controller` → `Question Bank Service` → `Question Repository`
  - `Practice`: `Practice Controller` → `Practice Service` → `Session / Plan Repository`
  - `Grading`: `Grading Controller` → `Grading Service` → `Attempt / Evidence Repository`
  - `Competency`: `Analytics Controller` → `Competency + Gap Service` → `Competency Repository`
- Section label: `SHARED DEPENDENCIES`
- Shared boxes:
  - `PostgreSQL 17` — `Application data, evidence and LLM cache`
  - `LLM Gateway` — `Sanitized requests; provider-agnostic assistive calls`
  - `SQL Sandbox` — `Isolated PostgreSQL; read-only, time and memory limits`
- Footnote: `Repositories persist application records. Services call the LLM Gateway or SQL Sandbox only when the workflow requires them.`

**CORRECT (old → new; 4 text changes, not 1)**
- Card title `Assessment` → `Practice`
- `Assessment Controller` → `Practice Controller`
- `Session + Adaptive Service` → `Practice Service`
- `Assessment / Selection Repository` → `Session / Plan Repository`
- `Attempt Controller` → `Grading Controller` (v1.2 already does this)
- `Attempt Repository` → `Attempt / Evidence Repository` (v1.2 already does this)
- `LLMCache` as a module/dependency name → `LLM cache` in the PostgreSQL
  box; `llm_cache` is a table, not a module (`schema-introspection.json`).

**ADD**
- None. The 6-module abstraction is deliberate; do not add Release/Localization
  cards to this figure (they are in the v1.2 text, not the original tile set).

**REMOVE**
- `Assessment` module, `Adaptive Service`, `Selection Repository` as live
  concepts. The legacy `assessment*` tables and `selection_log` remain in the
  database but are not a module.

**Wrong row:** W9.

---

## 5. Logical — Proposal Fig 3

Original: 4 tier bands, 6 Tier-2 service boxes, 2 portal boxes, 2 sandbox/LLM
boxes. v1.1/1.2 still embeds the old adaptive labels; this figure is **not**
redrawn in v1.2. Use the exact final labels below.

**KEEP (structure / exact unchanged labels)**
- Title: `DBCAS Logical System Architecture Diagram`
- Subtitle: `Four-Tier Architecture: Presentation, Application & Services, Data & Storage, External AI & Sandbox`
- Tier 1 title: `TIER 1: PRESENTATION TIER (REACT.JS / VITE / TAILWIND / CHART.JS)`
- Tier 2 title: `TIER 2: APPLICATION & SERVICES TIER (FASTAPI / PYTHON)`
- Tier 3 title: `TIER 3: DATA & STORAGE TIER (POSTGRESQL)`
- Tier 4 title: `TIER 4: EXTERNAL AI SERVICE & EXECUTION SANDBOX`
- Actors: `Learner`, `Administrator`
- `Request Validation` — `Pydantic Schemas · Rate Limiting`
- `Auth & Role Management` — `JWT Auth · RBAC · Stateless (FR-01)`
- `Automated Grading Engine` — `MCQ · SQL Output · Essay Rubric (FR-08/09/10)`
- `Competency & Gap Engine` — `Evidence · Competency · Gaps (FR-11/12/14)`
- `Docker SQL Sandbox` — `Isolated PostgreSQL · Read-Only Tx (FR-09)`
- `LLM Provider API (Any Provider)` — `Essay Scoring · CLO Mapping · Explanations (FR-10/03/14)`

**CORRECT (old → new)**
- `Learner Assessment Portal` → `Learner Practice Portal`
  — subtitle `Practice setup · Competency charts · SQL editor` (drop `Exam UI`).
- `Administrator Management Portal` — keep the title; subtitle
  `CLOs & Concepts (FR-02) · Question Bank (FR-04) · Analytics & review`.
- `Assessment Session Service / Session Coordination · Question Delivery`
  → `Practice Session Service / Plan assembly · Frozen delivery · 30-min session`
  — `practice_service.py` freezes `SessionQuestionPlan` before question one;
  `session_service.py`/`personalized_assessment.serve_planned` serve it.
  The plan balances the exact count across the selected concepts/bands and
  discloses widening to related concepts/bands when capacity is short; do
  not label it "every selected concept" unconditionally.
- `Adaptive Engine / Concept + Difficulty + Type · Gen/Validate (FR-15)`
  → `Practice Plan Assembly / Bank + AI selection · Validate · Freeze (FR-15)`
  — no adaptive engine is in the live learner flow; `practice_bank`,
  `practice_selection`, `practice_generation` do selection/validation/freeze.
- Tier 3 PostgreSQL subtitle:
  `Users & Roles | CLOs & Concept Model | Question Bank & Rubrics | Attempts | Evidence Logs | Cached LLM Responses — Stateless JWT (no session store)`
  → `41 tables: Users & Roles | CLOs & Concept Model | Question Bank & Rubrics | Practice Sessions & Frozen Plans | Attempts & Evidence | Grading/Release Audit | Cached LLM Responses — short-lived access JWT plus a refresh-session table`
  — exact counts from `schema-introspection.json`; `session_question_plan`,
  `evaluation_record`, `grading_job`, `grade_review`, `result_release_event`
  are real tables.
- Tier 4 `LLM Provider API` subtitle is correct; SQL sandbox subtitle may add
  `3 s timeout · 256 MB` (matches code/config).
- If a 6th service-box slot is needed for the release flow, the least
  disruptive exact label is `Release & Review Service / Result flow · Human review · Publish`
  — `grading_review.py`, `result_release_event`, `system_settings.result_flow`.
  Do not call it "Assessment Service" or "Adaptive Engine".

**ADD**
- None beyond the corrected release text if the owner wants human-verified
  release visible. The original 6-box count can be kept by replacing the
  Adaptive box with `Practice Plan Assembly`.

**REMOVE**
- `Adaptive Engine`, `Exam UI`, `Assessment Session Service`, `Learner Assessment Portal`.

**Wrong row:** W10 (no exact six labels; under-specified).

---

## 6. Pipeline — Proposal Fig 4

Original: 8 rounded boxes with an adaptive loop, a 13-question cap, a 10/2/1
target mix and "3 basic MCQs first". All four mechanisms are **wrong** for
the shipped learner flow. This is the largest content delta.

**KEEP (composition / style only)**
- 8 rounded boxes, two rows, solid forward arrows, dashed fallback/feedback
  line, bold box titles + regular body, italic footnote.
- `Candidate preparation` and `Validated item bank` remain real: AI drafts
  are held in `question_candidate`; administrators approve them into
  `question` (`ai_admin_service.py`, `governed_generation.py`).
- Footnote outside scope: `Ranked gap topics only; long-term learning paths and
  course-document retrieval are outside scope.` (keep).

**CORRECT (old → new; exact final box labels and body)**
1. `Opening` → `Practice setup`
   Body: `Concepts · difficulty bands EASY 1–2 / MEDIUM 3 / HARD 4–5 · count 1–20 (default 5) · source bank or AI`
2. `Grade each answer` stays in the loop, but not second:
   make box 4 `Grade each answer` — `MCQ key · SQL sandbox · essay rubric (Prompt Builder → Evaluator)`
3. `Evidence` → `Record evidence`
   Body: `Score · question snapshot · concept tags · validation flags` (`attempt`, `evaluation_record`)
4. `Adaptive selection` → `Plan assembly & freeze`
   Body: `Exact count · spread across selected concepts as far as the count allows · no repeated version families · SQL bank-only · AI MCQ/essay`
5. `Next item` → `Serve planned item`
   Body: `Only validated bank / approved AI items, in the frozen plan order`
6. `Complete assessment` → `Complete session`
   Body: `All planned items served or 30-minute expiry/00:00 · deterministic per-concept competency · ranked “What to study next”`
7. `Candidate preparation` — keep title; body `AI drafts → automated checks → administrator approval`
8. `Validated item bank` — keep title; body `Approved items only · source for all SQL · bank fallback`
- Remove `3 MCQs at levels 1–2 from validated bank` from the opening.
- Remove `After opening MCQs: 3/3 harder · 2/3 medium · 0–1/3 basic / weak`.
- Remove `Repeat after each answer until cap or timer`; replace with
  `Serve the next item from the frozen plan; repeat until all planned items are served or the 30-minute timer expires`.
- Remove the footer `Target mix for a full session: 10 MCQ / 2 SQL / 1 essay`;
  replace with `Session length 1–20 (default 5) · 30-minute expiry · SQL always from the validated bank; AI fallback shows one bank_mixed notice`.
- Title `Evidence-based adaptive assessment pipeline` → `Evidence-based Competency & Gap Evaluation Pipeline`
  (match the document caption exactly) and subtitle `Three basic MCQs first • each later question selected from live evidence`
  → `Complete practice plan frozen before question one • every served item comes from the plan`.

**ADD**
- `bank_mixed` fallback note: if AI cannot fill the plan, bank items complete it
  and one notice is shown (`practice_service.py`).
- Bank shortage is a hard stop with an explicit explanation; do not draw a
  silently shortened session (`practice_bank.assemble` raises
  `bank_capacity_error`).

**REMOVE**
- `Adaptive selection`, `adaptive`, `13-question cap`, `10 MCQ / 2 SQL / 1 essay`,
  `3 MCQs first`, `configured cap (≤13)`, `Repeat after each answer until cap or timer`.

**Wrong row:** W11. This row must not be implemented as "keep the loop and
change numbers only".

---

## 7. Component — Architecture Fig 4

Original: 7 controllers + 7 services + 7 repositories + LLM Gateway + Database +
Sandbox Runner + LLM Provider + SQL Sandbox. v1.2 already has the correct
7/7/7 replacement.

**KEEP (exact v1.2 labels)**
- Band titles: `Controller [Container: FastAPI routers, Pydantic validation]`;
  `Service [Container: business logic]`;
  `Repository [Container: SQLAlchemy data access]`
- Controllers (7): `Auth Controller` (`Register, login/logout, OAuth, password reset`);
  `Practice Controller` (`Practice setup, start, serve, submit`);
  `Curriculum Controller` (`CLOs, concepts, prerequisites, mappings`);
  `Question Bank Controller` (`Questions, options, datasets, rubrics, candidates`);
  `Analytics Controller` (`Profile, gaps, history, cohort analytics`);
  `Grading Controller` (`Answers, run SQL, review queue`);
  `Accounts Controller` (`Accounts, roles, system settings`)
- Services (7): `Auth Service` (`JWT, password hashing, OAuth, throttling`);
  `Practice Service` (`Plan assembly, 30-min session, serve plan`);
  `Curriculum Service` (`CLO rules, concept mapping confirmation`);
  `Question Bank Service` (`Validated bank curation, tags, candidates`);
  `Competency & Gap Service` (`Deterministic competency, gaps, study ranking`);
  `Grading & Evaluation Service` (`MCQ key, SQL sandbox, Prompt Builder → Evaluator`);
  `Admin & Settings Service` (`Accounts, roles, global result flow`)
- Repositories (7): `Account Repository` (`Account, Role, AccountRole, UserProfile`);
  `Session & Plan Repository` (`AssessmentSession, Plan, StartRequest`);
  `Curriculum Repository` (`CLO, Concept, CLOConcept`);
  `Question Repository` (`Question, Concept tag, MCQOption, Dataset, Rubric`);
  `Competency Repository` (`ConceptCompetency, Gap, EvaluationRecord`);
  `Grading Repository` (`Attempt, GradingJob, GradeReview, EditAudit`);
  `Audit & Settings Repository` (`SystemSetting, RoleAudit, Throttle, LLM cache`)
- Bottom: `LLM Gateway [Component: Python]` — `PII sanitizer, prompt templates, strict JSON schema, LLM cache`;
  `Database [Container: PostgreSQL 17]` — `Stores all application data (41 tables)`;
  `Sandbox Runner [Component: Python, Docker]` — `Read-only transaction, 3 s timeout, rollback after evaluation`;
  `LLM Provider API [External System]`; `SQL Sandbox [Container: Docker, PostgreSQL 17]`.

**CORRECT (old → new; exact mapping of the 3 retired controllers)**
- `Assessment Controller` → `Practice Controller`
- `Attempt Controller` → `Grading Controller`
- `Candidate Controller` → `Accounts Controller` (candidate review remains in
  the Question Bank/admin API; "Accounts" is the v1.2 grouping)
- Services also change 2 labels beyond the old file's "3 retired":
  `Assessment Session Service` → `Practice Service`;
  `Adaptive Engine Service` → `Admin & Settings Service`.
- Repositories: `Assessment Repository` → `Session & Plan Repository`;
  `Attempt Repository` → `Grading Repository`;
  `Selection & Candidate Repository` → `Audit & Settings Repository`.

**ADD**
- None. The service/repository names are already in the v1.2 figure. If a
  reviewer objects that `Accounts Controller` does not own system settings,
  split the label as `Accounts / Settings Controller`; the endpoints are
  `admin.py` (accounts/roles) and `practice.py` `/admin/system`.

**REMOVE**
- `Assessment Controller`, `Assessment Session Service`, `Adaptive Engine Service`,
  `Assessment Repository`, `Attempt Repository`, `Selection & Candidate Repository`
  as live components.

**Wrong row:** none in substance; the old file is under-specified (it says
"3 retired" but 3 controllers + 2 services + 3 repositories change). Use the
exact labels above.

---

## 8. ERD (Chen) — Architecture Fig 7 = Database Fig 1

Original: 17 entities, 17 key ellipses, 23–24 relationship diamonds (the old
file says "~20"), legend. v1.2 already redrew the 12-core + 4-legacy shape.

**KEEP (exact entity labels and keys)**
- 12 core entities: `Role`, `Account`, `UserProfile`, `SystemSetting`,
  `CourseLearningOutcome`, `Concept`, `Question`, `MCQOption`,
  `AssessmentSession`, `Attempt`, `ConceptCompetency`, `CompetencyGap`
- 4 legacy entities, dashed + `LEGACY` tag: `Assessment`, `AssessmentConcept`,
  `AssessmentQuestion`, `AssessmentBlueprint`
- Key ellipses (16): `role_id`, `account_id`, `user_id`, `setting_key`,
  `clo_id`, `concept_id`, `question_id`, `option_id`, `session_id`,
  `attempt_id`, `competency_id`, `gap_id`, `assessment_id`,
  `assessment_id, concept_id`, `assessment_id, question_id`, `blueprint_id`
- Legend: `Entity`, `Relationship`, `Key attribute`, `1 = one, N/M = many
  (M:N = many-to-many)`, `Legacy table (historical rows only)`

**CORRECT (old → new / exact relationship labels)**
- The old file's "12 diamonds" is **wrong**: FK reality supports **15**
  relationships among the 12 core entities. Use these exact diamond labels:
  1. `assigned` — Account M:N Role (via `account_role`)
  2. `has` — Account 1:1 UserProfile (`user_profile.account_id`)
  3. `defines` — Account 1:N CourseLearningOutcome (`created_by`)
  4. `takes` — Account 1:N AssessmentSession (`learner_id`)
  5. `tagged with` — Question M:N Concept (via `question_concept`)
  6. `offers` — Question 1:N MCQOption (`mcq_option.question_id`)
  7. `selected in` — Attempt N:1 MCQOption (`selected_option_id`)
  8. `records` — AssessmentSession 1:N Attempt (`attempt.session_id`)
  9. `yields` — AssessmentSession 1:N ConceptCompetency (`session_id`)
  10. `measured by` — Concept 1:N ConceptCompetency (`concept_id`)
  11. `diagnosed` — AssessmentSession 1:N CompetencyGap (`session_id`)
  12. `targets` — Concept 1:N CompetencyGap (`concept_id`)
  13. `versions` — Question 1:N Question (`family_id` self-FK)
  14. `updates` — Account 1:N SystemSetting (`updated_by`, nullable)
  15. `requires` — Concept M:N Concept (via `concept_dependency`)
- If the owner enforces a 12-diamond cap, drop `updates`, `requires`,
  `selected in`; do **not** drop `takes`, `records`, `yields`, `measured by`,
  `diagnosed`, `targets`, `versions` — those are the core learner/competency
  path.
- Legacy relationship labels (only if legacy entities are connected; each is
  FK-backed):
  - `targets` — Assessment 1:N AssessmentConcept (or M:N to Concept via the junction)
  - `pools` — Assessment 1:N AssessmentQuestion
  - `versions` — Assessment 1:N AssessmentBlueprint
  - `instantiates` — AssessmentSession N:1 Assessment (`assessment_id`, nullable)
  - `uses` — AssessmentSession N:1 AssessmentBlueprint (`blueprint_id`, nullable)
- **Do not** draw `pools` or `versions` between `AssessmentQuestion` and
  `AssessmentBlueprint`; there is no FK between those two tables
  (`schema.sql`/introspection). That was a defect in the earlier v1.2 redraw.

**ADD**
- `SystemSetting` core entity (already in v1.2).
- `CourseLearningOutcome` (the original called it `CLO`; v1.2 uses the full
  table name; keep one exact label, preferably `CourseLearningOutcome` to match
  the data dictionary, or `CLO` to match the original — do not mix).
- `ConceptDependency` relationship `requires` if the owner keeps 15 diamonds.
- `Question.family_id` self-reference `versions` (real lineage).

**REMOVE**
- `Rubric`, `QuestionCandidate`, `SQLTestDataset`, `SelectionLog`, `LLMCache`
  from the Chen ERD; they remain in the TRD/data dictionary. This is the
  original "core subset" decision, not a schema deletion.
- `pools`/`versions` between `AssessmentQuestion` and `AssessmentBlueprint`.
- The old "~20 diamonds" count.

**Wrong row:** W12.

---

## 9. TRD (Table Relationship Diagram) — Architecture Fig 8 = Database Fig 2

Original: ~21 table cards with PK/FK/type/null columns, crow's-foot legend.
v1.2 already has a 41-card redraw at 3440×2080.

**KEEP (exact)**
- Card grammar: table name header, PK/FK markers, `int`, `varchar(n)`,
  `text`, `bool`, `timestamptz`, `numeric(p,s)`, `jsonb`, `smallint`.
- Legend: `PK primary key`, `FK foreign key (target table shown after →)`,
  `dashed card = legacy table (historical rows only)`,
  `41 tables · 293 columns · 59 foreign keys · 19 migrations`.
- All 41 table cards, exact names:
  `account`, `account_identity`, `account_role`, `account_role_audit`,
  `adaptive_event`, `assessment`, `assessment_blueprint`, `assessment_concept`,
  `assessment_question`, `assessment_session`, `attempt`, `clo_concept`,
  `competency_gap`, `concept`, `concept_competency`, `concept_dependency`,
  `course_learning_outcome`, `evaluation_record`, `grade_edit_audit`,
  `grade_review`, `grading_job`, `llm_cache`, `login_throttle`, `mcq_option`,
  `oauth_handoff`, `password_reset_audit`, `password_reset_token`, `question`,
  `question_candidate`, `question_concept`, `question_translation`,
  `refresh_session`, `result_release_event`, `role`, `rubric`,
  `selection_log`, `session_question_plan`, `session_start_request`,
  `sql_test_dataset`, `system_setting`, `user_profile`.
- Legacy tag on exactly: `assessment`, `assessment_concept`,
  `assessment_question`, `assessment_blueprint`.
- Real FK/cardinality lines must follow `schema-introspection.json` (59 FKs),
  not the old 21-table drawing.

**CORRECT**
- `~21 table cards` → **41**.
- `~5 cols/card` → card density is a design choice; the **full 293 columns do
  not fit legibly on one 3440×2080 canvas**. The current v1.2 card set shows
  a subset and appends `+N more columns`. Do not claim "full schema per card"
  (W13).
- `36 tables` / `21 tables` anywhere → `41 tables`.
- `assessment*` cards must be dashed/`LEGACY`; `selection_log` is **active**
  (one audit row per served item, written by `personalized_assessment.serve_planned`),
  `adaptive_event` is historical/optional (legacy adaptive route), and
  `session_question_plan` is the active frozen plan; `system_setting` is active.

**ADD**
- `system_setting`, `evaluation_record`, `grade_edit_audit`,
  `refresh_session`, `assessment_question` cards (already added in v1.2).
- `session_question_plan`, `session_start_request`, `grading_job`,
  `grade_review`, `result_release_event`, `account_identity`,
  `account_role_audit`, `oauth_handoff`, `login_throttle`,
  `concept_dependency`, `question_translation` (already added in v1.2).

**REMOVE / PENDING**
- Remove any 21-card/36-table count.
- **PENDING OWNER DECISION:** whether the TRD may split into panels/pages to
  show all 293 columns. Content-delta says "no panel splitting", but 293
  columns cannot be full per card on one canvas. Record the page/figure count
  as pending; do not invent a 3-panel or 4-panel split in captions.
  The document caption must stay `Figure 8. Table Relationship Diagram`
  (Architecture) / `Figure 2: Table Relationship Diagram` (Database) until
  the owner decides.

**Wrong row:** W13.

---

## 10. Roadmap — Proposal Fig 1

**KEEP**
- The historical 6-track × Sprint 1–5 grid, July 28 – December 26, 2026.
- No delivery/current-state claim; it is a historical plan (`README.md`,
  Proposal §11.2). Do not modernise it.

**CORRECT / ADD / REMOVE**
- None.

---

## Bottom line for Stage B agents

1. The 18-use-case baseline, the 12-core ERD subset, the 6-module tile set,
   the 4-tier logical layout and the 8-box pipeline layout are the correct
   **abstractions**; keep them.
2. The exact labels in this file override the original PNG labels and the
   earlier v1.2 redraw labels where they differ.
3. The earlier `content-delta.md` rows **W1–W13** must not be copied blindly.
   In particular: no sandbox flow in Context; no 8th admin flow; no
   `AssessmentQuestion–AssessmentBlueprint` relationship; no "full schema"
   claim for the TRD; no adaptive loop in the pipeline.
4. Owner decisions still open: UC19/UC20 on the use-case figure, Email/OAuth
   nodes on Container/Allocation, TRD panel splitting. Record them as pending;
   do not guess.

# DBCAS documentation / codebase alignment and diagrams-as-code — 27 October 2026

Audit, preservation, incremental improvement and tooling task. **Not** a rewrite of the project's
documents. Headline: every architecture figure is now reproducible from a text source by one command,
all pre-existing figures are still present and recoverable, and the repository guides match the code at
HEAD `633fea3`. **One unresolved contradiction was found and deliberately not closed:** the shipped
blueprint policy serves 10 MCQ / 0 SQL / 3 essay for six theory subject areas, while
`docs/requirements-decisions.md` records an owner-approved 10 MCQ / 2 SQL / 1 essay formal contract
(matrix row H1). Six items are held for the document owner rather than resolved by editing whichever
side was convenient.

Scope and ground rules applied throughout:

- Nothing was deleted and replaced with an unrelated diagram. Each of the ten architecture figures
  keeps its filename, its identifiers and its original elements; changes are additive or label-level
  and each carries its own `evidence` and reason inside the ledger (Section 5).
- No application source file was modified. Verified claims were left alone; only objectively verifiable
  technical statements, endpoint names, broken links and executable commands were edited in place
  (Section 6). Dated acceptance records were not rewritten — they are superseded by this document.
- The persistent development database was inspected read-only. No writes, no migration execution and
  no volume deletion were performed. The catalog re-extraction ran against a container intended to be
  disposable; the `dbcas-catalog-7baff1` container was still running when the next phase began, so the
  removal reported here did not stick — it is flagged in
  [academic-documents-ver12-20261027.md](academic-documents-ver12-20261027.md) §8 rather than deleted
  retrospectively.
- Academic originals (root DOCX) were untouched by the audit. Proposed amendments and every item
  needing an owner decision were recorded in
  [academic-reconciliation-20261027.md](academic-reconciliation-20261027.md). No supervisor approval
  is claimed or invented. **Superseded the same day:** the owner then authorised in-place editing of
  the four documents, and the applied result is
  [academic-documents-ver12-20261027.md](academic-documents-ver12-20261027.md). There are no root PDF
  originals — the earlier phrase "DOCX/PDF" and any mention of "their PDF pairs" described the
  derived `output/*_references_fixed.pdf` exports of 2 October, not deliverables.
- Nothing was pushed. Local commits only (Section 9).

Status vocabulary used in Section 4: `MATCHES`, `PARTIALLY MATCHES`, `OUTDATED`, `CONTRADICTS`,
`FUTURE DESIGN-NOT IMPLEMENTED`, `REQUIRES HUMAN DECISION`, `NOT FOUND`.

---

## 1. Documentation inventory (Phase A)

36 Markdown documents in `docs/` (32 before this audit's own two records and the two added by the
same-day document reconciliation), plus root `README.md`, `AGENTS.md` and `CONTRIBUTING.md`. Diagram
assets: 9 `docs/diagrams/*.dot` models, 12 SVGs (10 in `docs/diagrams/`, 2 in `docs/diagrams/rendered/`),
11 preserved original PNGs in `docs/diagrams/originals/`, and 5 JSON ledgers/catalogs.

| Group | Documents |
|---|---|
| Living guides | `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `docs/learner-and-admin-manual.md`, `docs/api-conventions.md`, `docs/setup-and-migrations.md`, `docs/deployment-and-readiness.md`, `docs/testing-and-release-gates.md`, `docs/local-integration-troubleshooting.md`, `docs/requirements-decisions.md`, `docs/diagrams/README.md`, `docs/diagrams/sources/README.md`, `docs/inventory/README.md`, `docs/diagrams/inventory.md`, `docs/diagrams/semantic-review.md`, `docs/diagrams/system-context-review.md` |
| Feature records | `docs/supervisor-implementation.md`, `docs/bilingual-question-verification.md`, `docs/core-question-recovery.md`, `docs/draft-question-translation.md`, `docs/legacy-essay-resolution.md`, `docs/pg-m089-assessment-2-reconciliation.md`, `docs/remediation/*` |
| Dated acceptance / audit records | `docs/academic-reconciliation-20261023.md`, `docs/bilingual-architecture-completion-20261023.md`, `docs/final-integration-acceptance-20261023.md`, `docs/docker-stabilization-acceptance-20261023.md`, `docs/docker-wsl-root-cause-recovery-20261023.md`, `docs/ux-simplification-audit-20261023.md`, `docs/development-activation-20261024.md`, `docs/activation-readiness-20261025.md`, `docs/activation-release-20261025.md`, `docs/phase-2-first-time-user-acceptance-20261026.md`, `docs/diagrams/acceptance-review-20261023.md` |
| Academic originals (outside the repo) | four root `C1SE.70_*` DOCX originals — no root PDF originals exist — plus, since the owner authorised in-place editing the same day, the four `C1SE.70_*_DBCAS_ver1.2.docx` deliverables; `_docread/` holds the read-only extractions, the edit scripts and the Word render logs |

`FITAI - Documents/` in the same workspace is the faculty deliverable **structure**: 15 numbered
categories (Proposal, Project Plan, Product Backlog, User Stories, Architecture Design, Database
Design, User Interface, Test Plan, Test Case, Sprint Backlog, Code Standard, Meeting Minutes,
Reflection, Technologies Stack, AI Documentation). **Every file in all 15 folders belongs to another
project** (`C1SE.56_*SHFA*`, plus one `C1SE.56_FitnessAI_FNAI*`), so none is DBCAS work product and
nothing there was read for content or modified. DBCAS has originals for four of the fifteen
categories - the root Proposal, User Stories, Architecture Design and Database Design documents.

**NOT FOUND** — no such document exists in this project; the audit does not invent its contents:

- a standalone SRS document, which is also **not a category in the 15-item structure** (requirements
  live in `docs/requirements-decisions.md`, `docs/supervisor-implementation.md` and the academic
  originals);
- a standalone UI/screen-design document (category 7 exists in the structure with another project's
  example only; DBCAS design evidence is distributed across
  `docs/ux-simplification-audit-20261023.md` and the frontend tests);
- a university-format test plan, test case sheet or test report (categories 8 and 9 hold other
  projects' examples; DBCAS test evidence is in `docs/testing-and-release-gates.md` and the dated
  acceptance records);
- a technical report document;
- DBCAS documents for categories 2, 3, 10, 11, 12, 13, 14 and 15 (Project Plan, Product Backlog,
  Sprint Backlog, Code Standard, Meeting Minutes, Reflection, Technologies Stack, AI Documentation);
- any Draw.io, PlantUML or Excalidraw source (`docs/diagrams/inventory.md` recorded this on
  23 October and it is still true — `docs/diagrams/sources/` holds only `README.md`, so the PlantUML
  gate legitimately reports `SKIP`).

The missing-deliverable question is recorded as owner decision **H6** in
[academic-reconciliation-20261027.md](academic-reconciliation-20261027.md); drafting eleven academic
deliverables is authorship and was not attempted here.

---

## 2. Implementation evidence inventory (Phase B)

Built from code, not from a README or a historical diagram. Every claim below was read at HEAD
`633fea3`; the generated inventories in Section 7 are the machine-readable version of the interface rows.

**HTTP surface.** 6 routers mounted at `/api/v1` (`backend/app/main.py:65-70`) plus 3 app-level probes
(`:73 /health`, `:78 /api/v1/ping`, `:83 /readiness`) → **82 routes** total, enumerated by
`docs/inventory/api-routes.json`. Router prefixes: `/admin` (`routers/admin.py:64`), `/assessments`
(`routers/assessments.py:10`), `/auth` (`routers/auth.py:14`), `/concepts` (`routers/concepts.py:10`),
`/auth/oauth` (`routers/oauth.py:20`), `/sessions` (`routers/sessions.py:37`).

**Access control.** `require_roles(...)` (`backend/app/deps.py:41`) produces `CurrentAccount`,
`LearnerOnly`, `AdminOnly` (`:53-55`); role assignment is a separate capability
(`require_role_manager`, `:58-62`, `RoleManagerOnly` `:65`) — being an Administrator does not imply
permission to assign roles.

**Service layer.** 40 modules in `backend/app/services/` plus the `llm/` provider package. The paths
that the diagrams depend on:

| Responsibility | Evidence |
|---|---|
| Blueprint resolution and quota verification | `services/blueprints.py:191-235` (`resolve_blueprint`), `:261` (`verify_quotas`), `:242-258` (`snapshot_policy`), `:68-80` (`desired_mix`), `:23-30` (`THEORY_AREAS`) |
| Blueprint seeding on publication | `services/assessment_service.py:226-231` → `services/blueprints.py:139-165` |
| Personalized formal / practice assembly | `services/personalized_assessment.py:16-22` (imports), `:237-245` (resolve + verify + snapshot), `:289` (`blueprint_id` on the session) |
| Batch adaptive rounds and stop reasons | `services/batch_adaptive.py:33-45` (`_event`), `:149-189` (`advance`; `maximum_questions`, `inventory_exhausted`, `stable_performance` → `finalize`) |
| Legacy engine dispatch to batch | `services/adaptive_engine.py:121,444,562` |
| Grading | `services/assessment_lifecycle.py:97-121` (`grade_attempt`), `services/grading_service.py`, `services/sql_grading.py`, `services/essay_grading.py`, bounded retry in `services/grading_jobs.py:13-67` (worker `backend/app/worker.py:13-14`, in-process loop `main.py:30-33`) |
| Human verification and publication | `services/grading_review.py:22` (`transition`), `:155` (`publish`); routes `routers/admin.py:67-101` |
| Cumulative competency (published evidence only) | `services/cumulative_competency.py:64` (`profile`), `:13` (official/published gate) |
| Administrator AI assistance, grounded generation | `services/ai_admin_service.py:586,601,652` → `services/governed_generation.py`; candidate promotion `services/ai_admin_service.py:630-670` |
| Opt-in translation drafts, never persisted | `routers/admin.py:321-325` → `services/question_translation.py:1-2,122` |
| SQL execution | `services/sandbox_runner.py` against a separate PostgreSQL reached through `settings.sandbox_url` with the read-only `learner_ro` role inside `BEGIN`/`ROLLBACK`; not a per-execution Docker container |

**Schema.** `db/schema.sql` declares 35 `CREATE TABLE` statements over **34 distinct** tables
(`concept_dependency` is declared twice, once per ordering direction) with **49 foreign keys**;
`db/migrations/` holds 14 files (`001`–`014`). The persistent development database was read-only
checked on 27 October: `schema_migration` records 001–014 and `public` holds 35 relations (34
application tables + the runtime `schema_migration` table). See
`docs/setup-and-migrations.md` for the 013/014 descriptions.

**Frontend.** React 19.3 / Vite 8.3 / Router 7.18 / i18next 26 / Tailwind 4.3. 21 browser routes
(`docs/inventory/frontend-routes.json`, from `frontend/src/App.jsx:86-113`): 4 public, 1
authenticated-only, 6 learner and 10 administrator gates. The built-in Help guide is a single modal
rendered through `HelpProvider` mounted at `frontend/src/App.jsx:84`, with `HelpButton` in
`Layout.jsx` and `AuthShell.jsx:33` — it has **no route**, which is why `/help` appears in no inventory.

**Tests.** Backend: **1,109 tests collected** (`backend/.venv/Scripts/python.exe -m pytest
--collect-only -q`). Frontend unit: **281 tests in 35 files, all passing** (`npx vitest run`,
29.84 s wall). Playwright: 53 specs per browser across 4 browsers (212 executions, 0 failures) in the
release closure recorded on 26–27 October; deliberately **not** re-run here because no application
source changed during this task.

---

## 3. Diagram-by-diagram preservation report (Phases E–G)

| Diagram | Original location / format | Editable source found? | Preserved | Changed on 27 Oct (+ why) | Render |
|---|---|---|---|---|---|
| System Context | Architecture DOCX image3 (`2794fabf0d75`), PNG; rebuilt as SVG | `system-context.svg` (SVG *is* the source) + `system-context.json` ledger | all 21 original flows, labels and directions; 30 evidenced flows kept | none — `revalidated_20261027` recorded; proposed C52/C53 translation flows **held for owner review** | not re-rendered (SVG-as-source); label/direction assertions pass |
| Use Case | Architecture DOCX image2 (`081cc67a9e34`) | `use-cases.dot` + `.json` | all 20 goals, 30 associations, UML plain-association arrowheads | no visual change; per-row `evidence` corrected for U17–U30 (they shared one 4-file string) | ok (25 nodes / 30 relationships) |
| Container | Architecture DOCX image4 (`040acf4a4581`) | `containers.dot` + `.json` | 12 nodes, 13 relationships, browser-runtime vs process boundary | none — new features are in-process; `revalidated_20261027` | ok |
| Component | Architecture DOCX image5 (`09b28ece8b06`) | `components.dot` + `.json` | 24 original nodes and all 24 original relationships; C&C bands kept as layers of one process | `+bp` box with `B49` plan→bp, `B50` c1→bp, `B51` bp→db (blueprint policy existed in no architecture view); `B52` s3→llm (opt-in translation); labels `s6`, `r6`, `ai` | ok (34 nodes / 51 relationships) |
| Module | Architecture DOCX image6 (`fa0e6f217935` in Proposal / `799e9149e945` allocation) | `modules.dot` + `.json` | all 6 original module chains + shared adapters | labels only: `s2`, `s3`, `s4` now name `blueprints.py`, `batch_adaptive.py`, `grading_jobs.py`, `governed_generation.py`, `question_translation.py`; `M21` widened to include translation drafts | ok (24 nodes / 25 relationships) |
| Allocation / Deployment | Architecture DOCX image7 (`1918f7591e4f`) | `deployment.dot` + `.json` | 13 nodes, 15 relationships, dev-vs-release and gateway-as-requirement wording | none — 013/014 add tables only; `revalidated_20261027` | ok |
| Conceptual ER | Architecture DOCX image8 (`0e35cb0e44ac`) | `conceptual-core.dot` + `.json` | all 17 original entities and key attributes; the recorded `E09` removal kept as a removal | extended: `AssessmentBlueprint`, `AdaptiveEvent`, `E28`–`E30`; `E27` justification no longer calls migration 012 "prepared" | ok (20 nodes / 29 relationships) |
| Physical schema | Architecture DOCX image9 (`618b2479a1d6`) | generated: `schema-catalog.json` + `physical-schema-relationships.json` → `physical-schema.dot` | 21 original tables / 28 original FK associations retained | regenerated from a disposable PostgreSQL 17.11: `FK01`–`FK45` byte-identical, `FK46`–`FK49` appended (+60 diff lines, 0 deletions); `adaptive_event` and `assessment_blueprint` nodes; header now "34 real tables … migration 014" | ok (34 nodes / 49 relationships) |
| Logical architecture | Proposal DOCX image4 (`fa0e6f217935`) | `logical-architecture.dot` + `.json` | 13 original nodes, tier grouping, one-API-process caption | labels only: `adaptive` (batch practice), `plan` and `L15` (blueprint version + quotas), `ai` and `L17` (translation drafts) | ok (17 nodes / 27 relationships) |
| Assessment pipeline | Proposal DOCX image5 (`ef593781ce8c`) | `assessment-lifecycle.dot` + `.json` | 8 original nodes and all 8 original transitions incl. the legacy opening bias | `+bpv` node and `P28`; `mode` and `complete` labels; graph title (the "retain configured constraints" sentence is contradicted by approved theory-area mixes 10/0/3); `E`/`P` evidence paths fixed for `P02`, `P06`, `P14` | ok (18 nodes / 28 relationships) |
| Release workflow (Mermaid) | `docs/supervisor-implementation.md` fence | Markdown fence (authored) | fence text unchanged | nothing edited; now **rendered** to `docs/diagrams/rendered/supervisor-implementation-lifecycle-and-confidentiality.svg` | ok |
| Affected-schema excerpt (Mermaid) | `docs/ux-simplification-audit-20261023.md` fence | Markdown fence (authored, historical) | fence text unchanged, still labelled a three-entity excerpt | now rendered to `rendered/ux-…-after-migration-012.svg` | ok |
| Sprint roadmap | Proposal DOCX image2 (`ca2518ad1f51`) | PNG only | unchanged | none — historical schedule, not rewritten as a delivery claim | n/a |
| Rejected redraws (10) | `_docread/rejected_versions/*` | PNG only | retained as audit references | none — never used as a baseline | n/a |

No diagram disappeared, was replaced, or lost an element. `scripts/validate_diagrams.py` is the guard:
it asserts the 21 original context flows are unremoved, that every `REMOVE` carries a reason, that
each ledger's node count equals the rendered node count, and that every rendered edge id, endpoint and
direction matches its ledger. Original PNGs remain in `docs/diagrams/originals/` and the DOCX originals
are untouched, so every pre-edit figure is recoverable.

---

## 4. Alignment matrix (Phase C)

| Document | Section / Diagram | Existing claim | Actual code evidence | Status | Recommended change |
|---|---|---|---|---|---|
| `docs/diagrams/README.md` | Requirement-to-diagram matrix, physical schema row | "32 application tables, 45 FKs" | `db/schema.sql`: 34 distinct tables, 49 FKs; catalog regenerated | OUTDATED | **Applied** — row now "34 application tables, 49 FKs; migrations through 014" |
| `docs/academic-reconciliation-20261023.md` | rows 21, 96 | "Full catalog: 32 tables, 45 FKs" | same as above | OUTDATED (dated 23 Oct record) | **Applied** — left intact as history; superseded by this document, which carries the current counts |
| `docs/bilingual-architecture-completion-20261023.md` | §68, §121 | "all 32 current tables, 45 FKs"; validator line "32 tables / 45 FKs … match" | same | OUTDATED (dated) | **Applied** — historical record kept; new counts recorded here and in `docs/diagrams/README.md` |
| `docs/final-integration-acceptance-20261023.md` | §198 | "`validate_diagrams.py` … 45 FKs PASS" | it did pass then; it now passes 49 | OUTDATED (dated) | **Applied** — unchanged; this document is the current gate transcript |
| `docs/diagrams/schema-catalog.json` | `constraint.type` inventory, `schema_sha256` | earlier extraction ran on PostgreSQL **18**, which lists named `NOT NULL` pseudo-constraints (`contype='n'`) and matched the 012-era schema | PostgreSQL 17.11 `pg_constraint` records only `c/f/p/u`; nullability is carried per column (`nullable`), which the ERD prints | CONTRADICTS | **Applied** — regenerated from a disposable PostgreSQL 17.11 built from current `db/schema.sql`; provenance paragraph added to `docs/diagrams/README.md` |
| `README.md` | "Persistent migration 012 remains pending owner authorization." | 27 Oct read-only check: `schema_migration` holds 001–014; owner-authorized activation recorded 25 Oct | OUTDATED | **Applied** — annotated in place with the superseding pointer; the original sentence is still readable |
| `docs/setup-and-migrations.md` | migration status through 012 | 013 (`assessment_blueprint`) and 014 (`adaptive_event`) exist and are recorded | OUTDATED | **Applied** — dated 27 Oct section added describing both migrations, the 012-pending sentences marked historical, `app.migrate` kept as the only supported command |
| `docs/learner-and-admin-manual.md` | (absent) | built-in Help exists: `HelpProvider` `frontend/src/App.jsx:84`, `HelpButton` in `Layout.jsx` + `AuthShell.jsx:33`, 10 fixed + role-conditional sections, 14 mapped route contexts, `aria-modal`/Escape/focus-restore | NOT FOUND in docs although implemented | **Applied** — "Built-in Help guide" section added, including "there is no `/help` URL to bookmark" |
| `docs/api-conventions.md` | "Implemented endpoints" table | 82 routes exist; the table omitted the 5 grading-review routes, both cumulative-profile routes, `/sessions/{id}/questions`, both translation routes and `/api/v1/ping`; one row implied `POST /api/v1/admin/question-candidates`, which does not exist (actions are `/generate`, `/{id}/validate`, `/{id}/approve`, `/{id}/reject`) | PARTIALLY MATCHES | **Applied** — missing rows added, the implied collection row corrected, and the generated inventory declared authoritative for method/path |
| `docs/diagrams/components.json` / `.dot` | Component view | `blueprint` appears in **no** architecture ledger; `s6` said "legacy adaptive" only; `r6` listed only `SelectionLog` | `services/blueprints.py` and `assessment_blueprint` drive formal assembly; `batch_adaptive.py` writes immutable `adaptive_event` rounds (`models.py:414,417-421`) | OUTDATED | **Applied** — `bp` box + `B49`–`B51`, `B52`, label updates on `s6`, `r6`, `ai`, each with `evidence` |
| `docs/diagrams/conceptual-core.json` / `.dot` | Conceptual ER | 18 entities; no blueprint, no adaptive round evidence | migrations 013/014 add both; sessions bind 0..1 frozen versions (`models.py:406-408`) | OUTDATED | **Applied** — 2 entities + `E28`–`E30` added without redrawing; `baseline_count_convention` still describes the 23 Oct original |
| `docs/diagrams/logical-architecture.json` / `.dot` | `adaptive`, `plan`, `ai`, `L15`, `L17` | "Legacy bank selection **only**", "frozen plan" without quotas, AI tasks without translation | `adaptive_engine.py:444` dispatches `batch_adaptive.advance`; `personalized_assessment.py:237-245` resolves a blueprint; `routers/admin.py:321-325` translation | PARTIALLY MATCHES | **Applied** — five label updates; no node or edge added or removed |
| `docs/diagrams/assessment-lifecycle.json` / `.dot` | graph title, `mode`, `complete`, `P02`/`P06`/`P14` evidence | "personalized formal / practice plans retain configured constraints"; two assembly modes; three end conditions; grading/candidate/retry evidence cited to `adaptive_engine.py` | `blueprints.py:23-30,68-80` approves 10 MCQ / **0 SQL** / 3 essay for theory areas; `schemas.py:21` has `FORMAL|PRACTICE|ADAPTIVE`; `batch_adaptive.py:166-189` adds stop reasons + `finalize`; grading lives in `assessment_lifecycle.py:97-121`, promotion in `ai_admin_service.py:630-670`, retry in `grading_jobs.py:13-67` | CONTRADICTS | **Applied** — title and labels corrected, `bpv` + `P28` added, three mis-attributed citations fixed (citation-only; no visual change) |
| `docs/diagrams/modules.json` / `.dot` | `s2`, `s3`, `s4`, `M21` | three module names per band | five and four real modules in those bands | PARTIALLY MATCHES | **Applied** — labels list the actual modules |
| `docs/diagrams/containers.*`, `deployment.*` | topology | 12 / 13 nodes, sandbox and worker claims | no new deployable unit, network or provider | MATCHES | Applied — `revalidated_20261027` recorded in each ledger; figures unchanged |
| `docs/diagrams/system-context.json` | 51 external flows | provider flows C16–C21, C28–C31 cover four LLM task families but not translation | `routers/admin.py:321-325` → `question_translation.py:122` is a fourth provider task | REQUIRES HUMAN DECISION (**H3**) | **Held** — proposed C52/C53 recorded in the ledger and in [academic-reconciliation-20261027.md](academic-reconciliation-20261027.md); editing the hand-authored, academically scrutinized context SVG is an owner decision |
| `docs/requirements-decisions.md` | "Formal assessments retain the 60-minute 10MCQ/2SQL/1Essay contract" (`:6-7`) | the owner-approved mix is not the only mix the code will serve | `blueprints.py:23-30,68-73` approves **10 MCQ / 0 SQL / 3 essay** for six theory areas and `test_assessment_blueprints.py:108-112,180-185` locks that behaviour; `personalized_assessment.py:237-245` applies it to single-area FORMAL sessions on blueprint-managed assessments | REQUIRES HUMAN DECISION (**H1**) | **Not applied** — the requirement is not rewritten to fit the code and the code was not changed to fit the requirement. Amendment A4 and the two resolution paths are in `academic-reconciliation-20261027.md` |
| `assessment_blueprint` rows on the activated database | "approved" | 49 seeded rows carry `approved_by = NULL`; the basis text is generated per subject area | `blueprints.py:93-114,127`; already recorded as residual gate 3 in `docs/activation-release-20261025.md:82,172` | REQUIRES HUMAN DECISION (**H2**) | **Not applied** — re-seeding with a named approver writes persistent data and changes a contract; proposed in `academic-reconciliation-20261027.md` |
| `docs/diagrams/use-cases.dot` | 20 named goals | opt-in translation-draft preparation has no goal of its own | `routers/admin.py:321-325` → `question_translation.py`; mapped as a means inside UC07/UC08 in the ledger | REQUIRES HUMAN DECISION (**H4**) | **Not applied** — a 21st goal is an authoring decision, not a factual gap |
| `docs/diagrams/components.dot` / `.json` node `s1` | "Timer, auto-submit, **configurable** duration; max 13" | true of the stored column and the session timer, not of the Administrator API | `models.py:320`, `adaptive_engine.py:410` vs `schemas.py:776-780` (`Literal[60]`) and `assessment_validation.py:12-16` | REQUIRES HUMAN DECISION (**H5**) | **Not applied** — narrowing the wording would partially undo the recorded 23 October `caption_corrections` entry; proposed replacement text is in `academic-reconciliation-20261027.md` |
| `FITAI - Documents/` (15 numbered deliverable categories) | DBCAS counterparts expected by the faculty structure | every file in all 15 folders belongs to another project (`C1SE.56_*SHFA*`, one `C1SE.56_FitnessAI_FNAI*`); DBCAS has 4 of the 15 as root originals | workspace directory listing; no DBCAS file found in categories 2, 3, 7, 8, 9, 10, 11, 12, 13, 14, 15 | REQUIRES HUMAN DECISION (**H6**) | **Not applied** — drafting eleven academic deliverables is authorship, not alignment; none was invented. The mapping table is in `academic-reconciliation-20261027.md` §1 H6 |
| `docs/supervisor-implementation.md` | §39 "189 tests", §416-418 "901 tests", §701-703 "928 tests" | current collection is 1,109 backend tests and 281 frontend tests | MATCHES (as dated historical narrative inside the file's own "earlier observations remain historical" footer) | No edit — rewriting executed-test records would destroy evidence; the current counts are stated in this document |
| `docs/diagrams/inventory.md` | "No Draw.io, Mermaid-source, PlantUML or Excalidraw files were found" | still true: `docs/diagrams/sources/` contains only `README.md`; 0 `.puml` | MATCHES (dated snapshot) | No edit; `docs/diagrams/sources/README.md` states the PlantUML gate reports `SKIP` until a real source exists |
| `package.json`, `scripts/diagrams.mjs` | (absent before this task) | Mermaid and PlantUML sources existed in documents but nothing could render or validate them; only Graphviz had a renderer | FUTURE DESIGN-NOT IMPLEMENTED | **Applied** — pinned Mermaid/PlantUML/Graphviz toolchain with `diagrams:check`, `diagrams:render`, `diagrams:setup` |
| `scripts/render_diagrams.mjs` | documented one-off renderer requiring `DBCAS_VIZ_MODULE` | now delegates to the same implementation as `npm run diagrams:render` | PARTIALLY MATCHES (documented command still valid) | **Applied** — kept as a thin shim so older instructions keep working; `DBCAS_VIZ_MODULE` remains an override |
| `CONTRIBUTING.md`, `AGENTS.md` | no mention of how to change a diagram | tooling exists | NOT FOUND | **Applied** — "Diagrams and generated inventories" section added to `CONTRIBUTING.md`; `AGENTS.md` left alone (agent policy, not contributor policy) |
| standalone SRS, UI design document, university test plan / cases / report, technical report | — | no DBCAS file exists for any of them | NOT FOUND | Recorded as NOT FOUND; contents were not invented. A standalone SRS, a test report and a separate technical report are **not** among the 15 faculty deliverable categories, so those findings are non-gaps; UI design, test plan and test case are categories 7, 8 and 9 and currently hold only another project's example. Owner decision **H6** in `academic-reconciliation-20261027.md` |
| `docs/inventory/*.json` | (absent) | interface lists maintained by hand drift silently | FUTURE DESIGN-NOT IMPLEMENTED | **Applied** — generated inventories plus `inventory:check` / `inventory:write`, explicitly *not* claimed to be auto-synchronized |
| `README.md` (root) | release / setup commands | `npm ci`, backend/frontend commands still correct; diagram commands undocumented | MATCHES for app commands, OUTDATED for diagrams | **Applied** — 27 Oct section with the four commands and the guarantees (no browser download, sandbox intact, outside the application) |

---

## 5. Diagrams-as-code toolchain (Phase D)

Pinned in `package.json` + `package-lock.json` (private, non-application package; `npm ci` reproduces
it). Evidence from `npm run diagrams:setup` on this machine:

```
node 24.16.0
@mermaid-js/mermaid-cli: pinned 12.0.0, installed 12.0.0
@viz-js/viz: pinned 3.31.0, installed 3.31.0
package-lock.json: present (npm ci reproduces this toolchain)
browser: C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe (driven through Puppeteer; sandbox left enabled)
graphviz dot: not on PATH (not required; @viz-js/viz is a JavaScript Graphviz build)
java: java version "1.8.0_401"
plantuml 1.2023.13: tools/plantuml-1.2023.13.jar (sha256 e68a770f8fd386ca..., gitignored)
discovered sources: 9 DOT, 2 Mermaid, 0 PlantUML
python for validate_diagrams.py: <backend venv interpreter, resolved at runtime>
```

Design decisions and the constraints they satisfy:

- **No committed binaries.** `tools/` is gitignored; the PlantUML jar is fetched on demand by
  `npm run diagrams:setup` and only used if its SHA-256 equals
  `e68a770f8fd386ca6787589ffd70741303187ee214a075ee85a444fcd8a6da59`. Version `1.2023.13` is the last
  PlantUML line that runs on this machine's JRE 1.8, so no JDK upgrade and no elevation is needed.
- **No browser download, no sandbox weakening.** Mermaid CLI is driven with a generated Puppeteer
  config pointing at the *already installed* Edge/Chrome binary (`DBCAS_CHROME_PATH` overrides). The
  config's `args` list is deliberately empty — `--no-sandbox` is never passed.
- **Space-safe Windows paths.** Everything resolves through `import.meta.url` and `path.join`; the
  working copy sits in a directory whose path contains a space, and all gates pass from there.
  `node_modules/@mermaid-js/mermaid-cli/src/cli.js` is invoked with `process.execPath`
  rather than a `.cmd` wrapper, which `execFile` cannot run.
- **Discovery, not a list.** `scripts/diagrams.mjs` walks `docs/**/*.md` + root `README.md` for
  ````mermaid```` fences (labelled from the nearest heading, de-duplicated), `docs/diagrams/*.dot`,
  `docs/diagrams/sources/*.{mmd,puml,iuml}`. An unterminated fence is a named failure, not a skip.
- **Honest Mermaid determinism limits.** DOT output is byte-stable. Mermaid's `erDiagram` randomises
  relationship-curve control points every run — `look:classic`, a fixed `seed`, `themeVariables`
  font family and `--no-font-embed` were each tried and did not stabilise it. Non-DOT comparison
  therefore ignores only `d="..."` geometry; structure, identifiers, transforms, styles and all label
  text must match exactly, and `rendered/manifest.json` pins the SHA-256 of each source so a wording
  or cardinality change is still caught. This limit is documented rather than hidden.
- **Install failure is a reported limitation.** If Java is missing or the digest does not match,
  `setup` prints `UNAVAILABLE - …, partial configuration preserved` and the PlantUML gate reports
  `SKIP`; nothing claims a successful install it did not achieve.

Commands: `npm run diagrams:check` (validate + compare, writes nothing), `npm run diagrams:render`
(write SVGs + manifest), `npm run diagrams:setup` (report + fetch verified jar),
`npm run inventory:check`, `npm run inventory:write`.

---

## 6. What was edited in living documents, and why it was safe

Only objectively verifiable content changed: broken or missing links, endpoint names, executable
commands, schema counts, and statements contradicted by the code. No requirement was deleted because
the implementation differs; no code was touched to make a document agree.

`README.md`, `CONTRIBUTING.md`, `docs/api-conventions.md`, `docs/learner-and-admin-manual.md`,
`docs/setup-and-migrations.md`, `docs/diagrams/README.md`, `docs/diagrams/sources/README.md`,
`docs/diagrams/inventory/README.md` (new), 5 diagram ledgers + their `.dot` sources, the regenerated
schema artifacts, `scripts/validate_diagrams.py`, `scripts/render_diagrams.mjs`,
`scripts/diagrams.mjs` (new), `scripts/generate_schema_catalog.py` (new),
`scripts/generate_route_inventory.py` (new), `scripts/python.mjs` (new), `scripts/inventory.mjs` (new),
`package.json` (new), `package-lock.json` (new), `.gitignore`.

---

## 7. Generated vs authored, and drift detection (Phase H)

| Artifact | Kind | Producer | Drift detection |
|---|---|---|---|
| `docs/diagrams/schema-catalog.json`, `physical-schema-relationships.json`, `physical-schema.dot` + SVG | Generated | `scripts/generate_schema_catalog.py` against a **disposable** PostgreSQL 17.11 (it refuses any target that already holds rows) | `validate_diagrams.py` re-renders the DOT from the catalog and compares byte-for-byte; FK ids already in use are preserved, new ones appended |
| `docs/diagrams/rendered/manifest.json` | Generated | `npm run diagrams:render` | sources set must match exactly, else `FAIL` |
| every other `.dot` + `.json` ledger, `system-context.svg` | Authored | hand-maintained | ledger node count must equal the rendered node count; ids, endpoints, directions and labels asserted against the SVG |
| `docs/inventory/api-routes.json` (82 routes) | Generated | `scripts/generate_route_inventory.py` (static AST; no import, no DB, no network) | `npm run inventory:check` compares both content and the recorded source digests |
| `docs/inventory/frontend-routes.json` (21 routes) | Generated | same script, line-addressed scan of `<Route>` elements in `App.jsx` | same |

These inventories are **not** automatically synchronized with code. They are regenerated when someone
runs `inventory:write`, and `inventory:check` is what makes silence visible. Response schemas, roles
beyond the declared guard, status codes and domain rules remain authored in `docs/api-conventions.md`.

---

## 8. Validation report (Phase K)

Executed on 27 October 2026 after every edit:

| Check | Result |
|---|---|
| `npm run diagrams:check` | `EXIT=0`, reproduced twice in a row; `checked 9 Graphviz DOT, 2 Mermaid and 0 PlantUML source(s); ledger and DDL validation passed`; `PASS: 10 diagram model/render inventories; 34 tables, 49 foreign keys, schema.sql and 14 migration fingerprints match` |
| `npm run diagrams:render` twice | `EXIT=0` both times; **11 of the 12 SVGs are byte-identical across consecutive runs** and `rendered/manifest.json` is unchanged. The one exception is the Mermaid `erDiagram` excerpt, whose relationship curvature is randomised by Mermaid's ER renderer — a documented limitation, not drift: the text, structure and identifiers are identical, only path geometry differs, which is exactly the difference `diagrams:check` ignores in its skeleton comparison. All nine DOT renders are byte-stable, as is the Mermaid flowchart. |
| Preservation replay | generator reproduces the previously authored ERD from the old catalog with `--verify --keep-header` → "unchanged"; FK ledger diff is `+60 / -0` |
| Negative test — broken DOT | `scripts/_probe.dot` with `digest broken {` → `FAIL: scripts/_probe.dot: Graphviz rejected the source: …`, `EXIT=1`; probe deleted afterwards |
| Negative test — route drift | one comment appended to `backend/app/routers/auth.py` → `docs/inventory/api-routes.json: does not match its sources (changed contents: backend/app/routers/auth.py)`, `FAIL`, `EXIT=1`; file restored (`git diff --quiet` clean) and `inventory:check` passes again |
| Frontend unit tests | `npx vitest run` → 35 files, **281 passed**, 29.84 s |
| Backend collection | `python -m pytest --collect-only -q` → **1109 tests collected** |
| Playwright E2E | not re-run — no application source changed in this task; the 26–27 October closure (212 executions, 0 failures) stands |
| Markdown links | **211 relative links across 35 project documents resolve to existing files, 0 broken** (scanned with a throwaway script over `README.md`, `CONTRIBUTING.md`, all of `docs/*.md`, `docs/diagrams/*.md`, `docs/inventory/*.md` and `docs/remediation/*.md`; external `http(s)` and in-page anchors are skipped). The two documents linked from `README.md` are this file and [academic-reconciliation-20261027.md](academic-reconciliation-20261027.md). |
| Diagrams present | 9 `.dot`, 10 + 2 SVGs, 11 original PNGs, `originals/`, `sources/`, `rendered/` all present; no figure removed |
| Persistent database | read-only inspection only; no writes, no migration execution, no volume touched |
| Application behaviour | unchanged: `git status` shows no file under `backend/app/` or `frontend/src/` |

`npm run diagrams:check` is not a correctness oracle for architecture. It proves the sources parse,
the renders match the committed SVGs, and the ledgers agree with the SVGs and the DDL. Whether a
relationship is *semantically* right is established by the `evidence` citations in Section 2 and 4,
each read from the file and line it names.

---

## 9. Git state

No push, no tag, no force operation, no rebase. Local commits created by this task are listed in
`academic-reconciliation-20261027.md` §4 together with what remains deliberately uncommitted pending
owner review. Academic originals and `FITAI - Documents/` are outside the repository and unchanged.

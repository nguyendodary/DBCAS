# Word-document discrepancy list v2 — before editing (2026-11-08)

Scope: the three **original English v1.1** academic documents, compared
against the shipped project. This list replaces the earlier
`docs/qa/doc-discrepancies.md`, which was written for the rejected v1.2
rebuild. No document has been edited yet in this step.

## Method and sources of truth

| Evidence | What was read |
| --- | --- |
| `docs/qa/schema-introspection.json` | PostgreSQL 17 introspection of `db/schema.sql`: **41 tables, 293 columns, 59 foreign keys, 87 indexes, 0 enum types, 19 migrations** |
| `docs/qa/project-facts.json` | Compose services/ports, OpenAPI (**82 paths / 93 operations**), frontend routes (**23**), Admin nav (**5**), OAuth providers, sandbox, Prompt Builder, Evaluator, result flows, question count, sources |
| `docker-compose*.yml`, `backend/app/services/practice_*.py`, `evaluation_pipeline.py`, `prompt_builder.py`, `backend/app/routers/*`, `frontend/src/App.jsx`, `frontend/src/components/Layout.jsx` | Runtime behaviour cited in the “Project really has” column |
| `_review/docx-v2/{proposal,architecture,database}.txt` and `.json` | Full text, tables and image order of the three v1.1 originals |
| `docs/qa/doc-v2-original-diagrams/*.png` | The exact embedded diagram files, extracted from the originals |

The originals are English and remain English. The fixes below are **content
corrections only**; no section, heading, numbering, style, table style,
header/footer, TOC or caption format is to be redesigned.

## Summary

| Type | Items |
| --- | --- |
| Wrong fact | 11 |
| Missing content | 7 |
| Extra/retired content | 6 |
| Outdated version metadata | 3 |
| **Total distinct items** | **27** |

Many wrong statements recur in several places (for example “36 tables”
appears 1× in the Proposal, 14× in the Architecture and 1× in the Database
document; the 13-question/60-minute contract appears throughout). Each row
below names the section; the fix is applied at **every** occurrence in that
section group, not only the quoted one.

## Discrepancies

| # | Document | Section | Original says | Project really has | Fix |
| --- | --- | --- | --- | --- | --- |
| P1 | Proposal | §6.2 Project Scope, Table 6, §7.1 Feature 7, §7.2 FR-06/FR-15, §9, §12.2–12.4, Table 17 | Two session types: **FORMAL** (new standard contract **13 questions / 60 minutes / 10 MCQ / 2 SQL / 1 essay**) and **PRACTICE** (exactly 1, 2, 3, 5, 10 or 13 questions). Administrators configure assessments. | Only **learner-defined practice**: learner picks concepts, difficulty bands and an exact count **1–20 (default 5)**; source `bank` or `ai`; session window **30 minutes**; no formal/prebuilt exam and no admin exam creation. | Remove the FORMAL/PRACTICE split, the 13/60 contract and the 10/2/1 mix. State the single practice flow and 1–20/30-minute rules. |
| P2 | Proposal | §7.2 Table 8, FR-06 `Adaptive Assessment Builder` | Administrator configures assessments with target concepts and a result-release policy; publishes/closes assessment versions. | Admin has **five screens**: Cohort overview, Grading review, Accounts, Question bank/CLO authoring, System settings. There is no exam builder. Result flow is **one global `system_setting.result_flow`** (`IMMEDIATE` / `HUMAN_VERIFIED`), not per assessment. | Replace FR-06 with the real admin capability (curriculum, bank, accounts, grading review, global result flow). |
| P3 | Proposal | §7.2 Table 8, FR-15 `Adaptive Question Selection` | Adaptive delivery: three basic MCQs open the session, band moves one step per decision, mix served MCQ → SQL → essay; AI-generated formal mode and session-scoped storage. | Practice plan is assembled and frozen before question one; exact count is met from the validated bank, with per-type targets when `source=ai`; **SQL is always bank-only**; one `bank_mixed` notice if AI cannot fill the plan. No adaptive engine. | Rewrite FR-15 as deterministic practice-plan assembly and the bank/AI rules. |
| P4 | Proposal | §7.1 Table 7; §14 Table 17 | “Personalized formal and practice assessments”; “administrator portals for … human-verified result release, and cohort performance”. | Practice sessions only; admin still reviews human-verified results and sees cohort statistics, but does not create exams. | Keep the real admin review/cohort capabilities; delete formal-exam wording. |
| P5 | Proposal | §10 Table 12 Technology Stack | “PostgreSQL 17 database (36 tables)”. | **41 tables / 293 columns / 59 FKs / 87 indexes / 19 migrations**. | Replace “36 tables” with 41 (and the verified counts where the table already lists them). |
| P6 | Proposal | §12.1 Figure 2 System Context Diagram | Learner and Administrator exchange assessment/registration/auth flows; LLM Provider receives “Essay evaluation requests”, “Gap explanation requests”, “CLO/Concept mapping requests”. Only three external boxes. | Actors: Learner, Administrator. External systems: LLM Provider (two-AI pipeline), **Google/GitHub OAuth**, **email delivery (SMTP)**. The system is one black box. Flows are practice setup/answers/results, OAuth sign-in, password-reset mail, prompt/evaluation calls. | Redraw in the original style (title, actor rectangles, system oval, labelled arrows, legend); add the two missing external systems and correct labels. Keep the original size/placement/caption. |
| P7 | Proposal | §11.2 Sprint 5 roadmap | “Build administrator cohort overview API” (real) but the surrounding sprint text still describes formal/adaptive assessment work. | Cohort statistics endpoint exists (`/api/v1/admin/analytics/cohort`); practice assembly is real, adaptive engine is not. | Correct only the sprint bullets that name formal/adaptive behaviour. |
| P8 | Proposal | Cover, revision history | “Version 1.1”; revision history ends at 1.1 (30/10/2026). | New working revision is 1.2 (08/11/2026). Approver/date placeholders must stay. | Set cover to 1.2 and add one revision-history row in the existing format; do not invent approver names or dates beyond the document date. |
| A1 | Architecture | §1.2 Table 3/4, §1.3 Figure 1 Use Case Diagram | UC09 “Configure adaptive assessments”, UC12 “Take timed adaptive assessment”, UC13/14/15 formal assessment flow; 18 use cases drawn. | Only learner-defined practice. Admin cannot create exams. The real learner flow is: choose concepts/bands/count/source → start practice → answer MCQ/SQL/essay → submit → view result, competency profile and gaps. | Correct the UC names/descriptions and redraw Figure 1 with the same ellipse/actor/system-box style and the same caption. |
| A2 | Architecture | §2 Figure 2 System Context Diagram | Same three-external-box context as Proposal P6; labels include adaptive/formal assessment. | Same real context as P6. | Apply the same context correction/redraw as P6, sized for this document. |
| A3 | Architecture | §3.1 Tables 6–10 actor/entity descriptions | Learner “takes adaptive assessments”; Administrator “defines … adaptive assessment rules”; system “selects formal questions adaptively”. | Learner takes learner-defined practice; Administrator curates CLOs/concepts/bank/rubrics, manages accounts, reviews human-verified results, reads cohort statistics; system assembles a frozen practice plan. | Correct the actor/entity responsibilities; keep table structure. |
| A4 | Architecture | §3.2 Tables 19 and 22 (operational use cases) | Table 19 “Configure Adaptive Assessment Sessions” (13/60/10-2-1, publish/close versions); Table 22 “Take a Personalized Adaptive Assessment Session” (FORMAL/PRACTICE, frozen assessment contract). | Table 19's capability does not exist as written; the Admin configures the **global result flow** and curates content. Table 22 is one practice flow: concepts, bands, count 1–20, source, 30-minute expiry, frozen plan. | Rewrite both use cases in place; keep IDs, table captions and column structure. |
| A5 | Architecture | §4.1 Container Diagram text + Figure 3 | API “personalized plan assembly and formal adaptive selection”; “36 tables”; “assessment and question snapshots, assessment blueprints, adaptive decision notices”. | Practice plan assembly only; **41 tables**; no new assessment/blueprint rows; selection log/adaptive event remain audit tables for historical/legacy data. | Correct the prose and the container box text; do not restructure the C4 diagram. |
| A6 | Architecture | §4.2 Component Diagram + Figure 4 | Figure 4 has “Assessment Controller”, “Assessment Service / 60-min timer, auto-submit, 13-question cap”, “Adaptive Engine Service / next-question selection”, “Assessment Repository (Assessment, AssessmentConcept)”. | Real components: practice setup/start, frozen plan assembly, bank selection + AI generation (MCQ/essay only; SQL bank-only), grading (MCQ key, SQL sandbox, essay evaluator), competency/gap, admin review. No adaptive engine. | Redraw Figure 4 with the real controller/service/repository components, same C4 box/grey-band style, same size/caption. |
| A7 | Architecture | §5 Module View + Figure 5 | “Assessment / Session + Adaptive Service”; “Analytics Controller”; “Competency + Gap Service”; “LLMCache” as a shared dependency. | Practice module (setup, assembly, delivery), Grading/Evaluation (Prompt Builder → Evaluator), Competency & Guidance, Curriculum, Question Bank, Identity & Access; PostgreSQL, LLM gateway, SQL sandbox. `llm_cache` is a table, not a module. | Redraw Figure 5 with the real functional modules; keep the original tile layout/colors. |
| A8 | Architecture | §6 Allocation View + Figure 6 | Application Server does “adaptive selection”; cached LLM responses. | Application Server assembles practice plans and runs grading; `llm_cache` is used by the gateway. | Correct the box text; keep the deployment layout. |
| A9 | Architecture | §7 ERD text, Figure 7 ERD, Figure 8 TRD | “36 tables”; ERD has **17 entities / 23 relationships**; TRD has **21 tables**; assessment/blueprint shown as active. | **41 tables**, 59 FKs. Four legacy tables exist only for historical rows: `assessment`, `assessment_concept`, `assessment_question`, `assessment_blueprint` (migration 019 closes published exams; `assessment_session.assessment_id` nullable since migration 018). | Replace “36 tables” everywhere. Redraw the ERD at the original abstraction (core entities, key attributes, relationship diamonds, 1/N/M), marking the four legacy tables. Redraw the TRD at the original style, marking legacy tables and showing the real FK/cardinality relationships. |
| A10 | Architecture | §3.3 quality scenarios (Tables 31–40) | Several scenarios cite “Adaptive Engine Service”, “LLMCache”, “formal adaptive delivery”, 13-question cap. | Practice plan assembly, Prompt Builder/Evaluator with fallbacks, `llm_cache`, 30-minute session. | Correct the architectural-element and response-measure cells only. |
| A11 | Architecture | §4.1 text, §7 text | “PostgreSQL 17 database (36 tables)” (14 occurrences of 36-table wording across the document). | 41 tables. | Global replacement, including figure captions/notes if present. |
| D1 | Database | §Database Diagram → Table Overview, Table 1 | 36 tables listed; no `assessment_question`, `evaluation_record`, `grade_edit_audit`, `refresh_session`, `system_setting`. | **41 tables**. The five missing tables are real and active (assessment_question is legacy but must be listed). | Add the five rows to the existing Table Overview in the same format and column order; update the total. |
| D2 | Database | §Database Design for Sprint, all 36 table sections | The dictionary is accurate for 36 tables but: `concept.keywords` and `concept.learning_objectives` are `TEXT[]`, not `TEXT`; `question.original_locale` is missing; `assessment_session.assessment_id` is shown `Not` null although migration 018 made it nullable; `assessment`/`assessment_blueprint` are described as active. | Introspection: array types; `original_locale varchar(20) not null`; `assessment_id` nullable; assessment tables legacy. | Correct the three column rows; add a short legacy note in the existing table list/descriptions, not a new section. |
| D3 | Database | §3 Assessment, AssessmentConcept, AssessmentSession, AssessmentBlueprint, AdaptiveEvent descriptions | Assessment is “configured by an administrator … family/version lineage”; AssessmentConcept holds targets/passing benchmark; sessions bind a blueprint; adaptive decisions are part of the live flow. | Assessment/AssessmentConcept/AssessmentBlueprint/AssessmentQuestion are **legacy**, retained for historical rows; no current API creates them. `assessment_session.assessment_id` is nullable. `adaptive_event`/`selection_log` remain audit tables. | Mark the four tables legacy in their existing sections; describe the live session as learner-defined practice. |
| D4 | Database | §3 table descriptions and §Hardware and Software Requirements | 13/60 formal contract, 10/2/1 mix, “36 tables”, timer semantics tied to formal assessments. | Practice count 1–20 (default 5), 30-minute expiry, no fixed mix; 41 tables. | Correct every occurrence; keep section order and table captions. |
| D5 | Database | Figure 1 Entity Relationship Diagram | 17-entity Chen ERD; assessment/blueprint active; no legacy marking; missing account_identity, account_role_audit, question_translation, session_question_plan, evaluation_record, system_setting, etc. | Core real model plus four legacy tables. | Redraw in the same Chen notation/key ellipses/relationship diamonds/legend; mark legacy entities with the existing legend style (a faded fill and one legend entry). Same landscape size/caption. |
| D6 | Database | Figure 2 Table Relationship Diagram | 21-table physical diagram; no `system_setting`, `evaluation_record`, `grade_edit_audit`, `refresh_session`, `assessment_question`; assessment tables not marked legacy. | 41-table schema; 59 FKs. | Redraw at the original density/style; show the real FK lines/cardinality and the four legacy tables clearly separated/marked. Same landscape size/caption. |
| D7 | Database | Cover, revision history, TOC | Version 1.1, revision history ends at 1.1. | Working revision 1.2 (08/11/2026). | Cover 1.2; one new revision row in the original format; no invented approvers. |
| D8 | Database | Table 1 / §1 Scope | “36 tables of the DBCAS schema”. | 41 tables. | Replace and keep the surrounding sentence. |
| X1 | All three | TOC, list of figures, list of tables, page numbers | Reflects v1.1 (before diagram replacement and text edits). | Same headings/captions; page numbers may shift slightly after text corrections. | Update fields only (Word COM) after editing; do not restyle or renumber. |
| X2 | All three | Revision history / approvals | Placeholders only. | No real approver names/dates are known. | Keep every placeholder; add only the document-date row if the original format has one. |

## Diagram evidence

The original diagram files were extracted from `word/media/` and saved as PNG
under `docs/qa/doc-v2-original-diagrams/` (exact bytes, not screen captures):

| Document | Figure | Original file | Element count in the original |
| --- | --- | --- | --- |
| Proposal | Figure 2 System Context | `proposal-fig2-system-context.png` | 3 actor boxes + 1 system oval + 21 labelled arrows + legend |
| Architecture | Figure 1 Use Case | `architecture-fig1-use-case.png` | 2 actors + 18 use-case ellipses + system box + note |
| Architecture | Figure 2 System Context | `architecture-fig2-system-context.png` | Same image as Proposal Figure 2 |
| Architecture | Figure 3 Container | `architecture-fig3-container.png` | 2 persons + 4 containers + 2 data stores + 1 external system |
| Architecture | Figure 4 Component | `architecture-fig4-component.png` | 7 controllers + 7 services + 7 repositories + 2 infrastructure components + database + sandbox + external LLM |
| Architecture | Figure 7 ERD | `architecture-fig7-erd.png` | 17 entities, 17 key ellipses, 23 relationship diamonds, legend |
| Architecture | Figure 8 TRD | `architecture-fig8-trd.png` | 21 tables with PK/FK/type columns, crow’s-foot legend |
| Database | Figure 1 ERD | `database-fig1-erd.png` | Same ERD image as Architecture Figure 7 |
| Database | Figure 2 TRD | `database-fig2-trd.png` | Same TRD image as Architecture Figure 8 |

The original ERD and TRD are **landscape full-page** figures (Architecture
sections 7; Database “Database Diagram” section). The context figures are
portrait, about 6.1 in wide. The replacements keep those sizes and
placements.

## Legacy / retired tables (must not be hidden)

| Table | Why it is legacy |
| --- | --- |
| `assessment` | Prebuilt exam definitions; migration 019 sets every published exam to `closed`; no current API creates one. |
| `assessment_concept` | Target-concept weights of retired exam definitions. |
| `assessment_question` | Curated exam question pool (migration 017); unused by learner-defined practice. |
| `assessment_blueprint` | Blueprint of retired formal definitions; `assessment_session.assessment_id` became nullable in migration 018. |

These four tables stay in the schema/ERD and are labelled as legacy. Active
tables such as `selection_log`, `adaptive_event`, `result_release_event`,
`grade_review`, `grade_edit_audit`, `evaluation_record`, `system_setting`,
`session_start_request`, `session_question_plan`, `sql_test_dataset` and
`llm_cache` are **not** labelled legacy.

## What has not been changed in this step

- No `.docx` file was edited.
- No original page layout, header/footer, style, numbering or TOC field was touched.
- No approver, date or name was invented.
- The rejected v1.2 files stay in `_review/rejected-v1.2/` (git-ignored) and
  are not used as a source.

## Resolution (2026-11-08)

All 27 items above were fixed in the three in-place `ver1.2` files; none of the
original layout, headers/footers, styles, numbering, captions or revision
format was rebuilt.

| Document | Applied changes | Figures |
| --- | --- | --- |
| Proposal | 61 text corrections; email-delivery bullet cloned in the existing list format; cover/revision 1.2 | Figure 2 redrawn (OAuth + email added, 24 labelled flows) |
| Architecture | 68 text corrections; Table 54 completed to 41 tables; 4 legacy tables marked | Figures 1–8 redrawn at original extents (context shares the Proposal file) |
| Database | 17 text corrections; Table Overview to 41 rows; 5 missing table sections added; `original_locale` added; `assessment_id` nullable; legacy descriptions | Figures 1–2 redrawn (same ERD/TRD files) |

Verification: `npm run docs:check` (schema/data dictionary exactness, English
language, retired statements), Word COM open/page-count check, before/after
contact sheets in `docs/qa/doc-v2-verification/`, diagram element table in
`docs/qa/doc-v2-diagram-elements.md`.

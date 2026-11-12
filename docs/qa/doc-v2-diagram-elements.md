# Diagram element check — v1.2 figures vs project evidence

Every figure below was redrawn in place from repository evidence, at the
original canvas ratio, extent, notation and caption. “Original” counts are
from the exact embedded v1.1 images saved in
`docs/qa/doc-v2-original-diagrams/`.

## Data sources

| Evidence file | What it proves |
| --- | --- |
| `docs/qa/schema-introspection.json` | 41 tables, 293 columns, 59 FKs, 87 indexes, 0 enums, 19 migrations |
| `docs/qa/project-facts.json` | 6 Compose services (+ QA-only `qa-ai`), 82 OpenAPI paths / 93 operations, 23 frontend routes, 5 Admin nav items, 2 OAuth providers, sandbox limits, result flows, 1–20 count |
| `backend/app/services/practice_service.py`, `practice_config.py`, `evaluation_pipeline.py`, `prompt_builder.py` | Learner-defined practice, 1–20 count (default 5), 30-minute expiry, bank/AI source, bank-only SQL, Prompt Builder → Evaluator |
| `backend/app/routers/*`, `frontend/src/App.jsx`, `frontend/src/components/Layout.jsx` | Five Admin screens and the real controller boundaries |
| `db/schema.sql` | Real PK/FK constraints and legacy table definitions |

## Proposal Figure 2 — System Context (`proposal-fig2-system-context.png`)

| Element | Original | New | Evidence |
| --- | --- | --- | --- |
| Human actor boxes | 2 (Learner, Administrator) | 2 | Same roles as `account_role` (Learner/Administrator) |
| External system boxes | 1 (LLM Provider) | 3 (LLM Provider, OAuth Providers, Email Service) | `project-facts.json` OAuth providers [Google, GitHub]; `mail.py` / SMTP settings |
| System oval | 1 (DBCAS) | 1 | — |
| Labelled flows | 21 | 24 (learner 8, admin 7, LLM 6, OAuth 2, email 1) | Practice, results, competency, content curation, grading review, OAuth, password-reset mail |
| Legend | 3 entries | 3 entries (System / Actor / external system / Interaction) | Same legend grammar |

Removed claims: formal/adaptive assessment, 13-question/60-minute contract,
assessment builder, per-assessment result policy.

## Architecture Figure 1 — Use Case (`architecture-fig1-use-case.png`)

| Element | Original | New | Evidence |
| --- | --- | --- | --- |
| Actors | 2 | 2 | Learner, Administrator |
| System boundary | 1 | 1 | — |
| Use-case ellipses | 18 | 18 | Same UC01–UC18 set |
| Renamed use cases | UC09 “Configure adaptive assessments”, UC12 “Take timed adaptive assessment” | UC09 “Configure result flow and settings”, UC12 “Take personalized practice session” | `routers/admin` settings; `practice_service.py` |
| Note | 1 | 1 | Registration before sign-in; UC13/UC14 inside UC12 |

## Architecture Figure 2 — System Context

Same file and element table as Proposal Figure 2; drawn at the Architecture
extent (5.58 M × 4.14 M EMU).

## Architecture Figure 3 — Container (`architecture-fig3-container.png`)

| Element | Original | New | Evidence |
| --- | --- | --- | --- |
| Person boxes | 2 | 2 | Learner, Administrator |
| Containers | 4 (Web App, SPA, API, Database) | 5 (adds SQL Execution Sandbox) | `docker-compose*.yml` |
| External system | 1 (LLM Supplier) | 1 (LLM Provider API) | External REST |
| Container text | “grading, adaptive selection”, “configures assessments”, 36 tables | practice sessions, plan assembly, grading, competency; 41 tables | `routers`, `services`, schema introspection |
| Boundary/arrows | 1 dashed boundary, 6 arrows | 1 boundary, 7 arrows (API → sandbox explicit) | Compose topology |

## Architecture Figure 4 — Component (`architecture-fig4-component.png`)

| Element | Original | New | Evidence |
| --- | --- | --- | --- |
| Controllers | 7 | 7 (Auth, Practice, Curriculum, Question Bank, Analytics, Grading, Accounts) | FastAPI routers |
| Services | 7 | 7 (Auth, Practice, Curriculum, Question Bank, Competency & Gap, Grading & Evaluation, Admin & Settings) | `backend/app/services` |
| Repositories | 7 | 7 (Account, Session & Plan, Curriculum, Question, Competency, Grading, Audit & Settings) | SQLAlchemy repositories |
| Infrastructure | LLM Gateway, Sandbox Runner, PostgreSQL, LLM API, SQL Sandbox | same five | `prompt_builder`, `evaluation_pipeline`, sandbox runner |
| Removed components | Assessment Controller/Service/Repository, Adaptive Engine, Selection & Candidate Repository | — | No adaptive engine or exam builder in code |

## Architecture Figure 5 — Module View (`architecture-fig5-module.png`)

| Element | Original | New | Evidence |
| --- | --- | --- | --- |
| Top strip | 3 boxes | 3 boxes (Web UI, API entry, Backend services) | Same layout |
| Functional modules | 6 (Identity, Curriculum, Question Bank, Assessment, Grading, Competency) | 6 (Identity, Curriculum, Question Bank, **Practice**, Grading, Competency) | Practice module replaces Assessment |
| Shared dependencies | 3 (PostgreSQL, LLM Gateway, SQL Sandbox) | 3, with “LLM cache” instead of “LLMCache” | `llm_cache` table |

## Architecture Figure 6 — Allocation (`architecture-fig6-allocation.png`)

| Element | Original | New | Evidence |
| --- | --- | --- | --- |
| Nodes | Person, device, Internet, Web Server, Application Server, Database, SQL Sandbox, LLM API | same eight | Compose/deployment |
| Application Server text | “adaptive selection” | practice plan assembly | `practice_service.py` |
| Limits | 256 MB, 3 s, read-only | unchanged | sandbox configuration |

## Architecture Figure 7 / Database Figure 1 — ERD (`architecture-fig7-erd.png`)

| Element | Original | New | Evidence |
| --- | --- | --- | --- |
| Core entities | 17 | 12 (Role, Account, UserProfile, SystemSetting, CLO, Concept, Question, MCQOption, Session, Attempt, ConceptCompetency, CompetencyGap) | Core schema |
| Legacy entities | 0 marked | 4 dashed (Assessment, AssessmentConcept, AssessmentQuestion, AssessmentBlueprint) | Migration 019 closes published exams; no current API creates them |
| Key ellipses | 17 | 16 | PK of each shown entity |
| Relationship diamonds | 23 | 12 (assigned, has, defines, tagged with, offers, measured by, records, yields, diagnosed as, targets, pools, versions) | FK/PK evidence |
| Cardinalities | 1/N/M | 1/N on both ends of each diamond | `schema-introspection.json` |

## Architecture Figure 8 / Database Figure 2 — TRD (`architecture-fig8-trd.png`)

| Element | Original | New | Evidence |
| --- | --- | --- | --- |
| Table cards | 21 | 41 | `schema-introspection.json` |
| Columns shown | ~5 per card | PK, all FKs, then columns up to 7, plus “+N more columns” | `schema.sql` / introspection |
| Keys | PK/FK markers | PK/FK markers; FK cards show `→ target` | `foreign_keys` (59) |
| Legacy marking | none | 4 dashed cards with LEGACY tag | Migration 018/019 |
| Legend | 6 entries | PK, FK, legacy, 41/293/59/19 counts, domain colours | Introspection |

## Visual placement

| Figure | Extent (EMU) | Ratio | Placement |
| --- | --- | --- | --- |
| Proposal Figure 2 | 5,580,000 × 4,120,615 | 1.354 | In place, portrait, caption unchanged |
| Architecture Figure 1 | 5,580,000 × 6,138,000 | 0.909 | In place |
| Architecture Figure 2 | 5,580,000 × 4,136,285 | 1.349 | In place |
| Architecture Figure 3 | 5,238,750 × 5,143,500 | 1.019 | In place |
| Architecture Figure 4 | 8,366,760 × 5,047,488 | 1.658 | In place |
| Architecture Figure 5 | 8,193,024 × 5,084,064 | 1.612 | In place |
| Architecture Figure 6 | 4,191,000 × 4,038,600 | 1.038 | In place |
| Architecture Figure 7 | 8,124,825 × 4,191,000 | 1.939 | Landscape, unsplit |
| Architecture Figure 8 | 7,877,175 × 4,762,500 | 1.654 | Landscape, unsplit |
| Database Figures 1–2 | same two files | same | Landscape, unsplit |

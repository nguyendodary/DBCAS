# Content delta — original vs real project (2026-11-08)

Rules: keep original abstraction level. Context keeps few nodes + only
genuinely missing real actors/systems/flows. ERD keeps Chen subset
(core entities), updated to real core. TRD keeps card pattern, extended
to real tables (41). No redesign, no panel splitting.

Evidence keys: `schema-introspection.json` (41 tables, 293 cols, 59 FKs,
87 idx, 19 mig), `project-facts.json` (Compose 6+qa-ai, 82 paths, 23 routes,
5 admin nav, OAuth `[github, google]`, SMTP `mailpit:1025`, sandbox
`dbcas-sql-ephemeral:local`, 1–20 count), `system-context-model.json`
(nodes/flows + evidence), `db/schema.sql` + code (`routers/*`, `services/*`,
`App.jsx`/`Layout.jsx`).

Counts (kept / corrected / added / removed) per figure in summary below.

| Figure | Element | Original | Real project | Action | Evidence |
| --- | --- | --- | --- | --- | --- |
| Proposal Fig 2 = Arch Fig 2 Context | Actors | Learner, Administrator (2) | Same 2 (`account_role` Learner/Administrator) | keep | `account_role` in introspection |
| Proposal Fig 2 = Arch Fig 2 Context | System | DBCAS (1 oval) | Same | keep | Compose `app` + `frontend` |
| Proposal Fig 2 = Arch Fig 2 Context | External LLM | LLM Provider (1) | Same, via `LLM_BASE_URL` + Evaluator/Prompt Builder | keep | `LLM_*` env, `evaluation_pipeline.py` |
| Proposal Fig 2 = Arch Fig 2 Context | External OAuth | 0 (absent) | Google + GitHub (`/auth/oauth/{provider}/start,callback`) | add 1 box “OAuth Providers” + 2 flows | `routers/oauth.py` |
| Proposal Fig 2 = Arch Fig 2 Context | External Email | 0 (absent) | SMTP via Mailpit (`SMTP_HOST=mailpit`) | add 1 box “Email Service” + 1 flow | `services/mail.py` |
| Proposal Fig 2 = Arch Fig 2 Context | Sandbox | 0 | Ephemeral SQL via `docker.sock` (`--network none`) | add 1 flow only (no box; context stays system-level) | `ephemeral_sandbox.py` |
| Proposal Fig 2 = Arch Fig 2 Context | Learner flows (8) | Assessment requests, MCQ/SQL/Conceptual answers, View, Auth, Registration, Results, Competency & gaps, Study guidance | Practice requests, MCQ/SQL/essay answers, Result view, Auth, Registration, Practice results, Competency & gaps, Study guidance | correct 2 labels (Conceptual→essay/practice), keep 8 | `routers/practice*`, `sessions/*` |
| Proposal Fig 2 = Arch Fig 2 Context | Admin flows (8) | CLOs & Concepts, Questions, Rubrics, Assessment configuration, Learner performance, Competency analytics, AI mapping | CLOs & concepts, Questions, Rubrics, Result flow & settings, Performance, Analytics, AI mapping | correct 1 (config→result flow/settings) | `routers/admin`, settings |
| Proposal Fig 2 = Arch Fig 2 Context | LLM flows (6) | Gap explanation, Essay eval, CLO mapping, Mapping sugg, Essay results, Gap expl | Same 6 | keep | `evaluation_pipeline` |
| Arch Fig 1 Use Case | Actors/system | 2 actors, 18 ellipses UC01–UC18 | 2 actors, 18 goals (UC09/UC12 renamed in real router names) | keep 18; correct 2 titles | `App.jsx` routes, `Layout.jsx` |
| Arch Fig 1 Use Case | UC09 | Configure adaptive assessments | Configure result flow and settings | correct label | `routers/admin/system` |
| Arch Fig 1 Use Case | UC12 | Take timed adaptive assessment (13Q/60min) | Take personalized practice (1–20, default 5, expiry 30min) | correct label + note | `practice_service.py` 1–20 |
| Arch Fig 1 Use Case | Note | Registration before sign-in; UC13/UC14 inside UC12 | Same + practice note | keep | `App.jsx` guard |
| Arch Fig 3 Container | People/containers | Person boxes + Web App, SPA, API, Database + SQL Sandbox + LLM API (approx) | `frontend` Nginx :18080, `app` FastAPI :18000, `db` PG17, `mailpit`, `sandbox`, LLM | correct names/ports, keep 5-6 containers | `docker-compose.local.yml` |
| Arch Fig 3 Container | Version text | “36 tables” / “adaptive selection” | 41 tables; practice plan assembly | correct text | introspection 41 |
| Arch Fig 4 Component | Controllers/Services/Repos | 7 + 7 + 7 (with Assessment Controller, Adaptive Engine, Selection repo) | 7 Auth/Practice/Curriculum/Bank/Analytics/Grading/Accounts; no Adaptive Engine, no Assessment builder | correct: replace 3 retired with Practice equivalents; keep 7/7/7 | `routers/*`, `services/*` |
| Arch Fig 5 Module | Modules (6) | Identity, Curriculum, Question Bank, Assessment, Grading, Competency | Same but Practice replaces Assessment | correct 1 module name | `services/` |
| Arch Fig 6 Allocation | Nodes | Person, device, Internet, Web, App, DB, Sandbox, LLM (8) | Same 8 (Compose) | keep; correct “adaptive selection”→practice plan | Compose/networks |
| Arch Fig 7 = DB Fig 1 ERD (Chen) | Entities (17) | Role, Account, UserProfile, Rubric, CLO, Assessment, QuestionCandidate, Question, SQLTestDataset, Concept, AssessmentSession, SelectionLog, MCQOption, LLMCache, ConceptCompetency, CompetencyGap, Attempt | Keep 12 core (same minus retired/old, plus SystemSetting): Role, Account, UserProfile, SystemSetting, CLO, Concept, Question, MCQOption, Session, Attempt, ConceptCompetency, CompetencyGap; 4 legacy dashed (Assessment, AssessmentConcept, AssessmentQuestion, AssessmentBlueprint) | keep 12 core shape; correct: drop 5 non-core (Rubric, QuestionCandidate, SQLTestDataset, SelectionLog, LLMCache stay as TRD-only, not ERD); add SystemSetting + 4 legacy | 41 tables; legacy = migration 019; ERD is subset by design |
| Arch Fig 7 = DB Fig 1 ERD | Keys/diamonds | 17 key ellipses, ~20 diamonds (assigned, defines, has…) | 16 key ellipses, 12 diamonds (assigned, has, defines, tagged with, offers, measured by, records, yields, diagnosed, targets, pools, versions) | correct cardinalities/verbs to FK reality | FK ledger 59 |
| Arch Fig 8 = DB Fig 2 TRD | Cards (21) | ~21 table cards, ~5 cols/card | 41 cards, PK/FK/type/null per card (full schema) | extend to 41; add LEGACY tag on 4; legend + 41/293/59/19 counts | introspection; same card grammar |
| Proposal Fig 3 Logical | 4 tiers | Presentation, App/Services, Data, External AI+Sandbox | Same 4 tiers; Service boxes: Practice replaces Assessment/Adaptive | correct Tier-2 box names (6 boxes) | `services/` |
| Proposal Fig 4 Pipeline | Flow | Opening 3 MCQ (levels 1–2) → grade → evidence → adaptive (3/3 harder…) → complete cap ≤13 / 00:00, target 10/2/1 | Opening + practice plan (1–20, default 5) → grade → evidence → selection → complete (expiry 30min, no fixed 13-cap) | correct counts/caps; keep 8-box loop + fallback | `practice_service.py` |
| Proposal Fig 1 Roadmap | Grid | 6 tracks × Sprint 1–5, July 28–Dec 26 2026 | Historical plan (keep as-is) | keep (historical, not a delivery claim) | README |

Summary counts (kept / corrected / added / removed, by row above):

- Context: kept 10 (2 actors + DBCAS + LLM + 6+8 flows structure), corrected 3 labels,
  added 2 boxes (OAuth, Email) + 4 flows, removed 0 (no box for sandbox).
- Use Case: kept 16, corrected 2 (UC09/UC12), added 0, removed 0.
- Container: kept 6, corrected 4 (names/ports/text), added 0, removed 0.
- Component: kept 18, corrected 3 (Assessment/Adaptive/Selection → Practice),
  added 0, removed 3 retired claims.
- Module: kept 5 modules + 3 shared, corrected 1 (Assessment→Practice).
- Allocation: kept 8 nodes, corrected 1 text.
- ERD: kept 12 core entities + all diamond/ellipse notation, corrected 5
  removals (non-core) + 1 add (SystemSetting) + 4 legacy adds, removed 5
  non-core entities from ERD (they stay in TRD).
- TRD: kept 21-card pattern, corrected types/nullability, added 20 cards
  (21→41) + legacy tags + counts, removed 0.
- Logical/Pipeline/Roadmap: kept shapes, corrected Tier-2/pipeline counts,
  added 0, removed retired exam-builder claims in text (diagrams keep boxes).

No element is invented; every added/corrected name is in the evidence column.
If the original shows a subset, the redraw shows the same subset kind
(core ERD) or full list (TRD) — not a new structure.

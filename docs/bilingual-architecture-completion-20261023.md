# DBCAS bilingual UX and diagram completion — 23 October 2026

## A. Executive verdict

**PARTIALLY COMPLETE.** Bilingual authoring/display improvements and ten editable diagram companions are implemented. All prior work was preserved. Full PostgreSQL 17/Docker sandbox and standard release E2E acceptance remain blocked by the environment. The four university originals remain unchanged; precise academic amendments and portable figures are supplied here, not silently applied to those originals.

### Recovered state and gaps before editing

- Branch `main`; HEAD `5db597930cb512879ad1b9c577e6e88d33962b47`.
- Recovered tree: 34 modified tracked files, six new files, no deletions. The earlier UX audit describes its own earlier clean starting state; it was not overwritten as this task's baseline.
- Migration 012, original-language persistence, optional reviewed translations, named concept controls, structured rubrics, preview, role protections and prior tests were already present. They were reused.
- Remaining UX gaps: manual language selection, stored-reviewed preview requiring a redundant review checkbox, fixed visible exam/evidence language, and no display-language request retry.
- Diagram gap: the **current root DOCX retains 21 detailed context flows**. The collapsed four-connection redraw is in rejected versions. No restoration over the current originals was needed.
- Meaningful diagram errors: candidate dispatch attributed to adaptive selection; nonexistent repository class names; an assessment-to-candidate ER relationship absent from the schema; sandbox network-disabled wording; omitted personalized plans, publication and manual takeover branches.

## B. Bilingual UX

- One editor accepts Vietnamese or English. Recognizable prose is detected conservatively, including normalized Vietnamese Unicode; inline code is ignored. Ambiguous short/code-only input retains the current content-language value, which the administrator can correct. This is a heuristic convenience, not a claim of universal language detection.
- Existing originals are never relabeled. The original prompt/options/rubric remain the grading source; `question.original_locale` records their language. Existing English rows keep the default and existing translation fingerprints.
- Optional manual translations remain separate `question_translation` rows. Missing, unsaved draft/needs-review, reviewed and stale states are explained. Unsaved translation edits are not persisted unless the administrator explicitly confirms review. Stored current reviewed translations can be previewed without reapproving or rewriting them.
- Source changes invalidate stale translations through the existing hash contract. MCQ associations use stable option labels/IDs. SQL, identifiers, datasets, expected rows, score boundaries and rubric identifiers are shared technical/scoring data.
- Menus and controls follow the UI language. Exam/evidence reads now accept `display_locale=en|vi` and show **reviewed translations captured in the question snapshot**, with a labeled original fallback. The recorded session locale remains immutable. Personalized snapshots freeze with the plan; legacy snapshots are captured when served. Later bank edits/translations do not retrofit an existing snapshot.
- Language projections preserve local drafts and the authoritative countdown, ignore obsolete responses, recover after visibility refresh, and offer a localized retry when the requested display cannot be loaded. Evidence explains that official grading feedback keeps its recorded language; no narrative translation is fabricated.
- Bank titles follow current reviewed translations, with original fallback. Search includes current reviewed translated prompts and excludes stale ones; editing still opens the original source. Mobile bank actions wrap within the viewport.
- Legacy evidence without a captured question snapshot uses the known original language only; later bank translations have no historical provenance and are not projected retroactively. No missing snapshot is backfilled.
- Configuration inspection found an existing general LLM provider but **no approved translation task**. No live provider was called. No automatic translation endpoint or generated approval was invented. Original-only saves and optional human-reviewed translation work without a translation provider.

### Changes in this follow-up

| Files | Before → after |
|---|---|
| `frontend/src/components/QuestionAuthoring.jsx` | Required up-front manual choice → inferred prose language with correction; meaningful translation states; stored reviewed preview without duplicate approval |
| `backend/app/routers/sessions.py`, `services/adaptive_engine.py` | Session-locale-only read → validated optional display projection; ownership, timeout and release guards retained |
| `frontend/src/pages/ExamPage.jsx` | Menu-only switching → safe captured-content projection, retry and refresh recovery; answer/clock retained |
| `frontend/src/pages/EvidencePage.jsx` | Pinned prose display → requested reviewed projection; official feedback language explained |
| `backend/app/schemas.py`, `repositories.py`, `services/question_service.py`, `frontend/src/pages/admin/AdminQuestionsPage.jsx` | Source-only bank titles/search → read-only current-reviewed prompt map and search, preserving canonical writes and source editing; responsive action wrapping |
| `backend/app/services/evidence_context.py` | Legacy missing-snapshot reads could use later bank translations → original-only fallback; captured snapshots and canonical grading views unchanged |
| `frontend/src/i18n/en.json`, `vi.json` | Matching localized detection, review, content and error notices |
| Question authoring/localized exam/learner tests and E2E | Added detection, reviewed preview, stale/current behavior, language projection, answer preservation, failure/retry and request-contract checks |
| `docs/diagrams/`, `scripts/render_diagrams.mjs`, `scripts/validate_diagrams.py` | Inventoried originals → editable faithful companions, exhaustive relationship ledgers, DDL-bound catalog and validation |

The earlier audit contains the complete administrator/learner complexity review. This follow-up addresses its remaining language gaps; it does not claim live browser coverage of every administrator and learner route.

## C. Architecture diagram inventory

The scan covered 43 DOCX files, 19 PDFs and relevant Markdown/raster/vector/editable-source formats across the authorized workspace. Ten current raster diagram types, one historical roadmap and ten rejected raster variants were identified, plus two distinct Mermaid models in three occurrences. PDF renderings and repeated images are aliases, not new systems. Unrelated FITAI/SHFA documents are excluded from DBCAS requirements.

The [requirement-to-diagram matrix](diagrams/README.md) lists every diagram type, source and classification. The [full inventory](diagrams/inventory.md) and [machine-readable locations](diagrams/inventory.json) identify individual variants. There is no evidence justifying a star schema or invented DFD/sequence diagrams. Eleven current/historical original figures are retained unchanged under `docs/diagrams/originals/`.

## D. System Context comparison

| Version | Actors / systems | Relationships |
|---|---:|---:|
| Original and current root university diagram | 4 | 21 directed flows |
| Rejected collapsed redraw (not the baseline) | 5 | 4 broad bidirectional connections |
| Updated editable companion | 6 | 51 directed flows |

**All 21 original flows are retained verbatim and individually directed. None is removed, merged or relabeled.** The two added systems are separate optional Google and GitHub OAuth providers. Thirty additions describe implemented grade verification/publication, role management, question candidates, tagging and separate OAuth exchanges. Browser-mediated redirects/callbacks are distinguished from server-side token/profile/email requests and responses.

The [detailed before/after ledger](diagrams/system-context-review.md) identifies C01–C51 with code evidence. The [SVG](diagrams/system-context.svg) has every arrow and label; there is no arbitrary arrow-count limit. Internal databases/sandbox are shown at the container/deployment level.

## E. Other diagram corrections

The [semantic review and Matrix B](diagrams/semantic-review.md) lists every retained, modified, added or removed relationship. It includes original/final counts for all ten companions, original keys and physical FK preservation.

Only two incorrect **drawn** relationships are removed: component B19 Candidate Controller→Adaptive Engine, replaced by evidenced AI-administration dispatch; and conceptual E09 Assessment→QuestionCandidate seeding, replaced by the actual Concept→QuestionCandidate relationship. Original responsibilities/entities remain. Incorrect caption claims are separately corrected with code evidence. Use-case arrowheads become UML associations without deleting actor participation. No valid context request/response flow is removed.

The full physical schema retains all 21 original tables and 28 original FK associations, and adds 11 actual tables / 17 actual FKs. Its catalog contains all 32 current tables, 45 FKs, keys, nullability, types and complete constraint definitions. It reflects prepared 012, not an assertion that persistent data was upgraded. The conceptual figure retains all 17 original entities and key attributes and links to the exhaustive physical model.

## F. Matrix A — Requirement to implementation

| Requirement | Document source | Code evidence | Status | Action |
|---|---|---|---|---|
| R1 skill selection | Supervisor implementation R1; Proposal FR-06/07 | `personalized_assessment.py`, `PersonalizedAssessment.jsx` | MATCH by source; full gate NOT VERIFIED | Preserve selected IDs/coverage; show frozen-plan branch |
| R2 difficulty | R2; Proposal / Architecture selected difficulty | `personalized_assessment.py`, `adaptive_engine.py`, question validation | MATCH | Preserve Easy 1–2 / Medium 3 / Hard 4–5 and exact bank levels |
| R3 personalized assembly | R3; Proposal frozen plan; User Story assessment flow | `personalized_assessment.py`, session plan/snapshots | MATCH | Distinguish legacy opening loop from selected-band plans |
| R4 classification | R4; question-bank use cases | `question_service.py`, confirmed QuestionConcept, validators | MATCH | Preserve concepts, required techniques and validated serving gate |
| R5 configurable release | R5; Architecture UC20 | `assessment_lifecycle.py`, `grading_review.py`, result guards | MATCH | Make immediate/human publication branches explicit |
| R6 human verification | R6; UC20 | `grading_review.py`, `grade_review`, release audit | MATCH | Preserve required SQL/essay reviews, manual takeover and explicit publish |
| R7 cumulative competency | R7; cumulative profile descriptions | `cumulative_competency.py`, published evidence queries | MATCH | Preserve existing point-weighted algorithm; show published aggregation |
| R8 concept metadata | R8; curriculum / concept model | `curriculum_service.py`, `concept_graph_service.py`, snapshots | MATCH | Preserve descriptions, keywords, objectives, CLOs and prerequisite graph |
| Bilingual originals / reviewed translations | New user directive; older Admin 5 / UC07 / DB table 28 assume English source | Migration 012; localization, editor, snapshot v3 | MATCH implementation; external prose OUTDATED | Supply exact amendment below; no competing schema |
| Frozen assessment locale | Existing academic UC19 / session requirement | Session immutability trigger and snapshot grading | MATCH storage/evidence; display policy amended | Explicit new directive permits read-only reviewed display projections; never mutate recorded locale |
| SELECT-only SQL / sandbox isolation | Requirements decisions; Proposal FR-09 | SQL validator, SandboxRunner, separate Compose networks | MATCH by source; Docker runtime NOT VERIFIED | Correct network wording; preserve guards |
| Optional LLM / OAuth | Architecture / actual provider abstraction | `services/llm`, `oauth.py`, configuration flags | MATCH by source; no live verification | Separate external systems; no asserted translation provider |

Source agreement is not full release acceptance. No authoritative requirement or scoring weight was silently changed to suit a diagram.

## G. Documentation alignment and academic amendments

Current corrected guides: `README.md`, `docs/api-conventions.md`, `docs/learner-and-admin-manual.md`, `docs/setup-and-migrations.md`, `docs/deployment-and-readiness.md`. Testing/supervisor/earlier audit documents receive dated follow-up links; their earlier historical results remain intact. New diagram index, inventory, context comparison, semantic matrix and catalog are current companion documentation.

The four available originals were reviewed read-only:

| External original | Exact correction supplied; original remains unchanged | Status |
|---|---|---|
| `C1SE.70_UserStoryDocument_DBCAS_ver1.4.docx` | Admin 5: original content can be EN/VI, inferred with correction, optional separately reviewed other language. Learner assessment stories: selected-band frozen plans are distinct from legacy easy openings. Preferences: recorded locale/evidence stay fixed; reviewed captured prose can follow UI display language. | OUTDATED passages; amendments supplied, NOT applied |
| `C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx` | UC07 no longer prohibits English translations of VI originals; use original-locale comparison. UC12 scope easy openings to legacy path. Incorporate all eight corresponding diagram companions and their explicit semantic amendments; retain old figures as historical references if needed. | OUTDATED prose/figures; amendments supplied, NOT applied |
| `C1SE.70_DatabaseDesign_DBCAS_ver1.4.docx` | Question: `original_locale VARCHAR(16) NOT NULL DEFAULT 'en'`, check EN/VI. Translation table 28: reviewed other-language display text, EN permitted, original-locale exclusion at API validation. Existing English hashes preserved; VI hashes bind source locale. Snapshot v3 adds source locale; historical snapshots are not backfilled. Use full 32-table / 45-FK companion and preserved conceptual keys. | OUTDATED language/model scope; amendments supplied, NOT applied |
| `C1SE.70_ProposalDocument_DBCAS_ver1.5.docx` | Retain the detailed context interactions and historical roadmap. Link current logical/pipeline companions; include frozen personalized assembly, asynchronous/human verification and publication. Clarify reviewed captured display translations versus immutable recorded locale/evidence. | Core requirements retained; figure/prose amendments supplied, NOT applied |

No university original or old rendered PDF was overwritten. Their original editable diagram sources were not located. The new source/render companions allow incorporation without lossy reconstruction of the original raster files; this is **not** a claim that all academic documents are already aligned.

Unavailable DBCAS standalone formal SRS, UI Design, formal Test Plan/Test Cases, current university Test Report and separate Technical Report are **NOT REVIEWED**. User Stories serve as the available requirements artifact. Unrelated project files cannot substitute for them. No standalone checked-in OpenAPI specification was found; generated FastAPI OpenAPI remains the API specification.

## H. Verification

Environment: Windows, Node 24.16.0, Python 3.14.5; supplemental native PostgreSQL 18.4. These are not the target Python 3.13 / PostgreSQL 17 Docker release environment.

| Executed command (repository root unless stated) | Actual result |
|---|---|
| `npm test -- --maxWorkers=2 --reporter=json --outputFile=../../_review/bilingual-vitest-final.json` in `frontend` | 246/246 tests passed across 32 files; zero failed/skipped |
| `npm run build` in `frontend` | PASS; existing >500 kB chunk warning |
| `.venv/Scripts/python.exe -m pytest -q --maxfail=1` in `backend` | BLOCKED during conftest loading: Docker required; 1 collection/startup error, no backend test case executed |
| `npm --prefix frontend run test:e2e -- question-authoring.spec.js` | BLOCKED: Docker-dependent release server startup failed before browser cases |
| `backend/.venv/Scripts/python.exe ../_review/ux_native_regression.py` | Supplemental PG18 only: 32 direct regression calls passed, zero failed; includes five migration cases, five RBAC/role checks, current/stale translated bank search and original-only missing-snapshot evidence |
| `backend/.venv/Scripts/python.exe ../_review/ux_native_browser.py` | Supplemental real-app PG18/Chromium only: 10 passed, zero failed/skipped; includes original-language detection, reviewed/stale translation, four responsive widths with zero editor axe violations, SQL/essay authoring and learner display/visibility/evidence journey |
| `backend/.venv/Scripts/python.exe -m compileall -q backend/app backend/tests` | PASS |
| `backend/.venv/Scripts/python.exe db/validate_question_localization.py` | PASS: 442 questions; 326 MCQ, 67 SQL, 49 essay; no missing/extra translation keys, duplicates or integrity errors; not a sandbox execution check |
| `node scripts/render_diagrams.mjs` with separately installed renderer and `DBCAS_VIZ_MODULE` | Nine DOT/SVG renders passed without warnings; context is directly editable SVG |
| `py scripts/validate_diagrams.py` | PASS: 10 model/render inventories; exact relationship IDs and directions, 32 tables / 45 FKs and DDL fingerprint match |
| `node ../_review/render_context.mjs` and `node ../_review/validate_diagram_renders.mjs` | PASS: all ten renders inspected; 51 context arrows/labels, no clipped labels; explicit SVG visual review performed |
| `py ../_review/ux_check_links.py` | PASS: 22 Markdown files, 68 local links including three anchors, zero broken links |
| Public documentation HEAD/GET via Python urllib | PASS: the single external Markdown URL (PostgreSQL JSON documentation) returned HTTP 200 and its JSON-INDEXING anchor exists; no provider API called |
| Catalog leaf-key comparison | PASS: 1007 matching EN/VI leaf keys |
| `py ../_review/check_bilingual_preservation.py` | PASS: 43 external DOCX unchanged, no recovered file missing, .env/schema/migration bytes unchanged this phase |
| `git diff --check` | PASS |


The first browser run had one first-login URL timeout (six other journeys passed), with no login POST recorded in the diagnostic capture. It is retained outside Git as `bilingual-browser-first-run.json`; the unchanged seven-journey rerun passed. Later expanded native journeys cover automatic authoring detection and real learner language/evidence behavior. Earlier frontend runs had nine failures (232/241 passed), then one test-label failure (240/241 passed), exposing additional-request mock assumptions and one new test-label error; these were corrected and the complete suite rerun. Supplemental checks do not replace blocked release gates. A direct-SVG screenshot attempt initially timed out; HTML-hosted rendering of the same SVG succeeded. During boundary refinement the renderer rejected a CR in a label and the validator caught two not-yet-rendered edges; the encoding was corrected and all render/direction checks rerun successfully.

Warnings: existing frontend chunk above 500 kB; jsdom scrollTo notice; existing Starlette/httpx deprecation. Diagram render warnings were corrected; final renders report no warnings or clipped text. The single external Markdown documentation link and its anchor were checked; cross-browser release acceptance remains unverified.

## I. Data safety

Migration 012 is **prepared and was not applied to persistent development data by this task**. The previously reported persistent status was pending; the persistent catalog was not independently reverified here. Its bytes and `db/schema.sql` are unchanged from the recovered working tree. Migrations 001–011 are untouched. No competing migration was added. Native PostgreSQL clusters are UUID-named owned disposable fixtures, stopped after each run; no persistent cluster was reset and no Docker volume was deleted.

Preservation hashes confirm all 43 inventoried external DOCX files are unchanged, no previously recorded project file disappeared, `.env` is unchanged, and prior implementation files remain. Language reads project captured content and clone display-only grading labels; the display projection does not rewrite snapshots, answer keys, recorded locale, scores or official grading narratives. Normal session-GET timeout finalization remains in force. Tests deep-compare snapshots and canonical grading views, including a newer bank source after capture. No real learner submission was used or modified. No live AI call occurred.

## J. Git status

Branch `main`; HEAD `5db597930cb512879ad1b9c577e6e88d33962b47`. Working tree: **37 modified tracked, 56 new, 0 deleted**, no staged files. This includes prior work and new documentation/diagram artifacts. Exact paths:

```text
 M README.md
 M backend/app/models.py
 M backend/app/repositories.py
 M backend/app/routers/admin.py
 M backend/app/routers/sessions.py
 M backend/app/schemas.py
 M backend/app/services/adaptive_engine.py
 M backend/app/services/evidence_context.py
 M backend/app/services/question_localization.py
 M backend/app/services/question_service.py
 M backend/tests/test_admin_questions.py
 M backend/tests/test_migrations.py
 M db/schema.sql
 M docs/api-conventions.md
 M docs/bilingual-question-verification.md
 M docs/deployment-and-readiness.md
 M docs/learner-and-admin-manual.md
 M docs/setup-and-migrations.md
 M docs/supervisor-implementation.md
 M docs/testing-and-release-gates.md
 M frontend/e2e/release.spec.js
 M frontend/src/components/PersonalizedAssessment.jsx
 M frontend/src/i18n/en.json
 M frontend/src/i18n/vi.json
 M frontend/src/pages/EvidencePage.jsx
 M frontend/src/pages/ExamPage.jsx
 M frontend/src/pages/admin/AdminAssessmentsPage.jsx
 M frontend/src/pages/admin/AdminCandidatesPage.jsx
 M frontend/src/pages/admin/AdminCurriculumPage.jsx
 M frontend/src/pages/admin/AdminQuestionsPage.jsx
 M frontend/src/test/AdminManagement.test.jsx
 M frontend/src/test/BankControls.test.jsx
 M frontend/src/test/CurriculumEditing.test.jsx
 M frontend/src/test/LearnerPages.test.jsx
 M frontend/src/test/LocalizedExam.test.jsx
 M frontend/src/test/LocalizedWorkspaces.test.jsx
 M frontend/src/test/SupervisorWorkflows.test.jsx
?? backend/tests/test_question_original_locale.py
?? db/migrations/012_question_original_locale.sql
?? docs/bilingual-architecture-completion-20261023.md
?? docs/diagrams/README.md
?? docs/diagrams/assessment-lifecycle.dot
?? docs/diagrams/assessment-lifecycle.json
?? docs/diagrams/assessment-lifecycle.svg
?? docs/diagrams/components.dot
?? docs/diagrams/components.json
?? docs/diagrams/components.svg
?? docs/diagrams/conceptual-core.dot
?? docs/diagrams/conceptual-core.json
?? docs/diagrams/conceptual-core.svg
?? docs/diagrams/containers.dot
?? docs/diagrams/containers.json
?? docs/diagrams/containers.svg
?? docs/diagrams/deployment.dot
?? docs/diagrams/deployment.json
?? docs/diagrams/deployment.svg
?? docs/diagrams/inventory.json
?? docs/diagrams/inventory.md
?? docs/diagrams/logical-architecture.dot
?? docs/diagrams/logical-architecture.json
?? docs/diagrams/logical-architecture.svg
?? docs/diagrams/modules.dot
?? docs/diagrams/modules.json
?? docs/diagrams/modules.svg
?? docs/diagrams/originals/040acf4a4581.png
?? docs/diagrams/originals/081cc67a9e34.png
?? docs/diagrams/originals/09b28ece8b06.png
?? docs/diagrams/originals/0e35cb0e44ac.png
?? docs/diagrams/originals/1918f7591e4f.png
?? docs/diagrams/originals/2794fabf0d75.png
?? docs/diagrams/originals/618b2479a1d6.png
?? docs/diagrams/originals/799e9149e945.png
?? docs/diagrams/originals/ca2518ad1f51.png
?? docs/diagrams/originals/ef593781ce8c.png
?? docs/diagrams/originals/fa0e6f217935.png
?? docs/diagrams/physical-schema-baseline.json
?? docs/diagrams/physical-schema-relationships.json
?? docs/diagrams/physical-schema.dot
?? docs/diagrams/physical-schema.svg
?? docs/diagrams/schema-catalog.json
?? docs/diagrams/semantic-review.md
?? docs/diagrams/system-context-review.md
?? docs/diagrams/system-context.json
?? docs/diagrams/system-context.svg
?? docs/diagrams/use-cases.dot
?? docs/diagrams/use-cases.json
?? docs/diagrams/use-cases.svg
?? docs/ux-simplification-audit-20261023.md
?? frontend/e2e/question-authoring.spec.js
?? frontend/src/components/QuestionAuthoring.jsx
?? frontend/src/test/QuestionAuthoring.test.jsx
?? scripts/render_diagrams.mjs
?? scripts/validate_diagrams.py
```

No commit, push, merge, reset, clean, deployment, workflow creation or persistent migration was performed. New diagrams/render tools are local authoring artifacts; no application library or CI/CD requirement was introduced.

## K. Remaining work

1. Restore responsive Docker/WSL access, then run the standard backend PostgreSQL 17/sandbox and full release browser gates. Non-destructive diagnostics found WSL running but commands timing out and the Docker connection forcibly closed; no forced WSL/container reset was used.
2. Incorporate/review the supplied amendments and editable figures in separately revised university deliverables. The four originals intentionally remain unchanged; missing formal documents remain NOT REVIEWED.
3. Live automatic translation is neither enabled nor verified: no translation task is approved/configured. The supported current path is original-only authoring with optional manual reviewed translation.

First-time administrators can type once, save an original-only draft, select concepts by name, preview stored reviewed translations and understand missing/stale states. Learners can switch reviewed question prose with menus while keeping their answer and time. These improvements preserve assessment capabilities; all-route release readiness remains unclaimed while the standard environment gates are blocked.

## Final integration acceptance follow-up - 23 October 2026

See [the final integration acceptance record](final-integration-acceptance-20261023.md) for subsequent PostgreSQL 17 migration/browser checks, the verified backup, and the remaining Docker gates. Earlier dated results above remain historical. Migration 012 is still not applied to persistent development data.

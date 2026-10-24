# Final integration acceptance - 23 October 2026

## A. Executive verdict

**PARTIALLY COMPLETE.** The existing 93-file worktree was recovered intact. This
pass adds focused acceptance tests, a PostgreSQL 17 migration check and verified
backup, four-engine bilingual browser coverage, exact academic amendments and a
second semantic review of the existing diagrams. It does not restart the UX or
diagram implementation. Standard Docker backend/sandbox and full release E2E
remain blocked by intermittent Docker/WSL connectivity. Persistent activation is
**NO-GO pending the remaining gates and separate owner authorization**.

### Recovered pending gates

| Gate at recovery | Final disposition |
|---|---|
| Standard backend regression | Three startup attempts failed before test cases; still BLOCKED |
| PostgreSQL 17 migration 012 | Five disposable native PG17 migration cases passed, within 33 focused checks; Docker matrix still pending |
| Persistent inventory and verified backup | COMPLETE read-only inventory, checksum history check and restored-backup comparison; no migration applied |
| Full Chromium release E2E | Startup failed on Docker readiness; still BLOCKED |
| Bilingual multi-engine acceptance | 10 native-PG17 real-app journeys passed in each of four engines; explicitly supplemental |
| Diagram semantic/visual acceptance | All ten re-reviewed and rendered; all 51 context flows audited; C43 label corrected without removing a flow |
| Academic amendment reconciliation | Four available root originals re-inspected, ready draft text supplied; originals unchanged |

## B. Docker / WSL recovery

The active `wsl-engine` context uses a localhost TCP relay. `default` has no
Docker Desktop named pipe. WSLService is running and Ubuntu-24.04 is listed
running, but `/bin/echo` and `systemctl is-active docker` repeatedly exceed
12-15 second diagnostic deadlines. No WSL shutdown/reset or service restart was
performed. No Docker Desktop process/service was found.

The daemon briefly responded as Docker 29.8.1, listing 30 running containers,
including existing `dbcas-db` and `dbcas-sandbox`. The system volume is still
`dbcas_db-data`; its original bind/volume configuration was inspected read-only.
Subsequent CLI and raw HTTP probes alternated between success, forced connection
closure and timeout. A successful `/_ping` was not accepted as proof that
container startup, exec or the release gate was healthy.

The first pytest startup created `dbcas-test-06af4eb8` with this run's UUID label
and tmpfs, then `docker run` returned 125. A later `docker start` of this owned
disposable container succeeded. Its cleanup request subsequently failed on the
relay; final API inspection also timed out. **Its final removal cannot be
confirmed.** It belongs to run `b89bc16abc22483cbe2557106f78abe4`; clean up only
after verifying that label. No unrelated container/image/volume was removed.
Further pytest starts, including the documented private-interface setting, failed
at Docker readiness. No tests were skipped or checks relaxed to obtain a pass.

Windows had about 2.7 GiB free physical memory at initial diagnosis and about
1.9 GiB later; disk had about 146 GiB free. These observations and the 30 running
containers establish resource pressure as a possibility, **not a proven root
cause**. No OOM or disk-full cause was established. Unrelated workloads were left
running. Heavy suites and browser engines ran sequentially.

The configured database and sandbox loopback connections also became unreliable.
Their existing published services were reachable through WSL's private address.
That read-only override was scoped to diagnostics/backup processes, never saved
to `.env`. PostgreSQL 17.11 system inventory succeeded. Existing sandbox
`validate_environment()` returned no problems, `health_check()` returned true,
and `execute('SELECT 1 AS acceptance_probe')` returned one row under its rolled-back
learner transaction. These prove narrow role/timeout/connectivity health through
that transport, not dataset grading, outbound isolation or normal-loopback
application readiness. Current application readiness also correctly requires
the unapplied `original_locale` column.

## C. Migration 012 and persistent activation recommendation

Migration 012 adds `question.original_locale VARCHAR(16) NOT NULL DEFAULT 'en'`
and its EN/VI check. It removes migration 007's English-translation exclusion
while retaining a locale-format constraint. Existing primary/composite indexes
remain appropriate; no new query/index design is required. No prompts,
translations, answer keys, rubric scores, snapshots, submissions or review rows
are rewritten by 012. Source/translation inequality is enforced by the API;
historical translation rows are not relabeled or regenerated.

The existing transactional runner holds an advisory lock, verifies every applied
checksum and records each filename once. The disposable PG17 tests cover fresh,
pre-OAuth, post-OAuth and current schema paths; complete shape parity; repeated
runner/direct SQL execution; existing English source and Vietnamese translations;
new Vietnamese source and English translation; MCQ options, SQL fixtures, essay
criteria; captured attempts, official grade detail and grade-review preservation.
Original-only and stale/reviewed behavior is additionally covered by the API
checks. The expanded 012 test compares full protected-row JSON, not only counts.

Portable PostgreSQL **17.11** was downloaded from the
[EDB binary archive page](https://www.enterprisedb.com/download-postgresql-binaries)
(the [PostgreSQL Windows page](https://www.postgresql.org/download/windows/) links
this distribution). It was extracted outside Git without installing a service.
The archive SHA-256 and exact download URL are retained under the private review
directory. This is native Windows PG17, not the Debian Docker sandbox gate.

### Persistent read-only evidence

- PostgreSQL 17.11 Debian service; `original_locale` absent and 012 not recorded.
- Applied migrations 001-011: **all eleven checksums match current files**.
- Questions **442**, translations **442**, sessions **18**, attempts **109**,
  grade reviews **0**.
- Existing `question_translation_pkey` and `question_translation_locale_idx`
  remain present.
- Source fingerprints matched before backup and after restore verification;
  `.env`, migration 012 and schema source bytes remain unchanged.

Verified backup: `../_review/integration-acceptance-20261023/persistent-pre012-dc1764d9.dump`.
Size **336828 bytes**; SHA-256 `fc46986a89033d7cd189029a5ae3645e9910c198ef0ffde2e25289d8fd37e74e`.
`pg_restore --list` succeeded, and a full restore into an owned disposable PG17
cluster matched canonical row fingerprints for questions, translations, sessions,
attempts and grade reviews. This recovery drill used the owner data only for
backup integrity comparison, never for application acceptance cases. The cluster
was stopped. The private archive stays outside Git.

The initial localhost dump timed out. Early restored comparisons failed because
timestamp rendering and database collation differed between Linux and Windows.
The comparator was corrected to UTC and a stable Python string sort; no records
were altered to obtain a match. Both the initial source-order fingerprint and
canonical restore fingerprint are retained in the receipts. Failed comparisons
are diagnostic history, not claimed passes.

### Recommendation and exact owner procedure (NOT executed)

**GO for the additive migration design based on the focused PG17 results; NO-GO
for persistent activation now.** First resolve Docker/loopback readiness and pass
the complete standard backend/sandbox and release E2E gates. Then obtain separate
owner authorization. The procedure is:

1. Enter an owner-approved maintenance window; stop application writes/workers
   through the existing operational process. Do not remove volumes or reset data.
2. Re-inventory server identity, schema, migration checksums, counts and protected
   fingerprints in a repeatable-read/read-only transaction. The private WSL IP is
   ephemeral; rediscover and verify it rather than copying today's address.
3. Take a fresh backup if any drift occurred. With secure `PGHOST`, `PGPORT`,
   `PGUSER`, `PGPASSWORD`, `PGDATABASE` environment configured for the verified
   source, run `pg_dump --format=custom --no-owner --no-privileges --file <private-backup.dump>`.
   Hash it; use `pg_restore --list <private-backup.dump>` and a full restore to a
   new disposable PG17 cluster. Compare UTC/stable-order fingerprints. No source
   DDL or data changes occur during this preflight.
4. Only after authorization, from `backend` with the **verified intended database
   configuration**, run `.venv/Scripts/python.exe -m app.migrate` once. It should
   apply only `012_question_original_locale.sql`; any old checksum discrepancy
   must stop the process. Never stamp versions manually or edit 001-011.
5. Compare protected row counts/fingerprints; all old question rows should have
   `original_locale='en'`. Translation hashes/prose/timestamps and snapshots,
   scores, feedback/review rows must remain unchanged. Confirm one 012 history
   row and the source-locale check. A second migration command must report already
   current. Perform application readiness and authorized original/translation
   smoke checks with isolated disposable accounts, not real learner submissions.
6. Activate the matching API/frontend revision together. If preflight or
   post-checks fail, keep writes stopped and investigate. Do not perform an
   automatic destructive downgrade/restore over the live database.

No step applying migration or activating/deploying the application was performed
in this task. The backup is evidence for review, not authorization to activate.

## D. Bilingual functionality

Implemented: one editor, conservative prose detection with manual correction,
original-only saves, separate optional reviewed translations, stale invalidation,
preview, UI-language bank titles/search, captured learner display projections and
explicit original fallback. All existing English hashes stay compatible. SQL,
identifiers, option associations and scoring/rubric keys stay source technical
data. Source edits in referenced questions preserve the old version/snapshots.

Acceptance adds diacritic-free Vietnamese, mixed English/Vietnamese, SQL-heavy,
short/ambiguous text, backticked identifiers and persistent user-correction cases.
Unaccented Vietnamese is **not claimed reliably detectable**: it retains the
current fallback until corrected. Mixed strong Vietnamese prose chooses VI;
code-only input does not establish a language. These limits are visible through
the simple content-language correction, not a database metadata field.

No automatic question-translation task, route, generation button or persisted
machine-draft lifecycle exists. The general LLM provider has credentials for
existing tasks, but no approved translation task/configuration or translation
cost/quota policy. Its generic `generate_structured` method alone does not
provide task-specific technical-token/rubric validation or human-review storage.
No translation integration was added or live provider called during this
acceptance pass. No translation-provider mock success is claimed. The verified
translation scenario is **manual entry plus human review**, allowed by the
acceptance scenarios; unreviewed editor text is not persisted or published.
Adding optional machine preparation remains separately unfinished if required.
Existing essay grading was exercised with a mock, not a live translator.

Anonymous and Learner users are now explicitly tested against translated create
and update payloads: 401/403, with the authorized question detail unchanged.
Display switching preserves draft answers and expiry; official grading text and
recorded locale remain fixed. Missing-snapshot legacy evidence is original-only.

## E. Backend regression and exact checks

| Executed command | Actual result |
|---|---|
| `.venv/Scripts/python.exe -m pytest -q --junitxml=../../_review/integration-acceptance-20261023/backend-junit.xml` in `backend` | Three startup attempts, **zero pytest cases executed**. First Docker run exited 125 after create; later attempts failed conftest readiness. No passing full-suite count. |
| `backend/.venv/Scripts/python.exe ../_review/acceptance_pg17_regression.py` | **33 focused direct calls passed, 0 failed**, on a UUID-named owned native PG17.11 cluster. Not pytest and not standard Docker acceptance. Includes five migration cases and RBAC/roles, MCQ/SQL/essay language, stale/current search, frozen sessions and mocked essay grading. |
| `npm test -- --maxWorkers=2 --reporter=json --outputFile=../../_review/integration-acceptance-20261023/vitest.json` in `frontend` | **255 tests passed**, 0 failed/skipped, 32 files |
| `npm run build` in `frontend` | PASS; existing >500 kB chunk warning |
| `backend/.venv/Scripts/python.exe -m compileall -q backend/app backend/tests` | PASS |
| Read-only existing sandbox diagnostics via WSL private address | No environment problems; health true; rolled-back SELECT 1 succeeded. Not full sandbox/network acceptance. |
| `backend/.venv/Scripts/python.exe ../_review/acceptance_backup.py` | Final backup/list/full-restore/fingerprint validation PASS; earlier timeout/comparator failures retained above |
| `node scripts/render_diagrams.mjs` with `DBCAS_VIZ_MODULE` pointing to the existing external renderer | Nine DOT sources rendered; no warnings |
| `py scripts/validate_diagrams.py` | Ten inventories, source/render context labels/directions, DDL fingerprint and 45 FKs PASS |
| `node ../_review/render_context.mjs`; `node ../_review/validate_diagram_renders.mjs` | Ten browser renders; 51 context arrows/labels, no clipped labels. Separate visual inspection recorded below. |
| `py ../_review/check_bilingual_preservation.py` | All 43 external DOCX unchanged; no previous file missing; `.env`, schema and migration bytes unchanged |
| `py ../_review/ux_check_links.py`; `git diff --check` | PASS: 25 Markdown files, 133 local links including three anchors, zero broken links; whitespace PASS |
| External documentation HEAD checks | PASS: EDB binary archive and PostgreSQL Windows download pages returned HTTP 200; no AI provider API called |
| Final 93-path preservation / secret-pattern review | PASS: all 93 starting paths present, 012/schema bytes unchanged, no workflow introduced, no private-key/cloud-token patterns found in changed text artifacts; not a complete security proof |

The initial metadata-reader command used the Windows default codec and failed to
read a UTF-8 test report; explicit UTF-8 corrected that diagnostic. It was not a
test failure or evidence of an application encoding change. Existing jsdom
scrollTo and Starlette/httpx deprecation warnings remain. No assertion or security
guard was disabled. Python remains 3.14.5 on the host; target Python 3.13 release
runtime acceptance is not claimed.

## F. Browser acceptance

Standard `npm --prefix frontend run test:e2e` attempted the full Chromium suite,
but release-server startup failed on Docker readiness: **zero cases executed**.
Diagnostics are retained under the private `chromium` acceptance output.

Supplemental commands:

```powershell
$env:DBCAS_ACCEPTANCE_BROWSER='chromium' # then firefox, webkit, msedge, sequentially
backend/.venv/Scripts/python.exe ../_review/acceptance_pg17_browser.py
```

| Engine | Passed | Failed | Skipped | Environment |
|---|---:|---:|---:|---|
| chromium | 10 | 0 | 0 | Disposable native PostgreSQL 17.11 |
| firefox | 10 | 0 | 0 | Disposable native PostgreSQL 17.11 |
| webkit | 10 | 0 | 0 | Disposable native PostgreSQL 17.11 |
| msedge | 10 | 0 | 0 | Disposable native PostgreSQL 17.11 |

Each run uses a newly created native PG17.11 database and the real FastAPI app
and Vite frontend, one browser worker, no retries or external AI credentials.
No startup/schema override points tests at persistent data. Coverage includes VI
and EN automatic authoring detection, original-only saves, MCQ answer identity,
manual reviewed translation, bank search/display, source editing/staleness,
preview, named curriculum links, SQL/essay authoring and learner language/
visibility/draft/submission/evidence preservation. Editor/bank controls pass
390/768/1024/1440 px checks and editor axe violations are zero.

These ten journeys do **not** complete browser acceptance of live SQL dataset
execution, essay submission/provider wait, full human-publication/competency or
role-management journeys. Those broader journeys remain in the blocked standard
suite. Existing mock-backed provider tests and focused RBAC calls are separate
evidence, not substitutes. All four supplemental runs passed without retries.

## G. Diagram quality

The [acceptance review](diagrams/acceptance-review-20261023.md) audits every C01-C51
relationship against a named code symbol and UC/R requirement, classifies its
abstraction and explains apparent overlap. All ten actual diagrams, originals
and ledgers were re-reviewed. No DFD, sequence or star schema was invented.

System Context: **6 nodes / 51 directed relationships at both start and finish**.
All 21 university-original flows and labels remain verbatim. All 30 earlier
additions remain. Only C43 is clarified from “Profile / verified identity claims”
to “Profile / provider user ID”, because `_github_identity` obtains verified email
separately via C44-C45. **No relationship is added, removed, merged or redirected
in this pass.** The diagram is explicitly a detailed external-interaction context,
not a chronological sequence or a minimal C4 summary. OAuth detail is retained
and linked, not silently erased.

The assessment JSON had a corrupted R1-R3 range while DOT/SVG were correct. It
is fixed, and the validator now rejects corrupt text and checks exact context
label parity. Other node/relationship counts are unchanged. All nine DOT sources
were rendered again, and all ten actual images inspected. No clipped text,
overlapping nodes or missing arrowheads were found. Component, module, logical,
use-case and physical views retain some crossing curves; the detailed component
and physical canvases require zoom. They are not claimed readable as unzoomed
A4 thumbnails. The acceptance review lists each visual verdict and limitation.
Syntax success is separate from semantic and visual review.

## H. Academic documentation

The [document reconciliation](academic-reconciliation-20261023.md) supplies exact
U1/U2, A1/A2, D1-D4 and P1-P3 replacement prose and a document-by-document table.
User Stories v1.4, Architecture v1.3, Database Design v1.4 and Proposal v1.5 were
re-inspected from their actual root DOCX files. Amendments are ready for academic/
owner review and incorporation into separately revised copies; none is claimed
already incorporated or supervisor-approved. Current README/setup/testing/
deployment navigation links to this record. Earlier audits retain historical
results and receive dated follow-up links.

Unavailable standalone DBCAS formal SRS, UI Design, university Test Plan/Cases,
current university Test Report and separate Technical Report remain **NOT
REVIEWED**. Unrelated university project files were not substituted. No Word/PDF
original was edited or new Word artifact delivered.

## I. Consistency and data safety findings

- Prepared code/physical schema expects migration 012; the persistent database
  still lacks it. This is an explicit pending activation state, not a claim of
  working persistent readiness. No automatic application startup migration was
  run to hide the discrepancy.
- Reviewed manual translation/display works; automatic translation is absent.
  Generic LLM configuration is not represented as translation approval or live
  verification.
- Session locale and evidence immutability are preserved while display prose
  may follow a reviewed captured translation. Academic preferences prose needs
  the supplied clarification; the authoritative immutable-record requirement
  is not removed.
- The sandbox's no learner-controlled network/system-data access requirement
  remains mandatory. Narrow health checks and Compose inspection are not proof
  of complete runtime isolation.
- No persistent data modification, real-submission test mutation, live AI call,
  university-original overwrite or GitHub Actions introduction occurred. The
  source data fingerprints match the read-only pre-inventory. Backup restoration
  occurred only in a new owned cluster for recovery verification.

## J. Git status and safety review

Branch `main`; HEAD `5db597930cb512879ad1b9c577e6e88d33962b47`.
Working tree: **37 modified tracked, 59 new, 0 deleted**;
no staged files, commit, push, merge, reset, clean, history rewrite or deployment.
The original 93 paths all remain. Source/schema/migration preservation, exact
original DOCX hashes and secret-pattern review are part of the final checks.
New private binary downloads, backup archives, disposable clusters and raw test
diagnostics remain outside the Git repository. Exact review paths:

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
?? docs/academic-reconciliation-20261023.md
?? docs/bilingual-architecture-completion-20261023.md
?? docs/diagrams/README.md
?? docs/diagrams/acceptance-review-20261023.md
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
?? docs/final-integration-acceptance-20261023.md
```

This pass changes acceptance tests (`test_migrations`, original-language RBAC,
authoring ambiguity/correction), diagram validation/metadata/C43 labeling and
current documentation links/reconciliation. No new product library, backend
architecture, scoring rule or database migration was introduced.

## K. Genuine remaining work

1. Resolve the intermittent Docker/WSL relay and normal-loopback connectivity;
   then pass the standard backend suite with PostgreSQL 17, real sandbox and
   full Chromium release E2E. Do not infer success from this supplemental suite.
2. Verify removal of this task's one recorded disposable Docker container if it
   remains; preserve every unrelated container and persistent volume.
3. Review/incorporate the ready academic amendments in separately revised
   originals; obtain unavailable formal documents if complete academic alignment
   is required. Keep the no-network/security requirement pending runtime proof.
4. If automatic translation preparation is required, approve/configure its
   task-specific provider policy, bounded cost/quota controls and technical/rubric
   preservation contract before adding its draft-only integration and mock tests.
   No live translation capability is asserted here.
5. After the integration gates and separate owner authorization, perform the
   persistent activation procedure above. Migration 012 remains unapplied.

The worktree and verified backup are ready for owner review. Full acceptance,
persistent activation and GitHub synchronization are not claimed complete.

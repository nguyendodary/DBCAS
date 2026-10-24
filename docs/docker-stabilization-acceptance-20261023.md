# Docker stabilization and integration acceptance — 23 October 2026

## A. Executive verdict

**PARTIALLY COMPLETE.** Standard Docker PG17 regression reached 1004 passing
tests, and full Chromium release acceptance executed all 40 cases (38 passed,
2 failed). The two obsolete browser interactions were corrected, but their
rechecks and the final backend rerun are blocked by recurring Docker/WSL
transport failure. Full release acceptance and migration activation are **NO-GO**.
This is a continuation of
the recovered 96-path change set, not a replacement of the UX, diagram or
academic review. Persistent migration 012 remains unapplied. No commit, push,
deployment, persistent smoke test or new persistent backup is authorized here.

## B. Docker / WSL diagnosis and corrections

| Classification | Observed evidence | Disposition |
|---|---|---|
| WSL control instability | Listed running Ubuntu-24.04; WSLService/vmcompute running; bounded guest echo/journal/memory commands repeatedly timed out | Not proven resolved; no reset or host-wide restart |
| Docker transport instability | Active `wsl-engine` TCP context alternated between working API/CLI and timeouts; `exec -i` schema load timed out after TCP PG17 readiness | Bounded commands, recorded ownership before create, separate create/start; load identical schema using verified disposable PostgreSQL connection |
| Localhost forwarding | Development PostgreSQL/sandbox loopback connections unreliable; private WSL interface reachable | Process-scoped `DBCAS_TEST_DOCKER_HOST`, no `.env` change or new socket exposure |
| Host resource exhaustion | About 3.05 GiB free RAM initially, later 5.23 GiB; 145 GiB free disk; existing DB/sandbox restart=0, OOM=false, low CPU/memory | Possible pressure, not an established OOM/disk-full cause; suites sequential |
| Harness ownership defect | Previous combined create/start failure could leave a disposable container before cleanup registration | Register intended name/run receipt before daemon create; reject foreign ownership and persistent mounts |
| Test expectations | Migration expectation stopped at 011; bank/content browser tests expected superseded controls or English-only/pinned display | Expectations aligned with current contract; rollback, publication, source identity, answer/timer and evidence assertions retained |
| Translation validation defect found in new tests | Technical-only option `ORDER BY` could acquire prose | Whole technical-only options protected; explicit English instruction regression prevents overmasking prompts |

No broad process termination, Docker Desktop install/reinstall, WSL shutdown,
global prune, volume deletion or unrelated container action occurred. One
apparently successful closed-stdin WSL probe was contradicted by a paired
four-case timeout experiment; it is not represented as a fix. The underlying
intermittent host/control-plane cause remains unknown.

Final probes independently timed out after eight seconds in both the WSL system
distribution and root Ubuntu execution. Docker localhost `/_ping` and `/version`
timed out, while the private-interface Docker endpoint was unavailable. The
listener belongs to `wslrelay.exe`; PostgreSQL on the private interface remained
readable with matching fingerprints. This narrows the observed failure to the
control/forwarding path, without proving the guest daemon itself is defective.
Guest journal retrieval was unavailable; absence of daemon log evidence is not
a clean log result. No port conflict was established. At recurrence the host
still had roughly 3.8 GiB free physical memory. No OOM or disk/I/O root cause
was demonstrated. A service/distribution restart could interrupt unrelated
projects and requires an owner-managed maintenance decision; it was not attempted.

## C. Disposable-container cleanup

The old `dbcas-test-06af4eb8` (`26308dbee10fc352f74e82dbca639eef7870d8659fc441e51b7d2ad6b65216cc`)
was inspected: completed test run `b89bc16abc22483cbe2557106f78abe4`, no persistent
mounts, tmpfs only. Its explicit removal returned HTTP 204. Unrelated containers
and `dbcas_db-data` were retained. Cleanup refuses a mismatched run label or any
bind/volume mount, and never requests volume removal. All failures/receipts stay
outside Git under `../_review/docker-stabilization-20261023/` and
`../_review/docker-tests/`.

The 1004-test backend run passed its tests but reported two cleanup-inspection
timeouts at exit. Both named containers were subsequently inspected against
that run's labels and removed with HTTP 204; see `backend-current-cleanup.json`.
This warning is retained as instability evidence rather than hidden by pytest's
successful exit status. The later browser bootstrap failure's container was
confirmed absent with HTTP 404.

The complete 40-case Chromium run subsequently reported cleanup inspection
timeouts for `dbcas-test-f75f4e57` and `dbcas-sandbox-fa21e8ee`, owned by completed
run `c00dc257a27846bc88767b72e1d4a9cc`. Final direct API verification also timed
out (`cleanup-last.json`), so their removal **cannot be confirmed**. Do not
remove either name without rechecking that exact ownership label and absence
of persistent mounts. They may remain; no blind cleanup was performed. The
original earlier orphan was positively removed, as distinguished above.

## D. Standard backend regression

From `backend`, with a verified private WSL test address in the process:

```powershell
$env:DBCAS_TEST_DOCKER_HOST='<verified-private-WSL-address>'
.venv/Scripts/python.exe -m pytest -q --junitxml=<private-report.xml>
```

These use real disposable Docker PostgreSQL **17** and the actual SQL sandbox,
not the supplemental Windows cluster. Local AI credentials are blanked and live
provider transport is forbidden. Authentication/RBAC, role management, question
languages, assessment assembly, real SQL execution/security, mocked grading,
human verification, publication, competency, migrations and evidence are included.

Executed sequence:

- First full run: **1002 passed, 1 failed** (stale expected migration list).
- Corrected affected migration: **1 passed**; then full **1003 passed**.
- After final product changes: full **1004 passed, 0 failed, 0 skipped**, 444.53 s;
  cleanup warnings described above.
- New schema-transport targeted check: **1 passed, 25 deselected**, 5.41 s.
- Pure command/translation checks: **23 passed, 1 deselected** (API case excluded
  only from the daemon-free command; included in the standard full suite).
- Supplemental native PG17: **34 passed**; this is additional evidence only.

An initial new pure translation run had **2 failed, 17 passed, 1 deselected**.
The protected-option correction above addressed those failures; subsequent runs
passed. No live translation call was made.

Final full attempt after the last harness change: **BLOCKED before collection**,
exit 4: `Docker readiness failed: Docker info timed out after 15s` followed by
the intentional fail-closed fixture error. No tests executed or were skipped in
that attempt; no JUnit case result was produced. `backend-last.log` retains it.
The earlier 1004-case pass is not represented as a successful rerun of the later
schema-transport/cleanup changes. Those changes have a passing focused schema
case and the daemon-free ownership checks, but still need a full rerun.

## E. Release and browser acceptance

The actual repository gates are run one engine at a time with one test worker,
zero automatic retries, fresh app/sandbox containers and separate diagnostics:

```powershell
$env:DBCAS_BROWSER='chromium' # then firefox, webkit, msedge, sequentially
$env:DBCAS_E2E_OUTPUT='<separate-private-engine-directory>'
$env:DBCAS_TEST_MANIFEST='<absolute-private-container-manifest>'
npm --prefix frontend run test:e2e
# Normal application gate, from frontend:
npx playwright test -c playwright.application.config.js
```

| Gate | Actual result |
|---|---|
| Full standard Chromium release | **38 passed, 2 failed, 0 skipped, 0 flaky**, 18.6 minutes; additional global cleanup error |
| Affected bank/content Chromium | **6 passed**, 1.6 minutes, before the final full run |
| Corrected translation-review / supervisor recheck | **BLOCKED at startup**, exit 1, Docker info timeout after 15 s; zero cases executed |
| Full Firefox / WebKit / Edge release | **NOT EXECUTED**, shared Docker prerequisite unavailable; not replaced by earlier supplemental journeys |
| Normal application-entrypoint gate, all engines | **NOT EXECUTED**, same prerequisite; release fixture tests do not establish this separate gate |

All eight EN/VI responsive workspace journeys passed at 390/768/1024/1440 px,
as did the separate four-width critical-route accessibility journeys. MCQ/SQL/
essay completion, timeout recovery, cross-user rejection, human publication,
evidence and role administration are included among the 38 passing cases. Two
remaining test failures are documented explicitly below, so complete release
readiness is not claimed.

The translation-review test saved successfully (201 and expected translation),
then assumed its new item was visible before searching the paginated bank. The
failure snapshot shows **Page 1 of 39**. Search now precedes that visibility
assertion; language switching, independent edits, stale hash and correct-answer
assertions remain. The supervisor test called `fill('3')` on the new difficulty
`select` and would then use the removed concept-ID field. It now selects the
same difficulty and checks the same named concepts, with additional saved
difficulty/concept-set assertions. Both corrections pass JavaScript syntax
checking; their integrated execution remains blocked, not presumed passed.

Earlier full Chromium attempt contained two stale bank assertions; the owned
run was deliberately interrupted rather than counted as passed. Its diagnostics
remain in `release-chromium-initial-interrupted`. Six affected bank/content
journeys subsequently passed in **1.6 minutes**. A fresh full run then failed
before any cases on Docker `exec -i` schema loading; its complete trace is kept
in `release-chromium-bootstrap-failure`. The schema transport was corrected as
described above. These failed/interrupted attempts are not erased by later runs.

Frontend final unit result: **260 passed, 0 failed, 32 files**. Production build
passed (existing large-chunk advisory retained). Catalogs have **1016 matching
EN/VI leaf keys**. Bank localization validator: **442 questions**, 326 MCQ,
67 SQL, 49 essay; no errors.

These frontend unit/build and pure/localization checks were run again after
the final browser test changes: unit **260/260**, build exit 0, pure **23 passed,
1 deselected**, localization exit 0. The unit log retains existing jsdom
`window.scrollTo` warnings; they are not failed cases. Python compilation and
`pip check` passed. Private receipts: `vitest-last.json`, `frontend-build-last.log`,
`pure-unit-last.xml`, `backend-current.xml`, `backend-last.log`,
`release-chromium/browser-results-chromium.json`, and
`affected-review-classification.log`.

Additional exact checks from the repository root:

```powershell
npm --prefix frontend test -- --reporter=json --outputFile=../../_review/docker-stabilization-20261023/vitest-last.json
npm --prefix frontend run build
backend/.venv/Scripts/python.exe -m pytest --noconftest -q backend/tests/test_docker_runtime.py backend/tests/test_question_translation_draft.py -k 'not admin_route' --junitxml=../_review/docker-stabilization-20261023/pure-unit-last.xml
py db/validate_question_localization.py
node --check frontend/e2e/question-authoring.spec.js
node --check frontend/e2e/supervisor.spec.js
git diff --check
```

## F. Migration 012 readiness

**Design: GO. Persistent activation: NO-GO until required gates and operational
readiness are satisfied, then separate owner authorization.** No migration or
schema source bytes were changed during this continuation.

012 adds `question.original_locale NOT NULL DEFAULT 'en'` with EN/VI check and
removes the old exclusion of English display translations. Existing English
source defaults/translation hashes remain compatible. Existing question,
translation and evidence records are not rewritten. Current primary/locale
indexes remain appropriate. Source/translation inequality and review hashes
are enforced by the API. The runner serializes, validates old checksums, records
012 once and treats repeated runs as current; tests do not bypass that ledger.

The real PostgreSQL 17 migration tests include 001–011 upgrades, repeatability,
English and Vietnamese originals, reviewed/missing/stale translations, MCQ/SQL/
essay, schema constraints, history checksums, frozen session/attempt snapshots
and published grading/review evidence. Their final standard-suite result is
reported in D; supplemental PG17 checks are not a replacement.

### Exact owner procedure — prepared, NOT executed

1. After the required gates and host/application readiness are accepted, obtain
   a maintenance window and authorization. Quiesce application writes/workers
   through the existing operational process; do not remove volumes.
2. Verify intended server/database identity. In a repeatable-read, read-only
   transaction record counts and canonical SHA-256 row fingerprints for questions,
   translations, sessions, attempts and grade reviews, plus all eleven migration
   checksums. Use UTC JSON timestamps and a stable external string sort.
3. Configure secure `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` for
   the verified source; never paste secrets into documentation or command output.

   ```powershell
   pg_dump --format=custom --no-owner --no-privileges --file <private-backup.dump>
   Get-FileHash -Algorithm SHA256 <private-backup.dump>
   pg_restore --list <private-backup.dump>
   ```

   Restore to a separately created disposable PostgreSQL 17 database, with its
   verified connection variables, using
   `pg_restore --exit-on-error --no-owner --no-privileges --dbname <disposable-db> <private-backup.dump>`.
   Compare all canonical fingerprints. A readable table list alone is insufficient.
4. With the intended persistent connection verified again, from `backend` run
   `.venv/Scripts/python.exe -m app.migrate` once. Expect only
   `012_question_original_locale.sql`. Stop on any historical checksum mismatch;
   never stamp history or reapply old migrations manually.
5. Compare before/after data: existing question rows gain only
   `original_locale='en'` (exclude precisely this additive column when comparing
   their old fingerprint); translations, snapshots, answers, scores and grading
   evidence must match exactly. Verify the new constraint and one correct 012
   checksum row; repeated runner execution should report current.
6. Run the separately authorized local application smoke test against the matching
   API/frontend revision, using isolated test accounts, never real submissions.
   Local commit and GitHub push are separate later owner actions.

If any gate, backup restore or fingerprint check fails: **NO-GO**, keep writes
quiesced and investigate. A failed transactional migration is rolled back by
the runner; do not delete the ledger or downgrade schema blindly. After a
successful additive upgrade, retain the evidence and diagnose/revert application
code only if compatible; an owner-approved restore must target an isolated
recovery database first, never automatically overwrite the persistent database.

Previously verified backup: `persistent-pre012-dc1764d9.dump`, **336828 bytes**,
SHA-256 `fc46986a89033d7cd189029a5ae3645e9910c198ef0ffde2e25289d8fd37e74e`.
The prior PG17 full restore matched canonical source fingerprints. This task
rechecked its hash; it did not take another persistent backup or rerun a restore
using learner data. Fresh backup/verification before activation remains reserved
for the owner. See the [historical receipt summary](final-integration-acceptance-20261023.md).

## G. Automatic translation

Manual reviewed translations and original fallback are retained. A minimal
provider-agnostic draft preparation path now uses the existing LLM adapter, with
explicit opt-in **off**, no provider/network calls on save, no persistence/cache,
one bounded attempt, quotas and strict output/technical-marker checks. Human
review remains unchecked after preparation; only normal reviewed save can store
it. SQL/option/rubric identities and scoring are never generation outputs.

MockTransport tests cover both directions/types, protected code/math/options,
provider outage/quota errors, authorization and no persistence. Frontend tests
cover stale async responses, incomplete edits, failures and explicit review;
the browser draft test mocks those two draft endpoints only and uses a real
question save to prove unreviewed output is omitted. **No live-provider
verification, configured operational quota or approval to enable is claimed.**
See [the exact capability, limits and operator next step](draft-question-translation.md).

## H. Documentation and retained work

Updated current documents: README, API conventions, Administrator/Learner manual,
testing gates, local integration troubleshooting, optional draft translation,
setup/migration follow-up, this report and academic reconciliation U1 wording. Historical acceptance results
retain their dates and failures. The optional draft task has a text relationship
addendum; it introduces no new actor, service, database, worker or migration.

All **ten diagrams / 48 diagram artifacts** remain byte-identical to recovery,
including all **51 context relationships and 21 original flows**. All **43
external DOCX originals** remain unchanged. Academic amendment text remains
separate from originals; only the existing U1 draft is reconciled with the new
disabled-by-default capability. Missing formal documents and independent
network-isolation evidence recorded in the earlier academic report remain
unclaimed; this blocker-remediation pass does not invent or re-audit them.

Final documentation check: **146 local links**, including **3 Markdown anchors**,
across **28 documents**, with **0 broken**. External URLs were not checked. The
local checker is `py ../_review/ux_check_links.py`; its receipt stays outside Git.

## I. Data safety

Read-only fingerprint inventory: **442 questions, 442 translations, 18 sessions,
109 attempts, 0 grade reviews**. Five protected-table fingerprints match the
prior receipt; migration 001–011 checksums match; 012 is absent. `.env` unchanged;
translation opt-in false. No persistent SQL writes, new backup, submission edits,
evidence changes, volume removals or original academic document writes occurred.
Final post-run comparison: **PASS**, including source and prepared migration
bytes, all 96 starting paths, 48 diagram hashes, 43 DOCX hashes, all five data
fingerprints, the existing archive checksum and the eleven migration checksums.
`final-safety.json` records `transaction_read_only=on`. Persistent volume/data
were not removed or rewritten; final daemon-side volume inspection is unavailable
during the transport outage, so no final Docker health result is inferred.

## J. Git status

Branch **main**, HEAD **5db597930cb512879ad1b9c577e6e88d33962b47**.
**45 modified, 66 new, 0 deleted, 0 staged** (111 paths). No commit, push, merge, staging,
reset, clean, stash or deployment. All 96 recovered paths remain present.
`git diff --check` passed. Added-content scanning found no private-key or common
provider-token patterns and no added GitHub Actions workflow; this is a focused
credential-pattern check, not a claim of a complete security audit. Python and
JavaScript syntax checks passed. Untracked files are included below, rather than
being omitted from the tracked-only diff statistics.

## K. Remaining blockers

1. Recover reliable WSL control/Docker API access under an owner-managed host
   maintenance investigation. No safe remaining context/container action was
   identified during the outage; broader restart was outside authorization.
2. Verify cleanup of the two explicitly owned containers in C once API access
   returns; keep every unrelated container/volume intact.
3. Run the two corrected Chromium cases, then the full final backend suite and
   complete release/application browser matrix sequentially with zero retries.
   Keep this run's 38/2 result and transport errors as historical evidence.
4. Preserve the earlier academic limitations: incorporation into external
   originals and unavailable formal documents are not completed by amendments.

Live translation configuration/provider approval is optional follow-up, not a
claim that live calls were verified. Migration activation remains deliberately
unexecuted, not an action the agent should complete without separate approval.

## L. Next recommended action

Do not proceed automatically. Persistent verified backup, migration 012 activation,
final local persistent smoke test, local commit and GitHub push were not executed.
Their disposition is:

| Later owner action | Recommendation now |
|---|---|
| Verified persistent backup | Procedure ready; existing restored backup hash/data still match. Fresh backup reserved for owner after maintenance/gates |
| Migration 012 activation | **NO-GO**: final standard regression/release gates unresolved |
| Final persistent local smoke test | **NO-GO** until authorized backup/activation and matching app readiness |
| Local commit | Hold until owner reviews the complete worktree and unresolved failures |
| GitHub push | Hold until owner approves local commit and acceptance |

The safe work is left uncommitted for review. This report does not authorize a
host-wide restart, paid provider, persistent backup/activation, commit or push.


### Complete owner-review path inventory

Status is Git status against HEAD. No files were staged.

```text
 M README.md
 M backend/app/config.py
 M backend/app/deps.py
 M backend/app/models.py
 M backend/app/repositories.py
 M backend/app/routers/admin.py
 M backend/app/routers/sessions.py
 M backend/app/schemas.py
 M backend/app/services/adaptive_engine.py
 M backend/app/services/evidence_context.py
 M backend/app/services/question_localization.py
 M backend/app/services/question_service.py
 M backend/tests/cleanup_release.py
 M backend/tests/conftest.py
 M backend/tests/test_admin_questions.py
 M backend/tests/test_final_acceptance.py
 M backend/tests/test_migrations.py
 M db/schema.sql
 M docs/api-conventions.md
 M docs/bilingual-question-verification.md
 M docs/deployment-and-readiness.md
 M docs/learner-and-admin-manual.md
 M docs/setup-and-migrations.md
 M docs/supervisor-implementation.md
 M docs/testing-and-release-gates.md
 M frontend/e2e/bank-reconciliation.spec.js
 M frontend/e2e/question-content.spec.js
 M frontend/e2e/release.spec.js
 M frontend/e2e/supervisor.spec.js
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
?? backend/app/services/question_translation.py
?? backend/tests/docker_runtime.py
?? backend/tests/test_docker_runtime.py
?? backend/tests/test_question_original_locale.py
?? backend/tests/test_question_translation_draft.py
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
?? docs/docker-stabilization-acceptance-20261023.md
?? docs/draft-question-translation.md
?? docs/final-integration-acceptance-20261023.md
?? docs/local-integration-troubleshooting.md
?? docs/ux-simplification-audit-20261023.md
?? frontend/e2e/question-authoring.spec.js
?? frontend/src/components/QuestionAuthoring.jsx
?? frontend/src/test/QuestionAuthoring.test.jsx
?? scripts/render_diagrams.mjs
?? scripts/validate_diagrams.py
```

## Later conditional restart follow-up — 18:00, 23 October 2026

The owner subsequently authorized one Ubuntu-24.04 restart **only if** all
pre-restart safety gates pass. The [dated safety decision](docker-wsl-root-cause-recovery-20261023.md#n-conditional-restart-safety-decision-at-1800)
records A/C/D PASS, B UNVERIFIED and E FAIL. No restart was attempted because
inaccessible guest/container workloads cannot establish quiescence.

Fresh backup evidence is stronger than the earlier five-table comparison: the
existing verified archive was fully restored into a new isolated native
PostgreSQL 17.11 cluster and **all 33 public-table counts/fingerprints match the
current source**, including accounts, assessments and competency records. The
source stayed unchanged and the disposable cluster was stopped gracefully.
No archive was overwritten and no migration was executed.

Fresh sequential stability samples again show Docker API/metadata and guest
execution **0/3**, while system and learner sandbox private-interface PG17 queries
pass **3/3**. Heavy test gates and cleanup remain blocked. These are new safety
and restore observations, not reruns of the historical 1004 backend / 38-of-40
Chromium cases above. **Migration 012 activation remains NO-GO**. Existing source,
diagrams, academic originals and all prior test corrections are preserved.

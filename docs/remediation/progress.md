# Remediation verification record

## Baseline and authority

Work starts at develop2, 9f7353df9a359f710c901d09f0b11bd9fd7a0df9.
Origin/develop2 remains b32742603983d11eb04a120261123cfe538a16f4.
The six prior UI commits are preserved. Only additive commits are authorized;
no push, merge to main, rebase, reset, clean or history rewrite occurred.

Formal sources: Proposal1.4, Architecture1.2, DatabaseDesign1.3 and
UserStory1.3 in the parent workspace, together with their four extracted
texts. Explicit acceptance criteria outrank implementation extensions.
README, API conventions, DDL/migrations, environment examples, Compose and
prior alignment/UI audits supplied supporting implementation context.

requirements.json preserves all R01-R75 before/scope/source/acceptance fields,
then records implementation, actual test paths and runtime evidence.
findings.json preserves all F01-F34 severities and their re-audit dispositions.
These are traceability records, not a claim of external deployment certification.

## Implemented groups

- Fail-closed deployment configuration, safe API envelopes, typed JWTs,
  dummy bcrypt verification, DB-atomic throttle/OAuth handoff and bounded renewal.
- Durable revisioned ungraded drafts; authoritative database expiry; atomic
  answer/next state, lost-response recovery, idempotent finish and bounded jobs.
- Immutable served question/assessment context and legacy-cutoff backfill;
  historical competency uses only captured confirmed tags and submitted grades.
- Bounded typed SQL execution; catalog/dynamic-query rejection; minimal-role
  setup whitelist; executable multi/edge fixtures and explicit AST techniques.
- Real LLM service messages in all admin paths; explicit human review;
  four-level finite essay validation, calibration examples, strict wire schemas,
  domain validation before versioned cache insertion and boundary-aware privacy.
- Formal shortfall ranking, fresh gap explanations, safe untouched mappings,
  complete Concept/CLO CRUD, question filters and formal bank activation checks.
- Backend history/dashboard/analytics metrics, Admin-only provisioning,
  highlighted native SQL editor, accessible viewport dialogs and empty states.
- Additive migrations001-005, reviewed benchmark, local fonts, release images,
  readiness/bootstrap, pinned CI, migration/browser/load/image gates and manuals.
- Final re-audit removed unsupported evidence aggregate scoring and fixed
  WebKit modal focus restoration; repository persistence boundaries completed.

## Verification and artifact location

Final verification completed on12October2026. All65 required rows and seven
accepted extensions are implemented and verified. Three exclusions remain
explicit. F01-F30 and F32-F34 are fixed with code/test/runtime evidence; F31 is
preserved archive history. No confirmed application P0/P1 or security-critical P2
remains open. The explicit owner-approved read-only scope is recorded below.

Raw logs, JSON and screenshots remain at ../_review/remediation. The full39-section
report is full-remediation-report.md there. Its final Git record includes this
tracker commit without a self-referential committed HEAD.

Complete frontend:108 PASS in16 files,33.45s. Build:PASS. Complete backend:742 PASS,
zero failures/skips,323.87s, against real PostgreSQL17 and the bounded sandbox.
Host Python3.14.5; Linux release images verify Python3.13.16/two API workers,
additive migrations, unsafe-production-secret rejection, readiness, registration,
Nginx proxy/security headers and local fonts. Production login measured177ms.
Compile/import/pip check and both Compose syntax checks pass. Final npm/Python
advisory scans report zero known vulnerabilities. No live paid provider was called.

Chromium/installed Edge/Firefox/WebKit each pass all nine browser cases. Critical
routes at390/768/1024/1440 have axe/overflow/console/request-loop/reduced-motion
checks. WebKit is engine verification, not branded Safari/Apple hardware. The
native Windows browser fixture uses one API worker; remote Linux CI is configured
but unexecuted. Owner confirmed successful Google and GitHub returns to DBCAS.

Final burst:100 synchronized learners, peak100 in-flight,1000 requests, zero failures.
Submission p50=1688.66ms,p95=2201.84ms,p99=2217.73ms; it exceeds500ms. Final normal:
100 active identities at20 arrivals/sec, peak2 in-flight,1000 requests, zero failures.
Submission p50=55.07ms,p95=78.24ms,p99=84.71ms; endpoint means are below500ms. The
normal arrival pattern is a disclosed assumption. Separate SQL:concurrency4,
three rounds,12/12 successes,p50=130.43ms,p95=p99=193.85ms. Resource observations
are post-run samples, not peak-memory measurements.

Retained failures include the earlier100-request baseline, an intervening full
backend733-pass/1 sandbox ConnectionTimeout run, and a later stalled backend
attempt during WSL/Windows memory failure. The owner freed memory; Docker recovered
and the existing stopped app DB was started without reset. Full suites then passed
sequentially. Fresh readiness has bounded connection/statement probes with real
TCP-blackhole/PostgreSQL cancellation tests. Browser failures for WebKit focus,
Firefox navigation cancellation and an empty-dashboard heading remain in evidence;
corrections passed. One SQL load attempt had11 successes/1 ReadTimeout alongside
native Windows WinError10022 worker socket warnings. Fresh connections, matching
the HTTP load protocol, pass12/12 without retries. This does not claim native Windows
persistent multi-worker sockets were fixed. Framework/color-setting warnings are
separate from browser runtime/console errors; console evidence preserves cancellations.

No private secrets or prohibited current/outgoing attribution were found. Developer
.env remains untracked and unchanged. Existing personal data/volumes remain; local
migration005 and benchmark imports retain row/target evidence. Local assessments3
and4 are real. Main API/UI/Docker services remain running. Only owned labeled test
fixtures/processes/networks were removed, without volume deletion or unrelated
project cleanup. Main live AI remains disabled; essay work can stay pending until
a provider/opt-in worker is deliberately enabled. Mocked contracts do not establish
live model quality. External HTTPS/deployment/recovery checks remain operator work.

## Retained archives

refs/backup/pre-attribution-cleanup and refs/backup/pre-devin-cleanup are
pre-existing recovery refs. Static frontend prototypes/reference files are
not active React routes or assets. F31 is not a release defect requiring
unauthorized archive deletion or history rewriting. Current/outgoing commits
are audited for secrets and prohibited attribution; historical backup refs
are not described as rewritten or attribution-cleaned by this work.

## Formal scope decision applied

Proposal1.4 section6.2 includes practical DML/DDL; Architecture1.2 UC13/QA03
and Learner4 acceptance criteria require read-only execution and rollback.
The owner explicitly chose read-only execution with DML/DDL knowledge assessed
through MCQ/essay on11October2026. requirements-decisions.md records the reply;
R32 records the applied resolution. sql_knowledge_pack.json adds two concepts,
two MCQs, a four-level essay and a separate formal assessment. Its real sandbox
regression passes and preserves the original assessment targets. No learner
shared/system database mutation is enabled.

Development and UI demonstration are reviewable locally. Full staging or
production release requires operator environment,
HTTPS, backup/recovery and deployment checks; this work does not authorize
publishing. Final readiness is stated in the delivered report, not inferred
from passing unit tests alone.

# Docker / WSL root-cause recovery — 23 October 2026

Latest post-reboot result: **APPLICATION RUNNING IN DISPOSABLE PREVIEW**;
[migration readiness, fresh regression and service report](#p-post-reboot-recovery-and-application-acceptance).
Sections A-O below retain their pre-reboot historical meaning.

Current investigation: [deep Windows-side diagnosis at 19:00](#o-deep-windows-side-diagnosis-at-1900).
It adds independent host/virtualization/network observations, a correlated
timeline and a reviewable read-only Administrator collector. It does not claim
a confirmed internal root cause or a successful repair.

Latest follow-up: [conditional restart safety decision at 18:00](#n-conditional-restart-safety-decision-at-1800).
The owner has now conditionally authorized one Ubuntu-24.04 restart. The
authorization's workload/quiescence prerequisites are not met, so no restart
was attempted. Earlier observations below retain their historical meaning.

This continuation preserves the earlier [integration remediation record](docker-stabilization-acceptance-20261023.md).
Its historical test counts are not new results from this investigation.

## A. Executive verdict

**BLOCKED — OWNER ACTION REQUIRED.** A finite three-sample observation failed
every Docker API/metadata and guest-execution check. Both PostgreSQL 17 services
remained readable through the private WSL interface. Heavy regression was not
launched into this failed prerequisite. The precise internal WSL/relay/daemon
cause is still unconfirmed; disruptive recovery requires explicit approval.

## B. Root-cause analysis

Receipts are private under `../_review/root-cause-recovery-20261023/`:
`commands.json`, `host.json`, `windows-events.json`, `stability.json`,
`chromium-failure-evidence.json`, `direct-network-guest-metrics.json`,
`data-safety.json` and `baseline.json`.

| Suspected layer | Fresh evidence | Conclusion |
|---|---|---|
| Context/configuration | `docker context ls/inspect` return promptly; selected `wsl-engine` points to `tcp://127.0.0.1:2375`; default named-pipe context has no active Desktop engine | No supported context correction identified; context metadata success is not daemon health |
| Docker control plane / relay | `docker version`, `info`, `ps -a`, `system df` each exceed 12 s; raw ping and inventory exceed 3 s in all three samples | Consistently unavailable during this observation; not a one-off failing test |
| WSL execution/control | WSL status/list/version succeed; Ubuntu is listed Running; guest `/bin/echo` times out at 5 s in each sample | Failure extends beyond Docker CLI; exact internal cause unconfirmed |
| Localhost forwarding | Localhost system/sandbox authentication times out; same configured identities reach both services through private WSL interface | Observed forwarding/control-path failure; does not establish a PostgreSQL crash |
| Database / sandbox | Both authenticate and execute read-only version/`SELECT 1` checks in all three samples; major version 17 | Narrow TCP/auth/query health confirmed, not full SQL security or integration acceptance |
| Host memory/disk | About 2.7 GiB physical RAM free; 148.6 GB disk free; existing WSL cap 8 GB, 8 processors, 4 GB swap | Pressure possible; no proven OOM or disk-full cause; limits were not changed |
| Guest memory / pressure | Static `/proc` metrics read through the existing read-only PostgreSQL connection: about 5.54 GiB available guest memory, 3.79 GiB free swap, memory PSI avg10/60/300 all 0, load 0.46/0.36/0.30; database cgroup OOM counters 0 | No current guest-memory exhaustion evidence; database cgroup counters do not establish the daemon's historical OOM state |
| Proxy routing | No HTTP/HTTPS/ALL proxy or DOCKER_HOST/DOCKER_CONTEXT overrides; direct `http.client` connection also times out, bypassing proxy discovery | No proxy correction justified; failure is not confined to urllib or Docker CLI configuration |
| Engine lifecycle | WSLService/vmcompute running; no Docker Desktop service; listener previously identified as WSL relay | This is a WSL-hosted Docker Engine setup; restarting nonexistent Desktop is unjustified |
| Windows events / guest logs | Compute and Host Network Service event logs deny access; Lxss/Operational channel absent; filtered System errors give no relevant events; guest execution unavailable | Missing privileged diagnostics, not proof that logs are clean or the daemon is fault-free |
| Container or application defect | Current metadata unavailable; earlier two Chromium traces show local locator/assertion failures after successful bank API requests | No basis to label those two test failures Docker failures |

WSL reports version 2.7.11.0, kernel 6.18.33.2-2; Windows reports
10.0.26300.9711. These are observations, not a claim of a known version-specific
bug. No port conflict or filesystem-corruption cause was established.
The static guest metrics used `pg_read_file` only for `/proc/meminfo`,
`/proc/pressure/memory`, `/proc/loadavg` and cgroup `memory.events`; no OS command,
program execution, configuration write or persistent SQL mutation was performed.

## C. Repairs performed

No additional application or Docker configuration repair was justified by this
evidence. Existing bounded creation/cleanup, direct PostgreSQL schema loading,
one-worker/zero-retry gates and the two browser corrections were retained.
No timeout was increased, assertion weakened, retry added or feature removed.
Diagnostic commands are bounded, and their output is retained rather than
silently retried. This report and current navigation are the only repository
changes in this continuation unless a later authorized recovery is recorded.

## D. Stability acceptance

Three samples at approximately 0, 15 and 30 seconds, with independent bounded
queries per sample:

| Check | Passed samples | Disposition |
|---|---|---|
| Docker HTTP ping | 0 / 3 | FAIL |
| Docker container metadata | 0 / 3 | FAIL |
| WSL guest execution | 0 / 3 | FAIL |
| Private-interface system PostgreSQL 17 query | 3 / 3 | PASS, read-only |
| Private-interface learner sandbox PostgreSQL 17 query | 3 / 3 | PASS, read-only |
| Loopback system / sandbox connection, first sample | 0 / 1 each | FAIL |

This is a finite measurement window, not an unbounded readiness retry. A TCP
accept, running service, private SQL success or earlier passing suite does not
override the failed Docker-control prerequisite. Full sandbox grading/security
and normal-loopback application readiness are not claimed.

## E. Owned-container cleanup and service inventory

| Service/container | Ownership / storage evidence | Current status |
|---|---|---|
| `dbcas-db` | Compose DBCAS system database; earlier inspected ID `ccb7218d4f54038cc2031fe5c765695066e095d857c88ac77d9e6c9514c8a0f5`; named volume `dbcas_db-data` | Private SQL readable; data fingerprint matches; current Docker metadata unavailable |
| `dbcas-sandbox` | Compose sandbox; earlier inspected ID prefix `7b8040ca5546`; PostgreSQL data mount is a volume, not a disposable harness tmpfs | Private learner SQL readable; must not delete/recreate |
| `dbcas-test-f75f4e57` | Recorded completed run `c00dc257a27846bc88767b72e1d4a9cc`; intended harness tmpfs | Current existence, exact ID and mounts cannot be verified; no removal attempted |
| `dbcas-sandbox-fa21e8ee` | Same completed run and intended harness resource-limited sandbox | Current existence, exact ID and mounts cannot be verified; no removal attempted |
| Backend / release frontend | No listeners at 8000/8100/5174 in the port snapshot | No release test server assumed running |
| Owner development frontend | Port 5173 has an existing listener | Left running; not treated as an owned test process |
| Other projects | Prior report observed about 30 running containers; current complete inventory times out | Names, active writes and restart policies are not currently verified; a distro restart can interrupt them |

Names and an old manifest are insufficient deletion authorization. After API
recovery, inspect each exact ID, matching `dbcas.test-run`, current mounts and
owning-process completion, save diagnostics, remove only verified unused tmpfs
containers without volume flags, then verify absence. The older
`dbcas-test-06af4eb8` was positively removed in the previous task; that fact is
not represented as a new cleanup success here.

## F. Backend regression

**NOT EXECUTED in this continuation:** the stability prerequisite failed. The
documented command remains, from `backend`:

```powershell
$env:DBCAS_TEST_DOCKER_HOST='<rediscovered-and-verified-private-WSL-address>'
.venv/Scripts/python.exe -m pytest -q
```

Historical evidence: the previous real Docker PG17/sandbox run had **1004
passed, 0 failed, 0 skipped**, with cleanup warnings. The final subsequent
attempt failed before collection on Docker info timeout (exit 4). Neither is
presented as a new pass of the final harness state. After recovery, run affected
tests and then the full suite; do not skip the real sandbox or provider guard.

## G. Two original Chromium failures

Both screenshots were visually inspected; trace archives and source snapshots
were read without exposing authentication headers. The private evidence JSON
contains relevant failed calls and only method/path/status for bank requests.

| Original test | Independent evidence | Existing correction | Current disposition |
|---|---|---|---|
| `review an English translation of a Vietnamese original and preserve both on edit` | POST question returned 201; screenshot shows “Question created”, unfiltered bank; error snapshot Page 1 of 39; trace fails the visibility assertion before search | Search precedes visibility; reviewed language switching, original edit, stale status and correct-answer assertions retained | Corrected code preserved; integrated rerun BLOCKED, not claimed passed |
| `supervisor journeys A–E: classification, personalization, both release policies and cumulative evidence` | Trace attempts `fill('3')` on a real `select`; screenshot shows intact editor/answers; question creation requests succeeded | `selectOption('3')`, named concept checkboxes, plus saved difficulty/concept-set assertions | Corrected code preserved; integrated rerun BLOCKED, not claimed passed |

Both edited scripts pass `node --check`. The failure points precede SQL
sandbox execution; no contemporaneous sandbox-health telemetry at those precise
instants is available. Current private-interface sandbox health cannot be used
retroactively. No evidence supports attributing either failed step to Docker.

After stable recovery, from the repository root with separate output/manifest:

```powershell
$env:DBCAS_BROWSER='chromium'
npm --prefix frontend run test:e2e -- question-authoring.spec.js supervisor.spec.js --grep 'review an English translation|supervisor journeys'
```

Only after targeted success, run the full gate. Keep all earlier failed traces.

## H. Release / cross-browser coverage

No new heavy browser suite was launched after the failed observation window.
The previous standard full Chromium run was **38 passed, 2 failed, 0 skipped,
0 flaky**, plus an independent global cleanup error. The previous six targeted
bank/content cases passed; the final corrected-two-case attempt failed at
Docker startup before any case. Standard Firefox/WebKit/Edge and normal
application gates remain **NOT EXECUTED / BLOCKED**. Earlier native PostgreSQL
supplemental browser passes are not substitutes.

After targeted Chromium success, sequentially run `npm --prefix frontend run
test:e2e` with `DBCAS_BROWSER=chromium`, then `firefox`, `webkit`, `msedge`, one
worker and zero automatic retries. Use a separate absolute `DBCAS_E2E_OUTPUT`
and `DBCAS_TEST_MANIFEST` per run. From `frontend`, also run
`npx playwright test -c playwright.application.config.js` sequentially per engine.
Wait for complete cleanup and stable health before starting the next heavy suite.

## I. Migration 012 readiness

**NO-GO.** Mandatory final backend, corrected Chromium and full release gates
have not passed. Migration and schema source hashes are unchanged, 012 remains
absent from the persistent ledger, and all eleven old checksums match.

The previous disposable PG17 migration/compatibility tests and restored-backup
receipt remain valid historical evidence, not a new activation approval. After
the required gates, verify 012 again on disposable PG17, then seek separate
authorization. The exact prepared procedure is in
[migration readiness and owner steps](docker-stabilization-acceptance-20261023.md#f-migration-012-readiness):
quiesce writes, verified custom backup and hash, archive inspection, complete
isolated PG17 restore/fingerprint comparison, checksum runner application,
comparison excluding only the new source-locale column for old question rows,
and authorized matching-application smoke tests. No step applying 012 is executed
here. A rollback must not blindly restore over persistent data or erase history.

## J. Data and source safety

Fresh queries ran with `transaction_read_only=on`. Protected counts remain
**442 questions, 442 translations, 18 sessions, 109 attempts, 0 grade reviews**;
all five canonical fingerprints match the prior verified backup receipt.
Migration 001–011 checksums match; source-locale column and 012 ledger row remain
absent. The existing backup archive hash matches; no new persistent backup,
migration, real submission or evidence edit was performed.

All 48 diagram artifacts (ten reviewed diagrams) and all 43 external DOCX
originals match their protected hashes. The `.env`, schema and migration bytes
are unchanged. No Docker volume or unrelated container/image was removed.
Current complete Docker inventory is unavailable, so live container-volume
health is not inferred from older metadata alone.

## K. Git and verification inventory

Recovered branch **main**, HEAD **5db597930cb512879ad1b9c577e6e88d33962b47**;
**45 modified, 66 untracked, 0 staged/deleted** at entry, all 111 paths recorded
by SHA-256. No reset, clean, stash, commit, push, merge, deploy, migration or
GitHub Actions change. Final path counts and documentation checks are recorded
below:

- **45 modified, 67 untracked, 0 staged, 0 deleted** — 112 review paths.
- Every original 111-path worktree entry remains. **110 are byte-identical**;
  only README navigation was appended to link this new report. No existing
  application, test, diagram, migration or amendment bytes changed this pass.
- **149 local links**, including four Markdown anchors across 29 documents,
  resolve with zero broken links. External URLs were not checked.
- `git diff --check` and both corrected browser scripts' `node --check` passed.
  No GitHub Actions workflow file exists. No source runtime change requires
  repeating the already recorded frontend/unit/build checks during this outage.
- Read-only safety receipts and trace/screenshot inspections are fresh results;
  the previous **260 frontend**, **23 infrastructure/translation**, **1004
  backend** and production-build results remain explicitly historical.

## L. Remaining blockers

1. Docker API/metadata, localhost forwarding and guest execution are unavailable;
   exact internal failure lacks privileged Windows/guest log evidence.
2. Host/distro restart or service recovery can interrupt unrelated projects and
   needs explicit owner approval after writers/backups are considered.
3. Two completed-run containers cannot be inspected/cleaned safely yet.
4. Corrected browser cases, final full backend, release browser matrix and normal
   application gates remain unverified. Migration activation stays NO-GO.

## M. Reviewable owner recovery operation — NOT EXECUTED

There is no Docker Desktop service to restart. The narrow proposed restart is
the **Ubuntu-24.04 distribution**, not WSL unregister/reset, not volume removal,
and not an unapproved `wsl --shutdown` of all distributions. Ubuntu currently
hosts Docker for other projects; terminating it stops all of those Linux
processes and containers. A forced stop can lose uncommitted/in-flight work and
require PostgreSQL crash recovery. Current complete inventory is unavailable;
do not assume the prior count describes every affected workload.

Only after the owner approves the interruption, pauses other project writers,
confirms needed backups and accepts the forced-stop risk:

```powershell
# OWNER-APPROVED MAINTENANCE ONLY — not executed by this investigation
wsl --terminate Ubuntu-24.04
wsl -d Ubuntu-24.04 --exec /bin/true
wsl -d Ubuntu-24.04 --exec systemctl is-active docker
```

If Docker is inactive, use the distribution's existing authorized service-start
procedure (`sudo systemctl start docker` in Ubuntu), without installation or
configuration replacement. If WSL termination/start also hangs or fails, stop
and retain the exact error. Do not escalate automatically to WSLService/vmcompute
restart, broad process kills, VM reset or Windows reboot.

Then inspect the current context and inventory, existing IDs/volume mounts and
database readiness before starting any stopped existing DBCAS container. Do not
run compose commands that recreate the database, run migrations or initialize
fresh storage. Rediscover the private WSL address, rerun the finite stability
checks, verify persistent fingerprints/ledger, and clean only the two positively
owned disposable containers. Passing one Docker response is not acceptance.
Proceed to targeted and full tests only after stable control and data-plane
checks. No promise is made that this restart fixes an unconfirmed internal cause.

An explicit owner decision on this exact operation has been requested. No
approval has been received at report completion; the distro and host services
remain running. No broader recovery action is inferred from a request to
continue investigating.

## N. Conditional restart safety decision at 18:00

### A — Executive verdict

**BLOCKED — SAFETY PREREQUISITES NOT MET.** The owner conditionally authorized
one Ubuntu-24.04 restart only after gates A–E are independently verified. This
follow-up verified the target, actual Docker storage and a complete current
backup restore, but could not verify the distribution's active workload inventory
or quiescence. **Neither restart command was executed; the one-attempt allowance
remains unused.** This is a safety-gate failure, not a request for the owner to
repeat the authorization already supplied.

Fresh private receipts are under
`../_review/conditional-recovery-20261023-1754/`. No new duplicate project report
or source implementation was created. The earlier records above remain dated
history; this section records the later conditional authorization and decision.

### B — Pre-restart gates A–E

| Gate | Verdict | Independently observed evidence |
|---|---|---|
| A: exact distribution | **PASS** | `wsl --list --verbose` and `wsl --status` exit 0; exact `Ubuntu-24.04`, Running, WSL2, default. No other target selected |
| B: active workloads identified | **UNVERIFIED** | Docker inventory/info each time out at 12 s; `wsl -d Ubuntu-24.04 --exec ps -eo pid,ppid,stat,comm` also times out at 12 s. Windows shows development processes but cannot enumerate all guest/container workloads |
| C: actual data storage | **PASS** | Configured database `dbcas`, PostgreSQL 17.11 Debian, container hostname `ccb7218d4f54`; live kernel mount metadata identifies `/var/lib/docker/volumes/dbcas_db-data/_data` mounted at `/var/lib/postgresql/data` |
| D: consistent backup / restore readiness | **PASS** | Latest receipt-backed custom archive hash and database name verified; new isolated PG17.11 full restore matches counts and canonical fingerprints for **all 33 public tables**, not only the earlier five-table comparison |
| E: important work quiesced | **FAIL** | DBCAS has zero other client connections/XIDs/idle-in-transaction clients in three samples and zero prepared transactions, but other Ubuntu workloads/writers remain inaccessible. Failed inspection cannot establish global quiescence |

The restart permission requires every gate to pass. A valid DBCAS backup does
not establish backup coverage or quiescence for unrelated projects. Windows
process classification identified one DBCAS Vite process, other Vite processes
and Playwright tool services; a substring match on “playwright” is not proof of
an active browser test. No unrelated process was stopped. DBCAS's 112 recovered
worktree paths stayed byte-identical during the preflight, but that does not
prove other project files are idle.

### C — Recovery actions and exit status

Read-only diagnostics, storage inspection, activity samples and a disposable
restore were executed. These recovery commands were **NOT ATTEMPTED**, so there
is no restart exit status and no post-restart success to report:

```powershell
wsl --terminate Ubuntu-24.04
wsl -d Ubuntu-24.04 --exec /bin/true
```

No other distribution, WSLService, vmcompute, Windows host or Docker Desktop was
restarted. No reset, unregister, reinstall, force flag, broad process termination,
volume deletion, prune, database recreation or persistent migration was used.
The existing context remains `wsl-engine`; no functioning alternative engine was
found. Existing readiness/cleanup code was not changed to conceal the outage.

### D — Current health and stability

A fresh finite observation ran probes **sequentially** at approximately 0, 15
and 30 seconds. Each Docker HTTP call had a three-second deadline and each guest
echo a five-second deadline. The repeated measurements are observations, not
automatic test retries or arbitrary startup sleeps.

| Probe | Fresh success count | Result |
|---|---|---|
| Direct Docker HTTP ping | **0/3** | Timeout, approximately 3.0 s each |
| Docker container metadata | **0/3** | Timeout, approximately 3.0 s each |
| Ubuntu guest echo | **0/3** | Timeout at 5 s each |
| Private-interface system PostgreSQL 17 | **3/3** | Authentication/version/read-only queries pass |
| Private-interface learner sandbox PostgreSQL 17 | **3/3** | Authentication/version/read-only queries pass |

Guest available memory was approximately **5.46–5.51 GiB** across these samples.
No current resource-exhaustion cause is established. Container restart counts,
complete volume inventory and live Docker resource metrics remain unavailable;
older metadata cannot supply a current PASS. Windows listeners show no release
API at 8100 or release frontend at 5174; the existing development frontend at
5173 was left running. Private SQL reachability does not establish normal
loopback application readiness or full sandbox grading/security behavior.

### E — Persistent integrity and restored-backup evidence

The reachable database is **inside the distro being considered for restart**,
not an independent Windows PostgreSQL service. A read-only storage query
verified container hostname, data directory and the actual named-volume mount.
System identifier and identity metadata are retained privately; no credentials
or row contents are reported.

Verified archive:

- `../_review/integration-acceptance-20261023/persistent-pre012-dc1764d9.dump`
- **336828 bytes**, PostgreSQL custom format (`PGDMP`).
- SHA-256 `fc46986a89033d7cd189029a5ae3645e9910c198ef0ffde2e25289d8fd37e74e`.
- Archive table of contents confirms source database `dbcas`.
- A new unique, loopback-only disposable PostgreSQL **17.11** cluster was
  initialized outside the repository. `pg_restore --exit-on-error --no-owner
  --no-privileges --dbname postgres <existing-archive>` completed successfully.
- **All 33 public tables** match the live source's row counts and SHA-256
  fingerprints using UTC row JSON and stable external sorting. Accounts, role
  links, profiles, assessments, question/translation records, attempts, grading
  evidence, competency records and the migration ledger are included.
- Source fingerprints before and after verification match. The owned restore
  cluster was stopped with its own `pg_ctl -D <unique-cluster> -m fast -w stop`;
  no force-kill or persistent restore was performed. Its diagnostic files remain
  outside Git. The existing archive was neither changed nor overwritten, and
  no new backup was needed because the complete existing one is current.

Selected protected counts (no private records exposed):

| Table | Count |
|---|---:|
| account / account_role / user_profile | 18 each |
| assessment | 5 |
| assessment_session | 18 |
| question / question_translation | 442 each |
| attempt | 109 |
| grade_review | 0 |
| competency_gap | 26 |
| schema_migration | 11 |

All eleven applied migration checksums match the source files. **012 and the
new source-locale column are absent** from the persistent database. The restore
used the pre-012 archive as-is, without executing migrations or application
test journeys against learner data. Source connections used enforced read-only
transactions and statement deadlines. See `backup-verification.json`,
`persistent-all-tables-before.json`, `restored-all-tables.json`,
`storage-activity.json` and `ledger-verification.json` in the private receipt
directory.

### F — Owned disposable containers

`dbcas-test-f75f4e57` and `dbcas-sandbox-fa21e8ee` remain associated with the
recorded completed run `c00dc257a27846bc88767b72e1d4a9cc`. Current exact IDs,
labels, mounts and use could not be inspected because Docker metadata failed.
No removal was attempted and no cleanup success is claimed. Intended tmpfs
configuration in a manifest is not a substitute for current mount inspection.
The persistent system and sandbox containers/volumes were left intact.

### G — Backend regression

**NOT EXECUTED in this follow-up:** the mandatory stability prerequisite failed.
The earlier **1004 passed** run and subsequent pre-collection timeout remain
historical. No test was skipped, weakened or marked passing. No source/harness
change was made during this follow-up. Once the environment is stable, the
required command remains `.venv/Scripts/python.exe -m pytest -q` from `backend`,
using the real disposable Docker PG17/sandbox and existing live-provider guard.

### H — Browser verification

**No new targeted or full browser gate ran** against this unstable environment.
The previous full Chromium **38 passed / 2 failed** result and cleanup failure
remain historical. The prior screenshot/trace analysis in G above is retained:
the two failures were the page-one visibility assumption and `fill()` on the
new difficulty select, not demonstrated sandbox failures. Both existing
corrections are preserved; their integrated reruns remain blocked. Firefox,
WebKit, Edge and normal application-entrypoint gates remain unexecuted.
After stability, run the two focused Chromium cases first, then the full
standard backend and sequential release/application browser matrix, with
separate diagnostics and no automatic retry hiding a failure.

### I — Migration 012 readiness

**NO-GO.** Complete backup compatibility now has fresh 33-table restore evidence,
but stable Docker/WSL, final standard backend and required browser gates still
have not passed. No relevant source changed that would justify repeating old
disposable migration tests into the failed infrastructure. Migration 012 remains
unapplied. The prepared owner backup/restore/migration/fingerprint/smoke procedure
in the linked acceptance report remains a later separately authorized action.

### J — Preserved work

Before documentation updates, all **112 recovered paths were byte-identical**.
All bilingual UX, draft-only translation, tests, schema and migration sources
remain preserved; `.env` is unchanged. All **48 diagram artifacts** (ten reviewed
diagrams) and **43 original academic DOCX files** still match their recorded
hashes. No academic originals, historical grading evidence or learner records
were edited. Only the two existing recovery/acceptance reports receive dated
follow-ups; no redundant project report was introduced.

### K — Git and final checks

Branch **main**, HEAD **5db597930cb512879ad1b9c577e6e88d33962b47**;
**45 modified tracked files, 67 untracked files, 0 staged, 0 deleted** at
recovery. No commit, push, merge, deploy, destructive Git command or GitHub
Actions workflow. Final whitespace, link, path-preservation and credential-pattern
checks are recorded in the private final review receipt.

Final review: **110 of the 112 recovered paths remain byte-identical**; only
the two existing reports changed. Their older bodies match the recorded
baseline after excluding the dated follow-ups/navigation and accounting for
original CRLF endings. `git diff --check` passes. **151 local links**, including
six Markdown anchors across 29 documents, resolve with zero broken references.
External URLs were not checked. The added report text has no matched private-key
or common provider-token patterns; no backup files appear in Git changes and
no GitHub Actions workflow exists. A final enforced-read-only comparison again
matches **all 33 public tables** (`persistent-final-comparison.json`). These are
documentation/safety results, not a substitute for the blocked integration gates.

### L — Remaining blockers

1. Guest/Docker workload inspection is inaccessible, so gates B/E cannot establish
   quiescence under the supplied conditional restart policy.
2. Docker/WSL control-plane failure persists; precise internal cause remains
   unconfirmed. No single restart attempt was consumed.
3. Two recorded disposable containers cannot yet be inspected and cleaned safely.
4. Final backend, corrected Chromium, full browser/application and migration
   readiness gates remain incomplete.

### M — Next action

DBCAS is **not ready** for persistent migration activation or GitHub synchronization.
First obtain independently inspectable guest/container workload state and verified
quiescence for affected projects. Owners may need to pause their writers through
their normal graceful procedures; this agent did not terminate unrelated work.
If inspection itself remains impossible, do not treat another restart approval,
the DBCAS-only backup or an idle database snapshot as proof that gates B/E pass.
The current authorization explicitly forbids that inference. Preserve diagnostics
and establish a recovery process that can satisfy the safety gates before using
the single distro restart, then verify all integrity/stability and test gates.

## O. Deep Windows-side diagnosis at 19:00

### A — Verdict and scope

**OWNER ACTION REQUIRED.** The observable failure layer is narrower than a
generic Docker outage: TCP reaches the Windows WSL relay, but Docker HTTP does
not return; existing guest PostgreSQL and SSH services remain reachable through
the private interface. Ordinary new WSL execution does not complete. The exact
fault inside WSL/HvSocket/guest control versus the daemon is **not confirmed**.
No durable repair or full acceptance pass is claimed.

This investigation did not repeat the earlier collection of known-hanging CLI
commands or attempt any restart. It used host APIs, registry/VHD metadata,
named-pipe observations, crash/event metadata, resource counters, a newly
instrumented owned client and existing test timestamps. Private receipts are
in `../_review/deep-root-cause-20261023-1900/`.

### B — Failure mechanism and competing hypotheses

Microsoft's implementation shows that a Windows localhost listener establishes
a Hyper-V socket connection and then relays the TCP stream. WSL process creation
also involves the service and guest session/control channels. These explain
why direct guest IP traffic can survive a control/relay failure, but do not
prove which component is stuck on this machine. This is an **inference about
the affected layer**, not a confirmed kernel bug. Sources:
[WSL localhost relay implementation](https://github.com/microsoft/WSL/blob/master/src/windows/wslrelay/localhost.cpp)
and [WSL process/session startup](https://github.com/microsoft/WSL/blob/master/doc/docs/technical-documentation/boot-process.md).

| Hypothesis | Evidence for | Evidence against / missing | Confidence and next diagnostic |
|---|---|---|---|
| WSL session / HvSocket / localhost-relay fault | New guest execution stalls; relay accepts TCP in **4.6 ms** but HTTP times out at **3.011 s**; private SQL and an Ubuntu SSH banner respond | No guest wait stacks, direct daemon Unix-socket response or HvSocket trace yet | **Most probable failing layer, medium confidence**; privileged root-namespace process/kernel diagnostics, then a targeted HvSocket trace if necessary |
| Docker daemon / container-runtime deadlock | Docker endpoint unavailable | All requests use the failing relay; no direct Unix-socket test yet; existing containers and private SQL work | **Unconfirmed**; inspect daemon state/socket through a trusted guest/admin path before restarting Docker |
| Entire WSL VM stopped or failed boot / virtualization disabled | Host-side commands fail | Guest SQL and SSH respond; hypervisor present and firmware virtualization enabled; registered distro/VHD exists | **Not supported as current explanation**; no BIOS/feature reinstall justified |
| Docker Desktop backend / named-pipe failure | Default context references Desktop's pipe | Actual engine is WSL-hosted; no Desktop service, settings/log directories or Docker engine named pipe; `wsl-engine` is the configured context | **Not supported**; do not reset/reinstall nonexistent Desktop |
| HCS/HNS malfunction | These layers participate in WSL VM/network control; services Running is insufficient proof | `hcsdiag list` and HNS queries explicitly deny access; private IPv4 traffic works | **Unknown**; Administrator HCS/HNS metadata and event inspection needed |
| Host/guest memory or kernel-resource exhaustion | Host has multiple projects; about 1.7–2.3 GiB free physical memory in new snapshots | Commit **68%** (30.1/44.1 GB); no matching Resource-Exhaustion-Detector event in last day; fresh guest memory/IO PSI averages zero; guest memory available; no observed relay handle growth | **Not established**; privileged per-process limits/waits at failure time, not arbitrary limit increases |
| Test-container or process leak / browser concurrency as sole cause | Two completed-run containers remain unverified; many workloads existed | Docker/guest failures were recorded before later successful full tests; full Chromium uses one worker; relay snapshots stayed **341 handles / 27 threads** | **Low confidence as sole cause**; current workload/process inventory still required; counts alone do not rule out a guest-specific leak |
| Incorrect context, proxy or conflicting listener | Could redirect CLI requests | Context is WSL engine, direct HTTP bypassing proxy also stalls, and listener belongs to `wslrelay`; no relevant proxy overrides | **Not supported**; no context/proxy/firewall change justified |
| VHD or filesystem exhaustion/corruption | Storage stalls can affect processes | VHD metadata accessible (**128363528192 bytes**); host disk had ample space in earlier verified snapshot; live data and backup fingerprints match | **No supporting evidence**, guest filesystem fullness/errors not fully inspected; kernel/error logs are needed, not VHD resizing or repair |
| Sleep/Modern Standby resume bug | A [primary incident report](https://github.com/microsoft/WSL/issues/41777) describes a related failure pattern | No matching Kernel-Power/Power-Troubleshooter events today; `powercfg /a` reports **S3**, not S0 Low Power Idle; versions differ from that incident | **Not demonstrated**; do not identify this machine with a known issue or change power policy based on similarity |
| Antivirus/endpoint protection block | Security filtering can affect host IPC/network | Security Center lists Defender; no matching Defender detection/ASR/CFA event IDs in the inspected last-day window; no relevant WER crash report found | **Not demonstrated**, absence of selected events is not exhaustive exclusion; no protection was disabled |

The virtualization provider's CPU extension flags under a running hypervisor
are not used to diagnose missing hardware support. The live guest and
`HypervisorPresent=true` are stronger observations. No Windows feature,
firmware, firewall, network, memory, pagefile or security setting was changed.

### C — Correlated timeline

Times below are **Asia/Saigon (UTC+7), 23 October 2026**. Receipt modification
times identify when observations were recorded, not the exact first onset.

| Time | Evidence / interpretation |
|---|---|
| 11:58 receipt | Initial raw Docker API timeouts already recorded |
| 12:16 receipt | Direct API inspection succeeded and the earlier positively owned orphan was removed |
| 12:17 receipt | Guest memory/disk/journal invocations timed out |
| 12:14:11–12:22:26 | Real Docker PG17 backend: 1002 passed, one obsolete migration expectation failed |
| 12:25:59–12:33:49 | Full backend: 1003 passed after that test correction |
| 12:34:57–12:42:21 | Full backend: 1004 passed; cleanup inspection later timed out |
| 12:44 receipt | Direct API removed both positively owned containers after the CLI cleanup timeout |
| 13:03:02–13:03:07 | Targeted real Docker schema/migration case passed; container control worked during bootstrap |
| 13:03:24–about 13:22 | Fresh full Chromium, one worker/zero retries: 38 passed, two test locator/assertion failures; teardown Docker inspection timed out |
| 13:27–13:28 receipts | Both WSL/system guest execution and Docker transport failed; final backend attempt stopped before collection |
| 18:00 follow-up | Three sequential control probes failed while private system/sandbox queries passed; all 33 restored tables matched source |
| 19:00 investigation | HCS/HNS access denied; VHD, service, networking, memory/commit and named-pipe evidence collected independently |

This establishes intermittency before the full browser workload and later
persistent control failure, not a proven causal event. No matching host-service
error, container OOM event or sleep transition has been retrieved at the onset.
Other projects' concurrency is not known. The oldest discoverable WSL crash
artifacts were node/journald dumps from earlier dates, not a correlated new
WSL service crash; they were not opened or uploaded.

### D — Independent Windows evidence and access boundary

Fresh observations include HNS/vmcompute/WSLService Running, registry identity
`Ubuntu-24.04` at `%USERPROFILE%\WSL\Ubuntu-24.04`, existing VHD metadata,
the root debug-shell named pipe, and WSL relay listener ownership. Relevant
host commands completed without Docker CLI dependence. HNS query returned
**0x80070005 Access denied**. `hcsdiag list` explicitly reports insufficient
privileges. `wsl --debug-shell` returned immediately with the requirement to
run as Administrator — it did not merely hang.

Private-IP port 22 returned an Ubuntu OpenSSH banner. The Windows SSH directory
contains known-host files but no configured private key or WSL host entry.
No password was guessed, key installed, host-key check disabled or SSH security
control bypassed. This route confirms an existing guest service is alive but
does not supply authorized command execution.

One owned diagnostic `wsl.exe` client was observed in Windows thread Wait states
(`UserRequest` / `EventPairLow`) and closed after the bounded observation. Those
generic wait reasons do not identify a particular lock, server thread or kernel
deadlock. No unknown or unrelated process was killed.

Microsoft documents root-namespace inspection with `wsl --debug-shell` and
identifies WSL service/HvSocket event tracing for deeper diagnosis. Those are
new, concrete evidence paths rather than more CLI retries.
[Microsoft WSL debugging guidance](https://github.com/microsoft/WSL/blob/master/doc/docs/debugging.md)
and the [official Administrator-only collector](https://github.com/microsoft/WSL/blob/master/diagnostics/collect-wsl-logs.ps1)
describe the privilege requirements and targeted tracing profiles. No global
trace session, debug-console configuration or restart was enabled here.

### E — Prepared action and repairs

No product/configuration repair was justified yet. Existing one-worker gates,
bounded ownership cleanup, direct PostgreSQL schema bootstrap and both browser
test corrections remain unchanged. There was no timeout increase or new retry.
No claimed stable recovery can be based on a responsive TCP listener alone.

A concrete read-only collector is prepared outside Git:
`../_review/deep_admin_collect.py`, with its SHA-256 in the private
`collector-manifest.json`. It has been syntax-checked. It reads HCS/HNS state,
recent compute/network events and root-namespace process waits/kernel warnings;
all child commands have deadlines. It writes only private investigation receipts.
It contains **no restart, service stop, container removal, installation,
configuration change, package install, password collection or database access**.

An explicit request to launch its Windows UAC prompt is pending. **It has not
been run elevated**, and no Administrator output or successful root shell is
claimed. The collector is immutable after that review request. The authorized
launcher, if approved, uses the existing Python executable and `Start-Process
-Verb RunAs -WindowStyle Hidden` with only this fixed script as its argument;
no execution policy or other security setting is weakened. UAC consent is an
operating-system requirement, not an assumption that the earlier conditional
restart approval grants administrative diagnostics access.

If privileged read-only evidence identifies a project-owned process/resource
defect, fix only that component. If direct daemon or HvSocket evidence instead
requires an affected service/distro restart or kernel update, first verify
workload safety and quiescence and obtain the operation's required authorization.
The existing restart conditions are unchanged and still not met; no restart
attempt has been consumed. A generic restart is not presented as a durable fix.

### F — Infrastructure and test status

The new instrumented control probe still failed after a fast TCP connection;
ordinary guest execution did not complete. Earlier three-sample failures remain
historical, not new passes. Because no repair occurred and the current control
path is still unhealthy, additional identical hanging loops and heavy suites
were not launched. After a justified repair, run three sequential health
samples including direct daemon, metadata, guest execution, PG17 and sandbox
before any full regression.

| Gate | New execution in this investigation | Retained historical evidence |
|---|---|---|
| Standard backend | **NOT EXECUTED — infrastructure prerequisite failed** | 1004 passed / 0 failed / 0 skipped in earlier complete run; later final rerun blocked before collection |
| Full Chromium release | **NOT EXECUTED** | 38 passed / 2 failed / 0 skipped / 0 flaky plus cleanup failure |
| Focused corrected Chromium scenarios | **NOT EXECUTED** | Corrections preserved; last attempt stopped at Docker startup |
| Firefox / WebKit / Edge full release | **NOT EXECUTED / BLOCKED** | Earlier supplemental native journeys are not full standard passes |
| Normal application-entrypoint gates | **NOT EXECUTED / BLOCKED** | Not established by release fixture journeys |
| Frontend unit/build | No source or infrastructure change requiring repeat | Prior 260 passed and production build passed |
| Pure infrastructure/translation | No implementation change requiring repeat | Prior 23 passed, one API case deselected only from daemon-free command |

The two original Chromium failures remain independently identified test defects:
the new record was expected on page one before searching, and `fill('3')` was
used on a `select`. Their API/screenshot/trace evidence, preserved corrections
and unresolved integrated rechecks remain documented in G/N-H above. They are
not retrospectively labeled environmental or skipped.

The two completed-run container names remain unverified; no blind removal
occurred. Once control is healthy, inspect exact IDs/run label, live mounts and
current use, remove only positively owned unused disposable containers without
volume removal, and confirm absence through a fresh inventory.

### G — Migration 012 and data preservation

**NO-GO.** Stable infrastructure, final standard backend and required browser
gates have not passed. 012 has not been applied to persistent development data.
Fresh enforced-read-only comparison again matches **all 33 public tables** to
the preflight/verified-restoration baseline. All eleven applied migration
checksums match; the verified archive hash still matches. The complete PG17.11
restore in the previous continuation is dated evidence; it was not repeated
unnecessarily or misrepresented as a new integration test.

No account, question, translation, assessment, attempt, grade, competency or
historical evidence row was changed. Original/translation behavior, grading,
security, SQL isolation and scoring implementations are unchanged. No external
AI provider was called; optional draft translation remains disabled.

### H — Git and documentation

Branch **main**, HEAD **5db597930cb512879ad1b9c577e6e88d33962b47**; recovered
**45 modified tracked files / 67 untracked / 0 staged / 0 deleted**, 112 paths.
Only this existing recovery report receives a dated follow-up. No duplicate
project report, runtime source edit, GitHub Actions workflow, database dump in
Git, commit, push, merge or deployment is introduced. Diagrams, academic originals
and every recovered path remain protected; final verification receipts record
the hashes, link/whitespace checks and changed-file review.

Final checks: **111/112 existing paths are byte-identical**; only this report
changed, and its older body matches the protected baseline after excluding
the dated follow-up/navigation. All 48 diagram artifacts, 43 academic originals
and `.env` hashes match. **152 local links**, including seven anchors across
29 documents, resolve with zero broken references; external URLs were not
checked. `git diff --check` passed. No private-key/common provider-token pattern,
new workflow, staged file or backup-in-Git was found. The collector's recorded
hash is unchanged, and its elevated completion receipt is absent.

### I — Remaining work

1. Obtain approved Administrator read-only output from the prepared collector
   (or a separately trusted guest command channel) to distinguish the guest
   session/HvSocket fault from daemon/HCS/HNS internals. Exact root cause remains
   **insufficiently evidenced**; the most probable failing layer is not a fix.
2. Apply and verify only a correction supported by that evidence, observing
   unchanged workload/backup/quiescence gates for any disruptive operation.
3. Confirm both disposable containers' identity and safe cleanup after access
   recovers; then targeted Chromium, final full backend and full sequential
   release/application browser gates, plus disposable PG17 migration acceptance.
4. Only after those mandatory gates pass, request owner activation approval
   using the already prepared verified-backup/migration/integrity/smoke sequence.

### J — Immediate next action

Approve the **read-only Administrator diagnostic collector**, not an unverified
restart. No reply has yet authorized that operation at report completion.
Its purpose is to unlock the missing independent evidence, including a possible
root-namespace inventory, without interrupting other projects. No claim of
root-cause remediation, integration acceptance or migration readiness is made.


## P. Post-reboot recovery and application acceptance

Recorded after the owner's Windows reboot; completed 2026-10-24T00:01:42+07:00 (Asia/Saigon).
This section supersedes the earlier blocked infrastructure and pending-gate
dispositions for this recovered working tree. Sections A–O remain dated history.
The results below were freshly executed in this continuation.

### A. Executive verdict

**APPLICATION RUNNING IN DISPOSABLE PREVIEW.** All requested local regression
and browser gates passed. The current code requires migration 012, while the
protected persistent database remains at 001–011. A clearly identified,
independent PostgreSQL 17 preview serves the current application:

- Frontend: `http://127.0.0.1:5173`.
- Backend: `http://127.0.0.1:8000`; `/health` and `/readiness` return HTTP 200.
- Migration 012: **GO for later owner-authorized development activation**;
  it was **not applied** to persistent data.

The preview uses tmpfs storage and synthetic test identities. Its data is
disposable; the existing development database and sandbox remain intact.

### B. Docker/WSL recovery

Bounded `wsl --status`, `wsl --list --verbose`, `docker version`, `docker info`,
`docker context ls` and `docker ps -a` completed after running outside the
initial Windows sandbox permission boundary. Ubuntu-24.04 is WSL2 and executes
guest commands normally. This installation uses Docker Engine 29.8.1 inside WSL;
the native Windows CLI's existing `wsl-engine` context reaches the same engine
through `tcp://127.0.0.1:2375`. No context switch or Docker Desktop reset occurred.

Three sequential samples at approximately 0, 15 and 30 seconds passed Docker
API/container inspection, WSL guest execution, system PostgreSQL and learner
sandbox queries. The same three-sample gate passed again after all tests.
Ongoing bounded probes stayed responsive throughout the sequential suites.
No guest/service restart, WSL reset, package installation or resource-limit
change was needed. These observations establish recovery during this run;
they do not establish the internal cause of the earlier outage.

### C. PostgreSQL and sandbox

| Service | Verified identity | State |
|---|---|---|
| Persistent app database | `dbcas-db`, ID `ccb7218d4f54`, database `dbcas`, PostgreSQL 17.11, host port 5435 | SQL ready; original `dbcas_db-data` volume and system identifier match |
| Persistent SQL sandbox | `dbcas-sandbox`, ID `7b8040ca5546`, database `postgres`, PostgreSQL 17.11, host port 5434 | Both configured admin and `learner_ro` connections succeed; original volume preserved |
| Disposable preview app | `dbcas-preview-app-6efac65d`, database `dbcas_preview`, PostgreSQL 17 | Independent tmpfs; ledger 001–012; 442 reviewed-pack questions |
| Disposable preview sandbox | `dbcas-preview-sandbox-6efac65d` | Independent tmpfs; separate sandbox network; readiness passes |

The actual Compose services are `db` and `sandbox`; both original containers
were already running. No Compose recreation or initialization was necessary.
Their IDs and complete mount metadata match the initial inspection. Compose
does not define Docker healthchecks for these two development services;
readiness here is established by actual authenticated PostgreSQL queries.
Persistent migration 001–011 checksums match, and both the 012 ledger row and
`question.original_locale` column remain absent.

### D. Backend

The existing virtual environment passes `pip check`. Host runtime is Python
3.14.5; the existing dependencies were reused. The backend runs the supported
`python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` command in a managed
background process. Final listener PID: **20836**. There is one listener at 8000.
`/readiness` returns `ready` with both `database` and `sandbox` true; OpenAPI
contains 67 paths and no `/__test` routes.

The migration runner is explicit, not an API startup hook. The ORM and schema
readiness query require `question.original_locale`, so the newest application
was never started against the protected pre-012 database. Only the disposable
preview received explicit migrations. Its child environment was separately
validated: live AI credentials and automatic question translation are disabled.
The original `.env` and project secrets are unchanged.

### E. Frontend

The existing Node 24.16.0/npm 11.13.0 dependencies were reused. Vite runs with
`npm run dev -- --host 127.0.0.1 --port 5173 --strictPort` in a managed process.
Final listener PID: **20944**. The configured same-origin `/api` proxy reaches
the backend at 8000; frontend login and proxied API ping both return HTTP 200.
There was no port fallback. Test-only ports 8100 and 5174 have no listeners
after teardown.

### F. Browser verification

A real Chromium preview smoke authenticated both disposable principals and
verified Administrator cohort overview, question bank, curriculum/concepts,
assessments, grading review and account management; Learner dashboard,
available assessments, history, cumulative competency and settings. Both roles
switched English → Vietnamese → English. The preview smoke observed no failed
API responses or page exceptions, and its screenshots were visually reviewed.

Preview identities are `release-admin@test.dev` and `preview-learner@test.dev`.
They use the existing release-test fixture password from
`backend/tests/release_server.py`; no password or access token is reproduced
in this report. No persistent account was rebootstrapped or given new privileges.

The in-app Browser lacked its required execution tool in this session, so
verification used the repository's installed real Playwright browsers. Each
browser's separate normal-application suite also verified the actual
`app.main:app` entrypoint, authentication, refresh/logout, role promotion and
revocation with immediate token enforcement, and role boundaries.

### G. Bilingual functionality

All four engines passed the single question editor, Vietnamese and English
authoring, source-language detection, optional manual translations, reviewed
translation display, stale translation invalidation, question preview, named
curriculum mappings and accessible layouts. Learner language changes preserve
answers, question identity and expiry; refresh/draft/resume and recorded
evidence are covered. SQL identifiers, reference SQL, datasets and original
essay criteria remain intact.

Machine translation draft preparation was verified with mocks only: an
unreviewed draft is not persisted as reviewed content. Backend provider-boundary
tests use mocked transport; the browser draft case uses a mocked response.
Live automatic translation and live essay-provider quality were not claimed.
No live external AI provider was called.

### H. Backend tests

From `backend`, the actual standard command
`.venv/Scripts/python.exe -m pytest -q` passed against the documented disposable
Docker PostgreSQL 17 and real resource-limited SQL sandbox:

**1008 passed, 0 failed, 0 skipped**, in 420.97 seconds of pytest execution.
Authentication, RBAC/secure role management, bank/localization/translation,
assembly, SQL execution/security, mocked essay grading, human verification,
publication policies, competency/gaps, migration and security cases are included.

The first fresh run was 1005 passed. A verified cleanup defect was then fixed:
Docker's native CLI reports missing objects in lowercase, while the existing
helper matched uppercase text only. The helper now recognizes object/container
absence case-insensitively. Four message forms are covered, adding
three cases. Existing foreign-label, volume/bind mount refusal, connection
failure and timeout assertions remain intact. The final complete 1008-case run
and every browser gate used the same verified final harness hashes.

There is one Starlette TestClient deprecation warning. App compilation/import
and dependency checks passed; no dependency reinstall was performed.

### I. Frontend and E2E

**Frontend unit tests: 260 passed / 260, across 32 files. Production build:
PASS, npm exit 0.** The existing large-chunk warning remains informational.
The build receipt initially hit a Windows encoding error while printing its
already-successful output; the private reporter was corrected to UTF-8 and the
actual successful build log/exit code were verified.

| Browser | Complete standard suite | Complete normal-application suite | Suite durations (standard / normal) |
|---|---|---|---|
| Chromium | 40 passed / 0 failed / 0 skipped / 0 flaky | 8 passed / 0 failed / 0 skipped / 0 flaky | 17.48 / 3.39 min |
| Firefox | 40 passed / 0 failed / 0 skipped / 0 flaky | 8 passed / 0 failed / 0 skipped / 0 flaky | 22.18 / 3.77 min |
| WebKit | 40 passed / 0 failed / 0 skipped / 0 flaky | 8 passed / 0 failed / 0 skipped / 0 flaky | 24.03 / 4.29 min |
| Microsoft Edge | 40 passed / 0 failed / 0 skipped / 0 flaky | 8 passed / 0 failed / 0 skipped / 0 flaky | 17.23 / 3.41 min |

All heavy suites ran sequentially, with one Playwright worker and zero retries.
These are **192 full-suite browser executions**, plus the separate targeted
Chromium **2 passed / 0 failed / 0 skipped / 0 flaky** recheck of the two
previous failures. The original reviewed-translation and supervisor cases
also passed in every complete standard browser run. Their earlier search and
select-control corrections were preserved; no assertions were weakened.

All 194 per-case diagnostic records contain zero page exceptions and zero
HTTP 5xx responses. Expected invalid-login, insufficient-pool, unpublished
evidence and conflict responses are retained and were reviewed against the
test actions. Navigation cancellations, Firefox cache cancellation events and
the deliberately lost submission response are retained separately; they are
not silently counted as successful requests. Normal-application journeys
verify actual unavailable-AI behavior and human correction/publication.
WebKit coverage establishes that engine's compatibility, not branded Safari
on Apple hardware.

### J. Migration 012

**GO for later owner-authorized development activation. No persistent
activation occurred.** All mandatory local integration gates above passed.

The existing verified custom archive (336828 bytes, SHA-256
`fc46986a89033d7cd189029a5ae3645e9910c198ef0ffde2e25289d8fd37e74e`)
was restored into a uniquely labeled, disposable Docker PostgreSQL 17.11
database. All 33 restored table counts/fingerprints matched the protected
source before migration. The checksum runner applied **only 012**, then
returned no pending migrations on rerun.

All 32 business-table fingerprints are preserved after migration; the old
question comparison excludes only the new `original_locale` column. All 442
old questions default to English, and all 442 reviewed translations remain
current. Snapshots, attempts, grading evidence, account/role records and
competency data are unchanged. Eleven existing ledger rows, including their
timestamps/checksums, are unchanged; the disposable ledger has exactly 12
valid rows. All constraints are validated and all indexes valid/ready. The
owned restore container was stopped and removed without volume deletion.
New Vietnamese originals, English translations and original-language grading
are additionally covered by the complete backend and browser gates.

Later activation must use the already documented
[owner backup/migration/integrity procedure](docker-stabilization-acceptance-20261023.md#f-migration-012-readiness),
including quiescing writes and re-verifying a current backup before applying
the checksum runner and matching application. This GO is a recommendation,
not execution of that operation.

### K. Data preservation and final health

Fresh enforced-read-only snapshots before and after testing match the latest
recovery baseline for **all 33 public tables**, not only selected counts.
Intermediate comparisons after Chromium and after the complete standard
browser matrix also match. Selected final protected counts:

| Data | Count |
|---|---:|
| Accounts / account-role links / profiles | 18 each |
| Questions / translations | 442 each |
| Assessments / sessions / attempts | 5 / 18 / 109 |
| Competency results / gaps | 95 / 26 |
| Grade reviews / migration ledger rows | 0 / 11 |

All 48 diagram artifacts, all 43 academic DOCX originals, existing environment
files, schema and migration bytes match their protected hashes. Original
container IDs and mounts, including `dbcas_db-data` and the sandbox's existing
volume, are unchanged. Both persistent services and both preview containers
are running, with zero restart counts and no OOM flag.

The two pre-reboot orphans, `dbcas-test-f75f4e57` and
`dbcas-sandbox-fa21e8ee`, were inspected by exact ID, completed-run ownership
label, stopped status and tmpfs/no-persistent-mount metadata before removal.
Their absence is verified. All newly created regression/migration containers
were also cleaned by ownership; no `dbcas.test-run` container remains. The two
explicitly labeled preview containers are intentionally retained for manual
inspection. No volume, image, foreign container or project file was pruned.

Final HTTP liveness, dependency readiness, frontend login and proxied ping
passed. Only the intended API/Vite listeners at 8000/5173 remain; no duplicate
development server or test listener was left behind.

### L. Git status and reviewable changes

Branch **main**, HEAD **5db597930cb512879ad1b9c577e6e88d33962b47**.
Final state remains **45 modified tracked files, 67 untracked files, 0 staged,
0 deleted**. Every one of the original 112 review paths is present. All
previously modified tracked-file bytes are unchanged in this continuation.

Only these existing untracked paths were updated by this task:

- [Docker cleanup helper](../backend/tests/docker_runtime.py): recognize the
  native CLI's missing-object/container error casing while retaining ownership
  and persistent-mount guards.
- [Cleanup regression cases](../backend/tests/test_docker_runtime.py): exercise
  the four observed/supported missing-object/container message forms.
- This existing recovery report: preserve earlier history and append the new
  post-reboot result/navigation. Its original bytes are also retained privately.

The other **109/112 recovered paths are byte-identical**. No stash, reset,
clean, commit, push, merge or deployment was performed. No workflow was added;
no database backup/key artifact is in the Git inventory. Project secrets were
neither regenerated nor printed as resolved configuration. Credentials and
fixture tokens remain out of this report. `git diff --check` and the local
documentation-link check are part of the final verification receipts.

Private receipts are under `../_review/post-reboot-recovery-20261023/` outside
the repository: baseline/source hashes, timed health samples, final persistent
comparison, volume/process/listener metadata, preview smoke screenshots,
per-gate commands/logs/JSON, migration restore comparisons, sanitized network
diagnostics, cleanup receipts and final safety/link checks. Playwright traces
and fixture authentication material must remain private outside Git.

### M. Remaining blockers

The newest code still cannot use the persistent 001–011 schema until the owner
separately authorizes migration 012 activation. That is the only remaining
startup limitation. The working disposable preview is left running for manual
inspection. No requested regression or infrastructure gate remains failing.

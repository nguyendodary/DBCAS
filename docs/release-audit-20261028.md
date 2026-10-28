# Final release audit, document verification and publication decision — 28 October 2026

This record is the last audit before publication. It re-ran every gate the repository documents,
verified the four academic deliverables against the bytes that actually exist today rather than
against any earlier report, traced every embedded figure, and re-checked the remote before
touching it. Nothing here is carried over from a previous run: each row was measured on
28 October 2026 and names the artefact that proves it.

Scope of change: **documentation only.** No application code, migration, schema, blueprint row,
question-bank row or sandbox rule was modified by this audit. The persistent development database
`dbcas-db` stayed up for the whole session and was never written to.

Companion records: [academic-documents-ver12-20261027.md](academic-documents-ver12-20261027.md)
(edits applied to the four documents),
[academic-edit-ledger-20261027.md](academic-edit-ledger-20261027.md) (every edit by address),
[figure-update-ledger-20261027.md](figure-update-ledger-20261027.md) (every figure by hash),
[documentation-alignment-20261027.md](documentation-alignment-20261027.md) (repository-side
mismatch matrix), [testing-and-release-gates.md](testing-and-release-gates.md) (the gate list this
record is scored against).

---

## 1. Revision and remote state

| Check | Value |
|---|---|
| Local `HEAD` at the start of the audit | `24bd28d8faa9c654a351ca174144ea10471dded5` |
| `origin/main` as the remote actually reports it | `633fea3079a8631532cd35f9a5de49c7ddb32b61` |
| Merge base with `origin/main` | `633fea3` — identical to the remote tip |
| Commits ahead / behind (`git rev-list --left-right --count`) | `0 12` |
| Upstream tracking branch for `main` | **none configured** (`git config branch.main.remote` exits 1) |
| Remote | `https://github.com/nguyendodary/DBCAS.git` |

The remote was queried live (`git ls-remote origin main`) instead of trusting the cached tracking
ref or any earlier statement in this session's history. The server's tip equals the merge base, so
the pending push is a **strict fast-forward**: no divergence, therefore no integration plan, no
rebase and no force of any kind is needed or permitted. Because no upstream is configured, the
first publication is `git push -u origin main`.

Twelve commits were pending when this audit started, not seven as an earlier record stated; that
count was accurate when it was written and has since been superseded by five more documentation
commits. In order: `056ae8c`, `c970bb7`, `f79adb0`, `3fef3df`, `3f3ef0c`, `73f49a7`, `6193a9e`,
`97a944e`, `35f2c44`, `853a5ae`, `ba7d042`, `24bd28d`. Two are `build:` (the pinned
diagrams-as-code toolchain and the generated inventories); the rest are `docs:`.

The gate document requires that the revision under review is the revision that was run
("a green run on a different revision is not evidence for it"), so the relationship between the two
has to be exact rather than assumed. Everything in §2 was executed against the working tree at
`24bd28d`. This audit adds `docs/release-audit-20261028.md` and corrects two existing documents;
`git status --porcelain` before the commit shows those three markdown files and nothing else, so the
code, migrations, dependency manifests, fixtures and scripts in the published tree are byte-identical
to the ones that were tested. The checks that actually read `docs/**` were re-run on the finished
tree and repeated what they had said before any prose landed: `diagrams:check` **PASS** ("10 diagram
model/render inventories; 34 tables, 49 foreign keys, `schema.sql` and 14 migration fingerprints
match", "checked 9 Graphviz DOT, 2 Mermaid and 0 PlantUML source(s)"), `inventory:check` **OK**, and
the three static backend gates — `compileall -q app/`, `from app.main import app` (13 routes) and
`pip check` — all exit 0. The full browser and pytest suites were not re-run on it, because nothing
they exercise changed; that limitation is stated here rather than hidden behind the word "gate".

---

## 2. Automated gates, in the documented order

`docs/testing-and-release-gates.md` lists four gates. Every one was run on this revision on
28 October 2026. Results, not recollections:

| # | Gate | Command | Result |
|---|---|---|---|
| 1 | Frontend install | `npm ci` | exit 0 |
| 1 | Frontend unit | `npm test` | **35 files / 281 tests passed**, 35.29 s |
| 1 | Frontend build | `npm run build` | exit 0, `✓ built in 568ms` |
| 1 | Frontend advisories | `npm audit` | **4 vulnerabilities (2 moderate, 2 high)** — see §2.1 |
| 2 | Backend suite | `.venv/Scripts/python.exe -m pytest -q` | **1109 passed**, 1 warning, 569.07 s, exit 0 |
| 2 | Byte-compile | `-m compileall -q app/` | exit 0 |
| 2 | Import | `-c "from app.main import app"` | exit 0, 13 routes, dev-default `JWT_SECRET` warning |
| 2 | Requirement graph | `-m pip check` | `No broken requirements found.` |
| 3 | Compose (development) | `docker compose config -q` | exit 0 |
| 3 | Compose (release) | `docker compose --env-file deploy/release.env.example -f docker-compose.release.yml config --no-env-resolution -q` | exit 0 |
| 4 | Browser, chromium | `DBCAS_BROWSER=chromium npm run test:e2e` | **53 passed**, 25.6 m, exit 0 |
| 4 | Browser, firefox | `DBCAS_BROWSER=firefox npm run test:e2e` | **53 passed**, 31.4 m, exit 0 |
| 4 | Browser, webkit | `DBCAS_BROWSER=webkit npm run test:e2e` | attempt 1: **1 failed / 52 passed**, 34.2 m; repeat: **53 passed**, 35.1 m — §2.4 |

Additional repository checks that the release process also depends on:

| Check | Result |
|---|---|
| `npm run diagrams:check` | **PASS** — 10 diagram model/render inventories; 34 tables, 49 foreign keys, `schema.sql` and 14 migration fingerprints match; 9 Graphviz DOT, 2 Mermaid, 0 PlantUML sources |
| `npm run inventory:check` | **OK** — `api-routes.json` and `frontend-routes.json` match their sources |
| `db/validate_question_localization.py` | **PASS** — 442/442 sources and owner targets, MCQ 326/326, SQL 67/67, ESSAY 49/49, 0 missing translations, 0 validation errors |
| `pip-audit` on the backend environment | **44 known vulnerabilities in 2 packages** — see §2.2 |

Evidence files, all outside Git: `_review/frontend_gates_20261028.txt`,
`_review/pytest_clean_20261028.txt`, `_review/static_gates_20261028.txt`,
`_review/pip_audit_20261028.txt`, `_review/toolchain_gates_20261028.txt`,
`_review/e2e_chromium_20261028.txt` and the per-browser directories
`_review/e2e-release-20261028-<browser>/`, plus `_review/browser_firefox_20261028.txt`,
`_review/browser_webkit_20261028.txt`, `_review/e2e-rerun-formal-webkit/` and
`_review/e2e-repeat-webkit/` for the journeys in §2.4.

**Interpreter substitution, stated plainly.** The gate document says to run the sequence "on Python
3.13/Node 24" and names `py -3.13` for the localization validator. That interpreter is not
installed on this workstation; the repository's own backend environment is **Python 3.14.5**
(`node v24.16.0`, `npm 11.13.0`, Docker `29.8.1`). The validator was therefore executed with the
same code the suite imports, not with the interpreter the document names. This is a deviation from
the written gate and is recorded as such rather than glossed over.

### 2.1 The frontend advisory result is not at the project's own standard

Two past records state a clean scan as the achieved state — `docs/bilingual-question-verification.md:96`
("`npm audit | PASS: 0 vulnerabilities`") and `docs/supervisor-implementation.md:723`. Today the
same command reports four advisories:

| Advisory | Package installed | Fix offered |
|---|---|---|
| GHSA-rq7h-c2jc-7f22 — files outside `server.fs.allow` may be served | `vite 8.3.2` (`"vite": "^8.3.1"`) | `8.3.5`, inside the declared range |
| GHSA-vfpm-58rq-9qcg — first 4 bytes leaked by `?vite-wasm-instance` | `vite 8.3.2` | `8.3.5` |
| two further advisories reached through the same dev server | `vitest 4.1.11` (`"vitest": "4.1.11"`, exact pin) | `4.1.12`, requires changing the pin |

Three facts decide what may be done about it:

- Both packages are **devDependencies**. The advisories concern the Vite *development server*; the
  release stack serves the built `dist/` through Nginx (`deploy/nginx.conf`,
  `docker-compose.release.yml`), so the shipped artefact does not run the vulnerable code path.
- The condition **already exists on `origin/main`**. `git log origin/main..HEAD -- frontend/package.json
  frontend/package-lock.json` returns nothing: none of the twelve pending commits touches a
  dependency file. Upgrading here would not be fixing something this push introduces.
- The gate document itself forbids the fast route: *"Do not run blind forced dependency upgrades.
  A clean scan is not a security proof."* (`docs/testing-and-release-gates.md:62`), and
  `CONTRIBUTING.md` rule 1 forbids mixing a dependency change into a documentation commit.

The correct remediation is therefore a **separate `build(frontend):` commit** that raises the pins,
followed by a full re-run of every gate — the browser journeys included, which cost ~26 minutes
each. That is an owner decision about sequencing, not something to smuggle into a documentation
release.

### 2.2 The Python advisory scan: two orphan packages, neither shipped

`pip-audit` exits 1 with **44 known vulnerabilities in 2 packages**:

| Package in the local venv | Advisories | Fix version | In `backend/requirements.txt`? | Required by anything installed? | Imported by `app/`? |
|---|---|---|---|---|---|
| `filelock 4.1.0` | 5 CVEs (`CVE-2026-1129xx`) | `4.2.1` | no | `Required-by:` empty | no |
| `pillow 12.3.0` | 39 CVEs/GHSAs | `13.0.0` | no | `Required-by:` empty | no |

`backend/Dockerfile:4-5` installs **only** `backend/requirements.txt`, so neither package exists in
the release image. These are undeclared leftovers in one developer's virtualenv — the document
tooling on this workstation uses the *separate* system Python for exactly that kind of work. The
remediation is to delete them from the local environment (`pip uninstall filelock pillow`), which
is a machine change, not a repository change, and is deliberately **not** performed by an audit
whose mandate is to leave the working environment as it found it.

### 2.3 One earlier backend run failed, and why

The first full `pytest` attempt reported **4 failed / 1105 passed** with `sandbox_unavailable` and
`ConnectionTimeout`. The cause was this audit's own concurrency: a `npm ci` for the frontend was
running at the same time, against the explicit instruction to *"Run full backend and browser gates
sequentially on constrained local Docker/WSL"*. The four tests were re-run alone (4 passed, 1.07 s),
then the entire suite was re-run with the machine idle: **1109 passed**. No test was skipped,
marked, xfailed or weakened to obtain that number; the failed run is kept as evidence of the
contention, not deleted.

### 2.4 The webkit journey failed once, and what that failure actually was

Firefox and webkit have been run before, but never against a revision that exists in Git.
`docs/phase-2-first-time-user-acceptance-20261026.md:39-46` records chromium, firefox, webkit and
msedge at 49/49 each on 26 October, and the paragraph beneath it (`:48`) says what was really tested:
*"All browser gates: HEAD `7ccdc44d…` **with the preserved uncommitted source**."* That commit
(`docs: publish verified activation release and correction record`, 25 October) is an ancestor of
`origin/main`, but the tree those passes belong to is not reproducible from any commit, which is
exactly what the gate document requires. Since then the suite grew from 49 to 53 tests and the
application source moved twice (`0b497f3`, `633fea3`). Both journeys were therefore run here against
the current tree, in the documented order.

Firefox: 53/53, exit 0, 31.4 m. Webkit, attempt 1: **52 passed, 1 failed**, exit 1, 34.2 m. The
failure was `first-time-user-grading.spec.js:401 › formal immediate: …`, and it failed on the last
line of the test only:

```
- Expected  - 1          + Array [
- Array []               +   "/127.0.0.1:5174/api/v1/sessions due to access control checks.",
                          ]
  > 552 | expect(errors).toEqual([])      // collected from page.on('pageerror')
```

Everything the test is *about* passed: the 10/2/1 mix, draft persistence across a reload, all three
sandbox rejections, the connection-failure banner and its recovery, duplicate replay, history and
competency, and the Axe scan of the cumulative page. What was collected is one WebKit page error.
The trace gives the full message, and it names the transport:

```
{"class": "BrowserContext", "method": "pageError",
 "error": {"message": "XMLHttpRequest cannot load http://127.0.0.1:5174/api/v1/sessions
                        due to access control checks."}}
```

Four things follow from that.

1. The blocked call is `GET /api/v1/sessions` — the sessions *list*. It is not the request this test
   deliberately aborts. The same diagnostics record that abort separately and correctly:
   `failedRequests: [{"method": "POST", "path": "/api/v1/sessions/7/submit",
   "error": "Blocked by Web Inspector"}]`, which is Playwright's own interception report.
2. Every call site for that list catches its rejection: `HistoryPage.jsx:24-30`,
   `AssessmentsPage.jsx:32-40` and `DashboardPage.jsx:169-178` each chain `.then(...).catch(...)` and
   fall back to an in-page error state. There is no unhandled promise here, so the message is the
   engine's report of a request Playwright's interception layer cancelled, not the application
   failing to handle a network error. WebKit phrases interception cancellations as access-control
   failures; Chromium and Firefox do not, which is exactly why the identical sequence is silent on
   those two engines.
3. Re-run alone on webkit, on a fresh disposable pair, with nothing else on the machine: **1 passed
   (46.9 s)**, same test, same tree (`_review/e2e-rerun-formal-webkit/`). The failure is therefore
   not a property of the test or of the build; it depends on what the shared browser engine is doing
   while an interception window is open.
4. A full repeat journey on an idle workstation, started after the failed attempt and after its
   containers had been released: **53 passed in 35.1 m** (`_review/e2e-repeat-webkit/`, whose JSON
   reporter records `expected: 53, skipped: 0, unexpected: 0, flaky: 0`), with the same test passing
   in the same position in the same file. Webkit therefore has one clean full run, one run with a
   single engine-reported page error, and one clean isolated re-run of the affected test — three
   measurements, not one.

Nothing was skipped, marked, filtered or relaxed to get any of these numbers: the failing attempt is
kept in `_review/e2e-release-20261028-webkit/` with its trace, screenshot and diagnostics, and the
isolated and repeat runs are additional evidence rather than a replacement for it.

---

## 3. Schema, migrations and the persistent database

- Structure is verified against code, not prose: `diagrams:check` validates **34 tables, 49 foreign
  keys, `db/schema.sql` and 14 migration fingerprints** and passed.
- Migration behaviour is covered inside the 1109 passing tests (`backend/tests/test_migrations.py`).
- Every browser journey ran on a **disposable, memory-only pair**. The chromium preflight proof
  (`_review/remediation/db-isolation-proof-chromium.json`) records run `28d4ff04f0644f56…`,
  `dbcas-test-d5a14835` on `postgres:17` reporting `170011`, `dbcas-sandbox-cff23c6b` on
  `dbcas-sandbox-test`, both with `/var/lib/postgresql/data:rw,size=256m` and
  `persistent_mounts: []`.
- **`probe_rows_in_persistent: 0`** — the account the API created during the preflight appeared in
  the disposable database and nowhere else. `persistent_is_separate: true`.
- No DROP, TRUNCATE, RESET, reseed or overwrite of any kind was issued. Direct database access
  during this audit was `SELECT` only, and the isolation helper
  (`backend/tests/query_release_scalar.py`) refuses anything that does not begin with `SELECT` and
  connects with `default_transaction_read_only=on`.
- `dbcas-db` was still `Up 3 days` at the end of the session. Nothing was pruned.

**A cleanup trap worth recording, because it wasted a container pair and would waste the next
reader's too.** Each browser journey provisions *two* disposable pairs: the one held open by the
process that imports `conftest`, and another that the Playwright `webServer` (`tests/release_server.py`)
creates when it imports `conftest` a second time. `tests/cleanup_release.py` removes exactly the pair
named by `DBCAS_TEST_MANIFEST` — and the webServer rewrites that manifest with its own two container
names. So the documented teardown cleans the webServer pair and leaves the holder pair running,
silently and with exit 0. `create_owned`'s only other safety net is an `atexit` handler, which does not
run when the holder is stopped by a signal. The pair therefore has to be removed from the run receipt
it wrote, `_review/docker-tests/<run-id>.json`, which is what this audit did:

```
DBCAS_TEST_MANIFEST=_review/docker-tests/ef1db42e2c6b4f258df754945eddc510.json \
  .venv/Scripts/python.exe tests/cleanup_release.py        -> exit 0
docker ps --filter name=dbcas-                             -> only the pre-existing stack remains
```

`cleanup_owned` re-reads the `dbcas.test-run` label before touching anything and refuses a container
whose label differs or that carries a persistent mount, so a mistyped manifest removes nothing. No
repository change is proposed here: the behaviour is a harness property this audit had to work around,
and the fix belongs to whoever owns the browser gate, not to a documentation release.

One harness inconsistency worth recording: `frontend/e2e/global-setup.js` resolves
`DBCAS_TEST_MANIFEST` to a default path but does not export it, while
`backend/tests/query_release_scalar.py:28` reads it from the environment with `os.environ[...]` and
no default. The preflight therefore fails with an opaque `{"error":"KeyError"}` unless the operator
sets the variable to an **absolute** path, which `docs/testing-and-release-gates.md:168` does tell
you to do. The sibling scripts `cleanup_release.py:7` and `release_server.py:30` default it
instead. No code was changed here — the gate is run the documented way — but the asymmetry is a
real papercut for the next person.

---

## 4. The four v1.2 deliverables

Each document was opened in Word with `ReadOnly=True` and `OpenAndRepair=False`, measured, exported
to PDF, then closed with `wdDoNotSaveChanges`; the file was hashed before and after.
`_docread/release_docs_20261028.py`, full output
`_docread/release_audit_20261028_stdout.txt`, per-document JSON
`_docread/release_audit_20261028/docx_verification.json`.

| Deliverable | SHA-256 | Pages (Word) | Pages (PDF) | Expected | Paragraphs / tables | Inline shapes | Revision rows | Captions rendered |
|---|---|---|---|---|---|---|---|---|
| `C1SE.70_ProposalDocument_DBCAS_ver1.2.docx` | `efabc6f8…0dcf382b` | 57 | 57 | 57 | 1122 / 21 | 5 | 3 | 24 |
| `C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx` | `034d91c9…adc6dff73` | 62 | 62 | 62 | 1869 / 58 | 9 | 3 | 60 |
| `C1SE.70_UserStoryDocument_DBCAS_ver1.2.docx` | `abb68f78…cfbc6d34` | 23 | 23 | 23 | 472 / 7 | 1 | 3 | 3 |
| `C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx` | `5754fa8d…9ebe1bf0` | 33 | 33 | 33 | 2444 / 39 | 2 | 3 | 38 |

All four: opened **without a repair prompt**, `sha256 after Word` **UNCHANGED**, all three
Revision History comments exactly `Update`, version `1.2` displayed, and no media relationship
pointing at a missing part. Page counts match the numbers the owner previously reported, verified
independently rather than repeated.

Full checksums as published:

```text
efabc6f8db968de36ede224e2c155c3d4e6930e037b3629ddde57adf0dcf382b  C1SE.70_ProposalDocument_DBCAS_ver1.2.docx
034d91c9c1d09e4059283e64e33e01d2627fc5309ae7441e76a8568adc6dff73  C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx
abb68f78b2baa6efd49526ad7a0395e274ed69ab137eaf4a3215e12dcfbc6d34  C1SE.70_UserStoryDocument_DBCAS_ver1.2.docx
5754fa8d8aff0fa4cf99f11e2a6d738202a0e9cd3459f7eee2b1a71e9ebe1bf0  C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx
```

### 4.1 Contents, lists and fields

TOC, List of Tables and List of Figures were verified against the rendered page numbering that Word
itself prints in the footer (`_docread/toc_check_20261028.py` over the four PDFs above):

| Deliverable | TOC entries | LOT entries | LOF entries | List pages |
|---|---|---|---|---|
| Proposal | 36 ok / 0 mismatch | 17 ok / 0 | 4 ok / 0 | TOC p5–6, LOT p7, LOF p8 |
| Architecture Design | 17 ok / 0 | 51 ok / 0 | 8 ok / 0 | TOC p5, LOT p6–7, LOF p8 |
| User Stories | 7 ok / 0 | 3 ok / 0 | — (no figures) | TOC p5, LOT p6 |
| Database Design | 43 ok / 0 | 36 ok / 0 | 2 ok / 0 | TOC p4–5, LOT p6–7, LOF p5 |

**Total 224 entries: 224 correct, 0 mismatched, 0 not found** — the same 224 references the
27 October record claimed, now re-measured from this month's render. Separately,
`_docread/cached_vs_actual_20261028.py` compares the field results cached *inside* each DOCX (what
a reader sees before pressing anything) with that render: **224 cached entries, all SAME, 0 page
drift, 0 stale titles.** A reader does not need to press F9.

### 4.2 Two apparent defects that were the auditor's, not the documents'

Recorded because both were reported internally before being understood.

- **Database Design "no Revision History found".** The table exists and is correct; its header is
  `Version | Person(s) | Date | Description`, not `Version | Date | Comments`, and its version
  cell is where `1.2` lives (the prose never says "Version 1.2"). The detector was widened to
  locate the columns positionally and to read the displayed version from table cells as well as
  prose. The document was never wrong and was not touched.
- **Database Design "4 media parts but 3 references".** `word/media/image1.png` and
  `image2.png` are byte-identical (`12c89edc68a3…`, 16,805 B). The second is the legacy VML
  fallback for the same shape: `<v:imagedata r:id="rId15">` beside the DrawingML `r:embed`. All
  four parts resolve; none is orphaned; the count difference is a format artefact. This also
  explains why the document reports 3 body embeds but only 2 `InlineShapes` — the cover mark is
  drawn in a floating group, not inline.

### 4.3 Where the deliverables live, and why they are not in Git

The four `.docx` files are workspace-root files, siblings of the repository, exactly where they
have always been. This audit was asked to place the active deliverables under version control, and
the honest answer is that the repository's own policy forbids it:

> `CONTRIBUTING.md`, Quy tắc 3: *"Không commit file môi trường (`.env`) hay tài liệu dự án
> (docx/pdf) vào repo."* — do not commit environment files or project documents (docx/pdf) into
> the repo.

An established policy that excludes binary academic documents is followed and reported, not
bypassed. The four files were therefore **not copied into the repository**, not moved and not
renamed; their exact bytes are named by the SHA-256 list above so the published record still
identifies precisely which deliverables were audited. The intermediate PDFs, render crops and Word
lock files produced along the way stayed in `_docread/` and `_review/`, both outside Git.

---

## 5. Diagram audit

`_docread/diagram_trace_20261028.py`, `_docread/figure_dpi_20261028.py`,
`_docread/media_map_20261028.py`; outputs `_review/diagram_trace_20261028.txt`,
`_review/figure_dpi_20261028.txt`, `_review/media_map_20261028.md`.

**Inventory.** The four documents carry **19 embedded raster parts, 13 distinct digests**: 14
numbered figure placements and 5 cover-mark placements (the Architecture cover appears twice in
that document and once more as a VML fallback in Database Design). Word places 17 of them as
inline shapes; the Database Design cover is a floating VML group.

| Placement | Figure | Media part | Pixels | Placed size | Effective | Digest |
|---|---|---|---|---|---|---|
| Proposal | Fig 1 Sprint roadmap | `image2.png` | 4712×3497 | 439.4×326.0 pt | **772 ppi** | `46ed48ce323a` |
| Proposal | Fig 2 System Context | `image3.png` | 1431×1061 | 439.4×324.5 pt | **234 ppi** | `2794fabf0d75` |
| Proposal | Fig 3 Logical architecture | `image4.png` | 3200×3160 | 432.0×430.2 pt | **533 ppi** | `bdb30a4e15d4` |
| Proposal | Fig 4 Assessment pipeline | `image5.png` | 1342×762 | 439.4×249.4 pt | **220 ppi** | `ef593781ce8c` |
| Architecture | Fig 1 Use Case | `image2.png` | 3000×3300 | 439.4×483.3 pt | **492 ppi** | `081cc67a9e34` |
| Architecture | Fig 2 System Context | `image3.png` | 1431×1061 | 439.4×325.6 pt | **234 ppi** | `2794fabf0d75` |
| Architecture | Fig 3 Container | `image4.png` | 1444×1418 | 412.5×405.0 pt | **252 ppi** | `13457982a696` |
| Architecture | Fig 4 Component | `image5.png` | 2361×1423 | 658.8×397.4 pt | **258 ppi** | `46869d477901` |
| Architecture | Fig 5 Module view | `image6.png` | 3300×2050 | 645.1×400.3 pt | **368 ppi** | `98ef246cebce` |
| Architecture | Fig 6 Allocation | `image7.png` | 1331×1283 | 330.0×318.0 pt | **290 ppi** | `85d0003d1e1b` |
| Architecture | Fig 7 Conceptual ER | `image8.png` | 3251×1677 | 639.8×330.0 pt | **366 ppi** | `0e35cb0e44ac` |
| Architecture | Fig 8 Table relationships | `image9.png` | 3440×2080 | 620.2×375.0 pt | **399 ppi** | `c2b308b1e5e0` |
| Database Design | Fig 1 Conceptual ER | `image3.png` | 3251×1677 | 681.0×351.3 pt | **344 ppi** | `0e35cb0e44ac` |
| Database Design | Fig 2 Table relationships | `image4.png` | 3440×2080 | 681.0×411.8 pt | **364 ppi** | `c2b308b1e5e0` |
| Cover marks | not a figure | Proposal/UserStory `image1.png`, Architecture/Database `image1`–`image2.png` | 454×134 / 420×124 | ~148×44 pt | 212–220 ppi | `7610f45c2c7c`, `12c89edc68a3` |

Read honestly, eight of the seventeen inline placements are at or above 300 ppi and six numbered
figures are below it. The ledger already recorded three of them (252/258/290 for Figures 3, 4 and
6) and this audit reproduced those numbers exactly; the previously **unmeasured** ones are the
System Context at 234 ppi in both documents, the Proposal assessment pipeline at 220 ppi, and the
institutional cover marks at 212–220 ppi. `docs/academic-documents-ver12-20261027.md:216` described
the embedded artwork as "the team's own 300 dpi drawings" — true of how the matplotlib sources were
saved (`fig.savefig(path, dpi=fig.dpi)`), but readable as a claim about what a reader sees, so on this
revision it reads "each saved at the 300 dpi of its matplotlib source", says explicitly that that is
the save-time density rather than the resolution after Word scales the placement, and points here for
the placement-relative measurement. This table is that measurement. Raising the
low ones would mean enlarging rasters whose detail is already fixed — exactly the "upscale and call
it quality" move the owner forbade — so they were measured, not inflated.

**Provenance.** Each figure was traced from the 23 October baseline (`docs/diagrams/inventory.md`)
through every `before -> after` arrow in `docs/figure-update-ledger-20261027.md` to the bytes
embedded today. Nine of eleven baselines resolve by that grammar alone:

| View | 23 Oct baseline | Live bytes | Path |
|---|---|---|---|
| System Context | `2794fabf0d75` | `2794fabf0d75` | never edited; identical in Proposal Fig 2 and Architecture Fig 2 |
| Use Case | `081cc67a9e34` | `081cc67a9e34` | never edited |
| Conceptual ER | `0e35cb0e44ac` | `0e35cb0e44ac` | never edited; identical in Architecture Fig 7 and Database Fig 1 |
| Assessment pipeline | `ef593781ce8c` | `ef593781ce8c` | never edited |
| Table relationships | `618b2479a1d6` | `c2b308b1e5e0` | 1 edit; identical bytes in Architecture Fig 8 and Database Fig 2 |
| Logical architecture | `fa0e6f217935` | `bdb30a4e15d4` | 1 edit |
| Sprint roadmap | `ca2518ad1f51` | `46ed48ce323a` | 1 edit (header rule) |
| Module view | `799e9149e945` | `98ef246cebce` | 1 edit (version token) |
| Component | `09b28ece8b06` | `46869d477901` | 2 edits (27 Oct material update, 28 Oct labels) |
| Container | `040acf4a4581` | `13457982a696` | 2 edits, see below |
| Allocation | `1918f7591e4f` | `85d0003d1e1b` | 2 edits, see below |

The last two initially looked unresolved, because the ledger writes that step in a different
notation: the 28 October typography pass names its outputs by 16-hex digests
(`1ea5eddafc7411cc`, `03e844fad662ff85`) instead of a 12-hex `->` arrow. The chain closes on bytes,
not on prose:

```text
_docread/pre_typography_backup_20261028/image4.original.png  040acf4a4581e8c0…  == 23 Oct Container baseline
_docread/new_typo/image4.fixed.png                           1ea5eddafc7411cc…  == arrow source 1ea5eddafc74
ledger 1ea5eddafc74 -> 13457982a696                          == live Architecture Fig 3 bytes
_docread/pre_typography_backup_20261028/image7.original.png  1918f7591e4ff81e…  == 23 Oct Allocation baseline
_docread/new_typo/image7.fixed.png                           03e844fad662ff85…  == arrow source 03e844fad662
ledger 03e844fad662 -> 85d0003d1e1b                          == live Architecture Fig 6 bytes
```

So all eleven named views are accounted for and every figure in the delivered documents has an
identified origin and an edit history. The dated ledger was **not** rewritten to make the grammar
uniform; this table is the completion of it.

**Diagrams-as-code are current with code.** `npm run diagrams:check` verifies each committed SVG
against the digest of its source text and each model against the repository's own DDL —
"10 diagram model/render inventories; 34 tables, 49 foreign keys, `schema.sql` and 14 migration
fingerprints match" — and passed, so `docs/diagrams/*.dot`/`*.json`/`*.svg` cannot have drifted from
each other or from the schema. That is a *semantic* consistency check; it is not a claim that the
embedded PNGs are rendered from those sources. `docs/academic-documents-ver12-20261027.md` §5.2
records why they are deliberately different renderings (aspect ratios diverge by up to 124%) and
the decision to keep every embedded figure byte-identical.

**Version strings left the diagrams only.** The 28 October pass removed fourteen technology
versions from inside figure rasters (`PostgreSQL 17` ×7, `Python 3.13` ×2, one each of `React 19.3`,
`Vite 8`, `Tailwind CSS 4`, `Chart.js 4.5`, `FastAPI 0.141`). Raster pixels are not in the PDF text
layer, so every version token still found in the rendered text must be prose. Measured over the
four release PDFs:

| Token | Proposal | Architecture | Database | User Stories |
|---|---|---|---|---|
| `PostgreSQL 17` | 6 | 16 | 3 | 1 |
| `Python 3.13` | 0 | 4 | 1 | 0 |
| `FastAPI 0.141` | 0 | 1 | 1 | 0 |
| `React 19.3` | 1 | 1 | 1 | 0 |
| `Vite 8` | 1 | 1 | 1 | 0 |
| `Tailwind CSS 4` | 0 | 1 | 1 | 0 |
| `Chart.js 4.5` | 0 | 1 | 1 | 1 |

Nothing that a reader needs in order to reproduce the system was removed.
Evidence: `_review/version_prose_20261028.txt`.

**Diagram decisions still held open by the owner**, unchanged by this audit and restated so they
are not lost: H3 — the System Context model carries no flow for the fourth provider task family
(translator), proposed as C52/C53 but not added to an academically scrutinised, hand-authored SVG;
H5 — `docs/diagrams/components.dot` node `s1` still says "configurable duration", which is true of
the stored column and the session timer but not of the Administrator API (`schemas.py` fixes 60).
Both are in `docs/academic-reconciliation-20261027.md` awaiting a decision, not silently patched.

---

## 6. Formal assessment mix: what the code actually ships

`backend/app/services/blueprints.py:23-30` defines six `THEORY_AREAS` — Performance, PostgreSQL
Administration, PostgreSQL Concurrency, PostgreSQL Performance, PostgreSQL Security, PostgreSQL
Server Programming — and `desired_mix()` gives them **10 MCQ / 0 SQL / 3 Essay**, while every other
area gets **10 / 2 / 1** (`max_questions` 13, `target_sql` 2, `target_essay` 1, mirrored by
`Literal[13]`, `Literal[2]`, `Literal[1]` in `schemas.py` and locked by
`tests/test_assessment_blueprints.py`).

`docs/requirements-decisions.md:7` states the owner-approved contract as "60 minutes, 10 MCQ, two
SQL, one Essay". Re-running the read-only bank probe on 28 October
(`_docread/feasibility_probe_20261027.sql` against `dbcas-content-clone` / `dbcas_clone`,
713 questions / 82 concepts / 872 links; output
`_review/feasibility_probe_20261028.txt`) gives the reason:

- the query for SQL items **in any status** across the six theory areas returns **`(0 rows)`** — not
  zero approved, zero *at all*;
- bank-wide SQL is concentrated in nine areas: PostgreSQL Querying 65, SQL Querying 23, PostgreSQL
  Functions 13, Database Design 8, SQL Foundations 8, then Data Definition, Data Manipulation,
  Data Types and Querying — and exactly the six theory areas show 0/0/0;
- the same six areas carry 10–13 MCQ families and 2–4 Essay families per band, so 10/0/3 is
  satisfiable and 10/2/1 is not, for them, without authoring new SQL items.

The file's own comment states the engineering reason: the read-only sandbox cannot honestly execute
`EXPLAIN`, index DDL, configuration, backup, transaction-control or server-programming statements,
so no SQL practical is scheduled for those areas.

Conclusion, without overclaiming in either direction: **10/2/1 is the published contract and is
implemented for the areas that can support it; it is not fully implemented bank-wide, and this
audit does not claim it is.** Changing it would mean either writing SQL questions (authorship, an
owner decision) or narrowing the requirement (also an owner decision). Amendment A4 and the two
resolution paths remain in `docs/academic-reconciliation-20261027.md`. No blueprint behaviour was
changed and no SQL question was manufactured to make a document read better.

---

## 7. Hygiene

**Personal paths.** `git grep -l -i <user> HEAD` finds 87 tracked files: 86 under
`_content/expansion-20261024/generated/`, all already published on `origin/main` before this task,
and exactly one introduced by the pending commits — `docs/documentation-alignment-20261027.md`,
added by `3fef3df`, whose "Space-safe Windows paths" bullet quoted the absolute working-copy path.
That sentence has been rewritten to describe the property (a path containing a space) without the
path. After this commit the tracked tree holds 86 such files and **no new leak**; zero added lines
in the pending diff contain the path.

History is **not** rewritten to chase a string that is already committed locally: `git log -S`
shows `3fef3df` as the only pending commit that introduced it, and amending or rebasing published
or pre-existing commits for cosmetic consistency is forbidden by the release instruction. The
final state of `main` is what this change controls.

**Secrets and credentials.** No `.env` is tracked (`.gitignore:20`); no key material, token or
provider credential appears in any pending diff — a high-signal scan over the whole pending diff
returns 0 matches. Browser traces and screenshots, which can contain disposable fixture tokens,
stay under `_review/` outside Git. The `JWT_SECRET is the development default` line emitted by the
import check is the application correctly refusing to pretend it is configured; the release stack
takes the value from `deploy/release.env.example`-shaped configuration and
`docker-compose.release.yml` resolves it at deploy time.

**Documentation links.** Re-scanned on this revision after every edit in this record landed: 41
documents (`README.md`, `CONTRIBUTING.md`, `AGENTS.md` and every `docs/**/*.md`), 235 relative links,
**0 broken** — `SECTION 9 LINKS: PASS`
(`_docread/links_20261028.py`). The 27 October scan in `documentation-alignment-20261027.md` saw 35
documents and 211 links; the 24 new links are the records added since, including the ones pointing
into this file.

**What was deliberately not committed.** No `.docx`, no PDF, no render crop, no Word lock file, no
`_docread/` or `_review/` scratch, no snapshot directory, no database dump, no dependency change.
The only repository changes in this audit are the two documentation corrections described above and
this record.

---

## 8. Corrections this audit made to its own earlier findings

An audit is only worth as much as its willingness to retract. Six claims in this session were wrong
and are superseded by the measurements above:

1. *"No repository policy excludes binary academic documents."* Wrong. The first check looked at
   `.gitattributes` and LFS and missed `CONTRIBUTING.md` rule 3, which excludes exactly this. The
   policy was then followed rather than bypassed (§4.3).
2. *"Database Design has no Revision History and no displayed version."* Wrong — a detector that
   matched only one table layout (§4.2).
3. *"The post-edit figure checksums are carried by no committed ledger."* Wrong —
   `docs/figure-update-ledger-20261027.md` records every before/after pair, including the 28
   October label pass (§5).
4. *A 4-failure backend run as evidence of a broken build.* Wrong — self-inflicted resource
   contention from running `npm ci` concurrently (§2.3).
5. *"Firefox and webkit have never been run on this repository."* Wrong as written: the 26 October
   record runs all four browsers. What is actually true, and what §2.4 now says, is that those runs
   belong to an uncommitted working tree and so cannot certify this revision.
6. *"Eight of seventeen placements reach 300 ppi, so the documents' claim of 300 dpi artwork is
   fine."* Not fine — readable as a placement claim that the measurement does not support. The
   sentence in `academic-documents-ver12-20261027.md` now separates save-time density from
   placement resolution instead of being defended in prose here (§5).

---

## 9. Release decision

**Everything this audit was asked to verify is verified, and one required gate is not clean.**

Passed on the current tree, measured rather than recalled: the frontend gate (install, 281 unit
tests, build), the backend gate (1109 tests, byte-compile, import, requirement graph), both compose
configs, the localization validator at 442/442, `diagrams:check`, `inventory:check`, all four
document deliverables against their own bytes (§4), every embedded figure against its provenance and
its effective resolution (§5), the assessment mix against the code that produces it (§6), and the
hygiene scan (§7). The remote is a strict fast-forward and no history was rewritten to keep it that
way.

Not clean: browser gate 4 on webkit produced one failing attempt out of two full runs
(§2.4). The application behaved correctly in that attempt — every functional assertion in the test
passed — and the collection that tripped is an engine-level report of a request Playwright's
interception layer cancelled. The repeat run and the isolated re-run both came back clean. That is
the most honest description the evidence supports, and it is still not the same thing as "the webkit
journey passed".

Advisory findings are separate and neither blocks nor authorises a push: four npm advisories and 44
pip-audit findings exist, none of them in code this push touches, and the gate document forbids the
blind forced upgrade that would "fix" them (§2.1, §2.2).

**Decision: commit the audit record, do not push on this evidence without the owner's call.** The
authorisation for this release was a normal push *only after all required release checks pass*. One
required check has a recorded failing attempt whose cause is understood but not eliminated, so the
condition is not unambiguously met, and deciding that a documented engine artifact is acceptable is
the owner's judgement, not a step an audit takes for them. The commits are made locally and stay
local until that decision is given; when it is, publication is the single ordinary command
`git push -u origin main` — no force, no lease, no `--no-verify`, no hook bypass, and the fast-forward
must be re-proved with `git ls-remote` immediately before it.

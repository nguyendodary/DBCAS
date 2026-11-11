# W5 cleanup inventory — 2026-11-13 round

Evidence-only inventory. **Nothing was deleted, moved, renamed, staged or committed.** No Docker container was stopped; `.env` contents were not read or printed; `docs/qa/handover.md` was not edited.

- Worktree: `C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101`
- Owner root: `C:\Users\kudot\Downloads\proposal test`
- Snapshot: **2026-11-11 14:35 +0700** (local start is 2026-11-11; the round is named 20261113).
- Worktree state at scan: branch `develop2`, HEAD **`28c1784`** (`docs(qa): open final audit status table`). 20 uncommitted entries were present because W1–W4 were editing concurrently; they are not W5 changes.
- Sizes are logical bytes from `Get-ChildItem -Recurse | Measure-Object Length -Sum`; active test folders change while tests run.

## Summary

| Class | Paths / rows | Bytes | Files | Notes |
| --- | ---: | ---: | ---: | --- |
| DELETE (quarantine) | 84 | 8,552,932,765 | 186,306 | 3,238,708,922 B in worktree; 5,314,223,843 B in owner `_review` |
| KEEP (explicit) | 39 review subfolders + documented groups | — | — | worktree `_review` keep 3,581,209,707 B; owner `_review` keep 5,856,649,812 B |
| ASK | 56 rows | 8,182,726,945 | 31,560 | owner `_review` ASK 7,995,766,493 B; worktree ASK 31,140,002 B + backups/scripts + top-level owner items |
| `_trash-20261112` | 7 | 367,401 | 11 | prior quarantine; 370,225 B / 12 files including manifest; command at end |

Largest DELETE candidates: `_review/e2e-merged-webkit` **2,181,724,068 B / 10,443 files** (owner), `_review/audit-20261108` **723,017,401 B / 39,322** (worktree), `_review/fresh-final-20261105` **661,504,074 B / 38,521** (worktree), `_review/audit-fresh-20261104` **635,205,029 B / 37,224** (worktree), `_review/frontend-audit-e2e` **491,136,858 B / 1,966** (owner).

Reference-scan shorthand used in the tables:

```text
R0(name): git -C "<worktree-or-DBCAS>" grep -l --fixed-strings "<name>" -- .
          | filter out docs/qa/workspace-inventory-20261112.*
          => 0 hits in both checkouts (tracked text only)
```

No proposed DELETE is referenced by CI, `package.json`, docker-compose, or the docs index; that was checked before each row was classified.

## A. In-repo (worktree) inventory

### A1. DELETE — quarantine candidates

| Item | Type | Size / files | Class | Evidence / reference command | Proposed action |
| --- | --- | ---: | --- | --- | --- |
| `_review/audit-20261108` | dir | 723,017,401 B / 39,322 | DELETE | R0=0; `git -C _review/audit-20261108/fresh-clone status --porcelain`=0; HEAD b070b7e; `git cat-file -e b070b7e^{commit}` reachable | quarantine |
| `_review/fresh-final-20261105` | dir | 661,504,074 B / 38,521 | DELETE | R0=0; `git -C _review/fresh-final-20261105 status --porcelain`=0; HEAD e3d5034; `git cat-file -e e3d5034^{commit}` reachable | quarantine |
| `_review/audit-fresh-20261104` | dir | 635,205,029 B / 37,224 | DELETE | R0=0; `git -C _review/audit-fresh-20261104 status --porcelain`=0; HEAD 0c16327; `git cat-file -e 0c16327^{commit}` reachable | quarantine |
| `_review/fresh-local-20261102` | dir | 243,912,406 B / 5,909 | DELETE | R0=0; `git -C _review/fresh-local-20261102 status --porcelain`=0; HEAD 58b3301; `git cat-file -e 58b3301^{commit}` reachable | quarantine |
| `_review/continuation-fresh-clone` | dir | 242,644,815 B / 6,007 | DELETE | R0=0; `git -C _review/continuation-fresh-clone status --porcelain`=0; HEAD 98e227b; `git cat-file -e 98e227b^{commit}` reachable | quarantine |
| `_review/final-clean-20261102` | dir | 225,461,323 B / 5,827 | DELETE | R0=0; `git -C _review/final-clean-20261102 status --porcelain`=0; HEAD 6140e8e; `git cat-file -e 6140e8e^{commit}` reachable | quarantine |
| `_review/continuation-regression` | dir | 145,237,976 B / 478 | DELETE | R0=0; generated browser-results/screenshots only; no doc/CI reference | quarantine |
| `_review/readiness-clean-clone` | dir | 109,791,748 B / 795 | DELETE | R0=0; `git -C _review/readiness-clean-clone status --porcelain`=0; HEAD a6b7b07; `git cat-file -e a6b7b07^{commit}` reachable | quarantine |
| `_review/final-clone-20261103` | dir | 105,720,005 B / 809 | DELETE | R0=0; `git -C _review/final-clone-20261103 status --porcelain`=0; HEAD 853c275; `git cat-file -e 853c275^{commit}` reachable | quarantine |
| `_review/fresh-clone-20261103` | dir | 86,189,026 B / 778 | DELETE | R0=0; `git -C _review/fresh-clone-20261103 status --porcelain`=0; HEAD 2231c86; `git cat-file -e 2231c86^{commit}` reachable | quarantine |
| `_review/tmp` | dir | 26,940,799 B / 362 | DELETE | R0=0; scratch logs/crops/old diagram intermediates; no doc/CI reference | quarantine |
| `_review/continuation-fake-browser` | dir | 4,261,376 B / 23 | DELETE | R0=0; scratch logs/crops/old diagram intermediates; no doc/CI reference | quarantine |
| `_review/scratch-crops-20261109` | dir | 3,415,514 B / 65 | DELETE | R0=0; scratch logs/crops/old diagram intermediates; no doc/CI reference | quarantine |
| `_review/w3a-old-erd-b` | dir | 1,489,506 B / 16 | DELETE | R0=0; scratch logs/crops/old diagram intermediates; no doc/CI reference | quarantine |
| `_review/w3b-old-page6` | dir | 681,143 B / 13 | DELETE | R0=0; scratch logs/crops/old diagram intermediates; no doc/CI reference | quarantine |
| `_review/tmp-20261109` | dir | 173,307 B / 8 | DELETE | R0=0; scratch logs/crops/old diagram intermediates; no doc/CI reference | quarantine |
| `_review/ai-probe` | dir | 599 B / 2 | DELETE | R0=0; scratch logs/crops/old diagram intermediates; no doc/CI reference | quarantine |
| `_review/_review` | dir | 111 B / 1 | DELETE | R0=0; scratch logs/crops/old diagram intermediates; no doc/CI reference | quarantine |
| `_review/qa/_review` | dir | 111 B / 1 | DELETE | R0=0; empty/nested scratch dir inside active QA output | quarantine |
| `.pytest_cache` | dir | 1,163 B / 4 | DELETE | `git check-ignore -v .pytest_cache` matches .gitignore; generated cache | quarantine |
| `.ruff_cache` | dir | 291 B / 3 | DELETE | `git check-ignore -v .ruff_cache` matches .gitignore; generated cache | quarantine |
| `backend/.pytest_cache` | dir | 154,794 B / 5 | DELETE | `git check-ignore -v backend/.pytest_cache` matches .gitignore; generated cache | quarantine |
| `backend/.ruff_cache` | dir | 14,875 B / 10 | DELETE | `git check-ignore -v backend/.ruff_cache` matches .gitignore; generated cache | quarantine |
| `backend/app/__pycache__` | dir | 405,204 B / 24 | DELETE | `git check-ignore -v backend/app/__pycache__` matches .gitignore; generated cache | quarantine |
| `backend/tests/__pycache__` | dir | 3,301,955 B / 79 | DELETE | `git check-ignore -v backend/tests/__pycache__` matches .gitignore; generated cache | quarantine |
| `db/__pycache__` | dir | 5,060 B / 1 | DELETE | `git check-ignore -v db/__pycache__` matches .gitignore; generated cache | quarantine |
| `scripts/__pycache__` | dir | 907,321 B / 29 | DELETE | `git check-ignore -v scripts/__pycache__` matches .gitignore; generated cache | quarantine |
| `ai/__pycache__` | dir | 15,158 B / 2 | DELETE | `git check-ignore -v ai/__pycache__` matches .gitignore; generated cache | quarantine |
| `frontend/dist` | dir | 18,243,210 B / 38 | DELETE | R0=0; generated by `npm run build`; Dockerfile builds inside image (no tracked ref) | quarantine |
| `frontend/test-results` | dir | 45 B / 1 | DELETE | `git check-ignore -v frontend/test-results` matches .gitignore; Playwright output | quarantine |
| `scripts/check_diagram_geometry_f3.py` | file | 13,577 B / 1 | DELETE | R0=0; SHA256 identical to used `scripts/check_diagram_geometry.py` | quarantine |

Cache group (`A1` rows `backend/app/__pycache__` … `ai/__pycache__`) totals **4,805,821 B / 157 files**; all match `.gitignore` (`git check-ignore -v`). `frontend/dist` is 18,243,210 B / 38 files; `frontend/test-results` is 45 B / 1 file. `scripts/check_diagram_geometry_f3.py` is byte-identical to the used checker (same SHA256), so its removal is a pure duplicate cleanup.

### A2. KEEP — live/referenced

| Item | Type | Size / files | Class | Evidence | Action |
| --- | --- | ---: | --- | --- | --- |
| `backend/app/` | 99 tracked Python modules | 857,725 B / 99 | KEEP | 98 app modules leaf-name-referenced; 6 hits are CLI/test entrypoints; `ruff` F401/F841 findings are edits, not dead files | keep |
| `frontend/src/` | 114 tracked JS/JSX files (51 production modules) | 18,235,029 B / 114 | KEEP | import scan: 51 production modules, 0 unreferenced; 63 test files cover live behavior | keep |
| `frontend/src/assets/` | brand + font assets | 17,130,150 B / 18 | KEEP | every filename has >=1 import/CSS reference (hinhnen, nen1, SQL, video1, 6 woff2) | keep |
| `frontend/public/` | favicon/theme/license + new W4 brand set | 5,121 B / 2 | KEEP | tracked files referenced by index.html/config; `frontend/public/brand/` is active W4 work (untracked) | keep |
| `docs/` | 1360 tracked docs/diagrams/academic | 178,138,445 B / 1,360 | KEEP | docs/README.md index + CI docs:check + Word/diagram gates; protected originals | keep |
| `docs/academic/` | 8 official Word/PDF/README files | 15,190,770 B / 8 | KEEP | v1.1 originals + v1.2 Proposal/Architecture/Database protected by owner | keep |
| `docs/qa/` | 920 tracked QA evidence files | 133,530,832 B / 920 | KEEP | current/round evidence referenced by handover, docs index and tests | keep |
| `docs/diagrams/` | 327 tracked source/SVG/ledger files | 27,756,626 B / 327 | KEEP | `npm run diagrams:check` inputs; generated=checked by check_docs.py; rebuild=checked by check_rebuild_figures.py | keep |
| `docs/deliverables/` | 29 Jira deliverables | 70,735 B / 29 | KEEP | docs/deliverables/index.md maps every file | keep |
| `db/` | schema, 19 migrations, seeds, packs | 5,966,530 B / 37 | KEEP | schema/migrations required for history; never a W5 deletion target | keep |
| `_content/expansion-20261024/` | 203 historical bank-expansion files | 7,192,605 B / 203 | KEEP | referenced by content docs; not imported by app | keep |
| `backend/tests/` | 211 backend test files; frontend e2e/unit suites also kept | 6,746,603 B / 211 | KEEP | cover live behavior; never a W5 deletion target | keep |
| `tools/` | portable poppler + docs venv | 468,527,972 B / 7,005 | KEEP | `scripts/run_py.mjs --prefer-tools`/`docs:verify-word` need poppler and python-docx | keep |
| `node_modules/` | root docs/diagram toolchain | 390,252,515 B / 31,289 | KEEP | pinned @mermaid-js/mermaid-cli + @viz-js/viz; npm ci reproduces | keep |
| `frontend/node_modules/` | frontend local install | 155,769,819 B / 6,330 | KEEP | needed for lint/test/build; npm ci reproduces | keep |
| `backend/.venv/` | backend local venv | 397,608,277 B / 9,215 | KEEP | needed for backend lint/test; recreatable from requirements | keep |
| `.playwright-mcp/` | current browser evidence | 485,299 B / 111 | KEEP | active session evidence; handover explicitly preserves it | keep |
| `ai/output/` | 22 local inference artifacts | 701,366 B / 22 | KEEP | mounted read-only by docker-compose.ai.yml | keep |

Additional KEEP evidence:

- **Frontend import scan:** 51 production modules, **0 unreferenced** (tests and `main.jsx` excluded).
- **Backend module scan:** 98 `app` modules; every leaf name has a reference. The six CLI/test entrypoints (`bootstrap_admin`, `bootstrap_role_manager`, `reconcile_bank`, `sandbox_job`, `seed_demo`, `services/assessment_pool`) are intentionally kept.
- **Dependencies:** 22 frontend npm deps and 12 runtime Python deps all matched to imports/config; `npm ls --depth=0` shows only the two pinned root dev deps; `pip check` is not rerun in W5 (existing cleanup report records clean).
- **Docker Compose:** local services `mailpit`, `db`, `executor-image`, `init`, `app`, `frontend`; `sandbox`, `qa-ai`, `ai-worker`, `migrate`, `backend`, `worker` all referenced by launcher/CI/docs. 0 unused service.
- **Environment:** `node scripts/run_py.mjs scripts/check_environment.py` → **69 backend + 2 frontend keys documented; no values loaded**. 0 unused key found in static cross-check; `.env` untouched.
- **DB:** 41 schema tables; **0 unreferenced**. `assessment_question`, `system_setting`, `evaluation_record`, `grade_edit_audit`, `adaptive_event` are low-reference but live (legacy history/registry/triggers). No table drop is proposed.
- **Dead code:** 0 unreferenced app modules; `ruff check backend/app --select F401,F811,F841` reports **27 findings (24 auto-fixable)** — unused imports/local variables are code edits, not file deletions; deferred.
- **Tracked docs duplicates:** `docs/_backup-docx-20261107` is a byte-identical SHA256 copy of the four protected `docs/academic` v1.1 `.docx`; it is **ASK**, not DELETE, because `docs/qa/doc-discrepancies.md` cites it. Diagram originals repeated across `docs/diagrams/originals`, `docs/qa/diagram-originals`, `docs/qa/doc-v2-original-diagrams`, `docs/qa/rebuild-preview` are intentional evidence sets — KEEP.

### A3. ASK — in-repo

| Item | Type | Size / files | Class | Evidence | Action |
| --- | --- | ---: | --- | --- | --- |
| `_review/w4-20261109` | dir | 13,375,234 B / 21 | ASK | R0=0 but unique Word-edit/backup working set; owner decision | hold |
| `_review/word-backup-20261109-pre-logic` | dir | 17,764,768 B / 6 | ASK | R0=0 but unique Word-edit/backup working set; owner decision | hold |
| `docs/_backup-docx-20261107` | dir | 6,054,263 B / 4 | ASK | 4 SHA256 pairs match `docs/academic` v1.1; cited by `docs/qa/doc-discrepancies.md:95` | hold |
| `docs/_backup-docx-oauth-20261112` | dir | 9,161,806 B / 3 | ASK | pre-edit v1.2 Word backups; unique rollback copies | hold |
| `scripts/` 25 zero-ref utilities | group | 149,879 B / 25 | ASK | R0=0; manual Word/diagram/live-AI tools; not in CI/package.json | hold |

### A4. Database objects (schema + code scan)

| Table | Static refs | Where it is read/written | Disposition |
| --- | ---: | --- | --- |
| `assessment_question` | 2 | `repositories.py` legacy formal-assessment pool + `services/assessment_pool.py` | KEEP (legacy history; no drop) |
| `system_setting` | 1 | `services/corpus_seed.py` registry; `services/system_settings.py` marks it legacy/history | KEEP (legacy history; no drop) |
| `evaluation_record` | 1 | `services/evaluation_service.py` | KEEP (live) |
| `grade_edit_audit` | 1 | `services/grading_review.py`; immutable DB trigger | KEEP (audit history; no drop) |
| `adaptive_event` | 3 | `services/batch_adaptive.py`; immutable DB trigger | KEEP (audit history; no drop) |
| Other 36 tables | >=3 each | models.py + repositories/services/routers/tests | KEEP |

**Result:** 41/41 schema tables are mapped and referenced; **0 unreferenced DB objects**. No `DROP TABLE` is proposed. Legacy history tables would need a safe forward migration, not a cleanup script.

### A5. Dependencies, Compose and environment

| Check | Result | Evidence |
| --- | --- | --- |
| npm (frontend) | 22/22 used | `npm ls --depth=0`; import/config scan found no unreferenced package |
| npm (root) | 2/2 used | `@mermaid-js/mermaid-cli`, `@viz-js/viz`; `diagrams:*`/`docs:check` |
| Python runtime | 12/12 used | `backend/requirements.txt`; import scan; `certifi` is the TLS CA dependency |
| Compose services | 12/12 referenced | launcher (`scripts/local.mjs`), `browser-qa.mjs`, `real-provider-qa.mjs`, CI, docs |
| Environment names | 69 backend + 2 frontend | `node scripts/run_py.mjs scripts/check_environment.py`; 0 unused in static cross-check |

## B. Owner folder `proposal test`

### B1. Top level

| Item | Type | Size / files | Class | Evidence | Action |
| --- | --- | ---: | --- | --- | --- |
| `_review` | dir | 19,172,066,964 B / 110,545 | DELETE (partial) | 53 of 110 `_review` subfolders are generated browser/test/cache artifacts (51 R0=0 + 2 caches/nested); 22 referenced folders are KEEP and 35 unique/backup folders are ASK (B2-B4) | quarantine listed subfolders only |
| `_worktrees` | dir | 10,275,991,572 B / 299,583 | KEEP | active worktree + preserved stabilization worktree (122 uncommitted files) + live _review/docker-tests; never delete | keep |
| `DBCAS` | dir | 3,105,746,206 B / 54,006 | KEEP | protected main checkout; clean `main`; stash + root patch preserve earlier uncommitted work | keep |
| `_docread` | dir | 235,661,286 B / 644 | KEEP | referenced by docs/academic-documents-ver12-20261027.md; holds pre-task Word backups | keep |
| `devin-cleanup-backup` | dir | 88,815,357 B / 8 | ASK | git bundle + audit copy; R0=0 but recovery/backup | hold |
| `DBCAS-frontend-src` | dir | 71,615,969 B / 92 | KEEP | separate repository referenced by docs/supervisor-implementation.md and docs/ux-simplification-audit-20261023.md | keep |
| `FITAI - Documents` | dir | 37,714,494 B / 31 | ASK | teammate/personal documents; docs/academic-reconciliation-20261027.md says not DBCAS work | hold |
| `_extract` | dir | 28,852,824 B / 51 | KEEP | referenced by docs/diagrams/inventory.json; holds pre-task Word backups | keep |
| `output` | dir | 6,860,444 B / 33 | KEEP | derived PDFs/screenshots cited by academic docs (output/*_references_fixed.pdf) | keep |
| `C1SE.70_ProposalDocument_DBCAS_ver1.6.docx` | file | 2,856,798 B / 1 | ASK | older/newer revision outside protected v1.2 set | hold |
| `C1SE.70_ProposalDocument_DBCAS_ver1.5.docx` | file | 2,723,459 B / 1 | ASK | older/newer revision outside protected v1.2 set | hold |
| `C1SE.70_ProposalDocument_DBCAS_ver1.2.docx` | file | 2,710,000 B / 1 | KEEP | owner explicitly protects the three v1.2 root copies; not the v1.1 originals | keep |
| `C1SE.70_ArchitectureDesign_DBCAS_ver1.4.docx` | file | 2,399,322 B / 1 | ASK | older/newer revision outside protected v1.2 set | hold |
| `C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx` | file | 2,320,232 B / 1 | KEEP | owner explicitly protects the three v1.2 root copies; not the v1.1 originals | keep |
| `C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx` | file | 2,264,448 B / 1 | ASK | older/newer revision outside protected v1.2 set | hold |
| `.playwright-mcp` | dir | 1,618,049 B / 201 | KEEP | current session browser evidence | keep |
| `dbcas-db-backups` | dir | 1,421,009 B / 2 | ASK | two PostgreSQL dumps (pre-011); contain account data; recovery copy | hold |
| `C1SE.70_DatabaseDesign_DBCAS_ver1.5.docx` | file | 1,046,475 B / 1 | ASK | older/newer revision outside protected v1.2 set | hold |
| `C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx` | file | 996,457 B / 1 | KEEP | owner explicitly protects the three v1.2 root copies; not the v1.1 originals | keep |
| `C1SE.70_DatabaseDesign_DBCAS_ver1.4.docx` | file | 982,250 B / 1 | ASK | older/newer revision outside protected v1.2 set | hold |
| `_trash-20261112` | dir | 370,225 B / 12 | KEEP | prior quarantine, 7 items / 367,401 payload bytes; permanent delete only after owner confirmation | keep |
| `_backup_main_worktree_20261110.patch` | file | 286,575 B / 1 | KEEP | preserves DBCAS main uncommitted work (72 files, 1,945+/523-) | keep |
| `C1SE.70_UserStoryDocument_DBCAS_ver1.5.docx` | file | 72,788 B / 1 | ASK | teammate/personal User Story document; owner decision | hold |
| `C1SE.70_UserStoryDocument_DBCAS_ver1.2.docx` | file | 66,489 B / 1 | ASK | teammate/personal User Story document; owner decision | hold |
| `C1SE.70_UserStoryDocument_DBCAS_ver1.4.docx` | file | 65,297 B / 1 | ASK | teammate/personal User Story document; owner decision | hold |
| `_phase2_directive.txt` | file | 26,283 B / 1 | ASK | R0=0 historical directive; may be owner instruction record | hold |
| `.qoder` | dir | 6,607 B / 1 | KEEP | local Qoder settings (1 file); tool config, not project data | keep |
| `nul` | file | 33 B / 1 | ASK | reserved Windows device name; 33-byte historical diagnostic file; R0=0 | hold |
| `%temp%` | dir | 0 B / 0 | ASK | literal `%temp%` directory; 0 files; no project reference | hold |
| `docs` | dir | 0 B / 0 | ASK | empty directory tree (0 files); no content to delete | hold |

`_worktrees` contains the active worktree **8,552,181,125 B / 281,873 files**, the preserved `dbcas-final-stabilization-20261031` worktree **1,544,811,042 B / 16,601** with **122 uncommitted files**, `frontend-audit` **39,414,558 B / 361** (clean at c43b189) and live `_review` **155,252,236 B / 815**. All are KEEP: worktrees/`.git` metadata and the preserved uncommitted work must not be touched.

### B2. `_review` — DELETE subfolders (53)

| Item | Type | Size / files | Class | Evidence | Action |
| --- | --- | ---: | --- | --- | --- |
| `_review/e2e-merged-webkit` | dir | 2,181,724,068 B / 10,443 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/frontend-audit-e2e` | dir | 491,136,858 B / 1,966 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/e2e-postfix2-20261028-chromium` | dir | 129,190,590 B / 461 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/e2e-merged-chromium` | dir | 129,190,008 B / 461 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/e2e-postfix2-20261028-firefox` | dir | 113,366,447 B / 461 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/e2e-merged-firefox` | dir | 113,069,597 B / 461 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/cleanup-e2e-chromium` | dir | 112,889,737 B / 346 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/e2e-main-chromium` | dir | 110,439,329 B / 408 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/e2e-postfix2-20261028-webkit` | dir | 99,168,357 B / 461 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/e2e-merged-rerun-webkit` | dir | 95,965,162 B / 242 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/e2e-main-webkit2` | dir | 86,534,814 B / 408 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-pg18-4edf95e6` | dir | 66,612,239 B / 1,138 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-pg18-8f781aa9` | dir | 66,612,239 B / 1,138 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-pg18-9a6b790c` | dir | 66,612,239 B / 1,138 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-pg18-aad43cc1` | dir | 66,612,239 B / 1,138 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-pg18-be98926c` | dir | 66,612,239 B / 1,138 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-pg18-e11c307f` | dir | 66,612,239 B / 1,138 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-pg18-2c3ceb61` | dir | 66,604,047 B / 1,138 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-pg18-1d663467` | dir | 65,963,671 B / 1,138 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-pg18-c00132f8` | dir | 65,963,670 B / 1,138 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/acceptance-pg17-1a2bb2c6` | dir | 65,091,846 B / 1,136 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/acceptance-pg17-4722e460` | dir | 65,050,882 B / 1,136 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/e2e-main-webkit` | dir | 64,920,332 B / 333 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-browser-pg18-03db8167` | dir | 43,994,582 B / 1,139 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-browser-pg18-28c5ac4c` | dir | 43,994,133 B / 1,139 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-browser-pg18-f53c2944` | dir | 43,994,132 B / 1,139 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-browser-pg18-75496265` | dir | 43,994,029 B / 1,139 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-browser-pg18-84e351f7` | dir | 43,843,385 B / 1,139 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-browser-pg18-98d63d85` | dir | 43,794,608 B / 1,139 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-browser-pg18-3572483e` | dir | 43,794,131 B / 1,139 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-browser-pg18-1fa240d6` | dir | 43,793,817 B / 1,139 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-browser-pg18-d6910eb5` | dir | 43,759,709 B / 1,139 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-browser-pg18-6537f751` | dir | 43,691,869 B / 1,139 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-browser-pg18-acf3f877` | dir | 43,666,762 B / 1,139 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-pg18-63b6e285` | dir | 43,530,743 B / 1,137 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-browser-pg18-2fb958ae` | dir | 43,530,125 B / 1,137 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/acceptance-browser-pg17-acada110` | dir | 43,375,717 B / 1,137 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/acceptance-browser-pg17-11ec25c5` | dir | 43,375,285 B / 1,137 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/acceptance-browser-pg17-e0e594b2` | dir | 43,375,285 B / 1,137 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/acceptance-browser-pg17-7ee52444` | dir | 43,373,295 B / 1,137 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/ux-pg18-7efc866f` | dir | 41,714,564 B / 973 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/cleanup-e2e-retry` | dir | 24,793,674 B / 110 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/trace-webkit-formal` | dir | 23,856,452 B / 399 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/cleanup-e2e-application` | dir | 21,828,148 B / 106 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/postfix-gates-20261028` | dir | 2,425,547 B / 7 | DELETE | generated gate logs/JSON; R0=0 | quarantine |
| `_review/docs-security-merged-20261028` | dir | 525,837 B / 2 | DELETE | generated merged docs/security logs; R0=0 | quarantine |
| `_review/__pycache__` | dir | 199,273 B / 10 | DELETE | Python bytecode cache; `git check-ignore` matches `.gitignore`; regenerateable | quarantine |
| `_review/gate123-merged-20261028` | dir | 22,811 B / 10 | DELETE | generated merged gate logs; R0=0 | quarantine |
| `_review/_review` | dir | 13,376 B / 1 | DELETE | nested empty `_review` scratch directory; 1 file, 13 KB | quarantine |
| `_review/e2e-postfix-20261028-chromium` | dir | 7,467 B / 4 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/docs-gates-merged-20261028` | dir | 4,785 B / 4 | DELETE | generated merged docs-gate logs; R0=0 | quarantine |
| `_review/e2e-merged-rerun2-webkit` | dir | 4,238 B / 4 | DELETE | R0=0; generated Playwright browser-results/screenshots; not in docs index/CI/npm/compose | quarantine |
| `_review/bilingual-standard-e2e` | dir | 3,215 B / 2 | DELETE | generated browser-results JSON; R0=0 | quarantine |

Group totals: generated browser/e2e/repeat/cache artifacts **5,314,223,843 B / 49,948 files** (51 folders R0=0; `__pycache__` and the nested `_review` are caches). The three named `e2e-release-20261028-*` runs, `e2e-repeat-webkit`, `e2e-rerun-formal-webkit`, `e2e-application*` and all referenced audit folders are excluded and kept.

### B3. `_review` — KEEP (22)

| Item | Type | Size / files | Class | Evidence | Action |
| --- | --- | ---: | --- | --- | --- |
| `_review/remediation` | dir | 1,789,970,897 B / 8,838 | KEEP | referenced (70 tracked-text hits); evidence for a dated audit/release report | keep |
| `_review/docker-stabilization-20261023` | dir | 935,516,469 B / 4,374 | KEEP | referenced (2 tracked-text hits); evidence for a dated audit/release report | keep |
| `_review/integration-acceptance-20261023` | dir | 663,851,004 B / 5,139 | KEEP | referenced (19 tracked-text hits); evidence for a dated audit/release report | keep |
| `_review/post-reboot-recovery-20261023` | dir | 502,301,385 B / 2,247 | KEEP | referenced (2 tracked-text hits); evidence for a dated audit/release report | keep |
| `_review/dbcas-redo-20261025` | dir | 495,229,159 B / 2,207 | KEEP | referenced (2 tracked-text hits); evidence for a dated audit/release report | keep |
| `_review/release-20261025` | dir | 433,713,685 B / 1,603 | KEEP | referenced (11 tracked-text hits); evidence for a dated audit/release report | keep |
| `_review/final-acceptance-20261018` | dir | 245,418,008 B / 941 | KEEP | referenced (4 tracked-text hits); evidence for a dated audit/release report | keep |
| `_review/supervisor-20261018` | dir | 175,777,348 B / 593 | KEEP | referenced (2 tracked-text hits); evidence for a dated audit/release report | keep |
| `_review/e2e-release-20261028` | dir | 129,298,664 B / 460 | KEEP | referenced (2 tracked-text hits); evidence for a dated audit/release report | keep |
| `_review/e2e-release-20261028-webkit` | dir | 114,718,851 B / 464 | KEEP | referenced (2 tracked-text hits); evidence for a dated audit/release report | keep |
| `_review/e2e-release-20261028-firefox` | dir | 113,658,569 B / 461 | KEEP | R0=0 but docs/release-audit-20261028.md cites the `e2e-release-20261028-<browser>/` set | keep |
| `_review/e2e-repeat-webkit` | dir | 99,567,689 B / 461 | KEEP | referenced (2 tracked-text hits); evidence for a dated audit/release report | keep |
| `_review/bilingual-diagrams-20261023` | dir | 25,993,926 B / 98 | KEEP | referenced (4 tracked-text hits); evidence for a dated audit/release report | keep |
| `_review/e2e-application-chromium` | dir | 21,823,909 B / 107 | KEEP | referenced (2 tracked-text hits); evidence for a dated audit/release report | keep |
| `_review/activation-readiness` | dir | 21,469,625 B / 111 | KEEP | referenced (6 tracked-text hits); evidence for a dated audit/release report | keep |
| `_review/e2e-application-msedge` | dir | 21,021,617 B / 108 | KEEP | R0=0 but part of the same live application matrix as referenced e2e-application-chromium | keep |
| `_review/e2e-application` | dir | 20,487,391 B / 88 | KEEP | referenced (8 tracked-text hits); evidence for a dated audit/release report | keep |
| `_review/e2e-application-firefox` | dir | 19,048,671 B / 107 | KEEP | R0=0 but part of the same live application matrix as referenced e2e-application-chromium | keep |
| `_review/e2e-application-webkit` | dir | 15,674,956 B / 107 | KEEP | R0=0 but part of the same live application matrix as referenced e2e-application-chromium | keep |
| `_review/stabilization` | dir | 12,044,833 B / 41 | KEEP | referenced (16 tracked-text hits); evidence for a dated audit/release report | keep |
| `_review/docker-tests` | dir | 46,875 B / 423 | KEEP | referenced (8 tracked-text hits); evidence for a dated audit/release report | keep |
| `_review/e2e-rerun-formal-webkit` | dir | 16,281 B / 6 | KEEP | referenced (2 tracked-text hits); evidence for a dated audit/release report | keep |

### B4. `_review` — ASK (35)

| Item | Type | Size / files | Class | Evidence | Action |
| --- | --- | ---: | --- | --- | --- |
| `_review/supervisor-functional-20261026` | dir | 3,234,547,748 B / 11,845 | ASK | unique functional acceptance evidence: acceptance_runner.py, acceptance-evidence-final.json, browser matrices | hold |
| `_review/supervisor-completion-20261024` | dir | 1,359,313,417 B / 6,753 | ASK | unique supervisor-completion runs: browser-sequence JSONs, engineering evidence | hold |
| `_review/e2e-final-20261018` | dir | 695,831,100 B / 1,349 | ASK | final-acceptance logs/reports plus browser matrices; unique | hold |
| `_review/audit-20261024` | dir | 598,127,691 B / 2,663 | ASK | full audit logs/reports (backend/frontend/browser); unique | hold |
| `_review/theme-recovery-20261014` | dir | 457,657,879 B / 1,893 | ASK | theme-recovery checkpoint.md, audit.json, screenshots | hold |
| `_review/final` | dir | 337,360,943 B / 742 | ASK | old final review folder; mixed reports/screenshots | hold |
| `_review/final-owner-review-20261014` | dir | 290,858,917 B / 1,059 | ASK | owner visual-review screenshots + extract/i18n scripts | hold |
| `_review/admin-controls-20261014` | dir | 282,772,794 B / 1,065 | ASK | admin-control screenshots at 3 viewports x 2 themes | hold |
| `_review/release-preparation-20261019` | dir | 234,519,300 B / 1,063 | ASK | release-preparation logs/reports; unique | hold |
| `_review/full-audit-20261030` | dir | 136,843,648 B / 472 | ASK | 30 Oct full-audit reports + baseline e2e | hold |
| `_review/admin-vi-20261014` | dir | 84,024,396 B / 275 | ASK | R0=0 but contains unique audit/screenshot/recovery evidence; owner decision | hold |
| `_review/academic-v1.1` | dir | 54,537,826 B / 204 | ASK | intermediate Word v1.1 docx + editing scripts; not byte-identical to protected originals | hold |
| `_review/vi-copy-20261014` | dir | 50,249,018 B / 194 | ASK | R0=0 but contains unique audit/screenshot/recovery evidence; owner decision | hold |
| `_review/conditional-recovery-20261023-1754` | dir | 45,444,520 B / 1,167 | ASK | conditional-recovery logs/evidence | hold |
| `_review/learner-vi-20261014` | dir | 34,211,923 B / 190 | ASK | R0=0 but contains unique audit/screenshot/recovery evidence; owner decision | hold |
| `_review/backups` | dir | 30,805,860 B / 1 | ASK | privacy-cleanup-20261019 git bundle (30.8 MB) | hold |
| `_review/media-overlay-20261014` | dir | 17,140,166 B / 56 | ASK | R0=0 but contains unique audit/screenshot/recovery evidence; owner decision | hold |
| `_review/overflow-20261014` | dir | 10,524,584 B / 57 | ASK | R0=0 but contains unique audit/screenshot/recovery evidence; owner decision | hold |
| `_review/development-release-20261024` | dir | 8,472,332 B / 81 | ASK | R0=0 but contains unique audit/screenshot/recovery evidence; owner decision | hold |
| `_review/functional-completion-20261029` | dir | 7,558,819 B / 59 | ASK | R0=0 but contains unique audit/screenshot/recovery evidence; owner decision | hold |
| `_review/auth-landing-probe-20261028` | dir | 6,113,620 B / 12 | ASK | R0=0 but contains unique audit/screenshot/recovery evidence; owner decision | hold |
| `_review/diagram-tools` | dir | 4,995,522 B / 16 | ASK | separate node_modules toolchain for diagram previews (@viz-js/viz) | hold |
| `_review/password-recovery-20261028` | dir | 3,719,617 B / 36 | ASK | R0=0 but contains unique audit/screenshot/recovery evidence; owner decision | hold |
| `_review/landing-vi-20261014` | dir | 3,086,087 B / 6 | ASK | R0=0 but contains unique audit/screenshot/recovery evidence; owner decision | hold |
| `_review/continuation-20261027` | dir | 1,674,020 B / 60 | ASK | continuation logs/reports | hold |
| `_review/anim` | dir | 1,440,073 B / 2 | ASK | R0=0 but contains unique audit/screenshot/recovery evidence; owner decision | hold |
| `_review/connectivity-20261024` | dir | 1,270,927 B / 27 | ASK | R0=0 but contains unique audit/screenshot/recovery evidence; owner decision | hold |
| `_review/ux-native-browser` | dir | 1,240,872 B / 19 | ASK | browser evidence cited by docs/ux-simplification-audit-20261023.md | hold |
| `_review/bilingual-native-browser` | dir | 1,201,481 B / 25 | ASK | bilingual browser screenshots; unique states | hold |
| `_review/ui-start-20261014` | dir | 93,075 B / 4 | ASK | R0=0 but contains unique audit/screenshot/recovery evidence; owner decision | hold |
| `_review/deep-root-cause-20261023-1900` | dir | 48,388 B / 24 | ASK | deep root-cause recovery evidence | hold |
| `_review/root-cause-recovery-20261023` | dir | 42,808 B / 9 | ASK | root-cause recovery evidence | hold |
| `_review/bilingual-completion-20261015` | dir | 18,523 B / 11 | ASK | bilingual completion notes/screenshots | hold |
| `_review/wsl-recovery-20261028` | dir | 16,918 B / 9 | ASK | R0=0 but contains unique audit/screenshot/recovery evidence; owner decision | hold |
| `_review/wsl-docker-relay-20261028` | dir | 1,681 B / 1 | ASK | R0=0 but contains unique audit/screenshot/recovery evidence; owner decision | hold |

### `_trash-20261112` contents

| Item | Type | Bytes | Files | Note |
| --- | --- | ---: | ---: | --- |
| `_trash-20261112/.pytest_cache` | dir | 2,788 | 5 | prior quarantine |
| `_trash-20261112/_backend_test.log` | file | 1,760 | 1 | prior quarantine |
| `_trash-20261112/_boot_backend.log` | file | 24,311 | 1 | prior quarantine |
| `_trash-20261112/_boot_backend_restart.log` | file | 310,825 | 1 | prior quarantine |
| `_trash-20261112/_boot_frontend.log` | file | 16,223 | 1 | prior quarantine |
| `_trash-20261112/_frontend_build.log` | file | 3,946 | 1 | prior quarantine |
| `_trash-20261112/_npm_audit.json` | file | 7,548 | 1 | prior quarantine |
| **Payload total** |  | **367,401** | **11** | manifest.json adds 2,824 B; actual folder 370,225 B / 12 files |

Nothing was permanently deleted from `_trash-20261112` (0 bytes reclaimed).

## Quarantine plan (proposed; not executed)

Destination root: `C:\Users\kudot\Downloads\proposal test\_trash-20261113`. Do **not** create it in W5; it is created only when the owner approves the move.

Move rule: worktree paths keep their relative path under `_trash-20261113\worktree\`; owner `_review` paths go under `_trash-20261113\owner-review\`.

```text
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\audit-20261108
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\fresh-final-20261105
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\audit-fresh-20261104
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\fresh-local-20261102
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\continuation-fresh-clone
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\final-clean-20261102
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\continuation-regression
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\readiness-clean-clone
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\final-clone-20261103
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\fresh-clone-20261103
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\tmp
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\continuation-fake-browser
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\scratch-crops-20261109
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\w3a-old-erd-b
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\w3b-old-page6
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\tmp-20261109
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\ai-probe
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\_review
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\_review\qa\_review
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\.pytest_cache
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\.ruff_cache
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\backend\.pytest_cache
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\backend\.ruff_cache
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\backend\app\__pycache__
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\backend\tests\__pycache__
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\db\__pycache__
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\scripts\__pycache__
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\ai\__pycache__
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\frontend\dist
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\frontend\test-results
C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101\scripts\check_diagram_geometry_f3.py
C:\Users\kudot\Downloads\proposal test\_review\__pycache__
C:\Users\kudot\Downloads\proposal test\_review\_review
C:\Users\kudot\Downloads\proposal test\_review\acceptance-browser-pg17-11ec25c5
C:\Users\kudot\Downloads\proposal test\_review\acceptance-browser-pg17-7ee52444
C:\Users\kudot\Downloads\proposal test\_review\acceptance-browser-pg17-acada110
C:\Users\kudot\Downloads\proposal test\_review\acceptance-browser-pg17-e0e594b2
C:\Users\kudot\Downloads\proposal test\_review\acceptance-pg17-1a2bb2c6
C:\Users\kudot\Downloads\proposal test\_review\acceptance-pg17-4722e460
C:\Users\kudot\Downloads\proposal test\_review\bilingual-standard-e2e
C:\Users\kudot\Downloads\proposal test\_review\cleanup-e2e-application
C:\Users\kudot\Downloads\proposal test\_review\cleanup-e2e-chromium
C:\Users\kudot\Downloads\proposal test\_review\cleanup-e2e-retry
C:\Users\kudot\Downloads\proposal test\_review\docs-gates-merged-20261028
C:\Users\kudot\Downloads\proposal test\_review\docs-security-merged-20261028
C:\Users\kudot\Downloads\proposal test\_review\e2e-main-chromium
C:\Users\kudot\Downloads\proposal test\_review\e2e-main-webkit
C:\Users\kudot\Downloads\proposal test\_review\e2e-main-webkit2
C:\Users\kudot\Downloads\proposal test\_review\e2e-merged-chromium
C:\Users\kudot\Downloads\proposal test\_review\e2e-merged-firefox
C:\Users\kudot\Downloads\proposal test\_review\e2e-merged-rerun-webkit
C:\Users\kudot\Downloads\proposal test\_review\e2e-merged-rerun2-webkit
C:\Users\kudot\Downloads\proposal test\_review\e2e-merged-webkit
C:\Users\kudot\Downloads\proposal test\_review\e2e-postfix-20261028-chromium
C:\Users\kudot\Downloads\proposal test\_review\e2e-postfix2-20261028-chromium
C:\Users\kudot\Downloads\proposal test\_review\e2e-postfix2-20261028-firefox
C:\Users\kudot\Downloads\proposal test\_review\e2e-postfix2-20261028-webkit
C:\Users\kudot\Downloads\proposal test\_review\frontend-audit-e2e
C:\Users\kudot\Downloads\proposal test\_review\gate123-merged-20261028
C:\Users\kudot\Downloads\proposal test\_review\postfix-gates-20261028
C:\Users\kudot\Downloads\proposal test\_review\trace-webkit-formal
C:\Users\kudot\Downloads\proposal test\_review\ux-browser-pg18-03db8167
C:\Users\kudot\Downloads\proposal test\_review\ux-browser-pg18-1fa240d6
C:\Users\kudot\Downloads\proposal test\_review\ux-browser-pg18-28c5ac4c
C:\Users\kudot\Downloads\proposal test\_review\ux-browser-pg18-2fb958ae
C:\Users\kudot\Downloads\proposal test\_review\ux-browser-pg18-3572483e
C:\Users\kudot\Downloads\proposal test\_review\ux-browser-pg18-6537f751
C:\Users\kudot\Downloads\proposal test\_review\ux-browser-pg18-75496265
C:\Users\kudot\Downloads\proposal test\_review\ux-browser-pg18-84e351f7
C:\Users\kudot\Downloads\proposal test\_review\ux-browser-pg18-98d63d85
C:\Users\kudot\Downloads\proposal test\_review\ux-browser-pg18-acf3f877
C:\Users\kudot\Downloads\proposal test\_review\ux-browser-pg18-d6910eb5
C:\Users\kudot\Downloads\proposal test\_review\ux-browser-pg18-f53c2944
C:\Users\kudot\Downloads\proposal test\_review\ux-pg18-1d663467
C:\Users\kudot\Downloads\proposal test\_review\ux-pg18-2c3ceb61
C:\Users\kudot\Downloads\proposal test\_review\ux-pg18-4edf95e6
C:\Users\kudot\Downloads\proposal test\_review\ux-pg18-63b6e285
C:\Users\kudot\Downloads\proposal test\_review\ux-pg18-7efc866f
C:\Users\kudot\Downloads\proposal test\_review\ux-pg18-8f781aa9
C:\Users\kudot\Downloads\proposal test\_review\ux-pg18-9a6b790c
C:\Users\kudot\Downloads\proposal test\_review\ux-pg18-aad43cc1
C:\Users\kudot\Downloads\proposal test\_review\ux-pg18-be98926c
C:\Users\kudot\Downloads\proposal test\_review\ux-pg18-c00132f8
C:\Users\kudot\Downloads\proposal test\_review\ux-pg18-e11c307f
```

Totals: **84 paths, 8,552,932,765 B, 186,306 files** (3,238,708,922 B worktree + 5,314,223,843 B owner).

## Permanent delete command for `_trash-20261112`

Only after explicit owner confirmation, permanently delete the exact 2026-11-12 quarantine:

```powershell
Remove-Item -LiteralPath 'C:\Users\kudot\Downloads\proposal test\_trash-20261112' -Recurse -Force
```

The command has **not** been run. It deletes only `_trash-20261112`, not `_trash-20261113` and not any worktree, `.git` folder, schema/migration, test, academic original or teammate document.

## ASK list (owner decision required)

In-repo:

- `docs/_backup-docx-20261107/` — exact duplicate of protected v1.1 originals, but cited by a QA doc; update the reference before any deletion.
- `docs/_backup-docx-oauth-20261112/` — pre-edit v1.2 Word backups; unique rollback copies.
- `_review/w4-20261109/` and `_review/word-backup-20261109-pre-logic/` — Word-edit working sets/backups.
- 25 zero-reference scripts: `audit_secret_hygiene.py`, `build_erd_stage_b_w3a.py`, `build_trd_stage_b_w3b.py`, `check_allocation_stage_b_delta.py`, `check_container_stage_b_delta.py`, `check_use_case_stage_b_delta.py`, `docx_open_check.ps1`, `draw_trace_markers.py`, `export_one_pdf.ps1`, `export_original_pdf.ps1`, `insert_word_diagrams.py`, `lo_update_indexes.py`, `make_figure_previews.py`, `make_fix_previews_f3.py`, `make_text_content_component_w2b.py`, `real-provider-qa.mjs`, `render_pdf_pages.py`, `render_word_pages.py`, `stage_b_component_w2b.py`, `stage_b_pipeline_w2b.py`, `trd_common_w3b.py`, `update_fields.ps1`, `verify_live_ai.py`, `verify_trd_stage_b_w3b.py`, `word_update_toc.ps1`.

Owner folder:

- All 35 ASK `_review` subfolders, largest first: `_review/supervisor-functional-20261026` (3,234,547,748 B), `_review/supervisor-completion-20261024` (1,359,313,417 B), `_review/e2e-final-20261018` (695,831,100 B), `_review/audit-20261024` (598,127,691 B), `_review/theme-recovery-20261014` (457,657,879 B), `_review/final` (337,360,943 B), `_review/final-owner-review-20261014` (290,858,917 B), `_review/admin-controls-20261014` (282,772,794 B), `_review/release-preparation-20261019` (234,519,300 B), `_review/full-audit-20261030` (136,843,648 B), `_review/admin-vi-20261014` (84,024,396 B), `_review/academic-v1.1` (54,537,826 B), `_review/vi-copy-20261014` (50,249,018 B), `_review/conditional-recovery-20261023-1754` (45,444,520 B), `_review/learner-vi-20261014` (34,211,923 B), `_review/backups` (30,805,860 B), `_review/media-overlay-20261014` (17,140,166 B), `_review/overflow-20261014` (10,524,584 B), `_review/development-release-20261024` (8,472,332 B), `_review/functional-completion-20261029` (7,558,819 B), `_review/auth-landing-probe-20261028` (6,113,620 B), `_review/diagram-tools` (4,995,522 B), `_review/password-recovery-20261028` (3,719,617 B), `_review/landing-vi-20261014` (3,086,087 B), `_review/continuation-20261027` (1,674,020 B), `_review/anim` (1,440,073 B), `_review/connectivity-20261024` (1,270,927 B), `_review/ux-native-browser` (1,240,872 B), `_review/bilingual-native-browser` (1,201,481 B), `_review/ui-start-20261014` (93,075 B), `_review/deep-root-cause-20261023-1900` (48,388 B), `_review/root-cause-recovery-20261023` (42,808 B), `_review/bilingual-completion-20261015` (18,523 B), `_review/wsl-recovery-20261028` (16,918 B), `_review/wsl-docker-relay-20261028` (1,681 B)
- `devin-cleanup-backup/` (git bundle + audit copy), `dbcas-db-backups/` (2 PostgreSQL dumps with account data), `_phase2_directive.txt`, `nul`, `%temp%`, empty `docs/` tree.
- Root Word files: 3 `C1SE.70_UserStoryDocument_DBCAS_ver1.{2,4,5}.docx` (teammate/personal), Architecture v1.3/v1.4, Database v1.4/v1.5, Proposal v1.5/v1.6.
- `FITAI - Documents/` — teammate/other-project material.

## Reference commands used

```powershell
# file/size inventory
Get-ChildItem -LiteralPath <path> -Recurse -File -Force | Measure-Object Length -Sum
# reference scan (run in worktree and DBCAS main; exclude the inventory JSON)
git grep -l --fixed-strings "<name>" -- .
# duplicate proof
Get-FileHash -Algorithm SHA256 -LiteralPath <file>
# scratch-clone proof
git -C <clone> status --porcelain | wc -l
git -C <clone> rev-parse --short HEAD
git cat-file -e <sha>^{commit}
# imports / dependencies
backend/.venv/Scripts/python.exe <inline import scan>
npm ls --depth=0
node scripts/run_py.mjs scripts/check_environment.py
# dead-code static scan
backend/.venv/Scripts/ruff.exe check backend/app --select F401,F811,F841 --output-format concise
# DB objects
grep -oE 'CREATE TABLE (IF NOT EXISTS )?[a-z_]+' db/schema.sql
grep -rn --include="*.py" -w "<table>" backend/app backend/tests db
```

## Coverage and un-scanned nested areas

This is a **usable partial inventory**, not a claim that every nested file was opened.

- **Depth 0:** all 30 top-level owner items have bytes/files and a KEEP/DELETE/ASK class.
- **Depth 1:** all 110 owner `_review` subfolders and all 37 worktree `_review` subfolders have aggregate bytes/files and a class.
- **Depth 2+:** not individually enumerated. Contents inherit the parent classification; any deeper scratch inside a KEEP/ASK parent is **ASK/limited**, never DELETE. The containers `DBCAS`, `_worktrees/*`, `_docread`, `_extract`, `DBCAS-frontend-src`, `devin-cleanup-backup`, `dbcas-db-backups`, `FITAI - Documents` and `output` were sized but not exhaustively opened.
- In-repo tracked files were fully listed. Untracked depth >1 outside the two `_review` trees was not exhaustively scanned.

## Limitations

- W1–W4 were still editing the worktree; the scan is a point-in-time snapshot, not a frozen tree. No file from their work was classified DELETE.
- The owner `_review` folder is outside Git; R0 proves absence from tracked text, not that a folder has no research value. Therefore all non-generated/unique audit, backup and screenshot folders are ASK, and every DELETE is a reversible quarantine.
- No live `npm run docs:check` / Playwright / Docker suite was run by W5 (explicitly out of scope). Static references and the already-recorded gates were used.
- `.env` was not opened; only `.env.example` keys and `check_environment.py`'s no-value read were used.
- The 2026-11-11 scan predates the 2026-11-13 final gates; re-run the reference scan if files change before quarantine.


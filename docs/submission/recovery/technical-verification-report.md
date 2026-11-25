# Technical verification report (Phase 6)

Date 2026-11-25. Scope: the five authoritative ver1.3 DOCX at
`docs/submission/final/`, their PDFs, and the repository facts they claim.
"Pass" below means an output was observed in this session; it is not copied from
the previous agent's reports.

## 1. Source-of-truth measurements (independently re-run)

| Claim | Command / method used here | Observed | Status |
|---|---|---|---|
| Schema totals | `docs/diagrams/schema-028/schema-introspection.json` parsed with Python; `db/migrations/*.sql` enumerated | 67 tables, 561 columns, 122 FKs, 159 indexes, 0 enums, 28 migrations | Verified |
| Index breakdown | Classified all 159 index definitions: 67 `_pkey`, 50 `UNIQUE`, 42 standalone | 67 + 50 + 42 = 159 | Verified; document was wrong and is corrected |
| DDL statements | `Select-String -Pattern "CREATE TABLE" db/schema.sql` | 68 statements, 67 distinct tables (`concept_dependency` created twice) | Verified nuance |
| OpenAPI | `docs/openapi.json` parsed | 106 paths / 118 operations | Verified |
| ORM | `__tablename__` in `backend/app/models.py` | 67 | Verified |
| Routers / services | `backend/app/main.py`, `backend/app/services/` | 7 registered routers, 72 top-level + 11 subpackage service modules | Verified; docs corrected |
| i18n | flattened `frontend/src/i18n/{en,vi}.json` | 1,700 leaves each, 34 groups, zero drift | Verified |
| Browser specs | directory enumeration | 25 in `frontend/e2e/`, 3 in `frontend/e2e-application/` | Verified; convention stated |
| Contrast | `docs/agent/freeze-logs/final-ui-contrast.log` | "186 contrast pairs checked", all passed | Verified; now cited |
| Test logs | `docs/agent/freeze-logs/backend-pytest-final.log:35` | 1,940 passed, 7 skipped, 0:23:54 | Verified; duration corrected |
| CI evidence | `docs/agent/freeze-logs/final-ci-conclusion.log` | success, 14/14 jobs, head `d6df804` | Verified for that commit only; attribution corrected |

Full evidence, including the eight flagged discrepancies and the traceability
matrix, is in `implementation-audit.md`.

## 2. Structural DOCX validation

Ran before promotion of the staged edits using
`docs/submission/tools/docx_toolkit.validate_docx`: all five staged packages
returned an empty problem list (valid ZIP, parseable document.xml and rels, no
missing media, no duplicate relationship IDs). After promotion, `npm run
docs:verify-word` was re-run; output is recorded below in §5.

## 3. Footer-field behaviour

The DOCX footer cache reads `Page 1 of 1` before a Word field refresh. This is a
stale cache, not a layout defect: PyMuPDF extraction from the committed PDFs found
correct sequential values on every page (e.g. Proposal `Page 3 of 20` … `Page 20 of
20`, Database `Page 39 of 39`). The finalisation step refreshes fields in Word 16.0
before PDF export, as documented in `docs/agent/freeze-logs/doc-style-spec.md`.

## 4. Known limitations of the verification environment

- LibreOffice and Poppler are not installed; PDFs are produced with Word 16.0 COM
  and rasterised with PyMuPDF 1.28.2.
- Python is available through the `py` launcher (3.14.5), with python-docx 1.2.0,
  PyMuPDF 1.28.2 and Pillow 12.2.0.
- The full pytest / browser suites were not re-executed in this takeover; saved
  logs are cited instead, with commit attribution where available.
- `docs:check` still validates the **v1.2 academic** documents (66 tables / 558
  columns, migration 027) while the submitted ver1.3 set describes the 67-table
  versioned schema. This is a declared scope split, not a gate failure; see
  `docs/academic/README.md`.

## 5. Gate output after revision

| Gate | Command | Observed output |
|---|---|---|
| Submission document verifier | `npm run docs:verify-word` | `submission documents: 5 checked, 149 assertions, 0 failures` (re-run after final metadata restoration) |
| Documentation gate | `npm run docs:check` | `docs:check: 48 assertions, tables=67, columns=561, fks=122, indexes=159, migrations=28`; `verify_docx: 52 assertions, 0 failures` against the untouched v1.2 academic set; `rebuild figures: PASS` |
| DOCX package integrity | `docx_toolkit.validate_docx` on staged and final packages | Empty problem list for all five |
| Field refresh / export | Word 16.0 COM: `TablesOfContents.Update()`, `Fields.Update()`, `Repaginate()`, `ExportAsFixedFormat` | Word page counts 20 / 22 / 40 / 12 / 13; matching PDFs regenerated |
| Metadata | python-docx core properties after Word save | `author` and `last_modified_by` restored to `Do, Nguyen Quoc` (Word had rewritten the latter) |
| Footer field check | PyMuPDF text extraction on final PDFs | `Page N` present on body pages; no stale `Page 1 of 1` in the rendered output |
| Page counts | PyMuPDF on final PDFs | 20 / 22 / 40 / 12 / 13; `verification/page-counts.json` updated for Database (39 → 40) |

## 6. Final git working-tree review

`git status --short` after the work: five DOCX modified in place, the Gantt PNG
regenerated plus its new SVG source, `page-counts.json`, the verification report
(regenerated by the gate), `doc-verify.md`, `SOURCE_CODE.md` and `SUMMARY.md`
corrected, and `docs/submission/recovery/` added as untracked evidence. No file
was deleted; no commit, merge, push, branch change, reset or history rewrite was
performed. `main` and production status remain unchanged (HOLD).

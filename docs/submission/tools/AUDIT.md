# Tooling audit (2026-11-23, frozen develop2)

This is the read-only inventory that motivated the small toolkit. It covers the
repository tooling, not the application runtime.

## Word / .docx needs

| Need | Status before | Evidence / tool | After this change |
|---|---|---|---|
| Text replacement in runs preserving rPr | PRESENT | `scripts/docx_inplace.py` (only `word/document.xml` text nodes) | PRESENT; `docx_toolkit.replace_text` façade |
| Clone paragraph / clone table row | MISSING | no reusable helper; one-off scripts use deepcopy | PRESENT (`clone_paragraph`, `clone_table_row`) |
| Table cell edit | PARTIAL | raw python-docx in one-off scripts | PRESENT (`set_cell_text`) |
| Image replacement at identical display size | PRESENT | `scripts/insert_word_diagrams.py` package rewrite + inline extents | PRESENT (`replace_image`) |
| TOC / field refresh | PARTIAL | `scripts/update_fields.ps1`, `word_update_toc.ps1` (Word COM); `lo_update_indexes.py` hardcoded UNO/C:\tmp | PARTIAL/PRESENT (`docx_toolkit.refresh_fields`: LibreOffice if available, else Word COM; no LibreOffice locally) |
| Style/XML C14N audit | PARTIAL | `scripts/verify_word.py` deep audit writes reports; no small reusable auditor | PRESENT (`audit_package`) |
| docx -> PDF -> PNG | PRESENT | `export_one_pdf.ps1`, `render_pdf_pages.py`, `render_word_pages.py` (hardcoded paths) | PRESENT façade (`render_pdf`, `render_pdf_pages`) |
| Before/after page pairs | PARTIAL | `verify_word.py` contact sheets / preview scripts, hardcoded and previously wrote docs/qa | PRESENT (`make_pair`; page pairs from render_pages) |
| Fact audit (numbers vs repo) | PARTIAL | `scripts/verify_docx.py` checks academic docs against 41-table docs/qa; no submission-doc fact tool | PARTIAL/PRESENT (`fact_audit`: schema-028, OpenAPI, frontend routes; test JSON optional) |
| docx integrity | PRESENT | `scripts/verify_docx.py`, `scripts/docx_open_check.ps1`, python-docx open | PRESENT (`validate_docx`) |
| Safety guard for docs/qa writes | MISSING | `verify_word.py`, `doc_facts.py`, three preview scripts wrote under docs/qa | PRESENT (`scripts/docs_qa_guard.py`; writers redirected/refused) |

Dependencies already used and pinned for the dev toolchain:
`python-docx 1.2.0`, `docx2python 3.7.2`, `pywin32 312`, `lxml 6.1.3`,
`PyMuPDF 2.1` (pin text), `Pillow 13.0.0` in `scripts/requirements-docs.txt`.
No new package is introduced by this PR.

## Diagram needs

| Need | Status before | Evidence / source | After this change |
|---|---|---|---|
| ERD/TRD card generator for all 67 tables in the shipped card style | MISSING | `scripts/build_trd_stage_b_f6.py` hardcodes 41 tables and reads docs/qa; `docs/diagrams/rebuild/trd` stays 41; schema-028 diagrams use a different style | PARTIAL/PRESENT: `trd67.py` generates six continuation pages (26 cards) and a 67-count spec; original five pages stay frozen |
| ERD continuation for migration-020-028 tables | MISSING | shipped docx has a 2/2 page; no generator in repo | PRESENT: `erd67.py` generates the 26-entity page |
| Other figures reproducible from editable source in their style | PARTIAL | Graphviz DOT, Mermaid fences, PlantUML, DBML and rebuild drawio/SVG sources; build scripts are historical | PRESENT/PARTIAL; unchanged |
| Single shared style config | MISSING | values hardcoded in generators | PARTIAL: `diagram_style.py` captures TRD/ERD/C4 palette, fonts, sizes, grid |
| Export at exact display pixel size | PARTIAL | Chrome/Puppeteer/Word scripts with hardcoded paths and sizes | PRESENT for TRD/ERD (`render_svg` prefers Chrome at 3440x2080/4300x1677, PyMuPDF fallback) |
| Before/after comparison | PARTIAL | `make_*previews.py` wrote docs/qa; no stable CLI | PARTIAL/PRESENT: `reproduce_trd1.py` + `make_pair`; preview scripts redirected |
| Diagram contents vs schema/routes/cardinality | PARTIAL | `check_docs.py` (schema/OpenAPI), `check_doc_diagrams.py` (41-table pro set), `diagrams:check` (sources/SVG) | PARTIAL/PRESENT: `check_diagrams.py` validates 67/561/122/28, 11 pages, unique cards; `ci` still lacks a full 67-card docx gate |

Known source gap: `docs/diagrams/rebuild/trd/spec.json` remains the frozen
41-card source used by the v1.2 rebuild. `trd67.py` is the documented
superseding generator for the shipped continuation pages; this change does not
replace the shipped `.docx` figures.

## Scripts that could write outside docs/submission

Before the guard, these wrote under `docs/qa/**`:

- `scripts/verify_word.py` -> `docs/qa/word-verification/`
- `scripts/doc_facts.py` -> `docs/qa/project-facts.json`
- `scripts/make_figure_previews.py` -> `docs/qa/rebuild-preview/`
- `scripts/make_fix_previews_f3.py` -> `docs/qa/rebuild-preview/`
- `scripts/make_stage_b_previews.py` -> `docs/qa/rebuild-preview/system-context/`

They now write under `_review/` (or refuse an explicit `docs/qa` output via
`ensure_safe_output`). Other writers are intentional and outside docs/qa:
`build_*`/`insert_word_diagrams.py` (docs/academic or C:\tmp),
`generate_*`/`prerender_*`/`diagrams.mjs render` (docs/diagrams),
`export_*.ps1`/`render_word_pages.py`/`lo_update_indexes.py` (C:\tmp/_review).

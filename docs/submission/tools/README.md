# Submission document and diagram tooling

Small, dev-only helpers for the DBCAS `.docx` submission and its diagrams.
They never rebuild covers/styles and never write under `docs/qa/**`.

## Rules

- Work in place: edit runs/cells/images while preserving paragraph, run and
  table properties. Do not regenerate a document from a template.
- Outputs go under `_review/` or `docs/submission/tools/out/`; `docs/qa/**` is
  refused by `scripts/docs_qa_guard.py`.
- Shipped `.docx` files are not modified by these tools unless a caller names
  them as the output path.
- No runtime dependency is added to the backend/frontend images.

## Word tools

`docx_toolkit.py` is a facade over the existing `scripts/docx_inplace.py` and
new helpers:

| Function | Purpose |
|---|---|
| `replace_text` | replace text in runs, preserving rPr; refuses field results |
| `clone_paragraph` / `set_paragraph_text` | clone a paragraph and its formatting |
| `clone_table_row` / `set_cell_text` | clone a row, set cell text with existing run style |
| `replace_image` | replace an embedded image, preserving the inline extent |
| `audit_package` | C14N compare styles/theme/settings/numbering + cover/media counts |
| `refresh_fields` | update fields/TOC via Word COM (or LibreOffice if installed) |
| `render_pdf` / `render_pdf_pages` | docx -> PDF -> PNG (Word COM or LibreOffice; PyMuPDF pages) |
| `make_pair` | labelled before/after side-by-side PNG |
| `validate_docx` | zip, XML, relationship and media integrity |
| `fact_audit` | counts from schema/OpenAPI/frontend routes vs a tests JSON |

Examples:

```bash
python docs/submission/tools/docx_toolkit.py validate docs/submission/SRS.docx
python docs/submission/tools/docx_toolkit.py audit old.docx new.docx
python docs/submission/tools/docx_toolkit.py render docs/submission/Architecture.docx \
  --pdf _review/Architecture.pdf --pages-dir _review/pages
python docs/submission/tools/docx_toolkit.py refresh docs/submission/SRS.docx \
  --out _review/SRS-fields.docx
python docs/submission/tools/docx_toolkit.py facts --out _review/facts.json
```

`refresh_fields` uses the repository's `scripts/update_fields.ps1` Word COM
helper on Windows. If a headless LibreOffice binary is on `PATH`, its converter
is used instead. `render_pdf` prefers LibreOffice and falls back to Word COM.

## Diagram tools

The shipped TRD card grammar is captured in `diagram_style.py`: 3440x2080
canvas, four 795 px cards at x=40/890/1740/2590, 74 px header, 72 px rows,
Arial 38/32/22/24, palette `#1A1A1A`/`#E8E8E8`/`#FFFFFF`/`#DCDCDC`/`#B8B8B8`,
incoming `#0B6B3A`, outgoing `#1F3A93`, legacy `#7A0000`. The ERD values are
the 4300x1677 entity/key page.

- `trd67.py` generates the six continuation pages (tables 42-67) and
  `trd-spec-67.json`; the original five 41-card pages are the frozen source.
- `erd67.py` generates the ERD 2/2 page with the 26 migration-020-028 entities.
- `check_diagrams.py` validates 67 tables / 561 columns / 122 FKs / 28
  migrations / 11 pages and unique cards.
- `reproduce_trd1.py` regenerates the existing page 1 from its own spec and
  reports a pixel diff. With Chrome available the current proof is **0 changed
  pixels**; the fallback renderer is PyMuPDF.

```bash
python docs/submission/tools/trd67.py
python docs/submission/tools/erd67.py
python docs/submission/tools/check_diagrams.py
python docs/submission/tools/reproduce_trd1.py
```

`render_svg` in `diagram_style.py` prefers headless Chrome at the exact CSS
pixel size and falls back to PyMuPDF. No new dependency is introduced: Chrome,
PyMuPDF, Pillow, lxml and python-docx are already used by the repository's
document tooling (`scripts/requirements-docs.txt`).

## Tests

```bash
python -m unittest discover -s docs/submission/tools/tests -v
```

The docx tests create their own small fixture (no shipped document is read).
The diagram tests read the generated schema catalogue and write into a
temporary directory.

## Known gaps

- `docs/diagrams/rebuild/trd/spec.json` still describes the frozen 41-card
  source used by the v1.2 rebuild; `trd67.py` is the superseding generator for
  the six continuation pages. The shipped `.docx` figures are not regenerated
  by this repository change.
- `scripts/verify_word.py` and the historical preview scripts used to write
  under `docs/qa/rebuild-preview` and `docs/qa/word-verification`. They now
  write under `_review/`; `scripts/docs_qa_guard.py` refuses protected paths.
- `scripts/requirements-docs.txt` is the pinned toolkit list. Use an existing
  venv that already contains those packages; this change adds none.

## Inventory summary

`scripts/` already provided `docx_inplace.py` (run-preserving text edits),
`insert_word_diagrams.py` (package-level image replacement/splitting),
`docx_open_check.ps1`/`update_fields.ps1`/`word_update_toc.ps1` (Word COM),
`render_pdf_pages.py`, `export_*.ps1`, `verify_docx.py` (integrity/facts) and
`verify_word.py` (deep audit, now redirected). The gap was a documented,
tested facade plus a schema-driven 67-card generator and a safety guard.

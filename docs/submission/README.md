# DBCAS submission documents

Frozen baseline: `develop2` at `6421b5ad44a0eaaeb9be8d26068c8ca434ae5bb7`.
Production is **HOLD**. The data is synthetic.

| File | Contents |
| --- | --- |
| `Proposal.docx` | Problem, goals, scope, stakeholders, technology, plan, risks, limitations |
| `Architecture.docx` | Context, containers/components, modules, flows, security, sandbox, deployment, flags, CI, ADRs |
| `Database.docx` | All 67 tables, 561 columns, 122 FKs, 159 indexes, 28 migrations, v1/v2 versioning |
| `SRS.docx` | Actors, functional requirements, use cases, NFRs, traceability, full API inventory |

## Regenerate

From the repository root, with the backend virtual environment (Python 3.13+):

```bash
backend/.venv/Scripts/python.exe -m pip install -r docs/submission/tools/requirements.txt
backend/.venv/Scripts/python.exe docs/submission/tools/render_diagrams.py
backend/.venv/Scripts/python.exe docs/submission/tools/build_docs.py
powershell -ExecutionPolicy Bypass -File docs/submission/tools/render_with_libreoffice.ps1
backend/.venv/Scripts/python.exe docs/submission/tools/build_page_map.py
backend/.venv/Scripts/python.exe docs/submission/tools/build_docs.py
powershell -ExecutionPolicy Bypass -File docs/submission/tools/render_with_libreoffice.ps1
backend/.venv/Scripts/python.exe docs/submission/tools/page_counts.py
backend/.venv/Scripts/python.exe docs/submission/tools/verify_submission.py
```

`render_with_libreoffice.ps1` uses LibreOffice headless to export PDFs to `rendered/`; `page_counts.py` writes the page/word inventory. The build is two-pass: the first render provides heading pages for the static TOC, the second render uses that page map. The verifier re-reads the four `.docx` files and
checks every generated number, table, migration, route, flag and diagram count against a fresh
`repo_facts.collect()` run. It writes `verification-report.json` and `verification-report.md`;
the required result is **0 failures**.

## Sources

- `tools/repo_facts.py` — schema introspection (hash-checked against `db/schema.sql`), migrations,
  route inventories, OpenAPI, config flags, Compose, CI and test evidence.
- `tools/test-evidence.json` — nearest green `develop2` CI run: backend 1911, frontend 459,
  browser 140 passed + 2 skipped (83 E2E + 54 QA + 3 smoke).
- `tools/descriptions.py` — table/column descriptions and type/constraint formatting.
- `tools/render_diagrams.py` — Graphviz DOT and Mermaid sources; rendered PNG/SVG in `assets/`.
- `tools/build_docs.py`, `tools/doc_*.py` — the FITAI cover and template styles, then generated content.
- `tools/verify_submission.py` — independent document re-read and assertion report.

The FITAI cover is copied from the owner's template at
`FITAI - Documents/1. Proposal Document/C1SE.56_ProposalDocument_SHFA_ver1.2.docx`; the copy in
`tools/fitai-template.docx` makes the build reproducible. The template's Office default palette
(accent `#4472C4`, orange `#ED7D31`, green `#70AD47`) is used for diagrams and table headers.

## Scope notes

- The broker (#80) is not in scope; `docker.sock` (#66) is a known limitation.
- Free/Pro is UI-only; no payment, backend route or stored plan.
- Seed snapshot (#89) is skipped; OTP (#25) is not adopted.
- No migration, table, route or default-on flag was added for these documents.
- `docs/qa/**` was not modified.

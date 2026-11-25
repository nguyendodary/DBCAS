# Phase 5 — ver1.3 Word verification (2026-11-25)

Four new Word deliverables were generated from the preserved sources into
`../Documents/Final-ver1.3`. No approved academic DOCX, source text, template,
application runtime, validator, migration, `docs/qa/**` or `.env` was changed,
and no draft DOCX was committed to the repository. The SRS filename uses the
fallback `C1SE.70_SRS_DBCAS_ver1.3.docx` because no authoritative
`C1SE.70_*_SRS_*` naming convention was found in the workspace.

| File | Bytes | SHA-256 | Word / PDF pages |
|---|---:|---|---:|
| `C1SE.70_ProposalDocument_DBCAS_ver1.3.docx` | 2,773,752 | `119b9be0214b1dddbc6b578416aa9bb6d3ed7677d8e47b47a6e602dd06388a5b` | 61 / 61 |
| `C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx` | 5,151,772 | `1914e650c07e8f47e713f8e5db008367df822ccfd19f0dcd12e58bee1ed5d629` | 78 / 78 |
| `C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx` | 3,709,183 | `918b3919685dd3b60bbcfd26bd428d6abfa2e8ddc4ebf36267a436e68ef4946d` | 72 / 72 |
| `C1SE.70_SRS_DBCAS_ver1.3.docx` | 55,569 | `e005c5a751ac675b90a1e68749eb8b3e3cc6fd25811335d1714755f04b4baddf` | 9 / 9 |

## Verification performed

- The narrow collector fix now derives `question_count.min/max/default` from
  `backend/app/services/practice_config.py:public_config()` and exposes typed
  limits from the same source. Independently re-run verification reported
  min 1 / max 13 / default 5, single-type 50/5/10, mixed 20/2/3 and mixed
  total 25, all matching `public_config()`.
- Final document audit: **79 assertions, 79 passed, 0 failures**.
- Database dictionary: 67 sections, 561 columns, 67 overview rows, 0
  type/nullability errors. Schema facts: 67 tables / 561 columns / 122 FKs /
  159 indexes / 28 migrations.
- ZIP/OOXML, relationship, content-type and existing toolkit validation passed
  for all four files.
- Word COM 16.0 refreshed `TOC`/`SEQ` fields, saved and reopened all four
  documents; page counts were 61 / 78 / 72 / 9. Fresh Word PDF exports have
  the same page counts.
- Source SHA-256 comparison confirmed 8/8 preserved sources unchanged.
- `ruff check scripts/doc_facts.py scripts/build_ver13_documents.py` and
  `python -m py_compile` both exited 0 when re-run by the recovering agent.
- File hashes above were recomputed from the final DOCX files by the recovering
  agent and match the verification manifest.

Full command/exit tables and logs are in
`../Documents/Final-ver1.3/verification/commands.md`,
`final-manifest.json`, `fact-audit-final.log`, `schema-dictionary-audit.log`,
`docx-toolkit-validation.log`, `word-open-final.log` and `visual-audit.md`.
Labeled contact sheets and rendered PDFs are under `verification/contact-sheets`
and `rendered`. Visual review covered representative covers, front matter,
body/table pages, diagram families, headers/footers and final pages; all nine
SRS pages were inspected. This is representative visual verification, not a
claim that every page was manually inspected.

## Owner gates and limitations

- Document approvals and the public demo URL remain **OWNER UNKNOWN**. Team
  roles and schedule were preserved from verified v1.2 sources, not invented.
- Production release and provider-privacy gates remain owner decisions;
  production stays **HOLD**.
- Committing revised academic DOCX into `docs/academic/` would be an
  owner-approved product/snapshot decision and was not performed here. The
  deliverables remain outside the Git checkout at `../Documents/Final-ver1.3`.
- The earlier Word COM probe is preserved in
  [phase5-word-com-probe.log](phase5-word-com-probe.log).

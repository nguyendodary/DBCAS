# Academic documents — active version v1.2

The active official academic deliverables for DBCAS are the three Word
documents below, version 1.2 dated 08 November 2026. They were rebuilt from
`db/schema.sql` introspection, Compose/OpenAPI/frontend sources and the
regenerated diagrams; see `docs/qa/doc-discrepancies.md` for the before/after
discrepancy list and `docs/qa/docx-build-manifest.json` for build facts.

| Document | Active file | Archived |
| --- | --- | --- |
| Project Proposal Document | [C1SE.70_ProposalDocument_DBCAS_ver1.2.docx](C1SE.70_ProposalDocument_DBCAS_ver1.2.docx) | [ver1.1](C1SE.70_ProposalDocument_DBCAS_ver1.1.docx) |
| Architecture Design Document | [C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx](C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx) | [ver1.1](C1SE.70_ArchitectureDesign_DBCAS_ver1.1.docx) |
| Database Design Document | [C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx](C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx) | [ver1.1](C1SE.70_DatabaseDesign_DBCAS_ver1.1.docx) |

`C1SE.70_UserStoryDocument_DBCAS_ver1.1.docx` is kept unchanged as a historical
document; it is **not** part of this reconciliation (three-document scope) and
still contains the retired FORMAL/PRACTICE wording. The team must update it
separately: `[CẦN NGƯỜI ĐIỀN]`.

What v1.2 states (all verifiable in the repo):

- Learner-defined practice only (concepts, 3 difficulty bands, count 1–20,
  source `bank`/`ai`); no prebuilt exams, no admin exam creation, no fixed
  10/2/1 mix, no 13-question/60-minute contract.
- `source=ai`: AI generates MCQ/essay only; SQL always comes from the validated
  bank; exact-count guarantee; one-line `bank_mixed` notice.
- Two result flows from one `system_setting.result_flow`: `IMMEDIATE`
  (Tự động) / `HUMAN_VERIFIED` (Admin duyệt).
- Two-AI pipeline: Prompt Builder (local model or template fallback,
  `prompt_hash`) → Evaluator (external LLM or rule fallback).
- Admin has exactly 5 screens.
- PostgreSQL 17: 41 tables, 293 columns, 59 foreign keys, 87 indexes,
  0 enum types, 19 migrations. Four legacy/retired tables are shown explicitly
  in the ERD, never hidden.
- 6 Compose services (+ QA-only `qa-ai`, opt-in real-QA meter), 82 OpenAPI
  paths / 93 operations, 23 frontend routes.

Diagrams (generated, not hand-drawn): `docs/diagrams/generated/`
`system-context.png`, `erd.png` (+ 3 page slices), `table-relationships.png`
(+ 2 page slices). Automated gates: `npm run docs:check` (includes
`diagrams:check`, `check_docs.py`, `verify_docx.py`) wired into CI.

Only official academic files belong here (see
[`CONTRIBUTING.md`](../../CONTRIBUTING.md)). Review PDFs, rendered figures,
historical revisions, drafts and backups are **not** stored in this directory.

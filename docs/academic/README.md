# Academic documents — active version v1.2

The three official academic deliverables are the **original English v1.1
documents revised in place** to version 1.2 (08 November 2026). Cover pages,
headers/footers, heading styles, numbering, fonts, table styles, page layout,
TOC and revision-history format are inherited from the v1.1 packages; only
factually wrong, missing or retired content and the ten approved diagrams were
changed.

| Document | Active file | Previous revision |
| --- | --- | --- |
| Project Proposal Document | [C1SE.70_ProposalDocument_DBCAS_ver1.2.docx](C1SE.70_ProposalDocument_DBCAS_ver1.2.docx) | [ver1.1](C1SE.70_ProposalDocument_DBCAS_ver1.1.docx) |
| Architecture Design Document | [C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx](C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx) | [ver1.1](C1SE.70_ArchitectureDesign_DBCAS_ver1.1.docx) |
| Database Design Document | [C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx](C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx) | [ver1.1](C1SE.70_DatabaseDesign_DBCAS_ver1.1.docx) |

`C1SE.70_UserStoryDocument_DBCAS_ver1.1.docx` is kept unchanged as a historical
document; it is **not** part of this reconciliation (three-document scope) and
still contains the retired FORMAL/PRACTICE wording. The team must update it
separately: `[CẦN NGƯỜI ĐIỀN]`.

What the v1.2 documents state (all verifiable in the repository):

- Learner-defined practice only (concepts, 3 difficulty bands, count 1–20,
  default 5, source `bank`/`ai`); no prebuilt exams, no admin exam creation,
  no fixed 10/2/1 mix, no 13-question/60-minute contract.
- `source=ai`: AI generates MCQ/essay only; SQL always comes from the validated
  bank; exact-count guarantee; one-line `bank_mixed` notice.
- One mandatory release flow: AI grades/evaluates first, then an administrator
  reviews and approves. Only approved results are published; the old
  `IMMEDIATE` / `HUMAN_VERIFIED` choice is gone from the UI.
- Two-AI pipeline: Prompt Builder (local model or template fallback,
  `prompt_hash`) → Evaluator (external LLM or rule fallback).
- Google/GitHub OAuth supports sign-in and Learner sign-up; verified-email
  matching links one account and preserves existing roles. Login and Register
  retain both provider choices without credentials and explain email sign-in.
  Single-use handoffs issue rotating access/refresh sessions.
- Admin navigation has five destinations: Cohort overview, Grading, Accounts,
  Questions, System.
- PostgreSQL 17: 41 tables, 293 columns, 59 foreign keys, 87 indexes,
  0 enum types, 19 migrations. Four legacy/retired tables are marked, never
  hidden: `assessment`, `assessment_concept`, `assessment_question`,
  `assessment_blueprint`.
- 6 Compose services (+ QA-only `qa-ai`, opt-in real-QA meter), 82 OpenAPI
  paths / 92 operations, 23 frontend routes.

OAuth text reconciliation (20261112 request, performed 2026-11-11): 31 minimal
English replacements across the three v1.2 files, including the read-only
System page. Only `word/document.xml` changes; all original runs, appearance,
media, names/dates and other package parts are preserved. Two Architecture
caption fields are repaired in place to prevent duplicate table numbers on
refresh; four cached contents/table page references match native Word.
Pre-edit backups are in the ignored
`docs/_backup-docx-oauth-20261112/` and are ASK/preserved until owner confirmation.
See [the exact edit/format evidence](../qa/oauth-20261112/word-edits.json).
Native Word opens all three without repair (59/70/40 pages); contents, figure
and table caches remain unchanged after field refresh. Rendered pages and the
native Word layout of changed text/captions were visually checked; see
[render evidence and the LibreOffice limitation](../qa/oauth-20261112/word-render-qa.json).
No diagram-level service, table or directed flow changes in this restoration;
the existing approved OAuth Providers elements remain intact.

Verification evidence:

- Discrepancy list: [`docs/qa/doc-discrepancies-v2.md`](../qa/doc-discrepancies-v2.md)
- Diagram element check:
  [`docs/qa/doc-v2-diagram-elements.md`](../qa/doc-v2-diagram-elements.md)
- Before/after page contact sheets:
  [`docs/qa/doc-v2-verification/`](../qa/doc-v2-verification/)
- Original and redrawn diagram images:
  [`docs/qa/doc-v2-original-diagrams/`](../qa/doc-v2-original-diagrams/) and
  [`docs/qa/doc-v2-new-diagrams/`](../qa/doc-v2-new-diagrams/)
- `npm run docs:check` verifies the schema/data dictionary, language and
  retired-statement rules against the three active files.

Only official academic files belong here (see
[`CONTRIBUTING.md`](../../CONTRIBUTING.md)). Review PDFs, rendered figures,
historical revisions, drafts and backups are **not** stored in this directory.

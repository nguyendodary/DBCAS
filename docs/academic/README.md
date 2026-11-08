# Academic documents — working base v1.1, revision v1.2 in progress

The three official academic deliverables are being revised **in place** from
their original English v1.1 files. The rejected v1.2 rebuild (different
layout, regenerated diagrams, Vietnamese body) was moved out of this folder
and is not used as a source.

| Document | Working base |
| --- | --- |
| Project Proposal Document | [ver1.1](C1SE.70_ProposalDocument_DBCAS_ver1.1.docx) |
| Architecture Design Document | [ver1.1](C1SE.70_ArchitectureDesign_DBCAS_ver1.1.docx) |
| Database Design Document | [ver1.1](C1SE.70_DatabaseDesign_DBCAS_ver1.1.docx) |

`C1SE.70_UserStoryDocument_DBCAS_ver1.1.docx` is kept unchanged as a historical
document; it is **not** part of this reconciliation (three-document scope) and
still contains the retired FORMAL/PRACTICE wording. The team must update it
separately: `[CẦN NGƯỜI ĐIỀN]`.

What the revised documents must state (all verifiable in the repo):

- Learner-defined practice only (concepts, 3 difficulty bands, count 1–20,
  default 5, source `bank`/`ai`); no prebuilt exams, no admin exam creation,
  no fixed 10/2/1 mix, no 13-question/60-minute contract.
- `source=ai`: AI generates MCQ/essay only; SQL always comes from the validated
  bank; exact-count guarantee; one-line `bank_mixed` notice.
- Two result flows from one `system_setting.result_flow`: `IMMEDIATE`
  (Tự động) / `HUMAN_VERIFIED` (Admin duyệt).
- Two-AI pipeline: Prompt Builder (local model or template fallback,
  `prompt_hash`) → Evaluator (external LLM or rule fallback).
- Admin navigation has five destinations: Cohort overview, Grading, Accounts,
  Questions, System.
- PostgreSQL 17: 41 tables, 293 columns, 59 foreign keys, 87 indexes,
  0 enum types, 19 migrations. Four legacy/retired tables are marked, never
  hidden: `assessment`, `assessment_concept`, `assessment_question`,
  `assessment_blueprint`.
- 6 Compose services (+ QA-only `qa-ai`, opt-in real-QA meter), 82 OpenAPI
  paths / 93 operations, 23 frontend routes.

Step 1 evidence: `docs/qa/doc-discrepancies-v2.md` and the exact embedded
original diagrams in `docs/qa/doc-v2-original-diagrams/`.

Only official academic files belong here (see
[`CONTRIBUTING.md`](../../CONTRIBUTING.md)). Review PDFs, rendered figures,
historical revisions, drafts and backups are **not** stored in this directory.

# Baseline replacement — final report

Date: 2026-11-26. Branch: `docs/quality-pass-20261125` (from `develop2` at
`66045b7`). Production: **HOLD**.

## 1. Takeover and preservation

The previous session's quality pass was preserved in commit `932ee76`
(branch `docs/quality-pass-20261125`) before any replacement. Its five
condensed DOCX were byte-compared to `Archive/quality-pass-20261125-before/`
and to `docs/submission/recovery/backups/` (SHA-256, all matched). The
condensed set was then copied to `Archive/rejected-final-20261126/` (49 files,
`MANIFEST.sha256`, README) and `docs/submission/final/` was deleted and
recreated. No other file was deleted.

## 2. Final documents

| Document | File | Pages | Date |
|---|---|---:|---|
| Proposal | `docs/submission/final/C1SE.70_ProposalDocument_DBCAS_ver1.3.docx` | 62 | 26/11/2026 |
| Architecture Design | `docs/submission/final/C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx` | 79 | 26/11/2026 |
| Database Design | `docs/submission/final/C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx` | 75 | 26/11/2026 |
| Code Standards | `docs/submission/final/C1SE.70_CodeStandards_DBCAS_ver1.3.docx` | 14 | 26/11/2026 |
| Technical Report | `docs/submission/final/C1SE.70_TechnicalReport_DBCAS_ver1.3.docx` | 15 | 26/11/2026 |

Baselines were 61 / 78 / 72 / 12 / 13. The +9 pages are the two uniform
appendices (owner decisions, figure sources), the explicit Mode 1/Mode 2
paragraph, the reflowed 11 pt captions and the rebuilt 13-page ERD/ledger set.
No section was cut to make a document shorter.

## 3. Proposal 15-section audit

All 15 sections are present, in order. Nine contained a fact/structure defect
that was fixed in place; see
`docs/submission/final/verification/proposal-sections.md` for the
section | status | fix table. Highlights: supervisor department aligned;
citations added; FR-06 split; nine-layer stack with AI/ML and Testing rows;
Mode 1/Mode 2 explicit; RSK-01 writable-demo wording corrected; `OWNER UNKNOWN`
removed; SRS deliverable line removed; [13] author corrected.

## 4. Figures

- 13 ERD/ledger pages generated from `schema-028/schema-introspection.json`
  (67 tables / 561 columns / 122 FKs / 159 indexes / 28 migrations).
- Seven module ERDs draw intra-module FK lines (58 FKs) and list 64 cross-domain
  references; four ledgers enumerate all 122 FKs with cardinality and delete
  rules.
- Gantt rebuilt from Proposal Table 13: 13 dated rows, final submission
  (10–13/12) before defence (17–26/12); status reports 03/10, 17/10, 20/11, 05/12.
- A legible backend-layering figure added to Code Standards.
- Every figure has a caption and a source entry in Appendix B.

## 5. Verification and gates

- `npm run docs:verify-word`: 5 documents, **148 assertions, 0 failures**.
- `npm run docs:check`: PASS, 48 assertions, 67/561/122/159/28.
- `npm run inventory:check`: PASS.
- `npm run secrets:scan`: 3 296 files, 0 findings.
- PDF checks: 0 near-empty pages, 0 margin overflows (61/79/75/14/15 pages).
- TOC/List of Tables/Figures: 0 page-number mismatches against the printed
  footers.
- Visual sample: Architecture TOC/List of Figures/landscape ERD, Database
  landscape ERD, Proposal Gantt, plus scripted checks on every page.
- CI: GitHub Actions Local quality gate run 45679605273, 14/14 jobs green
  at 94bb39901d11f255ac12bde97bad8fb704e7658f.

Word cannot update the TOC fields on this baseline without hanging; the DOCX
ships with `updateFields` disabled, and the TOC/lists were aligned from the
rendered PDF. The PDFs are correct.

## 6. Owner questions (O1–O10)

Team identities; official faculty/department and co-supervisor; approvals and
signature dates; public URL decision; survey date/method and per-product
citations; per-member effort and velocity; two-slot sandbox acceptance; legacy
table drop/retention; classical appendices; reference URL/DOI verification.
The same list is in Appendix A of each document and in
`docs/agent/freeze-logs/doc-verify.md` §8.

## 7. Not verified

No learner study, usability test, public deployment or provider-retention
decision. The two-stage AI audit and writable DML path were not re-executed for
this document set. CI for the new commit is recorded only after the push.

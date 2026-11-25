# DBCAS document index — authority, supersession, archive, open issues

Updated 2026-11-26. The two ver1.3 lineages are now explicitly separated: the
content-complete baseline was used for the submission, and the condensed
generated set is rejected and archived.

## Authoritative final files (submission scope)

| Document | File | Revision |
|---|---|---|
| Proposal | `docs/submission/final/C1SE.70_ProposalDocument_DBCAS_ver1.3.docx` | ver1.3, in-place revision 2026-11-26 |
| Architecture Design | `docs/submission/final/C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx` | ver1.3, in-place revision 2026-11-26 |
| Database Design | `docs/submission/final/C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx` | ver1.3, in-place revision 2026-11-26 |
| Code Standards | `docs/submission/final/C1SE.70_CodeStandards_DBCAS_ver1.3.docx` | ver1.3, in-place revision 2026-11-26 (no older DBCAS baseline) |
| Technical Report | `docs/submission/final/C1SE.70_TechnicalReport_DBCAS_ver1.3.docx` | ver1.3, in-place revision 2026-11-26 (no older DBCAS baseline) |

Matching PDFs: `docs/submission/final/rendered/*.pdf` (62 / 79 / 75 / 14 / 15
pages). Verification: `docs/submission/final/verification/` — 148 assertions,
0 failures; 0 near-empty and 0 overflow pages; TOC/list pages 0 mismatches.
Editable figure sources: `docs/submission/final/assets/erd/` (13 ERD/ledger
pages), `assets/figures/gantt-roadmap.svg`, `assets/figures/backend-layering.svg`
and the shared context/logical/pipeline sources in `assets/figures/`.

Baseline table and rationale: `docs/agent/freeze-logs/baseline-selection.md`.
Pre-revision backups: `docs/submission/recovery/backups/` (the rejected
condensed set is in `Archive/rejected-final-20261126/` with a SHA-256 manifest).

## Declared academic authority (different scope)

`docs/academic/C1SE.70_{Proposal,Architecture,Database}_DBCAS_ver1.2.docx` remain
the source of truth for `npm run docs:check` and describe the migration-027
schema (66 tables / 558 columns). They are intentionally **not** overwritten by
this revision; the submission set describes the versioned migration-028 schema
(67 tables / 561 columns). See `docs/academic/README.md`.

## Lineages

| Set | Location | Note |
|---|---|---|
| Content-complete baseline | `Documents/Final-ver1.3/` | 61 / 78 / 72 pages; the source of the Proposal, Architecture and Database revisions. Retained unchanged. |
| Rejected condensed set | `Archive/rejected-final-20261126/` | 20 / 22 / 40 / 12 / 13 pages; byte-for-byte copy with `MANIFEST.sha256`; not the submission. |
| Pre-rejection quality pass | `Archive/quality-pass-20261125-before/final/` | Same condensed set before the last quality pass; retained as history. |
| v1.2 owner copies | `Documents/Final/` | byte copies of the academic v1.2 files |
| Root revisions | `Documents/Archive/root-old-revisions/`, `root-v1.2-20261028/` | v1.3–v1.6 and older v1.2 snapshots |
| SRS | `Documents/Archive/C1SE.70_SRS_DBCAS_ver1.3.docx` and `srs-verification-20261125/` | explicitly de-scoped by the owner; no SRS in the five-document set |
| User Story | `Documents/Other/` (v1.2/1.4/1.5), `docs/academic/…ver1.1.docx` | outside the five-document scope |

## Verification and evidence

`docs/submission/before/`, `before-after/`, `submission-pack/`, `tools/`,
`recovery/` (reports, QA images, backups, staging) and
`docs/submission/final/verification/` (148-assertion report, PDF checks,
TOC/list alignment, proposal section audit).

## Unresolved / owner-gated issues

1. Team identities (student IDs, emails, phones) — Appendix A O1 in every document.
2. Official faculty/department name and whether an industry co-supervisor is
   required — O2.
3. Approval decisions, signature dates and review-panel representative — O3.
4. Public document URL, or an explicit decision that the demo remains local — O4.
5. Survey date/method and one citation per surveyed product — O5.
6. Per-member effort allocation, story points/velocity and sprint attendance — O6.
7. Sandbox capacity (two slots) acceptance for the demonstration — O7.
8. Whether the legacy `assessment*` tables may be dropped after the defence and
   the data-retention period — O8.
9. Whether to restore the classical use-case/component appendices — O9.
10. Reference URL/DOI verification and any missing source — O10.
11. `develop2 → main` promotion, release tag and production release remain
    owner-gated; production stays **HOLD**.

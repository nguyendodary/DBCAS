# DBCAS document index — authority, supersession, archive, open issues

Companion to `document-inventory.md`. This index exists so two "ver1.3" sets can
no longer be mistaken for one another.

## Authoritative final files (submission scope)

| Document | File | Revision |
|---|---|---|
| Proposal | `docs/submission/final/C1SE.70_ProposalDocument_DBCAS_ver1.3.docx` | ver1.3, revised 2026-11-25 |
| Architecture Design | `docs/submission/final/C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx` | ver1.3, revised 2026-11-25 |
| Database Design | `docs/submission/final/C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx` | ver1.3, revised 2026-11-25 |
| Code Standards | `docs/submission/final/C1SE.70_CodeStandards_DBCAS_ver1.3.docx` | ver1.3, revised 2026-11-25 |
| Technical Report | `docs/submission/final/C1SE.70_TechnicalReport_DBCAS_ver1.3.docx` | ver1.3, revised 2026-11-25 |

Matching PDFs: `docs/submission/final/rendered/*.pdf` (20 / 22 / 40 / 12 / 13 pages).
Editable figure source added: `docs/submission/final/assets/gantt-roadmap.svg`.
Byte-identical pre-revision backups: `docs/submission/recovery/backups/`.

## Declared academic authority (different scope)

`docs/academic/C1SE.70_{Proposal,Architecture,Database}_DBCAS_ver1.2.docx` remain
the source of truth for `npm run docs:check` and describe the migration-027 schema
(66 tables / 558 columns). They are intentionally **not** overwritten by this
revision; the submission set describes the versioned migration-028 schema
(67 tables / 561 columns). See `docs/academic/README.md`.

## Superseded versions (retained, not deleted)

| Set | Location | Note |
|---|---|---|
| Older ver1.3 attempt | `Documents/Final-ver1.3/` | 61 / 78 / 72 pages, content-complete baseline, `OWNER UNKNOWN` on cover; not the submitted set |
| v1.2 owner copies | `Documents/Final/` | byte copies of the academic v1.2 files |
| Root revisions | `Documents/Archive/root-old-revisions/`, `root-v1.2-20261028/` | v1.3–v1.6 and older v1.2 snapshots |
| SRS | `Documents/Archive/C1SE.70_SRS_DBCAS_ver1.3.docx` and `srs-verification-20261125/` | explicitly de-scoped by the owner; do not revive without a decision |
| User Story | `Documents/Other/` (v1.2/1.4/1.5), `docs/academic/…ver1.1.docx` | outside the five-document scope |

## Verification and evidence (retained)

`docs/submission/before/`, `before-after/`, `submission-pack/`, `tools/`, and this
`recovery/` folder (reports, QA images, backups, staging copies).

## Unresolved / owner-gated issues

1. Approval decisions, signature dates, review-panel representative and public
   document URL are `[OWNER TO PROVIDE: …]` placeholders in all five documents.
2. Official faculty/department name ("CSE Center" vs "Software Engineering
   Department") and whether an industry co-supervisor is required.
3. Per-member effort allocation, story points/velocity and sprint attendance.
4. Survey date, method and one citation per surveyed product; only LeetCode is
   documented in detail.
5. Whether the legacy `assessment*` tables may be dropped after the defence, and
   the data-retention period for learner attempts.
6. Sandbox capacity (two slots) acceptance for the demonstration.
7. Whether to restore the classical use-case/component/TRD appendices that were
   dropped when the ver1.3 set was regenerated (see `document-inventory.md` §4.2).
8. `develop2 → main` promotion, release tag and production release remain
   owner-gated; production stays **HOLD**.

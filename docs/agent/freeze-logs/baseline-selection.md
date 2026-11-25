# Baseline selection — five ver1.3 documents

Date: 2026-11-26. The submission set was rebuilt by editing copies in place, not
by regenerating prose. The three academic documents come from the
content-complete `Documents/Final-ver1.3/` lineage; the two net-new documents
have no older DBCAS baseline, so the best surviving files are used and that
limitation is stated explicitly.

| Document | Baseline file | Baseline pages | Why chosen |
|---|---|---:|---|
| Proposal Document | `Documents/Final-ver1.3/C1SE.70_ProposalDocument_DBCAS_ver1.3.docx` | 61 | Content-complete in-place descendant of the v1.2 academic proposal: all 15 required sections, 17 tables, 4 figures, 10,784 words. The only set that preserves the full problem/survey/scope narrative. |
| Architecture Design | `Documents/Final-ver1.3/C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx` | 78 | Content-complete: 7 sections, 54 numbered tables, 20 figure parts, use-case/container/component/module/allocation/ERD views, 10 sections with landscape pages. |
| Database Design | `Documents/Final-ver1.3/C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx` | 72 | Content-complete: 41 core table sections plus Appendix A.1–A.26, 43 numbered tables, 13 figure parts, 67-table coverage, PostgreSQL narrative and hardware/software requirements. |
| Code Standards | `Archive/rejected-final-20261126/C1SE.70_CodeStandards_DBCAS_ver1.3.docx` (quality-pass file) | 12 | **No older DBCAS Code Standards exists** in the repository, `Documents/`, or recovery backups. The FITAI set contains only a different project's `C1SE.56_CodeStandard_SHFA_ver2.0.docx`; it was used as the measured style reference, not for content. The best DBCAS file was revised in place. |
| Technical Report | `Archive/rejected-final-20261126/C1SE.70_TechnicalReport_DBCAS_ver1.3.docx` (quality-pass file) | 13 | **No older DBCAS Technical Report and no FITAI technical-report template exist.** This is the only DBCAS report lineage. It was revised in place; every quantitative claim remains tied to a saved log. |

## Identity and integrity

- Proposal baseline SHA-256 prefix: see `Documents/Final-ver1.3/verification/final-manifest.json` (byte match).
- Architecture and Database baselines: same manifest; all three opened with
  python-docx and Word before editing.
- The rejected condensed set is preserved byte-for-byte in
  `Archive/rejected-final-20261126/` with `MANIFEST.sha256`.
- In-place revisions were made with `scripts/revise_submission_docs.py`; figures
  were rebuilt from `schema-028/schema-introspection.json` with
  `scripts/build_erd_relationships.py` and from the Proposal Table 13 schedule
  with `scripts/build_gantt.py`.
- No baseline prose was regenerated from a template. The only new prose blocks
  are the two appendices (owner decisions and figure sources), added uniformly
  to all five documents.

## Page counts after revision

Filled by `docs/submission/final/verification/page-counts.json` after the Word
render. Baseline-to-final deltas are explained in `docs/agent/freeze-logs/doc-verify.md`.

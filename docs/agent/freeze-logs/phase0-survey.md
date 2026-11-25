# Phase 0 — workspace and branch survey

Survey date: 2026-11-25. Branch comparison baseline: `253f272`. Measurements
are apparent file bytes, not allocated disk blocks; junction and symlink targets
were excluded to prevent duplicate traversal. The workspace was measured before
the isolated recovery worktree was added. Full counts, timestamps and traversal
errors are in [phase0-workspace-sizes.tsv](phase0-workspace-sizes.tsv).

## Workspace root

All entries except `DBCAS` itself are siblings outside its Git worktree. A name
match in tracked text is evidence of a reference to that name, not proof that
the reference points to the sibling path or that a path with zero matches is
unused. The [reference scan](phase0-references.tsv) records matching files.

| Entry | Apparent bytes | Evidence and current disposition |
|---|---:|---|
| `.playwright-mcp` | 742,897 | Six tracked files mention the name; the Playwright MCP process is active. Keep. |
| `_review` | 3,405,648,592 | Historical reports and current test receipts; 331 name matches include CI and README. Keep. |
| `_worktrees` | 197,412,672 | Contains junctions; later received the active recovery worktree. Keep. |
| `Archive` | 14,227,413,685 | Historical material; generic-name matches do not establish whether individual contents are unused. Keep. |
| `C1SE.70_ArchitectureDesign_DBCAS_ver1.2.txt` | 82,865 | One exact tracked-name match; requested Word source. Keep. |
| `C1SE.70_DatabaseDesign_DBCAS_ver1.2.txt` | 40,045 | No exact tracked-name match; requested Word source. Keep. |
| `C1SE.70_ProposalDocument_DBCAS_ver1.2.txt` | 75,915 | No exact tracked-name match; requested Word source. Keep. |
| `DBCAS` | 4,222,471,452 | Active Git checkout, including ignored dependencies and local data. Keep. |
| `dbcas-doc-edits-backup.patch` | 20,388 | [Byte-identical](phase0-patch-comparison.log) to `git show --format= --binary 8bc95fb`; candidate for owner-reviewed deletion, not deleted. |
| `DBCAS-feature-merge` | 0 excluding links | Contains two junctions into DBCAS dependency directories; not a registered Git worktree. Keep pending review. |
| `dbcas-seed-cold-start-20261120-123031` | 3,398,888 | Contains timing logs and CI evidence despite no exact tracked-name match. Keep. |
| `dbcas-seed-diagnostics-20261120-144812` | 588,437,946 | Contains diagnostics and artifacts despite no exact tracked-name match. Keep. |
| `docs` | 87,457 | Sibling directory containing `PROJECT_AUDIT.md`; distinct from tracked `DBCAS/docs`. Keep. |
| `Documents` | 27,636,666 | Contains `Final`, `Archive`, and `Other` Word sources. Keep. |
| `FITAI - Documents` | 37,714,494 | Contains the requested design templates; ten tracked files mention the exact name. Keep. |
| `README.txt` | 2,815 | Three tracked files mention the filename; preserve as workspace guidance. |
| `Software Requiremen Specification Template.docx` | 1,216,503 | Exact filename appears in `docs/submission/REVISION-PLAN.md`; requested SRS source. Keep. |

The size scan recorded zero traversal errors. It does not follow the two
junctions in `DBCAS-feature-merge`, so zero bytes there does not mean that the
targets are empty. No workspace item or Git ref was deleted.

## Branches

Ahead/behind counts are relative to `253f272`; the full commit lists and merge
bases are in [phase0-branches.log](phase0-branches.log). The audit streamed and
hashed first-parent diffs for all 82 distinct commits and records their paths
in [phase0-branch-commits.tsv](phase0-branch-commits.tsv); binary assets were
not visually inspected. Representative product and documentation diffs were
examined in detail. One large 32 MB historical synchronization diff has not
been semantically reviewed line by line; its hash/path inventory is evidence,
not a claim that every change is redundant.

| Branch | Ahead / behind | Findings and proposed disposition |
|---|---:|---|
| `backup/main-before-privacy-cleanup-20261019` | 6 / 744 | Historical assessment, grading, accessibility, migrations and tests. `git cherry` marks four non-merge patches equivalent and one different; retain the branch and do not import old schema or behavior blindly. |
| `docs/pending-readiness-edits` | 1 / 99 | `8bc95fb` simplifies onboarding and adds readiness guidance, but also contains old provider assumptions and removes substantial newer README material. Preserve useful ideas for a fresh, evidence-based rewrite; do not merge as-is. |
| `frontend` | 24 / 913 | Earlier static and React UI work; its 24 commits are also in `origin/frontend`. Retain; no unreviewed merge. |
| `origin/feature/han` | 24 / 268 | Free/Pro upgrade and financial reporting plus related tests. The isolated mobile-header adjustment `3412ce6` may be useful only if the current UI reproduces overflow; review with the owner before any cherry-pick. Do not add the costs feature. |
| `origin/feature/truong-free-pro-costs` | 25 / 268 | Contains the `feature/han` history plus `bd95673`, including subscription logic and migrations. Outside the approved UI-only Free/Pro scope; retain without merging. |
| `origin/frontend` | 48 / 913 | Includes the earlier frontend history and later navigation, contrast and admin UI changes. `560911d` changes when unserved questions can be opened, so it is not a safe cosmetic cherry-pick. Retain without merging. |
| `origin/nguyen/forget-password` | 2 / 217 | OTP implementation and migration; owner decided OTP is outside scope. Retain without merging. |

No cherry-pick or merge was performed. `git cherry` reports patch equivalence,
not semantic equivalence; changed or unmatched patches were not assumed safe.
The initial audit encountered a Git text-conversion error on `07e4985` and
resumed that and the remaining diffs with `--no-textconv`; see
[phase0-branch-audit-issues.log](phase0-branch-audit-issues.log).

## In-repository candidates

- `backend/app/services/assessment_pool.py` is tracked and imported by
  `backend/tests/historical_assessment_api.py:96,103`; preserve it.
- `scripts/README.md:9` links to absent `scripts/ai.mjs`. The broken link is
  documented in `docs/ARCHITECTURE_FREEZE.md`; do not infer that recreating or
  deleting the script is approved.
- `_patch_group*.patch` was not found in the inspected locations. Do not list
  an unlocated file as a deletion candidate.

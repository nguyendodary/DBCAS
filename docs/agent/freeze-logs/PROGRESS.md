# Recovery progress

Last updated: 2026-11-25. Project checkout: `develop2`.

| Phase | Status | Evidence or next action |
|---|---|---|
| A | Recovery and inventory complete; previous A.4 scope exception recorded | [phase-a-recovery.md](phase-a-recovery.md) |
| B | Complete with one limitation | [baseline-v2.md](baseline-v2.md): all gates passed with recorded exit codes except the old pytest child exit-code capture limitation; E2E 11+36+36, practice 12/2 skipped, local smoke 3/3, QA 54/54, all static/provider/secret gates green. |
| 0 | Review complete with stated limitation | [phase0-survey.md](phase0-survey.md) records all branches; [phase0-large-sync-review.md](phase0-large-sync-review.md) disposes of all 236 remaining paths with no import candidate, while preserving the binary/generated-file limitation. |
| 3 | Proposal ready; D1 pending | [cleanup-proposal.md](cleanup-proposal.md); item 1 is the only proposed deletion. |
| 4 | Review complete; no product change | [ui-review.md](ui-review.md) records desktop/mobile/admin evidence and two D4-gated copy findings; no image snapshot, translation or behavior was edited. |
| 5 | Superseded by phase 8 | [doc-verify.md](doc-verify.md) now records the five-document set; the earlier four-file record is history. |
| 6 | Complete | [final-gates-v2.md](final-gates-v2.md) records all local gates, QA-stack teardown and exact-commit CI run `45597486074` **success** (14/14 jobs). |
| 7 | Gates verified; no merge | [phase7-branch-gates.md](phase7-branch-gates.md): `main` unchanged, no open PR, no branch protection/ruleset bypass. |
| 8 | Document set complete; recovered push passed CI | SRS removed from the owner set (archived to `Documents/Archive/`), five `ver1.3` documents committed under `docs/submission/final`, FITAI layout measured from all 31 reference files, 149 XML assertions and 0 failures, clean-clone run passed. |

## Phase 8 — owner document set (2026-11-25)

- **SRS removed.** `C1SE.70_SRS_DBCAS_ver1.3.docx` was copied to
  `Documents/Archive/`, deleted from `Documents/Final-ver1.3`, and removed from
  the generator, both ver1.3 manifests, `docs:verify-word` and the traceability
  matrix. `scripts/build_ver13_documents.py` is deleted; the new generator
  cannot produce an SRS.
- **Formatting.** Every file in `FITAI - Documents` (14 DOCX, 15 PDF, 2 XLSX)
  was opened and measured; the Architecture file was chosen as the base and the
  documents are generated rather than cloned. Applied: A4, left 3.5 cm, top,
  bottom and right 2 cm, body 13 pt Times New Roman at 1.5, FITAI palette and
  cover, author `Do, Nguyen Quoc`. Exceptions are listed in
  [doc-style-spec.md](doc-style-spec.md).
- **Documents.** Proposal 20 pages, Architecture 22, Database 39, Code
  Standards 12, Technical Report 13; Word and PDF counts agree. Every figure
  was re-measured: 67 tables / 561 columns / 122 foreign keys / 159 indexes /
  28 migrations, 106 paths / 118 operations, 1 940 backend tests, 463 frontend
  tests, and zero whole-tree secret findings.
- **Proposal.** The 15 required sections already existed in order; ten carried
  content defects. Fixed: supervisor department conflict marked for the owner,
  unsourced survey replaced with cited literature, scope list restructured,
  `FR-06` split, AI/ML and testing rows added to the stack, risk register
  aligned with the writable demo, `OWNER UNKNOWN` placeholders replaced by
  explicit owner fields, and IEEE citations added in the text.
- **Source code.** `docs/submission-pack/SOURCE_CODE.md` records the commands,
  the observed gate results and the clean-clone run (`npm ci`, `env:check`,
  `npm start`, `/readiness` ready with database and sandbox true).
- **Gates.** `docs:check` PASS (48 assertions), `docs:verify-word` PASS (5
  documents, 149 assertions, 0 failures), `inventory:check` PASS,
  `secrets:scan` PASS (0 findings).
- **CI.** The interrupted push at `272e0df` passed all 14 jobs at 21:04 ICT on 25 November. [GitHub Actions run 45624475593](https://github.com/nguyendodary/DBCAS/actions/runs/45624475593).

## Next commands

[Step 0 inventory and recovery receipts](recovery-20261125-2054.md) cover all seven tasks. The five submission files are under `docs/submission/final/`. The external `Documents/Final-ver1.3` directory contains earlier material.

The interrupted push passed. For the recovery commits, push normally with `git push origin develop2`. Check the exact published revision with `gh run list --branch develop2 --commit <full HEAD SHA>` and watch that run through completion. The machine-local receipt for the recovery push is `_review/recovery-20261125-2054/final-ci.json`.

Separate owner decisions include
D1 cleanup deletion, D3 `develop2 → main` promotion, D4 approval of the two
stale-copy corrections, and the owner facts listed in
[doc-verify.md](doc-verify.md#8-owner-questions-raised-by-this-verification).
Production stays **HOLD**.

Never print secrets or commit `.env`; do not modify `docs/qa/**`, applied
migrations, validators or scoring schema; do not add dependencies, relax or
delete tests, force-push, rebase published history, or delete remote refs.
No changes to `main` are authorized before the release gate.

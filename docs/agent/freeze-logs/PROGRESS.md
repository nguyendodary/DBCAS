# Recovery progress

Last updated: 2026-11-26. Project checkout: `docs/quality-pass-20261125`
(created from `develop2` at `66045b7` on 2026-11-25 23:59 ICT).

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
| 9 | Baseline replacement complete; local gates green | The interrupted quality pass is committed as `932ee76`. The condensed set was archived to `Archive/rejected-final-20261126/` (49 files + `MANIFEST.sha256`), `docs/submission/final` was recreated, and the content-complete baselines were revised in place. Final pages 62/79/75/14/15; 148 XML assertions, 0 failures; 0 near-empty and 0 overflow PDF pages; TOC/list page numbers match the printed footers. See §Phase 9 below. |

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

## Phase 9 — baseline replacement takeover (2026-11-26)

State verified from files, not from the interrupted transcript.

| Item | Observed |
|---|---|
| Git root | `C:\Users\kudot\Downloads\proposal test\DBCAS` (the parent workspace is not a Git repository) |
| HEAD | `66045b7` — `docs(agent): close the interrupted submission CI record` |
| Branch | `docs/quality-pass-20261125`, cut from `develop2` (`origin/develop2` = same SHA) |
| Working tree | 19 modified tracked files and 6 untracked groups; the five `docs/submission/final` DOCX are the interrupted quality pass |
| Backups | `docs/submission/recovery/backups/` = byte-identical to HEAD versions (SHA-256 prefix for Proposal `1A50115D…`, Architecture `8F72A278…`, Database `AA009B2F…`, Code Standards `B43CEABA…`, Technical Report `FAC7A8F0…`); `Archive/quality-pass-20261125-before/final/` = byte-identical to the current five (Proposal `540FF23F…`, Architecture `2FBFE66F…`, Database `E7AE9FD6…`, Code Standards `C3864B46…`, Technical Report `1DD64E51…`) |
| `docs/submission/final` | **Not deleted.** Still the condensed regenerated set (20/22/40/12/13 pages), quality-pass revised. No `Archive/rejected-final-*` exists yet. |
| Content-complete baseline | `Documents/Final-ver1.3/` — Proposal 61, Architecture 78, Database 72 pages; 21/58/72 DOCX tables; 5/21/15 images; author `Do, Nguyen Quoc`; all three carry the 67-table/561-column/122-FK/159-index/28-migration facts in text. |
| Code Standards / Technical Report | No older DBCAS baseline exists in the repository, `Documents/`, or the recovery backups; only the current net-new 12/13-page files. The nearest FITAI reference is `FITAI - Documents/11. Code Standard/C1SE.56_CodeStandard_SHFA_ver2.0.docx`; no FITAI Technical Report template exists. |

The interrupted session's quality pass is preserved in a commit before any
replacement, so none of its factual corrections or QA evidence is lost. The
owner mission then starts by archiving and replacing the condensed set with
in-place revisions of the content-complete baseline.

## Phase 9 result

- **Archive.** `Archive/rejected-final-20261126/` holds the 49-file condensed
  set, a README and `MANIFEST.sha256`; every DOCX hash matches the rejected
  copy. No other file was deleted.
- **Working set.** `docs/submission/final` was recreated and filled with the
  three `Documents/Final-ver1.3` baselines and the two best-surviving DBCAS
  Code Standards / Technical Report files (no older baselines exist). Baseline
  table: [baseline-selection.md](baseline-selection.md).
- **In-place revision.** No prose was regenerated from a template. Common
  fixes: A4, 3.5/2/2/2 cm margins, 13 pt/1.5 body, explicit Normal style,
  author/creator/lastModifiedBy, date 26/11/2026, running heads/feet, captions
  11 pt, TOC/list page alignment. Document fixes: supervisor department,
  citations, FR-06 split, nine-layer stack, Mode 1/Mode 2, risk RSK-01, URL
  placeholders, SRS deliverable removed, Table 54 title, 67-table sentence.
- **Figures.** 13 ERD/ledger pages rebuilt from introspection (67/561/122,
  58 intra-domain + 64 cross-domain FKs); the Gantt rebuilt from Table 13
  (13 dated rows, final submission before defence); a legible backend-layering
  figure added to Code Standards. Every figure has a caption and a source table
  in Appendix B.
- **Page counts.** 62 / 79 / 75 / 14 / 15 (baseline 61 / 78 / 72 / 12 / 13).
  Deltas are the two appendices, the Mode 1/2 paragraph, the reflowed captions
  and the rebuilt figure pages; no content was cut to shorten a document.
- **Verification.** `docs:verify-word` 148 assertions / 0 failures;
  `docs:check` 48 assertions / PASS; `inventory:check` PASS; `secrets:scan`
  3 296 files / 0 findings; PDF checks 0 near-empty and 0 overflow pages; TOC
  and list page numbers 0 mismatches. Evidence: [doc-verify.md](doc-verify.md),
  `docs/submission/final/verification/`.
- **Limitation.** Word hangs when updating TOC fields on this baseline, so the
  DOCX ships with `updateFields` disabled and the TOC/lists are aligned from
  the rendered PDF. The rendered PDFs are correct.
- **Owner decisions.** The ten open items (O1-O10) are in Appendix A of each
  document and in [doc-verify.md](doc-verify.md#8-owner-questions-raised-by-this-verification).
- **Production.** HOLD. No `main` change, merge, tag or deployment.

## Phase 10 — diagram 1:1 restoration takeover (2026-11-26)

The previous session stopped on the image-limit guard after restoring the
Proposal, Architecture and Database figures. The uncommitted state was saved as
[recovery-20261126-1105.patch](recovery-20261126-1105.patch) with an untracked
manifest and a [recovery receipt](recovery-20261126-1105.md).

| Step | Status | Evidence |
|---|---|---|
| audit | complete | [diagram-audit.md](../../submission/final/verification/diagram-audit.md): 44 body images, 37 restored/shared originals, 1 new figure, 5 logos, 0 defects |
| restore | complete | Proposal 4/4, Architecture 20/20, Database 13/13 byte-identical to `Documents/Final-ver1.3`; Technical Report pipeline exact baseline bytes; Code Standards new figure has no baseline source |
| verify | complete | Word PDFs 61/79/76/17/18; `docs:check` 48/48, `docs:verify-word` 148/148, `inventory:check` PASS, `secrets:scan` 3 417 files / 0 findings; PDF 0 near-empty / 0 overflow; TOC and lists 0 mismatches |
| finish | complete | pushed to `develop2`; CI run [`45763819399`](https://github.com/nguyendodary/DBCAS/actions/runs/45763819399) passed all 14 jobs at `5583013` |

The baseline original-style SVGs already carry the current facts: `(67 tables)`
on the container/component pages, and the 11-page TRD set covers 67 tables,
561 columns, 122 foreign keys and 28 migrations. No figure is listed as
minimally extended. The Code Standards layering figure is the only new drawing;
it copies the original ERD/TRD style values and replaces the earlier blue
FITAI-palette asset. The stale `backend-layering.svg` and
`scripts/build_backend_layering.py` were retired with it.

**Phase 10 result.** Page counts are 61 / 79 / 76 / 17 / 18. The audit has 0
defects; the Word renderer produced 0 near-empty and 0 overflow pages; TOC and
list page numbers have 0 mismatches. `docs:check` passed 48 assertions,
`docs:verify-word` 148 assertions / 0 failures, `inventory:check` passed, and
`secrets:scan` covered 3 417 files with 0 findings. Word's default PDF export
stalled on the restored multi-megabyte media; the render used a fresh copy and
`SaveAs2` after clearing stale `~$` locks. The package-level fixes
(`updateFields=false`, static list entries, orphan-media pruning) are recorded
in the [recovery receipt](recovery-20261126-1105.md). CI run
[`45763819399`](https://github.com/nguyendodary/DBCAS/actions/runs/45763819399)
passed all 14 jobs at `5583013`; the final docs-only status commit is checked
separately.

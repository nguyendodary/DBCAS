# Change log — DBCAS document quality recovery

Date: 2026-11-25. Owner branch `develop2` at `66045b7`; no branch, commit, merge,
push, deletion or history rewrite was performed. All originals were backed up
byte-for-byte to `recovery/backups/` before editing.

## 1. Evidence gathered before editing

- `recovery-report.md` — repository/branch state, lineages, risks, tooling.
- `fitai-visual-audit.md` — measured FITAI design language (specialist A).
- `implementation-audit.md` — source-verified implementation state and traceability.
- `document-inventory.md` — every DBCAS document lineage and figure inventory.
- `defect-report.md` — independent audit of the five alleged final documents.
- `qa/contact-sheets/`, `qa/figures/`, `qa/fitai/`, `qa/text/` — visual and text evidence.

## 2. Files changed in place

The five authoritative DOCX at `docs/submission/final/` are revised **in place**;
no sixth "final" set was created. Staging copies were validated before promotion.

| Document | Change | Reason |
|---|---|---|
| Proposal ver1.3 | Publication-path wording corrected to the two actual flows; browser-spec count convention stated; Figure 1 replaced with a recreated FITAI-palette Gantt (new SVG source added to `assets/`); FITAI header/footer styling and cover signature rules; cover title aligned to FITAI size | C5, m1, M1–M3 in defect report |
| Architecture ver1.3 | Module/service counts corrected to the registered/runtime convention; header/footer and cover conventions aligned | C2, M1–M2 |
| Database ver1.3 | Index breakdown corrected from 68/41/51 (sum 160) to the measured 67/50/42 (sum 159); Table 4 standalone-index count corrected 51 → 42 and constraint-vs-index distinction explained; header/footer and cover conventions aligned | C1, M1–M2 |
| Code Standards ver1.3 | Router/service counts corrected and convention named; header/footer and cover conventions aligned | C3, M1–M2 |
| Technical Report ver1.3 | Unsupported/unattributed figures replaced with log-cited values (pytest duration, browser skips, secret-scan file count, CI commit attribution, contrast evidence, line counts); trigger breakdown added; figure claim qualified | C4, m2–m3 |

## 3. Supporting files changed

| File | Change |
|---|---|
| `docs/submission/final/assets/gantt-roadmap.svg` | **New** editable source for the recreated Gantt |
| `docs/submission/final/assets/gantt-roadmap.png` | Regenerated from the SVG in the FITAI palette |
| `docs/submission-pack/SOURCE_CODE.md` | Router/service counts, test counts/durations, secret-scan file count, CI commit attribution, browser-spec convention corrected |
| `docs/submission-pack/SUMMARY.md` | Test duration and secret-scan counts corrected; unsupported history-commit figure removed |
| `docs/agent/freeze-logs/doc-verify.md` | Log citations added; unsupported browser skips and stale file count removed |

## 4. What was deliberately *not* changed

- `docs/academic/` v1.2 files remain the declared `docs:check` authority and are
  untouched; their migration-027 numbers (66/558) are not overwritten.
- `Documents/Final-ver1.3/`, `Documents/Archive/`, `Documents/Other/` and all
  `before/`, `before-after/` evidence are untouched and not deleted.
- Existing ERD/TRD/C4 figures with editable sources are retained; only the
  unreadable legacy Gantt was recreated.
- Genuine owner-only fields (`[OWNER TO PROVIDE: …]` for approvals, public URL,
  capacity acceptance) are kept unresolved rather than invented.
- No new feature, table, migration, route or flag was introduced; production stays HOLD.

## 5. Content disposition (from `document-inventory.md`)

The regenerated ver1.3 set is intentionally more compact than the older 61/78/72-page
attempt. This revision restores accuracy and style but does not silently claim
content parity. The following retired material is recorded, not deleted: unsourced
survey prose (replaced by cited literature), the 41-table TRD card set (superseded by
the 67-table dictionary and schema-028 ERDs), and legacy component/ERD-2/2 figures
(superseded by module/allocation/schema-028 views). Any decision to restore the
classical use-case/component/TRD appendices in full is an owner decision.

## 6. Verification

See `visual-qa-report.md` and `technical-verification-report.md` for final evidence:
rendered PDFs, contact sheets, page-by-page review, structural gates and gate output.

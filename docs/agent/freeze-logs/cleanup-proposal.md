# Phase 3 — cleanup proposal (owner decision D1)

Prepared 2026-11-25 from [the workspace survey](phase0-survey.md). **No
deletion or move has been performed.** “No reference found” describes the
tracked-text name search only; it is not proof that an item is unused.

Paths without a `DBCAS/` prefix are relative to the workspace root, the parent
of the DBCAS checkout. Remote branches and tags are not deletion candidates.

| No. | Item | Type / tracked? | Evidence, risk and proposal |
|---:|---|---|---|
| 1 | `dbcas-doc-edits-backup.patch` | File; outside Git | [Comparison](phase0-patch-comparison.log) proves all 20,388 bytes match the diff for locally retained commit `8bc95fb`; no tracked file mentions this exact filename. **Propose delete only after explicit approval.** Risk: loss of the standalone backup if the retained local branch/object is later lost. |
| 2 | `DBCAS-feature-merge` | Directory; not a registered worktree or tracked | Contains two junctions pointing into DBCAS `node_modules`; the non-following survey found no ordinary files and no tracked exact-name reference. Process/path use was not exhaustively proven. **Keep pending further review**; never recursively follow its junctions. |
| 3 | `_worktrees/phase-b` | Directory; not a registered worktree | Observed dependency junctions; current use is not established. **Keep pending further review**; never recursively follow its junctions. |
| 4 | `.playwright-mcp` | Directory; outside Git | Playwright MCP is running and tracked records mention the directory. **Keep.** |
| 5 | `_review` | Directory; outside Git | Contains historical screenshots, logs, reports, and current test ownership receipts. **Keep.** |
| 6 | `_worktrees` | Directory; outside Git | Contains existing artifacts and the active recovery worktree. **Keep.** |
| 7 | `Archive` | Directory; outside Git | Historical contents have not been individually validated or duplicated. **Keep.** |
| 8 | `dbcas-seed-cold-start-20261120-123031` | Directory; outside Git | Contains CI timing and smoke evidence. **Keep.** |
| 9 | `dbcas-seed-diagnostics-20261120-144812` | Directory; outside Git | Contains diagnostics, PR artifacts, and reports. **Keep.** |
| 10 | `docs/PROJECT_AUDIT.md`, `Documents/`, `FITAI - Documents/`, `README.txt`, SRS template | Files/directories outside Git | Workspace audit, original submission documents, required templates, and guidance. **Keep.** |
| 11 | Three `C1SE.70_*_ver1.2.txt` files | Files; outside Git | Explicit sources for the new Word documents. **Keep until new documents are reviewed; no deletion proposed now.** |
| 12 | `DBCAS/backend/app/services/assessment_pool.py` | File; tracked | Imported by `backend/tests/historical_assessment_api.py`; historical API evidence depends on it. **Keep.** |
| 13 | `DBCAS/scripts/README.md` link to `ai.mjs` | Tracked README; target absent | The missing target is already documented in `docs/ARCHITECTURE_FREEZE.md`. **No file to delete**; consider a separate documentation correction after review. |
| 14 | `_worktrees/recovery-baseline-20261125/DBCAS` | Registered detached worktree; test-owned | In use for isolated Phase B browser/QA evidence. **Keep** while needed; any later removal requires the applicable owner decision and a fresh check for uncommitted or unique data. |
| 15 | Existing local and remote branches | Git refs | Several have unique commits; OTP and Free/Pro backend changes are outside scope. **Keep.** Remote ref deletion is forbidden. |

If the owner explicitly says **“xóa mục số 1”**, the concrete action is to
remove only `C:\Users\kudot\Downloads\proposal test\dbcas-doc-edits-backup.patch`
after rechecking its identity and byte comparison. It is outside the Git
checkout, so that deletion itself would not produce a Git commit; the decision
and result would be recorded in a separate documentation commit. No other
number is currently recommended for deletion.

The `_patch_group*.patch` files were not found in the inspected locations and
are therefore not presented as candidates.

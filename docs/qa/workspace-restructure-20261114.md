# Workspace restructure — 2026-11-14

Scope: `C:\Users\kudot\Downloads\proposal test`. Nothing was deleted. All
moves were on the same volume; content was preserved byte-for-byte except the
three active v1.2 copies placed in `Documents\Final` (identical SHA-256 to
`docs/academic`). The active worktree and `FITAI - Documents` stayed in place.

## Before

31 top-level items (12 Word files, 8 working/evidence folders, 2 trash
folders, 7 caches/logs/notes, 2 source/backup folders).

```text
proposal test\
  %temp%\  .playwright-mcp\  .qoder\
  _backup_main_worktree_20261110.patch  _docread\  _extract\
  _phase2_directive.txt  _review\  _trash-20261112\  _trash-20261113\
  _worktrees\  C1SE.70_*.docx (12)  DBCAS\  dbcas-db-backups\
  DBCAS-frontend-src\  devin-cleanup-backup\  docs\  FITAI - Documents\
  nul  output\
```

## After

7 top-level items.

```text
proposal test\
  DBCAS\                         main checkout, content untouched
  _worktrees\dbcas-dn-20261101\  active develop2 worktree, location unchanged
  Documents\
    Final\                       active Proposal/Architecture/Database v1.2
    Other\                       User Story v1.2/1.4/1.5
    Reference\                   note: FITAI stays at root
    Archive\                     root v1.2 copies + older revisions
  Archive\
    review\root-review\          former root _review
    extracts\{docread,extract,output}\
    backups\{dbcas-db-backups,devin-cleanup-backup,patch}\
    old-source\DBCAS-frontend-src\
    notes\_phase2_directive.txt
  _trash\
    20261112\ 20261113\ 20261114\
  FITAI - Documents\             kept in place (owner rule + inventory reference)
  README.txt
```

## Moves

| From | To | Reason | Reference check |
| --- | --- | --- | --- |
| `C1SE.70_{Proposal,Architecture,Database}_DBCAS_ver1.2.docx` (root) | `Documents\Archive\root-v1.2-20261028\` | Root copies are 2026-10-28 and predate the reconciled 2026-11-11 repo v1.2; kept for recovery, not presented as active | No script/CI/npm/Word reference; `docs/academic` is authoritative |
| `docs/academic/*_ver1.2.docx` | `Documents\Final\` (copy) | Single owner-facing Final set, byte-identical to the active repo files | `docs/academic` left untouched; SHA-256 verified |
| `C1SE.70_Proposal_ver1.5/1.6`, `Architecture_ver1.3/1.4`, `Database_ver1.4/1.5` | `Documents\Archive\root-old-revisions\` | Superseded revisions | No active reference |
| `C1SE.70_UserStory_ver1.2/1.4/1.5` | `Documents\Other\` | Out of the three-document scope; preserved | No active reference |
| `_review` | `Archive\review\root-review\` | Old root QA evidence; 13.8 GB | Active Playwright setup resolves `_worktrees\_review`, which remains; no active script points at the root copy |
| `_docread`, `_extract`, `output` | `Archive\extracts\...` | Generated extracts/old output | No active script/npm/CI reference |
| `dbcas-db-backups`, `devin-cleanup-backup`, `_backup_main_worktree_20261110.patch` | `Archive\backups\...` | Recovery copies; not runtime | No active reference; main-checkout patch preserved |
| `DBCAS-frontend-src` | `Archive\old-source\` | Earlier separate source snapshot | Historical docs name it only as a sibling; not active |
| `_phase2_directive.txt` | `Archive\notes\` | Historical owner directive | No active reference |
| `_trash-20261112` | `_trash\20261112\` | Merge quarantine | None |
| `_trash-20261113` | `_trash\20261113\` | Merge quarantine | None |
| `.playwright-mcp`, `.qoder`, `%temp%`, empty `docs`, `nul` | `_trash\20261114\` | Caches/empty/junk | None |
| partial duplicate of the 20261113 copy | `_trash\20261114\partial-copy-20261113\` | Failed long-path copy left a duplicate; preserved for owner deletion, not used | None |

`FITAI - Documents` was **not** moved: owner rule 2 protects it and
`docs/diagrams/inventory.json` contains 15 root-relative paths under it.
`_worktrees` was not restructured because it contains registered Git
worktrees; only `dbcas-dn-20261101` is active.

## Main checkout state

`DBCAS` is clean on `main`, one commit behind `origin/main`; it has no
uncommitted changes. Earlier work is preserved in its existing stash and in
`Archive\backups\_backup_main_worktree_20261110.patch` (286,575 B, 72 files
touched per the old inventory). No reset, checkout or discard was used.

## Safe delete

`_trash` is quarantined, not deleted. After owner review:

```powershell
Remove-Item -LiteralPath "C:\Users\kudot\Downloads\proposal test\_trash" -Recurse -Force
```

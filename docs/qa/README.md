# QA evidence

This directory holds reproducible QA evidence: screenshots, captured command output, audit reports, and review inventories. It is not a product documentation index.

## Evidence trees

| Tree                                                                              | Purpose                                                      |
| --------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `final-20261113/`                                                                 | Final W1–W6 acceptance evidence and screenshots              |
| `final-ui/`                                                                       | Final UI state/screenshot evidence                           |
| `rebuild-preview/`                                                                | Diagram rebuild previews, reports, and intermediate evidence |
| `logo-20261113/`                                                                  | Logo/brand verification evidence                             |
| `word-verification/`                                                              | Word/PDF rendering and document verification evidence        |
| `oauth-20261112/`                                                                 | OAuth root-cause, screenshots, and remediation evidence      |
| `diagram-originals/`                                                              | Diagram originals used for visual comparison                 |
| `doc-v2-*`                                                                        | Document v2 diagram/verification evidence                    |
| `final-20261103/`, `final-20261105/`, `final-20261110/`, `continuation-20261103/` | Historical acceptance snapshots                              |
| `screenshots/`                                                                    | Selected UI evidence                                         |
| `ai-20261114/`, `env-20261114/`                                                   | Targeted environment/AI audit evidence                       |

Top-level records such as `final-audit-20261113.md`, `task-audit.md`, and `handover.md` summarize these trees.

## Retention policy

- **Evidence, do not edit.** Preserve file bytes and names. Do not rewrite, format, normalize line endings, crop, or “clean up” files in these trees.
- **Files are hash-referenced.** Some evidence files are referenced by SHA-256 hashes in tests, manifests, or bundle records. Editing or moving them can break verification.
- **No moves or renames** without an owner-approved migration and a reference update.
- `raw/` directories, `*.log`, `*.zip`, and browser trace files are ignored by `.gitignore`; only deliberately selected, redacted evidence is committed.
- Prefer new dated subdirectories for new evidence. Add a short `README.md` or report in the dated tree rather than editing an older record.
- Large screenshot trees are retention candidates for external artifact storage, but deletion requires a separate owner decision.

## Reading order

Start with `final-audit-20261113.md` and `handover.md`, then open the dated tree referenced by the specific work item.

# PR #1 evidence retention

The November 12 remediation removes raw captures and reproducible logs with a normal commit. Their old paths in dated QA reports and inventory JSON describe historical runs; the files are no longer retained as current evidence. Those reports' claims are not new verification results.

| Previous scope | Paths | Bytes | Treatment |
|---|---:|---:|---|
| `docs/qa/final-20261113/w1/raw/**` | 123 | 46,035,702 | Removed, including the credential-bearing trace archive. |
| Tracked `docs/qa/**/*.log` | 62 | 88,678 | Removed; retain concise reports and structured summaries. |
| `docs/deliverables/5.14-final-report-slides.pptx` | 1 | 16,145 | Moved to `docs/academic/support/5.14-final-report-slides.pptx`; document references updated. |

The first two rows remove **185 paths / 46,124,380 bytes**. The old source locations of all three rows cover **186 paths / 46,140,525 bytes**; the slide bytes remain in the approved academic area.

Before deletion, the tracked documentation, CI configuration and npm/scripts sources were searched for the full paths and file names. Historical raw/log citations are labeled in the affected reports. Curated linked screenshots, the Word comparison galleries and diagram verification fixtures remain. No Markdown link resolved to an image in the removed raw subtree.

`.gitignore` now excludes raw QA directories, QA logs/ZIP files, browser trace archives and slide binaries outside the academic area. New captures belong under ignored `_review/` or restricted CI artifacts; redact authentication headers, cookies, credentials and personal data before sharing selected evidence.

Deleting tracked files does not erase Git history. Captured demo refresh sessions were explicitly revoked and the ignored demo signing-key configuration was rotated; see [the remediation record](pr1-remediation-20261114.md). No history rewrite or force-push is used.

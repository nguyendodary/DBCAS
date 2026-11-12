# Main protection and PR gates

PR #1 remediation keeps every existing backend/frontend Actions step and adds a separate `secrets` job. The workflow now runs for pushes to main/develop2 and pull requests targeting either branch. A skipped third-party review is not successful application CI.

The authenticated repository account's permissions were checked read-only and included `admin: true`. The following settings were applied and verified with the branch-protection API on November 12; never use an admin bypass:

| Setting | Required value |
|---|---|
| Target | `main` |
| Required status checks | `secrets`, `backend`, `frontend-local` from GitHub Actions app ID 15368 |
| Require up-to-date branch | yes |
| Pull request approval count | at least 1 |
| Dismiss stale approvals | yes |
| Enforce for administrators | yes |
| Allow force pushes / deletion | no / no |

Read current settings with `gh api repos/nguyendodary/DBCAS/branches/main/protection`. Review the exact final head and its check run URLs before approval. Merge only after the owner's later `merge approved`; do not merge during remediation.

## Secret gate

Run `npm run secrets:scan` for all tracked/new, non-ignored working-tree files. The configured pre-commit hook scans changed **index blobs**, so editing a working copy cannot conceal a staged credential. CI scans the checked-out tree, including ZIP/Office members; unreadable or oversized archives fail closed. Matches report only paths, rule names and line numbers, never values.

Rules cover JWT-like strings, provider/GitHub/AWS key formats, private-key headers and literal client-secret assignments. `scripts/secret_scan_allowlist.json` contains only manually reviewed fake OAuth/masking test fixtures, pinned to exact path, rule and value digest with a reason. Do not add directory-wide exemptions or real credentials. This is a pattern gate, not proof that every possible secret format is absent; historical exposed blobs remain in history and require revocation/rotation.

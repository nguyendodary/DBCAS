# PR #1 remediation record

Baseline reviewed: `44ab2c18df591ecf82520b5d50dfd23d6336039b`. Author remediation on the integration branch; no merge authorized.

## F1: captured demo credentials

Checked 2026-11-12T00:55:01.694142+00:00. Only iat/exp claims were decoded locally. IDs below are anonymous labels, not token fragments or hashes. The running demo DB was inspected read-only by SHA-256 token lookup; six idempotent logout calls then revoked the captured refresh families. No token or environment value was printed or persisted.

| ID | iat (UTC) | exp (UTC) | Expired | Refresh record after response |
|---|---|---|---|---|
| T01 | 2026-11-11T08:12:16Z | 2026-11-11T08:13:16Z | yes | not stored |
| T02 | 2026-11-11T08:12:13Z | 2026-11-18T08:12:13Z | no | revoked |
| T03 | 2026-11-11T08:13:52Z | 2026-11-11T08:14:52Z | yes | not stored |
| T04 | 2026-11-11T08:13:05Z | 2026-11-11T08:14:05Z | yes | not stored |
| T05 | 2026-11-11T08:12:13Z | 2026-11-11T08:13:13Z | yes | not stored |
| T06 | 2026-11-11T08:13:04Z | 2026-11-11T08:14:04Z | yes | not stored |
| T07 | 2026-11-11T08:13:52Z | 2026-11-18T08:12:13Z | no | revoked |
| T08 | 2026-11-11T08:14:01Z | 2026-11-11T08:15:01Z | yes | not stored |
| T09 | 2026-11-11T08:12:16Z | 2026-11-18T08:12:16Z | no | revoked |
| T10 | 2026-11-11T08:13:05Z | 2026-11-18T08:12:16Z | no | revoked |
| T11 | 2026-11-11T08:14:01Z | 2026-11-18T08:12:16Z | no | revoked |
| T12 | 2026-11-11T08:13:04Z | 2026-11-18T08:12:13Z | no | revoked |

Six access credentials had expired; all six refresh records are now revoked (five were previously consumed; one was still active). Every captured signature fails against the newly generated signing key written only to the ignored `.env`. These were QA/demo credentials captured against loopback port 18080.

**Activation boundary:** running dbcas-local containers were left running and still hold their previously loaded key. The captured credentials are already unusable because of expiry/revocation. A later owner-controlled API/container recreation must load the rotated configuration before claiming the running signing key itself has changed. Other existing demo sessions have not been globally invalidated.

Tree deletion does not remove historical blobs. Do not rewrite history; do not republish the trace.

## F4: artifact cleanup

See [exact scopes, counts and bytes](pr1-artifact-retention-20261114.md). All curated referenced screenshots and formal document/diagram verification fixtures remain.

## Finding resolutions

| Finding | Change | Integration commit / evidence |
|---|---|---|
| F1 | Captured sessions revoked; ignored signing-key configuration rotated; raw archive removed; staged/tree/ZIP secret gate and exact fake-fixture allowlist added. | `8a70b4b`, `4a39a79`; anonymous claims above. |
| F2 | Current/older public demo passwords fail startup outside development, including disabled accounts; known demo config values and initial-admin passwords are refused. Development still permits the demo. | `50f5b36`; 51 new deployment-policy cases plus expanded bootstrap/startup coverage. |
| F3 | Existing CI jobs/steps retained; main push/PR triggers and a separate secrets job added. Main protection applied after read-only admin confirmation. | `4a39a79`; [protection settings](main-protection-20261114.md). |
| F4 | 185 raw/log files deleted; referenced slides moved to the academic support area; historical citations labeled and narrow ignore rules added. | `8a70b4b`; [inventory](pr1-artifact-retention-20261114.md). |
| F5 | Seeded legacy-schema test upgrades through 018, records every application table's rows, then checks status-only 019, runner repetition and direct SQL repetition. SQL semantics/checksums remain unchanged. README/setup describe withdrawal of published exams, pg_dump backup and restoration. | `6a3468d`; corrected regression passed; existing migration matrix also passed. |
| F6 | Restored main's footer min-height/padding, settings section spacing and storage-note indentation; later neutral palette retained. | `273f8a4`; frontend lint/376 tests/build passed. |
| F7 | Ordinary-clone/main quick start replaces the author's checkout-specific instructions; PR checkout and linked-worktree configuration are explained. | `6a3468d`; launcher contract unchanged. |
| F8 | Diagram CLI pinned to 12.2.0, vulnerable KaTeX replaced with 0.18.10, lockfile and contributor pin updated. No figure baseline was weakened or regenerated to hide drift. | `2d27a13`; root/frontend audits both zero; docs gate passed. |
| F9 | All remediation subjects use Conventional Commits with the existing team-member identity and no AI/tool trailers. The 98 older nonconforming subjects are retained because shared history must not be rewritten. | Full remediation log; commit attribution hook remains active. |
| F10 | Removed both literal database credential fallbacks. Coverage retains its explicit DBCAS_COVERAGE_URL override; otherwise DATABASE_URL is mandatory. | `4bc116e`; 2 utilities compile and 5 isolated configuration checks pass. |

Each integration change is mirrored onto develop2 as a separate cherry-picked commit and pushed. Source-tree identity is checked after every mirror; no source edits are authored directly on develop2. Main's code/history are untouched. The original independent review remains an uncommitted historical input, not rewritten as author evidence.

## Executed local verification

| Check | Command / method | Result |
|---|---|---|
| Backend lint | `python backend/manage.py lint` using backend interpreter | PASS, all configured Ruff checks. |
| Touched backend | `python backend/manage.py test` for deployment_safety, bootstrap_admin, shared_auth, release_auth, migrations, DN database_initialization and refresh_tokens | 104 passed / 1 new-test failure in 31.67 s; fixed snapshot sorting to exclude the intentionally changed status. Only the failed test was rerun: **1 passed / 0.69 s**. **105 unique cases now pass**; no application migration change was needed. |
| Scanner regression | `npm run test:secrets` | **9 passed**; covers required formats, archive contents, exact allowlisting, staged-blob concealment and empty config values followed by another property. The final tree scan caught and corrected cross-line whitespace matching; templates are not exempted. |
| Whole-tree scanner | `npm run secrets:scan` | Initial calibration identified only seven fake-fixture occurrences; five exact allowlist entries reviewed. New negative-config fixture adds one exact entry. Final complete-tree result is recorded in the PR handoff after this documentation commit. |
| Frontend | `npm --prefix frontend run lint`; `npm --prefix frontend test -- --maxWorkers=2`; `npm --prefix frontend run build` | PASS; **43 files / 376 tests / 101.23 s**; build PASS. |
| Audits | Root and frontend `npm audit --json` | **0 advisories** each; root 204 / frontend 285 dependency records. |
| Environment | `npm run env:check` | PASS; all three AI variable names present and syntactically valid; values masked. No provider request made. |
| Documentation | `npm run docs:check` | PASS: **48 project assertions / 52 Word assertions / 10 model/render inventories**; **41 tables / 293 columns / 59 FKs / 87 indexes / 19 migrations / 82 paths / 92 operations / 23 routes**. Initial sandbox Chrome timeouts resolved by rerunning the unchanged gate outside the sandbox. |
| Word | `npm run docs:verify-word` | **3 documents / 0 failed**, all data/format/run/language/diagram checks clean. Initial sandbox COM logon failure was retried outside the sandbox: **all three Word COM open/field updates PASS**; source hashes unchanged. Generated timestamp-only report changes are kept out of source. |
| Utility configuration | Compile both content utilities; evaluate connection configuration with explicit override, fallback and missing-env cases without importing/executing DB work | **2 compile / 5 configuration checks PASS**. |
| CI | GitHub Actions on the final pushed integration head | See PR #1's exact-head run URL/result in the PR description and final handoff. Superseded/cancelled runs are not evidence for the final head. All three required jobs must succeed; no job or step was removed or bypassed. |

## Required operator/reviewer follow-up

- Obtain an independent GitHub approval and the owner's later `merge approved`; this author task does not merge or submit its own approval.
- Recreate the demo API/initializer later under owner control to load the rotated signing-key configuration and rebuilt code. Containers remain running during this task; captured credentials are already expired/revoked.
- Before promoting an existing database, take/restore-test the intended backup and notify teammates that migration 019 closes published prebuilt exams. A code revert does not restore assessment statuses.
- If the removed legacy database credential remains used elsewhere, its operator must rotate it separately. No running database password was changed.

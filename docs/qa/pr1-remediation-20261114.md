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

## Remaining implementation / verification

Secret gate, deployment policy, migration regression, onboarding/spacing/dependency cleanup, branch protection, branch synchronization and final head CI are in progress. This record will be completed before the final remediation commit.

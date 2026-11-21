# Owner decisions for PR-B1 (broker skeleton)

As of 2026-11-21. PR-B1 is the first implementation slice in the
[broker design](../sql-sandbox/broker/README.md#migration-and-validation): fixed
schema and authentication, no executor migration, behind a default-OFF flag.
Production remains **HOLD**; no decision below is inferred from production
access. Only items that block PR-B1 are in the first table. Everything else is
grouped under "Later". The QA-1 analysis is in
[qa1-sandbox-busy.md](qa1-sandbox-busy.md).

## Blocking PR-B1

| Question | Why it blocks PR-B1 | Proposed default | Consequence if unanswered | Needs owner |
| --- | --- | --- | --- | --- |
| Which channel and identity does the API use to call the broker, and who issues and rotates capabilities? | B1 freezes the authentication contract and must test peer identity, expired/replayed capabilities and forged requests ([design](../sql-sandbox/broker/README.md#proposed-protocol-and-authority)). | Unix socket with checked peer credentials for local/CI; mTLS with short-lived service certificates when deployed. Issuer is a broker deployment key; rotation is manual per release until automated. | B1 cannot fix its auth schema or acceptance tests; it remains design-only. | Platform security owner |
| What exact request/capability schema and trusted dataset source does the broker accept? | Schema validation, unknown-field rejection, digest verification and idempotent replay are B1 acceptance tests ([design](../sql-sandbox/broker/README.md#proposed-protocol-and-authority)). | Versioned JSON as illustrated in the design; UUID request IDs; SHA-256 dataset digest from a broker-owned allow-list; reject unknown fields, modes and duplicate IDs with different payloads. | Schema churn after B1 and no verifiable dataset-integrity test. | Security and data owner |
| Where does B1 run in local/CI, and what may it call? | B1 needs a runnable broker for contract tests without restoring a Docker socket to the API; the executor migration is deliberately deferred to B2. | A separate broker process/container with no Docker socket; a fake runtime for B1 tests; real container execution deferred to B2. | B1 is limited to unit tests with no integration acceptance evidence. | Operations owner |
| What is the flag/configuration contract and fail-closed behavior? | B1 must merge default OFF and leave the current sandbox path unchanged when disabled ([rollout](../sql-sandbox/broker/README.md#proposed-protocol-and-authority)). | `BROKER_ENABLED=false`; when off, the existing path is untouched; when on but the broker, identity verifier or audit sink is unavailable, reject all operations. | No safe merge or rollback story; B1 cannot be enabled for tests. | Owner and operations |
| May B1 audit records contain SQL text, and for how long are they retained? | The audit schema and redaction tests are part of B1; SQL text may contain learner data ([U14](../sql-sandbox/07-unknowns.md)). | No SQL text: script hash plus operation metadata and result class; 30-day retention. | Privacy risk, or a retention/schema migration immediately after B1. | Privacy owner |

## Later (not blocking PR-B1)

- **B2 substrate and executor isolation:** U6, U7, U8, U10, U11 and U15, plus the
  immutable image digest, rootless runtime and 512 MB / 256 PID / 60 s proposal.
  B1 does not migrate the executor, so these can follow before B2.
- **Capacity and performance:** U9, U17 and U18; queue size, per-subject quotas,
  deadlines and required CI checks. B1 can ship conservative constants, but B2
  and the QA-1 capacity work need measured values.
- **Writable grading and product semantics:** U1–U5, U12, U13 and U16. These
  block B3/B5, not the B1 skeleton.
- **QA-1 test expectation:** whether a bounded 503 is acceptable for the
  `concurrent_sql` assertion, or whether admission must guarantee success. This
  is an #71 product/SLO decision, not a B1 prerequisite; see
  [qa1-sandbox-busy.md](qa1-sandbox-busy.md).
- **Local `dbcas-*` inventory:** may the owner authorize a read-only
  identification of local `dbcas-*` containers and volumes, and who owns them?
  Proposed default: leave them untouched and run no local Docker test until the
  owner identifies them. This blocks local Docker verification, not B1 contract
  tests.
- **`docs/pending-readiness-edits`:** integrate selected edits or discard the
  local branch at `8bc95fb7ab423cba8583f092d64362cd6001838c`? Proposed default:
  keep it untouched, do not merge as-is against the stale `37a384a` baseline, and
  cherry-pick only after owner review. This does not block B1.

## Requested now

Answer the five blocking rows first; the later groups can follow in the order
shown. Until then PR-B1 stays unstarted, the broker remains documentation only,
and production stays on **HOLD**.

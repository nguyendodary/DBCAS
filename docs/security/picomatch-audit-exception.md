# Time-boxed frontend audit exception: GHSA-fc5q-39xc-vjpf

## Scope

The CI frontend security audit accepts exactly one advisory:
`GHSA-fc5q-39xc-vjpf` (picomatch ReDoS, affects `picomatch <= 4.0.7`).

The exception is active only until **2026-12-18 UTC**. After that date the audit
wrapper stops applying the exception and `npm audit --audit-level=high` runs
normally, so the same finding fails CI again.

This exception PR does not change dependency manifests or lockfiles. No audit
threshold was lowered, no step is skipped, and `continue-on-error` is not used.
Every other GHSA, every non-GHSA High/Critical advisory, unknown report
structure, and registry failure fails CI. The wrapper rejects legacy
fixture/date overrides and always runs the real npm audit in normal execution.

## Why

GitHub Advisory GHSA-fc5q-39xc-vjpf reports `picomatch <= 4.0.7` as affected and
lists **no patched version**. The latest published release is `4.0.7`; there is
no `4.0.8`. As of 2026-11-18, the upstream fix PR is open and is explicitly not
a security fix. The affected package is a transitive dev/build dependency of
Vite and Vitest, not a runtime frontend dependency.

## Accountability

- Accountable risk owner: DBCAS repository maintainer account `@nguyendodary`,
  acting as release/security gate owner.
- Tracking issue: https://github.com/nguyendodary/DBCAS/issues/36
- Deadline: **2026-12-18 UTC**.
- Monitoring cadence: at least weekly, the risk owner checks the GitHub Advisory
  and npm registry for a picomatch release newer than 4.0.7, and reviews the
  finding on every dependency-update PR. Each check is recorded in the tracking
  issue.

## Removal criteria

Remove the exception when all of the following are true:

1. A picomatch release newer than 4.0.7 is published and the advisory lists a
   patched version.
2. `frontend/package-lock.json` resolves to that patched version via
   `npm update`, without unrelated dependency changes.
3. `npm audit --audit-level=high` passes without the exception.
4. The removal PR merges and
   https://github.com/nguyendodary/DBCAS/issues/36 is closed.

## Remediation and follow-up PR plan

1. When a patched picomatch release exists, open a follow-up PR to `develop2`
   that refreshes `frontend/package-lock.json` with `npm update` (without
   unrelated dependency changes).
2. Run `npm audit --audit-level=high` without the exception and confirm it
   passes, together with the regression tests and frontend tests.
3. Remove the exception wrapper, its regression tests, the workflow step, and
   this document from the follow-up PR.
4. Close https://github.com/nguyendodary/DBCAS/issues/36 after the removal PR
   merges.
5. If no patched release exists by 2026-12-18 UTC, the exception expires
   automatically and CI fails. A new time-boxed exception requires a new
   owner-approved decision and a new tracking issue; do not extend this one.

## Verification

The audit wrapper prints the advisory ID, expiry date, and whether the exception
is active or expired on every CI run. The expiry is deterministic at the UTC
date boundary: 2026-12-18 is the last active day; 2026-12-19 runs the full
original `npm audit --audit-level=high`.

Regression tests: `node --test scripts/frontend_security_audit.test.mjs`.

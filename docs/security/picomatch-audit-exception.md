# Time-boxed frontend audit exception: GHSA-fc5q-39xc-vjpf

## Scope

The CI frontend security audit accepts exactly one advisory:
`GHSA-fc5q-39xc-vjpf` (picomatch ReDoS, affects `picomatch <= 4.0.7`).

The exception is active only until **2026-12-18**. After that date the audit
wrapper stops applying the exception and `npm audit --audit-level=high` runs
normally, so the same finding fails CI again.

No dependency manifests or lockfiles were changed. No audit threshold was
lowered, no step is skipped, and `continue-on-error` is not used. Every other
high/critical advisory, including a new advisory on the same packages, still
fails CI.

## Why

GitHub Advisory GHSA-fc5q-39xc-vjpf reports `picomatch <= 4.0.7` as affected and
lists **no patched version**. The latest published release is `4.0.7`; there is
no `4.0.8`. The upstream fix PR is open and is explicitly not a security fix.
The affected package is a transitive dev/build dependency of Vite and Vitest,
not a runtime frontend dependency.

## Removal condition

remove when picomatch has a patched release; then run npm update and drop the exception

## Verification

The audit wrapper prints the advisory ID, expiry date, and whether the exception
is active or expired on every CI run. The expiry can be simulated with
`DBCAS_SECURITY_AUDIT_NOW=YYYY-MM-DD`.

# Decision record

Append only. Each entry records evidence available when backfilled; later changes need a new entry.

## D01 | 2026-11-20 | OpenRouter release endpoint

Decision: staging/production OpenRouter routing accepts only `deepinfra/turbo`.
Reason: pin an approved private route; consequence: other endpoints fail release validation.
Evidence: [#61](https://github.com/nguyendodary/DBCAS/pull/61), [configuration](../../backend/app/config.py).

## D02 | 2026-11-20 | Preserve published v1 during regrade

Decision: admin regrade creates v2; v1 remains official during pending or failed analysis.
Reason: failed/interrupted analysis must not replace the published result; consequence: retry the reviewed v2.
Evidence: [#58](https://github.com/nguyendodary/DBCAS/pull/58), [#62](https://github.com/nguyendodary/DBCAS/pull/62).

## D03 | 2026-11-19 | Confirm large score changes

Decision: changes over 30% require confirmation before approval.
Reason: retain auditable review; consequence: the existing confirmation paths apply.
Evidence: [#59](https://github.com/nguyendodary/DBCAS/pull/59), [admin route](../../backend/app/routers/admin.py).

## D04 | 2026-11-20 | Read-only sandbox defaults

Decision: SELECT-only remains default; multi-statement, writable and state-grading flags default OFF.
Reason: preserve legacy behavior and isolate unreviewed capabilities; consequence: writable and state grading remain unimplemented.
Evidence: [#65](https://github.com/nguyendodary/DBCAS/pull/65), [configuration](../../backend/app/config.py).

## D05 | 2026-11-20 | Writable execution guard

Decision: staging/production reject writable mode unless `SANDBOX_MODE=ephemeral`; shared writable is development-only.
Reason: avoid shared writable execution in release environments; consequence: the broker decision gates future writable work.
Evidence: [#65](https://github.com/nguyendodary/DBCAS/pull/65), [#66](https://github.com/nguyendodary/DBCAS/issues/66), [configuration](../../backend/app/config.py).

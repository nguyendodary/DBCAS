# Legacy IDX Essay resolution — 2026-10-15

## Decision and dependency audit

Essay ID 5 remains the historical item: "Explain why indexes speed up reads
but slow down writes.", IDX, difficulty 3, maximum 5 points, version 1.
Its original rubric remains Missing 0, Partial 1–3, Complete 4–5, with the
original criteria. No four-band conversion or legacy grader exception exists.

Before changing its lifecycle, the development database audit found:

| Reference | Finding |
| --- | --- |
| Published assessment | ID 2, PostgreSQL Foundations, targets IDX/JOIN/SELECT |
| Draft assessment targeting IDX | None |
| Sessions for assessment 2 | Six finalized; four completed, two timed out; none active |
| Attempts containing ID 5 | IDs 5 and 14, sessions 2 and 5; both have three-band snapshots |
| Historical score | Attempt 5 scored 2; attempt 14 was unsubmitted |
| Selection logs | Two |
| Concept mapping | One confirmed IDX mapping |
| Candidate/family descendants | None |
| Reproducible source | Core pack key `legacy-essay-index-read-write` |

Assessments select dynamically through concepts; there is no fixed question
roster to rewrite. The current candidate validator already excludes ID 5
because its rubric is incompatible with current grading. Retirement removes
no usable candidate. Assessment 2's requested two Essay slots were already
undersupplied, and its older eight-question configuration remains unchanged.
The successor supplies one compatible IDX Essay; it does not resolve that
separate published configuration issue.

## Successor and import

Core pack 1.3 adds the distinct `essay-index-workload-tradeoff` item. It was
assigned development question ID **450**, confirmed IDX, difficulty 3,
maximum 5 points. Its original EN/VI content assesses selective B-tree reads,
INSERT/UPDATE maintenance, and when an index is not worthwhile. Its four
canonical bands use 0–1.24, 1.25–2.49, 2.50–3.74, and 3.75–5. These are the
new item's criteria, not a reinterpretation of historical scores.

The importer checks exact canonical content, creates and validates the
successor before retiring the existing legacy item, and matches retired
records on repeat imports. Ambiguous prompts or conflicting content stop
the import. It does not write attempts, scores, or session snapshots.

Disposable import and history regressions ran before the development upgrade.
Migration 007 then applied additively. The core import and its repeat passed:
27 core questions, 27 current Vietnamese translations, no duplicate successor.
The development bank contains 442 rows: 441 validated and one retired;
326 MCQ, 67 SQL, 49 Essay (48 active). PostgreSQL contributes 415 rows and
core contributes 27. The complete checked-in source has 442 VI translations.

The combined development import stopped safely at a separate pre-existing
conflict: PostgreSQL `pg-m089`, question ID 119, has an older correct-option
text and explanation than the checked-in correction from commit `988c2b1`.
The live row says jsonb_path_ops indexes only containment queries; the source
also names its jsonpath operators. This task does not change that question's
semantics. Earlier rows committed by the importer remain valid; development
currently has 115 translation rows, including all 27 core rows. Full-bank
deployment needs separate review of ID 119; fresh disposable imports use the
checked-in source and pass with all 442 translations.

## Historical integrity

Before/after SQL hashes are identical:

| Protected records | Count | MD5 of ordered serialized data |
| --- | --- | --- |
| All attempt rows | 96 | `699bc1e1d2f9f39055f32a7b1de4353a` |
| Full ID 5 attempt rows | 2 | `06c23973512d32b5508ed8618ff6cb9c` |
| ID 5 snapshot/score/grading detail | 2 | `c9bc5638d9c7efc19a0ab541399f8ca6` |
| Assessment 2 session configuration snapshots | 6 | `195ad82712b059e4c608297a55fbff6f` |
| Published assessment 2 row | 1 | `b29054270a52cba8f7f4c94fa7c11356` |

The evidence API now exposes saved rubric bands, and the learner history
renders those bands alongside the original score without regrading. Old
English-only snapshots remain English; new localized snapshots retain their
session locale. Admin shows the retired state and historical three-band
rubric badge, while the successor behaves like an ordinary validated item.
The evidence service was also exercised against actual finalized sessions
2 and 5: it returned the original prompt and three bands, score 2.00 and
unsubmitted/null respectively, with no dirty/new/deleted ORM records and a
rolled-back read transaction. An initial READ ONLY transaction probe was
rejected because the existing session guard uses SELECT FOR UPDATE; no data
was changed, and the normal guarded read then succeeded.

## Verification

All automated database/browser checks use disposable containers; the normal
database was inspected separately, upgraded additively, and imported only
through the versioned importer. Automated Essay provider calls are mocked.

| Gate | Result |
| --- | --- |
| Backend, local Python 3.14.5 | 829 passed, 0 failed, 0 skipped; one Starlette deprecation warning |
| Frontend | 178 passed in 24 files |
| Fresh import, repeat import, legacy history/selection focused checks | 4 passed |
| Migration matrix | Fresh/pre-OAuth/post-OAuth/current upgrades and repeat/schema checks passed in full backend suite |
| Question localization/integrity | 442/442, exit 0; zero missing, duplicate keys or English-prose flags |
| SQL references | 67 questions / 134 fixtures passed against the actual sandbox |
| Essay contract | All 48 active essays pass; retired three-band item preserved separately |
| Chromium | 24 unique cases passed: initial 22 pass/2 fail, corrected admin-route assertions then 2/2 pass |
| Firefox | 24/24 passed, no retries or skips |
| WebKit | 24/24 passed, no retries or skips |
| UI i18n | 819 EN / 819 VI keys, exact parity |
| Production build | Passed |
| npm audit | Zero vulnerabilities |
| pip check | No broken requirements |
| pip-audit | No known vulnerabilities in installed environment |
| docker compose config | Passed |
| git diff --check | Passed |

The first full backend run had 828 passes and one obsolete core-count
assertion (23 versus 24). After updating it, its isolated regression and the
entire 829-test suite passed. The initial Chromium failures were both new
tests expecting `/dashboard` after admin login; the existing admin destination
is `/admin`. No application routing change or flaky retry was used.

Docker initially became unavailable when its WSL instance shut down. A
temporary hidden WSL keepalive and the documented private-interface test
override restored disposable-container verification without owner environment
file edits or system configuration changes. Browser runs also report the
existing NO_COLOR/FORCE_COLOR warning and slow-file notices.

Separate follow-ups remain: review the ID 119 source conflict before full
development-bank localization deployment, and review assessment 2's existing
configuration/Essay coverage shortage. Neither was changed to force this
legacy resolution through. No historical scoring semantics changed.

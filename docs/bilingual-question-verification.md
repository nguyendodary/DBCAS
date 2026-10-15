# Bilingual question completion verification

Verification date: 2026-10-15. Branch: `develop2`. No push or development
database mutation was performed. All write tests used disposable databases.

## Recovery and review boundary

The four missing source records were recovered from existing validated
development database questions 2–5 after repository/history searches found no
recoverable definitions. Eighteen existing attempt snapshots corroborated the
records. See [recovery evidence and rubric repair](core-question-recovery.md).

The original three-band index Essay rubric is preserved in commit `6233e7c`.
Its separately prepared repair retains Partial at 1–3 and Complete at 4–5,
renames the lowest band to Incomplete (0–0.99), and defines Mostly Complete at
3.01–3.99. This semantic change is explicitly presented for owner review.
The guarded import option is disabled by default and has not been run against
the development database. It preserves question IDs and historical snapshots.

## Bank and localization

| Scope | Logical questions | EN | VI | Missing |
| --- | ---: | ---: | ---: | ---: |
| MCQ | 326 | 326 | 326 | 0 |
| SQL | 67 | 67 | 67 | 0 |
| Essay | 48 | 48 | 48 | 0 |
| PostgreSQL | 415 | 415 | 415 | 0 |
| Core | 26 | 26 | 26 | 0 |
| Total | 441 | 441 | 441 | 0 |

Fresh imports run twice leave 441 questions and 441 Vietnamese translation
rows, all current. There are no duplicate logical questions or translations.
All 437 canonical question definitions present at the starting commit remain
identical. The four recovered translations were manually checked for meaning,
natural Vietnamese and answer integrity. Technical options and identifiers
such as SELECT, WHERE, JOIN, customers, name and B-tree remain intact.

The VI manifest contains 2,532 human-facing strings. The localization validator
reports zero English-prose flags, missing translations, duplicate keys or
integrity errors. MCQ option labels/counts and correct-answer identities are
preserved. All 67 SQL questions pass 134 regular/edge fixture executions.

## Migration, grading and historical evidence

The migration matrix covers fresh, pre-OAuth, post-OAuth and current schemas.
Migrations 001–007 apply and rerun safely; schema shape and immutable session
locale checks pass. Column parity is compared by name because additive ALTER
TABLE operations append columns. The project supports transactional forward
migrations, not down-migration scripts.
Direct catalog inspection also confirms both translation indexes are valid,
the primary/foreign-key and JSON/locale constraints are validated, and the
session-locale immutability trigger is enabled.

All 48 source Essay rubrics satisfy the existing four-band contract. The
grader consumes canonical English rubric text and retains canonical band
identifiers. Vietnamese feedback instructions and presentation are tested
with mocks; no live provider call is made.

Six API flows cover EN/VI across MCQ, SQL and Essay. UI language changes do not
change the session locale, question ID, saved draft or deadline. New snapshots
retain localized display content. English-only historical snapshots remain
readable and unchanged. The explicit legacy repair refuses attempts without
rubric snapshots, increments the current question version once, and preserves
all existing evidence. A final read-only development check still found 441
questions, recovered records at version 1, three legacy Essay bands and all
18 historical snapshots.

## Verification results

| Gate | Result |
| --- | --- |
| Backend, Python 3.13.16 | PASS: 830, FAIL: 0, SKIP: 0; one Starlette deprecation warning |
| Frontend | PASS: 176 tests in 24 files |
| Migration/sandbox-safety/Essay subset | PASS: 149 tests (included in full suite) |
| Localization validator | PASS: 441/441, exit 0 |
| PostgreSQL pack structural check | PASS: 415/415 |
| SQL references | PASS: 67 questions / 134 fixtures |
| Essay rubric validator | PASS: 48/48 |
| Chromium | PASS: all 22 unique tests (10 localization + 12 release/content after fixture repair); final evidence recheck 2/2 |
| Firefox | PASS: 22/22; final evidence recheck 2/2; no retries or skips |
| WebKit | PASS: 22/22; final evidence recheck 2/2; no retries or skips |
| UI i18n parity | PASS: 817 EN / 817 VI |
| Production build | PASS |
| npm audit | PASS: 0 vulnerabilities |
| pip check | PASS, including the Python 3.13 test environment |
| pip-audit | PASS: no known vulnerabilities in the Python 3.13 environment |
| docker compose config | PASS |
| git diff --check | PASS |

Docker verification runs inside WSL because Windows could not reliably reach
the WSL daemon/test-container ports. The browser harness accepts
`DBCAS_TEST_PYTHON` for an isolated interpreter without changing owner `.env`
files. Linux native Node bindings and matching browser binaries were installed
locally; dependency manifests were not changed.

Initial failures exposed the historical rubric, outdated bilingual fixtures,
a column-order comparison, and a protected-operator test boundary. These were
fixed without changing the other question definitions or weakening graders.
An initial Chromium admin locator matched both language inputs; the fixture
now uses explicit EN/VI labels and verifies one row after an edit.
That initial run had 15 passes, one failure and six tests not run; the focused
release/content rerun passed all 12 tests. The final two-language history
rechecks passed on every browser, including rendered Essay explanation,
feedback and rubric labels. No flaky retry was used.

The final Chromium and Firefox rechecks emitted two and four maintenance
`OperationalError` log messages, respectively, after their tests completed.
The test cleanup removes owned containers while the API maintenance thread
can still be stopping. These teardown messages did not fail any test; they
remain a test-harness cleanup-order warning. Browser suites also emit slow-file
notices. The Starlette `httpx` deprecation warning remains unchanged.

## Owner review and remaining issues

- P0/P1: no unresolved translation, integrity or verification blocker.
- P2: review the separate rubric repair before deploying migration 007 and
  importing into the existing development database with the explicit repair
  option. This deployment was not performed during verification.
- P3: Starlette deprecation and browser teardown maintenance-log warnings.

The existing localization commits were preserved. Recovery, rubric repair,
guarded upgrade and verification changes are separate local commits. No push
was performed.

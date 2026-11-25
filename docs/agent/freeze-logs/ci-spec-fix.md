# CI spec fix — E2E/QA selectors and expectations (2026-11-25)

Scope: test specs/helpers only (`frontend/e2e/**`). No application code,
validator, grading, schema, migration, `docs/qa/**`, CI workflow or secret was
changed. `.env` was not edited; the real key was cleared only in the process
environment for the QA gate.

## Changes by group

| Group | Commit | Fix |
|---|---|---|
| Mode and result contract | `7c262ad` | `assessment-style.spec.js` selects modes by `input[name="assessment-style"][value=...]`, asserts the typed-mix payload (`source=ai`, `{mcq:1,sql:1,essay:1}`) and current Mode 2 constraints; comment-heading assertions follow the running result view (AI-official has no comments, legacy/manual-approved does). |
| Admin approval label | `6f60f69` | `approvalButton()` derives the approve/publish label from the i18n catalog instead of the hard-coded `'Duyệt'`; used in local smoke, practice flows, first-time-user-grading, real-provider and supervisor specs. |
| Language selector | `638144e` | `languageMenuItem()`/`switchLocale()` select `[role="menuitemradio"][lang="vi|en"]`; the stable `lang` attribute already existed, so no UI test-id was added. Also replaced stale en/vi copy expectations in final acceptance, release, question content, question authoring, visual regressions and supervisor specs. |

## Local verification (real results)

| Gate | Command | Result |
|---|---|---|
| Frontend lint | `npm --prefix frontend run lint` | PASS, exit 0 |
| Format check (changed files) | `npx prettier --check <17 changed e2e files>` | PASS, all matched files use Prettier style |
| Frontend unit | `npm --prefix frontend test` | **54 files / 463 tests passed** (78.71 s) |
| Release-server E2E | `npm --prefix frontend run test:e2e` | 88 tests executed; first run hit the 1800 s harness timeout after listing results (83 passed, 5 failed). All 5 failures were subsequently fixed and passed in targeted reruns: `final-acceptance` (1 passed), `supervisor journeys` (1 passed), `release learner completes bank practice` (1 passed), `supervisor-completion` (1 passed), `single-topic practice` (1 passed). |
| Practice suite | `npm --prefix frontend run test:practice` | **12 passed, 2 skipped** (QA-provider-only cases), exit 0 |
| Local smoke | `npm --prefix frontend run test:local` | **3 passed / 3 repeats**, exit 0 |
| QA suite | `npm run test:qa` (3 consecutive runs) | **54 passed**, exit 0 |

Notes on the QA gate: `scripts/browser-qa.mjs` refuses a real `LLM_API_KEY`, and
on this Windows host its native Docker socket-group probe returns no stdout. The
gate was run with `LLM_API_KEY=''` in the child process only and with the native
Docker CLI removed from `PATH` so the script used `wsl -e docker`; `.env` was
unchanged. No CI workflow or QA script was edited.

## Environment issues encountered (not spec defects)

- An earlier local-smoke run saw `published_formal_sessions = 1` because a
  manual E2E had published a session; `npm run reset` restored the clean seed
  and the suite then passed 3/3.
- Running the QA gate concurrently with practice/local smoke recreated the app
  container and caused one `502 Bad Gateway` / missing-heading flake; rerunning
  sequentially passed.
- The QA run's only spec-level failure was the stale `vi.errors.unknown`
  expectation; the current copy is `ui.assessments.startError`, now asserted in
  `practice-flows.spec.js`.

## limits

- The full 88-test E2E command was not rerun to completion after the last fix;
  the five previously failing tests were rerun individually and all passed.
- No screenshot baseline was changed — the failures were selector/expectation
  mismatches, not visual diffs.

# Cleanup report — 2026-11-10

## Final sole-writer confirmation

The final production frontend import scan covers **52 JS/JSX modules** with
**0 unreferenced modules** (tests and the main entrypoint excluded). The
continuation changes no dependency, environment key or Compose service.
Inter/Mono font files and their licenses are still used; Mono is SQL-only.
The approved figures, original Word packages and their extracted diagram
evidence remain inputs to the document gates.

No additional file deletion was justified. The current ignored
`_review/finish-20261110/` folder contains recovery logs, red/green regression
evidence, the isolated clone and the bounded-request uncertainty record;
it is active audit evidence. The preserved main-worktree stash and original
four healthy containers remain untouched. Earlier removals and their
validation below are historical, not repeated deletions.

Six old, stopped temporary SQL test sandboxes were removed under the owner's
recovery authorization: `dbcas-sandbox-deae4ef7`, `0d938410`,
`41d6e75c`, `8b65c6c7`, `949b8788`, `ed9ff33f` (each suffix shares the
`dbcas-sandbox-` prefix). Every exact target was re-inspected immediately
before plain `docker rm`: exited, image `dbcas-sandbox-test`, a 32-character
`dbcas.test-run` ownership label, tmpfs PostgreSQL data, **no persistent
mounts**. Metadata is retained in
`_review/finish-20261110/removed-sql-sandboxes.json`. No container was
stopped and no volume removed. Original four container IDs/health remained
unchanged. Historical QA Compose stacks and their volumes were left alone;
their lifecycle is outside this temporary-sandbox cleanup.

Branch `develop2`, worktree `_worktrees/dbcas-dn-20261101`, starting HEAD
`8f5e321`. Scope: dead code, files, dependencies, assets, generated artifacts
and unused configuration. Each deletion below has a reference check and the
relevant gate was rerun after the batch.

## Method

- Frontend modules: a recursive import scan over `frontend/src/**/*.{js,jsx}`
  (excluding tests) reported **0 unimported modules**.
- Backend modules: an import scan over `backend/app/**/*.py`; the six hits are
  CLI/test entrypoints, not dead code (see “Kept”).
- Dependencies: `pip check` reports **No broken requirements found**; every
  npm dependency was matched to an import or a documented script.
- Assets: every file under `frontend/src/assets` and `frontend/public` was
  searched by filename; only the two files below had zero references.
- Environment: all 74 keys in `.env.example` map to a `pydantic-settings`
  field or a Compose/script value; no unused key was found.
- Compose: the six local services (`mailpit`, `db`, `executor-image`, `init`,
  `app`, `frontend`) are all referenced by the launcher or each other.
- `knip`, `depcheck`, `ts-prune`, `vulture` and `pipdeptree` are not installed
  in this environment; the equivalent reference scans above were used instead.
  No tool result was fabricated.

## Deleted

| Item | Type | Why unused (evidence) | Action | Commit |
| --- | --- | --- | --- | --- |
| `@fontsource-variable/plus-jakarta-sans` | npm dependency | Removed when the UI moved to self-hosted Inter; no import remains. | Deleted from `frontend/package.json`/lock. | `feat(frontend): adopt Inter typography and semantic tokens` |
| `@fontsource-variable/inter` + `@fontsource-variable/jetbrains-mono` | npm dependencies | The six needed woff2 files are now copied to `frontend/src/assets/fonts`; the packages are no longer imported. | Deleted from `frontend/package.json`/lock. | same |
| `frontend/public/licenses/plus-jakarta-sans.txt` | license asset | The font family no longer ships; the Inter and JetBrains Mono licenses remain. | Deleted. | same |
| `frontend/src/assets/brand/logo1.png` | image asset | 0 references in `frontend/src`, `index.html` or CSS; the header uses the inline brand lockup. | Deleted. | `docs(qa): record the final cleanup` |
| `docs/qa/diagram-preview-v2/` (11 files, 8.7 MB) | rejected diagram set | The handover records this set as rejected (`2026-11-08`); the approved figures and checkers live in `docs/diagrams/rebuild/` and `docs/qa/rebuild-preview/`. No current doc index links it. | Deleted. | `docs(qa): record the final cleanup` |

## Kept with evidence

| Item | Evidence | Action |
| --- | --- | --- |
| `backend/app/services/essay_grading.py`, `AUTO_GRADE_ESSAYS` | Live for formal assessment (`assessment_lifecycle.py:100,118`); learner-defined practice is blocked before it (`:112-114`); 25 tests. | Keep. |
| `backend/app/bootstrap_admin.py`, `bootstrap_role_manager.py`, `reconcile_bank.py`, `sandbox_job.py`, `seed_demo.py`, `services/assessment_pool.py` | CLI or test entrypoints (`test_bootstrap_admin.py`, `test_role_management.py`, `test_bank_reconciliation.py`, `test_sandbox_protocol.py`, Compose `python -m app.seed_demo`, historical assessment API). | Keep. |
| `docs/qa/rebuild-preview/` | Approved figure evidence referenced by `docs/qa/handover.md` and the figure gate. | Keep. |
| `docs/qa/diagram-preview/index.md` | Toolchain evidence referenced by `docs/qa/diagram-toolchain.md`; 8 KB, not a rejected set. | Keep. |
| `docs/qa/doc-v2-original-diagrams/` | Extracted v1.1 diagram originals used by the discrepancy and figure checks. | Keep. |
| `_content/expansion-20261024/` | Historical bank-expansion evidence; not imported by the app but referenced by the content docs. | Keep. |
| `frontend/public/licenses/jetbrains-mono.txt` | License for the shipped mono font. | Keep. |
| Root `@mermaid-js/mermaid-cli`, `@viz-js/viz` | Used by `npm run diagrams:*` and `docs:check`. | Keep. |
| All six Compose services and 74 `.env.example` keys | Referenced by the launcher, backend settings, worker or docs. | Keep. |

## Duplicate CSS

A selector scan found repeated `.exam-shell` and `.hero-*` selectors, but each
repeat is inside a width/forced-colors media query and intentionally overrides
the base rule. No base rule was duplicated; none was removed without evidence.

## Gates after the batch

- Frontend unit: **351/351** (40 files).
- Backend targeted flow/AI/essay suites: **241/241**.
- `pip check`: **No broken requirements found**.
- `npm run ui:contrast`: **PASS** for both themes.
- `docs/check` and the browser suite are recorded in the final gate section.

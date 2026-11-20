# Working in DBCAS

DBCAS is a PostgreSQL practice and assessment application ([README](README.md)).
Its stack is FastAPI, PostgreSQL 17, React and Vite ([README](README.md)).
Work targets `develop2`; `main` is the release branch ([CONTRIBUTING](CONTRIBUTING.md)).

## Read first

Read [CONTRIBUTING.md](CONTRIBUTING.md) before doing anything, including its Commit Attribution Policy.
Then read [STATUS](docs/agent/STATUS.md), [BACKLOG](docs/agent/BACKLOG.md),
and, when needed, [DECISIONS](docs/agent/DECISIONS.md) and [RUNBOOK](docs/agent/RUNBOOK.md).

## Mandatory rules

- Do not change `main`, force-push, rebase shared branches, bypass protection, or deploy to production.
- Use at most three worktrees including the main checkout. Branch from the latest `origin/develop2`; target PRs to `develop2`.
- Do not merge without owner permission. Never delete a worktree with unsaved work.
- Do not touch `docs/qa/**`, v1/v2 data, or migrations without owner approval.
- Update STATUS and BACKLOG in the **same PR** when project state changes.
- Every test-result claim must cite its log and commit. Do not copy CI state into these files.
- No blind CI retries: save evidence first; at most one deliberate rerun only for a proven infrastructure timeout.

## Before every commit

1. Re-read [CONTRIBUTING.md](CONTRIBUTING.md), especially the Commit Attribution Policy.
2. Run `git diff --cached` and review the staged diff and the full commit message.
3. Confirm author and committer are team members, never bots, and no AI/tool credit trailer is present.

Never add AI or bot `Co-Authored-By:`, `Generated with ...`, `Generated-by:`,
`Generated-By:`, `AI-generated-by:`, `AI-assisted-by:`, or `Assisted-by:`
trailers pointing to tools, or credit/branding for Devin, ChatGPT, Claude, OpenAI,
Cursor, Copilot, or similar. Do not alter author/committer timestamps or add promotions.
The `.githooks/commit-msg` hook rejects these trailers; if hooks are not active, run
`git config core.hooksPath .githooks`. The policy applies either way.

## Commands

Use the build, test, E2E and seed procedures in [RUNBOOK](docs/agent/RUNBOOK.md),
derived from [backend/manage.py](backend/manage.py), [package.json](package.json)
and [frontend/package.json](frontend/package.json).

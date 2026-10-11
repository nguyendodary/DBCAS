# AGENTS.md — rules for coding agents working in DBCAS

Read `CONTRIBUTING.md` before doing anything. Commit policy lives there.

## Before every `git commit` (mandatory)

1. Read `CONTRIBUTING.md`, re-read the **Commit Attribution Policy**.
2. Run `git diff --cached` and review the staged diff.
3. Inspect the full commit message.
4. Confirm it contains no AI/tool credit trailer.
5. Confirm author/committer identity is a team member — never a bot.

Never add, under any circumstances:

- `Co-Authored-By:` for an AI assistant, coding agent, or bot
- `Generated with ...`
- `Generated-by:` / `Generated-By:`
- `AI-generated-by:` / `AI-assisted-by:` / `Assisted-by:` pointing at a tool
- Credit or branding for Devin, ChatGPT, Claude, OpenAI, Cursor, Copilot, or similar

Do not modify author/committer timestamps. Do not add tool promotional text.

A `commit-msg` hook in `.githooks/` rejects these trailers. If hooks are
not active, run `git config core.hooksPath .githooks` — the policy still
applies with or without the hook.

# DBCAS release notes — Architecture Freeze v1.1

- Release: `arch-freeze-v1.1`
- Commit: `696cdf9daee6e1d92678dda089ca22290fae55f9`
- Date: 2026-11-25
- Previous freeze: `arch-freeze-v1` at `38f8e06909790bef5530d423da8e86731ef2ea12`
- Branch: `develop2` (release preparation only; `main` unchanged)
- Status: demo/submission candidate, **production HOLD**

## Frozen feature set

| Area | Behaviour |
|---|---|
| Practice mode 1 | Reviewed question bank, FIXED paper, one concept and one difficulty band, MCQ/SQL/essay mix; single-type caps 50/5/10, mixed caps 20/2/3 (total 25). |
| Practice mode 2 | AI adaptive generation, one concept/band, one next question at a time; correct +1 level, wrong −1 level inside the band; prefetch for both outcomes; timeout/error/no key falls back to the reviewed bank. |
| AI provenance | Every served AI question is snapshotted on the attempt with `source=ai_generated`, labelled **AI** in the UI, and queued in `question_candidate` for admin validate/approve/reject. |
| SQL sandbox | Default read-only SELECT, no network, statement timeout, row/byte limits and a disposable container. The optional `writable` demo profile enables DML/DDL and always rolls back. |
| DML grading | Learner answer and trusted reference run on the same dataset; the final table state is compared with stable row ordering. SELECT grading is unchanged. |
| Results | FIXED TEST publishes the AI-official V1 at finish; LEGACY/practice uses AI pre-grading followed by human review. Result versions are immutable; score edits require an audit reason. |
| i18n | English and Vietnamese UI copy with identical key sets; technical identifiers are preserved. |
| Free/Pro | UI-only demo simulation, plan stored in `localStorage`; Free opens mode 1 with a 5-session/day notice, Pro opens mode 2. No payment API or migration. |
| Auth | JWT access plus rotating refresh tokens, bcrypt, RBAC, optional Google/GitHub OAuth and password-reset mail through Mailpit. |
| Documents | Nginx accepts 30 MB bodies; the backend accepts a 20 MB binary upload. |

## Architecture

FastAPI modular monolith (router → service → repository → SQLAlchemy), PostgreSQL 17
via Docker Compose, React/Vite SPA behind Nginx, and SQL execution in disposable
containers. No new service, database, queue technology or framework was introduced
for v1.1.

## Changes from v1 to v1.1

- **One generic LLM provider.** `OPENROUTER_*` settings and OpenRouter-only wire
  parameters/headers were removed. A single `LLM_API_KEY`, `LLM_BASE_URL` and
  `LLM_MODEL` block now selects any OpenAI-compatible Chat Completions provider
  (Mistral, OpenAI, OpenRouter, Gemini, Groq, ...). `LLM_PROVIDER` is optional and
  case-insensitive; unknown values are accepted as `openai_compatible` with a
  warning. Optional fields rejected with 400/422 are retried once without them.
  `npm run llm:check` checks `GET /models` and one minimal JSON completion without
  printing the key.
- **Prompt contract fix.** The mode 2 prompt now derives a complete JSON example
  from `GeneratedQuestion.model_json_schema()`, names the required `prompt` field,
  forbids extra keys, states the output language and uses a versioned official
  PostgreSQL documentation URL. Direct trials improved from **0/15 to 13/15**
  `validate_generated`; the two remaining cases are malformed `RETURNING` clauses
  correctly rejected by the unchanged validator.
- **Deterministic DML rotation.** SQL turns rotate **INSERT → UPDATE → DELETE**
  from the number of served SQL DML questions. A wrong DML verb is rejected with
  `dml_kind_mismatch` and uses the reviewed-bank fallback. The validator, grading
  and schema are unchanged.
- **Windows Docker exec fix.** The Windows launcher prefers WSL Docker when the
  native shim cannot stream `docker exec`; the in-container writable job declares
  `sandbox_mode=ephemeral`. A real UPDATE and DELETE each graded 5.00/5.00 with
  the table state captured before rollback.
- **Grade visibility regression test.** A controlled E2E with known answer keys
  showed ability 1→2 (correct), 2→1 (wrong), 1→2 (correct) and persisted scores
  `[1.00, 0.00, 1.00]`. The null `is_correct` in submit responses is the
  HUMAN_VERIFIED release policy, not a grading failure.
- **Final verification.** Backend 1940 passed / 7 skipped, frontend 54 files /
  463 tests, docs gate 48 assertions (106 API paths / 118 operations), OpenAPI,
  environment inventory, route inventory, secret scan and the real-stack manual
  flow are recorded in `docs/agent/freeze-logs/final-gates.md`.

## Verification summary

| Gate | Result |
|---|---|
| Backend lint | PASS (`ruff`) |
| Backend tests | 1940 passed, 7 skipped |
| Frontend lint | PASS (ESLint, `--max-warnings=0`) |
| Frontend unit tests | 54 files / 463 tests passed |
| Docs gate | PASS — 48 assertions; 106 API paths / 118 operations |
| OpenAPI contract | Matches the runtime contract |
| Environment inventory | 104 backend and 3 frontend keys documented |
| Route inventory | PASS after regenerating `docs/inventory/api-routes.json` |
| Secret scan | 2969 files, 0 findings (tree); history scan 0 real keys |
| `npm run llm:check` | PASS — provider reachable, JSON valid, key never printed |
| Manual stack | Login, Pro demo, mode 2, submit, admin approve/reject, vi/en switch, key-off fallback PASS |
| AI E2E | 8/8 AI questions in both `vi` and `en`; 16 candidates queued; 1 approved, 1 rejected |
| AI-generated DML | 14/14 served SQL items AI-generated with the correct verb; correct answers 1.00, wrong answers 0.00; every reference `rolled_back: true` |

## Upgrade notes

1. Replace any `OPENROUTER_*` block in `.env` with the single `LLM_*` block from
   `.env.example`. A missing key disables AI gracefully; the reviewed bank and
   deterministic templates remain available.
2. Migration **019** moves every `published` assessment to `closed` so practice
   uses the new session flow. It deletes no rows, sessions, submissions, scores or
   snapshots and is safe to re-run. Back up a populated database with `pg_dump`
   before applying it; see `docs/setup-and-migrations.md`.
3. The default passwords `change_me`, `Demo12345!` and `Admin123!` are **demo
   local only**. Staging and production reject them, including on disabled
   accounts. Change them before moving a demo database to a deployed environment.
4. `npm start` creates `.env` with random JWT/database secrets in a fresh clone.
   Never commit `.env`; run `npm run secrets:scan` before sharing changes.

## Known limits

- **Production is HOLD.** This is a local/demo release, not a production
  deployment; no cloud rollout is included.
- **SQL DML needs the disposable writable executor**, which on this Windows host
  requires WSL2 plus Docker. SELECT and the rest of the demo run with ordinary
  Docker Desktop.
- **Per-session token usage and monetary cost are N/A.** The application API does
  not expose provider `usage` per served question and the configured free model
  has no reliable published price; zero is not assumed.
- **OAuth was not verified against real Google/GitHub providers.** The buttons,
  callback handling and fake-provider paths are covered; real consent screens and
  provider credentials remain owner-supplied.
- **The overall validation rate was not re-measured.** The 13/15 figure is the
  direct 5-type × 3-repetition trial after the prompt fix; served E2E items were
  8/8 per locale, not a new population estimate.
- Broker/#66 (`docker.sock` in the API) and writable broker execution remain
  future work; `SANDBOX_BROKER` stays OFF. #71 (`sandbox_busy`) and #94
  (result-heading timeout) remain **UNKNOWN — owner must confirm**.
- SQL-run rate limiting is not implemented; per-execution limits and two-slot
  admission are the guard.
- Free/Pro is UI-only; there is no backend payment route, migration or charge.
- Cold seed takes about three minutes; no safe in-seed parallelism was found.

## References

- [Architecture freeze record](ARCHITECTURE_FREEZE.md)
- [Final gate log](agent/freeze-logs/final-gates.md)
- [Prompt contract fix](agent/freeze-logs/prompt-contract-fix.md)
- [AI DML verification](agent/freeze-logs/ai-dml-verification.md)
- [LLM provider notes](agent/freeze-logs/llm-provider-notes.md)
- [Demo runbook](demo/README.md)

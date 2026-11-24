# Final gates — Architecture Freeze v1.1 (2026-11-25)

All commands run on the real working tree with Docker available. Results below
are verbatim summaries of the command outputs; no gate was weakened.

## Step 5 — automated gates

| Gate | Command | Result |
|---|---|---|
| Backend lint | `backend\.venv\Scripts\python.exe -m ruff check backend\app backend\tests backend\manage.py` | All checks passed! |
| Backend full test | `.venv\Scripts\python.exe -m pytest -q` (from `backend/`) | 1940 passed, 7 skipped, 1 warning in 1434.00s — [`backend-pytest-final.log`](backend-pytest-final.log) |
| Frontend lint | `npm --prefix frontend run lint` | PASS (ESLint, `--max-warnings=0`) |
| Frontend unit | `npm --prefix frontend test -- --maxWorkers=2` | 54 files / 463 tests passed |
| Docs gate | `backend\.venv\Scripts\python.exe scripts\check_docs.py` | PASS — 48 assertions; 106 API paths / 118 operations |
| OpenAPI contract | `backend\.venv\Scripts\python.exe scripts\export_openapi.py --check` | OpenAPI matches the runtime contract |
| Env inventory | `backend\.venv\Scripts\python.exe scripts\check_environment.py` | 104 backend and 3 frontend keys documented; no values loaded |
| Inventory check | `npm run inventory:check` | OK after regenerating `docs/inventory/api-routes.json` (commit `9dc758c`) |
| LLM provider check | `npm run llm:check` | PASS — provider `openai_compatible`, base `https://api.mistral.ai/v1`, model `deepseek-v4-1-flash-1017`, GET /models HTTP 200 (63 models), chat HTTP 200, JSON hợp lệ: có |

Two gates were red initially, both due to stale/invoked-wrong inputs, not code:

- Backend lint first reported `E902 The system cannot find the file specified
  --> manage.py:1:1` because `manage.py` was passed relative to the repository
  root. Correct invocation from `backend/` passes.
- `inventory:check` first reported `docs/inventory/api-routes.json: does not
  match its sources (changed contents: backend/app/routers/sessions.py)` — only
  source hashes and line numbers had shifted. `npm run inventory:write`
  regenerated it (118 routes unchanged), then `inventory:check` passed.

## Step 4 — security review

| Check | Result |
|---|---|
| `npm run secrets:scan` | `Secret scan: 2968 files; 0 findings; mode=tree.` |
| Git history real-key pattern search (`sk-or-v1-[A-Za-z0-9]{20,}`, `sk-[A-Za-z0-9]{32,}`) | 0 commits matched |
| `.env` tracked? | No — `git check-ignore` → `.gitignore:23:.env` |
| Tracked files containing key material | Only `.env.example` and `deploy/release.env.example` placeholders; scripts that scan secrets; no real key |
| Default passwords | `change_me`, `Demo12345!`, `Admin123!` — documented in README as **demo local only** |
| `.env` final hash | `2FC8D20C1C591559DCA07CCA50607C417EC93342F869B507DFB82D338FC91D26` (unchanged from start) |

No real key was found; no key was printed in any log or commit.

## Step 6 — manual end-to-end on the real stack (`npm start`)

- Learner login → dashboard → Pro demo active → Assessments → Mode 2 with
  concept "DML knowledge" and mix MCQ 4 + SQL 2 + essay 2 → session 41 started
  (8 questions, first shown with the **AI** label).
- All 8 answers submitted (HTTP 200 each); 6 served questions were
  `ai_generated`, 2 fell back to bank under quota pressure. Finished →
  `/evaluations/41` showed `Estimated ability 2.0/5`, ability band Easy,
  8 answers collected, provisional (not official score).
- Language switch: English page showed "Assessment evaluation / Estimated
  ability"; Vietnamese page showed "Đánh giá bài làm / NĂNG LỰC ƯỚC TÍNH" —
  no mixed-language interface text.
- Admin login → `/admin/documents` candidate queue showed 119 items with
  statuses in Vietnamese. Revalidated/approved candidate **117** (HTTP 200,
  `promoted_question_id=4168`) and rejected candidate **120** (HTTP 200,
  `validation_status=rejected`). Final counts: approved 2, rejected 2,
  pending 93, validated 25.
- Key-off trial: `LLM_API_KEY` temporarily emptied (no other config changed),
  API restarted. Session 42 started, served a `bank` MCQ in Vietnamese, submit
  and finish returned HTTP 200 — bank fallback works without an AI key.
  `.env` restored byte-for-byte (hash above) and API restarted.

## Step 2 — tokens and cost

Per-session provider usage is not exposed by the application API → N/A.
Published price for the configured free model is absent → N/A, zero not assumed.
Details in [`ai-dml-verification.md`](ai-dml-verification.md).

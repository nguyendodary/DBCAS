# Final manual E2E — Architecture Freeze v1.1 (2026-11-25)

Real stack at `http://localhost:18080` / API `:18000`, seeded demo data, Windows
+ Docker Desktop 29.8.1 + WSL2. All actions were performed in the browser or
against the running API; no application code, validator, schema, migration,
`docs/qa/**` or `.env` value was changed permanently.

## 0. Environment and provider check

- `npm start` with `LOCAL_DOCKER_GID=988` (Windows native Docker CLI cannot read
  the socket group; WSL probe returned `988`).
- `npm run llm:check`: PASS — provider `openai_compatible` (configured label
  `Mistral` is unknown, accepted with warning), base `https://api.mistral.ai/v1`,
  model `deepseek-v4-1-flash-1017`; `GET /models` HTTP 200 (63 models), chat
  HTTP 200, JSON hợp lệ: có. No key printed.
- `npm run env:check`: PASS (names and syntax only).

## 1. Learner → Pro demo → Mode 2 (session 43)

- UI login `learner@dbcas.local` succeeded; dashboard showed “Gói Pro demo”
  and `localStorage.dbcas_demo_plan = "pro"` — Mode 2 unlocked (UI-only plan).
- `/assessments`: Mode 2 (`ADAPTIVE`), concept **DML knowledge** (16), band
  **Vừa/MEDIUM**, mix **4 MCQ + 2 SQL + 2 essay** (8 questions).
- All 8 answers submitted; session finished with `status=completed`,
  `answered_count=8`, `served_count=8`.
- Served sources: 6 `ai_generated` (all MCQ/essay) and 2 `bank` (both SQL).
  App log reason: `AI practice fallback session=43 seq=2/5 type=sql
  reason=generation_sql_execution detail=empty_or_nondeterministic`. No validator
  or grading change was made to force a pass.
- Result: ability `3/5` (MEDIUM, provisional), score **4.40 / 8.00 (55%)**,
  `review_status=LEGACY`, `result_version=null`. Evaluation page showed the
  provisional result and per-question comments.

## 2. Admin question candidate queue

- `GET /api/v1/admin/question-candidates` returned 124 items (29 validated,
  95 pending) at review time; the admin UI `/admin/documents` was opened to
  inspect the review surface.
- **Approve:** candidate **126** (validated, MCQ) → HTTP 200,
  `promoted_question_id=4175`. The response still reported
  `validation_status=validated`; the promotion id is the authoritative result.
- **Reject:** candidate **125** (pending, MCQ) → HTTP 200,
  `validation_status=rejected` (hidden from the default queue afterwards).
- Post-action groups: 29 validated, 94 pending, rejected hidden from the default
  listing. Generated `content_hash` was used for the explicit review.

## 3. en/vi language switch

- The header selector switched the whole UI chrome: Vietnamese
  “Câu 1 / tối đa 3 · Đã trả lời 0 câu · Dễ / Nộp bài” ↔ English
  “Question 1 of up to 3 · 0 answered · Easy / Finish assessment”.
- No mixed-language UI text was observed. The AI question prompt stayed in its
  generation locale (`vi`) after switching chrome language, which is the
  documented behaviour (content locale is fixed when the item is generated).

## 4. SQL-only session with AI DML (session 45, writable demo profile)

Restarted with `DBCAS_DEMO_PROFILE=writable,free-pro` so DML state grading can
run. Mode 2, concept **DML knowledge** (16), band **Dễ**, mix **0 MCQ + 3 SQL +
0 essay**. All three served questions were `ai_generated` with the deterministic
rotation **INSERT → UPDATE → DELETE**:

| Seq | Question | Learner answer | Score | Grader / status | Datasets |
|---|---|---|---|---|---|
| 1 | 4176 INSERT | `INSERT INTO products (id, name, price) VALUES (3, 'Bút chì', 5000);` (reference from candidate 127) | **1.00** | `sql_semantic` / `correct` | 2/2 passed |
| 2 | 4177 UPDATE | `UPDATE products SET price = price + 10 WHERE 1 = 0;` (deliberately wrong) | **0.00** | `sql_semantic` / `incorrect` | 0/2 passed |
| 3 | 4178 DELETE | `DELETE FROM products WHERE price < 100;` (reference from candidate 129) | **1.00** | `sql_semantic` / `correct` | 2/2 passed |

Session finished `status=completed`, `answered_count=3`, ability `2/5`
(EASY, provisional). Evidence taken from `GET /sessions/45/evidence`.

**Rollback:** each reference was re-executed with the project sandbox helper
(`provision_dataset(setup_sql)` → `execute_writable_script(sql, schema=schema,
capture_tables=["products"])` → `drop_dataset`). All three returned
`success: true`, `rolled_back: true`, `error_type: null`, and captured the
`products` table before rollback.

## 5. Key-off fallback (session 46)

- `.env` SHA-256 before: `2FC8D20C1C591559DCA07CCA50607C417EC93342F869B507DFB82D338FC91D26`.
  A byte-for-byte backup was kept outside the repository.
- Temporarily set `LLM_API_KEY=` only, restarted the stack, and started Mode 2
  (concept 16, EASY, 1 MCQ + 1 SQL + 1 essay). The first served question was
  `source=bank` (“Lệnh nào thay đổi giá trị trong các dòng hiện có mà vẫn giữ
  nguyên định nghĩa bảng?”) — the documented AI-off fallback.
- Session 46 completed with `answered_count=3`, `served_count=3`, `status=completed`.
- `.env` was restored from the backup; hash after equals the hash before
  (MATCH=True). `npm run env:check` PASS after restore; stack restarted with the
  normal key and default demo profile.

## 6. Token usage and cost

- **N/A for these E2E sessions.** The application API does not expose provider
  `usage` per served question and no token count was found in the app console
  logs. The earlier direct prompt-contract trial recorded 13,859 tokens across
  15 calls (`prompt-contract-fix.md`); that figure is not attributable to
  sessions 43–46.
- Monetary cost per session: **N/A** (no reliable published price for the
  configured model); zero is not assumed.

## 7. Notes / not verified

- In session 43 the SQL slots used the reviewed bank because AI SQL generation
  failed the deterministic-execution check. The AI DML evidence therefore comes
  from the dedicated SQL-only session 45, not from session 43.
- OAuth was not exercised against real Google/GitHub providers.
- SQL-run rate limiting is not implemented; per-execution limits and two-slot
  admission remain the guard.
- The legacy result policy leaves `is_correct` null in submit responses and
  practice results provisional; this is release policy, not a grading failure.
- Production remains **HOLD**; nothing was pushed or merged.

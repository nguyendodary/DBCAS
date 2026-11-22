# Free/Pro and cost reporting — design proposal

Status: **design only, no code, no migration, no owner approval**. Date: 2026-11-22.
Sources: `origin/feature/han` (PR [#10](https://github.com/nguyendodary/DBCAS/pull/10), head `9a89cf3`) and
`origin/feature/truong-free-pro-costs` (head `bd95673`). Both branch from `main`, not current `develop2`.

## 1. What the branches implement

### 1.1 `feature/han` / PR #10 — costs UI and report endpoint

- 24 commits, 17 files, **+1.222/−284** vs `main`.
- `frontend/src/pages/admin/AdminCostsPage.jsx` (+386) and `frontend/src/pages/UpgradePage.jsx` (+218);
  nav/route changes in `App.jsx`, `Layout.jsx`, `AssessmentsPage.jsx`.
- `GET /api/v1/admin/financial-report?month=YYYY-MM` in `backend/app/routers/admin.py` (+83); it queries
  `pro_purchase` and `operating_cost`, but #10 has **no** tables/migrations of its own.
- Updates `docs/openapi.json`, route inventories, `docs/academic/README.md`, and
  **`docs/qa/project-facts.json`** (forbidden without owner approval).
- Standalone #10 is incomplete: the page calls a report backed by tables that only exist on the later branch.

### 1.2 `feature/truong-free-pro-costs` — complete prototype

- 25 commits, 32 files, **+1.899/−304** vs `main`; adds 19 files/+868/−211 over #10.
- Subscription: `backend/app/services/subscription_service.py` (+104). `FREE_SESSION_LIMIT=3`,
  `PRO_DURATION=30 days`, Vietnam calendar month (`Asia/Ho_Chi_Minh`), per-account
  `SecurityRepository.lock("plan-session:<id>")`, and `Account.plan` / `pro_expires_at`.
- Demo checkout: `GET /auth/plan`, `GET /auth/pro-demo-offer`, `POST /auth/buy-pro-demo`
  (`DemoCheckoutRequest.request_id: UUID`, `test_token` literal `dbcas-demo-visa-approved`).
  `ProPurchase.checkout_request_id` is unique; repeated requests are idempotent; no card data.
- Costs: `backend/app/services/llm/costs.py` (+52) records one `OperatingCost` row per provider attempt
  (model, task_type, token counts, outcome, http_status, estimated USD). `provider.py`/`service.py` call it.
- Admin report: `GET /admin/financial-report?month=YYYY-MM` (Administrator only) returns VND revenue,
  AI/hosting cost, unpriced-call count and balance; admin account roster adds `plan`.
- Migrations `db/migrations/090_free_pro_costs.sql` and `091_demo_checkout_vnd.sql`; `db/schema.sql` changes.
  `test_free_pro_costs.py` (+232) covers quota, month boundary, checkout idempotency, cost estimates and report.
- Also edits `docs/qa/project-facts.json`, `docs/openapi.json`, inventories, `docs/academic/README.md`,
  `scripts/check_docs.py`, and four E2E specs.

## 2. Fit with current `develop2`

`develop2` has migrations `001`–`028` only. `090/091` do **not** collide numerically today, but they skip
the sequence, and `backend/tests/test_migrations.py:213-232` asserts the exact chain and count `28`
(plus `db/schema.sql`, schema catalog and diagram ledgers). Renumber to **`029_free_pro_costs.sql`** and
**`030_demo_checkout_vnd.sql`**, keep them forward-only/additive, and regenerate every generated inventory.

The branch’s `scripts/check_docs.py` and `docs/qa/project-facts.json` edits must **not** be inherited:
`docs/qa/**` needs owner approval. Rebuild the generated facts from current `develop2` after approval.

## 3. Proposed design (fits `develop2`)

- Keep `Account.plan` (`free|pro`, default `free`) and `pro_expires_at` additive; no v1/v2 data rewrite.
- New tables: `pro_purchase` (simulated demo purchase, unique `checkout_request_id`) and
  `operating_cost` (operational metadata only).
- Flags, all default **OFF**: `FREE_PRO_ENABLED`, `PRO_DEMO_CHECKOUT_ENABLED`,
  `COST_REPORTING_ENABLED`. Existing behavior is unchanged until the owner enables a flag.
- Free quota counts **sessions started** in the Vietnam calendar month, not completed sessions.
  A session started while Pro stays Pro for its lifetime. Pro periods stack from `max(now, expiry)`.
- Demo checkout accepts only a public demo token and a client idempotency UUID; no gateway, no card,
  no charge. Real payment is a separate owner decision.
- Cost rows store no prompt, SQL, essay, answer, email or provider payload. `account_id` is nullable
  and admin reports aggregate by month; retention is owner-defined.
- Admin financial report is read-only; unpriced calls are reported explicitly, never silently zeroed.

## 4. Owner questions and proposed defaults

| # | Question | Proposed default |
|---|---|---|
| 1 | Plan names | `free` and `pro` only |
| 2 | Price / duration | 99.000 VND for 30 days (demo) |
| 3 | Free quota | 3 started sessions per Vietnam calendar month |
| 4 | Payment | Demo only: test token, no card, no real charge; gateway later |
| 5 | Who sees financial reports | `Administrator` only; a Finance role is a later decision |
| 6 | Cost-log retention | 90 days for `operating_cost`; purchases retained 24 months |
| 7 | Free-session definition | Count started practice/assessment sessions; finishing is irrelevant |
| 8 | Pro expiry / stacking | 30-day extension from `max(now, pro_expires_at)`; no refunds in demo |
| 9 | Cost estimate authority | Advisory only; never used for billing or learner grading |
| 10 | Flag default | All three flags **OFF**; enable only in demo/staging by owner |

## 5. Phased plan (small PRs, each independently reversible)

1. **P0 — decisions:** approve this document and the table above; no code.
2. **P1 — schema:** `029/030`, models, `db/schema.sql`, migration-chain tests, generated docs, flags OFF.
3. **P2 — plan read:** `GET /auth/plan` and admin roster `plan` fields behind `FREE_PRO_ENABLED`; tests.
4. **P3 — demo checkout:** `pro-demo-offer`/`buy-pro-demo` behind `PRO_DEMO_CHECKOUT_ENABLED`; idempotency,
   unique request ID, no card data; enable only in demo.
5. **P4 — cost reporting:** cost observer and read-only financial report behind `COST_REPORTING_ENABLED`;
   privacy tests, unpriced-call reporting, retention job.
6. **P5 — UI:** upgrade/costs pages behind the same flags, route inventory/OpenAPI, E2E.
7. **P6 — owner enablement:** demo/staging only after review; production remains **HOLD**.

## 6. Risks

- **Migration/ledger:** wrong numbering, schema.sql drift, `test_migrations.py` count, diagram/schema catalog.
- **Fairness/concurrency:** month boundary and session-start lock; double start or double purchase.
- **Demo integrity:** test token or request-ID reuse could grant Pro repeatedly; unique index + row lock required.
- **Cost accuracy:** token rates, cache hit/miss, peak multiplier and holidays make the USD estimate approximate;
  unpriced calls must stay visible.
- **Privacy:** cost metadata could become learner-identifying if `account_id` or payloads are exposed; aggregate only.
- **Generated docs/QA gate:** `docs/qa/project-facts.json` needs explicit owner approval; do not copy branch edits.
- **Rollback:** flags OFF must restore current behavior; schema stays additive.
- **Product scope:** free quota, price, real payments and report audience are owner decisions, not agent defaults.

See [owner decisions](owner-decisions.md), [QA-1 sandbox busy](qa1-sandbox-busy.md), and
[deployment readiness](../deployment-and-readiness.md). Production stays **HOLD**.

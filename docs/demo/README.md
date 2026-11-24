# DBCAS demo runbook

Status: **DEMO only, synthetic data only, production HOLD.** This is not a
production release and does not enable real payments or real student data.

## Start

```bash
npm start                          # normal demo seed, read-only SQL
DBCAS_DEMO_PROFILE=writable npm start   # demo DDL/DML profile
```

The full demo seed runs on every fresh stack. A faster seed snapshot is **not
available on `develop2`**: PR #89 is skipped by the owner and
`npm run demo:snapshot` does not exist. Re-running `npm start` preserves an
existing seeded volume.

Accounts (local demo only): `admin@dbcas.local` / `Demo12345!`,
`learner@dbcas.local` / `Demo12345!`; additional learners are
`linh@dbcas.local` and `minh@dbcas.local` with the same password.

## 8–10 minute script

1. **0:00–1:00** — Open `http://localhost:18080`, sign in as admin; show the
   cohort dashboard and the seeded synthetic history.
2. **1:00–3:00** — Open `/admin/grading`, review one essay/SQL item, show
   evidence and publish (or use the already-published demo sessions).
3. **3:00–5:00** — Sign in as `learner@dbcas.local`; start a practice
   assessment; answer MCQ + essay; open a different question from the number
   grid and return to the current one.
4. **5:00–7:00** — Open a SQL question. With the writable profile, run
   `CREATE TABLE demo_item(...); INSERT ...; SELECT ...` in one editor run and
   show the result table; explain it is isolated, rolled back and result-graded.
5. **7:00–9:00** — Show history/competency and the evidence page; explain the
   AI wait state and human-verified release.
6. **9:00–10:00** — Close with limits: synthetic data, production HOLD,
   broker/#66 not done, #71 flaky unknown.

## Demo flags

- `DBCAS_DEMO_PROFILE=writable` adds `docker-compose.demo-writable.yml` and sets
  `SANDBOX_WRITABLE=true`, `SANDBOX_MULTI_STATEMENT=true` **for that run only**.
  Defaults stay OFF.
- The startup guard refuses writable SQL outside development/demo without
  `SANDBOX_MODE=ephemeral`. No new `docker.sock` mount is added; the existing
  ephemeral container uses `--network none`, read-only rootfs, dropped caps,
  a TTL and rollback-only transactions.
- `DBCAS_DEMO_PROFILE=free-pro` adds `docker-compose.demo-free-pro.yml` and
  builds the frontend with `VITE_DEMO_FREE_PRO=true`. This is a **UI-only
  simulation**: static sample costs, an in-browser plan badge and a fake
  upgrade button; no backend route, migration, API call, payment or stored
  data. Default is OFF. Combine profiles as `writable,free-pro` if needed.
- Backend Free/Pro design flags (`FREE_PRO_ENABLED`, etc.) are not used; the
  design is in [free-pro-design](../analysis/free-pro-design.md).

## Offline AI fallback (deterministic QA provider)

If the configured compatible provider is unavailable, use the repository's fake provider instead of a
real key. It is `backend/tests/qa_provider.py`, selected through the QA Compose
override. Start the normal stack first so `.env` and the `dbcas-local` project
exist and the seed has completed, then recreate the app with the override:

```bash
npm start
docker compose -p dbcas-local -f docker-compose.local.yml -f docker-compose.qa.yml \
  up -d --build --wait --wait-timeout 600 qa-ai app
```

The app gets `LLM_PROVIDER=compatible`, `LLM_BASE_URL=http://qa-ai:8080/v1` and
`LLM_MODEL=deterministic-local-qa` from that override. The provider makes no
outbound calls and stores no prompts.

`npm run test:qa` automates the same fake-provider path for the practice suite.
It refuses to run while `.env` contains a real `LLM_API_KEY`; clear that key
first. Stop the extra provider with
`docker compose -p dbcas-local -f docker-compose.local.yml -f docker-compose.qa.yml rm -s -f qa-ai`,
or stop the whole stack with `npm run stop`.

The runbook's demo E2E specs also need their host flags when run directly:
`DBCAS_DEMO_WRITABLE=1` and `DBCAS_DEMO_FREE_PRO=1`; the Compose profile itself
does not set them.

## Known limits

- Production is **HOLD**; this build is not the product.
- Broker/#80 is closed for demo scope; `SANDBOX_BROKER` stays OFF. #66
  (existing `docker.sock`) is accepted as a known demo limitation.
- #71 qa-1 `sandbox_busy` remains flaky; cause **UNKNOWN — owner must confirm**.
- #94 `practice-flows` heading “Nhận xét” timeout remains **UNKNOWN — owner must
  confirm**; the discriminating observation is recorded in the issue.
- A seed snapshot (#89) is not in this build; the full seed is used.
- OTP vs reset-link remains an owner decision ([#25](https://github.com/nguyendodary/DBCAS/pull/25)).
- Free/Pro is simulated design only; no real payment and no real charge.
- Never use real student data, real cards or production credentials.

## Rehearsal and tag

Run the full CI three times on the demo-equivalent head and keep the run links
in the PR/checkpoint. The owner decides whether to create a tag; this runbook
must not create or push one. A proposed name is `demo-v1` on the reviewed merge
SHA, or `v1.0-final` after the freeze record is merged.

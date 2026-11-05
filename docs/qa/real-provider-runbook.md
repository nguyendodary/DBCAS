# Opt-in real-provider continuation

Current ledger: `_review/real-provider-20261104/ledger.json`, **70/80 actual
requests,10 remaining** on2026-11-05. This continuation used30 requests. Failed,
uncached, diagnostic and retried wire requests all count; cache rows are not
request counts. Never reset/delete the ledger or silently increase its cap.

**Do not start another full live scenario with the remaining budget.** A full
passing run used16 requests. Current final live runs: run7 passes130.612s;
run8 fails110.990s at the strict no-generation-fallback assertion. The overall
real-provider stability criterion is NOT met. Failed6/8 evidence is retained.

Normal CI and `backend/tests/conftest.py` keep live networking disabled. Fake
practice/browser and budget tests always run. The separate real browser config
skips automatically unless a key exists and `DBCAS_RUN_REAL_PROVIDER=1` is set.
The full scenario performs three attempts of3 questions, automatic and human
release, SQL/reason/audit, cached evaluations and390px. Retries=0 and
stop-on-first-failure; fallback/skipped runs never count as live acceptance.
Real content must pass the unchanged schema/domain/executable SQL gates.

Before any later authorized run, reconcile maximum_total, prior_calls and all
numbered calls. Existing prior_calls is0 and maximum_total is80. Keep key/model
private in local.env/child memory; never print, log, commit or screenshot them.
The client accepts an API base or complete chat endpoint without duplicating
the path (`d4a541c`); no.env rewrite is needed.

The runner refuses missing counts or credentials before starting. It uses only
`dbcas-real-qa` (optional suffix permitted), default ports 18580/18500/18525/11525,
and preserves `.env`. It seeds with AI disabled, then replaces only this local
app with a metered server before enabling credentials. It disables the provider
again after the run, including failures. Do not run an unrelated browser/user
against this dedicated stack while accepting a scenario.

`backend/tests/real_provider_qa.py` instruments the real HTTP transport, keeping
the configured endpoint/model, provider-specific request formatting and cache.
It atomically reserves a slot **before each wire request**, including retries,
and refuses any request beyond the recorded80 total. One app process shares a
thread-safe ledger.
Reservations survive crashes and restarts. Never reset or delete the ledger to
recover budget; reconcile it instead.

Local artifacts:

- `_review/real-provider-20261104/ledger.json`: count, numbered request hashes,
  status/category, latency and whitelisted token/cost usage. No raw key/model,
  authorization headers, prompts or answers.
- `_review/audit-20261105/real-run6-*`, `real-run7-*`, `real-run8-*`: preserved
  separate statuses/arithmetic/synthetic screenshots; traces disabled.
- `docs/qa/final-20261105/gate-results.json`: sanitized measured checkpoint.

Report actual calls, reported tokens/cost (unknown when absent), latency,
failures/fallbacks and human quality review. A skipped or fallback run is not
real-provider acceptance. The helper tests simulate successful/failed HTTP,
timeouts, restart, concurrent reservations and exhaustion without live calls.

The live app is provider-disabled after each run, including failures. Keep the
unmet real-generation criterion visible while collecting independent CI results.

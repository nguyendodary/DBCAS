# Opt-in real-provider continuation

This task already authorizes local live QA within a total of fewer than 60
requests. The outstanding prerequisite is the **previous request count**, not
another permission request. Do not equate cache rows with requests: failed,
uncached and retried requests also consume the budget.

Normal CI and `backend/tests/conftest.py` keep live networking disabled. Fake
practice/browser and budget tests always run. The separate real browser config
skips automatically unless a key exists and `DBCAS_RUN_REAL_PROVIDER=1` is set.
It performs one three-attempt Learner/Admin scenario three consecutive times,
with 3 questions per attempt, retries=0 and stop-on-first-failure. Real content
must pass the application's unchanged schema/domain checks without fallback.

Once the previous count is reconciled, from the repository root:

```powershell
$env:DBCAS_REAL_PRIOR_CALLS = '<verified integer 0–59>'
node scripts/real-provider-qa.mjs
```

The runner refuses missing counts or credentials before starting. It uses only
`dbcas-real-qa` (optional suffix permitted), default ports 18580/18500/18525/11525,
and preserves `.env`. It seeds with AI disabled, then replaces only this local
app with a metered server before enabling credentials. It disables the provider
again after the run, including failures. Do not run an unrelated browser/user
against this dedicated stack while accepting a scenario.

`backend/tests/real_provider_qa.py` instruments the real HTTP transport, keeping
the configured endpoint/model, provider-specific request formatting and cache.
It atomically reserves a slot **before each wire request**, including retries,
and refuses a 60th total request. One app process shares a thread-safe ledger.
Reservations survive crashes and restarts. Never reset or delete the ledger to
recover budget; reconcile it instead.

Local artifacts:

- `_review/real-provider/ledger.json`: previous count; numbered calls; request
  hash; response status or exception type; latency; reported model/provider;
  whitelisted token/cost usage. No authorization headers, prompts or answers.
- `_review/real-provider-browser-results.json`: three-run status and arithmetic.
- `_review/real-provider-browser/`: synthetic UI screenshots; traces disabled.

Report actual calls, reported tokens/cost (unknown when absent), latency,
failures/fallbacks and human quality review. A skipped or fallback run is not
real-provider acceptance. The helper tests simulate successful/failed HTTP,
timeouts, restart, concurrent reservations and exhaustion without live calls.

Current continuation: no real requests sent; previous count still unresolved.

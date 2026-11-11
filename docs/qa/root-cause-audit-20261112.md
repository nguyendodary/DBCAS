# Root-cause audit — OAuth restoration and whole-project checks

Requested report identifier: 20261112. Investigation began 2026-11-11 +0700.
Baseline: clean `develop2` at `60f075a`; sole writer; main/stash preserved.
This is a measured checkpoint; pending gates below are not claimed as passed.

## Missing OAuth controls: investigation in the requested order

1. **Frontend rendering:** `OAuthButtons.jsx` reads `/auth/oauth/providers`;
   no VITE feature flag controls these buttons. `b4313b5cc944b404f60aae9d542f11e0ec3a5ee3`
   (2026-11-02, “UI: simplify local flows and complete assessment question selection”)
   added the configured-only filter and `if (!enabled.length) return null`.
   It also replaced the disable-provider regression with a hide-provider assertion.
   `git log -S 'if (!enabled.length)'` and the commit diff identify the change
   directly; bisect is unnecessary. Metadata loading/failure also hid both controls.
2. **Backend:** the public endpoint correctly lists Google/GitHub with boolean
   availability and no credentials. On the running local demo both are false.
   The endpoint was not deleted; start rejects unconfigured flows with 503.
3. **Environment/Compose:** actual keys are `GOOGLE_CLIENT_ID/SECRET`,
   `GITHUB_CLIENT_ID/SECRET` and each provider's `_REDIRECT_URI`.
   `env_file: .env` already forwards them to app/init. Thus missing explicit
   `environment:` entries did not drop them. Local missing credentials expose the
   frontend guard; neither W7 nor the owner's LLM-key replacement caused that guard.
   Separate defect: OAuth originally defaults to Vite 5173; local Compose sets
   FRONTEND_URL to 18080 but did not align callbacks. Compose now forwards the
   named keys explicitly and derives default callbacks from LOCAL_WEB_PORT.
   The WSL launcher now forwards operator OAuth overrides, as it does LLM ones.
4. **History/CSS/i18n/tests:** `.auth-oauth` uses inline-flex; there is no
   display:none theme rule. Both translations retain continue-provider keys.
   Recent typography/theme/Vietnamese-copy changes did not remove the controls.
   Existing configured-only browser fixtures could not expose the no-key case.
   The incorrect hide assertion is replaced with stronger visible-control,
   configured-link and safe-notice assertions, retaining the other tests.

## Defect register

| Defect | Symptom | Root cause | Fix | Commit | Test |
| --- | --- | --- | --- | --- | --- |
| A01 OAuth discovery | Both auth pages omit Google/GitHub on local demos | `b4313b5` filters on credentials and returns null; regression test was changed to expect hiding | Always show icons + localized short labels; pending reads stay visible; unavailable choices announce an email notice without navigation; provider section + divider precede one email form | OAuth restoration item | Nine new component regressions failed on baseline; affected units 31/31; browser theme/language/width matrix 8/8 (both pages), axe zero violations |
| A02 Local callback mismatch | Configured demo returns toward Vite port 5173 | Initial OAuth defaults from `b4743fc` outlived the local Compose launcher | Compose defaults use web port 18080/LOCAL_WEB_PORT; explicit override and WSL forwarding; empty example keys and README app-registration steps | OAuth restoration item | Real start/state/PKCE tests; localhost fake provider validates exact redirect and client registration |
| A03 OAuth session gap | OAuth sessions cannot rotate and lack email login's family logout revocation | OAuth completion retained its original token-only issuer when `cd4666c` added rotating email sessions | Use shared refresh_tokens.issue after atomic handoff consumption | OAuth restoration item | Both provider refresh/logout tests failed before fix; backend OAuth/payload suites 52/52 after fix; browser renews OAuth sessions |
| A04 Callback configuration validation | A malformed/off-host callback is reported as configured | ProviderSpec.configured only checked nonempty strings | Require fixed provider callback path, same SPA host/scheme, HTTPS except loopback, no credentials/query/fragment; requests never supply redirect_uri | OAuth restoration item | Five invalid-config cases failed before fix and pass after; starts return 503 without Location |

## Evidence and current verification

- [Screenshot index](oauth-20261112/screenshots/README.md): eight running-demo
  before captures and eight changed-UI captures, plus mobile notice; exact CSS
  dimensions and zero overflow are asserted by `node scripts/capture_oauth.mjs`.
  Changed UI is served on 5175 against the real unconfigured API on 18000.
  Before captures document the pre-existing running image; its build revision
  was not stamped, so it is not assumed identical to the source baseline.
- Configured success/error browser fixture uses local HTTP on 8101, production
  backend routes on a disposable PostgreSQL 17 database and browser proxy 5174.
  State cookies/PKCE/token exchange/account linking/handoff/session issuance run
  normally. No real client credential is involved.
- Harness correction: the first attempt routed only the external destination;
  Chromium followed the server redirect before interception, reaching external
  error pages with dummy registrations. The run was stopped. The corrected
  harness intercepts the initial start response (`maxRedirects: 0`), preserves
  cookies and replaces Location with the loopback fake. Corrected run: **7/7**.
- [Secret hygiene](oauth-20261112/secret-hygiene.json): both env files ignored,
  5,403 reachable blobs and current tracked files scanned, zero secret findings.
  Explicitly public default placeholders are classified by key name, never output.
  No environment value was printed. New owner LLM file is in the main checkout;
  the active worktree's env file is older. Old request ledger remains closed.
- Backend lint/build and OAuth/payload **52/52** pass. Frontend
  lint/format/build pass; full unit **364/364 (42 files, 91.38s)** and audit
  **zero vulnerabilities**. Fake OAuth + UI/accessibility repeated three times:
  **48/48, 2.6m**. Launcher **7/7**; route inventory matches. Docs: **46 project
  + 41 Word assertions + 10 figure gates PASS**. Whole-project walkthrough,
  cleanup, final Word and pushed-HEAD CI remain pending.

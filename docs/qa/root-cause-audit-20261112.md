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
| A01 OAuth discovery | Both auth pages omit Google/GitHub on local demos | `b4313b5` filters on credentials and returns null; regression test was changed to expect hiding | Always show icons + localized short labels; pending reads stay visible; unavailable choices announce an email notice without navigation; provider section + divider precede one email form | `58e2bd6` | Nine new component regressions failed on baseline; affected units 31/31; browser theme/language/width matrix 8/8 (both pages), axe zero violations |
| A02 Local callback mismatch | Configured demo returns toward Vite port 5173 | Initial OAuth defaults from `b4743fc` outlived the local Compose launcher | Compose defaults use web port 18080/LOCAL_WEB_PORT; explicit override and WSL forwarding; empty example keys and README app-registration steps | `58e2bd6` | Real start/state/PKCE tests; localhost fake provider validates exact redirect and client registration |
| A03 OAuth session gap | OAuth sessions cannot rotate and lack email login's family logout revocation | OAuth completion retained its original token-only issuer when `cd4666c` added rotating email sessions | Use shared refresh_tokens.issue after atomic handoff consumption | `58e2bd6` | Both provider refresh/logout tests failed before fix; backend OAuth/payload suites 52/52 after fix; browser renews OAuth sessions |
| A04 Callback configuration validation | A malformed/off-host callback is reported as configured | ProviderSpec.configured only checked nonempty strings | Require fixed provider callback path, same SPA host/scheme, HTTPS except loopback, no credentials/query/fragment; requests never supply redirect_uri | `58e2bd6` | Five invalid-config cases failed before fix and pass after; starts return 503 without Location |
| A05 Undocumented configuration | Operators cannot discover 11 backend settings and 2 Vite overrides from the example | Settings and frontend configuration grew without a name-coverage gate | Document all supported names with safe defaults; docs:check statically compares Settings/Vite names without loading .env | `a8b1fc9` | Checker failed with 13 missing names; regression assertion passes after fix; docs:check covers 69 backend + 2 frontend names |
| A06 Repeated terminal AI failure | Generation sends the same request again after a credential rejection | Outer generation recovery retries every exception, even though the transport treats 401/403 as terminal | Stop generation retries for AUTH_FAILED/NOT_CONFIGURED and retain reviewed bank/template recovery | `bbc272a` | New regression failed with two calls before fix; both terminal-code cases pass with exactly one call after fix; offline request-cap/no-key tests 2/2 |
| A07 Documentation drift | OAuth sign-up/session behavior ambiguous; index says 93 operations; database summary names five nonexistent tables; read-only System use case still saves settings; refreshing captions duplicates numbers | Narrative summaries were outside fact checks; two static captions retained empty sequence fields | Minimal owner-Word text edits; clarify Learner/linking/discovery/rotation, read-only status and real API/table names; restore caption sequence placement, refresh page caches and add gates | `32b87a9` | New Word/schema/index/retired-write/caption assertions fail on old content; strengthened checks verify 48 project + 52 Word assertions; Word 3/3 without repair, stable TOC/TOF caches |
| A08 Browser profile coupling | Production application browser profile selects the release test API after adding the fake OAuth server | Inherited config selects webServer array positions rather than server identity | Find the production API and frontend by health URL; exclude the fake OAuth fixture | `8761e57` | New configuration regression fails before fix; both browser profile assertions pass after; default browser 77/77 |
| A09 Admin reset localization | Password-reset action, form and cancellation remain Vietnamese after switching to English | `7baa905` adds hardcoded copy outside the translation resources; static key coverage cannot detect hardcoded strings | Use shared locale keys for all reset controls and help; retain existing session revocation | Admin reset localization item | English regression fails before fix, Vietnamese baseline passes; both locale flows pass after; full frontend 366/366, 84.11s; real browser checks bilingual cancel/reset, old access/refresh 401 and replacement-password sign-in |
| External provider 403 | New-key evaluator and question generation cannot reach an accepted completion | Configured gateway returns 403; exact account/provider policy requires owner investigation | Keep explicit fallback; do not change the owner's key/model or spend further requests | External blocker | Three reserved HTTP requests, all 403, no token usage returned; model acceptance and real output quality unverified |

A01–A04 are committed and pushed in `58e2bd6`. Their regression assertions
were reviewed without deleting or weakening unrelated coverage. A05 changes
documentation and the gate only; existing runtime defaults are preserved.
A05 is committed/pushed in `a8b1fc9`.
A06 and the bounded live-check tooling are committed/pushed in `bbc272a`.
A08 is committed/pushed in `8761e57`; it changes only test infrastructure.

## Interface and configuration coverage

[Static wiring evidence](wiring-audit-20261112.json) compares **92 operations /
82 OpenAPI paths**, **23 frontend routes**, **10 sidebar destinations** and
**653 literal translation keys**. Every sidebar destination has a route;
all literal keys resolve in Vietnamese and English, including i18next plural
forms. The six plural base names are not missing translations.

| Capability | UI / API surface | Assessment |
| --- | --- | --- |
| Email and social authentication | Login, Register, callback, Settings; server-managed start/callback/handoff/refresh | OAuth defects A01–A04 fixed; email and role guards retained |
| Learner practice | Assessments options/start, Exam, history/evidence, per-attempt/overall evaluation, dashboard | Present; AI source falls back with generation diagnostics and selection notice |
| Administrator | Cohort, grading/review, accounts/lock/unlock, unified question/concept/CLO bank, system status | All five sidebar destinations registered; curriculum URL intentionally redirects to the bank's concepts tab |
| Candidate drafting and translation | Admin API; translation requires its separate opt-in | Intentionally API-only; current README does not promise a Candidates sidebar or translation screen |
| Legacy formal assessment/blueprint APIs | Retained API/schema/history compatibility; current practice is learner-defined | No prebuilt-assessment claim in current README; retirement migration preserves historical evidence |
| Optional AI builder/evaluator | System page explicitly reports model/template and API/fallback state | No silent removal; offline behavior remains usable without credentials |

The real running-demo navigation walkthrough completed **24 role/route/width
checks** (Learner + Administrator, 1280/390), with **0 page errors, failed
requests, unexpected API failures or horizontal overflow**. See
[the detailed route evidence](oauth-20261112/navigation-walkthrough.json).
It used the changed frontend against the existing provider-disabled demo API;
the final full browser gate exercises current backend source in disposable
databases. That gate passed **77/77, 33.1m**, zero failures/skips/retries,
including Mailpit password reset/single-use replay, account provisioning and
activation, refresh security, provider errors and the new auth matrix.
Backend account-status denial/activation checks also pass in the full suite;
an explicit [browser disable/re-enable walkthrough](oauth-20261112/account-access.json)
passes all four checks: disable via Accounts, existing access/refresh rejected
with 401, sign-in shows a handled notice, re-enable permits sign-in. The
[bilingual admin reset walkthrough](oauth-20261112/admin-reset-browser.json)
also verifies cancellation, password replacement and revocation of both old
access and refresh tokens. Only a newly created disposable QA account is changed.

## New-key live ledger (closed for this run)

[New ledger](oauth-20261112/new-key-live-ledger.json) is separate from the old,
exhausted ledger. **3/5 requests used**, all HTTP **403**. Tokens were **not
reported**, so no token total or model-acceptance claim is invented. The key
is masked; model configuration is represented only by its fingerprint.

The one builder/evaluator check uses a synthetic finished MCQ/essay attempt:
one pure template build, unchanged input, exact byte equality between built
prompt and every evaluator message, two valid fallback comments. One generation
check requested one MCQ and produced zero accepted live questions; template
recovery is available. Its second request exposed A06, now fixed and verified
offline. No live check was repeated after the fix. Reasoning/parameter transport,
timeout and invalid-output fallback remain covered by the offline suites; a 403
occurs before model compatibility can be verified against the real gateway.

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
  lint/format/build pass; latest full unit **366/366 (42 files, 84.11s)** and audit
  **zero vulnerabilities**. Fake OAuth + UI/accessibility repeated three times:
  **48/48, 2.6m**. Launcher **7/7**; route inventory matches. Final docs:
  **48 project + 52 Word assertions + 10 figure gates PASS**.
- [Owner Word edit manifest](oauth-20261112/word-edits.json): 31 narrative
  replacements, two caption-field repairs retaining all original runs, four
  cached page references. Only document.xml differs; media/styles/package
  parts and names/dates are preserved. Native Word **3/3 without repair**,
  **59/70/40 pages**; TOC/figure/table caches stable after refresh. All
  LibreOffice pages and native changed pages were visually inspected; its
  Database front-table overlap is renderer-specific, native Word is clean.
  [Render evidence](oauth-20261112/word-render-qa.json).
- [No-env clone browser evidence](oauth-20261112/fresh-clone-browser.json):
  **16 auth states, 32 safe provider notices, 2/2 demo logins**, no page errors
  or external requests. Initial Docker startup exhausted the pre-existing
  default subnet pool. Only two new project-owned networks were created with
  explicit unused 10.232.240/241 subnets; no older network/stack was removed.
  Blank-key generated environment remains local and ignored.
- Three fake-AI repeats, the final demo rebuild and pushed-HEAD CI remain
  pending at this documentation checkpoint.

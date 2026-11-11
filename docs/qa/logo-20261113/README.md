# DBCAS logo QA screenshots — 13 November 2026

All images are full-page browser renders against the Vite dev server at
`127.0.0.1:5180` with the demo API at `:18000`. Desktop viewport: 1280 × 900;
mobile: 390 × 844. Both themes were captured. The capture script measures the
brand, nav and control boxes and fails on horizontal overflow or overlap; the
exact measurements are in [inventory.md](inventory.md) and `after/capture.json`.

## After — canonical database mark + `DBCAS` lockup

| Screen/state | 1280 light | 1280 dark | 390 light | 390 dark |
| --- | --- | --- | --- | --- |
| Landing | [image](after/landing-1280-light.png) | [image](after/landing-1280-dark.png) | [image](after/landing-390-light.png) | [image](after/landing-390-dark.png) |
| Login | [image](after/login-1280-light.png) | [image](after/login-1280-dark.png) | [image](after/login-390-light.png) | [image](after/login-390-dark.png) |
| Register | [image](after/register-1280-light.png) | [image](after/register-1280-dark.png) | [image](after/register-390-light.png) | [image](after/register-390-dark.png) |
| Learner header | [image](after/learner-header-1280-light.png) | [image](after/learner-header-1280-dark.png) | [image](after/learner-header-390-light.png) | [image](after/learner-header-390-dark.png) |
| Learner header, W1 long email | [image](after/learner-long-email-1280-light.png) | [image](after/learner-long-email-1280-dark.png) | [image](after/learner-long-email-390-light.png) | [image](after/learner-long-email-390-dark.png) |
| Admin sidebar | [image](after/admin-sidebar-1280-light.png) | [image](after/admin-sidebar-1280-dark.png) | sidebar hidden by design | sidebar hidden by design |

After measurements (light and dark identical):

- landing: `scrollWidth 1280/1280`; brand 133.6 px.
- login/register: `1280/1280`; brand 110.8 px.
- learner: `1280/1280`; brand 134 px, nav 816.3 px, controls 249.7 px, gap 16 px.
- learner long email: `1280/1280`; same boxes as learner (profile text hidden at 1280).
- learner 390: `390/390`; brand 123.8 px, controls 214 px.
- admin sidebar: `1280/1280`; brand 167.5 px.

Favicon/app icon responses: `favicon.ico` 200, `dbcas-16.png` 200,
`dbcas-32.png` 200, `dbcas-180.png` 200, `manifest.webmanifest` 200.
Generated icon sheet: [icons-preview.png](after/icons-preview.png).

## Before — old mixed lockups

These are retained to show the defect that was removed: inline D symbol +
`BCAS` wordmark, text-only `DBCAS` in auth/landing, no manifest/PWA icons. The
old learner header also overlapped its first nav pill; see
[before/learner-header-1280-light.png](before/learner-header-1280-light.png).

| Screen/state | 1280 light | 1280 dark | 390 light | 390 dark |
| --- | --- | --- | --- | --- |
| Landing | [image](before/landing-1280-light.png) | [image](before/landing-1280-dark.png) | [image](before/landing-390-light.png) | [image](before/landing-390-dark.png) |
| Login | [image](before/login-1280-light.png) | [image](before/login-1280-dark.png) | [image](before/login-390-light.png) | [image](before/login-390-dark.png) |
| Register | [image](before/register-1280-light.png) | [image](before/register-1280-dark.png) | [image](before/register-390-light.png) | [image](before/register-390-dark.png) |
| Learner header | [image](before/learner-header-1280-light.png) | [image](before/learner-header-1280-dark.png) | [image](before/learner-header-390-light.png) | [image](before/learner-header-390-dark.png) |
| Admin sidebar | [image](before/admin-sidebar-1280-light.png) | [image](before/admin-sidebar-1280-dark.png) | sidebar hidden by design | sidebar hidden by design |

Captured with `node docs/qa/logo-20261113/capture.mjs docs/qa/logo-20261113/after`.
The `before/` images were captured with the same browser matrix before the
brand change and are historical evidence only.

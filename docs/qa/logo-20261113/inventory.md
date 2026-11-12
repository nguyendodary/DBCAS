# DBCAS logo and brand unification — 13 November 2026

Canonical source: [`frontend/public/brand/dbcas-mark.svg`](../../../frontend/public/brand/dbcas-mark.svg).
Canonical React lockup: [`frontend/src/components/BrandLogo.jsx`](../../../frontend/src/components/BrandLogo.jsx).
Browser evidence: [README.md](README.md) and [capture.mjs](capture.mjs).

## 1. Before inventory — every visible variant

The old brand was composed in six different ways. `D` was both the symbol and
the first letter of `BCAS`, so the learner/admin lockup read **D + BCAS**; the
other surfaces printed a standalone **DBCAS** string.

| # | Path | Before | Occurrence |
| --- | --- | --- | --- |
| 1 | `frontend/src/components/Layout.jsx` (old `BrandSymbol`, `Brand`) | Inline SVG `viewBox="2 2 36 40"`: outline D, left record bars, inner arc. Wordmark was the literal `BCAS`, so the lockup read D+BCAS. | Learner topbar (`Brand`), mobile topbar (`Brand`), admin sidebar. The same SVG was copied into the admin block. |
| 2 | `frontend/src/components/Layout.jsx` | Hard-coded `<strong>DBCAS</strong>` | Shared chrome footer. |
| 3 | `frontend/src/components/Layout.jsx` | Hard-coded `<span>DBCAS</span>` | Admin utility-bar breadcrumb. |
| 4 | `frontend/src/components/AuthShell.jsx` | Text-only `DBCAS` at `text-lg` plus inline `nav.engineTagFull`. | Login, register and all auth surfaces. |
| 5 | `frontend/src/pages/LandingPage.jsx` | Text-only `DBCAS` plus `landing.brandTag` (`AI SKILL ANALYTICS`) and `landing.brandDesc` (`DATABASE COMPETENCY ASSESSMENT SYSTEM`). | Public landing header. |
| 6 | `frontend/src/pages/LoginPage.jsx` | `t('auth.loginTitle').replace('DBCAS', '')` plus a hard-coded `<span>DBCAS</span>`. | Login card heading. |
| 7 | `frontend/src/pages/ExamPage.jsx` | Hard-coded `<strong>DBCAS</strong>`. | Exam footer. |
| 8 | `frontend/public/favicon.svg` | Unrelated database-cylinder icon with a 32 × 32 viewBox. | Only icon linked from `frontend/index.html`; no manifest, apple-touch or PWA icons. |
| 9 | `frontend/src/index.css` | `.dbcas-brand*`, `.admin-art-brand`, `.admin-signature-*`, `.admin-refined-wordmark`, `.admin-art-caption`, `.auth-login-brand`, `.landing-brand`. | Styling for the duplicate lockups. |
| 10 | `frontend/src/i18n/en.json`, `vi.json` | `landing.brandTag` = `AI SKILL ANALYTICS`; `landing.brandDesc` duplicated the product descriptor. | Only `LandingPage.jsx` used them. |
| 11 | `backend/app/main.py:43` | `FastAPI(title="DBCAS API")`. | OpenAPI title already used the exact product name; no change required. |
| 12 | `backend/app/services/mail.py:33-42` | Subject and body use `DBCAS` in English and Vietnamese. | Password-reset email; already exact; no change required. |
| 13 | `README.md` | No brand-asset pointer. | Repository landing documentation. |
| 14 | `docs/academic/*.docx` (7 files) | Cover/header text: `DBCAS — AI-Assisted Database Competency Assessment and Skill Gap Analysis`; embedded mark images. | **Reported only.** W6 owns Word edits. This worktree did not touch any `.docx`. |

## 2. Canonical asset set

One SVG source, one generated icon set, one React lockup.

| File | Role |
| --- | --- |
| `frontend/public/brand/dbcas-mark.svg` | Canonical source. Database-cylinder mark in a rounded tile, 48 × 48 viewBox, `currentColor`, transparent bands. |
| `frontend/public/brand/favicon.ico` | Generated 16/32/48 px browser favicon. |
| `frontend/public/brand/dbcas-16.png` | 16 px transparent favicon. Visual check: three bold database bands remain legible. |
| `frontend/public/brand/dbcas-32.png` | 32 px transparent favicon. |
| `frontend/public/brand/dbcas-180.png` | Apple touch icon, opaque `#070708`. |
| `frontend/public/brand/dbcas-192.png` | Manifest icon, opaque `#070708`. |
| `frontend/public/brand/dbcas-512.png` | Manifest icon / maskable, opaque `#070708`. |
| `frontend/public/brand/manifest.webmanifest` | `name` and `short_name` exactly `DBCAS`; 192/512 icons. |
| `frontend/public/brand/README.md` | Asset contract and regeneration command. |
| `frontend/scripts/generate-brand-icons.mjs` | `npm --prefix frontend run brand:icons`; Chromium rasterizes the SVG and writes the ICO + five PNGs. |

**Why the mark is not a D:** the old D symbol plus the new full `DBCAS`
wordmark read as “D DBCAS”. The canonical mark is now a database cylinder; the
wordmark is the only lettering in the lockup. There is no second D and no split
`BCAS` wordmark.

**Light/dark:** no separate logo variant is needed. The component paints the
SVG as a CSS mask with `background-color: var(--primary)` (dark `#22d3ee`,
light `#0e6f7c`). Generated app icons use the dark-background cyan treatment.

**Tool note:** Python 3.14.5 + PIL 12.2.0 are available; `cairosvg` and `svglib`
are not. Chromium via the existing Playwright dependency is the SVG rasterizer,
and the script is checked in so the icons are reproducible.

## 3. Replacements

| Surface | After |
| --- | --- |
| Learner topbar, mobile topbar, admin sidebar | `<BrandLogo variant="header|admin">` from `BrandLogo.jsx`; the component owns the mark, `PRODUCT_NAME = 'DBCAS'` and `nav.engineTagFull`. |
| Admin breadcrumb, shared chrome footer, exam footer | `<BrandWordmark>` / `<BrandWordmark as="strong">`; no literal DBCAS in those components. |
| AuthShell (login/register and auth pages) | `<BrandLogo variant="auth">`; tagline hidden below 640 px. |
| Landing | `<BrandLogo variant="landing">`; tagline now `nav.engineTagFull` (`SKILL ANALYTICS` in both locales). Removed `landing.brandTag` / `landing.brandDesc`. |
| Login heading | Full `t('auth.loginTitle')`; removed the `replace('DBCAS','')` split. |
| `frontend/index.html` | `favicon.ico`, 32 px PNG, `apple-touch-icon` 180, `manifest.webmanifest`, `theme-color`; old `favicon.svg` removed. |
| Header layout | Brand is `flex: 0 0 auto`; full pill nav moves to `xl` (1280); below that the existing second-row scroll nav is used. Account name shows at `2xl`, and both account name blocks truncate at 220/240 px. |
| `README.md` | New “Logo và thương hiệu” section points to the canonical SVG and React lockup. |
| `en.json` / `vi.json` | Removed duplicate landing tagline/descriptor keys; footers use `DBCAS · Skill Analytics` / `DBCAS · Skill Analytics` (vi keeps its localized descriptor). |

Removed duplicates/assets: `frontend/public/favicon.svg`, `BrandSymbol`,
local `Brand`, `.dbcas-brand*`, `.admin-art-brand`, `.admin-signature-*`,
`.admin-refined-wordmark`, `.admin-art-caption`, `.auth-login-brand`,
`.landing-brand`.

## 4. Browser verification

Run against the Vite dev server at `127.0.0.1:5180` proxying the demo API at
`:18000`:

```powershell
node docs/qa/logo-20261113/capture.mjs docs/qa/logo-20261113/after
```

The script fails if the page scrolls horizontally, if any brand part leaves the
lockup, or if the brand overlaps a header/sidebar control. The long-email
scenario intercepts `/auth/me` with the exact W1 account shape
(`w1-locale-1794382816554@dbcas.local`). W1's original 1294 px evidence came
from the Docker build on `:18080`; this worktree did not restart Docker, so the
fixed source was measured on the Vite dev server against the same demo API.

| Scenario | 1280 light/dark | 390 light/dark |
| --- | --- | --- |
| Landing | `scrollWidth 1280 / 1280`; brand 133.6 px | `390 / 390`; brand 133.6 px |
| Login | `1280 / 1280`; brand 110.8 px | `390 / 390`; brand 101.6 px |
| Register | `1280 / 1280`; brand 110.8 px | `390 / 390`; brand 101.6 px |
| Learner header | `1280 / 1280`; brand 134 px, nav 816.3 px, controls 249.7 px, **brand-to-nav gap 16 px** | `390 / 390`; brand 123.8 px, controls 214 px |
| Learner long email (W1 shape) | `1280 / 1280`; brand 134 px, nav 816.3 px, controls 249.7 px, gap 16 px | `390 / 390`; brand 123.8 px, controls 214 px |
| Admin sidebar | `1280 / 1280`; brand 167.5 px | not applicable (sidebar hidden) |

Asset responses: `favicon.ico` 200 `image/x-icon` 2379 B, `dbcas-16.png` 200
`image/png` 449 B, `dbcas-32.png` 767 B, `dbcas-180.png` 3950 B,
`manifest.webmanifest` 200 `application/manifest+json` 479 B.

Screenshots: [after light/dark matrix](README.md). The before matrix is in
`before/`; the after matrix, including the W1 long-email header and the
generated icon sheet, is in `after/`.

## 5. Tests and gates

| Gate | Result |
| --- | --- |
| `frontend/src/test/BrandAssets.test.jsx` | 9/9 passed. Checks one SVG source, exact PNG/ICO sizes, manifest/index links, one `BrandLogo`, no inline brand geometry, no split `BCAS`, no hard-coded `DBCAS` outside `BrandLogo`. |
| `npm test -- --maxWorkers=2` | **43 files, 375 tests passed** (96.06 s). |
| `npm run lint` | 0 errors, 0 warnings. |
| `npm run format:check` | All matched files use Prettier code style. |
| `npm run build` | 142 modules transformed, built in 815 ms. |
| `node scripts/check_contrast.mjs` | **186/186 checks passed** (brand colours unchanged; `--primary` reused). |
| `npm --prefix frontend run brand:icons` | 16/32/180/192/512 PNGs + 16/32/48 ICO regenerated from `dbcas-mark.svg`. |

No commit was created. `docs/qa/handover.md`, `.env`, Docker and every `.docx`
were left untouched.

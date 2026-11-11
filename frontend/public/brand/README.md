# DBCAS brand assets

`dbcas-mark.svg` is the **only** logo source. Everything else in this folder is
generated from it:

| File                   | Size / purpose                                           |
| ---------------------- | -------------------------------------------------------- |
| `dbcas-mark.svg`       | Canonical database mark, `currentColor`, 48 × 48 viewBox |
| `favicon.ico`          | 16, 32 and 48 px browser favicon                         |
| `dbcas-16.png`         | Transparent favicon fallback                             |
| `dbcas-32.png`         | Transparent favicon fallback                             |
| `dbcas-180.png`        | Apple touch icon, opaque `#070708`                       |
| `dbcas-192.png`        | Web app manifest icon, opaque `#070708`                  |
| `dbcas-512.png`        | Web app manifest icon / maskable, opaque `#070708`       |
| `manifest.webmanifest` | PWA name, colours and icon references                    |

Regenerate the raster assets from the repository root:

```powershell
npm --prefix frontend run brand:icons
```

The script uses Chromium through the existing Playwright dependency. The
Python environment has PIL 12.2.0 but no SVG rasterizer (`cairosvg` and
`svglib` are absent), so PIL is not needed.

The mark is a database cylinder, not a letter D: the lockup must not read as
“D DBCAS” next to the full wordmark. The React lockup — mark, wordmark and the
`nav.engineTagFull` tagline — lives in `frontend/src/components/BrandLogo.jsx`.
Do not add another logo SVG or hard-code a second DBCAS wordmark in a page or
component.

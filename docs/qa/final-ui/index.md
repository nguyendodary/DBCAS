# Final UI evidence — 2026-11-10

The complete light/dark screen matrix (20 screens × 1280/390) is in
[`screenshots.md`](screenshots.md); this page keeps the earlier focused SQL and
dashboard evidence.

Captured from the `develop2` worktree with Vite + the local Compose API.
Every screenshot is a real page render; no mock markup.

| File | View | Width | Theme | What it proves |
| --- | --- | ---: | --- | --- |
| `sql-1280-light.png` | SQL question, full page | 1280 | light | Two-zone prompt/schema + editor, results below, no page overflow |
| `sql-1280-dark.png` | SQL question, full page | 1280 | dark | Dark theme did not regress |
| `sql-1920.png` | SQL question | 1920 | light | Max-width layout and wide editor |
| `sql-768.png` | SQL question, stacked | 768 | light | Prompt → editor order at tablet width |
| `sql-390.png` | SQL question, full page | 390 | light | Mobile prompt → schema → editor → results, no page-level horizontal scroll |
| `sql-390-dark.png` | SQL question, full page | 390 | dark | Mobile dark theme |
| `sql-error-full-1280.png` | SQL error state | 1280 | light | One short Vietnamese sentence + database message in a monospace box |
| `dashboard-1280-light.png` | Learner dashboard | 1280 | light | Stat cards, radar, horizontal category bars, table |
| `dashboard-1280-dark.png` | Learner dashboard | 1280 | dark | Dark parity; chart labels legible |
| `dashboard-390-light.png` | Learner dashboard | 390 | light | Stats, radar, cards stack without overflow |
| `dashboard-390-dark.png` | Learner dashboard | 390 | dark | Mobile dark parity |
| `admin-grading-1280-light.png` | Admin review queue/detail | 1280 | light | Queue, badges, review controls |
| `admin-system-1280-light.png` | Admin system workflow | 1280 | light | One mandatory AI → administrator flow, localized copy |
| `admin-system-1280-dark.png` | Admin system workflow | 1280 | dark | Dark parity |

## Automated checks

- `document.documentElement.scrollWidth === window.innerWidth` at 390, 768,
  1280 and 1920 for the SQL question: **PASS**.
- All four Inter weights plus Vietnamese glyphs (`ế ở ữ ỹ`) load:
  `document.fonts.check(...)` **true** for 400/500/600/700.
- `npm run ui:contrast` **PASS** for dark and light text/chart tokens.
- Chart canvases have 0–100 axes, text legends and tabular numeric labels; no
  series is distinguished by colour alone (the dashboard lists every value in
  text next to each chart).

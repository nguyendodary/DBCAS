# Light theme specification — 2026-11-10

Reference studied: <https://artificialanalysis.ai/> (home, `/models`,
`/leaderboards/models`). Screenshots used only for analysis are in
`docs/qa/final-ui/reference/`. No Artificial Analysis logo, brand mark, copy,
serif typeface or purple brand colour is copied into DBCAS.

## What the reference actually does

| Area | Observed | Principle adopted |
| --- | --- | --- |
| Page canvas | Flat white on the home page; a very light neutral grey field behind white cards on the comparison and leaderboard pages. | One neutral page canvas (`--bg`), white content surfaces. No blue cast, no page gradient. |
| Surfaces | White cards with a hairline border; almost no shadow. Cards sit on grey, not on other cards. | Borders first. Shadows only for dialogs/popovers. One raised level. |
| Borders | 1 px light grey (`#d9d9d9`–`#e7e7e7`), used for cards, table cells, inputs and dividers. | A quiet border token for structure; a stronger border only for inputs and selected states. |
| Type | Large editorial heading, 14–16 px UI text, 12 px tables, heavy weight contrast between title and metadata. Near-black text on white. | Keep Inter. Tight heading tracking, strong near-black body, muted metadata, no low-contrast grey-on-grey. |
| Tables | 12 px, ~45 px rows, 8 px cells, header strip on light grey, 1 px row dividers, no vertical decoration. | Dense, scannable tables; numbers tabular; sticky header/end column; hover row only. |
| Charts | White card, thin axes, dashed light grid, small labels, direct value labels above bars, saturated but distinct series colours, square legend swatches. | 0–100 % axes, dashed grid, readable labels, direct values, text legend, no colour-only encoding. |
| Tabs / chips | Grey pill group, active pill near-black with white text; secondary buttons light grey; primary actions black or one brand accent. | Pill navigation and filter chips. Active state is a filled dark pill, not a coloured glow. |
| Inputs | White field, 1 px grey border, 8 px radius, 36–44 px height. | White field on white/grey surfaces; border and focus ring carry the state. |
| Spacing | Generous section gaps, dense data regions; 4/8 px rhythm. | 4/8 grid; 24 px card padding, 16 px grid gap, 8 px cell padding. |
| Focus / hover | Hover is a small surface shift; focus is a clear outline, not a shadow. | 2 px primary outline with 2 px offset; hover surface shift only. |

## Design principles

1. **Neutral paper, white cards.** The page is a light neutral field; content is
   white. Colour is reserved for meaning and actions.
2. **Structure with lines, not depth.** A 1 px border separates; shadows are
   dialog-only. This keeps dense exam and admin screens calm.
3. **Quiet chrome, strong content.** Navigation, filters and metadata recede;
   question text, scores and primary actions carry the contrast.
4. **Dense but breathable.** Tables and charts are compact (12–13 px, 40–44 px
   rows) with 8 px cells; page sections keep 24–32 px breathing room.
5. **One accent, semantic status.** DBCAS keeps its teal identity for links,
   focus and primary actions; green/amber/red/blue stay semantic. Charts use a
   separate accessible categorical palette.
6. **No decoration without information.** No gradient blobs, glass, glow or
   coloured card washes in light mode. Tinted status remains a thin border and
   icon, not a background wash.
7. **Same contract in both themes.** Every token exists in dark and light; the
   dark theme keeps its current identity and only shares structure.

## Tokens (light)

| Token | Value | Use |
| --- | --- | --- |
| `--bg` | `#f4f5f7` | Page canvas |
| `--surface` | `#ffffff` | Cards, tables, inputs, dialogs |
| `--surface-elevated` | `#ffffff` | Raised card / sticky header |
| `--surface-muted` | `#f0f2f4` | Table head, segmented control, quiet fills |
| `--surface-sidebar` | `#fafbfc` | Sidebar / top chrome |
| `--border` | `#e4e7ea` | Card, table and divider lines |
| `--border-strong` | `#c9ced4` | Inputs, selected chips, stronger dividers |
| `--text` | `#0e1113` | Primary text |
| `--text-muted` | `#46505a` | Body secondary |
| `--text-subtle` | `#5c6772` | Metadata |
| `--text-faint` | `#65707a` | Hints, placeholders (≥ 4.5:1 on white) |
| `--text-disabled` | `#68727d` | Disabled label |
| `--primary` | `#0e6f7c` | Links, focus, primary action |
| `--primary-hover` | `#0a5864` | Hover / pressed |
| `--primary-foreground` | `#ffffff` | Text on primary |
| `--primary-dim` | `#cfe8ec` | Soft accent border |
| `--brand-text` | `#0b5f6a` | Brand text on light surfaces |
| `--success` | `#12813f` | Success icon/border |
| `--success-text` | `#116b36` | Success text |
| `--success-surface` | `#eaf7ef` | Success badge fill |
| `--warning` | `#9a6700` | Warning icon/border |
| `--warning-text` | `#7a5200` | Warning text |
| `--warning-surface` | `#fff6df` | Warning badge fill |
| `--danger` | `#c0183b` | Danger icon/border |
| `--danger-text` | `#a90f31` | Danger text |
| `--danger-surface` | `#fff0f3` | Danger badge fill |
| `--info` | `#0b6ca8` | Info icon/border |
| `--info-text` | `#075985` | Info text |
| `--secondary` | `#6d28d9` | Violet category / essay |
| `--neutral-status-text` | `#3f4a56` | Neutral badge text |
| `--overlay` | `rgb(14 17 19 / 0.45)` | Dialog backdrop |
| `--surface-hover` | `rgb(14 17 19 / 0.04)` | Row / control hover |
| `--surface-selected` | `rgb(14 111 124 / 0.08)` | Selected row/option |
| `--shadow-card` | `rgb(14 17 19 / 0.04)` | Max 1 px card lift |
| `--shadow-dialog` | `0 24px 48px -12px rgb(14 17 19 / 0.24)` | Dialogs only |
| `--shadow-header` | `rgb(14 17 19 / 0.06)` | Sticky header, optional |
| `--section-tint` | `#ffffff` | Card title band |
| `--section-border` | `#e4e7ea` | Section rule |
| `--selection-bg` | `rgb(14 111 124 / 0.18)` | Text selection |

### Editor / SQL

| Token | Value |
| --- | --- |
| `--editor-bg` | `#ffffff` |
| `--editor-surface` | `#f7f8f9` |
| `--editor-border` | `#d6dbe0` |
| `--editor-text` | `#111417` |
| `--editor-muted` | `#5c6772` |
| `--code-keyword` | `#0b5f87` |
| `--code-function` | `#6d28d9` |
| `--code-string` | `#116b36` |
| `--code-number` | `#8a5300` |
| `--code-comment` | `#66707a` |
| `--code-identifier` | `#1f262c` |

### Charts

Categorical palette, all ≥ 3:1 against white; series are also labelled in text,
never by colour alone. Bars get direct value labels; legends use text + swatch.

| Token | Value |
| --- | --- |
| `--chart-1` | `#2563eb` |
| `--chart-2` | `#c2410c` |
| `--chart-3` | `#15803d` |
| `--chart-4` | `#7c3aed` |
| `--chart-5` | `#a16207` |
| `--chart-6` | `#b91c1c` |
| `--chart-7` | `#0e7490` |
| `--chart-8` | `#4d7c0f` |
| `--chart-9` | `#a21caf` |
| `--chart-10` | `#475569` |
| `--chart-target` | `#be123c` |
| `--chart-grid` | `rgb(71 85 105 / 0.16)` |
| `--chart-axis` | `#cbd5e1` |
| `--chart-label` | `#46505a` |
| `--chart-muted` | `#5c6772` |
| `--chart-tooltip` | `#ffffff` |
| `--chart-tooltip-text` | `#0e1113` |

Chart rules: y-axis always 0–100 % for score charts; grid dashed 1 px; axis line
1 px `--chart-axis`; tick labels 11 px `--chart-label`; legend 12 px text with
an 8 px square; bar radius 2 px; line width 2 px; no shadows, no gradients, no
3-D. Missing data is a text “—” not a zero bar.

### Radius, spacing, elevation

| Token | Value |
| --- | --- |
| `--radius-sm` | `4px` |
| `--radius-md` | `6px` |
| `--radius-lg` | `8px` |
| `--radius-xl` | `12px` (dialogs only) |

Spacing follows a 4/8 grid: 4, 8, 12, 16, 24, 32, 48, 64 px. Card padding 20–24
px; grid gap 16 px; table cell padding 8–12 px; control height 36–44 px.

Elevation in light mode: `0` (page) → `1` (white card on canvas, border only) →
dialog (shadow + overlay). No nested shadows, no glow.

## Typography (unchanged fonts)

Inter Variable for every UI string, including scores, MCQ answers, essay input,
identifiers and micro-labels. Numeric UI uses tabular figures. JetBrains Mono
Variable is reserved for SQL queries, schema and SQL results. No serif and no
new font files.

| Role | Size / line-height | Weight | Tracking |
| --- | --- | --- | --- |
| Display / hero | 32–40 / 1.1 | 650 | -0.03em |
| Page title | 26–28 / 1.2 | 650 | -0.02em |
| Section title | 18 / 1.3 | 600 | -0.01em |
| Card title | 14–15 / 1.4 | 600 | 0 |
| Body | 14 / 1.55 | 400 | 0 |
| Table body | 13 / 1.4 | 400 | 0 |
| Table head | 11–12 / 1.3 | 600 | 0.06em uppercase |
| Metadata / hint | 12 / 1.5 | 400–500 | 0 |
| Micro label | 11 / 1.4 | 700 | 0.12em uppercase |

## Components

- **Top bar:** white, 1 px bottom border, 56–64 px tall. Brand at left; centred
  pill nav; account controls at right. No shadow unless content scrolls under it.
- **Pill nav:** 999 px radius, 8 px 14 px padding, 14 px/600. Inactive text
  `--text-muted`; hover `--surface-muted`; active filled `--text` with white text.
- **Buttons:** 8 px radius, 36–40 px height, 14 px/600. Primary = `--primary`
  fill, white text. Secondary = white with `--border-strong`. Quiet = text only.
  No gradients, no glow. Disabled = muted label + muted fill, no opacity alone.
- **Inputs / selects:** white, 1 px `--border-strong`, 8 px radius, 40–44 px,
  14 px text; focus 2 px primary ring with 2 px offset; error uses danger border
  plus text, never colour alone.
- **Cards:** white, 1 px `--border`, 8 px radius, 20–24 px padding, no shadow.
  Section header separated by a 1 px rule and `--surface-muted` band.
- **Tables:** white, 13 px; head `--surface-muted`, 11–12 px uppercase 600,
  8 px 12 px padding; rows 40–44 px with 1 px `--border` dividers; numeric
  values right-aligned and tabular; hover `--surface-hover`; sticky end column
  keeps its own white background and a left rule.
- **Tabs / chips:** pill group on `--surface-muted`; active pill filled dark;
  filter chips white/grey with 1 px border, 999 px radius, 12 px/500; selected
  uses `--surface-selected` and primary text, plus `aria-selected`.
- **Badges:** 999 px, 12 px/600, tinted semantic surface + matching text and a
  1 px border. Never a saturated fill with white text at small size.
- **Sidebar / admin nav:** `--surface-sidebar`, 1 px right border; active item
  uses `--surface-selected` and a 2 px primary left rule.
- **Charts:** as above; card header carries the title, unit and legend; canvas
  has a text alternative (`aria-label`) with the 0–100 range.
- **Empty/error states:** plain white panel, 1 px border, icon + one sentence +
  one action; no illustration dependency.
- **Dialogs:** white, 12 px radius, 24 px padding, dialog shadow, overlay;
  focus is trapped and restored.

## Application and verification

- Tokens are defined only in `frontend/src/index.css`; screens use semantic
  utility names (`bg-panel`, `text-ink`, `border-edge`, …) and never hard-code
  light colours.
- `scripts/check_contrast.mjs` checks every text token against every surface
  token (4.5:1) and every chart token (3:1), for both themes.
- Screenshots: `docs/qa/final-ui/light/` and `/dark/`, 1280 and 390 px, indexed
  in `docs/qa/final-ui/screenshots.md`; dark screenshots are compared against
  the pre-redesign set to prove no regression.
- No overflow at 390 px; no clipped text; focus visible at 1280 and 390.

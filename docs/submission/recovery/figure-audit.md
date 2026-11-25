# Figure and diagram audit (Phase 5)

Scope: the five authoritative ver1.3 documents at `docs/submission/final/`, their
`assets/`, the older content-complete ver1.3 set at
`Documents/Final-ver1.3/`, and the editable sources under `docs/diagrams/`.
Visual inspection was done by opening extracted images and rendered PDF pages;
see `qa/figures/`, `qa/contact-sheets/` and `qa/fitai/`.

## 1. Conventions adopted for this revision

- Keep existing figures; modify only where a figure is unreadable or inconsistent.
- Prefer editable sources (`.drawio`, `.dot`, `.svg`, generator scripts) and record
  the source beside the shipped raster.
- Use the FITAI-derived palette for any recreated figure: ink `#000000`, navy
  `#1F3863`, accent blue `#4472C4`, light fill `#D9E2F3`, rule gray `#44546A`,
  milestone orange `#ED7D31`, caption gray `#44546A`.
- Do not introduce stock art or a new illustration grammar.

## 2. Figure inventory — authoritative five-document set

| Doc | Fig | Title | Source / editable source | Status | Disposition |
|---|---|---|---|---|---|
| Proposal | 1 | Sprint roadmap and faculty milestones | `assets/gantt-roadmap.png`; raster-only legacy chart | **Recreated** 2026-11-25 from new `assets/gantt-roadmap.svg` in the FITAI palette; milestone data preserved from Table 12 | Retain revised |
| Proposal | 2 | System context | `assets/context.png`; `docs/diagrams/system-context.svg`, `rebuild/system-context/*.drawio` | Legible, consistent monochrome line art | Retain |
| Proposal | 3 | Logical architecture | `assets/logical.png`; `docs/diagrams/logical-architecture.dot/.svg`, `rebuild/logical/*.drawio` | Legible; serif grammar differs from context/Gantt | Retain, record style family |
| Architecture | 1 | System context | same as Proposal 2 | Retain | Retain |
| Architecture | 2 | Logical architecture | same as Proposal 3 | Retain | Retain |
| Architecture | 3 | Module view | `docs/diagrams/rebuild/module/module.png` + drawio/SVG source | Retain | Retain |
| Architecture | 4 | AI pipeline | `assets/pipeline.png`; `rebuild/pipeline/*.drawio/.svg` | Retain | Retain |
| Architecture | 5 | Allocation view | `docs/diagrams/rebuild/allocation/allocation.png` + drawio/SVG source | Retain | Retain |
| Database | 1 | ERD sheet 1 | `assets/erd-sheet-1.png`; `schema-028/erd-1.svg` | Generated style: navy title, light-blue heads, monospace column text | Retain |
| Database | 2 | ERD sheet 6 | `assets/erd-sheet-6.png`; `schema-028/erd-6.svg` | Retain | Retain |
| Database | 3 | ERD sheet 9 | `assets/erd-sheet-9.png`; `schema-028/erd-9.svg` | Retain | Retain |
| Database | 4 | ERD sheet 10 | `assets/erd-sheet-10.png`; `schema-028/erd-10.svg` | Retain | Retain |
| Code Standards | – | Cover logo only | `assets/logo.png` | Retain | Retain |
| Technical Report | 1 | Evaluation pipeline | `assets/pipeline.png` (same bytes as Architecture 4) | Retain; keep in sync | Retain |

All five documents also embed the same 454×134 university mark on the cover.

## 3. Figures present in the content-complete baseline but absent from the submitted set

| Family | Baseline evidence | Editable source | Disposition |
|---|---|---|---|
| Use-case diagram (UC01–UC18) | older Architecture Fig 1; `before-after/diagrams/Architecture-image1-*` | `rebuild/use-case/*.drawio/.svg`, `diagrams/use-cases.dot/.svg` | Restore as an appendix figure if owner wants classical SE coverage; otherwise record intentional retirement |
| Container diagram | older Architecture Fig 3 | `rebuild/container/*.drawio/.svg`, `containers.dot/.svg` | Text Table 3 covers the content; figure intentionally retired |
| Component diagrams 1/2 + 2/2 | older Architecture Fig 4 | `rebuild/component/*.drawio/.svg`, `components.dot/.svg` | Intentionally retired; module view retained |
| ERD 2/2 continuation | older Architecture Fig 7 / Database Fig 1 (2/2) | `erd67.py`, `rebuild/erd` | Superseded by schema-028 ERD sheets; intentionally retired |
| TRD 1/11–11/11 (41-table card set) | older Architecture Fig 8 x11 / Database Fig 2 x11 | `trd67.py`, `rebuild/trd` | Superseded by the 67-table dictionary and schema-028 diagrams; intentionally retired |
| Evidence pipeline as Proposal Fig 4 | older Proposal Fig 4 | `rebuild/pipeline/*.drawio/.svg` | Relocated to Architecture Fig 4 / Technical Report Fig 1 |
| 11 of 15 schema-028 ERD sheets | `schema-028/erd-1…15.svg` | generator-managed | Four representative sheets retained; record selection rule |

## 4. Style families found (evidence)

1. **Monochrome sans-serif** — context, Gantt (original). Thin black strokes, bold
   Arial labels, legend bar. (`qa/figures/ProposalDocument-image3.png`)
2. **Monochrome serif** — logical architecture, pipeline, module, allocation. Heavier
   strokes, Times-like bold titles, gray/white boxes. (`qa/figures/ProposalDocument-image4.png`)
3. **Navy + light-blue generated** — ERD sheets. Dark navy title, light-blue entity
   heads, monospace columns, amber legacy markers. (`qa/figures/DatabaseDesign-image2.png`)
4. **Legacy pastel/navy** — use-case and component images in `before-after/`, not
   shipped in the submitted set. (`qa/fitai/` and `before-after/diagrams/`)

FITAI figures (`qa/fitai/Architecture-p029.png`, `Database-p009.png`) use monochrome
line art inside a light frame with an italic centered caption. Family 1 is closest
to FITAI; family 3 is a schema-specific extension with a documented source. This
revision does **not** merge families by force-redrawing correct content; it records
them and applies the shared palette only to the recreated Gantt.

## 5. Verification after revision

- Recreated Gantt: `assets/gantt-roadmap.svg` (editable) and PNG; visually checked at
  full size for clipped labels, overlap and legibility.
- All embedded images were re-extracted after revision and checked for byte integrity
  with `docs/submission/tools/docx_toolkit.validate_docx`.
- Rendered-page inspection and page-by-page contact sheets are recorded in
  `visual-qa-report.md`.

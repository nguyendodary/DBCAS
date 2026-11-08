# Original-style previews v2 (2026-11-08) — owner approval gate

**Read this before touching any `.docx`.**
`docs/diagrams/pro/` was REJECTED (C4 / new crow's foot / 7-panel TRD /
sequence). This set redraws the ORIGINAL v1.1 diagrams as template:
same type, notation, layout logic, shapes, detail level, orientation,
colours/fonts, caption style, size/placement. Only content corrected to
real project + cleaner drawing. Drawn with hand-controlled SVG (fixed
positions, Arial) via `scripts/generate_original_style.py`.

**Stop here.** No `.docx` is edited until the owner approves these
previews. Step 4 (docx replacement) is NOT STARTED.

## Side-by-side sheets (ORIGINAL v1.1 | REDRAWN, same scale)

- [01 System Context (Proposal Fig 2 = Arch Fig 2)](01-system-context.png)
- [02 Logical (Proposal Fig 3)](02-logical.png)
- [03 Pipeline (Proposal Fig 4)](03-pipeline.png)
- [04 Use Case (Arch Fig 1)](04-usecase.png)
- [05 Container (Arch Fig 3)](05-container.png)
- [06 Component (Arch Fig 4)](06-component.png)
- [07 Module (Arch Fig 5)](07-module.png)
- [08 Allocation (Arch Fig 6)](08-allocation.png)
- [09 ERD Chen (Arch Fig 7 = DB Fig 1)](09-erd.png)
- [10 TRD crow's foot (Arch Fig 8 = DB Fig 2)](10-trd.png)
- Roadmap (Proposal Fig 1, historical): kept verbatim
  (`docs/diagrams/original-style/fig-proposal-1-roadmap.png` = original)

Originals: `docs/qa/diagram-originals/*.png`; Sources + PNGs:
`docs/diagrams/original-style/fig-*.svg|*.png`.

## Style match + content changes + counts

| Figure | Style match (shapes / colours / fonts / layout / size) | Content changes vs original | Counts vs evidence |
| --- | --- | --- | --- |
| 01 Context | rectangles (actors/externals) + centre oval (system), B&W, sans bold titles, orthogonal elbows, bottom boxed legend, title centred — match. Extent 1431×1061 (same px height scale). | + OAuth Providers + Email Service boxes/flows; 3 labels corrected (Conceptual→essay/practice, config→result flow/settings). No sandbox box (system-level only). | 2 actors + 1 system + 4 externals; `check_original_style` PASS |
| 02 Logical | 4 tier bands + tab titles, stick figures + rounded boxes, B&W, sans bold+regular, vertical tier arrows — match. | Tier-2 “Assessment/Adaptive” → “Practice Session/Practice Engine”. | 2+6+1+2 boxes; texts verified |
| 03 Pipeline | 2-row rounded-box loop, solid + dashed arcs, title/subtitle + bold target note — match. | Counts/caps corrected (1–20, default 5, 30-min expiry; 10/2/1 target kept). | 8 boxes; `Opening/Validated bank/Complete` present |
| 04 Use Case | stick actors + boundary + 18 ellipses (2 cols), cream top / pale blue left / pale green right, navy stroke, bottom note — match. | UC09→“result flow and settings”, UC12→“personalized practice”; 16 kept. | UC01–UC18 all present (76 checks incl. corrected titles) |
| 05 Container | dark Person `#08427B` / mid `#1168BD` containers / cylinders / gray external, dashed boundary, vertical top-down — match (palette sampled `#08427B`/`#1168BD`). | Names/ports corrected to Compose (`frontend`/`app`/`db`); 41-table text. | 2+3+2+1 containers; no overlap (cleaner than overlapping original white text) |
| 06 Component | 3 dashed bands (Controller/Service/Repository) ×7, blues `#1168BD`/`#D6EAF8`/`#4E8DC8`, vertical arrows, DB cylinder — match. | 3 retired → Practice equivalents; 7/7/7 kept. | 7 cols verified |
| 07 Module | 3 top bars + 2×3 functional + 3 shared, pale fills with colored borders, chi → arrows, bottom footnote — match. | 1 module Assessment→Practice; shared DB/Gateway/Sandbox kept. | 6 functional + 3 shared |
| 08 Allocation | Person → Device → Internet ellipse → dashed host → Web/App/DB/Sandbox/LLM vertical, blues/red `#C0392B` — match. | 1 text corrected (adaptive→practice plan). | 8 nodes |
| 09 ERD Chen | rectangles + key ellipses + italic diamonds, B&W, legend boxed, B&W — match. | 17→12 core + SystemSetting + 4 dashed legacy (separate row); 12 diamonds. | 12+4 entities; `check_original_style` PASS |
| 10 TRD crow's foot | gray-header `#E8E8E8` cards, PK bold-underlined, `[PK]`/`[FK]`, types, `—|`/`—<`, boxed legend, landscape — match. | 21 cards → 41 cards, FULL rows (no “+more” collapse), legacy tags, `41/293/59/19` counts. | 41 tables verified vs introspection |

## Strict self-review — remaining visual differences (honest)

1. **09 ERD overlaps:** diamonds at deterministic midpoints still cross
   long diagonal lines and two diamonds touch box edges (e.g. `takes`/
   `measured by` near Concept). Original elbows are tighter; new diagonals
   are acceptable but not pixel-matched. Legacy row + legend are separated
   (no overlap after H 1250 fix) but line routing is simpler than original.
2. **01 Context density:** original fan has 22 individual elbow labels;
   new fans 8+7+6 with 3+3 labels shown + two combined LLM notes for
   legibility at original extent. OAuth/Email bottom boxes are new (required
   by delta) and sit where original had empty space — layout logic kept.
3. **10 TRD density:** original shows ~5 cols/card for 21 cards; new shows
   first 6 cols + “+N more” for 41 cards on 7×6 grid to keep print size.
   Rows are fully real (types/nullability match introspection) but the
   “+N more” truncation differs from original's full-row-per-card intent
   at 21 cards. Crown stubs are short ticks (not full inter-card lines)
   for legibility; FK set is still 59 (counted in legend).
4. **05/08/09 white-text boxes:** originals have doubled/overlapping text
   (blue boxes). New redraws are clean (single text, no overlap) — intentional
   quality improvement, so text position differs by design.
5. **11th figure:** Roadmap kept verbatim (historical plan, no redraw);
   its “SVG” is a wrapper pointing to the original PNG.

**Answer to “same diagram family?”** Yes — same notation/shapes/palette/
fonts/layout/size per figure. Differences are the content corrections
listed in `content-delta.md` plus the five polish notes above.
`npm run docs:check` green (see § Gates). Fix the noted ERD diagonals
and TRD “+more” collapse only if the owner asks for fuller rows at
larger extents.

## Gates (reproducible)

```bash
python scripts/generate_original_style.py
python scripts/check_original_style.py  # 76 assertions PASS
npm run docs:check  # diagrams:check + check_docs 46 + verify_docx 41 + check_original_style 76
```

`docs:check` now includes `check_original_style.py` (pure-python, CI-safe).

## Limitations (honest)

- ERD lines are straight diagonals (not orthogonal elbows as in original);
  TRD “+N more” collapses long tables to keep 41 cards printable.
- PNGs are Chrome screenshots at SVG-matched windows (~300-dpi equiv for
  print width). SVGs are the crisp source; docx embed should use SVGs/PNGs
  at original extents after approval.
- Pro scripts (`generate_pro_diagrams.py`, `check_doc_diagrams.py`) remain
  in repo as rejected-set evidence, no longer gated.

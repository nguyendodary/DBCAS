# Visual audit

LibreOffice headless was used to render BEFORE and AFTER PDFs; Word was used to confirm the SRS cover rendering (no footer, mentor inside border).

## Page counts

| Document | BEFORE | AFTER | Change |
|---|---:|---:|---|
| Proposal | 59 | 60 | +1 (added writable/grounding/release text; Word counts) |
| Architecture | 70 | 70 | 0 (added counts/writable/release text; Word counts) |
| Database | 40 | 63 | +23 (26 appendix tables + expanded columns; Word counts) |
| SRS | 20 (Student Management base) | 4 (new DBCAS SRS) | new document; FITAI cover + root SRS structure |

## BEFORE/AFTER pairs

Page pairs (side-by-side) are in `before-after/pages/`:

- Proposal: cover, p10 practice limit, p48/49 release wording, p50/51 Fig 3, p52/53 Fig 4.
- Architecture: cover, p14 use case, p45 container, p48/49 component 4a, p49/50 component 4b.
- Database: cover, p9 Table 1, p12/13 ERD, p31/42 appendix, p41/64 hardware boundary.
- SRS: Student Management base cover vs FITAI/DBCAS SRS cover; base content page vs SRS content page.

Diagram pairs are in `before-after/diagrams/`:

- Proposal image 3 (logical), image 4 (pipeline).
- Architecture image 1 (use case), image 3 (container), image 4 (component 4a), image 5 (component 4b).

## Layout checks

- Proposal: edited paragraphs reflow within the same text column; no overlap. Page 11 continues the same paragraph; Table 1 remains intact.
- Architecture: edited paragraphs/table cells reflow; no overlap. Use-case/container/component figures keep their original position/size; text labels fit.
- Database: A.1–A.26 use the cloned 6-column grammar, dark header, same widths; no cell overflow except `UNIQUE` wrapping in the Key column of A.26, which is legible. Hardware section follows A.26.
- SRS: cover fits inside its border in Word; body tables fit; no overlap.

## Not changed

- Covers of the three existing docs: byte-level text/run/table equality verified by `style-audit.json`.
- Styles, fonts, sizes, colors, page setup and headers/footers: C14N equality verified.
- Architecture Fig 7/8 and Database Fig 1/2 (41-card core/legend) remain unchanged as **OWNER-DECISION**; expanding them to 67 cards requires new layout/pages.

Evidence: `style-audit.json/.md`, `fact-audit.json/.md`, `before/` and `after/` PDFs/pages.

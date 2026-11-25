# Visual QA report (Phase 6)

Date 2026-11-25. Method required by the master task: render every final DOCX to
PDF, rasterise every page, and actually look at the pages — not merely parse XML
or count PDF pages.

## 1. Tooling and artefacts

- Word 16.0 COM with TOC/field update, repagination and `ExportAsFixedFormat`;
  all five PDFs regenerated from the final DOCX after the edits.
- PyMuPDF 1.28.2 for rasterisation and text extraction; Pillow 12.2.0 for sheets.
- Contact sheets (6 labelled pages each): `qa/contact-sheets/` — 20 sheets,
  regenerated **after** the final render.
- Full-size pages: `qa/full-*.png`, `qa/crop-signature.png`.
- Extracted embedded figures: `qa/figures/`.
- FITAI reference pages for comparison: `qa/fitai/`.
- Structural evidence: `qa/text/` (full text of all five documents).

## 2. Pre-revision inspection (baseline)

Covers, front matter, TOCs, table-heavy pages, figure pages and final pages of
all five documents were viewed. Findings are recorded in `defect-report.md`:
header/footer pattern drift (M1), cover title/signature detail (M2), unreadable
legacy Gantt (M3), mixed figure grammars (M4), small figure display sizes (M5).
Positive findings retained: no empty pages, correct sequential page numbering,
consistent gray table heads, readable captions, working TOC fields, clean covers.

## 3. Corrections applied and re-inspection

| Check | Result after revision |
|---|---|
| All five PDFs regenerated with refreshed TOC and fields | Yes; Word page counts 20 / 22 / 40 / 12 / 13 match PyMuPDF counts |
| `Page N` footer | Extracted from every body page; stale `Page 1 of 1` cache resolved on export |
| Empty / near-empty pages | None in any document (script check: `near-empty pages: []` for all five) |
| Header | `C1SE.70 · DBCAS` + `International School Capstone 1 - 2026`, bold italic, hairline rule — viewed on all sheets |
| Cover | 20 pt title, frame and logo intact; signature labels aligned; horizontal signature rules remain a residual detail (see §5) |
| Gantt figure (Proposal p15) | Recreated from editable SVG in the FITAI palette; viewed full size and in contact sheet; no clipped or overlapping text; markedly more legible |
| Captions | 13 pt italic; viewed on Proposal, Architecture and Database pages |
| ERD sheets | Retained; no cropping or distortion observed on Database sheets 1/6/9/10 |
| Code blocks | Consolas blocks on Code Standards p5 and Architecture p18 remain inside the text column |
| Final pages / references | Present in all five; Proposal References on p18, Technical Report References on p13 |

Page-by-page coverage: every page of all five documents was rasterised into the
20 labelled contact sheets and reviewed sheet by sheet; covers, TOC pages,
table-heavy pages, all figure pages and final pages were additionally opened at
full size. Total: 107 pages reviewed.

## 4. Residual deviations

1. **Cover signature rules** are specified in OOXML (`w:pBdr/w:bottom`) and survive
   in the delivered DOCX, but Word does not paint the rule under those two cover
   paragraphs in this template. The labels and alignment are correct. Recorded
   as a **minor** residual deviation; changing the cover construction would risk
   the approved frame and logo layout.
2. **Figure grammars** remain three families (monochrome sans, monochrome serif,
   generated navy/light-blue ERD) because they come from different editable
   sources. No content was force-redrawn to fake uniformity.
3. **Table text** remains 9–11 pt in dense tables (FITAI inherits 13 pt); reducing
   the 67-table dictionary to 9 pt is a deliberate printability deviation.
4. Owner placeholders remain for approvals, public URL and capacity acceptance.

## 5. Critical/major defect resolution

Every item rated critical (C1–C5) and major (M1–M5) in `defect-report.md` was
resolved except the signature-rule portion of M2, which is explicitly recorded
above. No clipped image, broken table, empty page, wrong page number or
unreadable recreated figure remains in the reviewed pages.

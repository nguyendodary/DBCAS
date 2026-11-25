# DBCAS document design specification — FITAI-derived, evidence-based

This specification replaces the previous `docs/agent/freeze-logs/doc-style-spec.md`
as the authoritative design reference. Every "FITAI" value below was measured
directly from `FITAI - Documents/` by the independent visual audit
(`fitai-visual-audit.md`); every "applied" value was verified in the delivered
DOCX and PDFs.

## 1. What FITAI actually is

FITAI is a **family**, not one template. Three Office theme families coexist
(`dk2` `#44546A` with accent1 `#4472C4` in Architecture/Proposal/Plan; Database
swaps accent1 `#5B9BD5` and accent5 `#4472C4`; Code Standard `dk2` `#0E2841`;
TechStack/TestPlan `dk2` `#1F497D`). Visible text is overwhelmingly black on
white with neutral-gray fills (`E7E6E6`, `D0CECE`, `BFBFBF`). The accents are
mostly latent theme values, not body colour.

Genuinely transferable traits (measured in multiple files):

- A4-ish page geometry; Times New Roman body, typically 13 pt (Proposal is 12 pt).
- Body-size headings: H1 and H2 are **the same 13 pt as body**, distinguished by
  bold, numbering and spacing. Architecture H3 is 12 pt Calibri `#1F3863`.
- Caption paragraphs render at **13 pt** even where the Caption style is 9 pt.
- Running head is plain or two-cell, **bold italic black**, 11–13 pt; the hairline
  rule is 0.5 pt (`w:sz=4`) and is commonly in the footer.
- Footer is italic `C1SE.56` plus plain `Page N`; `NUMPAGES` appears in only 2 of
  14 files, so "Page X of Y" is an exception, not the pattern.
- Numbered captions with `TOC`/`SEQ` fields; centred figures with generous white space.
- Monochrome hairline diagrams with serif labels and a legend; no unified icon system.
- Two framed cover families with the 454×134 / 420×124 px DTU mark at 5.0–5.2 cm
  width; cover document/project titles are 20 pt ("Capstone Project 1" 28 pt in
  family B); signature blocks use horizontal rules.

## 2. Applied DBCAS design system

### 2.1 Global document styles

| Property | Applied value | FITAI basis / deviation |
|---|---|---|
| Page | A4 21.0 × 29.7 cm | FITAI mainstream |
| Margins | L 3.5, R 2, T 2, B 2 cm | **Deviation**: DBCAS house value; FITAI varies 1.5–3.5 cm and Architecture uses 3.0 cm |
| Body | Times New Roman 13 pt, 1.5 line, justified, 6 pt after | Font/size from FITAI; 1.5 spacing from FITAI CodeStandard/TestPlan |
| Heading 1 | 13 pt bold, `#1F3863`, numbered `1.` | Size now matches FITAI; colour from FITAI Architecture H3 |
| Heading 2 | 13 pt bold, `#44546A`, numbered `1.1.` | Size matches FITAI; colour from FITAI theme `dk2` |
| Caption | 13 pt italic, centred, `#44546A` | Matches rendered FITAI captions |
| Table head | 11 pt bold on `#D9D9D9`; borders `#BFBFBF` 0.5 pt | **Deviation**: FITAI uses 13 pt inherited table text and `E7E6E6`/`D0CECE`/`BFBFBF`; reduced sizes keep the 67-table dictionary printable |
| Code | Consolas 9 pt | **Deviation**: FITAI Code Standard defines an unused Courier New 10 pt style |
| Header | 12 pt bold italic black: left `C1SE.70 · DBCAS`, right `International School Capstone 1 - 2026`; hairline rule | FITAI bold-italic running head pattern; 12 pt within the measured 11–13 pt range |
| Footer | 12 pt bold italic: left `C1SE.70 · DBCAS · <document>`, right `Page N` (`PAGE` field) | FITAI `C1SE.56` / `Page N` pattern; stale codes removed |
| Cover | Framed, logo 454×134 px, 20 pt document title, 13 pt team/signature lines | FITAI family A/B; 26 pt previous title removed |

### 2.2 Section-specific styles

- **Cover section**: no header/footer, single frame, university mark, school
  labels in `#4472C4`, project identity, five member lines, review-panel and
  mentor signature blocks. Approval decisions remain owner-owned placeholders.
- **Front matter**: project information, document information, approvals,
  revision history, automatic TOC — the seven-block FITAI Architecture pattern
  condensed to five blocks appropriate to a technical submission.
- **Body**: numbered H1/H2, 13 pt justified prose, inline tables with centred
  13 pt captions, figures centred with captions below.
- **Database dictionary**: 67 `Heading 3` blocks, one 9 pt table per table —
  the only deliberate small-text exception, required for printability.

### 2.3 Figure and diagram styles

- Palette: ink `#000000`, navy `#1F3863`, accent `#4472C4`, light fill
  `#D9E2F3`, rule `#44546A`, milestone `#ED7D31`, caption `#44546A`.
- Line art: hairline-to-2 px strokes, rounded boxes for tasks, diamonds for
  gates, centred placement, numbered captions beneath.
- Existing source families (monochrome sans, monochrome serif, generated
  navy/light-blue ERD) are retained; they are not force-redrawn.
- The recreated Gantt has an editable SVG source at
  `docs/submission/final/assets/gantt-roadmap.svg`.

### 2.4 Table-specific styles

- Header row bold on light gray; body regular; 0.5 pt neutral borders.
- Dense tables use 10 pt; the 67-table column dictionary uses 9 pt.
- Caption above the table, centred, italic.

## 3. Deviations explicitly recorded

| Deviation | Reason |
|---|---|
| 3.5 cm left margin | DBCAS house/owner value retained |
| 13 pt H1/H2 with colour | Size aligned to FITAI; colour adds hierarchy for a five-document technical set |
| 9/10/11 pt table text | Printability of the 67-table dictionary and dense traceability tables |
| Consolas 9 pt code | No usable FITAI monospace style in the measured files |
| Cover signature rules rendered inconsistently by Word in this template | Residual minor deviation; text labels are present and aligned |

## 4. Verification

`docs:verify-word` enforces A4, 3.5/2/2/2 margins, TNR 13 pt body at 1.5 spacing,
core metadata, TOC and `PAGE` fields. All five documents pass 149/149 after the
revision. Rendered PDFs and contact sheets are in
`docs/submission/final/rendered/` and `recovery/qa/contact-sheets/`.

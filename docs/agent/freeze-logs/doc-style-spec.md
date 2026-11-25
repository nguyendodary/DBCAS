# Phase 5 — FITAI reference style specification

Reference inspection: 2026-11-25. The source documents are the FITAI Proposal
v1.2, Architecture v1.1, Database v1.2, User Story v1.1, and the separately
supplied SRS template. Measurements below come from their OOXML style, theme,
document and header/footer parts; [raw extraction](phase5-fitaistyle-raw.log)
records the underlying values. Reference PDF covers and front matter were also
rendered and inspected. A dash in the raw data means “not explicitly set”;
inherited or theme-based values must not be treated as missing or guessed.
The [source inventory](phase5-source-inventory.log) records hashes, structural
counts and headings for the existing DBCAS documents and text sources; it is an
inventory, not a completed fact or traceability audit.

## Measured tokens

| Property | Proposal / Architecture / User Story | Database | SRS template |
|---|---|---|---|
| Page size, twips | 11907 × 16840 | 11920 × 16860 | 12240 × 15840 |
| Margins, top / bottom / left / right, twips | 1134 / 1418 / 1701 / 1134 | 1701 / 1701 / 1985 / 1134 | 1440 / 1440 / 851 / 616 |
| Default or Normal font | Times New Roman (document default) | Times New Roman (Normal) | Times New Roman (Normal); most explicitly formatted runs are Arial |
| Normal size | Proposal 12 pt; User Story 13 pt; Architecture inherits document default 13 pt | 13 pt | 12 pt (Normal); most explicit runs 10 pt |
| Heading 1 / 2 | Proposal 13 / 13 pt; Architecture inherits 13 pt | 13 / 13 pt, black | 14 / 13 pt with theme-accent colors |
| Title style | 14 pt where explicitly set | Not present in the extracted matching styles | Uses template styles and direct formatting |
| Caption style | Proposal 13 pt; Architecture inherits; both have 200-twip space after | 9 pt, theme `text2` / `#44546A`, 200-twip space after | No matching caption style found by the extractor |
| Table fills seen in document XML | `#FFFFFF`, `#D0CECE`, `#E7E6E6`, `#D9D9D9`, `#F3F3F3`, `#BFBFBF` | `#BFBFBF`, `#D9D9D9` | `#BFBFBF`, `#D3DFFF`, black and automatic fills |
| Main explicit run colors | `#000000`; occasional `#4472C4` and `#201F35` | `#000000`, `#00000A`, `#4472C4` and automatic | Red and blue instructional markup also occurs; it is not project content |

The FITAI Word theme declares `dk1 #000000`, `lt1 #FFFFFF`, `dk2 #44546A`,
`lt2 #E7E6E6`, accents `#4472C4`, `#ED7D31`, `#A5A5A5`, `#FFC000`,
`#5B9BD5`, `#70AD47`, hyperlink `#0563C1`, and followed hyperlink `#954F72`.
These are theme definitions, not evidence that every accent is used visibly.
The logo is an embedded image with antialiasing; no single logo-red hex value
was declared by the OOXML extraction.

## Reference layout

- Covers have the university logo, blue school label, a black page frame,
  centered project/course and document titles, version, date, project name,
  author block, and signature lines. FITAI's names, dates, approvals and roles
  are examples and must not be copied as DBCAS facts.
- Front matter includes project information, a document-information table,
  optional approval/signature page, revision history, and an automatic table of
  contents. The document-information header uses gray fill and black borders;
  the revision-history columns include version, date, description and author,
  though their order differs across FITAI files.
- Running headers show the document name at left and the school/capstone label
  at right with a horizontal rule; the Database/Architecture sample also has a
  dark accent tab. Footers use a group identifier and Word `PAGE` field.
- The samples contain Word `TOC`, `SEQ Figure`, and `SEQ Table` fields rather
  than only static text. Captions, table numbering and references should remain
  updateable and their rendered page numbers checked.

## Consistent DBCAS interpretation

The FITAI files differ in margins, point sizes, table grays and front-matter
ordering. For the four new DBCAS files, use the common Proposal/Architecture
A4 geometry and Times New Roman as the shared baseline, black text, subdued
gray table headings and the existing university logo. Use 13 pt body text
where layout permits, preserving smaller readable table/caption text when
needed. Keep actual OOXML values traceable to the source table above; do not
describe the selected common geometry as identical to the Database sample.

Set group `C1SE.70`, project `DBCAS`, version `ver1.3`, and creator plus last
modified by `Do, Nguyen Quoc` consistently. Use only verified DBCAS metadata;
unknown schedule, roles and approvals must be listed for the owner, not
invented. Write the new files in a separate output directory and do not
overwrite the source documents.

## Rendering note

Poppler and LibreOffice were not found on PATH, in WSL, or in the checked
default Windows install locations. The repository's existing Windows PDF
renderer was used to inspect the supplied reference PDFs; no dependency was
installed. The required final Word render-and-visual-verify gate is still
pending, and this reference inspection is not evidence that the new documents
have been created or verified.

# FITAI reference style and the DBCAS ver1.3 interpretation

Updated 2026-11-25 after reading every file in `FITAI - Documents` (14 DOCX,
15 PDF, 2 XLSX). No file was unreadable; one embedded JPEG-XR preview
(`hdphoto1.wdp` in the Database DOCX) cannot be decoded by PIL, which affects
no visible pixel. The full per-file measurements are in
`_review/owner-docs-20261125/fitai-survey.md`; this file records the decisions
the generator implements.

## 1. What the FITAI set actually contains

| Property | Measured range across the 14 DOCX |
|---|---|
| Page size | Three "A4" widths coexist: 11906/11907 tw (21.00 × 29.70 cm), 11904 tw, 11920 × 16860 tw (21.03 × 29.74 cm); two files are US Letter 12240 × 15840 |
| Margins | From 851 tw to 1985 tw; the Architecture file is the only one with A4 + left 1701 tw (3.00 cm) |
| Body font | Times New Roman 13 pt is the mainstream family; Arial 11 pt (Reflection, FitnessAI), Open Sans 11 pt brown `695D46` (TechStack, TestPlan), Calibri 11 pt (SprintBacklog) |
| Body spacing | Single, 1.15× and 1.5× all occur; CodeStandard and TestPlan use 1.5× |
| Heading 1 / 2 | Proposal, ProjectPlan, ProductBacklog, UserStory, UI and Architecture use **13 pt bold** (no size step above body); CodeStandard H1/H2 are bold with no size at all; Meeting uses 20/16 pt `0F4761`; TechStack uses 18/16 pt orange/teal |
| Title | 14 pt bold centred in the mainstream family; 36 pt in CodeStandard/Reflection/FitnessAI |
| Caption | 9 pt `44546A` in Database and ProjectPlan; 13 pt in Proposal and UserStory (szCs only); absent in CodeStandard, FitnessAI and others |
| Table heads | `D9D9D9`, `E7E6E6`, `D0CECE`, `BFBFBF`; the Database file uses `BFBFBF` on 113 head cells with 0.5 pt auto borders |
| Theme | `dk1 #000000`, `lt1 #FFFFFF`, `dk2 #44546A`, `lt2 #E7E6E6`, accent1 `#4472C4`, accent2 `#ED7D31`, accent3 `#A5A5A5`, accent4 `#FFC000`, accent5 `#5B9BD5`, accent6 `#70AD47`, hyperlink `#0563C1` |
| Covers | Two families: A (stacked text, logo 454 × 134 px at 5.24 × 1.55 cm, signature line shapes) and B (framed box 17.5–18.4 × 25.6–27.7 cm, logo 420 × 124 px) |
| Front matter | Project information, document information, approvals (4 files only), revision history, TOC field; Architecture has all seven blocks |
| Header/footer | Text headers with a rule; 12 of 14 have a working `PAGE` field, several have stale project codes (`C1SE.03`, `C1SE.56`, "2024") |

Two conclusions follow. First, "FITAI style" is a family, not a single
specification: no two files agree on margins, and heading sizes are mostly the
body size. Second, the DBCAS house style that the previous versions already
used (A4, H1 18 pt) is *not* a FITAI file, so adopting FITAI is a format change,
made deliberately here and recorded below.

## 2. Template decision

`5. Architecture Design Document/C1SE.56_ArchitectureDesign_SHFA_ver1.1.docx`
is the single best base: exact A4 21.00 × 29.70 cm, Times New Roman 13 pt in
`docDefaults`, Title plus three heading levels with `outlineLvl`, the complete
seven-block front matter with an approvals page, a style-based TOC, a header
built as a two-cell table with a 0.75 pt rule, a working `PAGE` footer from page
two, and landscape sections for wide figures. The Database file is the better
*content* model for a schema document (automatic numbering, 9 pt captions,
`BFBFBF` heads) but its geometry and missing Title style disqualify it as the
shared base. The Code Standard file has no usable format base (H1/H2 are body
size, no caption, no monospace style), so Code Standards clones the Architecture
base and takes only its rule-list *content* pattern. The Technical Report uses
the same base because the set contains no report template.

The documents are **generated**, not cloned: cloning would inherit 39 one-off
table styles, duplicate TOC fields and stale running heads that the survey
found in the base file. `scripts/submission_style.py` implements the measured
FITAI values that matter and nothing else.

## 3. The applied specification

| Property | Value | Source of the decision |
|---|---|---|
| Page | A4, 21.0 × 29.7 cm | FITAI mainstream geometry |
| Margins | left 3.5 cm, top 2 cm, bottom 2 cm, right 2 cm | Owner requirement; left 3.5 cm equals the FITAI Database cover margin |
| Body | Times New Roman 13 pt, line spacing 1.5, justified, 6 pt after | FITAI mainstream font and size; 1.5× as in CodeStandard/TestPlan |
| Heading 1 | 18 pt bold `#1F3863`, 18 pt before, 8 pt after | FITAI Architecture Heading 3 colour `1F3863`; 18 pt keeps a hierarchy above 13 pt body and matches the DBCAS house H1 |
| Heading 2 | 14 pt bold `#44546A` | FITAI theme `dk2` |
| Heading 3 | 13 pt bold black | FITAI body-size heading convention |
| Caption | 9 pt italic `#44546A`, centred | FITAI Database caption style |
| Tables | header row 11 pt bold on `#D9D9D9`, body 11 pt, borders `#BFBFBF` 0.5 pt; dense requirement/registry tables 10 pt; the 67-block column dictionary 9 pt | FITAI table fills; smaller sizes only where the survey shows them |
| Code | Consolas 9 pt, left indent 0.5 cm, single spacing | No FITAI monospace style exists; 9 pt matches the caption step |
| Header | left `C1SE.70 · DBCAS`, right document name, 9 pt `#44546A`, 1 pt rule | FITAI header pattern |
| Footer | left `C1SE.70 · DBCAS · <document>`, right `Page X of Y` from `PAGE`/`NUMPAGES` fields | FITAI footer pattern, stale codes removed |
| Cover | page frame, university logo, blue school labels `#4472C4`, 26 pt title, version, date, project title, five member lines, signature block | FITAI cover family A |
| Front matter | project information, document information, approvals with an explicit pending status, revision history, automatic TOC | FITAI Architecture's seven blocks |
| Metadata | author and last modified by `Do, Nguyen Quoc`, group `C1SE.70`, project `DBCAS`, version `ver1.3` | Owner requirement |

### Documented size exceptions

Only these elements depart from 13 pt, and the verifier lists each one with its
run count:

1. Cover labels, team lines and signature lines: 11–26 pt.
2. Front-matter labels and the "Submitted by" line: 12 pt bold.
3. Table text: 11 pt, or 10 pt in the dense feature, requirement, constraint,
   risk, registry and migration tables, or 9 pt in the 67-table column
   dictionary and the experiment table.
4. Figure and table captions: 9 pt italic.
5. Code blocks: Consolas 9 pt.
6. Header and footer: 9 pt.
7. Table of contents entries as produced by Word.

Everything else — every paragraph in the body flow — is 13 pt at 1.5 line
spacing. `npm run docs:verify-word` fails if a body run is not 13 pt, if a body
paragraph is not 1.5, if a section is not A4 with 3.5/2/2/2 cm margins, or if
the author metadata differs.

## 4. Rendering and verification

Word 16.0 is used to update the TOC and every field, save the DOCX, export the
PDF and report the page count (`scripts/finalize_submission_docs.py`). Word
rewrites `cp:lastModifiedBy` to the Windows account name on save, so the script
restores the required metadata afterwards. LibreOffice and Poppler are not
installed; the PDF page images are produced with PyMuPDF from the Word exports.
The rendered PDFs and every page image are inspected as contact sheets and at
full size for covers, TOC, table pages and figure pages.

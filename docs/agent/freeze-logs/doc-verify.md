# ver1.3 submission document verification (2026-11-25)

Five Word deliverables were generated from one generator, finalised in Word 16.0,
rendered to PDF, inspected page by page, and checked by an XML-reading script.
The SRS is no longer part of the owner's set: the file was archived to
`Documents/Archive/C1SE.70_SRS_DBCAS_ver1.3.docx`, removed from
`Documents/Final-ver1.3`, and every generator, manifest, npm script and matrix
that produced it was removed or repointed.

## 1. Files and page counts

| Document | File | Word pages | PDF pages | Words |
|---|---|---:|---:|---:|
| Proposal | `C1SE.70_ProposalDocument_DBCAS_ver1.3.docx` | 20 | 20 | 4 141 |
| Architecture Design | `C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx` | 22 | 22 | 4 218 |
| Database Design | `C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx` | 39 | 39 | 5 988 |
| Code Standards | `C1SE.70_CodeStandards_DBCAS_ver1.3.docx` | 12 | 12 | 2 209 |
| Technical Report | `C1SE.70_TechnicalReport_DBCAS_ver1.3.docx` | 13 | 13 | 2 843 |

Word page counts come from `ComputeStatistics(2)` after the fields were updated;
PDF page counts come from PyMuPDF on the Word export
(`docs/submission/final/verification/page-counts.json`). Word and PDF agree for
all five files. The previous set was 61 / 78 / 72 / 9 pages plus an SRS; the new
set is 106 pages in total and covers one more document (Code Standards) and a
new Technical Report.

## 2. Visual inspection

Every page of every file was rendered at 100 dpi and reviewed as labelled
contact sheets (20 pages per sheet); covers, tables of contents, table-heavy
pages, figure pages and final pages were additionally opened at full size
(≈830 × 1170 px).

| Document | Sheets | Full-size pages checked | Result |
|---|---:|---|---|
| Proposal | 1 | cover, front matter, TOC, Gantt page, context/logical figures | Cover frame, blue school labels, 26 pt title, TOC with page numbers, 19 tables (front matter included) and 4 figures render correctly |
| Architecture | 2 | cover, TOC, algorithm pages, pipeline and module figures | Figures keep their captions; code blocks stay inside the text column |
| Database | 2 | cover, ERD sheets 1/6/9/10, registry, dictionary pages (78 tables in total) | ERD sheets are cropped to their content; every dictionary table repeats its header across pages |
| Code Standards | 1 | cover, TOC, code sample page | Code samples are monospaced 9 pt and do not overflow |
| Technical Report | 1 | cover, abstract, experiment table, references | References use a hanging indent; the experiment table fits the text width |

Colours are the measured FITAI palette: accent `#4472C4` on the cover, headings
`#1F3863` and `#44546A`, table heads `#D9D9D9`, rules `#BFBFBF`, body black.
No page shows clipped text, an empty page body, a missing caption or a broken
table header.

## 3. XML-reading checks

`scripts/verify_submission_docs.py` opens each DOCX package and checks its document structure and styles. Result: **5 documents, 149 assertions, 0
failures**.

| Check | Result |
|---|---|
| File set and names | Five expected files, no extra DOCX in the directory |
| Page size | A4 21.0 × 29.7 cm in every section |
| Margins | 3.5 cm left, 2 cm right, 2 cm top, 2 cm bottom in every section |
| Normal style | Times New Roman, 13 pt, line spacing 1.5 |
| Body runs | Every body run 13 pt; every body paragraph 1.5 |
| Core properties | author and last modified by `Do, Nguyen Quoc` |
| Fields | TOC field present; `PAGE` field present in the footer |
| Header/footer | `C1SE.70` in the header of every section |

A separate recovery check followed the XML ancestry and inherited styles of
all 252 nonempty body paragraphs in Normal or List Bullet style outside table
cells. All 282 text runs resolved to 13 pt and all 252 paragraphs to 1.5 spacing.
The verifier produces different exception counts across processes because it
uses temporary XML wrapper identities to identify table membership. Use the
independent check for body formatting and the style specification for table
formatting.

### Documented formatting exceptions

| Element | Size |
|---|---|
| Cover labels, team lines, signature lines | 26 / 13 / 12 / 11 pt |
| Front-matter labels and "Submitted by" | 12 pt bold |
| Table text | 11 pt; 10 pt in dense feature, requirement, constraint, risk, registry and migration tables; 9 pt in the 67-table column dictionary and the experiment table |
| Captions | 9 pt italic |
| Code blocks | Consolas 9 pt |
| Header and footer | 9 pt |

## 4. Number comparison

The table combines repository measurements with dated results from the freeze logs.

| Claim | Measured | Source |
|---|---:|---|
| Application tables | 67 | PostgreSQL 17.12 introspection after 28 migrations |
| Columns | 561 | same |
| Foreign keys | 122 | same |
| Indexes | 159 | same |
| Migrations | 28 | `db/migrations/*.sql` |
| API paths | 106 | `app.openapi()` |
| API operations | 118 | same |
| Backend tests | 1 940 passed, 7 skipped | `pytest -q`, re-run 2026-11-25 (24 min 22 s) |
| Frontend unit tests | 54 files / 463 tests | `vitest` |
| Browser tests | 152 passed, 4 skipped | sharded Playwright/QA runs |
| Secret scan | Whole tree (3 129 files in the pre-recovery run), 0 findings | `npm run secrets:scan` |

The live database reports 68 tables and 564 columns because it also holds
`schema_migration`; the documents state this exclusion explicitly instead of
quoting the smaller number as if it were the whole database.

## 5. Obsolete terms and SRS

The sweep searched every one of the five documents for `OpenRouter`,
`free model`, `66 tables`, `27 migrations`, `1-20 questions`,
`five destinations`, `OWNER UNKNOWN` and `SRS`: **zero occurrences**.
The old `OWNER UNKNOWN` placeholder is replaced by explicit
`[OWNER TO PROVIDE: ...]` fields, and no document mentions the SRS at all.

## 6. Traceability

`docs/submission/final/TRACEABILITY.md` is generated by the same script:

- 15 of 15 Proposal sections are present, in the required order, as Heading 1.
- 16 of 16 functional requirements appear in both the Proposal and the
  Architecture document; no orphan `FR-xx` exists in either.
- 67 of 67 schema tables have a dictionary block with the measured column count.
- No invented `*_id` column name appears in the Database document.
- The seven key features map to the requirement table and to the architecture
  sections.

## 7. Gates

| Gate | Command | Result |
|---|---|---|
| Documentation gate | `npm run docs:check` | PASS, exit 0 (48 assertions, 67 tables / 561 columns / 122 FKs / 159 indexes / 28 migrations) |
| Submission documents | `npm run docs:verify-word` | PASS, exit 0 (5 documents, 149 assertions, 0 failures) |
| Route inventory | `npm run inventory:check` | PASS, exit 0 |
| Secret scan | `npm run secrets:scan` | PASS, whole tree (3 129 files), 0 findings |
| Clean clone | `npm ci` + `npm run env:check` + `npm start` + `/readiness` | PASS, exit 0; readiness reports database true and sandbox true (`verification/clean-clone.log`) |

## 8. Owner questions raised by this verification

1. Student IDs, emails and roles are taken from the v1.2 covers; confirm they are
   still current, and confirm the official faculty/department name (the sources
   say both "CSE Center" and "Software Engineering Department").
2. The review-panel representative and all approval signatures/dates are empty.
3. No industry co-supervisor is recorded; confirm whether one is required.
4. Per-member effort allocation, story points and sprint-review attendance are
   not recorded anywhere.
5. The survey names seven products but documents only LeetCode; provide a date,
   method and one citation per surveyed product.
6. Reference access dates, and whether the Gemini paper should stay when no
   vendor is named in the survey.
7. The public document URL and any public demo URL are still absent.
8. Whether the legacy `assessment*` tables and the `schema_migration` exclusion
   policy are acceptable as documented.

## 9. Not verified

- The two-stage AI audit and the writable DML path were not re-executed for this
  document set; the numbers quoted come from the freeze logs, not from a new run.
- No learner study, usability test or provider-retention decision exists.
- LibreOffice and Poppler are not installed, so PDF page evidence comes only from
  the Word export.

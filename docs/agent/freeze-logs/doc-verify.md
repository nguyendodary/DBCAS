# ver1.3 submission document verification (2026-11-26)

This is the current verification record for the five owner documents. The
2026-11-25 record described the condensed generated set (20/22/40/12/13 pages);
that set was rejected and is preserved byte-for-byte in
`Archive/rejected-final-20261126/`. The submission set now consists of in-place
revisions of the content-complete baseline (Proposal, Architecture, Database)
and the best surviving DBCAS Code Standards and Technical Report.

## 1. Files and page counts

| Document | File | Baseline pages | Final pages | Change |
|---|---|---:|---:|---:|
| Proposal | `C1SE.70_ProposalDocument_DBCAS_ver1.3.docx` | 61 | 62 | +1 |
| Architecture Design | `C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx` | 78 | 79 | +1 |
| Database Design | `C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx` | 72 | 75 | +3 |
| Code Standards | `C1SE.70_CodeStandards_DBCAS_ver1.3.docx` | 12 | 14 | +2 |
| Technical Report | `C1SE.70_TechnicalReport_DBCAS_ver1.3.docx` | 13 | 15 | +2 |
| **Total** | | **236** | **245** | **+9** |

Page counts are from Word (`ComputeStatistics(2)`) and agree with PyMuPDF on the
exported PDFs. The deltas are explained: each document gains two uniform
appendices (owner decisions, figure sources); the Proposal gains the explicit
Mode 1/Mode 2 paragraph; Architecture/Database replace 13 low-detail ERD/TRD
pages with 13 rebuilt ERD/ledger pages and reflow their 11 pt captions; Code
Standards gains a legible layering figure and the appendices; the Technical
Report gains the appendices. No baseline section was deleted to shorten a
document.

## 2. Visual inspection

The five PDFs were rendered with Word 16.0 and checked by script for every page
(`verification/pdf-checks.json`): **0 near-empty pages and 0 pages with body
text or images outside the 3.5/2/2/2 cm margins**. The following pages were
also opened at full size and inspected:

| Document | Page | What was checked | Result |
|---|---:|---|---|
| Architecture | 5 | Table of Contents | Entries, dot leaders and page numbers fit; no overflow |
| Architecture | 8 | List of Figures | 20 entries, correct titles and pages, no clipping |
| Architecture | 60 | Landscape ERD overview | Header/footer, 20.5 cm figure, 11 pt caption, legible labels |
| Database | 22 | Landscape module ERD | Image title and caption both `(2/11)`; key columns legible; no overflow |
| Proposal | 43 | Gantt roadmap page | 13 dated rows; final submission before defence; caption and image agree |

Code Standards' new layering figure is 15.2 × 6.99 cm and the page passes the
same scripted overflow/empty-page checks; Technical Report Figure 1 is the
unchanged shared pipeline figure. No page shows clipped text, a missing caption,
a broken table header, or an empty body.

The ERD set is generated from `docs/diagrams/schema-028/schema-introspection.json`:
67 tables, 561 columns, 122 foreign keys, 159 indexes, 28 migrations. The
document has an overview page, an index page, seven module ERDs with
intra-module relationship lines, and four ledgers that enumerate every foreign
key with cardinality and delete/update rules. The full column dictionary remains
in §3 and Appendix A, so the ERD cards show keys only and stay legible.

## 3. XML-reading checks

`scripts/verify_submission_docs.py` opens each DOCX package and checks its
structure and styles. Result: **5 documents, 148 assertions, 0 failures**.

| Check | Result |
|---|---|
| File set and names | Five expected files; no extra DOCX in the final directory |
| Page size | A4 21.0 × 29.7 cm portrait or 29.7 × 21.0 cm landscape in every section |
| Margins | 3.5 cm left; 2 cm right, top and bottom in every section |
| Normal style | Times New Roman, 13 pt, line spacing 1.5 (direct style properties) |
| Body runs | Every body run 13 pt; every body paragraph 1.5 (cover/front matter, captions, tables, code and TOC are documented exceptions) |
| Core properties | author and last modified by `Do, Nguyen Quoc` |
| Fields | TOC field present; `PAGE`/`NUMPAGES` fields present in the footer |
| Header/footer | `C1SE.70 · DBCAS` left, `International School Capstone 1 – 2026` right; author left and page right in the footer |
| Metadata | group C1SE.70, project DBCAS, version ver1.3, date 26/11/2026 |

### Documented formatting exceptions

| Element | Size |
|---|---|
| Cover labels, team lines, signature lines | 11–20 pt |
| Front-matter labels and "Submitted by" | 12 pt bold |
| Table text | 11 pt; 10 pt in dense tables; 9 pt in the column dictionary and experiment table |
| Appendix owner/source tables | 8.5 pt |
| Figure and table captions | 11 pt italic, centred |
| Code blocks | Consolas 9 pt |
| Header and footer | 9 pt |
| TOC / List of Tables / List of Figures | as produced by Word, aligned from the rendered PDF |

## 4. Number comparison

| Claim | Measured | Source |
|---|---:|---|
| Application tables | 67 | PostgreSQL 17.12 introspection after migration 028 |
| Columns | 561 | same |
| Foreign keys | 122 | same |
| Indexes | 159 (67 primary-key + 50 unique + 42 standalone) | same; the breakdown sums to 159 |
| Migrations | 28 | `db/migrations/*.sql` |
| API paths / operations | 106 / 118 | `app.openapi()` and `docs/openapi.json` |
| Backend tests | 1 940 passed, 7 skipped in 23:54 | `docs/agent/freeze-logs/backend-pytest-final.log:35` |
| Frontend unit tests | 54 files, 463 tests | `docs/agent/freeze-logs/frontend-test.log:16-17` |
| Browser tests | 152 passed (11 + 72 + 12 + 3 + 54) | six baseline shard logs; no saved skip |
| Secret scan | Whole tree, 0 findings | `npm run secrets:scan` on 2026-11-26 (3 298 files at that run) |

The live database reports 68 tables and 564 columns because it also holds the
runtime `schema_migration` ledger; the documents state this exclusion.

## 5. Obsolete terms and SRS

The sweep searched all five documents for `OpenRouter`, `free model`,
`66 tables`, `27 migrations`, `1-20 questions`, `five destinations`,
`OWNER UNKNOWN`, `S. Ramírez`, `Table .` and `Figure .`: **zero occurrences**.
The old SRS deliverable line was removed from the Proposal; no document claims
an SRS exists.

## 6. Traceability

`docs/submission/final/TRACEABILITY.md` is generated by the same verifier:

- 15 of 15 Proposal sections are present, in the required order, as Heading 1
  (see `verification/proposal-sections.md`).
- 16 of 16 functional requirements appear in both the Proposal and the
  Architecture document; no orphan `FR-xx` exists in either.
- 67 of 67 schema tables have a dictionary block with the measured column count.
- No invented `*_id` column name appears in the Database document.
- The seven key features map to the requirement table and the architecture
  sections.

## 7. Gates

| Gate | Command | Result |
|---|---|---|
| Documentation gate | `npm run docs:check` | PASS, exit 0 (48 assertions; 67/561/122/159/28) |
| Submission documents | `npm run docs:verify-word` | PASS, exit 0 (5 documents, 148 assertions, 0 failures) |
| Route inventory | `npm run inventory:check` | PASS, exit 0 |
| Secret scan | `npm run secrets:scan` | PASS, whole tree, 0 findings |
| PDF geometry | `py scripts/verify_final_pdfs.py` | PASS; 0 near-empty, 0 overflow |
| TOC/list pages | `py scripts/check_toc.py` | PASS; 0 mismatches against printed footers |
| CI at the document commit | GitHub Actions `Local quality gate` | PASS, run `45679605273`, 14/14 jobs at `94bb39901d11f255ac12bde97bad8fb704e7658f` |

## 8. Owner questions raised by this verification

1. Confirm every student ID, email address and phone number (O1).
2. Confirm the official faculty/department name and whether an industry
   co-supervisor is required (O2).
3. Sign the approval table and supply the approval dates (O3).
4. Provide the public document URL, or confirm that the demo remains local (O4).
5. Confirm the survey date/method and add one citation per surveyed product (O5).
6. Confirm per-member effort allocation, story points and sprint attendance (O6).
7. Accept two concurrent SQL executions for the demonstration (O7).
8. Decide whether the legacy `assessment*` tables are dropped and confirm the
   retention period (O8).
9. Decide whether the classical use-case/component appendices are restored (O9).
10. Verify every reference URL/DOI and supply any missing source (O10).

The same ten items are listed in Appendix A of every document.

## 9. Not verified / limitations

- Word cannot update the TOC fields on this baseline without hanging (the
  global `Fields.Update()` path stalls). The DOCX is shipped with
  `updateFields` disabled; the TOC and both lists were aligned from the rendered
  PDF (0 mismatches). A future Word session may update them manually.
- The two-stage AI audit and the writable DML path were not re-executed for this
  document set; the numbers quoted come from the saved freeze logs.
- No learner study, usability test, provider-retention decision or public
  deployment exists. Production remains **HOLD**.
- LibreOffice/Poppler are not installed; PDF evidence comes from the Word export.
- CI for the new commit is recorded in the handover only after the push; see
  `STATUS.md` and the GitHub run link.

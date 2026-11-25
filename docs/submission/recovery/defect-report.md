# Phase 1 — Independent defect report on the five alleged final documents

Audit performed 2026-11-25 **before editing**. Targets: the five ver1.3 DOCX in
`docs/submission/final/` and their rendered PDFs in `docs/submission/final/rendered/`.
Method: python-docx structural extraction, full-text extraction, embedded-media
extraction, PyMuPDF rendering of every page to labelled contact sheets
(`qa/contact-sheets/`) and direct visual viewing of covers, front matter, figure
pages, table pages and full-size pages. Evidence paths are relative to
`docs/submission/recovery/`.

## 0. What the previous agent got right (verified, not assumed)

- All five DOCX open with python-docx; all five PDFs exist and render.
- A4 portrait, left 3.5 / right 2 / top 2 / bottom 2 cm margins and Times New
  Roman 13 pt body at 1.5 spacing are consistent across all five.
- Two sections per document: a cover section without header/footer, and a body
  section with a running header and a `PAGE`/`NUMPAGES` footer.
- **The footer fields are correct in the rendered PDFs**: actual `Page 3 of 20`
  … `Page 20 of 20` etc. were extracted from every page. The `Page 1 of 1`
  string in the verifier report is an unresolved *cached* field result in the
  DOCX, not a rendering defect. No near-empty page was found in any PDF.
- The measured schema numbers 67 tables / 561 columns / 122 FKs / 159 indexes /
  28 migrations, 106 OpenAPI paths / 118 operations, 67 ORM models, 13
  repositories, 1,700 i18n keys / 34 groups / zero drift, and 25+3 browser
  specs are all reproducible from source (see `implementation-audit.md`).
- `npm run docs:check` (48 assertions) and `npm run docs:verify-word` (149
  assertions, 0 failures) both pass at baseline.

## 1. Critical — factual and internal-consistency defects

| # | Document / page | Defect | Evidence | Required action |
|---|---|---|---|---|
| C1 | Database Design, §6 (PDF p35) | "68 are primary-key indexes, 41 back a unique constraint and 51 are standalone performance indexes" sums to **160**, but the document and the introspection both state **159** total. | `qa/text/…DatabaseDesign….txt` line 134; `docs/diagrams/schema-028/schema-introspection.json` classified by index definition: **67 PK, 50 unique, 42 standalone = 159** | Replace with the measured breakdown and make the sum explicit. |
| C2 | Architecture Design, §1.2 (PDF p6) | "8 router modules, 73 service modules" uses a file-counting convention that includes `__init__.py` and excludes the `broker/` and `llm/` service subpackages. | `backend/app/main.py:15,69-75` registers **7** routers; `backend/app/services/` has **72** top-level + 11 subpackage modules. `implementation-audit.md` §1 | State "7 registered routers (8 `.py` files including `__init__.py`)" and "72 top-level service modules (83 including `broker/` and `llm/`)" |
| C3 | Code Standards, §2 (PDF p5) | Same "routers/ (8 files), services/ (73 files)" convention drift. | Same evidence as C2 | Same correction, with the convention named. |
| C4 | Technical Report, Abstract / §5 Table 1 E4–E8 (PDF p5, p10) | Quantitative claims exceed saved evidence: "24 min 22 s" pytest duration (log says **23:54**), "152 passed, **4 skipped**" browser suites (no saved log contains skips), "**3,129 files**" secret scan (saved logs say **3,050** and **3,083**), "186 pairs, 0 failures" contrast and "1 042 commits" history scan are not tied to a saved log in this set. | `implementation-audit.md` §8 and `docs/agent/freeze-logs/{backend-pytest-final,baseline-e2e-*,final-secrets-tree,baseline-secrets-tree}.log` | Cite exact logs, drop unsupported figures, and attribute the 14/14 CI result to commit `d6df804` (not HEAD `66045b7`). |
| C5 | Proposal, §5 (PDF p8) and §7 (PDF p12) | "publishes a result only after deterministic scoring or human verification" conflicts with FR-12 and the implementation: fixed-test sessions publish an AI-official V1 at finalize; practice/legacy sessions require administrator review; `HUMAN_VERIFIED` is a stored release-policy value, not a UI choice. | Proposal text line 70 vs line 234; `backend/app/services/result_version.py:35-54`, `grading_review.py:23-86`; v1.2 academic README §25–39 | Rewrite to state the two actual publication paths. |
## 2. Major — visual / FITAI-fidelity defects

| # | Document / page | Defect | Evidence | Required action |
|---|---|---|---|---|
| M1 | All five, body header/footer | FITAI header convention is a **dark navy filled rule/block** with italic `International School Capstone 1 – <year>`; the footer is an italic `CISE.56` / `Page N` pair over a rule. The DBCAS set uses a plain 9 pt gray rule with a different label split and `Page X of Y`. This is a reinterpretation, not the reference pattern. | FITAI `Architecture-p029.png`, `Database-p009.png` vs `full-CodeStandards-p5.png` | Align the running head/foot to the measured FITAI convention while keeping DBCAS identifiers. |
| M2 | All five, cover | FITAI cover family A has **horizontal signature rules** above `Name / Signature / Date`; the DBCAS cover prints the labels but no rules. Title is 26 pt where FITAI mainstream cover titles are 14–18 pt. | `full-ProposalDocument-p1.png` vs FITAI `Architecture-p001.png`, `Proposal-p001.png` | Add the signature rules; reduce the title toward the FITAI mainstream size if confirmed by the design-system audit. |
| M3 | Proposal Figure 1 (PDF p15) | The Gantt roadmap image is a dense legacy black-and-white chart rendered at roughly one third of the text width. Its internal labels overlap cell borders and are illegible at normal viewing size; its style and palette are unrelated to the rest of the figure set. | `qa/figures/ProposalDocument-image2.png` viewed full size; `ProposalDocument-sheet-3.png` | Recreate in the FITAI-derived figure style at a legible size, or replace with a readable table-plus-figure composition; keep the approved milestone data. |
| M4 | Proposal Figures 2–3, Architecture Figures 1–5 | The line diagrams are monochrome, use larger type and lack the light bordered figure frame used in FITAI figure pages; the set is internally consistent with itself but not with the reference composition. | `qa/figures/ProposalDocument-image3.png`, FITAI `Architecture-p029.png` | Apply a single figure frame/caption convention across all diagrams; do not redraw content from scratch. |
| M5 | All five, figure placement | Caption numbering is correct but figures are embedded as fixed-size rasters; several ERD sheets and the logical architecture diagram are reduced to a size where fine labels are hard to read. | Contact sheets `ProposalDocument-sheet-3/4`, `DatabaseDesign-sheet-2`, `ArchitectureDesign-sheet-3` | Increase display size where page geometry allows (landscape section if needed), preserving aspect ratio. |

## 3. Minor — consistency / completeness

| # | Document | Defect | Action |
|---|---|---|---|
| m1 | Proposal Table 15 / SOURCE_CODE.md | "28 browser specs" vs "25 Playwright specs" — both are correct under different conventions (25 in `frontend/e2e/` + 3 in `frontend/e2e-application/`). | State the convention once in each place. |
| m2 | Technical Report §4.1 | "41 triggers" is stated without the 36 row-level + 5 constraint-trigger breakdown given in Database Design §9.3. | Add the breakdown for cross-document consistency. |
| m3 | All five | Revision-history row 1.3 claims "re-verify every measured figure" while several figures are unchanged legacy rasters. | Qualify to the figures actually re-measured. |
| m4 | Architecture §14 / Proposal §14 | Owner placeholders are appropriate for approvals, URLs and capacity decisions, but open items are not consolidated into one register across the five documents. | Add a short, identical "Open owner decisions" block to each document. |

## 4. Exclusions / non-defects

- The cached `Page 1 of 1` in the DOCX footer is not a rendering defect (verified in PDF).
- The Document Information `File name` row is **correct** in all five documents; the
  `[OWNER TO PROVIDE]` placeholder is confined to the `URL` row, which is genuinely
  owner-owned. (An initial low-resolution reading suggested otherwise and was
  corrected against the extracted text.)
- The light-blue ERD/TRD card style is an existing DBCAS diagram source style, not a
  newly introduced one; it will be preserved, not replaced with stock art.
- `schema_migration` being excluded from the 67-table count is documented and
  consistent with tests; no change needed.

## 5. Status after revision

- C1 resolved: prose now states 67 PK / 50 unique / 42 standalone = 159, and
  Table 4's stale "Standalone indexes 51" was corrected to 42 with a rule that
  separates constraint counts from index counts (verified on final PDF p36).
- C2, C3 resolved: registered/runtime module conventions stated in all three
  documents and the handover reports.
- C4 resolved: every quantitative claim is now tied to a saved log, and the CI
  result is attributed to `d6df804`.
- C5 resolved: publication paths now match the implementation.
- M1, M3, M4, M5 resolved; M2 resolved except the cosmetic signature-rule
  rendering noted in `visual-qa-report.md` §4.
- m1–m4 resolved or recorded in `document-index.md` / `figure-audit.md`.

Full evidence: `visual-qa-report.md`, `technical-verification-report.md`,
`traceability-matrix.md`, `change-log.md`.

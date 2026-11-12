# W6 — Final document alignment (2026-11-13)

> Historical raw captures and execution logs cited below were removed during PR #1 remediation. See [evidence retention](../pr1-artifact-retention-20261114.md); curated screenshots and structured summaries remain.

Worktree: `C:\Users\kudot\Downloads\proposal test\_worktrees\dbcas-dn-20261101`
Branch: `develop2` — HEAD `daceccf` (`refactor(backend): remove unused imports and locals`)
Audit execution: 2026-11-11 +0700; request identifier `20261113`.
Owner scope only: Proposal, Architecture Design, Database Design v1.2 and the
repository documents listed below. No `.docx`, User Story, teammate document,
`docs/qa/handover.md`, `.env`, application code or test was changed.

## Verdict

| Metric | Result |
| --- | ---: |
| Official Word documents checked | **3** |
| Factual Word content edits required | **0** |
| Word packages changed | **0** |
| Architecture elements / diagrams rebuilt | **0** |
| Word COM opens without repair | **3/3 PASS** |
| Native Word pages (Proposal / Architecture / Database) | **59 / 70 / 40** |
| TOC entries (Proposal / Architecture / Database) | **36 / 17 / 50** |
| Table-list entries (Proposal / Architecture / Database) | **17 / 54 / 43** |
| Figure-list entries (Proposal / Architecture / Database) | **4 / 13 / 6** |
| Vietnamese body paragraphs | **0** |
| `docs:check` | **48 project + 52 Word assertions + 10 diagram gates PASS** |
| `docs:verify-word` | **3/3 PASS**, 0 format/run/language/diagram/data mismatches |

## Documents checked

| Document | File | SHA-256 (unchanged) |
| --- | --- | --- |
| Project Proposal | `docs/academic/C1SE.70_ProposalDocument_DBCAS_ver1.2.docx` | `ec7d20982a0969462da9ddb56ffe2a411c6e1a789b5540590d288768fe6268ca` |
| Architecture Design | `docs/academic/C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx` | `9da81648dbd54bf7c534a4f185feaaa762d15de3393fc62103836e299615c685` |
| Database Design | `docs/academic/C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx` | `390723782cb9c2ec5b706c74d762c4f5947e3b04779ccc6bb62964dce8baffa3` |

The hashes match the post-edit values in
[`docs/qa/oauth-20261112/word-edits.json`](../oauth-20261112/word-edits.json).
All three packages were re-read after the Word COM field update; no source
package was saved or rewritten.

## Factual audit against the final project

| Surface | Final measured fact | Word document check | Drift |
| --- | --- | --- | --- |
| Schema | 41 app tables / 293 columns / 59 FKs / 87 indexes / 19 migrations | All three state **41 tables**; the Database Design documents 41 table sections and 293 columns; `verify_docx.py` matches every name/type/nullability and all 59 FK targets. | None |
| Compose | 6 local services (`mailpit`, `db`, `executor-image`, `init`, `app`, `frontend`); 7 with QA-only `qa-ai` | The container/context views name the six logical containers and the OAuth/LLM/email systems; `executor-image`, `mailpit` (as SMTP/Mailpit) and `qa-ai` are deployment/test details and are not falsely counted. | None |
| OpenAPI | 82 paths / 92 operations | No document states a conflicting API count; the Architecture component view matches the current routers and services. | None |
| Frontend routes | 23 routes; 5 admin destinations (`/admin`, Grading, Accounts, Questions, System) | No route count is claimed; the five administrator areas are all described in the use cases and container/component views. | None |
| AI pipeline | One finished-attempt Prompt Builder output → byte-identical Evaluator input; local/template and rule fallbacks | Proposal §12.5, Architecture design views and Database `LLMCache` text describe the same two-AI separation and fallback. | None |
| Mandatory result flow | AI grades/evaluates first; administrator reviews every SQL/essay score, may adjust with reason, then approves; only published results count | Proposal §§12.3–12.4, Architecture UC09/UC20 and Database `ResultReleaseEvent`/`GradeReview` text describe the mandatory flow and hidden pending scores. | None |
| OAuth | Google/GitHub sign-in and Learner sign-up; verified-email linking; single-use handoff; rotating access/refresh sessions; provider tokens not stored | 20261112 edits are present in all relevant paragraphs; no retired “OAuth never creates an account” wording remains. | None |
| Logo / brand | Canonical DBCAS mark is `frontend/public/brand/dbcas-mark.svg`; the Word covers embed only the Duy Tan University mark | No Word text claims a DBCAS logo or a different brand asset. Covers/headers were inspected image by image (below). | None |

No statement in the three v1.2 documents was found to be false or missing in a
way that requires a Word edit. The documents were therefore left byte-identical;
no cosmetic, caption, numbering, language or style edit was made.

## Logo finding — cover and header

The only small RGBA images are the **Duy Tan University** logo (red university
mark and wordmark), not DBCAS:

| Document | Image | Size | Bytes | Alpha fully transparent | SHA-256 |
| --- | --- | ---: | ---: | ---: | --- |
| Proposal | `word/media/image1.png` | 454 × 134 | 14,656 | 55.82% | `7610f45c2c7c374fa1f15a26135761ce9bbbd59add54c48f202e03bfee56a07e` |
| Architecture | `word/media/image1.png` | 420 × 124 | 16,805 | 54.73% | `12c89edc68a3a55aaaa83e5e9704f934b0a9210d3bed78638871de1d9e69725d` |
| Database | `word/media/image1.png` + VML `image2.png` | 420 × 124 | 16,805 each | 54.73% | `12c89edc68a3a55aaaa83e5e9704f934b0a9210d3bed78638871de1d9e69725d` |

- The Database Design repeats the same university image as a VML fallback
  (`rId15` → `media/image2.png`) in addition to the DrawingML image.
- Header/footer parts contain **no image relationship** (`a:blip` or VML
  `imagedata`). Their `w:drawing` elements are non-image header rules/shapes.
- No embedded media hash equals any file in `frontend/public/brand/` (including
  `dbcas-mark.svg`, the favicon and the generated PNGs).
- **Do not replace these images.** They are the university identity block, not
  a stale DBCAS logo. The canonical DBCAS mark remains application-only.

## Diagram decision

No architecture element changed in W1–W5: no service, table, directed flow or
component was added, removed or renamed. W3 only corrected generated route
inventory metadata; W4 changed brand presentation; W5 removed unused imports/
locals and quarantined review artifacts; D2 changed an nginx MIME mapping.
Package media counts remain Proposal 5 / Architecture 14 / Database 8. All
approved figures, captions, positions and page caches are untouched. **No
diagram was rebuilt, re-rendered or inserted, and no owner diagram approval is
pending.**

## Word COM and field results

Native Word COM 16.0 opened the three packages as temporary copies, updated all
fields, TOCs and TOFs, repaginated, and closed without saving:

| Document | Open without repair | Fields | TOCs | TOFs | Pages before → after | TOC entries | Table list | Figure list | Source hash after |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Proposal | PASS | 138 | 1 | 2 | 59 → 59 | 36 | 17 | 4 | unchanged |
| Architecture | PASS | 238 | 1 | 2 | 70 → 70 | 17 | 54 | 13 | unchanged |
| Database | PASS | 250 | 1 | 2 | 40 → 40 | 50 | 43 | 6 | unchanged |

- TOC entries exactly cover the Heading 1/2 sequence; table and figure lists
  exactly cover the caption sequence (including Figure 4 split 1/2–2/2 and
  Figure 8 split 1/5–5/5 in the Architecture document).
- Full body + table + header/footer scan: **0 Vietnamese characters and
  0 Vietnamese paragraphs** in each English document.
- `docs:verify-word` reports 0 format differences, 0 run/style issues, 0 new
  Vietnamese words, 0 diagram issues and 0 data mismatches.
- **PDF evidence:** LibreOffice 26.2.7.3 rendered all three packages to PDF and
  produced before/after contact sheets. All figure layouts are inside the text
  margins and every checked caption stays on the same page; no diagram issue
  was reported. Word COM native pages remain **59/70/40**.

## Gate numbers

```text
docs:check: 48 assertions, tables=41, columns=293, fks=59, indexes=87,
migrations=19, services=6, services_all=7, openapi_paths=82,
operations=92, frontend_routes=23
verify_docx: 52 assertions, 0 failures
diagram model/render inventories: 10 PASS
docs:verify-word: 3 documents, 0 failed; Word COM proposal/architecture/database = ok
LibreOffice/PyMuPDF: 3/3 PDF renders; figure/caption page checks PASS
```

Cross-workstream facts used for the current status documents:

| Workstream | Measured result |
| --- | --- |
| W1 Learner E2E | **30/30 PASS** post-rebuild; 68 screenshots; 0 page/console/5xx errors; D1 fixed in `d9c324b` |
| W2 Admin E2E | **DONE** — 33/33 checkpoints, 37 screenshots, 0 errors; not re-run by W6 |
| W3 Backend/AI | **1,067 targeted checks PASS**; exact-count matrix **2,291,100 / 0 failed**; bank **5,482 / 0 invalid**; prompt byte-equality; live calls **0** this round (ledger 3/5, all 403) |
| W4 Logo/brand | **22 captures / 0 overlap / 0 overflow**, 1280+390, light+dark; BrandAssets **9/9** in W4 and **10/10** final after the D2 manifest regression; final unit **376/376**; contrast **186/186** |
| W5 Cleanup | **84 paths / 8,552,970,863 B / 186,321 files** quarantined in `_trash-20261113`; 83 moved + 1 already absent; 0 dead in-repo modules/deps/services/DB objects; 0 bytes permanently deleted |
| W6 Documents | This report: 3/3 Word, 0 edits, 0 diagram/gate failures |

## Repository documents updated

| File | Change |
| --- | --- |
| `README.md` | Added the measured 20261113 audit/logo links including W2 33/33; Vietnamese quick start retained. |
| `docs/README.md` | Added W1/W3/W4/W5/W6, final-audit and academic-index links. |
| `docs/final-status.md` | Prepended the concise 20261113 section; historical sections retained. |
| `docs/qa/task-audit.md` | Prepended the current audit section; historical tables retained. |
| `docs/deliverables/index.md` | Added final evidence links; Jira scope and mappings retained. |
| `docs/academic/README.md` | Added the final audit, exact Word/logo findings and canonical logo statement; counts remain 41/293/59/87/19, 82/92, 23. |
| `docs/qa/final-20261113/w6-documents.md` | This report. |

Raw logs and machine-readable evidence are in
[`w6/`](w6/): `docs-check.log`, `verify-word.log`, `word-com.json`,
`word-com.log`, `independent-checks.json`, `checks.log`, `images.json`,
`packages.json` and the extraction scripts.

## Unfixed / ASK

1. **Live LLM acceptance** remains externally blocked (prior ledger 3/5,
   all HTTP 403); this round made **0** real provider calls. Real-model quality
   is unverified; offline/fake-provider behavior is verified.
2. **External Google/GitHub consent** was not exercised; safe unconfigured
   behavior, metadata handling and local fake-provider flows are verified.
3. **Final pushed-HEAD CI** is not run by W6; no commit or push was made.

No owner approval is needed for the document edits or diagrams. The only
remaining owner action is the final pushed-HEAD CI observation; W2 now has a
final 33/33 report, which W6 did not re-run.

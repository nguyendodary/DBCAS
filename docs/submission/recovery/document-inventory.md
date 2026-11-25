# DBCAS document & figure inventory - takeover audit

**Report:** C:\Users\kudot\Downloads\proposal test\DBCAS\docs\submission\recovery\document-inventory.md
**Date:** 2026-11-25 (audit run). **Mode:** read-only inspection; no existing document was modified.
**Workspace root:** C:\Users\kudot\Downloads\proposal test (not a Git repo). The only Git checkout is C:\Users\kudot\Downloads\proposal test\DBCAS on develop2; docs/submission/final is committed (add commit 198dcfa, generator commit 47ccb32). The sibling recovery directory already contained recovery-report.md plus byte-identical backups of the five committed DOCX; those backups were verified by SHA-256 and left untouched.

## 0. Method and evidence base

- Directory/file enumeration with sizes and timestamps; SHA-256 hashes for identity checks.
- Full text extraction from all 8 comparison DOCX with python-docx 1.2.0 (paragraphs + every table cell); raw word/document.xml inspected for TOC/SEQ Figure/SEQ Table fields and drawing counts; word/_rels used to map a:blip image embeds to captions.
- PDF page counts read with PyMuPDF 1.28.2 (not copied from manifests); manifest/manual counts cross-checked.
- Core properties (author, last-modified-by, created/modified, revision) read from DOCX packages.
- Image inventories from word/media/, docs/submission/final/assets/, docs/submission/before-after/, plus SHA-256 grouping for duplicates. Pillow used for pixel dimensions.
- Nine representative figure images opened and visually inspected (section 5.5).
- Governing context read: DBCAS/AGENTS.md, docs/agent/STATUS.md, docs/academic/README.md, docs/agent/freeze-logs/doc-style-spec.md, docs/agent/freeze-logs/doc-verify.md, docs/submission-pack/*.md, recovery/recovery-report.md.

Important scope note: the user-facing STATUS.md claim "ver1.3 complete" is a process claim (generator + verifier + CI + clean clone). This report audits document content and figure continuity, which the 149-assertion XML/style gate does not cover.

## 1. Executive summary

1. Two competing ver1.3 lineages exist and both are materially different documents:
   - Older/richer attempt - Documents\Final-ver1.3\ (3 DOCX, 61/78/72 pages, 21/58/72 DOCX tables, 5/21/15 embedded images, 30,404 words). Direct in-place descendants of the v1.2 academic documents with about 54/43/17 numbered figure/table lists preserved. Its hashes exactly match verification/final-manifest.json. Verified visually by contact sheets; SRS was part of that attempt and later removed.
   - Newer committed set - DBCAS\docs\submission\final\ (5 DOCX, 20/22/39/12/13 pages, 19,483 measured words). Fully regenerated from scripts/submission_content/*.py + scripts/submission_style.py, not cloned from v1.2. It is the set described by STATUS/SUMMARY and is the only one inside the Git repository.
2. Page-count verification: PyMuPDF confirms 61/78/72 (older PDFs) and 20/22/39/12/13 (newer PDFs) exactly. The shrink is not a rendering artifact: the three corresponding documents lost about 52.5% of their text (30,404 -> 14,437 words), lost 51 of 54 numbered Architecture tables, 41 of 43 numbered Database tables, and 13 of 17 numbered Proposal tables, and dropped all landscape sections (10/7 -> 2/2). Two of the new documents are genuine net-new deliverables (Code Standards, Technical Report); the other three are re-scoped, not page-for-page revisions.
3. Not "silently superseded" but "quietly replaced in scope": the README still declares docs/academic/ v1.2 authoritative for docs:check, while STATUS/SUMMARY/DEMO_CHECKLIST point at docs/submission/final/ ver1.3. No file states that the older ver1.3 lineage is obsolete; final-manifest.json merely notes the current five-document set exists elsewhere. The SRS was explicitly de-scoped by the owner (archived). The older ver1.3 set remains on disk with no "superseded" marker.
4. Figures: the new set embeds 18 images total (5 are the same logo); 13 are substantive. All substantive images are also in assets/. Ten legacy diagram families (use-case, component x2, ERD 2/2, TRD 1/11-11/11) present in the older attempt and in before-after/ have no counterpart in the new set; only 4 of 15 schema-028 ERD sheets were carried over. Editable sources exist for most legacy figures (.drawio, .dot, .svg, generators), but the four shipped ERD sheets, Gantt, and the logo are effectively raster-only in practice.
5. Style consistency: the new figure set is not a single visual family - it mixes three styles (black/white sans-serif context + Gantt; black/white serif logical + pipeline; navy/light-blue monospace ERD sheets), while the retained module/allocation PNGs and the before/after legacy set use a fourth (navy/serif/pastel). Within-document consistency is acceptable; cross-document/legacy consistency is not.
6. Disposition recommendation: retain docs/submission/final/ as the submitted set only after owner sign-off on the condensation; retain Documents/Final-ver1.3/ as the content-complete baseline (do not delete); keep docs/academic/ v1.2 as the declared docs:check authority; archive older root revisions and SRS variants; explicitly mark lineages in a single index to prevent accidental supersession.

## 2. Document lineage map

All paths below are under C:\Users\kudot\Downloads\proposal test\ unless absolute. "Pages" = PDF pages measured with PyMuPDF; where no PDF exists the source of the number is stated.

| # | Lineage / directory | Purpose | Authoritative version | Latest in lineage? | Pages (measured) | Disposition | Evidence |
|---|---|---|---|---|---|---|---|
| L1 | DBCAS\docs\academic\ (Proposal/Architecture/Database v1.1 + v1.2, README, support PPTX) | Declared "official academic deliverables"; source of truth for npm run docs:check | v1.2 (08 Nov 2026 in-place revision of v1.1) | Yes for v1.2; superseded in submission scope by ver1.3 | No PDFs here; README records native Word 59/70/40 | Retain as authority; do not overwrite; update only with owner approval | README lines 1-22, 81-90, 117-119; hashes 8685a6..., ba359c..., 84fc13... |
| L1a | DBCAS\docs\academic\C1SE.70_UserStoryDocument_DBCAS_ver1.1.docx | Historical user-story doc | v1.1 | No | n/a | Retain unchanged / archive; README says not in three-doc scope and still contains retired FORMAL/PRACTICE wording | README lines 20-23 |
| L2 | Documents\Final\ (3 DOCX v1.2) | Owner-facing "final" v1.2 copies | v1.2 | Superseded by L1 (same date, richer Database: 46 vs 71 headings) | Before PDFs rendered from these exact files: 61/69/41 | Retain as dated baseline, do not treat as active | Fingerprint hashes match (ec7d20..., 9da816..., 390723...) in before/fingerprint.md lines 6, 44, 91 |
| L3 | Documents\Archive\root-v1.2-20261028\ (3 DOCX) | Old root v1.2 snapshots | v1.2 (28 Oct 2026) | No | n/a | Archive | 35-table Database dictionary vs 42 (L2) and 67 (L1) |
| L4 | Documents\Archive\root-old-revisions\ (Architecture v1.3/v1.4, Database v1.4/v1.5, Proposal v1.5/v1.6) | Pre-release root revisions | v1.3-v1.6 | No | n/a | Archive | Modified 02-29 Oct 2026; word counts 9.6k-10.8k / 3.9k / 9.7k-10.2k |
| L5 | Documents\Archive\C1SE.70_SRS_DBCAS_ver1.3.docx + srs-verification-20261125\ (5 variants) | SRS derived from Software Requiremen Specification Template.docx; explicitly removed from owner's document set | ver1.3 (archived) | No | Main SRS 9 pages per visual-audit.md line 5 (no PDF in rendered/); base template PDF 20 pages | Archived - do not revive without owner decision | final-manifest.json note line 48; SUMMARY line 102; DEMO_CHECKLIST lines 33-34; base hash B7C184FD... identical to root template |
| L6 | Documents\Other\C1SE.70_UserStoryDocument_DBCAS_ver1.2/v1.4/v1.5.docx | Parallel user-story lineage | v1.5 (29 Oct 2026) | Yes within Other | n/a | Retain/archive; note new Architecture section 13 now carries learner/admin stories | 58-59 paras, 7 tables each; v1.5 last modified by "Do Nguyen" |
| L7 | Documents\Final-ver1.3\ (3 DOCX + 3 PDFs + verification + contact sheets + layout diagnostics) | Older ver1.3 attempt: content-rich in-place descendants of L1/L2 | ver1.3 | No (superseded in submission scope, not marked as such on disk) | 61 / 78 / 72 (PDF + manifest agree) | Retain as content-complete baseline / recovery source | Hashes in verification/final-manifest.json match files byte-for-byte; word counts 10,784 / 12,029 / 7,591 |
| L8 | DBCAS\docs\submission\final\ (5 DOCX + 5 PDFs + assets + verification + TRACEABILITY) | Currently submitted ver1.3 set; generated, not cloned | ver1.3 | Yes - newest committed lineage | 20 / 22 / 39 / 12 / 13 (PDF + page-counts.json agree) | Retain as submitted set; update/consolidate only via generator + owner sign-off | STATUS.md lines 19-24; SUMMARY section 6; commit 198dcfa; generator scripts/build_submission_docs.py |
| L9 | Root C1SE.70_*_ver1.2.txt (3 files) | Plain-text v1.2 sources used by earlier generation/verification | v1.2 | No | n/a | Retain as evidence, not a deliverable | Hashes in Final-ver1.3/verification/source-manifest.json lines 14-25 match root files |
| L10 | Root Software Requiremen Specification Template.docx | Generic Student Management SRS template | 1.0 | No | 20 pages (as before/SRS-base.pdf) | Retain as template/evidence | SHA-256 equals before/SRS-base.docx |
| L11 | Root dbcas-doc-edits-backup.patch | Backup diff for README.md, docs/README.md, docs/deployment-and-readiness.md only - not a DOCX edit backup | n/a | n/a | n/a | Retain as evidence | Three diff --git headers only |
| L12 | DBCAS\docs\submission\before\ (4 PDFs, 4 text dumps, 191 page PNGs, fingerprints) | Immutable v1.2 baseline for before/after QA | v1.2 | n/a | 61 / 69 / 41 / 20 (Proposal/Architecture/Database/SRS-base) | Retain as baseline evidence | fingerprint.md, figures.json, text/*.txt |
| L13 | DBCAS\docs\submission\before-after\ (50 diagram PNGs + 62 page PNGs) | Visual QA pairs, legacy diagram before/after | v1.2-revised | n/a | n/a | Retain as evidence; 30 unique diagram images (20 duplicated across Architecture/Database) | SHA-256 grouping, section 7.3 |
| L14 | DBCAS\docs\submission-pack\*.md (3 files) | Handover: summary, source-code run guide, demo checklist | Current ver1.3 set | Yes | n/a | Retain; keep consistent with L8 | SUMMARY section 6; SOURCE_CODE section 7; DEMO_CHECKLIST sections A/D |
| L15 | DBCAS\docs\submission\recovery\ (recovery-report + 5 byte-identical backups + QA images) | Takeover safety net | n/a | Current | n/a | Retain; add this report only | Backups hash-equal to L8 DOCX |

## 3. Per-document records

### 3.1 Active academic set (L1)

| Document | File (prefix C:\Users\kudot\Downloads\proposal test\) | Pages | Paragraphs / tables | Core properties | Assessment |
|---|---|---|---|---|---|
| Proposal v1.1 | DBCAS\docs\academic\C1SE.70_ProposalDocument_DBCAS_ver1.1.docx | no PDF; v1.2 = 59 | 224 / 21 | author "Tu,Tran Van", rev 64, modified 2026-10-30 | Previous revision; retain |
| Proposal v1.2 | DBCAS\docs\academic\C1SE.70_ProposalDocument_DBCAS_ver1.2.docx | 59 (README, native Word) | 225 / 21 | rev 70, modified 2026-11-09 | Active authority |
| Architecture v1.1 | DBCAS\docs\academic\C1SE.70_ArchitectureDesign_DBCAS_ver1.1.docx | v1.2 = 70 | 235 / 58, 10 sections (3 landscape) | rev 41 | Previous revision |
| Architecture v1.2 | DBCAS\docs\academic\C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx | 70 | 250 / 58, 10 sections | rev 47 | Active authority |
| Database v1.1 | DBCAS\docs\academic\C1SE.70_DatabaseDesign_DBCAS_ver1.1.docx | v1.2 = 40 | 196 / 41 | rev 162 | Previous revision |
| Database v1.2 | DBCAS\docs\academic\C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx | 40 | 274 / 71 (67 table dictionaries), 7 sections (1 landscape) | rev 166 | Active authority |
| User Story v1.1 | DBCAS\docs\academic\C1SE.70_UserStoryDocument_DBCAS_ver1.1.docx | n/a | 58 / 7 | rev 49 | Historical, retired wording |

### 3.2 Older ver1.3 attempt (L7)

| Document | Pages (PDF and manifest) | DOCX tables | Numbered captions | Embedded media | Full text words | TOC / SEQ fields |
|---|---:|---:|---:|---:|---:|---|
| Proposal | 61 | 21 | 17 tables + 4 figures | 5 | 10,784 | TOC 3, SEQ Fig 4, SEQ Tab 17 |
| Architecture | 78 | 58 | 54 tables + 20 figure parts | 21 | 12,029 | TOC 3, SEQ Fig 20, SEQ Tab 54 |
| Database | 72 | 72 | 43 tables + 13 figure parts | 15 | 7,591 | TOC 3, SEQ Fig 13, SEQ Tab 43 |
| SRS (archived) | 9 per visual audit | 12 DOCX tables, 90 paras | - | - | 2,282 | TOC 1 |

Core properties of all three: author/last-modified "Do, Nguyen Quoc", created/modified 2026-11-25, revision 13. Titles carry "ver1.3". These are clearly derived from the v1.2 packages (same section/orientation structure: 2 / 10 / 7 sections, 3 / 3 / 3 TOC fields including List of Tables and List of Figures).

### 3.3 Newer committed ver1.3 set (L8)

| Document | Pages (PDF and page-counts.json) | Word count (measured / manifest) | DOCX tables | Numbered captions | Embedded media | Heading 1 count |
|---|---:|---:|---:|---:|---:|---:|
| Proposal | 20 | 4,155 / 4,141 | 19 | 15 tables + 3 figures | 4 | 15 |
| Architecture | 22 | 4,226 / 4,218 | 18 | 14 tables + 5 figures | 6 | 14 |
| Database | 39 | 6,056 / 5,988 | 78 | 7 tables + 4 figures | 5 | 10 (+67 table H3) |
| Code Standards | 12 | 2,204 / 2,209 | 12 | 8 tables | 1 | 15 |
| Technical Report | 13 | 2,842 / 2,843 | 5 | 1 table + 1 figure | 2 | 9 (+Abstract/References) |

All five: A4, margins 3.5/2/2/2 cm, Times New Roman 13 pt, 1.5 spacing, author "Do, Nguyen Quoc", core created 2013-12-23 (template artefact), revision 2-3, only 2 sections each (portrait), one TOC field and no SEQ Figure/SEQ Table fields. verification-report.md records 149/149 PASS assertions; TRACEABILITY.md maps 16 FRs, 67 schema tables, 7 features. Footer field caches read "Page 1 of 1" in the verifier detail (fields refreshed in Word before PDF export; the DOCX cache itself is stale) - see recovery-report.md section 5.

## 4. Content comparison - what was lost or condensed

### 4.1 Measured word and structure deltas

| Document | Older ver1.3 (L7) | v1.2 baseline text (before/text) | New ver1.3 (L8) | Delta vs older |
|---|---:|---:|---:|---:|
| Proposal | 10,784 words / 21 tables / 4 figures | 11,773 words (incl. [Pnnn] tags) | 4,155 words / 19 tables / 3 figures | -61% words, -1 figure |
| Architecture | 12,029 words / 58 tables / 20 figure parts | 13,710 words | 4,226 words / 18 tables / 5 figures | -65% words, -15 figure parts, -40 DOCX tables |
| Database | 7,591 words / 72 tables / 13 figure parts | 7,786 words | 6,056 words / 78 tables / 4 figures | -20% words, -9 figure parts, +6 tables (dictionary expansion) |
| Three-document total | 30,404 | 33,269 | 14,437 | -52.5% |
| Plus net-new docs | - | - | Code Standards 2,204 + Technical Report 2,842 | New total 19,483 (-36% vs L7 three-doc total) |

### 4.2 Concrete lost/condensed sections and tables

Proposal (L7 -> L8). All 15 required H1 sections survive, but the deeper H2 structure is collapsed:
- Lost H2s: 4.1 One Overall Grade Hides Real Strengths and Weaknesses; 4.2 Lack of Detailed Explanations for Mistakes; 4.3 Heavy Grading Workload in Large Classes; 4.4 Problem Identification Through Online Research; 4.5 How DBCAS Solves These Problems; 5.1 Online Query Practice Sites; 5.2 Traditional Learning Management Systems; 5.3 Conversational AI Chatbots; 12.1 System Context Diagram; 12.2 Multi-Tier Logical System Architecture; 12.3 Evidence-Based Competency and Gap Evaluation Pipeline; 12.4 Multi-Format Practice and How Scores Are Calculated; 12.5 AI Integration and Prompt Engineering. New has only 6.1/6.2, 7.1/7.2/7.3, 11.1/11.2/11.3.
- Lost numbered tables (17 -> 15): Table 6 Knowledge Scope and Assessment Exam Structure (the concept/band/four-format scope matrix) and Table 15 AI Evaluation Guardrails and Prompt Design Rules; Table 4 Comparison of Existing Solutions is retained but explicitly "condensed" (verification/proposal-sections.md line 14). Table 8 (FR01-FR16) and Table 9 (NFR01-NFR09) are renumbered to 7/8 and re-ID'd FR-01...FR-16.
- Lost figure: L7 Figure 4 Evidence-based Competency and Gap Evaluation Pipeline - relocated to Architecture Fig 4 / Technical Report Fig 1, not duplicated in the Proposal.
- Long-form narrative lost: the detailed problem illustration (two learners with the same grade but opposite strengths), research provenance (Stack Overflow / Reddit / teaching blogs), out-of-scope bullet catalogue (advanced transactions, physical storage, NoSQL, campus systems, chatbot, long-term paths, webcam surveillance), and per-modal grading explanation. New text replaces these with short cited paragraphs and 8 OWNER TO PROVIDE placeholders (student IDs/effort, faculty name, co-supervisor, survey dates/citations, velocity, URLs).
- Gains: IEEE references [1]-[14] with in-text citations, measured repository facts (67 tables / 561 columns / 122 FKs / 159 indexes / 28 migrations / 106 paths / 118 operations), explicit re-scope (no public deployment, no model weights).

Architecture (L7 -> L8). This is the largest loss:
- L7 7 H1 sections: 1. Actor, Use Case and UC Diagram (1.1 Actors, 1.2 Use Cases, 1.3 UC Diagram); 2. System Context Diagram; 3. Architectural Drivers (3.1 Use Case Entities, 3.2 Operational Use Cases, 3.3 Quality Attribute Scenarios, 3.4 Technical Constraints, 3.5 Business Constraints); 4. C4 Model (4.1 Container, 4.2 Component); 5. Module View; 6. Allocation View; 7. Entity Relationship Diagram.
- L8 14 H1 sections replace this with a generic measured narrative (Introduction, Overall Architecture, Main Flows, AI Pipeline, SQL Sandbox, Grading and Result Versions, Security, Architectural Decisions, Key Algorithms, Modules and Allocation, User Stories by Role, Open Items). The classical SE architecture artifacts - use-case diagram, use-case entity catalogue, 20 operational use-case specification tables, 11 quality-attribute scenario tables, 8 technical/business constraint tables, container/component responsibility tables, and the 11-page Table Relationship Diagram - are gone.
- Numbered tables: 54 -> 14. Lost (by title, from L7 List of Tables): Actors of the DBCAS system; four Use cases of ... tables; five Use Case Entities tables; Operational Use Cases: Register Learner Account through Review and Approve Results (Tables 11-30); Quality Attribute Scenarios: Page and API Response Time through Practice Interface Usability (Tables 31-41); Technical Constraints (42-45); Business Constraints (46-49); Responsibilities of Container/Component/Module/Allocation Diagram; Details about ERD tables. New tables are compact one-screen summaries (e.g., Table 1 Quality attribute scenarios and their architectural response; Table 10 Decision record; Table 14 Functional requirement to architecture section).
- Figures: L7 20 figure parts (Use Case, Context, Container, Component 1/2 + 2/2, Module, Allocation, ERD 1/2 + 2/2, TRD 1/11-11/11) -> L8 5 (Context, Logical, Module, AI pipeline, Allocation). No use case, no container, no component, no ERD, and no TRD figures remain in the Architecture document.
- Landscape sections 3 -> 0; all wide figures removed or replaced by portrait-scaled re-exports.

Database (L7 -> L8). Dictionary coverage expanded but descriptive depth shrank:
- Lost sections: Introduction about PostgreSQL, Table Overview narrative, Database Design for Sprint introductory prose, Hardware and Software Requirements (L7 Table 43), and the conceptual-model explanation of many-to-many junction tables.
- L7 Table 1 Table Overview was a 68x2 table with a prose description for each table (e.g., Account: "Stores login credentials ... including email, password hash, account status ..."). L8 Table 3 Table registry is 68x6 but columns are Table / Domain / Columns / Primary key / FKs / Idx - the per-table descriptions are gone.
- Per-table dictionary tables: L7 used a 6-column Attributes / Datatype / Null / Key / Default / Extra layout where Extra carried per-column meaning (e.g., "Owning account identifier.", "SHA-256 of the bearer token."). L8 uses 3 columns Column / Type / Key-nullability-default - the semantic Extra descriptions are removed. This is why word count drops 7,591 -> 6,056 even though DOCX tables increase 72 -> 78 (all 67 current tables now have a block; L7 covered 41 core + 26 appendix tables).
- Figures: L7 13 parts (ERD 1/2 + 2/2, TRD 1/11-11/11) -> L8 4 ERD sheets only (1, 6, 9, 10 of a 15-sheet schema-028 series). All 11 TRD sheets disappear.
- Gains: measured schema totals (67 / 561 / 122 / 159 / 28), data-type inventory, key/index inventory, migration history, seed sources, audit tables, version/snapshot/audit sections, and an explicit exclusion of schema_migration from the 67-table count.

Net-new in L8: Code Standards (15 sections, 12 tables) and Technical Report (Abstract + 7 sections, 9 references, measured results table) have no predecessor in L7/L1/L2. They add 5,046 words but do not restore the removed academic detail.

### 4.3 Verification of STATUS page-count claim

- STATUS.md lines 19-24 and SUMMARY.md lines 91-97 state 20/22/39/12/13 for the new set; PyMuPDF on final/rendered/*.pdf returns exactly those values; verification/page-counts.json agrees. Claim verified.
- Older sets: README.md lines 81-90 records 59/70/40 for academic v1.2 native Word. Documents\Final-ver1.3\verification\final-manifest.json records 61/78/72 Word and PDF pages; PyMuPDF confirms 61/78/72. before/*.pdf (rendered from Documents\Final v1.2) measure 61/69/41 - small renderer/field differences from the README's native Word numbers. Claim verified with that caveat.
- Explanation of the shrink: (a) about 52.5% fewer words in the three shared documents; (b) front-matter List of Tables / List of Figures removed (no SEQ fields: 74/56/20 -> 0 in Architecture/Database/Proposal); (c) all landscape figure pages removed (10/7 sections -> 2/2); (d) dense 9-11 pt tables replace long narrative and 54/43 numbered tables; (e) five documents split the remaining scope, with two genuinely new short documents. The 149-assertion gate checks style, metadata, required sections, counts and traceability - it does not assert content parity with v1.2/older ver1.3, so "149/149 PASS" cannot be read as "nothing was lost".

## 5. Figure inventory - newer five-document set (L8)

### 5.1 Embedded images (word/media/), mapped by relationship to captions

| # | Document | Media part | Size / px | SHA-256 prefix | Figure / placement | Source / editable source | Status |
|---|---|---|---|---|---|---|---|
| 1 | Proposal | image1.png | 14,656 B / 454x134 | 7610f45c2c7c | Cover university mark (unnumbered) | assets/logo.png; same raster as v1.2 covers; no vector source for this exact mark (canonical frontend/public/brand/dbcas-mark.svg is a different brand) | Retain |
| 2 | Proposal | image2.png | 790,793 / 2000x1484 | a7aae4498266 | Figure 1 Sprint roadmap and faculty milestones | assets/gantt-roadmap.png; re-export of legacy Gantt; no DOT/SVG/drawio source found | Retain; recreate from source if schedule changes (raster-only) |
| 3 | Proposal | image3.png | 80,318 / 1431x1061 | 2e08d1e2c69e | Figure 2 System context | assets/context.png; legacy context diagram re-render; candidate sources docs/diagrams/system-context.svg, docs/diagrams/generated/system-context.svg, scripts/build_system_context.py, docs/diagrams/rebuild/system-context/system-context.drawio | Retain; verify equivalence before editing |
| 4 | Proposal | image4.png | 571,647 / 2200x2172 | f6b2fe3fc420 | Figure 3 Logical architecture | assets/logical.png; candidate sources docs/diagrams/logical-architecture.dot and .svg, docs/diagrams/rebuild/logical/logical.drawio and .svg | Retain; modify via editable source |
| 5 | Architecture | image1.png | logo | 7610f45c2c7c | Cover mark | as #1 | Retain |
| 6 | Architecture | image2.png | 80,318 / 1431x1061 | 2e08d1e2c69e | Figure 1 System context (two actors, three external services) | as #3 | Retain |
| 7 | Architecture | image3.png | 571,647 / 2200x2172 | f6b2fe3fc420 | Figure 2 Logical architecture (four tiers) | as #4 | Retain |
| 8 | Architecture | image4.png | 296,420 / 3300x2050 | 46468d95254f | Figure 3 Module view | docs/diagrams/rebuild/module/module.png (drawio + SVG source), byte-identical to older Architecture image7 | Retain; editable source exists |
| 9 | Architecture | image5.png | 163,292 / 1342x762 | d23f9bf0f24b | Figure 4 AI pipeline (new placement) | assets/pipeline.png; docs/diagrams/rebuild/pipeline/pipeline.drawio and .svg; docs/submission/before-after/diagrams/Proposal-image4-after.png (127,856 B, same visual, older encoding) | Retain; modify via drawio |
| 10 | Architecture | image6.png | 180,421 / 1725x1600 | 49389d8c7dd4 | Figure 5 Allocation view | docs/diagrams/rebuild/allocation/allocation.png (drawio + SVG), byte-identical to older Architecture image8 | Retain; editable source exists |
| 11 | Database | image1.png | logo | 7610f45c2c7c | Cover mark | as #1 | Retain |
| 12 | Database | image2.png | 256,858 / 1433x1520 | bc427124cb9d | Figure 1 ERD sheet 1 | assets/erd-sheet-1.png; related vector docs/diagrams/schema-028/erd-1.svg and docs/diagrams/generated/erd-1.svg (different encoding) | Retain; recreate via schema generator if data changes |
| 13 | Database | image3.png | 286,209 / 1433x1744 | 5341dc80b8ea | Figure 2 ERD sheet 6 | assets/erd-sheet-6.png; schema-028/erd-6.svg | Retain / generator-managed |
| 14 | Database | image4.png | 232,257 / 1454x1434 | 28b7de129373 | Figure 3 ERD sheet 9 | assets/erd-sheet-9.png; schema-028/erd-9.svg | Retain / generator-managed |
| 15 | Database | image5.png | 247,688 / 1433x1616 | d29d0e550a50 | Figure 4 ERD sheet 10 | assets/erd-sheet-10.png; schema-028/erd-10.svg | Retain / generator-managed |
| 16 | Code Standards | image1.png | logo | 7610f45c2c7c | Cover mark only | as #1 | Retain |
| 17 | Technical Report | image1.png | logo | 7610f45c2c7c | Cover mark only | as #1 | Retain |
| 18 | Technical Report | image2.png | 163,292 / 1342x762 | d23f9bf0f24b | Figure 1 Evaluation pipeline | assets/pipeline.png (same bytes as Architecture Fig 4) | Retain; keep in sync with Architecture |

Total: 18 embedded parts (5 logos + 13 substantive); 12 distinct substantive hashes. recovery/qa/figures/ contains extracted copies of all 18.

### 5.2 Asset folder (all 9 are referenced by the generator)

C:\Users\kudot\Downloads\proposal test\DBCAS\docs\submission\final\assets\: logo.png, gantt-roadmap.png, context.png, logical.png, erd-sheet-1.png, erd-sheet-6.png, erd-sheet-9.png, erd-sheet-10.png, pipeline.png. Each byte-matches its embedded counterpart (section 5.1). No unreferenced assets. scripts/submission_content/*.py points to ASSETS directly, so replacing an asset and rebuilding regenerates the DOCX/PDF - do not hand-edit DOCX (DEMO_CHECKLIST lines 124-125).

### 5.3 Before/after and legacy figure evidence

- docs\submission\before-after\diagrams\: 50 PNGs, 30 unique. 20 are duplicated verbatim between Architecture-image7/8-* and Database-image1/2-* (same ERD/TRD images reused across two documents). Families: use-case Architecture-image1 (before+after), context image3, component image4/5 (before+after), ERD image7 (before + after-1 + after-2), TRD image8-trd-1...11 (before for 1-5, after for 1-11). Proposal-image3/4 cover logical + pipeline (before+after). Note: ERD "before" and "after-1" are byte-identical (7e2eb785...); only the added continuation page changed.
- docs\submission\after\diagrams\: 22 PNGs + 22 SVGs (14 unique PNGs); SVGs provide editable vector copies for exactly the legacy set (use-case, context, component, ERD, TRD 1-5 and 10-11, logical, pipeline).
- docs\submission\before-after\pages\: 62 PNGs (59 unique; three cover before/after pairs are identical). docs\submission\before\pages\: Architecture 69 + Database 41 + Proposal 61 + SRS-base 20 = 191 page PNGs.
- docs\diagrams\: editable sources by family - Graphviz *.dot (assessment-lifecycle, components, conceptual-core, containers, deployment, logical-architecture, modules, physical-schema, use-cases) + matching .svg/.json; drawio/SVG rebuilds under rebuild/{use-case,system-context,container,component,pipeline,logical,module,allocation,erd,trd}; generated ERD/TRD SVG/PNG under generated/ and schema-028/; Mermaid/PlantUML discovery documented in sources/README.md. docs/submission/tools/{diagram_style.py,trd67.py,erd67.py,reproduce_trd1.py} capture the legacy TRD/ERD grammar and generate continuation pages.
- Raster-only in practice: shipped ERD sheets 1/6/9/10 (no exact SVG of those PNGs), Gantt roadmap, cover logo, and the TRD page PNGs that were dropped. Legacy sources exist for most others.

### 5.4 Figures present in older/richer sets but absent from the new five documents

| Legacy figure family | Older ver1.3 / before-after evidence | Editable source | New set |
|---|---|---|---|
| Use Case Diagram (UC01-UC18) | L7 Architecture Fig 1; before-after/diagrams/Architecture-image1-before.png and -after.png | use-case.drawio/.svg, docs/diagrams/use-cases.dot/.svg | Absent |
| Container Diagram | L7 Architecture Fig 3 | container.drawio/.svg, containers.dot/.svg | Absent (only text Table 3) |
| Component Diagram 1/2 + 2/2 | L7 Architecture Fig 4 parts | component*.drawio/.svg, components.dot/.svg | Absent |
| ERD 2/2 (26 continuation entities) | L7 Architecture Fig 7 (2/2), Database Fig 1 (2/2) | erd.drawio/.svg, erd67.py | Absent |
| Table Relationship Diagram 1/11-11/11 | L7 Architecture Fig 8 x11, Database Fig 2 x11 | trd-{1..5}.drawio/.svg, trd67.py, trd67 spec | Absent entirely |
| Evidence pipeline as Proposal Fig 4 | L7 Proposal Fig 4 (legacy raster b0ce2cf4...) | pipeline.drawio/.svg | Present only as Architecture Fig 4 / TR Fig 1 (new raster d23f9bf...) |
| 11 of 15 schema-028 ERD sheets | schema-028/erd-1...15.svg, generated/erd-1...14.png | SVG/DOT/JSON | Only sheets 1, 6, 9, 10 shipped |

### 5.5 Visual style of representative images (opened and inspected)

1. assets/context.png - white background, thin (about 2 px) black strokes, plain rectangles + central ellipse, bold sans-serif title and labels (about 28-34 px), small 20 px edge labels, simple legend. Clean, monochrome.
2. assets/logical.png - white background, heavy black 2-3 px strokes, serif (Times-like) bold title and box headings, 4 stacked tier bands with rounded boxes, dense small serif body text. Monochrome.
3. assets/erd-sheet-1.png - white background, dark navy sans-serif title, light-blue table headers, monospace column text, thin navy borders, note that legacy/retired tables are shaded amber; 4-column grid of entity boxes. Clearly generated from a schema catalogue.
4. assets/pipeline.png - white background, serif bold title/subtitle, light-gray filled rounded boxes, thin black outlines, solid and dashed arrows, two-row flow with feedback loop. Visually consistent with logical.png.
5. assets/gantt-roadmap.png - white background, sans-serif bold title, strict 5-column grid, rounded task boxes, two starred hexagon faculty milestone gates, dotted vertical sprint separators; entirely black/white.
6. before-after/diagrams/Architecture-image1-after.png - dark navy serif title, pale blue (learner) / pale green (administrator) ellipses, gold ellipses for shared UC02/UC03, thin navy strokes, stick actors, serif labels. This is the legacy "rebuilt v1.2" style and is not used by the new set.
7. before-after/diagrams/Architecture-image7-erd-after-1.png - classic Chen-style ERD: black rectangles/ellipses/diamonds, 1/N/M cardinalities, dashed retired tables, serif labels, separate rounded legend bar; no blue headers or monospace text.
8. before-after/diagrams/Proposal-image4-after.png - the legacy pipeline: same serif/gray-box layout as assets/pipeline.png but smaller encoding; shows the new pipeline is a re-render, not a new design.
9. before-after/pages/Architecture-component-a-pair.png - page-level composite showing the legacy component diagram in gray-filled rounded rectangles, dashed container bands, italic serif captions and running header/footer; grayscale, low-contrast at page scale.

Consistency verdict: the new set is internally coherent in page-level typography (the 149-assertion gate enforces 13 pt Times New Roman body, heading/caption styles and A4 margins), but its figures are not mutually consistent: three distinct visual grammars coexist (monochrome sans-serif context/Gantt; monochrome serif logical/pipeline/module/allocation; navy + light-blue monospace ERD sheets), plus the reused legacy pastel/navy diagrams in before-after/ that no longer appear in the submitted documents. There is no single figure-style guide covering both the generated ERD sheets and the C4/flow diagrams; docs/submission/tools/diagram_style.py documents only the legacy TRD/ERD/C4 palette.

## 6. Duplicate / competing deliverables and supersession risks

| Risk | Evidence | Severity |
|---|---|---|
| Two "ver1.3" sets with identical version labels but different content/page counts | L7 (61/78/72) vs L8 (20/22/39/12/13); both named C1SE.70_*_DBCAS_ver1.3.docx; no "superseded" marker on L7 | High |
| Authority conflict between docs/academic (declared active v1.2) and docs/submission/final (declared submitted ver1.3) | README lines 1-18 vs STATUS lines 19-24 / SUMMARY section 6; no document states which governs which scope | High |
| "Complete" claim based on 149 structural assertions that do not test content parity | verification-report.md 149/149; recovery-report.md section 5 already flagged "document-format drift may have dropped figures/tables"; this inventory confirms the drift | High |
| OWNER UNKNOWN -> OWNER TO PROVIDE migration hides unresolved facts rather than resolving them | 23 owner placeholders across the five new docs (8/6/4/3/2); doc-verify.md section 8 lists eight open questions | Medium |
| Six v1.2 database dictionaries with different coverage (35 / 42 / 67 tables) under the same "v1.2" label | Archive/root-v1.2, Documents/Final, docs/academic | Medium |
| Multiple SRS copies (main, 4 verification variants, base template) with no single index | Documents/Archive/... + root template; hashes differ across variants | Medium |
| Legacy diagram evidence duplicated across Architecture and Database (before-after/diagrams 50 PNG -> 30 unique) and ERD before == after-1 | SHA-256 grouping section 5.3 | Low |
| Cached footer fields "Page 1 of 1" inside shipped DOCX; page counts only correct after Word refresh/PDF export | verification-report.md lines 29-30, 42-43, 55-56; recovery-report.md section 5 | Low-Medium |
| recovery/ is untracked (git status shows ?? docs/submission/recovery/) - audit evidence is not versioned with the deliverables | git status --short | Medium |

## 7. Recommended disposition (no changes made by this audit)

1. Do not delete Documents\Final-ver1.3\. Label it externally (e.g., in a new index under recovery/) as "older ver1.3 attempt - content-complete baseline; not the submitted set". Its 61/78/72 pages and 54/43/17 numbered tables are the only surviving full academic detail.
2. Keep DBCAS\docs\academic\ v1.2 as the declared docs:check authority; if the owner wants ver1.3 to become authoritative, update README.md and STATUS.md in the same change and state the scope explicitly (submission vs academic gate).
3. Consolidate, dont silently replace: decide per lost artifact whether it should be (a) restored into the new set from the older ver1.3 text (e.g., Proposal 4.1-4.5 and 12.1-12.5; Architecture use-case entities and operational use cases; Database per-table descriptions and Hardware/Software Requirements), (b) intentionally retired with a recorded rationale, or (c) relocated (pipeline already relocated). The new Technical Report does not compensate for removed academic content.
4. Figures: if any of the ten legacy diagram families must appear in the final submission, generate them from the existing drawio/DOT/SVG sources at the style established by the new documents, or reinsert the verified legacy PNGs with a style note. If they stay out, record that TRD 1/11-11/11 and use-case/component diagrams are intentionally absent. Regenerate ERD sheets from schema-028 if the schema changes; never hand-edit the shipped PNGs.
5. Archive root-old-revisions, root-v1.2 snapshot, SRS verification variants and stale user-story versions in a single indexed location; retain Documents/Other v1.5 as the latest user-story lineage unless Architecture section 13 is formally declared its replacement.
6. Verification: add a content-parity assertion (section titles / numbered tables / figure families) to scripts/verify_submission_docs.py so a future regeneration cannot pass while silently dropping content. Keep the byte-identical backups in recovery/backups/ until owner sign-off.

## 8. Evidence index (files inspected)

- C:\Users\kudot\Downloads\proposal test\DBCAS\docs\agent\STATUS.md; docs\academic\README.md; docs\submission-pack\{SUMMARY,SOURCE_CODE,DEMO_CHECKLIST}.md; docs\agent\freeze-logs\{doc-style-spec,doc-verify}.md.
- C:\Users\kudot\Downloads\proposal test\Documents\Final-ver1.3\verification\{final-manifest,source-manifest}.json, visual-audit.md, verification\commands.md; DBCAS\docs\submission\final\verification\proposal-sections.md.
- C:\Users\kudot\Downloads\proposal test\DBCAS\docs\submission\final\verification\{page-counts.json,verification-report.md}; parent TRACEABILITY.md; clean-clone.log.
- C:\Users\kudot\Downloads\proposal test\DBCAS\docs\submission\before\{fingerprint.md,figures.json,text\*.txt}; before-after\diagrams\*.png; after\diagrams\*.svg; docs\diagrams\** (DOT/drawio/SVG/JSON); docs\submission\tools\{README.md,diagram_style.py}; scripts\build_submission_docs.py and scripts\submission_content\*.py.
- C:\Users\kudot\Downloads\proposal test\DBCAS\docs\submission\recovery\recovery-report.md and backups\*.docx (hash-verified).
- Root C1SE.70_*_ver1.2.txt, Software Requiremen Specification Template.docx, dbcas-doc-edits-backup.patch.

Limitations: no contact sheets were produced for the newer five-document set by this audit (read-only); page counts come from the committed PDFs, not a fresh Word field refresh. FITAI reference files under FITAI - Documents\ were not re-measured here - style conclusions rely on doc-style-spec.md and direct figure inspection. page-counts.json word counts differ from python-docx counts by about 0.2% due to field/hyperlink text handling; both are reported.


## 9. Late observation at audit close

During this read-only run, git status at the start showed only the pre-existing untracked recovery directory; at close it additionally showed modified docs/submission/final/verification/verification-report.md and verification-report.json (style-exception counts changed, e.g., Architecture Heading 2 25 -> 23, Database Heading 3 32 -> 24). This audit did not write to either file; the changes are concurrent work by another process. Consequently, any assertion counts quoted above should be re-read from the current verification report before use. The page counts, DOCX hashes, text extracts and figure inventory in this report were captured before those changes and describe the five DOCX files whose SHA-256 prefixes are recorded in section 1; re-check hashes if those DOCX are rebuilt.

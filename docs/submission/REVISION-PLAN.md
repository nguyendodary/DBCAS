# REVISION PLAN — DBCAS documents

Ngày: 2026-11-23. Baseline code: `develop2` `6421b5ad44a0eaaeb9be8d26068c8ca434ae5bb7`.
Phạm vi: **sửa tại chỗ** ba tài liệu existing; SRS mới từ root SRS structure + FITAI cover.
Không rebuild cover/layout/diagrams. Production: **HOLD**.

## 1. Baseline fingerprint

| Tài liệu | File gốc | Bytes / SHA-256 | Trang (LibreOffice) | Ảnh nhúng |
|---|---|---:|---:|---:|
| Proposal | `C1SE.70_ProposalDocument_DBCAS_ver1.2.docx` | 2,832,300 / `ec7d2098…` | 61 | 5 |
| Architecture | `C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx` | 4,020,592 / `9da81648…` | 69 | 14 |
| Database | `C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx` | 2,278,780 / `39072378…` | 41 | 6 |
| SRS base | `Software Requiremen Specification Template.docx` | 1,216,503 / `b7c184fd…` | 20 | 10 |

- Page size 8.269×11.694 in; margins L/R/T/B 1.378/0.787/0.787/0.787 in.
- Cover Proposal/Architecture/Database: giữ nguyên 100%; team, mentor, version 1.2, date 08/11/2026 đã đúng.
- TOC fields: Proposal `TOC \o "1-3"`, Architecture `TOC \o "1-2"`, Database `TOC \o "1-2"`; table/figure TOCs riêng.
- Fonts/sizes: cover 14/20/16 pt (Proposal), 14/28/16/15 pt (Architecture); body style riêng từng file.
- Diagrams: Proposal 4 (Fig 1–4), Architecture 13 (Fig 1–8, 8 gồm 5 trang), Database 6 (Fig 1–2, Fig 2 gồm 5 trang); tất cả có SVG/DrawIO source trong `docs/diagrams/rebuild` hoặc `docs/qa/diagram-originals`.

## 2. Discrepancy report

### Proposal

| # | Vị trí | Nội dung hiện tại | Code nói gì | Phân loại |
|---|---|---|---|---|
| P1 | P066 / tr.10 | Practice `1–20`, default 5 | Legacy max **13**; typed **25 mixed / 50 single-type** (`practice_config.py:4-20`) | FACT-ERROR |
| P2 | P089 / tr.11 | "Every submission is reviewed … before published" | FIXED Test publishes **AI-official V1**; legacy/practice = human review (`assessment_lifecycle.py:233-238`) | FACT-ERROR |
| P3 | P110 / tr.22 | Read-only SELECT only; DML/DDL never executed | Default read-only; opt-in `DBCAS_DEMO_PROFILE=writable` allows DDL/DML in disposable container (`docker-compose.demo-writable.yml`) | STALE |
| P4 | P117 / tr.23 | RAG/course-document ingestion outside scope | Admin document grounding/generation implemented (`document_generation.py`, `/admin/documents`) | STALE |
| P5 | P167 / tr.48 | Admin reviews every submission | FIXED V1 AI-official; legacy/practice reviewed | FACT-ERROR |
| P6 | P172, P174 / tr.48 | Mandatory AI-then-admin workflow; review every submission | Two release paths (`result_version.py`, `grading_review.py`) | FACT-ERROR |
| P7 | P183, P184 / tr.51 | DB 41 tables; every SQL transaction read-only | **67 tables**; default read-only, demo writable rollback | FACT-ERROR |
| P8 | P189, P190, P196 / tr.52-54 | Every result published after admin review | FIXED V1 AI-official; legacy/practice admin review | FACT-ERROR |
| P9 | Table 9 tr.25; Table 10 tr.26; Table 11 tr.27-29 | `1–20`; "Every submission waits in admin review queue"; mandatory two-stage; read-only SQL | Actual limits; conditional release; default read-only | FACT-ERROR |
| P10 | Table 12 tr.30; Table 13 tr.31; Table 14 tr.33 | SELECT-only/Mandatory review | Default read-only + opt-in writable; conditional release | STALE |
| P11 | Fig 3 tr.51 | `41 tables` | 67 tables | FACT-ERROR |
| P12 | Fig 4 tr.52 | `1–20`; course-document retrieval outside scope; no release nuance | Actual limits; grounding implemented; FIXED/LEGACY paths | STALE |

### Architecture

| # | Vị trí | Nội dung hiện tại | Code nói gì | Phân loại |
|---|---|---|---|---|
| A1 | P197, P209, P245, P246, P680, P689, P713, P722 | `41 tables` | **67 tables**, 561 columns, 122 FKs, 159 indexes, 28 migrations | FACT-ERROR |
| A2 | P196 / tr.46 | Admin reviews/approves every result | FIXED V1 AI-official; legacy/practice human review | FACT-ERROR |
| A3 | P197, P209, P226; Tables 26/27 | SELECT-only / read-only role | Default read-only; opt-in writable demo in ephemeral container | STALE |
| A4 | P218, P407-408, P714 | Mandatory admin review before publication | Conditional release policy | FACT-ERROR |
| A5 | Fig 1 tr.14 | UC12 `1–20`; UC09 reviews every submitted session | Actual limits; conditional release | FACT-ERROR |
| A6 | Fig 3 tr.45 | `(41 tables)`; `[read-only transaction]` | 67 tables; default read-only | FACT-ERROR |
| A7 | Fig 4a/4b tr.49-50 | `(41 tables)` | 67 tables | FACT-ERROR |
| A8 | Fig 7 tr.59; Fig 8 tr.60-64 | ERD/TRD 41 cards, legend 41/293/59/19 | 67-table schema; 26 tables missing from cards | **OWNER-DECISION** (layout/new pages) |

### Database

| # | Vị trí | Nội dung hiện tại | Code nói gì | Phân loại |
|---|---|---|---|---|
| D1 | P075 tr.9; P083 tr.13 | `41 tables` | **67 tables** | FACT-ERROR |
| D2 | Table 1 tr.9-12 | 41 rows | 67 rows | FACT-ERROR |
| D3 | Sections 3.x tr.9-41 | 41 table sections | 67 table sections; 26 missing | FACT-ERROR |
| D4 | P083 tr.13 | "all 41 tables appear in Figure 2" | Figure is 41-card core; full dictionary 67 | STALE |
| D5 | GradeReview description tr.31 | "mandatory administrator approval" | Legacy/practice only; FIXED V1 AI-official | FACT-ERROR |
| D6 | Fig 1 tr.12; Fig 2 tr.14-18 | 41-card core ERD/TRD; legend 41/293/59/19 | 67 tables | **OWNER-DECISION** (no layout rewrite) |

### SRS

Không có bản DBCAS trước đó. Owner đã chọn **root SRS structure + FITAI cover**; nội dung mới dùng route/screen/test facts, không dùng layout của PR #99.

### Diagram-only list (elements wrong/missing)

- Proposal Fig 3: legend `41 tables` → `67 tables`.
- Proposal Fig 4: `count 1–20`; `1–20` session note; `course-document retrieval are outside scope`; no FIXED/LEGACY release note.
- Architecture Fig 1: `UC12: 1–20`; `UC09 Review and approve results` implies every result.
- Architecture Fig 3: `(41 tables)`; `[read-only transaction]`.
- Architecture Fig 4a/4b: `(41 tables)`.
- Architecture Fig 7/8, Database Fig 1/2: 26 tables absent and legend `41/293/59/19`; **OWNER-DECISION** because faithful expansion needs new cards/pages, which the owner prohibited without approval.
- Các diagram còn lại không có thành phần sai đủ để sửa.

## 3. Edits to apply

**Chỉ FACT-ERROR + STALE:**
- Proposal: practice limits; release wording; writable demo; document grounding; 41→67 tables; table cells.
- Architecture: 41→67 tables; release wording; default read-only/writable; table cells; use-case/container/component diagram text.
- Database: 41→67; 26 missing table sections (Appendix A), 26 overview rows; all 67 column lists refreshed to 561 columns; counts, Figure 2 note, GradeReview wording.
- SRS: new document from FITAI cover + root SRS sections; facts from code.

**Không sửa:** cover, fonts/sizes/colors, page setup, headers/footers, styles, TOC structure, 41-card ERD/TRD layout (OWNER-DECISION).

## 4. Counts

- FACT-ERROR: **14**
- STALE: **6**
- OWNER-DECISION: **3**
- STYLE-ONLY: **0**
- Diagram edits: **6** (Proposal 2, Architecture 4); unchanged diagrams: 7; OWNER-DECISION diagrams: 6 (ERD/TRD sets).

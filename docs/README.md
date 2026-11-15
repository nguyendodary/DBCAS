# docs/ index

Trang này là bảng ánh xạ Jira task tới file kết quả. Thêm một mục mới khi
bạn thêm một deliverable mới.

- `docs/deliverables/index.md` — bảng ánh xạ Jira → file.
- `docs/proposal.md` — đề xuất gốc (viết từ thời điểm phát triển ban đầu).
- `docs/architecture.md`, `docs/database.md`, `docs/ai-pipeline.md` — tài
  liệu kỹ thuật hiện tại.
- `docs/qa/task-audit.md` — bảng QA task cuối cùng.
- `docs/qa/handover.md` — nhật để tiếp quản kế tiếp.
- [Kiểm toán cuối 20261113](qa/final-audit-20261113.md) — W1–W6, lỗi D1–D4, gate và giới hạn.
- [W1 learner E2E](qa/final-20261113/w1-learner.md) — 30/30, 68 ảnh; D1 đã sửa.
- [W2 admin E2E](qa/final-20261113/w2-admin.md) — **33/33**, 37 ảnh, 0 lỗi; review/duyệt, tài khoản, CSV, RBAC.
- [W3 backend/AI](qa/final-20261113/w3-backend-ai.md) — 1.067 kiểm tra targeted; ma trận 2.291.100/0; ngân hàng 5.482/0.
- [W4 logo/thương hiệu](qa/logo-20261113/inventory.md) — 22 ảnh / 0 lỗi, 10/10 BrandAssets, 186/186 contrast.
- [W5 dọn dẹp](qa/final-20261113/w5-cleanup-inventory.md) — 84 đường dẫn / 8,55 GB đã quarantine.
- [W6 tài liệu](qa/final-20261113/w6-documents.md) — ba Word v1.2, Word COM 3/3, 0 sửa nội dung/diagram.
- [Ba tài liệu học thuật v1.2](academic/README.md) — 41/293/59/87/19, 82/92, 23; logo chuẩn của ứng dụng.
- [OAuth và root-cause audit 20261112](qa/root-cause-audit-20261112.md) — nguyên nhân `b4313b5`, sửa và regression.
- [Ảnh OAuth trước/sau](qa/oauth-20261112/screenshots/README.md) — login/register, sáng/tối, 1280/390.
- [Kiểm kê proposal test](qa/workspace-inventory-20261112.md) — KEEP/DELETE/ASK; 7 mục đã quarantine, chưa xóa vĩnh viễn.
- [Sổ request key mới](qa/oauth-20261112/new-key-live-ledger.json) — 3/5 request, cả ba HTTP 403; chất lượng/model chưa xác minh.
- [Ba Word v1.2: manifest chỉnh sửa](qa/oauth-20261112/word-edits.json) — text tiếng Anh, giữ nguyên run/định dạng/diagram.
- [Vòng hoàn tất W1–W8](qa/final-20261110/README.md) — số đo hiện tại, nguồn CI và giới hạn.
- `docs/qa/ux-copy-audit.md` — rà soát câu chữ tiếng Việt và tiếng Anh.
- `docs/qa/ai-pipeline-audit.md` — kiểm chứng Prompt Builder → Evaluator.
- `docs/qa/cleanup-report.md` — file/phụ thuộc đã xóa và bằng chứng.
- [Ảnh vòng cuối](qa/final-ui/screenshots.md) — 102 ảnh / 25 trạng thái, sáng/tối và mobile.
- [Mô tả từng ảnh](qa/final-ui/visual-review.md) — kết quả xem ảnh và bốn lỗi đã sửa.
- [Rà soát Word cuối](qa/final-20261110/word-audit.md) — ba bản v1.2 và đối chiếu dự án.
- [Sổ request live](qa/final-20261110/live-request-ledger.json) — giới hạn đã dùng hết; chất lượng model chưa xác minh.
- [Kịch bản demo](demo/demo-script.md) — tài khoản demo và profile local đã kiểm chứng.
- `docs/academic/support/5.14-final-report-slides.pptx` — slides báo cáo cuối.

## Complete root-document index

### Current guides

- [Architecture](architecture.md)
- [Database](database.md)
- [AI pipeline](ai-pipeline.md)
- [API conventions](api-conventions.md)
- [Analytics](analytics-dn.md)
- [Authentication](authentication-dn.md)
- [Competency](competency-dn.md)
- [Question bank](question-bank-dn.md)
- [Attempts and MCQ](attempts-and-mcq.md)
- [Grading and sandbox](grading-and-sandbox.md)
- [SQL grading](sql-grading-dn.md)
- [Essay AI](essay-ai-dn.md)
- [Local grading](local-grading.md)
- [Deployment and readiness](deployment-and-readiness.md)
- [Setup and migrations](setup-and-migrations.md)
- [Testing and release gates](testing-and-release-gates.md)
- [Local integration troubleshooting](local-integration-troubleshooting.md)
- [Learner and administrator manual](learner-and-admin-manual.md)
- [Development](development-dn.md)
- [Docker sandbox](docker-sandbox-dn.md)
- [Requirements decisions](requirements-decisions.md)
- [Proposal](proposal.md)

### Dated records

- [Academic documents v1.2 (2026-10-27)](academic-documents-ver12-20261027.md)
- [Academic edit ledger (2026-10-27)](academic-edit-ledger-20261027.md)
- [Academic reconciliation (2026-10-23)](academic-reconciliation-20261023.md)
- [Academic reconciliation (2026-10-27)](academic-reconciliation-20261027.md)
- [Activation readiness (2026-10-25)](activation-readiness-20261025.md)
- [Activation release (2026-10-25)](activation-release-20261025.md)
- [Bilingual architecture completion (2026-10-23)](bilingual-architecture-completion-20261023.md)
- [Bilingual question verification](bilingual-question-verification.md)
- [Core question recovery](core-question-recovery.md)
- [Development activation (2026-10-24)](development-activation-20261024.md)
- [Docker stabilization acceptance (2026-10-23)](docker-stabilization-acceptance-20261023.md)
- [Docker/WSL root-cause recovery (2026-10-23)](docker-wsl-root-cause-recovery-20261023.md)
- [Documentation alignment (2026-10-27)](documentation-alignment-20261027.md)
- [Draft question translation](draft-question-translation.md)
- [Figure update ledger (2026-10-27)](figure-update-ledger-20261027.md)
- [Final integration acceptance (2026-10-23)](final-integration-acceptance-20261023.md)
- [Final status](final-status.md)
- [Formal adaptive delivery (2026-10-29)](formal-adaptive-delivery-20261029.md)
- [Legacy essay resolution](legacy-essay-resolution.md)
- [Password recovery deferred (2026-10-28)](password-recovery-deferred-20261028.md)
- [PG-M089 assessment 2 reconciliation](pg-m089-assessment-2-reconciliation.md)
- [Phase 2 first-time-user acceptance (2026-10-26)](phase-2-first-time-user-acceptance-20261026.md)
- [Release audit (2026-10-28)](release-audit-20261028.md)
- [Supervisor implementation](supervisor-implementation.md)
- [UX simplification audit (2026-10-23)](ux-simplification-audit-20261023.md)

### Diagrams

- [Diagram guide](diagrams/README.md)
- [Source guidance](diagrams/sources/README.md)
- [Rendered diagrams](diagrams/rendered/)
- [Generated diagrams](diagrams/generated/)

### Academic

- [Academic documents](academic/README.md)
- [Deliverables index](deliverables/index.md)

### QA evidence

- [QA evidence policy](qa/README.md)
- [Final audit 2026-11-13](qa/final-audit-20261113.md)
- [Task audit](qa/task-audit.md)
- [Handover](qa/handover.md)

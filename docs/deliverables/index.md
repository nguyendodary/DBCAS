# Bảng phân phối tài liệu — DBCAS

> Tài liệu này ánh xạ từng mã Jira tới file kết quả tương ứng. Mọi tài liệu
> `docs/deliverables/*.md` được viết theo trạng thái thực của kho tại HEAD
> hiện tại, tiếng Việt, gọn và tái dùng bảng thuật ngữ/diagram chung.
> Bốn tài liệu học thuật v1.1 (đã có sẵn) giữ nguyên không sửa: xem
> `docs/academic/README.md`.

Vòng cuối dùng ba bản chính thức **v1.2** của Proposal, Architecture Design
và Database Design, được chỉnh tiếng Anh trong tài liệu gốc trước đó.
Rà soát cuối: [Word audit](../qa/final-20261110/word-audit.md) và
[kết quả Word 3/3](../qa/word-verification/summary.md). Bản v1.1 và User Story
gốc vẫn được giữ. Không có tên/ngày được tự đặt hay diagram mới được chèn.
Quy trình hiện tại luôn là AI sơ bộ → quản trị viên kiểm tra/duyệt →
công bố; chỉ bài đã công bố được tính thống kê.

Vòng OAuth/kiểm toán 20261112: ba v1.2 đã bổ sung rõ đăng nhập và đăng ký
Google/GitHub, liên kết email đã xác minh, nút luôn hiện khi thiếu cấu hình,
handoff một lần và phiên access/refresh xoay vòng. Giữ toàn bộ run/định dạng/
tên/ngày và diagram; sửa thêm 2 field caption và 4 số trang cache trong
Architecture, bỏ các bước ghi setting đã nghỉ; User Story không sửa.
Xem [root-cause audit](../qa/root-cause-audit-20261112.md),
[edit manifest](../qa/oauth-20261112/word-edits.json) và
[kiểm kê/quarantine](../qa/workspace-inventory-20261112.md).

Kiểm toán cuối 20261113: [tổng hợp](../qa/final-audit-20261113.md),
[W1 learner](../qa/final-20261113/w1-learner.md) 30/30,
[W2 admin](../qa/final-20261113/w2-admin.md) 33/33,
[W3 backend/AI](../qa/final-20261113/w3-backend-ai.md) ma trận 2.291.100/0,
[W4 logo](../qa/logo-20261113/inventory.md) 22 ảnh/0 lỗi,
[W5 dọn dẹp](../qa/final-20261113/w5-cleanup-inventory.md) 84 đường dẫn /
8,55 GB đã quarantine, [W6 tài liệu](../qa/final-20261113/w6-documents.md)
Word 3/3 / 0 sửa nội dung. W2 admin E2E đã hoàn tất 33/33. Ba `.docx` v1.2 giữ nguyên hash; ảnh bìa là
logo Đại học Duy Tân, không phải logo DBCAS.

Số đo và giới hạn hiện tại: [W1–W8](../qa/final-20261110/README.md),
[UI cuối](../qa/final-ui/screenshots.md), [trạng thái](../final-status.md).
Các báo cáo sprint/ngày cũ bên dưới giữ nguyên vai trò bằng chứng lịch sử;
trạng thái Jira chưa được cung cấp.

| Jira | Deliverable | File |
| --- | --- | --- |
| 1.1 | Cập nhật Proposal | [1.1-proposal-update.md](1.1-proposal-update.md) · [`docs/proposal.md`](../proposal.md) · [Proposal v1.2](../academic/C1SE.70_ProposalDocument_DBCAS_ver1.2.docx) |
| 1.2 | Kế hoạch dự án + Sprint Backlog | [1.2-project-plan.md](1.2-project-plan.md) |
| 1.9 | Kế hoạch kiểm thử | [1.9-test-plan.md](1.9-test-plan.md) |
| 1.10 | Product Backlog | [1.10-product-backlog.md](1.10-product-backlog.md) |
| 2.11 | Tóm tắt tiến trình Sprint 2 | [2.11-sprint-2-progress.md](2.11-sprint-2-progress.md) |
| 3.10 | Docker / chấm điểm / AI | [3.10-docker-grading-ai.md](3.10-docker-grading-ai.md) |
| 3.11 | Báo cáo xác thực 1 | [3.11-validation-report-1.md](3.11-validation-report-1.md) |
| 3.12 | Báo cáo kiểm thử 1 | [3.12-testing-report-1.md](3.12-testing-report-1.md) |
| 3.13 | Sprint backlog cập nhật + chuẩn bị review | [3.13-sprint-backlog-review.md](3.13-sprint-backlog-review.md) |
| 3.14 | User Stories | [3.14-user-stories.md](3.14-user-stories.md) |
| 3.15 | Thiết kế kiến trúc | [3.15-architecture-design.md](3.15-architecture-design.md) · [Architecture v1.2](../academic/C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx) |
| 3.16 | Thiết kế cơ sở dữ liệu | [3.16-database-design.md](3.16-database-design.md) · [Database v1.2](../academic/C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx) |
| 3.17 | Tài liệu UI | [3.17-ui-document.md](3.17-ui-document.md) |
| 3.18 | Test case và dữ liệu kiểm thử | [3.18-test-cases.md](3.18-test-cases.md) |
| 4.11 | Báo cáo yêu cầu / tiến trình | [4.11-progress-report.md](4.11-progress-report.md) |
| 4.13 | Cập nhật kiến trúc + CSDL | [4.13-architecture-db-update.md](4.13-architecture-db-update.md) |
| 4.14 | Cập nhật User Stories + UI | [4.14-user-stories-ui-update.md](4.14-user-stories-ui-update.md) |
| 4.15 | Tài liệu AI | [4.15-ai-documentation.md](4.15-ai-documentation.md) |
| 5.9 | Bộ tài liệu kiểm thử | [5.9-test-documentation.md](5.9-test-documentation.md) |
| 5.10 | Tài liệu kỹ thuật | [5.10-technical-documentation.md](5.10-technical-documentation.md) |
| 5.11 | Thiết kế UI + Hướng dẫn sử dụng | [5.11-ui-design-user-guide.md](5.11-ui-design-user-guide.md) |
| 5.12 | Biên bản họp / bằng chứng nhóm | [5.12-meeting-minutes.md](5.12-meeting-minutes.md) |
| 5.13 | Báo cáo kỹ thuật (bản nháp) | [5.13-technical-report-draft.md](5.13-technical-report-draft.md) |
| 5.14 | Báo cáo cuối + slides | [5.14-final-report.md](5.14-final-report.md) · [5.14-final-report-slides.pptx](../academic/support/5.14-final-report-slides.pptx) |
| 5.15 | Kiến trúc + CSDL đầy đủ | [5.15-final-architecture-db.md](5.15-final-architecture-db.md) |
| 5.16 | Reflection (liên hệ) | [5.16-reflection.md](5.16-reflection.md) |
| glossary | Thuật ngữ dùng chung | [glossary.md](glossary.md) |

Vùng ảnh/diagram dùng chung: `docs/diagrams/*.svg` và `_review/audit-20261107/`.
Số liệu lấy từ `docs/qa/task-audit.md`, `docs/final-status.md`,
`docs/qa/final-20261105/README.md`, `docs/qa/final-20261105/gate-results.json`,
`_review/audit-20261107/*`, và hàng thực trong DB sau seed.

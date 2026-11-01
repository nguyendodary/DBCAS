# Kiểm kê hoàn thiện local — 02/11/2026

Baseline `9d540a6`, nhánh `develop2`. Phạm vi mới thay thế giới hạn DN cũ:
toàn bộ backend, frontend, test, seed và tài liệu; chỉ chạy local bằng Compose.
Nguồn: Proposal FR01–FR12, 13 task Sprint 1–4 trong `docs/dn/report.md`,
route/API hiện hành và ma trận yêu cầu `docs/remediation/requirements.json`.
Không có connector Jira trong phiên; danh sách sprint do người dùng cung cấp là
nguồn đối chiếu Jira, không giả định đã cập nhật ticket trên dịch vụ.

`Working end to end` ban đầu dựa vào bằng chứng kiểm thử hiện hữu; các tính năng
`Partial` còn thiếu tích hợp hoặc dữ liệu khởi tạo. Gate cuối sẽ kiểm lại toàn bộ.

| Tính năng | Ban đầu | Hiện tại | Bằng chứng / việc cần hoàn thiện |
| --- | --- | --- | --- |
| Khởi động một lệnh, migrate, cấu hình tự sinh | Missing | Missing | Compose DN cần tạo env/tham số thủ công, UI dùng profile |
| Demo accounts và dữ liệu có ý nghĩa | Partial | Partial | Seed thiếu Learner, lịch sử và ngân hàng formal đầy đủ |
| Đăng ký, đăng nhập, phân quyền, đăng xuất | Working end to end | Working end to end | Auth/RBAC/rotation đã có; kiểm lại login demo |
| Learner: tổng quan | Partial | Partial | Có profile gần nhất, chưa nối thống kê đa chiều mới |
| Learner: chọn đề formal/practice | Partial | Partial | Luồng có sẵn, ngân hàng mới khởi tạo thiếu câu |
| Learner: MCQ và đáp án snapshot | Working end to end | Working end to end | 51 tests lifecycle/MCQ và integration hiện hữu |
| Learner: SQL SELECT, chạy thử và chấm | Working end to end | Working end to end | Sandbox/comparator đã kiểm; kiểm lại Windows/local |
| Learner: tự luận AI hoặc giảng viên | Partial | Partial | Chấm/review có sẵn, thiếu trạng thái rõ khi không cấu hình AI |
| Learner: autosave, resume, deadline, nộp một lần | Working end to end | Working end to end | Draft revision/server deadline/idempotency có test |
| Learner: lịch sử, kết quả và bằng chứng | Broken | Working end to end | Request mới hủy request cũ; giữ test race, thêm single-click/late failure; frontend 296/296 đạt |
| Learner: CLO/topic/độ khó, skill gap, tiến độ | Partial | Partial | API statistics có, UI mới hiển thị concept |
| Learner: xếp hạng | Missing | Missing | Chưa có API/hiển thị hạng riêng tư cho Learner |
| Learner/Admin: cài đặt ngôn ngữ/giao diện | Working end to end | Working end to end | Màn hình chung dùng account thật và preference local |
| Admin: dashboard | Partial | Partial | Có cohort, thiếu distribution/CLO/ranking mới |
| Admin: CLO, kỹ năng và liên kết | Working end to end | Working end to end | CRUD/mapping trong curriculum UI/API |
| Admin: người học, tài khoản, lịch sử | Working end to end | Working end to end | Roster/account/RBAC, drill-down đã có |
| Admin: ngân hàng MCQ/SQL/essay và phân loại | Working end to end | Working end to end | Authoring/validation/filter/API thật đã có |
| Admin: tạo đề, gắn phạm vi câu hỏi, công bố | Partial | Partial | Có CRUD/coverage; cần trải nghiệm demo đủ câu và pool rõ ràng |
| Admin: duyệt câu hỏi/đề xuất AI | Working end to end | Working end to end | Luồng duyệt thật; sinh bằng AI chỉ khi có provider |
| Admin: chấm/duyệt tự luận và công bố kết quả | Partial | Partial | UI/API có; cần kiểm E2E và fallback không key |
| Admin: báo cáo và thống kê | Partial | Partial | API đầy đủ, thiếu UI/bản xuất báo cáo thực |
| API contract, migration, bảo vệ dữ liệu | Working end to end | Working end to end | Backend baseline 1.161 tests đạt, OpenAPI/export đã kiểm |
| UX tiếng Việt, lỗi/retry/loading nhất quán | Partial | Partial | Có states chung, còn default tiếng Anh và menu/luồng dư |
| Full gate và smoke local lặp ba lần | Partial | Partial | Backend xanh; frontend còn 1 lỗi, chưa kiểm fresh-clone một lệnh |

Giới hạn nghiệm thu: local-only, AI tùy chọn; không triển khai cloud/production,
không chứng nhận tải. Không xóa hoặc nới lỏng test để đạt gate.

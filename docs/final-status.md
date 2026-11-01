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
| Khởi động một lệnh, migrate, cấu hình tự sinh | Missing | Working end to end | npm start tự sinh secret, nhận group socket, migrate/seed và chờ UI/API healthy |
| Demo accounts và dữ liệu có ý nghĩa | Partial | Working end to end | 24 câu, 2 CLO, 3 Learner, 4 bài công bố; login demo và API thật đạt |
| Đăng ký, đăng nhập, phân quyền, đăng xuất | Working end to end | Working end to end | Auth/RBAC/rotation đã có; kiểm lại login demo |
| Learner: tổng quan | Partial | Partial | Có profile gần nhất, chưa nối thống kê đa chiều mới |
| Learner: chọn đề formal/practice | Partial | Partial | Luồng có sẵn, ngân hàng mới khởi tạo thiếu câu |
| Learner: MCQ và đáp án snapshot | Working end to end | Working end to end | 51 tests lifecycle/MCQ và integration hiện hữu |
| Learner: SQL SELECT, chạy thử và chấm | Working end to end | Working end to end | Sandbox/comparator đã kiểm; kiểm lại Windows/local |
| Learner: tự luận AI hoặc giảng viên | Partial | Partial | Đã thêm fallback chờ giảng viên, worker local khi có key; 4 regression API và 42 UI tests đạt; chờ smoke Compose |
| Learner: autosave, resume, deadline, nộp một lần | Working end to end | Working end to end | Draft revision/server deadline/idempotency có test |
| Learner: lịch sử, kết quả và bằng chứng | Broken | Working end to end | Request mới hủy request cũ; giữ test race, thêm single-click/late failure; frontend 296/296 đạt |
| Learner: CLO/topic/độ khó, skill gap, tiến độ | Partial | Partial | Đã nối StatisticsPanel vào Năng lực, giữ gap/guidance; chờ smoke cuối |
| Learner: xếp hạng | Missing | Partial | API hạng riêng tư và UI đã có; 5 API tests và 8 UI/race tests đạt |
| Learner/Admin: cài đặt ngôn ngữ/giao diện | Working end to end | Working end to end | Màn hình chung dùng account thật và preference local |
| Admin: dashboard | Partial | Partial | Có cohort, thiếu distribution/CLO/ranking mới |
| Admin: CLO, kỹ năng và liên kết | Working end to end | Working end to end | CRUD/mapping trong curriculum UI/API |
| Admin: người học, tài khoản, lịch sử | Working end to end | Working end to end | Roster/account/RBAC, drill-down đã có |
| Admin: ngân hàng MCQ/SQL/essay và phân loại | Working end to end | Working end to end | Authoring/validation/filter/API thật đã có |
| Admin: tạo đề, gắn phạm vi câu hỏi, công bố | Partial | Partial | Editor chọn câu thật qua API pool, kiểm đủ mix, lọc theo kỹ năng/độ khó; chờ smoke cuối |
| Admin: duyệt câu hỏi/đề xuất AI | Working end to end | Working end to end | Luồng duyệt thật; sinh bằng AI chỉ khi có provider |
| Admin: chấm/duyệt tự luận và công bố kết quả | Partial | Partial | UI/API có; cần kiểm E2E và fallback không key |
| Admin: báo cáo và thống kê | Partial | Partial | Đã nối statistics/ranking theo filter và CSV tổng hợp thật; chờ smoke cuối |
| API contract, migration, bảo vệ dữ liệu | Working end to end | Working end to end | Backend baseline 1.161 tests đạt, OpenAPI/export đã kiểm |
| UX tiếng Việt, lỗi/retry/loading nhất quán | Partial | Partial | Mặc định VI, luyện tập tùy chọn, menu gọn, retry/timeout/error boundary; frontend 303 tests đạt trước gate cuối |
| Full gate và smoke local lặp ba lần | Partial | Partial | Backend xanh; frontend còn 1 lỗi, chưa kiểm fresh-clone một lệnh |

Giới hạn nghiệm thu: local-only, AI tùy chọn; không triển khai cloud/production,
không chứng nhận tải. Không xóa hoặc nới lỏng test để đạt gate.

## Ghi nhận thay đổi test

Giữ nguyên test race ban đầu, bổ sung single-click và hủy request cũ. Hai assertion
copy tại `GradingWait.test.jsx` và `SupervisorWorkflows.test.jsx` được cập nhật:
không còn khẳng định AI đã hoàn tất khi chưa bật AI; vẫn kiểm trạng thái chờ
giảng viên, không lộ kết quả tạm và cho phép refresh. Các assertion không bị bỏ.
Seed kiểm bằng DB/sandbox thật; audit bất biến được giữ, không lùi ngày hoặc sửa
bản ghi review/publication sau khi tạo.
Fixture `CumulativeRace.test.jsx` tách mock theo URL mới của statistics, giữ đủ
bốn trường hợp success/failure sau refresh/navigation và thêm kiểm tra số lần
gọi cumulative. Không bỏ các assertion chống ghi đè phản hồi cũ.
Locale test được cập nhật để yêu cầu mặc định tiếng Việt; test component/journey
tiếng Anh chọn locale rõ ràng. Test OAuth vẫn kiểm route thật của provider đã
cấu hình và yêu cầu ẩn provider chưa cấu hình, thay cho nút disabled dư thừa.

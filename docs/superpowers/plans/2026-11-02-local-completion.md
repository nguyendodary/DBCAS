# Kế hoạch hoàn thiện DBCAS local

> Thực hiện từng bước trong phiên này; người dùng yêu cầu tự hoàn thiện, không dừng xin phê duyệt.

**Mục tiêu:** Mọi luồng Learner/Admin chạy với API thật, demo sẵn và toàn bộ gate xanh.
**Kiến trúc:** Giữ FastAPI/PostgreSQL/React và sandbox tạm; một Compose local với
bootstrap nhỏ tự sinh cấu hình. Tái dùng CRUD/review/profile, ghép analytics và
báo cáo vào màn hình hiện có, không thêm infrastructure.
**Stack:** Python 3.13, PostgreSQL 17, React 19/Vite, Node 24, Docker Compose.
**Đặc tả:** `docs/final-status.md`, `docs/proposal.md`, yêu cầu hoàn thiện local ngày 02/11.

## Ràng buộc chung

- Chỉ develop2; commit nhỏ `<Area>: <description>` và push sau từng bước đạt kiểm tra.
- Tài liệu tiếng Việt, code/comment/commit tiếng Anh; giữ phong cách UI hiện tại.
- Không secret trong Git, không mock trong production, không giảm chất lượng test.
- Compose trên một máy là runtime duy nhất; không cloud, TLS hoặc load infrastructure.
- AI tùy chọn: không key thì chờ giảng viên, có cấu hình thì worker hiện hữu chấm thật.

## Điểm review

- Refresh lỗi/chậm không được ghi đè snapshot mới hoặc buộc bấm hai lần: test HistoryPage.
- Chạy lại bootstrap không ghi đè env, đổi mật khẩu hoặc nhân đôi demo: test launcher/seed.
- Không key không để bài treo ở spinner AI: test fallback, review và công bố.
- Ranking Learner không tiết lộ danh tính/kết quả người khác: test API authorization.
- Refresh/resume không mất nháp, lỗi mạng có retry hữu hạn: giữ regression và smoke thực.

## Bước 1 — Kiểm kê

File: `docs/final-status.md`, kế hoạch này, phạm vi hiện hành trong Proposal.
- [x] Đọc policy, README/docs/report, route, manifest, seed và cấu hình.
- [x] Fetch/checkout/pull rebase develop2 và lập bảng ban đầu.
- [x] Commit/push kết quả kiểm kê (`99e0f43`).

## Bước 2 — Sửa refresh kết quả

File: `frontend/src/pages/HistoryPage.jsx`, `frontend/src/test/ResultRace.test.jsx`.
Interface: `load(): void` tiếp tục chỉ nhận response của request sequence mới nhất.
- [x] Tái hiện regression hiện hữu.
- [x] Cho một lần refresh có thể thay request cũ; không yêu cầu người dùng bấm hai lần.
- [x] Giữ test out-of-order, thêm test single-click, late failure; frontend 296/296 và build đạt.
- [x] Commit/push bước refresh.

## Bước 3 — Khởi động local và seed

File mới: `scripts/local.mjs`, `docker-compose.local.yml`, `backend/app/seed_demo.py`;
test `backend/tests/test_demo_seed.py`, `scripts/local.test.mjs`.
Interface: `node scripts/local.mjs [start|stop|reset]`; `seed_demo(db, runner)` idempotent.
- [x] Test bootstrap tạo env URL-safe, không ghi đè cấu hình, lỗi Docker rõ ràng.
- [x] Compose tự migrate/seed, chạy UI/API và executor image không cần profile.
- [x] Seed ngân hàng đã review, đề đủ 10 MCQ/2 SQL/1 essay, tài khoản và lịch sử thật.
- [x] Test chạy seed hai lần, bảo toàn chỉnh sửa và rollback khi import lỗi: 4 tests đạt.
- [x] Kiểm khởi động, login, readiness; commit/push bước local.

## Bước 4 — Tự luận tùy chọn và review

File: `app/worker.py`, `services/grading_jobs.py`, `services/grading_review.py`,
UI grading/results và i18n; test fallback/provider/review tương ứng.
Interface: giữ job bền vững và release policy; API trả trạng thái chờ giảng viên rõ ràng.
- [x] Test không key: nộp bài, Admin chấm thay, công bố, Learner xem được.
- [x] Nối cấu hình AI local với worker hiện hữu; timeout/retry/cache giữ nguyên.
- [x] Test adapter provider qua mock HTTP transport, không gọi dịch vụ trả phí.
- [x] Kiểm SQL timeout/cleanup trên Docker hiện tại; commit/push.

## Bước 5 — Analytics, ranking, reports và UX

File: `services/statistics_service.py`, `schemas_analytics.py`, routers;
`components/StatisticsPanel.jsx`, Dashboard/Cumulative/AdminPage, Layout/i18n.
Interface: statistics Learner owned-only; thêm own rank không lộ roster;
Admin dùng statistics/ranking và xuất CSV từ dữ liệu API đã lọc.
- [x] Test API hạng/tie/no evidence/privacy và UI loading/empty/error/retry.
- [x] Nối CLO/topic/difficulty/distribution/progress; giữ ít màn hình.
- [x] Một hành động chính trên mỗi màn hình; tiếng Việt mặc định, gộp liên kết phụ.
- [x] Kiểm CRUD CLO/learners/question/exam/review/settings bằng smoke thực; sửa nguyên nhân.
- [x] Chạy tests theo phạm vi, build, export/inventory; commit/push.

## Bước 6 — Gate cuối và tài liệu

File: `frontend/e2e/local-smoke.spec.js`, cấu hình smoke Playwright nhỏ, CI, README,
`docs/final-status.md`.
- [x] Full backend lint/build/tests và frontend npm ci/tests/build, không skip để xanh.
- [x] Từ clone Git sạch, không env, chạy lệnh duy nhất; readiness và demo login đạt.
- [x] Smoke Admin dashboard → Learner đủ ba dạng → nộp → review → kết quả/năng lực;
  kiểm các trang quản trị và chạy ba lần liên tiếp, không retry che flakiness.
- [x] Kiểm thêm toàn bộ 55 ca trình duyệt: 55/55, không filter/skip và không retry.
- [x] README quickstart năm dòng; cập nhật bảng trạng thái bằng bằng chứng thực.
- [x] Commit/push, CI cả hai job xanh; đối chiếu remote HEAD khi bàn giao.

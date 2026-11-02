# Nghiệm thu DBCAS local — 02/11/2026

Baseline `9d540a6`, nhánh `develop2`. Phạm vi hiện hành gồm toàn bộ frontend,
backend, test, seed và tài liệu; chạy bằng Compose trên một máy. Bảng ban đầu
được lập ở commit `99e0f43` từ Proposal FR01–FR12, 13 task Sprint 1–4 trong
`docs/dn/report.md`, route/API và ma trận `docs/remediation/requirements.json`.
Danh sách sprint do người dùng cung cấp là nguồn đối chiếu Jira; không có thao
tác cập nhật ticket trên dịch vụ Jira trong phiên này.

Đợt QA bằng trình duyệt từ mốc `6140e8e` ghi nhận và sửa các lỗi chờ chấm,
phân tích 0/1/nhiều bài, điểm tổng, refresh hai tab, proxy và bố cục. Bằng chứng,
phép tính tay, từng commit và thay đổi assertion nằm trong
[báo cáo QA Learner/Admin](qa/browser-qa.md). Bảng tính năng dưới giữ mốc audit
ban đầu; cổng kiểm tra sau QA được cập nhật bằng số thực tế.

| Tính năng | Trước | Sau | File chính | Kiểm thử |
| --- | --- | --- | --- | --- |
| Một lệnh khởi động, secret, migrate | Missing | Working end to end | `scripts/local.mjs`, `docker-compose.local.yml` | Launcher, clone sạch, readiness |
| Dữ liệu demo và tài khoản sẵn dùng | Partial | Working end to end | `backend/app/seed_demo.py` | 4 test seed thật, login demo |
| Đăng ký, đăng nhập, RBAC, refresh/logout | Working end to end | Working end to end | `frontend/src/auth.jsx`, `frontend/src/api.js`, auth backend | Auth API/UI, smoke xác nhận token cũ 401 |
| Khôi phục mật khẩu qua hộp thư local | Partial | Working end to end | Compose, `ForgotPasswordPage.jsx`, `ResetPasswordPage.jsx` | Gửi thư thật, đổi mật khẩu, đăng nhập mới; chống dùng lại link |
| Learner: tổng quan | Partial | Working end to end | `DashboardPage.jsx`, API competency | Dashboard tests, smoke login |
| Learner: chọn đề, luyện tập | Partial | Working end to end | `AssessmentsPage.jsx`, `PersonalizedAssessment.jsx` | 49 phạm vi qua UI, formal/practice/adaptive |
| Learner: MCQ và đáp án snapshot | Working end to end | Working end to end | `grading_service.py`, `ExamPage.jsx` | Lifecycle/MCQ API, smoke 10 MCQ |
| Learner: chạy và chấm SQL SELECT | Working end to end | Working end to end | `ephemeral_sandbox.py`, SQL comparator | Sandbox/comparator/timeout, smoke 2 SQL |
| Learner: tự luận AI hoặc giảng viên | Partial | Working end to end | `worker.py`, `grading_jobs.py`, `llm/provider.py` | Optional essay, provider HTTP, smoke 1 tự luận |
| Learner: autosave, resume, hạn giờ, nộp một lần | Working end to end | Working end to end | `ExamPage.jsx`, draft/lifecycle backend | Reload giữ nháp, timeout, duplicate/concurrency |
| Learner: lịch sử và bằng chứng kết quả | Broken | Working end to end | `HistoryPage.jsx`, `EvidencePage.jsx` | Giữ `ResultRace`, thêm refresh một lần và lỗi phản hồi cũ |
| Learner: CLO/topic/độ khó, skill gap, tiến độ | Partial | Working end to end | `StatisticsPanel.jsx`, `CumulativePage.jsx`, statistics backend | Statistics/cumulative API/UI, smoke sau công bố |
| Learner: xếp hạng riêng tư | Missing | Working end to end | `/sessions/ranking`, `StatisticsPanel.jsx` | Tie/no evidence/privacy; không lộ danh tính người khác |
| Learner/Admin: cài đặt ngôn ngữ, giao diện | Working end to end | Working end to end | `SettingsPage.jsx`, `i18n/`, theme | VI mặc định, lưu EN/VI và light/dark, touch/keyboard |
| Admin: dashboard | Partial | Working end to end | `AdminPage.jsx`, analytics backend | Cohort/filter/drill-down, statistics và smoke |
| Admin: CLO, kỹ năng, liên kết | Working end to end | Working end to end | `AdminCurriculumPage.jsx`, curriculum backend | CRUD, prerequisite/CLO mapping qua UI/API |
| Admin: người học, tài khoản, lịch sử | Working end to end | Working end to end | `AdminAccountsPage.jsx`, account/analytics backend | Provisioning, RBAC, roster, kết quả cá nhân |
| Admin: ngân hàng MCQ/SQL/tự luận và phân loại | Working end to end | Working end to end | `AdminQuestionsPage.jsx`, `QuestionAuthoring.jsx` | Authoring, topic/difficulty/CLO, tìm kiếm/lọc, snapshot |
| Admin: tạo đề, chọn câu hỏi, công bố | Partial | Working end to end | `AdminAssessmentsPage.jsx`, `AssessmentPoolEditor.jsx` | Pool API/UI, đủ mix 10/2/1, activation/versioning; lưu/mở lại 19 câu thật |
| Admin: duyệt câu hỏi và đề xuất AI | Working end to end | Working end to end | `AdminCandidatesPage.jsx`, generation backend | AI authoring vẫn là draft đến khi người có quyền duyệt |
| Admin: duyệt/chấm tự luận, công bố kết quả | Partial | Working end to end | `AdminGradingPage.jsx`, `grading_review.py` | Revision conflict, chấm thay, Retry một lần, smoke công bố |
| Admin: báo cáo, phân bố điểm, xếp hạng | Partial | Working end to end | `StatisticsPanel.jsx`, statistics backend | API thật theo filter, CSV UTF-8, chống công thức CSV |
| API contract, schema và bảo vệ dữ liệu | Working end to end | Working end to end | `docs/openapi.json`, `db/migrations/`, middleware | OpenAPI/export, migration, authorization và audit bất biến |
| UX Việt, loading/empty/error và Retry | Partial | Working end to end | i18n, `States.jsx`, `ErrorBoundary.jsx`, API timeout | UI regression, accessibility, responsive, lỗi mạng/retry |

Tên component/page trong bảng nằm trong `frontend/src`; tên service Python nằm
trong `backend/app/services`. Mọi màn hình gọi API thật; fake provider và mock
response chỉ nằm trong test. Demo được seed vào DB bằng service của ứng dụng.

## Cổng kiểm tra

- Backend: lint, build, pip check đạt; **1.179 passed, 0 failed, 0 errors,
  0 skipped** trong 1.022,25 giây. Một deprecation warning Starlette/httpx.
- Frontend: `npm ci` đạt; **322 passed / 37 suites**, 0 failed, build đạt
  (198,20 giây cho tests); `npm audit` báo **0 vulnerabilities** sau bản vá
  `follow-redirects` 1.16.2.
- Launcher: **3/3**. OpenAPI khớp runtime, **76 paths / 91 API routes**;
  **23 frontend routes**; diagram/DDL gate khớp **17 migrations, 38 bảng,
  54 FK, 9 DOT, 2 Mermaid** và 10 inventory sơ đồ.
- Clone sạch trên Windows tại `9b1bf6a`: ban đầu không `.env`, chạy `npm start`, tự sinh
  secret, migrate/seed, bốn service healthy và hai job init/image exit 0.
  Có **24 câu / 3 dạng, 2 CLO, 3 Learner, 4 bài đã công bố, 1 đề đã công bố**;
  Admin và Learner đăng nhập qua Chromium thành công. Lượt kiểm lại dùng project
  `dbcas-qa-clean-final`, cổng 18280/18200/18225/11225 để không ngắt kiểm thử khác;
  đã dọn volume và container của lượt này.
- Smoke sau cập nhật cuối: **3/3**, retries=0, **35,3 / 34,9 / 33,9 giây**
  (tổng 106,23 giây). Suite trình duyệt đầy đủ: **55/55 passed**, 0 failed,
  0 skipped, 0 flaky, retries=0, **1.734,87 giây**.
- QA từ DB sạch: **12/12**, ba lượt liên tiếp ở cả chế độ không key và AI HTTP
  giả có độ trễ/lỗi; mỗi lượt Learner làm ba bài, Admin duyệt/công bố, kiểm 0/1/2/3
  bài, số học, đồng hạng/riêng tư, hai tab và JWT hết hạn thật. Không retry.
  [Số liệu từng lượt](qa/gate-results.json) và [ảnh bằng chứng](qa/browser-qa.md#bằng-chứng-sau-sửa).
- [CI của mã ứng dụng 9b1bf6a](https://github.com/nguyendodary/DBCAS/actions/runs/41415155355)
  xanh cả backend và frontend, gồm startup không .env, smoke 3/3 và QA 12/12.

Chạy hệ thống và lặp lại gate theo [README](../README.md). Smoke thực hiện Admin
dashboard → Learner làm đủ MCQ/SQL/tự luận, reload giữ nháp → nộp → Admin chấm,
công bố → Learner xem kết quả/năng lực/hạng → Admin xuất CSV; đồng thời kiểm tra
logout thu hồi token và đổi mật khẩu qua Mailpit. Không có retry che flakiness.

## Giả định và giới hạn

- Chỉ local trên một máy có Docker Linux containers; chưa load test, không có
  nghiệm thu production/cloud. API tin cậy dùng Docker socket để tạo executor.
- AI tùy chọn; không key thì chờ giảng viên. Với key hợp lệ, Compose mặc định
  OpenAI; có thể đổi URL/model. Kiểm thử adapter dùng HTTP transport kiểm thử,
  chưa gọi model trả phí và không chứng nhận chất lượng chấm của model thật.
- Demo học thuật PostgreSQL: đề formal 13 câu/60 phút. Seed giữ dữ liệu đã sửa
  khi chạy lại, không lùi ngày hoặc sửa audit; reset là thao tác xóa dữ liệu rõ ràng.
  Thống kê chính thức chỉ dùng bài formal đã công bố, hạng có thể đồng hạng.

## Ghi nhận thay đổi kiểm thử

Giữ test race ban đầu; thêm refresh một lần/hủy request cũ. Cập nhật copy trạng
thái chờ giảng viên trong `GradingWait`/`SupervisorWorkflows`, locale mặc định VI,
provider OAuth chưa cấu hình được ẩn, và mock cumulative tách theo URL statistics;
giữ các assertion bảo vệ dữ liệu, concurrency và phản hồi cũ.

Journey tiếng Anh chọn locale rõ ràng, gồm context cảm ứng; kiểm tra fallback
ngôn ngữ vẫn bắt buộc VI và giữ theme đã lưu. Helper luyện tập mở mục tùy chọn
trước khi thao tác, vẫn kiểm đầy đủ đáp án/độ khó/resume/kết quả. Isolation preflight
dùng DB guard tmpfs thuộc phiên test thay phụ thuộc DB cá nhân: giữ kiểm nhãn,
version, không volume/bind, marker và probe không ghi sang DB khác.

Thêm năm ca tham số OpenAI/custom provider và hai ca phục hồi lỗi hàng đợi/detail
chấm bài (đã tái hiện thất bại trước sửa). Không xóa hoặc vô hiệu hóa test để xanh.
Hai assertion migration/JWT sid được DN phê duyệt trong commit lịch sử `ee99a12`
vẫn được ghi rõ file/dòng trong [báo cáo DN](dn/report.md); không trộn với triển
khai đợt này. Phạm vi hiện tại không chờ bàn giao hay phê duyệt thành viên khác.

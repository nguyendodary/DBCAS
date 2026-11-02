# Kế hoạch hoàn thiện DBCAS local — 02/11/2026

**Mục tiêu:** Hoàn thiện luyện tập tự chọn, pipeline hai AI, hai luồng công bố và giao diện gọn; xác minh bằng API và trình duyệt thật.

**Kiến trúc:** Giữ FastAPI/PostgreSQL, sandbox SELECT, snapshot câu hỏi, worker và Chart.js. Bổ sung cấu hình hệ thống và job đánh giá bền vững, cache theo hash dữ liệu. Prompt Builder local chỉ tạo prompt; Evaluator API chỉ trả JSON đã kiểm tra; thiếu model/key dùng template và quy tắc xác định.

**Công nghệ:** Python 3.13+, SQLAlchemy, PostgreSQL 17, React/Vite, Vitest, Playwright, Docker Compose. Baseline `4317754`, chỉ nhánh `develop2`.

**Đặc tả:** Yêu cầu người dùng ngày 02/11/2026: bảy nhóm tính năng và stability gate. [QA baseline](qa/browser-qa.md) là bằng chứng lịch sử, không phải nghiệm thu mã mới.

## Ràng buộc

- Một máy local, `npm start`; không cloud/production; không secret trong Git/log.
- Commit nhỏ `Area: description`, push `origin develop2`; không force push hoặc sửa checkout khác.
- Code/comment/commit tiếng Anh; UI/docs tiếng Việt; không xóa/làm yếu test.
- Thống kê/xếp hạng chỉ dùng kết quả đã công bố; training optional offline; clone không env hoạt động.

## Điểm cần rà soát

1. Hai tab nộp/chạy đánh giá: idempotent, không nhân job hoặc công bố sớm.
2. Worker/provider/model lỗi: fallback hữu hạn, retry, không spinner vô hạn.
3. Sửa điểm: bắt buộc lý do, audit actor/time/old/new, cập nhật cache/thống kê.
4. AI vượt khái niệm/độ khó, SQL lỗi, MCQ nhiều đáp án: loại trước snapshot, fallback hợp lệ.
5. 0/1/3 bài và bài chờ duyệt, session hết hạn, mobile 390px: không lộ điểm/tràn ngang/xu hướng giả.

## Bước 1 — Kiểm kê

File: `docs/final-status.md`. Đã đọc routes, seed, worker, release boundary và UI.

- [x] Fetch, checkout, pull develop2; sạch; giữ nguyên checkout main đang có thay đổi.
- [x] Baseline: đề demo dựng sẵn; Admin quản lý đề/candidate; chưa có pipeline hai AI/overall AI.
- [ ] Commit/push kế hoạch. Các gate mới chưa chạy.

## Bước 2 — Hai AI và huấn luyện

File mới `backend/app/services/prompt_builder.py`, `evaluation_pipeline.py`, `ai/`, `docs/ai-pipeline.md`; sửa config/worker/package scripts.
Giao diện `build_prompt(data: dict) -> PromptResult`, `evaluate(data: dict) -> dict`; log hash/duration/status/fallback, JSON strict.

- [ ] Test template/local-model/validation fallback, schema evaluator, timeout/cache/log không secret.
- [ ] Triển khai template tiếng Việt, model nhỏ local tùy chọn, evaluator API hoặc fake có delay/errors.
- [ ] Dataset/train/evaluate/export qua npm run ai:train; verify tiny smoke hoặc ghi giới hạn phần cứng.
- [ ] Chạy tests liên quan; commit/push.

## Bước 3 — Setting và công bố

File migration tiếp theo, models/schemas/admin router, grading_review/lifecycle/statistics.
Giao diện setting `result_flow=IMMEDIATE|HUMAN_VERIFIED`, mặc định IMMEDIATE, snapshot lúc bắt đầu. Chỉ công bố khi chấm và đánh giá xong.

- [ ] Test hai flow/visibility/revision conflict/edit reason/audit/approve/SQL SELECT.
- [ ] Triển khai setting, release boundary, audit và invalidation; giữ lịch sử/FK.
- [ ] Chạy integration tests; commit/push.

## Bước 4 — Practice tự chọn, không đề dựng sẵn

File mới `routers/practice.py`, `services/practice_service.py`; sửa seed/schema/AssessmentsPage/api.
`POST /practice/start`: concept IDs, difficulties, source, count, request ID → session và snapshot riêng, không tạo assessment.

- [ ] Test phạm vi/thiếu câu/idempotency/AI schema/SQL/MCQ/fallback.
- [ ] Session không cần exam; seed 0 exam, có câu/CLO/concept/learners/past attempts; bỏ API quản lý exam.
- [ ] UI chip/chọn tất cả/đa độ khó/hai nguồn/Bắt đầu/số câu tùy chọn.
- [ ] Chạy API/UI tests; commit/push.

## Bước 5 — Evaluation views

File evaluation router/service/model, EvaluationPage/CumulativePage/HistoryPage/ExamPage.
GET/Retry per-session và overall; chỉ dùng bài công bố, đếm bài chờ; cache hash answer/score/rubric/history.

- [ ] Test 0/1/3, polling hữu hạn/retry/cache/score edit/Flow 2 privacy.
- [ ] Xem đánh giá; loading đúng copy; question/CLO/topic/difficulty; overall/trend/lộ trình; Chart.js 0–100%.
- [ ] Chạy API/UI tests; commit/push.

## Bước 6 — Admin và UX

File App/Layout/Admin pages/CSS/i18n. Chỉ Dashboard, Duyệt bài, Tài khoản, Ngân hàng & khái niệm/CLO, Hệ thống.

- [ ] Test menu/routes/settings/review/SQL/edit/reason/approve/mobile.
- [ ] Một hành động chính mỗi màn, nhãn tiếng Việt, xóa controls không cần.
- [ ] Chạy UI tests/build; commit/push.

## Bước 7 — Bug hunt và gate

File frontend/e2e/scripts/CI/README/docs/qa và báo cáo này.

- [ ] E2E bank/AI/overall 0–1–3/Flow 2/Admin/mobile; ảnh desktop và 390px.
- [ ] Audit arithmetic/double-submit/refresh/two-tabs/session expiry/ranking privacy; test mỗi lỗi, bảng issue/commit.
- [ ] Backend lint/build/all tests; frontend ci/tests/build/audit; browser 0 retry/flaky.
- [ ] Clone không env, npm start, seed 0 exam/demo login; scenario ba lần; CI xanh.
- [ ] README 5 dòng đầu, pipeline doc, feature/issue/gate tables, limits/log; commit/push.

## Gate mới

**Chưa chạy.** Không tái dùng số pass baseline. Kết quả, số thực tế và phần chưa xác minh sẽ được cập nhật sau từng bước.

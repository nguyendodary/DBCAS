# Trạng thái DBCAS — develop2

Phạm vi: một máy local, Docker Compose, `npm start`. Kế hoạch ban đầu đã được
commit trước triển khai tại `e15f788`. Bảy nhóm tính năng đã triển khai; 29 lỗi/
điều chỉnh QA được ghi dưới đây. Gate đầy đủ trên mã `853c275` đã đạt, gồm
88 lượt browser và ba vòng Learner–Admin local liên tiếp.

## Tính năng

| Feature | Before | After | Key files | Tests |
| --- | --- | --- | --- | --- |
| 1. Hai AI | Chấm tự luận riêng, chưa có Prompt Builder local | Builder chỉ tạo prompt Việt; LoRA tùy chọn, validation/template fallback; Evaluator JSON strict, timeout/retry/cache/log metadata | `prompt_builder.py`, `evaluation_pipeline.py`, `ai/pipeline.py` | 17 pipeline + 4 HTTP fake; smoke train/export/inference |
| 2. Đánh giá người học | Bằng chứng/biểu đồ, chưa có đánh giá tổng thể AI | Xem đánh giá từng bài; tổng thể 0/1/3+, loại bài chờ, trend/CLO/chủ đề/độ khó; polling hữu hạn và Retry | `evaluation_service.py`, `EvaluationPage.jsx`, `EvaluationCharts.jsx` | Practice API + 12 UI; browser bank/history/overall |
| 3. Hai luồng kết quả | Policy theo đề, duyệt SQL/essay | Một setting chung; Flow 1 tự động, Flow 2 ẩn trước duyệt; mọi điểm sửa phải có lý do, audit bất biến, SQL SELECT và công bố nhất quán | `system_settings.py`, `grading_review.py`, `routers/practice.py`, `AdminGradingPage.jsx` | API hai flow/revision/audit/SQL; UI + E2E duyệt |
| 4. Tự tạo bài | Đề/blueprint tạo trước, nhiều chọn cấu hình | Khái niệm → đa độ khó → nguồn bank/AI → Bắt đầu; mặc định 5 câu, count tùy chọn; snapshot riêng, idempotency, thiếu câu báo rõ; seed 0 đề | `practice_service.py`, migration 018/019, `seed_demo.py`, `AssessmentsPage.jsx` | 21 practice API; seed/migration; ma trận browser 49 scope |
| 5. Admin gọn | Quản lý đề và trang candidate riêng | Năm mục: Tổng quan, Duyệt bài, Tài khoản, Ngân hàng & khái niệm/CLO, Hệ thống; gỡ 8 API quản lý đề | `Layout.jsx`, `AdminSystemPage.jsx`, `App.jsx`, `routers/admin.py` | Removed API theo ba vai trò, menu/settings/reset password |
| 6. UI/UX | Chọn một kỹ năng phải bỏ nhiều lựa chọn; hướng dẫn cũ | Chọn một khái niệm và Bắt đầu trong hai click; hướng dẫn đúng luồng mới; Chart.js 0–100%, số liệu chữ, theme và 390px | `HelpGuide.jsx`, `EvaluationCharts.jsx`, `AdminPage.jsx`, i18n | 340 UI; axe/keyboard/theme ở 390/768/1024/1440px |
| 7. Ổn định | Gate lịch sử chưa bao phủ luồng mới | Regression race/lease, nộp sớm, score arithmetic, refresh, hai tab, hết hạn đăng nhập và fake HTTP có delay/lỗi | `frontend/e2e`, `backend/tests`, `scripts/browser-qa.mjs`, CI | 55 regression + 10 QA × 3 + 3 scenario CI = 88 lượt đạt; local 3/3 đạt |

## Lỗi và xử lý

| # | What happened | Expected | Severity | Status | Commit |
| --- | --- | --- | --- | --- | --- |
| 1 | Nộp sớm bỏ câu chưa mở khỏi mẫu số | Tính mọi câu đã chọn, câu trống 0; regression 1/5 = 20% | Cao | Đã sửa | `a08d7b5` |
| 2 | SQL sinh mới thiếu kiểm tra dataset biên trước khi lưu | Chạy được cả fixture chính/biên rồi snapshot | Cao | Đã sửa | `a08d7b5` |
| 3 | Điểm/dimensions có thể xuất hiện khi đánh giá chưa công bố | Ẩn toàn bộ điểm trước release | Cao | Đã sửa | `3049807` |
| 4 | Câu sinh cho bài riêng xuất hiện trong ngân hàng Admin | Lưu tái lập trong bài, không làm đầy ngân hàng | Vừa | Đã sửa | `3049807` |
| 5 | Essay chưa chấm bị coi là 0 trong nhận xét, lệch biểu đồ sau đề xuất | Dùng cùng điểm đề xuất và làm tròn half-up | Vừa | Đã sửa + regression | `0e8e91a` |
| 6 | Refresh đúng lúc hoàn tất có thể nhận ready nhưng không có feedback | Đọc release/evaluation nhất quán, thiếu payload thì có Retry | Cao | Đã sửa + regression | `0e8e91a`, `c38d4c4` |
| 7 | Worker giữ ORM cache có thể ghi đè kết quả Retry mới | Kiểm tra lease/hash với dữ liệu DB mới | Cao | Đã sửa + giao dịch hai session | `0e8e91a` |
| 8 | Mở review bằng URL khiến polling bỏ kết quả mới do string/number ID | Nút Duyệt tự bật khi xong AI | Cao | Đã sửa + route regression | `c38d4c4` |
| 9 | Refresh bài hoàn tất dùng state cũ để chọn trang kết quả | Đi thẳng đến evaluation của practice | Vừa | Đã sửa | `c38d4c4` |
| 10 | Trang mới lồng thêm landmark main | Một main, modal/focus/axe hợp lệ | Vừa | Đã sửa | `c38d4c4` |
| 11 | Nút Duyệt bài ở theme sáng có contrast 3,76:1 | Dùng màu semantic đạt AA | Vừa | Đã sửa; axe giữ nguyên | `2231c86` |
| 12 | Đợi giảng viên quá 45 giây thì ngừng cập nhật | Tiếp tục kiểm tra chậm, công bố tự xuất hiện | Vừa | Đã sửa + timer regression | `2231c86` |
| 13 | Rubric dài làm bộ giới hạn prompt bỏ câu khỏi nhận xét | Giữ mọi question ID, rút gọn text, hash vẫn bao phủ đáp án gốc | Cao | Đã sửa + test 20 câu dài | `2231c86` |
| 14 | Hướng dẫn còn yêu cầu chọn đề/chế độ chính thức và nói practice không tính | Giải thích đúng practice và setting chung | Vừa | Đã sửa + guide tests | `3c45482` |
| 15 | Mặc định chọn toàn bộ khiến chọn một khái niệm tốn nhiều click | Chọn một chip hoặc Chọn tất cả, rồi Bắt đầu | Vừa | Đã sửa + test hai click | `3c45482` |
| 16 | Assertion migration cũ không biết 018/019 | Giữ kiểm tra migration và rollback trên danh sách hiện hành | QA | Đã cập nhật assertion, không bỏ test | `3049807` |
| 17 | Fake provider mới đọc messages trước khi từ chối task không hỗ trợ | Giữ contract HTTP 503; thêm protocol generation/evaluation | QA | 4/4 HTTP tests đạt | `c45a97a` |
| 18 | Script locale của browser test chạy vào iframe opaque của axe | Chỉ đặt locale trong tài liệu HTTP chính; không lọc bỏ page errors | QA | Đã sửa; giữ assertion page errors | `4e4c97e` |
| 19 | JSON provider cho essay chưa chấm có thể thiếu điểm đề xuất nhưng vẫn bị coi hợp lệ | Bắt buộc đề xuất hữu hạn trong thang điểm, sai thì dùng fallback và ghi rõ | Cao | Đã sửa + strict schema regression | `d65fb00` |
| 20 | Provider trả nhận xét đủ ID nhưng đảo thứ tự câu | Kiểm tra coverage/duplicate, sắp theo thứ tự bài làm | Vừa | Đã sửa + provider order regression | `e82c166` |
| 21 | Hai click trong cùng tick gửi hai request nộp trước khi React render disabled | Khóa đồng bộ trước request; server vẫn idempotent | Cao | Đã tái hiện đỏ, sửa, unit/browser regression | `0bc7d91` |
| 22 | Hai bài AI mới có cùng scope dùng lại batch từ cache prompt | Gọi generation cho mỗi request_id mới, retry vẫn dùng bài cũ | Vừa | Đã sửa + kiểm tra provider/cache thực | `772148b` |
| 23 | File JavaScript tải treo khiến Suspense hiện skeleton vô hạn | Sau 15 giây có thông báo/Thử lại; file về thì trang tự mở | Vừa | Đã sửa + unit và browser giữ module 17 giây | `e403278`, `4e4c97e` |
| 24 | Sau AI/điểm sửa, queue vẫn báo đang chấm dù chi tiết đã chờ duyệt | Badge bài đang mở dùng trạng thái chi tiết mới nhất | Vừa | Tái hiện qua ảnh; unit đỏ → xanh; thêm browser assertion | `60e0b81` |
| 25 | Điểm Admin đã sửa vẫn mang nhãn điểm tự động đề xuất | Gọi đúng là Điểm hiện tại, audit giữ cũ/mới | Vừa | Đã sửa + unit/browser regression | `60e0b81` |
| 26 | Queue một trang vẫn hiện hai nút phân trang bị vô hiệu hóa | Ẩn khi không cần; giữ đi tới/lùi khi đủ 100 bài | Thấp | Đã sửa + kiểm tra trang tiếp rỗng vẫn quay lại được | `60e0b81` |
| 27 | Harness đổi flow ở Hệ thống nhưng kiểm CSV ngay, chưa mở phần MCQ và chụp trước khi câu hỏi render | Quay về Dashboard; mở chi tiết MCQ; chờ đúng câu hỏi rồi giữ mọi assertion | QA | Đã sửa; không giảm kiểm tra 13 câu/CSV/ảnh | `853c275` |
| 28 | Đổi desktop → 390px làm canvas giữ width cũ một frame, scrollWidth 1023 | CSS giới hạn canvas ngay trước ResizeObserver; giữ assertion tức thì không tràn | Vừa | Tái hiện đỏ → xanh; 3 scenario mới liên tiếp đạt | `853c275` |
| 29 | Compose báo healthy sau thay API nhưng proxy vẫn trả 502; một lượt CI đăng nhập đầu không chuyển trang | Kiểm tra readiness thực qua proxy trước khi báo sẵn sàng và trước/sau QA | Cao | Docker tái hiện 502 → 200 sau guard; 7/7 launcher tests đạt. Log CI cũ chưa ghi mã HTTP nên không khẳng định đó là nguyên nhân duy nhất | `438e68d` |

## Gate đo thực tế

| Gate | Kết quả hiện có |
| --- | --- |
| Backend lint/build | Đạt |
| Backend toàn bộ | **1228/1228 pass**, 0 failure/skip, 1 deprecation warning, **514,68 giây** trên CI tại `853c275` |
| Pipeline/practice/provider liên quan | 42/42 pass, 25,97 giây |
| Frontend npm ci | Đạt sau khi dừng Vite; không đổi dependency để né lỗi |
| Frontend tests | **340/340**, 39 suites, **33,13 giây CI / 80,32 giây local**, 0 failures |
| Frontend build/audit | Đạt; **0 lỗ hổng**, gồm 0 high/critical |
| Launcher và readiness proxy | **7/7**, 0 failure; thử nghiệm đổi API với DNS chậm: readiness/đăng nhập 502 → 200 sau guard |
| OpenAPI / inventory | OpenAPI khớp runtime; inventory **93 API / 23 frontend routes**, không drift |
| Browser đầy đủ | **55/55 pass**, **23,3 phút** theo Playwright CI; 0 failure/skip/flaky/retry |
| Fake HTTP | **30/30 pass (10 ca × 3 lượt)**, **12,5 phút** theo CI; 0 failure/skip/flaky/retry. Bản sửa review cũng đạt 10/10 local |
| Learner–Admin local liên tiếp | **3/3 pass**, **208,79 giây**, 0 failure/skip/flaky/retry; gồm 13 câu, SQL, sửa/duyệt/audit, CSV, resize tức thì 390px và email reset thật |
| Clone sạch không .env | **Đạt** tại `853c275`: một npm start, 4 dịch vụ healthy, init/executor exit 0, 0 đề/24 câu/15 khái niệm/2 CLO/4 tài khoản/4 bài lịch sử; 4/4 demo login UI, 0 page errors |
| Huấn luyện smoke | **96 cặp (80 train/16 test)**; 2 bước LoRA CPU, loss **5,5685620**, optimizer **0,31 giây**; export/inference chạy, **0/1 prompt model hợp lệ**, template fallback hợp lệ |
| Image inference tùy chọn | Build và pip check đạt; export hiện diện, builder trả prompt fallback hợp lệ |
| CI | **Xanh** tại `853c275`: [run 41510594920](https://github.com/nguyendodary/DBCAS/actions/runs/41510594920). Run `268a5c0` có 29/30 QA đạt, một ca đăng nhập lỗi; đã bổ sung guard và assertion HTTP. [Trạng thái nhánh](https://github.com/nguyendodary/DBCAS/actions?query=branch%3Adevelop2) thể hiện lượt sau sửa |

Các lượt dò lỗi không được tính là lượt nghiệm thu xanh. Một lượt cài dependencies
bị khóa file do Vite còn chạy trên Windows; đã dừng lượt đó, chạy npm ci lại rồi
xác minh đầy đủ tests/build/audit; lượt cuối đạt 340 tests. Không có retries tự động để che flakiness. Thời gian browser CI được
Playwright làm tròn theo phút. [JSON số đo và ảnh đã kiểm tra](qa/final-20261103/README.md)
được lưu cùng báo cáo; trace chứa phiên đăng nhập chỉ giữ local.

## Assertion thay đổi có chủ đích

- Seed: từ một đề có sẵn sang 0 đề và session không cần đề. Giữ kiểm tra bốn bài lịch sử, 13 câu/bài, đủ MCQ/SQL/essay, snapshot và seed lặp an toàn.
- API quản lý đề: tám route trả 404 và không xuất hiện trong OpenAPI. Toàn bộ assertion regression quản lý đề lịch sử vẫn chạy qua adapter chỉ trong `backend/tests/historical_assessment_api.py`; app không mount adapter. Định nghĩa đề cũ nằm trong test fixture, không trong pack seed runtime.
- Giữ **55 ca browser** hiện hành. Ma trận 49 blueprint chuyển thành 49 scope người học, giữ giới hạn khái niệm/độ khó, snapshot, idempotency, không trùng và nộp sớm.
- Các assertion practice không vào competency được đổi sang practice đã công bố được tính, theo yêu cầu mới. Bài chờ tiếp tục bị loại. Nguồn bank giữ count/phạm vi và đủ loại khi khả dụng, thay cơ cấu đề cũ 10/2/1 cố định.
- Essay UI chuyển từ payload grader cũ sang JSON Evaluator, kiểm tra grader/điểm và đủ nhận xét từng câu. Unit/integration của grader lịch sử vẫn giữ.
- Các kiểm tra tài khoản, SQL sandbox, dịch/nội dung, reserved bank edit, snapshot cũ, timeout, RBAC, CSV, reset password, focus/keyboard, contrast và motion vẫn được thực hiện trên luồng hiện hành.
- Harness local quay về Dashboard sau khi đổi flow, mở MCQ trước khi kiểm 13 form; giữ assertion CSV/điểm/audit. Ảnh chỉ chụp sau khi câu hỏi đã hiện. Probe demo kiểm lời chào của tài khoản có lịch sử, khác tiêu đề tài khoản rỗng.
- Component đề/candidate đã gỡ khỏi bundle runtime; fixture giao diện lịch sử giữ các unit assertion cũ. Không skip/xóa test để đạt gate.

## Sử dụng

`npm start` → http://localhost:18080 · http://localhost:18000/docs · hộp thư
http://localhost:18025. Không cần tạo .env trước.

Admin `admin@dbcas.local`; người học `learner@dbcas.local`, `linh@dbcas.local`,
`minh@dbcas.local`. Mật khẩu demo chung **Demo12345!**.

Đổi flow: **Admin → Hệ thống → Tự động / Admin duyệt → Lưu cấu hình**. Áp dụng
cho bài bắt đầu sau khi lưu; bài đang làm giữ policy đã snapshot.

Training tùy chọn: `npm run ai:train`; smoke nhỏ:
`npm run ai:train -- --smoke`. Dataset/train/evaluate/export cũng chạy riêng qua
`ai/pipeline.py`. Xem [pipeline](ai-pipeline.md).

## Giới hạn đã biết

- Chưa gọi provider LLM thật hoặc xác minh chất lượng model Qwen 0,5B fine-tuned. Smoke chỉ kiểm tra cơ chế; 0/1 prompt hợp lệ không phải bằng chứng chất lượng.
- Chưa huấn luyện với bài làm thật của người học. Dữ liệu mặc định là ngân hàng hiện có và đáp án tổng hợp; bản export thật đã ẩn danh có thể thêm bằng --real.
- Rule evaluator và câu MCQ dự phòng cơ bản không thay thế kiểm định giáo dục; độ khó metadata được ràng buộc, độ khó thực tế của câu AI cần đánh giá chuyên môn.
- Điểm essay là đề xuất tự động. Flow 2 cho phép giảng viên điều chỉnh có audit; các bài đã công bố không được sửa âm thầm.
- Toàn bộ lịch sử tham gia số học/hash; giới hạn prompt rút gọn văn bản quá dài và chi tiết gần nhất của tổng thể, được thông báo trong giao diện.
- Các bản ghi đề lịch sử được đóng và giữ để bảo toàn FK/snapshot; seed mới không tạo đề. Không còn UI/API Admin để tạo đề.
- Đã kiểm tra Chromium với viewport 390px và desktop; chưa kiểm tra trên điện thoại thật hoặc chất lượng GPU. Image training mặc định dùng CPU.
- Python host 3,14 và container 3,13; một deprecation warning Starlette/httpx. CI ghi hai log Maintenance OperationalError lúc teardown DB kiểm thử dùng một lần, sau khi các ca đã đạt; không có lỗi JavaScript trong các scenario. Không có triển khai production/cloud.

## Git

Các commit triển khai dưới đây đã được đẩy lên `origin develop2`; sau mốc
`853c275`, `268a5c0` bổ sung báo cáo và `438e68d` sửa readiness. Chỉ làm trên
develop2; không force-push, không commit secret. Xem `git log` cho các commit tiếp theo.

```text
853c275 UI: keep charts within the viewport during resize
60e0b81 Admin: keep review status and adjusted score labels consistent
4e4c97e Tests: verify learner practice and approval across browser stability gates
e403278 UI: bound workspace loading and recover when modules arrive
772148b Practice: generate a fresh question batch for each new attempt
0bc7d91 Exam: prevent synchronous double submission before rendering
e82c166 Evaluation: preserve question order in provider feedback
d65fb00 AI: require proposals for ungraded essays and expose fallback honestly
c45a97a Tests: extend the local HTTP provider to evaluation and generation
2231c86 Stability: preserve question feedback and observe delayed approvals
f15ecb7 AI: support optional local inference in the Compose launcher
3c45482 UX: make concept selection direct and align the in-app guide
c38d4c4 UI: fix live review refresh and clarify released evaluation scores
0e8e91a Evaluation: keep feedback and publication consistent across worker races
3049807 Admin: retire prebuilt exams and protect released practice evidence
7baa905 UI: simplify practice setup and learner-admin evaluation views
a08d7b5 Grading: count unanswered practice items and verify generated fixtures
d206ba0 Practice: add exam-free sessions and auditable evaluation release
f054bbe AI: add validated prompt builder and optional local LoRA training
e15f788 Docs: plan learner practice and two-AI evaluation
```

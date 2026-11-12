# Kiểm thử Learner và Admin bằng trình duyệt

Ngày 02/11/2026; mốc ban đầu `6140e8e`; nhánh `develop2`. Chạy `npm run reset`
rồi `npm start`, thao tác trên Chromium thật qua Playwright tại `localhost:18080`.
Ảnh gốc nằm trong `_review/qa/before/`; không dùng đáp án từ API quản trị để làm bài.
Tài khoản mới được đăng ký qua UI để kiểm tra trạng thái chưa có bài; Linh có một bài
đã công bố, An có hai bài mẫu trước khi bắt đầu kiểm thử.

## Lỗi ghi nhận trước khi sửa

| # | Kịch bản và thao tác | Thực tế | Mong đợi | Mức độ | Trạng thái / commit | Ảnh trước sửa |
|---|---|---|---|---|---|---|
| 1 | Learner giữ trang kết quả; Admin duyệt và công bố #5 | Vẫn chờ giảng viên; bấm làm mới mới nhận kết quả | Tự cập nhật khi công bố, kể cả chờ lâu | Cao | Đã sửa: kiểm tra chờ duyệt mỗi 5–30s khi trang mở; không dừng sau timeout AI | `17-stale-after-publication.png` |
| 2 | Mở phân tích với 0 hoặc 1 bài | 0 bài có nhiều khối rỗng; 1 bài vẫn có điểm tích lũy, hạng, phân bố và tiến độ | 0 bài một lời mời làm bài; 1 bài chỉ phân tích bài đó; 2+ mới có xu hướng | Cao | Đã sửa: 0/1/2+ riêng, pending tách biệt | `20-zero-analysis.png`, `21-single-analysis.png` |
| 3 | Đối chiếu cùng bài giữa Tổng quan, Bài đánh giá, Lịch sử | Tổng quan 69%, hai trang kia 59% do lấy trung bình khái niệm | Điểm bài nhất quán theo tổng điểm / tổng điểm tối đa | Cao | Đã sửa: Tổng quan dùng overall_result_pct; chi tiết có tổng điểm | `02-learner-dashboard.png` |
| 4 | Đọc mã sau quan sát trạng thái chờ | Timeout dừng polling nhưng vẫn bật spinner; chưa có backoff/khóa request | Chờ AI hữu hạn, hết hạn dừng spinner và có thử lại | Vừa | Đã sửa: AI backoff 5–15s trong 5 phút, retry/focus; giảng viên 5–30s không spinner, không gửi request khi tab ẩn | Test `PendingResults`, `GradingWait` |
| 5 | Ở trang phân tích khi điểm được công bố | Nút làm mới chỉ nạp phần kỹ năng; thống kê là request riêng | Điểm, kỹ năng, hạng cùng cập nhật | Vừa | Đã sửa: refresh phối hợp và pending_formal_sessions; 43 test UI + 5 test PostgreSQL đạt | `08-analysis-pending.png` |
| 6 | Tải trang đăng nhập/bài làm | CSP chặn hai font nhúng data URL | Không có lỗi CSP; font phục vụ từ cùng nguồn | Vừa | Đã sửa: xuất font thành file, giữ CSP nghiêm ngặt | Console trình duyệt |
| 7 | Xem phân tích và cài đặt ở desktop | Toàn trang tràn ngang; cài đặt sát lề, chữ trợ giúp bị cắt | Bố cục vừa viewport cả desktop/390px | Vừa | Đã sửa; đọc ảnh sau sửa, scrollWidth bằng clientWidth cả 1521px và 375px | `08-analysis-pending.png`, `09-settings.png` |
| 8 | Mở Tổng quan Learner lần đầu | Nút bắt đầu nằm dưới phần biểu đồ; trạng thái chờ có nút sát link | Một hành động chính dễ thấy, nút chờ rõ ràng | Vừa | Đã sửa: nút bắt đầu trên đầu, bỏ nút lặp; nút chờ có kiểu dùng chung | `02-learner-dashboard.png`, `07-no-key-wait.png` |
| 9 | Làm SQL và đọc ngữ nghĩa trang bài thi | DDL một dòng dài; hai landmark main lồng nhau | DDL dễ đọc và một main | Thấp | Đã sửa: wrap DDL, bỏ main lồng | `05-sql-result.png` |
| 10 | Admin đọc CLO và duyệt tự luận | Nguồn gắn CLO hiển thị Không xác định; badge ESSAY | Nhãn nguồn gắn đúng và loại câu tiếng Việt | Vừa | Đã sửa nhãn. Kiểm tra lại: cấp tài khoản chỉ dành cho Admin theo UC04, mặc định này đúng hợp đồng và được giữ nguyên | `11b-clo-mapping.png`, `15-manual-review.png` |
| 11 | Hai tab cùng đăng nhập, reload đồng thời với access token ngắn hạn thật | Hai tab cùng xoay refresh token, server phát hiện replay và đăng xuất cả hai | Một lần xoay token dùng chung; không mất nháp | Cao | Đã sửa `ade433b`: Web Locks, đọc lại token sau khóa; 16 test auth đạt, kiểm lại browser giữ đăng nhập | `22-two-tabs-logout.png` |
| 12 | Tạo lại API container khi chuyển mode AI | API readiness đạt nhưng đăng nhập qua frontend trả 502 vì IP upstream cũ | Nginx cập nhật DNS Docker khi container thay đổi | Cao | Đã sửa `c84cb1e`: upstream resolve + zone, healthcheck kiểm cả proxy; nginx -t/readiness đạt | Log `provider-start`, ảnh lỗi đăng nhập |
| 13 | Provider AI lỗi khi đang chờ | Thông báo cần xử lý chấm điểm nhưng chưa nói rõ chờ giảng viên; Admin đọc JSON kỹ thuật để tìm feedback | Fallback giảng viên rõ, feedback/tiêu chí/trích dẫn dễ đọc | Vừa | Đã sửa; 31 test UI chấm/duyệt đạt | `discovery-ai/test-failed-1.png` |
| 14 | Gate CI chấm lại job lỗi | Test đọc object ORM cũ sau HTTP, rồi dùng now() của transaction trước retry; phụ thuộc vòng đời GC | Kiểm tra đúng dữ liệu đã commit và transaction mới của worker | Vừa / kiểm thử | Đã tái hiện bằng giữ tham chiếu job; sửa refresh và ranh giới transaction, giữ nguyên mọi assertion kết quả | `stale-job-repro.log`, `stale-job-fixed.log` |
| 15 | Smoke đổi từ Learner demo sang tài khoản của lượt kiểm | Xóa storage phía sau AuthProvider rồi goto login đua với redirect, gây ERR_ABORTED trên CI | Đăng xuất như người dùng, hoàn tất 204 và điều hướng trước đăng nhập mới | Vừa / kiểm thử | Đã sửa: bấm Đăng xuất, kiểm tra 204 và URL login; smoke 3/3 đạt, retries=0 | `smoke-final.log` |
| 16 | Browser test timeout AI rồi reload | Locator khớp một phần, nhận nhầm tiêu đề timeout là trạng thái giảng viên từ server | Chờ chính xác trạng thái server trước khi kiểm reload | Thấp / kiểm thử | Đã sửa: exact=true, không bỏ assertion; ca lỗi/timeout/chờ giảng viên lâu/công bố tự cập nhật đạt | `failure-exact.log` |
| 17 | Admin đọc nhật ký bài AI #8 | Hoàn tất chấm lúc 15:29 nhưng sự kiện nộp bài trước đó lại 15:30; now() lấy đầu transaction AI dài | Thời gian phản ánh lúc chuyển trạng thái; công bố và sự kiện dùng cùng mốc | Vừa | Đã sửa `9b1bf6a`: clock DB hiện tại, giữ nguyên lịch sử cũ; hồi quy PostgreSQL tái hiện đỏ rồi đạt, browser kiểm thứ tự events từ response công bố | `ai-feedback-before-timeline.png` |
| 18 | Điều phối gate local | Chạy đồng thời backend, browser, QA và seed mới trên một Docker; một response nộp SQL vượt mốc 20s của harness dù DB lưu đủ 13 câu | Gate trên một máy không tranh Docker với nhau | Thấp / kiểm thử | Chuyển sang chạy tuần tự các gate Docker, giữ nguyên timeout và assertion; ghi cách chạy trong README | `three-runs-audit-final.log` |

Không xóa hoặc giảm yêu cầu kiểm thử. Các assertion về chu kỳ polling/spinner được
cập nhật theo hành vi đúng mới và bổ sung kiểm tra backoff, timeout, chống chồng request.

| Lỗi | Commit sửa | File chính |
|---|---|---|
| 1, 4 | `d1ef46e`, `2b47c28` | `usePendingResults.js`, `EvidencePage.jsx`, `GradingStatusPanel.jsx` |
| 2, 3, 5 | `a94c8d8`, `2b47c28` | `StatisticsPanel.jsx`, `CumulativePage.jsx`, `DashboardPage.jsx`, `statistics_service.py` |
| 6–10 | `f9315af` | `index.css`, `vite.config.js`, `ExamPage.jsx`, `SettingsPage.jsx`, các trang Admin |
| 11 | `ade433b` | `frontend/src/api.js`, `AccessRenewal.test.jsx` |
| 12 | `c84cb1e` | `deploy/nginx.conf`, `docker-compose.local.yml` |
| 13 | `1f901f3` | `GradingStatusPanel.jsx`, `AdminGradingPage.jsx`, i18n |
| 14 | `0573e3c` | `backend/tests/test_supervisor_requirements.py` |
| 15 | `7da111d` | `frontend/e2e/local-smoke.spec.js` |
| 16 | `453fcc1` | `frontend/e2e/browser-qa.spec.js` |
| 17 | `9b1bf6a` | `grading_review.py`, `test_release_timestamps.py`, `browser-qa.spec.js` |

`382f85f` bổ sung provider HTTP giả, Compose override và journey hồi quy; không
đưa dữ liệu giả vào đường chạy ứng dụng. Không có xung đột Git trong đợt QA.

## Những bước đã kiểm tra trước sửa

- Làm đủ 13 câu bằng UI: 10 trắc nghiệm, hai SELECT chạy trong sandbox, một tự luận.
- Reload sau autosave khôi phục lựa chọn; đồng hồ tiếp tục giảm; hộp xác nhận nộp rõ ràng.
- Không có API key: chuyển sang chờ giảng viên; bài chờ chưa được tính vào phân tích.
- Admin mở dashboard, CLO, tài khoản, ngân hàng câu hỏi, bài đánh giá, hàng chờ chấm;
  duyệt SQL 5/5 + 5/5, sửa tự luận thành 4,25/5 rồi công bố.
- Lịch sử, thống kê và báo cáo sau tải lại dùng kết quả đã công bố, không lộ danh sách
  người khác trong bảng hạng của Learner.

## Đối chiếu số học độc lập

Bài #5: cố ý sai một trắc nghiệm JOIN; 9/10 trắc nghiệm + 10/10 SQL + 4,25/5 tự luận
= **23,25/25 = 93%**. Các câu được duyệt hiển thị đúng điểm thành phần.

- CLO SQL: 5/6 trắc nghiệm + 10/10 SQL = **15/16 = 93,75%**.
- CLO thiết kế: 4/4 trắc nghiệm + 4,25/5 tự luận = **8,25/9 = 91,67%**.
- An: (67 + 59 + 93) / 3 = **73%**, UI thống kê 73%.
- Cả nhóm: (67 + 59 + 95 + 47 + 93) / 5 = **72,2%**, UI Admin 72,2%.
- Phân bố Admin: [0, 0, 2, 1, 2] cho năm khoảng 20%, tổng **5 bài**; UI khớp.
- CLO tích lũy của An: SQL **35/48 = 72,92%**; thiết kế **19,75/27 = 73,15%**,
  UI khớp. Đây là tổng điểm có trọng số, không phải trung bình các khái niệm.

Trong journey hồi quy, mỗi tài khoản mới làm ba bài cùng thang 25 điểm. Admin
đổi điểm tự luận sau khi đọc điểm AI (4,38/5) hoặc chấm thủ công rồi công bố;
mọi phép tính sau đây dùng điểm chính thức. Bài đang chờ vẫn hiển thị riêng và
không làm tăng số bài đã công bố.

Trong harness, Admin chủ động đặt hai câu SQL thành 5/5 để kiểm luồng thay điểm;
đây không phải khẳng định mọi truy vấn người học đều khớp đáp án tham chiếu.
Đề chọn SQL thích ứng theo phần MCQ: bài thứ hai có thể phục vụ SQL WHERE thay
cho SQL SELECT. Điểm kỹ năng WHERE khi đó gộp cả MCQ và SQL (sau hai bài là
6/7 = 85,71%, thay vì chỉ lấy hai MCQ thành 1/2). Đối chiếu độc lập với dữ liệu
điểm/câu hỏi xác nhận không có sai lệch giữa profile và UI. So sánh tự động,
điểm bộ phận và SELECT nguy hiểm được kiểm riêng trong backend và bộ browser cũ.

| Chỉ số | Tính tay | Trên màn hình |
|---|---|---|
| Bài 1 | (9 MCQ + 10 SQL + 4,25 tự luận) / 25 | 93% ở kết quả, lịch sử, tổng quan, phân tích một bài |
| Bài 2 | (8 + 10 + 3) / 25 | 84%; tích lũy hai bài 88,5% |
| Bài 3 | (10 + 10 + 5) / 25 | 100%; tích lũy ba bài 92,33% |
| Trung bình ba bài | (93 + 84 + 100) / 3 = 277/3 | 92,33% |
| CLO SQL, ba bài | (15 + 14 + 16) / 48 = 45/48 | 93,75% |
| CLO thiết kế, ba bài | (8,25 + 7 + 9) / 27 = 24,25/27 | 89,81% |
| Admin sau hai journey | (67 + 59 + 95 + 47 + 2 × 277) / 10 | 82,2%; 10 bài, 5 học viên |
| Phân bố Admin | Hai bài 40–60%, một bài 60–80%, bảy bài 80–100% | [0, 0, 2, 1, 7], tổng 10 |
| Đồng hạng | Linh 95%; hai Learner QA cùng 92,33%; An 63%; Minh 47% | Hạng 1, 2, 2, 4, 5; Learner chỉ thấy hạng của mình 2/5 |

Snapshot báo cáo 10 bài được chụp trước ca provider lỗi riêng; ca đó sau khi
giảng viên chấm sẽ thêm một bài 93%, không bị tính nhầm vào snapshot trước.
Đọc lại UI sau ca này: **11 bài / 6 học viên**, **(822 + 93) / 11 = 83,18%**,
đúng với Admin hiển thị.

Assertion cũ yêu cầu 60 lần polling/5 phút đổi thành 20 lần có backoff; assertion
spinner còn chạy sau timeout đổi thành không chạy, đồng thời kiểm tra aria-busy=false,
thông báo giảng viên, giới hạn request treo và khởi động lại. Đây là cập nhật theo
yêu cầu đúng mới, không bỏ kiểm tra. `ResultRace.test.jsx` vẫn giữ nguyên và đạt.
`SupervisorWorkflows` được sửa fixture để trả đúng contract cho từng API, kiểm tra
một empty state và CTA thay cho khối rỗng lặp; smoke cũ đổi kiểm tra hạng ở bài đầu
thành kiểm tra phân tích một bài và không có xu hướng/hạng. 49 test UI liên quan đạt.
Hai browser assertion cũ trong `first-time-user-grading.spec.js` và
`supervisor-completion.spec.js` được cập nhật nhãn fallback/empty state; thêm kiểm
tra chờ giảng viên, tổng điểm chưa cuối cùng, CTA và không có điểm tích lũy giả.
CI còn phát hiện test retry giữ cache ORM. Tại
`backend/tests/test_supervisor_requirements.py:650`, thêm kiểm tra job ban đầu
failed/1, giữ tham chiếu để lỗi không phụ thuộc GC; tại dòng 664 đọc lại job và
kết thúc transaction đọc trước khi chạy worker. Giữ nguyên pending/0, 403, 409,
chấm lại và năng lực 100%. Không sửa hành vi ứng dụng để né assertion.

Harness giữ request AI giả đến khi browser thấy màn hình chờ, rồi trả sau 20 giây;
tránh trường hợp AI xong trong lúc Learner còn làm SQL. Chỉ fixture kiểm thử có
điều khiển này. Các locator trạng thái giảng viên dùng exact=true để không nhầm
với tiêu đề timeout phía client; bài kiểm tra reload vẫn giữ nguyên và đạt.

## Bằng chứng sau sửa

Ảnh sau sửa dưới đây từ các lượt QA đã đạt trên mã `9b1bf6a`; chỉ có tài khoản và dữ
liệu demo local. Provider giả giữ request cho đến khi UI thấy chờ, rồi trả sau
20 giây. Chờ timeout 5 phút và chờ giảng viên 6 phút dùng clock của Playwright;
hết hạn access token được đợi **61 giây thật**.

| Yêu cầu | Bằng chứng UI | Test hồi quy |
|---|---|---|
| AI đang chấm có spinner, ghi chú có thể rời trang, tự cập nhật | [Chờ AI](screenshots/ai-waiting.png), [chờ giảng viên không key](screenshots/instructor-waiting.png) | `browser-qa`: journey, `GradingWait`, `PendingResults` |
| AI chậm/lỗi không kẹt; có thử lại và giữ bài đã nộp sau reload | [Timeout](screenshots/ai-timeout.png), [provider lỗi](screenshots/ai-error.png), [công bố sau chờ lâu](screenshots/long-wait-published.png) | `AI failure and bounded waiting remain recoverable after reload` |
| 0 bài: một CTA bắt đầu, không có điểm giả | [Chưa có bài](screenshots/analysis-zero.png) | `shows one action and no invented statistics before the first published attempt` và journey |
| 1 bài: CLO/topic/độ khó và nhận xét riêng bài đó, chưa có xu hướng/hạng | [Một bài](screenshots/analysis-one.png) | `uses only single-assessment dimensions and advice with exactly one graded attempt` và journey |
| 2+ bài: tích lũy, tiến độ, skill gap/hạng; pending không được cộng | [Hai bài](screenshots/analysis-two.png), [ba bài](screenshots/analysis-three.png), [390px](screenshots/analysis-mobile.png) | Journey ba bài; `keeps pending attempts separate and reloads after a coordinated refresh` |
| Nháp/timer khôi phục, SQL SELECT chạy thật, nộp một lần | [Reload giữ nháp](screenshots/autosave-restored.png), [SQL bốn dòng](screenshots/sql-result.png) | Journey đủ 10 MCQ + 2 SQL + 1 tự luận và double-click nộp; browser lifecycle/timeout |
| Admin đọc AI, sửa điểm, công bố; Learner/analysis tự nhận; báo cáo nhất quán | [Phản hồi AI](screenshots/ai-feedback.png), [duyệt điểm](screenshots/instructor-review.png), [báo cáo](screenshots/admin-report.png) | Journey giữ hai tab kết quả/phân tích, duyệt ba câu và xuất CSV; đồng hạng 2, 2 |
| Hai tab gia hạn JWT thật không mất đăng nhập/nháp | Ảnh đầy đủ ở `_review/qa/browser/run-*-ai/` | `two tabs refresh expiring authentication without losing a saved draft` |
| Nhật ký AI không lùi thời gian sau nộp bài | [Trước sửa](screenshots/timeline-before.png), [sau sửa](screenshots/instructor-review.png) | `test_release_events_use_current_database_time_in_a_long_transaction` và mọi response công bố trong journey |

`ResultRace.test.jsx` ban đầu được giữ nguyên. Bộ 55 browser test còn kiểm 49
blueprint, CRUD quản trị, phân quyền, pass/timeout/nộp trùng, khôi phục mật khẩu
qua Mailpit, ngôn ngữ, accessibility và viewport 390/768/1024/1440px.

## Cổng kiểm tra sau cùng

Số liệu máy đọc được: [gate-results.json](gate-results.json), mã ứng dụng
`9b1bf6a`. Chạy các gate Docker lần lượt trên cùng máy; giữ
nguyên timeout và assertion sau sự cố tranh tài nguyên ở lỗi 18.

| Gate | Kết quả | Thời gian |
|---|---|---|
| Backend lint / build / pip check | Đạt | — |
| Backend toàn bộ | **1179/1179**, 0 failed/errors/skipped | 1.022,25 s |
| Frontend npm ci / build | Đạt; audit 0 lỗ hổng | — |
| Frontend toàn bộ | **322/322**, 37 suite, 0 failed | 198,20 s |
| Browser hồi quy toàn bộ | **55/55**, 0 failed/skipped/flaky, retries=0 | 1.734,87 s |
| Smoke local liên tiếp | **3/3**, 0 failed/skipped/flaky, retries=0 | 106,23 s |
| Launcher / OpenAPI / inventory | **3/3**; contract và danh mục khớp mã | — |
| Checkout sạch không .env | npm start tự sinh secret, migrate/seed; 4 service healthy, 2 job exit 0; hai demo login qua UI đạt | — |

Mỗi lượt dưới reset DB, chạy hành trình Learner/Admin không key, rồi hành trình
AI bằng một học viên mới; mỗi hành trình làm ba bài MCQ/SQL/tự luận. Thêm ca AI
lỗi/timeout/chờ giảng viên lâu và hai tab hết hạn JWT. Tổng **12/12**, tương ứng
**3/3 lượt ở cả hai chế độ**, không retry che lỗi.

| Lượt DB sạch | Không key | AI + phục hồi + hai tab | Failed / flaky / retry | Thời gian test |
|---|---|---|---|---|
| 1 | 1/1 | 3/3 | 0 / 0 / 0 | 433,96 s |
| 2 | 1/1 | 3/3 | 0 / 0 / 0 | 436,92 s |
| 3 | 1/1 | 3/3 | 0 / 0 / 0 | 417,82 s |

Thời gian Playwright không gồm build/migrate/seed. Có một cảnh báo deprecation
Starlette/httpx ở backend và cảnh báo scrollTo của jsdom; không phải lỗi trên UI
Chromium. [CI của mã ứng dụng](https://github.com/nguyendodary/DBCAS/actions/runs/41415155355)
xanh cả backend và frontend, gồm startup không .env, smoke ba lượt và QA ba lượt.

## Cách chạy và giới hạn

Từ repo develop2 chạy `npm start`; UI http://localhost:18080, Swagger
http://localhost:18000/docs, Mailpit http://localhost:18025. Demo
`admin@dbcas.local` và `learner@dbcas.local`, mật khẩu `Demo12345!`.
`npm run stop` để dừng; `npm run reset` xóa DB demo và tạo lại.
Các lệnh backend/frontend/browser nằm trong [README](../../README.md).
`npm run test:qa` lặp ba lượt và xóa DB demo; `npm run test:smoke` lặp smoke ba lần.

- Kiểm trên Windows + Docker Linux qua WSL, Chromium desktop và giả lập 390px;
  không khẳng định đã kiểm thiết bị di động thật hoặc Safari/Firefox.
- Chưa có key LLM thật: provider HTTP giả local có độ trễ/lỗi kiểm luồng API,
  schema JSON, worker và UI; chưa kiểm chất lượng chấm của model trả phí.
- Chỉ local một máy; chưa load test hoặc nghiệm thu production/cloud.

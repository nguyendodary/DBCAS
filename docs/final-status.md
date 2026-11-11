# Trạng thái DBCAS — develop2

## OAuth/root-cause audit — yêu cầu 20261112, thực hiện 2026-11-11

Google/GitHub đã trở lại trên Login/Register, sáng/tối và Việt/Anh, cả 1280/390.
Nguyên nhân chính xác là `b4313b5`: lọc provider chưa cấu hình rồi return null,
đồng thời đổi regression thành mong đợi ẩn nút. Sửa ở `58e2bd6`; callback Compose,
kiểm tra redirect và phiên OAuth xoay vòng cũng đã được sửa. Gate cấu hình ở
`a8b1fc9`; tránh retry lỗi thông tin đăng nhập ở `bbc272a`; quarantine ở `371b751`.

| Bằng chứng mới đã đo | Kết quả |
| --- | --- |
| Backend đầy đủ | 1464/1464, 1360.92s; sau thay đổi cuối chạy lại 111/111, 38.83s |
| Frontend | 366/366 (42 file, 84.11s); ci/lint/format/build/audit PASS, build 1.70s, audit 0 lỗ hổng |
| OAuth browser lặp ba lần | 48/48, 2.6m; gồm flow fake local, lỗi consent/email/provider, hai theme/ngôn ngữ/kích thước và axe |
| Điều hướng demo | 24/24 role/route/width; 0 lỗi trang, request thất bại, API bất thường, overflow |
| Tài khoản | 4/4 disable/re-enable; reset quản trị Việt/Anh, hủy, đổi mật khẩu, thu hồi access/refresh cũ và đăng nhập lại PASS |
| Browser mặc định | 77/77, 33.1m; không lỗi/skip/retry |
| Word | 31 thay đổi text tiếng Anh trong đúng 3 v1.2; giữ toàn bộ run/định dạng/media/tên/ngày và ZIP part khác; sửa 2 field caption, cập nhật 4 số trang; Word 3/3, 59/70/40 trang, cache TOC/TOF ổn định |
| Fresh clone | Không có .env trước startup; 16 trạng thái auth, 32 thông báo provider, 2/2 demo login; 0 lỗi trang/request ngoài |
| Cleanup | Kiểm kê 36 mục gốc, 0 lỗi scan; 7 mục / 367401 byte trong `_trash-20261112`; chưa xóa vĩnh viễn, thu hồi dung lượng 0 byte |
| LLM key mới | 3/5 request, cả ba HTTP 403; token không được provider báo; model/chất lượng chưa xác minh; builder purity/hash và fallback PASS |

[Root-cause audit](qa/root-cause-audit-20261112.md),
[ảnh trước/sau](qa/oauth-20261112/screenshots/README.md),
[kiểm kê KEEP/DELETE/ASK](qa/workspace-inventory-20261112.md),
[Word edit manifest](qa/oauth-20261112/word-edits.json).
Browser đầy đủ, fresh clone, demo rebuild và CI của HEAD cuối là gate phát hành;
kết quả cuối được ghi trong handover và phản hồi bàn giao. Các checkpoint bên
dưới là lịch sử. Không gọi lại provider thật trong vòng kiểm tra này.

## Historical sole-writer checkpoint — 2026-11-10

Recovery is complete. W4 now has **102 reviewed images / 25 screen states**
in both themes, SQL at four widths, **186/186 contrast pairs**, and **0 page
overflow/errors**. Final visual fixes are `26d7e6d`, evidence `7301a7f`.
W8 audited the unchanged English Word v1.2 packages against the final schema,
Compose, OpenAPI, routes, AI pipeline and mandatory approval workflow:
**Word COM 3/3 PASS**, zero mismatches or Vietnamese paragraphs. No
architecture element or approved diagram changed.

| Current measured evidence | Result |
| --- | --- |
| Verified unchanged backend/AI | Green CI `42825915679`, `9f3cd92`: **1455/1455, 1148.02s**; includes 141 purity/hash/fallback checks |
| Verified browser/provider baseline | Same green CI: **55/55** browser, **39/39** fake-provider across three repeats, **3/3** smoke, **7/7** launcher |
| Changed frontend checks | Auth **38/38**; final affected components **32/32, 9.64s**; lint/format/build PASS, build **716ms** |
| New UI regressions | Landing **1/1, 1.8s**; final visual cases **4/4, 3.6s**, no retries; OAuth callback regression added |
| Current visual evidence | **102 images**, source/hash/dimensions recorded; every image viewed and described, dark parity checked |
| Documents | **46 project + 41 Word assertions + 10 diagram gates PASS**; local Word open/field verification **3/3** |
| Fresh isolated clone/demo | No initial `.env`; reset **186.32s**, initial start **17.32s**, final UI start **26.26s**; health/readiness **200/200**; learner/admin logins/settings **2/2**, 0 page errors |
| Real request cap | One confirmed rejected request + one conservatively consumed unverified attempt; **0 slots remaining**, quality unverified |

The final pushed-HEAD CI result is authoritative in
[develop2 Actions](https://github.com/nguyendodary/DBCAS/actions?query=branch%3Adevelop2);
it is pending when this documentation checkpoint is published. The final
handover response records its actual run ID/counts after completion.
No unchanged long suite was repeated locally. The original four healthy
`dbcas-local` containers keep their IDs; the refreshed demo is at
**http://localhost:19180**, API 19100, Mailpit 19125.

See [W1–W8 evidence](qa/final-20261110/README.md),
[screenshot index](qa/final-ui/screenshots.md),
[per-image review](qa/final-ui/visual-review.md),
[Word audit](qa/final-20261110/word-audit.md) and
[demo script](demo/demo-script.md). Live-model quality, external OAuth
credentials and production load remain unverified. Human meeting,
signature/reflection and Jira fields remain owner-supplied.

## Historical initial completion checkpoint — 2026-11-10

The following measurements preserve the interrupted initial round. Its
browser migration failures were subsequently resolved and verified by green
`9f3cd92`; they are not current open W5 failures.

The final round delivered the UI system (self-hosted Inter + JetBrains Mono,
semantic light/dark tokens, AA contrast gate), the SQL question workspace
(prompt/schema cards, editor, scoped results), the Vietnamese/English copy
audit, AI pipeline purity/hash hardening, and an evidence-based cleanup.

**Result release is one mandatory flow:** AI grades/evaluates first, then the
administrator reviews the SQL/essay evidence, may adjust any score with a
reason, and approves; only approved results are published and counted. The
old automatic/admin choice is not present in the code or UI. This is the
owner correction recorded in `docs/qa/handover.md` on 2026-11-09; the README,
glossary and admin system page now match it.

| Measured gate (2026-11-10) | Result |
| --- | --- |
| Backend lint/build/pip | PASS, no broken requirements |
| Backend targeted flow/AI/essay | **241/241**, 244.17 s |
| AI purity/hash suites | **141/141**, 18.91 s |
| Frontend unit | **351/351**, 40 files, 60.15 s |
| Frontend lint/format/build/audit | PASS; build 0.92 s; **0 vulnerabilities** |
| Light/dark contrast gate | PASS for all text and chart tokens |
| Docs check + Word verify | `docs:check` PASS; `docs:verify-word` **3/3** |
| UI evidence | `docs/qa/final-ui/` SQL, dashboard, admin at 390/768/1280/1920, light/dark |
| Cleanup | 8.7 MB rejected diagram set + unused brand/font assets removed; report in `docs/qa/cleanup-report.md` |
| Full backend | **1455/1455**, 28:59 (the 18 legacy fixtures were pinned to `IMMEDIATE`; affected files 115/115) |
| Browser, mandatory flow | `test:practice` **6 passed / 3 skipped**, 4.2 min, including admin SQL check, score adjustment with reason and approval at 1440/390 |
| Browser, default suite | **14 passed / 15 failed / 10 did not run**; 13 failures are pre-mandatory-review specs that never approve the session. Migration remains open |
| Live AI | 1 real evaluator call; builder/evaluator hash matched; provider `llm_auth_failed`; rule fallback returned 5 comments |
| CI (run `42681385886`, `f99855a`) | backend **PASS** 15m19s; frontend-local lint/format/unit/build/audit/test:local/inventory/docs **PASS**; `test:e2e` **21 passed / 24 failed / 10 did not run** because the legacy specs still assert automatic publication. The mandatory `test:practice` suite is green |

Details: `docs/qa/ux-copy-audit.md`, `docs/qa/ai-pipeline-audit.md`,
`docs/qa/cleanup-report.md`, `docs/qa/handover.md`.

## Historical checkpoint — 2026-11-05

**Overall acceptance is NOT met:** final live run7 passes; run8 falls back
during generation and fails the unchanged strict assertion. The ledger is
**70/80 actual requests (30 this continuation),10 remaining**. A passing full
run used16, so live calls stopped without raising/resetting the cap. The saved
attempt still contains exactly3 validated bank questions with disclosed fallback.

The45 engineering/QA titles currently count **21 Verified OK /23 Fixed /1 Still
failing (5.8)**. All25 document-only IDs remain excluded; Jira server statuses
are Unknown. The complete current issue table is in [task audit](qa/task-audit.md).

| Measured gate | Result |
| --- | --- |
| Bank, unchanged verified content |5482 questions:2006MCQ/1747SQL/1729essay;80concepts;720cells each>=7;6988 repeated SQL executions |
| Exact-count guarantee |2268700/2268700; counts1–20, default5; disclosed widening and validated bounded recovery |
| Full backend before endpoint repair |1393/1393,769.93s,0failed/skipped; current endpoint/provider/meter regression146/146,17.06s |
| Production application entrypoint |13/13,320.910s; original240s scenario deadline/edit-before-save restored and targeted1/1,91.586s |
| Three consecutive fake repeats |39/39,1130.341s;0fail/skip/flaky/retry |
| Final clean clone |npm ci root40s/UI17s; no.env then one npm start;4/4 logins,5482questions/80concepts, SQL/no-key fallback,390px,0pageerrors |
| Final consecutive smoke |3/3,205.638s;13-question learner/admin work and real Mailpit reset;0fail/skip/flaky/retry |
| Current live runs |run7 1/1,130.612s;run8 0/1,110.990s; consecutive live criterion FAILED |
| Controlled load |8x20 questions,259HTTP/42.186s;8published/8ownership denials;SQLpeak4/providerpeak2;3025ms timeout and size rejections |
| Final pushed-HEAD CI |Required after this report commit; authoritative status is the [develop2 workflow](https://github.com/nguyendodary/DBCAS/actions?query=branch%3Adevelop2). Local completed totals go to `_review/audit-20261105/final-ci-results.json` |

This continuation fixed pre-SQL transport recovery (`3b3994f`), restored current
browser fixtures (`5b67ca0`), and prevented duplicate completion paths (`d4a541c`).
No production resource/retry/token limit or domain validation was loosened.
Existing.env files, old question definitions, published evidence and unrelated
stacks were preserved. The new clone project is stopped with volumes retained;
the live project is provider-disabled.

Reported provider usage:98048 input/26165 output tokens across33 reported calls;
37 other calls have129810 input-token estimates and no reported output usage.
Mean wire latency3576.04ms/p9510138ms/max12199ms. HTTP totals33x200,32x400
(mandatory-reasoning compatibility responses included),4x404 and1ReadTimeout;
failed historical probes are retained. Key/model stay private.

Frontend audit0 vulnerabilities; installed Python audit passes. Root diagram
tooling retains2low/0high-critical advisories. Chromium/desktop/390px coverage
does not establish physical-device or broad educational-model quality. Run8's
precise extraction/validation reason was not retained after container cleanup.

See the [handover](qa/handover.md), [measured checkpoint](qa/final-20261105/README.md)
and [live-budget rules](qa/real-provider-runbook.md). Older figures below are
historical; they must not replace this failed live acceptance result.

## Historical status — 2026-11-03 and earlier

> Tiếp quản ngày 03/11: xem [handover mới nhất](qa/handover.md) và
> [báo cáo/ảnh QA bổ sung](qa/continuation-20261103/README.md).
> Gate local trước guard fixture cuối: backend **1251/1251**, frontend **344/344**, clone không
> `.env` khởi động và hoàn thành bài với fallback. Nghiệm thu real-key ba lượt
> chưa thực hiện vì chưa đối soát được số request cũ; phần tiếp quản dùng **0**.
> Các số đo bên dưới là lịch sử tại commit được ghi, không phải kết quả real-key.

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
- Python host 3,14 và container 3,13; cảnh báo deprecation Starlette/httpx đã được loại bỏ bằng `httpx2==2.16.0` trong `requirements-dev.txt` (2026-11-09); CI ghi hai log Maintenance OperationalError lúc teardown DB kiểm thử dùng một lần, sau khi các ca đã đạt; không có lỗi JavaScript trong các scenario. Không có triển khai production/cloud.

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

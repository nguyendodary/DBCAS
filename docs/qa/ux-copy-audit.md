# Vietnamese UX copy audit

## Final authentication correction — 2026-11-10

The shared desktop introduction still promised that difficulty changed after
each response. Current learner-defined attempts freeze the selected scope.
Three keys in each locale now describe chosen concepts/difficulty/count and
administrator approval, without changing keys or interpolation. A real-browser
regression verifies both rendered translations; the refreshed authentication
captures verify wrapping. These six value changes are separate from the
historical counts below.

## Final landing correction — 2026-11-10

Visual review found two retired prototype claims: 60 minutes and a fixed
13-question allocation. The landing now shows **30 default minutes** and
**up to 20 questions**, with **1–20 / default 5** in both languages. The
results paragraph now states that administrator approval precedes results.
This continuation changes nine locale values and two numeric constants;
the initial audit counts below are preserved as historical measurements.

The real browser regression failed on the old 60/13 values, then passed
for English/Vietnamese, light/dark and 1280/390 widths: **1/1, 1.8s**, no
page overflow, no retries. The same check protects flat light surfaces and
the existing dark surfaces. Source: `LandingPage.jsx`, both locale catalogs,
and `frontend/e2e/localization.spec.js`.

## Initial W3 audit

**Scope:** `frontend/src/i18n/vi.json` and `en.json` (learner and admin UI), plus a read-only sweep of `frontend/src/components` and `frontend/src/pages` for hardcoded user-facing copy.  
**Date:** 2026-11-10 · **Branch:** `develop2`  
**Out of scope (not edited):** backend, database, `package.json`, CSS, `docs/academic`, and all component/page files.

## Method

1. Read every leaf string in both locales (including plural forms) and checked interpolation tokens.
2. Reviewed copy as Vietnamese product copy: natural phrasing, one term per concept, sentence case, verb-led actions, helpful empty/error states, no English leftovers, correct diacritics and punctuation.
3. Checked the English locale independently for the same qualities rather than treating it as a literal translation.
4. Applied surgical value edits only; no key renames, no structural changes, no interpolation changes.
5. Grepped components/pages for hardcoded Vietnamese/English text nodes, `aria-label`, `placeholder`, `title` and `alt`; did not edit those files.
6. Located the backend error surface at `backend/app/errors.py`: API errors carry a machine `code` and an English fallback `message`; the frontend localizes by code. No backend edit needed.

## Counts

| Measure | Count |
|---|---:|
| Leaf strings reviewed per locale | 1,278 |
| Leaf strings reviewed (both locales) | 2,556 |
| Values changed — Vietnamese | 64 |
| Values changed — English | 95 |
| Values changed — total | 159 |
| Unique keys changed | 140 |
| Keys changed in both locales | 19 |
| Hardcoded user-facing occurrences | 136 |
| Files with hardcoded copy | 15 |
| Hardcoded files edited | 0 |

Four keys (`sql.noRows`, `sql.schemaHint`, `sql.tableSummary`, `sql.sampleRows`) were added by concurrent frontend work during the audit. They were reviewed, are correct in both locales, and were left unchanged.

Two Vietnamese labels (`exam.submit`, `sql.run`) were also changed by concurrent work. They were left untouched and are excluded from the counts below.

Three English labels (`supervisor.comments`, `admin.questions.addOption`, `admin.questions.search`) were left unchanged because existing tests assert the old text. Update the tests and the copy together; changing only the locale would break those contracts.

## Terminology decisions

- **bài đánh giá** = an assessment; **bài luyện tập / luyện tập** = practice. Adaptive practice is “bài luyện tập thích ứng”, not an official assessment.
- **khái niệm**, **độ khó**, **chuẩn đầu ra**, **mức chuẩn** (benchmark), **bằng chứng** (evidence), **giảng viên duyệt** (instructor approval).
- **lần làm bài** for one attempt; **lượt làm bài** for a count. Removed “phiên” where it meant an attempt.
- **bài tự luận** everywhere; removed “bài luận”, “bài trả lời viết”.
- Approval is **duyệt**; removed “rubric”, “Admin” and “minh chứng” leftovers.
- English uses **benchmark** for the configured threshold, **instructor** for the human reviewer, and US spelling (`practice`, `practicing`). The legacy “Grader comments” label is test-locked and remains for now.

## Changed strings — Vietnamese

| Key | Before | After | Reason |
|---|---|---|---|
| `analytics.singleHelp` | Điểm mạnh và nội dung cần ôn của bài đã công bố duy nhất này, theo chuẩn đầu ra, chủ đề và độ khó. | Điểm mạnh và nội dung cần ôn của bài đã công bố này, theo chuẩn đầu ra, chủ đề và độ khó. | Bỏ “duy nhất” thừa. |
| `analytics.unknownClo` | {{count}} câu lịch sử chưa có chuẩn đầu ra tại thời điểm làm bài. | {{count}} câu trả lời cũ chưa có chuẩn đầu ra tại thời điểm làm bài. | Dùng “câu trả lời cũ” tự nhiên hơn “câu lịch sử”. |
| `supervisor.retryGrading` | Thử chấm lại câu bị lỗi | Thử chấm lại bài bị lỗi | Lỗi chấm áp dụng cho cả bài nộp, không chỉ một câu. |
| `supervisor.unavailableSelection` | Chưa có bài đánh giá đang mở cho nhóm kỹ năng này. Hãy chọn nhóm kỹ năng được hỗ trợ. | Nhóm kỹ năng này chưa có bài đánh giá nào đang mở. Hãy chọn một nhóm kỹ năng được hỗ trợ. | Câu chủ động, ngắn hơn; bỏ vế phủ định đặt trước. |
| `supervisor.humanHelp` | Kết quả chính thức được công bố sau khi người chấm có quyền xác nhận và công bố. | Kết quả chính thức được công bố sau khi giảng viên có quyền xác nhận và công bố. | Thống nhất “giảng viên” cho người có quyền xác nhận và công bố. |
| `supervisor.pending_review` | Chờ người chấm xác nhận | Chờ giảng viên duyệt | Thống nhất thuật ngữ “giảng viên duyệt”; bỏ “người chấm/xác nhận”. |
| `supervisor.reviewed` | Đã xác nhận — sẵn sàng công bố | Đã duyệt — sẵn sàng công bố | Thống nhất thuật ngữ “giảng viên duyệt”; bỏ “người chấm/xác nhận”. |
| `supervisor.pendingHelp` | Câu trả lời đã được lưu. Kết quả chính thức sẽ hiển thị sau khi chấm và xác nhận nếu cần. Hãy làm mới để kiểm tra trạng thái. | Câu trả lời đã được lưu. Kết quả chính thức sẽ hiển thị sau khi chấm và duyệt nếu cần. Hãy làm mới để kiểm tra trạng thái. | Thống nhất thuật ngữ duyệt. |
| `supervisor.reviewDetails` | Chi tiết xác nhận bài làm | Chi tiết duyệt bài làm | Thống nhất thuật ngữ “giảng viên duyệt”; bỏ “người chấm/xác nhận”. |
| `supervisor.reviewPages` | Trang danh sách bài chờ chấm | Trang danh sách bài chờ duyệt | Thống nhất thuật ngữ “giảng viên duyệt”; bỏ “người chấm/xác nhận”. |
| `supervisor.queueEmpty` | Không có bài làm chờ xác nhận | Không có bài làm chờ duyệt | Thống nhất thuật ngữ “giảng viên duyệt”; bỏ “người chấm/xác nhận”. |
| `supervisor.publish` | Công bố kết quả đã xác nhận | Công bố kết quả đã duyệt | Thống nhất thuật ngữ “giảng viên duyệt”; bỏ “người chấm/xác nhận”. |
| `supervisor.optionalReview` | Xác nhận tùy chọn | Duyệt tùy chọn | Thống nhất thuật ngữ “giảng viên duyệt”; bỏ “người chấm/xác nhận”. |
| `supervisor.requiredReview` | Bắt buộc xác nhận | Bắt buộc duyệt | Thống nhất thuật ngữ “giảng viên duyệt”; bỏ “người chấm/xác nhận”. |
| `supervisor.rubric` | Thang tiêu chí chấm điểm | Thang chấm điểm | Rút gọn thành “thang chấm điểm”. |
| `supervisor.finalScore` | Điểm đã xác nhận | Điểm đã duyệt | Thống nhất thuật ngữ “giảng viên duyệt”; bỏ “người chấm/xác nhận”. |
| `supervisor.comments` | Nhận xét của người chấm | Nhận xét của giảng viên | Thống nhất thuật ngữ “giảng viên duyệt”; bỏ “người chấm/xác nhận”. |
| `supervisor.recurring` | Thiếu hụt qua các bài đánh giá | Khoảng trống kỹ năng qua các bài đánh giá | Dùng “khoảng trống kỹ năng” thay “thiếu hụt”. |
| `common.pageOf` | Trang {{page}} / {{pages}} | Trang {{page}}/{{pages}} | Định dạng phân trang gọn “1/5”. |
| `errors.review_conflict` | Người chấm khác đã cập nhật bài làm. Hãy làm mới trước khi tiếp tục. | Giảng viên khác đã cập nhật bài làm. Hãy làm mới trước khi tiếp tục. | Thống nhất thuật ngữ “giảng viên duyệt”; bỏ “người chấm/xác nhận”. |
| `errors.invalid_review_score` | Nhập điểm từ không đến điểm tối đa của câu hỏi. | Nhập điểm từ 0 đến điểm tối đa của câu hỏi. | Dùng “0” thay “không” cho rõ nghĩa. |
| `auth.forgotSubtitle` | Nhập email tài khoản; nếu tài khoản tồn tại, chúng tôi sẽ gửi liên kết đặt lại. | Nhập email tài khoản. Nếu tài khoản tồn tại, chúng tôi sẽ gửi liên kết đặt lại. | Tách câu, bỏ dấu chấm phẩy. |
| `auth.oauthDisabled` | Một số phương thức đăng nhập chưa được cấu hình nên chưa thể sử dụng. | Một số phương thức đăng nhập chưa được cấu hình trên máy chủ này. | Bỏ vế lặp “chưa cấu hình nên chưa dùng được”. |
| `auth.oauthEmail` | Tài khoản liên kết chưa cung cấp email đã xác minh. Vì vậy, DBCAS chưa thể liên kết tài khoản an toàn. | Tài khoản liên kết chưa cung cấp email đã xác minh nên DBCAS chưa thể liên kết tài khoản một cách an toàn. | Bỏ “Vì vậy,” mang giọng dịch máy. |
| `auth.introBody` | Đánh giá năng lực cơ sở dữ liệu qua trắc nghiệm, SQL và tự luận, với câu hỏi thích ứng và minh chứng rõ ràng. | Đánh giá năng lực cơ sở dữ liệu qua trắc nghiệm, SQL và tự luận, với câu hỏi thích ứng và bằng chứng rõ ràng. | Thống nhất “bằng chứng” thay cho “minh chứng”. |
| `auth.namePlaceholder` | Nhập họ và tên | Nhập họ và tên… | Thêm … cho đồng bộ placeholder. |
| `assessment.emptyBody` | Hiện chưa có bài đánh giá nào dành cho bạn. Hãy quay lại sau nhé. | Hiện chưa có bài đánh giá nào dành cho bạn. Vui lòng quay lại sau. | Bỏ “nhé” để giữ giọng trung tính. |
| `assessment.pastSessions` | Xem lại các lần làm bài trong | Xem các lần làm bài trước trong | Sửa câu lặp “lịch sử làm bài”. |
| `assessment.historyLink` | lịch sử làm bài | lịch sử | Sửa câu lặp “lịch sử làm bài”. |
| `gradingWait.gradingTitle` | Đang chờ AI chấm bài... | Đang chờ AI chấm bài… | Dùng ký tự dấu ba chấm … thống nhất. |
| `gradingWait.reviewedTitle` | Người chấm đã xác nhận | Giảng viên đã duyệt | Thống nhất thuật ngữ “giảng viên duyệt”; bỏ “người chấm/xác nhận”. |
| `gradingWait.failedTitle` | Bài nộp cần được xử lý chấm điểm | Bài nộp cần được chấm lại | Tiêu đề ngắn, nêu đúng thao tác “chấm lại”. |
| `gradingWait.history` | Mở Lịch sử bài đánh giá | Mở lịch sử bài đánh giá | Viết thường giữa câu. |
| `exam.adaptive` | Bài đánh giá thích ứng | Bài luyện tập thích ứng | Luyện tập thích ứng không phải bài đánh giá chính thức. |
| `dashboard.session` | Phiên làm bài | Lần làm bài | Thống nhất “lần làm bài” thay cho “phiên”. |
| `dashboard.summary` | Tóm tắt phiên làm bài | Tóm tắt lần làm bài | Thống nhất “lần làm bài” thay cho “phiên”. |
| `cumulativeView.detailsHint` | Tìm hoặc lọc theo mức mục tiêu, sau đó mở một khái niệm để xem ý nghĩa kết quả và nội dung nên ôn tiếp. | Tìm hoặc lọc theo mức chuẩn, sau đó mở một khái niệm để xem ý nghĩa kết quả và nội dung nên ôn tiếp. | Thống nhất “mức chuẩn” thay cho “mục tiêu”. |
| `cumulativeView.filter` | Lọc theo mức mục tiêu | Lọc theo mức chuẩn | Thống nhất “mức chuẩn” thay cho “mục tiêu”. |
| `cumulativeView.met` | Đạt mục tiêu | Đạt mức chuẩn | Thống nhất “mức chuẩn” thay cho “mục tiêu”. |
| `cumulativeView.neutral` | Chưa có mục tiêu | Chưa có mức chuẩn | Thống nhất “mức chuẩn” thay cho “mục tiêu”. |
| `evidence.heroEyebrow` | HỌC VIÊN · MINH CHỨNG | HỌC VIÊN · BẰNG CHỨNG | Thống nhất “bằng chứng” thay cho “minh chứng”. |
| `admin.accounts.searchPlaceholder` | tìm theo tên hoặc email… | Tìm theo tên hoặc email… | Viết hoa đầu placeholder. |
| `admin.accounts.allRoles` | mọi vai trò | Mọi vai trò | Viết hoa lựa chọn lọc. |
| `admin.accounts.allStatuses` | mọi trạng thái | Mọi trạng thái | Viết hoa lựa chọn lọc. |
| `admin.curriculum.model` | Khái niệm | Thêm khái niệm | Tiêu đề biểu mẫu rõ hành động “Thêm khái niệm”. |
| `admin.curriculum.searchPlaceholder` | tìm theo mã hoặc tên… | Tìm theo mã hoặc tên… | Viết hoa đầu placeholder. |
| `admin.questions.legacyRubric` | Rubric 3 mức cũ | Thang chấm ba mức cũ | Thay “rubric” bằng thuật ngữ tiếng Việt “thang chấm”. |
| `admin.questions.legacyRubricHint` | Ngừng sử dụng — chấm theo rubric 3 mức lịch sử. | Ngừng sử dụng — chấm theo thang ba mức cũ. | Thay “rubric” bằng thuật ngữ tiếng Việt “thang chấm”. |
| `admin.questions.promptPlaceholder` | Nội dung câu hỏi | Nhập nội dung câu hỏi… | Placeholder hướng dẫn thay vì lặp lại nhãn. |
| `admin.questions.idsHint` | ID khái niệm, ví dụ: 1,2 | ID khái niệm, ví dụ: 1, 2 | Thêm khoảng trắng sau dấu phẩy. |
| `admin.assessments.selectConcept` | — chọn khái niệm — | — Chọn khái niệm — | Viết hoa sau dấu gạch. |
| `authoring.draftTranslation` | Bản dịch nháp - cần duyệt; thay đổi chưa duyệt sẽ không được lưu. | Bản dịch nháp, cần duyệt; thay đổi chưa duyệt sẽ không được lưu. | Thay gạch nối bằng dấu phẩy. |
| `authoring.preparingDraft` | Đang chuẩn bị bản nháp... | Đang chuẩn bị bản nháp… | Dùng ký tự dấu ba chấm … thống nhất. |
| `help.context.history.title` | Lịch sử đánh giá | Lịch sử làm bài | Thống nhất “lần làm bài” thay cho “phiên”. |
| `help.context.history.body` | Lịch sử liệt kê các phiên và trạng thái công bố. Chọn một phiên để xem bằng chứng khi kết quả đã công bố. | Lịch sử liệt kê các lần làm bài và trạng thái công bố. Chọn một lần làm bài để xem bằng chứng khi kết quả đã công bố. | Thống nhất “lần làm bài” thay cho “phiên”. |
| `help.section.essay` | Bài luận và xử lý AI | Tự luận và xử lý AI | Thống nhất “bài tự luận”; bỏ “bài luận/bài trả lời viết”. |
| `help.overview.body` | DBCAS là nền tảng đánh giá PostgreSQL song ngữ. Hệ thống kết hợp câu hỏi trắc nghiệm, SQL và bài luận, chấm theo nội dung đã duyệt và báo cáo bằng chứng theo từng kỹ năng. | DBCAS là nền tảng đánh giá PostgreSQL song ngữ. Hệ thống kết hợp câu hỏi trắc nghiệm, SQL và bài tự luận, chấm theo nội dung đã duyệt và báo cáo bằng chứng theo từng kỹ năng. | Thống nhất “bài tự luận”; bỏ “bài luận/bài trả lời viết”. |
| `help.types.essayTitle` | Bài trả lời viết | Bài tự luận | Thống nhất “bài tự luận”; bỏ “bài luận/bài trả lời viết”. |
| `help.types.essayBody` | Trình bày lập luận trong giới hạn từ. Bài luận có thể được chấm tự động và, tùy chính sách, được người duyệt kiểm tra. | Trình bày lập luận trong giới hạn từ. Bài tự luận có thể được chấm tự động và, tùy chính sách, được giảng viên kiểm tra. | Thống nhất “bài tự luận”; bỏ “bài luận/bài trả lời viết”. |
| `help.essay.body` | Soạn câu trả lời trong ô. Bản nháp được lưu riêng với việc nộp bài, nên bạn có thể làm mới trang hoặc quay lại phiên mà không mất nội dung chưa nộp. | Soạn câu trả lời trong ô. Bản nháp được lưu riêng với việc nộp bài, nên bạn có thể làm mới trang hoặc quay lại bài làm mà không mất nội dung chưa nộp. | Dùng “bài làm” thay “phiên”. |
| `help.essay.review` | Khi bài yêu cầu người duyệt, quản trị viên sẽ kiểm tra bằng chứng SQL và bài luận trước khi công bố. Điểm có thể được xác nhận hoặc điều chỉnh kèm nhận xét được lưu. | Khi bài yêu cầu duyệt, giảng viên sẽ kiểm tra bằng chứng SQL và bài tự luận trước khi công bố. Điểm có thể được xác nhận hoặc điều chỉnh kèm nhận xét được lưu. | Thống nhất “bài tự luận”; bỏ “bài luận/bài trả lời viết”. |
| `help.results.body` | Mọi bài luyện tập đã công bố được tính vào năng lực tích lũy. Kết quả chờ chấm hoặc duyệt chưa được tính. | Mọi bài đánh giá chính thức đã công bố được tính vào năng lực tích lũy. Kết quả chờ chấm hoặc duyệt chưa được tính. | Sửa mâu thuẫn: chỉ bài chính thức đã công bố mới tính vào năng lực. |
| `help.admin.item3` | Mọi bài nộp đều do AI chấm sơ bộ, sau đó Admin kiểm tra và duyệt; không có lựa chọn luồng. | Mọi bài nộp đều do AI chấm sơ bộ, sau đó quản trị viên kiểm tra và duyệt; không có lựa chọn luồng. | Thay “Admin” bằng “quản trị viên”. |
| `help.admin.item4` | Kiểm tra đáp án và SQL theo rubric; nhập lý do khi chỉnh bất kỳ điểm nào. | Kiểm tra đáp án và SQL theo thang chấm; nhập lý do khi chỉnh bất kỳ điểm nào. | Thay “rubric” bằng thuật ngữ tiếng Việt “thang chấm”. |

## Changed strings — English

| Key | Before | After | Reason |
|---|---|---|---|
| `supervisor.unavailableSelection` | These skills are not offered together in an open assessment. Choose a supported group of skills. | No open assessment covers this skill group. Choose a supported group of skills. | Direct sentence; removes the fronted negative clause. |
| `supervisor.humanHelp` | Official results become available after an authorized grader verifies and publishes them. | Official results become available after an authorized instructor verifies and publishes them. | Unified reviewer term “instructor” instead of “grader”. |
| `supervisor.buildingStrengths` | Keep practising to build evidence of your strengths. | Keep practicing to build evidence of your strengths. | US spelling: “practice/practicing” (the file otherwise uses -ize). |
| `supervisor.adaptiveHelp` | Choose one skill. Five-question MCQ rounds adjust difficulty using finalized answer-key results. At least five answers are needed; the session stops at stable performance, inventory exhaustion, 13 questions or the time limit. This practice does not contribute to official competency. | Choose one skill. Each round has up to five multiple-choice questions, and difficulty adjusts to your graded answers. At least five answers are required. The session stops when your performance is stable, the question pool runs out, 13 questions have been served, or time runs out. This practice does not count toward official competency. | Rewrites round/inventory jargon into clear session rules. |
| `errors.review_conflict` | Another grader has updated this submission. Refresh before continuing. | Another instructor has updated this submission. Refresh before continuing. | Unified reviewer term “instructor” instead of “grader”. |
| `errors.validation_error` | Check the form fields and try again. Required values or formats may be invalid. | Some fields are missing or invalid. Check them and try again. | Plain, concise error copy; removes duplicated “required values”. |
| `errors.assessment_bank_incomplete` | Review the question bank before activation: three basic opening MCQs, the required 10/2/1 mix, SQL datasets and four-level essay rubrics must be valid. | The question bank is not ready for activation: it needs three basic opening MCQs, the required 10/2/1 mix, valid SQL datasets and valid four-level essay rubrics. | States exactly what is missing instead of “review the bank”. |
| `nav.questions` | Question Bank | Question bank | Sentence case; clearer bank label. |
| `nav.candidates` | AI Candidates | AI candidates | Sentence case; clearer bank label. |
| `nav.bank` | Questions & concepts/CLO | Question bank & concepts/CLO | Sentence case; clearer bank label. |
| `auth.loginFailed` | Login failed | Sign-in failed | Matches the “Sign in” term used across auth. |
| `auth.oauthDisabled` | Unavailable sign-in methods are disabled on this server. | Some sign-in methods are not configured on this server. | Removes the tautology “unavailable methods are disabled”. |
| `auth.oauthFailed` | Social sign-in failed. Please try again. | Provider sign-in failed. Please try again. | Matches the “provider” term used elsewhere. |
| `auth.sessionUnavailable` | Your session could not be checked. Retry when the connection is available. | Your session could not be checked. Check your connection and try again. | Concrete recovery step. |
| `auth.namePlaceholder` | Your full name | Enter your full name… | Placeholder style matches the other fields. |
| `assessment.intro` | Track your exam schedule, practice SQL and review assessment results. | Start an assessment, resume one in progress, or review your results. | Removes “exam schedule”, which the product does not have. |
| `assessment.statInProgress` | Sessions in progress | In progress | Stat label parallels “Ready” and “Completed”. |
| `assessment.resetFilters` | Reset | Clear filters | Names the action instead of the generic “Reset”. |
| `assessment.emptyBody` | Check back later — your administrator has not activated an assessment yet. | No assessments are available for you yet. Check back later. | Accurate, learner-facing empty state. |
| `assessment.statUnit` | tests | assessments | Product term is “assessment”, not “test”. |
| `assessment.durationAll` | Duration: All | Duration: all | Consistent label casing. |
| `sql.schema` | Test-table schema | Table schema | Plain label; removes “Test-table”. |
| `history.heroSub` | Every finalized session with its per-concept outcome and evidence link. | Resume an assessment in progress or review your results and submitted answers. | Matches the page, which also lists attempts still in progress. |
| `dashboard.subtitle` | Review and close your knowledge gaps to be ready for the final exam. | Review your results and see what to study next. | Removes the non-existent “final exam”; states the real next step. |
| `dashboard.gapsMeta` | Concepts below their configured target | Concepts below their benchmark | Unified “benchmark” term. |
| `dashboard.emptyBody` | Your competency profile appears here after you finish an assessment. | Finish an assessment to see what you have mastered and what to review. | More helpful empty state. |
| `dashboard.noGap` | No assessed concept is below its configured target | No assessed concept is below its benchmark | Unified “benchmark” term. |
| `dashboard.masteryTarget` | Concept mastery vs target | Concept mastery vs. benchmark | Unified “benchmark” term. |
| `dashboard.statProgress` | Outcome progress | Benchmark progress | Label describes the metric without duplicating the unit. |
| `dashboard.radarNote` | Weighted across all assessed database concepts | Compares each concept's competency with its benchmark. | Corrects the false “weighted across all concepts” description. |
| `dashboard.analysisTitle` | Skill-gap diagnosis & prioritized guidance | Skill gaps and study guidance | Plain heading/description; removes marketing jargon. |
| `dashboard.analysisSub` | Deep competency analysis with a personalized remediation path | See your strengths and what to review. | Plain heading/description; removes marketing jargon. |
| `dashboard.analysisNote` | Computed from your submitted assessments by the analysis engine | Based on graded answers. | Accurate data source: graded answers, not an “analysis engine”. |
| `cumulativeView.detailsHint` | Search or filter by target status, then open a concept to see what the result means and what to practise next. | Search or filter by target status, then open a concept to see what the result means and what to practice next. | US spelling: “practice/practicing” (the file otherwise uses -ize). |
| `cumulativeView.metHelp` | This cumulative result meets or exceeds the benchmark. Keep practising to maintain it. | This cumulative result meets or exceeds the benchmark. Keep practicing to maintain it. | US spelling: “practice/practicing” (the file otherwise uses -ize). |
| `cumulativeView.nextImprove` | Review {{name}}, then practise related questions and compare your answers with the feedback in published results. | Review {{name}}, then practice related questions and compare your answers with the feedback in published results. | US spelling: “practice/practicing” (the file otherwise uses -ize). |
| `cumulativeView.nextMaintain` | Continue practising {{name}} in different question formats to consolidate it. | Continue practicing {{name}} in different question formats to consolidate it. | US spelling: “practice/practicing” (the file otherwise uses -ize). |
| `admin.analytics.subtitle` | Class-wide competency and below-benchmark prevalence. | Cohort competency and the share of learners below benchmark. | Replaces epidemiological “prevalence” with plain language. |
| `admin.analytics.scope` | Cohort means all learners assessed in the selected assessment. Select a learner below for individual results. | This overview uses published assessments from all learners. Select a learner for details. | Explains the view instead of defining “cohort”. |
| `admin.accounts.searchPlaceholder` | search name or email… | Search by name or email… | Capitalized placeholder. |
| `admin.accounts.allRoles` | all roles | All roles | Capitalized filter options. |
| `admin.accounts.allStatuses` | all statuses | All statuses | Capitalized filter options. |
| `admin.curriculum.model` | Concept model | New concept | Form title names the action. |
| `admin.curriculum.noTechnique` | No SQL technique | Not applicable | Natural select option (“Not applicable”). |
| `admin.curriculum.prereqIds` | prerequisites (ids): | Prerequisite concept IDs: | Full labels; removes lowercase sentence fragments. |
| `admin.curriculum.idsExample` | e.g. 1,2 | e.g. 1, 2 | Space after the comma in examples. |
| `admin.curriculum.aiSuggest` | AI suggest | Suggest with AI | Grammatical verb phrase. |
| `admin.curriculum.confirmedSet` | confirmed set (concept ids): | Confirmed concept IDs: | Full labels; removes lowercase sentence fragments. |
| `admin.curriculum.searchPlaceholder` | search code or name… | Search by code or name… | Capitalized placeholder. |
| `admin.questions.legacyRubricHint` | Retired — scored on the historical 3-level rubric. | Retired — scored with the old three-level rubric. | Plain wording; avoids “3-level” shorthand. |
| `admin.questions.subtitle` | Search, review, and maintain the questions used by adaptive assessments. | Search, review and maintain the questions used in assessments. | Removes the inaccurate claim that every question is adaptive. |
| `admin.questions.allConcepts` | all concepts | All concepts | Capitalized filter options. |
| `admin.questions.allTypes` | all types | All types | Capitalized filter options. |
| `admin.questions.allStatuses` | all statuses | All statuses | Capitalized filter options. |
| `admin.questions.allDifficulties` | all difficulties | All difficulties | Capitalized filter options. |
| `admin.questions.allTopics` | all topics | All topics | Capitalized filter options. |
| `admin.questions.searchPlaceholder` | search prompt… | Search questions… | Matches the question bank content. |
| `admin.questions.pendingHint` | Stored as pending tags — confirm them below. | Confirm or reject the suggested tags below. | Direct instruction: confirm or reject the suggested tags. |
| `admin.questions.promptPlaceholder` | Prompt | Enter the question prompt… | Guides input instead of repeating the field label. |
| `admin.questions.referenceHint` | Reference answer (sql/essay) | Reference answer (SQL/essay) | Uppercase SQL. |
| `admin.questions.idsHint` | concept ids, e.g. 1,2 | Concept IDs, e.g. 1, 2 | Space after the comma in examples. |
| `admin.questions.requiredHint` | required concept ids (subset) | Required concept IDs (subset of the selected concepts) | Clarifies that the subset comes from selected concepts. |
| `admin.questions.datasets` | datasets (JSON array) | Datasets (JSON array) | Sentence case. |
| `admin.questions.rubrics` | rubrics (JSON array) | Rubrics (JSON array) | Sentence case. |
| `admin.questions.suggesting` | suggesting… | Suggesting… | Sentence case. |
| `admin.questions.aiTags` | AI tags | Suggest tags with AI | Action-oriented button label. |
| `admin.questions.approvedSuggestion` | Suggestion approved. Revalidate the changed question. | Suggestion applied. Re-validate the question before use. | Plain next step; “re-validate” is clearer than “revalidate”. |
| `admin.questions.correct` | correct | Correct | Capitalized label. |
| `admin.assessments.title` | Adaptive assessments | Assessment management | Accurate page title; the page manages all assessments, not only adaptive ones. |
| `admin.assessments.subtitle` | Configure target concepts, time limits, and question mix for adaptive sessions. | Choose the concept scope and benchmarks before publishing. | Describes the controls that actually exist on the page. |
| `admin.assessments.maxQuestions` | max q | Maximum questions | Removes the “max q” abbreviation. |
| `admin.assessments.selectConcept` | — concept — | — Select a concept — | Capitalized option and consistent label/unit. |
| `admin.assessments.benchmark` | benchmark % | Benchmark (%) | Capitalized option and consistent label/unit. |
| `admin.assessments.addConcept` | + add concept | + Add concept | Sentence case for button labels. |
| `admin.assessments.published` | Published after bank validation. | Assessment published. | Consistent assessment toast phrasing. |
| `admin.assessments.closed` | Closed. | Assessment closed. | Consistent assessment toast phrasing. |
| `admin.candidates.generated` | Candidates generated and checked. | Candidates generated and checked. Review them before approving. | Adds the required next step: review before approving. |
| `admin.candidates.activeQueue` | Active queue | Awaiting review | Matches the “awaiting review” state. |
| `admin.candidates.promotedQuestion` | promoted → question #{{id}} | Promoted to question #{{id}} | Full sentence fragment instead of an arrow. |
| `admin.remove` | remove | Remove | Capitalized button label. |
| `landing.badge` | ADAPTIVE DATABASE ASSESSMENT | UNDERSTAND YOUR DATABASE COMPETENCY | Natural landing copy aligned with the Vietnamese intent. |
| `landing.title` | Measure real database competency, adaptively | How well do you know database concepts? | Natural landing copy aligned with the Vietnamese intent. |
| `landing.desc` | DBCAS serves adaptive assessments — multiple choice, live PostgreSQL sandboxes and essays — then turns results into a competency profile, skill gaps and prioritized study guidance. | DBCAS combines multiple-choice questions, live PostgreSQL sandboxes and essays, then turns your results into a competency profile, skill gaps and prioritized study guidance. | Natural landing copy aligned with the Vietnamese intent. |
| `landing.statMinutesSub` | SERVER-TIMED | REMAINING TIME TRACKED | Describes the real behaviour instead of internal/marketing labels. |
| `landing.pillarAdaptive` | Adaptive serving | Adaptive question selection | Describes the real behaviour instead of internal/marketing labels. |
| `landing.pillarSandboxBody` | Write and run real PostgreSQL SELECT queries against isolated datasets before you submit — sanitized errors, timed limits. | Write and run real PostgreSQL SELECT queries against isolated datasets before you submit, with clear errors and time limits. | Concrete benefits; removes “sanitized/immutable/finalized” jargon. |
| `landing.pillarEvidenceBody` | Finalized sessions produce an immutable grading record, a concept-level competency profile and ordered study guidance. | Completed assessments give you a permanent grading record, a competency profile by concept and prioritized study guidance. | Concrete benefits; removes “sanitized/immutable/finalized” jargon. |
| `landing.ctaSignIn` | View my competency | Sign in to start | Natural landing copy aligned with the Vietnamese intent. |
| `settings.subtitle` | Your account identity and workspace preferences. | Review your account and choose your theme and language. | Plain description of the page. |
| `authoring.draftTranslation` | Draft translation - needs review; unchecked edits are not saved. | Draft translation — needs review; unchecked edits are not saved. | Em dash for punctuation. |
| `authoring.preparingDraft` | Preparing draft... | Preparing draft… | Standard ellipsis character. |
| `help.context.assessments.body` | Choose concepts, one or more difficulties and bank or AI questions, then Bắt đầu. Five questions is the default; count is optional. | Choose concepts, one or more difficulties and bank or AI questions, then select Start. Five questions is the default; the count is optional. | Removes the leftover Vietnamese “Bắt đầu” from the English locale. |
| `help.modes.formalBody` | Questions are generated at the start within your chosen scope. Answers are validated before storing the attempt. A disclosed fallback is used when AI fails. | Questions are generated at the start within your chosen scope. Answers are checked before the attempt is saved. If AI fails, the system uses a disclosed fallback. | Plain conditional; removes the passive fallback construction. |
| `help.modes.note` | Questions and grading criteria are stored with the attempt. Released practice contributes to statistics and cumulative competency. | Questions and grading criteria are stored with the attempt. Published assessment scores contribute to statistics and cumulative competency. | Corrects “released practice” to published assessment scores. |
| `help.results.body` | Every released practice contributes to cumulative competency. Attempts awaiting grading or review are excluded until released. | Every published formal assessment contributes to cumulative competency. Attempts awaiting grading or review are excluded. | Corrects the contradiction: only published formal assessments count. |

## Hardcoded user-facing strings (not edited)

Counted 136 deduplicated occurrences across 15 files. Brand names (`DBCAS`, `BCAS`), the language autonym (`Tiếng Việt`) and the `aria-hidden` landing code preview are excluded. Each row lists the source lines and the copy found there.

| File | Lines | Hardcoded copy |
|---|---|---|
| `components/EvaluationCharts.jsx` | 26, 32, 58, 63, 72, 79, 82, 96, 103–105, 115, 121, 135, 141 | “Nhóm bằng chứng”, “Tỷ lệ điểm (%)”, “Xu hướng qua các bài”, aria-label “Xu hướng điểm từ 0 đến 100 phần trăm”, “Bài làm theo thứ tự thời gian”, “Bài {n}”, “Điểm (%)”, tooltip “Bài {n}: {pct}%”, “Điểm theo CLO/chủ đề/độ khó”, aria-label “… thang 0 đến 100 phần trăm”, “{points} điểm”, “Chưa có bằng chứng cho nhóm này.” |
| `components/StatisticsPanel.jsx` | 194 | “Bổ sung câu hỏi” |
| `components/SqlEditor.jsx` | 93 | placeholder `SELECT ...` (should be `SELECT …`) |
| `components/QuestionAuthoring.jsx` | 482 | example URL placeholder (neutral; no translation needed) |
| `pages/admin/AdminAccountsPage.jsx` | 164, 294, 360–361, 384, 396, 407 | `email@example.com`, “Đặt lại mật khẩu”, “Đặt lại mật khẩu · {email}”, “Mật khẩu mới sẽ thay mật khẩu cũ…”, “Mật khẩu mới”, “Lưu mật khẩu mới”, “Hủy” |
| `pages/admin/AdminBankPage.jsx` | 10, 16, 24 | aria-label “Ngân hàng câu hỏi và khái niệm”, “Câu hỏi”, “Khái niệm & CLO” |
| `pages/admin/AdminGradingPage.jsx` | 189, 208, 213, 217, 224, 260, 264–265, 333, 387, 398, 423, 430, 439, 445–446 | “Duyệt”, “Đánh giá AI”, “Đánh giá dự phòng theo quy tắc.”, “Câu {n}”, “Đang chờ AI đánh giá...”, “Lịch sử điều chỉnh điểm”, “Giảng viên #{id}”, “Chưa chấm”, “điểm”, “Điểm hiện tại”, “Lý do điều chỉnh”, “Lưu điểm điều chỉnh”, “Sandbox chưa sẵn sàng…”, “SQL kiểm tra (chỉ SELECT)”, “Đang chạy...”, “Chạy SQL kiểm tra”, “Thành công · {n} dòng · {ms} ms”, “Không chạy được truy vấn…” |
| `pages/admin/AdminSystemPage.jsx` | 28, 35–38, 42–50, 53–55, 59–72, 77–78 | “Hệ thống”, “Cấu hình dùng chung trên máy local.”, “Quy trình công bố kết quả”, “Admin kiểm tra…”, “Admin duyệt…”, “admin-reviewed”, “Trạng thái AI”, “Prompt Builder:”, “Evaluator:”, “Đã đặt đường dẫn model local…”, “Template dự phòng sẵn sàng”, “Đã cấu hình API · có fallback khi lỗi”, “Đánh giá dự phòng theo quy tắc”, “API key chỉ đặt trong biến môi trường LLM_API_KEY…”, “Thông tin cơ bản”, “Chạy local · {database}” |
| `pages/AdminPage.jsx` | 98 | “Duyệt bài” |
| `pages/AssessmentsPage.jsx` | 8–10, 82, 91–93, 99–100, 104–106, 115, 120, 124, 155, 158, 175, 178–179, 198, 208, 212, 225–227, 245–249, 253 | “Dễ/Vừa/Khó”, “Chưa tạo được bài luyện tập…”, “Luyện tập cơ sở dữ liệu”, “Tạo bài luyện tập”, “Chọn nội dung bạn muốn ôn…”, “Ngân hàng chưa có khái niệm”, “Bạn có bài đang làm”, “Câu trả lời đã lưu sẽ được khôi phục.”, “Tiếp tục bài làm”, “1. Chọn khái niệm”, “Chọn tất cả khái niệm”, “Tìm khái niệm”, “Đã chọn {n} khái niệm.”, “2. Chọn độ khó”, “3. Chọn nguồn câu hỏi”, “Từ ngân hàng câu hỏi”, “AI tạo câu hỏi”, “4. Số câu”, “{n} câu”, “Số câu (…)”, “AI sẽ chấm và đánh giá sơ bộ…”, “Đang tạo câu hỏi...”, “Đang chuẩn bị bài...”, “Thử lại”, “Bắt đầu” |
| `pages/EvaluationPage.jsx` | 23–26, 32, 36, 39, 45, 48, 54, 69–72, 86, 90, 93, 105–106, 186, 188, 196–197, 199, 201, 207–210, 212, 215, 225–226, 230, 232 | “Đã được giảng viên duyệt”, “Điểm đã được điều chỉnh”, “{n} bài đang chờ chấm hoặc duyệt…”, “Làm thêm bài để xem xu hướng”, “Đánh giá dự phòng theo quy tắc…”, “Điểm tích lũy/Điểm bài làm”, “Nhận xét”, “Điểm mạnh”, “Điểm cần cải thiện”, “Gợi ý luyện tập”, “Lộ trình học”, “Nhận xét từng câu”, “Câu {n}”, “Điểm tự luận đề xuất:”, “Thống kê gồm toàn bộ bài đã công bố…”, “Xem bài làm”, “Bắt đầu hành trình của bạn”, “Hoàn thành một bài luyện tập…”, “Bắt đầu luyện tập”, “Đang chờ giảng viên duyệt”, “Kiểm tra cập nhật”, “Lịch sử bài làm”, “Đánh giá đang mất nhiều thời gian…”, “Đang chờ AI đánh giá...”, “Đang tải...”, “Thử lại” |
| `pages/EvidencePage.jsx` | 126 | “Xem đánh giá” |
| `pages/ExamPage.jsx` | 373, 735 | “Đã dùng câu hỏi dự phòng đã kiểm chứng.”, “query.sql — PostgreSQL” |
| `pages/HistoryPage.jsx` | 167 | “Xem đánh giá” |
| `pages/LandingPage.jsx` | 234 | “Learn. Practice. Grow.” |

The largest concentration is in legacy pages that do not use `t()`: `AssessmentsPage`, `EvaluationPage`, `AdminGradingPage`, `AdminSystemPage` and `EvaluationCharts`. They should be migrated to the i18n keys before translation review.

## Long strings to verify at 390px / 1280px

The 15 longest strings in the button/chip/table/chart/tooltip surface, by character count (vi / en). The longest button is `admin.questions.approveCriteria` — “Approve difficulty and criteria” (31 characters); the longest chip is `supervisor.pending_review` / `supervisor.reviewed` (27 characters), so neither reaches the top 15.

| # | Key | Surface | Chars (vi/en) | String |
|---:|---|---|---:|---|
| 1 | `dashboard.displayAverage` | chart | 140 / 103 | Biểu đồ hiển thị năng lực trung bình của các khái niệm đã đánh giá. Năng lực và mức chuẩn chính thức vẫn được tính riêng cho từng khái niệm. |
| 2 | `charts.conceptDescription` | chart | 109 / 93 | Biểu đồ so sánh năng lực từng khái niệm với mức chuẩn. Số liệu chi tiết có trong bảng kết quả theo khái niệm. |
| 3 | `sql.editorHelp` | tooltip | 76 / 108 | SQL syntax is highlighted. Use the schema viewer to inspect available tables. Tab moves to the next control. |
| 4 | `exam.gridNote` | tooltip | 98 / 94 | Chọn số câu để xem lại câu trả lời đã lưu. Câu hỏi mới được hiển thị theo thứ tự của bài đánh giá. |
| 5 | `admin.assessments.summary` | table | 93 / 89 | {{questions}} câu hỏi · {{minutes}} phút · {{concepts}} khái niệm · {{sessions}} lượt làm bài |
| 6 | `charts.areaDescription` | chart | 93 / 62 | Biểu đồ hiển thị năng lực trung bình của các khái niệm đã đánh giá trong từng nhóm kiến thức. |
| 7 | `admin.analytics.areaHelp` | chart | 93 / 61 | Biểu đồ hiển thị năng lực trung bình của các khái niệm đã đánh giá trong từng nhóm kiến thức. |
| 8 | `admin.analytics.trendHelp` | chart | 71 / 87 | Daily mean of fully graded answer results; pending sessions are excluded from the mean. |
| 9 | `admin.assessments.contract` | table | 75 / 64 | Cấu trúc cố định: 13 câu hỏi · 60 phút · 10 trắc nghiệm · 2 SQL · 1 tự luận |
| 10 | `charts.trendDescription` | chart | 71 / 40 | Kết quả trung bình theo ngày, chỉ tính các lượt làm bài đã chấm đầy đủ. |
| 11 | `dashboard.withoutBenchmark` | table | 60 / 38 | {{count}} khái niệm đã được đánh giá nhưng chưa có mức chuẩn |
| 12 | `dashboard.competencySub` | chart | 45 / 60 | Multi-dimensional profile built from your graded assessments |
| 13 | `essay.placeholder` | tooltip | 56 / 28 | Nhập câu trả lời và giải thích cách bạn đi đến kết luận… |
| 14 | `admin.questions.requiredHint` | tooltip | 56 / 54 | ID khái niệm bắt buộc, thuộc danh sách khái niệm đã chọn |
| 15 | `dashboard.radarNote` | chart | 46 / 54 | Compares each concept's competency with its benchmark. |

## Verification

- `npx vitest run src/test/Localization.test.jsx` — **1 file, 8 tests passed**. Covers key parity, non-empty leaves, interpolation names, locale switching, number/date formatting, plural forms, and every literal key used in production modules.
- `npx vitest run src/test/Localization.test.jsx src/test/LocalizedAuth.test.jsx src/test/LocalizedExam.test.jsx src/test/LocalizedWorkspaces.test.jsx src/test/LocalRecovery.test.jsx` — **5 files, 35 tests passed**.
- JSON parse, key parity and interpolation tokens were re-checked after the edits: **0 mismatches**.

## Product-scope corrections after review

| Key | Before | After | Reason |
|---|---|---|---|
| `help.results.body` (vi) | Mọi bài đánh giá chính thức đã công bố… | Mọi bài luyện tập đã được giảng viên duyệt… | Product has learner-defined practice, not formal assessments. |
| `help.results.body` (en) | Every published formal assessment… | Every practice attempt approved by an instructor… | Same product-scope correction. |
| `help.modes.note` (vi/en) | Điểm các bài đã công bố… / Published assessment scores… | Điểm các bài đã được giảng viên duyệt… / Approved practice scores… | Approval is the release gate; avoid “formal assessment”. |

## Notes

- No key names, plural forms or interpolation tokens were changed.
- The four concurrent `sql.*` keys were left untouched.
- Hardcoded component copy was reported only; per the task it was not edited.

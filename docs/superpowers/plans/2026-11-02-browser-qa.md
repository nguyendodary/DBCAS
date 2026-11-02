# Kế hoạch QA bằng trình duyệt

> Thực hiện trực tiếp từng bước trong phiên theo yêu cầu tự chủ của người dùng.

**Mục tiêu:** Kiểm hai vai trò bằng UI thật, sửa lỗi tại chỗ và giữ hồi quy bằng test.
**Kiến trúc:** Giữ Compose/FastAPI/PostgreSQL/React. Provider giả chỉ thuộc harness
kiểm thử local, có độ trễ và lỗi điều khiển được; không thay provider production.
**Đặc tả:** Yêu cầu QA Learner/Admin ngày 02/11/2026 trong phiên này.

## Ràng buộc và điểm kiểm

- develop2, commit nhỏ và push sau mỗi bản sửa; không nới lỏng/xóa test.
- Tài liệu tiếng Việt; code/comment/commit tiếng Anh; không thêm hạ tầng production.
- Ảnh chụp trước/sau từng bước chính; đọc màn hình trước khi thao tác tiếp.
- Không có key thì chờ giảng viên; có AI thì polling hữu hạn, tự cập nhật và fallback rõ ràng.
- Chỉ bài formal đã công bố mới tính vào năng lực; 0/1/2+ phải có bố cục phù hợp.
- Kiểm độc lập điểm CLO và điểm tích lũy từ bằng chứng câu trả lời, đối chiếu UI.
- Double click, hai tab, refresh, quay lại và token hết hạn không làm mất nháp/nộp trùng.

## 1. Chạy bản hiện tại và ghi nhận lỗi

- [x] Đọc policy, fetch/checkout/pull develop2; reset và khởi động bằng npm.
- [ ] Learner demo: đăng nhập, đề 13 câu, nháp/reload/timer, nộp, kết quả và phân tích.
- [ ] Admin demo: dashboard/CLO/learners/bank/exam/reports, chấm và công bố bài Learner.
- [ ] Ghi expected/actual, ảnh và severity trong `docs/qa/browser-qa.md`.
- [ ] Tạo Learner mới qua UI để kiểm 0/1/2/3 bài (demo có sẵn hai bài lịch sử).

## 2. Sửa trạng thái chấm và đồng bộ

Files: `frontend/src/usePendingResults.js`, `components/GradingStatusPanel.jsx`,
`pages/EvidencePage.jsx`, `pages/DashboardPage.jsx`, i18n; backend grading jobs nếu cần.
Interface: refresh không chồng request; polling/backoff hữu hạn, tự cập nhật sau công bố;
timeout/lỗi dừng spinner và cho thử lại. Giữ release policy, ownership và snapshot.
- [ ] Viết regression trước sửa, tái hiện lỗi; triển khai và kiểm lại qua UI/ảnh.
- [ ] Browser test chờ AI có delay, tự cập nhật, lỗi/timeout và chế độ không key.
- [ ] Commit/push bản sửa, ghi hash vào issue log.

## 3. Sửa phân tích và tính nhất quán

Files: `components/StatisticsPanel.jsx`, `pages/CumulativePage.jsx`,
`pages/DashboardPage.jsx`, statistics API và test liên quan nếu dữ liệu thiếu.
Interface: count=0 một CTA; count=1 chỉ dữ liệu bài đó; count>=2 cumulative/trend;
pending không tăng count, dữ liệu tự cập nhật sau giảng viên công bố.
- [ ] Test 0/1/2+ và refresh/publish trước sửa; giữ công thức điểm đã thống nhất.
- [ ] Kiểm một CLO và một trung bình tích lũy bằng phép tính độc lập.
- [ ] Kiểm ranking/privacy/tie và các màn hình sau Admin chỉnh điểm; commit/push.

## 4. Harness và gate cuối

Files mới: provider HTTP giả và override Compose kiểm thử; browser journey trong
`frontend/e2e/`, config và báo cáo `docs/qa/browser-qa.md`.
- [ ] Chạy lại hai scenario sau reset, ba lần liên tiếp; chụp và đọc các ảnh chính.
- [ ] Backend lint/build/toàn bộ tests, frontend npm ci/tests/build và browser tests.
- [ ] CI xanh, dọn tài nguyên test, phục hồi stack local và đối chiếu remote HEAD.
- [ ] Báo cáo issue/commit, ảnh, số học, số test thật và giới hạn chưa kiểm chứng.

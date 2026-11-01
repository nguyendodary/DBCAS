# Task 4.2 — Gap và API thống kê

Trạng thái đầu: **Đã có một phần**: gap/guidance per-session, cumulative profile,
Admin cohort/latest và trend. Review: phép gap/authorization cũ đạt, thiếu API
tổng hợp CLO/difficulty/distribution/ranking. Tài liệu/gate cần tích hợp đầy đủ.

Kế hoạch/thực hiện: thêm `schemas_analytics.py`, `statistics_service.py`, repository
read-only và GET statistics cho Learner/Admin; filter/limit/offset, publication/
formal/ownership, distribution, progress và recommendations reuse gap/target
weighted. Không dùng AI để tính thống kê. Bổ sung test DN/OpenAPI/inventory/docs.

Integration: readiness đòi schema refresh/pool; bộ chọn pool hỗ trợ ngữ cảnh đề
không có ID, clone đề giữ pool và xử lý conflict commit. Compose thêm profile UI
dùng nguyên frontend/Nginx hiện có qua alias backend; bỏ publish DB nội bộ.
Không sửa frontend; test độc lập chỉ có ngoại lệ hai assertion được DN phê duyệt
riêng bên dưới. Phụ thuộc Task 4.1 và toàn bộ pipeline trước.

Kiểm tra theo phạm vi: **94 passed** stats/Admin analytics/gaps/guidance/result/
readiness; lint/build/pip check, OpenAPI 75 path/90 operation/1.025 ref, inventory,
diagram/Compose/link validation đạt. Production frontend/app images build đạt.
Smoke qua Nginx đăng ký/login/statistics/refresh/logout và offline SQL đạt.
Sau các sửa integration cuối, bank DN/statistics DN/localized bank chạy lại
**75 passed**, gồm clone đề giữ pool. Không sửa test gốc để đạt kết quả này.

Gate trước phê duyệt: **1.159 passed / 2 failed**, không skip, 699,82 giây. Cả hai là
assertion contract cũ trong `test_final_acceptance.py` (migration chỉ đến 015) và
`test_login_throttle.py` (claim set chưa có sid). DN đã phê duyệt cập nhật đúng
hai assertion; diff được hiển thị trước khi áp dụng và commit riêng `ee99a12`
chỉ chứa hai file test này. Exact migration list được thêm 016/017; exact JWT
claim set thêm sid cùng kiểm tra hex 32 ký tự. Hai test riêng sau sửa: **2 passed**.
Vị trí: test_final_acceptance.py assertion dòng 213, phần tử thêm 221/222;
test_login_throttle.py dòng 166/167. **HN cần review hai assertion này.**

Gate backend sau phê duyệt: **1.161 passed, 0 failed, 0 skipped**, 660,29 giây;
lint/build/pip check đạt. Bổ sung kiểm tra artifact LF/CRLF và metadata; 18 file
DDL khớp byte với Git blob, không thay SQL hay assertion validator độc lập.
Frontend nguyên trạng được chạy bổ sung: 293 passed / 1 failed; ResultRace.test.jsx
dòng 46 còn lỗi và chạy riêng vẫn tái hiện. **Báo TN/HN xử lý; không sửa ngoài DN.**

Hai commit 4.2 tách biệt: `ee99a12` chỉ assertion, và implementation với message:
`Task 4.2: expose published competency dashboards and skill-gap statistics`.
Task DN đạt gate backend; lỗi frontend còn lại không được báo xanh. Cách chạy/test/
giả định và trạng thái bàn giao ở `docs/analytics-dn.md` và báo cáo tổng hợp.

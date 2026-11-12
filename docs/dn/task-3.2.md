# Task 3.2 — So sánh và chấm SQL

Trạng thái đầu: **Đã có một phần**. Review: comparator multiset/order/columns,
typed values và partial credit đạt; quality chia sql_result/sql_grading đạt;
test thực thi PostgreSQL đầy đủ; bảo mật không lộ expected/setup đạt; tài liệu
thiếu mô tả tiếng Việt và lỗi danh sách dataset rỗng có thể nhận full điểm.

Kế hoạch/thực hiện: sửa guard `grade_sql` từ chối không có dataset bằng 422;
thêm test DN cho lỗi này và number/text/bool/NULL/duplicate; tạo hướng dẫn thuật
toán/feedback. Không đổi trọng số đều hoặc cách xác minh kỹ thuật đã duyệt.
Phụ thuộc sandbox/expected JSON của task trước. Rủi ro precision có test wire thật.

Kiểm tra: lint/build/OpenAPI/diff check đạt; **93 passed** SQL scoring/release/DN.
Có SQL tương đương, edge dataset, partial điểm, required technique, hạ tầng lỗi,
thứ tự/cột/NULL/typed decimal và giới hạn kết quả. Không có dataset không chấm.

Chạy: `python backend/manage.py test tests/test_sql_scoring.py tests/test_sql_release.py tests/dn/test_sql_contracts.py`.
Giả định: mỗi dataset có weight 1; typed semantics theo nhóm giá trị PostgreSQL,
không yêu cầu int4/int8 khác nhau nếu cùng số. Giới hạn được ghi trong
`docs/sql-grading-dn.md`. Không còn thiếu hụt Task 3.2.
Commit: `Task 3.2: reject empty SQL fixtures and verify semantic scoring`.

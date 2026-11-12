# Thuật toán chấm SQL

So sánh kết quả thực thi với `sql_test_dataset.expected_result`, không so chuỗi
SQL. Reference được Admin kiểm tra khi duyệt; người học chạy query trên mọi dataset
(thường và edge). Dữ liệu expected/setup nội bộ không trả trong grading_detail.

Định dạng expected:

```json
{"columns":["name"],"rows":[["Ana"],["Bao"]],"ordered":false,"check_columns":false}
```

Số cột luôn được so khi fixture khai báo. Alias khác được chấp nhận mặc định;
`check_columns=true` đòi tên khớp không phân biệt hoa thường, không trùng, và căn
lại vị trí cột trước khi so. `ordered=false` so multiset bằng Counter: thứ tự không
quan trọng, số lần lặp vẫn quan trọng. Với `ordered=true`, từng vị trí phải khớp.

Giá trị được gắn nhóm number/boolean/text/null. Số dùng Decimal theo giá trị,
không đồng nhất bool với số hoặc chuỗi ký tự "1" với số 1. Wire string của cột
NUMERIC chỉ chuyển thành số khi có metadata PostgreSQL. Khoảng trắng trong text
có ý nghĩa; NULL khác chuỗi rỗng. JSON fixture sai/NaN/vô hạn bị từ chối.

Điểm = `points × passed_datasets / total_datasets`, làm tròn HALF_UP hai chữ số.
Đây là trọng số đều 1 cho mỗi dataset, giữ thuật toán đã duyệt; không có trường
weight tùy ý trong schema hiện tại. Ví dụ 4 điểm, đạt 1/2 dataset → 2 điểm.
Thiếu kỹ thuật bắt buộc mà AST xác minh được → 0; kỹ thuật chưa thể xác minh
được ghi unverified, không bịa kết luận. Execution error làm fail dataset;
hạ tầng không sẵn sàng phải retry/chưa chấm, không coi là lỗi kiến thức.
Không có dataset trả 422 `dataset_not_configured`, tuyệt đối không thưởng điểm.

Phản hồi gồm status correct/partial/incorrect/error, số dataset đạt/tổng, tiêu chí
columns/rows matched/failed, mã lỗi an toàn, kỹ thuật thiếu/chưa xác minh, điểm
earned/possible. Không tiết lộ expected rows hoặc setup SQL. Giới hạn result quá
lớn là lỗi có giới hạn, không tự cắt rồi chấm như kết quả đầy đủ.

Chạy: `python backend/manage.py test tests/test_sql_scoring.py tests/test_sql_release.py tests/dn/test_sql_contracts.py`.

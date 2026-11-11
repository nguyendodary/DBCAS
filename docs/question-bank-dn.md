# Ngân hàng câu hỏi và đề

CRUD hiện hữu ở `/api/v1/admin/questions` và `/admin/assessments`; schema chi tiết
trong [OpenAPI](openapi.json). API dùng loại `mcq`, `sql`, `essay` viết thường.
MCQ có ít nhất hai lựa chọn, một đúng; SQL phải có dataset thường và edge case,
reference được kiểm tra; essay dùng bốn mức rubric. Bản sửa đã dùng có version,
ảnh chụp trong attempt giữ nguyên. Learner không truy cập endpoint Admin.

Danh sách câu hỗ trợ `concept_id`, `question_type`, `difficulty` (1–5), `status`,
`q`, `tag`, thêm `clo_id` và `topic` (khớp subject_area chính xác). CLO chỉ tính
mapping confirmed và tag câu hỏi confirmed. Tìm kiếm gồm nội dung gốc/bản dịch
được duyệt còn hiện hành. Danh sách đề có `q`, `status`; cả hai danh sách hỗ trợ
`limit` (1–100), `offset` (>=0), lọc trước phân trang và giữ thứ tự ổn định.
Không truyền limit thì giữ danh sách cũ để UI team không bị cắt dữ liệu ngầm.
Phân trang response là mảng; client đọc trang kế tiếp đến khi ít hơn limit.
Đây là giới hạn response; một phần lọc bản dịch/phân trang được làm tại service,
chưa là cam kết query bounded cho ngân hàng rất lớn.

Admin gắn câu bằng `PUT /api/v1/admin/assessments/{id}/questions`:

```json
{"question_ids":[12,15,18]}
```

`GET` cùng path trả assessment_id, question_ids tăng dần, selection `CURATED` hoặc
`CONCEPTS`. Chỉ đề draft chưa có phiên được sửa pool; mọi ID phải tồn tại, validated,
có tag xác nhận phù hợp target và khoảng khó. Toàn bộ cập nhật atomic; ID trùng/sai
trả 422; đề đã dùng/đã công bố trả 409. Câu trong pool không được xóa trực tiếp.
Mảng rỗng bỏ hạn chế pool, trở lại pool theo concept hiện có.

Pool là allowlist cho adaptive, không ép thứ tự cố định hoặc giảm quota formal.
Nộp pool ít câu có thể lưu draft, nhưng start vẫn báo thiếu chính xác nếu không
đủ 10/2/1 và độ phủ. Đề cũ không có pool giữ hành vi cũ. Các phiên đã bắt đầu có
snapshot/kế hoạch riêng và không bị viết lại. Migration 017 là cộng thêm.

Kiểm tra: `python manage.py test tests/test_admin_questions.py tests/test_admin_assessments.py tests/test_assessment_blueprints.py tests/dn/test_bank_contracts.py tests/test_migrations.py`.

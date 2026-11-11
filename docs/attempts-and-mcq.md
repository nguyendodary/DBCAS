# Phiên làm bài, nháp và chấm MCQ

Các API đã có trong [OpenAPI](openapi.json), prefix `/api/v1`:

1. `POST /assessments/{assessment_id}/sessions` bắt đầu/resume với lựa chọn hợp lệ
   và UUID request id theo DTO. Server kiểm tra pool/quota trước khi phục vụ câu.
2. `GET /sessions/{id}/state`, `/questions` lấy trạng thái/câu đã phục vụ; không trả
   key, reference hoặc rubric đáp án nội bộ. Thời hạn do DB/server quyết định.
3. `PUT /sessions/{id}/draft` lưu `question_id`, answer theo loại và `revision`.
   Revision tăng đúng một; retry cùng revision/cùng nội dung không tạo bản mới.
   Revision cũ khác nội dung trả 409 `draft_revision_conflict`; GET `/draft` phục hồi.
4. `POST /sessions/{id}/submit` thực hiện nộp + chuyển câu atomically; retry cùng
   đáp án trả kết quả cũ, nội dung khác sau submit bị từ chối. API cũ `/answers`
   chủ động trả conflict khi gửi trùng. Không tự đổi endpoint ở UI đang chạy.
5. `POST /sessions/{id}/finish` hoàn tất một lần. Khi hết hạn, worker hoặc request
   kế tiếp nộp các nháp đã lưu với thời điểm hết hạn; không nhận sửa đáp án quá hạn.

MCQ: option_id phải thuộc câu đã serve; chọn đúng được toàn bộ points, sai/bỏ
trống được 0. `attempt` giữ answer/score/grading_detail. Key, points và tags lấy
từ snapshot tại thời điểm serve, không lấy lại đáp án đã bị Admin sửa. SQL/essay
được dispatch sang service tương ứng; pending không biến thành điểm 0 chính thức.

Row lock trên session và constraint attempt/session/seq bảo vệ nộp đồng thời.
Chỉ Learner sở hữu được đọc/sửa nháp hoặc nộp; Admin không giả làm Learner.
Kết quả/evidence tuân theo review/publication policy; frontend phải xử lý pending,
manual review và chưa công bố trước khi dựng số liệu chính thức.

Kiểm tra từ backend:

```powershell
python manage.py test tests/test_grading.py tests/test_sessions.py tests/test_draft_lifecycle.py tests/test_start_request_bindings.py
```

Test có kiểm tra timeout background không cần browser callback, mất HTTP response,
hai kết nối finish/timeout, thời gian DB authoritative, ownership, nháp ba định
dạng, option thuộc câu khác, snapshot sau khi bank thay đổi và idempotency key
không được đổi lựa chọn hoặc đề. Không cần tạo cơ chế autosave thứ hai.

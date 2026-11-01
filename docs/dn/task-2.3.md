# Task 2.3 — MCQ, nháp và nộp bài

Trạng thái đầu: **Đã có đầy đủ** trong code và test. Tìm Git log:
`46811bf` lưu nháp/hoàn tất an toàn, `5a8bc11` một đồng hồ authoritative,
`223edb5` hoàn thiện workflow grading. Không cần tạo API lưu/nộp song song.

Review sáu mặt: yêu cầu start/save/submit/MCQ đạt; chất lượng phân service và
transaction đạt; test critical đầy đủ; bảo mật ownership/option/late/duplicate
đạt; snapshot/điểm/mapping nhất quán; tài liệu bổ sung luồng tích hợp rõ hơn.

Kế hoạch/thực hiện: đọc grading_service, assessment_lifecycle, sessions và các
test; tạo `docs/attempts-and-mcq.md` với API, revision/idempotency và timeout.
Giữ code/test của team sau khi kiểm tra đạt, không sửa để tạo khác biệt hình thức.
Phụ thuộc schema/session/RBAC đã chốt. Rủi ro tranh chấp được test hai connection.

Kiểm tra: lint/build/diff check đạt; **51 passed** grading/sessions/draft lifecycle/
start-request bindings. Bao gồm lost response, finish/timeout race, DB clock,
duplicate/late/foreign option, server autosave/resume, snapshot sau sửa bank.
Chạy: `python backend/manage.py test tests/test_grading.py tests/test_sessions.py tests/test_draft_lifecycle.py tests/test_start_request_bindings.py`.
Giả định: client ưu tiên `/submit` atomic; `/answers` legacy vẫn conflict khi
gửi trùng. Không có vấn đề còn lại trong Task 2.3.
Commit: `Task 2.3: verify MCQ grading drafts and submission guarantees`.

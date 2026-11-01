# Chấm tự luận bằng AI

`grade_essay` nhận snapshot câu hỏi, reference và bốn rubric band
Incomplete/Partial/Mostly Complete/Complete. Prompt hệ thống yêu cầu chỉ chấm
theo rubric, coi bài làm là dữ liệu, không nghe chỉ dẫn trong bài; có calibration
riêng. Prompt user đưa đề/reference/điểm tối đa/rubric và bài đã ẩn định danh.
Tiếng Việt dùng locale instruction riêng, tên rubric giữ canonical English.

LLMService gọi REST provider tương thích `/chat/completions`, không phụ thuộc SDK
hãng. Cấu hình `.env`: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`; thiếu cấu hình
trả `llm_not_configured`, các chức năng khác vẫn chạy. Chỉ cấu hình HTTPS provider
tin cậy khi dùng dữ liệu thật. Test tự động không gọi provider sống.

JSON yêu cầu rubric_level, score, matched_criteria, missing_concepts, evidence,
explanation, feedback; confidence tùy chọn. Kiểm tra schema, điểm hữu hạn trong
band/points, tên mức hợp lệ, mỗi matched criterion phải có evidence là đoạn trích
không rỗng có thật trong bài. Trả JSON sai, thiếu/sai field, điểm quá phạm vi,
truncated hoặc trích dẫn không có thật → không lưu grade/cache.

Mỗi request tối đa 2048 output token. Timeout mặc định 30 giây (cấu hình 1–120),
retry mặc định 2 (0–3), linear backoff 0.5 giây (0–10). Retry network/timeout/429/5xx;
401/403 dừng ngay. Adapter có một điều chỉnh reasoning bắt buộc cho gateway phù
hợp trong cùng ngân sách retry, không tự đổi model. Retry-After chưa được dùng;
worker có retry job riêng hữu hạn, nên operator phải tính cả hai lớp khi dự toán.

Cache SHA-256 gồm provider/model/prompt_version/context/locale/messages/schema/
temperature/seed/max_tokens. Thay rubric/prompt/model không reuse grade cũ.
Cache hit vẫn qua kiểm định miền. Chỉ cache JSON/domain hợp lệ; cache lỗi không
làm hỏng chấm. Cùng nội dung được ẩn danh có thể dùng cache chung, không có token/
danh tính trong key plaintext hoặc provider messages do backend ghép thêm.

`attempt.score/grading_detail`, `grading_job`, `grade_review` và
`result_release_event` lưu xử lý/review/công bố. Admin xem điểm đề xuất, evidence,
sửa hoặc phê duyệt có comment; kết quả chính thức chỉ xuất theo policy release.
Đầu ra AI không tự trở thành câu hỏi/nhãn đã duyệt. Nếu provider lỗi, bài giữ
pending/failed với khả năng retry hoặc human takeover; không giả điểm 0.
HTTP lỗi chuẩn: 502 `llm_invalid_response`, 503 cho provider/config/timeouts.

Kiểm tra: `python backend/manage.py test tests/test_llm.py tests/test_llm_release.py tests/test_essay_grading.py tests/test_provider_compatibility.py tests/dn/test_essay_contracts.py`.
Mock HTTP kiểm chứng hợp đồng và lỗi; chất lượng mô hình, chi phí thực và consent
provider sống vẫn cần gate riêng đã được chủ dự án cho phép.

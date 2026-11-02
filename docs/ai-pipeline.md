# Pipeline hai AI

AI #1 (Prompt Builder) chỉ xây dựng prompt tiếng Việt: bối cảnh, dữ liệu bài làm,
rubric, schema JSON và ràng buộc. AI #2 (Evaluator) nhận prompt, trả nhận xét từng
câu, điểm mạnh/yếu, gợi ý, lộ trình và đề xuất điểm tự luận. Điểm MCQ/SQL do hệ
thống chấm, không bị mô hình sửa. Dữ liệu người học là bằng chứng, không phải chỉ thị.

Không model local: dùng template xác định. Model lỗi, thiếu mục, thay dữ liệu/schema
hoặc prompt quá 192 KiB: dùng template. Không key/timeout/JSON không hợp lệ:
Evaluator dùng quy tắc; UI ghi rõ đánh giá dự phòng. Log chỉ hash prompt, thời gian,
trạng thái và fallback, không key/câu trả lời. Provider hiện có giữ timeout/retry/cache.

`npm run ai:train` là bước tùy chọn, không chạy cùng ứng dụng. Docker tạo dataset
từ ngân hàng thật và câu trả lời tổng hợp, chia train/test theo câu gốc để tránh
rò rỉ biến thể. Có thể bổ sung bản export bài thật đã ẩn danh bằng `--real`;
không tự lấy thông tin cá nhân từ database. Lệnh train dùng
[Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct),
khoảng 0,5 tỷ tham số, và
[LoRA/PEFT](https://huggingface.co/docs/peft/quicktour), rank 4, q_proj/v_proj.
Lần đầu cần tải dependencies/model; các bước dataset/train/evaluate/export sau đó
chạy trên máy, không gửi bài làm đến dịch vụ huấn luyện. GPU tùy chọn, CPU được hỗ trợ.

`npm run ai:train -- --smoke` dùng GPT-2 cấu hình cực nhỏ khởi tạo ngẫu nhiên,
hai bước optimizer, export và inference; chỉ xác minh dây chuyền, không chứng minh
chất lượng tiếng Việt. Báo cáo ở `ai/output/training.json`, `evaluation.json`.
Mặc định 30 bước chỉ là minh họa, không đủ chứng nhận chất lượng; cần đánh giá độc
lập với dữ liệu thật. CPU 0,5B có thể cần nhiều GB RAM và hàng chục phút đến nhiều
giờ tùy máy; đây là ước lượng, không phải thời gian đo. Template là đường chạy tin cậy.

Để dùng export, cài `ai/requirements.txt` trong interpreter backend và đặt
`PROMPT_BUILDER_MODEL_PATH` tới `ai/output/export` (mount model vào container khi
chạy Compose). Model không được tự tải trong request; inference có timeout.
Không đưa output/model/dữ liệu thật/key vào Git. Kết quả gate thực tế nằm trong
[báo cáo](final-status.md).

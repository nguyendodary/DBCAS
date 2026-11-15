# Pipeline hai AI

AI #1 (Prompt Builder) chỉ xây dựng prompt tiếng Việt: bối cảnh, dữ liệu bài làm,
rubric, schema JSON và ràng buộc. AI #2 (Evaluator) nhận prompt, trả nhận xét từng
câu, điểm mạnh/yếu, gợi ý, lộ trình và đề xuất điểm tự luận. Điểm MCQ/SQL do hệ
thống chấm, không bị mô hình sửa. Dữ liệu người học là bằng chứng, không phải chỉ thị.

Prompt Builder dùng template xác định và được validate trước khi gửi. Template
thiếu mục, thay dữ liệu/schema, chèn nội dung chấm điểm/nhận xét/sao chép đáp án
hoặc prompt quá 192 KiB bị từ chối và ghi `reason=` trong log. Không key/timeout/
JSON không hợp lệ: Evaluator dùng quy tắc và ghi lý do; UI ghi rõ đánh giá dự phòng.
Dữ liệu được che thông tin trước khi build, nên `prompt_hash`, prompt đã build và
prompt gửi provider là một. Log chỉ hash prompt, thời gian, trạng thái, fallback và
mã lý do, không key/câu trả lời. Provider hiện có giữ timeout/retry/cache.

Cache dùng hash của đáp án, điểm, rubric, snapshot và toàn bộ lịch sử. Điểm sửa
làm mất hiệu lực đánh giá cũ. Bài chờ duyệt không vào tổng thể/thống kê. Tổng thể
đọc mọi bài để tổng hợp điểm và lỗi lặp; prompt giữ tối đa 80 câu chi tiết gần nhất
và 500 mốc biểu đồ (gồm bài đầu). Mỗi bài riêng vẫn có nhận xét cho mọi câu;
nội dung quá dài được rút gọn và UI thông báo. Dữ liệu/đáp án gốc vẫn được giữ.

AI #2 có timeout tối đa 10 giây mỗi lần, retry tối đa một lần. Màn hình chờ AI
sau 45 giây yêu cầu fallback, có Thử lại. Chờ giảng
viên duyệt tiếp tục kiểm tra chậm, không quay spinner vô hạn. Đặt
`EVALUATION_FAKE_DELAY_SECONDS=0..15`, `EVALUATION_FAKE_ERROR=true` để quan sát
fallback; `npm run test:qa` dùng HTTP provider riêng với delay/lỗi/giữ phản hồi.
Cùng provider AI #2 sinh câu hỏi khi bắt đầu; MCQ kiểm tra một đáp án, SQL chạy
cả dataset chính và biên, rubric tự luận được kiểm tra trước khi lưu. Mỗi bài AI
mới có khóa generation riêng; gửi lại cùng request không tạo bài hay câu mới.

## Local model research (not adopted)

Một model local/self-hosted cho framing và prompt building đã được nghiên cứu và
benchmark trên CPU/GPU (Ryzen 5 5600H, RTX 3050 Laptop 4 GB, WSL2 8 GB / 8 CPU).
README framing ghi `quality_verified=false`; gate single-request không đạt (GPU p95
3,23 s ở 40 token và 10,04 s ở 96 token; CPU p95 20,82–40,98 s). Model chưa từng
được triển khai; production dùng template xác định và evaluator qua provider hiện
tại. Hướng này được đánh giá không khả thi và code tham chiếu đã được xóa khỏi
`main`. Code vẫn còn trong lịch sử Git, hiện diện lần cuối tại `f82eb24`, và trên
nhánh local chưa push `nguyendodary/feature-prompt-builder-model`.

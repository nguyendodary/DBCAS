# Tự luận và SQL khi chạy local

`npm start` bật maintenance worker hiện hữu trong API, không cần thêm service.
Để bật AI, điền `LLM_API_KEY` trong `.env` rồi chạy lại `npm start`. Compose mặc
định dùng `https://api.openai.com/v1` và `gpt-5.4-mini`; đặt `LLM_BASE_URL` và
`LLM_MODEL` nếu dùng provider khác. Không gửi danh tính người học.
JSON/rubric/cache/timeout/retry tiếp tục dùng hợp đồng hiện hữu.

Model mặc định hỗ trợ Chat Completions, JSON schema và reasoning `none` theo
[OpenAI Docs](https://developers.openai.com/api/docs/models/gpt-5.4-mini).
Adapter dùng `max_completion_tokens`, không gửi seed cho model mặc định; cache
vẫn định danh đầy đủ prompt/model/tham số. Model/provider tùy chọn giữ hợp đồng
tham số cũ. Tài khoản provider cần key hợp lệ và quyền sử dụng model tương ứng.

Không có provider: bài tự luận được lưu, trả trạng thái chờ giảng viên thay vì
spinner AI vô hạn. Admin vào Chấm bài, nhập điểm/lý do và duyệt. Đề Human verified
vẫn yêu cầu kiểm tra SQL/tự luận và bấm công bố; đề Immediate tự công bố khi đủ
điểm sau khi giảng viên chấm thay. Không đổi policy hoặc snapshot đã lưu.

Có provider: API local đưa tự luận vào job bền vững để phản hồi nhanh; worker chấm
với retry hữu hạn. Lỗi provider cuối cùng vẫn cho giảng viên chấm thay, không tự
cho điểm 0. Không key thì worker không liên tục thử gọi dịch vụ chưa cấu hình.

Nhật ký công bố lấy thời gian hiện tại từ DB tại mỗi lần chuyển trạng thái,
không dùng mốc bắt đầu transaction của request AI dài. Mốc công bố trên phiên
và sự kiện công bố dùng cùng một giá trị; không sửa ngược lịch sử đã lưu.

SQL learner chỉ SELECT; executor PostgreSQL tạm không mạng, 1 CPU/256 MiB,
statement timeout tối đa 3 giây, watchdog và cleanup theo ownership. Không chạy
SQL learner trên DB hệ thống. Launcher tự nhận group socket cho app không root.

Test provider dùng adapter HTTP thật với transport kiểm thử; chưa gọi model
trả phí và không coi test này là chứng nhận chất lượng chấm của một model thật.

# Tự luận và SQL khi chạy local

`npm start` bật maintenance worker hiện hữu trong API, không cần thêm service.
Để bật AI, điền đủ `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` trong `.env` rồi
chạy lại `npm start`. Base URL/model theo provider đã chọn; không gửi danh tính
người học. JSON/rubric/cache/timeout/retry tiếp tục dùng hợp đồng hiện hữu.

Không có provider: bài tự luận được lưu, trả trạng thái chờ giảng viên thay vì
spinner AI vô hạn. Admin vào Chấm bài, nhập điểm/lý do và duyệt. Đề Human verified
vẫn yêu cầu kiểm tra SQL/tự luận và bấm công bố; đề Immediate tự công bố khi đủ
điểm sau khi giảng viên chấm thay. Không đổi policy hoặc snapshot đã lưu.

Có provider: API local đưa tự luận vào job bền vững để phản hồi nhanh; worker chấm
với retry hữu hạn. Lỗi provider cuối cùng vẫn cho giảng viên chấm thay, không tự
cho điểm 0. Không key thì worker không liên tục thử gọi dịch vụ chưa cấu hình.

SQL learner chỉ SELECT; executor PostgreSQL tạm không mạng, 1 CPU/256 MiB,
statement timeout tối đa 3 giây, watchdog và cleanup theo ownership. Không chạy
SQL learner trên DB hệ thống. Launcher tự nhận group socket cho app không root.

Test provider dùng adapter HTTP thật với transport kiểm thử; chưa gọi model
trả phí và không coi test này là chứng nhận chất lượng chấm của một model thật.

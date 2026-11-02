# Ảnh nghiệm thu ngày 03/11/2026

Nguồn: commit `60e0b81` trên develop2; ảnh nguồn AI dự phòng tại `853c275`, Chromium thật qua Playwright trên
Windows/WSL Docker Compose. Tài khoản và bài làm trong ảnh là dữ liệu kiểm thử.
Provider HTTP giả có delay/lỗi; ảnh câu hỏi là fallback khi không có key; không dùng API LLM trả phí. Các ảnh đã được mở
để kiểm tra chữ, biểu đồ, trạng thái và bố cục. Viewport mobile là 390px, không
phải thiết bị thật.

Lượt kiểm tra đủ đầu tiên: **10/10 pass**, **282,87 giây**, 0 lỗi/skip/flaky,
retries = 0. Kết quả gate lặp cuối nằm trong [báo cáo](../../final-status.md)
và `gate-results.json` cạnh file này.

| Màn hình | Ảnh |
| --- | --- |
| Chưa có bài, một nút bắt đầu | [Tổng thể 0 bài](overall-0.png) |
| Một bài, chưa hiển thị xu hướng | [Tổng thể 1 bài](overall-1.png) |
| Ba bài, trend và năng lực tích lũy | [Tổng thể 3 bài](overall-3.png) |
| Điểm và nhận xét từng câu | [Đánh giá bài](attempt-1.png) |
| Nguồn AI có phạm vi được chọn | [Câu sinh mới](generated-source.png) |
| Flow 2, kết quả chưa công bố | [Chờ duyệt](waiting-approval.png) |
| Admin xem đáp án/SQL, sửa điểm và audit | [Duyệt bài](admin-review.png) |
| Dấu đã duyệt và điểm đã điều chỉnh | [Kết quả công bố](approved-result.png) |
| Chọn bài ở 390px | [Thiết lập mobile](mobile-setup.png) |
| Biểu đồ, điểm và nhận xét ở 390px | [Đánh giá mobile](mobile-evaluation.png) |
| Giữ file JavaScript, sau 15 giây có Thử lại | [Tải trang hữu hạn](bounded-workspace-loading.png) |

Các kiểm tra số học so sánh API evidence, điểm bài, lịch sử và thống kê; không
suy ra độ đúng chỉ từ ảnh. Trace chứa thông tin phiên chỉ giữ trong `_review/`
local, không đưa vào Git.

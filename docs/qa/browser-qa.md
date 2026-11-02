# Kiểm thử Learner và Admin bằng trình duyệt

Ngày 02/11/2026; mốc ban đầu `6140e8e`; nhánh `develop2`. Chạy `npm run reset`
rồi `npm start`, thao tác trên Chromium thật qua Playwright tại `localhost:18080`.
Ảnh gốc nằm trong `_review/qa/before/`; không dùng đáp án từ API quản trị để làm bài.
Tài khoản mới được đăng ký qua UI để kiểm tra trạng thái chưa có bài; Linh có một bài
đã công bố, An có hai bài mẫu trước khi bắt đầu kiểm thử.

## Lỗi ghi nhận trước khi sửa

| # | Kịch bản và thao tác | Thực tế | Mong đợi | Mức độ | Trạng thái / commit | Ảnh trước sửa |
|---|---|---|---|---|---|---|
| 1 | Learner giữ trang kết quả; Admin duyệt và công bố #5 | Vẫn chờ giảng viên; bấm làm mới mới nhận kết quả | Tự cập nhật khi công bố | Cao | Đã sửa: polling cả khi chờ duyệt; 18 test hồi quy đạt | `17-stale-after-publication.png` |
| 2 | Mở phân tích với 0 hoặc 1 bài | 0 bài có nhiều khối rỗng; 1 bài vẫn có điểm tích lũy, hạng, phân bố và tiến độ | 0 bài một lời mời làm bài; 1 bài chỉ phân tích bài đó; 2+ mới có xu hướng | Cao | Chưa sửa | `20-zero-analysis.png`, `21-single-analysis.png` |
| 3 | Đối chiếu cùng bài giữa Tổng quan, Bài đánh giá, Lịch sử | Tổng quan 69%, hai trang kia 59% do lấy trung bình khái niệm | Điểm bài nhất quán theo tổng điểm / tổng điểm tối đa | Cao | Chưa sửa | `02-learner-dashboard.png` |
| 4 | Đọc mã sau quan sát trạng thái chờ | Timeout dừng polling nhưng vẫn bật spinner; chưa có backoff/khóa request | Chờ hữu hạn, hết hạn dừng spinner và có thử lại | Vừa | Đã sửa: backoff 5–15/30s, giới hạn 5 phút độc lập với request, retry/focus; spinner dừng | Test `PendingResults`, `GradingWait` |
| 5 | Ở trang phân tích khi điểm được công bố | Nút làm mới chỉ nạp phần kỹ năng; thống kê là request riêng | Điểm, kỹ năng, hạng cùng cập nhật | Vừa | Chưa sửa | `08-analysis-pending.png` |
| 6 | Tải trang đăng nhập/bài làm | CSP chặn hai font nhúng data URL | Không có lỗi CSP; font phục vụ từ cùng nguồn | Vừa | Chưa sửa | Console trình duyệt |
| 7 | Xem phân tích và cài đặt ở desktop | Toàn trang tràn ngang; cài đặt sát lề, chữ trợ giúp bị cắt | Bố cục vừa viewport cả desktop/390px | Vừa | Chưa sửa | `08-analysis-pending.png`, `09-settings.png` |
| 8 | Mở Tổng quan Learner lần đầu | Nút bắt đầu nằm dưới phần biểu đồ; trạng thái chờ có nút sát link | Một hành động chính dễ thấy, nút chờ rõ ràng | Vừa | Chưa sửa | `02-learner-dashboard.png`, `07-no-key-wait.png` |
| 9 | Làm SQL và đọc ngữ nghĩa trang bài thi | DDL một dòng dài; hai landmark main lồng nhau | DDL dễ đọc và một main | Thấp | Chưa sửa | `05-sql-result.png` |
| 10 | Admin đọc CLO, tài khoản và duyệt tự luận | Đã xác nhận đi cùng Không xác định; tạo tài khoản mặc định Admin; badge ESSAY | Nhãn tiếng Việt rõ; mặc định Learner; không hiển thị độ tin cậy không có dữ liệu | Vừa | Chưa sửa | `11b-clo-mapping.png`, `12-accounts.png`, `15-manual-review.png` |

Không xóa hoặc giảm yêu cầu kiểm thử. Những assertion về chu kỳ polling/spinner sẽ
được cập nhật theo hành vi đúng mới và bổ sung kiểm tra backoff, timeout, chống chồng request.

## Những bước đã kiểm tra trước sửa

- Làm đủ 13 câu bằng UI: 10 trắc nghiệm, hai SELECT chạy trong sandbox, một tự luận.
- Reload sau autosave khôi phục lựa chọn; đồng hồ tiếp tục giảm; hộp xác nhận nộp rõ ràng.
- Không có API key: chuyển sang chờ giảng viên; bài chờ chưa được tính vào phân tích.
- Admin mở dashboard, CLO, tài khoản, ngân hàng câu hỏi, bài đánh giá, hàng chờ chấm;
  duyệt SQL 5/5 + 5/5, sửa tự luận thành 4,25/5 rồi công bố.
- Lịch sử, thống kê và báo cáo sau tải lại dùng kết quả đã công bố, không lộ danh sách
  người khác trong bảng hạng của Learner.

## Đối chiếu số học độc lập

Bài #5: cố ý sai một trắc nghiệm JOIN; 9/10 trắc nghiệm + 10/10 SQL + 4,25/5 tự luận
= **23,25/25 = 93%**. Các câu được duyệt hiển thị đúng điểm thành phần.

- CLO SQL: 5/6 trắc nghiệm + 10/10 SQL = **15/16 = 93,75%**.
- CLO thiết kế: 4/4 trắc nghiệm + 4,25/5 tự luận = **8,25/9 = 91,67%**.
- An: (67 + 59 + 93) / 3 = **73%**, UI thống kê 73%.
- Cả nhóm: (67 + 59 + 95 + 47 + 93) / 5 = **72,2%**, UI Admin 72,2%.
- Phân bố Admin: [0, 0, 2, 1, 2] cho năm khoảng 20%, tổng **5 bài**; UI khớp.
- CLO tích lũy của An: SQL **35/48 = 72,92%**; thiết kế **19,75/27 = 73,15%**,
  UI khớp. Đây là tổng điểm có trọng số, không phải trung bình các khái niệm.

Assertion cũ yêu cầu 60 lần polling/5 phút đổi thành 20 lần có backoff; assertion
spinner còn chạy sau timeout đổi thành không chạy, đồng thời kiểm tra aria-busy=false,
thông báo giảng viên, giới hạn request treo và khởi động lại. Đây là cập nhật theo
yêu cầu đúng mới, không bỏ kiểm tra. `ResultRace.test.jsx` vẫn giữ nguyên và đạt.

Kết quả gate, ảnh sau sửa, hash commit và giới hạn được ghi khi hoàn tất kiểm thử.

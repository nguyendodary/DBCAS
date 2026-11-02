# Kiểm thử Learner và Admin bằng trình duyệt

Ngày 02/11/2026; mốc ban đầu `6140e8e`; nhánh `develop2`. Chạy `npm run reset`
rồi `npm start`, thao tác trên Chromium thật qua Playwright tại `localhost:18080`.
Ảnh gốc nằm trong `_review/qa/before/`; không dùng đáp án từ API quản trị để làm bài.
Tài khoản mới được đăng ký qua UI để kiểm tra trạng thái chưa có bài; Linh có một bài
đã công bố, An có hai bài mẫu trước khi bắt đầu kiểm thử.

## Lỗi ghi nhận trước khi sửa

| # | Kịch bản và thao tác | Thực tế | Mong đợi | Mức độ | Trạng thái / commit | Ảnh trước sửa |
|---|---|---|---|---|---|---|
| 1 | Learner giữ trang kết quả; Admin duyệt và công bố #5 | Vẫn chờ giảng viên; bấm làm mới mới nhận kết quả | Tự cập nhật khi công bố, kể cả chờ lâu | Cao | Đã sửa: kiểm tra chờ duyệt mỗi 5–30s khi trang mở; không dừng sau timeout AI | `17-stale-after-publication.png` |
| 2 | Mở phân tích với 0 hoặc 1 bài | 0 bài có nhiều khối rỗng; 1 bài vẫn có điểm tích lũy, hạng, phân bố và tiến độ | 0 bài một lời mời làm bài; 1 bài chỉ phân tích bài đó; 2+ mới có xu hướng | Cao | Đã sửa: 0/1/2+ riêng, pending tách biệt | `20-zero-analysis.png`, `21-single-analysis.png` |
| 3 | Đối chiếu cùng bài giữa Tổng quan, Bài đánh giá, Lịch sử | Tổng quan 69%, hai trang kia 59% do lấy trung bình khái niệm | Điểm bài nhất quán theo tổng điểm / tổng điểm tối đa | Cao | Đã sửa: Tổng quan dùng overall_result_pct; chi tiết có tổng điểm | `02-learner-dashboard.png` |
| 4 | Đọc mã sau quan sát trạng thái chờ | Timeout dừng polling nhưng vẫn bật spinner; chưa có backoff/khóa request | Chờ AI hữu hạn, hết hạn dừng spinner và có thử lại | Vừa | Đã sửa: AI backoff 5–15s trong 5 phút, retry/focus; giảng viên 5–30s không spinner, không gửi request khi tab ẩn | Test `PendingResults`, `GradingWait` |
| 5 | Ở trang phân tích khi điểm được công bố | Nút làm mới chỉ nạp phần kỹ năng; thống kê là request riêng | Điểm, kỹ năng, hạng cùng cập nhật | Vừa | Đã sửa: refresh phối hợp và pending_formal_sessions; 43 test UI + 5 test PostgreSQL đạt | `08-analysis-pending.png` |
| 6 | Tải trang đăng nhập/bài làm | CSP chặn hai font nhúng data URL | Không có lỗi CSP; font phục vụ từ cùng nguồn | Vừa | Đã sửa: xuất font thành file, giữ CSP nghiêm ngặt | Console trình duyệt |
| 7 | Xem phân tích và cài đặt ở desktop | Toàn trang tràn ngang; cài đặt sát lề, chữ trợ giúp bị cắt | Bố cục vừa viewport cả desktop/390px | Vừa | Đã sửa; đọc ảnh sau sửa, scrollWidth bằng clientWidth cả 1521px và 375px | `08-analysis-pending.png`, `09-settings.png` |
| 8 | Mở Tổng quan Learner lần đầu | Nút bắt đầu nằm dưới phần biểu đồ; trạng thái chờ có nút sát link | Một hành động chính dễ thấy, nút chờ rõ ràng | Vừa | Đã sửa: nút bắt đầu trên đầu, bỏ nút lặp; nút chờ có kiểu dùng chung | `02-learner-dashboard.png`, `07-no-key-wait.png` |
| 9 | Làm SQL và đọc ngữ nghĩa trang bài thi | DDL một dòng dài; hai landmark main lồng nhau | DDL dễ đọc và một main | Thấp | Đã sửa: wrap DDL, bỏ main lồng | `05-sql-result.png` |
| 10 | Admin đọc CLO và duyệt tự luận | Nguồn gắn CLO hiển thị Không xác định; badge ESSAY | Nhãn nguồn gắn đúng và loại câu tiếng Việt | Vừa | Đã sửa nhãn. Kiểm tra lại: cấp tài khoản chỉ dành cho Admin theo UC04, mặc định này đúng hợp đồng và được giữ nguyên | `11b-clo-mapping.png`, `15-manual-review.png` |
| 11 | Hai tab cùng đăng nhập, reload đồng thời với access token ngắn hạn thật | Hai tab cùng xoay refresh token, server phát hiện replay và đăng xuất cả hai | Một lần xoay token dùng chung; không mất nháp | Cao | Đã sửa `ade433b`: Web Locks, đọc lại token sau khóa; 16 test auth đạt, kiểm lại browser giữ đăng nhập | `22-two-tabs-logout.png` |
| 12 | Tạo lại API container khi chuyển mode AI | API readiness đạt nhưng đăng nhập qua frontend trả 502 vì IP upstream cũ | Nginx cập nhật DNS Docker khi container thay đổi | Cao | Đã sửa `c84cb1e`: upstream resolve + zone, healthcheck kiểm cả proxy; nginx -t/readiness đạt | Log `provider-start`, ảnh lỗi đăng nhập |
| 13 | Provider AI lỗi khi đang chờ | Thông báo cần xử lý chấm điểm nhưng chưa nói rõ chờ giảng viên; Admin đọc JSON kỹ thuật để tìm feedback | Fallback giảng viên rõ, feedback/tiêu chí/trích dẫn dễ đọc | Vừa | Đã sửa; 31 test UI chấm/duyệt đạt | `discovery-ai/test-failed-1.png` |
| 14 | Gate CI chấm lại job lỗi | Test đọc object ORM cũ sau HTTP, rồi dùng now() của transaction trước retry; phụ thuộc vòng đời GC | Kiểm tra đúng dữ liệu đã commit và transaction mới của worker | Vừa / kiểm thử | Đã tái hiện bằng giữ tham chiếu job; sửa refresh và ranh giới transaction, giữ nguyên mọi assertion kết quả | `stale-job-repro.log`, `stale-job-fixed.log` |

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
`SupervisorWorkflows` được sửa fixture để trả đúng contract cho từng API, kiểm tra
một empty state và CTA thay cho khối rỗng lặp; smoke cũ đổi kiểm tra hạng ở bài đầu
thành kiểm tra phân tích một bài và không có xu hướng/hạng. 49 test UI liên quan đạt.
Hai browser assertion cũ trong `first-time-user-grading.spec.js` và
`supervisor-completion.spec.js` được cập nhật nhãn fallback/empty state; thêm kiểm
tra chờ giảng viên, tổng điểm chưa cuối cùng, CTA và không có điểm tích lũy giả.
CI còn phát hiện test retry giữ cache ORM. Tại
`backend/tests/test_supervisor_requirements.py:650`, thêm kiểm tra job ban đầu
failed/1, giữ tham chiếu để lỗi không phụ thuộc GC; tại dòng 664 đọc lại job và
kết thúc transaction đọc trước khi chạy worker. Giữ nguyên pending/0, 403, 409,
chấm lại và năng lực 100%. Không sửa hành vi ứng dụng để né assertion.

Kết quả gate, ảnh sau sửa, hash commit và giới hạn được ghi khi hoàn tất kiểm thử.

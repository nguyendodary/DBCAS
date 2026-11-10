# Kịch bản demo 5 phút — DBCAS

Mọi bài mới đều được đánh giá sơ bộ rồi quản trị viên kiểm tra và duyệt.
Không chọn luồng công bố. Dùng số lượt và trạng thái thực trên màn hình;
không phụ thuộc một tên học viên hay mã bài cố định.

## Địa chỉ và tài khoản

| Mục | Clone mới dùng mặc định | Profile cô lập đã kiểm chứng |
| --- | --- | --- |
| Ứng dụng | http://localhost:18080 | http://localhost:19180 |
| API / Swagger | http://localhost:18000/docs | http://localhost:19100/docs |
| Hộp thư local | http://localhost:18025 | http://localhost:19125 |
| Học viên | `learner@dbcas.local` | cùng tài khoản |
| Quản trị | `admin@dbcas.local` | cùng tài khoản |
| Mật khẩu chung | `Demo12345!` | cùng mật khẩu |

Profile cô lập `dbcas-finish-20261110` dùng mã ứng dụng cuối
`26d7e6d` (clone tại `7301a7f`). Readiness/API trả **200/200**; hai đăng nhập
qua trình duyệt và trang Cài đặt đều PASS, **0 page errors**. Bốn container
`dbcas-local` đang chạy của chủ dự án được giữ nguyên. Capture review tạo
các bài chờ duyệt trong profile cô lập; mở bài mới nhất của lần demo.

## Click path 5 phút

### 0:00–2:30 — Học viên

1. Đăng nhập `learner@dbcas.local` → **Tổng quan**: xem số lượt thực, điểm
   đã công bố và khái niệm cần ôn.
2. **Luyện tập** → chọn chip hoặc **Chọn tất cả khái niệm** → độ khó
   Dễ/Vừa/Khó → **Từ ngân hàng câu hỏi** → 3 hoặc 5 câu → **Bắt đầu**.
   Miền hợp lệ 1–20, mặc định 5 câu/30 phút; thông báo mở rộng phạm vi được giữ.
3. Chọn đáp án MCQ; ở SQL xem cấu trúc/dữ liệu, chạy một SELECT rồi lưu nháp.
   Tải lại để thấy đáp án còn nguyên. Nộp từng câu, rồi **Nộp bài** và xác nhận.
4. **Đánh giá bài làm** có thể đi qua trạng thái đang đánh giá trước khi hiện
   **Đang chờ giảng viên duyệt**. Điểm/đáp án chấm chưa được công bố.
5. **Đánh giá tổng thể** chỉ dùng bài đã công bố; bài mới đang chờ được báo
   riêng. Không bài: hướng dẫn bắt đầu; một bài: chưa có xu hướng; nhiều bài:
   xem xu hướng 0–100% và nội dung cần ôn.

### 2:30–4:30 — Quản trị

1. Đăng xuất → đăng nhập `admin@dbcas.local`.
2. **Tổng quan nhóm**: đối chiếu số bài đã công bố, thông báo chờ, bảng khái
   niệm và thống kê/xếp hạng. Bài chờ chưa được cộng điểm.
3. **Duyệt bài** → mở bài vừa nộp theo trạng thái **Chờ giảng viên duyệt**.
   Đọc nhận xét AI/dự phòng, mở đáp án và thang chấm; SQL có ô kiểm tra chỉ SELECT.
4. Nếu cần sửa điểm: nhập điểm và **Lý do điều chỉnh**, lưu; lịch sử giữ lý do.
   Bấm **Duyệt**, nhập ghi chú duyệt trong hộp xác nhận rồi xác nhận.
5. Quay lại học viên, kiểm tra cập nhật/tải lại để thấy kết quả đã duyệt.
   Đối chiếu đánh giá bài, tổng thể, lịch sử và thống kê đã cập nhật.
6. **Hệ thống** hiển thị quy trình bắt buộc cùng trạng thái AI; không hiển thị
   khóa API và không có bộ chọn luồng.

### 4:30–5:00 — Hoàn tất

- Cho thấy Cài đặt sáng/tối và tiếng Việt/Anh; nhãn và nội dung vẫn đủ ở mobile.
- Kế hoạch khái niệm/độ khó/số câu đóng băng trước câu đầu. SQL dùng ngân hàng
  đã kiểm định, sandbox SELECT cô lập. Prompt Builder chỉ xây một prompt;
  Evaluator đánh giá; quản trị viên duyệt kết quả chính thức.
- Demo dùng provider tắt/template và quy tắc dự phòng, có nhãn rõ ràng.
  Không thực hiện request live: ngân sách vòng cuối đã dùng hết theo sổ request.

## Khởi động và dự phòng

Clone mới: `npm start` không cần `.env` có sẵn. `npm run reset` tạo lại dữ
liệu demo của project được chọn; `npm start` bình thường giữ dữ liệu.

Để kiểm chứng mà giữ stack gốc, chạy trong clone
`_review/finish-20261110/fresh-clone` bằng PowerShell:

```powershell
$env:DBCAS_LOCAL_PROJECT='dbcas-finish-20261110'
$env:LOCAL_WEB_PORT='19180'
$env:LOCAL_API_PORT='19100'
$env:LOCAL_MAIL_PORT='19125'
$env:LOCAL_SMTP_PORT='19126'
$env:LOCAL_QA_PROVIDER_PORT='19199'
$env:LLM_API_KEY=' '
$env:LLM_BASE_URL='http://127.0.0.1:1/v1'
$env:LLM_MODEL='disabled-final-qa'
npm start
```

SMTP phải là 19126 để tránh đụng 11025 của stack gốc. Reset cô lập đã PASS
186.32s, start ban đầu 17.32s, start sau cập nhật UI 26.26s. Không reset lại
stack gốc hoặc xóa bài đang dùng làm bằng chứng.

- Readiness: `/readiness` trên cổng web trả 200; API `/health` trả 200.
- Mailpit là thư local, không gửi email thật. Dùng để minh họa đặt lại mật khẩu.
- Khi AI chưa xong, dùng **Kiểm tra cập nhật**; nếu provider tắt, nói rõ kết quả
  dự phòng chưa chứng minh chất lượng model thật.
- `npm run stop` chỉ dùng trong đúng clone/profile muốn dừng; dữ liệu được giữ.

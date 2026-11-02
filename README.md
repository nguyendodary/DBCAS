1. Cần Node.js 24 và Docker Desktop/Engine (Linux containers, Compose v2).
2. Clone nhánh `develop2`, vào thư mục repo và chạy `npm start`; không cần `.env` có sẵn.
3. Mở http://localhost:18080 · API http://localhost:18000/docs · Hộp thư http://localhost:18025.
4. Demo `admin@dbcas.local`, `learner@dbcas.local` · mật khẩu chung `Demo12345!`.
5. Đổi luồng: Admin → Hệ thống → Tự động / Admin duyệt → Lưu cấu hình. Huấn luyện tùy chọn: `npm run ai:train`.

# DBCAS local

Luyện tập cơ sở dữ liệu PostgreSQL với MCQ, SQL SELECT và tự luận. Một máy, một
lệnh khởi động; FastAPI, PostgreSQL 17, React/Vite. Không triển khai cloud.

Người học mở **Luyện tập**, chọn khái niệm, độ khó và nguồn **ngân hàng** hoặc
**AI tạo câu hỏi**, rồi **Bắt đầu**. Mặc định 5 câu/30 phút; số câu có thể đổi
trong tùy chọn. Thiếu câu ngân hàng thì chọn rộng hơn hoặc giảm số câu.
Không có đề dựng sẵn; demo có ngân hàng, CLO/khái niệm, ba người học và bốn bài
lịch sử. `linh@dbcas.local`, `minh@dbcas.local` cũng dùng mật khẩu demo ở trên.

Câu trả lời tự lưu nháp, tiếp tục được sau tải lại. SQL chạy trong sandbox tạm,
chỉ SELECT, không mạng, có giới hạn thời gian/tài nguyên. Kết thúc bài → **Xem
đánh giá**; **Đánh giá tổng thể** tổng hợp các bài đã công bố, hiển thị riêng số
bài còn chờ. Chưa có bài có nút bắt đầu; một bài chưa có xu hướng.

Flow 1 **Tự động** là mặc định: chấm và đánh giá xong thì công bố. Flow 2 **Admin
duyệt**: người học chờ; Admin mở **Duyệt bài**, kiểm tra đáp án/SQL/AI, có thể sửa
bất kỳ điểm nào với lý do rồi **Duyệt**. Kết quả có dấu đã duyệt/đã điều chỉnh;
thống kê và xếp hạng chỉ dùng kết quả công bố. Setting áp dụng cho bài bắt đầu
sau khi lưu, bài cũ giữ policy đã snapshot.

## AI tùy chọn

AI #1 chỉ xây dựng prompt tiếng Việt; model local không có/lỗi thì dùng template.
AI #2 đánh giá JSON, đồng thời là provider cho sinh câu hỏi. Không key hoặc API
lỗi thì dùng quy tắc/mẫu dự phòng, ghi rõ trên kết quả. Không cần key để chạy demo.
Đặt `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` trong `.env` để dùng API tương thích
Chat Completions. Không commit `.env`; giao diện chỉ hiển thị trạng thái cấu hình.

`npm run ai:train -- --smoke` xây dataset, chạy hai bước LoRA CPU trên model cực
nhỏ, export và inference. `npm run ai:train` dùng Qwen2.5-0.5B-Instruct; cần tải
dependencies/model ở lần đầu, training chạy trên máy và có thể tốn nhiều GB RAM.
Model smoke không có chất lượng ngôn ngữ hữu ích. Xem [pipeline, dữ liệu và giới
hạn](docs/ai-pipeline.md) trước khi dùng model để xây prompt.

## Dừng và kiểm thử

`npm run stop` dừng stack. `npm run reset` **xóa volume của project local** rồi
tạo lại demo; startup bình thường giữ dữ liệu đã sửa. Bản migration mới đóng đề
dựng sẵn của bản cũ, giữ FK và snapshot lịch sử.

```powershell
py -3.13 -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
backend/.venv/Scripts/python.exe backend/manage.py lint
backend/.venv/Scripts/python.exe backend/manage.py build
backend/.venv/Scripts/python.exe backend/manage.py test
npm --prefix frontend ci
npm --prefix frontend test -- --maxWorkers=2
npm --prefix frontend run build
npm --prefix frontend audit
npm run test:local
npm --prefix frontend exec playwright install chromium
npm --prefix frontend run test:practice -- --repeat-each=3
```

Linux/macOS dùng `.venv/bin/python`. Chạy tuần tự các gate dùng Docker
(backend → browser) để sandbox không tranh tài nguyên. Browser practice dùng
stack local đang chạy, tạo tài khoản kiểm thử riêng và phục hồi Flow 1 sau Flow 2;
không xóa DB demo. Ảnh/JSON nằm trong `_review/practice-browser*`.

`npm run test:qa` kiểm tra bằng provider HTTP giả local có delay/errors; không
gọi dịch vụ trả phí. `npm --prefix frontend run test:e2e` là suite trên DB/sandbox
dùng một lần có kiểm tra ownership. Kết quả đo, lỗi và phần chưa xác minh nằm
trong [trạng thái cuối](docs/final-status.md); báo cáo ngày cũ chỉ là lịch sử.

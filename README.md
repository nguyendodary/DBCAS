1. Điều kiện: Node.js 24 và Docker Desktop/Engine đang chạy Linux containers, có Compose v2.
2. Từ thư mục repo chạy `npm start` — tự tạo `.env`, migrate và seed demo.
3. Ứng dụng: http://localhost:18080 · Swagger: http://localhost:18000/docs · Hộp thư: http://localhost:18025.
4. Demo: `admin@dbcas.local` hoặc `learner@dbcas.local`, mật khẩu `Demo12345!`.
5. Dừng: `npm run stop` · Xóa dữ liệu stack local và tạo lại: `npm run reset`.

# DBCAS

Đánh giá năng lực PostgreSQL bằng trắc nghiệm, SQL và tự luận; xem kết quả,
CLO/kỹ năng còn thiếu và gợi ý ôn tập. Chỉ chạy local bằng Docker Compose trên
một máy. Stack: FastAPI/Python 3.13, PostgreSQL 17, React 19/Vite.

## Sử dụng

Learner: đăng nhập → Bài đánh giá → Bắt đầu; câu trả lời tự lưu nháp, có thể tiếp tục
sau khi tải lại. Đề demo gồm 10 MCQ, 2 SQL và 1 tự luận trong 60 phút. SQL chỉ SELECT,
chạy trong container tạm không mạng và có timeout. Admin: quản lý CLO, câu hỏi,
đề và người học; duyệt bài trước khi công bố. Mật khẩu demo là thông tin công khai
chỉ dùng cho dữ liệu thử trên máy cá nhân.

Quên mật khẩu: gửi liên kết từ trang đăng nhập rồi mở Hộp thư demo. Mailpit chỉ
nhận thư trong Compose trên máy này, không gửi email ra bên ngoài.

AI tùy chọn: đặt `LLM_API_KEY` trong `.env`, rồi chạy lại `npm start` để dùng
OpenAI (`gpt-5.4-mini`). Có thể đổi `LLM_BASE_URL` và `LLM_MODEL` theo provider.
Không có key thì giảng viên chấm tự luận; xem [cấu hình AI](docs/local-grading.md).
Không đưa `.env` vào Git. Startup giữ nguyên cấu hình/dữ liệu hiện có; reset chỉ
xóa volume thuộc project Compose `dbcas-local`, không tác động stack khác.

## Kiểm tra

Python 3.13 và Docker cho backend; Node 24 cho frontend:

```powershell
py -3.13 -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
backend/.venv/Scripts/python.exe backend/manage.py lint
backend/.venv/Scripts/python.exe backend/manage.py build
backend/.venv/Scripts/python.exe backend/manage.py test
npm --prefix frontend ci
npm --prefix frontend test -- --maxWorkers=2
npm --prefix frontend run build
```

Linux/macOS dùng `python3.13` và `.venv/bin/python`.
Bootstrap: `npm run test:local`. Test backend tự tạo/dọn DB và sandbox dùng một lần,
không dùng volume demo hoặc gọi provider trả phí.
Trên cùng máy, chạy lần lượt các gate dùng Docker (backend → browser → QA/smoke)
để sandbox không tranh tài nguyên và làm sai lệch kiểm tra thời gian chờ.

Smoke trên Compose đang chạy (ba lần liên tiếp, không retry):

```powershell
npm --prefix frontend ci
cd frontend
npx playwright install chromium
cd ..
npm run test:smoke
```

QA Learner/Admin từ DB sạch, cả không key và AI giả có độ trễ/lỗi, ba lượt liên tiếp:
`npm run test:qa`. Lệnh này **xóa DB demo trước mỗi lượt**, tạo tài khoản qua UI,
làm ba bài mỗi chế độ, duyệt/công bố, kiểm 0/1/nhiều bài, số học và hai tab/token
hết hạn. `.env` phải không có key thật; provider giả chỉ chạy bằng override
`docker-compose.qa.yml`, được dọn và phục hồi chế độ không key sau kiểm thử.
Ảnh và kết quả JSON: `_review/qa/`. Dùng `npm run test:qa -- 1` để kiểm tra một lượt.
Xem [báo cáo QA](docs/qa/browser-qa.md) về lỗi, ảnh và đối chiếu điểm.

Suite trình duyệt đầy đủ: `npm --prefix frontend run test:e2e`; cần venv backend
ở trên, Chromium và stack local đang chạy để dùng hộp thư. Suite tự tạo/dọn ba
container test có nhãn sở hữu và dùng các cổng 8100/5174, không sửa DB demo.

## Tài liệu

- [Trạng thái tính năng và nghiệm thu](docs/final-status.md)
- [Yêu cầu](docs/proposal.md), [kiến trúc/API](docs/architecture.md), [OpenAPI](docs/openapi.json)
- [Database](docs/database.md), [thuật toán năng lực](docs/competency-dn.md)
- [Sandbox và chấm SQL/AI](docs/grading-and-sandbox.md)
- [Báo cáo 13 task DN trước đợt hoàn thiện local](docs/dn/report.md)

Các báo cáo có ngày cũ trong `docs/` là bằng chứng lịch sử. Hướng dẫn Compose ở
đầu README là cách chạy hiện hành; không cần cấu hình production/cloud.

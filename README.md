Điều kiện: Node.js 24 và Docker Desktop/Engine đang chạy Linux containers, có Compose v2.
Chạy từ thư mục repo: `npm start` — tự tạo `.env` với secret ngẫu nhiên, migrate và seed demo.
Mở ứng dụng: http://localhost:18080 · Swagger: http://localhost:18000/docs.
Demo: `admin@dbcas.local` hoặc `learner@dbcas.local`, cùng mật khẩu `Demo12345!`.
Dừng: `npm run stop` · Xóa dữ liệu stack local và tạo lại: `npm run reset`.

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

AI tùy chọn: đặt đủ `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` trong `.env`, rồi
chạy lại `npm start`. Không cấu hình provider thì giảng viên chấm tự luận.
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
cd frontend
npm ci
npm test -- --maxWorkers=2
npm run build
```

Linux/macOS dùng `python3.13` và `.venv/bin/python`.
Bootstrap: `npm run test:local`. Test backend tự tạo/dọn DB và sandbox dùng một lần,
không dùng volume demo hoặc gọi provider trả phí.

## Tài liệu

- [Trạng thái tính năng và nghiệm thu](docs/final-status.md)
- [Yêu cầu](docs/proposal.md), [kiến trúc/API](docs/architecture.md), [OpenAPI](docs/openapi.json)
- [Database](docs/database.md), [thuật toán năng lực](docs/competency-dn.md)
- [Sandbox và chấm SQL/AI](docs/grading-and-sandbox.md)
- [Báo cáo 13 task DN trước đợt hoàn thiện local](docs/dn/report.md)

Các báo cáo có ngày cũ trong `docs/` là bằng chứng lịch sử. Hướng dẫn Compose ở
đầu README là cách chạy hiện hành; không cần cấu hình production/cloud.

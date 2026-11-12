# Chạy môi trường DN

Điều kiện: Git, Python 3.13, Docker Engine/Compose v2; Node theo lockfile nếu chạy UI.
Nhánh `develop2`; không dùng thay đổi chưa commit ở worktree khác.

## Chạy toàn bộ backend và DB trong Docker

Từ root, tạo `.env` nếu chưa có; không ghi đè cấu hình có sẵn:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
# Docker trên WSL: lấy số group, đặt DN_DOCKER_GID cùng số đó trong .env trước khi up.
wsl.exe -e stat -c '%g' /var/run/docker.sock
docker compose -f docker-compose.dn.yml up --build -d
docker compose -f docker-compose.dn.yml ps
```

API `http://localhost:18000/docs`, health `/health`, readiness `/readiness`.
Linux lấy group bằng `stat -c '%g' /var/run/docker.sock`; Docker Desktop socket
thường dùng group 0. Xem [mode sandbox tạm](docker-sandbox-dn.md) và quyền socket.
DB/sandbox chỉ trong network nội bộ, không publish cổng; container dùng tên service/cổng 5432.
Compose dùng volume `dbcas-dn_dn-db-data`, tách stack hiện có. Chỉ môi trường dev
mới seed admin công khai trong seed.sql; đổi mật khẩu trước khi chia sẻ.
API key AI bị để trống trong stack này; kiểm thử không gọi dịch vụ trả phí.
Nếu tự chạy backend trên host, dùng DB/sandbox riêng truy cập được trên host
(theo Quickstart Compose gốc trong README), cấu hình các DSN trong `.env`.
Mật khẩu trong URL phải được
percent-encode khi có ký tự dành riêng; credential Compose dùng chuỗi gốc.
Dev Compose phù hợp mật khẩu URL-safe; production theo hướng dẫn release riêng.

Dừng bằng `docker compose -f docker-compose.dn.yml stop`. Không xóa volume khi nâng cấp.
Init chạy schema/migration và seed lặp an toàn mỗi lần service init được tạo lại.
DB đang tồn tại có thể nâng cấp qua `docker compose -f docker-compose.dn.yml run --rm init`.

## Chạy trên host và kiểm tra

```powershell
cd backend
py -3.13 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe manage.py lint
.venv/Scripts/python.exe manage.py build
.venv/Scripts/python.exe manage.py test
.venv/Scripts/python.exe manage.py run
```

Linux/macOS dùng `python3.13` và `.venv/bin/python`. Test yêu cầu Docker, tự tạo
PostgreSQL 17/sandbox dùng một lần trên cổng ngẫu nhiên và dọn theo ownership label;
không đọc credential AI thật, không dùng volume dev. `test tests/dn` chỉ chạy test
DN; gate hoàn chỉnh chạy `test` không đối số. Lint chặn lỗi cú pháp/tên không tồn
tại/điều kiện sai; không áp formatter lên mã của team. Build compile và import
FastAPI/OpenAPI; image Docker có user không phải root.

Chạy cả giao diện hiện hữu mà không sửa file frontend:

```powershell
docker compose -f docker-compose.dn.yml --profile ui up --build -d
```

Giao diện tại `http://localhost:18080`, Nginx dùng API nội bộ qua alias `backend`.
`DN_WEB_PORT` tùy chỉnh cổng. Để làm UI trên host: trong `frontend`, `npm ci`,
`npm test`, `npm run build`, `npm run dev`; Vite proxy mặc định đòi backend host
ở 8000 theo cấu hình của nhóm. DN chỉ thêm wiring Compose, không đổi file frontend.

CI `.github/workflows/dn-backend.yml` chạy lint/build/test, kiểm tra OpenAPI, Compose
và build image trên push/PR develop2. Các tuyên bố "không CI" trong báo cáo cũ là
trạng thái lịch sử trước 01/11; CI mới không thay các gate browser/load/release của team.
Không coi việc push workflow là bằng chứng CI đã chạy thành công; xem kết quả Actions.

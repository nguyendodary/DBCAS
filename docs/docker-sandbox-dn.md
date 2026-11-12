# Sandbox Docker tạm của DN

`SANDBOX_MODE=shared` giữ stack/schema tạm cũ; `ephemeral` tạo một PostgreSQL 17
mới cho từng dataset thực thi, giữ giao diện provision/execute/drop cũ để toàn
bộ validator/chấm bài/worker/import bank cùng dùng. DN Compose chọn ephemeral.

```powershell
docker build -f sandbox/Dockerfile.ephemeral -t dbcas-sql-ephemeral:local .
docker compose -f docker-compose.dn.yml up --build -d
```

API image chứa Docker CLI, user app không phải root. Compose DN gắn socket Docker
và bổ sung group `DN_DOCKER_GID` (mặc định 0; chỉnh theo socket trên Docker host).
Socket cho backend tin cậy quyền điều khiển daemon, chỉ phù hợp máy phát triển/
executor chuyên dụng; không trao socket cho trình duyệt hoặc container chạy SQL.
Release/shared Compose của team không tự được gắn socket bởi thay đổi này.

Container SQL dùng user 10001, cap-drop ALL, no-new-privileges, root filesystem
chỉ đọc, tmpfs cho PGDATA/socket/tmp; không bind mount dữ liệu hoặc Docker socket.
`--network none`, không publish port; host truyền JSON bằng Docker exec stdin,
runner tin cậy dùng Unix socket nội bộ. [Docker none driver](https://docs.docker.com/engine/network/drivers/none/)
chỉ tạo loopback trong namespace container.

Giới hạn: 256 MiB RAM (không swap), 1 CPU, 128 PID, statement tối đa 3 giây;
SQL/kết quả/cell/setup bị giới hạn như runner cũ. Hai container đồng thời mỗi
process; nhân số worker khi tính RAM toàn máy. Lifetime mặc định 45 giây, cấu
hình 10–90 qua `SANDBOX_CONTAINER_LIFETIME_SECONDS`. Đang chờ slot trả
`sandbox_busy` sau 5 giây. Timeout/daemon/image lỗi trả mã an toàn, không ghi DSN.

Trước thực thi vẫn AST SELECT-only, chặn catalog/hàm nguy hiểm/multi-statement;
dataset chỉ chứa DDL/DML được allowlist, chạy bằng role setup không đăng nhập;
learner_ro không có quyền ghi/temp/create. SELECT trong READ ONLY transaction
luôn rollback. Không chuyển SQL người học sang DB hệ thống khi sandbox lỗi.

Đường thành công/lỗi luôn dọn ở finally và chỉ xóa container có owner label đúng.
Trong container còn watchdog gửi signal cho PID 1 khi lifetime hết; Docker `--rm`
tự xóa ngay khi Postgres dừng, kể cả process host chết. Nếu daemon đang ngừng,
dọn sẽ tiếp tục khi daemon/container hoạt động lại; không thể hứa dọn khi Docker
hoàn toàn không phục vụ. Watchdog giới hạn phiên còn tồn tại; không prune volume.

Readiness kiểm tra daemon truy cập được và image có protocol label, không tạo DB
mỗi probe. `validate_environment`/test tạo container thật để kiểm tra PostgreSQL,
role và timeout. Trên Windows có docker.cmd trỏ WSL, runner gọi `wsl.exe -e docker`
trực tiếp để giữ stdin, không chạy SQL qua shell.

Test: `python backend/manage.py test tests/dn/test_ephemeral_sandbox.py tests/test_sandbox.py tests/test_sandbox_safety.py`.

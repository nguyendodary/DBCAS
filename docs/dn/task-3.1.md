# Task 3.1 — Sandbox Docker tạm

Trạng thái đầu: **Đã có một phần**: container PostgreSQL riêng, schema tạm, AST
allowlist, learner_ro/READ ONLY/rollback, hạn mức kết quả. Review: an toàn SQL và
test shared đạt; chưa có container tạm/network none/hạn CPU ở mọi đường triển khai.
Tài liệu cần phân biệt mode shared/ephemeral và quyền Docker daemon.

Kế hoạch/thực hiện: thêm Dockerfile.ephemeral, stdin job và EphemeralSandboxRunner;
factory thống nhất cho HTTP/worker/validation/import/reconcile. Giữ shared legacy.
Container không mạng/cổng, chỉ tmpfs, rootfs read-only, UID 10001, cap-drop ALL,
no-new-privileges, 256 MiB/1 CPU/128 PID; lifetime hữu hạn/watchdog/--rm và finally
dọn có owner label. Hai lease đồng thời mỗi process. DN Compose build image và
gắn socket chỉ cho app tin cậy, hướng dẫn group/config. SQL editor đổi lỗi transport
thành 503. Phụ thuộc Docker Linux và image local, không có fallback sang DB hệ thống.

Kiểm tra: lint/build/OpenAPI/config/image build đạt; **121 passed** shared safety
và DN ephemeral; sau thêm probe network, test DN **3 passed**. Các test dùng Docker
thật: inspect limits/no mount/no port, typed rows, DDL/multi-statement bị chặn,
transport failure cleanup, statement timeout và watchdog xóa lease bỏ dở.
Smoke từ app container: EphemeralSandboxRunner → SELECT 7 → [[7]], readiness true.
Wrapper docker.cmd trên Windows làm mất exec stdin; đã gọi WSL CLI trực tiếp và
chạy lại đạt. Socket group máy này là 988, chỉ ghi vào .env local, không hardcode.

Chạy theo `docs/docker-sandbox-dn.md`; test bằng `python backend/manage.py test
tests/dn/test_ephemeral_sandbox.py tests/test_sandbox.py tests/test_sandbox_safety.py`.
Giới hạn: Docker socket có quyền cao, dành executor tin cậy; readiness kiểm tra
daemon/image, không khởi tạo SQL mỗi probe; daemon dừng làm chậm cleanup, watchdog
tiếp tục khi container chạy. Không còn thiếu hụt Task 3.1.
Commit: `Task 3.1: isolate SQL execution in disposable offline containers`.

# Task 3.10 — Tài liệu Docker, thuật toán và AI

Trạng thái đầu: **Đã có một phần**: setup/gates và các tài liệu riêng ở 3.1–3.3;
chưa có runbook tổng hợp hiện hành. Review: mã/thuật toán/test đạt ở task trước;
bảo mật cần mô tả quyền socket/opt-in provider; tài liệu cũ có mô tả lịch sử
khác max_tokens/CI hiện tại; nhất quán được xử lý bằng tài liệu DN có ngày rõ ràng.

Kế hoạch/thực hiện: tạo `docs/grading-and-sandbox.md`, liên kết README/kiến trúc,
gộp Docker/cleanup/lifecycle/MCQ/SQL/prompt/rubric/JSON/cache/retry/review và mã lỗi.
Thêm profile `ai-worker` có chủ đích vào Compose DN để hướng dẫn chạy chấm essay
qua env có thể thực hiện, không bật trong stack mặc định/test. Không chạy profile
thật hoặc sửa tài liệu testing/validation của team.

Kiểm tra: lint/build/OpenAPI, Compose config gồm profile, UTF-8/liên kết nội bộ
7 tài liệu đạt; **9 passed** release environment/result contracts, diff check đạt.
Command start/stop/schema/image đã được smoke tại Task 1.5/3.1; profile dùng cùng
worker đã có, env_file và network đúng. Chạy `python backend/manage.py test
tests/test_release_environment.py tests/test_result_contracts.py`.

Giả định/giới hạn: chưa live AI/load/TLS/production; redaction không phát hiện mọi
PII tự do; retry hai lớp và concurrent cache miss có thể tăng số call, được ghi
rõ. Không đổi điểm/quota hoặc nới validator. Không còn thiếu hụt Task 3.10.
Commit: `Task 3.10: document Docker scoring and AI operations`.

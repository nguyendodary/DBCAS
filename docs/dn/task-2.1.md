# Task 2.1 — Xác thực và phân quyền

Trạng thái đầu: **Đã có một phần**. Review: register/login/bcrypt/RBAC/guard,
OAuth/reset và test hiện hữu đạt; `/renew` không phải refresh độc lập. Chất lượng
phân lớp đạt, bảo mật thiếu refresh rotation/replay/logout; docs cần hợp đồng mới.

Kế hoạch/thực hiện: `services/refresh_tokens.py` dùng bảng Task 1.4, JWT purpose
refresh và hash SHA-256, expiry family tuyệt đối, khóa transaction, phát hiện
replay; thêm `/auth/refresh`, `/auth/logout`, config/DTO; gắn sid cho access và
kiểm tra family trong guard/renew. Đọc role/account hiện tại, không tự cấp Admin.
Password reset vô hiệu hóa token theo credential version. Thêm test DN riêng,
`docs/authentication-dn.md`, export OpenAPI/inventory. Phụ thuộc PyJWT/DB hiện có.

Kiểm tra: lint/build/OpenAPI drift/diff check đạt; **57 passed** auth/RBAC/shared
auth/password reset/refresh DN. Test gồm storage hash, rotation/replay, logout
lặp, expired/disabled/changed credentials, purpose separation, hai refresh đồng
thời chỉ một thành công và thu hồi family sau replay. Không gọi OAuth/LLM thật.

Chạy: `python backend/manage.py test tests/test_auth.py tests/test_rbac.py tests/test_shared_auth.py tests/test_password_reset.py tests/dn/test_refresh_tokens.py`.
Giả định: client mới dùng JSON refresh bearer; UI cũ giữ `/renew`. OAuth legacy
không có refresh family; không sửa frontend của team. Giới hạn vận hành được ghi
trong tài liệu auth; không còn thiếu hụt Task 2.1.
Commit: `Task 2.1: implement rotating refresh JWTs and session revocation`.

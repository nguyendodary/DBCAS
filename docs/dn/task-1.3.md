# Task 1.3 — Kiến trúc và API

Trạng thái đầu: **Đã có một phần** (84 route, DOT/SVG thành phần và luồng, DTO,
quy ước lỗi). Review: yêu cầu module/luồng đạt; chất lượng phân lớp đạt; test/RBAC
đã có; bảo mật runtime đạt; tài liệu thiếu OpenAPI lưu trong repo và Swagger chưa
mô tả Bearer/role/error envelope đúng; tính nhất quán được sửa bằng export runtime.

Kế hoạch/thực hiện: tạo `docs/architecture.md`, `backend/app/openapi.py`,
`scripts/export_openapi.py`, `docs/openapi.json`, test riêng `tests/dn`;
gắn role metadata vào guard và OpenAPI vào main, cập nhật inventory sinh tự động.
Không đổi hành vi kiểm tra quyền hoặc API response. Phụ thuộc FastAPI 0.141.1;
dùng `iter_route_contexts` vì phiên bản này giữ router dưới dạng context.

Kiểm tra: test hợp đồng thực tế **1 passed**, compileall thành công, export
70 path/84 operation và `--check` thành công; `git diff --check` đạt.
Test ban đầu phát hiện chưa duyệt included router; đã sửa và chạy lại đạt.
Có warning deprecation Starlette/httpx của dependency, không bỏ qua test.

Chạy từ root: `python scripts/export_openapi.py --check`; từ backend:
`python -m pytest -q tests/dn/test_openapi_contract.py`. Swagger `/docs`.
Giả định và giới hạn: metadata role không thay cho ownership/capability trong
service; frontend tiếp tục hợp đồng hiện tại. Không còn thiếu hụt Task 1.3.
Commit: `Task 1.3: publish architecture and executable OpenAPI contracts`.

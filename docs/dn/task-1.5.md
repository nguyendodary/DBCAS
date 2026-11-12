# Task 1.5 — Môi trường phát triển và CI

Trạng thái đầu: **Đã có một phần**. Review: stack/thư mục/Dockerfile/env đạt;
Compose dev chỉ DB/sandbox; chưa có lint/run script backend hay CI. Bảo mật release
đã có user không root/config fail-closed. Tài liệu cũ ghi kiểm tra thủ công.

Kế hoạch/thực hiện: thêm Compose DN độc lập app+init+DB+sandbox, cổng 18000,
biến env mẫu, `backend/manage.py`, ruff pin và workflow chỉ develop2. Tạo hướng
dẫn tiếng Việt và liên kết README; không sửa frontend/Compose hiện tại của team.
Lint ban đầu phát hiện hai forward annotation chưa khai báo; thêm TYPE_CHECKING
import, không đổi dependency runtime. Phụ thuộc Docker/Compose/Python.

Kiểm tra: cài mới virtualenv thành công; lint/build/pip check đạt; **15 passed**
cho readiness/release environment/test DN hiện có. Docker build/Compose config/up
đạt; app Python **3.13.16**, DB và sandbox readiness đều true. Host chỉ cài Python
3.14 nên gate host dùng 3.14; image đã smoke trên đúng Python 3.13, CI định nghĩa
3.13. Không khẳng định workflow remote đã xanh chỉ từ việc push.

Chạy/test theo `docs/development-dn.md`; `.env` local mới có credential ngẫu nhiên,
được Git ignore và không stage. Stack DN có volume riêng, không xóa dữ liệu cũ.
LLM thật bị tắt. Các gate UI/load/release của team giữ riêng.
Không còn thiếu hụt Task 1.5. Commit: `Task 1.5: add isolated development stack and backend CI`.

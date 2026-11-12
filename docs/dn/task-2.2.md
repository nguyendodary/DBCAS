# Task 2.2 — Ngân hàng và đề

Trạng thái đầu: **Đã có một phần**. Review: CRUD ba loại, phân loại, version và
blueprint đạt; thiếu phân trang/CLO/topic và gắn pool tường minh. Chất lượng/test/
bảo mật CRUD hiện hữu đạt; tài liệu cần phân biệt enum API viết thường và mode
formal viết hoa. Giữ toàn bộ validation/nghiệp vụ của team.

Kế hoạch/thực hiện: mở rộng bộ lọc và limit/offset, giữ response list legacy;
thêm migration 017/ORM assessment_question, service pool, GET/PUT pool và DTO;
bộ chọn eligible chỉ chọn trong allowlist khi có pool. Chặn xóa câu đang gắn,
chỉ draft chưa có phiên được sửa, invalid update rollback toàn bộ.
Thêm test DN, hướng dẫn ngân hàng, cập nhật DB/OpenAPI/inventory/ERD theo catalog
38 bảng/54 FK. Phụ thuộc schema/curriculum/RBAC Task 1.x–2.1.

Kiểm tra: **43 passed** CRUD/blueprint/migration và test DN; sau thêm response DTO,
test DN **2 passed**. Lint/build/OpenAPI/diagram render/check/diff check đạt.
Test DN kiểm tra CLO confirmed, topic/search/pagination, bounds, pool dùng bởi
repository thực, rollback khi ID sai, trùng, xóa câu có tham chiếu, bỏ pool và auth.

Chạy theo `docs/question-bank-dn.md`. Giả định: gắn câu là giới hạn pool, vẫn
adaptive và quota đã duyệt; không chuyển hệ thống thành đề có thứ tự tĩnh.
Limit bỏ trống giữ UI cũ. Lọc bản dịch/phân trang có phần chạy service; không hứa
query bounded cho ngân hàng rất lớn. Không còn thiếu hụt chức năng Task 2.2.
Commit: `Task 2.2: complete bank filters pagination and curated exam pools`.

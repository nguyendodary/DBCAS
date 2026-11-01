# Task 1.4 — Schema, migration và khởi tạo

Trạng thái đầu: **Đã có một phần**. Review sáu mặt: schema nghiệp vụ và FK/index
đạt; ORM theo DDL đạt; test migration hiện có đạt; seed chỉ dành cho dev; tài liệu
chưa có một lệnh init an toàn; thiếu nơi lưu refresh token cho Task 2.1.

Kế hoạch/thực hiện: giữ toàn bộ bảng nghiệp vụ, thêm migration
`016_refresh_sessions.sql`, ORM `RefreshSession`, đồng bộ `schema.sql`; tạo
`app.init_db`, `docs/database.md` và test DN riêng. Init có khóa/transaction,
chạy lặp, không reset, từ chối seed ngoài development và schema lạ.
Phụ thuộc PostgreSQL 17; không áp dụng vào DB/volume đang chạy của người dùng.

ERD/catalog/ledger được sinh lại từ DB PostgreSQL 17.11 tạm: 37 bảng/52 FK.
Giữ toàn bộ ID FK cũ; thêm quan hệ refresh → account. Cập nhật đúng số đếm/schema
fingerprint trong gate diagram, không thay logic validation/test độc lập của team.

Kiểm tra: **10 passed** (`test_migrations.py` + test init DN), compileall,
`npm run diagrams:render` và `diagrams:check` đạt (9 DOT, 2 Mermaid).
Đã sửa URL driver SQLAlchemy trong test DN để dùng URI libpq trước khi chạy lại.
Không có PlantUML source, tool báo không có nguồn; không bỏ test DB/sandbox.

Chạy từ backend: `python -m app.init_db --seed-development` với môi trường dev;
`python -m app.init_db` để init/upgrade không seed; `python -m app.migrate` để chỉ
nâng cấp. Seed hiện hữu tạo role/admin; benchmark đã duyệt dùng CLI
`python -m app.benchmark --help`, không tự xuất bản câu hỏi không được duyệt.
Giả định: tên miền được ánh xạ như Proposal; không tạo bảng song song.
Không còn thiếu hụt Task 1.4. Commit: `Task 1.4: initialize databases and add refresh session storage`.

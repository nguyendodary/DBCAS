# Kế hoạch triển khai DN cho DBCAS

**Mục tiêu:** Hoàn thành tuần tự 13 task DN, mỗi task có review, kiểm tra, commit và push develop2.
**Kiến trúc:** Giữ FastAPI/service/repository/PostgreSQL hiện có; bổ sung hợp đồng và các thiếu hụt.
**Stack:** Python 3.13, FastAPI, SQLAlchemy, psycopg, PostgreSQL 17, Docker Compose.
**Đặc tả:** [Proposal](../../proposal.md).

## Ràng buộc chung

- Thực hiện trực tiếp, tuần tự theo yêu cầu của người dùng; không chờ phê duyệt kế hoạch.
- Chỉ develop2; pull rebase trước từng task; commit/push khi đạt gate.
- Không sửa frontend hay test độc lập của thành viên khác, không dùng DB lâu dài trong kiểm thử.
- Chỉ SELECT trong sandbox; không gọi LLM thật ở test; giữ tên API/schema hiện có.
- Tài liệu tiếng Việt; code/comment/commit tiếng Anh; không secret trong Git.

## Điểm cần kiểm tra

Refresh replay/concurrency và password reset; nộp trùng/hết hạn; container cleanup khi lỗi;
kiểu số/NULL/bản sao khi so SQL; không có bằng chứng và kết quả AI chưa công bố khi tổng hợp.

## Danh sách theo thứ tự

Mỗi mục thực hiện: pull → tìm code/docs/test/log → ghi review sáu mặt → bổ sung →
lint/build/test theo phạm vi → stage/review chính xác → commit/push → ghi bằng chứng.

- [x] 1.1: Tạo `docs/proposal.md`, kế hoạch này và `docs/dn/task-1.1.md`.
  Kiểm tra liên kết, stack và ràng buộc so README/schema/config. Không đổi runtime.
- [x] 1.3: Tạo `docs/architecture.md`, export `docs/openapi.json`, công cụ
  `scripts/export_openapi.py`; thêm error/RBAC metadata trong `backend/app/main.py`.
  Tái sử dụng component/flow DOT hiện có; kiểm tra export lặp không lệch runtime.
- [x] 1.4: Tạo hướng dẫn DB/khởi tạo `backend/app/init_db.py` và migration cộng thêm
  cho refresh token; đồng bộ schema. Kiểm tra DB fresh/upgrade/repeat và constraint.
- [x] 1.5: Thêm Compose DN app/DB/sandbox, backend quality scripts, CI,
  README tiếng Việt; giữ Compose của team. Build image, lint, pip check và smoke.
- [x] 2.1: Thêm `services/refresh_tokens.py`, DTO/route và config refresh;
  dùng bảng Task 1.4, bảo toàn `/auth/renew`. Test rotation/replay/expiry/revoke/RBAC.
- [x] 2.2: Review `question_service.py`, `assessment_service.py`, repositories và
  routers admin; bổ sung thiếu phân trang/lọc/CLO/gắn câu qua hợp đồng hiện hữu.
  Test CRUD, filter, ownership, enum; cập nhật OpenAPI.
- [x] 2.3: Review session_service/grading_service/session_guard/draft lifecycle;
  sửa lỗi được chứng minh; test nháp, gửi trùng, hết hạn và snapshot MCQ.
- [x] 3.1: Thêm `services/ephemeral_sandbox.py` dùng Docker CLI với exec/pipe Unix
  socket, container `--network none`, timeout/RAM/CPU, cleanup và lease janitor.
  Tích hợp `deps.py` bằng mode config; test thực thi thật và cleanup.
- [x] 3.2: Review sql_result/sql_grading và feedback; test số/cột/dòng/kiểu/dataset
  có trọng số, trường hợp sai và điểm từng phần, giữ comparator xác định.
- [x] 3.3: Review essay_grading/LLM provider/cache/validation/review; bổ sung giới hạn
  output và test lỗi/quyền/caching, không dùng khóa thật.
- [x] 3.10: Tạo `docs/grading-and-sandbox.md` với cấu hình, công thức, prompt/rubric,
  flow, retry/cache/review, vận hành/cleanup và hạn chế. Kiểm tra lệnh/cấu hình.
- [x] 4.1: Bổ sung tổng hợp CLO/topic/difficulty từ điểm snapshot đã công bố trong
  `services/competency_dimensions.py`, giữ công thức point-weighted hiện có.
  Test số mẫu chính xác và không có evidence, xếp hạng/tie, đa nhãn.
- [x] 4.2: Thêm API dimensions/distribution/progress cho Learner/Admin dùng Task 4.1,
  tái sử dụng gap/guidance; test quyền, publication, thống kê và xuất OpenAPI.
  Chạy full backend/CI gates, xuất `docs/dn/report.md` cùng hash và hướng dẫn.

## Quy trình Git

Trước commit đọc CONTRIBUTING, review staged diff, kiểm tra danh tính team và
toàn bộ message; ưu tiên format `Task X.Y:` do người dùng chỉ định. Không force push.
Report của từng task đặt tại `docs/dn/task-X.Y.md`. Hash được ghi vào báo cáo tổng
hợp sau commit tương ứng; task cuối có thể có commit báo cáo bổ sung.

## K?t qu? ki?m tra cu?i

Backend: 1.161 test ??t, kh?ng l?i; hai assertion c? c?p nh?t ri?ng v?i ph? duy?t DN.
Frontend ch?y nguy?n tr?ng: 293 ??t, m?t l?i refresh/history ???c ghi cho TN/HN.
Chi ti?t ph? duy?t, file/d?ng, c?c hash v? gi?i h?n ? `docs/dn/report.md`.

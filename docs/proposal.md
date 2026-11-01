# Đề xuất DBCAS — yêu cầu triển khai DN

Ngày đối chiếu: 01/11/2026. Phạm vi: 13 task DN trên nhánh `develop2`.
Tài liệu này bổ sung đặc tả triển khai cho tài liệu học thuật trong
`docs/academic/`; không thay thế nội dung hay sửa các bản Word đã duyệt.

## Mục tiêu và bối cảnh

Đánh giá năng lực PostgreSQL của người học bằng MCQ, truy vấn SQL và tự luận;
lưu bằng chứng chấm điểm, xác định CLO/kỹ năng còn thiếu và đề xuất ôn tập.
Giữ stack hiện có: Python 3.13, FastAPI, SQLAlchemy, psycopg, PostgreSQL 17,
React 19/Vite; giao tiếp REST JSON với tiền tố `/api/v1`.

## Tác nhân và phân quyền

| Tác nhân | Trách nhiệm | Giới hạn |
| --- | --- | --- |
| Khách | Đăng ký Learner, đăng nhập, khôi phục mật khẩu | Không tự cấp quyền Admin |
| Learner | Làm bài, lưu nháp, nộp, xem kết quả đã công bố và tiến độ của mình | Không đọc đáp án/rubric nội bộ hoặc dữ liệu người khác |
| Admin (`Administrator` trong DB/API) | Quản lý ngân hàng, CLO, đề, người học; duyệt AI và công bố kết quả | Chỉ người có `can_manage_roles` được quản lý quyền quản trị |
| Worker | Chấm SQL/tự luận, xử lý hạn bài và tác vụ có retry | Không tin đầu ra AI trước kiểm định |
| Nhà cung cấp LLM | Trả JSON chấm tự luận theo rubric | Không nhận danh tính hoặc thông tin kết nối |

## Yêu cầu chức năng

| Mã | Yêu cầu và tiêu chí nghiệm thu | Task |
| --- | --- | --- |
| FR01 | Đăng ký chỉ tạo Learner; email duy nhất, mật khẩu băm bcrypt, JWT access và refresh có hết hạn, quay vòng và thu hồi | 2.1 |
| FR02 | Kiểm tra tài khoản active, quyền hiện tại và quyền sở hữu tại API; trả 401/403 nhất quán | 2.1 |
| FR03 | Admin CRUD câu MCQ/SQL/ESSAY, lựa chọn, dữ liệu kiểm thử, rubric; lọc/phân trang/tìm theo nội dung, topic, độ khó, CLO | 2.2 |
| FR04 | Admin CRUD assessment, gắn câu hỏi qua concept/blueprint và kế hoạch câu hỏi; chỉ kích hoạt ngân hàng hợp lệ, báo thiếu câu chính xác | 2.2 |
| FR05 | Bắt đầu/resume phiên bằng khóa idempotency, lưu nháp phía server, nộp một lần; hạn chót do server quyết định, bài quá hạn dùng nháp đã lưu | 2.3 |
| FR06 | MCQ so khớp lựa chọn hợp lệ với đáp án snapshot; lưu điểm và bằng chứng, không chấm lại do gửi trùng | 2.3 |
| FR07 | SQL chạy trong container tạm PostgreSQL biệt lập; không mạng, có giới hạn CPU/RAM/thời gian, chỉ SELECT; dọn tài nguyên cả khi lỗi | 3.1 |
| FR08 | Chấm SQL theo nhiều dataset có trọng số; so số cột, kiểu giá trị, NULL, bản sao và thứ tự khi đề yêu cầu; có điểm từng phần và phản hồi | 3.2 |
| FR09 | Chấm tự luận bằng LLM theo rubric, JSON có kiểm định; timeout/retry hữu hạn, cache theo nội dung và cấu hình, lưu để Admin duyệt | 3.3 |
| FR10 | Tính năng lực theo concept/kỹ năng, CLO, topic và độ khó từ điểm đã chấm; công thức xác định, xử lý không có bằng chứng riêng với điểm 0 | 4.1 |
| FR11 | Xếp hạng khoảng thiếu theo mục tiêu, gợi ý chủ đề, dashboard Learner/Admin, phân bố điểm và tiến độ; số liệu chính thức chỉ dùng kết quả được công bố | 4.2 |
| FR12 | Khởi tạo DB, migration cộng thêm và seed phát triển chạy lặp được; OpenAPI và hướng dẫn chạy/test đồng bộ mã | 1.3–1.5, 3.10 |

## Use case và luồng chính

1. Khách đăng ký → đăng nhập → nhận cặp token; refresh quay vòng khi access hết hạn;
   đăng xuất thu hồi phiên refresh. Frontend hiện tại vẫn dùng `/auth/renew` trong
   thời hạn tuyệt đối của phiên access để tương thích.
2. Admin tạo concept/CLO → tác giả tạo câu nháp → kiểm định/duyệt → gắn vào đề
   bằng hợp đồng assessment hiện có → xem trước và kích hoạt.
3. Learner chọn đề → server kiểm tra pool và thời hạn → tạo phiên, snapshot cấu hình
   và nội dung → lưu nháp → nộp → chấm MCQ tức thời, SQL/AI qua tác vụ bền vững.
4. Admin xem bằng chứng AI, phê duyệt hoặc sửa điểm có lý do → công bố → Learner
   xem kết quả/năng lực/khoảng thiếu; bài practice không tính vào năng lực chính thức.
5. Admin xem tổng quan cohort, phân bố điểm, CLO và xu hướng; Learner chỉ xem mình.

## Phạm vi nghiệp vụ

- Đề formal hiện hành: 60 phút, 10 MCQ / 2 SQL / 1 ESSAY, tối đa 13 câu;
  ba MCQ mở đầu cơ bản. Giữ adaptive theo quyết định đã duyệt và snapshot lịch sử.
- Practice có độ dài và phạm vi riêng, không thay thế kết quả formal.
- DML/DDL được đánh giá kiến thức bằng MCQ/tự luận, không thực thi SQL người học.
  Xem [quyết định phạm vi](requirements-decisions.md).
- CLO dùng bảng `course_learning_outcome`, kỹ năng dùng `concept`, liên kết
  `clo_concept`; không tạo hệ tên bảng song song user/exam/answer/result.
- DN phụ trách backend, DB, kiến trúc, DevOps và test hồi quy trực tiếp cho thay đổi
  của DN. Frontend, bộ validation và kiểm thử độc lập của TN/NN/N/HN được giữ nguyên.
- Ngoài phạm vi: trình duyệt chống gian lận chuyên dụng, thi lập trình đa ngôn ngữ,
  thực thi DML/DDL người học, multi-tenant, triển khai production/TLS và trả phí LLM
  thực tế trong bộ test tự động.

## Yêu cầu phi chức năng

| Mã | Chỉ tiêu | Bằng chứng nghiệm thu |
| --- | --- | --- |
| NFR01 | Không secret trong Git/log/response; môi trường production từ chối cấu hình mặc định | Kiểm tra config, test deployment, `.env.example` |
| NFR02 | SQL: không mạng, tối đa 1 CPU, 256 MiB, giới hạn PID, 3 giây cho statement, giới hạn kích thước SQL/kết quả; không dùng DB hệ thống | Kiểm tra cấu hình container và test thực thi PostgreSQL |
| NFR03 | Bất biến lịch sử, transaction/row lock/idempotency cho nộp và token rotation | Test gửi trùng, tranh chấp và migration giữ dữ liệu |
| NFR04 | LLM timeout mặc định 30 giây, mặc định 2 retry cho lỗi tạm thời; lỗi có mã máy, không công bố điểm không hợp lệ và tuân thủ release policy | Mock HTTP cho timeout/429/5xx/JSON sai |
| NFR05 | API có OpenAPI, request/response/error/RBAC rõ ràng, không làm hỏng client hiện có | Kiểm tra export không lệch runtime và test API |
| NFR06 | Migration có checksum và khóa, không reset/xóa volume; CI dùng DB dùng một lần | Test fresh/upgrade/idempotency |
| NFR07 | Mục tiêu tải: 100 người học hoạt động; SQL giới hạn đồng thời theo tài nguyên. Báo p95 và lỗi theo workload, không coi mục tiêu là kết quả đo | Gate tải riêng, không bịa chứng nhận hiệu năng |
| NFR08 | Tài liệu DN tiếng Việt; code/comment/commit tiếng Anh; lint/build/test và push từng task | Báo cáo DN, CI và Git log |

## Rủi ro và biện pháp

| Rủi ro | Biện pháp | Giới hạn còn lại |
| --- | --- | --- |
| SQL độc hại/cạn tài nguyên | AST allowlist + role chỉ đọc + rollback + container tạm có hạn mức, không mạng | Docker daemon có đặc quyền; chỉ backend/worker tin cậy được truy cập |
| AI chấm sai/prompt injection | Rubric cố định, tách nội dung không tin cậy, kiểm định JSON/điểm/evidence, duyệt thủ công | Kiểm thử mock không chứng minh chất lượng mô hình thật |
| Mất dữ liệu khi nâng cấp | Chỉ thử DB tạm; migration cộng thêm, backup trước nâng cấp dữ liệu thật | Không tự migrate DB phát triển đang chạy |
| Pool thiếu câu/nhãn sai | Dùng nội dung đã duyệt, kiểm tra độ phủ, báo thiếu thay vì tự giảm số câu | Seed lịch sử chưa đủ mọi tổ hợp formal |
| Rò refresh token | Token ngẫu nhiên, chỉ lưu hash, xoay vòng dưới khóa và thu hồi family khi replay | Client tích hợp mới cần lưu token an toàn |
| Tài liệu/lịch sử repo không đồng nhất | Hợp đồng mới liên kết rõ bảng/API hiện hữu; kiểm tra generated artifacts | Các báo cáo có ngày cũ là bằng chứng lịch sử |
| Worktree có thay đổi của thành viên khác | Checkout DN sạch riêng trên develop2, stage đúng file của từng task | Không đưa thay đổi chưa commit từ các worktree khác vào DN |

## Giả định và chuẩn hoàn thành

Admin là bí danh nghiệp vụ của `Administrator`; topic là `concept.subject_area`,
độ khó là số 1–5 (EASY 1–2, MEDIUM 3, HARD 4–5). Không đổi enum hiện có.
Nhánh `develop2` đã tồn tại, bắt đầu từ local HEAD `2823b28`; pull rebase lên
remote giữ các commit lịch sử của nhánh, không có xung đột. Các thay đổi chưa
commit ở worktree trước đó không thuộc baseline DN.

Mỗi task phải ghi review sáu mặt (yêu cầu, chất lượng, test, bảo mật, tài liệu,
nhất quán), hoàn tất code/tài liệu, chạy kiểm tra phù hợp, commit `Task X.Y:`
và push `origin develop2` trước task sau. Không đánh dấu Done nếu gate thất bại.

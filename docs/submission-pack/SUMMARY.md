# DBCAS — Tóm tắt bàn giao

- **Mốc chốt:** Architecture Freeze v1.2, tag cục bộ `arch-freeze-v1.2`; tài liệu nộp **ver1.3**.
- **Nhánh:** `develop2`; `main` chưa merge, chưa push.
- **Trạng thái:** ứng dụng demo/submission chạy thật; **production HOLD**.
- **Ngày tổng hợp:** 2026-11-25.

## 1. Tính năng chốt

| Khu vực | Hành vi đã chốt |
|---|---|
| Luyện tập chế độ 1 | Ngân hàng câu hỏi đã duyệt, đề FIXED, một concept và một band; trộn MCQ/SQL/tự luận; trần 25 câu (20/2/3), đơn loại 50/5/10. |
| Luyện tập chế độ 2 | AI sinh câu hỏi thích ứng theo năng lực; đúng +1 band, sai −1 band trong band hiện tại; prefetch cả hai nhánh; lỗi/timeout/thiếu key quay về ngân hàng đã duyệt. |
| Nguồn gốc AI | Câu AI được snapshot trên attempt với `source=ai_generated`, gắn nhãn **AI** trên UI và đưa vào hàng đợi `question_candidate` để admin duyệt/từ chối. |
| Sandbox SQL | Mặc định chỉ SELECT, không mạng, có statement timeout, giới hạn dòng/byte, container dùng một lần. Profile demo `writable` cho DML/DDL và luôn rollback. |
| Chấm DML | Câu trả lời và reference chạy trên cùng dataset; so sánh trạng thái bảng cuối với thứ tự dòng ổn định. Chấm SELECT giữ nguyên. |
| Kết quả | Bài FIXED công bố điểm AI chính thức V1 khi kết thúc; bài legacy/practice qua AI pre-grading rồi admin duyệt. Result version bất biến; sửa điểm phải có lý do audit. |
| i18n | UI tiếng Việt và tiếng Anh cùng bộ key; không lẫn ngôn ngữ; định danh kỹ thuật giữ nguyên. |
| Free/Pro | Mô phỏng UI, lưu plan trong `localStorage`; Free mở chế độ 1 kèm thông báo 5 phiên/ngày, Pro mở chế độ 2. Không có API thanh toán. |
| Xác thực | JWT access + refresh token luân chuyển, bcrypt, RBAC, OAuth Google/GitHub tùy chọn, mail đặt lại mật khẩu qua Mailpit. |
| Tài liệu | Nginx nhận body 30 MB; backend nhận upload nhị phân 20 MB. |

## 2. Kiến trúc

FastAPI modular monolith (router → service → repository → SQLAlchemy), PostgreSQL 17
qua Docker Compose, React/Vite SPA sau Nginx, SQL chạy trong container dùng một lần.
v1.1 không thêm service, database, queue hay framework mới. Một khối `LLM_*` chọn
provider OpenAI-compatible; prompt sinh câu hỏi lấy ví dụ trực tiếp từ JSON Schema.

## 3. Kết quả kiểm thử thật

| Gate | Kết quả |
|---|---|
| Backend lint (`ruff`) | PASS |
| Backend test | **1940 passed, 7 skipped** (1462.64 s, đo lại 2026-11-25) |
| Frontend lint (ESLint `--max-warnings=0`) | PASS |
| Frontend unit test | **54 file / 463 test** PASS |
| Docs gate | PASS — 48 assertion; 106 API path / 118 operation |
| OpenAPI contract | Khớp runtime |
| Environment inventory | 104 key backend + 3 key frontend |
| Route inventory | PASS sau khi tái sinh `docs/inventory/api-routes.json` |
| Secret scan (cây hiện tại) | **toàn bộ cây, 0 finding** (3129 file ở lần chạy cuối, 2026-11-25) |
| Secret scan lịch sử (mẫu key thật) | 1042 commit, **0 commit khớp**; các fixture giả nằm trong allowlist hash-pinned |
| Tài liệu nộp (`npm run docs:verify-word`) | **5 tài liệu, 149 assertion, 0 lỗi** |
| `npm run llm:check` | PASS — provider `openai_compatible`, `GET /models` HTTP 200 (63 model), chat HTTP 200, JSON hợp lệ, không in key |
| Clone sạch không có `.env` | Copy `.env.example` → `env:check` PASS chế độ AI-off → `npm start` PASS sau khi đặt `LOCAL_DOCKER_GID=988` qua WSL; `/readiness` báo `database: true`, `sandbox: true`; đăng nhập demo và Mailpit HTTP 200; stop + xoá container/volume sạch |
| Merge thử `develop2 → main` | `git merge-tree` không xung đột (`main` `e7e432c`, `develop2` hơn 200 commit) |
| E2E cuối (phiên 43/45/46) | 43: 8/8 câu, ability 3/5, điểm 4.40/8.00 (6 AI + 2 SQL fallback ngân hàng). 45: 3/3 SQL AI (INSERT/UPDATE/DELETE), điểm 1.00/0.00/1.00, rollback `true`. 46: tắt key → câu `bank`, hoàn thành 3/3; `.env` khôi phục đúng hash. Admin duyệt 126 → câu 4175, từ chối 125; chuyển vi/en không lẫn chữ |

## 4. Kết quả AI

- **Sửa prompt:** trial trực tiếp 5 loại × 3 lần tăng từ **0/15 lên 13/15** câu qua
  `validate_generated`. Hai ca còn lại là `RETURNING` sai cú pháp và được validator
  giữ nguyên từ chối — không nới validator.
- **E2E Mode 2 trước đó:** **8/8 câu `ai_generated`** ở cả tiếng Việt (phiên 22) và
  tiếng Anh (phiên 23), không fallback ngân hàng; độ khó đổi 1↔2 theo năng lực.
- **DML do AI sinh:** 14/14 câu SQL phục vụ đúng verb mục tiêu trong đợt kiểm chứng
  trước (INSERT 6, UPDATE 6, DELETE 2). Đáp án đúng **1.00**, sai **0.00**, reference
  `rolled_back: true`.
- **E2E cuối:** phiên 43 có 6/8 câu AI (MCQ/tự luận), 2 câu SQL fallback ngân hàng;
  phiên 45 (SQL-only) có **3/3 câu AI** theo vòng INSERT → UPDATE → DELETE với điểm
  **1.00 / 0.00 / 1.00** và rollback `true`; phiên 46 tắt key dùng câu `bank` và vẫn
  hoàn thành bài.
- **Hàng đợi admin:** đợt trước duyệt 1 (`promoted_question_id=4063`) và từ chối 1;
  đợt này duyệt ứng viên 126 (`promoted_question_id=4175`), từ chối ứng viên 125.

## 5. Giới hạn trung thực

- **Tỷ lệ validate tổng chưa đo lại.** Con số 13/15 là trial trực tiếp sau sửa
  prompt, không phải ước lượng cho toàn bộ câu đã phục vụ.
- **Token/chi phí theo phiên E2E là N/A.** API ứng dụng không trả `usage` cho từng
  câu; nhà cung cấp đang dùng không công bố đơn giá đáng tin cậy. Trial trực tiếp
  dùng 13.859 token/15 lần gọi, không quy cho các phiên E2E.
- **SQL DML cần WSL2 + Docker trên Windows.** SELECT và phần còn lại chạy với Docker
  Desktop thường; máy demo phải có WSL2 nếu muốn trình diễn DML.
- **OAuth chưa kiểm với provider thật.** Nút, callback và fake-provider đã có test;
  consent screen và credential Google/GitHub vẫn do owner cung cấp.
- **Câu SQL trong phiên 43 không do AI sinh.** Cả hai slot SQL fallback ngân hàng
  (`generation_sql_execution: empty_or_nondeterministic`); bằng chứng AI DML của đợt
  cuối đến từ phiên SQL-only 45, không phải từ phiên hỗn hợp.
- **Production HOLD.** Đây là bản demo/submission, không có triển khai cloud, thanh
  toán thật hay dữ liệu sinh viên thật.
- **Free/Pro chỉ là UI.** Không có route thanh toán, migration hay giao dịch thật.
- **Chưa có rate limit riêng cho SQL.** Giới hạn mỗi lần chạy và hai slot đồng thời
  là hàng rào hiện tại.

## 6. Bộ tài liệu nộp ver1.3

Sinh bằng một generator, đo lại toàn bộ số liệu, kiểm tra XML và render từng trang:

| Tài liệu | Tệp | Trang | Ngày |
|---|---|---:|---|
| Proposal | `C1SE.70_ProposalDocument_DBCAS_ver1.3.docx` | 20 | 25/11/2026 |
| Architecture Design | `C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx` | 22 | 25/11/2026 |
| Database Design | `C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx` | 39 | 25/11/2026 |
| Code Standards | `C1SE.70_CodeStandards_DBCAS_ver1.3.docx` | 12 | 25/11/2026 |
| Technical Report | `C1SE.70_TechnicalReport_DBCAS_ver1.3.docx` | 13 | 25/11/2026 |

- Thư mục: [`docs/submission/final`](../submission/final) (DOCX + PDF trong `rendered/`).
- Kiểm chứng: [`verification-report.md`](../submission/final/verification/verification-report.md) và
  [`TRACEABILITY.md`](../submission/final/TRACEABILITY.md).
- SRS **không còn** trong bộ tài liệu của owner (bản lưu: `Documents/Archive/C1SE.70_SRS_DBCAS_ver1.3.docx`).
- Quy cách đo được: [`doc-style-spec.md`](../agent/freeze-logs/doc-style-spec.md).
- Mã nguồn và lệnh chạy: [`SOURCE_CODE.md`](SOURCE_CODE.md).

## 7. Tài liệu

- [Release notes v1.1](../RELEASE_NOTES_v1.1.md)
- [Architecture freeze](../ARCHITECTURE_FREEZE.md)
- [Final gates](../agent/freeze-logs/final-gates.md)
- [Final manual E2E](../agent/freeze-logs/final-e2e.md)
- [Prompt contract fix](../agent/freeze-logs/prompt-contract-fix.md)
- [AI DML verification](../agent/freeze-logs/ai-dml-verification.md)
- [Demo runbook](../demo/README.md)

# DBCAS — Tóm tắt bàn giao

- **Mốc chốt:** Architecture Freeze v1.1, tag `arch-freeze-v1.1`, commit `696cdf9`.
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
| Backend test | **1940 passed, 7 skipped** (1434 s) |
| Frontend lint (ESLint `--max-warnings=0`) | PASS |
| Frontend unit test | **54 file / 463 test** PASS |
| Docs gate | PASS — 48 assertion; 106 API path / 118 operation |
| OpenAPI contract | Khớp runtime |
| Environment inventory | 104 key backend + 3 key frontend |
| Route inventory | PASS sau khi tái sinh `docs/inventory/api-routes.json` |
| Secret scan (cây hiện tại) | 2969 file, **0 finding** |
| Secret scan toàn bộ lịch sử (8038 blob) | 16 match, tất cả là fixture/placeholder (chuỗi `mock-only`, khóa QA giả, token giả trong test, giá trị `sk-` rút gọn dùng kiểm tra mask); **0 key thật** |
| `npm run llm:check` | PASS — provider `openai_compatible`, `GET /models` HTTP 200 (63 model), chat HTTP 200, JSON hợp lệ, không in key |
| Clone sạch + `.env` giả lập | `npm start` PASS sau khi đặt `LOCAL_DOCKER_GID`; `/readiness` báo `database: true`, `sandbox: true`; đăng nhập admin và `/api/v1/admin/accounts` trả 4 tài khoản; Mailpit HTTP 200; `npm run stop` sạch |
| Merge thử `develop2 → main` | `git merge-tree` không xung đột (`main` `e7e432c`, `develop2` hơn 200 commit) |
| E2E thủ công | Phiên 41: 8/8 câu trả lời HTTP 200, 6 câu `ai_generated` + 2 câu fallback ngân hàng, ability 2.0; admin duyệt/từ chối ứng viên; chuyển vi/en; tắt key vẫn chạy bằng ngân hàng |

## 4. Kết quả AI

- **Sửa prompt:** trial trực tiếp 5 loại × 3 lần tăng từ **0/15 lên 13/15** câu qua
  `validate_generated`. Hai ca còn lại là `RETURNING` sai cú pháp và được validator
  giữ nguyên từ chối — không nới validator.
- **E2E Mode 2:** **8/8 câu `ai_generated`** ở cả tiếng Việt (phiên 22) và tiếng Anh
  (phiên 23), không fallback ngân hàng; độ khó đổi 1↔2 theo năng lực.
- **DML do AI sinh:** 14/14 câu SQL phục vụ đúng verb mục tiêu (INSERT 6, UPDATE 6,
  DELETE 2). Đáp án đúng được **1.00**, đáp án sai **0.00**; toàn bộ reference
  `rolled_back: true`.
- **Hàng đợi admin:** 16 ứng viên sau hai phiên AI; duyệt 1
  (`promoted_question_id=4063`), từ chối 1; các phiên sau duyệt thêm ứng viên 117
  (`promoted_question_id=4168`) và từ chối 120.

## 5. Giới hạn trung thực

- **Tỷ lệ validate tổng chưa đo lại.** Con số 13/15 là trial trực tiếp sau sửa
  prompt, không phải ước lượng cho toàn bộ câu đã phục vụ.
- **Token/chi phí theo phiên E2E là N/A.** API ứng dụng không trả `usage` cho từng
  câu; model miễn phí đang dùng không có giá công bố đáng tin cậy. Trial trực tiếp
  dùng 13.859 token/15 lần gọi, không quy cho các phiên E2E.
- **SQL DML cần WSL2 + Docker trên Windows.** SELECT và phần còn lại chạy với Docker
  Desktop thường; máy demo phải có WSL2 nếu muốn trình diễn DML.
- **OAuth chưa kiểm với provider thật.** Nút, callback và fake-provider đã có test;
  consent screen và credential Google/GitHub vẫn do owner cung cấp.
- **Production HOLD.** Đây là bản demo/submission, không có triển khai cloud, thanh
  toán thật hay dữ liệu sinh viên thật.
- **Free/Pro chỉ là UI.** Không có route thanh toán, migration hay giao dịch thật.
- **Chưa có rate limit riêng cho SQL.** Giới hạn mỗi lần chạy và hai slot đồng thời
  là hàng rào hiện tại.

## 6. Tài liệu

- [Release notes v1.1](../RELEASE_NOTES_v1.1.md)
- [Architecture freeze](../ARCHITECTURE_FREEZE.md)
- [Final gates](../agent/freeze-logs/final-gates.md)
- [Prompt contract fix](../agent/freeze-logs/prompt-contract-fix.md)
- [AI DML verification](../agent/freeze-logs/ai-dml-verification.md)
- [Demo runbook](../demo/README.md)

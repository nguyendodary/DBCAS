# Vận hành Docker và pipeline chấm DBCAS

Tài liệu DN ngày 01/11/2026 trên develop2; các báo cáo có ngày trước đó giữ giá
trị lịch sử. Nội dung hiện hành được đối chiếu service/config/OpenAPI và các gate
PostgreSQL/Docker/HTTP mock. Không sửa Word học thuật hay hướng dẫn test của team.

## Khởi động, schema và sandbox

1. Làm theo [môi trường DN](development-dn.md), tạo `.env` từ mẫu nếu chưa có;
   cấu hình group Docker socket và mật khẩu URL-safe, không commit `.env`.
2. `docker compose -f docker-compose.dn.yml up --build -d` tạo stack DN biệt lập.
   Init giữ khóa, tạo schema/migrate/seed dev lặp an toàn; không xóa volume cũ.
3. Đọc `/health` và `/readiness` tại cổng 18000; Swagger `/docs`. Câu hỏi seed
   lịch sử chưa đủ mọi tổ hợp formal: nhập bank benchmark đã duyệt bằng CLI hiện
   hữu sau review, không giảm quota để che thiếu dữ liệu.
4. Mode ephemeral tạo container riêng từng dataset, truyền JSON qua Docker exec,
   Unix socket nội bộ, không mạng/cổng/mount dữ liệu. READ ONLY/AST allowlist vẫn
   áp dụng; giới hạn 256 MiB/1 CPU/128 PID/3 giây, rootfs chỉ đọc và tmpfs.
5. Mọi nhánh thành công/lỗi dọn theo owner label; watchdog + `--rm` xử lý lease
   bị bỏ dở. Không prune hệ thống hoặc xóa volume. Không dùng SQL người học trên
   DB hệ thống khi sandbox lỗi. Chi tiết [sandbox Docker](docker-sandbox-dn.md).

CLI Docker/socket chỉ nằm trong app/worker tin cậy; không đưa vào executor SQL.
Host process giới hạn hai container đồng thời; toàn hệ thống phải tính theo số
worker. Sự cố daemon có thể trì hoãn dọn tài nguyên đến khi daemon trở lại.

## Lưu/nộp và chấm xác định

Client bắt đầu phiên/idempotency UUID → server snapshot đề/câu → lưu nháp theo
revision → submit atomic. Deadline dùng đồng hồ DB, không tin đồng hồ browser.
Gửi trùng cùng đáp án trả kết quả cũ ở `/submit`; `/answers` legacy trả conflict.
Timeout nộp nháp đã lưu đúng một lần; xem [lifecycle/MCQ](attempts-and-mcq.md).

MCQ: lựa chọn thuộc câu và đúng key snapshot → toàn điểm, sai/bỏ trống → 0.
SQL: từng dataset → provision → execute SELECT → typed comparator → cleanup.
Score SQL = points × số dataset đạt / tổng dataset, HALF_UP hai chữ số; mọi
dataset có trọng số 1. Không dataset là lỗi cấu hình 422. Kỹ thuật bắt buộc mà
AST chứng minh là thiếu → 0; không thể chứng minh thì ghi unverified. Không so
chuỗi query; mặc định bỏ thứ tự dòng nhưng giữ số lần lặp, có thể bật ordered
và check_columns. Decimal/NULL/boolean/text được phân biệt. Xem [SQL grading](sql-grading-dn.md).

## Prompt, rubric và JSON AI

Nguồn prompt chuẩn: [essay_grading.py](../backend/app/services/essay_grading.py).
Prompt hệ thống yêu cầu chấm đúng tiêu chí, không thưởng dài dòng, không làm
theo lệnh chèn trong bài, trích một evidence cùng index cho từng matched criterion.
Calibration là bộ ví dụ riêng; điểm/band của câu thật vẫn là thẩm quyền duy nhất.
Prompt user gồm đề, reference để hiệu chuẩn, maximum score, bốn band/criteria và
bài đã ẩn danh. Không ghép account_id/email/tên/SĐT vào prompt; bộ sanitizer che
định danh trong bài và các identifier được caller truyền.

Ví dụ rubric cho câu 1 điểm, không thay rubric hiện hữu:

| Mức | Khoảng điểm | Tiêu chí mẫu |
| --- | --- | --- |
| Incomplete | 0–0.24 | Không giải thích đúng điều kiện 3NF |
| Partial | 0.25–0.49 | Chỉ nêu một phần định nghĩa |
| Mostly Complete | 0.50–0.74 | Có điều kiện chính, còn thiếu trường hợp thuộc tính prime |
| Complete | 0.75–1 | Giải thích đúng mọi dependency không tầm thường |

Một JSON hợp đồng hợp lệ về cấu trúc (evidence phải có thật trong bài tương ứng):

```json
{"rubric_level":"Complete","score":0.9,"confidence":0.8,"matched_criteria":["Điều kiện 3NF"],"missing_concepts":[],"evidence":["superkey or A prime"],"explanation":"Định nghĩa thể hiện đủ điều kiện.","feedback":"Luyện thêm ví dụ phân rã."}
```

LLMService ẩn PII → hash cache gồm provider/model/prompt/rubric/schema/locale và
tham số → nếu miss, gọi REST `/chat/completions` → parse/kiểm schema/điểm/evidence
→ chỉ cache JSON đã qua miền → lưu attempt/evidence. Cache hit cũng kiểm định lại.
Điểm ngoài band, thiếu field, NaN, evidence không nằm trong bài, trả safety text
hoặc truncated đều không được coi là grade. Cache không có cam kết chống gọi
trùng đồng thời; hai miss đồng thời có thể gọi provider hai lần.

## Retry, lưu trữ và human review

Timeout HTTP mặc định 30 giây, hai retry và backoff tuyến tính 0.5 giây; output
tối đa 2048 token. Retry chỉ lỗi tạm thời/network/429/5xx, ngoài một compatibility
điều chỉnh reasoning trong cùng budget; 401/403 dừng. Không honor Retry-After.
Worker grading_job retry riêng mặc định tối đa ba lần, cách 30 giây. Như vậy tổng
lượt gọi có thể lớn hơn ba; timeout từng request không là deadline toàn job.

API bình thường xử lý MCQ/SQL, quét hạn bài; DN Compose để LLM trống ở app nhằm
không tự phát sinh chi phí. Sau khi operator đã duyệt provider/model/ngân sách,
điền LLM_API_KEY/BASE_URL/MODEL trong `.env` và chủ động bật riêng worker:

```powershell
docker compose -f docker-compose.dn.yml --profile ai-worker up --build -d ai-worker
```

Profile này là hành động bật provider calls; không được chạy trong test. Worker
đọc key từ env_file và không trả key ra API. Xem [AI essay](essay-ai-dn.md).
Ngừng worker bằng `docker compose -f docker-compose.dn.yml stop ai-worker`.
Điểm đề xuất/evidence lưu trong attempt; Admin review có audit, sửa hoặc approve
rồi publish theo result_release_policy. Practice không góp vào năng lực chính thức.
Mọi bài practice mới dùng `HUMAN_VERIFIED`: AI chấm/đánh giá sơ bộ, quản trị viên
duyệt các điểm SQL/essay rồi mới công bố. `IMMEDIATE` chỉ còn trong dữ liệu lịch sử;
giao diện không còn lựa chọn hai luồng.

## Lỗi và khắc phục

| Mã/HTTP | Ý nghĩa | Xử lý |
| --- | --- | --- |
| session_expired / 409 | Hết thời hạn server | Lấy trạng thái, dùng kết quả nháp đã lưu, không gửi answer mới |
| draft_revision_conflict / 409 | Nháp mới hơn đã tồn tại | GET draft và hợp nhất input của client |
| not_a_select, multiple_statements | SQL ngoài phạm vi | Trả feedback, không thực thi |
| timeout, result_too_large | Query vượt hạn | Tối ưu query; không tăng giới hạn tùy tiện |
| sandbox_busy/unavailable / 503 | Hết slot/daemon/image/transport | Retry hữu hạn, kiểm tra image và group socket |
| dataset_not_configured / 422 | Câu SQL không có fixture | Admin sửa/duyệt bank, không thưởng điểm |
| llm_not_configured/auth_failed / 503 | Thiếu/sai cấu hình provider | Kiểm tra env phía server, không hỏi Learner về API key |
| llm_timeout/rate_limited/provider_error / 503 | Provider chưa hoàn tất | Job retry hữu hạn hoặc human takeover |
| llm_invalid_response / 502 | JSON/điểm/evidence không hợp lệ | Không cache/chấp nhận điểm, Admin xử lý |

## Kiểm tra và giới hạn

Từ root với virtualenv đã cài dev requirements:

```powershell
python backend/manage.py lint
python backend/manage.py build
python backend/manage.py test
python scripts/export_openapi.py --check
docker compose -f docker-compose.dn.yml --profile ai-worker config -q
```

Test tạo PostgreSQL 17/Docker tạm và dùng HTTP mock cho LLM, không migrate volume
dev và không gọi model thật. Gate browser/load/production/TLS ở tài liệu team là
quy trình khác; chưa có phép đo mới không được ghi đã đạt 100 người đồng thời.
PII redaction không bảo đảm phát hiện mọi dữ liệu cá nhân viết tự do. Output token
limit không là giới hạn chi phí dollar. Docker giảm phạm vi ảnh hưởng, không phải
VM cách ly kernel; cần executor host tin cậy/giới hạn tải ở triển khai thật.

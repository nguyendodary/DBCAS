# Báo cáo triển khai DN — 01/11/2026

> Báo cáo lịch sử của 13 task DN. Đợt hoàn thiện ngày 02/11 nhận toàn bộ phạm vi
> frontend/backend/test, đã sửa lỗi refresh được ghi ở cuối bản này. Trạng thái
> hiện hành và cổng nghiệm thu nằm trong [báo cáo local](../final-status.md);
> các ghi chú phân công cũ không phải công việc đang chờ thành viên khác.

Nhánh làm việc: `develop2`. Checkout DN:
`_worktrees/dbcas-dn-20261101` trong workspace. Các thay đổi chưa commit của các
worktree main/stabilization cũ được giữ nguyên, không được đưa vào commit DN.
Nhánh develop2 đã tồn tại từ trước, local HEAD ban đầu `2823b28`; fetch/checkout/
pull rebase không có xung đột, giữ 55 commit lịch sử sau rebase. Mỗi task đã push
trước khi bắt đầu task tiếp theo; không force push, không commit lên main/develop.

## Ma trận công việc

"Done (một phần)" ở cột đầu nghĩa là repo đã có triển khai cần review/bổ sung,
không phải trạng thái nghiệm thu cuối. Các nhóm test có giao nhau, không cộng số
ở bảng để suy ra số test toàn hệ thống. Report chi tiết ở `task-X.Y.md`.

| Task | Ban đầu | Review / thực hiện | File chính | Test theo phạm vi | Commit |
| --- | --- | --- | --- | --- | --- |
| 1.1 | Not done | Yêu cầu nằm rải rác, thiếu Proposal Markdown; chốt FR/NFR, actor, use case, phạm vi/rủi ro | docs/proposal.md | UTF-8, link, diff | 458bc1c |
| 1.3 | Done (một phần) | Tái dùng sơ đồ, thêm kiến trúc tiếng Việt/OpenAPI đúng error/Bearer/RBAC, export/check | app/openapi.py, docs/architecture.md, docs/openapi.json | 1 passed + export/compile | 577c6b7 |
| 1.4 | Done (một phần) | Giữ schema, init có khóa/transaction, seed dev lặp an toàn; migration refresh; ERD catalog thật | app/init_db.py, db/schema.sql, migrations/016, docs/database.md | 10 passed + diagram gate | e2f5ea2 |
| 1.5 | Done (một phần) | Compose DN biệt lập, env, lint/build/test, CI Python 3.13 và README | docker-compose.dn.yml, backend/manage.py, .github/workflows/dn-backend.yml | 15 passed; image/Compose/readiness | f6bdb29 |
| 2.1 | Done (một phần) | Bổ sung refresh JWT rotation/hash/replay/logout và thu hồi access family, giữ renew cũ | services/refresh_tokens.py, security.py, routers/auth.py | 57 passed | cd4666c |
| 2.2 | Done (một phần) | CRUD cũ đạt; thêm CLO/topic/filter/pagination và gắn pool adaptive; migration 017 | services/assessment_pool.py, routers/admin.py, migrations/017 | 43 passed + 2 DTO regression | 42014d7 |
| 2.3 | Done | Xác nhận start/nháp/revision/MCQ/atomic submit/timeout/snapshot, bổ sung hợp đồng tích hợp | docs/attempts-and-mcq.md; code lifecycle hiện hữu | 51 passed | fbed853 |
| 3.1 | Done (một phần) | Container tạm không mạng, 1 CPU/256 MiB, UID/cap/rootfs/tmpfs/timeout/watchdog/cleanup | services/ephemeral_sandbox.py, sandbox/Dockerfile.ephemeral, sandbox_job.py | 121 passed + 3 network/watchdog; app SQL smoke | 2a062bc |
| 3.2 | Done (một phần) | Comparator/partial có sẵn; sửa không dataset được full điểm, kiểm typed multiset | services/sql_grading.py, docs/sql-grading-dn.md | 93 passed | 1ddbdf2 |
| 3.3 | Done (một phần) | AI/rubric/cache/review đạt; thêm bounds config, 502 và test trần token/cache khi đổi rubric | config.py, docs/essay-ai-dn.md, tests/dn/test_essay_contracts.py | 132 passed | d4afc21 |
| 3.10 | Not done | Runbook Docker/MCQ/SQL/prompt/rubric/AI/cache/retry/review; worker AI opt-in | docs/grading-and-sandbox.md, Compose ai-worker | 9 passed, Compose/link/OpenAPI | a1a7e13 |
| 4.1 | Done (một phần) | Bổ sung CLO/topic/difficulty/rank point-weighted, snapshot CLO và báo unknown lịch sử | services/competency_dimensions.py, evidence_context.py | 112 passed | 5161f62 |
| 4.2 | Done (một phần) | Dashboard Learner/Admin, distribution/progress/rank/topic gap; sửa integration pool; assertion được duyệt tách commit | services/statistics_service.py, schemas_analytics.py, docs/analytics-dn.md | Backend full gate 1.161 passed, 0 failed; lint/build đạt | ee99a12 (assertion); HEAD (implementation) |

`HEAD` trong hàng 4.2 là commit implementation chứa chính phiên bản báo cáo này;
lấy hash bằng `git log -1 --format=%h -- docs/dn/report.md`. Bản tổng kết bàn giao
ghi hash thực sau khi tạo commit. Hai commit 4.2 tách biệt hoàn toàn.

## Chạy toàn hệ thống

Từ checkout develop2, tạo `.env` từ `.env.example` nếu chưa có; điền secret dev
riêng và `DN_DOCKER_GID` đúng group của Docker socket. Trên WSL lấy số bằng
`wsl.exe -e stat -c '%g' /var/run/docker.sock`, Linux dùng `stat` trực tiếp.

```powershell
docker compose -f docker-compose.dn.yml --profile ui up --build -d
docker compose -f docker-compose.dn.yml ps
```

UI `http://localhost:18080`, Swagger `http://localhost:18000/docs`, health/readiness
trên cổng 18000. DB nội bộ có init/migration/seed lặp an toàn, không publish cổng
và không dùng volume của stack team. Frontend được build nguyên trạng từ repo,
không sửa file frontend. Mặc định không gọi provider LLM.

Muốn chấm essay qua provider thật, operator chọn provider/model/ngân sách và cấu
hình LLM_* trong env, rồi chủ động bật `--profile ai-worker ... up -d ai-worker`
theo [runbook](../grading-and-sandbox.md). Không có key thật hoặc live call trong
gate DN. Dừng stack bằng `docker compose -f docker-compose.dn.yml stop`; không xóa
volume để nâng cấp. Seed dev có mật khẩu công khai, phải đổi trước khi chia sẻ.

## Lệnh kiểm tra

Python 3.13 theo stack/CI; máy Windows này chỉ cài 3.14 nên host gate dùng 3.14,
image app/sandbox và CI dùng Python 3.13. Chưa đồng nhất phiên bản host không
được báo là đã kiểm bằng Python 3.13 trên host.

```powershell
cd backend
py -3.13 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe manage.py lint
.venv/Scripts/python.exe manage.py build
.venv/Scripts/python.exe manage.py test
.venv/Scripts/python.exe -m pip check
cd ..
backend/.venv/Scripts/python.exe scripts/export_openapi.py --check
backend/.venv/Scripts/python.exe scripts/generate_route_inventory.py --verify
npm ci
npm run diagrams:check
docker compose -f docker-compose.dn.yml --profile ui --profile ai-worker config -q
```

Linux/macOS thay bằng `python3.13` và `.venv/bin/python`. Test tự tạo PostgreSQL
17/sandbox tạm với owner label và dọn, không dùng DB lâu dài; image ephemeral được
build từ Dockerfile trong fixture. Không skip gate DB/Docker khi thiếu dependency.
Report/log test local nằm `_review/`, Git ignore. Thông tin test giả không phải dữ
liệu người học thật; không đưa log nội bộ vào Git.

Đã kiểm thêm: lint mạnh E4/E7/E9/F trên toàn file DN mới; build/import; pip check;
OpenAPI 75 path/90 operation và 1.025 reference nội bộ hợp lệ; 27 tài liệu có link/
UTF-8 đạt; 9 DOT + 2 Mermaid/schema fingerprint đạt; cả ba Compose hợp lệ.
Smoke network thực qua Nginx: UI/proxy/readiness, register/login, statistics owned,
refresh/logout và SELECT 777 trong container không mạng đều đạt. Frontend production
image build đạt; unit test frontend được chạy nguyên trạng, không sửa nguồn/test UI.
Chưa chạy lại bộ browser E2E của thành viên khác.

Gate host trước phê duyệt: **1.159 passed, 2 failed, 1 warning**, 699,82 giây, không skip.
Hai failure duy nhất là assertion danh sách migration đến 015 và exact JWT claim
set không có sid. Lỗi ngữ cảnh assessment thiếu ID thấy trên CI trước đó đã sửa,
test localized bank tương ứng đạt trong gate này. XML/log tại
`_review/dn-full.xml` và `_review/dn-full.log`; đây là bằng chứng lỗi lịch sử.
Sau sửa bảo toàn pool khi clone và xử lý conflict, chạy lại bank DN/statistics DN/
localized bank: **75 passed**. Đây là kết quả trước khi áp dụng cập nhật assertion
được duyệt; giữ log cũ để đối chiếu, không thay bằng một lần chạy được mô tả sai.

Gate backend sau phê duyệt: **1.161 passed, 0 failed, 0 skipped, 1 warning**,
660,29 giây. Lint, build/import và pip check đạt trước toàn bộ test. XML/log mới
ở `_review/dn-full-approved.xml` và `_review/dn-full-approved.log`. Runtime và
test backend không thay đổi sau gate; chỉ hoàn thiện tài liệu/công cụ artifact.

Kiểm tra phát hành phát hiện hash artifact lệch theo LF/CRLF giữa Windows/Linux.
DN bổ sung pin LF cho DDL bằng `.gitattributes`, hash source text chuẩn hóa trong
generator catalog/route và manifest diagram, rồi cập nhật metadata. Kiểm tra
LF/CRLF cho cùng nội dung bằng nhau, nội dung SQL thay đổi vẫn đổi hash, và 18
file SQL khớp byte với Git blob đã commit đều đạt. Không đổi nội dung DDL hoặc
assertion trong `scripts/validate_diagrams.py`; checksum JAR nhị phân vẫn byte exact.

Frontend bổ sung: image Node 24, fixture DB tĩnh đầy đủ, `npm test -- --maxWorkers=2`
chạy **293 passed / 1 failed**, 34/35 suite đạt, 66,61 giây. Lỗi còn lại:
`frontend/src/test/ResultRace.test.jsx:46`, test
`keeps published history when an older refresh returns a pending snapshot`.
Test click refresh hai lần nhưng `HistoryPage.jsx:55` disable nút khi đang refresh,
nên mock response mới không được yêu cầu; không tìm thấy 100%. Chạy riêng file
với một worker vẫn lỗi (2 passed / 1 failed). Test mock hoàn toàn API, và
`git diff ea65df5 -- frontend` rỗng: lỗi nằm trong phần UI/test chưa được DN sửa.
**TN/HN cần review; DN không thay đổi frontend/test này.** Log:
`_review/dn-frontend-with-fixtures.log`, `_review/dn-frontend-result-race.log`.
Lần frontend đầu thiếu fixture trong build image đã được ghi log riêng; sau khi
sửa bố trí fixture trong container kiểm tra, suite AdminManagement đạt. Không
coi toàn bộ frontend hoặc toàn bộ project là xanh khi còn lỗi nêu trên.

## Phê duyệt cập nhật hai assertion trong khu vực testing

DN đã phê duyệt rõ trong phiên làm việc: chỉ cập nhật hai assertion lỗi thời,
hiển thị diff trước khi áp dụng và commit tách khỏi implementation. Diff được
hiển thị đầy đủ trước khi áp dụng; `git apply --check` đạt. Commit riêng:
`ee99a12 — Task 4.2: update outdated migration and JWT sid assertions (approved by DN)`.
Commit chỉ có hai file dưới đây, tổng 4 dòng thêm/1 dòng bỏ; không sửa test khác.

| File/dòng chính xác | Nội dung được duyệt | Kiểm tra được giữ |
| --- | --- | --- |
| [backend/tests/test_final_acceptance.py:213](../../backend/tests/test_final_acceptance.py#L213), phần tử thêm tại dòng 221 và 222 | Thêm migration 016_refresh_sessions.sql và 017_assessment_question_pool.sql vào danh sách mong đợi | Vẫn so khớp chính xác toàn danh sách, rollback khi DB busy và chạy lặp trả [] |
| [backend/tests/test_login_throttle.py:166](../../backend/tests/test_login_throttle.py#L166), kiểm tra sid tại dòng 167 | Thêm sid vào exact claim set; kiểm tra dài 32 ký tự và parse được hex | Giữ typ/access, Learner role, credential epoch và expiry; không bỏ assertion |

Hai test lỗi trước đó đã chạy riêng sau cập nhật: **2 passed**. HN cần review
hai assertion và diff commit `ee99a12` trước khi tích hợp chung. Đây là đề nghị
peer review, không có việc tự gửi tin hoặc thay đổi phần testing khác của HN.

## Giả định, rủi ro và phần còn lại

- Admin = Administrator, skill = concept, topic = subject_area; formal 60 phút,
  10 MCQ/2 SQL/1 essay; practice riêng; SQL chỉ SELECT theo quyết định đã duyệt.
- DN không deploy production, không migrate DB dev lâu dài, không sửa Word hoặc
  mang thay đổi chưa commit của worktree khác vào develop2.
- Socket Docker cho app/worker tin cậy có quyền cao; executor SQL không nhận
  socket/mạng/mount dữ liệu. Cần máy executor chuyên dụng khi vận hành thật.
- Ngân hàng seed lịch sử chưa đủ mọi tổ hợp; import/review benchmark trước bài
  formal. Không tự giảm quota hoặc công bố câu sinh chưa duyệt.
- Chưa kiểm model thật/chi phí/TLS/load 100 người bằng gate mới; không chứng nhận
  chất lượng LLM từ mock. Retry-After chưa hỗ trợ; retry HTTP/job là hai lớp.
- Phân trang bank/progress có phần tổng hợp service; lịch sử lớn cần aggregate
  SQL/materialized views. Rank không chuẩn hóa độ khó hoặc thi lại.
- Lịch sử thiếu snapshot CLO được báo unknown, không lấy mapping mới gán hồi tố.
- Starlette/httpx có deprecation warning trong suite, dependency check vẫn đạt.
- Hai assertion trong khu vực testing được cập nhật với phê duyệt DN tại commit
  riêng `ee99a12`, có giới hạn chính xác như bảng trên; HN cần review chúng.
- Frontend còn một test refresh/history thất bại thuộc phạm vi TN/HN, đã tái hiện
  độc lập và giữ nguyên; browser/load/TLS/live-provider chưa được chứng nhận mới.

## Jira và trạng thái Git hiện tại

Đề xuất `To Do → Done` cho cả 13 task **trong phạm vi DN**: 1.1, 1.3, 1.4, 1.5,
2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.10, 4.1, 4.2. HN review commit assertion riêng;
TN/HN tiếp nhận lỗi frontend còn lại. Không đánh dấu toàn dự án/release Done.

14 commit Task cho 13 task DN gồm 12 commit trước và hai commit 4.2 riêng biệt.
Commit assertion `ee99a12`; commit implementation chứa chính báo cáo này. Lấy log:
`git log --oneline --grep='^Task '`, trạng thái `git status -sb` và so
`git rev-parse HEAD` với `git ls-remote origin refs/heads/develop2` sau push cuối.

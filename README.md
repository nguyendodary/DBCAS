# DBCAS local

## Khởi động từ một clone bình thường

Cần Node.js 24 và Docker Desktop/Engine (Linux containers, Compose v2).
Hướng dẫn áp dụng cho nhánh đang xem và cho `main` sau khi PR tích hợp được duyệt.

```bash
git clone https://github.com/nguyendodary/DBCAS.git
cd DBCAS
npm start
```

Trước khi PR #1 được merge, chọn nhánh PR bằng
`git switch integration/develop2-to-main-20261114` sau khi clone để kiểm tra bản này.
Clone mới không cần `.env` có sẵn; launcher tạo khóa JWT/mật khẩu DB ngẫu nhiên.
Chỉ sửa `.env` tại thư mục repo đang chạy lệnh. Với worktree liên kết, tạo riêng
tệp này từ `.env.example`; launcher không tự tạo môi trường thứ hai cho worktree.
Thay đổi tệp không tự cập nhật môi trường đã nạp trong container đang chạy.

Kiểm tra tên biến và định dạng key mà không in giá trị:

```bash
npm run env:check
```

1. Mở http://localhost:18080 · API http://localhost:18000/docs · Hộp thư http://localhost:18025.
2. Demo `admin@dbcas.local`, `learner@dbcas.local` · mật khẩu chung `Demo12345!`.
3. Kết quả chỉ được công bố sau khi quản trị viên duyệt. Huấn luyện tùy chọn: `npm run ai:train`.

Tài khoản/mật khẩu demo chỉ dành cho development. Staging/production từ chối
các mật khẩu công khai hiện tại và cũ, kể cả trên tài khoản bị vô hiệu hóa;
phải đổi mật khẩu trước khi chuyển DB demo sang môi trường triển khai. Các
khóa cấu hình cũng không được dùng lại giá trị demo. Chạy `npm run secrets:scan`
trước khi chia sẻ thay đổi; hook kiểm tra cả nội dung đang stage.

## Nâng cấp dữ liệu và sao lưu

Migration **019** chuyển mọi assessment `published` sang `closed`, để bắt đầu
luyện tập qua luồng mới. Không xóa hàng, session, bài nộp, điểm hay snapshot;
chạy lại không thay đổi thêm dữ liệu. Assessment `draft`/`closed` giữ nguyên.
Đây là thay đổi khả năng mở đề cũ: thông báo cho nhóm trước khi nâng cấp.

Trước khi áp dụng migration lên DB có dữ liệu, dùng cấu hình kết nối libpq của
DB cần nâng cấp (host/port/user của người vận hành; thay `dbcas` nếu tên khác):

```bash
pg_dump --dbname=dbcas --format=custom --file=dbcas-before-pr1.dump
pg_restore --list dbcas-before-pr1.dump
```

Không đưa mật khẩu vào dòng lệnh hoặc commit bản dump. Người vận hành phải kiểm
tra khả năng khôi phục bản sao lưu. Revert code không khôi phục trạng thái đề;
dùng backup hoặc một migration sửa tiếp đã được duyệt. Không sửa nội dung
migration đã áp dụng. Xem [hướng dẫn nâng cấp](docs/setup-and-migrations.md).

# DBCAS local

Luyện tập cơ sở dữ liệu PostgreSQL với MCQ, SQL SELECT và tự luận. Một máy, một
lệnh khởi động; FastAPI, PostgreSQL 17, React/Vite. Không triển khai cloud.

## Logo và thương hiệu

Tên sản phẩm là **DBCAS**; dòng mô tả là **SKILL ANALYTICS**
(`nav.engineTagFull`). Logo chuẩn duy nhất nằm ở
[`frontend/public/brand/dbcas-mark.svg`](frontend/public/brand/dbcas-mark.svg);
favicon, biểu tượng PWA và manifest trong cùng thư mục được sinh từ file này
bằng `npm --prefix frontend run brand:icons`. Khóa logo React dùng chung là
[`frontend/src/components/BrandLogo.jsx`](frontend/src/components/BrandLogo.jsx).
Không thêm file logo SVG thứ hai và không gõ lại chữ DBCAS trong trang/component.

Người học mở **Luyện tập**, chọn khái niệm, độ khó và nguồn **ngân hàng** hoặc
**AI tạo câu hỏi**, rồi **Bắt đầu**. Chọn **1–20 câu**, mặc định 5 câu/30 phút.
Kế hoạch đủ số câu được đóng băng trước câu đầu; nếu ngân hàng thiếu phạm vi
hẹp, hệ thống mở rộng có kiểm soát và thông báo phần mở rộng.
Không có đề dựng sẵn; demo có ngân hàng, CLO/khái niệm, ba người học và bốn bài
lịch sử. `linh@dbcas.local`, `minh@dbcas.local` cũng dùng mật khẩu demo ở trên.

Câu trả lời tự lưu nháp, tiếp tục được sau tải lại. SQL chạy trong sandbox tạm,
chỉ SELECT, không mạng, có giới hạn thời gian/tài nguyên. Kết thúc bài → **Xem
đánh giá**; **Đánh giá tổng thể** tổng hợp các bài đã công bố, hiển thị riêng số
bài còn chờ. Chưa có bài có nút bắt đầu; một bài chưa có xu hướng.

Mọi bài nộp đều qua một quy trình duy nhất: AI chấm và đánh giá sơ bộ, sau đó
quản trị viên mở **Duyệt bài**, kiểm tra đáp án/SQL/AI, có thể sửa bất kỳ điểm nào
với lý do rồi **Duyệt**. Người học thấy trạng thái chờ duyệt, không thấy điểm trước
khi công bố. Kết quả có dấu đã duyệt/đã điều chỉnh; thống kê và xếp hạng chỉ dùng
kết quả đã duyệt. Các bài cũ giữ policy đã snapshot trong lịch sử.

## Đăng nhập Google / GitHub (tùy chọn)

Đăng nhập và Đăng ký luôn có hai nút **Tiếp tục với Google/GitHub**. Chưa cấu
hình thì nút giải thích ngắn và hướng dẫn dùng email; demo vẫn hoạt động.
Các biến thật của dự án là `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`,
`GOOGLE_REDIRECT_URI`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`,
`GITHUB_REDIRECT_URI` (không có tiền tố `VITE_` hay `OAUTH_` cho thông tin ứng dụng).
Chỉ điền trong `.env` đã được git-ignore; không đưa secret vào frontend.

| Chạy local | Google callback | GitHub callback |
| --- | --- | --- |
| `npm start` (mặc định) | `http://localhost:18080/api/v1/auth/oauth/google/callback` | `http://localhost:18080/api/v1/auth/oauth/github/callback` |
| API trực tiếp (cùng hostname) | `http://localhost:18000/api/v1/auth/oauth/google/callback` | `http://localhost:18000/api/v1/auth/oauth/github/callback` |
| Vite | `http://localhost:5173/api/v1/auth/oauth/google/callback` | `http://localhost:5173/api/v1/auth/oauth/github/callback` |

Compose mặc định dùng callback qua cổng web 18080 (hoặc `LOCAL_WEB_PORT`),
`FRONTEND_URL=http://localhost:18080`; API là 18000 (`LOCAL_API_PORT`). Dùng
callback trực tiếp thì điền đúng URI ở trên; giữ cùng `localhost`, không đổi
sang `127.0.0.1` giữa luồng. Bản Vite phải đặt `FRONTEND_URL` và hai URI theo 5173.

1. **Google:** trong Google Cloud chọn/tạo project, cấu hình consent/audience
   và test users nếu ứng dụng đang thử nghiệm; tạo OAuth client loại **Web
   application**, thêm đúng Google callback ở trên vào Authorized redirect URIs.
   Chép Client ID/Secret vào hai biến `GOOGLE_CLIENT_*`.
   [Hướng dẫn chính thức](https://developers.google.com/identity/protocols/oauth2/web-server#creatingcred).
2. **GitHub:** Settings → Developer settings → OAuth Apps → New OAuth App;
   Homepage URL `http://localhost:18080`, Authorization callback URL là GitHub
   callback ở trên. Tạo client secret, điền hai biến `GITHUB_CLIENT_*`.
   [Hướng dẫn chính thức](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app).
3. Chạy lại `npm start`; `/api/v1/auth/oauth/providers` chỉ công khai tên và
   trạng thái, không trả secret. Email đã được provider xác minh sẽ liên kết
   tài khoản hiện có; người mới nhận vai trò Learner. Handoff dùng một lần;
   phiên có refresh token xoay vòng và đăng xuất thu hồi phiên.

## AI tùy chọn

AI #1 chỉ chuyển dữ liệu bài đã kết thúc thành **một prompt**, không chấm điểm;
model local không có/lỗi thì dùng template. Evaluator nhận đúng prompt đã xây.
AI #2 đánh giá JSON, đồng thời là provider cho sinh câu hỏi. Không key hoặc API
lỗi thì dùng quy tắc/mẫu dự phòng, ghi rõ trên kết quả. Không cần key để chạy demo.
Đặt `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` trong `.env` để dùng API tương thích
Chat Completions. Không commit `.env`; giao diện chỉ hiển thị trạng thái cấu hình.

`npm run ai:train -- --smoke` xây dataset, chạy hai bước LoRA CPU trên model cực
nhỏ, export và inference. `npm run ai:train` dùng Qwen2.5-0.5B-Instruct; cần tải
dependencies/model ở lần đầu, training chạy trên máy và có thể tốn nhiều GB RAM.
Model smoke không có chất lượng ngôn ngữ hữu ích. Xem [pipeline, dữ liệu và giới
hạn](docs/ai-pipeline.md) trước khi dùng model để xây prompt.

## Dừng và kiểm thử

`npm run stop` dừng stack. `npm run reset` **xóa volume của project local** rồi
tạo lại demo; startup bình thường giữ dữ liệu đã sửa. Bản migration mới đóng đề
dựng sẵn của bản cũ, giữ FK và snapshot lịch sử.

```powershell
py -3.13 -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
backend/.venv/Scripts/python.exe backend/manage.py lint
backend/.venv/Scripts/python.exe backend/manage.py build
backend/.venv/Scripts/python.exe backend/manage.py test
npm --prefix frontend ci
npm --prefix frontend test -- --maxWorkers=2
npm --prefix frontend run build
npm --prefix frontend audit
npm run ui:contrast
npm run test:local
npm --prefix frontend exec playwright install chromium
npm --prefix frontend run test:practice -- --repeat-each=3
```

Linux/macOS dùng `.venv/bin/python`. Chạy tuần tự các gate dùng Docker
(backend → browser) để sandbox không tranh tài nguyên. Browser practice dùng
stack local đang chạy, tạo tài khoản kiểm thử riêng và khôi phục trạng thái demo sau
mỗi lượt; không xóa DB demo. Ảnh/JSON nằm trong `_review/practice-browser*`.

`npm run test:qa` kiểm tra bằng provider HTTP giả local có delay/errors; không
gọi dịch vụ trả phí. `npm --prefix frontend run test:e2e` là suite trên DB/sandbox
dùng một lần có kiểm tra ownership. Kết quả đo, lỗi và phần chưa xác minh nằm
trong [trạng thái cuối](docs/final-status.md); báo cáo ngày cũ chỉ là lịch sử.

Bằng chứng vòng cuối: [báo cáo W1–W8](docs/qa/final-20261110/README.md),
[102 ảnh sáng/tối](docs/qa/final-ui/screenshots.md),
[kiểm chứng Word](docs/qa/final-20261110/word-audit.md) và
[kịch bản demo](docs/demo/demo-script.md).

Kiểm toán OAuth/20261112: [nguyên nhân và regression](docs/qa/root-cause-audit-20261112.md),
[ảnh trước/sau](docs/qa/oauth-20261112/screenshots/README.md),
[kiểm kê thư mục](docs/qa/workspace-inventory-20261112.md) và
[ba Word v1.2](docs/academic/README.md). Key mới bị gateway trả 403 trong
3 request có sổ riêng; model/chất lượng live chưa xác minh, fallback vẫn hoạt động.

Kiểm toán cuối 20261113: [W1 learner](docs/qa/final-20261113/w1-learner.md)
**30/30**, [W3 backend/AI](docs/qa/final-20261113/w3-backend-ai.md) ma trận
**2.291.100/0**, ngân hàng **5.482/0 invalid**;
[logo/thương hiệu](docs/qa/logo-20261113/inventory.md) 22 ảnh / 0 lỗi;
[W5 dọn dẹp](docs/qa/final-20261113/w5-cleanup-inventory.md) 84 đường dẫn đã
quarantine; [W6 tài liệu](docs/qa/final-20261113/w6-documents.md) Word **3/3**,
**0** sửa nội dung/diagram; [W2 admin](docs/qa/final-20261113/w2-admin.md)
**33/33**, 37 ảnh. Xem [kiểm toán tổng](docs/qa/final-audit-20261113.md) và
[trạng thái](docs/final-status.md).

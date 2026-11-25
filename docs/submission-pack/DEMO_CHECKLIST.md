# DBCAS — Checklist demo bảo vệ

Mục tiêu: trình diễn bản chốt kiến trúc (Architecture Freeze v1.2) và bộ tài liệu
**ver1.3** trong 5 phút, có phương án dự phòng khi mạng/API/Docker lỗi. Chỉ dùng dữ
liệu tổng hợp; **production HOLD**.

## A. Checklist máy bảo vệ (làm trước T-60 phút)

### Phần cứng và hệ điều hành

- [ ] Laptop đã cắm sạc; tắt sleep, notification và Windows Update.
- [ ] Có adapter HDMI/USB-C và một laptop dự phòng đã clone sẵn repo.
- [ ] Màn hình phụ hoặc projector đã test độ phân giải; trình duyệt đặt zoom 110%.

### Docker và WSL2

- [ ] Docker Desktop đang chạy **Linux containers**.
- [ ] `docker version --format '{{.Server.Version}}'` trả về phiên bản.
- [ ] `wsl -e docker info --format '{{.ServerVersion}}'` trả về phiên bản (cần cho SQL DML).
- [ ] `wsl -l -v` thấy `Ubuntu-24.04` ở trạng thái `Running` (hoặc bật khi cần).
- [ ] Nếu `npm start` báo `Không đọc được group Docker socket`: lấy GID bằng
      `wsl -e docker run --rm --network none --entrypoint stat -v /var/run/docker.sock:/var/run/docker.sock postgres:17 -c "%g" /var/run/docker.sock`
      rồi thêm `LOCAL_DOCKER_GID=<gid>` vào `.env`.

### Bộ tài liệu nộp

- [ ] Mở sẵn `docs/submission/final/` (5 DOCX + PDF trong `rendered/`).
- [ ] Đã đọc `docs/submission/final/verification/verification-report.md`
      (149 assertion, 0 lỗi) và `TRACEABILITY.md`.
- [ ] Biết bộ số liệu hiện tại để trả lời: 67 bảng / 561 cột / 122 khóa ngoại /
      159 index / 28 migration; 106 API path / 118 operation; 1940 backend test;
      463 frontend test; quét secret toàn cây, 0 finding.
- [ ] Nếu bị hỏi về SRS: nói rõ SRS không thuộc phạm vi tài liệu của owner và bản
      lưu nằm ở `Documents/Archive/`.

### Mã nguồn và cấu hình

- [ ] `git status --short` sạch; `git log -1 --oneline` khớp commit bàn giao trong
      `docs/agent/freeze-logs/handover-gates.md`.
- [ ] `npm run docs:verify-word` PASS (5 tài liệu, 0 lỗi) trước khi demo.
- [ ] `.env` tồn tại trên máy demo, có `LLM_API_KEY` thật; **không** mở `.env` trước khán giả.
- [ ] `npm run env:check` PASS (chỉ in tên biến và dạng che).
- [ ] `npm run llm:check` PASS; nếu FAIL, ghi nhận và chuyển sang phương án ngân hàng.
- [ ] Cổng 18000, 18080, 18025, 11025 đang trống:
      `Get-NetTCPConnection -State Listen -LocalPort 18000,18080,18025,11025 -ErrorAction SilentlyContinue`
- [ ] `npm start` kết thúc bằng `DBCAS: http://localhost:18080`.
- [ ] `Invoke-RestMethod http://localhost:18080/readiness | ConvertTo-Json` trả
      `database: true` và `sandbox: true`.

### Tài khoản và dữ liệu

- [ ] Đăng nhập được `admin@dbcas.local` / `Demo12345!`.
- [ ] Đăng nhập được `learner@dbcas.local` / `Demo12345!`; thêm `linh@dbcas.local`,
      `minh@dbcas.local` cùng mật khẩu.
- [ ] Mailpit mở được tại `http://localhost:18025`.
- [ ] Đã chạy thử một phiên Mode 2 và một lần duyệt/từ chối ứng viên.
- [ ] Có sẵn ảnh chụp hoặc video ngắn của: dashboard, câu hỏi gắn nhãn **AI**,
      trang kết quả, hàng đợi admin, Mailpit, màn hình SQL.
- [ ] Mật khẩu demo chỉ dùng local; không dùng lại cho staging/production.

### Trước khi khán giả vào

- [ ] Đóng terminal, tab `.env`, email cá nhân và mọi cửa sổ có khóa.
- [ ] Mở sẵn 3 tab: `http://localhost:18080`, `http://localhost:18025`,
      `http://localhost:18000/docs`.
- [ ] Đăng nhập sẵn admin ở cửa sổ chính; learner ở cửa sổ ẩn danh thứ hai.
- [ ] Tắt thông báo trình duyệt và chat.

## B. Kịch bản 5 phút

| Thời gian | Việc làm | Điểm nhấn |
|---|---|---|
| 0:00–0:35 | Đăng nhập admin, mở dashboard/cohort | Nêu dữ liệu tổng hợp, kiến trúc một máy, production HOLD. |
| 0:35–0:55 | Sang cửa sổ learner, mở Free/Pro demo, chọn Pro | Free mở chế độ 1; Pro mở chế độ 2; chỉ là mô phỏng UI. |
| 0:55–2:10 | Bắt đầu Mode 2, chọn concept, trả lời 3–4 câu (1 MCQ + 1 SQL) | Câu AI có nhãn **AI**; độ khó đổi theo đúng/sai; SQL chạy trong sandbox. |
| 2:10–2:45 | Kết thúc phiên, mở trang kết quả | Điểm/ability và trạng thái provisional; bài practice chờ admin duyệt. |
| 2:45–3:30 | Về admin, mở hàng đợi ứng viên, validate rồi duyệt hoặc từ chối | Truy vết `ai_generated` → candidate → câu hỏi đã duyệt. |
| 3:30–4:00 | Mở Mailpit, kích hoạt quên mật khẩu cho learner | Mail đi qua Mailpit local; không gửi ra ngoài. |
| 4:00–4:30 | Chuyển VI/EN trên một trang | Không lẫn ngôn ngữ; định danh kỹ thuật giữ nguyên. |
| 4:30–5:00 | Mở SQL sandbox: SELECT thành công, DML bị chặn ở profile mặc định | Nêu profile `writable` rollback và giới hạn WSL2 nếu có. |

**Câu nói kết thúc gợi ý:** “Đây là bản demo đã chốt kiến trúc, không phải bản
production. AI có thể fallback về ngân hàng câu hỏi, DML luôn rollback, và các
giới hạn đã ghi trong `docs/submission-pack/SUMMARY.md`.”

## C. Phương án dự phòng mạng/API

### LLM chậm, lỗi hoặc mất mạng

- Ứng dụng tự fallback sang ngân hàng câu hỏi đã duyệt; bài làm vẫn tiếp tục.
- Nếu cần chứng minh fallback: xóa tạm `LLM_API_KEY`, khởi động lại API, mở một
  phiên mới; câu hỏi sẽ là `bank` và không có nhãn AI. Khôi phục `.env` ngay sau đó.
- Nếu provider chậm: nêu thời gian sinh thực tế 2–9 giây và cơ chế prefetch; không
  bấm refresh liên tục.
- Nếu mất internet: stack local, PostgreSQL, Mailpit và ngân hàng câu hỏi vẫn chạy;
  chỉ phần gọi LLM bên ngoài bị ảnh hưởng.

### Docker/WSL2 hoặc sandbox lỗi

- `/readiness` báo `sandbox: false`: kiểm tra `LOCAL_DOCKER_GID`, chạy lại `npm start`;
  nếu vẫn lỗi, **không demo SQL trực tiếp**, dùng ảnh/video đã chuẩn bị.
- Docker Desktop treo: thoát và mở lại Docker, chạy `npm start` (volume đã seed được
  giữ nguyên, không mất dữ liệu); chỉ dùng `npm run reset` khi còn thời gian.
- Cổng bị chiếm: đổi `LOCAL_API_PORT`, `LOCAL_WEB_PORT`, `LOCAL_MAIL_PORT`,
  `LOCAL_SMTP_PORT` trong `.env`, chạy lại `npm start`, mở URL mới.
- API trả 5xx: xem `docker compose --project-name dbcas-local -f docker-compose.local.yml logs app`;
  khởi động lại service `app`; nếu không hồi phục, chuyển sang video.

### Sự cố máy chiếu/máy tính

- Máy dự phòng: đã clone đúng commit, build sẵn image, `npm start` trước giờ demo.
- Nếu không kịp khởi động: dùng bộ ảnh/video và mở `docs/submission-pack/SUMMARY.md`,
  `docs/submission-pack/SOURCE_CODE.md` cùng `docs/agent/freeze-logs/final-gates.md`
  để trả lời bằng số liệu thật.
- Không bao giờ mở `.env`, log có khóa, hay commit chứa bí mật để “chứng minh”.

## D. Sau demo

- [ ] `npm run stop` (hoặc để stack chạy nếu buổi bảo vệ còn tiếp).
- [ ] Thu thập log lỗi (nếu có) và ghi vào biên bản; không sửa số liệu đã công bố.
- [ ] Không commit `.env`, file dump, ảnh có khóa hoặc dữ liệu thật.
- [ ] Nếu phát hiện lỗi mới: ghi vào `docs/agent/BACKLOG.md`, không sửa code tại chỗ
      trong lúc bảo vệ.
- [ ] Không sửa DOCX tại chỗ sau khi công bố số trang; mọi thay đổi phải chạy lại
      `npm run docs:build`, `npm run docs:finalize`, `npm run docs:verify-word`.

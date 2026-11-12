# Midterm delivery status — 2026-11-09

Mốc: owner đã trả lời **“diagrams approved”** cho cả 10 hình tại `a74568f`.
Đợt chèn Word + demo + tài liệu midterm nằm ở `590751a` trên `develop2`.

## 1. Word v1.2 — đã chèn hình

| Tài liệu | Hình | Trang PDF (số footer) |
| --- | --- | --- |
| Proposal | System Context, Logical, Pipeline | 46 (37), 50 (41), 52 (43) |
| Architecture | Use Case, Context, Container, Component (1/2)-(2/2), Module, Allocation, ERD, TRD (1/5)-(5/5) | 14 (5), 15 (6), 45 (36), 48-49 (39-40), 53 (44), 56 (47), 59 (50), 60-64 (51-55) |
| Database | ERD, TRD (1/5)-(5/5) | 12 (5), 14-18 (7-11) |

- TOC, danh sách hình và danh sách bảng đã cập nhật bằng Word COM; danh sách
  hình hiển thị đúng `Figure 4 (1/2)/(2/2)` và `Figure 8 (1/5)…(5/5)`.
- Cả ba file mở/update trong Word **không lỗi repair**.
- `docs:verify-word`: **PASS 3/3**; `docs:check`: **PASS** (46/46 + 41/41).
- Bản backup trước khi sửa: `_review/word-backup-20261109/`.
- TRD là hình nhỏ nhất khi in A4 (tên bảng ~6,3 pt, dòng ~4,7 pt); đọc tốt
  trên màn hình/A3, nên phóng to khi trình bày.

## 2. Demo stack — đang chạy

| Mục | Giá trị |
| --- | --- |
| Ứng dụng | http://localhost:18080 |
| API/Swagger | http://localhost:18000/docs |
| Mailpit | http://localhost:18025 |
| Tài khoản | `learner@`, `admin@`, `linh@`, `minh@dbcas.local` / `Demo12345!` |
| Health | app/db/frontend/mailpit healthy; readiness 200 |
| Trạng thái demo | learner có **3 bài đã công bố**; **bài #6 đang chờ Admin duyệt**; không có lựa chọn luồng — mọi bài mới đều chờ duyệt |

Đã kiểm tra bằng trình duyệt: setup (khái niệm/độ khó/nguồn Bank/5 câu) → làm
MCQ + SQL + tự luận → nộp → đánh giá fallback 67,67%; dashboard; Admin
dashboard; Duyệt bài; mở chi tiết bài #6.

Kịch bản 5 phút: `docs/demo/demo-script.md`. Hỏi đáp midterm:
`docs/demo/midterm-qa.md`.

## 3. Gate codebase

Commit logic correction: `2479254` (mandatory review, no result-flow toggle).

Các gate không phá stack demo đã chạy:

- Backend lint, build, `pip check`, OpenAPI check: **PASS**.
- Frontend lint, Prettier, build, audit high: **PASS** (0 high/critical;
  root audit 2 low từ mermaid-cli).
- Frontend unit: **347/347 PASS** (39 file, 131,45 giây).
- Bank validation: **5.482 câu, 0 invalid** (2.006 MCQ / 1.747 SQL / 1.729 essay).
- `npm run test:local`: **7/7 PASS**.
- `npm run inventory:check`: **PASS** (API/frontend routes khớp).
- `npm run docs:check` + `docs:verify-word`: **PASS**.

Frontend unit đã chạy đầy đủ: **347/347**. Backend full pytest **không hoàn
tất** trong môi trường midterm: chỉ đạt 10% sau 14 phút (ước tính nhiều giờ)
khi stack demo cùng dùng Docker, nên đã dừng và dọn container test; không
thay đổi app code. Lượt full gần nhất là **1429/1429 tại `700f19a`**
(1772,96 giây, `docs/deliverables/4.11`). Không chạy browser suite đầy đủ
trong lúc demo đang phục vụ midterm; lần ghi nhận gần nhất là **55/55**.

## 4. Còn lại — chỉ con người làm được

- `5.12` biên bản họp: ngày họp thật, người tham dự, chữ ký.
- `5.16` reflection: tên người viết và nội dung cá nhân.
- Chữ ký/approver trong các tài liệu học thuật.
- Chất lượng LLM thật (mới có targeted live nhỏ), load test > 8×20, production.

Không tạo ngày/số liệu/chữ ký giả.

## 5. Gate log

- Backend lint: PASS
- Backend build: PASS
- Backend pip check: PASS
- OpenAPI check: PASS
- Frontend lint/format/build/audit: PASS
- Frontend unit: 347/347 PASS
- Bank validation: 5482 questions, 0 invalid
- `test:local`: 7/7 PASS
- `inventory:check`: PASS
- `docs:verify-word`: 3/3 PASS
- `docs:check`: PASS
- Backend full pytest: xem `C:\tmp\backend-test.log`

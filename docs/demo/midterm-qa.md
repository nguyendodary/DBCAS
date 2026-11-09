# Midterm QA — câu hỏi thường gặp và số liệu thật

> Nguồn: `docs/final-status.md`, `docs/deliverables/4.11-progress-report.md`,
> `docs/qa/erd-evidence.md`, `docs/qa/rebuild-preview/`, `docs/qa/schema-introspection.json`.
> Chỉ dùng số có trong repo; không tạo số mới.

## Hỏi nhanh — đáp ngắn

| Câu hỏi | Trả lời có căn cứ |
| --- | --- |
| Vì sao ERD còn 4 bảng legacy? | `assessment`, `assessment_concept`, `assessment_question`, `assessment_blueprint` vẫn nằm trong schema để giữ **dữ liệu lịch sử** và các báo cáo/bài cũ tham chiếu; phiên practice mới có `assessment_id = NULL` (kiểm tra 6/6 phiên demo). Chúng được vẽ nét đứt + nhãn **LEGACY**, không dùng để tạo đề mới. |
| Vì sao dùng practice thay vì đề dựng sẵn? | Theo quyết định của owner: bỏ đề dựng sẵn (migration 019 archive), người học chọn khái niệm → độ khó → số câu 1–20 (mặc định 5) → nguồn Bank/AI; plan được đóng băng trước câu 1, mỗi bài có snapshot riêng. Seed demo có **0 đề dựng sẵn**. |
| SQL có lấy từ AI không? | **Không.** Với `source=ai`, SQL là **bank-only** (`practice_generation.py:113`); AI chỉ sinh MCQ/essay. Mọi câu SQL chạy trên dataset cố định và được kiểm tra cả dataset chính lẫn biên trước khi lưu; sandbox chỉ cho SELECT. |
| Pipeline hai AI là gì? | **AI #1 Prompt Builder** tạo prompt tiếng Việt (bối cảnh, rubric, JSON schema); **AI #2 Evaluator** trả nhận xét/điểm tự luận. MCQ/SQL do hệ thống chấm, model không sửa điểm. Thiếu key/timeout/JSON sai → **template + chấm dự phòng theo quy tắc**, UI ghi rõ. |
| Vì sao đôi khi thấy "Đánh giá dự phòng"? | Không có `LLM_API_KEY` hoặc provider lỗi/timeout; hệ thống không chặn bài mà dùng quy tắc và ghi rõ trong kết quả. Đây là đường fallback đã thiết kế, không phải lỗi. |
| CSDL hiện có bao nhiêu? | **41 bảng, 293 cột, 59 khóa ngoại, 19 migration** (schema-introspection + `docs:check`). ERD: **21 thực thể, 28 diamond, 21 khóa** (17 gốc + SystemSetting + 3 legacy). TRD: **5 trang**, 29 connector cùng trang + 30 cặp stub xuyên trang, phủ **59/59 FK**. |
| Kiểm thử đến đâu? | Backend **1429/1429** ở lượt đầy đủ gần nhất `700f19a` (bộ hiện tại khoảng 1430 ca; không chạy lại full trong lúc demo chạy), frontend **347/347**, browser **55/55**, 0 fail/skip/flaky trong lượt ghi nhận. |
| Chịu tải được không? | Có kiểm soát **8 học viên × 20 câu**: 259 HTTP request, 42,186 giây, 8 bài published, SQL peak 4, provider peak 2; chưa test vượt mức này. |
| Đã chạy cloud/production chưa? | **Chưa.** Toàn bộ là local Docker Compose (PostgreSQL 17, FastAPI, Nginx, Mailpit); chưa có nghiệm thu production/cloud. |

## Giới hạn đã biết (nói thật)

1. **Tải**: mới có controlled load 8 học viên × 20 câu; chưa có load test lớn hơn
   hoặc nhiều máy.
2. **Chất lượng LLM thật**: phần lớn gate dùng fake HTTP/fallback; mới có các
   lượt targeted live nhỏ (2/2 và 1/1). Chất lượng tiếng Việt/điểm tự luận của
   model thật **chưa được xác nhận đầy đủ**; train smoke chỉ chứng minh dây
   chuyền, không chứng minh chất lượng.
3. **Môi trường**: chỉ local một máy; chưa có HA, backup/restore production,
   hay đo chi phí cloud.

## Tiến độ so với kế hoạch

| Hạng mục | Kế hoạch | Hiện tại |
| --- | --- | --- |
| 1.1 Proposal, 1.2 kế hoạch, 1.9 test plan, 1.10 backlog | Có | **Xong** |
| 2.11 tiến trình Sprint 2 | Có | **Xong** |
| 3.10–3.18 Docker, pipeline AI, kiểm thử, kiến trúc, CSDL, UI, test case | Có | **Xong** |
| 4.11–4.15 báo cáo tiến trình, cập nhật kiến trúc/CSDL/US-UI, tài liệu AI | Có | **Xong** |
| 5.9–5.15 bộ tài liệu cuối, báo cáo cuối, slide, kiến trúc/CSDL đầy đủ | Có | **Xong** |
| 5.12 biên bản họp, 5.16 reflection | Có | **Còn trống** — cần người thật điền/chữ ký |
| Diagram v1.2 + 3 file Word | Trong đợt review | **Xong** — 10 hình đã duyệt, chèn Word, cập nhật mục lục |
| Chất lượng LLM thật, load > 8×20, production | Ngoài phạm vi midterm | **Còn lại** |

## Talk track 3 ý (30 giây)

- **Đã làm**: hệ thống chạy thật end-to-end — người học tự tạo bài từ ngân hàng
  validated, làm MCQ/SQL/essay, nhận đánh giá theo CLO/chủ đề; Admin duyệt bài,
  xem dashboard nhóm, cấu hình luồng công bố; CSDL 41 bảng/59 FK khớp tài liệu.
- **Khó khăn**: giữ đúng bằng chứng khi AI không ổn định (timeout/không key) —
  giải bằng template + fallback theo quy tắc; dung lượng câu hỏi lớn (5.482 câu)
  và nhiều luồng duyệt — giải bằng snapshot/plan đóng băng và audit.
- **Tiếp theo**: xác nhận chất lượng với LLM thật, mở rộng load test, hoàn thiện
  biên bản/reflection và chuẩn bị nghiệm thu cuối.

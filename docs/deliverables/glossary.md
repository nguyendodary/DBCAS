# Thuật ngữ dùng chung (bản rút gọn)

Các tài liệu trong thư mục này dùng chung bộ thuật ngữ sau để tránh lặp và để
các tên gọi khớp mã nguồn.

| Thuật ngữ | Ý nghĩa trong DBCAS |
| --- | --- |
| Concept | Một khái niệm mô hình dữ liệu (SELECT, JOIN, NORMALIZATION, ER modeling, TRANSACTION…). Liên kết CLO qua bảng `clo_concept`. |
| Difficulty band | Ba nhóm độ khó theo mức điểm DBAS: `EASY` (1–2), `MEDIUM` (3), `HARD` (4–5). |
| Question type | Ba loại câu: `mcq` (trắc nghiệm 4 đáp án/1 đúng), `sql` (câu SQL), `essay` (tự luận). |
| Question source | `bank` = chọn từ ngân hàng đã kiểm chứng; `ai` = hỏi AI và dùng ngân hàng cho phần SQL. |
| Validated bank | Ngân hàng câu hỏi đã qua bộ kiểm tra nội dung + SQL, hiện 5482 câu (2006 MCQ / 1747 SQL / 1729 essay). |
| Exact-count guarantee | Đối chiếu subset độ khó/khái niệm rồi mở rộng; luôn trả đúng `question_count` (1–20, mặc định 5). |
| Result release | Sau nộp bài, AI chấm/đánh giá sơ bộ rồi quản trị viên duyệt; chỉ kết quả đã duyệt mới được công bố. Bài cũ giữ policy đã snapshot. |
| Two-AI pipeline | Prompt Builder tạo prompt — có thể chạy mô hình học tăng cường; Evaluator chấm bằng AI; khi không cấu hình builder, Prompt Builder dùng template fallback nhưng vẫn đi qua pipeline. |
| Prompt Builder | Bước tạo prompt đánh giá (schema `Evaluation`), chỉ định dạng dữ liệu bài làm, không chấm/không viết nhận xét; lưu `prompt_hash` của đúng prompt gửi Evaluator. |
| Evaluator | Thành phần chấm (`services/evaluation_pipeline.py`) chạy qua provider AI; trả JSON giải thích chi tiết. |
| Reason code | Mã từ chối AI không có bí mật: `json_parse`, `schema`, `truncated`, `refusal`, `mcq_options`, `sql_syntax`, `sql_fixture`, `sql_empty_output`, `out_of_scope_concept`, `difficulty_mismatch`, `duplicate`, `count`, `type_source`, `type_fields`, `timeout`. |
| Admin (5 mục) | Tổng quan, Duyệt bài, Tài khoản, Ngân hàng & khái niệm/CLO, Hệ thống. Không quản lý đề thi cố định. |
| Learner-defined practice | Người học tự chọn khái niệm, độ khó, số câu, nguồn `bank`/`ai`. Không có đề trước. |

Vai trò hệ thống: Learner (người học), Admin (giảng viên/QA). Không có role
giáo viên trung gian. Vai trò "AI worker" chỉ dùng nội bộ.

# Task 4.1 — Thuật toán đánh giá năng lực

Trạng thái đầu: **Đã có một phần**: năng lực concept, cumulative và gap theo target
đã có. Review: công thức point-weighted/Decimal và publication boundary đạt;
thiếu nhóm CLO/difficulty và rank; topic mới là category display. Test/bảo mật
đạt cho phần cũ, tài liệu chưa có đầy đủ công thức mới.

Kế hoạch/thực hiện: `competency_dimensions.py` với Evidence đã kiểm định,
extract/filter publication/formal, de-duplicate, tổng/CLO/topic/difficulty, dense
rank nhóm và competition rank Learner; thêm capture CLO confirmed vào snapshot
qua repository. Không backfill mapping hiện tại vào lịch sử thiếu thông tin.
Thêm test DN và `docs/competency-dn.md` nêu công thức/ví dụ/giới hạn.
Phụ thuộc snapshot/schema/verified grades ở các task trước; không gọi LLM.

Kiểm tra: lint/build/OpenAPI/diff check đạt; **112 passed** dimensions DN,
competency/gaps, original locale và draft lifecycle. Số mẫu 8/10+1/2=75%, loại
double count, no evidence=null, tie 1/1/3, rounding, nonfinite/conflict evidence,
pending/practice/unpublished, mapping confirmed/immutable đều được kiểm tra.

Chạy: `python backend/manage.py test tests/dn/test_competency_dimensions.py tests/test_competency.py tests/test_competency_gaps.py tests/test_question_original_locale.py tests/test_draft_lifecycle.py`.
Giả định: nhóm nhiều CLO/topic nhận toàn điểm, tổng chung đếm một lần; lịch sử
thiếu mapping báo unknown, không tự suy diễn. Ranking không là chuẩn hóa độ khó
hay đo tâm trắc. Không còn thiếu hụt Task 4.1.
Commit: `Task 4.1: compute competency dimensions and preserve CLO evidence`.

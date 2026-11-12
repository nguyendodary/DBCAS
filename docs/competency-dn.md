# Công thức đánh giá năng lực

Năng lực concept/kỹ năng hiện có giữ nguyên: tổng điểm đạt / tổng điểm có thể ×100,
Decimal, làm tròn HALF_UP hai chữ số. Câu nhiều tag đóng góp toàn phần vào từng
concept đã xác nhận; không có trọng số tag tự đặt. Gap concept = max(0, target_pct
− competency_pct), xếp giảm dần khoảng thiếu, concept_id phá hòa.

Task DN bổ sung `competency_dimensions.py`: CLO, topic (`subject_area` snapshot),
độ khó của câu (1–5), điểm tổng và xếp hạng. Đầu vào duy nhất là attempt đã nộp,
có score/graded, thuộc phiên formal đã hoàn tất và được công bố. Practice/ADAPTIVE,
pending/failed/chưa công bố không vào thống kê chính thức. Không gọi LLM để tính số.

Với dimension d: `pct(d) = 100 × Σ earned(a) / Σ possible(a)` cho các attempt a
thuộc d. Mỗi attempt tính một lần cho cùng topic/CLO/difficulty, kể cả nhiều
concept cùng topic hoặc nhiều mapping cùng CLO. Một câu thuộc nhiều CLO/topic
có thể đóng góp toàn phần vào mỗi nhóm; tổng chung luôn đếm câu một lần, không
cộng các nhóm với nhau. Không lấy trung bình các phần trăm phiên.

Ví dụ: câu SQL 8/10 ở khó 1 và câu Index 1/2 ở khó 3 → tổng 9/12 = 75%; SQL/CLO1
80%, Index/CLO2 50%, không phải trung bình (80+50)/2. Không có bằng chứng → pct
null và nhóm rỗng, không chuyển thành thất bại 0. Điểm không hữu hạn/ngoài phạm vi
bị từ chối, evidence trùng ID giống nhau được loại, trùng khác nội dung bị báo lỗi.

Nhóm năng lực xếp giảm dần pct đã làm tròn, dense rank (1,1,2), khóa nhóm phá hòa.
Xếp Learner dùng competition rank (1,1,3), learner_id phá hòa, chỉ learner có bằng
chứng. Phép so cùng ngân hàng/độ khó vẫn cần người đọc cân nhắc; không khẳng định
rank này là chuẩn hóa tâm trắc hoặc loại trừ ảnh hưởng thi lại.

Mapping CLO active/confirmed của tag confirmed được lưu vào `question_snapshot`
ở lúc phục vụ mới. Lịch sử thiếu trường `clo_mappings` không bị gán theo mapping
hiện tại: tăng `clo_mapping_unknown_attempts`, vẫn tính tổng/topic/difficulty nhưng
không tạo điểm CLO giả. Snapshot có mảng rỗng nghĩa là đã biết không có mapping.
Đổi CLO/tag/topic/độ khó trong bank không thay dữ liệu snapshot cũ. Label CLO tổng
hợp dùng tên của bằng chứng mới nhất theo attempt_id; bằng chứng cũ giữ tên riêng.

Kiểm tra: `python backend/manage.py test tests/dn/test_competency_dimensions.py tests/test_competency.py tests/test_competency_gaps.py tests/test_question_original_locale.py tests/test_draft_lifecycle.py`.

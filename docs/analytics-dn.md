# API thống kê và khoảng thiếu kỹ năng

Learner: `GET /api/v1/sessions/statistics`. Admin:
`GET /api/v1/admin/analytics/statistics`. DTO ở `schemas_analytics.py`, đầy đủ
schema/error/Bearer/role trong [OpenAPI](openapi.json). Không đổi endpoint cũ của UI.

Query chung: `assessment_id` tùy chọn (>0), `limit` 1–500 mặc định 100 và `offset`
>=0 để phân trang **progress**. Aggregate/distribution/ranking tính toàn bộ tập
đã lọc trước khi phân trang, không chỉ trang hiện tại. Admin có thêm `learner_id`;
Learner luôn lấy identity từ token, không nhận tùy chọn xem người khác.
Assessment/Learner không có trả 404; lỗi role 403, chưa xác thực 401, input sai 422.

Response gồm:

| Trường | Ý nghĩa |
| --- | --- |
| dimensions.overall | Điểm tổng weighted và số attempt làm bằng chứng |
| dimensions.clos/topics/difficulties | Điểm theo từng nhóm và rank nhóm; công thức Task 4.1 |
| dimensions.clo_mapping_unknown_attempts | Lịch sử thiếu snapshot mapping CLO, không được suy diễn |
| published_formal_sessions/graded_sessions | Số phiên formal công bố / số có bằng chứng đã chấm |
| progress/progress_total/limit/offset | Điểm từng phiên theo thời gian hoàn tất, trang và tổng |
| score_distribution | Năm bin [0,20), [20,40), [40,60), [60,80), [80,100], đếm phiên có điểm |
| recommendations | Chủ đề cần ôn cho một Learner, concept_ids và khoảng thiếu lớn nhất |
| ranking | Competition rank Learner trong tập lọc, chỉ có ở API Admin |

Điểm Decimal serialize chuỗi JSON; pct không có bằng chứng là null. Không trả
essay/SQL answer, expected result, reference, email hoặc token. Learner không
nhìn thấy bảng xếp hạng hoặc phiên người khác. Endpoint mới chỉ đọc, không gọi AI
và không tự xuất bản kết quả. Practice/ADAPTIVE/pending/chưa công bố bị loại.

Khoảng thiếu reuse phép pool point-weighted `aggregate_sessions` và target snapshot
đã chốt: target weighted theo possible của các phiên có target, shortfall = target
− competency nếu dương. Gom concept gap theo subject_area, thứ tự topic giảm theo
shortfall lớn nhất; concept trong topic giảm theo gap rồi concept_id. Đây là gợi
ý ôn theo chủ đề; thứ tự guidance concept và prerequisite readiness hiện hữu vẫn
ở `/sessions/{id}/gaps` và `/guidance`. Không tự đặt target cho CLO/độ khó.

Admin cohort không có một Learner cụ thể thì recommendations rỗng; xem
`/admin/analytics/cohort` để thấy gap prevalence/weakest concepts. Cohort endpoint
cũ dùng **phiên mới nhất mỗi Learner/concept**, endpoint statistics mới pool toàn
bộ phiên formal công bố (bao gồm thi lại), nên hai phép mô tả có thể khác nhau.
Khi lọc learner_id, recommendations dùng chính tập assessment đã lọc.

Giới hạn: progress response có phân trang, tổng hợp vẫn đọc evidence toàn tập;
cần aggregate/materialized query khi lịch sử rất lớn. Rank không chuẩn hóa độ
khó/selection và không chứng nhận mức thành thạo ngoài phạm vi bank. Lịch sử cũ
không có snapshot vẫn dùng fallback evidence của hệ thống hiện có, CLO báo unknown.

Chạy: `python backend/manage.py test tests/dn/test_statistics_api.py tests/test_admin_analytics.py tests/test_competency_gaps.py tests/test_guidance.py tests/test_result_contracts.py`.

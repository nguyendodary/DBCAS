# API thống kê và khoảng thiếu kỹ năng

Tích hợp local 02/11: trang Năng lực hiển thị điểm tích lũy, hạng riêng và chi
tiết CLO/chủ đề/độ khó, tiến độ/phân bố từ API thật. Dashboard Admin dùng cùng
bộ lọc đề và xuất CSV tổng hợp, gồm số liệu toàn bộ tập đã lọc (không chỉ trang
progress đang xem). CSV có BOM UTF-8, escape dấu nháy và công thức spreadsheet.

Learner có thêm `GET /api/v1/sessions/ranking?assessment_id=...`:
`{"rank":2,"participants":3,"competency_pct":"75.00"}`. Chỉ hạng của tài khoản
đang đăng nhập; không chấp nhận danh tính từ query, không trả roster hoặc điểm
người khác. Chưa có bằng chứng thì rank/điểm là null. Cùng điểm đồng hạng kiểu
1,1,3. Auth 401, sai role 403, đề không tồn tại 404, query không hợp lệ 422.

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

## Cách đọc theo số bài

`pending_formal_sessions` chỉ đếm bài formal đã nộp nhưng chưa công bố, theo đúng
phạm vi Learner/đề lọc; không cộng vào điểm hoặc số bài đã chấm. UI tự kiểm tra
trong thời gian chờ, đồng thời nạp lại thống kê và hồ sơ kỹ năng khi làm mới.
Không có bài: một nút bắt đầu. Một bài: điểm và CLO/chủ đề/độ khó, điểm mạnh/yếu
của bài đó; chưa hiển thị xu hướng, hạng hoặc phân bố. Từ hai bài: điểm tích lũy
theo tổng điểm/tổng điểm tối đa, tiến độ và hạng riêng của người học. Tổng quan
và kết quả chi tiết dùng điểm chính thức của bài đang chọn, không lấy trung bình
các khái niệm có thể cùng gắn vào một câu hỏi.

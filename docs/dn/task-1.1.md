# Task 1.1 — Yêu cầu và Proposal

## Trạng thái đầu và review

Đã có một phần: README, requirements-decisions, tài liệu học thuật, schema và API.
Chưa có `docs/proposal.md`. Git log có các đợt hoàn thiện formal/adaptive trước DN.

| Mặt review | Kết quả ban đầu | Hoàn thiện |
| --- | --- | --- |
| Yêu cầu | Có nghiệp vụ MCQ/SQL/essay, formal/practice | Gộp FR01–12/NFR01–08, actor/use case/phạm vi/rủi ro |
| Chất lượng | Stack/service boundary rõ | Giữ stack và tên miền hiện hữu |
| Test | Có bộ backend Docker/PostgreSQL | Ánh xạ tiêu chí vào gate từng task, không sửa test của team |
| Bảo mật | SELECT-only, RBAC, duyệt AI có sẵn | Ghi refresh rotation và sandbox container tạm cần bổ sung |
| Tài liệu | Thiếu Proposal Markdown | Tạo Proposal tiếng Việt và liên kết quyết định đã duyệt |
| Nhất quán | Admin/Exam/Skill khác tên vật lý | Ánh xạ Administrator/assessment/concept/CLO rõ ràng |

## Kế hoạch và kết quả

Tạo Proposal, kế hoạch 13 task và báo cáo này; phụ thuộc README/schema/config và
quyết định đã duyệt. Rủi ro là ghi đè công việc cũ: dùng checkout sạch riêng và chỉ
stage file DN. `git pull --rebase origin develop2` thành công, không có xung đột;
nhánh có 55 commit lịch sử được rebase trước phần DN, không sửa nội dung của chúng.

## Kiểm tra và cách dùng

Kiểm tra UTF-8, liên kết Markdown nội bộ và `git diff --check`; đọc so sánh bảng
schema với yêu cầu. Đây là task tài liệu, không đổi executable, không cần test giả
chỉ để kiểm tra sự tồn tại của đoạn văn. Các gate runtime chạy tại task sở hữu code.
Đọc `docs/proposal.md` và kế hoạch để theo dõi tiêu chí nghiệm thu.

Giả định: topic = subject_area, skill = concept, Admin = Administrator; không sửa
tài liệu Word hoặc frontend. Không còn thiếu hụt trong phạm vi Task 1.1.
Commit: `Task 1.1: define requirements and document the proposal`.

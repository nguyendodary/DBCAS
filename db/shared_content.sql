-- DBCAS shared Admin content. Commit this file with the project.
-- Contains curriculum and questions only; no accounts or learner results.
-- Restore only after schema.sql and seed.sql, into an empty content catalog.
BEGIN;
SET LOCAL standard_conforming_strings = on;
SET LOCAL lock_timeout = '5s';
LOCK TABLE "concept" IN SHARE ROW EXCLUSIVE MODE;
LOCK TABLE "course_learning_outcome" IN SHARE ROW EXCLUSIVE MODE;
LOCK TABLE "question" IN SHARE ROW EXCLUSIVE MODE;
LOCK TABLE "mcq_option" IN SHARE ROW EXCLUSIVE MODE;
LOCK TABLE "sql_test_dataset" IN SHARE ROW EXCLUSIVE MODE;
LOCK TABLE "rubric" IN SHARE ROW EXCLUSIVE MODE;
LOCK TABLE "question_translation" IN SHARE ROW EXCLUSIVE MODE;
LOCK TABLE "clo_concept" IN SHARE ROW EXCLUSIVE MODE;
LOCK TABLE "question_concept" IN SHARE ROW EXCLUSIVE MODE;
LOCK TABLE "concept_dependency" IN SHARE ROW EXCLUSIVE MODE;
DO $guard$ BEGIN
IF EXISTS (SELECT 1 FROM "concept") THEN RAISE EXCEPTION 'Content catalog is not empty; restore cancelled'; END IF;
IF EXISTS (SELECT 1 FROM "course_learning_outcome") THEN RAISE EXCEPTION 'Content catalog is not empty; restore cancelled'; END IF;
IF EXISTS (SELECT 1 FROM "question") THEN RAISE EXCEPTION 'Content catalog is not empty; restore cancelled'; END IF;
IF EXISTS (SELECT 1 FROM "mcq_option") THEN RAISE EXCEPTION 'Content catalog is not empty; restore cancelled'; END IF;
IF EXISTS (SELECT 1 FROM "sql_test_dataset") THEN RAISE EXCEPTION 'Content catalog is not empty; restore cancelled'; END IF;
IF EXISTS (SELECT 1 FROM "rubric") THEN RAISE EXCEPTION 'Content catalog is not empty; restore cancelled'; END IF;
IF EXISTS (SELECT 1 FROM "question_translation") THEN RAISE EXCEPTION 'Content catalog is not empty; restore cancelled'; END IF;
IF EXISTS (SELECT 1 FROM "clo_concept") THEN RAISE EXCEPTION 'Content catalog is not empty; restore cancelled'; END IF;
IF EXISTS (SELECT 1 FROM "question_concept") THEN RAISE EXCEPTION 'Content catalog is not empty; restore cancelled'; END IF;
IF EXISTS (SELECT 1 FROM "concept_dependency") THEN RAISE EXCEPTION 'Content catalog is not empty; restore cancelled'; END IF;
IF NOT EXISTS (SELECT 1 FROM account a JOIN account_role ar USING(account_id) JOIN role r USING(role_id) WHERE r.role_name='Administrator' AND a.status='active') THEN RAISE EXCEPTION 'An existing active administrator is required'; END IF;
END $guard$;

-- concept: 22 rows
INSERT INTO "concept" ("concept_id", "concept_code", "concept_name", "subject_area", "description", "difficulty_level", "sql_feature", "keywords", "learning_objectives") OVERRIDING SYSTEM VALUE VALUES
(1, 'SQL-SELECT', 'Truy vấn dữ liệu bằng SELECT', 'Truy vấn SQL', 'Lấy các cột dữ liệu từ một bảng.', 1, NULL, '{}', '{}'),
(2, 'SQL-WHERE', 'Lọc dữ liệu bằng WHERE', 'Truy vấn SQL', 'Chọn các hàng thỏa mãn điều kiện.', 1, NULL, '{}', '{}'),
(3, 'SQL-JOIN', 'Kết hợp bảng bằng JOIN', 'Truy vấn SQL', 'Kết hợp dữ liệu từ nhiều bảng theo điều kiện liên kết.', 2, NULL, '{}', '{}'),
(4, 'SQL-GROUP-BY', 'Nhóm và tổng hợp dữ liệu', 'Truy vấn SQL', 'Nhóm dữ liệu và tính COUNT, SUM, AVG.', 2, NULL, '{}', '{}'),
(5, 'DB-PRIMARY-KEY', 'Khóa chính', 'Thiết kế cơ sở dữ liệu', 'Xác định duy nhất mỗi hàng trong bảng', 1, NULL, '{}', '{}'),
(6, 'DB-FOREIGN-KEY', 'Khóa ngoại', 'Thiết kế cơ sở dữ liệu', 'Tạo liên kết và bảo đảm tính toàn vẹn giữa các bảng.', 2, NULL, '{}', '{}'),
(7, 'DB-NORMALIZATION', 'Chuẩn hóa dữ liệu', 'Thiết kế cơ sở dữ liệu', 'Tổ chức bảng để giảm dư thừa và bất thường khi cập nhật.', 3, NULL, '{}', '{}'),
(8, 'SQL-INSERT', 'Thêm dữ liệu bằng INSERT', 'Thao tác dữ liệu SQL', '', 1, NULL, '{}', '{}'),
(9, 'SQL-UPDATE', 'Cập nhật dữ liệu bằng UPDATE', 'Thao tác dữ liệu SQL', '', 2, NULL, '{}', '{}'),
(10, 'SQL-DELETE', 'Xóa dữ liệu bằng DELETE', 'Thao tác dữ liệu SQL', '', 2, NULL, '{}', '{}'),
(11, 'SQL-HAVING', 'Lọc nhóm bằng HAVING', 'Truy vấn SQL', 'Lọc các nhóm theo điều kiện tổng hợp.', 3, NULL, '{}', '{}'),
(12, 'SQL-SUBQUERY', 'Truy vấn con', 'Truy vấn SQL', 'Sử dụng kết quả truy vấn bên trong một truy vấn khác.', 3, NULL, '{}', '{}'),
(13, 'DB-TRANSACTION', 'Giao dịch và thuộc tính ACID', 'Giao dịch', 'Giải thích giao dịch, COMMIT, ROLLBACK và ACID.', 3, NULL, '{}', '{}'),
(14, 'SQL-CORRELATED', 'Truy vấn con tương quan', 'Truy vấn SQL nâng cao', 'Viết truy vấn con tham chiếu dữ liệu của truy vấn ngoài.', 4, NULL, '{}', '{}'),
(15, 'SQL-WINDOW', 'Hàm cửa sổ', 'Truy vấn SQL nâng cao', 'Tính toán theo nhóm hàng mà vẫn giữ từng hàng dữ liệu.', 4, NULL, '{}', '{}'),
(16, 'SQL-RANKING', 'Xếp hạng dữ liệu', 'Truy vấn SQL nâng cao', 'Áp dụng ROW_NUMBER, RANK và DENSE_RANK.', 4, NULL, '{}', '{}'),
(17, 'SQL-RUNNING-TOTAL', 'Tính tổng lũy kế', 'Truy vấn SQL nâng cao', 'Dùng hàm cửa sổ để tính tổng theo thứ tự.', 4, NULL, '{}', '{}'),
(18, 'DB-INDEX', 'Thiết kế chỉ mục', 'Hiệu năng cơ sở dữ liệu', 'Lựa chọn chỉ mục theo điều kiện lọc, nối và sắp xếp.', 4, NULL, '{}', '{}'),
(19, 'SQL-RECURSIVE', 'Truy vấn đệ quy', 'Truy vấn SQL nâng cao', 'Dùng WITH RECURSIVE để xử lý dữ liệu phân cấp', 5, NULL, '{}', '{}'),
(20, 'SQL-WINDOW-FRAME', 'Khung cửa sổ nâng cao', 'Truy vấn SQL nâng cao', 'Sử dụng ROWS, RANGE và giới hạn khung tính toán.', 5, NULL, '{}', '{}'),
(21, 'DB-QUERY-TUNING', 'Tối ưu truy vấn phức tạp', 'Hiệu năng cơ sở dữ liệu', 'Kết hợp viết lại truy vấn và thiết kế chỉ mục để cải thiện hiệu năng.', 5, NULL, '{}', '{}'),
(22, 'DB-QUERY-PLAN', 'Phân tích kế hoạch thực thi', 'Hiệu năng cơ sở dữ liệu', 'Đọc EXPLAIN ANALYZE để xác định điểm nghẽn truy vấn.', 5, NULL, '{}', '{}');

-- course_learning_outcome: 10 rows
INSERT INTO "course_learning_outcome" ("clo_id", "clo_code", "title", "description", "status", "created_by") OVERRIDING SYSTEM VALUE VALUES
(1, 'CLO1', 'Truy vấn và lọc dữ liệu', 'Viết câu lệnh SELECT để lấy, lọc và sắp xếp dữ liệu theo yêu cầu.', 'active', (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(2, 'CLO2', 'Kết hợp và tổng hợp dữ liệu', 'Sử dụng JOIN, GROUP BY và các hàm tổng hợp để giải quyết yêu cầu truy vấn.', 'active', (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(3, 'CLO3', 'Thiết kế cơ sở dữ liệu quan hệ', 'Xác định bảng, khóa chính, khóa ngoại và các ràng buộc phù hợp.', 'active', (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(4, 'CLO4', 'Chuẩn hóa cơ sở dữ liệu', 'Phân tích phụ thuộc hàm và chuẩn hóa lược đồ đến dạng chuẩn 3NF.', 'active', (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(5, 'CLO5', 'Thao tác dữ liệu', 'Viết câu lệnh INSERT, UPDATE và DELETE đúng yêu cầu, bảo đảm các ràng buộc dữ liệu.', 'active', (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(6, 'CLO6', 'Sử dụng truy vấn con', 'Viết truy vấn con và truy vấn con tương quan để giải quyết yêu cầu truy xuất dữ liệu.', 'active', (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(7, 'CLO7', 'Phân tích dữ liệu bằng hàm cửa sổ', 'Sử dụng hàm cửa sổ để xếp hạng, tính tổng lũy kế và tính toán theo khung dữ liệu.', 'active', (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(8, 'CLO8', 'Truy vấn dữ liệu phân cấp', 'Sử dụng truy vấn đệ quy để xử lý dữ liệu có cấu trúc phân cấp.', 'active', (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(9, 'CLO9', 'Phân tích và tối ưu hiệu năng truy vấn', 'Đọc kế hoạch thực thi, lựa chọn chỉ mục và tối ưu truy vấn phù hợp.', 'active', (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(10, 'CLO10', 'Hiểu và vận dụng giao dịch', 'Giải thích các thuộc tính ACID và sử dụng giao dịch để bảo đảm tính nhất quán dữ liệu.', 'active', (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1));

-- question: 90 rows
INSERT INTO "question" ("question_id", "question_type", "prompt", "reference_answer", "difficulty_level", "points", "source", "status", "family_id", "version_no", "explanation", "tags", "source_refs", "created_by") OVERRIDING SYSTEM VALUE VALUES
(1, 'mcq', 'Câu lệnh nào lấy toàn bộ các cột trong bảng sinh_vien?', NULL, 1, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(2, 'mcq', 'Đề bài: Bảng sinh_vien có cột diem. Câu lệnh nào lấy những sinh viên có điểm từ 8 trở lên?', NULL, 1, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(3, 'mcq', 'Muốn lấy tất cả sinh viên, kể cả người chưa được xếp lớp, khi nối bảng sinh_vien bên trái với bảng lop bên phải, nên dùng phép nối nào?', NULL, 1, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(4, 'mcq', 'Bảng doanh_thu có đúng một hàng cho mỗi ngày. Câu lệnh sau tính giá trị gì?
SELECT ngay, so_tien,
       SUM(so_tien) OVER (
           ORDER BY ngay
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS tong_luy_ke
FROM doanh_thu;', NULL, 5, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(5, 'mcq', 'Với ba mức điểm 10, 10, 8, những phát biểu nào đúng khi xếp theo điểm giảm dần?', NULL, 4, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(8, 'mcq', 'Những phát biểu nào sau đây đúng về PostgreSQL? Chọn những đáp án đúng', NULL, 5, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(9, 'mcq', 'Câu lệnh sau tìm những sinh viên nào?
SELECT sv.ho_ten
FROM sinh_vien sv
WHERE sv.diem > (
    SELECT AVG(sv2.diem)
    FROM sinh_vien sv2
    WHERE sv2.ma_lop = sv.ma_lop
);', NULL, 4, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(10, 'mcq', 'Khi thực hiện chuyển tiền giữa hai tài khoản trong một giao dịch, thao tác trừ tiền đã chạy nhưng thao tác cộng tiền bị lỗi. Cần làm gì để hủy toàn bộ thay đổi chưa được xác nhận của giao dịch đó?', NULL, 3, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(11, 'mcq', 'Những phát biểu nào sau đây là đúng?', NULL, 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(12, 'mcq', 'Câu lệnh sau dùng để làm gì?
SELECT ho_ten
FROM sinh_vien
WHERE diem > (SELECT AVG(diem) FROM sinh_vien);', NULL, 3, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(13, 'sql', 'Cho sẵn bảng sinh_vien và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Liệt kê mã, họ tên và điểm của sinh viên có điểm từ 8 trở lên', 'SELECT ma_sv, ho_ten, diem
FROM sinh_vien
WHERE diem >= 8;', 1, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(14, 'sql', 'Cho sẵn bảng lop, sinh_vien và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Liệt kê họ tên sinh viên và tên lớp tương ứng. Chỉ lấy sinh viên có lớp khớp trong bảng lop', 'SELECT sv.ho_ten, l.ten_lop
FROM sinh_vien sv
JOIN lop l ON sv.ma_lop = l.ma_lop;', 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(15, 'sql', 'Cho sẵn bảng sinh_vien và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Liệt kê mã lớp và số sinh viên của những lớp có ít nhất hai sinh viên. Đặt tên cột đếm là so_sinh_vien', 'SELECT ma_lop, COUNT(*) AS so_sinh_vien
FROM sinh_vien
GROUP BY ma_lop
HAVING COUNT(*) >= 2;', 3, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(16, 'sql', 'Liệt kê mã, họ tên và điểm của sinh viên có điểm cao hơn điểm trung bình của chính lớp mình', 'SELECT sv.ma_sv, sv.ho_ten, sv.diem
FROM sinh_vien sv
WHERE sv.diem > (
    SELECT AVG(sv2.diem)
    FROM sinh_vien sv2
    WHERE sv2.ma_lop = sv.ma_lop
);', 4, 1.00, 'bank', 'retired', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(17, 'sql', 'Cho sẵn bảng doanh_thu và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Bảng doanh_thu có đúng một hàng cho mỗi ngày. Liệt kê ngày, số tiền và tổng doanh thu từ ngày đầu tiên đến ngày hiện tại. Đặt tên cột tổng là tong_luy_ke', 'SELECT ngay, so_tien,
       SUM(so_tien) OVER (
           ORDER BY ngay
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS tong_luy_ke
FROM doanh_thu;', 5, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(18, 'essay', 'Phân biệt khóa chính và khóa ngoại. Cho ví dụ với hai bảng lop và sinh_vien, giải thích vai trò của mỗi loại khóa', 'Khóa chính xác định duy nhất mỗi hàng trong bảng, không được trùng hoặc NULL. Khóa ngoại tham chiếu đến khóa chính hoặc khóa duy nhất phù hợp, giúp bảo đảm tính toàn vẹn tham chiếu. Ví dụ: lop.ma_lop là khóa chính; sinh_vien.ma_lop là khóa ngoại tham chiếu đến lop.ma_lop, thể hiện sinh viên thuộc lớp nào', 2, 2.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(19, 'essay', 'Phân biệt WHERE và HAVING. Với bảng sinh_vien(ma_sv, ma_lop, diem), hãy trình bày cách tìm các lớp có ít nhất 10 sinh viên đạt điểm từ 5 trở lên', 'WHERE lọc từng hàng trước khi nhóm dữ liệu; HAVING lọc các nhóm sau khi tổng hợp. Với yêu cầu trên, dùng WHERE diem >= 5 để giữ những sinh viên đạt yêu cầu, GROUP BY ma_lop để nhóm theo lớp, rồi HAVING COUNT(*) >= 10 để lấy các lớp có ít nhất 10 sinh viên đạt yêu cầu.
Câu lệnh:
SELECT ma_lop, COUNT(*) AS so_sinh_vien FROM sinh_vien WHERE diem >= 5 GROUP BY ma_lop HAVING COUNT(*) >= 10;', 3, 2.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(20, 'essay', 'Khi chuyển tiền từ tài khoản A sang tài khoản B, hệ thống phải trừ tiền ở A và cộng tiền vào B. Vì sao hai thao tác này cần nằm trong cùng một giao dịch? Giải thích vai trò của tính nguyên tử, COMMIT và ROLLBACK khi thao tác cộng tiền thất bại trước khi giao dịch được xác nhận', 'Hai thao tác cần nằm trong cùng một giao dịch để tránh tình trạng tiền đã bị trừ ở A nhưng chưa được cộng vào B. Tính nguyên tử bảo đảm toàn bộ giao dịch thành công hoặc các thay đổi của giao dịch bị hủy. Khi cả hai thao tác thành công và các điều kiện nghiệp vụ được thỏa mãn, COMMIT xác nhận giao dịch. Nếu thao tác cộng tiền thất bại trước khi COMMIT, thực hiện ROLLBACK để hoàn tác cả thao tác trừ tiền đã thực hiện trong giao dịch đó.', 4, 2.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(21, 'mcq', 'Câu lệnh nào lấy tất cả các cột từ bảng students?', NULL, 1, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(22, 'mcq', 'Câu lệnh nào lấy sinh viên có điểm từ 8 trở lên?', NULL, 1, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(23, 'mcq', 'INNER JOIN trả về những hàng nào?', NULL, 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(24, 'mcq', 'Câu lệnh nào đếm số sinh viên của từng lớp?', NULL, 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(25, 'mcq', 'Muốn chỉ hiển thị các lớp có từ 5 sinh viên trở lên sau khi nhóm dữ liệu, cần dùng điều kiện nào?', NULL, 3, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(26, 'sql', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Từ bảng students, lấy hai cột name và score của những sinh viên có điểm từ 8 trở lên', 'SELECT name, score
FROM students
WHERE score >= 8;', 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(27, 'sql', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Từ bảng students, trả về class_id và số sinh viên total_students của mỗi lớp có ít nhất 2 sinh viên', 'SELECT class_id, COUNT(*) AS total_students
FROM students
GROUP BY class_id
HAVING COUNT(*) >= 2;', 3, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(28, 'essay', 'Phân biệt WHERE và HAVING trong SQL. Cho ví dụ sử dụng từng mệnh đề', 'WHERE lọc từng hàng trước khi nhóm và tổng hợp dữ liệu. HAVING lọc các nhóm sau khi nhóm và tổng hợp. Ví dụ: SELECT * FROM students WHERE score >= 8; lấy các sinh viên đạt từ 8 điểm. SELECT class_id, COUNT(*) FROM students GROUP BY class_id HAVING COUNT(*) >= 2; lấy các lớp có ít nhất 2 sinh viên.', 3, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(29, 'mcq', 'Mục đích chính của chuẩn hóa cơ sở dữ liệu quan hệ là gì?', NULL, 1, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(30, 'mcq', 'Trong thiết kế thông thường, bảng nào vi phạm dạng chuẩn thứ nhất (1NF)?', NULL, 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(31, 'mcq', 'Câu lệnh nào thêm sinh viên có id = 1, name = ''An'' vào bảng students?', NULL, 1, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(32, 'mcq', 'Bảng students có cột status TEXT DEFAULT ''active''. Nếu thêm một hàng và không chỉ định cột status, giá trị của cột này là gì?', NULL, 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(33, 'mcq', 'Những phát biểu nào đúng về khóa chính? Chọn các đáp án đúng.', NULL, 1, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(34, 'mcq', 'Bảng students có class_id là khóa ngoại tham chiếu classes(id). Khi class_id khác NULL, ràng buộc này yêu cầu điều gì?', NULL, 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(35, 'mcq', 'Câu lệnh nào chỉ đổi tên sinh viên có id = 5 thành ''Thu''?', NULL, 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(36, 'mcq', 'Tính nguyên tử — Atomicity — trong ACID có nghĩa là gì?', NULL, 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(37, 'mcq', 'Trong PostgreSQL, thành phần nào cho phép một CTE tham chiếu lại chính nó để xử lý dữ liệu phân cấp?', NULL, 4, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(38, 'sql', 'Cho sẵn bảng student_import và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Bảng student_import chứa dữ liệu sinh viên chưa được kiểm tra và chưa có khóa chính. Trước khi dùng student_id làm khóa chính, hãy tìm các mã xuất hiện nhiều hơn một lần. Trả về hai cột student_id và occurrences.', 'SELECT student_id, COUNT(*) AS occurrences FROM student_import GROUP BY student_id HAVING COUNT(*) > 1;', 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(39, 'sql', 'Cho sẵn bảng classes, student_import và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Trước khi thêm ràng buộc khóa ngoại, hãy kiểm tra bảng student_import. Tìm sinh viên có class_id khác NULL nhưng không tồn tại lớp tương ứng trong bảng classes. Trả về student_id, name, class_id.', 'SELECT s.student_id, s.name, s.class_id FROM student_import AS s LEFT JOIN classes AS c ON s.class_id = c.id WHERE s.class_id IS NOT NULL AND c.id IS NULL;', 3, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(40, 'mcq', 'SELECT DISTINCT class_id FROM students có tác dụng gì?', NULL, 1, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(41, 'mcq', 'Điều kiện nào tìm các hàng có email chưa được nhập (giá trị NULL)?', NULL, 1, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(42, 'mcq', 'Điều kiện score BETWEEN 5 AND 8 tương đương điều kiện nào?', NULL, 1, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(43, 'mcq', 'Với ba hàng có score lần lượt là 8, NULL, 6, COUNT(score) và COUNT(*) lần lượt bằng bao nhiêu?', NULL, 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(44, 'mcq', 'LEFT JOIN giữ lại hàng bên trái không có hàng tương ứng bên phải như thế nào?', NULL, 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(45, 'mcq', 'Trong PostgreSQL, xét bảng sales không có ràng buộc khóa: câu SELECT region, SUM(amount) FROM sales cần thêm gì để tổng hợp theo từng vùng?', NULL, 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(46, 'mcq', 'Khóa chính ghép PRIMARY KEY(student_id, course_id) bảo đảm điều gì?', NULL, 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(47, 'mcq', 'Trong PostgreSQL, một cột khóa ngoại đơn cho phép NULL và không có NOT NULL. Phát biểu nào đúng?', NULL, 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(48, 'mcq', 'Khi dùng INSERT INTO students (name, age) VALUES (...), thứ tự giá trị được hiểu theo gì?', NULL, 1, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(49, 'mcq', 'UPDATE products SET price = 100; không có WHERE sẽ tác động thế nào nếu chạy thành công?', NULL, 1, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(50, 'mcq', 'Những phát biểu nào đúng về DELETE FROM students; nếu thực thi thành công? Chọn các đáp án đúng.', NULL, 1, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(51, 'mcq', 'Bảng enrollment(student_id, course_id, student_name, grade) có khóa ghép (student_id, course_id); student_id xác định student_name. Phụ thuộc này gây vấn đề gì?', NULL, 3, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(52, 'mcq', 'Bảng employee(emp_id, dept_id, dept_name) có khóa emp_id, với emp_id → dept_id và dept_id → dept_name; dept_id không là siêu khóa, dept_name không thuộc khóa ứng viên nào. Vì sao vi phạm 3NF?', NULL, 3, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(53, 'mcq', 'Với R(A,B,C), tách thành R1(A,B) và R2(B,C). Điều kiện nào đủ bảo đảm phép tách không mất mát theo phụ thuộc hàm?', NULL, 4, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(54, 'mcq', 'Trong một giao dịch PostgreSQL chưa COMMIT, ROLLBACK toàn bộ giao dịch có tác dụng gì với các thay đổi INSERT/UPDATE/DELETE của giao dịch đó?', NULL, 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(55, 'mcq', 'Trong PostgreSQL ở mức READ COMMITTED, hai SELECT liên tiếp trong cùng giao dịch có thể đọc giá trị khác nhau của một hàng vì giao dịch khác đã COMMIT thay đổi giữa hai lần đọc. Hiện tượng này là gì?', NULL, 4, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(56, 'mcq', 'Một truy vấn con dùng ở vị trí giá trị vô hướng trả về hai hàng. PostgreSQL sẽ xử lý thế nào?', NULL, 3, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(57, 'mcq', 'EXISTS (SELECT 1 FROM orders WHERE customer_id = 5) kiểm tra điều gì?', NULL, 3, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(58, 'mcq', 'Đặc điểm nào nhận diện truy vấn con tương quan?', NULL, 4, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(59, 'mcq', 'Những phát biểu nào đúng về SUM(amount) OVER (PARTITION BY customer_id)? Chọn các đáp án đúng.', NULL, 3, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(60, 'mcq', 'Với ba điểm 90, 90, 80 và RANK() OVER (ORDER BY score DESC), hạng tương ứng là gì?', NULL, 4, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(61, 'mcq', 'Với ba điểm 90, 90, 80 và DENSE_RANK() OVER (ORDER BY score DESC), hạng tương ứng là gì?', NULL, 4, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(62, 'mcq', 'Với id duy nhất, biểu thức nào tính tổng lũy kế amount theo thứ tự id?', NULL, 4, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(63, 'mcq', 'Trong PostgreSQL, SUM(amount) OVER (ORDER BY sale_date) không ghi frame, với nhiều hàng cùng sale_date, có đặc điểm nào?', NULL, 5, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(64, 'mcq', 'Muốn LAST_VALUE(score) trả về giá trị cuối toàn bộ phân vùng theo thứ tự id, frame nào phù hợp?', NULL, 5, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(65, 'mcq', 'Với CTE đệ quy sinh số từ 1 bằng cách cộng 1 và dùng UNION ALL, điều kiện nào giúp dừng ở 10?', NULL, 4, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(66, 'mcq', 'Trong CTE đệ quy PostgreSQL, UNION khác UNION ALL ở điểm nào liên quan đến các hàng kết quả?', NULL, 5, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(67, 'mcq', 'Với B-tree ghép (customer_id, created_at), truy vấn nào thường phù hợp với thứ tự cột của chỉ mục để lọc và duyệt theo thời gian?', NULL, 4, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(68, 'mcq', 'Những phát biểu nào đúng về EXPLAIN ANALYZE trong PostgreSQL? Chọn các đáp án đúng.', NULL, 5, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(69, 'mcq', 'Bảng orders có chỉ mục B-tree thông thường trên created_at kiểu timestamp. Cách lọc ngày nào thường giúp tận dụng chỉ mục mà không bọc cột trong hàm?', NULL, 5, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(70, 'sql', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Từ bảng students, lấy id và name của sinh viên có score từ 9 trở lên.', 'SELECT id, name FROM students WHERE score >= 9;', 1, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(71, 'sql', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Từ bảng students, lấy id và name của sinh viên chưa có điểm (score là NULL).', 'SELECT id, name FROM students WHERE score IS NULL;', 1, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(72, 'sql', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Đếm số sinh viên của mỗi class_id trong students, kể cả sinh viên chưa có điểm. Trả về class_id và student_count.', 'SELECT class_id, COUNT(*) AS student_count FROM students GROUP BY class_id;', 2, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(73, 'sql', 'Tìm các lớp có điểm trung bình từ 8 trở lên. Bỏ qua score NULL khi tính trung bình. Trả về class_id và average_score.', 'SELECT class_id, AVG(score) AS average_score FROM students GROUP BY class_id HAVING AVG(score) >= 8;', 3, 1.00, 'bank', 'retired', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(74, 'sql', 'Kết hợp students và classes để lấy students.id thành student_id, students.name thành student_name, classes.name thành class_name cho sinh viên có lớp tương ứng.', 'SELECT s.id AS student_id, s.name AS student_name, c.name AS class_name FROM students s JOIN classes c ON s.class_id=c.id;', 2, 1.00, 'bank', 'retired', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(75, 'sql', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Lấy id, name, score của sinh viên có điểm cao hơn điểm trung bình của toàn bộ sinh viên có điểm trong students.', 'SELECT id, name, score FROM students WHERE score > (SELECT AVG(score) FROM students);', 3, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(76, 'sql', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Lấy id, name, score của sinh viên có điểm cao hơn điểm trung bình của chính lớp mình. Không tính score NULL vào trung bình.', 'SELECT s.id, s.name, s.score FROM students s WHERE s.score > (SELECT AVG(t.score) FROM students t WHERE t.class_id=s.class_id);', 4, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(77, 'sql', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Xếp hạng các sinh viên có điểm theo score giảm dần bằng hạng liên tiếp không có khoảng trống; các điểm bằng nhau cùng hạng. Trả về id và score_rank.', 'SELECT id, DENSE_RANK() OVER (ORDER BY score DESC) AS score_rank FROM students WHERE score IS NOT NULL;', 4, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(78, 'sql', 'Cho sẵn bảng sales và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Từ bảng sales có day_no duy nhất, tính doanh thu lũy kế từ ngày đầu đến ngày hiện tại. Trả về day_no và running_total.', 'SELECT day_no, SUM(amount) OVER (ORDER BY day_no ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total FROM sales;', 4, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(79, 'sql', 'Cho sẵn bảng sales và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Từ bảng sales có day_no duy nhất, tính trung bình amount của ngày hiện tại và hàng ngày liền trước trong thứ tự day_no. Ngày đầu chỉ dùng chính nó. Trả về day_no và moving_average.', 'SELECT day_no, AVG(amount) OVER (ORDER BY day_no ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) AS moving_average FROM sales;', 5, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(80, 'sql', 'Cho sẵn bảng employees và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Bảng employees biểu diễn cây quản lý không có chu trình, với CEO có id=1. Lấy id và depth của CEO cùng toàn bộ nhân viên cấp dưới trực tiếp hoặc gián tiếp; CEO có depth=0.', 'WITH RECURSIVE tree AS (SELECT id, 0 AS depth FROM employees WHERE id=1 UNION ALL SELECT e.id, t.depth+1 FROM employees e JOIN tree t ON e.manager_id=t.id) SELECT id, depth FROM tree;', 5, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(81, 'sql', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Chọn đúng một sinh viên có điểm cao nhất ở mỗi lớp trong students. Nếu bằng điểm, chọn id nhỏ hơn. Sinh viên có score NULL không được xét. Trả về class_id, id, name, score.', 'SELECT class_id, id, name, score FROM (SELECT class_id,id,name,score,ROW_NUMBER() OVER (PARTITION BY class_id ORDER BY score DESC,id) AS rn FROM students WHERE score IS NOT NULL) ranked WHERE rn=1;', 5, 1.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(82, 'essay', 'Thiết kế khóa cho bảng enrollment lưu việc sinh viên đăng ký học phần. Giải thích cách tránh đăng ký trùng và giữ liên kết hợp lệ đến sinh viên, học phần.', 'Có thể dùng khóa chính ghép (student_id, course_id) để mỗi cặp chỉ xuất hiện một lần; hoặc dùng id riêng kèm UNIQUE(student_id, course_id). student_id và course_id là khóa ngoại đến students và courses, thường đặt NOT NULL. Ràng buộc khóa ngoại ngăn tham chiếu đối tượng không tồn tại; chính sách xóa cần được chọn rõ theo nghiệp vụ.', 3, 2.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(83, 'essay', 'Bảng employee(emp_id, emp_name, dept_id, dept_name) có emp_id là khóa, dept_id xác định dept_name. Hãy chỉ ra bất thường cập nhật và đề xuất tách bảng đến 3NF với giả định dept_id không phải siêu khóa của employee.', 'dept_name bị lặp trên nhiều nhân viên cùng phòng. Đổi tên phòng phải sửa nhiều hàng, dễ không nhất quán; khó lưu phòng chưa có nhân viên. Tách departments(dept_id PK, dept_name) và employees(emp_id PK, emp_name, dept_id FK). Phép nối qua dept_id khôi phục thông tin và loại bỏ phụ thuộc bắc cầu của dept_name vào emp_id trong bảng nhân viên.', 3, 2.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(84, 'essay', 'Giải thích vì sao chuyển tiền giữa hai tài khoản cần một giao dịch. Nêu cách xử lý khi đã trừ tiền nhưng bước cộng tiền thất bại.', 'Hai cập nhật phải thuộc cùng một giao dịch: BEGIN, kiểm tra điều kiện nghiệp vụ và khóa phù hợp, trừ tiền, cộng tiền rồi COMMIT khi mọi bước thành công. Nếu bước cộng tiền lỗi phải ROLLBACK cả giao dịch để không giữ trạng thái chỉ trừ tiền. Atomicity bảo đảm tất cả hoặc không thao tác nào có hiệu lực. Cần xử lý đồng thời để tránh đọc và cập nhật số dư không nhất quán.', 3, 2.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(85, 'essay', 'Phân biệt truy vấn con độc lập và truy vấn con tương quan. Minh họa bằng việc tìm nhân viên có lương cao hơn trung bình toàn công ty và trung bình phòng mình.', 'Truy vấn con độc lập không tham chiếu cột bên ngoài: SELECT id FROM employees WHERE salary > (SELECT AVG(salary) FROM employees). Truy vấn con tương quan tham chiếu hàng ngoài: SELECT e.id FROM employees e WHERE e.salary > (SELECT AVG(x.salary) FROM employees x WHERE x.dept_id=e.dept_id). Không nên khẳng định truy vấn con tương quan luôn chạy đúng một lần cho mỗi hàng ở mức thực thi vì bộ tối ưu có thể biến đổi kế hoạch.', 4, 2.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(86, 'essay', 'So sánh GROUP BY với hàm cửa sổ. Khi cần giữ từng nhân viên và hiển thị thêm tổng lương phòng cùng hạng lương trong phòng, nên làm thế nào?', 'GROUP BY thường gộp nhiều hàng thành một hàng cho mỗi nhóm. Hàm cửa sổ tính trên phân vùng nhưng giữ hàng chi tiết. Có thể dùng SUM(salary) OVER (PARTITION BY dept_id) và DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) trong SELECT từng nhân viên. RANK và ROW_NUMBER cũng có thể phù hợp nếu nêu rõ quy tắc xử lý hòa hạng.', 4, 2.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(87, 'essay', 'Có nên tạo chỉ mục cho mọi cột để tăng tốc cơ sở dữ liệu không? Phân tích lợi ích, chi phí và cách chọn chỉ mục cho truy vấn thường dùng.', 'Không nên tạo mọi chỉ mục. Chỉ mục có thể giảm lượng dữ liệu đọc cho truy vấn lọc, nối hoặc sắp xếp phù hợp; hiệu quả phụ thuộc độ chọn lọc, kích thước bảng và kế hoạch. Chỉ mục chiếm bộ nhớ lưu trữ và tăng chi phí INSERT/UPDATE/DELETE vì phải duy trì. Nên dựa vào truy vấn thực tế, chọn cột và thứ tự chỉ mục ghép, đo với EXPLAIN ANALYZE trên môi trường phù hợp, tránh chỉ mục dư thừa.', 4, 2.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(88, 'essay', 'EXPLAIN ANALYZE cho thấy estimated rows rất khác actual rows ở một nút và một phép JOIN tốn thời gian. Trình bày quy trình tìm nguyên nhân và tối ưu có kiểm chứng.', 'Đọc kế hoạch theo cây, chú ý actual time, rows và loops thay vì cộng máy móc thời gian các nút lồng nhau. Sai lệch ước lượng có thể đến từ thống kê cũ, phân bố lệch hoặc tương quan cột. Kiểm tra điều kiện lọc/nối, thống kê, chỉ mục và kiểu nối; cân nhắc ANALYZE hay thống kê mở rộng khi phù hợp. Thử từng thay đổi, chạy lại với dữ liệu và tham số đại diện, bảo đảm kết quả tương đương và so sánh số liệu trước/sau. EXPLAIN ANALYZE thực sự thực thi câu lệnh nên chọn môi trường phù hợp.', 5, 2.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(89, 'essay', 'Khi duyệt quan hệ quản lý bằng WITH RECURSIVE, chu trình trong dữ liệu có thể gây vấn đề gì? Đề xuất cách phát hiện hoặc ngăn lặp và giải thích giới hạn của UNION.', 'Với UNION ALL, quan hệ tạo chu trình có thể sinh hàng lặp vô hạn nếu không có điều kiện dừng. Có thể mang theo mảng đường đi và bỏ nút đã có trong đường đi, dùng CYCLE khi phiên bản PostgreSQL hỗ trợ, hoặc giới hạn độ sâu theo nghiệp vụ nhưng giới hạn đó có thể cắt mất kết quả. UNION loại hàng trùng trên toàn bộ cột; nếu có depth tăng hoặc path thay đổi thì các hàng vẫn khác nhau, nên không bảo đảm ngăn mọi chu trình. Cần quy định rõ xử lý dữ liệu chu trình.', 5, 2.00, 'bank', 'validated', NULL, 1, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(91, 'sql', 'Cho sẵn bảng sinh_vien và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Liệt kê mã, họ tên và điểm của sinh viên có điểm cao hơn điểm trung bình của chính lớp mình', 'SELECT sv.ma_sv, sv.ho_ten, sv.diem
FROM sinh_vien sv
WHERE sv.diem > (
    SELECT AVG(sv2.diem)
    FROM sinh_vien sv2
    WHERE sv2.ma_lop = sv.ma_lop
);', 4, 1.00, 'bank', 'validated', 16, 2, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(92, 'sql', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Tìm các lớp có điểm trung bình từ 8 trở lên. Bỏ qua score NULL khi tính trung bình. Trả về class_id và average_score.', 'SELECT class_id, AVG(score) AS average_score FROM students GROUP BY class_id HAVING AVG(score) >= 8;', 3, 1.00, 'bank', 'validated', 73, 2, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)),
(93, 'sql', 'Cho sẵn bảng students, classes và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Kết hợp students và classes để lấy students.id thành student_id, students.name thành student_name, classes.name thành class_name cho sinh viên có lớp tương ứng.', 'SELECT s.id AS student_id, s.name AS student_name, c.name AS class_name FROM students s JOIN classes c ON s.class_id=c.id;', 2, 1.00, 'bank', 'validated', 74, 2, NULL, '{}', '[]'::jsonb, (SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1));

-- mcq_option: 216 rows
INSERT INTO "mcq_option" ("option_id", "question_id", "option_label", "option_text", "is_correct") OVERRIDING SYSTEM VALUE VALUES
(5, 1, 'A', 'SELECT * FROM sinh_vien;', true),
(6, 1, 'B', 'SELECT sinh_vien FROM *;', false),
(7, 1, 'C', 'GET ALL FROM sinh_vien;', false),
(8, 1, 'D', 'SHOW ROWS sinh_vien;', false),
(13, 2, 'A', 'SELECT * FROM sinh_vien WHERE diem > 8;', false),
(14, 2, 'B', 'SELECT * FROM sinh_vien WHERE diem >= 8;', true),
(15, 2, 'C', 'SELECT * FROM sinh_vien WHERE diem < 8;', false),
(16, 2, 'D', 'SELECT * FROM sinh_vien ORDER BY diem;', false),
(17, 3, 'A', 'INNER JOIN', false),
(18, 3, 'B', 'CROSS JOIN', false),
(19, 3, 'C', 'LEFT JOIN', true),
(20, 3, 'D', 'RIGHT JOIN', false),
(21, 4, 'A', 'Tổng doanh thu từ ngày đầu tiên đến ngày của hàng hiện tại', true),
(22, 4, 'B', 'Chỉ doanh thu của ngày hiện tại', false),
(23, 4, 'C', 'Tổng doanh thu của các ngày sau ngày hiện tại', false),
(24, 4, 'D', 'Doanh thu lớn nhất trong toàn bảng.', false),
(25, 5, 'A', 'RANK() tạo các hạng 1, 1, 3', false),
(26, 5, 'B', 'DENSE_RANK() tạo các hạng 1, 1, 2', true),
(27, 5, 'C', 'ROW_NUMBER() gán cùng một số thứ tự cho hai hàng có điểm 10', false),
(28, 5, 'D', 'Hàm cửa sổ luôn gộp nhiều hàng thành một hàng như GROUP BY', false),
(38, 8, 'A', 'EXPLAIN ANALYZE thực sự thực thi câu lệnh để thu thập số liệu thực tế', true),
(39, 8, 'B', 'Chỉ mục phù hợp có thể giúp tăng tốc một số truy vấn có WHERE hoặc JOIN', true),
(40, 8, 'C', 'Càng tạo nhiều chỉ mục thì mọi thao tác INSERT, UPDATE và DELETE càng nhanh', false),
(41, 8, 'D', 'PostgreSQL luôn phải sử dụng chỉ mục nếu bảng có chỉ mục', false),
(42, 9, 'A', 'Sinh viên có điểm cao hơn trung bình toàn trường', false),
(43, 9, 'B', 'Sinh viên có điểm cao hơn trung bình của chính lớp mình', true),
(44, 9, 'C', 'Sinh viên có điểm thấp nhất trong mỗi lớp', false),
(45, 9, 'D', 'Sinh viên chưa được xếp lớp', false),
(46, 10, 'A', 'Chạy COMMIT', false),
(47, 10, 'B', 'Chạy ROLLBACK', true),
(48, 10, 'C', 'Chạy DELETE để xóa hai tài khoản', false),
(49, 10, 'D', 'Chạy SELECT để tự động hoàn tác', false),
(50, 11, 'A', 'UPDATE sinh_vien SET diem = 10; cập nhật điểm của tất cả hàng nếu không bị ràng buộc khác ngăn cản', true),
(51, 11, 'B', 'DELETE FROM sinh_vien WHERE diem < 5; xóa các hàng có điểm nhỏ hơn 5', true),
(52, 11, 'C', 'DELETE FROM sinh_vien; xóa cả cấu trúc bảng', false),
(53, 11, 'D', 'UPDATE không có WHERE chỉ cập nhật hàng đầu tiên', false),
(54, 12, 'A', 'Tìm sinh viên có điểm cao hơn điểm trung bình của toàn bảng', true),
(55, 12, 'B', 'Tìm sinh viên có điểm cao nhất trong mỗi lớp', false),
(56, 12, 'C', 'Tăng điểm của tất cả sinh viên', false),
(57, 12, 'D', 'Tìm sinh viên có điểm bằng điểm trung bình', false),
(58, 21, 'A', 'SELECT * FROM students;', true),
(59, 21, 'B', 'SELECT students;', false),
(60, 21, 'C', 'GET * FROM students;', false),
(61, 21, 'D', 'FROM students SELECT;', false),
(62, 22, 'A', 'SELECT * FROM students WHERE score > 8;', false),
(63, 22, 'B', 'SELECT * FROM students WHERE score >= 8;', true),
(64, 22, 'C', 'SELECT * FROM students HAVING score >= 8;', false),
(65, 22, 'D', 'SELECT * FROM students WHERE score = 8;', false),
(66, 23, 'A', 'Tất cả hàng của bảng bên trái', true),
(67, 23, 'B', 'Tất cả hàng của cả hai bảng', false),
(68, 23, 'C', 'Các hàng kết hợp thỏa điều kiện nối', false),
(69, 23, 'D', 'Các hàng kết hợp thỏa điều kiện nố', false),
(70, 24, 'A', 'SELECT class_id, COUNT(*) FROM students GROUP BY class_id;', true),
(71, 24, 'B', 'SELECT class_id, COUNT(*) FROM students;', false),
(72, 24, 'C', 'SELECT class_id FROM students WHERE COUNT(*) > 0;', false),
(73, 24, 'D', 'SELECT COUNT(class_id) FROM students;', false),
(74, 25, 'A', 'WHERE COUNT(*) >= 5', false),
(75, 25, 'B', 'HAVING COUNT(*) >= 5', true),
(76, 25, 'C', 'GROUP BY COUNT(*) >= 5', false),
(77, 25, 'D', 'ORDER BY COUNT(*) >= 5', false),
(78, 29, 'A', 'Giảm dư thừa dữ liệu và hạn chế bất thường khi thêm, sửa, xóa', true),
(79, 29, 'B', 'Gộp tất cả dữ liệu vào một bảng duy nhất', false),
(80, 29, 'C', 'Loại bỏ mọi khóa ngoại', false),
(81, 29, 'D', 'Bảo đảm mọi truy vấn luôn chạy nhanh hơn', false),
(82, 30, 'A', 'Bảng có khóa chính gồm hai cột', false),
(83, 30, 'B', 'Bảng lưu nhiều số điện thoại trong một ô, phân cách bằng dấu phẩy', true),
(84, 30, 'C', 'Bảng có khóa ngoại', false),
(85, 30, 'D', 'Bảng không có cột kiểu số', false),
(86, 31, 'A', 'INSERT INTO students (id, name) VALUES (1, ''An'');', true),
(87, 31, 'B', 'INSERT students SET (1, ''An'');', false),
(88, 31, 'C', 'ADD INTO students (id, name) VALUES (1, ''An'');', false),
(89, 31, 'D', 'UPDATE students VALUES (1, ''An'');', false),
(90, 32, 'A', 'Luôn là NULL.', false),
(91, 32, 'B', 'Chuỗi rỗng.', false),
(92, 32, 'C', '''active''.', true),
(93, 32, 'D', 'Câu lệnh luôn bị lỗi.', false),
(94, 33, 'A', 'Giá trị khóa chính xác định duy nhất mỗi hàng.', true),
(95, 33, 'B', 'Các cột thuộc khóa chính không được chứa NULL.', true),
(96, 33, 'C', 'Một khóa chính có thể gồm nhiều cột.', true),
(97, 33, 'D', 'Một bảng có thể có nhiều ràng buộc PRIMARY KEY riêng biệt.', false),
(98, 34, 'A', 'class_id phải khác nhau ở mọi sinh viên.', false),
(99, 34, 'B', 'Phải tồn tại hàng trong classes có id bằng class_id.', true),
(100, 34, 'C', 'Hai bảng phải có cùng số hàng.', false),
(101, 34, 'D', 'class_id phải là khóa chính của students.', false),
(102, 35, 'A', 'UPDATE students SET name = ''Thu'';', false),
(103, 35, 'B', 'UPDATE students SET name = ''Thu'' WHERE id = 5;', true),
(104, 35, 'C', 'INSERT INTO students SET name = ''Thu'' WHERE id = 5;', false),
(105, 35, 'D', 'UPDATE name = ''Thu'' FROM students WHERE id = 5;', false),
(106, 36, 'A', 'Các thao tác trong giao dịch hoặc được thực hiện toàn bộ, hoặc không thao tác nào có hiệu lực sau khi hoàn tác.', true),
(107, 36, 'B', 'Mọi giao dịch chỉ được chứa một câu lệnh.', false),
(108, 36, 'C', 'Mọi giao dịch luôn thành công.', false),
(109, 36, 'D', 'Dữ liệu không bao giờ được thay đổi.', false),
(110, 37, 'A', 'WITH RECURSIVE.', true),
(111, 37, 'B', 'ORDER BY.', false),
(112, 37, 'C', 'SELECT DISTINCT.', false),
(113, 37, 'D', 'LIMIT.', false),
(114, 40, 'A', 'Trả về mỗi giá trị class_id khác nhau một lần.', true),
(115, 40, 'B', 'Xóa các hàng trùng khỏi bảng students.', false),
(116, 40, 'C', 'Chỉ lấy class_id xuất hiện đúng một lần.', false),
(117, 40, 'D', 'Luôn sắp xếp class_id tăng dần.', false),
(118, 41, 'A', 'email = NULL', false),
(119, 41, 'B', 'email IS NULL', true),
(120, 41, 'C', 'email = NULL_STRING', false),
(121, 41, 'D', 'email IS EMPTY', false),
(122, 42, 'A', 'score > 5 AND score < 8', false),
(123, 42, 'B', 'score >= 5 AND score <= 8', true),
(124, 42, 'C', 'score >= 5 OR score <= 8', false),
(125, 42, 'D', 'score = 5 AND score = 8', false),
(126, 43, 'A', '3 và 3.', false),
(127, 43, 'B', '2 và 2.', false),
(128, 43, 'C', '2 và 3.', true),
(129, 43, 'D', '3 và 2.', false),
(130, 44, 'A', 'Loại bỏ hàng đó.', false),
(131, 44, 'B', 'Giữ hàng đó, các cột bên phải nhận NULL.', true),
(132, 44, 'C', 'Tự tạo hàng tương ứng trong bảng bên phải.', false),
(133, 44, 'D', 'Luôn báo lỗi.', false),
(134, 45, 'A', 'GROUP BY region.', true),
(135, 45, 'B', 'GROUP BY amount.', false),
(136, 45, 'C', 'WHERE SUM(amount).', false),
(137, 45, 'D', 'Không cần thêm gì.', false),
(138, 46, 'A', 'Mỗi student_id chỉ được xuất hiện một lần.', false),
(139, 46, 'B', 'Mỗi course_id chỉ được xuất hiện một lần.', false),
(140, 46, 'C', 'Mỗi cặp student_id và course_id chỉ được xuất hiện một lần.', true),
(141, 46, 'D', 'Hai cột luôn phải có cùng giá trị.', false),
(142, 47, 'A', 'Mọi hàng đều bắt buộc tham chiếu một hàng cha.', false),
(143, 47, 'B', 'Giá trị NULL có thể được lưu mà không cần hàng cha tương ứng.', true),
(144, 47, 'C', 'Cột này tự động là khóa chính.', false),
(145, 47, 'D', 'Các giá trị khác NULL được phép tham chiếu mã không tồn tại.', false),
(146, 48, 'A', 'Thứ tự chữ cái của tên cột.', false),
(147, 48, 'B', 'Thứ tự cột trong danh sách name, age.', true),
(148, 48, 'C', 'Thứ tự tạo chỉ mục.', false),
(149, 48, 'D', 'PostgreSQL tự đoán theo nội dung.', false),
(150, 49, 'A', 'Chỉ cập nhật hàng đầu tiên.', false),
(151, 49, 'B', 'Chỉ cập nhật hàng có price NULL.', false),
(152, 49, 'C', 'Cập nhật price của tất cả các hàng.', true),
(153, 49, 'D', 'Xóa toàn bộ bảng.', false),
(154, 50, 'A', 'Xóa tất cả các hàng của students.', true),
(155, 50, 'B', 'Giữ lại định nghĩa bảng students.', true),
(156, 50, 'C', 'Xóa luôn định nghĩa bảng students.', false),
(157, 50, 'D', 'Chỉ xóa các hàng có NULL.', false),
(158, 51, 'A', 'Phụ thuộc bộ phận của thuộc tính không khóa vào một phần khóa, vi phạm 2NF.', true),
(159, 51, 'B', 'Khóa chính bị thiếu cột grade.', false),
(160, 51, 'C', 'Bảng chắc chắn đã đạt BCNF.', false),
(161, 51, 'D', 'Đây là phụ thuộc đa trị duy nhất có thể có.', false),
(162, 52, 'A', 'dept_name phụ thuộc bắc cầu vào khóa qua dept_id.', true),
(163, 52, 'B', 'Mọi cột TEXT đều vi phạm 3NF.', false),
(164, 52, 'C', 'Bảng có hơn hai cột.', false),
(165, 52, 'D', 'Mọi khóa ngoại đều vi phạm 3NF.', false),
(166, 53, 'A', 'B → A hoặc B → C được suy ra từ tập phụ thuộc hàm.', true),
(167, 53, 'B', 'A và C có cùng kiểu dữ liệu.', false),
(168, 53, 'C', 'R1 và R2 có cùng số hàng ở một thời điểm.', false),
(169, 53, 'D', 'Hai bảng đều không có NULL.', false),
(170, 54, 'A', 'Giữ lại tất cả thay đổi.', false),
(171, 54, 'B', 'Hủy các thay đổi dữ liệu chưa được commit của giao dịch.', true),
(172, 54, 'C', 'Chỉ hủy câu SELECT gần nhất.', false),
(173, 54, 'D', 'Xóa luôn cơ sở dữ liệu.', false),
(174, 55, 'A', 'Dirty read.', false),
(175, 55, 'B', 'Non-repeatable read.', true),
(176, 55, 'C', 'Mất khóa chính.', false),
(177, 55, 'D', 'Phụ thuộc hàm.', false),
(178, 56, 'A', 'Tự chọn hàng đầu tiên.', false),
(179, 56, 'B', 'Ghép hai hàng thành chuỗi.', false),
(180, 56, 'C', 'Báo lỗi vì truy vấn con vô hướng trả về nhiều hơn một hàng.', true),
(181, 56, 'D', 'Tự lấy trung bình.', false),
(182, 57, 'A', 'Tổng giá trị các đơn hàng.', false),
(183, 57, 'B', 'Có ít nhất một hàng thỏa customer_id = 5 hay không.', true),
(184, 57, 'C', 'Mọi đơn hàng đều thuộc khách hàng 5.', false),
(185, 57, 'D', 'Khách hàng 5 có đúng một đơn hàng.', false),
(186, 58, 'A', 'Có tham chiếu đến cột của truy vấn bên ngoài.', true),
(187, 58, 'B', 'Luôn có ORDER BY.', false),
(188, 58, 'C', 'Không được có WHERE.', false),
(189, 58, 'D', 'Luôn trả về toàn bộ bảng.', false),
(190, 59, 'A', 'Có thể giữ nguyên từng hàng đầu vào.', true),
(191, 59, 'B', 'Tính tổng trong từng nhóm customer_id mà không gộp các hàng thành một hàng.', true),
(192, 59, 'C', 'Bắt buộc làm giảm số hàng như GROUP BY.', false),
(193, 59, 'D', 'Tự sửa amount trong bảng.', false),
(194, 60, 'A', '1, 2, 3.', false),
(195, 60, 'B', '1, 1, 2.', false),
(196, 60, 'C', '1, 1, 3.', true),
(197, 60, 'D', '0, 0, 1.', false),
(198, 61, 'A', '1, 1, 2.', true),
(199, 61, 'B', '1, 1, 3.', false),
(200, 61, 'C', '1, 2, 3.', false),
(201, 61, 'D', '0, 1, 2.', false),
(202, 62, 'A', 'SUM(amount) OVER (ORDER BY id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW).', true),
(203, 62, 'B', 'SUM(amount) OVER ().', false),
(204, 62, 'C', 'COUNT(amount) GROUP BY id.', false),
(205, 62, 'D', 'SUM(amount) WHERE id IS NOT NULL.', false),
(206, 63, 'A', 'Frame mặc định bao gồm các hàng đồng hạng theo sale_date đến hàng hiện tại.', true),
(207, 63, 'B', 'Luôn chỉ cộng đúng một hàng vật lý.', false),
(208, 63, 'C', 'Luôn tương đương ROWS BETWEEN 1 PRECEDING AND CURRENT ROW.', false),
(209, 63, 'D', 'Không được phép có ngày trùng.', false),
(210, 64, 'A', 'ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING.', true),
(211, 64, 'B', 'ROWS BETWEEN CURRENT ROW AND CURRENT ROW.', false),
(212, 64, 'C', 'ROWS BETWEEN 1 PRECEDING AND CURRENT ROW.', false),
(213, 64, 'D', 'Không có frame nào thực hiện được.', false),
(214, 65, 'A', 'WHERE n < 10 trong nhánh sinh n + 1.', true),
(215, 65, 'B', 'ORDER BY n trong SELECT ngoài.', false),
(216, 65, 'C', 'Đổi tên CTE thành numbers.', false),
(217, 65, 'D', 'Thêm một cột TEXT bất kỳ.', false),
(218, 66, 'A', 'UNION loại các hàng trùng theo toàn bộ cột kết quả, còn UNION ALL giữ chúng.', true),
(219, 66, 'B', 'UNION ALL tự phát hiện mọi chu trình đồ thị.', false),
(220, 66, 'C', 'UNION luôn bảo đảm kết thúc kể cả khi mỗi vòng sinh một giá trị mới.', false),
(221, 66, 'D', 'UNION ALL không cho phép đệ quy.', false),
(222, 67, 'A', 'WHERE customer_id = 10 ORDER BY created_at.', true),
(223, 67, 'B', 'WHERE LOWER(note) = ''x''.', false),
(224, 67, 'C', 'WHERE random() > 0.5.', false),
(225, 67, 'D', 'SELECT mọi hàng và sắp xếp theo cột không liên quan.', false),
(226, 68, 'A', 'Thực sự chạy câu lệnh để thu thập số liệu thực tế.', true),
(227, 68, 'B', 'Có thể so sánh số hàng ước lượng và thực tế để tìm điểm sai lệch.', true),
(228, 68, 'C', 'Chỉ phân tích cú pháp và tuyệt đối không thực thi.', false),
(229, 68, 'D', 'Tự tạo tất cả chỉ mục còn thiếu.', false),
(230, 69, 'A', 'created_at >= TIMESTAMP ''2026-10-01 00:00:00'' AND created_at < TIMESTAMP ''2026-10-02 00:00:00''.', true),
(231, 69, 'B', 'TO_CHAR(created_at, ''YYYY-MM-DD'') = ''2026-10-01''.', false),
(232, 69, 'C', 'EXTRACT(DAY FROM created_at) = 1, không giới hạn tháng và năm.', false),
(233, 69, 'D', 'CAST(created_at AS TEXT) LIKE ''2026-10-01%''.', false);

-- sql_test_dataset: 24 rows
INSERT INTO "sql_test_dataset" ("dataset_id", "question_id", "dataset_name", "setup_sql", "expected_result", "is_edge_case") OVERRIDING SYSTEM VALUE VALUES
(1, 13, 'dataset_1', 'CREATE TABLE "sinh_vien" (
  "ma_sv" INTEGER,
  "ho_ten" TEXT,
  "diem" INTEGER
);

INSERT INTO "sinh_vien" VALUES
  (1, ''An'', 9),
  (2, ''Bình'', 6),
  (3, ''Chi'', 8);', '{"rows": [[1, "An", 9], [3, "Chi", 8]], "columns": ["ma_sv", "ho_ten", "diem"], "ordered": false, "check_columns": false}'::jsonb, false),
(2, 14, 'dataset_1', 'CREATE TABLE "lop" (
  "ma_lop" INTEGER,
  "ten_lop" TEXT
);

INSERT INTO "lop" VALUES
  (10, ''CNTT1''),
  (20, ''CNTT2'');

CREATE TABLE "sinh_vien" (
  "ma_sv" INTEGER,
  "ho_ten" TEXT,
  "ma_lop" INTEGER
);

INSERT INTO "sinh_vien" VALUES
  (1, ''An'', 10),
  (2, ''Bình'', 20),
  (3, ''Chi'', 10);',  E'{"rows": [["Chi", "CNTT1"], ["An", "CNTT1"], ["B\\u00ecnh", "CNTT2"]], "columns": ["ho_ten", "ten_lop"], "ordered": false, "check_columns": false}'::jsonb, false),
(3, 15, 'dataset_1', 'CREATE TABLE "sinh_vien" (
  "ma_sv" INTEGER,
  "ma_lop" INTEGER
);

INSERT INTO "sinh_vien" VALUES
  (1, 10),
  (2, 10),
  (3, 20),
  (4, 30),
  (5, 30),
  (6, 30);', '{"rows": [[30, 3], [10, 2]], "columns": ["ma_lop", "so_sinh_vien"], "ordered": false, "check_columns": false}'::jsonb, false),
(4, 16, 'dataset_1', 'CREATE TABLE "sinh_vien" (
  "ma_sv" INTEGER,
  "ho_ten" TEXT,
  "ma_lop" INTEGER,
  "diem" INTEGER
);

INSERT INTO "sinh_vien" VALUES
  (1, ''An'', 10, 9),
  (2, ''Bình'', 10, 5),
  (3, ''Chi'', 20, 8),
  (4, ''Dũng'', 20, 6);', '{"rows": [[1, "An", 9], [3, "Chi", 8]], "columns": ["ma_sv", "ho_ten", "diem"], "ordered": false, "check_columns": false}'::jsonb, false),
(5, 17, 'dataset_1', 'CREATE TABLE "doanh_thu" (
  "ngay" DATE,
  "so_tien" INTEGER
);

INSERT INTO "doanh_thu" VALUES
  (''2026-10-01'', 100),
  (''2026-10-02'', 200),
  (''2026-10-03'', 150),
  (''2026-10-04'', 50);', '{"rows": [["2026-10-01", 100, 100], ["2026-10-02", 200, 300], ["2026-10-03", 150, 450], ["2026-10-04", 50, 500]], "columns": ["ngay", "so_tien", "tong_luy_ke"], "ordered": false, "check_columns": false}'::jsonb, false),
(6, 26, 'dataset_1', 'CREATE TABLE "students" (
  "id" INTEGER,
  "name" TEXT,
  "score" INTEGER
);

INSERT INTO "students" VALUES
  (1, ''An'', 9),
  (2, ''Bình'', 6),
  (3, ''Chi'', 8);', '{"rows": [["An", 9], ["Chi", 8]], "columns": ["name", "score"], "ordered": false, "check_columns": false}'::jsonb, false),
(7, 27, 'dataset_1', 'CREATE TABLE "students" (
  "id" INTEGER,
  "class_id" TEXT
);

INSERT INTO "students" VALUES
  (1, ''A''),
  (2, ''A''),
  (3, ''B''),
  (4, ''C''),
  (5, ''C''),
  (6, ''C'');', '{"rows": [["C", 3], ["A", 2]], "columns": ["class_id", "total_students"], "ordered": false, "check_columns": false}'::jsonb, false),
(8, 38, 'dataset_1', 'CREATE TABLE student_import (student_id INTEGER, name TEXT); INSERT INTO student_import VALUES (1,''An''),(2,''Binh''),(2,''Chi''),(3,''Dung''),(3,''Ha''),(3,''Lan'');', '{"rows": [[2, 2], [3, 3]], "columns": ["student_id", "occurrences"], "ordered": false, "check_columns": false}'::jsonb, false),
(9, 39, 'dataset_1', 'CREATE TABLE classes (id INTEGER, class_name TEXT); INSERT INTO classes VALUES (1,''CSDL A''),(2,''CSDL B''); CREATE TABLE student_import (student_id INTEGER, name TEXT, class_id INTEGER); INSERT INTO student_import VALUES (1,''An'',1),(2,''Binh'',9),(3,''Chi'',2),(4,''Dung'',8);', '{"rows": [[2, "Binh", 9], [4, "Dung", 8]], "columns": ["student_id", "name", "class_id"], "ordered": false, "check_columns": false}'::jsonb, false),
(10, 70, 'dataset_1', 'CREATE TABLE students (id INTEGER, name TEXT, class_id TEXT, score INTEGER); INSERT INTO students VALUES (1,''An'',''A'',9),(2,''Binh'',''A'',6),(3,''Chi'',''B'',8),(4,''Dung'',''B'',NULL),(5,''Ha'',''C'',9);', '{"rows": [[1, "An"], [5, "Ha"]], "columns": ["id", "name"], "ordered": false, "check_columns": false}'::jsonb, false),
(11, 71, 'dataset_1', 'CREATE TABLE students (id INTEGER, name TEXT, class_id TEXT, score INTEGER); INSERT INTO students VALUES (1,''An'',''A'',9),(2,''Binh'',''A'',6),(3,''Chi'',''B'',8),(4,''Dung'',''B'',NULL),(5,''Ha'',''C'',9);', '{"rows": [[4, "Dung"]], "columns": ["id", "name"], "ordered": false, "check_columns": false}'::jsonb, false),
(12, 72, 'dataset_1', 'CREATE TABLE students (id INTEGER, name TEXT, class_id TEXT, score INTEGER); INSERT INTO students VALUES (1,''An'',''A'',9),(2,''Binh'',''A'',6),(3,''Chi'',''B'',8),(4,''Dung'',''B'',NULL),(5,''Ha'',''C'',9);', '{"rows": [["A", 2], ["B", 2], ["C", 1]], "columns": ["class_id", "student_count"], "ordered": false, "check_columns": false}'::jsonb, false),
(13, 73, 'dataset_1', 'CREATE TABLE students (id INTEGER, name TEXT, class_id TEXT, score INTEGER); INSERT INTO students VALUES (1,''An'',''A'',9),(2,''Binh'',''A'',6),(3,''Chi'',''B'',8),(4,''Dung'',''B'',NULL),(5,''Ha'',''C'',9);', '{"rows": [["B", 8], ["C", 9]], "columns": ["class_id", "average_score"], "ordered": false, "check_columns": false}'::jsonb, false),
(14, 74, 'dataset_1', 'CREATE TABLE students (id INTEGER, name TEXT, class_id TEXT, score INTEGER); INSERT INTO students VALUES (1,''An'',''A'',9),(2,''Binh'',''A'',6),(3,''Chi'',''B'',8),(4,''Dung'',''B'',NULL),(5,''Ha'',''C'',9);CREATE TABLE classes (id TEXT, name TEXT); INSERT INTO classes VALUES (''A'',''Data Basics''),(''B'',''SQL''),(''C'',''Advanced'');', '{"rows": [[1, "An", "Data Basics"], [2, "Binh", "Data Basics"], [3, "Chi", "SQL"], [4, "Dung", "SQL"], [5, "Ha", "Advanced"]], "columns": ["student_id", "student_name", "class_name"], "ordered": false, "check_columns": false}'::jsonb, false),
(15, 75, 'dataset_1', 'CREATE TABLE students (id INTEGER, name TEXT, class_id TEXT, score INTEGER); INSERT INTO students VALUES (1,''An'',''A'',9),(2,''Binh'',''A'',6),(3,''Chi'',''B'',8),(4,''Dung'',''B'',NULL),(5,''Ha'',''C'',9);', '{"rows": [[1, "An", 9], [5, "Ha", 9]], "columns": ["id", "name", "score"], "ordered": false, "check_columns": false}'::jsonb, false),
(16, 76, 'dataset_1', 'CREATE TABLE students (id INTEGER, name TEXT, class_id TEXT, score INTEGER); INSERT INTO students VALUES (1,''An'',''A'',9),(2,''Binh'',''A'',6),(3,''Chi'',''B'',8),(4,''Dung'',''B'',NULL),(5,''Ha'',''C'',9);', '{"rows": [[1, "An", 9]], "columns": ["id", "name", "score"], "ordered": false, "check_columns": false}'::jsonb, false),
(17, 77, 'dataset_1', 'CREATE TABLE students (id INTEGER, name TEXT, class_id TEXT, score INTEGER); INSERT INTO students VALUES (1,''An'',''A'',9),(2,''Binh'',''A'',6),(3,''Chi'',''B'',8),(4,''Dung'',''B'',NULL),(5,''Ha'',''C'',9);', '{"rows": [[1, 1], [5, 1], [3, 2], [2, 3]], "columns": ["id", "score_rank"], "ordered": false, "check_columns": false}'::jsonb, false),
(18, 78, 'dataset_1', 'CREATE TABLE sales (day_no INTEGER, amount INTEGER); INSERT INTO sales VALUES (1,100),(2,200),(3,50);', '{"rows": [[1, 100], [2, 300], [3, 350]], "columns": ["day_no", "running_total"], "ordered": false, "check_columns": false}'::jsonb, false),
(19, 79, 'dataset_1', 'CREATE TABLE sales (day_no INTEGER, amount INTEGER); INSERT INTO sales VALUES (1,100),(2,200),(3,50);', '{"rows": [[1, 100], [2, 150], [3, 125]], "columns": ["day_no", "moving_average"], "ordered": false, "check_columns": false}'::jsonb, false),
(20, 80, 'dataset_1', 'CREATE TABLE employees (id INTEGER, name TEXT, manager_id INTEGER); INSERT INTO employees VALUES (1,''CEO'',NULL),(2,''Manager'',1),(3,''Developer'',2),(4,''Analyst'',1);', '{"rows": [[1, 0], [2, 1], [3, 2], [4, 1]], "columns": ["id", "depth"], "ordered": false, "check_columns": false}'::jsonb, false),
(21, 81, 'dataset_1', 'CREATE TABLE students (id INTEGER, name TEXT, class_id TEXT, score INTEGER); INSERT INTO students VALUES (1,''An'',''A'',9),(2,''Binh'',''A'',6),(3,''Chi'',''B'',8),(4,''Dung'',''B'',NULL),(5,''Ha'',''C'',9);', '{"rows": [["A", 1, "An", 9], ["B", 3, "Chi", 8], ["C", 5, "Ha", 9]], "columns": ["class_id", "id", "name", "score"], "ordered": false, "check_columns": false}'::jsonb, false),
(23, 91, 'dataset_1', 'CREATE TABLE "sinh_vien" (
  "ma_sv" INTEGER,
  "ho_ten" TEXT,
  "ma_lop" INTEGER,
  "diem" INTEGER
);

INSERT INTO "sinh_vien" VALUES
  (1, ''An'', 10, 9),
  (2, ''Bình'', 10, 5),
  (3, ''Chi'', 20, 8),
  (4, ''Dũng'', 20, 6);', '{"rows": [[1, "An", 9], [3, "Chi", 8]], "columns": ["ma_sv", "ho_ten", "diem"], "ordered": false, "check_columns": false}'::jsonb, false),
(24, 92, 'dataset_1', 'CREATE TABLE students (id INTEGER, name TEXT, class_id TEXT, score INTEGER); INSERT INTO students VALUES (1,''An'',''A'',9),(2,''Binh'',''A'',6),(3,''Chi'',''B'',8),(4,''Dung'',''B'',NULL),(5,''Ha'',''C'',9);', '{"rows": [["B", 8], ["C", 9]], "columns": ["class_id", "average_score"], "ordered": false, "check_columns": false}'::jsonb, false),
(25, 93, 'dataset_1', 'CREATE TABLE students (id INTEGER, name TEXT, class_id TEXT, score INTEGER); INSERT INTO students VALUES (1,''An'',''A'',9),(2,''Binh'',''A'',6),(3,''Chi'',''B'',8),(4,''Dung'',''B'',NULL),(5,''Ha'',''C'',9);CREATE TABLE classes (id TEXT, name TEXT); INSERT INTO classes VALUES (''A'',''Data Basics''),(''B'',''SQL''),(''C'',''Advanced'');', '{"rows": [[1, "An", "Data Basics"], [2, "Binh", "Data Basics"], [3, "Chi", "SQL"], [4, "Dung", "SQL"], [5, "Ha", "Advanced"]], "columns": ["student_id", "student_name", "class_name"], "ordered": false, "check_columns": false}'::jsonb, false);

-- rubric: 48 rows
INSERT INTO "rubric" ("rubric_id", "question_id", "level_name", "min_score", "max_score", "criteria") OVERRIDING SYSTEM VALUE VALUES
(5, 19, 'Incomplete', 0.00, 0.49, 'Không phân biệt được WHERE và HAVING hoặc trình bày sai cơ bản cách lọc hàng và lọc nhóm.'),
(6, 19, 'Partial', 0.50, 0.99, 'Giải thích đúng một phần vai trò của WHERE hoặc HAVING nhưng chưa kết hợp đúng các bước lọc sinh viên, nhóm theo lớp và đếm sinh viên.'),
(7, 19, 'Mostly Complete', 1.00, 1.49, 'Phân biệt đúng WHERE và HAVING, đề xuất đúng hướng xử lý nhưng còn thiếu hoặc sai một chi tiết về ngưỡng điểm, điều kiện số lượng hay nhóm theo mã lớp.'),
(8, 19, 'Complete', 1.50, 2.00, 'Giải thích đúng WHERE lọc hàng trước khi nhóm và HAVING lọc nhóm sau tổng hợp. Trình bày đúng WHERE diem >= 5, GROUP BY ma_lop và HAVING COUNT(*) >= 10 bằng lời hoặc SQL tương đương.'),
(9, 20, 'Incomplete', 0.00, 0.49, 'Không giải thích được nhu cầu sử dụng giao dịch hoặc cho rằng nên xác nhận thao tác trừ tiền dù thao tác cộng tiền đã thất bại.'),
(10, 20, 'Partial', 0.50, 0.99, 'Nhận biết nguy cơ trừ tiền mà không cộng tiền hoặc nhắc đến hoàn tác nhưng giải thích chưa đúng hoặc chưa rõ tính nguyên tử, COMMIT và ROLLBACK.'),
(11, 20, 'Mostly Complete', 1.00, 1.49, 'Giải thích đúng cần thực hiện hai thao tác trong cùng giao dịch và dùng ROLLBACK khi thất bại, nhưng còn thiếu vai trò của COMMIT hoặc phạm vi hoàn tác.'),
(12, 20, 'Complete', 1.50, 2.00, 'Giải thích đầy đủ nguy cơ mất nhất quán, tính nguyên tử là tất cả thành công hoặc hủy toàn bộ thay đổi, COMMIT khi giao dịch thành công và ROLLBACK hoàn tác thao tác trừ tiền nếu cộng tiền thất bại trước COMMIT.'),
(13, 18, 'Incomplete', 0.00, 0.49, 'Không nêu được vai trò đúng của hai loại khóa hoặc nhầm lẫn cơ bản giữa khóa chính và khóa ngoại.'),
(14, 18, 'Partial', 0.50, 0.99, 'Giải thích đúng vai trò của một loại khóa; loại còn lại còn sai hoặc thiếu. Chưa có ví dụ liên kết đúng giữa hai bảng.'),
(15, 18, 'Mostly Complete', 1.00, 1.49, 'Phân biệt đúng vai trò của hai loại khóa nhưng còn thiếu điều kiện của khóa chính, ý nghĩa toàn vẹn tham chiếu hoặc ví dụ chưa đầy đủ.'),
(16, 18, 'Complete', 1.50, 2.00, 'Giải thích đúng khóa chính xác định duy nhất mỗi hàng, không trùng và không NULL; khóa ngoại tham chiếu khóa phù hợp và bảo đảm toàn vẹn tham chiếu. Có ví dụ đúng về lop.ma_lop và sinh_vien.ma_lop, diễn đạt rõ mối liên kết.'),
(17, 28, 'Incomplete', 0.00, 0.24, 'Không trả lời hoặc giải thích sai chức năng của cả WHERE và HAVING'),
(18, 28, 'Partial', 0.25, 0.49, 'Giải thích đúng một mệnh đề, nhưng chưa phân biệt được WHERE lọc hàng trước khi nhóm và HAVING lọc nhóm sau khi nhóm'),
(19, 28, 'Mostly Complete', 0.50, 0.74, 'Phân biệt đúng chức năng và thời điểm lọc của cả hai mệnh đề, nhưng thiếu hoặc sai ví dụ SQL của ít nhất một mệnh đề'),
(20, 28, 'Complete', 0.75, 1.00, 'Nêu đúng WHERE lọc từng hàng trước khi nhóm, HAVING lọc các nhóm sau khi nhóm; có ví dụ SQL đúng cho từng mệnh đề. Ví dụ khác đáp án tham khảo vẫn được chấp nhận nếu đúng'),
(21, 82, 'Incomplete', 0.00, 0.49, 'Không trả lời hoặc trả lời sai nội dung cốt lõi của đề bài.'),
(22, 82, 'Partial', 0.50, 0.99, 'Nêu đúng một ràng buộc khóa nhưng chưa giải quyết đồng thời đăng ký trùng và liên kết hợp lệ.'),
(23, 82, 'Mostly Complete', 1.00, 1.49, 'Nêu đúng cách chống trùng và khóa ngoại, nhưng thiếu giải thích hoặc thiếu điều kiện NOT NULL khi bắt buộc đăng ký phải có sinh viên và học phần.'),
(24, 82, 'Complete', 1.50, 2.00, 'Đề xuất khóa ghép hoặc khóa thay thế kèm UNIQUE cho cặp sinh viên–học phần; khóa ngoại hợp lệ, NOT NULL phù hợp; giải thích rõ vai trò từng ràng buộc.'),
(25, 83, 'Incomplete', 0.00, 0.49, 'Không trả lời hoặc trả lời sai nội dung cốt lõi của đề bài.'),
(26, 83, 'Partial', 0.50, 0.99, 'Nhận ra dữ liệu phòng bị lặp nhưng chưa đưa được cách tách phù hợp.'),
(27, 83, 'Mostly Complete', 1.00, 1.49, 'Tách đúng hai bảng và nhận diện phụ thuộc bắc cầu nhưng thiếu khóa hoặc giải thích bất thường.'),
(28, 83, 'Complete', 1.50, 2.00, 'Nêu phụ thuộc và ít nhất một bất thường cụ thể; tách đúng hai bảng, chỉ rõ khóa chính, khóa ngoại và khả năng nối khôi phục dữ liệu.'),
(29, 84, 'Incomplete', 0.00, 0.49, 'Không trả lời hoặc trả lời sai nội dung cốt lõi của đề bài.'),
(30, 84, 'Partial', 0.50, 0.99, 'Nêu giao dịch hoặc hoàn tác nhưng chưa giải thích vì sao hai bước cần được gắn liền.'),
(31, 84, 'Mostly Complete', 1.00, 1.49, 'Mô tả đúng BEGIN/COMMIT/ROLLBACK và tính nguyên tử nhưng chưa nêu kiểm tra số dư hay vấn đề đồng thời.'),
(32, 84, 'Complete', 1.50, 2.00, 'Giải thích tính nguyên tử, ranh giới giao dịch và rollback toàn bộ khi lỗi; đề cập kiểm tra số dư và cơ chế xử lý đồng thời phù hợp.'),
(33, 85, 'Incomplete', 0.00, 0.49, 'Không trả lời hoặc trả lời sai nội dung cốt lõi của đề bài.'),
(34, 85, 'Partial', 0.50, 0.99, 'Giải thích đúng một loại truy vấn con nhưng chưa phân biệt bằng tham chiếu cột.'),
(35, 85, 'Mostly Complete', 1.00, 1.49, 'Phân biệt đúng hai loại và ý nghĩa hai yêu cầu, nhưng thiếu hoặc sai một ví dụ.'),
(36, 85, 'Complete', 1.50, 2.00, 'Phân biệt đúng tham chiếu bên ngoài; đưa hai ví dụ đúng cho trung bình công ty và trung bình từng phòng, chấp nhận cách viết SQL tương đương.'),
(37, 86, 'Incomplete', 0.00, 0.49, 'Không trả lời hoặc trả lời sai nội dung cốt lõi của đề bài.'),
(38, 86, 'Partial', 0.50, 0.99, 'Nhận biết có thể tổng hợp nhưng chưa giải thích khác biệt về số hàng kết quả.'),
(39, 86, 'Mostly Complete', 1.00, 1.49, 'So sánh đúng việc gộp hàng và giữ chi tiết, nhưng chỉ minh họa được tổng lương hoặc xếp hạng.'),
(40, 86, 'Complete', 1.50, 2.00, 'So sánh đúng; đưa cách tính tổng theo phòng và xếp hạng theo phòng bằng cửa sổ, giải thích phân vùng và quy tắc hòa hạng.'),
(41, 87, 'Incomplete', 0.00, 0.49, 'Không trả lời hoặc trả lời sai nội dung cốt lõi của đề bài.'),
(42, 87, 'Partial', 0.50, 0.99, 'Nêu được lợi ích hoặc chi phí đơn lẻ nhưng kết luận chưa có căn cứ.'),
(43, 87, 'Mostly Complete', 1.00, 1.49, 'Nêu đúng lợi ích, dung lượng và chi phí ghi nhưng thiếu cách chọn hoặc kiểm chứng chỉ mục.'),
(44, 87, 'Complete', 1.50, 2.00, 'Phân tích cân bằng lợi ích và chi phí; chọn theo truy vấn, độ chọn lọc và thứ tự cột; nêu đo kế hoạch hoặc thời gian thực tế để xác nhận.'),
(45, 88, 'Incomplete', 0.00, 0.49, 'Không trả lời hoặc trả lời sai nội dung cốt lõi của đề bài.'),
(46, 88, 'Partial', 0.50, 0.99, 'Chỉ đề xuất thêm chỉ mục hoặc sửa truy vấn mà chưa đọc hay kiểm chứng kế hoạch.'),
(47, 88, 'Mostly Complete', 1.00, 1.49, 'Nhận diện sai lệch ước lượng và đề xuất cải thiện hợp lý nhưng thiếu đo trước/sau hoặc kiểm tra kết quả.'),
(48, 88, 'Complete', 1.50, 2.00, 'Đọc đúng estimated/actual rows và loops; phân tích thống kê, điều kiện và kế hoạch JOIN; đề xuất thay đổi có căn cứ và đo trước/sau, giữ tương đương kết quả.'),
(49, 89, 'Incomplete', 0.00, 0.49, 'Không trả lời hoặc trả lời sai nội dung cốt lõi của đề bài.'),
(50, 89, 'Partial', 0.50, 0.99, 'Nhận ra nguy cơ lặp nhưng chưa nêu được biện pháp khả thi.'),
(51, 89, 'Mostly Complete', 1.00, 1.49, 'Nêu đúng một cách chống lặp nhưng chưa giải thích giới hạn của UNION hay giới hạn độ sâu.'),
(52, 89, 'Complete', 1.50, 2.00, 'Giải thích nguy cơ chu trình, đưa biện pháp đường đi/CYCLE phù hợp, chỉ rõ UNION so sánh toàn bộ cột và không bảo đảm dừng khi depth/path thay đổi.');

-- question_translation: 90 rows
INSERT INTO "question_translation" ("question_id", "locale", "source_hash", "prompt", "explanation", "option_texts", "rubrics")  VALUES
(1, 'vi', '293a4451206cf0eae75d88e745d3e19a7df113e446c1064489e8d6859726985f', 'Câu lệnh nào lấy toàn bộ các cột trong bảng sinh_vien?', NULL, '{"A": "SELECT * FROM sinh_vien;", "B": "SELECT sinh_vien FROM *;", "C": "GET ALL FROM sinh_vien;", "D": "SHOW ROWS sinh_vien;"}'::jsonb, '{}'::jsonb),
(2, 'vi', '6409d3e07a9a9aaacba47aeced7b8cac972940f069fee7b94b16a3c5bc1c1a0a', 'Đề bài: Bảng sinh_vien có cột diem. Câu lệnh nào lấy những sinh viên có điểm từ 8 trở lên?', NULL, '{"A": "SELECT * FROM sinh_vien WHERE diem > 8;", "B": "SELECT * FROM sinh_vien WHERE diem >= 8;", "C": "SELECT * FROM sinh_vien WHERE diem < 8;", "D": "SELECT * FROM sinh_vien ORDER BY diem;"}'::jsonb, '{}'::jsonb),
(3, 'vi', '83d18b69a094ce80964e14ee00138ba5f8fb1f96024ab9b0de4dbe824ae405f1', 'Muốn lấy tất cả sinh viên, kể cả người chưa được xếp lớp, khi nối bảng sinh_vien bên trái với bảng lop bên phải, nên dùng phép nối nào?', NULL, '{"A": "INNER JOIN", "B": "CROSS JOIN", "C": "LEFT JOIN", "D": "RIGHT JOIN"}'::jsonb, '{}'::jsonb),
(4, 'vi', '9304b9fdb83680e355c17bf9f784a7289f321c77cf6915925521368f3db64b0f', 'Bảng doanh_thu có đúng một hàng cho mỗi ngày. Câu lệnh sau tính giá trị gì?
SELECT ngay, so_tien,
       SUM(so_tien) OVER (
           ORDER BY ngay
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS tong_luy_ke
FROM doanh_thu;', NULL,  E'{"A": "T\\u1ed5ng doanh thu t\\u1eeb ng\\u00e0y \\u0111\\u1ea7u ti\\u00ean \\u0111\\u1ebfn ng\\u00e0y c\\u1ee7a h\\u00e0ng hi\\u1ec7n t\\u1ea1i", "B": "Ch\\u1ec9 doanh thu c\\u1ee7a ng\\u00e0y hi\\u1ec7n t\\u1ea1i", "C": "T\\u1ed5ng doanh thu c\\u1ee7a c\\u00e1c ng\\u00e0y sau ng\\u00e0y hi\\u1ec7n t\\u1ea1i", "D": "Doanh thu l\\u1edbn nh\\u1ea5t trong to\\u00e0n b\\u1ea3ng."}'::jsonb, '{}'::jsonb),
(5, 'vi', '719ccde4e1d2086fc6653b379ed0664fd9aa1f289804709ba599f2b98986a804', 'Với ba mức điểm 10, 10, 8, những phát biểu nào đúng khi xếp theo điểm giảm dần?', NULL,  E'{"A": "RANK() t\\u1ea1o c\\u00e1c h\\u1ea1ng 1, 1, 3", "B": "DENSE_RANK() t\\u1ea1o c\\u00e1c h\\u1ea1ng 1, 1, 2", "C": "ROW_NUMBER() g\\u00e1n c\\u00f9ng m\\u1ed9t s\\u1ed1 th\\u1ee9 t\\u1ef1 cho hai h\\u00e0ng c\\u00f3 \\u0111i\\u1ec3m 10", "D": "H\\u00e0m c\\u1eeda s\\u1ed5 lu\\u00f4n g\\u1ed9p nhi\\u1ec1u h\\u00e0ng th\\u00e0nh m\\u1ed9t h\\u00e0ng nh\\u01b0 GROUP BY"}'::jsonb, '{}'::jsonb),
(8, 'vi', '8c76f1280d451c57d64eaca3e623c415f1f5f4699d7b421387b93c4dc30db724', 'Những phát biểu nào sau đây đúng về PostgreSQL? Chọn những đáp án đúng', NULL,  E'{"A": "EXPLAIN ANALYZE th\\u1ef1c s\\u1ef1 th\\u1ef1c thi c\\u00e2u l\\u1ec7nh \\u0111\\u1ec3 thu th\\u1eadp s\\u1ed1 li\\u1ec7u th\\u1ef1c t\\u1ebf", "B": "Ch\\u1ec9 m\\u1ee5c ph\\u00f9 h\\u1ee3p c\\u00f3 th\\u1ec3 gi\\u00fap t\\u0103ng t\\u1ed1c m\\u1ed9t s\\u1ed1 truy v\\u1ea5n c\\u00f3 WHERE ho\\u1eb7c JOIN", "C": "C\\u00e0ng t\\u1ea1o nhi\\u1ec1u ch\\u1ec9 m\\u1ee5c th\\u00ec m\\u1ecdi thao t\\u00e1c INSERT, UPDATE v\\u00e0 DELETE c\\u00e0ng nhanh", "D": "PostgreSQL lu\\u00f4n ph\\u1ea3i s\\u1eed d\\u1ee5ng ch\\u1ec9 m\\u1ee5c n\\u1ebfu b\\u1ea3ng c\\u00f3 ch\\u1ec9 m\\u1ee5c"}'::jsonb, '{}'::jsonb),
(9, 'vi', 'a3280a7ebda860a435551bbcd060e862113996110915093a53d91cc2498fbb73', 'Câu lệnh sau tìm những sinh viên nào?
SELECT sv.ho_ten
FROM sinh_vien sv
WHERE sv.diem > (
    SELECT AVG(sv2.diem)
    FROM sinh_vien sv2
    WHERE sv2.ma_lop = sv.ma_lop
);', NULL,  E'{"A": "Sinh vi\\u00ean c\\u00f3 \\u0111i\\u1ec3m cao h\\u01a1n trung b\\u00ecnh to\\u00e0n tr\\u01b0\\u1eddng", "B": "Sinh vi\\u00ean c\\u00f3 \\u0111i\\u1ec3m cao h\\u01a1n trung b\\u00ecnh c\\u1ee7a ch\\u00ednh l\\u1edbp m\\u00ecnh", "C": "Sinh vi\\u00ean c\\u00f3 \\u0111i\\u1ec3m th\\u1ea5p nh\\u1ea5t trong m\\u1ed7i l\\u1edbp", "D": "Sinh vi\\u00ean ch\\u01b0a \\u0111\\u01b0\\u1ee3c x\\u1ebfp l\\u1edbp"}'::jsonb, '{}'::jsonb),
(10, 'vi', 'ba66322aca81e3c0c89382725603b0ad0d7358f076c35ed9231f4630f70a688e', 'Khi thực hiện chuyển tiền giữa hai tài khoản trong một giao dịch, thao tác trừ tiền đã chạy nhưng thao tác cộng tiền bị lỗi. Cần làm gì để hủy toàn bộ thay đổi chưa được xác nhận của giao dịch đó?', NULL,  E'{"A": "Ch\\u1ea1y COMMIT", "B": "Ch\\u1ea1y ROLLBACK", "C": "Ch\\u1ea1y DELETE \\u0111\\u1ec3 x\\u00f3a hai t\\u00e0i kho\\u1ea3n", "D": "Ch\\u1ea1y SELECT \\u0111\\u1ec3 t\\u1ef1 \\u0111\\u1ed9ng ho\\u00e0n t\\u00e1c"}'::jsonb, '{}'::jsonb),
(11, 'vi', '956cc4a728d9ba0b9c8556d453b2e5140b578a32e78ed45c92f45d662cc4ef7c', 'Những phát biểu nào sau đây là đúng?', NULL,  E'{"A": "UPDATE sinh_vien SET diem = 10; c\\u1eadp nh\\u1eadt \\u0111i\\u1ec3m c\\u1ee7a t\\u1ea5t c\\u1ea3 h\\u00e0ng n\\u1ebfu kh\\u00f4ng b\\u1ecb r\\u00e0ng bu\\u1ed9c kh\\u00e1c ng\\u0103n c\\u1ea3n", "B": "DELETE FROM sinh_vien WHERE diem < 5; x\\u00f3a c\\u00e1c h\\u00e0ng c\\u00f3 \\u0111i\\u1ec3m nh\\u1ecf h\\u01a1n 5", "C": "DELETE FROM sinh_vien; x\\u00f3a c\\u1ea3 c\\u1ea5u tr\\u00fac b\\u1ea3ng", "D": "UPDATE kh\\u00f4ng c\\u00f3 WHERE ch\\u1ec9 c\\u1eadp nh\\u1eadt h\\u00e0ng \\u0111\\u1ea7u ti\\u00ean"}'::jsonb, '{}'::jsonb),
(12, 'vi', '4dc6b5bdf9ea67658b371a7c62b581faa749868c027b08241fa38a0645ea65a9', 'Câu lệnh sau dùng để làm gì?
SELECT ho_ten
FROM sinh_vien
WHERE diem > (SELECT AVG(diem) FROM sinh_vien);', NULL,  E'{"A": "T\\u00ecm sinh vi\\u00ean c\\u00f3 \\u0111i\\u1ec3m cao h\\u01a1n \\u0111i\\u1ec3m trung b\\u00ecnh c\\u1ee7a to\\u00e0n b\\u1ea3ng", "B": "T\\u00ecm sinh vi\\u00ean c\\u00f3 \\u0111i\\u1ec3m cao nh\\u1ea5t trong m\\u1ed7i l\\u1edbp", "C": "T\\u0103ng \\u0111i\\u1ec3m c\\u1ee7a t\\u1ea5t c\\u1ea3 sinh vi\\u00ean", "D": "T\\u00ecm sinh vi\\u00ean c\\u00f3 \\u0111i\\u1ec3m b\\u1eb1ng \\u0111i\\u1ec3m trung b\\u00ecnh"}'::jsonb, '{}'::jsonb),
(13, 'vi', '10dc6106369c989623012e16bc82479d0f3fb265661ec670ef78c729750f514d', 'Cho sẵn bảng sinh_vien và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Liệt kê mã, họ tên và điểm của sinh viên có điểm từ 8 trở lên', NULL, '{}'::jsonb, '{}'::jsonb),
(14, 'vi', 'd86ac0fd0ea9d12e90ea211d2271989f97f7cbb1f9e563905f2eeab48bddbd2f', 'Cho sẵn bảng lop, sinh_vien và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Liệt kê họ tên sinh viên và tên lớp tương ứng. Chỉ lấy sinh viên có lớp khớp trong bảng lop', NULL, '{}'::jsonb, '{}'::jsonb),
(15, 'vi', '7da6f2f876ced7010d6e892271aad3e0a84881b9fbab04ea683ad1004c8dbaa8', 'Cho sẵn bảng sinh_vien và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Liệt kê mã lớp và số sinh viên của những lớp có ít nhất hai sinh viên. Đặt tên cột đếm là so_sinh_vien', NULL, '{}'::jsonb, '{}'::jsonb),
(16, 'vi', 'bff8f3bb21524aa6b6030e7bb670fac71041d539aaad96e73571b9f737eb25d8', 'Liệt kê mã, họ tên và điểm của sinh viên có điểm cao hơn điểm trung bình của chính lớp mình', NULL, '{}'::jsonb, '{}'::jsonb),
(17, 'vi', '4aa0e760e8aca7d8f83be83c61aaffb1b879a9798e1d4999d4f1b47d11c67120', 'Cho sẵn bảng doanh_thu và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Bảng doanh_thu có đúng một hàng cho mỗi ngày. Liệt kê ngày, số tiền và tổng doanh thu từ ngày đầu tiên đến ngày hiện tại. Đặt tên cột tổng là tong_luy_ke', NULL, '{}'::jsonb, '{}'::jsonb),
(18, 'vi', '675d4897aae8ea53a6301a90528ffdcc4048a22bc1d875d7928229ccce95b52b', 'Phân biệt khóa chính và khóa ngoại. Cho ví dụ với hai bảng lop và sinh_vien, giải thích vai trò của mỗi loại khóa', NULL, '{}'::jsonb,  E'{"Partial": {"label": "Partial", "criteria": "Gi\\u1ea3i th\\u00edch \\u0111\\u00fang vai tr\\u00f2 c\\u1ee7a m\\u1ed9t lo\\u1ea1i kh\\u00f3a; lo\\u1ea1i c\\u00f2n l\\u1ea1i c\\u00f2n sai ho\\u1eb7c thi\\u1ebfu. Ch\\u01b0a c\\u00f3 v\\u00ed d\\u1ee5 li\\u00ean k\\u1ebft \\u0111\\u00fang gi\\u1eefa hai b\\u1ea3ng."}, "Complete": {"label": "Complete", "criteria": "Gi\\u1ea3i th\\u00edch \\u0111\\u00fang kh\\u00f3a ch\\u00ednh x\\u00e1c \\u0111\\u1ecbnh duy nh\\u1ea5t m\\u1ed7i h\\u00e0ng, kh\\u00f4ng tr\\u00f9ng v\\u00e0 kh\\u00f4ng NULL; kh\\u00f3a ngo\\u1ea1i tham chi\\u1ebfu kh\\u00f3a ph\\u00f9 h\\u1ee3p v\\u00e0 b\\u1ea3o \\u0111\\u1ea3m to\\u00e0n v\\u1eb9n tham chi\\u1ebfu. C\\u00f3 v\\u00ed d\\u1ee5 \\u0111\\u00fang v\\u1ec1 lop.ma_lop v\\u00e0 sinh_vien.ma_lop, di\\u1ec5n \\u0111\\u1ea1t r\\u00f5 m\\u1ed1i li\\u00ean k\\u1ebft."}, "Incomplete": {"label": "Incomplete", "criteria": "Kh\\u00f4ng n\\u00eau \\u0111\\u01b0\\u1ee3c vai tr\\u00f2 \\u0111\\u00fang c\\u1ee7a hai lo\\u1ea1i kh\\u00f3a ho\\u1eb7c nh\\u1ea7m l\\u1eabn c\\u01a1 b\\u1ea3n gi\\u1eefa kh\\u00f3a ch\\u00ednh v\\u00e0 kh\\u00f3a ngo\\u1ea1i."}, "Mostly Complete": {"label": "Mostly Complete", "criteria": "Ph\\u00e2n bi\\u1ec7t \\u0111\\u00fang vai tr\\u00f2 c\\u1ee7a hai lo\\u1ea1i kh\\u00f3a nh\\u01b0ng c\\u00f2n thi\\u1ebfu \\u0111i\\u1ec1u ki\\u1ec7n c\\u1ee7a kh\\u00f3a ch\\u00ednh, \\u00fd ngh\\u0129a to\\u00e0n v\\u1eb9n tham chi\\u1ebfu ho\\u1eb7c v\\u00ed d\\u1ee5 ch\\u01b0a \\u0111\\u1ea7y \\u0111\\u1ee7."}}'::jsonb),
(19, 'vi', 'fb4e8f073b9e91cfa5b8386fb85800bb2e03db7a5509edb94a574fe028724c80', 'Phân biệt WHERE và HAVING. Với bảng sinh_vien(ma_sv, ma_lop, diem), hãy trình bày cách tìm các lớp có ít nhất 10 sinh viên đạt điểm từ 5 trở lên', NULL, '{}'::jsonb,  E'{"Partial": {"label": "Partial", "criteria": "Gi\\u1ea3i th\\u00edch \\u0111\\u00fang m\\u1ed9t ph\\u1ea7n vai tr\\u00f2 c\\u1ee7a WHERE ho\\u1eb7c HAVING nh\\u01b0ng ch\\u01b0a k\\u1ebft h\\u1ee3p \\u0111\\u00fang c\\u00e1c b\\u01b0\\u1edbc l\\u1ecdc sinh vi\\u00ean, nh\\u00f3m theo l\\u1edbp v\\u00e0 \\u0111\\u1ebfm sinh vi\\u00ean."}, "Complete": {"label": "Complete", "criteria": "Gi\\u1ea3i th\\u00edch \\u0111\\u00fang WHERE l\\u1ecdc h\\u00e0ng tr\\u01b0\\u1edbc khi nh\\u00f3m v\\u00e0 HAVING l\\u1ecdc nh\\u00f3m sau t\\u1ed5ng h\\u1ee3p. Tr\\u00ecnh b\\u00e0y \\u0111\\u00fang WHERE diem >= 5, GROUP BY ma_lop v\\u00e0 HAVING COUNT(*) >= 10 b\\u1eb1ng l\\u1eddi ho\\u1eb7c SQL t\\u01b0\\u01a1ng \\u0111\\u01b0\\u01a1ng."}, "Incomplete": {"label": "Incomplete", "criteria": "Kh\\u00f4ng ph\\u00e2n bi\\u1ec7t \\u0111\\u01b0\\u1ee3c WHERE v\\u00e0 HAVING ho\\u1eb7c tr\\u00ecnh b\\u00e0y sai c\\u01a1 b\\u1ea3n c\\u00e1ch l\\u1ecdc h\\u00e0ng v\\u00e0 l\\u1ecdc nh\\u00f3m."}, "Mostly Complete": {"label": "Mostly Complete", "criteria": "Ph\\u00e2n bi\\u1ec7t \\u0111\\u00fang WHERE v\\u00e0 HAVING, \\u0111\\u1ec1 xu\\u1ea5t \\u0111\\u00fang h\\u01b0\\u1edbng x\\u1eed l\\u00fd nh\\u01b0ng c\\u00f2n thi\\u1ebfu ho\\u1eb7c sai m\\u1ed9t chi ti\\u1ebft v\\u1ec1 ng\\u01b0\\u1ee1ng \\u0111i\\u1ec3m, \\u0111i\\u1ec1u ki\\u1ec7n s\\u1ed1 l\\u01b0\\u1ee3ng hay nh\\u00f3m theo m\\u00e3 l\\u1edbp."}}'::jsonb),
(20, 'vi', 'bec96576c7e2e2243e89874dd58b3cfb369d000cc7f5125f1eb29e42d57ac2e4', 'Khi chuyển tiền từ tài khoản A sang tài khoản B, hệ thống phải trừ tiền ở A và cộng tiền vào B. Vì sao hai thao tác này cần nằm trong cùng một giao dịch? Giải thích vai trò của tính nguyên tử, COMMIT và ROLLBACK khi thao tác cộng tiền thất bại trước khi giao dịch được xác nhận', NULL, '{}'::jsonb,  E'{"Partial": {"label": "Partial", "criteria": "Nh\\u1eadn bi\\u1ebft nguy c\\u01a1 tr\\u1eeb ti\\u1ec1n m\\u00e0 kh\\u00f4ng c\\u1ed9ng ti\\u1ec1n ho\\u1eb7c nh\\u1eafc \\u0111\\u1ebfn ho\\u00e0n t\\u00e1c nh\\u01b0ng gi\\u1ea3i th\\u00edch ch\\u01b0a \\u0111\\u00fang ho\\u1eb7c ch\\u01b0a r\\u00f5 t\\u00ednh nguy\\u00ean t\\u1eed, COMMIT v\\u00e0 ROLLBACK."}, "Complete": {"label": "Complete", "criteria": "Gi\\u1ea3i th\\u00edch \\u0111\\u1ea7y \\u0111\\u1ee7 nguy c\\u01a1 m\\u1ea5t nh\\u1ea5t qu\\u00e1n, t\\u00ednh nguy\\u00ean t\\u1eed l\\u00e0 t\\u1ea5t c\\u1ea3 th\\u00e0nh c\\u00f4ng ho\\u1eb7c h\\u1ee7y to\\u00e0n b\\u1ed9 thay \\u0111\\u1ed5i, COMMIT khi giao d\\u1ecbch th\\u00e0nh c\\u00f4ng v\\u00e0 ROLLBACK ho\\u00e0n t\\u00e1c thao t\\u00e1c tr\\u1eeb ti\\u1ec1n n\\u1ebfu c\\u1ed9ng ti\\u1ec1n th\\u1ea5t b\\u1ea1i tr\\u01b0\\u1edbc COMMIT."}, "Incomplete": {"label": "Incomplete", "criteria": "Kh\\u00f4ng gi\\u1ea3i th\\u00edch \\u0111\\u01b0\\u1ee3c nhu c\\u1ea7u s\\u1eed d\\u1ee5ng giao d\\u1ecbch ho\\u1eb7c cho r\\u1eb1ng n\\u00ean x\\u00e1c nh\\u1eadn thao t\\u00e1c tr\\u1eeb ti\\u1ec1n d\\u00f9 thao t\\u00e1c c\\u1ed9ng ti\\u1ec1n \\u0111\\u00e3 th\\u1ea5t b\\u1ea1i."}, "Mostly Complete": {"label": "Mostly Complete", "criteria": "Gi\\u1ea3i th\\u00edch \\u0111\\u00fang c\\u1ea7n th\\u1ef1c hi\\u1ec7n hai thao t\\u00e1c trong c\\u00f9ng giao d\\u1ecbch v\\u00e0 d\\u00f9ng ROLLBACK khi th\\u1ea5t b\\u1ea1i, nh\\u01b0ng c\\u00f2n thi\\u1ebfu vai tr\\u00f2 c\\u1ee7a COMMIT ho\\u1eb7c ph\\u1ea1m vi ho\\u00e0n t\\u00e1c."}}'::jsonb),
(21, 'vi', 'df32f6c3844bc5b1103f8ef722dec00e7b7cf980d2fd8ca73ebf2e17e2c24257', 'Câu lệnh nào lấy tất cả các cột từ bảng students?', NULL, '{"A": "SELECT * FROM students;", "B": "SELECT students;", "C": "GET * FROM students;", "D": "FROM students SELECT;"}'::jsonb, '{}'::jsonb),
(22, 'vi', '9f4cae4c985bf8e8e19481ce0b96443fa7693ec331e4217c19997d8274373f46', 'Câu lệnh nào lấy sinh viên có điểm từ 8 trở lên?', NULL, '{"A": "SELECT * FROM students WHERE score > 8;", "B": "SELECT * FROM students WHERE score >= 8;", "C": "SELECT * FROM students HAVING score >= 8;", "D": "SELECT * FROM students WHERE score = 8;"}'::jsonb, '{}'::jsonb),
(23, 'vi', '73990e605f804d2c43dcc84b62d7e4cc68571878773d257aa524ca8033ca2292', 'INNER JOIN trả về những hàng nào?', NULL,  E'{"A": "T\\u1ea5t c\\u1ea3 h\\u00e0ng c\\u1ee7a b\\u1ea3ng b\\u00ean tr\\u00e1i", "B": "T\\u1ea5t c\\u1ea3 h\\u00e0ng c\\u1ee7a c\\u1ea3 hai b\\u1ea3ng", "C": "C\\u00e1c h\\u00e0ng k\\u1ebft h\\u1ee3p th\\u1ecfa \\u0111i\\u1ec1u ki\\u1ec7n n\\u1ed1i", "D": "C\\u00e1c h\\u00e0ng k\\u1ebft h\\u1ee3p th\\u1ecfa \\u0111i\\u1ec1u ki\\u1ec7n n\\u1ed1"}'::jsonb, '{}'::jsonb),
(24, 'vi', '3fc492b537ad059c1bca1c9bd9af31bedd4008ceb023474dcf9ef51d7528e783', 'Câu lệnh nào đếm số sinh viên của từng lớp?', NULL, '{"A": "SELECT class_id, COUNT(*) FROM students GROUP BY class_id;", "B": "SELECT class_id, COUNT(*) FROM students;", "C": "SELECT class_id FROM students WHERE COUNT(*) > 0;", "D": "SELECT COUNT(class_id) FROM students;"}'::jsonb, '{}'::jsonb),
(25, 'vi', 'f2aa19224160bbecae24eec697c2e4db003ffeb9f154d02c042f38090664af00', 'Muốn chỉ hiển thị các lớp có từ 5 sinh viên trở lên sau khi nhóm dữ liệu, cần dùng điều kiện nào?', NULL, '{"A": "WHERE COUNT(*) >= 5", "B": "HAVING COUNT(*) >= 5", "C": "GROUP BY COUNT(*) >= 5", "D": "ORDER BY COUNT(*) >= 5"}'::jsonb, '{}'::jsonb),
(26, 'vi', 'cd964e0ff8ba3d4005a452e1ff1ce95cbcb7655adf0e21eed15ad77ec43ff427', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Từ bảng students, lấy hai cột name và score của những sinh viên có điểm từ 8 trở lên', NULL, '{}'::jsonb, '{}'::jsonb),
(27, 'vi', '9360bb2dc27938145420105b2d68f19dfb7d407e2e5ce0544ef0cbdd8df38921', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Từ bảng students, trả về class_id và số sinh viên total_students của mỗi lớp có ít nhất 2 sinh viên', NULL, '{}'::jsonb, '{}'::jsonb),
(28, 'vi', '68cd75181165c3e8fd89c7b0e21fdcdcf2b6ab2456399d5686596d5d77ba6ac5', 'Phân biệt WHERE và HAVING trong SQL. Cho ví dụ sử dụng từng mệnh đề', NULL, '{}'::jsonb,  E'{"Partial": {"label": "Partial", "criteria": "Gi\\u1ea3i th\\u00edch \\u0111\\u00fang m\\u1ed9t m\\u1ec7nh \\u0111\\u1ec1, nh\\u01b0ng ch\\u01b0a ph\\u00e2n bi\\u1ec7t \\u0111\\u01b0\\u1ee3c WHERE l\\u1ecdc h\\u00e0ng tr\\u01b0\\u1edbc khi nh\\u00f3m v\\u00e0 HAVING l\\u1ecdc nh\\u00f3m sau khi nh\\u00f3m"}, "Complete": {"label": "Complete", "criteria": "N\\u00eau \\u0111\\u00fang WHERE l\\u1ecdc t\\u1eebng h\\u00e0ng tr\\u01b0\\u1edbc khi nh\\u00f3m, HAVING l\\u1ecdc c\\u00e1c nh\\u00f3m sau khi nh\\u00f3m; c\\u00f3 v\\u00ed d\\u1ee5 SQL \\u0111\\u00fang cho t\\u1eebng m\\u1ec7nh \\u0111\\u1ec1. V\\u00ed d\\u1ee5 kh\\u00e1c \\u0111\\u00e1p \\u00e1n tham kh\\u1ea3o v\\u1eabn \\u0111\\u01b0\\u1ee3c ch\\u1ea5p nh\\u1eadn n\\u1ebfu \\u0111\\u00fang"}, "Incomplete": {"label": "Incomplete", "criteria": "Kh\\u00f4ng tr\\u1ea3 l\\u1eddi ho\\u1eb7c gi\\u1ea3i th\\u00edch sai ch\\u1ee9c n\\u0103ng c\\u1ee7a c\\u1ea3 WHERE v\\u00e0 HAVING"}, "Mostly Complete": {"label": "Mostly Complete", "criteria": "Ph\\u00e2n bi\\u1ec7t \\u0111\\u00fang ch\\u1ee9c n\\u0103ng v\\u00e0 th\\u1eddi \\u0111i\\u1ec3m l\\u1ecdc c\\u1ee7a c\\u1ea3 hai m\\u1ec7nh \\u0111\\u1ec1, nh\\u01b0ng thi\\u1ebfu ho\\u1eb7c sai v\\u00ed d\\u1ee5 SQL c\\u1ee7a \\u00edt nh\\u1ea5t m\\u1ed9t m\\u1ec7nh \\u0111\\u1ec1"}}'::jsonb),
(29, 'vi', '4eaf9e5cf4f204b54c2d8cdc464fad541e1bea4157d1ceaf9aecd41d41e57903', 'Mục đích chính của chuẩn hóa cơ sở dữ liệu quan hệ là gì?', NULL,  E'{"A": "Gi\\u1ea3m d\\u01b0 th\\u1eeba d\\u1eef li\\u1ec7u v\\u00e0 h\\u1ea1n ch\\u1ebf b\\u1ea5t th\\u01b0\\u1eddng khi th\\u00eam, s\\u1eeda, x\\u00f3a", "B": "G\\u1ed9p t\\u1ea5t c\\u1ea3 d\\u1eef li\\u1ec7u v\\u00e0o m\\u1ed9t b\\u1ea3ng duy nh\\u1ea5t", "C": "Lo\\u1ea1i b\\u1ecf m\\u1ecdi kh\\u00f3a ngo\\u1ea1i", "D": "B\\u1ea3o \\u0111\\u1ea3m m\\u1ecdi truy v\\u1ea5n lu\\u00f4n ch\\u1ea1y nhanh h\\u01a1n"}'::jsonb, '{}'::jsonb),
(30, 'vi', 'fbc881e8c567b2e1890c0aec9a24a38f9b94512cf3665bec921b4b3a80bcd5b0', 'Trong thiết kế thông thường, bảng nào vi phạm dạng chuẩn thứ nhất (1NF)?', NULL,  E'{"A": "B\\u1ea3ng c\\u00f3 kh\\u00f3a ch\\u00ednh g\\u1ed3m hai c\\u1ed9t", "B": "B\\u1ea3ng l\\u01b0u nhi\\u1ec1u s\\u1ed1 \\u0111i\\u1ec7n tho\\u1ea1i trong m\\u1ed9t \\u00f4, ph\\u00e2n c\\u00e1ch b\\u1eb1ng d\\u1ea5u ph\\u1ea9y", "C": "B\\u1ea3ng c\\u00f3 kh\\u00f3a ngo\\u1ea1i", "D": "B\\u1ea3ng kh\\u00f4ng c\\u00f3 c\\u1ed9t ki\\u1ec3u s\\u1ed1"}'::jsonb, '{}'::jsonb),
(31, 'vi', '7efd544ef28e95e9e9abf341f75418aa1b6b71fb3bb5dce77a6a35ca785c7e1a', 'Câu lệnh nào thêm sinh viên có id = 1, name = ''An'' vào bảng students?', NULL, '{"A": "INSERT INTO students (id, name) VALUES (1, ''An'');", "B": "INSERT students SET (1, ''An'');", "C": "ADD INTO students (id, name) VALUES (1, ''An'');", "D": "UPDATE students VALUES (1, ''An'');"}'::jsonb, '{}'::jsonb),
(32, 'vi', 'ce415b3f20b9d6ab606d905f4972ad47b80e4964ef129e962bb919bc1919f3c0', 'Bảng students có cột status TEXT DEFAULT ''active''. Nếu thêm một hàng và không chỉ định cột status, giá trị của cột này là gì?', NULL,  E'{"A": "Lu\\u00f4n l\\u00e0 NULL.", "B": "Chu\\u1ed7i r\\u1ed7ng.", "C": "''active''.", "D": "C\\u00e2u l\\u1ec7nh lu\\u00f4n b\\u1ecb l\\u1ed7i."}'::jsonb, '{}'::jsonb),
(33, 'vi', '0f16bcc63495a9d9403524b7f97c29e1df26cf7a630c25648a953cc80b825f4d', 'Những phát biểu nào đúng về khóa chính? Chọn các đáp án đúng.', NULL,  E'{"A": "Gi\\u00e1 tr\\u1ecb kh\\u00f3a ch\\u00ednh x\\u00e1c \\u0111\\u1ecbnh duy nh\\u1ea5t m\\u1ed7i h\\u00e0ng.", "B": "C\\u00e1c c\\u1ed9t thu\\u1ed9c kh\\u00f3a ch\\u00ednh kh\\u00f4ng \\u0111\\u01b0\\u1ee3c ch\\u1ee9a NULL.", "C": "M\\u1ed9t kh\\u00f3a ch\\u00ednh c\\u00f3 th\\u1ec3 g\\u1ed3m nhi\\u1ec1u c\\u1ed9t.", "D": "M\\u1ed9t b\\u1ea3ng c\\u00f3 th\\u1ec3 c\\u00f3 nhi\\u1ec1u r\\u00e0ng bu\\u1ed9c PRIMARY KEY ri\\u00eang bi\\u1ec7t."}'::jsonb, '{}'::jsonb),
(34, 'vi', '0192846c82b1862bbfb1959ba8e5bd268b705fd7063264c4a5fc53f1be8a1ad1', 'Bảng students có class_id là khóa ngoại tham chiếu classes(id). Khi class_id khác NULL, ràng buộc này yêu cầu điều gì?', NULL,  E'{"A": "class_id ph\\u1ea3i kh\\u00e1c nhau \\u1edf m\\u1ecdi sinh vi\\u00ean.", "B": "Ph\\u1ea3i t\\u1ed3n t\\u1ea1i h\\u00e0ng trong classes c\\u00f3 id b\\u1eb1ng class_id.", "C": "Hai b\\u1ea3ng ph\\u1ea3i c\\u00f3 c\\u00f9ng s\\u1ed1 h\\u00e0ng.", "D": "class_id ph\\u1ea3i l\\u00e0 kh\\u00f3a ch\\u00ednh c\\u1ee7a students."}'::jsonb, '{}'::jsonb),
(35, 'vi', '50bfc025cf7ef9c2cb04db606099c433505947b5fb5d5f6f0318a6dc217eab2d', 'Câu lệnh nào chỉ đổi tên sinh viên có id = 5 thành ''Thu''?', NULL, '{"A": "UPDATE students SET name = ''Thu'';", "B": "UPDATE students SET name = ''Thu'' WHERE id = 5;", "C": "INSERT INTO students SET name = ''Thu'' WHERE id = 5;", "D": "UPDATE name = ''Thu'' FROM students WHERE id = 5;"}'::jsonb, '{}'::jsonb),
(36, 'vi', '26cca423ec9b291d21d4747d28bbd8ee80bea7603636df91f4654c046a68f210', 'Tính nguyên tử — Atomicity — trong ACID có nghĩa là gì?', NULL,  E'{"A": "C\\u00e1c thao t\\u00e1c trong giao d\\u1ecbch ho\\u1eb7c \\u0111\\u01b0\\u1ee3c th\\u1ef1c hi\\u1ec7n to\\u00e0n b\\u1ed9, ho\\u1eb7c kh\\u00f4ng thao t\\u00e1c n\\u00e0o c\\u00f3 hi\\u1ec7u l\\u1ef1c sau khi ho\\u00e0n t\\u00e1c.", "B": "M\\u1ecdi giao d\\u1ecbch ch\\u1ec9 \\u0111\\u01b0\\u1ee3c ch\\u1ee9a m\\u1ed9t c\\u00e2u l\\u1ec7nh.", "C": "M\\u1ecdi giao d\\u1ecbch lu\\u00f4n th\\u00e0nh c\\u00f4ng.", "D": "D\\u1eef li\\u1ec7u kh\\u00f4ng bao gi\\u1edd \\u0111\\u01b0\\u1ee3c thay \\u0111\\u1ed5i."}'::jsonb, '{}'::jsonb),
(37, 'vi', 'b9313cef627249d997a60d3ca9d7f0a34dcab2e659f609a3c44d1219ecbbbb81', 'Trong PostgreSQL, thành phần nào cho phép một CTE tham chiếu lại chính nó để xử lý dữ liệu phân cấp?', NULL, '{"A": "WITH RECURSIVE.", "B": "ORDER BY.", "C": "SELECT DISTINCT.", "D": "LIMIT."}'::jsonb, '{}'::jsonb),
(38, 'vi', '407e97ad32855cbd9ac14855527e4bd04c29763c4739ed2e33acdde4b62908b2', 'Cho sẵn bảng student_import và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Bảng student_import chứa dữ liệu sinh viên chưa được kiểm tra và chưa có khóa chính. Trước khi dùng student_id làm khóa chính, hãy tìm các mã xuất hiện nhiều hơn một lần. Trả về hai cột student_id và occurrences.', NULL, '{}'::jsonb, '{}'::jsonb),
(39, 'vi', '675457239be45bc6cbab6a5a741797effe30cf88c2eb120d5707c74c07a75816', 'Cho sẵn bảng classes, student_import và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Trước khi thêm ràng buộc khóa ngoại, hãy kiểm tra bảng student_import. Tìm sinh viên có class_id khác NULL nhưng không tồn tại lớp tương ứng trong bảng classes. Trả về student_id, name, class_id.', NULL, '{}'::jsonb, '{}'::jsonb),
(40, 'vi', '584168fae22aee48b42d7189c1fa9a1c496940a17a99d9f2eb66036e3e9ea449', 'SELECT DISTINCT class_id FROM students có tác dụng gì?', NULL,  E'{"A": "Tr\\u1ea3 v\\u1ec1 m\\u1ed7i gi\\u00e1 tr\\u1ecb class_id kh\\u00e1c nhau m\\u1ed9t l\\u1ea7n.", "B": "X\\u00f3a c\\u00e1c h\\u00e0ng tr\\u00f9ng kh\\u1ecfi b\\u1ea3ng students.", "C": "Ch\\u1ec9 l\\u1ea5y class_id xu\\u1ea5t hi\\u1ec7n \\u0111\\u00fang m\\u1ed9t l\\u1ea7n.", "D": "Lu\\u00f4n s\\u1eafp x\\u1ebfp class_id t\\u0103ng d\\u1ea7n."}'::jsonb, '{}'::jsonb),
(41, 'vi', '35689875b875f85efc59d71791dd060ceb6dcd2082d4357594a3737940baf730', 'Điều kiện nào tìm các hàng có email chưa được nhập (giá trị NULL)?', NULL, '{"A": "email = NULL", "B": "email IS NULL", "C": "email = NULL_STRING", "D": "email IS EMPTY"}'::jsonb, '{}'::jsonb),
(42, 'vi', '865afb116274bce62aad294727c51042c9657be49074f718fc0d52ebd49d1314', 'Điều kiện score BETWEEN 5 AND 8 tương đương điều kiện nào?', NULL, '{"A": "score > 5 AND score < 8", "B": "score >= 5 AND score <= 8", "C": "score >= 5 OR score <= 8", "D": "score = 5 AND score = 8"}'::jsonb, '{}'::jsonb),
(43, 'vi', '5f5ac44ab767c30c8f394f8ec82de41366298d5edc940a7fb0d1bd52a73bb236', 'Với ba hàng có score lần lượt là 8, NULL, 6, COUNT(score) và COUNT(*) lần lượt bằng bao nhiêu?', NULL,  E'{"A": "3 v\\u00e0 3.", "B": "2 v\\u00e0 2.", "C": "2 v\\u00e0 3.", "D": "3 v\\u00e0 2."}'::jsonb, '{}'::jsonb),
(44, 'vi', '864ae9fe1c69954afeb04140ff179e2de7a53be586d358927f79e191ce448ea4', 'LEFT JOIN giữ lại hàng bên trái không có hàng tương ứng bên phải như thế nào?', NULL,  E'{"A": "Lo\\u1ea1i b\\u1ecf h\\u00e0ng \\u0111\\u00f3.", "B": "Gi\\u1eef h\\u00e0ng \\u0111\\u00f3, c\\u00e1c c\\u1ed9t b\\u00ean ph\\u1ea3i nh\\u1eadn NULL.", "C": "T\\u1ef1 t\\u1ea1o h\\u00e0ng t\\u01b0\\u01a1ng \\u1ee9ng trong b\\u1ea3ng b\\u00ean ph\\u1ea3i.", "D": "Lu\\u00f4n b\\u00e1o l\\u1ed7i."}'::jsonb, '{}'::jsonb),
(45, 'vi', 'd90482161c95fe97f46ee73a0ed439c5674eb9bbd2dd6d2a9d768ed41394d730', 'Trong PostgreSQL, xét bảng sales không có ràng buộc khóa: câu SELECT region, SUM(amount) FROM sales cần thêm gì để tổng hợp theo từng vùng?', NULL,  E'{"A": "GROUP BY region.", "B": "GROUP BY amount.", "C": "WHERE SUM(amount).", "D": "Kh\\u00f4ng c\\u1ea7n th\\u00eam g\\u00ec."}'::jsonb, '{}'::jsonb),
(46, 'vi', '14be5dcfe72828fd6831f604c4238c817793ff5e822473e2659abb07c0191a4a', 'Khóa chính ghép PRIMARY KEY(student_id, course_id) bảo đảm điều gì?', NULL,  E'{"A": "M\\u1ed7i student_id ch\\u1ec9 \\u0111\\u01b0\\u1ee3c xu\\u1ea5t hi\\u1ec7n m\\u1ed9t l\\u1ea7n.", "B": "M\\u1ed7i course_id ch\\u1ec9 \\u0111\\u01b0\\u1ee3c xu\\u1ea5t hi\\u1ec7n m\\u1ed9t l\\u1ea7n.", "C": "M\\u1ed7i c\\u1eb7p student_id v\\u00e0 course_id ch\\u1ec9 \\u0111\\u01b0\\u1ee3c xu\\u1ea5t hi\\u1ec7n m\\u1ed9t l\\u1ea7n.", "D": "Hai c\\u1ed9t lu\\u00f4n ph\\u1ea3i c\\u00f3 c\\u00f9ng gi\\u00e1 tr\\u1ecb."}'::jsonb, '{}'::jsonb),
(47, 'vi', '0e9e4005406eaefd54814e62aa4912e01102b685f18e38220d6e84e40543bdf9', 'Trong PostgreSQL, một cột khóa ngoại đơn cho phép NULL và không có NOT NULL. Phát biểu nào đúng?', NULL,  E'{"A": "M\\u1ecdi h\\u00e0ng \\u0111\\u1ec1u b\\u1eaft bu\\u1ed9c tham chi\\u1ebfu m\\u1ed9t h\\u00e0ng cha.", "B": "Gi\\u00e1 tr\\u1ecb NULL c\\u00f3 th\\u1ec3 \\u0111\\u01b0\\u1ee3c l\\u01b0u m\\u00e0 kh\\u00f4ng c\\u1ea7n h\\u00e0ng cha t\\u01b0\\u01a1ng \\u1ee9ng.", "C": "C\\u1ed9t n\\u00e0y t\\u1ef1 \\u0111\\u1ed9ng l\\u00e0 kh\\u00f3a ch\\u00ednh.", "D": "C\\u00e1c gi\\u00e1 tr\\u1ecb kh\\u00e1c NULL \\u0111\\u01b0\\u1ee3c ph\\u00e9p tham chi\\u1ebfu m\\u00e3 kh\\u00f4ng t\\u1ed3n t\\u1ea1i."}'::jsonb, '{}'::jsonb),
(48, 'vi', 'e4fca73f3f5df78e4ecc72d31a65af99d8d2c1cfb6f0ba8163f1b21e72323409', 'Khi dùng INSERT INTO students (name, age) VALUES (...), thứ tự giá trị được hiểu theo gì?', NULL,  E'{"A": "Th\\u1ee9 t\\u1ef1 ch\\u1eef c\\u00e1i c\\u1ee7a t\\u00ean c\\u1ed9t.", "B": "Th\\u1ee9 t\\u1ef1 c\\u1ed9t trong danh s\\u00e1ch name, age.", "C": "Th\\u1ee9 t\\u1ef1 t\\u1ea1o ch\\u1ec9 m\\u1ee5c.", "D": "PostgreSQL t\\u1ef1 \\u0111o\\u00e1n theo n\\u1ed9i dung."}'::jsonb, '{}'::jsonb),
(49, 'vi', '6db954f872156c75ab955bd281b44f9d00ff439fd2795e0d80f94a9558184bdf', 'UPDATE products SET price = 100; không có WHERE sẽ tác động thế nào nếu chạy thành công?', NULL,  E'{"A": "Ch\\u1ec9 c\\u1eadp nh\\u1eadt h\\u00e0ng \\u0111\\u1ea7u ti\\u00ean.", "B": "Ch\\u1ec9 c\\u1eadp nh\\u1eadt h\\u00e0ng c\\u00f3 price NULL.", "C": "C\\u1eadp nh\\u1eadt price c\\u1ee7a t\\u1ea5t c\\u1ea3 c\\u00e1c h\\u00e0ng.", "D": "X\\u00f3a to\\u00e0n b\\u1ed9 b\\u1ea3ng."}'::jsonb, '{}'::jsonb),
(50, 'vi', 'd307bf4752d805893714b26d293a6978eee2fc0787bfb9db550f25832a3025bd', 'Những phát biểu nào đúng về DELETE FROM students; nếu thực thi thành công? Chọn các đáp án đúng.', NULL,  E'{"A": "X\\u00f3a t\\u1ea5t c\\u1ea3 c\\u00e1c h\\u00e0ng c\\u1ee7a students.", "B": "Gi\\u1eef l\\u1ea1i \\u0111\\u1ecbnh ngh\\u0129a b\\u1ea3ng students.", "C": "X\\u00f3a lu\\u00f4n \\u0111\\u1ecbnh ngh\\u0129a b\\u1ea3ng students.", "D": "Ch\\u1ec9 x\\u00f3a c\\u00e1c h\\u00e0ng c\\u00f3 NULL."}'::jsonb, '{}'::jsonb),
(51, 'vi', '288c961aed6b568ea8e4e5afd024493abf55bcacfe10f580146a14752b84f2bf', 'Bảng enrollment(student_id, course_id, student_name, grade) có khóa ghép (student_id, course_id); student_id xác định student_name. Phụ thuộc này gây vấn đề gì?', NULL,  E'{"A": "Ph\\u1ee5 thu\\u1ed9c b\\u1ed9 ph\\u1eadn c\\u1ee7a thu\\u1ed9c t\\u00ednh kh\\u00f4ng kh\\u00f3a v\\u00e0o m\\u1ed9t ph\\u1ea7n kh\\u00f3a, vi ph\\u1ea1m 2NF.", "B": "Kh\\u00f3a ch\\u00ednh b\\u1ecb thi\\u1ebfu c\\u1ed9t grade.", "C": "B\\u1ea3ng ch\\u1eafc ch\\u1eafn \\u0111\\u00e3 \\u0111\\u1ea1t BCNF.", "D": "\\u0110\\u00e2y l\\u00e0 ph\\u1ee5 thu\\u1ed9c \\u0111a tr\\u1ecb duy nh\\u1ea5t c\\u00f3 th\\u1ec3 c\\u00f3."}'::jsonb, '{}'::jsonb),
(52, 'vi', 'bbacca3b7c58e4de139b0a250c53e2914d48eaa88cfe5f79368d2a5a95f50845', 'Bảng employee(emp_id, dept_id, dept_name) có khóa emp_id, với emp_id → dept_id và dept_id → dept_name; dept_id không là siêu khóa, dept_name không thuộc khóa ứng viên nào. Vì sao vi phạm 3NF?', NULL,  E'{"A": "dept_name ph\\u1ee5 thu\\u1ed9c b\\u1eafc c\\u1ea7u v\\u00e0o kh\\u00f3a qua dept_id.", "B": "M\\u1ecdi c\\u1ed9t TEXT \\u0111\\u1ec1u vi ph\\u1ea1m 3NF.", "C": "B\\u1ea3ng c\\u00f3 h\\u01a1n hai c\\u1ed9t.", "D": "M\\u1ecdi kh\\u00f3a ngo\\u1ea1i \\u0111\\u1ec1u vi ph\\u1ea1m 3NF."}'::jsonb, '{}'::jsonb),
(53, 'vi', 'db926a90b3128c9f0a30a9a96f77c19ba1b7e042efb4e92ce698b433fd67bea5', 'Với R(A,B,C), tách thành R1(A,B) và R2(B,C). Điều kiện nào đủ bảo đảm phép tách không mất mát theo phụ thuộc hàm?', NULL,  E'{"A": "B \\u2192 A ho\\u1eb7c B \\u2192 C \\u0111\\u01b0\\u1ee3c suy ra t\\u1eeb t\\u1eadp ph\\u1ee5 thu\\u1ed9c h\\u00e0m.", "B": "A v\\u00e0 C c\\u00f3 c\\u00f9ng ki\\u1ec3u d\\u1eef li\\u1ec7u.", "C": "R1 v\\u00e0 R2 c\\u00f3 c\\u00f9ng s\\u1ed1 h\\u00e0ng \\u1edf m\\u1ed9t th\\u1eddi \\u0111i\\u1ec3m.", "D": "Hai b\\u1ea3ng \\u0111\\u1ec1u kh\\u00f4ng c\\u00f3 NULL."}'::jsonb, '{}'::jsonb),
(54, 'vi', '0c40daf1cf7ba2271403691a246da56c85fa8136baf5b7da11f7ef62ff349609', 'Trong một giao dịch PostgreSQL chưa COMMIT, ROLLBACK toàn bộ giao dịch có tác dụng gì với các thay đổi INSERT/UPDATE/DELETE của giao dịch đó?', NULL,  E'{"A": "Gi\\u1eef l\\u1ea1i t\\u1ea5t c\\u1ea3 thay \\u0111\\u1ed5i.", "B": "H\\u1ee7y c\\u00e1c thay \\u0111\\u1ed5i d\\u1eef li\\u1ec7u ch\\u01b0a \\u0111\\u01b0\\u1ee3c commit c\\u1ee7a giao d\\u1ecbch.", "C": "Ch\\u1ec9 h\\u1ee7y c\\u00e2u SELECT g\\u1ea7n nh\\u1ea5t.", "D": "X\\u00f3a lu\\u00f4n c\\u01a1 s\\u1edf d\\u1eef li\\u1ec7u."}'::jsonb, '{}'::jsonb),
(55, 'vi', '2636de58275696bfd728f2fa071f8475e5526159acfc9b05065c9d6b42f48aeb', 'Trong PostgreSQL ở mức READ COMMITTED, hai SELECT liên tiếp trong cùng giao dịch có thể đọc giá trị khác nhau của một hàng vì giao dịch khác đã COMMIT thay đổi giữa hai lần đọc. Hiện tượng này là gì?', NULL,  E'{"A": "Dirty read.", "B": "Non-repeatable read.", "C": "M\\u1ea5t kh\\u00f3a ch\\u00ednh.", "D": "Ph\\u1ee5 thu\\u1ed9c h\\u00e0m."}'::jsonb, '{}'::jsonb),
(56, 'vi', '32fa61362f487b048e94cd5941548962d338390f493fa85e51eed96819f88d94', 'Một truy vấn con dùng ở vị trí giá trị vô hướng trả về hai hàng. PostgreSQL sẽ xử lý thế nào?', NULL,  E'{"A": "T\\u1ef1 ch\\u1ecdn h\\u00e0ng \\u0111\\u1ea7u ti\\u00ean.", "B": "Gh\\u00e9p hai h\\u00e0ng th\\u00e0nh chu\\u1ed7i.", "C": "B\\u00e1o l\\u1ed7i v\\u00ec truy v\\u1ea5n con v\\u00f4 h\\u01b0\\u1edbng tr\\u1ea3 v\\u1ec1 nhi\\u1ec1u h\\u01a1n m\\u1ed9t h\\u00e0ng.", "D": "T\\u1ef1 l\\u1ea5y trung b\\u00ecnh."}'::jsonb, '{}'::jsonb),
(57, 'vi', 'caae4e8447f9245b500057428d8f8f1d4a08da3b0d3906ba5d6272a7b5e2007b', 'EXISTS (SELECT 1 FROM orders WHERE customer_id = 5) kiểm tra điều gì?', NULL,  E'{"A": "T\\u1ed5ng gi\\u00e1 tr\\u1ecb c\\u00e1c \\u0111\\u01a1n h\\u00e0ng.", "B": "C\\u00f3 \\u00edt nh\\u1ea5t m\\u1ed9t h\\u00e0ng th\\u1ecfa customer_id = 5 hay kh\\u00f4ng.", "C": "M\\u1ecdi \\u0111\\u01a1n h\\u00e0ng \\u0111\\u1ec1u thu\\u1ed9c kh\\u00e1ch h\\u00e0ng 5.", "D": "Kh\\u00e1ch h\\u00e0ng 5 c\\u00f3 \\u0111\\u00fang m\\u1ed9t \\u0111\\u01a1n h\\u00e0ng."}'::jsonb, '{}'::jsonb),
(58, 'vi', 'a8d7de530ca6d38f3364facb304fd5e25dbd9180721de3a60972444cd2a773f6', 'Đặc điểm nào nhận diện truy vấn con tương quan?', NULL,  E'{"A": "C\\u00f3 tham chi\\u1ebfu \\u0111\\u1ebfn c\\u1ed9t c\\u1ee7a truy v\\u1ea5n b\\u00ean ngo\\u00e0i.", "B": "Lu\\u00f4n c\\u00f3 ORDER BY.", "C": "Kh\\u00f4ng \\u0111\\u01b0\\u1ee3c c\\u00f3 WHERE.", "D": "Lu\\u00f4n tr\\u1ea3 v\\u1ec1 to\\u00e0n b\\u1ed9 b\\u1ea3ng."}'::jsonb, '{}'::jsonb),
(59, 'vi', '28f0567a88f0e8be9f6463e463712cc70723e7739704087f18aff02157761374', 'Những phát biểu nào đúng về SUM(amount) OVER (PARTITION BY customer_id)? Chọn các đáp án đúng.', NULL,  E'{"A": "C\\u00f3 th\\u1ec3 gi\\u1eef nguy\\u00ean t\\u1eebng h\\u00e0ng \\u0111\\u1ea7u v\\u00e0o.", "B": "T\\u00ednh t\\u1ed5ng trong t\\u1eebng nh\\u00f3m customer_id m\\u00e0 kh\\u00f4ng g\\u1ed9p c\\u00e1c h\\u00e0ng th\\u00e0nh m\\u1ed9t h\\u00e0ng.", "C": "B\\u1eaft bu\\u1ed9c l\\u00e0m gi\\u1ea3m s\\u1ed1 h\\u00e0ng nh\\u01b0 GROUP BY.", "D": "T\\u1ef1 s\\u1eeda amount trong b\\u1ea3ng."}'::jsonb, '{}'::jsonb),
(60, 'vi', '7359e5ae4b0ed0ed6851eab7b3ad384782a6d29c59e31cd8151cb8f6eb733add', 'Với ba điểm 90, 90, 80 và RANK() OVER (ORDER BY score DESC), hạng tương ứng là gì?', NULL, '{"A": "1, 2, 3.", "B": "1, 1, 2.", "C": "1, 1, 3.", "D": "0, 0, 1."}'::jsonb, '{}'::jsonb),
(61, 'vi', '1778248b3f694f1d4947c9e7fe9a59b859a86fb37fcbf0411dd4f2255886f2fb', 'Với ba điểm 90, 90, 80 và DENSE_RANK() OVER (ORDER BY score DESC), hạng tương ứng là gì?', NULL, '{"A": "1, 1, 2.", "B": "1, 1, 3.", "C": "1, 2, 3.", "D": "0, 1, 2."}'::jsonb, '{}'::jsonb),
(62, 'vi', 'c16eec121337d1185e78cac989eb0b50c275cd2983eb76c11aeb99832dcaed69', 'Với id duy nhất, biểu thức nào tính tổng lũy kế amount theo thứ tự id?', NULL, '{"A": "SUM(amount) OVER (ORDER BY id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW).", "B": "SUM(amount) OVER ().", "C": "COUNT(amount) GROUP BY id.", "D": "SUM(amount) WHERE id IS NOT NULL."}'::jsonb, '{}'::jsonb),
(63, 'vi', 'b4d5d0b1a0ed8815a6587b082013c69b5992d428db5cfce4cfb2f35b68eb968f', 'Trong PostgreSQL, SUM(amount) OVER (ORDER BY sale_date) không ghi frame, với nhiều hàng cùng sale_date, có đặc điểm nào?', NULL,  E'{"A": "Frame m\\u1eb7c \\u0111\\u1ecbnh bao g\\u1ed3m c\\u00e1c h\\u00e0ng \\u0111\\u1ed3ng h\\u1ea1ng theo sale_date \\u0111\\u1ebfn h\\u00e0ng hi\\u1ec7n t\\u1ea1i.", "B": "Lu\\u00f4n ch\\u1ec9 c\\u1ed9ng \\u0111\\u00fang m\\u1ed9t h\\u00e0ng v\\u1eadt l\\u00fd.", "C": "Lu\\u00f4n t\\u01b0\\u01a1ng \\u0111\\u01b0\\u01a1ng ROWS BETWEEN 1 PRECEDING AND CURRENT ROW.", "D": "Kh\\u00f4ng \\u0111\\u01b0\\u1ee3c ph\\u00e9p c\\u00f3 ng\\u00e0y tr\\u00f9ng."}'::jsonb, '{}'::jsonb),
(64, 'vi', '0283e8c0b1b9115118e29aa918357abe5d58255ad72e10060e01f5d0214e63d2', 'Muốn LAST_VALUE(score) trả về giá trị cuối toàn bộ phân vùng theo thứ tự id, frame nào phù hợp?', NULL,  E'{"A": "ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING.", "B": "ROWS BETWEEN CURRENT ROW AND CURRENT ROW.", "C": "ROWS BETWEEN 1 PRECEDING AND CURRENT ROW.", "D": "Kh\\u00f4ng c\\u00f3 frame n\\u00e0o th\\u1ef1c hi\\u1ec7n \\u0111\\u01b0\\u1ee3c."}'::jsonb, '{}'::jsonb),
(65, 'vi', '8f4134095af77e0f42ff53ddf9a1c05297426ad257ddedb72fbe1c667cdfddcb', 'Với CTE đệ quy sinh số từ 1 bằng cách cộng 1 và dùng UNION ALL, điều kiện nào giúp dừng ở 10?', NULL,  E'{"A": "WHERE n < 10 trong nh\\u00e1nh sinh n + 1.", "B": "ORDER BY n trong SELECT ngo\\u00e0i.", "C": "\\u0110\\u1ed5i t\\u00ean CTE th\\u00e0nh numbers.", "D": "Th\\u00eam m\\u1ed9t c\\u1ed9t TEXT b\\u1ea5t k\\u1ef3."}'::jsonb, '{}'::jsonb),
(66, 'vi', '946f63a929672d41caeb1750bba8c13e7f6568db47a60607c64f1909e16f1353', 'Trong CTE đệ quy PostgreSQL, UNION khác UNION ALL ở điểm nào liên quan đến các hàng kết quả?', NULL,  E'{"A": "UNION lo\\u1ea1i c\\u00e1c h\\u00e0ng tr\\u00f9ng theo to\\u00e0n b\\u1ed9 c\\u1ed9t k\\u1ebft qu\\u1ea3, c\\u00f2n UNION ALL gi\\u1eef ch\\u00fang.", "B": "UNION ALL t\\u1ef1 ph\\u00e1t hi\\u1ec7n m\\u1ecdi chu tr\\u00ecnh \\u0111\\u1ed3 th\\u1ecb.", "C": "UNION lu\\u00f4n b\\u1ea3o \\u0111\\u1ea3m k\\u1ebft th\\u00fac k\\u1ec3 c\\u1ea3 khi m\\u1ed7i v\\u00f2ng sinh m\\u1ed9t gi\\u00e1 tr\\u1ecb m\\u1edbi.", "D": "UNION ALL kh\\u00f4ng cho ph\\u00e9p \\u0111\\u1ec7 quy."}'::jsonb, '{}'::jsonb),
(67, 'vi', '441318fa32fa51516cfbbdb05b14a6eb0a45cafff834a54d4b0af0051b27f9e5', 'Với B-tree ghép (customer_id, created_at), truy vấn nào thường phù hợp với thứ tự cột của chỉ mục để lọc và duyệt theo thời gian?', NULL,  E'{"A": "WHERE customer_id = 10 ORDER BY created_at.", "B": "WHERE LOWER(note) = ''x''.", "C": "WHERE random() > 0.5.", "D": "SELECT m\\u1ecdi h\\u00e0ng v\\u00e0 s\\u1eafp x\\u1ebfp theo c\\u1ed9t kh\\u00f4ng li\\u00ean quan."}'::jsonb, '{}'::jsonb),
(68, 'vi', '8b2ad50f01e037203881ad2ea0fb8be293766749e76a7530ae04e61aaa905f48', 'Những phát biểu nào đúng về EXPLAIN ANALYZE trong PostgreSQL? Chọn các đáp án đúng.', NULL,  E'{"A": "Th\\u1ef1c s\\u1ef1 ch\\u1ea1y c\\u00e2u l\\u1ec7nh \\u0111\\u1ec3 thu th\\u1eadp s\\u1ed1 li\\u1ec7u th\\u1ef1c t\\u1ebf.", "B": "C\\u00f3 th\\u1ec3 so s\\u00e1nh s\\u1ed1 h\\u00e0ng \\u01b0\\u1edbc l\\u01b0\\u1ee3ng v\\u00e0 th\\u1ef1c t\\u1ebf \\u0111\\u1ec3 t\\u00ecm \\u0111i\\u1ec3m sai l\\u1ec7ch.", "C": "Ch\\u1ec9 ph\\u00e2n t\\u00edch c\\u00fa ph\\u00e1p v\\u00e0 tuy\\u1ec7t \\u0111\\u1ed1i kh\\u00f4ng th\\u1ef1c thi.", "D": "T\\u1ef1 t\\u1ea1o t\\u1ea5t c\\u1ea3 ch\\u1ec9 m\\u1ee5c c\\u00f2n thi\\u1ebfu."}'::jsonb, '{}'::jsonb),
(69, 'vi', 'fe0b8fd5944355b7d1cc9ae4a32f2d536e22f11b9472498997e52cfd42e716d3', 'Bảng orders có chỉ mục B-tree thông thường trên created_at kiểu timestamp. Cách lọc ngày nào thường giúp tận dụng chỉ mục mà không bọc cột trong hàm?', NULL,  E'{"A": "created_at >= TIMESTAMP ''2026-10-01 00:00:00'' AND created_at < TIMESTAMP ''2026-10-02 00:00:00''.", "B": "TO_CHAR(created_at, ''YYYY-MM-DD'') = ''2026-10-01''.", "C": "EXTRACT(DAY FROM created_at) = 1, kh\\u00f4ng gi\\u1edbi h\\u1ea1n th\\u00e1ng v\\u00e0 n\\u0103m.", "D": "CAST(created_at AS TEXT) LIKE ''2026-10-01%''."}'::jsonb, '{}'::jsonb),
(70, 'vi', '09615c7e5b8dc498a985a35569484ed3814f0398147b44ed551efbd899db4967', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Từ bảng students, lấy id và name của sinh viên có score từ 9 trở lên.', NULL, '{}'::jsonb, '{}'::jsonb),
(71, 'vi', '1d2a09c8dc6e05e59ed021d0b43b0c7cdc14f99b6f10cae0dd7c047e2545a5d8', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Từ bảng students, lấy id và name của sinh viên chưa có điểm (score là NULL).', NULL, '{}'::jsonb, '{}'::jsonb),
(72, 'vi', 'd9981d2406ce001df9642f205daac20946d62844a70920b268de3b86548e8ed0', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Đếm số sinh viên của mỗi class_id trong students, kể cả sinh viên chưa có điểm. Trả về class_id và student_count.', NULL, '{}'::jsonb, '{}'::jsonb),
(73, 'vi', '4a559ed7be1be37356fc55fe4e12f0d5a26be73e2a74749b5849b384036b2f43', 'Tìm các lớp có điểm trung bình từ 8 trở lên. Bỏ qua score NULL khi tính trung bình. Trả về class_id và average_score.', NULL, '{}'::jsonb, '{}'::jsonb),
(74, 'vi', '9ef8729d115bb5ad0428392f6ef83b7cc9339469411615d06c4fb4d944195cc0', 'Kết hợp students và classes để lấy students.id thành student_id, students.name thành student_name, classes.name thành class_name cho sinh viên có lớp tương ứng.', NULL, '{}'::jsonb, '{}'::jsonb),
(75, 'vi', '701aa9a108065e170a6f262173025b5aff87080d7a08a9fcfb6bc3b97d4a0719', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Lấy id, name, score của sinh viên có điểm cao hơn điểm trung bình của toàn bộ sinh viên có điểm trong students.', NULL, '{}'::jsonb, '{}'::jsonb),
(76, 'vi', '3297ffb4bd8dbb3e1bb3ae8c2fd6f9adcea28a922a3b527a6b38c4ec6b520a73', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Lấy id, name, score của sinh viên có điểm cao hơn điểm trung bình của chính lớp mình. Không tính score NULL vào trung bình.', NULL, '{}'::jsonb, '{}'::jsonb),
(77, 'vi', 'b4755da1a2149921ddb1d03885163fc60558bbe66ab608b7fadcc35a3b3d156c', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Xếp hạng các sinh viên có điểm theo score giảm dần bằng hạng liên tiếp không có khoảng trống; các điểm bằng nhau cùng hạng. Trả về id và score_rank.', NULL, '{}'::jsonb, '{}'::jsonb),
(78, 'vi', '8f6e9ae75888af58cab31e4ecff2885a99f2c5cf8dade3a774917df3179e7b45', 'Cho sẵn bảng sales và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Từ bảng sales có day_no duy nhất, tính doanh thu lũy kế từ ngày đầu đến ngày hiện tại. Trả về day_no và running_total.', NULL, '{}'::jsonb, '{}'::jsonb),
(79, 'vi', 'd63a48a8023bd831dffb402dd5e106af5b5ef6de9280a8df5a6d13b28b602d26', 'Cho sẵn bảng sales và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Từ bảng sales có day_no duy nhất, tính trung bình amount của ngày hiện tại và hàng ngày liền trước trong thứ tự day_no. Ngày đầu chỉ dùng chính nó. Trả về day_no và moving_average.', NULL, '{}'::jsonb, '{}'::jsonb),
(80, 'vi', '7446d6ec0cec79bd339130229f1b8242a20bbf0b630821574007b9d0e7a4fe8b', 'Cho sẵn bảng employees và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Bảng employees biểu diễn cây quản lý không có chu trình, với CEO có id=1. Lấy id và depth của CEO cùng toàn bộ nhân viên cấp dưới trực tiếp hoặc gián tiếp; CEO có depth=0.', NULL, '{}'::jsonb, '{}'::jsonb),
(81, 'vi', '072c66a34a33305b4c8d110f76716e4e62e1180cd9fe45d42ed40c1e3b144a2c', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Chọn đúng một sinh viên có điểm cao nhất ở mỗi lớp trong students. Nếu bằng điểm, chọn id nhỏ hơn. Sinh viên có score NULL không được xét. Trả về class_id, id, name, score.', NULL, '{}'::jsonb, '{}'::jsonb),
(82, 'vi', '71e6e385f4ea0b00fa82101df84e0ca5fe1ee1c2548bf860bcd3a0c1b51b1542', 'Thiết kế khóa cho bảng enrollment lưu việc sinh viên đăng ký học phần. Giải thích cách tránh đăng ký trùng và giữ liên kết hợp lệ đến sinh viên, học phần.', NULL, '{}'::jsonb,  E'{"Partial": {"label": "\\u0110\\u00fang m\\u1ed9t ph\\u1ea7n", "criteria": "N\\u00eau \\u0111\\u00fang m\\u1ed9t r\\u00e0ng bu\\u1ed9c kh\\u00f3a nh\\u01b0ng ch\\u01b0a gi\\u1ea3i quy\\u1ebft \\u0111\\u1ed3ng th\\u1eddi \\u0111\\u0103ng k\\u00fd tr\\u00f9ng v\\u00e0 li\\u00ean k\\u1ebft h\\u1ee3p l\\u1ec7."}, "Complete": {"label": "\\u0110\\u1ea7y \\u0111\\u1ee7", "criteria": "\\u0110\\u1ec1 xu\\u1ea5t kh\\u00f3a gh\\u00e9p ho\\u1eb7c kh\\u00f3a thay th\\u1ebf k\\u00e8m UNIQUE cho c\\u1eb7p sinh vi\\u00ean\\u2013h\\u1ecdc ph\\u1ea7n; kh\\u00f3a ngo\\u1ea1i h\\u1ee3p l\\u1ec7, NOT NULL ph\\u00f9 h\\u1ee3p; gi\\u1ea3i th\\u00edch r\\u00f5 vai tr\\u00f2 t\\u1eebng r\\u00e0ng bu\\u1ed9c."}, "Incomplete": {"label": "Ch\\u01b0a \\u0111\\u1ea1t", "criteria": "Kh\\u00f4ng tr\\u1ea3 l\\u1eddi ho\\u1eb7c tr\\u1ea3 l\\u1eddi sai n\\u1ed9i dung c\\u1ed1t l\\u00f5i c\\u1ee7a \\u0111\\u1ec1 b\\u00e0i."}, "Mostly Complete": {"label": "G\\u1ea7n \\u0111\\u1ea7y \\u0111\\u1ee7", "criteria": "N\\u00eau \\u0111\\u00fang c\\u00e1ch ch\\u1ed1ng tr\\u00f9ng v\\u00e0 kh\\u00f3a ngo\\u1ea1i, nh\\u01b0ng thi\\u1ebfu gi\\u1ea3i th\\u00edch ho\\u1eb7c thi\\u1ebfu \\u0111i\\u1ec1u ki\\u1ec7n NOT NULL khi b\\u1eaft bu\\u1ed9c \\u0111\\u0103ng k\\u00fd ph\\u1ea3i c\\u00f3 sinh vi\\u00ean v\\u00e0 h\\u1ecdc ph\\u1ea7n."}}'::jsonb),
(83, 'vi', '3f06d5f1c299e52bba577ba61de1c5a2a0b1942c2dd959820c3442a394a93674', 'Bảng employee(emp_id, emp_name, dept_id, dept_name) có emp_id là khóa, dept_id xác định dept_name. Hãy chỉ ra bất thường cập nhật và đề xuất tách bảng đến 3NF với giả định dept_id không phải siêu khóa của employee.', NULL, '{}'::jsonb,  E'{"Partial": {"label": "\\u0110\\u00fang m\\u1ed9t ph\\u1ea7n", "criteria": "Nh\\u1eadn ra d\\u1eef li\\u1ec7u ph\\u00f2ng b\\u1ecb l\\u1eb7p nh\\u01b0ng ch\\u01b0a \\u0111\\u01b0a \\u0111\\u01b0\\u1ee3c c\\u00e1ch t\\u00e1ch ph\\u00f9 h\\u1ee3p."}, "Complete": {"label": "\\u0110\\u1ea7y \\u0111\\u1ee7", "criteria": "N\\u00eau ph\\u1ee5 thu\\u1ed9c v\\u00e0 \\u00edt nh\\u1ea5t m\\u1ed9t b\\u1ea5t th\\u01b0\\u1eddng c\\u1ee5 th\\u1ec3; t\\u00e1ch \\u0111\\u00fang hai b\\u1ea3ng, ch\\u1ec9 r\\u00f5 kh\\u00f3a ch\\u00ednh, kh\\u00f3a ngo\\u1ea1i v\\u00e0 kh\\u1ea3 n\\u0103ng n\\u1ed1i kh\\u00f4i ph\\u1ee5c d\\u1eef li\\u1ec7u."}, "Incomplete": {"label": "Ch\\u01b0a \\u0111\\u1ea1t", "criteria": "Kh\\u00f4ng tr\\u1ea3 l\\u1eddi ho\\u1eb7c tr\\u1ea3 l\\u1eddi sai n\\u1ed9i dung c\\u1ed1t l\\u00f5i c\\u1ee7a \\u0111\\u1ec1 b\\u00e0i."}, "Mostly Complete": {"label": "G\\u1ea7n \\u0111\\u1ea7y \\u0111\\u1ee7", "criteria": "T\\u00e1ch \\u0111\\u00fang hai b\\u1ea3ng v\\u00e0 nh\\u1eadn di\\u1ec7n ph\\u1ee5 thu\\u1ed9c b\\u1eafc c\\u1ea7u nh\\u01b0ng thi\\u1ebfu kh\\u00f3a ho\\u1eb7c gi\\u1ea3i th\\u00edch b\\u1ea5t th\\u01b0\\u1eddng."}}'::jsonb),
(84, 'vi', '87b0b46136fcbcd91dace972a4940531bd2ab2c3f1a9cafcd4fa8038fec87a11', 'Giải thích vì sao chuyển tiền giữa hai tài khoản cần một giao dịch. Nêu cách xử lý khi đã trừ tiền nhưng bước cộng tiền thất bại.', NULL, '{}'::jsonb,  E'{"Partial": {"label": "\\u0110\\u00fang m\\u1ed9t ph\\u1ea7n", "criteria": "N\\u00eau giao d\\u1ecbch ho\\u1eb7c ho\\u00e0n t\\u00e1c nh\\u01b0ng ch\\u01b0a gi\\u1ea3i th\\u00edch v\\u00ec sao hai b\\u01b0\\u1edbc c\\u1ea7n \\u0111\\u01b0\\u1ee3c g\\u1eafn li\\u1ec1n."}, "Complete": {"label": "\\u0110\\u1ea7y \\u0111\\u1ee7", "criteria": "Gi\\u1ea3i th\\u00edch t\\u00ednh nguy\\u00ean t\\u1eed, ranh gi\\u1edbi giao d\\u1ecbch v\\u00e0 rollback to\\u00e0n b\\u1ed9 khi l\\u1ed7i; \\u0111\\u1ec1 c\\u1eadp ki\\u1ec3m tra s\\u1ed1 d\\u01b0 v\\u00e0 c\\u01a1 ch\\u1ebf x\\u1eed l\\u00fd \\u0111\\u1ed3ng th\\u1eddi ph\\u00f9 h\\u1ee3p."}, "Incomplete": {"label": "Ch\\u01b0a \\u0111\\u1ea1t", "criteria": "Kh\\u00f4ng tr\\u1ea3 l\\u1eddi ho\\u1eb7c tr\\u1ea3 l\\u1eddi sai n\\u1ed9i dung c\\u1ed1t l\\u00f5i c\\u1ee7a \\u0111\\u1ec1 b\\u00e0i."}, "Mostly Complete": {"label": "G\\u1ea7n \\u0111\\u1ea7y \\u0111\\u1ee7", "criteria": "M\\u00f4 t\\u1ea3 \\u0111\\u00fang BEGIN/COMMIT/ROLLBACK v\\u00e0 t\\u00ednh nguy\\u00ean t\\u1eed nh\\u01b0ng ch\\u01b0a n\\u00eau ki\\u1ec3m tra s\\u1ed1 d\\u01b0 hay v\\u1ea5n \\u0111\\u1ec1 \\u0111\\u1ed3ng th\\u1eddi."}}'::jsonb),
(85, 'vi', 'db488e8722a3e45cbed941f31c4d3cab38d65adde2d5c332b4bfa78c94e8319f', 'Phân biệt truy vấn con độc lập và truy vấn con tương quan. Minh họa bằng việc tìm nhân viên có lương cao hơn trung bình toàn công ty và trung bình phòng mình.', NULL, '{}'::jsonb,  E'{"Partial": {"label": "\\u0110\\u00fang m\\u1ed9t ph\\u1ea7n", "criteria": "Gi\\u1ea3i th\\u00edch \\u0111\\u00fang m\\u1ed9t lo\\u1ea1i truy v\\u1ea5n con nh\\u01b0ng ch\\u01b0a ph\\u00e2n bi\\u1ec7t b\\u1eb1ng tham chi\\u1ebfu c\\u1ed9t."}, "Complete": {"label": "\\u0110\\u1ea7y \\u0111\\u1ee7", "criteria": "Ph\\u00e2n bi\\u1ec7t \\u0111\\u00fang tham chi\\u1ebfu b\\u00ean ngo\\u00e0i; \\u0111\\u01b0a hai v\\u00ed d\\u1ee5 \\u0111\\u00fang cho trung b\\u00ecnh c\\u00f4ng ty v\\u00e0 trung b\\u00ecnh t\\u1eebng ph\\u00f2ng, ch\\u1ea5p nh\\u1eadn c\\u00e1ch vi\\u1ebft SQL t\\u01b0\\u01a1ng \\u0111\\u01b0\\u01a1ng."}, "Incomplete": {"label": "Ch\\u01b0a \\u0111\\u1ea1t", "criteria": "Kh\\u00f4ng tr\\u1ea3 l\\u1eddi ho\\u1eb7c tr\\u1ea3 l\\u1eddi sai n\\u1ed9i dung c\\u1ed1t l\\u00f5i c\\u1ee7a \\u0111\\u1ec1 b\\u00e0i."}, "Mostly Complete": {"label": "G\\u1ea7n \\u0111\\u1ea7y \\u0111\\u1ee7", "criteria": "Ph\\u00e2n bi\\u1ec7t \\u0111\\u00fang hai lo\\u1ea1i v\\u00e0 \\u00fd ngh\\u0129a hai y\\u00eau c\\u1ea7u, nh\\u01b0ng thi\\u1ebfu ho\\u1eb7c sai m\\u1ed9t v\\u00ed d\\u1ee5."}}'::jsonb),
(86, 'vi', 'f7c680d369d96b0d54682450352784fb5a869a74ee795f7c6512f695a37f0fb1', 'So sánh GROUP BY với hàm cửa sổ. Khi cần giữ từng nhân viên và hiển thị thêm tổng lương phòng cùng hạng lương trong phòng, nên làm thế nào?', NULL, '{}'::jsonb,  E'{"Partial": {"label": "\\u0110\\u00fang m\\u1ed9t ph\\u1ea7n", "criteria": "Nh\\u1eadn bi\\u1ebft c\\u00f3 th\\u1ec3 t\\u1ed5ng h\\u1ee3p nh\\u01b0ng ch\\u01b0a gi\\u1ea3i th\\u00edch kh\\u00e1c bi\\u1ec7t v\\u1ec1 s\\u1ed1 h\\u00e0ng k\\u1ebft qu\\u1ea3."}, "Complete": {"label": "\\u0110\\u1ea7y \\u0111\\u1ee7", "criteria": "So s\\u00e1nh \\u0111\\u00fang; \\u0111\\u01b0a c\\u00e1ch t\\u00ednh t\\u1ed5ng theo ph\\u00f2ng v\\u00e0 x\\u1ebfp h\\u1ea1ng theo ph\\u00f2ng b\\u1eb1ng c\\u1eeda s\\u1ed5, gi\\u1ea3i th\\u00edch ph\\u00e2n v\\u00f9ng v\\u00e0 quy t\\u1eafc h\\u00f2a h\\u1ea1ng."}, "Incomplete": {"label": "Ch\\u01b0a \\u0111\\u1ea1t", "criteria": "Kh\\u00f4ng tr\\u1ea3 l\\u1eddi ho\\u1eb7c tr\\u1ea3 l\\u1eddi sai n\\u1ed9i dung c\\u1ed1t l\\u00f5i c\\u1ee7a \\u0111\\u1ec1 b\\u00e0i."}, "Mostly Complete": {"label": "G\\u1ea7n \\u0111\\u1ea7y \\u0111\\u1ee7", "criteria": "So s\\u00e1nh \\u0111\\u00fang vi\\u1ec7c g\\u1ed9p h\\u00e0ng v\\u00e0 gi\\u1eef chi ti\\u1ebft, nh\\u01b0ng ch\\u1ec9 minh h\\u1ecda \\u0111\\u01b0\\u1ee3c t\\u1ed5ng l\\u01b0\\u01a1ng ho\\u1eb7c x\\u1ebfp h\\u1ea1ng."}}'::jsonb),
(87, 'vi', 'b78b6c8ccd2af27c9c526825ea6627a54e795a6e04d0a8b5ab7a955f0ebf311c', 'Có nên tạo chỉ mục cho mọi cột để tăng tốc cơ sở dữ liệu không? Phân tích lợi ích, chi phí và cách chọn chỉ mục cho truy vấn thường dùng.', NULL, '{}'::jsonb,  E'{"Partial": {"label": "\\u0110\\u00fang m\\u1ed9t ph\\u1ea7n", "criteria": "N\\u00eau \\u0111\\u01b0\\u1ee3c l\\u1ee3i \\u00edch ho\\u1eb7c chi ph\\u00ed \\u0111\\u01a1n l\\u1ebb nh\\u01b0ng k\\u1ebft lu\\u1eadn ch\\u01b0a c\\u00f3 c\\u0103n c\\u1ee9."}, "Complete": {"label": "\\u0110\\u1ea7y \\u0111\\u1ee7", "criteria": "Ph\\u00e2n t\\u00edch c\\u00e2n b\\u1eb1ng l\\u1ee3i \\u00edch v\\u00e0 chi ph\\u00ed; ch\\u1ecdn theo truy v\\u1ea5n, \\u0111\\u1ed9 ch\\u1ecdn l\\u1ecdc v\\u00e0 th\\u1ee9 t\\u1ef1 c\\u1ed9t; n\\u00eau \\u0111o k\\u1ebf ho\\u1ea1ch ho\\u1eb7c th\\u1eddi gian th\\u1ef1c t\\u1ebf \\u0111\\u1ec3 x\\u00e1c nh\\u1eadn."}, "Incomplete": {"label": "Ch\\u01b0a \\u0111\\u1ea1t", "criteria": "Kh\\u00f4ng tr\\u1ea3 l\\u1eddi ho\\u1eb7c tr\\u1ea3 l\\u1eddi sai n\\u1ed9i dung c\\u1ed1t l\\u00f5i c\\u1ee7a \\u0111\\u1ec1 b\\u00e0i."}, "Mostly Complete": {"label": "G\\u1ea7n \\u0111\\u1ea7y \\u0111\\u1ee7", "criteria": "N\\u00eau \\u0111\\u00fang l\\u1ee3i \\u00edch, dung l\\u01b0\\u1ee3ng v\\u00e0 chi ph\\u00ed ghi nh\\u01b0ng thi\\u1ebfu c\\u00e1ch ch\\u1ecdn ho\\u1eb7c ki\\u1ec3m ch\\u1ee9ng ch\\u1ec9 m\\u1ee5c."}}'::jsonb),
(88, 'vi', 'd2be1f4864d4d449453a5a777bb88deb95a0c90b973ac901dd3a79058beb95a2', 'EXPLAIN ANALYZE cho thấy estimated rows rất khác actual rows ở một nút và một phép JOIN tốn thời gian. Trình bày quy trình tìm nguyên nhân và tối ưu có kiểm chứng.', NULL, '{}'::jsonb,  E'{"Partial": {"label": "\\u0110\\u00fang m\\u1ed9t ph\\u1ea7n", "criteria": "Ch\\u1ec9 \\u0111\\u1ec1 xu\\u1ea5t th\\u00eam ch\\u1ec9 m\\u1ee5c ho\\u1eb7c s\\u1eeda truy v\\u1ea5n m\\u00e0 ch\\u01b0a \\u0111\\u1ecdc hay ki\\u1ec3m ch\\u1ee9ng k\\u1ebf ho\\u1ea1ch."}, "Complete": {"label": "\\u0110\\u1ea7y \\u0111\\u1ee7", "criteria": "\\u0110\\u1ecdc \\u0111\\u00fang estimated/actual rows v\\u00e0 loops; ph\\u00e2n t\\u00edch th\\u1ed1ng k\\u00ea, \\u0111i\\u1ec1u ki\\u1ec7n v\\u00e0 k\\u1ebf ho\\u1ea1ch JOIN; \\u0111\\u1ec1 xu\\u1ea5t thay \\u0111\\u1ed5i c\\u00f3 c\\u0103n c\\u1ee9 v\\u00e0 \\u0111o tr\\u01b0\\u1edbc/sau, gi\\u1eef t\\u01b0\\u01a1ng \\u0111\\u01b0\\u01a1ng k\\u1ebft qu\\u1ea3."}, "Incomplete": {"label": "Ch\\u01b0a \\u0111\\u1ea1t", "criteria": "Kh\\u00f4ng tr\\u1ea3 l\\u1eddi ho\\u1eb7c tr\\u1ea3 l\\u1eddi sai n\\u1ed9i dung c\\u1ed1t l\\u00f5i c\\u1ee7a \\u0111\\u1ec1 b\\u00e0i."}, "Mostly Complete": {"label": "G\\u1ea7n \\u0111\\u1ea7y \\u0111\\u1ee7", "criteria": "Nh\\u1eadn di\\u1ec7n sai l\\u1ec7ch \\u01b0\\u1edbc l\\u01b0\\u1ee3ng v\\u00e0 \\u0111\\u1ec1 xu\\u1ea5t c\\u1ea3i thi\\u1ec7n h\\u1ee3p l\\u00fd nh\\u01b0ng thi\\u1ebfu \\u0111o tr\\u01b0\\u1edbc/sau ho\\u1eb7c ki\\u1ec3m tra k\\u1ebft qu\\u1ea3."}}'::jsonb),
(89, 'vi', '6c20d88b2d9d4b19013f6d16a1da6cb6074f7c60f6b576babb3884662d345af6', 'Khi duyệt quan hệ quản lý bằng WITH RECURSIVE, chu trình trong dữ liệu có thể gây vấn đề gì? Đề xuất cách phát hiện hoặc ngăn lặp và giải thích giới hạn của UNION.', NULL, '{}'::jsonb,  E'{"Partial": {"label": "\\u0110\\u00fang m\\u1ed9t ph\\u1ea7n", "criteria": "Nh\\u1eadn ra nguy c\\u01a1 l\\u1eb7p nh\\u01b0ng ch\\u01b0a n\\u00eau \\u0111\\u01b0\\u1ee3c bi\\u1ec7n ph\\u00e1p kh\\u1ea3 thi."}, "Complete": {"label": "\\u0110\\u1ea7y \\u0111\\u1ee7", "criteria": "Gi\\u1ea3i th\\u00edch nguy c\\u01a1 chu tr\\u00ecnh, \\u0111\\u01b0a bi\\u1ec7n ph\\u00e1p \\u0111\\u01b0\\u1eddng \\u0111i/CYCLE ph\\u00f9 h\\u1ee3p, ch\\u1ec9 r\\u00f5 UNION so s\\u00e1nh to\\u00e0n b\\u1ed9 c\\u1ed9t v\\u00e0 kh\\u00f4ng b\\u1ea3o \\u0111\\u1ea3m d\\u1eebng khi depth/path thay \\u0111\\u1ed5i."}, "Incomplete": {"label": "Ch\\u01b0a \\u0111\\u1ea1t", "criteria": "Kh\\u00f4ng tr\\u1ea3 l\\u1eddi ho\\u1eb7c tr\\u1ea3 l\\u1eddi sai n\\u1ed9i dung c\\u1ed1t l\\u00f5i c\\u1ee7a \\u0111\\u1ec1 b\\u00e0i."}, "Mostly Complete": {"label": "G\\u1ea7n \\u0111\\u1ea7y \\u0111\\u1ee7", "criteria": "N\\u00eau \\u0111\\u00fang m\\u1ed9t c\\u00e1ch ch\\u1ed1ng l\\u1eb7p nh\\u01b0ng ch\\u01b0a gi\\u1ea3i th\\u00edch gi\\u1edbi h\\u1ea1n c\\u1ee7a UNION hay gi\\u1edbi h\\u1ea1n \\u0111\\u1ed9 s\\u00e2u."}}'::jsonb),
(91, 'vi', '1436e048b8c01a67c4d4b8386b095fea65b702d69d53dec252f26a9d0b51dd08', 'Cho sẵn bảng sinh_vien và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Liệt kê mã, họ tên và điểm của sinh viên có điểm cao hơn điểm trung bình của chính lớp mình', NULL, '{}'::jsonb, '{}'::jsonb),
(92, 'vi', '24fe3095b59823abad4001294f14a55d158a32b8c69e1e1b53312e635d9c1205', 'Cho sẵn bảng students và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Tìm các lớp có điểm trung bình từ 8 trở lên. Bỏ qua score NULL khi tính trung bình. Trả về class_id và average_score.', NULL, '{}'::jsonb, '{}'::jsonb),
(93, 'vi', '852b46f3ad2378a2b298aba7c68479a9079a8865ce5ddaddab20804d36a4ce05', 'Cho sẵn bảng students, classes và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:

Kết hợp students và classes để lấy students.id thành student_id, students.name thành student_name, classes.name thành class_name cho sinh viên có lớp tương ứng.', NULL, '{}'::jsonb, '{}'::jsonb);

-- clo_concept: 22 rows
INSERT INTO "clo_concept" ("clo_id", "concept_id", "mapping_source", "status")  VALUES
(1, 1, 'admin', 'confirmed'),
(1, 2, 'admin', 'confirmed'),
(2, 3, 'admin', 'confirmed'),
(2, 4, 'admin', 'confirmed'),
(2, 11, 'admin', 'confirmed'),
(3, 5, 'admin', 'confirmed'),
(3, 6, 'admin', 'confirmed'),
(4, 7, 'admin', 'confirmed'),
(5, 8, 'admin', 'confirmed'),
(5, 9, 'admin', 'confirmed'),
(5, 10, 'admin', 'confirmed'),
(6, 12, 'admin', 'confirmed'),
(6, 14, 'admin', 'confirmed'),
(7, 15, 'admin', 'confirmed'),
(7, 16, 'admin', 'confirmed'),
(7, 17, 'admin', 'confirmed'),
(7, 20, 'admin', 'confirmed'),
(8, 19, 'admin', 'confirmed'),
(9, 18, 'admin', 'confirmed'),
(9, 21, 'admin', 'confirmed'),
(9, 22, 'admin', 'confirmed'),
(10, 13, 'admin', 'confirmed');

-- question_concept: 147 rows
INSERT INTO "question_concept" ("question_id", "concept_id", "tag_source", "is_required", "confirmed", "review_status")  VALUES
(1, 1, 'admin', true, true, 'confirmed'),
(2, 1, 'admin', false, true, 'confirmed'),
(2, 2, 'admin', false, true, 'confirmed'),
(3, 3, 'admin', false, true, 'confirmed'),
(4, 15, 'admin', false, true, 'confirmed'),
(4, 17, 'admin', false, true, 'confirmed'),
(4, 20, 'admin', false, true, 'confirmed'),
(5, 15, 'admin', false, true, 'confirmed'),
(5, 16, 'admin', false, true, 'confirmed'),
(8, 18, 'admin', false, true, 'confirmed'),
(8, 21, 'admin', false, true, 'confirmed'),
(8, 22, 'admin', false, true, 'confirmed'),
(9, 2, 'admin', false, true, 'confirmed'),
(9, 12, 'admin', false, true, 'confirmed'),
(9, 14, 'admin', false, true, 'confirmed'),
(10, 9, 'admin', false, true, 'confirmed'),
(10, 13, 'admin', false, true, 'confirmed'),
(11, 2, 'admin', false, true, 'confirmed'),
(11, 9, 'admin', false, true, 'confirmed'),
(11, 10, 'admin', false, true, 'confirmed'),
(12, 1, 'admin', false, true, 'confirmed'),
(12, 2, 'admin', false, true, 'confirmed'),
(12, 12, 'admin', false, true, 'confirmed'),
(13, 1, 'admin', false, true, 'confirmed'),
(13, 2, 'admin', false, true, 'confirmed'),
(14, 1, 'admin', false, true, 'confirmed'),
(14, 3, 'admin', false, true, 'confirmed'),
(15, 4, 'admin', false, true, 'confirmed'),
(15, 11, 'admin', false, true, 'confirmed'),
(16, 2, 'admin', false, true, 'confirmed'),
(16, 12, 'admin', false, true, 'confirmed'),
(16, 14, 'admin', false, true, 'confirmed'),
(17, 15, 'admin', false, true, 'confirmed'),
(17, 17, 'admin', false, true, 'confirmed'),
(17, 20, 'admin', false, true, 'confirmed'),
(18, 5, 'admin', false, true, 'confirmed'),
(18, 6, 'admin', false, true, 'confirmed'),
(19, 2, 'admin', false, true, 'confirmed'),
(19, 4, 'admin', false, true, 'confirmed'),
(19, 11, 'admin', false, true, 'confirmed'),
(20, 9, 'admin', false, true, 'confirmed'),
(20, 13, 'admin', false, true, 'confirmed'),
(21, 1, 'admin', false, true, 'confirmed'),
(22, 1, 'admin', false, true, 'confirmed'),
(22, 2, 'admin', false, true, 'confirmed'),
(23, 3, 'admin', false, true, 'confirmed'),
(24, 1, 'admin', false, true, 'confirmed'),
(24, 4, 'admin', false, true, 'confirmed'),
(25, 4, 'admin', false, true, 'confirmed'),
(25, 11, 'admin', false, true, 'confirmed'),
(26, 1, 'admin', false, true, 'confirmed'),
(26, 2, 'admin', false, true, 'confirmed'),
(27, 1, 'admin', false, true, 'confirmed'),
(27, 4, 'admin', false, true, 'confirmed'),
(27, 11, 'admin', false, true, 'confirmed'),
(28, 2, 'admin', false, true, 'confirmed'),
(28, 4, 'admin', false, true, 'confirmed'),
(28, 11, 'admin', false, true, 'confirmed'),
(29, 7, 'admin', false, true, 'confirmed'),
(30, 7, 'admin', false, true, 'confirmed'),
(31, 8, 'admin', false, true, 'confirmed'),
(32, 8, 'admin', false, true, 'confirmed'),
(33, 5, 'admin', false, true, 'confirmed'),
(34, 5, 'admin', false, true, 'confirmed'),
(34, 6, 'admin', false, true, 'confirmed'),
(35, 9, 'admin', false, true, 'confirmed'),
(36, 13, 'admin', false, true, 'confirmed'),
(37, 19, 'admin', false, true, 'confirmed'),
(38, 5, 'admin', false, true, 'confirmed'),
(39, 6, 'admin', false, true, 'confirmed'),
(40, 1, 'admin', false, true, 'confirmed'),
(41, 2, 'admin', false, true, 'confirmed'),
(42, 2, 'admin', false, true, 'confirmed'),
(43, 4, 'admin', false, true, 'confirmed'),
(44, 3, 'admin', false, true, 'confirmed'),
(45, 4, 'admin', false, true, 'confirmed'),
(46, 5, 'admin', false, true, 'confirmed'),
(47, 6, 'admin', false, true, 'confirmed'),
(48, 8, 'admin', false, true, 'confirmed'),
(49, 9, 'admin', false, true, 'confirmed'),
(50, 10, 'admin', false, true, 'confirmed'),
(51, 7, 'admin', false, true, 'confirmed'),
(52, 7, 'admin', false, true, 'confirmed'),
(53, 7, 'admin', false, true, 'confirmed'),
(54, 13, 'admin', false, true, 'confirmed'),
(55, 13, 'admin', false, true, 'confirmed'),
(56, 12, 'admin', false, true, 'confirmed'),
(57, 12, 'admin', false, true, 'confirmed'),
(58, 14, 'admin', false, true, 'confirmed'),
(59, 15, 'admin', false, true, 'confirmed'),
(60, 16, 'admin', false, true, 'confirmed'),
(61, 16, 'admin', false, true, 'confirmed'),
(62, 17, 'admin', false, true, 'confirmed'),
(62, 20, 'admin', false, true, 'confirmed'),
(63, 20, 'admin', false, true, 'confirmed'),
(64, 15, 'admin', false, true, 'confirmed'),
(64, 20, 'admin', false, true, 'confirmed'),
(65, 19, 'admin', false, true, 'confirmed'),
(66, 19, 'admin', false, true, 'confirmed'),
(67, 18, 'admin', false, true, 'confirmed'),
(68, 22, 'admin', false, true, 'confirmed'),
(69, 18, 'admin', false, true, 'confirmed'),
(69, 21, 'admin', false, true, 'confirmed'),
(70, 1, 'admin', false, true, 'confirmed'),
(70, 2, 'admin', false, true, 'confirmed'),
(71, 1, 'admin', false, true, 'confirmed'),
(71, 2, 'admin', false, true, 'confirmed'),
(72, 4, 'admin', false, true, 'confirmed'),
(73, 4, 'admin', false, true, 'confirmed'),
(73, 11, 'admin', false, true, 'confirmed'),
(74, 3, 'admin', false, true, 'confirmed'),
(75, 2, 'admin', false, true, 'confirmed'),
(75, 12, 'admin', false, true, 'confirmed'),
(76, 12, 'admin', false, true, 'confirmed'),
(76, 14, 'admin', false, true, 'confirmed'),
(77, 15, 'admin', false, true, 'confirmed'),
(77, 16, 'admin', false, true, 'confirmed'),
(78, 15, 'admin', false, true, 'confirmed'),
(78, 17, 'admin', false, true, 'confirmed'),
(79, 15, 'admin', false, true, 'confirmed'),
(79, 20, 'admin', false, true, 'confirmed'),
(80, 19, 'admin', false, true, 'confirmed'),
(81, 12, 'admin', false, true, 'confirmed'),
(81, 15, 'admin', false, true, 'confirmed'),
(81, 16, 'admin', false, true, 'confirmed'),
(82, 5, 'admin', false, true, 'confirmed'),
(82, 6, 'admin', false, true, 'confirmed'),
(83, 7, 'admin', false, true, 'confirmed'),
(84, 9, 'admin', false, true, 'confirmed'),
(84, 13, 'admin', false, true, 'confirmed'),
(85, 12, 'admin', false, true, 'confirmed'),
(85, 14, 'admin', false, true, 'confirmed'),
(86, 4, 'admin', false, true, 'confirmed'),
(86, 15, 'admin', false, true, 'confirmed'),
(86, 16, 'admin', false, true, 'confirmed'),
(87, 18, 'admin', false, true, 'confirmed'),
(87, 21, 'admin', false, true, 'confirmed'),
(88, 18, 'admin', false, true, 'confirmed'),
(88, 21, 'admin', false, true, 'confirmed'),
(88, 22, 'admin', false, true, 'confirmed'),
(89, 19, 'admin', false, true, 'confirmed'),
(91, 2, 'admin', false, true, 'confirmed'),
(91, 12, 'admin', false, true, 'confirmed'),
(91, 14, 'admin', false, true, 'confirmed'),
(92, 4, 'admin', false, true, 'confirmed'),
(92, 11, 'admin', false, true, 'confirmed'),
(93, 3, 'admin', false, true, 'confirmed');

-- concept_dependency: 27 rows
INSERT INTO "concept_dependency" ("concept_id", "prerequisite_concept_id")  VALUES
(2, 1),
(3, 1),
(4, 1),
(6, 5),
(7, 5),
(7, 6),
(9, 2),
(10, 2),
(11, 4),
(12, 1),
(12, 2),
(13, 8),
(13, 9),
(13, 10),
(14, 12),
(15, 4),
(16, 15),
(17, 15),
(18, 2),
(18, 3),
(19, 12),
(20, 15),
(21, 18),
(21, 22),
(22, 1),
(22, 2),
(22, 3);
SELECT setval(pg_get_serial_sequence('concept', 'concept_id'), GREATEST(COALESCE((SELECT MAX("concept_id") FROM "concept"), 0), 1), EXISTS(SELECT 1 FROM "concept"));
SELECT setval(pg_get_serial_sequence('course_learning_outcome', 'clo_id'), GREATEST(COALESCE((SELECT MAX("clo_id") FROM "course_learning_outcome"), 0), 1), EXISTS(SELECT 1 FROM "course_learning_outcome"));
SELECT setval(pg_get_serial_sequence('question', 'question_id'), GREATEST(COALESCE((SELECT MAX("question_id") FROM "question"), 0), 1), EXISTS(SELECT 1 FROM "question"));
SELECT setval(pg_get_serial_sequence('mcq_option', 'option_id'), GREATEST(COALESCE((SELECT MAX("option_id") FROM "mcq_option"), 0), 1), EXISTS(SELECT 1 FROM "mcq_option"));
SELECT setval(pg_get_serial_sequence('sql_test_dataset', 'dataset_id'), GREATEST(COALESCE((SELECT MAX("dataset_id") FROM "sql_test_dataset"), 0), 1), EXISTS(SELECT 1 FROM "sql_test_dataset"));
SELECT setval(pg_get_serial_sequence('rubric', 'rubric_id'), GREATEST(COALESCE((SELECT MAX("rubric_id") FROM "rubric"), 0), 1), EXISTS(SELECT 1 FROM "rubric"));
COMMIT;

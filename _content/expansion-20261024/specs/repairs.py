"""Targeted repairs for legacy questions with missing explanations.

Each entry supplies the canonical English explanation, the Vietnamese
explanation for the existing translation, and verified source references.
The repair script updates the live row in place (attempts keep their frozen
question snapshots) and revalidates through the production service.
"""

from sources import (
    CODD_1971,
    PG_AGGREGATE,
    PG_COMPARISON,
    PG_CONSTRAINTS,
    PG_CREATE_INDEX,
    PG_CREATE_TABLE,
    PG_DELETE,
    PG_EXPRESSIONS,
    PG_INDEX_TYPES,
    PG_INDEXES,
    PG_INSERT,
    PG_JOIN_TUTORIAL,
    PG_ROUTINE_VACUUM,
    PG_SELECT,
    PG_SUBQUERY_FUNCTIONS,
    PG_TABLE_EXPRESSIONS,
    PG_UPDATE,
    WATT_DB_DESIGN,
)


def repair(en, vi, refs, tags, reference_answer=None):
    return {
        "explanation_en": en,
        "explanation_vi": vi,
        "source_refs": refs,
        "tags": tags,
        "reference_answer": reference_answer,
    }


REPAIRS = {
    2: repair(
        "WHERE evaluates a Boolean condition for each candidate row before "
        "grouping; rows for which the condition is not true are removed. "
        "ORDER BY sorts the result, GROUP BY forms groups, and LIMIT restricts "
        "how many rows are returned.",
        "WHERE đánh giá điều kiện Boolean cho từng dòng ứng viên trước khi gom "
        "nhóm; các dòng mà điều kiện không đúng bị loại. ORDER BY sắp xếp kết "
        "quả, GROUP BY tạo nhóm, còn LIMIT giới hạn số dòng trả về.",
        [PG_SELECT],
        ["sql", "select", "where"],
    ),
    3: repair(
        "INNER JOIN keeps only row pairs for which the join condition is true; "
        "unmatched rows from either side are discarded. LEFT and FULL joins "
        "preserve unmatched rows through NULL extension, and CROSS JOIN pairs "
        "every row with every row.",
        "INNER JOIN chỉ giữ các cặp dòng mà điều kiện nối đúng; các dòng không "
        "khớp ở một trong hai bên bị loại. LEFT và FULL JOIN giữ lại dòng "
        "không khớp bằng cách bổ sung NULL, còn CROSS JOIN ghép mọi dòng với "
        "mọi dòng.",
        [PG_JOIN_TUTORIAL, PG_TABLE_EXPRESSIONS],
        ["sql", "join", "inner-join"],
    ),
    4: repair(
        "The projection selects the name column from every row of customers; "
        "an empty table yields an empty result with the same one-column shape. "
        "No ORDER BY is requested, so row order is not part of the expected "
        "result.",
        "Phép chiếu chọn cột name từ mọi dòng của customers; bảng rỗng cho kết "
        "quả rỗng với cùng cấu trúc một cột. Truy vấn không yêu cầu ORDER BY "
        "nên thứ tự dòng không thuộc kết quả mong đợi.",
        [PG_SELECT],
        ["sql", "select", "projection"],
    ),
    6: repair(
        "The SELECT list (projection list) names the expressions and columns "
        "returned; it can also compute expressions and assign output labels. "
        "ORDER BY only orders rows, and HAVING filters groups after "
        "aggregation.",
        "Danh sách sau SELECT (danh sách chiếu) xác định các biểu thức và cột "
        "được trả về; nó cũng có thể tính biểu thức và đặt nhãn đầu ra. ORDER "
        "BY chỉ sắp xếp dòng, còn HAVING lọc nhóm sau khi tổng hợp.",
        [PG_SELECT],
        ["sql", "select", "projection"],
    ),
    7: repair(
        "amount >= 20 evaluates to UNKNOWN when amount is NULL, and WHERE keeps "
        "only rows whose condition is TRUE, so the NULL row is excluded. "
        "amount IS NULL selects exactly that row, and IS NOT DISTINCT FROM NULL "
        "is also true for it.",
        "amount >= 20 cho giá trị UNKNOWN khi amount là NULL, và WHERE chỉ giữ "
        "các dòng có điều kiện TRUE, nên dòng NULL bị loại. amount IS NULL chọn "
        "đúng dòng đó, còn IS NOT DISTINCT FROM NULL cũng đúng với nó.",
        [PG_SELECT, PG_COMPARISON],
        ["sql", "null-handling", "where"],
    ),
    8: repair(
        "INNER JOIN emits only combined rows that satisfy the join condition. "
        "An unmatched left or right row is not emitted at all; NULL extension "
        "belongs to outer joins, and a join never invents a matching record.",
        "INNER JOIN chỉ phát ra các dòng kết hợp thỏa điều kiện nối. Dòng "
        "không khớp ở bên trái hoặc bên phải không được phát ra; việc bổ sung "
        "NULL thuộc về outer join, và phép nối không tự tạo bản ghi khớp.",
        [PG_JOIN_TUTORIAL, PG_TABLE_EXPRESSIONS],
        ["sql", "join", "inner-join"],
    ),
    9: repair(
        "GROUP BY partitions the input rows into one group per distinct "
        "region_id and evaluates SUM(amount) once per group, producing one "
        "output row per group. It does not sort individual sales and does not "
        "change table constraints.",
        "GROUP BY chia các dòng đầu vào thành một nhóm cho mỗi region_id khác "
        "nhau và tính SUM(amount) một lần cho mỗi nhóm, tạo một dòng kết quả "
        "cho mỗi nhóm. Nó không sắp xếp từng giao dịch bán hàng và không thay "
        "đổi ràng buộc của bảng.",
        [PG_TABLE_EXPRESSIONS, PG_AGGREGATE],
        ["sql", "group-by", "aggregate"],
    ),
    10: repair(
        "Logical evaluation runs FROM/JOIN, WHERE, GROUP BY, HAVING, SELECT, "
        "DISTINCT, ORDER BY, LIMIT. HAVING therefore runs after groups and "
        "aggregates exist, which is why it can test an aggregate result such "
        "as SUM(amount) >= 30.",
        "Thứ tự đánh giá logic là FROM/JOIN, WHERE, GROUP BY, HAVING, SELECT, "
        "DISTINCT, ORDER BY, LIMIT. Vì vậy HAVING chạy sau khi các nhóm và giá "
        "trị tổng hợp đã hình thành, nên nó có thể kiểm tra kết quả tổng hợp "
        "như SUM(amount) >= 30.",
        [PG_TABLE_EXPRESSIONS, PG_SELECT],
        ["sql", "having", "group-by"],
    ),
    11: repair(
        "Aggregates ignore NULL inputs. AVG over an empty set, or a set "
        "containing only NULLs, returns NULL rather than zero; a scalar "
        "subquery therefore yields NULL, which can make an enclosing "
        "comparison UNKNOWN.",
        "Các hàm tổng hợp bỏ qua đầu vào NULL. AVG trên tập rỗng, hoặc tập chỉ "
        "chứa NULL, trả về NULL chứ không phải 0; do đó truy vấn con vô hướng "
        "trả về NULL, có thể làm phép so sánh bao ngoài thành UNKNOWN.",
        [PG_AGGREGATE, PG_EXPRESSIONS],
        ["sql", "aggregate", "subquery", "null-handling"],
    ),
    12: repair(
        "A many-to-many relationship becomes an associative (junction) table "
        "whose columns are foreign keys to the two entity tables, usually with "
        "a composite primary key or unique constraint over the pair. Storing "
        "key lists or merging entities violates atomicity and creates update "
        "anomalies.",
        "Mối quan hệ nhiều-nhiều được biểu diễn bằng bảng kết hợp (junction) "
        "gồm các khóa ngoại tới hai bảng thực thể, thường có khóa chính ghép "
        "hoặc ràng buộc duy nhất trên cặp khóa. Lưu danh sách khóa hoặc gộp "
        "thực thể sẽ vi phạm tính nguyên tố và gây dị thường cập nhật.",
        [WATT_DB_DESIGN, CODD_1971],
        ["database-design", "er-modeling", "many-to-many"],
    ),
    13: repair(
        "A repeating multivalued attribute is removed by moving each value "
        "into rows of a related table at atomic granularity, with a foreign "
        "key back to the owning entity. A longer delimited string still stores "
        "several values in one cell and does not satisfy 1NF.",
        "Thuộc tính đa trị lặp lại được loại bỏ bằng cách chuyển từng giá trị "
        "thành các dòng của một bảng liên quan ở mức nguyên tố, có khóa ngoại "
        "trỏ về thực thể sở hữu. Một chuỗi phân tách dài hơn vẫn lưu nhiều giá "
        "trị trong một ô và không đạt 1NF.",
        [WATT_DB_DESIGN, CODD_1971],
        ["database-design", "normalization", "first-normal-form"],
    ),
    14: repair(
        "X -> Y means that any two tuples agreeing on X must agree on Y; "
        "equivalently, X functionally determines at most one Y value. It does "
        "not require X and Y to be equal and does not imply the reverse "
        "dependency.",
        "X -> Y nghĩa là hai bộ dòng bất kỳ giống nhau trên X thì phải giống "
        "nhau trên Y; tương đương, X xác định hàm nhiều nhất một giá trị Y. Nó "
        "không đòi X và Y bằng nhau và không suy ra phụ thuộc ngược.",
        [WATT_DB_DESIGN, CODD_1971],
        ["database-design", "functional-dependency"],
    ),
    15: repair(
        "1NF requires each attribute value to be atomic. One row per "
        "student-course pair keeps every cell single-valued; a list in one "
        "column or repeating course_1..course_n columns stores multiple values "
        "per attribute.",
        "1NF yêu cầu mỗi giá trị thuộc tính phải nguyên tố. Mỗi dòng ứng với "
        "một cặp sinh viên-học phần giữ mọi ô đơn trị; danh sách trong một cột "
        "hoặc các cột course_1..course_n lặp lại lưu nhiều giá trị trong một "
        "thuộc tính.",
        [WATT_DB_DESIGN, CODD_1971],
        ["database-design", "normalization", "first-normal-form"],
    ),
    16: repair(
        "2NF forbids a non-prime attribute from depending on a proper subset "
        "of a candidate key. With composite key (student_id, course_id), "
        "student_id -> student_name is partial; (student_id, course_id) -> "
        "grade and the trivial student_id -> student_id are not violations.",
        "2NF cấm thuộc tính không khóa phụ thuộc vào một tập con thực sự của "
        "khóa ứng viên. Với khóa ghép (student_id, course_id), student_id -> "
        "student_name là phụ thuộc bộ phận; (student_id, course_id) -> grade và "
        "phụ thuộc hiển nhiên student_id -> student_id không vi phạm.",
        [WATT_DB_DESIGN, CODD_1971],
        ["database-design", "normalization", "second-normal-form"],
    ),
    17: repair(
        "The chain student_id -> dept_id -> dept_name is a transitive "
        "dependency because dept_id is not a superkey. Removing dept_name into "
        "Department(dept_id, dept_name) and keeping dept_id as a foreign key in "
        "the student relation eliminates the redundancy while preserving the "
        "join.",
        "Chuỗi student_id -> dept_id -> dept_name là phụ thuộc bắc cầu vì "
        "dept_id không phải siêu khóa. Tách dept_name vào Department(dept_id, "
        "dept_name) và giữ dept_id làm khóa ngoại trong quan hệ sinh viên loại "
        "bỏ dư thừa mà vẫn bảo toàn phép nối.",
        [WATT_DB_DESIGN, CODD_1971],
        ["database-design", "normalization", "third-normal-form"],
    ),
    18: repair(
        "The query projects id and amount for every sales row, including a row "
        "whose amount is NULL; an empty table yields an empty result with the "
        "same two-column shape. No ordering is required.",
        "Truy vấn chiếu id và amount cho mọi dòng sales, kể cả dòng có amount "
        "NULL; bảng rỗng cho kết quả rỗng với cùng cấu trúc hai cột. Không yêu "
        "cầu thứ tự.",
        [PG_SELECT],
        ["sql", "select", "projection"],
    ),
    19: repair(
        "WHERE keeps rows for which amount >= 20 is TRUE. A NULL amount makes "
        "the comparison UNKNOWN, so that row is excluded, and an empty table "
        "returns no rows.",
        "WHERE giữ các dòng mà amount >= 20 là TRUE. amount NULL làm phép so "
        "sánh thành UNKNOWN nên dòng đó bị loại, và bảng rỗng trả về không "
        "dòng.",
        [PG_SELECT, PG_COMPARISON],
        ["sql", "where", "comparison"],
    ),
    20: repair(
        "An inner join matches each sale to the region with the same id "
        "through region_id; only matching pairs are returned, and an empty "
        "sales table produces no rows.",
        "Inner join ghép mỗi dòng sales với region có id tương ứng qua "
        "region_id; chỉ các cặp khớp được trả về, và bảng sales rỗng không sinh "
        "dòng nào.",
        [PG_JOIN_TUTORIAL, PG_TABLE_EXPRESSIONS],
        ["sql", "join"],
    ),
    21: repair(
        "GROUP BY region_id forms one group per region, and SUM(amount) adds "
        "the non-NULL amounts in each group; a group whose amounts are all NULL "
        "yields SUM NULL. The empty-table dataset returns no groups.",
        "GROUP BY region_id tạo một nhóm cho mỗi region, và SUM(amount) cộng "
        "các amount khác NULL trong mỗi nhóm; nhóm mà mọi amount đều NULL cho "
        "SUM là NULL. Tập dữ liệu bảng rỗng không có nhóm nào.",
        [PG_TABLE_EXPRESSIONS, PG_AGGREGATE],
        ["sql", "group-by", "aggregate"],
    ),
    22: repair(
        "HAVING filters groups after aggregation, keeping region_id groups "
        "whose SUM(amount) is at least 30. Rows with NULL amount do not "
        "contribute to SUM, and no groups exist for an empty table.",
        "HAVING lọc các nhóm sau khi tổng hợp, giữ các nhóm region_id có "
        "SUM(amount) từ 30 trở lên. Các dòng amount NULL không đóng góp vào "
        "SUM, và bảng rỗng không có nhóm nào.",
        [PG_TABLE_EXPRESSIONS, PG_AGGREGATE],
        ["sql", "having", "group-by"],
    ),
    23: repair(
        "The scalar subquery computes AVG(amount) over the whole table once, "
        "ignoring NULLs; the outer query keeps rows whose amount is greater "
        "than that average. If the subquery returns NULL because there are no "
        "non-NULL amounts, every comparison is UNKNOWN and no rows are "
        "returned.",
        "Truy vấn con vô hướng tính AVG(amount) trên toàn bảng một lần, bỏ qua "
        "NULL; truy vấn ngoài giữ các dòng có amount lớn hơn mức trung bình đó. "
        "Nếu truy vấn con trả về NULL vì không có amount khác NULL, mọi phép so "
        "sánh thành UNKNOWN và không dòng nào được trả về.",
        [PG_EXPRESSIONS, PG_SUBQUERY_FUNCTIONS, PG_AGGREGATE],
        ["sql", "subquery", "aggregate"],
    ),
    24: repair(
        "The given dependencies create partial dependencies on the composite "
        "key (student_name via student_id, course_title via course_id) and a "
        "transitive dependency dept_name via dept_id. Normalization separates "
        "Student(student_id, student_name, dept_id), Department(dept_id, "
        "dept_name), Course(course_id, course_title), and "
        "Enrollment(student_id, course_id, grade). Enrollment is the "
        "many-to-many junction. Each step is a lossless join because the shared "
        "attribute is a key of one side, and every dependency is enforced in a "
        "relation, so the decomposition is dependency-preserving.",
        "Các phụ thuộc đã cho tạo phụ thuộc bộ phận vào khóa ghép (student_name "
        "qua student_id, course_title qua course_id) và phụ thuộc bắc cầu "
        "dept_name qua dept_id. Chuẩn hóa tách thành Student(student_id, "
        "student_name, dept_id), Department(dept_id, dept_name), "
        "Course(course_id, course_title) và Enrollment(student_id, course_id, "
        "grade). Enrollment là bảng kết hợp nhiều-nhiều. Mỗi bước là phép nối "
        "không mất mát vì thuộc tính chung là khóa của một bên, và mọi phụ "
        "thuộc đều được thực thi trong một quan hệ, nên phân rã bảo toàn phụ "
        "thuộc.",
        [WATT_DB_DESIGN, CODD_1971],
        ["database-design", "normalization", "functional-dependency", "essay"],
    ),
    25: repair(
        "UPDATE changes values in existing rows and leaves the table definition "
        "intact; it is DML. SELECT only reads, CREATE TABLE defines a new "
        "table, and ALTER TABLE changes the definition.",
        "UPDATE thay đổi giá trị trong các dòng hiện có và giữ nguyên định "
        "nghĩa bảng; đây là DML. SELECT chỉ đọc, CREATE TABLE định nghĩa bảng "
        "mới, còn ALTER TABLE thay đổi định nghĩa.",
        [PG_UPDATE],
        ["sql", "dml", "update"],
    ),
    26: repair(
        "CREATE TABLE declares columns, types, and constraints, including a "
        "FOREIGN KEY that references another table's key. INSERT, UPDATE, and "
        "SELECT operate on data rather than defining referential integrity.",
        "CREATE TABLE khai báo cột, kiểu dữ liệu và ràng buộc, bao gồm FOREIGN "
        "KEY tham chiếu khóa của bảng khác. INSERT, UPDATE và SELECT thao tác "
        "trên dữ liệu chứ không định nghĩa toàn vẹn tham chiếu.",
        [PG_CREATE_TABLE, PG_CONSTRAINTS],
        ["sql", "ddl", "foreign-key"],
    ),
    27: repair(
        "DDL (CREATE TABLE, ALTER TABLE) defines structure, primary keys and "
        "the FOREIGN KEY from Employee.dept_id to Department.dept_id. DML "
        "changes rows: INSERT adds, UPDATE modifies, DELETE removes. A targeted "
        "salary update must include a WHERE predicate; without it every row can "
        "be changed. Deleting a referenced department is rejected unless the "
        "foreign key declares a permitted action such as ON DELETE CASCADE, "
        "which must never be assumed. These statements are conceptual here "
        "because the assessment sandbox accepts one read-only SELECT and rolls "
        "back, so DDL/DML cannot run.",
        "DDL (CREATE TABLE, ALTER TABLE) định nghĩa cấu trúc, khóa chính và "
        "FOREIGN KEY từ Employee.dept_id tới Department.dept_id. DML thay đổi "
        "dòng: INSERT thêm, UPDATE sửa, DELETE xóa. Cập nhật lương có mục tiêu "
        "phải có điều kiện WHERE; nếu thiếu, mọi dòng có thể bị thay đổi. Xóa "
        "một phòng ban đang được tham chiếu bị từ chối trừ khi khóa ngoại khai "
        "báo hành động được phép như ON DELETE CASCADE, và không được mặc định "
        "điều đó. Các câu lệnh ở đây chỉ mang tính khái niệm vì sandbox đánh "
        "giá chỉ nhận một SELECT chỉ đọc và luôn rollback, nên DDL/DML không "
        "thể chạy.",
        [PG_CREATE_TABLE, PG_CONSTRAINTS, PG_INSERT, PG_UPDATE, PG_DELETE],
        ["sql", "ddl", "dml", "referential-integrity", "essay"],
    ),
    450: repair(
        "A B-tree index on the filtered column can turn a sequential scan into "
        "a selective index scan or bitmap heap scan for equality and range "
        "predicates, reducing pages read and CPU. Every INSERT adds an index "
        "entry, every UPDATE of an indexed key must maintain it, and DELETE "
        "leaves entries for vacuum to clean, adding WAL, buffer, and "
        "page-maintenance work. The index may not be worthwhile when the "
        "predicate is not selective and a sequential scan is cheaper, when the "
        "table is small, when the column is rarely filtered, or when write "
        "volume dominates the read benefit.",
        "Chỉ mục B-tree trên cột được lọc có thể biến tuần tự quét thành quét "
        "chỉ mục chọn lọc hoặc quét bitmap cho điều kiện bằng và khoảng, giảm "
        "số trang đọc và CPU. Mỗi INSERT thêm một mục chỉ mục, mỗi UPDATE khóa "
        "được đánh chỉ mục phải bảo trì mục đó, và DELETE để lại mục cho vacuum "
        "dọn dẹp, làm tăng WAL, buffer và công việc bảo trì trang. Chỉ mục có "
        "thể không đáng tạo khi điều kiện không chọn lọc và tuần tự quét rẻ "
        "hơn, khi bảng nhỏ, khi cột ít được lọc, hoặc khi khối lượng ghi chiếm "
        "ưu thế so với lợi ích đọc.",
        [PG_INDEXES, PG_INDEX_TYPES, PG_CREATE_INDEX, PG_ROUTINE_VACUUM],
        ["postgres", "indexing", "write-amplification", "essay"],
        reference_answer=(
            "A B-tree index accelerates selective equality and range lookups "
            "by locating matching entries in sorted order instead of scanning "
            "the heap. It costs maintenance on every INSERT, on UPDATE of an "
            "indexed key, and on DELETE until vacuum removes dead entries, "
            "which adds WAL and buffer work and can cause page splits and "
            "bloat. It is not worthwhile when most rows match the predicate, "
            "the table is small, the column is rarely filtered, or writes "
            "dominate; partial or covering indexes can sometimes reduce the "
            "cost when the workload is known."
        ),
    ),
}

"""A2 Performance blueprint fill: index reasoning without fake SQL practicals.

The A2 Performance blueprint is 6 MCQ / 0 SQL / 2 essay at EASY/MEDIUM because
index selection, plan reading and workload trade-offs cannot be measured by a
read-only SELECT practical. Every item measures index reasoning directly.
"""

from gap_lib import essay_vi, mcq_vi
from sources import (
    PG_CONSTRAINTS,
    PG_CREATE_INDEX,
    PG_EXPLAIN,
    PG_INDEX_MULTICOLUMN,
    PG_INDEX_ORDERING,
    PG_INDEX_TYPES,
    PG_INDEXES,
    PG_STATS,
    PG_TYPECONV,
)

QUESTIONS = [
    # EASY: 3 MCQ (difficulty 2)
    mcq_vi(
        "a2b-easy-fk-no-index",
        ["IDX"],
        2,
        (
            "A child table has a foreign key column customer_id referencing "
            "customers(customer_id). Does the foreign key automatically provide "
            "an index for queries that filter or join on the child's customer_id?"
        ),
        [
            "No. PostgreSQL does not create an index on the referencing column; "
            "add one when child lookups or parent deletes need it.",
            "Yes. The foreign key creates a unique index on the child column.",
            "Yes. The foreign key creates a B-tree index, but only for DELETE "
            "statements.",
            "No, and an index on the child column is never useful because the "
            "constraint already optimizes joins.",
        ],
        0,
        (
            "A foreign key constraint enforces referential integrity; it does not "
            "create an index on the referencing side. When a parent row is "
            "deleted or its key changes, PostgreSQL must find child rows that "
            "reference it, and joins on the child column also need an index. "
            "Without one, those operations can scan the whole child table. "
            "Primary key and UNIQUE constraints are the constraints that create "
            "indexes automatically."
        ),
        [PG_CONSTRAINTS, PG_INDEXES],
        vi_prompt=(
            "Một bảng con có cột khóa ngoại customer_id tham chiếu "
            "customers(customer_id). Khóa ngoại có tự động tạo chỉ mục cho các "
            "truy vấn lọc hoặc nối trên cột customer_id của bảng con không?"
        ),
        vi_options=[
            "Không. PostgreSQL không tạo chỉ mục trên cột tham chiếu; hãy thêm "
            "chỉ mục khi cần tra cứu bảng con hoặc khi xóa/cập nhật bảng cha.",
            "Có. Khóa ngoại tạo một chỉ mục duy nhất trên cột của bảng con.",
            "Có. Khóa ngoại tạo chỉ mục B-tree nhưng chỉ dùng cho câu lệnh DELETE.",
            "Không, và chỉ mục trên cột bảng con không bao giờ hữu ích vì ràng "
            "buộc đã tối ưu hóa phép nối.",
        ],
        vi_explanation=(
            "Ràng buộc khóa ngoại bảo đảm toàn vẹn tham chiếu; nó không tạo chỉ "
            "mục ở phía tham chiếu. Khi xóa một dòng cha hoặc thay đổi khóa của "
            "nó, PostgreSQL phải tìm các dòng con tham chiếu tới nó, và phép nối "
            "trên cột của bảng con cũng cần chỉ mục. Nếu không có chỉ mục, các "
            "thao tác này có thể quét toàn bộ bảng con. Chỉ ràng buộc khóa chính "
            "và UNIQUE tự động tạo chỉ mục."
        ),
        tags=["postgresql", "performance", "index"],
    ),
    mcq_vi(
        "a2b-easy-constraint-index",
        ["IDX"],
        2,
        "Which constraint automatically creates an index on the constrained column in PostgreSQL?",
        [
            "A PRIMARY KEY or UNIQUE constraint.",
            "A CHECK constraint.",
            "A FOREIGN KEY constraint.",
            "A NOT NULL constraint.",
        ],
        0,
        (
            "PRIMARY KEY and UNIQUE constraints are enforced with a unique B-tree "
            "index, which is why lookups by the constrained columns are fast. "
            "CHECK and NOT NULL are validated per row without an index. A FOREIGN "
            "KEY is also validated without creating an index on the referencing "
            "column."
        ),
        [PG_CONSTRAINTS, PG_INDEXES],
        vi_prompt=(
            "Ràng buộc nào tự động tạo chỉ mục trên (các) cột được ràng buộc "
            "trong PostgreSQL?"
        ),
        vi_options=[
            "Ràng buộc PRIMARY KEY hoặc UNIQUE.",
            "Ràng buộc CHECK.",
            "Ràng buộc FOREIGN KEY.",
            "Ràng buộc NOT NULL.",
        ],
        vi_explanation=(
            "Ràng buộc PRIMARY KEY và UNIQUE được thực thi bằng một chỉ mục "
            "B-tree duy nhất, nhờ đó tra cứu theo các cột này nhanh. CHECK và NOT "
            "NULL được kiểm tra trên từng dòng mà không cần chỉ mục. FOREIGN KEY "
            "cũng được kiểm tra mà không tạo chỉ mục trên cột tham chiếu."
        ),
        tags=["postgresql", "performance", "index"],
    ),
    mcq_vi(
        "a2b-easy-order-by-index",
        ["IDX"],
        2,
        (
            "A B-tree index exists on orders(created_at). A query runs "
            "SELECT * FROM orders ORDER BY created_at LIMIT 20. What is the main "
            "benefit of the index?"
        ),
        [
            "The index can return rows in created_at order, avoiding a full sort "
            "of the table.",
            "The index guarantees that only 20 rows are read from disk, regardless "
            "of any filters.",
            "The index stores the full rows, so the table is never read.",
            "The index makes the ORDER BY clause unnecessary in the SQL text.",
        ],
        0,
        (
            "An ordered index scan can produce rows in created_at order and stop "
            "after the requested limit, avoiding a sort of the whole table. It "
            "does not guarantee that only 20 rows are read when filters are "
            "applied or the plan combines it with other operations. A plain index "
            "stores keys and row references, not full rows, and the query still "
            "needs ORDER BY to define the required order."
        ),
        [PG_INDEX_ORDERING, PG_EXPLAIN],
        vi_prompt=(
            "Có chỉ mục B-tree trên orders(created_at). Một truy vấn chạy "
            "SELECT * FROM orders ORDER BY created_at LIMIT 20. Lợi ích chính "
            "của chỉ mục là gì?"
        ),
        vi_options=[
            "Chỉ mục có thể trả về các dòng theo thứ tự created_at, tránh phải "
            "sắp xếp toàn bộ bảng.",
            "Chỉ mục bảo đảm chỉ đọc 20 dòng từ đĩa, bất kể có bộ lọc nào.",
            "Chỉ mục lưu toàn bộ dòng nên bảng không bao giờ bị đọc.",
            "Chỉ mục làm cho mệnh đề ORDER BY không còn cần thiết trong câu SQL.",
        ],
        vi_explanation=(
            "Quét chỉ mục có thứ tự có thể trả về các dòng theo thứ tự "
            "created_at và dừng sau số dòng giới hạn, tránh sắp xếp toàn bảng. "
            "Nó không bảo đảm chỉ đọc 20 dòng khi có bộ lọc hoặc khi kế hoạch "
            "kết hợp nhiều thao tác. Chỉ mục thường lưu khóa và tham chiếu tới "
            "dòng, không lưu toàn bộ dòng, và truy vấn vẫn cần ORDER BY để xác "
            "định thứ tự."
        ),
        tags=["postgresql", "performance", "index"],
    ),
    # EASY: 2 essays (difficulty 2)
    essay_vi(
        "a2b-easy-selectivity",
        ["IDX"],
        2,
        (
            "A table has 2 million rows. Query A filters an indexed column "
            "matching about 0.1% of rows; Query B filters a different indexed "
            "column matching about 45% of rows. Explain why the planner may use "
            "an index for A but a sequential scan for B. Include selectivity, "
            "random I/O and the small-table case."
        ),
        (
            "A filter matching 0.1% of 2 million rows selects about 2000 rows. An "
            "index can locate those rows with relatively few page reads, so the "
            "random I/O is justified. A filter matching 45% selects about 900000 "
            "rows; visiting that many heap pages in index order causes many "
            "random reads and repeated page visits, while a sequential scan reads "
            "each page once in physical order. The planner compares estimated "
            "costs using statistics, so it may choose the sequential scan. For a "
            "small table, even a selective filter may use a sequential scan "
            "because the whole table fits in a few pages and the index lookup "
            "overhead is not repaid."
        ),
        (
            "Index usefulness depends on selectivity and access cost, not on the "
            "existence of an index alone. The planner estimates how many rows "
            "match from column statistics, estimates heap page visits, and "
            "compares the result with the cost of reading the table sequentially."
        ),
        [
            "Little or no explanation of selectivity; claims an index is always faster.",
            "Mentions that an index is used for few rows and a scan for many, but does not explain random versus sequential I/O or planner costing.",
            "Explains the selective versus broad filter trade-off and the role of statistics, but omits the small-table case or one cost factor.",
            "Explains selectivity, random heap access, sequential I/O, statistics-based costing and why a small table may still use a sequential scan.",
        ],
        [PG_EXPLAIN, PG_INDEXES, PG_STATS],
        vi_prompt=(
            "Một bảng có 2 triệu dòng. Truy vấn A lọc trên một cột có chỉ mục và "
            "khớp khoảng 0,1% số dòng; truy vấn B lọc trên một cột có chỉ mục "
            "khác và khớp khoảng 45% số dòng. Hãy giải thích vì sao bộ lập kế "
            "hoạch có thể dùng chỉ mục cho A nhưng quét tuần tự cho B. Nêu độ "
            "chọn lọc, I/O ngẫu nhiên và trường hợp bảng nhỏ."
        ),
        vi_reference=(
            "Bộ lọc khớp 0,1% của 2 triệu dòng chọn khoảng 2000 dòng. Chỉ mục có "
            "thể định vị các dòng này với tương đối ít lần đọc trang, nên I/O "
            "ngẫu nhiên là hợp lý. Bộ lọc khớp 45% chọn khoảng 900000 dòng; truy "
            "cập từng trang heap theo thứ tự chỉ mục gây nhiều lần đọc ngẫu nhiên "
            "và đọc lặp trang, trong khi quét tuần tự đọc mỗi trang một lần theo "
            "thứ tự vật lý. Bộ lập kế hoạch so sánh chi phí ước tính từ thống kê "
            "nên có thể chọn quét tuần tự. Với bảng nhỏ, ngay cả bộ lọc chọn lọc "
            "cao vẫn có thể dùng quét tuần tự vì toàn bảng nằm trong vài trang và "
            "chi phí tra chỉ mục không đáng."
        ),
        vi_explanation=(
            "Chỉ mục hữu ích hay không phụ thuộc vào độ chọn lọc và chi phí truy "
            "cập, không chỉ vào việc chỉ mục có tồn tại. Bộ lập kế hoạch ước "
            "lượng số dòng khớp từ thống kê cột, ước lượng số trang heap phải "
            "truy cập rồi so sánh với chi phí đọc bảng tuần tự."
        ),
        vi_criteria=[
            "Giải thích rất ít hoặc không giải thích về độ chọn lọc; cho rằng chỉ mục luôn nhanh hơn.",
            "Nêu được chỉ mục dùng khi ít dòng và quét bảng khi nhiều dòng, nhưng không giải thích I/O ngẫu nhiên so với tuần tự hay cách tính chi phí.",
            "Giải thích được đánh đổi giữa bộ lọc chọn lọc và bộ lọc rộng cùng vai trò của thống kê, nhưng bỏ sót trường hợp bảng nhỏ hoặc một yếu tố chi phí.",
            "Giải thích đầy đủ độ chọn lọc, truy cập heap ngẫu nhiên, I/O tuần tự, chi phí dựa trên thống kê và lý do bảng nhỏ vẫn có thể dùng quét tuần tự.",
        ],
        tags=["postgresql", "performance", "index"],
    ),
    essay_vi(
        "a2b-easy-index-budget",
        ["IDX"],
        2,
        (
            "A team proposes adding an index for every column that appears in a "
            "WHERE clause. Explain the costs of this strategy: storage, write "
            "amplification, maintenance and planner overhead. Then describe a "
            "procedure for deciding whether a proposed index is worth keeping."
        ),
        (
            "Each index is a separate structure that stores keys and row "
            "references, consumes disk and memory, and must be updated on every "
            "insert, update and delete that changes its columns. More indexes "
            "mean more WAL, more maintenance work, and potentially more planner "
            "time to consider access paths. Low-selectivity or rarely used "
            "indexes cost writes without helping reads. A practical procedure is "
            "to start from measured, frequent queries, propose the smallest set "
            "of indexes that support them, verify with EXPLAIN (ANALYZE, BUFFERS) "
            "and pg_stat_user_indexes.idx_scan, monitor write overhead, and drop "
            "indexes that are unused or redundant after a representative period."
        ),
        (
            "Index design is a workload trade-off. The goal is not to index every "
            "predicate but to buy the most read improvement for the least write "
            "and storage cost, using evidence rather than guesses."
        ),
        [
            "Treats indexes as free or only lists one cost with no decision procedure.",
            "Lists storage or write costs but gives no practical way to decide which indexes to keep.",
            "Explains the main costs and proposes measurement, but omits one dimension such as redundant indexes or planner overhead.",
            "Explains storage, write amplification, maintenance and planner overhead, and gives a measurement-driven keep or drop procedure using real usage statistics.",
        ],
        [PG_INDEXES, PG_STATS],
        vi_prompt=(
            "Một nhóm đề xuất thêm chỉ mục cho mọi cột xuất hiện trong mệnh đề "
            "WHERE. Hãy giải thích chi phí của chiến lược này: dung lượng, gia "
            "tăng ghi, bảo trì và chi phí cho bộ lập kế hoạch. Sau đó mô tả quy "
            "trình quyết định một chỉ mục được đề xuất có đáng giữ lại không."
        ),
        vi_reference=(
            "Mỗi chỉ mục là một cấu trúc riêng lưu khóa và tham chiếu dòng, chiếm "
            "đĩa và bộ nhớ, và phải được cập nhật mỗi khi chèn, sửa, xóa làm thay "
            "đổi các cột của nó. Càng nhiều chỉ mục càng nhiều WAL, càng nhiều "
            "công việc bảo trì và có thể càng nhiều thời gian lập kế hoạch để cân "
            "nhắc đường truy cập. Chỉ mục ít được dùng hoặc độ chọn lọc thấp gây "
            "chi phí ghi mà không giúp đọc. Quy trình thực tế là bắt đầu từ các "
            "truy vấn thường gặp đã được đo, đề xuất bộ chỉ mục nhỏ nhất hỗ trợ "
            "chúng, kiểm chứng bằng EXPLAIN (ANALYZE, BUFFERS) và "
            "pg_stat_user_indexes.idx_scan, theo dõi chi phí ghi và xóa các chỉ "
            "mục không dùng hoặc trùng lặp sau một thời gian đại diện."
        ),
        vi_explanation=(
            "Thiết kế chỉ mục là đánh đổi theo khối lượng công việc. Mục tiêu "
            "không phải đánh chỉ mục cho mọi vị từ mà là mua cải thiện đọc lớn "
            "nhất với chi phí ghi và dung lượng nhỏ nhất, dựa trên bằng chứng "
            "thay vì phỏng đoán."
        ),
        vi_criteria=[
            "Coi chỉ mục là miễn phí hoặc chỉ nêu một chi phí mà không có quy trình quyết định.",
            "Nêu được chi phí dung lượng hoặc ghi nhưng không đưa ra cách thực tế để quyết định giữ chỉ mục nào.",
            "Giải thích các chi phí chính và đề xuất đo lường, nhưng bỏ sót một khía cạnh như chỉ mục trùng lặp hoặc chi phí lập kế hoạch.",
            "Giải thích đầy đủ dung lượng, gia tăng ghi, bảo trì và chi phí lập kế hoạch, đồng thời đưa ra quy trình dựa trên số liệu sử dụng thực tế để giữ hoặc bỏ chỉ mục.",
        ],
        tags=["postgresql", "performance", "index"],
    ),
    # MEDIUM: 4 MCQ (difficulty 3)
    mcq_vi(
        "a2b-medium-concurrently",
        ["IDX"],
        3,
        (
            "Why might a DBA use CREATE INDEX CONCURRENTLY instead of CREATE INDEX "
            "on a busy production table?"
        ),
        [
            "It avoids blocking writes for the whole build, at the cost of a "
            "longer build and extra cleanup if it fails.",
            "It builds the index in memory and therefore never writes WAL.",
            "It creates a clustered index that physically reorders the table.",
            "It can be run inside a transaction block and rolled back like "
            "ordinary DDL.",
        ],
        0,
        (
            "CREATE INDEX CONCURRENTLY allows ordinary writes to continue while "
            "the index is built. It performs more work and takes longer, can leave "
            "an invalid index if it fails, and cannot run inside a transaction "
            "block. It is still a normal index, not a clustered one, and the index "
            "build is WAL-logged."
        ),
        [PG_CREATE_INDEX],
        vi_prompt=(
            "Vì sao quản trị viên có thể dùng CREATE INDEX CONCURRENTLY thay cho "
            "CREATE INDEX trên bảng sản xuất đang bận?"
        ),
        vi_options=[
            "Nó tránh chặn ghi trong suốt quá trình xây dựng, đổi lại thời gian "
            "xây dựng lâu hơn và cần dọn dẹp thêm nếu thất bại.",
            "Nó xây dựng chỉ mục trong bộ nhớ nên không bao giờ ghi WAL.",
            "Nó tạo chỉ mục clustered và sắp xếp lại vật lý bảng.",
            "Nó có thể chạy trong khối giao dịch và được hoàn tác như DDL thông thường.",
        ],
        vi_explanation=(
            "CREATE INDEX CONCURRENTLY cho phép các thao tác ghi thông thường tiếp "
            "tục trong khi xây dựng chỉ mục. Nó làm nhiều việc hơn, mất nhiều thời "
            "gian hơn, có thể để lại chỉ mục không hợp lệ nếu thất bại và không "
            "thể chạy trong khối giao dịch. Đây vẫn là chỉ mục thường, không phải "
            "clustered, và quá trình xây dựng vẫn ghi WAL."
        ),
        tags=["postgresql", "performance", "index"],
    ),
    mcq_vi(
        "a2b-medium-column-order",
        ["IDX"],
        3,
        (
            "Queries run WHERE status = 'open' AND created_at >= '2026-01-01' "
            "ORDER BY created_at. Which B-tree index best supports both the filter "
            "and the ordering?"
        ),
        [
            "(status, created_at): equality on the leading column, then range and "
            "order on created_at.",
            "(created_at, status): the range comes first, so status cannot be used "
            "efficiently.",
            "Two separate indexes on status and created_at, always combined by a "
            "bitmap scan.",
            "An index on status alone, because ORDER BY can always use an external "
            "sort.",
        ],
        0,
        (
            "A composite B-tree is ordered by its leading column first. With "
            "status leading, an equality condition fixes the status prefix and the "
            "trailing created_at values are then ordered, so the index supports "
            "both the filter and the requested order. With created_at leading, a "
            "range scan cannot efficiently apply the status filter by index. A "
            "bitmap scan combines indexes but does not preserve order, and sorting "
            "on status alone is not a good reason to prefer the wrong column order."
        ),
        [PG_INDEX_MULTICOLUMN, PG_INDEX_TYPES],
        vi_prompt=(
            "Truy vấn chạy WHERE status = 'open' AND created_at >= '2026-01-01' "
            "ORDER BY created_at. Chỉ mục B-tree nào hỗ trợ tốt nhất cả bộ lọc và "
            "thứ tự?"
        ),
        vi_options=[
            "(status, created_at): đẳng thức trên cột đầu, sau đó khoảng và thứ "
            "tự trên created_at.",
            "(created_at, status): khoảng đứng trước nên không thể dùng status "
            "hiệu quả.",
            "Hai chỉ mục riêng trên status và created_at, luôn được kết hợp bằng "
            "quét bitmap.",
            "Chỉ mục trên một mình status, vì ORDER BY luôn có thể dùng sắp xếp "
            "ngoài.",
        ],
        vi_explanation=(
            "Chỉ mục B-tree tổ hợp được sắp theo cột đầu tiên. Khi status đứng "
            "đầu, điều kiện đẳng thức cố định tiền tố status và các giá trị "
            "created_at phía sau có thứ tự, nên chỉ mục hỗ trợ cả bộ lọc và thứ "
            "tự yêu cầu. Khi created_at đứng đầu, quét khoảng không thể áp dụng "
            "hiệu quả bộ lọc status bằng chỉ mục. Quét bitmap kết hợp chỉ mục "
            "nhưng không bảo toàn thứ tự, và sắp xếp chỉ vì status không phải lý "
            "do tốt để chọn sai thứ tự cột."
        ),
        tags=["postgresql", "performance", "index"],
    ),
    mcq_vi(
        "a2b-medium-child-fk-delete",
        ["IDX"],
        3,
        (
            "A parent table is deleted from frequently. The child table has a "
            "foreign key to it but no index on the child's foreign key column. "
            "What is the likely performance impact?"
        ),
        [
            "Each parent delete or key update must find referencing child rows, "
            "which can require a sequential scan of the child table.",
            "No impact: the foreign key constraint stores a reverse index "
            "automatically.",
            "Only INSERT statements into the child table become slower.",
            "The child table is locked exclusively for the whole transaction, so "
            "only one delete can run at a time.",
        ],
        0,
        (
            "Referential integrity checks must locate child rows that reference "
            "the parent key being deleted or changed. Without an index on the "
            "child's foreign key column, that lookup can scan the child table, so "
            "parent deletes and key updates can be slow. The constraint does not "
            "create a reverse index, and it does not impose an exclusive "
            "table-level lock for the transaction."
        ),
        [PG_CONSTRAINTS, PG_INDEXES],
        vi_prompt=(
            "Một bảng cha thường xuyên bị xóa dòng. Bảng con có khóa ngoại tham "
            "chiếu tới bảng cha nhưng không có chỉ mục trên cột khóa ngoại của "
            "bảng con. Tác động hiệu năng có khả năng là gì?"
        ),
        vi_options=[
            "Mỗi lần xóa hoặc cập nhật khóa của bảng cha phải tìm các dòng con "
            "tham chiếu, có thể phải quét tuần tự bảng con.",
            "Không ảnh hưởng: ràng buộc khóa ngoại tự động lưu một chỉ mục ngược.",
            "Chỉ các câu INSERT vào bảng con trở nên chậm hơn.",
            "Bảng con bị khóa độc quyền suốt giao dịch nên chỉ một lệnh xóa chạy "
            "tại một thời điểm.",
        ],
        vi_explanation=(
            "Kiểm tra toàn vẹn tham chiếu phải định vị các dòng con tham chiếu "
            "tới khóa cha đang bị xóa hoặc thay đổi. Không có chỉ mục trên cột "
            "khóa ngoại của bảng con, việc tra cứu có thể quét bảng con, nên xóa "
            "và cập nhật khóa ở bảng cha có thể chậm. Ràng buộc không tạo chỉ mục "
            "ngược và không áp đặt khóa độc quyền toàn bảng cho giao dịch."
        ),
        tags=["postgresql", "performance", "index"],
    ),
    mcq_vi(
        "a2b-medium-implicit-cast",
        ["IDX"],
        3,
        (
            "An indexed varchar column code is compared as WHERE code = 42 while "
            "the application sends an integer parameter. What happens, and what is "
            "the clean fix?"
        ),
        [
            "There is no varchar = integer operator, so the statement fails with an "
            "operator-resolution error; send '42' as text or use an explicit cast, "
            "and index the cast expression if the cast is intended.",
            "The index is still used because PostgreSQL silently converts the "
            "integer to text.",
            "The index is used only when the column is nullable.",
            "Increasing work_mem makes a plain index usable for cross-type "
            "comparisons.",
        ],
        0,
        (
            "PostgreSQL resolves operators by argument types. There is no character "
            "varying = integer operator, so WHERE code = 42 raises 'operator does "
            "not exist: character varying = integer'. Passing the value as text "
            "keeps the existing varchar = varchar operator and the plain index "
            "usable. If a cast on the column is intended, such as "
            "code::integer = 42, the plain varchar index no longer matches and an "
            "expression index on the cast is required. Nullability and work_mem "
            "are unrelated."
        ),
        [PG_TYPECONV, PG_INDEXES],
        vi_prompt=(
            "Một cột varchar code có chỉ mục được so sánh bằng WHERE code = 42 "
            "trong khi ứng dụng gửi tham số kiểu số nguyên. Điều gì xảy ra, và "
            "cách sửa đúng là gì?"
        ),
        vi_options=[
            "Không có toán tử varchar = integer nên câu lệnh thất bại với lỗi "
            "phân giải toán tử; hãy gửi '42' dưới dạng text hoặc ép kiểu tường "
            "minh, và đánh chỉ mục cho biểu thức ép kiểu nếu việc ép kiểu là chủ "
            "đích.",
            "Chỉ mục vẫn được dùng vì PostgreSQL tự động chuyển số nguyên thành "
            "text.",
            "Chỉ mục chỉ được dùng khi cột cho phép NULL.",
            "Tăng work_mem giúp chỉ mục thường dùng được cho so sánh khác kiểu.",
        ],
        vi_explanation=(
            "PostgreSQL phân giải toán tử theo kiểu toán hạng. Không có toán tử "
            "character varying = integer, nên WHERE code = 42 báo lỗi 'operator "
            "does not exist: character varying = integer'. Truyền giá trị dưới "
            "dạng text giữ nguyên toán tử varchar = varchar và chỉ mục thường vẫn "
            "dùng được. Nếu việc ép kiểu trên cột là chủ đích, ví dụ "
            "code::integer = 42, chỉ mục varchar thường không còn khớp và cần "
            "chỉ mục biểu thức trên phép ép kiểu. Tính nullable và work_mem không "
            "liên quan."
        ),
        tags=["postgresql", "performance", "index"],
    ),
    # MEDIUM: 1 essay (difficulty 3)
    essay_vi(
        "a2b-medium-orders-index-strategy",
        ["IDX"],
        3,
        (
            "An orders table with 50 million rows serves three workloads: "
            "(a) WHERE customer_id = ? ORDER BY created_at DESC LIMIT 20; "
            "(b) WHERE status = 'pending' AND created_at < now() - interval '1 "
            "day'; (c) a nightly report that groups by status. Propose indexes for "
            "(a) and (b), explain the column order, and explain why a new index "
            "for (c) may be a poor trade-off. Describe how you would verify the "
            "effect with EXPLAIN and usage statistics."
        ),
        (
            "For (a), an index on (customer_id, created_at DESC) supports the "
            "equality on customer_id, returns rows in the requested order and "
            "lets the scan stop after 20 rows; the DESC direction matches the "
            "index ordering and avoids a sort. For (b), a partial index on "
            "(created_at) WHERE status = 'pending' is small because only pending "
            "rows are stored and matches the predicate; alternatively a composite "
            "(status, created_at) index works but is larger. For (c), status has "
            "low cardinality and the report reads a large fraction of the table, "
            "so a sequential scan is usually efficient and an index would add "
            "write and storage cost for little read benefit; a materialized view "
            "or summary table refreshed nightly may be a better fit. Verification "
            "means comparing EXPLAIN (ANALYZE, BUFFERS) before and after, checking "
            "actual rows and buffers, and monitoring pg_stat_user_indexes.idx_scan "
            "and write latency."
        ),
        (
            "The proposal must connect each index to a specific query shape, "
            "explain why the column order or partial predicate matches, and "
            "justify rejecting the low-cardinality reporting index. Verification "
            "must use measured plans and usage counters."
        ),
        [
            "Proposes unrelated indexes without connecting them to the workloads, or claims an index always helps.",
            "Proposes plausible indexes but does not justify column order, the partial predicate or the rejection of (c).",
            "Justifies the two indexes and the main trade-off, but verification or one query detail is incomplete.",
            "Matches both query shapes to justified index designs, explains the low-cardinality trade-off, and verifies with measured plans and usage statistics.",
        ],
        [PG_INDEXES, PG_CREATE_INDEX, PG_EXPLAIN, PG_STATS],
        vi_prompt=(
            "Bảng orders 50 triệu dòng phục vụ ba khối công việc: (a) WHERE "
            "customer_id = ? ORDER BY created_at DESC LIMIT 20; (b) WHERE status "
            "= 'pending' AND created_at < now() - interval '1 day'; (c) báo cáo "
            "hàng đêm nhóm theo status. Hãy đề xuất chỉ mục cho (a) và (b), giải "
            "thích thứ tự cột, và giải thích vì sao thêm chỉ mục cho (c) có thể "
            "là đánh đổi kém. Mô tả cách kiểm chứng hiệu quả bằng EXPLAIN và "
            "thống kê sử dụng."
        ),
        vi_reference=(
            "Với (a), chỉ mục (customer_id, created_at DESC) hỗ trợ đẳng thức "
            "trên customer_id, trả về đúng thứ tự và cho phép dừng sau 20 dòng; "
            "chiều DESC khớp thứ tự chỉ mục và tránh sắp xếp. Với (b), chỉ mục "
            "một phần trên (created_at) WHERE status = 'pending' nhỏ vì chỉ lưu "
            "dòng đang chờ và khớp vị từ; cách khác là chỉ mục tổ hợp (status, "
            "created_at) nhưng lớn hơn. Với (c), status có số giá trị phân biệt "
            "thấp và báo cáo đọc phần lớn bảng, nên quét tuần tự thường hiệu quả "
            "và chỉ mục chỉ tăng chi phí ghi, dung lượng mà ít cải thiện đọc; "
            "materialized view hoặc bảng tổng hợp làm mới hàng đêm có thể phù hợp "
            "hơn. Kiểm chứng bằng cách so sánh EXPLAIN (ANALYZE, BUFFERS) trước "
            "và sau, xem số dòng thực tế và buffer, theo dõi "
            "pg_stat_user_indexes.idx_scan và độ trễ ghi."
        ),
        vi_explanation=(
            "Đề xuất phải gắn từng chỉ mục với một dạng truy vấn cụ thể, giải "
            "thích vì sao thứ tự cột hoặc vị từ một phần khớp, và biện minh cho "
            "việc không thêm chỉ mục báo cáo có số giá trị phân biệt thấp. Kiểm "
            "chứng phải dùng kế hoạch đo được và bộ đếm sử dụng."
        ),
        vi_criteria=[
            "Đề xuất chỉ mục không liên quan đến khối công việc, hoặc cho rằng chỉ mục luôn giúp ích.",
            "Đề xuất chỉ mục hợp lý nhưng không biện minh thứ tự cột, vị từ một phần hoặc việc không thêm chỉ mục cho (c).",
            "Biện minh được hai chỉ mục và đánh đổi chính, nhưng phần kiểm chứng hoặc một chi tiết truy vấn còn thiếu.",
            "Khớp cả hai dạng truy vấn với thiết kế chỉ mục có lý do, giải thích đánh đổi số giá trị phân biệt thấp và kiểm chứng bằng kế hoạch đo được cùng thống kê sử dụng.",
        ],
        tags=["postgresql", "performance", "index"],
    ),
]

"""PostgreSQL Performance fill: plan reading, statistics and index choices."""

from gap_lib import essay_vi, mcq_vi
from sources import (
    PG_BTREE,
    PG_CONFIG,
    PG_EXPLAIN,
    PG_INDEX_ORDERING,
    PG_INDEX_PARTIAL,
    PG_INDEX_TYPES,
    PG_INDEXES,
    PG_PATTERN,
    PG_PLANNER_OPTIONS,
    PG_PREPARE,
    PG_STATS,
)

QUESTIONS = [
    # EASY: 4 MCQ (difficulty 2)
    mcq_vi(
        "perfb-easy-index-scan-node",
        ["PG-EXPLAIN"],
        2,
        "In EXPLAIN output, what does an Index Scan node mean?",
        [
            "The index was used to locate matching row locations, and the table "
            "rows are fetched from the heap unless the plan is an index-only scan.",
            "The whole index was read sequentially and the table was not touched.",
            "The query used an index but returned no rows.",
            "The planner decided that no index could be used.",
        ],
        0,
        (
            "An Index Scan traverses the index to find entries that match the "
            "predicate, then fetches the corresponding heap tuples to check "
            "visibility and return columns. An Index Only Scan can avoid heap "
            "fetches when all needed columns are in the index and the visibility "
            "map permits it. A plan with no index access shows a Seq Scan, not an "
            "Index Scan."
        ),
        [PG_EXPLAIN],
        vi_prompt="Trong kết quả EXPLAIN, nút Index Scan có nghĩa là gì?",
        vi_options=[
            "Chỉ mục được dùng để định vị vị trí các dòng khớp, và các dòng được "
            "lấy từ heap trừ khi kế hoạch là index-only scan.",
            "Toàn bộ chỉ mục được đọc tuần tự và bảng không bị chạm tới.",
            "Truy vấn dùng chỉ mục nhưng không trả về dòng nào.",
            "Bộ lập kế hoạch quyết định không thể dùng chỉ mục nào.",
        ],
        vi_explanation=(
            "Index Scan duyệt chỉ mục để tìm các mục khớp vị từ, sau đó lấy các "
            "tuple heap tương ứng để kiểm tra khả năng hiển thị và trả về cột. "
            "Index Only Scan có thể tránh lấy heap khi mọi cột cần thiết nằm trong "
            "chỉ mục và bản đồ hiển thị cho phép. Kế hoạch không dùng chỉ mục hiển "
            "thị Seq Scan, không phải Index Scan."
        ),
        tags=["postgresql", "performance", "explain"],
    ),
    mcq_vi(
        "perfb-easy-rows-estimate",
        ["PG-EXPLAIN", "PG-STATS"],
        2,
        "In an EXPLAIN plan node, what does the rows= value estimate?",
        [
            "The expected number of rows produced by that node per execution, "
            "derived from table statistics.",
            "The exact number of rows returned by the whole query.",
            "The number of bytes read from disk by that node.",
            "The number of worker processes used by the node.",
        ],
        0,
        (
            "Each plan node has an estimated row count per execution based on "
            "statistics and selectivity estimates. It is not exact; EXPLAIN "
            "ANALYZE adds actual rows and loops so estimates can be compared with "
            "reality. Bytes are not shown as rows, and worker counts appear only "
            "for parallel plans."
        ),
        [PG_EXPLAIN, PG_STATS],
        vi_prompt=(
            "Trong một nút kế hoạch EXPLAIN, giá trị rows= ước lượng điều gì?"
        ),
        vi_options=[
            "Số dòng dự kiến do nút đó tạo ra trong mỗi lần thực thi, dựa trên "
            "thống kê bảng.",
            "Số dòng chính xác do toàn bộ truy vấn trả về.",
            "Số byte nút đó đọc từ đĩa.",
            "Số tiến trình worker mà nút sử dụng.",
        ],
        vi_explanation=(
            "Mỗi nút kế hoạch có số dòng ước tính cho mỗi lần thực thi dựa trên "
            "thống kê và ước lượng độ chọn lọc. Đây không phải số chính xác; "
            "EXPLAIN ANALYZE thêm số dòng thực tế và số vòng lặp để so sánh ước "
            "lượng với thực tế. Byte không hiển thị dưới dạng rows, và số worker "
            "chỉ xuất hiện với kế hoạch song song."
        ),
        tags=["postgresql", "performance", "explain"],
    ),
    mcq_vi(
        "perfb-easy-seq-scan-choice",
        ["PG-INDEX", "PG-EXPLAIN"],
        2,
        "When is a sequential scan usually a reasonable choice?",
        [
            "For a small table, or when the predicate matches a large fraction of "
            "the table so an index would add random heap access.",
            "Only when the table has no indexes at all.",
            "Only when the query returns a single row.",
            "Whenever the query contains an ORDER BY clause.",
        ],
        0,
        (
            "A sequential scan reads the table's pages in physical order, which is "
            "efficient when the table is small or most rows are needed. For a "
            "broad predicate, an index would visit many heap pages in less "
            "predictable order and can be slower than reading the table once. A "
            "table with indexes can still use a sequential scan, and single-row "
            "lookups usually favor an index instead."
        ),
        [PG_INDEXES, PG_EXPLAIN],
        vi_prompt="Khi nào quét tuần tự thường là lựa chọn hợp lý?",
        vi_options=[
            "Với bảng nhỏ, hoặc khi vị từ khớp phần lớn bảng nên chỉ mục sẽ thêm "
            "truy cập heap ngẫu nhiên.",
            "Chỉ khi bảng hoàn toàn không có chỉ mục.",
            "Chỉ khi truy vấn trả về một dòng.",
            "Bất cứ khi nào truy vấn có mệnh đề ORDER BY.",
        ],
        vi_explanation=(
            "Quét tuần tự đọc các trang của bảng theo thứ tự vật lý, hiệu quả khi "
            "bảng nhỏ hoặc cần phần lớn số dòng. Với vị từ rộng, chỉ mục sẽ truy "
            "cập nhiều trang heap theo thứ tự khó dự đoán và có thể chậm hơn đọc "
            "bảng một lần. Bảng có chỉ mục vẫn có thể dùng quét tuần tự, còn tra "
            "cứu một dòng thường nên dùng chỉ mục."
        ),
        tags=["postgresql", "performance", "index"],
    ),
    mcq_vi(
        "perfb-easy-leading-wildcard",
        ["PG-INDEX", "PG-STATS"],
        2,
        (
            "Which predicate most likely prevents a plain B-tree index on the "
            "email column from being used?"
        ),
        [
            "WHERE email LIKE '%@example.com'",
            "WHERE email = 'a@example.com'",
            "WHERE email > 'a@example.com'",
            "WHERE email IN ('a@example.com', 'b@example.com')",
        ],
        0,
        (
            "A B-tree index is ordered by the leading characters of the value. A "
            "pattern with a leading wildcard, such as LIKE '%@example.com', has no "
            "fixed prefix, so the index cannot narrow the search and a scan is "
            "likely. Equality, range and IN predicates on the indexed column can "
            "use the index. Solutions for suffix searches include trigram indexes "
            "or full-text search, not a plain B-tree."
        ),
        [PG_BTREE, PG_PATTERN],
        vi_prompt=(
            "Vị từ nào có khả năng cao nhất khiến chỉ mục B-tree thường trên cột "
            "email không được dùng?"
        ),
        vi_options=[
            "WHERE email LIKE '%@example.com'",
            "WHERE email = 'a@example.com'",
            "WHERE email > 'a@example.com'",
            "WHERE email IN ('a@example.com', 'b@example.com')",
        ],
        vi_explanation=(
            "Chỉ mục B-tree được sắp theo các ký tự đầu của giá trị. Mẫu có ký tự "
            "đại diện ở đầu, như LIKE '%@example.com', không có tiền tố cố định "
            "nên chỉ mục không thu hẹp được tìm kiếm và nhiều khả năng phải quét. "
            "Vị từ đẳng thức, khoảng và IN trên cột có chỉ mục có thể dùng chỉ "
            "mục. Cách xử lý tìm theo hậu tố gồm chỉ mục trigram hoặc tìm kiếm "
            "toàn văn, không phải B-tree thường."
        ),
        tags=["postgresql", "performance", "index"],
    ),
    # EASY: 3 essays (difficulty 2)
    essay_vi(
        "perfb-easy-cost-model",
        ["PG-EXPLAIN", "PG-STATS"],
        2,
        (
            "Explain the main components of PostgreSQL's plan cost estimates, such "
            "as seq_page_cost, random_page_cost, cpu_tuple_cost and estimated row "
            "counts. Why is cost not a number of milliseconds, and how can actual "
            "timings differ from estimates?"
        ),
        (
            "The planner assigns costs per operation using configuration constants "
            "and statistics. Reading a page sequentially has seq_page_cost, a "
            "randomly accessed page has random_page_cost, and processing a row or "
            "evaluating an operator has CPU costs. It multiplies these by estimated "
            "page and row counts derived from table statistics and selectivity "
            "estimates. The units are relative cost units, not milliseconds; their "
            "purpose is to compare alternative plans consistently. Actual time can "
            "differ because of caching, concurrency, I/O variability, inaccurate "
            "statistics, or because cost constants do not model every hardware "
            "effect. EXPLAIN ANALYZE reports actual time and rows for comparison."
        ),
        (
            "The answer must separate relative cost units from wall-clock time and "
            "connect estimates to statistics and workload conditions."
        ),
        [
            "Claims cost is milliseconds or lists constants without explaining how they combine.",
            "Explains that cost is relative but not which inputs drive it or why actual time differs.",
            "Explains cost inputs and relative units, but omits statistics or real-world differences.",
            "Explains page, random and CPU costs, row estimates from statistics, relative units and why measured time can differ.",
        ],
        [PG_EXPLAIN, PG_CONFIG, PG_STATS],
        vi_prompt=(
            "Hãy giải thích các thành phần chính trong ước lượng chi phí kế hoạch "
            "của PostgreSQL, như seq_page_cost, random_page_cost, cpu_tuple_cost và "
            "số dòng ước tính. Vì sao chi phí không phải số mili giây, và thời "
            "gian thực tế có thể khác ước lượng như thế nào?"
        ),
        vi_reference=(
            "Bộ lập kế hoạch gán chi phí cho từng thao tác dựa trên hằng số cấu "
            "hình và thống kê. Đọc một trang tuần tự có seq_page_cost, truy cập "
            "ngẫu nhiên một trang có random_page_cost, còn xử lý một dòng hoặc "
            "đánh giá toán tử có chi phí CPU. Nó nhân các chi phí này với số trang "
            "và số dòng ước tính từ thống kê bảng và ước lượng độ chọn lọc. Đơn vị "
            "là đơn vị chi phí tương đối, không phải mili giây; mục đích là so sánh "
            "các kế hoạch thay thế một cách nhất quán. Thời gian thực tế có thể "
            "khác do bộ nhớ đệm, đồng thời, I/O biến động, thống kê không chính "
            "xác, hoặc vì hằng số chi phí không mô hình hóa mọi ảnh hưởng phần "
            "cứng. EXPLAIN ANALYZE báo thời gian và số dòng thực tế để so sánh."
        ),
        vi_explanation=(
            "Câu trả lời phải tách đơn vị chi phí tương đối khỏi thời gian thực và "
            "gắn ước lượng với thống kê cùng điều kiện khối lượng công việc."
        ),
        vi_criteria=[
            "Cho rằng chi phí là mili giây hoặc chỉ liệt kê hằng số mà không giải thích cách kết hợp.",
            "Giải thích chi phí là tương đối nhưng không nêu đầu vào nào chi phối hoặc vì sao thời gian thực khác.",
            "Giải thích đầu vào chi phí và đơn vị tương đối, nhưng bỏ sót thống kê hoặc khác biệt thực tế.",
            "Giải thích chi phí trang, ngẫu nhiên và CPU, số dòng từ thống kê, đơn vị tương đối và vì sao thời gian đo được có thể khác.",
        ],
        tags=["postgresql", "performance", "explain"],
    ),
    essay_vi(
        "perfb-easy-statistics",
        ["PG-STATS"],
        2,
        (
            "Explain what ANALYZE collects for the planner, including distinct "
            "value estimates, histograms and correlation. Why do stale statistics "
            "lead to bad plans, and what changes after a large data load?"
        ),
        (
            "ANALYZE samples a table and records statistics that describe its "
            "columns: the estimated number of distinct values, a histogram of value "
            "distribution used for range selectivity, null fraction, average width "
            "and the correlation between physical row order and column order. The "
            "planner uses these to estimate how many rows a predicate returns and "
            "therefore which scan or join is cheapest. After a large insert, "
            "delete or update, the stored statistics can describe an old "
            "distribution, so selectivity estimates may be far too low or high and "
            "the planner can choose a bad nested loop, a sequential scan or a poor "
            "join order. Running ANALYZE after a bulk load, or relying on "
            "autovacuum, refreshes the estimates. Skewed or correlated columns may "
            "need a higher statistics target or extended statistics."
        ),
        (
            "The answer must name concrete statistics, link them to selectivity "
            "and plan choice, and explain the post-load stale-statistics failure."
        ),
        [
            "Says only that ANALYZE helps the planner without naming any statistic.",
            "Names one statistic but does not connect it to selectivity or plan choice.",
            "Explains several statistics and stale-statistics problems, but omits the post-load case or correlation.",
            "Explains distinct values, histograms, correlation and null fraction, how they drive selectivity, and why a bulk load makes old statistics harmful.",
        ],
        [PG_STATS, PG_EXPLAIN],
        vi_prompt=(
            "Hãy giải thích ANALYZE thu thập gì cho bộ lập kế hoạch, gồm ước lượng "
            "số giá trị phân biệt, biểu đồ tần suất và tương quan. Vì sao thống kê "
            "cũ dẫn đến kế hoạch kém, và điều gì thay đổi sau khi nạp lượng lớn dữ "
            "liệu?"
        ),
        vi_reference=(
            "ANALYZE lấy mẫu bảng và ghi thống kê mô tả các cột: số giá trị phân "
            "biệt ước tính, biểu đồ phân bố giá trị dùng cho độ chọn lọc khoảng, "
            "tỷ lệ NULL, độ rộng trung bình và tương quan giữa thứ tự vật lý của "
            "dòng với thứ tự cột. Bộ lập kế hoạch dùng chúng để ước lượng một vị "
            "từ trả về bao nhiêu dòng và do đó chọn cách quét hoặc nối rẻ nhất. "
            "Sau khi chèn, xóa hoặc cập nhật lượng lớn, thống kê đã lưu có thể mô "
            "tả phân bố cũ, nên ước lượng độ chọn lọc có thể quá thấp hoặc quá cao "
            "và bộ lập kế hoạch chọn nested loop, quét tuần tự hoặc thứ tự nối "
            "kém. Chạy ANALYZE sau khi nạp hàng loạt, hoặc dựa vào autovacuum, sẽ "
            "làm mới ước lượng. Cột lệch hoặc tương quan có thể cần "
            "default_statistics_target cao hơn hoặc thống kê mở rộng."
        ),
        vi_explanation=(
            "Câu trả lời phải nêu thống kê cụ thể, liên hệ chúng với độ chọn lọc "
            "và việc chọn kế hoạch, đồng thời giải thích hỏng hóc do thống kê cũ "
            "sau khi nạp dữ liệu."
        ),
        vi_criteria=[
            "Chỉ nói ANALYZE giúp bộ lập kế hoạch mà không nêu thống kê nào.",
            "Nêu một thống kê nhưng không liên hệ với độ chọn lọc hoặc chọn kế hoạch.",
            "Giải thích nhiều thống kê và vấn đề thống kê cũ, nhưng bỏ sót trường hợp sau nạp dữ liệu hoặc tương quan.",
            "Giải thích số giá trị phân biệt, biểu đồ, tương quan và tỷ lệ NULL, cách chúng chi phối độ chọn lọc, và vì sao nạp hàng loạt làm thống kê cũ gây hại.",
        ],
        tags=["postgresql", "performance", "statistics"],
    ),
    essay_vi(
        "perfb-easy-buffers",
        ["PG-EXPLAIN"],
        2,
        (
            "Explain what EXPLAIN (ANALYZE, BUFFERS) reports for buffer usage. "
            "What is the difference between shared hits and reads, why are hits "
            "usually cheaper, and how can caching change the actual timing of a "
            "plan?"
        ),
        (
            "BUFFERS adds counts of shared buffer blocks hit and read, plus local "
            "and temporary blocks, for each plan node. A shared hit means the "
            "required block was already in PostgreSQL's shared buffers; a read "
            "means it had to be fetched from the operating system or disk. Hits "
            "are usually much cheaper because they avoid I/O, although they still "
            "cost CPU and memory bandwidth. Caching can make a plan look fast on a "
            "warm cache and slow on a cold one, and it can change the planner's "
            "cost assumptions because random_page_cost may overstate or "
            "understate real SSD behavior. Measuring both warm and cold runs, and "
            "comparing estimated rows with actual rows, separates I/O effects from "
            "estimation errors."
        ),
        (
            "The answer must define hits and reads, explain the cost difference, "
            "and connect cache state to plan timing and planning assumptions."
        ),
        [
            "Confuses buffer hits with disk reads or gives no meaning for the counters.",
            "Defines hits and reads but does not explain cost or caching effects.",
            "Explains the counters and cost difference, but omits cache effects on planning or timing.",
            "Explains shared hits and reads, their cost difference, and how warm or cold caches affect measured timing and planner assumptions.",
        ],
        [PG_EXPLAIN, PG_CONFIG],
        vi_prompt=(
            "Hãy giải thích EXPLAIN (ANALYZE, BUFFERS) báo cáo gì về việc dùng bộ "
            "đệm. Shared hit và read khác nhau thế nào, vì sao hit thường rẻ hơn, "
            "và bộ nhớ đệm có thể làm thay đổi thời gian thực tế của kế hoạch ra "
            "sao?"
        ),
        vi_reference=(
            "BUFFERS thêm số khối bộ đệm shared được hit và read, cùng khối local "
            "và temporary, cho từng nút kế hoạch. Shared hit nghĩa là khối cần "
            "thiết đã nằm trong shared buffers của PostgreSQL; read nghĩa là phải "
            "lấy từ hệ điều hành hoặc đĩa. Hit thường rẻ hơn nhiều vì tránh I/O, "
            "dù vẫn tốn CPU và băng thông bộ nhớ. Bộ nhớ đệm có thể làm kế hoạch "
            "trông nhanh với cache ấm và chậm với cache lạnh, đồng thời có thể làm "
            "sai giả định chi phí của bộ lập kế hoạch vì random_page_cost có thể "
            "ước cao hoặc thấp so với hành vi SSD thực. Đo cả lần chạy ấm và lạnh, "
            "so sánh số dòng ước tính với thực tế để tách ảnh hưởng I/O khỏi lỗi ước "
            "lượng."
        ),
        vi_explanation=(
            "Câu trả lời phải định nghĩa hit và read, giải thích khác biệt chi phí, "
            "và liên hệ trạng thái cache với thời gian kế hoạch cùng giả định lập "
            "kế hoạch."
        ),
        vi_criteria=[
            "Nhầm buffer hit với đọc đĩa hoặc không giải thích ý nghĩa các bộ đếm.",
            "Định nghĩa hit và read nhưng không giải thích chi phí hoặc ảnh hưởng của cache.",
            "Giải thích bộ đếm và khác biệt chi phí, nhưng bỏ sót ảnh hưởng cache lên lập kế hoạch hoặc thời gian.",
            "Giải thích shared hit và read, khác biệt chi phí, và cách cache ấm hoặc lạnh ảnh hưởng thời gian đo cùng giả định của bộ lập kế hoạch.",
        ],
        tags=["postgresql", "performance", "explain"],
    ),
    # MEDIUM: 2 MCQ (difficulty 3)
    mcq_vi(
        "perfb-medium-orderby-limit",
        ["PG-INDEX", "PG-EXPLAIN"],
        3,
        (
            "A query runs SELECT * FROM events ORDER BY created_at DESC LIMIT 10 "
            "and an index exists on created_at. What is the main benefit, and what "
            "is the main caveat?"
        ),
        [
            "The index can return rows in order and stop early, but a filter on an "
            "unindexed column may force reading many rows before 10 matches are "
            "found.",
            "The index guarantees exactly 10 heap reads even when a selective "
            "filter is applied.",
            "The index removes the need for the planner to estimate selectivity.",
            "The index makes the query use a bitmap scan, which always preserves "
            "created_at order.",
        ],
        0,
        (
            "An ordered index scan can walk the index in created_at order and stop "
            "after the LIMIT is satisfied, avoiding a sort. If the query also "
            "filters on a column not in the index, the scan may inspect many index "
            "entries and heap rows before finding 10 matches, so a composite or "
            "partial index may be better. A bitmap scan does not preserve index "
            "order, and the planner still estimates selectivity."
        ),
        [PG_INDEX_ORDERING, PG_EXPLAIN],
        vi_prompt=(
            "Một truy vấn chạy SELECT * FROM events ORDER BY created_at DESC LIMIT "
            "10 và có chỉ mục trên created_at. Lợi ích chính và hạn chế chính là "
            "gì?"
        ),
        vi_options=[
            "Chỉ mục trả về dòng đúng thứ tự và dừng sớm, nhưng bộ lọc trên cột "
            "không có chỉ mục có thể buộc đọc nhiều dòng trước khi tìm đủ 10 dòng "
            "khớp.",
            "Chỉ mục bảo đảm đúng 10 lần đọc heap kể cả khi có bộ lọc chọn lọc cao.",
            "Chỉ mục loại bỏ nhu cầu bộ lập kế hoạch ước lượng độ chọn lọc.",
            "Chỉ mục làm truy vấn dùng quét bitmap, vốn luôn bảo toàn thứ tự "
            "created_at.",
        ],
        vi_explanation=(
            "Quét chỉ mục có thứ tự có thể đi theo thứ tự created_at và dừng khi "
            "đủ LIMIT, tránh sắp xếp. Nếu truy vấn còn lọc trên cột không nằm "
            "trong chỉ mục, lần quét có thể xem nhiều mục chỉ mục và dòng heap "
            "trước khi tìm đủ 10 dòng khớp, nên chỉ mục tổ hợp hoặc một phần có thể "
            "tốt hơn. Quét bitmap không bảo toàn thứ tự chỉ mục, và bộ lập kế hoạch "
            "vẫn ước lượng độ chọn lọc."
        ),
        tags=["postgresql", "performance", "index"],
    ),
    mcq_vi(
        "perfb-medium-boolean-index",
        ["PG-INDEX", "PG-INDEX-TYPES"],
        3,
        (
            "A boolean column is true for about half the rows. Queries sometimes "
            "filter is_active = true. Why is a plain B-tree index on is_active "
            "often a poor choice, and what is a better option?"
        ),
        [
            "It has very low selectivity, so it rarely narrows the scan; a partial "
            "index on a rarer condition or a composite index matching the query is "
            "often better.",
            "B-tree indexes cannot store boolean values at all.",
            "The index helps equality but breaks range queries on other columns.",
            "The index is useful only if the column is nullable.",
        ],
        0,
        (
            "With two evenly distributed values, an equality predicate selects "
            "about half the table, so an index does not narrow the search enough "
            "to justify random heap access and write maintenance. If the workload "
            "actually targets a rarer subset, a partial index on that predicate "
            "stores only the interesting rows and is much smaller; if the query "
            "combines is_active with another filter, a composite index may be the "
            "better fit. B-tree does support boolean keys, and an index on this "
            "column does not disable indexes on other columns."
        ),
        [PG_INDEX_PARTIAL, PG_INDEX_TYPES, PG_EXPLAIN],
        vi_prompt=(
            "Một cột boolean có khoảng một nửa số dòng là true. Truy vấn đôi khi "
            "lọc is_active = true. Vì sao chỉ mục B-tree thường trên is_active "
            "thường là lựa chọn kém, và lựa chọn tốt hơn là gì?"
        ),
        vi_options=[
            "Độ chọn lọc rất thấp nên hiếm khi thu hẹp lần quét; chỉ mục một phần "
            "cho điều kiện hiếm hơn hoặc chỉ mục tổ hợp khớp với truy vấn thường "
            "tốt hơn.",
            "Chỉ mục B-tree hoàn toàn không lưu được giá trị boolean.",
            "Chỉ mục giúp đẳng thức nhưng phá vỡ truy vấn khoảng trên cột khác.",
            "Chỉ mục chỉ hữu ích nếu cột cho phép NULL.",
        ],
        vi_explanation=(
            "Với hai giá trị phân bố đều, vị từ đẳng thức chọn khoảng nửa bảng nên "
            "chỉ mục không thu hẹp đủ để biện minh cho truy cập heap ngẫu nhiên và "
            "bảo trì ghi. Nếu khối lượng công việc thực sự nhắm tới một tập con "
            "hiếm hơn, chỉ mục một phần trên vị từ đó chỉ lưu các dòng đáng quan tâm "
            "và nhỏ hơn nhiều; nếu truy vấn kết hợp is_active với bộ lọc khác, chỉ "
            "mục tổ hợp có thể phù hợp hơn. B-tree hỗ trợ khóa boolean, và chỉ mục "
            "trên cột này không vô hiệu hóa chỉ mục trên cột khác."
        ),
        tags=["postgresql", "performance", "index"],
    ),
    # MEDIUM: 1 essay (difficulty 3)
    essay_vi(
        "perfb-medium-pagination",
        ["PG-INDEX", "PG-EXPLAIN"],
        3,
        (
            "An API paginates events with ORDER BY created_at DESC LIMIT 50 "
            "OFFSET 10000. Explain why later pages become slower even with an "
            "index on created_at, and how keyset pagination changes the plan and "
            "the index requirements. Give one limitation of keyset pagination."
        ),
        (
            "With OFFSET, PostgreSQL must still produce and discard the first "
            "10000 ordered rows before returning 50, so the work grows with the "
            "offset even when an index supplies the order. Keyset pagination "
            "remembers the last seen sort key, for example (created_at, id), and "
            "requests rows with created_at < last_created_at or a tuple comparison, "
            "so an index on (created_at DESC, id DESC) can seek directly to the "
            "next page and return only the requested rows. The limitation is that "
            "the client must carry the cursor, and the ordering key must be unique "
            "or made unique with a tiebreaker; arbitrary page jumps and changes to "
            "the sort order are harder."
        ),
        (
            "The answer must explain offset work, show how a keyset predicate uses "
            "an index, and name a real usability limitation."
        ),
        [
            "Blames the index for offset slowness or proposes only a bigger LIMIT.",
            "Explains that OFFSET discards rows but does not explain the keyset alternative or its index.",
            "Explains keyset pagination and the index, but not why OFFSET grows or a limitation of keyset.",
            "Explains OFFSET work, a keyset predicate with a matching unique index, and a real limitation such as cursor handling or no arbitrary page jumps.",
        ],
        [PG_INDEX_ORDERING, PG_EXPLAIN],
        vi_prompt=(
            "Một API phân trang sự kiện bằng ORDER BY created_at DESC LIMIT 50 "
            "OFFSET 10000. Hãy giải thích vì sao các trang sau chậm hơn dù có chỉ "
            "mục trên created_at, và phân trang theo khóa (keyset) thay đổi kế "
            "hoạch cùng yêu cầu chỉ mục như thế nào. Nêu một hạn chế của phân trang "
            "theo khóa."
        ),
        vi_reference=(
            "Với OFFSET, PostgreSQL vẫn phải tạo và bỏ 10000 dòng có thứ tự đầu "
            "tiên trước khi trả 50 dòng, nên công việc tăng theo offset ngay cả "
            "khi chỉ mục cung cấp thứ tự. Phân trang theo khóa ghi nhớ khóa sắp "
            "xếp cuối cùng, ví dụ (created_at, id), và yêu cầu các dòng có "
            "created_at < last_created_at hoặc so sánh tuple, nên chỉ mục trên "
            "(created_at DESC, id DESC) có thể nhảy trực tiếp tới trang kế tiếp và "
            "chỉ trả các dòng được yêu cầu. Hạn chế là ứng dụng phải mang theo con "
            "trỏ, khóa sắp xếp phải duy nhất hoặc được làm duy nhất bằng khóa phụ; "
            "nhảy tùy ý tới trang bất kỳ và thay đổi thứ tự sắp xếp trở nên khó "
            "hơn."
        ),
        vi_explanation=(
            "Câu trả lời phải giải thích công việc của offset, chỉ ra vị từ theo "
            "khóa dùng chỉ mục thế nào, và nêu một hạn chế thực tế về khả năng sử "
            "dụng."
        ),
        vi_criteria=[
            "Đổ lỗi cho chỉ mục về độ chậm của offset hoặc chỉ đề xuất tăng LIMIT.",
            "Giải thích OFFSET bỏ dòng nhưng không giải thích cách thay thế theo khóa hoặc chỉ mục của nó.",
            "Giải thích phân trang theo khóa và chỉ mục, nhưng không nêu vì sao OFFSET tăng việc hoặc một hạn chế của keyset.",
            "Giải thích công việc OFFSET, vị từ keyset với chỉ mục duy nhất phù hợp, và hạn chế thực tế như phải mang con trỏ hoặc không nhảy trang tùy ý.",
        ],
        tags=["postgresql", "performance", "index"],
    ),
    # HARD: 1 MCQ (difficulty 4)
    mcq_vi(
        "perfb-hard-generic-plan",
        ["PG-EXPLAIN", "PG-STATS"],
        4,
        (
            "A prepared statement uses a generic plan that performs poorly for "
            "skewed parameter values. What does PostgreSQL do, and what is a "
            "reasonable response?"
        ),
        [
            "It may switch between custom and generic plans based on estimated "
            "cost; if the generic plan is still bad, force a custom plan or "
            "restructure the query and improve statistics.",
            "It always uses the first custom plan forever, so prepared statements "
            "cannot be affected by parameter skew.",
            "It disables indexes for all prepared statements as soon as a generic "
            "plan is chosen.",
            "It automatically creates a new partial index for each parameter value.",
        ],
        0,
        (
            "PostgreSQL normally tries custom plans for the first executions and "
            "compares their estimated cost with a generic plan; it may keep using "
            "the generic plan if that looks cheaper. With skewed data, the average "
            "generic plan can be much worse than a custom plan for specific values. "
            "Responses include forcing a custom plan for that statement, "
            "restructuring the query, improving statistics, or using dynamic SQL "
            "where appropriate. It does not permanently freeze the first plan or "
            "create indexes per parameter."
        ),
        [PG_PREPARE, PG_PLANNER_OPTIONS],
        vi_prompt=(
            "Một prepared statement dùng kế hoạch generic chạy kém với các giá trị "
            "tham số bị lệch. PostgreSQL xử lý thế nào, và phản ứng hợp lý là gì?"
        ),
        vi_options=[
            "Nó có thể chuyển đổi giữa kế hoạch custom và generic dựa trên chi phí "
            "ước tính; nếu generic vẫn kém, buộc dùng custom hoặc tái cấu trúc truy "
            "vấn và cải thiện thống kê.",
            "Nó luôn dùng kế hoạch custom đầu tiên mãi mãi, nên prepared statement "
            "không thể bị ảnh hưởng bởi tham số lệch.",
            "Nó vô hiệu hóa chỉ mục cho mọi prepared statement ngay khi chọn kế "
            "hoạch generic.",
            "Nó tự động tạo chỉ mục một phần mới cho từng giá trị tham số.",
        ],
        vi_explanation=(
            "PostgreSQL thường thử kế hoạch custom trong những lần thực thi đầu và "
            "so sánh chi phí ước tính với kế hoạch generic; nó có thể tiếp tục dùng "
            "generic nếu thấy rẻ hơn. Với dữ liệu lệch, kế hoạch generic trung bình "
            "có thể kém hơn nhiều so với custom cho giá trị cụ thể. Cách xử lý gồm "
            "buộc dùng custom cho câu lệnh đó, tái cấu trúc truy vấn, cải thiện "
            "thống kê, hoặc dùng SQL động khi phù hợp. Nó không cố định kế hoạch đầu "
            "tiên mãi mãi và không tạo chỉ mục theo từng tham số."
        ),
        tags=["postgresql", "performance", "explain"],
    ),
]

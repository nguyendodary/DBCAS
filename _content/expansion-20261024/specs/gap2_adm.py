"""Administration EASY fill: operational reasoning, not configuration trivia."""

from gap_lib import essay_vi, mcq_vi
from sources import (
    PG_BASEBACKUP,
    PG_CONFIG,
    PG_MONITOR,
    PG_MONITOR_ACTIVITY,
    PG_MONITOR_STATS,
    PG_ROUTINE_VACUUM,
    PG_STATS,
    PG_WAL,
    PG_WAL_CONFIG,
)

QUESTIONS = [
    # EASY: 3 MCQ (difficulty 2)
    mcq_vi(
        "admb-easy-idle-in-transaction",
        ["PG-MONITOR"],
        2,
        (
            "In pg_stat_activity, what does a session with state = "
            "'idle in transaction' indicate?"
        ),
        [
            "A transaction is open but the client is not currently sending "
            "statements; it may hold a snapshot and locks and can delay vacuum.",
            "The backend has no open transaction and holds no resources.",
            "The session is actively executing a long-running statement.",
            "The session is waiting for the checkpointer to finish a cycle.",
        ],
        0,
        (
            "The state shows that BEGIN has been issued and the transaction has "
            "not ended, but no statement is running at that moment. Such sessions "
            "can hold locks, block vacuum from cleaning up rows, and keep an old "
            "snapshot alive. Very long ones are usually an application bug; "
            "idle_in_transaction_session_timeout can terminate them. Active work "
            "is shown as 'active', and a plain idle session has no open "
            "transaction."
        ),
        [PG_MONITOR_ACTIVITY, PG_CONFIG],
        vi_prompt=(
            "Trong pg_stat_activity, trạng thái 'idle in transaction' của một "
            "phiên cho biết điều gì?"
        ),
        vi_options=[
            "Giao dịch đang mở nhưng ứng dụng chưa gửi câu lệnh; phiên có thể giữ "
            "snapshot và khóa, làm chậm vacuum.",
            "Backend không có giao dịch mở và không giữ tài nguyên nào.",
            "Phiên đang thực thi một câu lệnh chạy lâu.",
            "Phiên đang chờ checkpointer hoàn tất một chu kỳ.",
        ],
        vi_explanation=(
            "Trạng thái này cho thấy BEGIN đã được phát và giao dịch chưa kết "
            "thúc, nhưng hiện không có câu lệnh nào chạy. Các phiên như vậy có "
            "thể giữ khóa, cản vacuum dọn dẹp dòng và giữ snapshot cũ tồn tại. "
            "Phiên kéo dài thường là lỗi ứng dụng; "
            "idle_in_transaction_session_timeout có thể kết thúc chúng. Công việc "
            "đang chạy hiển thị là 'active', còn phiên idle thông thường không có "
            "giao dịch mở."
        ),
        tags=["postgresql", "administration", "monitoring"],
    ),
    mcq_vi(
        "admb-easy-xact-rollback",
        ["PG-MONITOR"],
        2,
        "In pg_stat_database, what does xact_rollback count?",
        [
            "Transactions that ended with ROLLBACK or were aborted by an error.",
            "Transactions currently waiting for a lock.",
            "Checkpoints performed by the checkpointer.",
            "Rows removed by autovacuum.",
        ],
        0,
        (
            "The counter records transactions that rolled back, whether the "
            "application issued ROLLBACK or a statement error aborted the "
            "transaction. Lock waits are visible in pg_stat_activity, checkpoints "
            "in the checkpoint statistics, and removed rows in the vacuum and "
            "table statistics."
        ),
        [PG_MONITOR_STATS],
        vi_prompt=(
            "Trong pg_stat_database, xact_rollback đếm điều gì?"
        ),
        vi_options=[
            "Các giao dịch kết thúc bằng ROLLBACK hoặc bị lỗi hủy bỏ.",
            "Các giao dịch đang chờ khóa.",
            "Các checkpoint do checkpointer thực hiện.",
            "Số dòng bị autovacuum xóa.",
        ],
        vi_explanation=(
            "Bộ đếm ghi nhận các giao dịch bị hoàn tác, dù ứng dụng phát ROLLBACK "
            "hay một lỗi câu lệnh làm giao dịch bị hủy. Chờ khóa hiển thị trong "
            "pg_stat_activity, checkpoint trong thống kê checkpoint, và số dòng "
            "bị xóa trong thống kê vacuum và bảng."
        ),
        tags=["postgresql", "administration", "monitoring"],
    ),
    mcq_vi(
        "admb-easy-basebackup",
        ["PG-BACKUP"],
        2,
        "Which utility creates a physical base backup of a running PostgreSQL cluster?",
        [
            "pg_basebackup.",
            "pg_dump.",
            "pg_dumpall.",
            "ANALYZE.",
        ],
        0,
        (
            "pg_basebackup copies the cluster's data files while the server runs, "
            "producing a physical base backup that can be combined with archived "
            "WAL for point-in-time recovery or used to initialize a standby. "
            "pg_dump and pg_dumpall produce logical dumps that do not include the "
            "WAL needed for recovery to an arbitrary point. ANALYZE only refreshes "
            "planner statistics."
        ),
        [PG_BASEBACKUP, PG_WAL],
        vi_prompt=(
            "Công cụ nào tạo bản sao lưu vật lý (base backup) của một cụm "
            "PostgreSQL đang chạy?"
        ),
        vi_options=["pg_basebackup.", "pg_dump.", "pg_dumpall.", "ANALYZE."],
        vi_explanation=(
            "pg_basebackup sao chép các tệp dữ liệu của cụm khi máy chủ đang chạy, "
            "tạo bản sao lưu vật lý có thể kết hợp với WAL đã lưu trữ để phục hồi "
            "đến thời điểm bất kỳ hoặc dùng khởi tạo standby. pg_dump và "
            "pg_dumpall tạo bản dump logic không chứa WAL cần cho phục hồi đến "
            "một thời điểm tùy ý. ANALYZE chỉ làm mới thống kê cho bộ lập kế hoạch."
        ),
        tags=["postgresql", "administration", "backup"],
    ),
    # EASY: 3 essays (difficulty 2)
    essay_vi(
        "admb-easy-connection-scaling",
        ["PG-CONFIG"],
        2,
        (
            "Explain why simply increasing max_connections can make a PostgreSQL "
            "server slower, and how a connection pooler changes the picture. Cover "
            "per-connection memory, context switching, and the difference between "
            "idle sessions and active work."
        ),
        (
            "Each client connection has a dedicated server process with its own "
            "memory, including catalog caches and potentially large per-operation "
            "buffers such as work_mem while a query runs. Raising "
            "max_connections allows more concurrent sessions, but many active "
            "backends compete for CPU, memory and I/O and increase context "
            "switching, which can reduce throughput. Idle sessions still consume "
            "process memory and connection slots even though they do no work. A "
            "pooler keeps a small, controlled set of server connections and "
            "multiplexes many application connections onto them, so the database "
            "sees fewer backends; it must manage transaction or session state "
            "carefully and is not a substitute for fixing long-running "
            "transactions."
        ),
        (
            "Answer should distinguish concurrency from throughput: more "
            "connections add memory and scheduling overhead, while a pooler "
            "separates client concurrency from server concurrency."
        ),
        [
            "Says only that more connections need more memory, with no explanation of throughput or pooling.",
            "Explains per-connection memory or context switching but does not describe how a pooler helps.",
            "Explains the main resource costs and the pooler's role, but does not distinguish idle sessions from active work.",
            "Explains per-connection memory, context switching, idle versus active sessions, and how a pooler bounds server connections while preserving client concurrency.",
        ],
        [PG_CONFIG, PG_MONITOR],
        vi_prompt=(
            "Hãy giải thích vì sao chỉ tăng max_connections có thể làm máy chủ "
            "PostgreSQL chậm hơn, và bộ gộp kết nối (connection pooler) thay đổi "
            "bức tranh như thế nào. Nêu bộ nhớ theo từng kết nối, chuyển đổi ngữ "
            "cảnh, và khác biệt giữa phiên idle và công việc đang hoạt động."
        ),
        vi_reference=(
            "Mỗi kết nối khách có một tiến trình máy chủ riêng với bộ nhớ riêng, "
            "gồm bộ đệm catalog và có thể cả các bộ đệm lớn theo thao tác như "
            "work_mem khi truy vấn chạy. Tăng max_connections cho phép nhiều phiên "
            "đồng thời hơn, nhưng nhiều backend hoạt động cùng tranh CPU, bộ nhớ "
            "và I/O, đồng thời tăng chuyển đổi ngữ cảnh, có thể giảm thông lượng. "
            "Phiên idle vẫn chiếm bộ nhớ tiến trình và chỗ kết nối dù không làm "
            "việc. Pooler giữ một tập kết nối máy chủ nhỏ, được kiểm soát và ghép "
            "nhiều kết nối ứng dụng lên đó, nên cơ sở dữ liệu thấy ít backend "
            "hơn; nó phải quản lý cẩn thận trạng thái giao dịch hoặc phiên và "
            "không thay thế việc sửa các giao dịch chạy lâu."
        ),
        vi_explanation=(
            "Câu trả lời cần phân biệt mức đồng thời với thông lượng: thêm kết "
            "nối làm tăng bộ nhớ và chi phí lập lịch, còn pooler tách mức đồng "
            "thời phía ứng dụng khỏi mức đồng thời phía máy chủ."
        ),
        vi_criteria=[
            "Chỉ nói thêm kết nối cần thêm bộ nhớ, không giải thích thông lượng hay pooling.",
            "Giải thích bộ nhớ theo kết nối hoặc chuyển đổi ngữ cảnh nhưng không mô tả pooler giúp gì.",
            "Giải thích các chi phí tài nguyên chính và vai trò của pooler, nhưng chưa phân biệt phiên idle với công việc đang hoạt động.",
            "Giải thích đầy đủ bộ nhớ theo kết nối, chuyển đổi ngữ cảnh, phiên idle so với hoạt động, và cách pooler giới hạn kết nối máy chủ mà vẫn giữ mức đồng thời phía ứng dụng.",
        ],
        tags=["postgresql", "administration", "configuration"],
    ),
    essay_vi(
        "admb-easy-autovacuum-two-jobs",
        ["PG-VACUUM"],
        2,
        (
            "Autovacuum does more than reclaim space. Explain its two main jobs, "
            "VACUUM and ANALYZE, and what can go wrong when each falls behind on a "
            "high-churn table."
        ),
        (
            "VACUUM removes or marks reusable the dead row versions left by "
            "updates and deletes, updates the visibility map, and helps prevent "
            "transaction ID wraparound; if it falls behind, the table and its "
            "indexes bloat, scans read more pages, and eventually the database "
            "approaches a wraparound emergency. ANALYZE samples the table and "
            "refreshes statistics such as value distributions and distinct counts; "
            "if it falls behind, the planner underestimates or overestimates "
            "row counts and may choose bad joins or scans. Autovacuum schedules "
            "both, but thresholds and cost limits determine whether they keep up."
        ),
        (
            "The answer must separate space reclamation and wraparound protection "
            "from statistics refresh. They are related background jobs with "
            "different failure symptoms."
        ),
        [
            "Treats VACUUM and ANALYZE as the same job or lists no failure symptom.",
            "Explains one job and its failure but only mentions the other.",
            "Explains both jobs and their main failure symptoms, but omits wraparound or planner consequences.",
            "Explains VACUUM space reclamation and wraparound protection plus ANALYZE statistics, with the distinct bloat and bad-plan symptoms of each falling behind.",
        ],
        [PG_ROUTINE_VACUUM, PG_STATS, PG_MONITOR],
        vi_prompt=(
            "Autovacuum làm nhiều hơn việc thu hồi không gian. Hãy giải thích hai "
            "công việc chính của nó, VACUUM và ANALYZE, và điều gì có thể xảy ra "
            "khi mỗi công việc bị tụt lại trên một bảng có nhiều thay đổi."
        ),
        vi_reference=(
            "VACUUM xóa hoặc đánh dấu có thể tái sử dụng các phiên bản dòng đã "
            "chết do cập nhật và xóa, cập nhật bản đồ hiển thị và giúp ngăn ngừa "
            "quay vòng transaction ID; nếu tụt lại, bảng và các chỉ mục phình to, "
            "các lần quét đọc nhiều trang hơn và cuối cùng cơ sở dữ liệu tiến gần "
            "tình trạng khẩn cấp quay vòng. ANALYZE lấy mẫu bảng và làm mới thống "
            "kê như phân bố giá trị và số giá trị phân biệt; nếu tụt lại, bộ lập "
            "kế hoạch ước lượng thiếu hoặc thừa số dòng và có thể chọn phép nối "
            "hay quét kém. Autovacuum lên lịch cả hai, nhưng ngưỡng và giới hạn "
            "chi phí quyết định chúng có theo kịp hay không."
        ),
        vi_explanation=(
            "Câu trả lời phải tách việc thu hồi không gian và bảo vệ chống quay "
            "vòng khỏi việc làm mới thống kê. Đây là hai công việc nền liên quan "
            "nhưng có triệu chứng hỏng khác nhau."
        ),
        vi_criteria=[
            "Coi VACUUM và ANALYZE là cùng một việc hoặc không nêu triệu chứng hỏng nào.",
            "Giải thích một công việc và triệu chứng của nó nhưng chỉ nhắc đến công việc kia.",
            "Giải thích cả hai công việc và triệu chứng chính, nhưng bỏ sót quay vòng hoặc hậu quả với bộ lập kế hoạch.",
            "Giải thích VACUUM thu hồi không gian và chống quay vòng, ANALYZE làm mới thống kê, cùng triệu chứng phình bảng và kế hoạch kém riêng của từng việc khi tụt lại.",
        ],
        tags=["postgresql", "administration", "vacuum"],
    ),
    essay_vi(
        "admb-easy-checkpoint-wal",
        ["PG-WAL"],
        2,
        (
            "Explain the relationship between WAL, COMMIT durability and "
            "checkpoints. Why does PostgreSQL not need to write every data page at "
            "commit, and how do checkpoints affect crash recovery time and I/O "
            "spikes?"
        ),
        (
            "At commit, PostgreSQL flushes the transaction's WAL records and "
            "reports success, so the change is durable even though the corresponding "
            "data pages may still be dirty in shared buffers. Data pages are "
            "written later. A checkpoint flushes dirty data pages, marks a redo "
            "position in the WAL, and allows older WAL to be recycled. After a "
            "crash, recovery starts from the last checkpoint and replays WAL from "
            "that point, so frequent checkpoints mean a shorter recovery but more "
            "frequent I/O; infrequent checkpoints reduce background I/O but make "
            "crash recovery longer. checkpoint_completion_target spreads the write "
            "work over the interval to avoid spikes."
        ),
        (
            "The answer must connect the write-ahead rule to durability at commit, "
            "deferred data-page writes, and the checkpoint's role as a recovery "
            "starting point with an I/O trade-off."
        ),
        [
            "Claims data pages are always flushed at commit or that checkpoints make commits durable.",
            "Explains WAL at commit but not why data pages are deferred or how recovery uses checkpoints.",
            "Explains the write-ahead rule, deferred pages and checkpoints, but not the recovery-time versus I/O trade-off.",
            "Explains WAL flush at commit, deferred dirty pages, checkpoint redo positions, and the trade-off between recovery time and I/O spikes.",
        ],
        [PG_WAL, PG_WAL_CONFIG, PG_CONFIG],
        vi_prompt=(
            "Hãy giải thích mối quan hệ giữa WAL, tính bền vững của COMMIT và "
            "checkpoint. Vì sao PostgreSQL không cần ghi mọi trang dữ liệu khi "
            "commit, và checkpoint ảnh hưởng thế nào đến thời gian phục hồi sau "
            "sự cố và các đợt tăng I/O?"
        ),
        vi_reference=(
            "Khi commit, PostgreSQL ghi xuống WAL của giao dịch và báo thành công, "
            "nên thay đổi vẫn bền vững dù các trang dữ liệu tương ứng có thể còn "
            "bẩn trong shared buffers. Các trang dữ liệu được ghi sau đó. "
            "Checkpoint ghi các trang dữ liệu bẩn, đánh dấu vị trí redo trong WAL "
            "và cho phép tái sử dụng WAL cũ hơn. Sau sự cố, phục hồi bắt đầu từ "
            "checkpoint gần nhất và phát lại WAL từ điểm đó, nên checkpoint thường "
            "xuyên cho thời gian phục hồi ngắn hơn nhưng I/O thường xuyên hơn; "
            "checkpoint ít thường xuyên giảm I/O nền nhưng làm phục hồi lâu hơn. "
            "checkpoint_completion_target trải đều công việc ghi trong khoảng thời "
            "gian để tránh đột biến."
        ),
        vi_explanation=(
            "Câu trả lời phải nối quy tắc ghi trước (write-ahead) với tính bền "
            "vững khi commit, việc ghi trang dữ liệu bị hoãn, và vai trò của "
            "checkpoint là điểm bắt đầu phục hồi với đánh đổi I/O."
        ),
        vi_criteria=[
            "Cho rằng trang dữ liệu luôn được ghi khi commit hoặc checkpoint tạo ra tính bền vững của commit.",
            "Giải thích WAL khi commit nhưng không giải thích vì sao ghi trang dữ liệu bị hoãn hoặc phục hồi dùng checkpoint thế nào.",
            "Giải thích quy tắc ghi trước, ghi trang hoãn và checkpoint, nhưng không nêu đánh đổi giữa thời gian phục hồi và I/O.",
            "Giải thích đầy đủ ghi WAL khi commit, trang bẩn được ghi sau, vị trí redo của checkpoint, và đánh đổi giữa thời gian phục hồi với các đợt tăng I/O.",
        ],
        tags=["postgresql", "administration", "wal"],
    ),
]

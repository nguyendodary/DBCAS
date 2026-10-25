"""Concurrency fill: transaction semantics, anomalies and lock behaviour."""

from gap_lib import essay_vi, mcq_vi
from sources import (
    PG_CONFIG,
    PG_CREATE_TABLE,
    PG_ISOLATION,
    PG_LOCK,
    PG_MONITOR_STATS,
    PG_MVCC,
    PG_PROTOCOL,
    PG_SERIALIZATION_FAILURE,
    PG_STORAGE_HOT,
    PG_SUBXACTS,
    PG_TXN,
    PG_WAL,
)

QUESTIONS = [
    # EASY: 4 MCQ (difficulty 2)
    mcq_vi(
        "concb-easy-commit-guarantee",
        ["PG-TXN"],
        2,
        "What does a successful COMMIT guarantee?",
        [
            "The transaction's changes become visible and, with synchronous "
            "commit, its WAL is flushed before success is reported.",
            "All dirty data pages of the transaction have already been written to "
            "their tables.",
            "Every index on the affected tables has been rebuilt.",
            "The session's locks are retained until the client disconnects.",
        ],
        0,
        (
            "Commit makes the transaction's changes permanent from the "
            "application's point of view. With synchronous commit PostgreSQL waits "
            "for the WAL records to be flushed before reporting success, but data "
            "pages may still be written later by the background writer or a "
            "checkpoint. Indexes are updated as part of the changes, not rebuilt at "
            "commit, and transaction locks are released when the transaction ends."
        ),
        [PG_TXN, PG_WAL],
        vi_prompt="Một COMMIT thành công bảo đảm điều gì?",
        vi_options=[
            "Các thay đổi của giao dịch trở nên hiển thị và, với commit đồng bộ, "
            "WAL của giao dịch được ghi xuống trước khi báo thành công.",
            "Mọi trang dữ liệu bẩn của giao dịch đã được ghi vào bảng tương ứng.",
            "Mọi chỉ mục trên các bảng bị ảnh hưởng đã được xây dựng lại.",
            "Khóa của phiên được giữ đến khi ứng dụng ngắt kết nối.",
        ],
        vi_explanation=(
            "Commit làm thay đổi của giao dịch trở nên vĩnh viễn dưới góc nhìn ứng "
            "dụng. Với commit đồng bộ, PostgreSQL chờ các bản ghi WAL được ghi "
            "xuống trước khi báo thành công, nhưng các trang dữ liệu vẫn có thể "
            "được ghi sau đó bởi background writer hoặc checkpoint. Chỉ mục được "
            "cập nhật cùng các thay đổi, không xây dựng lại khi commit, và khóa "
            "giao dịch được giải phóng khi giao dịch kết thúc."
        ),
        tags=["postgresql", "concurrency", "transactions"],
    ),
    mcq_vi(
        "concb-easy-dirty-read",
        ["PG-ISOLATION"],
        2,
        "What is a dirty read?",
        [
            "Reading data written by another transaction that has not committed; "
            "PostgreSQL's READ COMMITTED prevents it.",
            "Reading the same row twice and getting the same values.",
            "Reading a row that was committed after the reader's snapshot was "
            "taken.",
            "Reading a table while another session holds a row lock.",
        ],
        0,
        (
            "A dirty read observes uncommitted data from another transaction, "
            "which could still roll back. PostgreSQL does not allow dirty reads at "
            "any supported isolation level; READ COMMITTED takes a new snapshot "
            "per statement and only sees committed data. Re-reading a row and "
            "getting the same values describes repeatable behaviour, while seeing "
            "newly committed rows is a non-repeatable or phantom phenomenon, not a "
            "dirty read."
        ),
        [PG_ISOLATION],
        vi_prompt="Dirty read là gì?",
        vi_options=[
            "Đọc dữ liệu do giao dịch khác ghi khi chưa commit; READ COMMITTED "
            "của PostgreSQL ngăn hiện tượng này.",
            "Đọc cùng một dòng hai lần và nhận cùng giá trị.",
            "Đọc một dòng đã được commit sau thời điểm chụp ảnh của người đọc.",
            "Đọc một bảng trong khi phiên khác đang giữ khóa dòng.",
        ],
        vi_explanation=(
            "Dirty read quan sát dữ liệu chưa commit của giao dịch khác, dữ liệu "
            "có thể vẫn bị hoàn tác. PostgreSQL không cho phép dirty read ở bất kỳ "
            "mức cô lập nào được hỗ trợ; READ COMMITTED chụp ảnh mới cho từng câu "
            "lệnh và chỉ thấy dữ liệu đã commit. Đọc lại một dòng và nhận cùng giá "
            "trị mô tả tính lặp lại, còn thấy dòng mới commit là hiện tượng "
            "non-repeatable hoặc phantom, không phải dirty read."
        ),
        tags=["postgresql", "concurrency", "isolation"],
    ),
    mcq_vi(
        "concb-easy-independent-rows",
        ["PG-LOCK"],
        2,
        (
            "Two transactions update different rows of the same table at the same "
            "time. What normally happens?"
        ),
        [
            "Both can proceed concurrently because row-level locks conflict only "
            "when the same row is targeted.",
            "The second transaction waits until the first commits because UPDATE "
            "takes an exclusive table lock.",
            "Both transactions are aborted immediately with a deadlock error.",
            "The second transaction sees the first transaction's uncommitted "
            "changes.",
        ],
        0,
        (
            "PostgreSQL uses row-level locks for ordinary UPDATE and DELETE; "
            "different rows do not conflict, so the two transactions can proceed "
            "concurrently. An UPDATE does take a table-level lock, but it is a "
            "mode that does not block ordinary row updates. Deadlocks require "
            "conflicting lock waits, and uncommitted changes are not visible to "
            "other transactions."
        ),
        [PG_LOCK, PG_MVCC],
        vi_prompt=(
            "Hai giao dịch cập nhật các dòng khác nhau của cùng một bảng cùng lúc. "
            "Thông thường điều gì xảy ra?"
        ),
        vi_options=[
            "Cả hai có thể chạy đồng thời vì khóa cấp dòng chỉ xung đột khi cùng "
            "nhắm tới một dòng.",
            "Giao dịch thứ hai chờ giao dịch đầu commit vì UPDATE lấy khóa độc "
            "quyền toàn bảng.",
            "Cả hai giao dịch bị hủy ngay với lỗi deadlock.",
            "Giao dịch thứ hai thấy các thay đổi chưa commit của giao dịch đầu.",
        ],
        vi_explanation=(
            "PostgreSQL dùng khóa cấp dòng cho UPDATE và DELETE thông thường; các "
            "dòng khác nhau không xung đột nên hai giao dịch có thể chạy đồng "
            "thời. UPDATE có lấy khóa cấp bảng nhưng ở chế độ không chặn cập nhật "
            "dòng thông thường. Deadlock cần các lần chờ khóa xung đột, và thay "
            "đổi chưa commit không hiển thị với giao dịch khác."
        ),
        tags=["postgresql", "concurrency", "locking"],
    ),
    mcq_vi(
        "concb-easy-disconnect",
        ["PG-TXN"],
        2,
        (
            "A client disconnects while its transaction is still open. What "
            "happens to the transaction?"
        ),
        [
            "The server rolls it back and releases its locks; uncommitted changes "
            "are discarded.",
            "The server commits it automatically to avoid losing work.",
            "It remains open until an administrator terminates the backend.",
            "It is committed but only the WAL records are kept.",
        ],
        0,
        (
            "If a connection is lost before COMMIT, the server cannot know whether "
            "the client intended to commit, so the transaction is rolled back. Its "
            "uncommitted changes are discarded and its locks and snapshot are "
            "released, allowing vacuum to proceed. PostgreSQL does not "
            "auto-commit an interrupted transaction."
        ),
        [PG_TXN, PG_PROTOCOL],
        vi_prompt=(
            "Ứng dụng ngắt kết nối khi giao dịch vẫn đang mở. Điều gì xảy ra với "
            "giao dịch?"
        ),
        vi_options=[
            "Máy chủ hoàn tác giao dịch và giải phóng khóa; các thay đổi chưa "
            "commit bị bỏ.",
            "Máy chủ tự động commit để tránh mất công việc.",
            "Giao dịch vẫn mở cho đến khi quản trị viên kết thúc backend.",
            "Giao dịch được commit nhưng chỉ giữ lại các bản ghi WAL.",
        ],
        vi_explanation=(
            "Nếu kết nối mất trước COMMIT, máy chủ không thể biết ứng dụng có định "
            "commit hay không, nên giao dịch bị hoàn tác. Các thay đổi chưa commit "
            "bị bỏ, khóa và snapshot được giải phóng, cho phép vacuum tiếp tục. "
            "PostgreSQL không tự commit một giao dịch bị gián đoạn."
        ),
        tags=["postgresql", "concurrency", "transactions"],
    ),
    # EASY: 3 essays (difficulty 2)
    essay_vi(
        "concb-easy-savepoints",
        ["PG-TXN"],
        2,
        (
            "Explain how SAVEPOINT works, including ROLLBACK TO SAVEPOINT and "
            "RELEASE, and give a realistic case where partial rollback is better "
            "than aborting the whole transaction."
        ),
        (
            "SAVEPOINT name marks a point inside the current transaction. After a "
            "later statement fails, ROLLBACK TO SAVEPOINT name undoes all changes "
            "made after the savepoint while keeping the transaction and the work "
            "before the savepoint alive. RELEASE discards the savepoint marker "
            "without undoing its work. A typical case is a batch that inserts many "
            "rows: each item is wrapped in a savepoint so a duplicate or invalid "
            "row can be rolled back individually and the batch can continue, "
            "instead of aborting and reprocessing everything. Savepoints create "
            "subtransactions, so using one per row has overhead and should be "
            "measured."
        ),
        (
            "The answer must distinguish rolling back to a savepoint from rolling "
            "back the whole transaction and explain the practical cost of "
            "subtransactions."
        ),
        [
            "Confuses SAVEPOINT with a new independent transaction or says it commits work.",
            "Explains partial rollback but not RELEASE, or gives no realistic use case.",
            "Explains savepoints, partial rollback and a use case, but omits subtransaction overhead.",
            "Explains SAVEPOINT, ROLLBACK TO, RELEASE, a realistic partial-rollback case and the subtransaction cost.",
        ],
        [PG_TXN, PG_SUBXACTS],
        vi_prompt=(
            "Hãy giải thích SAVEPOINT hoạt động thế nào, gồm ROLLBACK TO SAVEPOINT "
            "và RELEASE, và nêu một tình huống thực tế mà hoàn tác một phần tốt hơn "
            "hủy toàn bộ giao dịch."
        ),
        vi_reference=(
            "SAVEPOINT tên đánh dấu một điểm trong giao dịch hiện tại. Sau khi một "
            "câu lệnh phía sau thất bại, ROLLBACK TO SAVEPOINT tên hoàn tác mọi "
            "thay đổi sau savepoint nhưng giữ giao dịch và công việc trước "
            "savepoint. RELEASE xóa dấu savepoint mà không hoàn tác công việc của "
            "nó. Tình huống điển hình là lô chèn nhiều dòng: mỗi mục được bọc "
            "trong một savepoint để dòng trùng hoặc không hợp lệ được hoàn tác "
            "riêng và lô tiếp tục, thay vì hủy toàn bộ rồi xử lý lại từ đầu. "
            "Savepoint tạo giao dịch con, nên dùng một savepoint cho mỗi dòng có "
            "chi phí và cần đo lường."
        ),
        vi_explanation=(
            "Câu trả lời phải phân biệt hoàn tác đến savepoint với hoàn tác toàn "
            "bộ giao dịch và giải thích chi phí thực tế của giao dịch con."
        ),
        vi_criteria=[
            "Nhầm SAVEPOINT với một giao dịch độc lập mới hoặc cho rằng nó commit công việc.",
            "Giải thích hoàn tác một phần nhưng không nêu RELEASE, hoặc không có tình huống sử dụng thực tế.",
            "Giải thích savepoint, hoàn tác một phần và tình huống sử dụng, nhưng bỏ sót chi phí giao dịch con.",
            "Giải thích SAVEPOINT, ROLLBACK TO, RELEASE, một tình huống hoàn tác một phần thực tế và chi phí giao dịch con.",
        ],
        tags=["postgresql", "concurrency", "transactions"],
    ),
    essay_vi(
        "concb-easy-optimistic-pessimistic",
        ["PG-LOCK", "PG-ISOLATION"],
        2,
        (
            "Compare optimistic and pessimistic concurrency control in an "
            "application using PostgreSQL. Where does SELECT FOR UPDATE fit, and "
            "where do version checks plus retry or SERIALIZABLE transactions fit? "
            "Give one trade-off of each."
        ),
        (
            "Pessimistic control prevents conflicts before they happen: SELECT FOR "
            "UPDATE locks the selected rows so another transaction must wait, "
            "which is simple but can serialize work and create lock waits or "
            "deadlocks. Optimistic control lets transactions proceed and checks at "
            "write time, for example with a version column incremented in an "
            "UPDATE whose WHERE clause includes the old version; if no row is "
            "updated, the application retries. SERIALIZABLE with retry on "
            "serialization failures takes this further by detecting dangerous "
            "interleavings. Optimistic control has less blocking but requires "
            "correct retry logic and can waste work under high contention; "
            "pessimistic control is easier to reason about for short, hot updates "
            "but reduces concurrency."
        ),
        (
            "The answer must match each technique to a scenario and name a real "
            "cost, not claim one approach is always better."
        ),
        [
            "Defines the terms but gives no PostgreSQL mechanism or trade-off.",
            "Explains one approach and its mechanism but not the other.",
            "Explains both approaches with a mechanism and a trade-off, but does not connect SERIALIZABLE or retry to optimistic control.",
            "Explains pessimistic row locking and optimistic version checks or SERIALIZABLE retry, with correct trade-offs for contention and wasted work.",
        ],
        [PG_LOCK, PG_ISOLATION],
        vi_prompt=(
            "Hãy so sánh kiểm soát đồng thời lạc quan và bi quan trong một ứng dụng "
            "dùng PostgreSQL. SELECT FOR UPDATE phù hợp ở đâu, còn kiểm tra phiên "
            "bản cộng với thử lại hoặc giao dịch SERIALIZABLE phù hợp ở đâu? Nêu "
            "một đánh đổi của mỗi cách."
        ),
        vi_reference=(
            "Kiểm soát bi quan ngăn xung đột trước khi xảy ra: SELECT FOR UPDATE "
            "khóa các dòng được chọn để giao dịch khác phải chờ, đơn giản nhưng có "
            "thể tuần tự hóa công việc và tạo chờ khóa hoặc deadlock. Kiểm soát lạc "
            "quan cho giao dịch tiếp tục và kiểm tra khi ghi, ví dụ dùng cột phiên "
            "bản tăng lên trong UPDATE với WHERE chứa phiên bản cũ; nếu không dòng "
            "nào được cập nhật, ứng dụng thử lại. SERIALIZABLE với thử lại khi gặp "
            "lỗi tuần tự hóa đi xa hơn bằng cách phát hiện các xen kẽ nguy hiểm. "
            "Kiểm soát lạc quan ít chặn hơn nhưng cần logic thử lại đúng và có thể "
            "lãng phí công việc khi tranh chấp cao; kiểm soát bi quan dễ suy luận "
            "hơn cho cập nhật ngắn, nóng nhưng giảm đồng thời."
        ),
        vi_explanation=(
            "Câu trả lời phải gắn từng kỹ thuật với một tình huống và nêu chi phí "
            "thực, không khẳng định một cách luôn tốt hơn."
        ),
        vi_criteria=[
            "Định nghĩa khái niệm nhưng không nêu cơ chế PostgreSQL hay đánh đổi.",
            "Giải thích một cách và cơ chế của nó nhưng không giải thích cách còn lại.",
            "Giải thích cả hai cách với cơ chế và đánh đổi, nhưng không gắn SERIALIZABLE hoặc thử lại với kiểm soát lạc quan.",
            "Giải thích khóa dòng bi quan và kiểm tra phiên bản hoặc thử lại SERIALIZABLE lạc quan, cùng đánh đổi đúng về tranh chấp và công việc lãng phí.",
        ],
        tags=["postgresql", "concurrency", "locking"],
    ),
    essay_vi(
        "concb-easy-aborted-transaction",
        ["PG-TXN"],
        2,
        (
            "A statement fails inside an open transaction. Explain why subsequent "
            "statements fail until the transaction is rolled back, and how a "
            "savepoint changes the recovery path."
        ),
        (
            "In PostgreSQL an error aborts the whole transaction, not just the "
            "failed statement. The session is left in a failed transaction state, "
            "and further commands are rejected with a message such as 'current "
            "transaction is aborted' until the application issues ROLLBACK or "
            "COMMIT; COMMIT in this state effectively rolls back. The reason is "
            "that the database cannot guarantee a consistent state after a failed "
            "operation without undoing the transaction's earlier effects. If a "
            "SAVEPOINT was established before the failing statement, ROLLBACK TO "
            "that savepoint clears the error, undoes only the work after the "
            "savepoint, and allows the transaction to continue."
        ),
        (
            "The answer must explain the failed-transaction state, why only a full "
            "rollback normally clears it, and the savepoint exception."
        ),
        [
            "Says only the failed statement is undone or that the session can continue normally.",
            "Explains the aborted transaction but not why, or omits savepoint recovery.",
            "Explains abort and rollback plus savepoints, but not why the whole transaction is aborted.",
            "Explains the failed-transaction state and its reason, the need to roll back, and how ROLLBACK TO SAVEPOINT allows partial recovery.",
        ],
        [PG_TXN],
        vi_prompt=(
            "Một câu lệnh thất bại trong giao dịch đang mở. Hãy giải thích vì sao "
            "các câu lệnh sau đó đều thất bại cho đến khi giao dịch được hoàn tác, "
            "và savepoint thay đổi đường phục hồi như thế nào."
        ),
        vi_reference=(
            "Trong PostgreSQL, lỗi hủy toàn bộ giao dịch chứ không chỉ câu lệnh "
            "thất bại. Phiên bị đưa vào trạng thái giao dịch lỗi, và các lệnh tiếp "
            "theo bị từ chối với thông báo như 'current transaction is aborted' "
            "cho đến khi ứng dụng phát ROLLBACK hoặc COMMIT; COMMIT trong trạng "
            "thái này thực chất là hoàn tác. Lý do là cơ sở dữ liệu không thể bảo "
            "đảm trạng thái nhất quán sau thao tác lỗi nếu không hoàn tác các hiệu "
            "ứng trước đó của giao dịch. Nếu một SAVEPOINT được tạo trước câu lệnh "
            "lỗi, ROLLBACK TO savepoint đó xóa lỗi, chỉ hoàn tác công việc sau "
            "savepoint và cho giao dịch tiếp tục."
        ),
        vi_explanation=(
            "Câu trả lời phải giải thích trạng thái giao dịch lỗi, vì sao thông "
            "thường chỉ hoàn tác toàn bộ mới xóa được, và ngoại lệ savepoint."
        ),
        vi_criteria=[
            "Chỉ nói câu lệnh lỗi bị hoàn tác hoặc phiên có thể tiếp tục bình thường.",
            "Giải thích giao dịch bị hủy nhưng không nêu lý do, hoặc bỏ sót phục hồi bằng savepoint.",
            "Giải thích hủy và hoàn tác cùng savepoint, nhưng không nêu vì sao toàn bộ giao dịch bị hủy.",
            "Giải thích trạng thái giao dịch lỗi và lý do, nhu cầu hoàn tác, và cách ROLLBACK TO SAVEPOINT cho phép phục hồi một phần.",
        ],
        tags=["postgresql", "concurrency", "transactions"],
    ),
    # MEDIUM: 1 essay (difficulty 3)
    essay_vi(
        "concb-medium-retry-design",
        ["PG-ISOLATION"],
        3,
        (
            "Design application retry handling for PostgreSQL serialization "
            "failures (SQLSTATE 40001) and deadlocks (40P01). Explain where the "
            "retry boundary goes, which errors are retryable, how to avoid "
            "duplicate side effects, and what to log and alert on."
        ),
        (
            "Both errors abort the current transaction, so the retry boundary must "
            "be the whole transaction, not a single statement. The application "
            "should detect the SQLSTATE, roll back, and replay the transaction "
            "from the beginning with a bounded number of attempts, exponential "
            "backoff and jitter to avoid synchronized retries. Retrying should not "
            "duplicate external side effects: keep the transaction free of "
            "irreversible external calls, or use an outbox and idempotency keys. "
            "Only transient concurrency errors should be retried; constraint "
            "violations, syntax errors and authorization failures are permanent "
            "and must surface to the caller. Log the SQLSTATE, attempt count, "
            "transaction identity and latency, and alert on a rising retry rate "
            "because it signals contention or an inefficient access pattern, not "
            "a healthy success."
        ),
        (
            "The answer must place the retry at transaction scope, distinguish "
            "transient from permanent errors, and protect side effects and "
            "observability."
        ),
        [
            "Retries the failed statement alone or retries every error.",
            "Retries the transaction but ignores idempotency or which errors are safe to retry.",
            "Covers transaction scope and retryable SQLSTATEs, but omits side-effect safety or observability.",
            "Retries the whole transaction with bounded backoff, handles idempotency, excludes permanent errors and logs or alerts on retry rate.",
        ],
        [PG_ISOLATION, PG_LOCK, PG_SERIALIZATION_FAILURE],
        vi_prompt=(
            "Hãy thiết kế cách ứng dụng thử lại khi gặp lỗi tuần tự hóa "
            "(SQLSTATE 40001) và deadlock (40P01) trong PostgreSQL. Nêu ranh giới "
            "thử lại, lỗi nào có thể thử lại, cách tránh hiệu ứng phụ trùng lặp, "
            "và ghi log hoặc cảnh báo những gì."
        ),
        vi_reference=(
            "Cả hai lỗi đều hủy giao dịch hiện tại, nên ranh giới thử lại phải là "
            "toàn bộ giao dịch, không phải một câu lệnh. Ứng dụng nên nhận diện "
            "SQLSTATE, hoàn tác rồi chạy lại giao dịch từ đầu với số lần thử có "
            "giới hạn, lùi thời gian theo cấp số nhân kèm nhiễu để tránh thử lại "
            "đồng loạt. Không nên làm trùng hiệu ứng phụ bên ngoài: giữ giao dịch "
            "không chứa lời gọi bên ngoài không thể hoàn tác, hoặc dùng outbox và "
            "khóa idempotency. Chỉ nên thử lại lỗi đồng thời tạm thời; vi phạm "
            "ràng buộc, lỗi cú pháp và lỗi phân quyền là vĩnh viễn và phải trả về "
            "cho người gọi. Ghi log SQLSTATE, số lần thử, định danh giao dịch và "
            "độ trễ, cảnh báo khi tỷ lệ thử lại tăng vì đó là dấu hiệu tranh chấp "
            "hoặc mẫu truy cập kém hiệu quả, không phải thành công lành mạnh."
        ),
        vi_explanation=(
            "Câu trả lời phải đặt việc thử lại ở phạm vi giao dịch, phân biệt lỗi "
            "tạm thời với lỗi vĩnh viễn, đồng thời bảo vệ hiệu ứng phụ và khả "
            "năng quan sát."
        ),
        vi_criteria=[
            "Chỉ thử lại câu lệnh lỗi hoặc thử lại mọi lỗi.",
            "Thử lại giao dịch nhưng bỏ qua tính idempotency hoặc lỗi nào an toàn để thử lại.",
            "Nêu phạm vi giao dịch và các SQLSTATE có thể thử lại, nhưng bỏ sót an toàn hiệu ứng phụ hoặc khả năng quan sát.",
            "Thử lại toàn bộ giao dịch với lùi thời gian có giới hạn, xử lý idempotency, loại trừ lỗi vĩnh viễn và ghi log hoặc cảnh báo theo tỷ lệ thử lại.",
        ],
        tags=["postgresql", "concurrency", "isolation"],
    ),
    # HARD: 3 MCQ (difficulty 4)
    mcq_vi(
        "concb-hard-ssi-structure",
        ["PG-ISOLATION", "PG-MVCC"],
        4,
        "How does PostgreSQL implement SERIALIZABLE isolation?",
        [
            "It uses Serializable Snapshot Isolation, tracking read-write "
            "dependencies and aborting transactions when a dangerous structure is "
            "detected.",
            "It acquires two-phase read locks on every row read, so readers block "
            "writers.",
            "It runs all serializable transactions one at a time using a global "
            "mutex.",
            "It prevents serialization failures by retrying failed statements "
            "inside the same transaction.",
        ],
        0,
        (
            "PostgreSQL's SERIALIZABLE builds on snapshot isolation and adds "
            "Serializable Snapshot Isolation, which monitors read-write "
            "antidependencies and aborts a transaction when the pattern could "
            "produce a serialization anomaly. It does not use two-phase locking "
            "for ordinary reads, so readers do not block writers, and it does not "
            "serialize transactions with a global mutex. A serialization failure "
            "means the application must roll back and retry the whole transaction; "
            "the server does not retry statements inside it."
        ),
        [PG_ISOLATION, PG_MVCC],
        vi_prompt="PostgreSQL thực hiện mức cô lập SERIALIZABLE như thế nào?",
        vi_options=[
            "Dùng Serializable Snapshot Isolation, theo dõi phụ thuộc đọc-ghi và "
            "hủy giao dịch khi phát hiện cấu trúc nguy hiểm.",
            "Lấy khóa đọc hai pha trên mọi dòng được đọc, nên người đọc chặn "
            "người ghi.",
            "Chạy mọi giao dịch tuần tự lần lượt bằng một mutex toàn cục.",
            "Tránh lỗi tuần tự hóa bằng cách tự thử lại câu lệnh lỗi trong cùng "
            "giao dịch.",
        ],
        vi_explanation=(
            "SERIALIZABLE của PostgreSQL dựa trên snapshot isolation và thêm "
            "Serializable Snapshot Isolation, theo dõi phụ thuộc đọc-ghi và hủy "
            "giao dịch khi mẫu xen kẽ có thể tạo ra bất thường tuần tự hóa. Nó "
            "không dùng khóa hai pha cho đọc thông thường, nên người đọc không "
            "chặn người ghi, và không tuần tự hóa giao dịch bằng mutex toàn cục. "
            "Lỗi tuần tự hóa nghĩa là ứng dụng phải hoàn tác và thử lại toàn bộ "
            "giao dịch; máy chủ không tự thử lại câu lệnh bên trong."
        ),
        tags=["postgresql", "concurrency", "isolation"],
    ),
    mcq_vi(
        "concb-hard-no-gap-locks",
        ["PG-LOCK"],
        4,
        (
            "Transaction A runs SELECT ... FOR UPDATE and finds no row matching "
            "id = 10. Transaction B then inserts id = 10 and commits. What does "
            "PostgreSQL's row locking prevent?"
        ),
        [
            "Nothing for the missing row: PostgreSQL has no gap locks, so B can "
            "insert; a unique constraint, advisory lock or SERIALIZABLE is needed "
            "to coordinate this.",
            "It blocks B because SELECT FOR UPDATE locks the entire index range "
            "where the row would be.",
            "It blocks B only if the table has a foreign key.",
            "It forces B to wait until A ends, then B fails with a duplicate-key "
            "error.",
        ],
        0,
        (
            "SELECT FOR UPDATE locks rows that exist; if the predicate matches no "
            "row, there is no row to lock. PostgreSQL does not take gap locks like "
            "some other databases, so a concurrent insert into the missing key "
            "range can proceed. To coordinate this, use a unique constraint, an "
            "advisory lock, or SERIALIZABLE isolation, which detects a dangerous "
            "dependency and aborts one transaction with a serialization failure."
        ),
        [PG_LOCK, PG_ISOLATION],
        vi_prompt=(
            "Giao dịch A chạy SELECT ... FOR UPDATE và không tìm thấy dòng nào khớp "
            "id = 10. Sau đó giao dịch B chèn id = 10 và commit. Khóa dòng của "
            "PostgreSQL ngăn được điều gì?"
        ),
        vi_options=[
            "Không ngăn gì với dòng chưa tồn tại: PostgreSQL không có gap lock nên "
            "B có thể chèn; cần ràng buộc duy nhất, advisory lock hoặc "
            "SERIALIZABLE để phối hợp.",
            "Nó chặn B vì SELECT FOR UPDATE khóa toàn bộ khoảng chỉ mục nơi dòng "
            "sẽ nằm.",
            "Nó chỉ chặn B nếu bảng có khóa ngoại.",
            "Nó buộc B chờ đến khi A kết thúc, sau đó B thất bại với lỗi trùng khóa.",
        ],
        vi_explanation=(
            "SELECT FOR UPDATE khóa các dòng tồn tại; nếu vị từ không khớp dòng "
            "nào thì không có dòng để khóa. PostgreSQL không lấy gap lock như một "
            "số cơ sở dữ liệu khác, nên lệnh chèn đồng thời vào khoảng khóa còn "
            "thiếu vẫn có thể chạy. Để phối hợp, dùng ràng buộc duy nhất, advisory "
            "lock hoặc mức SERIALIZABLE, vốn phát hiện phụ thuộc nguy hiểm và hủy "
            "một giao dịch với lỗi tuần tự hóa."
        ),
        tags=["postgresql", "concurrency", "locking"],
    ),
    mcq_vi(
        "concb-hard-hot-update",
        ["PG-MVCC"],
        4,
        (
            "Under what condition can an UPDATE avoid creating new index entries "
            "for the updated row (a HOT update)?"
        ),
        [
            "When no indexed column changes and the new row version fits on the "
            "same page with enough free space.",
            "Whenever the table has a primary key.",
            "Whenever the transaction uses READ COMMITTED.",
            "Only when the table has no indexes at all.",
        ],
        0,
        (
            "A HOT update keeps the new row version on the same page and avoids "
            "new index entries when no indexed column is changed and there is "
            "enough free space, often reserved with a lower fillfactor. The old "
            "version is chained to the new one, and index entries point to the "
            "chain. A primary key, the isolation level, or having no indexes at "
            "all are not the conditions; tables with no indexes can of course "
            "avoid index work, but HOT still matters for indexed tables."
        ),
        [PG_STORAGE_HOT, PG_CREATE_TABLE, PG_MONITOR_STATS],
        vi_prompt=(
            "Trong điều kiện nào một UPDATE có thể tránh tạo mục chỉ mục mới cho "
            "dòng được cập nhật (cập nhật HOT)?"
        ),
        vi_options=[
            "Khi không có cột nào được đánh chỉ mục thay đổi và phiên bản dòng mới "
            "vừa cùng trang với đủ không gian trống.",
            "Bất cứ khi nào bảng có khóa chính.",
            "Bất cứ khi nào giao dịch dùng READ COMMITTED.",
            "Chỉ khi bảng hoàn toàn không có chỉ mục.",
        ],
        vi_explanation=(
            "Cập nhật HOT giữ phiên bản dòng mới trên cùng trang và tránh mục chỉ "
            "mục mới khi không cột được đánh chỉ mục nào thay đổi và có đủ không "
            "gian trống, thường được dự trữ bằng fillfactor thấp hơn. Phiên bản cũ "
            "được nối chuỗi tới phiên bản mới, và mục chỉ mục trỏ tới chuỗi. Khóa "
            "chính, mức cô lập, hay việc không có chỉ mục nào không phải điều kiện; "
            "bảng không có chỉ mục đương nhiên tránh được việc chỉ mục, nhưng HOT "
            "vẫn quan trọng với bảng có chỉ mục."
        ),
        tags=["postgresql", "concurrency", "mvcc"],
    ),
]

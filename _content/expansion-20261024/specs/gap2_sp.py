"""Server Programming fill: function, procedure and trigger behaviour."""

from gap_lib import essay_vi, mcq_vi
from sources import (
    PG_ALTER,
    PG_FUNCTIONS_INFO,
    PG_PLPGSQL,
    PG_PLPGSQL_TRIGGER,
    PG_PROC,
    PG_TRIGGER,
    PG_UDF,
)

QUESTIONS = [
    # EASY: 6 MCQ (difficulty 2)
    mcq_vi(
        "spb-easy-returns-void",
        ["PG-UDF"],
        2,
        "A SQL function is declared RETURNS void. What does that mean for the caller?",
        [
            "The function performs work and returns no useful value; it can be "
            "called with SELECT, or with PERFORM inside PL/pgSQL.",
            "The function cannot be called at all.",
            "The function returns an empty table with one column.",
            "The function must be used only in a trigger.",
        ],
        0,
        (
            "RETURNS void means the function has no result value. It is still "
            "executed for its side effects, for example when called as SELECT "
            "perform_maintenance();. Inside PL/pgSQL, PERFORM is the usual way to "
            "discard a result. It is not restricted to triggers, and it does not "
            "return a table."
        ),
        [PG_UDF, PG_PLPGSQL],
        vi_prompt=(
            "Một hàm SQL được khai báo RETURNS void. Điều đó có nghĩa gì với người "
            "gọi?"
        ),
        vi_options=[
            "Hàm thực hiện công việc và không trả về giá trị hữu ích; có thể gọi "
            "bằng SELECT, hoặc PERFORM trong PL/pgSQL.",
            "Không thể gọi hàm.",
            "Hàm trả về một bảng rỗng có một cột.",
            "Hàm chỉ được dùng trong trigger.",
        ],
        vi_explanation=(
            "RETURNS void nghĩa là hàm không có giá trị kết quả. Hàm vẫn được thực "
            "thi vì hiệu ứng phụ, ví dụ khi gọi SELECT perform_maintenance();. "
            "Trong PL/pgSQL, PERFORM là cách thông thường để bỏ qua kết quả. Hàm "
            "không bị giới hạn cho trigger và không trả về bảng."
        ),
        tags=["postgresql", "server-programming", "functions"],
    ),
    mcq_vi(
        "spb-easy-trigger-return-type",
        ["PG-TRIGGER"],
        2,
        "What return type must a trigger function declare?",
        [
            "trigger, and a row-level BEFORE trigger returns NEW to continue with "
            "the row or NULL to skip it.",
            "void, because a trigger never returns anything.",
            "integer, which is the number of affected rows.",
            "The same row type as the table.",
        ],
        0,
        (
            "A function used by CREATE TRIGGER must return type trigger. For a "
            "row-level BEFORE trigger, returning NEW lets the operation proceed "
            "with the possibly modified row, while returning NULL skips the "
            "operation for that row. AFTER trigger return values are ignored. void, "
            "integer and the table row type are not valid trigger function return "
            "types."
        ),
        [PG_TRIGGER, PG_PLPGSQL],
        vi_prompt="Hàm trigger phải khai báo kiểu trả về nào?",
        vi_options=[
            "trigger, và trigger BEFORE cấp dòng trả NEW để tiếp tục với dòng hoặc "
            "NULL để bỏ qua.",
            "void, vì trigger không bao giờ trả về gì.",
            "integer, là số dòng bị ảnh hưởng.",
            "Cùng kiểu dòng với bảng.",
        ],
        vi_explanation=(
            "Hàm dùng cho CREATE TRIGGER phải trả về kiểu trigger. Với trigger "
            "BEFORE cấp dòng, trả NEW cho phép thao tác tiếp tục với dòng có thể đã "
            "sửa, còn trả NULL bỏ qua thao tác cho dòng đó. Giá trị trả về của "
            "trigger AFTER bị bỏ qua. void, integer và kiểu dòng của bảng không "
            "phải kiểu trả về hợp lệ cho hàm trigger."
        ),
        tags=["postgresql", "server-programming", "triggers"],
    ),
    mcq_vi(
        "spb-easy-create-or-replace",
        ["PG-UDF"],
        2,
        "What does CREATE OR REPLACE FUNCTION do when a function with the same name and argument types exists?",
        [
            "It replaces the body and attributes without dropping the function, "
            "but it cannot change the return type.",
            "It creates a second overloaded function with the same signature.",
            "It drops all dependent objects and then recreates the function.",
            "It fails unless the existing function is first dropped.",
        ],
        0,
        (
            "CREATE OR REPLACE FUNCTION updates an existing function in place when "
            "the name and argument types match, preserving grants and dependencies. "
            "It does not create a duplicate signature, and it cannot change the "
            "function's return type; that requires DROP and CREATE. It also does "
            "not drop dependent objects automatically."
        ),
        [PG_UDF],
        vi_prompt=(
            "CREATE OR REPLACE FUNCTION làm gì khi đã có hàm cùng tên và cùng kiểu "
            "tham số?"
        ),
        vi_options=[
            "Thay thế thân hàm và thuộc tính mà không xóa hàm, nhưng không thể đổi "
            "kiểu trả về.",
            "Tạo thêm một hàm quá tải thứ hai với cùng chữ ký.",
            "Xóa mọi đối tượng phụ thuộc rồi tạo lại hàm.",
            "Thất bại trừ khi xóa hàm hiện có trước.",
        ],
        vi_explanation=(
            "CREATE OR REPLACE FUNCTION cập nhật hàm hiện có tại chỗ khi tên và kiểu "
            "tham số khớp, giữ nguyên quyền và phụ thuộc. Nó không tạo chữ ký trùng "
            "và không thể đổi kiểu trả về; việc đó cần DROP rồi CREATE. Nó cũng "
            "không tự xóa các đối tượng phụ thuộc."
        ),
        tags=["postgresql", "server-programming", "functions"],
    ),
    mcq_vi(
        "spb-easy-raise-notice",
        ["PG-PLPGSQL"],
        2,
        "What does RAISE NOTICE do inside a PL/pgSQL function?",
        [
            "It sends a message to the client and server log at NOTICE level "
            "without aborting execution.",
            "It aborts the transaction with an error.",
            "It writes a row to a system table.",
            "It raises the statement's isolation level.",
        ],
        0,
        (
            "RAISE NOTICE reports a diagnostic message; depending on client and "
            "log settings it is shown to the client and written to the server log. "
            "It does not abort execution. RAISE EXCEPTION aborts the current "
            "transaction, and RAISE does not change isolation levels or write audit "
            "rows by itself."
        ),
        [PG_PLPGSQL],
        vi_prompt="RAISE NOTICE làm gì bên trong hàm PL/pgSQL?",
        vi_options=[
            "Gửi thông báo tới máy khách và log máy chủ ở mức NOTICE mà không hủy "
            "thực thi.",
            "Hủy giao dịch với lỗi.",
            "Ghi một dòng vào bảng hệ thống.",
            "Nâng mức cô lập của câu lệnh.",
        ],
        vi_explanation=(
            "RAISE NOTICE phát thông báo chẩn đoán; tùy cấu hình máy khách và log, "
            "nó hiển thị cho máy khách và ghi vào log máy chủ. Nó không hủy thực "
            "thi. RAISE EXCEPTION hủy giao dịch hiện tại, còn RAISE không đổi mức "
            "cô lập hay tự ghi dòng kiểm toán."
        ),
        tags=["postgresql", "server-programming", "plpgsql"],
    ),
    mcq_vi(
        "spb-easy-after-trigger",
        ["PG-TRIGGER"],
        2,
        "An AFTER UPDATE row trigger runs. What can it do with NEW?",
        [
            "It can read NEW and OLD to audit or react, but modifying NEW does not "
            "change the already-updated row.",
            "It can modify NEW to change the stored row before the update is applied.",
            "It cannot access NEW or OLD at all.",
            "It must return NULL to keep the update.",
        ],
        0,
        (
            "An AFTER trigger runs after the row change has been applied, so NEW and "
            "OLD are available for reading, but returning a modified NEW does not "
            "alter the stored row. To validate or modify the row before it is "
            "written, use a BEFORE trigger and return NEW. AFTER triggers are "
            "appropriate for auditing and cascading actions."
        ),
        [PG_TRIGGER],
        vi_prompt="Trigger AFTER UPDATE cấp dòng chạy. Nó có thể làm gì với NEW?",
        vi_options=[
            "Đọc NEW và OLD để kiểm toán hoặc phản ứng, nhưng sửa NEW không làm thay "
            "đổi dòng đã được cập nhật.",
            "Sửa NEW để thay đổi dòng được lưu trước khi cập nhật được áp dụng.",
            "Không thể truy cập NEW hoặc OLD.",
            "Phải trả NULL để giữ bản cập nhật.",
        ],
        vi_explanation=(
            "Trigger AFTER chạy sau khi thay đổi dòng đã được áp dụng, nên NEW và "
            "OLD có thể đọc, nhưng trả NEW đã sửa không làm thay đổi dòng được lưu. "
            "Để kiểm tra hoặc sửa dòng trước khi ghi, dùng trigger BEFORE và trả NEW. "
            "Trigger AFTER phù hợp cho kiểm toán và hành động dây chuyền."
        ),
        tags=["postgresql", "server-programming", "triggers"],
    ),
    mcq_vi(
        "spb-easy-return-next",
        ["PG-PLPGSQL"],
        2,
        "In a PL/pgSQL set-returning function, what does RETURN NEXT do?",
        [
            "It appends the current row to the function's result set and continues "
            "execution; RETURN ends the function.",
            "It exits the function immediately with the current row.",
            "It returns a single scalar value and ignores any further rows.",
            "It commits the current transaction and starts a new one.",
        ],
        0,
        (
            "RETURN NEXT adds the current values to the result set and lets the "
            "function continue, which is how a set-returning function can build "
            "multiple rows. A plain RETURN without an expression ends the function. "
            "RETURN NEXT does not commit transactions and is not limited to one "
            "scalar result."
        ),
        [PG_PLPGSQL],
        vi_prompt=(
            "Trong hàm trả về tập hợp của PL/pgSQL, RETURN NEXT làm gì?"
        ),
        vi_options=[
            "Thêm dòng hiện tại vào tập kết quả của hàm và tiếp tục thực thi; RETURN "
            "kết thúc hàm.",
            "Thoát hàm ngay với dòng hiện tại.",
            "Trả về một giá trị vô hướng và bỏ qua mọi dòng sau.",
            "Commit giao dịch hiện tại và bắt đầu giao dịch mới.",
        ],
        vi_explanation=(
            "RETURN NEXT thêm các giá trị hiện tại vào tập kết quả và cho hàm tiếp "
            "tục, nhờ đó hàm trả về tập hợp có thể tạo nhiều dòng. RETURN không kèm "
            "biểu thức kết thúc hàm. RETURN NEXT không commit giao dịch và không bị "
            "giới hạn ở một giá trị vô hướng."
        ),
        tags=["postgresql", "server-programming", "plpgsql"],
    ),
    # EASY: 3 essays (difficulty 2)
    essay_vi(
        "spb-easy-updated-at-trigger",
        ["PG-TRIGGER"],
        2,
        (
            "Design a trigger that maintains an updated_at column on UPDATE. State "
            "whether it should be BEFORE or AFTER, what it returns, how it accesses "
            "the row, and one risk for bulk loads or security."
        ),
        (
            "Use a BEFORE UPDATE FOR EACH ROW trigger. In the trigger function, "
            "assign NEW.updated_at = now() and RETURN NEW so the modified row is "
            "written. BEFORE is required because the change must happen before the "
            "row is stored; an AFTER trigger could only write a second UPDATE. "
            "NEW refers to the new row version and OLD to the previous one. Risks: "
            "the trigger fires for every row, so a bulk load can be much slower than "
            "a set-based update, and the function should have a safe search_path and "
            "not run as a careless SECURITY DEFINER routine. Consider whether the "
            "application can set the column itself before adding per-row overhead."
        ),
        (
            "The answer must choose BEFORE, return NEW and assign NEW.updated_at, "
            "then name a real operational risk."
        ),
        [
            "Chooses AFTER or returns NULL, or writes a separate UPDATE that recurses.",
            "Chooses BEFORE and assigns NEW but does not explain the return value or a risk.",
            "Explains BEFORE, NEW and RETURN NEW, but omits bulk-load or security risk.",
            "Explains BEFORE, NEW.updated_at and RETURN NEW, plus per-row bulk cost and a security or search_path consideration.",
        ],
        [PG_TRIGGER, PG_PLPGSQL],
        vi_prompt=(
            "Hãy thiết kế trigger duy trì cột updated_at khi UPDATE. Nêu nên dùng "
            "BEFORE hay AFTER, trả về gì, truy cập dòng thế nào, và một rủi ro khi "
            "nạp hàng loạt hoặc về bảo mật."
        ),
        vi_reference=(
            "Dùng trigger BEFORE UPDATE FOR EACH ROW. Trong hàm trigger, gán "
            "NEW.updated_at = now() và RETURN NEW để dòng đã sửa được ghi. Cần "
            "BEFORE vì thay đổi phải xảy ra trước khi dòng được lưu; trigger AFTER "
            "chỉ có thể ghi thêm một UPDATE thứ hai. NEW là phiên bản dòng mới, OLD "
            "là phiên bản trước. Rủi ro: trigger chạy cho từng dòng nên nạp hàng "
            "loạt có thể chậm hơn nhiều so với cập nhật theo tập hợp, và hàm nên có "
            "search_path an toàn, không chạy như SECURITY DEFINER cẩu thả. Cân nhắc "
            "xem ứng dụng có thể tự đặt cột trước khi thêm chi phí theo dòng."
        ),
        vi_explanation=(
            "Câu trả lời phải chọn BEFORE, trả NEW và gán NEW.updated_at, rồi nêu "
            "một rủi ro vận hành thực tế."
        ),
        vi_criteria=[
            "Chọn AFTER hoặc trả NULL, hoặc viết UPDATE riêng gây đệ quy.",
            "Chọn BEFORE và gán NEW nhưng không giải thích giá trị trả về hoặc rủi ro.",
            "Giải thích BEFORE, NEW và RETURN NEW, nhưng bỏ sót rủi ro nạp hàng loạt hoặc bảo mật.",
            "Giải thích BEFORE, NEW.updated_at và RETURN NEW, cùng chi phí theo dòng khi nạp hàng loạt và cân nhắc bảo mật hoặc search_path.",
        ],
        tags=["postgresql", "server-programming", "triggers"],
    ),
    essay_vi(
        "spb-easy-language-choice",
        ["PG-UDF", "PG-PLPGSQL"],
        2,
        (
            "Compare SQL-language functions, PL/pgSQL functions and an external "
            "language for implementing a business rule. Consider set-based work, "
            "control flow, performance and maintainability, and recommend a "
            "default."
        ),
        (
            "A SQL-language function is best when the logic can be expressed as a "
            "single query or a few statements; PostgreSQL may inline it into the "
            "calling query, which can improve performance, and it keeps the logic "
            "declarative. PL/pgSQL is appropriate for procedural control flow, "
            "loops, exception handling and multiple statements, but row-by-row "
            "loops are usually slower than set-based SQL and should be reserved "
            "for cases that need them. An external language can reuse libraries "
            "but adds deployment, trust and performance overhead and may require "
            "superuser installation. The practical default is set-based SQL, then "
            "PL/pgSQL for procedural needs, and an external language only with a "
            "clear justification."
        ),
        (
            "The answer must connect each option to a concrete strength and cost, "
            "and give a defensible default."
        ),
        [
            "Recommends PL/pgSQL for everything without discussing set-based SQL or costs.",
            "Compares two options but not all three, or gives no recommendation.",
            "Compares all three with strengths, but omits inlining, deployment or maintainability.",
            "Compares SQL, PL/pgSQL and external languages with set-based performance, control flow, deployment and maintainability, and recommends a default.",
        ],
        [PG_UDF, PG_PLPGSQL],
        vi_prompt=(
            "Hãy so sánh hàm ngôn ngữ SQL, hàm PL/pgSQL và ngôn ngữ bên ngoài để "
            "hiện thực một quy tắc nghiệp vụ. Xét công việc theo tập hợp, luồng điều "
            "khiển, hiệu năng và khả năng bảo trì, và đề xuất mặc định."
        ),
        vi_reference=(
            "Hàm ngôn ngữ SQL tốt nhất khi logic biểu diễn được bằng một truy vấn "
            "hoặc vài câu lệnh; PostgreSQL có thể nội tuyến nó vào truy vấn gọi, "
            "giúp hiệu năng và giữ logic khai báo. PL/pgSQL phù hợp cho luồng điều "
            "khiển thủ tục, vòng lặp, xử lý ngoại lệ và nhiều câu lệnh, nhưng vòng "
            "lặp từng dòng thường chậm hơn SQL theo tập hợp và nên dành cho trường "
            "hợp cần thiết. Ngôn ngữ bên ngoài có thể tái dùng thư viện nhưng thêm "
            "chi phí triển khai, tin cậy và hiệu năng, có thể cần superuser cài đặt. "
            "Mặc định thực tế là SQL theo tập hợp, rồi PL/pgSQL cho nhu cầu thủ tục, "
            "và ngôn ngữ ngoài chỉ khi có lý do rõ ràng."
        ),
        vi_explanation=(
            "Câu trả lời phải gắn mỗi lựa chọn với một điểm mạnh và chi phí cụ thể, "
            "đồng thời đưa ra mặc định có thể bảo vệ."
        ),
        vi_criteria=[
            "Khuyên dùng PL/pgSQL cho mọi thứ mà không bàn SQL theo tập hợp hay chi phí.",
            "So sánh hai lựa chọn nhưng không đủ ba, hoặc không đưa ra khuyến nghị.",
            "So sánh cả ba với điểm mạnh, nhưng bỏ sót nội tuyến, triển khai hoặc bảo trì.",
            "So sánh SQL, PL/pgSQL và ngôn ngữ ngoài về hiệu năng theo tập hợp, luồng điều khiển, triển khai và bảo trì, và đề xuất mặc định.",
        ],
        tags=["postgresql", "server-programming", "functions"],
    ),
    essay_vi(
        "spb-easy-raise-validation",
        ["PG-PLPGSQL"],
        2,
        (
            "Explain how to validate input inside a PL/pgSQL function: using "
            "constraints, explicit checks and RAISE, and when to catch an "
            "exception. What should the caller receive on invalid input?"
        ),
        (
            "Prefer declarative constraints when the rule belongs to the data: NOT "
            "NULL, CHECK, UNIQUE and foreign keys are enforced consistently for "
            "every writer. For procedural rules, test the values and use RAISE "
            "EXCEPTION with a clear message and, where appropriate, an ERRCODE so "
            "callers can distinguish error classes. Catch exceptions only when the "
            "function can recover or add context; catching and swallowing an error "
            "hides failures. On invalid input the caller should receive a failure, "
            "not a fabricated success value, and the transaction should not be left "
            "in a misleading state. Exception blocks create subtransactions, which "
            "have a cost, so do not wrap every statement."
        ),
        (
            "The answer must prefer constraints for data rules, show RAISE for "
            "procedural rules, and explain why errors must not be swallowed."
        ),
        [
            "Suggests catching every exception and returning a default value.",
            "Mentions RAISE or constraints but not both, or does not say what the caller receives.",
            "Explains constraints, explicit checks and RAISE, but omits exception cost or error codes.",
            "Prefers constraints, uses RAISE with message or ERRCODE, avoids swallowing errors, and notes subtransaction cost or caller signalling.",
        ],
        [PG_PLPGSQL, PG_UDF],
        vi_prompt=(
            "Hãy giải thích cách kiểm tra đầu vào trong hàm PL/pgSQL: dùng ràng buộc, "
            "kiểm tra tường minh và RAISE, và khi nào nên bắt ngoại lệ. Người gọi "
            "nên nhận gì khi đầu vào không hợp lệ?"
        ),
        vi_reference=(
            "Ưu tiên ràng buộc khai báo khi quy tắc thuộc về dữ liệu: NOT NULL, "
            "CHECK, UNIQUE và khóa ngoại được thực thi nhất quán cho mọi người ghi. "
            "Với quy tắc thủ tục, kiểm tra giá trị và dùng RAISE EXCEPTION với thông "
            "báo rõ ràng và, khi phù hợp, ERRCODE để người gọi phân biệt nhóm lỗi. "
            "Chỉ bắt ngoại lệ khi hàm có thể phục hồi hoặc thêm ngữ cảnh; bắt rồi bỏ "
            "qua lỗi sẽ che giấu hỏng hóc. Với đầu vào không hợp lệ, người gọi nên "
            "nhận thất bại, không phải giá trị thành công giả tạo, và giao dịch không "
            "bị để ở trạng thái gây hiểu nhầm. Khối ngoại lệ tạo giao dịch con có chi "
            "phí, nên đừng bọc mọi câu lệnh."
        ),
        vi_explanation=(
            "Câu trả lời phải ưu tiên ràng buộc cho quy tắc dữ liệu, dùng RAISE cho "
            "quy tắc thủ tục, và giải thích vì sao không được nuốt lỗi."
        ),
        vi_criteria=[
            "Đề xuất bắt mọi ngoại lệ và trả giá trị mặc định.",
            "Nêu RAISE hoặc ràng buộc nhưng không đủ cả hai, hoặc không nói người gọi nhận gì.",
            "Giải thích ràng buộc, kiểm tra tường minh và RAISE, nhưng bỏ sót chi phí ngoại lệ hoặc mã lỗi.",
            "Ưu tiên ràng buộc, dùng RAISE với thông báo hoặc ERRCODE, tránh nuốt lỗi, và nêu chi phí giao dịch con hoặc cách báo hiệu cho người gọi.",
        ],
        tags=["postgresql", "server-programming", "plpgsql"],
    ),
    # HARD: 2 MCQ (difficulty 4)
    mcq_vi(
        "spb-hard-trigger-recursion",
        ["PG-TRIGGER"],
        4,
        (
            "A trigger on table A updates table B, and a trigger on B updates A. "
            "What is the main control for preventing runaway recursion?"
        ),
        [
            "Guard the trigger with a condition or pg_trigger_depth(), and design "
            "the write path so the two triggers do not keep re-firing each other.",
            "Set the transaction to READ ONLY.",
            "Use a BEFORE trigger instead of AFTER; this always stops recursion.",
            "PostgreSQL automatically disables recursive triggers after one level.",
        ],
        0,
        (
            "PostgreSQL does not automatically stop a trigger from causing another "
            "trigger that eventually re-fires the first one. Use a WHEN condition, "
            "inspect pg_trigger_depth(), or restructure the logic so only one layer "
            "owns the relationship. A read-only transaction prevents writes but is "
            "not a general fix, and BEFORE versus AFTER does not by itself prevent "
            "recursion. Infinite recursion can consume resources or hit limits."
        ),
        [PG_FUNCTIONS_INFO, PG_PLPGSQL_TRIGGER],
        vi_prompt=(
            "Trigger trên bảng A cập nhật bảng B, và trigger trên B cập nhật A. "
            "Kiểm soát chính để ngăn đệ quy mất kiểm soát là gì?"
        ),
        vi_options=[
            "Bảo vệ trigger bằng điều kiện hoặc pg_trigger_depth(), và thiết kế "
            "đường ghi để hai trigger không liên tục kích hoạt lẫn nhau.",
            "Đặt giao dịch ở chế độ READ ONLY.",
            "Dùng trigger BEFORE thay vì AFTER; cách này luôn chặn đệ quy.",
            "PostgreSQL tự động vô hiệu hóa trigger đệ quy sau một mức.",
        ],
        vi_explanation=(
            "PostgreSQL không tự động ngăn trigger gây ra trigger khác rồi kích hoạt "
            "lại trigger đầu. Dùng điều kiện WHEN, kiểm tra pg_trigger_depth(), hoặc "
            "tái cấu trúc logic để chỉ một lớp chịu trách nhiệm quan hệ. Giao dịch "
            "chỉ đọc ngăn ghi nhưng không phải cách sửa chung, và BEFORE so với AFTER "
            "tự nó không ngăn đệ quy. Đệ quy vô hạn có thể tiêu tốn tài nguyên hoặc "
            "chạm giới hạn."
        ),
        tags=["postgresql", "server-programming", "triggers"],
    ),
    mcq_vi(
        "spb-hard-transition-tables",
        ["PG-TRIGGER"],
        4,
        "What do transition tables provide for statement-level triggers?",
        [
            "An AFTER statement trigger can query the complete set of old and new "
            "rows for the statement, enabling set-based processing.",
            "They allow a BEFORE row trigger to see rows from other concurrent "
            "transactions.",
            "They make every row trigger execute once per statement instead of per row.",
            "They store trigger output in a permanent table automatically.",
        ],
        0,
        (
            "Transition tables are declared with REFERENCING OLD TABLE AS ... and "
            "NEW TABLE AS ... on an AFTER statement-level trigger, and give the "
            "trigger a relation-like view of all rows affected by the statement. "
            "That supports set-based auditing or cascading work without a per-row "
            "trigger. They do not expose other transactions' rows, do not change a "
            "row trigger's timing, and do not persist results automatically."
        ),
        [PG_TRIGGER],
        vi_prompt=(
            "Transition table cung cấp gì cho trigger cấp câu lệnh?"
        ),
        vi_options=[
            "Trigger AFTER cấp câu lệnh có thể truy vấn toàn bộ tập dòng cũ và mới "
            "của câu lệnh, cho phép xử lý theo tập hợp.",
            "Chúng cho trigger BEFORE cấp dòng thấy dòng từ giao dịch đồng thời khác.",
            "Chúng làm mọi trigger cấp dòng chạy một lần mỗi câu lệnh thay vì mỗi dòng.",
            "Chúng tự động lưu kết quả trigger vào bảng vĩnh viễn.",
        ],
        vi_explanation=(
            "Transition table được khai báo bằng REFERENCING OLD TABLE AS ... và NEW "
            "TABLE AS ... trên trigger AFTER cấp câu lệnh, cho trigger một khung "
            "nhìn giống quan hệ trên toàn bộ dòng bị ảnh hưởng bởi câu lệnh. Điều "
            "này hỗ trợ kiểm toán hoặc hành động dây chuyền theo tập hợp mà không cần "
            "trigger từng dòng. Chúng không phơi bày dòng của giao dịch khác, không "
            "đổi thời điểm trigger cấp dòng và không tự lưu kết quả."
        ),
        tags=["postgresql", "server-programming", "triggers"],
    ),
    # HARD: 2 essays (difficulty 4)
    essay_vi(
        "spb-hard-audit-trail",
        ["PG-TRIGGER", "PG-PLPGSQL"],
        4,
        (
            "Design an audit trail for changes to a business table. Cover trigger "
            "timing and granularity, old and new row capture, transaction identity, "
            "bulk operations, recursion, failure semantics and permissions. What "
            "would you sacrifice to keep the audit reliable?"
        ),
        (
            "A row-level AFTER INSERT OR UPDATE OR DELETE trigger can write one "
            "audit row per change with operation, table, key, OLD and NEW as JSONB, "
            "current_user, transaction ID and timestamp. AFTER is appropriate "
            "because the change has succeeded and the trigger return value is "
            "ignored. For bulk operations, a per-row trigger can be expensive; a "
            "statement-level AFTER trigger with transition tables can process the "
            "whole set, or the loader can write an audit summary. Prevent recursion "
            "by ensuring the audit table has no trigger that writes back to the "
            "business table and by guarding with WHEN or pg_trigger_depth(). Decide "
            "failure semantics: if the audit insert fails, should the business "
            "change fail too? For high-assurance auditing, let it fail the "
            "transaction rather than silently lose the record. The audit writer "
            "needs INSERT on the audit table but the application should not be able "
            "to update or delete audit rows; use a dedicated role, revoke UPDATE and "
            "DELETE, and consider partitioning and retention. The cost is extra "
            "write amplification and latency, which is the price of a trustworthy "
            "trail."
        ),
        (
            "The answer must choose a concrete trigger design, handle bulk and "
            "recursion, and make an explicit reliability trade-off."
        ),
        [
            "Suggests logging from application code only, with no database enforcement or failure semantics.",
            "Designs a row trigger but ignores bulk operations, recursion or permissions.",
            "Covers trigger and audit fields plus some reliability concerns, but leaves failure semantics or retention vague.",
            "Designs row and statement-level paths, handles bulk and recursion, locks down audit permissions, and explicitly chooses fail-the-transaction for reliability with its cost.",
        ],
        [PG_TRIGGER, PG_PLPGSQL],
        vi_prompt=(
            "Hãy thiết kế nhật ký kiểm toán cho các thay đổi trên một bảng nghiệp "
            "vụ. Bao gồm thời điểm và mức chi tiết của trigger, ghi nhận dòng cũ và "
            "mới, định danh giao dịch, thao tác hàng loạt, đệ quy, ngữ nghĩa khi lỗi "
            "và quyền. Bạn sẽ đánh đổi gì để nhật ký đáng tin cậy?"
        ),
        vi_reference=(
            "Trigger AFTER INSERT OR UPDATE OR DELETE cấp dòng có thể ghi một dòng "
            "kiểm toán cho mỗi thay đổi với thao tác, bảng, khóa, OLD và NEW dạng "
            "JSONB, current_user, transaction ID và thời điểm. AFTER phù hợp vì thay "
            "đổi đã thành công và giá trị trả về của trigger bị bỏ qua. Với thao tác "
            "hàng loạt, trigger từng dòng có thể tốn kém; trigger AFTER cấp câu lệnh "
            "với transition table có thể xử lý cả tập, hoặc bộ nạp ghi bản tóm tắt "
            "kiểm toán. Ngăn đệ quy bằng cách bảo đảm bảng kiểm toán không có trigger "
            "ghi ngược lại bảng nghiệp vụ và dùng điều kiện WHEN hoặc "
            "pg_trigger_depth(). Quyết định ngữ nghĩa lỗi: nếu ghi kiểm toán thất "
            "bại, thay đổi nghiệp vụ có nên thất bại theo? Với kiểm toán độ tin cậy "
            "cao, hãy để giao dịch thất bại thay vì âm thầm mất bản ghi. Bộ ghi kiểm "
            "toán cần INSERT trên bảng kiểm toán nhưng ứng dụng không được sửa hoặc "
            "xóa dòng kiểm toán; dùng role chuyên dụng, thu hồi UPDATE và DELETE, cân "
            "nhắc phân vùng và lưu trữ. Cái giá là gia tăng ghi và độ trễ, đổi lấy "
            "nhật ký đáng tin cậy."
        ),
        vi_explanation=(
            "Câu trả lời phải chọn thiết kế trigger cụ thể, xử lý hàng loạt và đệ "
            "quy, và nêu đánh đổi độ tin cậy rõ ràng."
        ),
        vi_criteria=[
            "Chỉ đề xuất ghi log từ mã ứng dụng, không có thực thi trong cơ sở dữ liệu hoặc ngữ nghĩa lỗi.",
            "Thiết kế trigger cấp dòng nhưng bỏ qua thao tác hàng loạt, đệ quy hoặc quyền.",
            "Bao quát trigger và trường kiểm toán cùng một số lo ngại độ tin cậy, nhưng ngữ nghĩa lỗi hoặc lưu trữ còn mơ hồ.",
            "Thiết kế cả đường cấp dòng và cấp câu lệnh, xử lý hàng loạt và đệ quy, siết quyền kiểm toán, và chọn rõ ràng để giao dịch thất bại khi kiểm toán lỗi cùng cái giá của nó.",
        ],
        tags=["postgresql", "server-programming", "audit"],
    ),
    essay_vi(
        "spb-hard-bulk-load-triggers",
        ["PG-TRIGGER", "PG-PLPGSQL"],
        4,
        (
            "A nightly load inserts millions of rows into a table that has row-level "
            "triggers. Explain why this is slow, how statement-level triggers with "
            "transition tables or a staging table can help, and what risks come with "
            "disabling triggers."
        ),
        (
            "Row-level triggers execute the trigger function once per inserted row, "
            "so millions of rows mean millions of function calls and possibly many "
            "extra statements or index writes. A statement-level trigger with "
            "transition tables runs once and can process the affected rows "
            "set-based, which is usually much faster. A staging table can accept "
            "the raw load and then apply one set-based INSERT or MERGE, with "
            "validation and auditing performed in bulk. Disabling triggers with "
            "ALTER TABLE ... DISABLE TRIGGER can speed the load, but it requires "
            "ownership or superuser, skips integrity and audit logic, and risks "
            "inconsistent data; it should be a controlled, short operation with a "
            "re-enable and verification step. Always measure before and after, "
            "because the trigger body itself may be doing per-row queries that can "
            "be rewritten set-based."
        ),
        (
            "The answer must explain per-row cost, offer a set-based alternative, "
            "and state the integrity and privilege risks of disabling triggers."
        ),
        [
            "Suggests disabling all triggers permanently or removing them without discussing integrity.",
            "Explains per-row cost but offers no set-based alternative or risk.",
            "Explains transition tables or staging and some risk, but does not cover privileges or verification.",
            "Explains per-row cost, set-based transition-table or staging design, and the ownership, integrity and verification risks of disabling triggers.",
        ],
        [PG_PLPGSQL_TRIGGER, PG_ALTER],
        vi_prompt=(
            "Một lần nạp hàng đêm chèn hàng triệu dòng vào bảng có trigger cấp dòng. "
            "Hãy giải thích vì sao chậm, trigger cấp câu lệnh với transition table "
            "hoặc bảng tạm giúp thế nào, và rủi ro nào đi kèm việc vô hiệu hóa "
            "trigger."
        ),
        vi_reference=(
            "Trigger cấp dòng thực thi hàm trigger một lần cho mỗi dòng chèn, nên "
            "hàng triệu dòng nghĩa là hàng triệu lần gọi hàm và có thể nhiều câu lệnh "
            "hoặc lần ghi chỉ mục thêm. Trigger cấp câu lệnh với transition table "
            "chạy một lần và có thể xử lý các dòng bị ảnh hưởng theo tập hợp, thường "
            "nhanh hơn nhiều. Bảng tạm có thể nhận dữ liệu thô rồi áp một INSERT hoặc "
            "MERGE theo tập hợp, với kiểm tra và kiểm toán thực hiện hàng loạt. Vô "
            "hiệu hóa trigger bằng ALTER TABLE ... DISABLE TRIGGER có thể tăng tốc "
            "nạp, nhưng cần quyền sở hữu hoặc superuser, bỏ qua logic toàn vẹn và "
            "kiểm toán, và có nguy cơ dữ liệu không nhất quán; đây nên là thao tác có "
            "kiểm soát, ngắn, kèm bước bật lại và xác minh. Luôn đo trước và sau, vì "
            "thân trigger có thể đang chạy truy vấn từng dòng mà có thể viết lại theo "
            "tập hợp."
        ),
        vi_explanation=(
            "Câu trả lời phải giải thích chi phí từng dòng, đưa ra giải pháp theo tập "
            "hợp, và nêu rủi ro toàn vẹn cùng quyền khi vô hiệu hóa trigger."
        ),
        vi_criteria=[
            "Đề xuất vô hiệu hóa mọi trigger vĩnh viễn hoặc xóa chúng mà không bàn toàn vẹn.",
            "Giải thích chi phí từng dòng nhưng không có giải pháp theo tập hợp hoặc rủi ro.",
            "Giải thích transition table hoặc bảng tạm và một số rủi ro, nhưng không bao quát quyền hoặc xác minh.",
            "Giải thích chi phí từng dòng, thiết kế theo tập hợp bằng transition table hoặc bảng tạm, và rủi ro quyền sở hữu, toàn vẹn và xác minh khi vô hiệu hóa trigger.",
        ],
        tags=["postgresql", "server-programming", "triggers"],
    ),
]

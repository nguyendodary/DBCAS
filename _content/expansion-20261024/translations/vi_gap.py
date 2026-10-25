"""Vietnamese drafts for the blueprint-gap specs (a2perf, adm, perf, sec, sp)."""

DRAFTS = {
    "a2-easy-index-tradeoff": {
        "prompt": "Một chỉ mục B-tree được thêm trên một cột thường xuyên được lọc. Phát biểu nào mô tả đúng nhất hiệu ứng?",
        "explanation": "Chỉ mục là một sự đánh đổi: nó có thể làm các phép đọc chọn lọc rẻ hơn nhưng tiêu tốn dung lượng và phải được duy trì khi ghi, nên các thay đổi hàng loạt có thể chậm đi. Bộ lập kế hoạch so sánh chi phí và có thể bỏ qua chỉ mục, ví dụ khi phần lớn dòng khớp hoặc bảng nhỏ. Chỉ chỉ mục UNIQUE hoặc ràng buộc mới thực thi tính duy nhất.",
        "option_texts": {
            "A": "Mọi truy vấn trên bảng trở nên nhanh hơn vì bộ lập kế hoạch buộc phải dùng chỉ mục mới nhất.",
            "B": "Việc tra cứu các dòng khớp có thể nhanh hơn, nhưng chỉ mục tốn lưu trữ và thêm việc cho INSERT, UPDATE và DELETE, và bộ lập kế hoạch vẫn có thể chọn quét tuần tự.",
            "C": "Thao tác ghi trở nên nhanh hơn vì chỉ mục tổ chức các dòng mới trước khi chúng được lưu.",
            "D": "Chỉ mục cũng bảo đảm cột là duy nhất.",
        },
        "rubrics": {},
    },
    "a2-easy-composite-leftmost": {
        "prompt": "Một chỉ mục B-tree phức hợp được tạo trên (customer_id, created_on). Vị từ nào có thể dùng nó một cách hiệu quả?",
        "explanation": "Một B-tree trên (customer_id, created_on) được sắp theo customer_id trước, rồi created_on trong từng khách hàng. Nó có thể được dùng khi customer_id được ràng buộc, tùy chọn cùng một khoảng trên created_on. Vị từ chỉ trên created_on không thể dùng chỉ mục hiệu quả vì cột dẫn đầu không được ràng buộc. Đẳng thức trên cả hai cột hoạt động, nhưng khoảng trên cột cuối cũng được hỗ trợ.",
        "option_texts": {
            "A": "Bất kỳ bộ lọc trên bất kỳ cột nào của bảng, vì chỉ mục bao phủ toàn bộ dòng.",
            "B": "Bộ lọc chỉ trên created_on, vì nó là một phần của chỉ mục.",
            "C": "Bộ lọc trên customer_id, hoặc trên customer_id cùng với một khoảng trên created_on, vì cột dẫn đầu được ràng buộc.",
            "D": "Chỉ bộ lọc ràng buộc cả hai cột bằng đẳng thức; một khoảng trên created_on làm chỉ mục không dùng được.",
        },
        "rubrics": {},
    },
    "a2-easy-index-write-cost": {
        "prompt": "Vì sao thêm nhiều chỉ mục vào một bảng làm chậm các câu lệnh INSERT, UPDATE và DELETE?",
        "explanation": "Mỗi chỉ mục là một cấu trúc dữ liệu riêng có khóa trên các cột của nó. Một lệnh chèn hoặc thay đổi trên cột được đánh chỉ mục đòi hỏi một mục trong mọi chỉ mục bị ảnh hưởng, làm tăng công việc I/O và CPU. Người ghi không bị tuần tự hóa bởi khóa toàn bảng, chỉ mục được cập nhật tăng dần thay vì xây lại, và chỉ mục lưu khóa cùng tham chiếu dòng, không phải bản sao của bảng.",
        "option_texts": {
            "A": "PostgreSQL ghi lại mọi chỉ mục từ đầu sau mỗi lần ghi.",
            "B": "Các chỉ mục khóa toàn bộ bảng trong mỗi lần ghi, nên chỉ một người ghi có thể tiến hành tại một thời điểm.",
            "C": "Mọi chỉ mục bị ảnh hưởng phải được cập nhật để phản ánh các dòng đã thay đổi, nên càng nhiều chỉ mục càng nhiều việc bảo trì cho mỗi lần ghi.",
            "D": "Chỉ mục sao chép toàn bộ bảng, nên mỗi lần ghi bị nhân bản một lần cho mỗi chỉ mục.",
        },
        "rubrics": {},
    },
    "a2-medium-expression-index": {
        "prompt": "Các truy vấn chạy WHERE lower(email) = 'a@example.com' trên một bảng lớn có chỉ mục B-tree thường trên email. Vì sao chỉ mục không được dùng, và điều gì giúp ích?",
        "explanation": "Một chỉ mục thường trên email lưu các giá trị email, trong khi vị từ so sánh lower(email). Bộ lập kế hoạch sẽ cần một chỉ mục có khóa là cùng biểu thức đó, được tạo bằng CREATE INDEX ... ON t (lower(email)). PostgreSQL hỗ trợ chỉ mục biểu thức, và hàm được dùng phải bất biến. Tính cho phép NULL và hỗ trợ văn bản của B-tree không phải lý do.",
        "option_texts": {
            "A": "Không gì giúp được: PostgreSQL không thể đánh chỉ mục kết quả của bất kỳ hàm nào.",
            "B": "Chỉ mục không được dùng vì chỉ mục B-tree không bao giờ hỗ trợ văn bản; chỉ chỉ mục hash mới hỗ trợ.",
            "C": "Chỉ mục chỉ bị bỏ qua khi email cho phép NULL; thêm NOT NULL làm lower(email) dùng chỉ mục thường.",
            "D": "Biểu thức lower(email) không phải giá trị được đánh chỉ mục, nên cần một chỉ mục biểu thức trên lower(email) để khớp vị từ.",
        },
        "rubrics": {},
    },
    "a2-medium-partial-index": {
        "prompt": "Một cột status có giá trị 'pending' cho khoảng 1% số dòng, và gần như mọi truy vấn lọc status = 'pending'. Chỉ mục nào phù hợp nhất?",
        "explanation": "Chỉ mục bộ phận được định nghĩa với một vị từ WHERE; nó chỉ chứa các dòng thỏa vị từ đó, nên nhỏ hơn nhiều so với chỉ mục đầy đủ và chỉ được bảo trì cho các dòng khớp. Truy vấn phải bao gồm một vị từ hàm ý vị từ của chỉ mục để dùng nó. Lực lượng thấp tự nó không ngăn việc đánh chỉ mục, và bộ lọc có độ chọn lọc cao chính là nơi chỉ mục có thể giúp.",
        "option_texts": {
            "A": "Không có chỉ mục nào, vì bộ lọc khớp 1% số dòng luôn dùng quét tuần tự.",
            "B": "Một chỉ mục B-tree đầy đủ trên status, vì chỉ mục bộ phận không dùng được cho bộ lọc đẳng thức.",
            "C": "Một chỉ mục trên mọi cột khác, vì status có lực lượng thấp và không thể đánh chỉ mục.",
            "D": "Một chỉ mục bộ phận với WHERE status = 'pending', chỉ lưu các dòng khớp và chỉ được bảo trì khi vị từ đúng.",
        },
        "rubrics": {},
    },
    "adm-easy-wal-purpose": {
        "prompt": "Vì sao PostgreSQL ghi các thay đổi vào write-ahead log (WAL)?",
        "explanation": "WAL là cơ chế phục hồi sau sự cố: các bản ghi thay đổi được ghi và đẩy xuống đĩa trước khi các trang dữ liệu bị sửa tới đĩa, nên sau sự cố máy chủ có thể phát lại các thay đổi đã xác nhận. Nó tồn tại độc lập với sao chép, dù sao chép dùng lại cùng dòng dữ liệu. Nó không phải bộ đệm kế hoạch và không phải bộ đệm dòng.",
        "option_texts": {
            "A": "Các bản ghi WAL được đẩy xuống đĩa trước các trang dữ liệu tương ứng, nên các thay đổi đã xác nhận có thể được làm lại sau sự cố.",
            "B": "WAL lưu một bản sao của mọi kế hoạch truy vấn để các truy vấn thường dùng bỏ qua bước lập kế hoạch.",
            "C": "WAL chỉ cần khi bật sao chép luồng; một máy chủ đơn lẻ không dùng nó.",
            "D": "WAL giữ các dòng gần đây trong bộ nhớ để các câu lệnh SELECT tránh đọc các trang bảng.",
        },
        "rubrics": {},
    },
    "adm-easy-streaming-standby": {
        "prompt": "Trong sao chép luồng, một máy chủ hot standby nhận gì từ máy chủ chính và có thể làm gì?",
        "explanation": "Sao chép luồng gửi các bản ghi WAL từ máy chính tới standby, và standby liên tục áp dụng chúng. Hot standby chấp nhận truy vấn chỉ đọc, và vì việc áp dụng có thể chạy sau máy chính, việc đọc trên bản sao có thể hơi cũ. Không có việc truyền dòng qua bộ nhớ chia sẻ và không có bản kết xuất logic theo checkpoint.",
        "option_texts": {
            "A": "Nó nhận văn bản SQL của các câu lệnh SELECT và trả kết quả về máy chính.",
            "B": "Nó chỉ nhận một bản kết xuất logic đầy đủ của từng bảng ở mỗi checkpoint và không thể phục vụ truy vấn.",
            "C": "Nó liên tục nhận các bản ghi WAL và áp dụng chúng, và có thể phục vụ truy vấn chỉ đọc trong khi có thể bị trễ so với máy chính.",
            "D": "Nó nhận trực tiếp các phiên bản dòng đã xác nhận qua bộ nhớ chia sẻ và luôn chính xác tức thời.",
        },
        "rubrics": {},
    },
    "adm-hard-alter-system": {
        "prompt": "ALTER SYSTEM SET work_mem = '16MB'; làm gì?",
        "explanation": "ALTER SYSTEM lưu ghi đè trong postgresql.auto.conf, được đọc bổ sung cho postgresql.conf. Việc máy chủ đang chạy nhận giá trị sau khi nạp lại hay cần khởi động lại phụ thuộc ngữ cảnh của tham số; work_mem là tham số ngữ cảnh người dùng, nên chỉ cần nạp lại (các phiên nhận giá trị mới trước lệnh kế tiếp), trong khi các tham số ngữ cảnh postmaster cần khởi động lại. Thay đổi ở mức phiên sẽ là SET, không phải ALTER SYSTEM, và cụm không bao giờ bị tạo lại.",
        "option_texts": {
            "A": "Nó chỉ thay đổi phiên hiện tại và biến mất khi phiên kết thúc.",
            "B": "Nó sửa postgresql.conf tại chỗ và áp dụng giá trị cho mọi phiên đang chạy ngay lập tức.",
            "C": "Nó ghi thiết lập vào postgresql.auto.conf; giá trị mới có hiệu lực theo ngữ cảnh của tham số, có thể cần nạp lại hoặc khởi động lại.",
            "D": "Nó tạo lại cụm để giá trị mới trở thành mặc định biên dịch.",
        },
        "rubrics": {},
    },
    "adm-hard-pg-stat-activity": {
        "prompt": "Phát biểu nào về view pg_stat_activity là đúng?",
        "explanation": "pg_stat_activity là một view trực tiếp, một dòng cho mỗi backend: nó báo trạng thái, sự kiện chờ và truy vấn hiện tại của mỗi tiến trình máy chủ. Nó không mang tính lịch sử; lịch sử câu lệnh cần một phần mở rộng như pg_stat_statements. Vì quyền riêng tư, người dùng không phải siêu người dùng thấy thông tin hạn chế về các phiên của người khác trừ khi có pg_read_all_stats. Các backend máy khách và worker autovacuum đều xuất hiện trong cùng view.",
        "option_texts": {
            "A": "Nó có một dòng cho mỗi tiến trình máy chủ với trạng thái và truy vấn hiện tại; một vai trò thông thường thường chỉ thấy văn bản truy vấn của các phiên khác khi được cấp pg_read_all_stats hoặc quyền tương đương.",
            "B": "Nó lưu lịch sử vĩnh viễn của mọi câu lệnh từng được thực thi trên máy chủ.",
            "C": "Nó chỉ báo số dòng trong mỗi bảng người dùng và không có gì về các phiên.",
            "D": "Nó chỉ hiển thị các worker autovacuum, vì các backend máy khách được liệt kê trong một view riêng theo cơ sở dữ liệu.",
        },
        "rubrics": {},
    },
    "perf-easy-default-index-type": {
        "prompt": "Phát biểu nào đối chiếu đúng kiểu chỉ mục mặc định của PostgreSQL với kiểu hash?",
        "explanation": "CREATE INDEX không nêu kiểu sẽ tạo B-tree, phục vụ các so sánh đẳng thức, khoảng và kiểu ORDER BY. Chỉ mục hash chỉ hỗ trợ đẳng thức. GIN chuyên cho các giá trị phức hợp như mảng, jsonb và lexeme toàn văn, không phải mặc định cho cột vô hướng. Hỗ trợ toán tử khác nhau, không chỉ kích thước.",
        "option_texts": {
            "A": "B-tree và hash hỗ trợ chính xác các toán tử giống nhau, nên lựa chọn chỉ ảnh hưởng kích thước chỉ mục.",
            "B": "Hash là mặc định và hỗ trợ truy vấn khoảng, trong khi B-tree chỉ hỗ trợ đẳng thức.",
            "C": "GIN là mặc định cho mọi cột vô hướng, trong khi B-tree chỉ dùng cho tìm kiếm toàn văn.",
            "D": "B-tree là mặc định và hỗ trợ các phép đẳng thức, khoảng và sắp xếp, trong khi hash chỉ hỗ trợ so sánh đẳng thức.",
        },
        "rubrics": {},
    },
    "perf-easy-planner-statistics": {
        "prompt": "Các thống kê bảng do ANALYZE thu thập được dùng để làm gì?",
        "explanation": "ANALYZE lấy mẫu nội dung bảng và lưu các phân bố như giá trị phổ biến nhất và biểu đồ tần suất. Bộ lập kế hoạch dùng chúng để ước lượng một điều kiện sẽ khớp bao nhiêu dòng và so sánh chi phí kế hoạch. Nếu thống kê cũ, ước lượng có thể sai nghiêm trọng và một kế hoạch kém có thể được chọn, đó là lý do autovacuum và ANALYZE thủ công quan trọng. Ràng buộc và kết quả truy vấn không liên quan.",
        "option_texts": {
            "A": "Chúng cho phép bộ lập kế hoạch ước lượng số dòng và độ chọn lọc để chọn giữa các kế hoạch như quét tuần tự và quét chỉ mục.",
            "B": "Chúng thực thi các quy tắc duy nhất và khóa ngoại tại thời điểm chèn.",
            "C": "Chúng lưu đệm kết quả của các truy vấn gần đây để các SELECT lặp lại bỏ qua việc thực thi.",
            "D": "Chúng ghi lại dung lượng đĩa mỗi chỉ mục sử dụng chỉ để báo cáo.",
        },
        "rubrics": {},
    },
    "sec-easy-rls-basics": {
        "prompt": "Một bảng được bật bảo mật cấp dòng mà không có chính sách nào được định nghĩa. Điều gì xảy ra khi một người dùng thông thường chọn từ nó?",
        "explanation": "Bảo mật cấp dòng là từ chối theo mặc định: khi đã đặt ENABLE ROW LEVEL SECURITY và không chính sách nào cấp quyền, người dùng thông thường không thấy dòng nào. Quyền truy cập được cấp bởi các biểu thức CREATE POLICY. Chủ sở hữu bảng bỏ qua bảo mật cấp dòng trừ khi đặt FORCE ROW LEVEL SECURITY, nhưng người dùng thông thường bị lọc. Không có lỗi cú pháp và không có lấy mẫu ngầm.",
        "option_texts": {
            "A": "Câu lệnh thất bại với lỗi cú pháp cho tới khi một chính sách được tạo.",
            "B": "Người dùng thấy mọi dòng, vì bảo mật cấp dòng chỉ lọc sau khi một chính sách được thêm.",
            "C": "Người dùng không thấy dòng nào, vì bật bảo mật cấp dòng mà không có chính sách sẽ từ chối truy cập theo mặc định.",
            "D": "Người dùng thấy mỗi dòng thứ ba, vì PostgreSQL áp dụng một chính sách lấy mẫu mặc định.",
        },
        "rubrics": {},
    },
    "sp-easy-procedure-basics": {
        "prompt": "Một procedure PostgreSQL được tạo bằng CREATE PROCEDURE được gọi như thế nào, và nó khác hàm thường ra sao?",
        "explanation": "Procedure được gọi bằng câu lệnh CALL và được thiết kế cho công việc thủ tục có thể bao gồm điều khiển giao dịch. Hàm trả về một giá trị, có thể được dùng bên trong biểu thức SQL, và không thể commit hay rollback. Procedure nhận tham số, và bộ lập kế hoạch không bao giờ gọi chúng một cách ngầm.",
        "option_texts": {
            "A": "Nó được gọi bằng CALL và có thể thực thi các câu lệnh điều khiển giao dịch, trong khi hàm được dùng trong biểu thức và không thể commit hay rollback.",
            "B": "Nó được gọi bằng SELECT và phải trả về một bảng, trong khi hàm không thể trả về dòng.",
            "C": "Nó được gọi bằng CALL nhưng không thể nhận tham số, trong khi hàm có thể nhận tham số.",
            "D": "Nó được bộ lập kế hoạch gọi tự động bất cứ khi nào tên của nó xuất hiện trong truy vấn.",
        },
        "rubrics": {},
    },
    "sp-hard-call-transaction-control": {
        "prompt": "Một procedure chứa câu lệnh COMMIT. Nó có thể thực thi COMMIT đó dưới điều kiện nào?",
        "explanation": "Tài liệu CALL nêu rằng nếu CALL được thực thi trong một khối giao dịch, procedure được gọi không thể thực thi câu lệnh điều khiển giao dịch; chúng chỉ được phép khi CALL chạy trong giao dịch riêng. Procedure có hỗ trợ COMMIT và ROLLBACK, đó là khác biệt then chốt so với hàm, nhưng một khối giao dịch tường minh bao ngoài gỡ bỏ khả năng đó.",
        "option_texts": {
            "A": "Chỉ khi procedure được tạo bằng CREATE FUNCTION thay vì CREATE PROCEDURE.",
            "B": "Luôn luôn, vì procedure được phép commit kể cả bên trong một khối giao dịch tường minh.",
            "C": "Chỉ khi CALL chạy trong giao dịch riêng của nó, không phải khi CALL được thực thi bên trong một khối giao dịch tường minh.",
            "D": "Không bao giờ, vì procedure SQL hoàn toàn không thể chứa câu lệnh điều khiển giao dịch.",
        },
        "rubrics": {},
    },
}

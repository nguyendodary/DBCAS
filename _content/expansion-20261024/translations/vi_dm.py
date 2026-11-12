"""Vietnamese drafts for the data-modification specs (dm_easy, dm_hard, dm_medium)."""

DRAFTS = {
    "dm-easy-default-values": {
        "prompt": "Bảng session_log(session_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, started_at TEXT NOT NULL DEFAULT 'unknown', note TEXT) đang rỗng. Câu lệnh INSERT INTO session_log DEFAULT VALUES; được thực thi. Điều gì được lưu?",
        "explanation": "DEFAULT VALUES chèn một dòng trong đó mọi cột nhận giá trị mặc định của nó. Cột identity sinh một giá trị, started_at nhận giá trị mặc định đã khai báo, còn note không có mặc định và cho phép NULL nên trở thành NULL. Câu lệnh hợp lệ khi mọi cột NOT NULL đều có thể được thỏa bởi mặc định hoặc identity.",
        "option_texts": {
            "A": "Không có dòng nào, vì DEFAULT VALUES yêu cầu ít nhất một giá trị cột tường minh.",
            "B": "Một dòng với session_id được sinh, started_at = 'unknown' và note = NULL.",
            "C": "Một dòng với mọi cột đều là NULL.",
            "D": "Lỗi, vì không thể kết hợp cột identity với DEFAULT VALUES.",
        },
        "rubrics": {},
    },
    "dm-easy-insert-select": {
        "prompt": "Câu lệnh INSERT INTO archive (sale_id, amount) SELECT sale_id, amount FROM sale WHERE status = 'closed'; được thực thi. Những dòng nào được thêm vào archive?",
        "explanation": "INSERT ... SELECT chèn một dòng cho mỗi dòng mà SELECT trả về, nên mệnh đề WHERE quyết định những lượt bán nào được lưu trữ. Bảng nguồn có thể không rỗng và bảng đích có thể đã có dòng; không có gì ngăn việc thêm vào.",
        "option_texts": {
            "A": "Một dòng archive cho mỗi dòng sale có status là 'closed'.",
            "B": "Một dòng archive cho mỗi cột của sale, vì SELECT được đánh giá theo từng cột.",
            "C": "Tất cả các dòng sale bất kể status, vì INSERT sao chép toàn bộ bảng nguồn.",
            "D": "Không dòng nào trừ khi archive rỗng, vì INSERT từ chối thêm vào bảng không rỗng.",
        },
        "rubrics": {},
    },
    "dm-easy-update-null-flag": {
        "prompt": "Bảng account có cột verified BOOLEAN cho phép NULL. Câu lệnh UPDATE account SET verified = FALSE WHERE verified IS NULL; được thực thi hai lần liên tiếp. Hiệu ứng là gì?",
        "explanation": "Mệnh đề WHERE chỉ chọn các dòng có giá trị là NULL, nên lần chạy đầu đặt chúng thành FALSE. Sau đó không dòng nào thỏa vị từ, nên lần chạy thứ hai cập nhật 0 dòng. UPDATE không bao giờ ghi lại các dòng không thỏa WHERE.",
        "option_texts": {
            "A": "Mỗi lần chạy thay đổi mọi dòng, vì UPDATE luôn ghi lại toàn bộ bảng.",
            "B": "Lần chạy đầu thay đổi các dòng có verified là NULL; lần chạy thứ hai không thay đổi dòng nào.",
            "C": "Lần chạy thứ hai khôi phục các giá trị NULL, vì WHERE được đánh giá lại trên ảnh chụp ban đầu.",
            "D": "Câu lệnh thất bại lần thứ hai vì FALSE không phải giá trị boolean hợp lệ.",
        },
        "rubrics": {},
    },
    "dm-easy-insert-returning": {
        "prompt": "Bảng task(task_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, title TEXT) được dùng với INSERT INTO task (title) VALUES ('write report') RETURNING task_id; Câu lệnh trả về gì?",
        "explanation": "RETURNING có trên INSERT cũng như UPDATE và DELETE và báo các giá trị từ những dòng mà câu lệnh đã tác động. Ở đây nó trả về giá trị identity được sinh cho dòng mới, nên ứng dụng khách biết khóa mà không cần truy vấn thứ hai.",
        "option_texts": {
            "A": "Mọi task_id hiện có trong bảng.",
            "B": "Kết quả rỗng, vì RETURNING chỉ áp dụng cho UPDATE và DELETE.",
            "C": "Một dòng chứa task_id được sinh của dòng vừa chèn.",
            "D": "Chuỗi 'write report' thay vì một số.",
        },
        "rubrics": {},
    },
    "dm-easy-merge-purpose": {
        "prompt": "MERGE được dùng để làm gì?",
        "explanation": "MERGE so sánh các dòng nguồn với các dòng đích bằng điều kiện ON và chạy hành động của mệnh đề WHEN khớp đầu tiên, nên một câu lệnh có thể cập nhật các dòng khớp, chèn các dòng nguồn không khớp và, trong PostgreSQL 17, xóa các dòng đích không khớp nguồn. Nó không phải lệnh lưu trữ hay phép toán tập hợp.",
        "option_texts": {
            "A": "Kết hợp hai tập kết quả thành một đầu ra, như UNION.",
            "B": "Gộp hai bảng thành một tệp vật lý duy nhất trên đĩa.",
            "C": "Nối các cột văn bản của hai bảng.",
            "D": "Áp dụng các hành động chèn, cập nhật hoặc xóa có điều kiện lên bảng đích từ các dòng của bảng nguồn trong một câu lệnh.",
        },
        "rubrics": {},
    },
    "dm-easy-multi-row-atomicity": {
        "prompt": "INSERT INTO tag (tag_id, label) VALUES (1, 'a'), (1, 'b'); được chạy trên tag(tag_id INT PRIMARY KEY, label TEXT), và chưa có dòng nào với tag_id = 1. Kết quả là gì?",
        "explanation": "Một câu lệnh INSERT là nguyên tử: khóa chính được kiểm tra cho từng dòng đề xuất, và vi phạm hủy bỏ câu lệnh, nên dòng đầu cũng không được giữ. Việc tiếp tục theo từng dòng kiểu MySQL và thay thế âm thầm đều cần cú pháp khác và không phải hành vi của PostgreSQL.",
        "option_texts": {
            "A": "Cả hai dòng được lưu, vì khóa chính được kiểm tra sau câu lệnh.",
            "B": "Dòng đầu được lưu và chỉ dòng thứ hai bị từ chối.",
            "C": "Toàn bộ câu lệnh thất bại và không dòng nào được lưu, vì dòng thứ hai vi phạm khóa chính.",
            "D": "Dòng thứ hai thay thế dòng thứ nhất một cách âm thầm.",
        },
        "rubrics": {},
    },
    "dm-easy-inserted-state": {
        "prompt": "Thiết lập tạo shipment(shipment_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, carrier TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', note TEXT) rồi chạy các lệnh INSERT được hiển thị trong tập dữ liệu. Trả về shipment_id, carrier, status và note cho mọi dòng đã lưu, sắp xếp theo shipment_id tăng dần.",
        "explanation": "Mỗi INSERT chỉ lưu đúng các cột mà nó nêu; cột identity tự điền giá trị, và mọi cột bị bỏ qua khỏi danh sách cột nhận giá trị mặc định hoặc NULL. Tập dữ liệu thứ nhất có một lệnh chèn nêu status tường minh là 'delivered' còn các lệnh khác dùng mặc định 'pending', và mọi note đều NULL; tập dữ liệu thứ hai có status 'pending' ở mọi dòng vì không lệnh nào nêu status. Vì id là GENERATED ALWAYS, các câu lệnh không thể tự cung cấp shipment_id.",
        "option_texts": {},
        "rubrics": {},
    },
    "dm-easy-insert-select-rows": {
        "prompt": "Thiết lập tạo sale(sale_id INT PRIMARY KEY, status TEXT, amount INT) và archive(sale_id INT PRIMARY KEY, amount INT), chèn các dòng vào sale và để archive rỗng. Bước tiếp theo là INSERT INTO archive (sale_id, amount) SELECT sale_id, amount FROM sale WHERE status = 'closed'; Không thể viết chính lệnh INSERT trong sandbox, nên hãy trả về đúng các dòng sale_id và amount mà câu lệnh này sẽ thêm vào archive, sắp xếp theo sale_id tăng dần.",
        "explanation": "INSERT ... SELECT sao chép một dòng cho mỗi dòng mà SELECT của nó trả về, nên các dòng được lưu trữ chính là các lượt bán 'closed': 1, 3 và 4, bao gồm lượt bán 3 có amount NULL được sao chép nguyên vẹn. Tập dữ liệu thứ hai không có lượt bán closed, nên INSERT sẽ không thêm gì và kết quả đúng là rỗng.",
        "option_texts": {},
        "rubrics": {},
    },
    "dm-easy-returning": {
        "prompt": "Giải thích RETURNING trong INSERT, UPDATE và DELETE của PostgreSQL. Nêu các giá trị mà nó trả về, cho một ví dụ INSERT ... RETURNING và một ví dụ DELETE ... RETURNING, và giải thích vì sao trả về các dòng bị tác động ngay trong cùng câu lệnh tốt hơn phát hành một SELECT tiếp theo.",
        "explanation": "Câu trả lời phải định nghĩa RETURNING cho cả ba câu lệnh, cho một ví dụ hợp lệ, và biện luận tính nguyên tử: các dòng được trả về chính xác là các dòng bị tác động trong cùng câu lệnh, nên một SELECT tiếp theo có thể gặp tranh chấp.",
        "option_texts": {},
        "rubrics": {
            "Incomplete": {
                "label": "Chưa đạt",
                "criteria": "Nói RETURNING chỉ tồn tại cho các truy vấn kiểu SELECT hoặc không cho ví dụ; không có lập luận về tính nguyên tử.",
            },
            "Partial": {
                "label": "Một phần",
                "criteria": "Ví dụ cơ bản đúng nhưng nhầm lẫn câu lệnh nào trả về dòng, hoặc cho rằng RETURNING thay thế mệnh đề WHERE.",
            },
            "Mostly Complete": {
                "label": "Phần lớn đầy đủ",
                "criteria": "Ngữ nghĩa và ví dụ đúng, nhưng lập luận nguyên tử/tranh chấp còn thiếu hoặc mơ hồ.",
            },
            "Complete": {
                "label": "Đầy đủ",
                "criteria": "Hoàn toàn chính xác: RETURNING trả về giá trị của dòng bị tác động cho INSERT, UPDATE và DELETE với ví dụ hợp lệ, nêu rằng UPDATE báo giá trị sau cập nhật, và giải thích rằng SELECT tiếp theo có thể thấy dữ liệu đã thay đổi trong khi RETURNING báo chính xác các dòng bị tác động trong cùng câu lệnh.",
            },
        },
    },
    "dm-hard-merge-returning": {
        "prompt": "PostgreSQL 17 thực thi MERGE INTO stock s USING feed f ON s.item = f.item WHEN MATCHED THEN UPDATE SET qty = f.qty WHEN NOT MATCHED THEN INSERT (item, qty) VALUES (f.item, f.qty) RETURNING merge_action(), s.item; RETURNING tạo ra gì?",
        "explanation": "PostgreSQL 17 thêm RETURNING cho MERGE. Đầu ra bao phủ mọi dòng được chèn, cập nhật hoặc xóa bởi lệnh, và merge_action() báo hành động nào đã chạy cho dòng đó. Các dòng bị bỏ qua vì không mệnh đề WHEN nào áp dụng không được báo.",
        "option_texts": {
            "A": "Chỉ các dòng được chèn, vì RETURNING trên MERGE bị giới hạn ở hành động INSERT.",
            "B": "Một dòng cho mỗi dòng nguồn, bất kể có khớp hay không.",
            "C": "Một dòng cho mỗi dòng đích bị tác động với hành động đã thực hiện ('INSERT', 'UPDATE' hoặc 'DELETE') và item.",
            "D": "Lỗi, vì RETURNING không được hỗ trợ trên MERGE trong PostgreSQL 17.",
        },
        "rubrics": {},
    },
    "dm-hard-merge-not-matched-by-source": {
        "prompt": "MERGE INTO product p USING feed f ON f.product_id = p.product_id WHEN MATCHED THEN UPDATE SET price = f.price WHEN NOT MATCHED BY SOURCE THEN DELETE; được thực thi. Mệnh đề NOT MATCHED BY SOURCE tác động lên những dòng nào?",
        "explanation": "WHEN NOT MATCHED BY SOURCE là phần mở rộng của PostgreSQL xử lý các dòng đích mà nguồn chưa bao giờ khớp, nên đây là nơi tự nhiên để xóa các sản phẩm không còn trong feed. Các dòng nguồn không khớp đích là trường hợp NOT MATCHED [BY TARGET] thông thường, tức là chèn.",
        "option_texts": {
            "A": "Mọi dòng đích, vì BY SOURCE ghi đè điều kiện ON.",
            "B": "Các dòng nguồn không có dòng đích khớp.",
            "C": "Các dòng đích đã khớp nhưng có price là NULL.",
            "D": "Các dòng đích không có dòng nguồn khớp; mệnh đề xóa chúng.",
        },
        "rubrics": {},
    },
    "dm-hard-merge-duplicate-match": {
        "prompt": "Một bảng nguồn MERGE chứa hai dòng có cùng khóa nối, và cả hai khớp một dòng đích qua WHEN MATCHED THEN UPDATE không điều kiện. Điều gì xảy ra?",
        "explanation": "MERGE yêu cầu tối đa một dòng thay đổi ứng viên cho mỗi dòng đích. Khi nhiều dòng nguồn khớp, chỉ một dòng được dùng để sửa đích và mọi nỗ lực sau đó sửa cùng dòng sẽ gây lỗi, nên toàn bộ câu lệnh thất bại. Loại trùng hoặc tổng hợp nguồn trước khi MERGE là cách sửa tiêu chuẩn.",
        "option_texts": {
            "A": "Dòng đích bị sửa bởi một dòng thay đổi ứng viên, và nỗ lực sau đó sửa cùng dòng sẽ gây lỗi, nên phép nối phải tạo tối đa một dòng nguồn cho mỗi dòng đích.",
            "B": "Dòng đích được cập nhật hai lần và giá trị thứ hai thắng.",
            "C": "Hai dòng nguồn được gộp thành một một cách tự động.",
            "D": "Mệnh đề WHEN MATCHED bị bỏ qua cho dòng đích đó và câu lệnh được xác nhận.",
        },
        "rubrics": {},
    },
    "dm-hard-cte-move-upsert": {
        "prompt": "WITH pulled AS (DELETE FROM inbox WHERE processed RETURNING *) INSERT INTO archive (id, body) SELECT id, body FROM pulled ON CONFLICT (id) DO NOTHING; được thực thi. Kết quả là gì?",
        "explanation": "DELETE trong CTE chạy một lần và các dòng RETURNING của nó cấp dữ liệu cho INSERT. Vì ON CONFLICT (id) DO NOTHING được đánh giá trên đích, các id đã lưu trữ bị bỏ qua, trong khi các dòng nguồn vẫn bị xóa bất kể. Tổ hợp này không thất bại, và không thể tạo id trùng vì archive thực thi tính duy nhất.",
        "option_texts": {
            "A": "Các dòng inbox đã xử lý chỉ bị xóa nếu dòng archive thực sự được chèn.",
            "B": "Các dòng inbox đã xử lý bị xóa một lần, và archive nhận các dòng có id chưa tồn tại.",
            "C": "Câu lệnh thất bại, vì CTE thay đổi dữ liệu không thể cấp dữ liệu cho INSERT có ON CONFLICT.",
            "D": "Mỗi dòng inbox đã xử lý đều được chuyển đi kể cả khi archive đã có cùng id, tạo ra bản sao.",
        },
        "rubrics": {},
    },
    "dm-hard-multi-column-subquery": {
        "prompt": "UPDATE account a SET (tier, score) = (SELECT m.tier, m.score FROM metrics m WHERE m.account_id = a.account_id); được thực thi, và một tài khoản không có dòng metrics nào. Tài khoản đó ra sao?",
        "explanation": "Phép gán nhiều cột bằng truy vấn con đặt mọi cột được liệt kê từ dòng duy nhất của truy vấn con. Khi truy vấn con không trả về dòng nào, giá trị dòng là NULL, nên mọi cột được gán trở thành NULL. Tất cả các dòng đích đều được cập nhật, đó là lý do thường thêm chốt WHERE EXISTS khi các dòng không khớp cần giữ nguyên giá trị.",
        "option_texts": {
            "A": "Tài khoản được giữ nguyên, vì không có dòng metrics nào khớp.",
            "B": "Cả tier và score được đặt thành NULL, vì truy vấn con vô hướng trả về không dòng.",
            "C": "Câu lệnh thất bại vì thiếu một dòng trong metrics.",
            "D": "Chỉ score trở thành NULL; tier giữ giá trị cũ.",
        },
        "rubrics": {},
    },
    "dm-hard-cte-evaluated-once": {
        "prompt": "WITH changed AS (UPDATE task SET done = TRUE RETURNING task_id) SELECT (SELECT count(*) FROM changed) AS updated, (SELECT count(*) FROM changed) AS total; được thực thi. Hai truy vấn con báo cáo gì?",
        "explanation": "Một truy vấn WITH được đánh giá một lần cho mỗi câu lệnh kể cả khi được tham chiếu nhiều lần; do đó cả hai truy vấn con thấy cùng tập dòng do mệnh đề RETURNING của UPDATE trả về. Không có việc thực thi hai lần và không có hạn chế tham chiếu CTE nhiều lần.",
        "option_texts": {
            "A": "UPDATE chạy hai lần, một lần cho mỗi tham chiếu.",
            "B": "Truy vấn thứ nhất báo các dòng đã cập nhật và truy vấn thứ hai báo số đếm gấp đôi.",
            "C": "Truy vấn thứ hai báo 0, vì CTE chỉ có thể được dùng một lần.",
            "D": "Cả hai báo cùng một số đếm, vì CTE được thực thi một lần và cả hai tham chiếu đọc cùng các dòng.",
        },
        "rubrics": {},
    },
    "dm-hard-overriding-system-value": {
        "prompt": "Bảng invoice(invoice_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, total INT) đã chứa các id từ 1 đến 5, và câu lệnh INSERT INTO invoice (invoice_id, total) OVERRIDING SYSTEM VALUE VALUES (100, 50); được thực thi. Hệ quả là gì?",
        "explanation": "OVERRIDING SYSTEM VALUE chính là lối thoát cho phép một giá trị tường minh vào cột identity GENERATED ALWAYS, nên câu lệnh thành công. Bản thân chuỗi không được đồng bộ bởi lệnh chèn, để lại xung đột trong tương lai trừ khi chuỗi được tăng hoặc khởi động lại thủ công. Phương án D mô tả hành vi mà PostgreSQL không tự thực hiện.",
        "option_texts": {
            "A": "Câu lệnh thất bại, vì cột identity GENERATED ALWAYS không bao giờ nhận giá trị tường minh.",
            "B": "Id tường minh 100 được lưu, và chuỗi identity không được tăng, nên một lần chèn mặc định sau đó có thể xung đột khi chuỗi đạt tới 100.",
            "C": "Giá trị 100 bị bỏ qua và một id từ chuỗi được dùng.",
            "D": "Chuỗi tự động được đặt thành 101, ngăn mọi xung đột trong tương lai.",
        },
        "rubrics": {},
    },
    "dm-hard-self-join-delete": {
        "prompt": "DELETE FROM price p USING price older WHERE p.product_id = older.product_id AND older.valid_from < p.valid_from; được thực thi. Nó làm gì?",
        "explanation": "Bảng đích và bảng USING là cùng một bảng dưới các bí danh khác nhau, điều PostgreSQL cho phép. Một dòng bị xóa khi tồn tại một dòng có cùng product_id và valid_from nhỏ hơn, nên chỉ các dòng không phải sớm nhất bị gỡ bỏ; các giá trị valid_from bằng nhau không xóa lẫn nhau vì phép so sánh là nghiêm ngặt.",
        "option_texts": {
            "A": "Câu lệnh không hợp lệ, vì một bảng không thể tham chiếu chính nó trong USING.",
            "B": "Nó xóa mọi dòng price của các sản phẩm xuất hiện nhiều hơn một lần.",
            "C": "Nó xóa cả dòng mới hơn lẫn dòng cũ hơn cho mỗi sản phẩm.",
            "D": "Nó xóa mọi dòng price có một dòng cũ hơn cho cùng sản phẩm, giữ lại các dòng có valid_from sớm nhất.",
        },
        "rubrics": {},
    },
    "dm-hard-update-from-changes": {
        "prompt": "Thiết lập tạo account(account_id INT PRIMARY KEY, email TEXT) và staging(account_id INT PRIMARY KEY, email TEXT). Bước tiếp theo là UPDATE account a SET email = s.email FROM staging s WHERE s.account_id = a.account_id AND s.email IS DISTINCT FROM a.email; Không thể viết chính lệnh UPDATE trong sandbox, nên hãy trả về các dòng mà câu lệnh sẽ thay đổi với các cột account_id, old_email và new_email, sắp xếp theo account_id tăng dần.",
        "explanation": "UPDATE ... FROM thay đổi mỗi dòng đích mà đối tác nối cung cấp giá trị khác với giá trị đã lưu, và IS DISTINCT FROM coi NULL là giá trị có thể so sánh. Tài khoản 1 bằng nhau và bị bỏ qua; tài khoản 2 đổi từ NULL thành 'b@x.edu'; tài khoản 3 đổi từ 'c@x.edu' thành NULL; tài khoản 4 không có dòng staging và không bị chạm tới; staging id 5 không có dòng đích và không thay đổi gì. Tập dữ liệu đã đồng bộ không tạo ra thay đổi nào.",
        "option_texts": {},
        "rubrics": {},
    },
    "dm-hard-merge-by-source-delete": {
        "prompt": "Thiết lập tạo product(product_id INT PRIMARY KEY, name TEXT NOT NULL) và feed(product_id INT PRIMARY KEY, price INT). Bước tiếp theo là MERGE INTO product p USING feed f ON f.product_id = p.product_id WHEN NOT MATCHED BY SOURCE THEN DELETE; Không thể viết chính lệnh MERGE trong sandbox, nên hãy trả về các dòng đích mà nó sẽ xóa với các cột product_id và name, sắp xếp theo product_id tăng dần.",
        "explanation": "WHEN NOT MATCHED BY SOURCE xử lý các dòng đích mà điều kiện ON không khớp dòng nguồn nào, nên tập bị xóa là phép phản nối của product với feed. Trong tập dữ liệu thứ nhất chỉ có product 2 vắng mặt trong feed; dòng feed 4 là dòng chỉ có ở nguồn, mà mệnh đề này không xử lý. Tập dữ liệu thứ hai khớp hoàn toàn, nên kết quả đúng là rỗng.",
        "option_texts": {},
        "rubrics": {},
    },
    "dm-hard-merge-versus-upsert": {
        "prompt": "So sánh INSERT ... ON CONFLICT với MERGE trong PostgreSQL 17 cho một công việc nạp dữ liệu. Trình bày câu lệnh nào có thể biểu đạt hành động nào, mỗi cách xử lý nguồn tạo ra nhiều dòng cho một khóa đích ra sao, RETURNING cung cấp gì ở mỗi cách, hành vi giao dịch và khóa, và khi nào bạn chọn cách này thay vì cách kia.",
        "explanation": "Câu trả lời phải phân biệt phạm vi hành động (upsert so với chèn/cập nhật/xóa), nêu chỉ mục duy nhất là trọng tài cho ON CONFLICT, mô tả quy tắc một dòng nguồn cho mỗi dòng đích ở cả hai, nhắc đến MERGE RETURNING/NOT MATCHED BY SOURCE của PostgreSQL 17, và đưa ra quy tắc lựa chọn có lý lẽ.",
        "option_texts": {},
        "rubrics": {
            "Incomplete": {
                "label": "Chưa đạt",
                "criteria": "Coi hai cách là đồng nghĩa, hoặc cho rằng MERGE không thể xóa. Không thảo luận về dòng nguồn trùng.",
            },
            "Partial": {
                "label": "Một phần",
                "criteria": "Phạm vi hành động đúng nhưng bỏ sót quy tắc nguồn trùng hoặc yêu cầu trọng tài, và quy tắc lựa chọn còn mơ hồ.",
            },
            "Mostly Complete": {
                "label": "Phần lớn đầy đủ",
                "criteria": "Hành động, trọng tài và quy tắc trùng đúng, nhưng RETURNING, khóa hoặc hướng dẫn lựa chọn chưa đầy đủ.",
            },
            "Complete": {
                "label": "Đầy đủ",
                "criteria": "Hoàn toàn chính xác: ON CONFLICT là phần mở rộng của INSERT cần trọng tài duy nhất và chỉ có thể bỏ qua/cập nhật xung đột; MERGE có thể chèn, cập nhật, xóa và (17+) xóa các dòng đích không khớp, với RETURNING và merge_action(); cả hai yêu cầu một dòng nguồn cho mỗi dòng đích và thất bại khi có bản sao; cả hai là một câu lệnh, có giao dịch và khóa các dòng bị thay đổi; quy tắc lựa chọn xuất phát từ các hành động cần thiết.",
            },
        },
    },
    "dm-medium-on-conflict-update-where": {
        "prompt": "Câu lệnh INSERT INTO stock (item, qty) VALUES ('bolt', 5) ON CONFLICT (item) DO UPDATE SET qty = EXCLUDED.qty WHERE stock.qty < EXCLUDED.qty được thực thi, và qty đã lưu cho 'bolt' là 9. Điều gì xảy ra?",
        "explanation": "Mệnh đề WHERE gắn với DO UPDATE là điều kiện trên chính cập nhật. Khi nó sai, dòng xung đột được giữ nguyên và dòng đề xuất cũng không được chèn, nên câu lệnh chỉ bỏ qua dòng đó. Nó không bao giờ biến xung đột thành lệnh chèn.",
        "option_texts": {
            "A": "Lệnh chèn xảy ra và một dòng 'bolt' thứ hai được thêm.",
            "B": "Cả cập nhật lẫn chèn đều không xảy ra; dòng bị bỏ qua vì điều kiện DO UPDATE sai.",
            "C": "Cập nhật vẫn xảy ra, và mệnh đề WHERE bị bỏ qua đối với DO UPDATE.",
            "D": "qty đã lưu được đặt thành 5 rồi thành 9.",
        },
        "rubrics": {},
    },
    "dm-medium-merge-clause-order": {
        "prompt": "Một câu lệnh MERGE có hai mệnh đề WHEN MATCHED, mệnh đề thứ nhất có chốt AND s.priority = 'high' và mệnh đề thứ hai không điều kiện. Một dòng đích khớp với một dòng nguồn có priority là 'low'. Mệnh đề nào chạy?",
        "explanation": "MERGE đánh giá các mệnh đề WHEN theo thứ tự được viết và chạy mệnh đề đầu tiên có điều kiện đúng; các mệnh đề sau không được áp dụng cho cùng dòng. Nhiều mệnh đề WHEN MATCHED là hợp lệ, đó là cách biểu đạt các hành động phụ thuộc mức ưu tiên.",
        "option_texts": {
            "A": "Cả hai mệnh đề chạy, thực hiện hai lần cập nhật.",
            "B": "Mệnh đề WHEN MATCHED thứ hai, không điều kiện, vì các mệnh đề được đánh giá theo thứ tự và điều kiện thứ nhất sai.",
            "C": "Không mệnh đề nào chạy, vì một mệnh đề có chốt vô hiệu hóa các mệnh đề còn lại.",
            "D": "Câu lệnh bị từ chối vì chỉ được phép có một mệnh đề WHEN MATCHED.",
        },
        "rubrics": {},
    },
    "dm-medium-data-modifying-cte": {
        "prompt": "Câu lệnh WITH moved AS (DELETE FROM inbox WHERE archived RETURNING *) INSERT INTO archive SELECT * FROM moved; được thực thi. Hiệu ứng là gì?",
        "explanation": "PostgreSQL cho phép các câu lệnh thay đổi dữ liệu bên trong WITH. DELETE chạy một lần, và đầu ra RETURNING của nó là tập dòng mà INSERT tiêu thụ, nên việc di chuyển là nguyên tử trong câu lệnh. CTE được thực thi một lần kể cả khi được tham chiếu nhiều lần, và cả hai thao tác thấy cùng một ảnh chụp.",
        "option_texts": {
            "A": "Câu lệnh thất bại, vì CTE không được chứa DELETE.",
            "B": "Các dòng được sao chép vào archive và vẫn nằm trong inbox cho tới khi một DELETE riêng chạy.",
            "C": "Các dòng inbox khớp bị xóa và cùng các dòng đó được chèn vào archive trong một câu lệnh nguyên tử.",
            "D": "DELETE chạy một lần cho mỗi dòng được chèn vào archive, nhân bản nguồn.",
        },
        "rubrics": {},
    },
    "dm-medium-returning-scope": {
        "prompt": "Trong PostgreSQL 17, đối với UPDATE, mệnh đề RETURNING báo các giá trị nào?",
        "explanation": "Trong PostgreSQL 17, RETURNING báo dòng ở trạng thái sau câu lệnh, nên nó hiển thị các giá trị mới; không có quan hệ OLD trong RETURNING. PostgreSQL 18 đã thêm hỗ trợ OLD/NEW, nên phiên bản có ý nghĩa. Thu giữ giá trị trước đó trong phiên bản 17 cần đọc chúng trước hoặc dùng trigger. Các dòng khớp WHERE vẫn được báo kể cả khi giá trị mới bằng giá trị cũ.",
        "option_texts": {
            "A": "Giá trị của mỗi dòng đã cập nhật sau khi cập nhật; trong PostgreSQL 17 không có dòng giả OLD phơi bày giá trị trước đó.",
            "B": "Giá trị mà mỗi dòng đã cập nhật có trước khi cập nhật.",
            "C": "Cả giá trị cũ và mới, trong hai cột song song.",
            "D": "Chỉ các dòng có giá trị thực sự thay đổi; các dòng không đổi bị bỏ qua.",
        },
        "rubrics": {},
    },
    "dm-medium-on-conflict-on-constraint": {
        "prompt": "Một chỉ mục biểu thức duy nhất được định nghĩa trên lower(email). Đích xung đột nào cho phép INSERT ... ON CONFLICT giải quyết nó một cách tường minh?",
        "explanation": "Chỉ mục duy nhất là chỉ mục biểu thức trên lower(email), và chỉ mục biểu thức không phải ràng buộc bảng, nên ON CONFLICT ON CONSTRAINT không thể nêu tên nó. Suy luận theo danh sách cột khớp với chỉ mục duy nhất có biểu thức bằng các biểu thức được liệt kê, nên đích phải là (lower(email)); email trần không khớp chỉ mục trên lower(email). DO ANYTHING không phải cú pháp PostgreSQL, và tên hàm không có đối số không phải biểu thức.",
        "option_texts": {
            "A": "ON CONFLICT DO ANYTHING, bắt mọi chỉ mục duy nhất.",
            "B": "ON CONFLICT (email), vì cột trần được suy ra từ biểu thức.",
            "C": "ON CONFLICT (lower(email)), lặp lại biểu thức chỉ mục chính xác.",
            "D": "ON CONFLICT (lower), nêu tên hàm mà không có đối số.",
        },
        "rubrics": {},
    },
    "dm-medium-merge-values-source": {
        "prompt": "Câu lệnh MERGE nào dùng đúng danh sách VALUES nội tuyến làm nguồn?",
        "explanation": "Danh sách VALUES dùng làm nguồn MERGE phải là truy vấn con trong ngoặc với bí danh bảng và tên cột tường minh, để ON và các hành động có thể tham chiếu src.item. Không có bí danh và danh sách cột, các cột nguồn không có tên xác định. Các phương án khác là cú pháp PostgreSQL không chấp nhận.",
        "option_texts": {
            "A": "MERGE INTO stock s USING (VALUES (1, 'bolt')) ON s.item = item WHEN MATCHED THEN UPDATE SET id = 1;",
            "B": "MERGE INTO stock s USING VALUES (1, 'bolt') ON s.item = item WHEN MATCHED THEN UPDATE SET id = 1;",
            "C": "MERGE INTO stock s USING (VALUES (1, 'bolt'), (2, 'nut')) AS src (id, item) ON s.item = src.item WHEN MATCHED THEN UPDATE SET id = src.id;",
            "D": "MERGE INTO stock s USING src VALUES (1, 'bolt') ON s.item = src.item WHEN MATCHED THEN UPDATE SET id = 1;",
        },
        "rubrics": {},
    },
    "dm-medium-delete-using-returning": {
        "prompt": "DELETE FROM stale s USING current c WHERE s.sale_id = c.sale_id RETURNING s.sale_id, s.amount; được thực thi. RETURNING chứa gì?",
        "explanation": "RETURNING báo các dòng mà DELETE đã gỡ bỏ, nên nó chỉ chứa các cột của stale. Bảng USING tham gia phép nối nhưng không dòng nào của current bị xóa, và RETURNING cùng USING là hợp lệ.",
        "option_texts": {
            "A": "Lỗi, vì RETURNING không thể kết hợp với USING.",
            "B": "Một dòng cho mỗi dòng current khớp bởi mệnh đề USING.",
            "C": "Các cột từ cả stale lẫn current.",
            "D": "Một dòng cho mỗi dòng stale bị xóa, với sale_id và amount của dòng đã xóa.",
        },
        "rubrics": {},
    },
    "dm-medium-update-result": {
        "prompt": "Thiết lập tạo account(account_id INT PRIMARY KEY, balance INT) và chèn các dòng, một số có balance NULL. Bước tiếp theo là UPDATE account SET balance = balance + 100 WHERE balance IS NOT NULL; Không thể viết chính lệnh UPDATE trong sandbox, nên hãy trả về các dòng mà câu lệnh sẽ để lại với các cột account_id và balance (giá trị mới), sắp xếp theo account_id tăng dần.",
        "explanation": "UPDATE áp dụng cho các dòng có balance khác NULL, nên các dòng kết quả là 1 -> 100, 3 -> 350 và 4 -> 60; tài khoản 2 bị loại vì NULL IS NOT NULL là sai, và balance NULL của nó không được coi là 0. Tập dữ liệu thứ hai không có dòng khớp, nên câu lệnh sẽ không cập nhật gì và kết quả đúng là rỗng.",
        "option_texts": {},
        "rubrics": {},
    },
    "dm-medium-on-conflict-skips": {
        "prompt": "Thiết lập tạo customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL) và staging(customer_id INT PRIMARY KEY, name TEXT NOT NULL). Bước tiếp theo là INSERT INTO customer (customer_id, name) SELECT customer_id, name FROM staging ON CONFLICT (customer_id) DO NOTHING; Không thể viết chính lệnh INSERT trong sandbox, nên hãy trả về các dòng staging mà câu lệnh sẽ bỏ qua vì customer_id của chúng đã tồn tại trong customer, với các cột customer_id và name, sắp xếp theo customer_id tăng dần.",
        "explanation": "Đích xung đột là customer_id, nên DO NOTHING bỏ qua đúng các dòng staging có khóa đã tồn tại. Trong tập dữ liệu thứ nhất, các khóa staging 2 và 3 không khớp customer nào nên không có gì bị bỏ qua; trong tập dữ liệu thứ hai, customer_id 2 xung đột và bị bỏ qua còn 3 và 4 sẽ được chèn. Phép nối biểu đạt trực tiếp sự trùng khóa đó, nên tập dữ liệu thứ hai trả về một dòng bị bỏ qua.",
        "option_texts": {},
        "rubrics": {},
    },
}

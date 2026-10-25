"""Vietnamese drafts for the SQL query-semantics specs (sq)."""

DRAFTS = {
    "sq-easy-select-alias": {
        "prompt": "Bảng customer(customer_id, name, city) có một dòng cho mỗi khách hàng. Câu lệnh nào trả về một dòng cho mỗi khách hàng với các cột name và city_label, trong đó city_label chứa giá trị city?",
        "explanation": "AS đổi tên cột đầu ra mà không đổi giá trị, nên city AS city_label tạo ra nhãn được yêu cầu. Phương án B hỏi một cột tên city_label không tồn tại; phương án A gán nhãn cho name thay vì city; phương án D là biểu thức so sánh tham chiếu một định danh chưa định nghĩa.",
        "option_texts": {
            "A": "SELECT name AS city_label, city FROM customer;",
            "B": "SELECT name, city, city_label FROM customer;",
            "C": "SELECT name, city AS city_label FROM customer;",
            "D": "SELECT name, city = city_label FROM customer;",
        },
        "rubrics": {},
    },
    "sq-easy-left-join-semantics": {
        "prompt": "Phép nối nào trả về mọi dòng của bảng trái và điền các cột từ bảng phải bằng NULL khi không có dòng khớp?",
        "explanation": "LEFT JOIN giữ nguyên đầu vào bên trái và mở rộng NULL cho các dòng không khớp. INNER JOIN loại bỏ các dòng không khớp ở cả hai phía. RIGHT JOIN giữ nguyên đầu vào bên phải, không phải bên trái. CROSS JOIN tạo mọi cặp mà không có điều kiện khớp.",
        "option_texts": {
            "A": "INNER JOIN",
            "B": "LEFT JOIN",
            "C": "RIGHT JOIN",
            "D": "CROSS JOIN",
        },
        "rubrics": {},
    },
    "sq-easy-where-before-grouping": {
        "prompt": "Mệnh đề nào lọc từng dòng trước khi nhóm và do đó không thể chứa một tổng hợp như count(*)?",
        "explanation": "WHERE chạy trên các dòng riêng lẻ trước khi các nhóm tồn tại, nên các giá trị tổng hợp không khả dụng. HAVING chạy sau khi nhóm và là nơi dành cho các điều kiện tổng hợp. ORDER BY sắp xếp kết quả cuối cùng, và SELECT đánh giá các biểu thức đầu ra sau khi nhóm.",
        "option_texts": {
            "A": "ORDER BY",
            "B": "HAVING",
            "C": "WHERE",
            "D": "SELECT",
        },
        "rubrics": {},
    },
    "sq-easy-group-count-star": {
        "prompt": "Truy vấn SELECT region_id, count(*) FROM sales GROUP BY region_id trả về một dòng cho mỗi vùng. count(*) đếm gì bên trong mỗi nhóm?",
        "explanation": "count(*) đếm các dòng trong nhóm hiện tại và không bỏ qua giá trị cột nào. Các dòng có region_id NULL tạo thành nhóm riêng khi dùng GROUP BY. count(region_id) thì sẽ bỏ qua NULL. Đếm toàn bảng đòi hỏi bỏ GROUP BY; đếm phân biệt cần count(DISTINCT ...).",
        "option_texts": {
            "A": "Mọi dòng trong toàn bộ bảng, không chỉ trong nhóm.",
            "B": "Chỉ các dòng mà region_id không NULL.",
            "C": "Chỉ các tổ hợp phân biệt của mọi cột.",
            "D": "Mọi dòng trong nhóm, bao gồm các dòng mà các cột khác là NULL.",
        },
        "rubrics": {},
    },
    "sq-easy-customer-name-length": {
        "prompt": "Bảng customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL, city TEXT). Trả về customer_id, name, và name_length (INT, số ký tự trong name) cho các khách hàng có city không NULL. Sắp xếp theo name tăng dần, rồi customer_id tăng dần.",
        "explanation": "length trả về số ký tự và được gắn nhãn name_length. WHERE ... IS NOT NULL chỉ giữ các dòng có city; viết city <> 'x' cũng sẽ loại các city NULL. Khóa sắp xếp phụ customer_id làm thứ tự tất định khi tên lặp lại, và tập dữ liệu biên đúng là trả về không dòng.",
        "option_texts": {},
        "rubrics": {},
    },
    "sq-easy-select-logical-order": {
        "prompt": "Giải thích thứ tự logic mà các mệnh đề FROM, WHERE, GROUP BY, HAVING, SELECT và ORDER BY được xử lý. Sau đó giải thích vì sao một bí danh đầu ra được định nghĩa trong SELECT không thể được tham chiếu trong WHERE nhưng có thể được dùng trong ORDER BY.",
        "explanation": "Điểm phân biệt then chốt là khả năng hiển thị: WHERE thấy các cột đầu vào nhưng không thấy bí danh đầu ra hay giá trị tổng hợp; HAVING thấy các giá trị tổng hợp đã nhóm; ORDER BY thấy danh sách chọn. Nêu các giai đoạn đúng thứ tự và gắn chúng với khả năng hiển thị của bí danh là mục tiêu học tập.",
        "option_texts": {},
        "rubrics": {
            "Incomplete": {
                "label": "Chưa đạt",
                "criteria": "Liệt kê các mệnh đề sai thứ tự hoặc khẳng định WHERE có thể thấy bí danh SELECT; không đưa ra lý do mạch lạc cho khả năng hiển thị của bí danh.",
            },
            "Partial": {
                "label": "Một phần",
                "criteria": "Đúng một phần thứ tự và nêu WHERE chạy trước SELECT, nhưng đặt sai HAVING hoặc không giải thích được vì sao ORDER BY có thể dùng bí danh.",
            },
            "Mostly Complete": {
                "label": "Phần lớn đầy đủ",
                "criteria": "Đúng thứ tự và giải thích bí danh, nhưng bỏ sót rằng HAVING thao tác trên các nhóm hoặc LIMIT áp dụng sau ORDER BY.",
            },
            "Complete": {
                "label": "Đầy đủ",
                "criteria": "Sắp xếp đúng FROM, WHERE, GROUP BY, HAVING, SELECT và ORDER BY; giải thích rằng WHERE được đánh giá trước SELECT nên bí danh không tồn tại ở đó, trong khi ORDER BY được đánh giá sau SELECT và có thể dùng chúng; nêu rằng đây là thứ tự logic, không nhất thiết là thứ tự vật lý.",
            },
        },
    },
    "sq-easy-join-null-fanout": {
        "prompt": "So sánh INNER JOIN và LEFT JOIN. Giải thích ý nghĩa của việc mở rộng NULL đối với các dòng trái không khớp, và giải thích điều gì xảy ra với số dòng khi một dòng bên trái khớp với nhiều dòng bên phải.",
        "explanation": "INNER JOIN là một bộ lọc khớp; LEFT JOIN giữ nguyên phía trái và mở rộng NULL. Không phép nối nào tự nó loại bỏ trùng, nên một phép nối một-nhiều tạo ra các dòng trái lặp lại và có thể làm phồng số đếm và tổng.",
        "option_texts": {},
        "rubrics": {
            "Incomplete": {
                "label": "Chưa đạt",
                "criteria": "Nhầm hành vi INNER và LEFT hoặc nói LEFT JOIN điền NULL vào các cột bên trái; không đề cập phép nhân dòng.",
            },
            "Partial": {
                "label": "Một phần",
                "criteria": "Phân biệt đúng dòng khớp so với dòng được giữ nhưng giải thích việc mở rộng NULL không chính xác hoặc bỏ sót phép nhân dòng.",
            },
            "Mostly Complete": {
                "label": "Phần lớn đầy đủ",
                "criteria": "Đúng ngữ nghĩa của cả hai phép nối và việc mở rộng NULL; có đề cập trùng lặp nhưng không gắn chúng với các tổng hợp sai.",
            },
            "Complete": {
                "label": "Đầy đủ",
                "criteria": "Giải thích INNER là chỉ các cặp khớp, LEFT là mọi dòng trái với các cột không khớp được mở rộng NULL, ngữ nghĩa túi với phép nhân dòng một-nhiều rõ ràng, và rủi ro số đếm hoặc tổng bị phồng khi tổng hợp sau phép nối.",
            },
        },
    },
    "sq-hard-distinct-on": {
        "prompt": "Cả hai câu lệnh dưới đây đều nhằm trả về một dòng cho mỗi vùng. Phát biểu nào về chúng là đúng? (1) SELECT DISTINCT ON (region_id) region_id, sale_id, amount FROM sale ORDER BY region_id, amount DESC; (2) SELECT DISTINCT region_id, sale_id FROM sale;",
        "explanation": "DISTINCT ON giữ dòng đầu tiên của mỗi nhóm dòng chia sẻ các biểu thức DISTINCT ON, trong đó 'đầu tiên' được xác định bởi ORDER BY của truy vấn, và ORDER BY phải bắt đầu bằng các biểu thức đó. Ngược lại, DISTINCT so sánh toàn bộ dòng đầu ra, nên các cặp (region_id, sale_id) được loại trùng, không phải các vùng. DISTINCT ON không yêu cầu biểu thức xuất hiện hai lần, và nó không tương đương với DISTINCT.",
        "option_texts": {
            "A": "Câu lệnh 2 trả về một dòng cho mỗi vùng vì DISTINCT tự động loại bỏ mọi cột không phải khóa.",
            "B": "Câu lệnh 1 thất bại, vì DISTINCT ON yêu cầu biểu thức DISTINCT ON xuất hiện hai lần trong danh sách chọn.",
            "C": "Câu lệnh 1 trả về sale có amount cao nhất cho mỗi vùng vì DISTINCT ON giữ dòng đầu tiên của mỗi vùng theo thứ tự ORDER BY; câu lệnh 2 trả về một dòng cho mỗi cặp (region_id, sale_id) phân biệt, nên nó không gộp thành một dòng cho mỗi vùng.",
            "D": "Cả hai câu lệnh trả về cùng các dòng, vì DISTINCT ON và DISTINCT tương đương khi khóa ORDER BY đầu tiên là đối số DISTINCT ON.",
        },
        "rubrics": {},
    },
    "sq-hard-not-predicate-null": {
        "prompt": "Bảng t(x INT) chứa các dòng 1, 2 và NULL. Câu lệnh SELECT x FROM t WHERE NOT (x > 5) được thực thi. PostgreSQL trả về tập kết quả nào?",
        "explanation": "So sánh NULL với 5 cho UNKNOWN. NOT UNKNOWN là UNKNOWN, không phải TRUE, nên WHERE loại dòng NULL. Các dòng 1 và 2 đều thỏa NOT (x > 5) vì 1 > 5 và 2 > 5 là FALSE và NOT FALSE là TRUE. Lỗi thường gặp là đọc NOT (x > 5) như x <= 5, điều sẽ bao gồm NULL theo một cách đọc hai giá trị không hợp lệ.",
        "option_texts": {
            "A": "Chỉ các dòng 1 và 2; dòng NULL bị loại vì NOT (UNKNOWN) vẫn là UNKNOWN và WHERE chỉ giữ TRUE.",
            "B": "Các dòng 1 và 2, cộng dòng NULL, vì NOT biến phép so sánh không xác định thành đúng.",
            "C": "Không dòng nào, vì một giá trị NULL làm toàn bộ vị từ không hợp lệ.",
            "D": "Chỉ dòng NULL, vì NOT (x > 5) là đúng bất cứ khi nào x là NULL.",
        },
        "rubrics": {},
    },
    "sq-hard-full-join-symmetric": {
        "prompt": "Các bảng a(id) và b(id) không có id NULL. Truy vấn nào trả về chính xác các id xuất hiện ở một bảng nhưng không ở bảng kia?",
        "explanation": "Một FULL JOIN phát ra các dòng khớp cộng một dòng mở rộng NULL cho mỗi dòng không khớp ở một trong hai phía. Sau USING (id), cột nối được hợp nhất, nhưng a.id và b.id vẫn cho thấy phía nào đã được mở rộng NULL. Do đó giữ các dòng mà đúng một phía là NULL sẽ trả về hiệu đối xứng. Phương án A chỉ giữ các dòng khớp, còn phương án C và D là các phép nối trong.",
        "option_texts": {
            "A": "SELECT id FROM a FULL JOIN b USING (id) WHERE a.id IS NOT NULL AND b.id IS NOT NULL;",
            "B": "SELECT id FROM a FULL JOIN b USING (id) WHERE a.id IS NULL OR b.id IS NULL;",
            "C": "SELECT id FROM a INNER JOIN b USING (id);",
            "D": "SELECT id FROM a CROSS JOIN b WHERE a.id = b.id;",
        },
        "rubrics": {},
    },
    "sq-hard-grouping-sets": {
        "prompt": "Câu lệnh SELECT region_id, count(*) AS n FROM sale GROUP BY GROUPING SETS ((region_id), ()) ORDER BY region_id NULLS LAST được thực thi trên một bảng không rỗng. Nó trả về gì?",
        "explanation": "Một grouping set là tập các cột mà một lượt tổng hợp nhóm theo. GROUPING SETS ((region_id), ()) chạy hai lượt: một nhóm theo region_id và một trên toàn bảng. Vì vậy tổng cộng toàn bộ xuất hiện như một dòng bổ sung, và các cột không thuộc grouping set đó được báo là NULL. Tập rỗng có ý nghĩa, không bị bỏ qua, và GROUP BY có chấp nhận grouping set trong PostgreSQL.",
        "option_texts": {
            "A": "Một dòng cho mỗi dòng của sale, vì các grouping set vô hiệu hóa tổng hợp.",
            "B": "Chỉ một dòng cho mỗi region_id phân biệt, vì một grouping set rỗng không đóng góp dòng nào.",
            "C": "Một dòng cho mỗi region_id phân biệt cộng một dòng tổng cộng toàn bộ có region_id là NULL.",
            "D": "Một lỗi, vì GROUP BY chỉ nhận danh sách cột, không bao giờ nhận grouping set.",
        },
        "rubrics": {},
    },
    "sq-hard-having-without-group": {
        "prompt": "Bảng sale hiện đang rỗng. Câu lệnh SELECT count(*) AS n FROM sale HAVING count(*) > 0 được thực thi. Kết quả là gì?",
        "explanation": "Khi một truy vấn có HAVING nhưng không có GROUP BY, toàn bộ bảng được coi là một nhóm duy nhất, nên đúng một dòng ứng viên được tạo trước khi HAVING chạy. count(*) trên bảng rỗng là 0, nên điều kiện 0 > 0 là sai và nhóm bị loại, để lại kết quả rỗng. PostgreSQL cho phép HAVING mà không có GROUP BY; đây không phải lỗi cú pháp.",
        "option_texts": {
            "A": "Một dòng chứa giá trị 0.",
            "B": "Không dòng nào, vì không có GROUP BY thì toàn bộ bảng tạo thành một nhóm và HAVING loại nhóm đó khi điều kiện của nó không đúng.",
            "C": "Một dòng chứa NULL.",
            "D": "Một lỗi cú pháp, vì HAVING yêu cầu mệnh đề GROUP BY.",
        },
        "rubrics": {},
    },
    "sq-hard-exists-semi-join": {
        "prompt": "customer(customer_id) có một dòng cho mỗi khách hàng, trong khi orders có thể chứa nhiều dòng cho mỗi khách hàng. Truy vấn nào trả về mỗi khách hàng có ít nhất một đơn hàng đúng một lần?",
        "explanation": "EXISTS là một bán nối: nó trả lời câu hỏi có/không cho mỗi dòng ngoài và không bao giờ nhân bản dòng đó, nên nhiều đơn hàng vẫn cho một dòng khách hàng. Phép JOIN thường nhân khách hàng lên một lần cho mỗi đơn hàng. EXISTS không tương quan ở phương án C đúng cho mọi khách hàng ngay khi orders không rỗng, và phương án D dùng truy vấn con vô hướng sẽ báo lỗi khi khách hàng có nhiều hơn một đơn hàng.",
        "option_texts": {
            "A": "SELECT c.customer_id FROM customer c WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id);",
            "B": "SELECT c.customer_id FROM customer c JOIN orders o ON o.customer_id = c.customer_id;",
            "C": "SELECT c.customer_id FROM customer c WHERE EXISTS (SELECT 1 FROM orders);",
            "D": "SELECT c.customer_id FROM customer c WHERE c.customer_id = (SELECT o.customer_id FROM orders o WHERE o.customer_id = c.customer_id);",
        },
        "rubrics": {},
    },
    "sq-hard-window-rank": {
        "prompt": "Bảng score(player TEXT, points INT) chứa ('a',100), ('b',100) và ('c',90). Câu lệnh SELECT player, points, row_number() OVER (ORDER BY points DESC) AS rn, rank() OVER (ORDER BY points DESC) AS rk, dense_rank() OVER (ORDER BY points DESC) AS dr FROM score được thực thi. Mẫu giá trị nào được tạo ra?",
        "explanation": "row_number luôn gán các số nguyên phân biệt, nên hai dòng bằng nhau nhận 1 và 2, nhưng người chơi nào nhận 1 là không được xác định vì ORDER BY points DESC không phải một thứ tự toàn phần. rank để lại một khoảng trống sau các giá trị bằng nhau và tiếp tục ở 3, trong khi dense_rank tiếp tục ở 2. Phương án A và B gán sai một giá trị trùng cho row_number, và phương án D giả định sai rằng cả ba hàm hành xử giống nhau.",
        "option_texts": {
            "A": "rn 1,1,2; rk 1,1,2; dr 1,1,2",
            "B": "rn 1,1,2; rk 1,1,3; dr 1,1,2",
            "C": "rn nhận 1 và 2 cho hai dòng bằng nhau theo thứ tự không xác định, rk là 1 cho cả hai dòng bằng nhau rồi 3, và dr là 1 cho cả hai dòng bằng nhau rồi 2.",
            "D": "rn, rk và dr đều nhận 1,2,3 vì mọi hàm cửa sổ đánh số các dòng liên tiếp.",
        },
        "rubrics": {},
    },
    "sq-hard-lateral-from": {
        "prompt": "Phát biểu nào về từ khóa LATERAL là đúng?",
        "explanation": "Một truy vấn con FROM thông thường được đánh giá độc lập và không thể thấy các mục FROM khác. LATERAL gỡ bỏ hạn chế đó, cho phép truy vấn con tham chiếu các cột của các mục đứng trước, đó là cách biểu diễn một phép tra cứu top-N theo từng dòng. LATERAL hợp lệ trong FROM, nó không phải tính năng của danh sách chọn, và nó không liên quan đến số dòng trả về.",
        "option_texts": {
            "A": "Một truy vấn con trong FROM được đánh dấu LATERAL có thể tham chiếu các cột của các mục FROM xuất hiện trước nó, điều mà một truy vấn con FROM thông thường không thể làm.",
            "B": "LATERAL chỉ có thể xuất hiện trong danh sách chọn, không bao giờ trong FROM.",
            "C": "Không có LATERAL, PostgreSQL vẫn cho phép một truy vấn con FROM tham chiếu các cột của các mục FROM trước đó.",
            "D": "LATERAL chỉ cần khi truy vấn con trả về nhiều hơn một dòng.",
        },
        "rubrics": {},
    },
    "sq-hard-aggregate-filter": {
        "prompt": "Bảng emp(dept_id INT, salary INT) có cột salary cho phép NULL. Truy vấn SELECT dept_id, count(*) AS all_rows, count(*) FILTER (WHERE salary > 5000) AS high FROM emp GROUP BY dept_id trả về một dòng cho mỗi phòng ban. Cột high chứa gì?",
        "explanation": "FILTER giới hạn các dòng được đưa vào một tổng hợp bên trong nhóm hiện tại. So sánh salary NULL với 5000 cho UNKNOWN, và chỉ các dòng TRUE được đưa vào tổng hợp, nên các salary NULL bị bỏ qua trong khi count(*) vẫn đếm chúng trong all_rows. FILTER có tính tổng quát: nó áp dụng cho mọi tổng hợp, bao gồm count.",
        "option_texts": {
            "A": "Số dòng trong phòng ban đó mà salary > 5000 là TRUE; các dòng có salary NULL không được đếm.",
            "B": "Số dòng trong toàn bộ bảng mà salary > 5000, lặp lại trên mỗi dòng phòng ban.",
            "C": "Số dòng trong phòng ban đó mà salary > 5000, coi salary NULL là cao.",
            "D": "Nó không hợp lệ, vì FILTER có thể áp dụng cho sum nhưng không cho count.",
        },
        "rubrics": {},
    },
    "sq-hard-grouping-function": {
        "prompt": "Bảng sale(region_id INT, amount INT) lưu các dòng mà region_id có thể là NULL. Truy vấn SELECT region_id, GROUPING(region_id) AS g, count(*) AS n FROM sale GROUP BY ROLLUP (region_id) ORDER BY g, region_id được thực thi. Làm thế nào phân biệt dòng tổng cộng toàn bộ với nhóm được tạo bởi các dòng có region_id là NULL?",
        "explanation": "ROLLUP (region_id) là dạng viết tắt của GROUPING SETS ((region_id), ()), nên nó tạo ra các dòng theo vùng cộng một dòng tổng cộng toàn bộ. Cả hai đều có thể hiển thị NULL ở region_id, đó là lý do hàm GROUPING tồn tại: nó trả về 1 khi cột được cung cấp bởi cơ chế grouping set thay vì được đọc từ dữ liệu, và 0 khi đó là giá trị thật. Các vùng NULL được nhóm bình thường, chúng không bị loại bỏ.",
        "option_texts": {
            "A": "ROLLUP loại bỏ các dòng có region_id NULL, nên không thể có sự nhập nhằng.",
            "B": "Cả hai dòng đều có GROUPING(region_id) = 0, nên không thể phân biệt chúng.",
            "C": "Nhóm region NULL có GROUPING(region_id) = 1 và tổng cộng toàn bộ có GROUPING(region_id) = 0.",
            "D": "Tổng cộng toàn bộ có GROUPING(region_id) = 1, trong khi nhóm region NULL có GROUPING(region_id) = 0.",
        },
        "rubrics": {},
    },
    "sq-hard-top-sale-per-region": {
        "prompt": "Bảng sale(sale_id INT PRIMARY KEY, region_id INT, amount INT) ghi lại các giao dịch; amount cho phép NULL và một vùng có thể có nhiều giao dịch. Trả về một dòng cho mỗi vùng với các cột region_id (INT), sale_id (INT) và amount (INT): giao dịch có amount lớn nhất trong vùng đó, phá vỡ hòa bằng sale_id nhỏ hơn. Một vùng mà mọi giao dịch đều có amount NULL vẫn nhận một dòng, chọn giao dịch có sale_id nhỏ nhất. Sắp xếp theo region_id tăng dần.",
        "explanation": "DISTINCT ON giữ dòng đầu tiên của mỗi vùng theo thứ tự ORDER BY. Trong một vùng, amount DESC NULLS LAST xếp amount lớn nhất trước và đặt các amount NULL ở cuối, còn sale_id phá vỡ hòa 500/500 theo hướng có lợi cho giao dịch 1. Với vùng 3, nơi mọi amount đều NULL, khóa sale_id quyết định và giao dịch 4 được chọn. Tập dữ liệu rỗng đúng là trả về không dòng.",
        "option_texts": {},
        "rubrics": {},
    },
    "sq-hard-three-valued-reporting": {
        "prompt": "Một nhóm báo cáo viết: SELECT order_id FROM orders o WHERE amount <> 0   AND customer_id NOT IN (SELECT customer_id FROM blocked) Bảng orders có các cột amount và customer_id cho phép NULL, và bảng blocked có thể chứa NULL. (a) Giải thích mệnh đề WHERE giữ những dòng nào và vì sao amount NULL hoặc một NULL trong truy vấn con âm thầm loại bỏ các dòng. (b) Viết lại phép loại trừ sao cho an toàn với NULL, dùng NOT EXISTS, và nêu những dòng nào bản viết lại bây giờ bao gồm mà bản gốc đã loại. (c) Giải thích cách lập luận tương tự áp dụng cho HAVING với sum(amount) > 100 trên một nhóm mà mọi amount đều NULL, và nêu điều bạn phải quyết định một cách tường minh.",
        "explanation": "Câu trả lời phải gắn hành vi với logic ba giá trị thay vì một khẳng định mơ hồ 'NULL là đặc biệt'. Phần (a) phải chỉ ra UNKNOWN không phải TRUE cũng không phải FALSE và WHERE/HAVING chỉ giữ TRUE. Phần (b) phải đưa ra dạng NOT EXISTS và xác định các dòng nó khôi phục. Phần (c) phải lưu ý rằng SUM trên một nhóm toàn NULL là NULL và cần coalesce hoặc một quy tắc loại trừ tường minh.",
        "option_texts": {},
        "rubrics": {
            "Incomplete": {
                "label": "Chưa đạt",
                "criteria": "Khẳng định NULL bằng nhau, coi UNKNOWN là FALSE, hoặc không đưa ra bản viết lại; không gắn hành vi WHERE với câu hỏi HAVING.",
            },
            "Partial": {
                "label": "Một phần",
                "criteria": "Nhận ra NULL làm các phép so sánh thành UNKNOWN và có thể nêu rằng các dòng bị loại, nhưng bản viết lại NOT EXISTS bị thiếu hoặc vẫn nhạy cảm với NULL, và HAVING không được đề cập.",
            },
            "Mostly Complete": {
                "label": "Phần lớn đầy đủ",
                "criteria": "Giải thích đúng sự lan truyền NULL qua NOT IN và bản viết lại NOT EXISTS đúng, nhưng các dòng được bản viết lại khôi phục không được xác định, hoặc phần HAVING chỉ đúng một phần.",
            },
            "Complete": {
                "label": "Đầy đủ",
                "criteria": "Hoàn toàn chính xác: giải thích rằng chỉ các dòng TRUE tồn tại, rằng amount NULL hoặc NULL trong truy vấn con biến vị từ thành UNKNOWN, đưa ra bản viết lại NOT EXISTS với IS DISTINCT FROM hoặc một quy tắc NULL tường minh, nêu các dòng mà bản viết lại khôi phục, và giải thích rằng SUM trên một nhóm toàn NULL là NULL nên cần coalesce hoặc một chính sách tường minh trong HAVING.",
            },
        },
    },
    "sq-medium-alias-visibility": {
        "prompt": "Phát biểu nào về một bí danh đầu ra được đưa vào danh sách chọn SELECT là đúng trong PostgreSQL?",
        "explanation": "Thứ tự đánh giá logic đến WHERE trước khi SELECT tính các biểu thức đầu ra, nên bí danh chưa tồn tại. ORDER BY chạy sau SELECT và có thể tham chiếu một tên đầu ra. HAVING cũng chạy trước SELECT, nên bí danh thường không khả dụng ở đó. Bí danh chỉ đổi tên đầu ra; các cột đầu vào vẫn truy cập được bằng tên của chúng.",
        "option_texts": {
            "A": "Bí danh có thể được dùng trong WHERE vì WHERE được đánh giá sau SELECT.",
            "B": "Bí danh có thể được dùng trong ORDER BY nhưng không trong WHERE, vì WHERE được đánh giá trước danh sách chọn SELECT.",
            "C": "Bí danh hiển thị trong mọi mệnh đề, bao gồm HAVING và WHERE.",
            "D": "Bí danh thay thế cột đầu vào, nên cột gốc không còn truy cập được ở đâu nữa.",
        },
        "rubrics": {},
    },
    "sq-medium-not-in-null": {
        "prompt": "Bảng orders có customer_id cho phép NULL, và truy vấn con SELECT customer_id FROM orders hiện trả về ít nhất một NULL. Truy vấn nào trả về đáng tin cậy các khách hàng không có đơn hàng?",
        "explanation": "NOT IN tương đương với một chuỗi các phép so sánh <>. So sánh bất kỳ giá trị nào với NULL cho UNKNOWN, nên một NULL trong truy vấn con làm vị từ thành UNKNOWN cho mọi khách hàng và truy vấn trả về không dòng. NOT EXISTS kiểm tra sự vắng mặt của một dòng khớp và không bị ảnh hưởng bởi các giá trị NULL. Phương án C có cùng độ nhạy với NULL, và phương án D áp NOT lên chính phép thử IN đó, nên cũng nhạy với NULL và trả về không dòng khi truy vấn con có NULL.",
        "option_texts": {
            "A": "SELECT c.id FROM customer c WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id);",
            "B": "SELECT id FROM customer WHERE id NOT IN (SELECT customer_id FROM orders);",
            "C": "SELECT id FROM customer WHERE id <> ALL (SELECT customer_id FROM orders);",
            "D": "SELECT id FROM customer WHERE NOT id IN (SELECT customer_id FROM orders);",
        },
        "rubrics": {},
    },
    "sq-medium-left-join-filter": {
        "prompt": "Truy vấn nào chỉ trả về các khách hàng có ít nhất một đơn hàng, mặc dù được viết bằng LEFT JOIN?",
        "explanation": "Một LEFT JOIN phát ra các dòng mở rộng NULL cho những khách hàng không khớp. Lọc o.customer_id IS NOT NULL sau đó loại các dòng ấy, chỉ để lại các khách hàng có ít nhất một dòng khớp. IS NULL là phép phản nối và trả về tập ngược lại. HAVING không có GROUP BY không lọc theo từng khách hàng. Chuyển điều kiện vào ON chỉ giới hạn các đơn hàng khớp và vẫn giữ các khách hàng không khớp.",
        "option_texts": {
            "A": "SELECT c.id FROM customer c LEFT JOIN orders o ON o.customer_id = c.id HAVING count(*) > 0;",
            "B": "SELECT c.id FROM customer c LEFT JOIN orders o ON o.customer_id = c.id WHERE o.customer_id IS NULL;",
            "C": "SELECT c.id FROM customer c LEFT JOIN orders o ON o.customer_id = c.id WHERE o.customer_id IS NOT NULL;",
            "D": "SELECT c.id FROM customer c LEFT JOIN orders o ON o.customer_id = c.id AND o.amount > 0;",
        },
        "rubrics": {},
    },
    "sq-medium-count-null": {
        "prompt": "Bảng customer có cột email cho phép NULL. SELECT count(*), count(email) FROM customer trả về gì?",
        "explanation": "count(*) đếm các dòng. count(biểu thức) đếm các giá trị không NULL của biểu thức đó, nên hai con số có thể khác nhau. Các dạng này có thể được kết hợp trong một truy vấn tổng hợp không có GROUP BY, khi đó tạo ra đúng một dòng.",
        "option_texts": {
            "A": "Hai số đếm bằng nhau, vì count bỏ qua NULL trong cả hai dạng.",
            "B": "count(*) đếm mọi dòng, trong khi count(email) chỉ đếm các dòng mà email không NULL.",
            "C": "count(email) đếm mọi dòng, trong khi count(*) chỉ đếm các email không NULL.",
            "D": "Truy vấn phát sinh lỗi vì một tổng hợp không có GROUP BY không thể kết hợp hai dạng.",
        },
        "rubrics": {},
    },
    "sq-medium-where-having-order": {
        "prompt": "Xét SELECT dept_id FROM emp WHERE salary > 1000 GROUP BY dept_id HAVING count(*) >= 2. Truy vấn trả về gì?",
        "explanation": "WHERE loại các nhân viên có salary <= 1000 hoặc salary NULL trước khi nhóm. Sau đó GROUP BY tạo các phòng ban từ những dòng còn lại, và HAVING giữ các phòng ban có số dòng còn lại ít nhất là hai. Bộ lọc là theo từng nhân viên trước khi nhóm, không phải một tổng, và kết quả có một dòng cho mỗi phòng ban thỏa mãn.",
        "option_texts": {
            "A": "Mọi phòng ban có ít nhất hai nhân viên, bất kể lương.",
            "B": "Các phòng ban có ít nhất hai nhân viên mà lương lớn hơn 1000.",
            "C": "Các phòng ban có tổng lương lớn hơn 1000.",
            "D": "Các nhân viên riêng lẻ kiếm hơn 1000 và xuất hiện ít nhất hai lần.",
        },
        "rubrics": {},
    },
    "sq-medium-group-functional-dependency": {
        "prompt": "Bảng dept có dept_id là khóa chính và một cột dept_name. Vì sao PostgreSQL chấp nhận SELECT d.dept_id, d.dept_name, count(*) FROM dept d JOIN emp e ON e.dept_id = d.dept_id GROUP BY d.dept_id?",
        "explanation": "PostgreSQL cho phép một cột không được nhóm khi nó phụ thuộc hàm vào các cột được nhóm, và một khóa chính xác định các cột khác của bảng nó. Phép nối không phá vỡ sự phụ thuộc đó vì dept_name đến từ dept. Không có phụ thuộc như vậy, mỗi nhóm có thể chứa nhiều giá trị dept_name và PostgreSQL từ chối truy vấn thay vì bịa ra một câu trả lời.",
        "option_texts": {
            "A": "Nó không được chấp nhận; mọi cột được chọn phải xuất hiện trong GROUP BY.",
            "B": "Vì PostgreSQL luôn cho phép các cột không được nhóm và chọn một giá trị tùy ý cho chúng.",
            "C": "Vì dept_name được bộ lập kế hoạch thêm ngầm vào danh sách GROUP BY.",
            "D": "Vì dept_name phụ thuộc hàm vào khóa chính được nhóm dept_id; các cột không được nhóm khác đều bị từ chối.",
        },
        "rubrics": {},
    },
    "sq-medium-join-fanout-sum": {
        "prompt": "Mỗi đơn hàng có ba dòng trong orders và hai dòng trong items cho mỗi đơn hàng. Truy vấn SELECT sum(o.amount) FROM orders o JOIN items i ON i.order_id = o.order_id trả về một tổng lớn hơn nhiều so với tổng các amount của đơn hàng. Vì sao?",
        "explanation": "Một phép nối một-nhiều nhân mỗi dòng đơn hàng với số dòng mục của nó. SUM ở đây không có DISTINCT, nên amount lặp lại đóng góp một lần cho mỗi dòng được nối. Cách sửa là tổng hợp items trước hoặc tính tổng các amount của đơn hàng trong một truy vấn con riêng. SUM không tự loại trùng, NULL bị bỏ qua chứ không chuyển thành 0, và việc loại bỏ dòng không thể làm tăng tổng của các amount không âm.",
        "option_texts": {
            "A": "Phép nối phát ra một dòng cho mỗi cặp đơn hàng-mục, nên mỗi amount của đơn hàng được lặp lại một lần cho mỗi mục và được cộng lặp lại.",
            "B": "SUM tự động đếm các giá trị trùng, nên mỗi amount của đơn hàng được đếm hai lần.",
            "C": "Các amount NULL được coi là 0, điều làm tăng tổng.",
            "D": "Phép nối loại bỏ các dòng không có mục, điều làm phồng giá trị trung bình nhưng không làm phồng tổng.",
        },
        "rubrics": {},
    },
    "sq-medium-select-computed-column": {
        "prompt": "Biểu thức danh sách chọn nào trả về một dòng cho mỗi giao dịch với id gốc và một cột được tính có nhãn gross, bằng amount nhân với 1.1?",
        "explanation": "AS gắn nhãn gross cho biểu thức được tính mà không đổi số dòng. Phương án B là một phép so sánh boolean với một định danh chưa định nghĩa; phương án C đặt bí danh cho bảng thay vì cột đầu ra và để cột được tính không có tên; phương án A đặt nhãn gross cho id.",
        "option_texts": {
            "A": "SELECT id AS gross, amount * 1.1 FROM sales;",
            "B": "SELECT id, gross = amount * 1.1 FROM sales;",
            "C": "SELECT id, amount * 1.1 FROM sales AS gross;",
            "D": "SELECT id, amount * 1.1 AS gross FROM sales;",
        },
        "rubrics": {},
    },
    "sq-medium-where-null-exclusion": {
        "prompt": "Cột status cho phép NULL. WHERE status <> 'cancelled' trả về những dòng nào?",
        "explanation": "Trong logic ba giá trị, NULL <> 'cancelled' đánh giá là UNKNOWN, và WHERE chỉ giữ TRUE. Vì vậy các dòng có status NULL bị loại. Để bao gồm chúng, kiểm tra status IS NULL OR status <> 'cancelled', hoặc dùng IS DISTINCT FROM, coi NULL như một giá trị có thể so sánh. NULL không phải chuỗi rỗng.",
        "option_texts": {
            "A": "Chỉ các dòng mà status là một giá trị không NULL khác 'cancelled'; các dòng NULL bị loại vì phép so sánh là UNKNOWN.",
            "B": "Các dòng mà status là bất kỳ giá trị nào trừ 'cancelled', bao gồm các dòng NULL.",
            "C": "Mọi dòng, vì NULL được coi là chuỗi rỗng.",
            "D": "Truy vấn thất bại vì <> không thể dùng với một cột cho phép NULL.",
        },
        "rubrics": {},
    },
    "sq-medium-scalar-subquery-multirow": {
        "prompt": "Một truy vấn con vô hướng xuất hiện trong danh sách chọn. Điều gì xảy ra nếu truy vấn con đó trả về nhiều hơn một dòng tại thời điểm thực thi?",
        "explanation": "Một truy vấn con vô hướng được dùng ở nơi mong đợi một giá trị duy nhất. Không dòng nào cho NULL, nhưng nhiều hơn một dòng là lỗi ('more than one row returned by a subquery used as an expression'). PostgreSQL không âm thầm chọn một dòng hay tổng hợp; truy vấn phải bảo đảm bản số bằng một tổng hợp, LIMIT 1, hoặc một điều kiện tương quan.",
        "option_texts": {
            "A": "PostgreSQL trả về dòng đầu tiên và bỏ qua phần còn lại.",
            "B": "PostgreSQL tự động tổng hợp các dòng thành một giá trị.",
            "C": "PostgreSQL trả về NULL cho các dòng thừa.",
            "D": "PostgreSQL phát sinh lỗi vì một truy vấn con vô hướng phải trả về nhiều nhất một dòng.",
        },
        "rubrics": {},
    },
    "sq-medium-customer-order-count": {
        "prompt": "Bảng customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL) và bảng orders(order_id INT PRIMARY KEY, customer_id INT, amount NUMERIC(10,2)). Trả về customer_id, name và order_count (BIGINT) cho mọi khách hàng, bao gồm các khách hàng không có đơn hàng. Sắp xếp theo order_count giảm dần, rồi customer_id tăng dần.",
        "explanation": "LEFT JOIN giữ các khách hàng không có đơn hàng, và đếm o.order_id thay vì * biến giá trị thay thế NULL của phép nối thành 0. Nhóm theo customer_id và name giữ cho name được chọn hợp lệ. ORDER BY có thể dùng bí danh đầu ra order_count; khóa phá hòa trên customer_id làm kết quả tất định.",
        "option_texts": {},
        "rubrics": {},
    },
    "sq-medium-order-customer-flag": {
        "prompt": "Bảng customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL) và bảng orders(order_id INT PRIMARY KEY, customer_id INT). Trả về order_id (INT), name (TEXT) và has_customer (BOOLEAN) cho mọi đơn hàng. Các đơn hàng có customer_id không khớp với khách hàng nào được trả về với name NULL và has_customer false; customer_id NULL được xử lý giống như vậy. Sắp xếp theo order_id tăng dần.",
        "explanation": "LEFT JOIN giữ mọi đơn hàng. c.customer_id IS NOT NULL là FALSE cho cả khóa mồ côi lẫn khóa NULL, nên cờ boolean phân biệt các đơn hàng khớp và không khớp mà không chuyển NULL thành văn bản. Tập dữ liệu biên không có đơn hàng và đúng là trả về không dòng.",
        "option_texts": {},
        "rubrics": {},
    },
    "sq-medium-result-bag-join": {
        "prompt": "Giải thích cách một câu lệnh SELECT nối hai bảng và áp dụng WHERE tạo ra kết quả của nó. Trình bày danh sách chọn, lọc dòng, ngữ nghĩa túi và phép nhân trùng lặp. Nêu một ví dụ trong đó một phép nối một-nhiều thay đổi số dòng và giải thích khi nào DISTINCT hoặc tổng hợp trước là cách sửa phù hợp.",
        "explanation": "Các điểm thiết yếu là thứ tự mệnh đề logic, ngữ nghĩa túi, phép nhân dòng một-nhiều, và sự phân biệt giữa DISTINCT như việc loại bỏ dòng trùng và tổng hợp trước như cách sửa các tổng hợp sai.",
        "option_texts": {},
        "rubrics": {
            "Incomplete": {
                "label": "Chưa đạt",
                "criteria": "Coi kết quả SQL là tập hợp có loại trùng tự động, hoặc không giải thích được các dòng bị lọc ở đâu; không có ví dụ về phép nhân dòng.",
            },
            "Partial": {
                "label": "Một phần",
                "criteria": "Mô tả FROM/WHERE/SELECT nhưng khẳng định phép nối loại bỏ trùng, hoặc đề xuất DISTINCT như cách sửa phổ quát cho các tổng hợp bị phồng.",
            },
            "Mostly Complete": {
                "label": "Phần lớn đầy đủ",
                "criteria": "Đúng thứ tự logic và ngữ nghĩa túi; có ví dụ, nhưng hướng dẫn về DISTINCT so với tổng hợp trước chưa đầy đủ.",
            },
            "Complete": {
                "label": "Đầy đủ",
                "criteria": "Giải thích đúng FROM/ON, WHERE, SELECT, ngữ nghĩa túi và phép nhân một-nhiều với một ví dụ cụ thể; phân biệt DISTINCT (loại bỏ toàn bộ dòng trùng) với tổng hợp trước (tổng đúng theo từng thực thể) và chọn đúng công cụ cho từng mục tiêu.",
            },
        },
    },
    "sq-medium-join-aggregate-null": {
        "prompt": "Giải thích cách INNER JOIN và LEFT JOIN ảnh hưởng đến các tổng hợp count và sum. Trình bày các dòng không khớp, amount NULL, count(*) so với count(cột), và phép nhân dòng khi bảng được nối có nhiều dòng khớp. Nêu quy tắc bạn sẽ dùng để đếm đúng các khách hàng không có đơn hàng.",
        "explanation": "Quy tắc đúng kết hợp LEFT JOIN, nhóm theo khách hàng, và count(o.order_id); count(*) sau một LEFT JOIN đếm dòng thay thế và báo một thay vì không.",
        "option_texts": {},
        "rubrics": {
            "Incomplete": {
                "label": "Chưa đạt",
                "criteria": "Dùng INNER JOIN cho khách hàng không có đơn hàng hoặc count(*) sau một LEFT JOIN; không thảo luận tổng hợp NULL hay phép nhân dòng.",
            },
            "Partial": {
                "label": "Một phần",
                "criteria": "Biết LEFT JOIN giữ khách hàng nhưng nhầm lẫn count(*) với count(cột), hoặc bỏ qua phép nhân dòng.",
            },
            "Mostly Complete": {
                "label": "Phần lớn đầy đủ",
                "criteria": "Xử lý đúng NULL và count(cột), nhưng thảo luận về phép nhân dòng hoặc quy tắc đếm cuối cùng chưa đầy đủ.",
            },
            "Complete": {
                "label": "Đầy đủ",
                "criteria": "Giải thích INNER so với việc giữ nguyên của LEFT, mở rộng NULL, count(*) so với count(cột), hành vi NULL của sum, phép nhân một-nhiều và tổng hợp trước; nêu quy tắc khách hàng không có đơn hàng là LEFT JOIN cộng count(o.order_id) nhóm theo khách hàng.",
            },
        },
    },
}

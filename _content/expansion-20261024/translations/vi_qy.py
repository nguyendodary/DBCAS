"""Vietnamese drafts for the query-semantics specs (qy)."""

DRAFTS = {
    "qy-easy-recursive-cte": {
        "prompt": "Giải thích cấu trúc của một truy vấn WITH RECURSIVE trong PostgreSQL. Chỉ ra phần cơ sở và phần đệ quy, nêu phần đệ quy phải tham chiếu đến gì, và giải thích vì sao cần có điều kiện dừng. Mô tả sự khác biệt giữa UNION và UNION ALL trong ngữ cảnh này.",
        "explanation": "Câu trả lời phải xác định phần cơ sở là các dòng khởi đầu không đệ quy, phần đệ quy là phần tham chiếu CTE, và việc đánh giá lặp lại cho tới khi không còn dòng nào được tạo ra. Nó phải giải thích một điều kiện dừng và phân biệt UNION (loại bỏ trùng) với UNION ALL (giữ trùng, nhanh hơn, có rủi ro chu trình).",
        "option_texts": {},
        "rubrics": {
            "Incomplete": {
                "label": "Chưa đạt",
                "criteria": "Mô tả CTE đệ quy như một truy vấn con thông thường, hoặc không phân tách phần cơ sở/phần đệ quy và không lập luận về điều kiện dừng.",
            },
            "Partial": {
                "label": "Một phần",
                "criteria": "Nêu được phần cơ sở và phần đệ quy nhưng không giải thích vòng lặp dừng như thế nào, hoặc nhầm UNION với UNION ALL.",
            },
            "Mostly Complete": {
                "label": "Phần lớn đầy đủ",
                "criteria": "Giải thích cấu trúc và điều kiện dừng, nhưng phân biệt UNION với UNION ALL chưa đầy đủ hoặc không nêu rủi ro chu trình.",
            },
            "Complete": {
                "label": "Đầy đủ",
                "criteria": "Hoàn toàn chính xác: phần cơ sở, phần đệ quy tự tham chiếu, đánh giá lặp tới kết quả rỗng, điều kiện dừng tường minh hoặc đạt được tự nhiên, và UNION loại trùng so với UNION ALL cùng rủi ro chu trình của nó.",
            },
        },
    },
    "qy-hard-case-no-else": {
        "prompt": "Biểu thức CASE WHEN rating >= 4 THEN 'high' WHEN rating >= 2 THEN 'mid' END được đánh giá với rating = 1. Kết quả là gì?",
        "explanation": "CASE dạng tìm kiếm đánh giá các điều kiện WHEN theo thứ tự và trả về kết quả của điều kiện đúng đầu tiên; các nhánh sau không được đánh giá. Nếu không nhánh nào đúng và không có ELSE, kết quả là NULL. Không có hạng thấp nhất ngầm định và không xảy ra lỗi.",
        "option_texts": {
            "A": "Một lỗi, vì biểu thức CASE luôn phải trả về một giá trị.",
            "B": "'mid', vì CASE rơi về nhánh cuối khi không có nhánh nào khớp.",
            "C": "'low', vì CASE coi giá trị không khớp là hạng thấp nhất.",
            "D": "NULL, vì không điều kiện WHEN nào đúng và CASE không có nhánh ELSE.",
        },
        "rubrics": {},
    },
    "qy-hard-distinct-rows-and-nulls": {
        "prompt": "Bảng customer(city, state) chứa các dòng ('Hue', NULL), ('Hue', NULL) và ('Hue', 'Thua Thien Hue'). SELECT DISTINCT city, state FROM customer trả về bao nhiêu dòng?",
        "explanation": "DISTINCT thao tác trên toàn bộ dòng được chọn, không phải trên một cột. Đối với mục đích loại trùng, các giá trị NULL được coi là bằng nhau, nên hai dòng ('Hue', NULL) gộp thành một và kết quả có hai dòng. Điều này khác với phép so sánh =, trong đó NULL = NULL là không xác định.",
        "option_texts": {
            "A": "Một lỗi, vì DISTINCT không thể dùng với các cột cho phép NULL.",
            "B": "Ba, vì NULL không bao giờ bằng NULL, nên mỗi dòng NULL là phân biệt.",
            "C": "Một, vì DISTINCT chỉ giữ giá trị city đầu tiên.",
            "D": "Hai, vì DISTINCT so sánh toàn bộ dòng và coi hai giá trị state NULL là bằng nhau.",
        },
        "rubrics": {},
    },
    "qy-hard-exponent-operator": {
        "prompt": "Biểu thức PostgreSQL 2 ^ 3 trả về gì?",
        "explanation": "Trong PostgreSQL, ^ là toán tử lũy thừa: 2 ^ 3 nâng 2 lên lũy thừa ba và cho 8 (dưới dạng giá trị dấu phẩy động). Nó không phải XOR và không phải phép nhân. Dấu trừ một ngôi liên kết chặt hơn ^, nên -2 ^ 2 nghĩa là (-2) ^ 2 và cho 4; hãy viết -(2 ^ 2) để bình phương trước rồi đổi dấu.",
        "option_texts": {
            "A": "6, vì ^ được coi là phép nhân với hai.",
            "B": "1, vì ^ là toán tử XOR theo bit.",
            "C": "9, vì ^ được đánh giá là 2 lũy thừa 3 trừ 1.",
            "D": "8, vì ^ là phép lũy thừa trong PostgreSQL.",
        },
        "rubrics": {},
    },
    "qy-hard-limit-pagination-ties": {
        "prompt": "Một ứng dụng khách phân trang kết quả bằng ORDER BY score DESC LIMIT 10 OFFSET n, và nhiều dòng có cùng score. Rủi ro về tính đúng đắn là gì?",
        "explanation": "LIMIT/OFFSET được áp dụng cho một kết quả đã sắp xếp, nhưng ORDER BY trên một cột không duy nhất để thứ tự các dòng bằng nhau không được xác định và có thể khác nhau giữa các lần thực thi. Vì vậy các lần thực thi tách biệt có thể đặt một dòng bằng nhau trên hai trang hoặc không trang nào. Thêm một cột duy nhất, chẳng hạn khóa chính, làm khóa ORDER BY cuối cùng khiến việc phân trang tất định. Phân trang theo khóa (keyset) là giải pháp thay thế có khả năng mở rộng.",
        "option_texts": {
            "A": "Các dòng có score bằng nhau có thể xuất hiện trên nhiều trang hoặc bị bỏ sót hoàn toàn, vì thứ tự tương đối của chúng không tất định; thêm một khóa phân giải duy nhất vào ORDER BY sẽ khắc phục.",
            "B": "OFFSET không thể kết hợp với LIMIT, nên truy vấn thất bại ngay khi n lớn hơn không.",
            "C": "Trang thứ hai nhất thiết tiếp nối chính xác trang thứ nhất, vì các dòng bằng nhau được trả về theo thứ tự chèn vật lý.",
            "D": "LIMIT chỉ đếm các score phân biệt, nên mỗi trang có thể chứa hơn mười dòng.",
        },
        "rubrics": {},
    },
    "qy-hard-order-by-nulls": {
        "prompt": "Với thứ tự sắp xếp mặc định, các giá trị NULL xuất hiện ở đâu trong ORDER BY score ASC và ORDER BY score DESC?",
        "explanation": "PostgreSQL sắp các NULL như thể chúng lớn hơn mọi giá trị không NULL, nên thứ tự tăng dần đặt chúng cuối cùng và thứ tự giảm dần đặt chúng đầu tiên. ORDER BY ... NULLS FIRST hoặc NULLS LAST ghi đè mặc định một cách tường minh; các dòng NULL không bị loại.",
        "option_texts": {
            "A": "Đầu tiên trong ASC và cuối cùng trong DESC, vì NULL được sắp như giá trị nhỏ nhất.",
            "B": "Cuối cùng trong ASC và đầu tiên trong DESC, vì NULL được coi là lớn hơn mọi giá trị không NULL.",
            "C": "Ở vị trí không xác định trong cả hai chiều, vì NULL không có thứ tự.",
            "D": "Các dòng NULL bị loại khỏi kết quả trong cả hai chiều.",
        },
        "rubrics": {},
    },
    "qy-hard-intersect-precedence": {
        "prompt": "SELECT 1 UNION SELECT 2 INTERSECT SELECT 2 trả về gì?",
        "explanation": "INTERSECT có độ ưu tiên cao hơn UNION và EXCEPT, nên phép giao của SELECT thứ hai và thứ ba được tính trước và cho 2; phép hợp với 1 sau đó tạo ra {1, 2}. Việc dùng lẫn các phép toán tập hợp là hợp lệ, và dấu ngoặc có thể làm rõ một cách nhóm khác. Khi còn nghi ngờ, hãy đặt ngoặc.",
        "option_texts": {
            "A": "Các dòng 1 và 2, vì INTERSECT liên kết chặt hơn UNION và được đánh giá trước.",
            "B": "Chỉ dòng 2, vì UNION được đánh giá trước và phép giao sau đó giữ 2.",
            "C": "Chỉ dòng 1, vì INTERSECT loại 2 khỏi phép hợp.",
            "D": "Một lỗi cú pháp, vì các phép toán tập hợp phải được đặt trong ngoặc khi dùng lẫn nhau.",
        },
        "rubrics": {},
    },
    "qy-hard-distinct-order-by-expression": {
        "prompt": "Vì sao SELECT DISTINCT city FROM customer ORDER BY lower(city) thất bại trong PostgreSQL?",
        "explanation": "Với DISTINCT, đầu ra là một tập các dòng, và PostgreSQL yêu cầu mỗi biểu thức ORDER BY khớp với một cột đầu ra. lower(city) không có trong danh sách chọn, nên truy vấn bị từ chối với 'for SELECT DISTINCT, ORDER BY expressions must appear in select list'. Chọn lower(city) AS city_key hoặc sắp xếp theo cột city đã chọn sẽ tránh lỗi. Ngoài ra DISTINCT và ORDER BY có thể kết hợp bình thường.",
        "option_texts": {
            "A": "Nó thất bại vì lower() không thể được dùng trong ORDER BY.",
            "B": "Nó không thất bại: ORDER BY được đánh giá sau DISTINCT, nên biểu thức luôn được phép.",
            "C": "Với SELECT DISTINCT, các biểu thức ORDER BY phải xuất hiện trong danh sách chọn, nên lower(city) phải được chọn hoặc phải dùng ORDER BY city.",
            "D": "Nó thất bại vì DISTINCT và ORDER BY không bao giờ có thể kết hợp trong một truy vấn.",
        },
        "rubrics": {},
    },
    "qy-hard-alias-visibility": {
        "prompt": "Điều gì xảy ra khi thực thi SELECT price * qty AS total FROM item WHERE total > 100 ORDER BY total?",
        "explanation": "WHERE được đánh giá trước danh sách chọn, nên bí danh đầu ra không tồn tại tại thời điểm đó; truy vấn báo lỗi 'column total does not exist'. Ngược lại, ORDER BY có thể tham chiếu tên cột đầu ra và chấp nhận total. Lặp lại price * qty trong WHERE, hoặc bọc truy vấn trong một truy vấn con để lộ total, sẽ giải quyết vấn đề.",
        "option_texts": {
            "A": "Nó chạy, nhưng WHERE chỉ được áp dụng sau phép nhân khi bí danh cũng được dùng trong ORDER BY.",
            "B": "Nó chạy thành công vì một bí danh đầu ra hiển thị trong mọi mệnh đề của truy vấn.",
            "C": "Nó thất bại vì total là bí danh đầu ra và không hiển thị trong WHERE, mặc dù cùng bí danh đó được phép trong ORDER BY.",
            "D": "Nó chỉ thất bại nếu hai cột được chọn đều có tên total.",
        },
        "rubrics": {},
    },
    "qy-medium-clause-order-limit": {
        "prompt": "Xét SELECT dept, count(*) AS n FROM employee WHERE active GROUP BY dept HAVING count(*) > 2 ORDER BY n DESC LIMIT 3. Phát biểu nào về cách các mệnh đề tương tác là đúng?",
        "explanation": "Thứ tự xử lý logic là FROM, WHERE, GROUP BY, HAVING, SELECT, rồi ORDER BY và LIMIT. Do đó WHERE chỉ thấy các dòng riêng lẻ và không thể lọc theo một giá trị tổng hợp; HAVING là bộ lọc tổng hợp. ORDER BY sắp xếp kết quả của danh sách chọn, và LIMIT được áp dụng cuối cùng cho kết quả đã sắp xếp đó. Một bí danh đầu ra như n có thể được dùng trong ORDER BY, nhưng không được dùng trong WHERE.",
        "option_texts": {
            "A": "ORDER BY n không hợp lệ vì không thể dùng một bí danh đầu ra trong ORDER BY khi truy vấn cũng có GROUP BY.",
            "B": "WHERE chạy sau GROUP BY, nên nó có thể lọc các nhóm theo số đếm của chúng.",
            "C": "LIMIT được áp dụng trước ORDER BY, nên nó chọn ba nhân viên tùy ý rồi sắp xếp chúng.",
            "D": "WHERE lọc các dòng riêng lẻ trước khi nhóm, HAVING lọc các nhóm sau khi tổng hợp, ORDER BY sắp xếp các dòng được chọn, và LIMIT giữ ba dòng đầu tiên của kết quả đã sắp xếp đó.",
        },
        "rubrics": {},
    },
}

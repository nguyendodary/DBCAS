"""Vietnamese drafts for the database-design specs (db_easy, db_hard, db_medium).

Draft text only: merge_translations.py validates label alignment and writes the
pending manifest. Nothing here is imported into question_translation.
"""

DRAFTS = {
    "db-easy-weak-entity": {
        "prompt": "Trong mô hình ER, một thực thể phụ thuộc chỉ có thể tồn tại khi thực thể chủ sở hữu của nó tồn tại, và khóa định danh của nó bao gồm khóa chính của chủ sở hữu. Cách ánh xạ quan hệ nào là đúng?",
        "explanation": "Thực thể yếu được định danh thông qua chủ sở hữu: khóa của chủ sở hữu là một phần khóa chính của thực thể yếu và đồng thời là khóa ngoại. Khóa phức hợp ngăn hai chủ sở hữu chia sẻ cùng giá trị khóa bộ phận, còn khóa ngoại cùng quy tắc xóa bảo toàn phụ thuộc tồn tại. Khóa thay thế đơn thuần không mã hóa quan hệ định danh; danh sách phân cách không nguyên tử; và khóa ngoại cho phép NULL mâu thuẫn với phụ thuộc tồn tại đã nêu.",
        "option_texts": {
            "A": "Cấp cho bảng phụ thuộc khóa chính thay thế riêng và bỏ khóa của chủ sở hữu, vì khóa thay thế làm chủ sở hữu trở nên không cần thiết.",
            "B": "Thêm khóa ngoại cho phép NULL tới chủ sở hữu và cho phép các dòng phụ thuộc không tham chiếu chủ sở hữu nào, vì NULL nghĩa là 'chưa được gán'.",
            "C": "Lưu các dòng phụ thuộc dưới dạng danh sách phân tách bằng dấu phẩy trong một cột của bảng chủ sở hữu, vì quan hệ là một-nhiều.",
            "D": "Dùng khóa chính phức hợp gồm khóa chính của chủ sở hữu cộng với khóa bộ phận của thực thể phụ thuộc, cùng khóa ngoại tới chủ sở hữu.",
        },
        "rubrics": {},
    },
    "db-easy-one-to-many-fk": {
        "prompt": "Một đơn hàng phải thuộc đúng một khách hàng, và một khách hàng có thể đặt không hoặc nhiều đơn hàng. Khóa ngoại nên được đặt ở đâu để biểu diễn quan hệ một-nhiều này?",
        "explanation": "Ở phía nhiều, mỗi đơn hàng lưu một khóa khách hàng, nên customer_id trong orders có thể là NOT NULL và tham chiếu customer. Đặt order_id trong customer sẽ chỉ cho phép tối đa một đơn hàng mỗi khách hàng và tạo phụ thuộc vòng. Bảng liên kết cần cho quan hệ nhiều-nhiều, không phải một-nhiều. Sao chép các cột mô tả của khách hàng tái tạo dị thường cập nhật và không thực thi quan hệ.",
        "option_texts": {
            "A": "Trong bảng orders, dưới dạng customer_id NOT NULL tham chiếu khóa chính của customer.",
            "B": "Trong bảng customer, dưới dạng order_id tham chiếu orders, để mỗi dòng khách hàng trỏ tới đơn hàng mới nhất của mình.",
            "C": "Trong một bảng liên kết riêng có khóa là customer_id và order_id, vì mọi quan hệ đều cần bảng riêng.",
            "D": "Trong bảng orders, dưới dạng sao chép các cột customer_name và customer_city thay vì khóa.",
        },
        "rubrics": {},
    },
    "db-easy-deletion-anomaly": {
        "prompt": "Một nhà cung cấp và các linh kiện mà nhà cung cấp đó cung cấp được lưu trong part(part_id, part_name, supplier_id, supplier_name, supplier_city). Xóa linh kiện cuối cùng do một nhà cung cấp cung cấp cũng xóa bản ghi duy nhất về tên và thành phố của nhà cung cấp đó. Đây là dị thường nào?",
        "explanation": "Dòng dữ liệu trộn lẫn hai thực thể, part và supplier. Xóa linh kiện cuối cùng buộc phải xóa thông tin nhà cung cấp vốn không có nơi lưu riêng: đó là dị thường xóa. Dị thường chèn và dị thường cập nhật là các vấn đề dư thừa liên quan, nhưng triệu chứng được nêu là mất thông tin khi xóa. Đọc ma là hiện tượng cô lập giao dịch và không liên quan đến thiết kế lược đồ.",
        "option_texts": {
            "A": "Dị thường chèn, vì không thể ghi một nhà cung cấp mới nếu chưa có linh kiện.",
            "B": "Dị thường xóa, vì xóa một dòng part phá hủy các thông tin không liên quan về nhà cung cấp.",
            "C": "Dị thường cập nhật, vì thành phố của nhà cung cấp được lưu nhiều lần.",
            "D": "Dị thường đọc ma, vì một giao dịch đồng thời nhìn thấy dòng chưa từng được xác nhận.",
        },
        "rubrics": {},
    },
    "db-easy-update-anomaly": {
        "prompt": "Một bảng orders lặp lại customer_phone trên mỗi dòng đơn hàng. Khi khách hàng đổi số điện thoại, ứng dụng phải cập nhật nhiều dòng, và một dòng bị bỏ sót để lại các giá trị mâu thuẫn. Điều này mô tả dị thường nào?",
        "explanation": "Cùng một thông tin khách hàng bị lặp lại trên nhiều dòng, nên một thay đổi logic cần nhiều cập nhật vật lý; bỏ sót một dòng tạo ra không nhất quán. Đó là định nghĩa của dị thường cập nhật. Dị thường xóa và chèn liên quan đến việc mất thông tin hoặc không thể ghi thông tin; dị thường tuần tự hóa thuộc về điều khiển đồng thời, không phải dư thừa của lược đồ.",
        "option_texts": {
            "A": "Dị thường xóa do gỡ bỏ đơn hàng cuối cùng.",
            "B": "Dị thường cập nhật do lưu cùng một thông tin ở nhiều nơi.",
            "C": "Dị thường chèn do thêm đơn hàng mà không có số điện thoại.",
            "D": "Dị thường tuần tự hóa do các giao dịch đồng thời.",
        },
        "rubrics": {},
    },
    "db-easy-multivalued-skill": {
        "prompt": "Một nhân viên có thể có nhiều kỹ năng. Thiết kế nào vừa mô hình hóa đúng quan hệ vừa giữ các giá trị thuộc tính nguyên tử?",
        "explanation": "Thuộc tính đa trị trở thành một quan hệ riêng có khóa kết hợp khóa của chủ sở hữu và khóa của giá trị; mỗi ô khi đó chỉ chứa một giá trị. Chuỗi phân cách và mảng JSONB đều lưu nhiều giá trị trong một ô, không nguyên tử trong mô hình quan hệ dù PostgreSQL cho phép các kiểu đó. Các cột cố định skill_1..skill_3 là nhóm lặp và áp đặt một giới hạn tùy ý.",
        "option_texts": {
            "A": "Một bảng liên kết employee_skill(employee_id, skill_id) có khóa chính là (employee_id, skill_id), cùng khóa ngoại tới cả hai bảng cha.",
            "B": "Ba cột skill_1, skill_2 và skill_3, để các cột không dùng là NULL.",
            "C": "Một cột skills TEXT chứa các giá trị như 'SQL,Python,Go'.",
            "D": "Một cột mảng JSONB trên employee, vì PostgreSQL có thể đánh chỉ mục phần tử mảng.",
        },
        "rubrics": {},
    },
    "db-easy-normalization-goal": {
        "prompt": "Phát biểu nào mô tả đúng nhất mục đích của chuẩn hóa?",
        "explanation": "Chuẩn hóa phân rã các quan hệ theo phụ thuộc hàm để mỗi thông tin chỉ được lưu một lần, giảm dị thường chèn, cập nhật và xóa. Nó không loại bỏ phép nối (phân rã tốt thường cần phép nối), nó ngược lại với việc thêm cột dư thừa, và chỉ mục là vấn đề hiệu năng vật lý không liên quan đến tính đúng đắn của dạng chuẩn.",
        "option_texts": {
            "A": "Nó loại bỏ nhu cầu phép nối bằng cách đặt mọi thông tin vào một bảng.",
            "B": "Nó tổ chức các thuộc tính thành các quan hệ để giảm dư thừa và các dị thường cập nhật do đó phát sinh, đồng thời bảo toàn các phụ thuộc.",
            "C": "Nó sao chép các cột thường được đọc để truy vấn tránh phải tổng hợp.",
            "D": "Nó bảo đảm mọi truy vấn đều dùng chỉ mục.",
        },
        "rubrics": {},
    },
    "db-easy-total-participation": {
        "prompt": "Mỗi khoản vay phải gắn với đúng một thành viên, trong khi một thành viên có thể không có khoản vay nào. Ràng buộc quan hệ nào biểu đạt sự tham gia bắt buộc của loan trong mối quan hệ?",
        "explanation": "Sự tham gia bắt buộc ở phía nhiều được thực thi bằng cách đặt khóa ngoại NOT NULL: mọi dòng loan phải nêu một member tồn tại. UNIQUE sẽ hạn chế sai mỗi thành viên chỉ có một khoản vay. Đặt khóa ngoại trong member đảo ngược quan hệ và không thể biểu diễn nhiều khoản vay cho một thành viên. Một CHECK số học không nói gì về sự tồn tại của member được tham chiếu.",
        "option_texts": {
            "A": "Một UNIQUE member_id trong bảng loan, vì mỗi khoản vay cần một thành viên riêng.",
            "B": "Một khóa ngoại member_id NOT NULL trong bảng loan tham chiếu tới member.",
            "C": "Một khóa ngoại từ member tới loan, để mỗi dòng thành viên trỏ tới một khoản vay.",
            "D": "CHECK (member_id > 0) trên bảng loan.",
        },
        "rubrics": {},
    },
    "db-easy-repeating-group": {
        "prompt": "Bảng contact(customer_id, phone_1, phone_2, phone_3) lưu tối đa ba số điện thoại cho mỗi khách hàng và để các cột không dùng là NULL. Dạng chuẩn nào bị vi phạm trực tiếp nhất, và vì sao?",
        "explanation": "1NF yêu cầu mỗi vị trí thuộc tính chỉ chứa một giá trị nguyên tử và cấm nhóm lặp. Các cột được đánh số là một nhóm lặp và đồng thời giới hạn số điện thoại. Khóa của bảng là thuộc tính đơn customer_id, nên phụ thuộc bộ phận (2NF) không thể phát sinh ở đây, và không có yếu tố xác định bắc cầu hay không phải siêu khóa nào được mô tả; khiếm khuyết nằm ở mức nguyên tử.",
        "option_texts": {
            "A": "Dạng chuẩn thứ hai, vì phone_2 chỉ phụ thuộc vào một phần của khóa phức hợp.",
            "B": "Dạng chuẩn thứ nhất, vì các cột phone_1..phone_3 tạo thành một nhóm lặp thay vì các thuộc tính đơn trị nguyên tử.",
            "C": "Dạng chuẩn thứ ba, vì phone_3 phụ thuộc bắc cầu vào khóa.",
            "D": "Dạng chuẩn Boyce-Codd, vì tồn tại một yếu tố xác định không phải siêu khóa.",
        },
        "rubrics": {},
    },
    "db-easy-city-customer-count": {
        "prompt": "Bảng customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL, city TEXT) lưu một dòng cho mỗi khách hàng. Trả về mỗi thành phố một dòng với các cột city (TEXT) và customers (BIGINT), đếm số khách hàng trong thành phố đó. Bao gồm một nhóm cho city NULL. Sắp xếp theo city tăng dần với NULL ở cuối.",
        "explanation": "GROUP BY city tạo một nhóm cho mỗi giá trị không NULL khác nhau và một nhóm cho tất cả các NULL; count(*) đếm số dòng trong mỗi nhóm, không phải số khách hàng khác nhau, điều này đúng vì customer_id là khóa chính. NULLS LAST làm nhóm NULL có thứ tự xác định. Tập dữ liệu rỗng trả về không dòng, đó là kết quả đúng chứ không phải lỗi.",
        "option_texts": {},
        "rubrics": {},
    },
    "db-easy-order-owner-left-join": {
        "prompt": "Bảng customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL) và bảng orders(order_id INT PRIMARY KEY, customer_id INT, amount NUMERIC(10,2)). Trả về order_id (INT), name (TEXT) và amount cho mọi đơn hàng. Nếu customer_id của một đơn hàng không khớp khách hàng nào, trả về đơn hàng đó với name là NULL. Sắp xếp theo order_id tăng dần.",
        "explanation": "Trong tập dữ liệu này, quan hệ là tùy chọn từ phía đơn hàng, nên LEFT JOIN giữ mọi đơn hàng và tạo NULL khi không có khách hàng khớp, bao gồm cả khóa mồ côi và khóa NULL. Tên khách hàng trùng lặp không phải vấn đề vì phép nối dùng khóa. Khi không có đơn hàng, kết quả rỗng, và tập cột vẫn được xác định bởi danh sách SELECT.",
        "option_texts": {},
        "rubrics": {},
    },
    "db-hard-bcnf-dependency-loss": {
        "prompt": "Quan hệ R(A,B,C,D) có các phụ thuộc hàm AB -> CD và D -> A. Một phân rã BCNF tạo ra R1(A,D) và R2(B,C,D). Phát biểu nào đúng?",
        "explanation": "Các khóa ứng viên là AB và BD: AB+ là toàn bộ thuộc tính, còn BD+ đạt A qua D -> A rồi đạt C qua AB -> C. D -> A vi phạm BCNF. Phép tách có thuộc tính chung D, và D -> A làm D trở thành khóa của R1, nên phép nối bảo toàn kết nối. R2 không có phụ thuộc chiếu không tầm thường nào, nhưng AB -> CD không thể kiểm tra trong một quan hệ nào vì cần A từ R1 và B,C,D từ R2. Do đó phân rã BCNF không nhất thiết bảo toàn phụ thuộc.",
        "option_texts": {
            "A": "Phân rã bảo toàn kết nối nhưng không bảo toàn AB -> CD.",
            "B": "Phân rã bảo toàn kết nối và bảo toàn AB -> CD.",
            "C": "Phân rã mất mát vì A và B được đặt ở các quan hệ khác nhau.",
            "D": "Không tồn tại phân rã BCNF của quan hệ này, nên câu hỏi không hợp lệ.",
        },
        "rubrics": {},
    },
    "db-hard-four-candidate-keys": {
        "prompt": "Quan hệ R(A,B,C,D,E) thỏa AB -> C, C -> D, D -> E và E -> B. Tập nào đúng chính xác là tập khóa ứng viên?",
        "explanation": "AB+ = {A,B,C,D,E}. AC+ đạt D qua C -> D, đạt E qua D -> E, và đạt B qua E -> B, nên AC là khóa. AD+ đạt E qua D -> E, đạt B qua E -> B, và đạt C qua AB -> C, nên AD là khóa. AE+ đạt B qua E -> B, đạt C qua AB -> C, và đạt D qua C -> D, nên AE là khóa. Không cặp nào không chứa A xác định được toàn bộ thuộc tính: BC+ thiếu A và mọi cặp khác đều nhỏ hơn. Vì vậy chính xác AB, AC, AD và AE là các khóa tối tiểu.",
        "option_texts": {
            "A": "{AB, AC, AD, AE}",
            "B": "{AB, AC}",
            "C": "{AB}",
            "D": "{AB, AC, AD, AE, BC}",
        },
        "rubrics": {},
    },
    "db-hard-3nf-synthesis": {
        "prompt": "Quan hệ R(A,B,C,D,E) có các phụ thuộc hàm AB -> C, C -> D và D -> E. Khóa ứng viên duy nhất là AB. Tập quan hệ nào là tổng hợp 3NF đúng của R?",
        "explanation": "Các phụ thuộc hàm đã cho tạo thành phủ tối tiểu, nên tổng hợp tạo một quan hệ cho mỗi phụ thuộc: (A,B,C), (C,D), (D,E). Khóa ứng viên AB nằm trong R1, nên không cần thêm quan hệ khóa. Yếu tố xác định của mỗi quan hệ là khóa của quan hệ đó, nên kết quả đạt BCNF, bảo toàn kết nối và bảo toàn phụ thuộc. Phương án B làm mất AB -> C; quan hệ giữ nguyên không đạt 3NF vì C -> D và D -> E là bắc cầu; phương án A không bảo toàn phụ thuộc gốc nào.",
        "option_texts": {
            "A": "R1(A,C), R2(B,D), R3(C,E).",
            "B": "R1(A,B), R2(C,D,E).",
            "C": "R(A,B,C,D,E) giữ nguyên, vì các phụ thuộc tạo thành một chuỗi.",
            "D": "R1(A,B,C), R2(C,D), R3(D,E).",
        },
        "rubrics": {},
    },
    "db-hard-lossless-key-test": {
        "prompt": "Quan hệ R(A,B,C) thỏa B -> C và được phân rã thành R1(A,B) và R2(B,C). Phụ thuộc hàm nào là lý do phân rã bảo toàn kết nối?",
        "explanation": "Thuộc tính chung là B. Bảo toàn kết nối đòi hỏi các thuộc tính chung là siêu khóa của ít nhất một phép chiếu. B -> C nghĩa là B xác định mọi thuộc tính của R2(B,C), nên B là khóa của R2 và phép nối không thể tạo ra bộ dữ liệu giả. Chỉ bảo toàn thuộc tính không bảo đảm bảo toàn kết nối, và không có phụ thuộc nào liên quan tới A hay C được đưa ra.",
        "option_texts": {
            "A": "A -> B, vì A phải xác định phía còn lại.",
            "B": "Không cần phụ thuộc hàm nào; mọi phân rã nhị phân giữ đủ thuộc tính đều bảo toàn kết nối.",
            "C": "C -> A, vì A và C phải có quan hệ với nhau.",
            "D": "B -> C, vì khi đó B là khóa của R2.",
        },
        "rubrics": {},
    },
    "db-hard-array-1nf": {
        "prompt": "Một bảng PostgreSQL lưu tags TEXT[] với nhiều giá trị thẻ trong một dòng. Xét theo mô hình quan hệ, phát biểu nào đúng?",
        "explanation": "1NF là thuộc tính của mô hình quan hệ: mỗi vị trí thuộc tính chỉ chứa một giá trị. Kiểu mảng của PostgreSQL là phần mở rộng có chủ đích cho phép lưu trữ phi 1NF, không phải bằng chứng về tính nguyên tử. Một quan hệ con với một thẻ mỗi dòng khôi phục 1NF và hỗ trợ ràng buộc, phép nối và lập luận phụ thuộc. Không có khóa phức hợp nào được mô tả ở đây, và việc dùng mảng không hàm ý cũng không ngăn cản 3NF.",
        "option_texts": {
            "A": "Cột chứa giá trị không nguyên tử; 1NF quan hệ yêu cầu một bảng con như tag(entity_id, tag), dù PostgreSQL chấp nhận và đánh chỉ mục mảng.",
            "B": "Bảng đạt 1NF vì mảng PostgreSQL là một kiểu cột được định nghĩa với các toán tử cấp phần tử.",
            "C": "Bảng vi phạm 2NF vì mỗi thẻ phụ thuộc vào một phần của khóa chính phức hợp.",
            "D": "Bảng tự động đạt 3NF vì các phần tử mảng không thể tham gia phụ thuộc hàm.",
        },
        "rubrics": {},
    },
    "db-hard-specialization-mapping": {
        "prompt": "Person được chuyên biệt hóa thành Employee và Contractor. Một person có thể là cả hai, và mỗi person phải là ít nhất một trong hai. Ánh xạ nào thực thi mô hình trung thực nhất trong PostgreSQL?",
        "explanation": "Các thuộc tính chung thuộc về siêu kiểu, và mỗi bảng kiểu con tham chiếu tới nó bằng cùng khóa chính, nên một person có thể xuất hiện trong cả hai bảng kiểu con (chuyên biệt hóa chồng lấn). Khóa ngoại từ kiểu con tới siêu kiểu bảo đảm dòng kiểu con có một person, nhưng SQL không thể thực thi ràng buộc ngược 'mọi person đều có kiểu con'; điều đó cần trigger, kiểm tra kiểu assertion hoặc bảng vai trò. Các bảng kiểu con trùng lặp làm mất danh tính; cột vai trò cho phép NULL không thể biểu diễn cả hai vai trò một cách độc lập; ràng buộc UNIQUE ở phương án D cấm chồng lấn.",
        "option_texts": {
            "A": "Tạo person(person_id PK), employee(person_id PK/FK REFERENCES person) và contractor(person_id PK/FK REFERENCES person); các dòng kiểu con riêng cho phép chồng lấn, còn sự tham gia toàn phần cần trigger hoặc bảng vai trò vì khóa ngoại thông thường không thể yêu cầu có ít nhất một dòng kiểu con.",
            "B": "Tạo bảng employee và contractor, mỗi bảng lặp lại toàn bộ thuộc tính của person, không có bảng person chung.",
            "C": "Tạo một bảng person với các cột employee và contractor cho phép NULL, điều này cho phép một person là cả hai.",
            "D": "Tạo person_role(person_id, role) với UNIQUE(person_id) để mỗi person có đúng một vai trò.",
        },
        "rubrics": {},
    },
    "db-hard-2nf-decomposition": {
        "prompt": "Quan hệ R(student_id, course_id, student_name, course_title, grade) có khóa chính (student_id, course_id), với student_id -> student_name và course_id -> course_title. Phân rã nào đạt 2NF và bảo toàn cả các phụ thuộc lẫn phép nối?",
        "explanation": "Cả hai thuộc tính không khóa đều phụ thuộc vào một tập con thực sự của khóa phức hợp, nên 2NF yêu cầu tách mỗi phụ thuộc bộ phận vào quan hệ riêng. Quan hệ enrollment giữ phụ thuộc toàn khóa grade. Nối lại theo student_id và course_id là bảo toàn kết nối vì mỗi thuộc tính chung là khóa của quan hệ tham chiếu, và cả ba phụ thuộc gốc đều có thể thực thi trong một quan hệ mỗi phụ thuộc. Phương án C lặp lại các thuộc tính và không chuẩn hóa; phương án A là quan hệ 1NF gốc.",
        "option_texts": {
            "A": "Giữ R nguyên vẹn, vì mọi thuộc tính không khóa đều phụ thuộc vào toàn bộ khóa.",
            "B": "student_course(student_id, course_id), names(student_id, student_name, course_title).",
            "C": "enrollment(student_id, course_id, grade) và attributes(student_id, course_id, student_name, course_title).",
            "D": "student(student_id, student_name), course(course_id, course_title), enrollment(student_id, course_id, grade).",
        },
        "rubrics": {},
    },
    "db-hard-overlapping-keys-bcnf": {
        "prompt": "Quan hệ R(Student, Course, Teacher) có các phụ thuộc hàm (Student, Course) -> Teacher và Teacher -> Course. Các khóa ứng viên của nó là (Student, Course) và (Student, Teacher). Phát biểu nào đúng?",
        "explanation": "Teacher -> Course có yếu tố xác định không phải siêu khóa, nên BCNF thất bại. Course là thuộc tính khóa (nó xuất hiện trong khóa ứng viên (Student, Course)), nên ngoại lệ thuộc tính khóa của 3NF áp dụng và R đạt 3NF. Tách theo Teacher là bảo toàn kết nối vì Teacher là khóa của (Teacher, Course). Phụ thuộc (Student, Course) -> Teacher cần cả Student lẫn Course, mà không quan hệ phân rã nào chứa cả hai, nên nó không được bảo toàn. 2NF nói về phụ thuộc bộ phận của thuộc tính không khóa; Course là thuộc tính khóa.",
        "option_texts": {
            "A": "R đạt 3NF nhưng không đạt BCNF; phân rã BCNF thành (Student, Teacher) và (Teacher, Course) bảo toàn kết nối nhưng làm mất (Student, Course) -> Teacher.",
            "B": "R đã đạt BCNF vì cả hai yếu tố xác định đều là khóa ứng viên.",
            "C": "R vi phạm 2NF vì Teacher -> Course phụ thuộc vào một phần của khóa ứng viên.",
            "D": "Phân rã mất mát vì Course chỉ xuất hiện trong một quan hệ.",
        },
        "rubrics": {},
    },
    "db-hard-weak-entity-key": {
        "prompt": "Số thanh toán chỉ duy nhất trong phạm vi một khoản vay, và một thanh toán không thể tồn tại nếu không có khoản vay. Định nghĩa khóa chính nào ánh xạ đúng thực thể yếu này?",
        "explanation": "Khóa của chủ sở hữu định danh loan_id cộng với khóa bộ phận payment_no tạo thành khóa chính phức hợp của thực thể yếu. Khóa ngoại thực thi phụ thuộc tồn tại, và ON DELETE CASCADE xóa các thanh toán khi khoản vay của chúng biến mất. Khóa chủ sở hữu cho phép NULL tạo ra các bản ghi mồ côi; thêm amount vào khóa làm thay đổi danh tính; và tính duy nhất chỉ trên payment_no mâu thuẫn với việc số thanh toán lặp lại giữa các khoản vay.",
        "option_texts": {
            "A": "payment(payment_id PK) với khóa ngoại loan_id cho phép NULL, vì mỗi thanh toán vẫn cần một định danh duy nhất toàn cục.",
            "B": "payment(payment_id PK, loan_id, payment_no) với ràng buộc UNIQUE chỉ trên payment_no.",
            "C": "payment(payment_no, amount) với khóa chính (payment_no, amount), vì cặp này là duy nhất.",
            "D": "payment(loan_id, payment_no, amount, paid_at) với khóa chính (loan_id, payment_no) và loan_id REFERENCES loan ON DELETE CASCADE.",
        },
        "rubrics": {},
    },
    "db-hard-prime-attribute-3nf": {
        "prompt": "Quan hệ R(A,B,C,D) thỏa AB -> C, C -> D và D -> B. Các khóa ứng viên của nó là AB, AC và AD. Phát biểu nào đúng?",
        "explanation": "Mọi thuộc tính đều là thuộc tính khóa (A, B, C và D đều xuất hiện trong ít nhất một khóa ứng viên), nhưng BCNF quan tâm tới yếu tố xác định chứ không phải việc thuộc tính có phải thuộc tính khóa hay không. C và D không phải siêu khóa, nên C -> D và D -> B vi phạm BCNF. Vì D và B là thuộc tính khóa, ngoại lệ của 3NF áp dụng và quan hệ đạt 3NF. 2NF được thỏa vì khóa là phức hợp và không thuộc tính không khóa nào phụ thuộc vào một tập con thực sự; 1NF nói về giá trị nguyên tử.",
        "option_texts": {
            "A": "R đạt BCNF vì mọi thuộc tính đều là thuộc tính khóa.",
            "B": "R vi phạm 1NF vì D xuất hiện ở cả hai vế của một phụ thuộc.",
            "C": "R chỉ đạt 2NF vì D -> B là phụ thuộc bộ phận vào khóa ứng viên AD.",
            "D": "R đạt 3NF nhưng không đạt BCNF vì C -> D và D -> B có yếu tố xác định không phải siêu khóa mà thuộc tính phụ thuộc là thuộc tính khóa.",
        },
        "rubrics": {},
    },
    "db-hard-category-tree": {
        "prompt": "Bảng category(category_id INT PRIMARY KEY, name TEXT NOT NULL, parent_id INT) biểu diễn quan hệ một-nhiều tự tham chiếu; parent_id NULL đánh dấu nút gốc. Giả sử không có chu trình, trả về category_id, name, depth (INT, 0 cho nút gốc) và root_name (TEXT, tên của tổ tiên cấp cao nhất) cho mọi danh mục có thể đạt tới từ một nút gốc. Các dòng có chuỗi cha không bao giờ tới nút gốc không được trả về. Sắp xếp theo depth tăng dần, rồi category_id tăng dần.",
        "explanation": "Phần đệ quy bắt đầu từ các nút gốc và thêm một cấp mỗi lần lặp trong khi mang theo tên gốc, qua đó thực thi quan hệ cha-con mà không giả định độ sâu cố định. Trong tập dữ liệu biên, hai nút gốc được trả về với cùng tên, điều này hợp lệ vì tên không phải khóa, và bản ghi mồ côi có cha không tồn tại là không thể đạt tới nên bị loại. ORDER BY làm kết quả xác định giữa các lần thực thi.",
        "option_texts": {},
        "rubrics": {},
    },
    "db-hard-transitive-audit": {
        "prompt": "Bảng employee(employee_id INT PRIMARY KEY, dept_id INT, dept_name TEXT) có thể chứa vi phạm phụ thuộc bắc cầu. Trả về dept_id, name_variants (BIGINT: số giá trị dept_name không NULL khác nhau) và employees (BIGINT: số dòng trong phòng ban) cho mọi dept_id không NULL có nhiều hơn một dept_name không NULL khác nhau. Sắp xếp theo name_variants giảm dần, rồi dept_id tăng dần.",
        "explanation": "Nếu dept_id -> dept_name đúng, mỗi phòng ban sẽ có một tên không NULL khác nhau duy nhất. Mệnh đề HAVING chỉ lộ ra những phòng ban mà điều đó sai. Tên phòng ban NULL không được tính là một biến thể, nên một phòng ban có nhiều NULL và một tên thật vẫn nhất quán; các dòng có dept_id NULL không thuộc phòng ban nào và bị loại. Tập dữ liệu biên không chứa vi phạm và trả về không dòng.",
        "option_texts": {},
        "rubrics": {},
    },
    "db-hard-ternary-decomposition": {
        "prompt": "Một chuỗi cung ứng ghi lại supply(supplier_id, supplier_name, supplier_city, part_id, part_name, project_id, project_name, quantity). Các phụ thuộc hàm là: supplier_id -> supplier_name, supplier_city; part_id -> part_name; project_id -> project_name; và (supplier_id, part_id, project_id) -> quantity. (a) Xác định khóa ứng viên và chứng minh nó tối tiểu. (b) Nêu dạng chuẩn cao nhất và gọi tên mọi phụ thuộc ngăn dạng chuẩn kế tiếp. (c) Phân rã quan hệ về 3NF, liệt kê khóa chính và khóa ngoại. (d) Chứng minh phân rã bảo toàn kết nối và bảo toàn phụ thuộc.",
        "explanation": "Bộ ba là khóa vì quantity chỉ có ý nghĩa với một tổ hợp nhà cung cấp-linh kiện-dự án. Các phụ thuộc bộ phận vào từng thuộc tính khóa đơn giữ quan hệ gốc ở 1NF. Tách thành supplier, part, project và supply loại bỏ chúng, bảo toàn mỗi phụ thuộc trong một quan hệ và nối lại qua các khóa, nên phân rã vừa bảo toàn kết nối vừa bảo toàn phụ thuộc.",
        "option_texts": {},
        "rubrics": {
            "Incomplete": {
                "label": "Chưa đạt",
                "criteria": "Không xác định được khóa ứng viên hoặc khóa thiếu yếu tố xác định của quantity; không có lập luận dạng chuẩn hợp lệ; phân rã đề xuất làm mất sự kiện supply hoặc không thể nối lại.",
            },
            "Partial": {
                "label": "Một phần",
                "criteria": "Gọi đúng khóa bộ ba nhưng bỏ sót ít nhất một phụ thuộc bộ phận hoặc gán sai dạng chuẩn cao nhất; phân rã tách được một số thực thể nhưng khóa hoặc khóa ngoại chưa đầy đủ.",
            },
            "Mostly Complete": {
                "label": "Phần lớn đầy đủ",
                "criteria": "Đúng khóa và cả bốn phụ thuộc bộ phận; phân rã thành supplier, part, project và supply với khóa, nhưng lập luận bảo toàn kết nối hoặc bảo toàn phụ thuộc còn thiếu.",
            },
            "Complete": {
                "label": "Đầy đủ",
                "criteria": "Hoàn toàn chính xác: khóa {supplier_id, part_id, project_id} với chứng minh tối tiểu; dạng cao nhất là 1NF vì bốn phụ thuộc bộ phận; phân rã supplier, part, project và supply với khóa chính, khóa ngoại đúng; bảo toàn kết nối theo phép thử thuộc tính chung là khóa; bảo toàn phụ thuộc vì mỗi phụ thuộc được thực thi trong một quan hệ.",
            },
        },
    },
    "db-medium-closure": {
        "prompt": "Quan hệ R(A,B,C,D) thỏa các phụ thuộc hàm A -> B và B -> C. Phát biểu nào đúng?",
        "explanation": "Tính bao đóng thuộc tính: bắt đầu với {A}; A -> B thêm B; B -> C thêm C; không phụ thuộc nào có vế trái nằm trong {A,B,C} sinh ra D. Do đó A+ = {A,B,C}, A không phải siêu khóa, và không phụ thuộc nào suy ra D -> A. Khóa ứng viên phải xác định mọi thuộc tính, điều A không làm được.",
        "option_texts": {
            "A": "A là khóa ứng viên vì nó xác định B và C.",
            "B": "Bao đóng A+ là {A,B,C,D} vì tính bắc cầu lan tới mọi thuộc tính của quan hệ.",
            "C": "Bao đóng A+ là {A,B,C}, nên A không xác định D và không phải siêu khóa.",
            "D": "D -> A phải đúng vì A không phải khóa ứng viên.",
        },
        "rubrics": {},
    },
    "db-medium-candidate-keys": {
        "prompt": "Quan hệ R(A,B,C,D) có các phụ thuộc hàm AB -> C, C -> D và D -> A. Tập nào đúng chính xác là tập khóa ứng viên?",
        "explanation": "AB+ = {A,B,C,D}, nên AB là khóa và riêng A hay B đều không phải. BC+ = {B,C,D,A}, nên BC là khóa. BD+ = {B,D,A,C}: D -> A thêm A, rồi AB -> C thêm C, nên BD cũng là khóa. AC+ = {A,C,D} và không chứa B, nên AC không phải khóa. Ba khóa đều tối tiểu vì không thuộc tính đơn nào trong mỗi khóa xác định được cả bốn thuộc tính.",
        "option_texts": {
            "A": "{AB}",
            "B": "{AB, BC, BD}",
            "C": "{AB, BC}",
            "D": "{AB, AC}",
        },
        "rubrics": {},
    },
    "db-medium-partial-dependency": {
        "prompt": "Quan hệ enrollment(student_id, course_id, course_title, grade) có khóa chính (student_id, course_id) và phụ thuộc hàm course_id -> course_title. Phát biểu nào xác định đúng vi phạm 2NF và cách sửa?",
        "explanation": "2NF cấm thuộc tính không khóa phụ thuộc vào một phần của khóa ứng viên. course_title là thuộc tính không khóa và phụ thuộc chỉ vào course_id, một tập con thực sự của {student_id, course_id}. Loại bỏ phụ thuộc bộ phận đó cho ra course(course_id, course_title) và enrollment(student_id, course_id, grade). Phụ thuộc vào toàn bộ khóa chính là điều được phép; grade không phải vấn đề.",
        "option_texts": {
            "A": "Không có vi phạm, vì course_title được xác định bởi toàn bộ khóa chính thông qua course_id.",
            "B": "Quan hệ đã đạt 3NF vì mọi thuộc tính không khóa đều phụ thuộc vào khóa chính.",
            "C": "grade phụ thuộc vào toàn bộ khóa, nên grade phải được chuyển sang quan hệ riêng để đạt 2NF.",
            "D": "course_title phụ thuộc vào course_id, một tập con thực sự của khóa phức hợp; chuyển (course_id, course_title) sang quan hệ course và giữ (student_id, course_id, grade) trong enrollment.",
        },
        "rubrics": {},
    },
    "db-medium-3nf-not-bcnf": {
        "prompt": "Quan hệ R(A,B,C) có các phụ thuộc hàm AB -> C và C -> B. Các khóa ứng viên là AB và AC. Phát biểu nào đúng?",
        "explanation": "3NF cho phép phụ thuộc hàm X -> Y khi X là siêu khóa hoặc mọi thuộc tính của Y là thuộc tính khóa. C không phải siêu khóa, nhưng B là một phần của khóa ứng viên AB, nên phụ thuộc này được 3NF cho phép. BCNF không có ngoại lệ thuộc tính khóa, nên C -> B vi phạm BCNF. 2NF liên quan tới phụ thuộc của thuộc tính không khóa vào một phần của khóa phức hợp; B là thuộc tính khóa, và 1NF nói về giá trị nguyên tử, không phải ký hiệu lặp lại.",
        "option_texts": {
            "A": "Quan hệ đạt 3NF nhưng không đạt BCNF vì C -> B có yếu tố xác định không phải siêu khóa và B là thuộc tính khóa.",
            "B": "Quan hệ đạt BCNF vì mọi thuộc tính đều là thuộc tính khóa.",
            "C": "Quan hệ vi phạm 2NF vì C -> B là phụ thuộc bộ phận.",
            "D": "Quan hệ vi phạm 1NF vì B xuất hiện ở cả hai vế của một phụ thuộc hàm.",
        },
        "rubrics": {},
    },
    "db-medium-nonatomic-list": {
        "prompt": "Quan hệ order_item(order_id, items) lưu một giá trị như 'pen,notebook,stapler' trong items. Phát biểu nào đúng?",
        "explanation": "Một giá trị chứa nhiều mặt hàng trong một ô không nguyên tử, nên quan hệ không đạt 1NF bất kể kiểu chuỗi. Cách sửa là một quan hệ con với một dòng cho mỗi cặp đơn hàng-sản phẩm, có khóa gồm cả hai định danh. 2NF và 3NF giả định 1NF và nói về phụ thuộc giữa các thuộc tính, không phải nhiều giá trị ẩn trong một thuộc tính.",
        "option_texts": {
            "A": "Quan hệ vi phạm 1NF; hãy mô hình hóa thành order_line(order_id, product_id, quantity) với khóa chính (order_id, product_id).",
            "B": "1NF được thỏa vì mỗi dòng chứa một giá trị chuỗi trong cột items.",
            "C": "Quan hệ chỉ vi phạm 2NF, vì tên sản phẩm phụ thuộc vào một phần của khóa.",
            "D": "Quan hệ vi phạm 3NF vì tên mặt hàng phụ thuộc bắc cầu vào order_id.",
        },
        "rubrics": {},
    },
    "db-medium-one-to-one-mapping": {
        "prompt": "Mỗi laptop phải được gán cho đúng một nhân viên, và mỗi nhân viên có tối đa một laptop. Sự tham gia của laptop là toàn phần. Ánh xạ nào tránh khóa ngoại duy nhất cho phép NULL?",
        "explanation": "Khóa ngoại thuộc về phía có sự tham gia toàn phần: laptop.employee_id NOT NULL bảo đảm mọi laptop có chủ, và UNIQUE bảo đảm một nhân viên sở hữu tối đa một laptop. Đặt khóa trên employee sẽ khiến nó cho phép NULL với nhân viên không có laptop. Gộp bảng tạo các cột rộng cho phép NULL và trộn lẫn thực thể; bảng liên kết mô hình hóa nhiều-nhiều và sẽ cho phép nhiều chủ sở hữu cho một laptop.",
        "option_texts": {
            "A": "Cấp cho employee một laptop_id UNIQUE cho phép NULL tham chiếu laptop.",
            "B": "Cấp cho laptop một employee_id NOT NULL UNIQUE tham chiếu employee.",
            "C": "Gộp employee và laptop vào một bảng với các cột laptop cho phép NULL.",
            "D": "Tạo bảng liên kết employee_laptop có khóa gồm employee_id và laptop_id.",
        },
        "rubrics": {},
    },
    "db-medium-lossless-common-attribute": {
        "prompt": "Quan hệ R(A,B,C) thỏa B -> A và được phân rã thành R1(A,B) và R2(B,C). Phân rã có bảo toàn kết nối không, và vì sao?",
        "explanation": "Với phân rã nhị phân, phép nối bảo toàn kết nối nếu các thuộc tính chung tạo thành siêu khóa của ít nhất một phía. Thuộc tính chung là B, và B -> A nghĩa là B xác định mọi thuộc tính của R1(A,B), nên B là khóa của R1. Do đó chiếu lên {A,B} và {B,C} rồi nối lại không thể tạo bộ dữ liệu thừa. Bảo toàn thuộc tính không phải cùng thuộc tính với bảo toàn kết nối, và B -> C không liên quan.",
        "option_texts": {
            "A": "Luôn bảo toàn kết nối vì phân rã giữ nguyên cả ba tên thuộc tính.",
            "B": "Chỉ bảo toàn kết nối nếu B -> C cũng đúng.",
            "C": "Mất mát vì A và C nằm ở các quan hệ khác nhau.",
            "D": "Bảo toàn kết nối vì thuộc tính chung B là khóa của R1: B -> A đúng trong R1.",
        },
        "rubrics": {},
    },
    "db-medium-ternary-association": {
        "prompt": "Một nhà cung cấp cung cấp linh kiện cho các dự án. Quantity được ghi cho một nhà cung cấp, linh kiện và dự án cụ thể, và một cặp nhà cung cấp-linh kiện có thể cung cấp cho nhiều dự án. Lược đồ nào biểu diễn đúng quan hệ này?",
        "explanation": "Sự kiện 'nhà cung cấp này đã cung cấp lượng này linh kiện này cho dự án này' phụ thuộc vào cả ba thực thể, nên khóa của quan hệ kết hợp là bộ ba. Bảng nhị phân không thể ghi lượng chỉ có ý nghĩa với bộ ba. Lặp linh kiện theo dự án nhân bản thông tin linh kiện, và mảng che giấu quan hệ đa trị trong một giá trị không nguyên tử.",
        "option_texts": {
            "A": "Quan hệ supply(supplier_id, part_id, project_id, quantity) với khóa chính phức hợp trên ba khóa và khóa ngoại tới từng bảng cha.",
            "B": "Ba quan hệ nhị phân supplier_part, part_project và supplier_project, không quan hệ nào có thể chứa quantity cho bộ ba.",
            "C": "Thêm project_id vào bảng part và lặp lại mỗi dòng part một lần cho mỗi dự án.",
            "D": "Lưu danh sách định danh dự án trong một cột mảng trên supplier.",
        },
        "rubrics": {},
    },
    "db-medium-augmentation": {
        "prompt": "Chỉ cho trước phụ thuộc hàm A -> B, phụ thuộc nào suy ra được bằng tiên đề tăng cường?",
        "explanation": "Tiên đề tăng cường nói rằng nếu X -> Y đúng thì XZ -> YZ đúng với mọi tập thuộc tính Z. Thêm C vào cả hai vế của A -> B cho ra AC -> BC. B -> A sẽ cần một phụ thuộc khác; A -> C không thể suy ra vì C không xuất hiện ở tiền đề; C -> B cũng không được hàm ý.",
        "option_texts": {
            "A": "B -> A",
            "B": "C -> B",
            "C": "A -> C",
            "D": "AC -> BC",
        },
        "rubrics": {},
    },
    "db-medium-3nf-synthesis": {
        "prompt": "Phát biểu nào về tổng hợp 3NF và phân rã BCNF là đúng?",
        "explanation": "Thuật toán tổng hợp 3NF tạo ra phân rã bảo toàn kết nối và bảo toàn phụ thuộc. BCNF chặt hơn và một phân rã BCNF bảo toàn kết nối có thể tách một phụ thuộc ra giữa các quan hệ, nên không bảo đảm bảo toàn phụ thuộc. 3NF cũng cấm phụ thuộc bắc cầu của thuộc tính không khóa vào một yếu tố không phải siêu khóa; BCNF hoàn toàn không có ngoại lệ thuộc tính khóa.",
        "option_texts": {
            "A": "Tổng hợp 3NF có thể bảo toàn kết nối và bảo toàn phụ thuộc, trong khi phân rã BCNF bảo toàn kết nối nhưng có thể làm mất một phụ thuộc hàm.",
            "B": "Mọi phân rã BCNF đều bảo toàn mọi phụ thuộc hàm.",
            "C": "3NF cấm phụ thuộc bộ phận nhưng cố ý cho phép phụ thuộc bắc cầu giữa các thuộc tính không khóa.",
            "D": "BCNF cho phép yếu tố xác định không phải siêu khóa bất cứ khi nào thuộc tính phụ thuộc là thuộc tính khóa.",
        },
        "rubrics": {},
    },
    "db-medium-email-audit": {
        "prompt": "Bảng customer_email(row_id INT PRIMARY KEY, customer_id INT NOT NULL, email TEXT) ghi các dòng liên hệ, và cùng một khách hàng có thể xuất hiện nhiều lần. Trả về email (TEXT), copies (BIGINT: số dòng có email đó) và ids (BIGINT: số định danh khách hàng khác nhau có email đó) cho mọi email không NULL được nhiều hơn một khách hàng khác nhau dùng. Sắp xếp theo copies giảm dần, rồi email tăng dần.",
        "explanation": "Cuộc kiểm toán tìm một email gắn với nhiều khách hàng, bằng chứng rằng email không phải khóa và quan hệ lưu thông tin liên hệ dư thừa. count(*) đếm số dòng, còn count(DISTINCT customer_id) đếm số khách hàng; tập dữ liệu biên có ba dòng nhưng hai khách hàng, nên cần cả hai con số. Email NULL bị loại vì NULL không phải một giá trị được chia sẻ.",
        "option_texts": {},
        "rubrics": {},
    },
    "db-medium-customer-order-totals": {
        "prompt": "Bảng customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL) và bảng orders(order_id INT PRIMARY KEY, customer_id INT, amount NUMERIC(10,2)). Trả về customer_id, name, order_count (BIGINT) và total (NUMERIC, bằng 0 khi không có đơn hàng hoặc mọi amount đều NULL) cho mọi khách hàng, kể cả khách hàng không có đơn hàng. Sắp xếp theo customer_id tăng dần.",
        "explanation": "LEFT JOIN giữ lại khách hàng không có đơn hàng. count(o.order_id) bỏ qua NULL do phép nối tạo ra, nên số đếm là 0, trong khi count(*) sẽ trả về sai là 1. sum bỏ qua amount NULL, và coalesce biến tổng toàn NULL hoặc không có dòng thành 0. Nhóm theo cả customer_id và name giữ truy vấn hợp lệ dù tên không duy nhất.",
        "option_texts": {},
        "rubrics": {},
    },
    "db-medium-library-normalization": {
        "prompt": "Một thư viện lưu các lượt mượn trong loan(member_id, member_name, member_city, book_id, book_title, book_author, loan_date, due_date). Các phụ thuộc hàm là: member_id -> member_name, member_city; book_id -> book_title, book_author; và (member_id, book_id, loan_date) -> due_date. Một thành viên có thể mượn lại cùng một cuốn sách vào ngày khác. (a) Xác định khóa ứng viên. (b) Xác định dạng chuẩn cao nhất và gọi tên từng phụ thuộc ngăn dạng chuẩn kế tiếp. (c) Phân rã quan hệ về 3NF, liệt kê khóa và khóa ngoại. (d) Giải thích vì sao phân rã bảo toàn kết nối và bảo toàn phụ thuộc.",
        "explanation": "Khóa phức hợp phải bao gồm ngày mượn vì cùng một thành viên có thể mượn lại cùng một cuốn sách. Các phụ thuộc bộ phận vào member_id và book_id chỉ giữ quan hệ gốc ở 1NF. Tách member, book và loan loại bỏ chúng; các thuộc tính chung là khóa của quan hệ tham chiếu, nên phân rã bảo toàn kết nối, và mỗi phụ thuộc đều có thể thực thi trong một quan hệ.",
        "option_texts": {},
        "rubrics": {
            "Incomplete": {
                "label": "Chưa đạt",
                "criteria": "Không xác định được khóa ứng viên hoặc khóa thiếu loan_date, và không có lập luận dạng chuẩn hợp lệ; phân rã, nếu có, không dùng được hoặc làm mất sự kiện mượn.",
            },
            "Partial": {
                "label": "Một phần",
                "criteria": "Nêu một khóa có vẻ hợp lý nhưng bỏ sót ít nhất một phụ thuộc bộ phận hoặc gán sai dạng chuẩn cao nhất; phân rã tách được một số nhưng không phải toàn bộ thông tin thực thể, hoặc thiếu khóa và khóa ngoại.",
            },
            "Mostly Complete": {
                "label": "Phần lớn đầy đủ",
                "criteria": "Đúng khóa và xác định được cả hai phụ thuộc bộ phận; phân rã thành member, book và loan với khóa đúng, nhưng lập luận bảo toàn kết nối hoặc bảo toàn phụ thuộc còn thiếu.",
            },
            "Complete": {
                "label": "Đầy đủ",
                "criteria": "Hoàn toàn chính xác: khóa {member_id, book_id, loan_date} với lập luận tối tiểu; dạng cao nhất là 1NF vì các phụ thuộc bộ phận member_id -> thuộc tính member và book_id -> thuộc tính book; phân rã member, book và loan với khóa chính, khóa ngoại đúng; bảo toàn kết nối theo phép thử thuộc tính chung là khóa trên mỗi phép tách; bảo toàn phụ thuộc vì mọi phụ thuộc hàm được thực thi trong một quan hệ duy nhất.",
            },
        },
    },
    "db-medium-optional-self-reference": {
        "prompt": "Một khách hàng có thể được giới thiệu bởi khách hàng khác, nhưng nhiều khách hàng không có người giới thiệu. Lược đồ nào mô hình hóa đúng quan hệ tự tham chiếu tùy chọn này?",
        "explanation": "Sự tham gia tùy chọn cho phép NULL, nên khóa ngoại tự tham chiếu phải cho phép NULL; nút gốc chỉ cần lưu NULL. Tự tham chiếu NOT NULL khiến khách hàng đầu tiên không thể chèn. Lưu tên thay vì khóa làm mất danh tính và tái tạo dị thường cập nhật. Bảng referrer bắt buộc mâu thuẫn với việc nhiều khách hàng không có người giới thiệu.",
        "option_texts": {
            "A": "customer(customer_id PK, name, referred_by_id INT NULL REFERENCES customer(customer_id)).",
            "B": "customer(customer_id PK, name, referred_by_id INT NOT NULL REFERENCES customer).",
            "C": "customer(customer_id PK, name, referred_by_name TEXT).",
            "D": "Một bảng referrer với hai khóa ngoại NOT NULL, trong đó mọi khách hàng đều phải xuất hiện.",
        },
        "rubrics": {},
    },
    "db-medium-residual-transitive": {
        "prompt": "Một quan hệ đạt 2NF nhưng không đạt 3NF vì một thuộc tính không khóa phụ thuộc vào một thuộc tính không khóa khác. Vấn đề vận hành nào vẫn còn?",
        "explanation": "Phụ thuộc bắc cầu chính là dư thừa: sự kiện phụ thuộc được lưu một lần cho mỗi lần xuất hiện của yếu tố xác định, tạo ra dị thường cập nhật, chèn và xóa. Giá trị không nguyên tử là vấn đề 1NF; phụ thuộc vào một phần của khóa phức hợp là vấn đề 2NF đã được loại bỏ; và 2NF không hàm ý 3NF với bất kỳ dạng khóa nào.",
        "option_texts": {
            "A": "Một thuộc tính không khóa chỉ phụ thuộc vào một phần của khóa phức hợp.",
            "B": "Một ô có thể chứa nhiều giá trị, nên quan hệ không nguyên tử.",
            "C": "Sự kiện phụ thuộc bị lặp lại cho mỗi giá trị của yếu tố xác định, nên thay đổi nó có thể cần nhiều cập nhật và dòng bị bỏ sót tạo ra không nhất quán.",
            "D": "Không còn vấn đề gì, vì 2NF và 3NF tương đương khi khóa là phức hợp.",
        },
        "rubrics": {},
    },
}

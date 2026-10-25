"""Vietnamese drafts for the function/text-search specs (fn_easy, fn_hard, fn_medium)."""

DRAFTS = {
    "fn-easy-tsvector": {
        "prompt": "Kiểu PostgreSQL nào lưu một tài liệu đã được phân tích thành các lexeme có thể tìm kiếm cho tìm kiếm toàn văn?",
        "explanation": "to_tsvector phân tích một tài liệu thành các lexeme đã chuẩn hóa và lưu chúng, kèm vị trí, trong một tsvector. tsquery là phía truy vấn của cùng tìm kiếm đó, được xây từ các thuật ngữ tìm kiếm và toán tử. Văn bản thường giữ tài liệu gốc, và jsonb là kiểu tài liệu có cấu trúc, không phải biểu diễn tìm kiếm.",
        "option_texts": {
            "A": "text",
            "B": "tsquery",
            "C": "tsvector",
            "D": "jsonb",
        },
        "rubrics": {},
    },
    "fn-easy-full-text-basics": {
        "prompt": "Giải thích vai trò của tsvector, tsquery và toán tử @@ trong tìm kiếm toàn văn của PostgreSQL. Trình bày cách một tài liệu được chuẩn bị và truy vấn, mô tả chuẩn hóa làm gì với các từ như 'running', và giải thích vì sao vị từ LIKE '%term%' là một sự thay thế kém cho tìm kiếm toàn văn.",
        "explanation": "Câu trả lời phải định nghĩa tsvector là tài liệu đã chuẩn hóa, tsquery là truy vấn đã chuẩn hóa, @@ là phép so khớp, và trình bày việc lấy gốc từ để các dạng biến tố khớp nhau. Nó phải nêu ít nhất hai lý do cụ thể vì sao LIKE với ký tự đại diện ở đầu kém hơn.",
        "option_texts": {},
        "rubrics": {
            "Incomplete": {
                "label": "Chưa đạt",
                "criteria": "Nhầm tsvector với tsquery, hoặc cho rằng tìm kiếm toàn văn so sánh chuỗi con thô; không có ví dụ về chuẩn hóa.",
            },
            "Partial": {
                "label": "Một phần",
                "criteria": "Vai trò đúng nhưng không có ví dụ lấy gốc từ, hoặc chỉ nêu một lý do chống lại LIKE.",
            },
            "Mostly Complete": {
                "label": "Phần lớn đầy đủ",
                "criteria": "Định nghĩa và so khớp đúng với một ví dụ lấy gốc từ, nhưng thiếu lập luận về chỉ mục hoặc về cụm từ/logic boolean.",
            },
            "Complete": {
                "label": "Đầy đủ",
                "criteria": "Hoàn toàn chính xác: tsvector chứa các lexeme đã chuẩn hóa kèm vị trí, tsquery biểu đạt truy vấn, @@ kiểm tra so khớp, việc lấy gốc từ làm 'running' khớp 'run', và LIKE '%term%' thất bại về biến tố, cụm từ/logic boolean và hỗ trợ chỉ mục.",
            },
        },
    },
    "fn-hard-round-negative": {
        "prompt": "round(-1.7) và trunc(-1.7) trả về gì với đối số numeric?",
        "explanation": "round tiến tới số nguyên gần nhất, nên -1.7 thành -2. trunc bỏ phần phân số về phía số 0, nên -1.7 thành -1. Với giá trị âm, hai hàm do đó khác nhau; trunc không phải từ đồng nghĩa của làm tròn.",
        "option_texts": {
            "A": "round trả về -1 và trunc trả về -2.",
            "B": "Cả hai trả về -1, vì giá trị âm được làm tròn về phía số 0.",
            "C": "round trả về -2 và trunc trả về -1.",
            "D": "Cả hai trả về -2, vì trunc làm tròn tới số nguyên gần nhất.",
        },
        "rubrics": {},
    },
    "fn-hard-integer-division": {
        "prompt": "Cả hai cột a và b đều được khai báo INT. Biểu thức a / b được đánh giá với a = 7 và b = 2. Kết quả là gì, và làm thế nào để có 3.5?",
        "explanation": "Phép chia giữa hai số nguyên thực hiện chia nguyên, cắt bỏ phần phân số, nên 7 / 2 là 3. Nâng một toán hạng lên numeric hoặc double precision đổi toán tử thành phép chia có phần phân số và cho 3.5. Không có làm tròn và không có lỗi.",
        "option_texts": {
            "A": "Kết quả là 3.5, vì phép chia luôn tạo ra giá trị numeric.",
            "B": "Kết quả là 3, vì phép chia nguyên cắt bỏ phần phân số; hãy ép một toán hạng, ví dụ a::numeric / b, để có 3.5.",
            "C": "Kết quả là lỗi, vì phép chia không chính xác.",
            "D": "Kết quả là 4, vì phép chia nguyên làm tròn tới số nguyên gần nhất.",
        },
        "rubrics": {},
    },
    "fn-hard-mod-sign": {
        "prompt": "mod(-7, 3) trả về gì trong PostgreSQL?",
        "explanation": "mod trả về phần dư của phép chia và mang dấu của số bị chia, nên -7 = (-3) * 3 + 2 không mô tả kết quả; thương bị cắt là -2, để lại phần dư -1. Đối tác dương mod(7, 3) là 1, đó là lý do phải kiểm tra dấu một cách tường minh khi cần phần dư không âm.",
        "option_texts": {
            "A": "3",
            "B": "1",
            "C": "2",
            "D": "-1",
        },
        "rubrics": {},
    },
    "fn-hard-concat-null": {
        "prompt": "Cho cột middle_name là NULL, 'An' || middle_name || 'Le' và concat('An', middle_name, 'Le') khác nhau thế nào?",
        "explanation": "Toán tử || lan truyền NULL: một toán hạng NULL làm toàn bộ phép nối thành NULL. concat là hàm coi đối số NULL như chuỗi rỗng, nên nó trả về 'AnLe'. Khác biệt này quan trọng khi xây nhãn từ các cột tùy chọn.",
        "option_texts": {
            "A": "Cả hai trả về NULL, vì mọi đầu vào NULL đều lan truyền.",
            "B": "Biểu thức || cho ra NULL, trong khi concat trả về 'AnLe' vì nó bỏ qua các đối số NULL.",
            "C": "Cả hai trả về 'AnLe', vì cả hai toán tử đều bỏ qua NULL.",
            "D": "Biểu thức || trả về 'AnLe', trong khi concat trả về NULL.",
        },
        "rubrics": {},
    },
    "fn-hard-char-length": {
        "prompt": "Với cơ sở dữ liệu UTF-8 và giá trị name = 'é' (một ký tự, hai byte), char_length(name) và octet_length(name) trả về gì?",
        "explanation": "char_length đếm ký tự, nên ký tự có dấu được đếm một lần. octet_length đếm byte trong mã hóa của máy chủ, và trong UTF-8 'é' chiếm hai byte. Không hàm nào đệm hay cắt giá trị.",
        "option_texts": {
            "A": "char_length trả về 2 và octet_length trả về 1.",
            "B": "Cả hai trả về 1, vì độ dài được đo bằng ký tự.",
            "C": "char_length trả về 1 và octet_length trả về 2.",
            "D": "Cả hai trả về 2, vì PostgreSQL lưu chuỗi dưới dạng byte.",
        },
        "rubrics": {},
    },
    "fn-hard-like-escape": {
        "prompt": "Cột code chứa giá trị 'A_B'. Mẫu LIKE nào khớp dấu gạch dưới theo nghĩa đen thay vì coi nó là ký tự đại diện một ký tự?",
        "explanation": "Trong LIKE, _ khớp bất kỳ một ký tự nào, nên 'A_B' cũng khớp 'AXB'. Thoát dấu gạch dưới bằng một ký tự ESCAPE làm nó trở thành ký tự đen. 'A__B' yêu cầu thêm hai ký tự, và SIMILAR TO cũng giữ _ là ký tự đại diện.",
        "option_texts": {
            "A": "code LIKE 'A__B'",
            "B": "code LIKE 'A_B'",
            "C": "code LIKE 'A\\_B' ESCAPE '\\'",
            "D": "code SIMILAR TO 'A_B'",
        },
        "rubrics": {},
    },
    "fn-hard-like-is-whole-string": {
        "prompt": "Phát biểu nào về so khớp mẫu là đúng?",
        "explanation": "LIKE coi mẫu là so khớp toàn chuỗi trừ khi các ký tự đại diện % mở rộng nó, nên 'Post' không khớp 'PostgreSQL'. Toán tử ~ khớp một chuỗi con ở bất kỳ đâu trừ khi mẫu được neo bằng ^ và $. ILIKE là đối tác không phân biệt hoa thường của LIKE.",
        "option_texts": {
            "A": "LIKE tìm mẫu ở bất kỳ đâu trong chuỗi, chính xác như ~.",
            "B": "LIKE phải khớp toàn bộ chuỗi, nên 'PostgreSQL' LIKE 'Post' là sai, trong khi toán tử biểu thức chính quy ~ tìm so khớp ở bất kỳ đâu trừ khi được neo.",
            "C": "Toán tử ~ luôn yêu cầu neo ở cả hai đầu.",
            "D": "ILIKE phân biệt hoa thường và LIKE không phân biệt hoa thường.",
        },
        "rubrics": {},
    },
    "fn-hard-date-plus-integer": {
        "prompt": "Cho today = DATE '2024-02-28', today + 1 là gì?",
        "explanation": "Cộng một số nguyên vào một date sẽ tiến ngày đó thêm đúng số ngày, và các quy tắc lịch được áp dụng, nên 2024-02-28 cộng một ngày là 2024-02-29 vì 2024 là năm nhuận. Cộng một interval cũng hoạt động, nhưng số nguyên không được hiểu là số giây.",
        "option_texts": {
            "A": "DATE '2024-02-29', vì cộng một số nguyên vào date sẽ tiến nó thêm đúng số ngày đó và năm này là năm nhuận.",
            "B": "Lỗi, vì không thể cộng một số nguyên vào date.",
            "C": "TIMESTAMP '2024-02-28 00:00:01', vì số nguyên được đọc là số giây.",
            "D": "DATE '2024-03-01', vì tháng Hai luôn có 28 ngày.",
        },
        "rubrics": {},
    },
    "fn-medium-plainto-vs-phraseto": {
        "prompt": "Với văn bản 'database systems', phát biểu nào đối chiếu đúng plainto_tsquery và phraseto_tsquery?",
        "explanation": "plainto_tsquery biến đầu vào thành các thuật ngữ kết hợp bằng AND (&), nên mỗi thuật ngữ có thể xuất hiện ở bất kỳ đâu. phraseto_tsquery kết hợp các thuật ngữ bằng toán tử cụm từ <->, yêu cầu chúng liền nhau và theo đúng thứ tự đã cho. Cả hai đều đưa từ qua từ điển tìm kiếm văn bản, nên việc lấy gốc từ được áp dụng ở cả hai.",
        "option_texts": {
            "A": "Cả hai tạo ra truy vấn giống hệt nhau; chúng chỉ khác từ điển được dùng.",
            "B": "plainto_tsquery yêu cầu các thuật ngữ liền nhau, trong khi phraseto_tsquery chấp nhận chúng theo bất kỳ thứ tự nào.",
            "C": "plainto_tsquery tạo ra truy vấn yêu cầu cả hai thuật ngữ ở bất kỳ đâu trong tài liệu, trong khi phraseto_tsquery yêu cầu chúng liền nhau và đúng thứ tự.",
            "D": "phraseto_tsquery vô hiệu hóa việc lấy gốc từ, trong khi plainto_tsquery áp dụng nó.",
        },
        "rubrics": {},
    },
    "fn-medium-tsquery-operators": {
        "prompt": "Trong một tsquery, biểu thức 'alpha <-> beta' yêu cầu gì?",
        "explanation": "Toán tử <-> là toán tử cụm từ: nó yêu cầu các toán hạng liền nhau và theo thứ tự được chỉ định. Toán tử & nghĩa là cả hai ở bất kỳ đâu, | nghĩa là một trong hai, và ! phủ định. Sự gần nhau theo câu, không phải liền kề nghiêm ngặt, sẽ được biểu đạt bằng toán tử khoảng cách như <N>.",
        "option_texts": {
            "A": "Lexeme alpha theo ngay sau beta trong tài liệu.",
            "B": "Lexeme alpha và beta ở bất kỳ đâu trong tài liệu.",
            "C": "Alpha hoặc beta, nhưng không phải cả hai.",
            "D": "alpha trong cùng câu với beta, theo bất kỳ thứ tự nào.",
        },
        "rubrics": {},
    },
    "fn-medium-websearch-to-tsquery": {
        "prompt": "websearch_to_tsquery('english', 'database or network -nosql') tạo ra gì?",
        "explanation": "websearch_to_tsquery phân tích đầu vào thành 'databas' | 'network' & !'nosql' (các thuật ngữ được lấy gốc). Dấu trừ chỉ phủ định thuật ngữ theo sau, và & kết dính chặt hơn |, nên truy vấn có nghĩa là database OR (network AND NOT nosql). Một tài liệu chứa database và nosql nhưng không có network vẫn khớp. Hàm không bao giờ báo lỗi với đầu vào như vậy, đó là lý do nó phù hợp với văn bản thô của người dùng.",
        "option_texts": {
            "A": "Một truy vấn chỉ khớp cụm từ đen 'database or network -nosql'.",
            "B": "Một truy vấn tương đương database OR (network AND NOT nosql); dấu trừ chỉ phủ định nosql, và AND kết dính chặt hơn OR.",
            "C": "Lỗi cú pháp, vì websearch_to_tsquery không chấp nhận từ or.",
            "D": "Một truy vấn yêu cầu database AND network AND nosql.",
        },
        "rubrics": {},
    },
}

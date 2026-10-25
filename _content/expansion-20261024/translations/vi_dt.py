"""Vietnamese drafts for the data-type specs (dt_easy, dt_hard, dt_medium)."""

DRAFTS = {
    "dt-easy-json-carrier": {
        "prompt": "Thiết lập tạo shipment(order_id INT PRIMARY KEY, payload JSONB NOT NULL) và chèn các đối tượng JSON. Trả về order_id và giá trị carrier được trích từ payload dưới dạng văn bản, với bí danh carrier, sắp xếp theo order_id tăng dần. Các dòng có đối tượng không có khóa carrier, hoặc có giá trị carrier là JSON null, phải hiển thị NULL.",
        "explanation": "Toán tử ->> trích một trường của đối tượng dưới dạng văn bản, nên chuỗi JSON \"dhl\" trở thành văn bản SQL dhl. Một khóa bị thiếu và một JSON null đều cho ra SQL NULL, đó là lý do đơn hàng 3 và dòng JSON-null báo NULL thay vì lỗi hay chuỗi rỗng. Dùng -> thay vào đó sẽ trả về giá trị JSON chứ không phải văn bản.",
        "option_texts": {},
        "rubrics": {},
    },
    "dt-easy-range-overlap": {
        "prompt": "Thiết lập tạo booking(room_id INT PRIMARY KEY, period INT4RANGE NOT NULL) với các khoảng số nguyên nửa mở. Trả về room_id cho mọi lượt đặt có period chồng lấn với int4range(4, 6), sắp xếp theo room_id tăng dần.",
        "explanation": "Toán tử && kiểm tra xem hai khoảng có điểm chung nào không. Vì các khoảng là nửa mở, [1,5) và [5,9) đều chứa các điểm nằm trong [4,6), trong khi [10,12) thì không. Trong tập dữ liệu biên, [1,4) và [6,9) chỉ kề với khoảng kiểm tra và không chia sẻ điểm nào với nó, nên kết quả rỗng.",
        "option_texts": {},
        "rubrics": {},
    },
    "dt-easy-domain-collation": {
        "prompt": "Giải thích domain trong PostgreSQL là gì và collation kiểm soát điều gì. Với domain, mô tả cách một ràng buộc gắn với domain được thực thi trên mọi cột sử dụng nó. Với collation, giải thích cách lựa chọn giữa collation C và collation nhận biết ngôn ngữ có thể thay đổi kết quả ORDER BY và các phép so sánh.",
        "explanation": "Câu trả lời phải định nghĩa domain là một kiểu có tên với các ràng buộc tùy chọn, giải thích rằng các quy tắc CHECK/NOT NULL của nó áp dụng cho mọi cột thuộc domain đó, và định nghĩa collation là các quy tắc so sánh và sắp xếp văn bản. Nó phải nêu ít nhất một hệ quả cụ thể, chẳng hạn một giá trị ngoài phạm vi bị từ chối hoặc kết quả ORDER BY khác nhau giữa C và một collation nhận biết ngôn ngữ.",
        "option_texts": {},
        "rubrics": {
            "Incomplete": {
                "label": "Chưa đạt",
                "criteria": "Không nhận diện được ý tưởng domain-là-kiểu lẫn collation-là-quy-tắc-so-sánh; hoặc mô tả sai cả hai.",
            },
            "Partial": {
                "label": "Một phần",
                "criteria": "Định nghĩa đúng một trong hai khái niệm; ví dụ giải thích ràng buộc domain nhưng chỉ coi collation là mã hóa ký tự, hoặc ngược lại.",
            },
            "Mostly Complete": {
                "label": "Phần lớn đầy đủ",
                "criteria": "Định nghĩa đúng cả hai khái niệm và nêu một hệ quả cụ thể, nhưng bỏ sót việc tái sử dụng domain trên nhiều cột hoặc ảnh hưởng của collation lên hành vi sắp xếp/so bằng.",
            },
            "Complete": {
                "label": "Đầy đủ",
                "criteria": "Định nghĩa domain là kiểu có tên tái sử dụng mà các ràng buộc của nó được thực thi trong mọi cột sử dụng nó, và định nghĩa collation là quy tắc so sánh/sắp xếp; nêu hệ quả cụ thể cho cả hai, bao gồm khác biệt ORDER BY hoặc so bằng giữa C và ngôn ngữ.",
            },
        },
    },
    "dt-hard-numeric-vs-float-round": {
        "prompt": "Trong PostgreSQL, round(2.5::numeric) và round(2.5::float8) trả về gì?",
        "explanation": "numeric là số thập phân chính xác và làm tròn điểm giữa về phía xa số 0, nên 2.5 thành 3. float8 tuân theo quy tắc dấu phẩy động nhị phân làm tròn điểm giữa về số nguyên chẵn gần nhất, nên 2.5 thành 2. Đây là khác biệt ngữ nghĩa thực sự giữa hai họ kiểu số, không phải hiện tượng hiển thị.",
        "option_texts": {
            "A": "3 cho cả hai, vì round luôn làm tròn điểm giữa về phía xa số 0.",
            "B": "3 cho numeric và 2 cho float8, vì numeric làm tròn điểm giữa về phía xa số 0 trong khi float8 làm tròn điểm giữa về số nguyên chẵn gần nhất.",
            "C": "2 cho cả hai, vì round luôn làm tròn điểm giữa về số chẵn.",
            "D": "2 cho numeric và 3 cho float8, vì float8 mang độ chính xác cao hơn.",
        },
        "rubrics": {},
    },
    "dt-hard-date-difference": {
        "prompt": "Biểu thức DATE '2024-03-01' - DATE '2024-02-01' trả về gì?",
        "explanation": "Toán tử date - date trả về số ngày dưới dạng số nguyên, và 2024 là năm nhuận nên tháng Hai có 29 ngày. Ngược lại, trừ hai timestamp trả về một interval. Không phép trừ nào tạo ra timestamp.",
        "option_texts": {
            "A": "Số nguyên 28, vì tháng Hai 2024 được tính là 28 ngày.",
            "B": "Interval '29 days', vì phép toán ngày luôn trả về interval.",
            "C": "Số nguyên 29, vì trừ hai date trả về số ngày.",
            "D": "Timestamp 2024-02-29 00:00:00, vì ngày muộn hơn bị dịch lùi.",
        },
        "rubrics": {},
    },
    "dt-hard-bool-aggregate": {
        "prompt": "Bảng flag(v BOOLEAN) chứa ba dòng TRUE, NULL và TRUE. SELECT bool_and(v) và SELECT bool_or(v) trả về gì?",
        "explanation": "Giống các hàm tổng hợp thông thường khác, bool_and và bool_or bỏ qua đầu vào NULL thay vì lan truyền chúng. Các giá trị còn lại đều là TRUE, nên bool_and là TRUE và bool_or là TRUE. Nếu chỉ có đầu vào NULL thì cả hai trả về NULL, nhưng đó không phải tập dữ liệu này.",
        "option_texts": {
            "A": "bool_and trả về FALSE và bool_or trả về TRUE, vì NULL được coi là FALSE.",
            "B": "bool_and trả về NULL và bool_or trả về TRUE, vì bất kỳ đầu vào NULL nào làm phép tích lũy and trở nên không xác định.",
            "C": "Cả hai trả về NULL, vì NULL lan truyền qua các hàm tổng hợp.",
            "D": "Cả hai trả về TRUE, vì các hàm tổng hợp boolean bỏ qua đầu vào NULL.",
        },
        "rubrics": {},
    },
    "dt-hard-char-concatenation": {
        "prompt": "Với biểu thức 'ab'::char(4) || 'cd', PostgreSQL trả về gì?",
        "explanation": "Giá trị character(4) được đệm khoảng trắng trong lưu trữ, nhưng các khoảng trắng ở cuối bị gỡ bỏ khi giá trị được chuyển thành text cho toán tử nối, nên 'ab' trở thành 'ab' và kết quả là 'abcd'. Phần đệm là thuộc tính lưu trữ và so sánh của character(n), không phải nội dung mà toán tử mang vào kết quả.",
        "option_texts": {
            "A": "Lỗi, vì không thể nối một giá trị character(4) với một literal không định kiểu.",
            "B": "'ab  cd', vì các khoảng trắng đệm đã lưu được giữ nguyên.",
            "C": "'abcd', vì phần đệm ở cuối của giá trị character không thuộc văn bản được nối.",
            "D": "'abcd    ', vì kết quả được đệm tới độ rộng khai báo kết hợp.",
        },
        "rubrics": {},
    },
    "dt-hard-domain-constraints": {
        "prompt": "Một domain được định nghĩa là CREATE DOMAIN positive_int AS integer CHECK (VALUE > 0). Phát biểu nào về việc dùng nó là đúng?",
        "explanation": "Domain đóng gói một kiểu cơ sở cùng các ràng buộc, và các ràng buộc đó được thực thi bất cứ khi nào một giá trị được lưu trong bất kỳ cột nào của domain đó, nên 0 và số âm bị từ chối ở mọi nơi domain được dùng. Ép một giá trị domain về kiểu cơ sở tạo ra giá trị cơ sở không ràng buộc, trong khi ép một giá trị cơ sở sang domain sẽ áp dụng các ràng buộc của domain.",
        "option_texts": {
            "A": "Ép một số nguyên thường sang positive_int bỏ qua CHECK, vì phép ép không chạy ràng buộc domain.",
            "B": "CHECK chỉ được sao chép vào cột đầu tiên dùng domain; các cột sau nhận số nguyên thường.",
            "C": "CHECK được đánh giá một lần khi domain được tạo và không bao giờ nữa, nên các lệnh chèn sau đó không bị kiểm tra.",
            "D": "Mọi cột khai báo với positive_int từ chối giá trị 0 và số âm, và ép một giá trị positive_int sang integer sẽ gỡ bỏ ràng buộc domain.",
        },
        "rubrics": {},
    },
    "dt-hard-inet-containment": {
        "prompt": "'192.168.1.5'::inet << '192.168.1.0/24'::inet và '192.168.1.0/24'::inet >> '192.168.1.5'::inet trả về gì?",
        "explanation": "Kiểu inet lưu một địa chỉ, tùy chọn kèm netmask. Toán tử << hỏi liệu địa chỉ hoặc mạng bên trái có bị chứa nghiêm ngặt bởi bên phải hay không, nên một địa chỉ host (/32) nằm trong 192.168.1.0/24 thỏa điều kiện; >> hỏi câu hỏi đối xứng và cũng đúng ở đây. Các netmask giống hệt nhau làm << sai, vì việc chứa là nghiêm ngặt. Cả hai toán tử trả về boolean.",
        "option_texts": {
            "A": "Kết quả thứ nhất là TRUE và kết quả thứ hai là FALSE, vì >> chỉ so sánh các độ dài netmask giống hệt nhau.",
            "B": "Cả hai trả về FALSE, vì một địa chỉ không có netmask không thể so sánh với một mạng.",
            "C": "Cả hai trả về TRUE: << kiểm tra xem địa chỉ hoặc mạng bên trái có bị chứa nghiêm ngặt bởi bên phải hay không, và >> là phép kiểm tra ngược lại.",
            "D": "Cả hai trả về địa chỉ host 192.168.1.5, vì các toán tử inet trả về địa chỉ chứ không phải boolean.",
        },
        "rubrics": {},
    },
    "dt-medium-boolean-input": {
        "prompt": "Một giá trị văn bản được ép sang boolean. Chuỗi đầu vào nào trong số này KHÔNG được PostgreSQL chấp nhận làm giá trị boolean?",
        "explanation": "PostgreSQL chấp nhận TRUE/FALSE, các cách viết t/f, true/false, y/n, yes/no, on/off và 1/0, cùng các tiền tố duy nhất của true và false. 'enable' không thuộc các dạng này và không quy tắc tiền tố nào làm nó hợp lệ, nên phép ép thất bại. Ba phương án còn lại là các từ đồng nghĩa được ghi nhận cho true.",
        "option_texts": {
            "A": "'1'",
            "B": "'yes'",
            "C": "'on'",
            "D": "'enable'",
        },
        "rubrics": {},
    },
    "dt-medium-char-padding": {
        "prompt": "Phát biểu nào mô tả đúng cách character(n) và character varying(n) lưu trữ và so sánh giá trị?",
        "explanation": "Các giá trị kiểu character(n) được đệm khoảng trắng vật lý tới độ rộng khai báo; các khoảng trắng ở cuối bị gỡ bỏ khi giá trị được chuyển sang kiểu chuỗi khác, và các phép so sánh bỏ qua chúng, nên các độ rộng khai báo khác nhau có thể so bằng nhau. character varying(n) lưu giá trị không đệm và chỉ thực thi độ dài tối đa. Các phép so sánh không bao giờ gây lỗi chỉ vì độ dài khai báo khác nhau.",
        "option_texts": {
            "A": "character(n) lưu chính xác các ký tự được cung cấp và chỉ đệm khi giá trị được hiển thị.",
            "B": "character(n) được đệm khoảng trắng tới n ký tự, nhưng khoảng trắng ở cuối không có ý nghĩa trong so sánh, nên 'ab'::char(4) = 'ab'::char(2) là đúng.",
            "C": "character varying(n) đệm khoảng trắng mọi giá trị tới n, trong khi character(n) lưu độ dài đầu vào chính xác.",
            "D": "So sánh các giá trị character có độ dài khai báo khác nhau gây lỗi thay vì trả về boolean.",
        },
        "rubrics": {},
    },
}

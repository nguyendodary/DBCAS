"""Vietnamese drafts for the schema and file-operation specs (sf)."""

DRAFTS = {
    "sf-easy-alter-add-column": {
        "prompt": "Một bảng đã chứa các dòng sản xuất và cần thêm một cột mới cho phép NULL mà không mất dữ liệu. Câu lệnh nào làm được điều đó?",
        "explanation": "ALTER TABLE ... ADD COLUMN mở rộng bảng hiện có tại chỗ; cột mới mặc định cho phép NULL và các dòng hiện có nhận NULL. CREATE TABLE sẽ cố tạo một bảng thứ hai, UPDATE không thể thêm cột, và INSERT thêm dòng chứ không thêm cột.",
        "option_texts": {
            "A": "ALTER TABLE customer ADD COLUMN loyalty_code TEXT;",
            "B": "CREATE TABLE customer ADD loyalty_code TEXT;",
            "C": "UPDATE customer SET loyalty_code = NULL;",
            "D": "INSERT INTO customer (loyalty_code) VALUES (NULL);",
        },
        "rubrics": {},
    },
    "sf-easy-delete-selected-rows": {
        "prompt": "Câu lệnh nào xóa các dòng được chọn khỏi một bảng trong khi giữ nguyên định nghĩa bảng và mọi dòng khác?",
        "explanation": "DELETE xóa các dòng thỏa mệnh đề WHERE và giữ nguyên cấu trúc bảng cùng các dòng còn lại. DROP TABLE xóa chính bảng, ALTER ... DROP COLUMN xóa một cột khỏi mọi dòng, và TRUNCATE làm rỗng toàn bộ bảng vì nó không nhận mệnh đề WHERE.",
        "option_texts": {
            "A": "ALTER TABLE customer DROP COLUMN city;",
            "B": "DROP TABLE customer;",
            "C": "DELETE FROM customer WHERE city = 'Hue';",
            "D": "TRUNCATE TABLE customer;",
        },
        "rubrics": {},
    },
    "sf-easy-update-expression": {
        "prompt": "Câu lệnh UPDATE product SET price = price * 2; được thực thi trên một bảng mà mọi dòng đều không NULL. Hiệu ứng là gì?",
        "explanation": "Không có mệnh đề WHERE, UPDATE áp dụng cho mọi dòng, và biểu thức bên phải được đánh giá từ giá trị hiện tại của dòng, nên giá mới gấp đôi giá cũ. UPDATE không bao giờ thêm cột, và việc tham chiếu cột đang được gán là hợp lệ.",
        "option_texts": {
            "A": "Giá của mọi dòng được nhân đôi, dùng giá trị hiện tại của từng dòng.",
            "B": "Chỉ giá của dòng đầu tiên được nhân đôi.",
            "C": "Câu lệnh thất bại vì một cột không thể xuất hiện ở cả hai vế của phép gán.",
            "D": "Một cột mới tên price * 2 được thêm vào bảng.",
        },
        "rubrics": {},
    },
    "sf-easy-primary-key-guarantees": {
        "prompt": "Ràng buộc PRIMARY KEY trên một cột bảo đảm điều gì?",
        "explanation": "Khóa chính kết hợp NOT NULL với tính duy nhất và được hỗ trợ bởi một chỉ mục duy nhất. Cho phép nhiều NULL lặp lại là hành vi của ràng buộc UNIQUE thường trong PostgreSQL, không phải của khóa chính. Thứ tự dòng vật lý không bao giờ được bất kỳ ràng buộc nào bảo đảm.",
        "option_texts": {
            "A": "Các giá trị được sắp xếp vật lý trong bảng.",
            "B": "Mọi giá trị là duy nhất nhưng NULL được phép nhiều lần.",
            "C": "Mọi giá trị đều không NULL nhưng cho phép trùng lặp.",
            "D": "Mọi giá trị đều không NULL và duy nhất, và một chỉ mục duy nhất hỗ trợ ràng buộc.",
        },
        "rubrics": {},
    },
    "sf-easy-insert-omitted-column": {
        "prompt": "Bảng note(note_id INT PRIMARY KEY, body TEXT, pinned BOOLEAN) không có giá trị mặc định. Câu lệnh INSERT INTO note (note_id, body) VALUES (1, 'hello'); được thực thi. Giá trị nào được lưu trong pinned?",
        "explanation": "Các cột bị bỏ khỏi danh sách cột của INSERT nhận giá trị mặc định đã khai báo; không có mặc định thì giá trị là NULL. PostgreSQL không có mặc định FALSE ngầm cho boolean, không bắt buộc liệt kê mọi cột, và không xảy ra chuyển đổi văn bản ngầm.",
        "option_texts": {
            "A": "Một chuỗi rỗng, vì PostgreSQL chuyển các giá trị thiếu thành văn bản.",
            "B": "FALSE, vì cột boolean mặc định là false.",
            "C": "Một lỗi, vì mọi cột phải được liệt kê trong INSERT.",
            "D": "NULL, vì cột bị bỏ khỏi danh sách cột và không có giá trị mặc định.",
        },
        "rubrics": {},
    },
    "sf-easy-drop-column": {
        "prompt": "Câu lệnh ALTER TABLE customer DROP COLUMN nickname; được thực thi. Kết quả là gì?",
        "explanation": "DROP COLUMN xóa định nghĩa cột và các giá trị đã lưu của nó khỏi mọi dòng; bảng và các cột khác vẫn tồn tại. Làm rỗng một cột mà không xóa nó là UPDATE ... SET col = NULL, không phải DROP COLUMN, và xóa một bảng là DROP TABLE.",
        "option_texts": {
            "A": "Cột và dữ liệu nó chứa bị xóa; các cột khác và các dòng còn lại vẫn giữ nguyên.",
            "B": "Cột bị làm rỗng nhưng vẫn tồn tại với các giá trị NULL.",
            "C": "Chỉ các giá trị trong cột bị xóa; định nghĩa cột vẫn còn.",
            "D": "Toàn bộ bảng bị xóa.",
        },
        "rubrics": {},
    },
    "sf-easy-check-constraint": {
        "prompt": "Bảng order_line(quantity INT) được tạo với ràng buộc CHECK (quantity > 0). Điều gì xảy ra khi một INSERT cung cấp quantity = 0?",
        "explanation": "Ràng buộc CHECK phải đánh giá là TRUE hoặc NULL cho mọi dòng được chèn hoặc cập nhật; dòng mà nó đánh giá là FALSE sẽ bị từ chối và câu lệnh thất bại. PostgreSQL không bao giờ tự sửa giá trị hay hạ mức vi phạm thành cảnh báo.",
        "option_texts": {
            "A": "Dòng được lưu với quantity được đặt thành NULL.",
            "B": "Dòng được lưu với quantity được đặt thành 1.",
            "C": "Dòng được lưu và một cảnh báo được ghi log.",
            "D": "Câu lệnh bị từ chối vì dòng vi phạm ràng buộc kiểm tra.",
        },
        "rubrics": {},
    },
    "sf-easy-multi-row-insert": {
        "prompt": "Câu lệnh nào chèn hai dòng vào tag(tag_id, label) trong một lệnh duy nhất?",
        "explanation": "Danh sách VALUES nhiều dòng là cách tiêu chuẩn để chèn nhiều dòng trong một câu lệnh. Lặp lại từ khóa VALUES là lỗi cú pháp, SELECT 1, 'sql' AND 2, 'db' không phải cách tạo dòng hợp lệ, và phương án cuối dùng hai câu lệnh thay vì một lệnh.",
        "option_texts": {
            "A": "INSERT INTO tag (tag_id, label) VALUES (1, 'sql') VALUES (2, 'db');",
            "B": "INSERT INTO tag (tag_id, label) VALUES (1, 'sql'), (2, 'db');",
            "C": "INSERT INTO tag (tag_id, label) SELECT 1, 'sql' AND 2, 'db';",
            "D": "INSERT INTO tag VALUES (1, 'sql'); INSERT INTO tag VALUES (2, 'db');",
        },
        "rubrics": {},
    },
    "sf-easy-view-rows": {
        "prompt": "Phần thiết lập tạo bảng product(product_id INT PRIMARY KEY, name TEXT NOT NULL, price INT) và sau đó là view cheap_product, với truy vấn được lưu chọn product_id, name và price từ product nơi price < 100. Các dòng được chèn sau khi view được tạo. Trả về product_id, name và price cho các dòng mà view phơi ra, sắp xếp theo product_id tăng dần.",
        "explanation": "View lưu một truy vấn, không phải một bản sao dữ liệu, và các dòng được chèn sau CREATE VIEW vẫn hiển thị khi truy vấn view: mệnh đề WHERE price < 100 giữ sản phẩm 1 và 3, loại 2 và 4. Tập dữ liệu rỗng trả về không dòng, đúng như mong đợi.",
        "option_texts": {},
        "rubrics": {},
    },
    "sf-easy-identity-defaults": {
        "prompt": "Phần thiết lập tạo bảng ticket(ticket_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, subject TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open') và chèn các dòng, đôi khi nêu status và đôi khi bỏ qua. Trả về ticket_id, subject và status cho mọi dòng, sắp xếp theo ticket_id tăng dần.",
        "explanation": "Cột identity tự động điền ticket_id, nên các câu lệnh INSERT không bao giờ cung cấp nó và các giá trị được tạo bắt đầu từ 1. Bỏ qua status sẽ áp dụng giá trị mặc định 'open' đã khai báo, trong khi một giá trị tường minh như 'closed' được lưu đúng như đã cho. Vì vậy tập dữ liệu thứ hai đối chiếu các giá trị status mặc định và tường minh.",
        "option_texts": {},
        "rubrics": {},
    },
    "sf-hard-merge-actions": {
        "prompt": "PostgreSQL 17 thực thi MERGE INTO stock s USING delivery d ON s.item = d.item WHEN MATCHED THEN UPDATE SET qty = s.qty + d.qty WHEN NOT MATCHED THEN INSERT (item, qty) VALUES (d.item, d.qty). Câu lệnh bảo đảm điều gì?",
        "explanation": "MERGE đánh giá nguồn so với đích và áp dụng mệnh đề WHEN khớp đầu tiên cho mỗi dòng đích, nên một dòng đích bị sửa nhiều nhất một lần; nếu nhiều dòng nguồn khớp cùng một dòng đích, PostgreSQL 17 báo lỗi cardinality thay vì cập nhật hai lần. WHEN NOT MATCHED tham chiếu các dòng nguồn không có dòng đích khớp và chèn chúng; thứ tự mệnh đề không tạo ra lượt thứ hai. MERGE được giới thiệu trong PostgreSQL 15 và mở rộng trong 17, nên câu lệnh hợp lệ.",
        "option_texts": {
            "A": "Mỗi dòng đích bị thay đổi nhiều nhất một lần; các dòng khớp được cập nhật và các dòng nguồn không khớp được chèn.",
            "B": "Một dòng đích khớp với nhiều dòng nguồn được cập nhật một lần cho mỗi dòng nguồn.",
            "C": "Mệnh đề WHEN NOT MATCHED chỉ chèn các dòng nguồn không khớp với dòng đích nào sau khi các cập nhật chạy.",
            "D": "MERGE không có trong PostgreSQL 17 và câu lệnh không phân tích được.",
        },
        "rubrics": {},
    },
    "sf-hard-on-conflict-expression-index": {
        "prompt": "Bảng account có UNIQUE (lower(email)) là chỉ mục duy nhất duy nhất trên email. Câu lệnh INSERT INTO account (email) VALUES ('a@x.edu') ON CONFLICT (email) DO NOTHING; được thực thi. Điều gì xảy ra?",
        "explanation": "Việc suy luận cho ON CONFLICT (danh sách cột) tìm một chỉ mục duy nhất có các biểu thức khớp chính xác với các biểu thức được liệt kê. Một chỉ mục trên lower(email) không khớp với biểu thức trần email, nên suy luận arbiter thất bại và câu lệnh báo lỗi. Nêu biểu thức làm arbiter trở nên tường minh; chỉ mục biểu thức không phải ràng buộc, nên ON CONFLICT ON CONSTRAINT không thể nêu nó.",
        "option_texts": {
            "A": "Nó thất bại, vì ON CONFLICT (email) không tìm thấy chỉ mục duy nhất trên cột trần; đích xung đột phải lặp lại chính xác biểu thức của chỉ mục, như ON CONFLICT (lower(email)).",
            "B": "Nó thành công và bỏ qua dòng, vì PostgreSQL khớp với bất kỳ chỉ mục duy nhất nào liên quan đến email.",
            "C": "Nó thành công và chèn dòng, vì chỉ mục biểu thức bị ON CONFLICT bỏ qua.",
            "D": "Nó chỉ thành công khi giá trị email không có chữ hoa.",
        },
        "rubrics": {},
    },
    "sf-hard-on-conflict-duplicate-source": {
        "prompt": "INSERT INTO account (account_id, email) SELECT account_id, email FROM staging ON CONFLICT (account_id) DO UPDATE SET email = EXCLUDED.email; được thực thi, và staging chứa cùng một account_id hai lần. Điều gì xảy ra?",
        "explanation": "ON CONFLICT DO UPDATE yêu cầu mỗi dòng đích bị tác động nhiều nhất một lần trong mỗi câu lệnh; một khóa trùng trong tập kết quả đầu vào sẽ tác động cùng một dòng hai lần, nên PostgreSQL báo lỗi. Cách khắc phục là loại trùng nguồn trước khi chèn. Không có người thắng đầu/cuối được xác định và không có việc gộp tự động.",
        "option_texts": {
            "A": "Câu lệnh thất bại: ON CONFLICT DO UPDATE không thể tác động lên cùng một dòng lần thứ hai trong một lệnh.",
            "B": "Câu lệnh thành công và dòng staging cuối cùng thắng.",
            "C": "Câu lệnh thành công và dòng staging đầu tiên thắng.",
            "D": "Câu lệnh thành công và cả hai dòng staging được gộp thành một giá trị bằng phép nối chuỗi.",
        },
        "rubrics": {},
    },
    "sf-hard-deferrable-fk": {
        "prompt": "Bảng line tham chiếu header với một ràng buộc được khai báo DEFERRABLE INITIALLY DEFERRED. Trong một giao dịch, một dòng line được chèn trước dòng header của nó. Điều gì xảy ra?",
        "explanation": "Ràng buộc được khai báo DEFERRABLE INITIALLY DEFERRED được kiểm tra ở cuối giao dịch thay vì sau mỗi câu lệnh, nên header tạm thời thiếu là chấp nhận được miễn là header được chèn trước COMMIT. Nó vẫn được thực thi tại commit, nên phương án C sai. Các ràng buộc NOT DEFERRABLE, mặc định, được kiểm tra ngay lập tức.",
        "option_texts": {
            "A": "Cả hai câu lệnh thành công; khóa ngoại được kiểm tra tại COMMIT, lúc đó header đã tồn tại.",
            "B": "Việc chèn line thất bại ngay lập tức, vì khóa ngoại luôn được kiểm tra theo từng câu lệnh.",
            "C": "Cả hai câu lệnh thành công ngay cả tại COMMIT, vì DEFERRABLE vô hiệu hóa ràng buộc vĩnh viễn.",
            "D": "Việc chèn line thất bại tại COMMIT, vì việc chèn header không thể được hoàn tác.",
        },
        "rubrics": {},
    },
    "sf-hard-generated-stored": {
        "prompt": "Bảng invoice(id INT, qty INT, unit_price INT, total INT GENERATED ALWAYS AS (qty * unit_price) STORED) được tạo. Điều gì xảy ra khi một INSERT cung cấp giá trị cho total?",
        "explanation": "Một cột sinh được lưu được cơ sở dữ liệu duy trì: giá trị của nó được tính khi chèn và mỗi khi các cột được tham chiếu cập nhật, và chỉ DEFAULT mới có thể được ghi cho nó. Cung cấp một giá trị bằng chữ là lỗi, vì cơ sở dữ liệu sẽ không chấp nhận một giá trị mà nó không thể kiểm chứng với biểu thức.",
        "option_texts": {
            "A": "Giá trị được cung cấp được lưu và biểu thức bị bỏ qua.",
            "B": "Câu lệnh bị từ chối; một cột sinh được lưu được tính từ dòng và không thể ghi trực tiếp.",
            "C": "Giá trị được cung cấp được lưu, và biểu thức chỉ được áp dụng khi UPDATE.",
            "D": "Giá trị được thay thế một cách âm thầm bằng NULL.",
        },
        "rubrics": {},
    },
    "sf-hard-alter-type-using": {
        "prompt": "Một cột amount được khai báo TEXT và chứa văn bản số. Câu lệnh ALTER TABLE sale ALTER COLUMN amount TYPE INT; thất bại. Thay đổi nào làm cho việc chuyển đổi tường minh và đúng?",
        "explanation": "Không có mệnh đề USING, PostgreSQL chỉ áp dụng một phép ép kiểu gán, và TEXT sang INT không phải vậy, nên câu lệnh thất bại. USING định nghĩa biểu thức theo từng dòng tạo ra giá trị mới, ở đây là một phép ép kiểu tường minh. Mệnh đề DEFAULT không chuyển đổi các giá trị hiện có, CASCADE không liên quan đến chuyển đổi kiểu, và CTAS tạo một bảng mới thay vì sửa bảng này.",
        "option_texts": {
            "A": "ALTER TABLE sale ALTER COLUMN amount SET DATA TYPE INT CASCADE;",
            "B": "ALTER TABLE sale ALTER COLUMN amount TYPE INT DEFAULT 0;",
            "C": "ALTER TABLE sale ALTER COLUMN amount TYPE INT USING amount::INT;",
            "D": "CREATE TABLE sale_new AS SELECT * FROM sale;",
        },
        "rubrics": {},
    },
    "sf-hard-create-like-including": {
        "prompt": "Câu lệnh nào đối chiếu đúng CREATE TABLE copy (LIKE sale INCLUDING ALL) với CREATE TABLE copy AS SELECT * FROM sale?",
        "explanation": "CREATE TABLE ... LIKE tạo một bảng rỗng kế thừa các định nghĩa cột, và INCLUDING ALL thêm các giá trị mặc định, ràng buộc, chỉ mục và thuộc tính identity. CREATE TABLE AS hiện thực hóa kết quả truy vấn, nên nó sao chép dòng và kiểu cột, nhưng không mang theo khóa chính, ràng buộc duy nhất hay khóa ngoại.",
        "option_texts": {
            "A": "LIKE ... INCLUDING ALL sao chép các dòng; CREATE TABLE AS chỉ sao chép định nghĩa.",
            "B": "Cả hai đều sao chép các dòng và các ràng buộc.",
            "C": "LIKE ... INCLUDING ALL sao chép định nghĩa cùng các ràng buộc và chỉ mục nhưng không sao chép dòng; CREATE TABLE AS sao chép dòng với các cột được suy ra nhưng không sao chép ràng buộc.",
            "D": "CREATE TABLE AS không sao chép cả dòng lẫn kiểu cột.",
        },
        "rubrics": {},
    },
    "sf-hard-truncate-restart": {
        "prompt": "Bảng ticket có một cột identity, và bảng comment tham chiếu ticket(ticket_id). Câu lệnh TRUNCATE TABLE ticket RESTART IDENTITY; được thực thi mà không có tùy chọn nào khác. Điều gì xảy ra?",
        "explanation": "TRUNCATE từ chối chạy khi một bảng khác có khóa ngoại tới bảng đích, trừ khi bảng đó được bao gồm bằng CASCADE. RESTART IDENTITY đặt lại các chuỗi thuộc sở hữu, nên tùy chọn này có ý nghĩa; nó không bị bỏ qua. Các bảng tham chiếu không bao giờ bị sửa âm thầm khi không có CASCADE.",
        "option_texts": {
            "A": "Nó thành công và truncate comment thay vì ticket.",
            "B": "Nó thành công và đặt lại chuỗi identity; các dòng tham chiếu bị xóa tự động.",
            "C": "Nó thành công nhưng để nguyên chuỗi identity, vì TRUNCATE không bao giờ ảnh hưởng đến chuỗi.",
            "D": "Nó thất bại, vì một bảng khác tham chiếu ticket; cần TRUNCATE CASCADE để truncate cả bảng tham chiếu.",
        },
        "rubrics": {},
    },
    "sf-hard-updatable-view": {
        "prompt": "View nào PostgreSQL có thể cập nhật tự động mà không cần trigger hoặc rule INSTEAD OF?",
        "explanation": "Một view có thể cập nhật tự động khi nó có đúng một quan hệ cơ sở, không có DISTINCT, GROUP BY, HAVING, phép toán tập hợp, tổng hợp hay hàm cửa sổ, và mỗi cột đầu ra ánh xạ tới một cột cơ sở. Tổng hợp, phép toán tập hợp và DISTINCT phá vỡ ánh xạ đó, nên những view ấy cần trigger hoặc rule INSTEAD OF để nhận ghi.",
        "option_texts": {
            "A": "Một view trên một bảng cơ sở duy nhất với danh sách chọn chỉ chứa các cột thuần, không có DISTINCT, nhóm hay tổng hợp.",
            "B": "Một view có danh sách chọn chứa một tổng hợp như count(*) được nhóm theo department.",
            "C": "Một view dùng UNION của hai bảng cơ sở.",
            "D": "Một view chọn DISTINCT city from customer.",
        },
        "rubrics": {},
    },
    "sf-hard-fk-match-simple": {
        "prompt": "Bảng line(order_id INT, product_id INT, FOREIGN KEY (order_id, product_id) REFERENCES order_item(order_id, product_id)) dùng MATCH SIMPLE mặc định. Dòng (NULL, 99) được chèn. Điều gì xảy ra?",
        "explanation": "MATCH SIMPLE, mặc định, yêu cầu điều kiện khóa ngoại chỉ đúng khi tất cả các cột khóa đều không NULL; một NULL duy nhất vô hiệu hóa việc kiểm tra cho dòng đó. MATCH FULL sẽ từ chối một khóa có NULL một phần, và không có việc tra cứu tự động product_id trong cả hai chế độ.",
        "option_texts": {
            "A": "Dòng được chấp nhận chỉ khi 99 cũng xuất hiện trong order_item.",
            "B": "Dòng bị từ chối, vì product_id 99 không có dòng order_item khớp.",
            "C": "Dòng được chấp nhận, vì với MATCH SIMPLE, khóa ngoại phức hợp không được kiểm tra khi bất kỳ cột nào của nó là NULL.",
            "D": "Dòng bị từ chối, vì khóa ngoại phức hợp không được chứa NULL.",
        },
        "rubrics": {},
    },
    "sf-hard-view-join-filter": {
        "prompt": "Phần thiết lập tạo customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL) và orders(order_id INT PRIMARY KEY, customer_id INT, status TEXT, qty INT, unit_price INT), sau đó là view open_order_value với truy vấn được lưu nối orders với customer, giữ các dòng có status 'open', và tính line_value = qty * unit_price. Trả về order_id, name và line_value cho mọi dòng của view, sắp xếp theo order_id tăng dần.",
        "explanation": "Truy vấn được lưu của view được đánh giá khi view được đọc, nên phép nối, bộ lọc status và phép nhân đều áp dụng tại thời điểm truy vấn. Đơn 10 và 12 tồn tại với giá trị tính được 100 và 60; đơn đã đóng 11 bị lọc ra, và đơn 13 biến mất vì customer_id NULL của nó không khớp với customer nào qua phép nối trong. Tập dữ liệu không có đơn mở trả về không dòng.",
        "option_texts": {},
        "rubrics": {},
    },
    "sf-hard-unique-null-groups": {
        "prompt": "Phần thiết lập tạo article(article_id INT PRIMARY KEY, code TEXT UNIQUE) dùng cách xử lý NULL mặc định và chèn các dòng, bao gồm nhiều hơn một dòng có code NULL. Trả về code và copies (BIGINT) cho số dòng được lưu theo từng code, sắp xếp theo code tăng dần với các giá trị NULL ở cuối.",
        "explanation": "UNIQUE so sánh bằng đẳng thức, và NULL không bao giờ bằng NULL, nên cả ba dòng có code NULL đều được chấp nhận và GROUP BY gom chúng thành một nhóm ba dòng. Mỗi code không NULL là duy nhất, nên mỗi code có copies = 1. Một ràng buộc UNIQUE NULLS NOT DISTINCT sẽ từ chối lần chèn NULL thứ hai.",
        "option_texts": {},
        "rubrics": {},
    },
    "sf-hard-delete-truncate-drop": {
        "prompt": "So sánh DELETE, TRUNCATE và DROP TABLE trong PostgreSQL. Trình bày (a) mỗi lệnh xóa những dòng hoặc đối tượng nào, (b) lọc và WHERE, (c) hành vi giao dịch và hoàn tác, (d) phụ thuộc khóa ngoại và các tùy chọn cần thiết, (e) chuỗi identity và RESTART IDENTITY, và (f) các hệ quả khóa bạn sẽ cân nhắc trước khi chạy mỗi lệnh trong môi trường sản xuất.",
        "explanation": "Câu trả lời phải phân biệt ba lệnh theo phạm vi (dòng so với toàn bộ dòng so với đối tượng), theo khả năng lọc, theo tính giao dịch, theo hành vi khóa ngoại, theo cách xử lý identity và theo khóa, và phải gắn mỗi lệnh với một mục đích sử dụng sản xuất phù hợp.",
        "option_texts": {},
        "rubrics": {
            "Incomplete": {
                "label": "Chưa đạt",
                "criteria": "Coi ba lệnh là có thể thay thế cho nhau, hoặc khẳng định TRUNCATE không thể hoàn tác trong PostgreSQL; không đề cập khóa ngoại hay khóa.",
            },
            "Partial": {
                "label": "Một phần",
                "criteria": "Đúng phạm vi cơ bản nhưng nhầm ít nhất hai thuộc tính, ví dụ nói DROP có thể lọc hoặc DELETE đặt lại chuỗi. Không thảo luận khóa.",
            },
            "Mostly Complete": {
                "label": "Phần lớn đầy đủ",
                "criteria": "Đúng phạm vi, lọc, tính giao dịch và hành vi khóa ngoại, nhưng chi tiết về identity hoặc khóa bị thiếu hay nêu không chính xác.",
            },
            "Complete": {
                "label": "Đầy đủ",
                "criteria": "Hoàn toàn chính xác: DELETE là DML có lọc trên dòng, TRUNCATE làm rỗng bảng không có WHERE và có tính giao dịch nhưng lấy khóa mạnh, DROP xóa đối tượng như DDL; yêu cầu CASCADE của khóa ngoại, RESTART IDENTITY, quyền sở hữu và các đánh đổi sản xuất đều được nêu chính xác.",
            },
        },
    },
    "sf-medium-on-conflict-do-nothing": {
        "prompt": "Bảng account(account_id INT PRIMARY KEY, email TEXT NOT NULL UNIQUE) đã chứa account_id = 7. Câu lệnh INSERT INTO account (account_id, email) VALUES (7, 'new@example.edu') ON CONFLICT (account_id) DO NOTHING; được thực thi. Kết quả là gì?",
        "explanation": "ON CONFLICT (account_id) DO NOTHING nêu account_id làm arbiter; khi xảy ra xung đột với khóa hiện có, dòng đề xuất bị loại bỏ và lệnh vẫn thành công. Thay thế email cần DO UPDATE, và khóa trùng chỉ là lỗi khi không cung cấp hành động xung đột.",
        "option_texts": {
            "A": "Email của dòng hiện có được thay bằng 'new@example.edu'.",
            "B": "Không có dòng mới nào được lưu và câu lệnh hoàn tất thành công.",
            "C": "Một lỗi được phát sinh vì account_id đã tồn tại.",
            "D": "Một dòng thứ hai với account_id = 7 được chèn.",
        },
        "rubrics": {},
    },
    "sf-medium-on-conflict-excluded": {
        "prompt": "Trong INSERT INTO t (id, qty) VALUES (1, 5) ON CONFLICT (id) DO UPDATE SET qty = EXCLUDED.qty, EXCLUDED tham chiếu đến gì?",
        "explanation": "EXCLUDED là quan hệ đặc biệt chứa dòng mà INSERT đã cố gắng thêm. Tham chiếu đến nó cho phép cập nhật sao chép các giá trị được đề xuất; dòng đang được lưu được tham chiếu qua tên bảng đích, không phải qua EXCLUDED.",
        "option_texts": {
            "A": "Chỉ mục duy nhất đã phát hiện xung đột.",
            "B": "Dòng hiện đang được lưu với id = 1.",
            "C": "Một bản sao của toàn bộ bảng sau khi chèn.",
            "D": "Dòng được INSERT đề xuất, có qty là 5.",
        },
        "rubrics": {},
    },
    "sf-medium-update-from": {
        "prompt": "Câu lệnh UPDATE sale s SET amount = p.amount FROM price p WHERE p.sale_id = s.sale_id; được thực thi và một sale khớp với nhiều hơn một dòng price. PostgreSQL bảo đảm điều gì?",
        "explanation": "UPDATE ... FROM nối đích với nguồn, và một dòng đích khớp với nhiều dòng nguồn vẫn chỉ được cập nhật một lần; dòng khớp nào cung cấp giá trị là không được xác định. Vì vậy kết quả tất định đòi hỏi phía nguồn phải duy nhất theo khóa. Không có lỗi về bản số được phát sinh, và UPDATE không bao giờ chèn dòng.",
        "option_texts": {
            "A": "Mỗi dòng price khớp được chèn như một dòng sale mới.",
            "B": "Dòng đích được cập nhật một lần cho mỗi dòng price khớp, nên kết quả cuối cùng thắng một cách tất định.",
            "C": "Câu lệnh thất bại với lỗi về bản số.",
            "D": "Mỗi dòng đích được cập nhật nhiều nhất một lần, dùng một trong các dòng price khớp được chọn tùy ý.",
        },
        "rubrics": {},
    },
    "sf-medium-delete-using": {
        "prompt": "Câu lệnh DELETE FROM sale s USING customer c WHERE c.customer_id = s.customer_id AND c.status = 'closed'; được thực thi. Những dòng nào bị xóa?",
        "explanation": "DELETE ... USING nêu các bảng bổ sung mà mệnh đề WHERE có thể tham chiếu; chỉ các dòng của đích xóa (sale) thỏa phép nối và bộ lọc mới bị xóa. Các dòng customer không bao giờ bị xóa bởi một DELETE nhắm vào sale, và các sale không khớp sẽ không thỏa điều kiện nối và tồn tại.",
        "option_texts": {
            "A": "Mọi dòng customer có status 'closed'.",
            "B": "Các sale có customer tồn tại trong customer và có status 'closed'.",
            "C": "Mọi dòng sale, vì USING thay thế mệnh đề WHERE.",
            "D": "Các sale không có customer khớp.",
        },
        "rubrics": {},
    },
    "sf-medium-identity-vs-serial": {
        "prompt": "Phát biểu nào về cột identity so với serial là đúng trong PostgreSQL?",
        "explanation": "Cột identity là giải pháp thay thế chuẩn cho serial. Cả hai đều dùng một chuỗi, nhưng GENERATED ALWAYS từ chối giá trị chèn tường minh trừ khi câu lệnh nêu OVERRIDING SYSTEM VALUE; GENERATED BY DEFAULT chấp nhận giá trị tường minh. Serial là dạng viết tắt cũ hơn, không theo chuẩn.",
        "option_texts": {
            "A": "GENERATED ALWAYS AS IDENTITY chấp nhận các giá trị tường minh giống hệt serial.",
            "B": "Cột identity không lưu chuỗi và tạo các giá trị duy nhất mà không cần đối tượng catalog nào.",
            "C": "GENERATED ALWAYS AS IDENTITY theo chuẩn SQL, được hỗ trợ bởi một chuỗi, và từ chối giá trị tường minh trừ khi có OVERRIDING SYSTEM VALUE.",
            "D": "Cột serial là cú pháp chuẩn và cột identity là một tính năng tương thích đã bị phản đối.",
        },
        "rubrics": {},
    },
    "sf-medium-fk-on-delete": {
        "prompt": "Bảng order_line tham chiếu order với ON DELETE RESTRICT, trong khi bảng audit_note tham chiếu order với ON DELETE CASCADE. Một order có các dòng trong cả hai bảng bị xóa. Điều gì xảy ra?",
        "explanation": "Hành động tham chiếu được thực thi theo từng ràng buộc. RESTRICT ngăn việc xóa khi còn dòng tham chiếu, và toàn bộ câu lệnh thất bại một cách nguyên tử, nên order không bị xóa và hiệu ứng CASCADE không bao giờ xảy ra. SET NULL chỉ áp dụng khi ràng buộc khai báo ON DELETE SET NULL.",
        "option_texts": {
            "A": "Order bị xóa và chỉ các dòng audit_note bị xóa.",
            "B": "Order và mọi dòng tham chiếu trong cả hai bảng đều bị xóa.",
            "C": "DELETE bị từ chối vì các dòng order_line sẽ trở thành mồ côi; không dòng order nào bị xóa.",
            "D": "Order bị xóa và các dòng tham chiếu được đặt thành NULL.",
        },
        "rubrics": {},
    },
    "sf-medium-unique-nulls": {
        "prompt": "Bảng customer(email TEXT UNIQUE) dùng cách xử lý NULL mặc định. Hai dòng được chèn với email = NULL. Điều gì xảy ra?",
        "explanation": "Ràng buộc UNIQUE so sánh các giá trị bằng đẳng thức, và NULL không bao giờ bằng NULL, nên bất kỳ số lượng NULL nào cũng có thể cùng tồn tại. Một ràng buộc khai báo UNIQUE NULLS NOT DISTINCT sẽ từ chối NULL thứ hai. Không giá trị nào bị viết lại.",
        "option_texts": {
            "A": "NULL thứ nhất được thay bằng NULL thứ hai.",
            "B": "Lần chèn thứ hai bị từ chối, vì NULL bằng NULL đối với ràng buộc duy nhất.",
            "C": "Cả hai dòng được chấp nhận, vì ràng buộc UNIQUE coi các giá trị NULL là phân biệt.",
            "D": "Cả hai dòng được chấp nhận, và một NULL được chuyển thành chuỗi rỗng.",
        },
        "rubrics": {},
    },
    "sf-medium-create-table-as": {
        "prompt": "CREATE TABLE sale_backup AS SELECT * FROM sale; được thực thi. Bảng mới chứa gì?",
        "explanation": "CREATE TABLE AS hiện thực hóa kết quả truy vấn một lần; các thay đổi sau đó trên sale không xuất hiện. Tên và kiểu cột được suy ra từ truy vấn, nhưng các ràng buộc như khóa chính, ràng buộc duy nhất và khóa ngoại không được sao chép. View hoặc materialized view là một đối tượng khác.",
        "option_texts": {
            "A": "Một bản sao các dòng hiện tại, với kiểu cột được suy ra nhưng không có khóa chính hay các ràng buộc khác của sale.",
            "B": "Một bảng rỗng có các cột và ràng buộc được sao chép từ sale.",
            "C": "Một view trên sale luôn hiển thị các dòng mới nhất.",
            "D": "Một bảng tự động đồng bộ với sale.",
        },
        "rubrics": {},
    },
    "sf-medium-constraint-not-valid": {
        "prompt": "ALTER TABLE sale ADD CONSTRAINT sale_amount_ck CHECK (amount >= 0) NOT VALID; được thực thi trên một bảng đã chứa một amount âm. Hiệu ứng là gì?",
        "explanation": "NOT VALID bỏ qua lần quét đầu tiên trên các dòng hiện có, đó là lý do câu lệnh thành công dù amount âm đã được lưu. Ràng buộc được thực thi cho mọi dòng mới hoặc bị thay đổi. Các dòng hiện có có thể được kiểm tra sau bằng ALTER TABLE ... VALIDATE CONSTRAINT. Không gì bị xóa hay viết lại tự động.",
        "option_texts": {
            "A": "Ràng buộc được thêm và các giá trị vi phạm được đặt thành 0.",
            "B": "Câu lệnh bị từ chối vì các dòng hiện có vi phạm ràng buộc.",
            "C": "Ràng buộc được thêm và các dòng vi phạm bị xóa.",
            "D": "Ràng buộc được thêm mà không kiểm tra các dòng hiện có; các lần chèn mới và cập nhật bất kỳ dòng nào đều phải thỏa nó.",
        },
        "rubrics": {},
    },
    "sf-medium-truncate": {
        "prompt": "Phát biểu nào về TRUNCATE TABLE sale là đúng trong PostgreSQL?",
        "explanation": "TRUNCATE làm rỗng bảng; nó không có mệnh đề WHERE, nên không thể xóa các dòng được chọn. Trong PostgreSQL, TRUNCATE có tính giao dịch và được hoàn tác cùng giao dịch. Nó không xóa bảng; DROP TABLE xóa định nghĩa.",
        "option_texts": {
            "A": "Nó xóa các dòng được chọn khi có mệnh đề WHERE.",
            "B": "Nó xóa mọi dòng và không thể hoàn tác vì nó commit ngay lập tức.",
            "C": "Nó xóa mọi dòng, không nhận mệnh đề WHERE, và có thể hoàn tác vì nó có tính giao dịch.",
            "D": "Nó xóa cả định nghĩa bảng lẫn các dòng của nó.",
        },
        "rubrics": {},
    },
    "sf-medium-view-aggregate": {
        "prompt": "Phần thiết lập tạo dept(dept_id INT PRIMARY KEY, dept_name TEXT NOT NULL) và emp(emp_id INT PRIMARY KEY, dept_id INT, name TEXT), sau đó là view dept_headcount với truy vấn được lưu nối trái emp với dept và nhóm theo phòng ban, tạo ra dept_id, dept_name và headcount = count(emp.emp_id). Trả về dept_id, dept_name và headcount cho mọi dòng của view, sắp xếp theo dept_id tăng dần.",
        "explanation": "View lưu truy vấn, nên tổng hợp được tính lại mỗi lần đọc. Vì view nối trái từ dept, phòng Sales có headcount 0 thay vì biến mất, và nhân viên có dept_id NULL không khớp phòng ban nào nên không được đếm. Tập dữ liệu rỗng trả về không dòng.",
        "option_texts": {},
        "rubrics": {},
    },
    "sf-medium-insert-duplicates": {
        "prompt": "Phần thiết lập tạo note(note_id INT, body TEXT) không có khóa chính hay ràng buộc duy nhất và chèn một số giá trị note_id nhiều hơn một lần. Trả về note_id và copies (BIGINT) cho các giá trị note_id được lưu nhiều hơn một lần, sắp xếp theo note_id tăng dần.",
        "explanation": "Không có khóa chính hay ràng buộc duy nhất, INSERT không kiểm tra trùng, nên cùng một note_id có thể được lưu nhiều lần. GROUP BY với HAVING count(*) > 1 làm nổi bật các khóa đó; note_id 1 xuất hiện hai lần và note_id 3 ba lần trong tập dữ liệu đầu tiên, và tập dữ liệu sạch đúng là trả về không dòng. Khai báo note_id là khóa chính sẽ từ chối các giá trị lặp lại.",
        "option_texts": {},
        "rubrics": {},
    },
    "sf-medium-upsert": {
        "prompt": "Giải thích cách INSERT ... ON CONFLICT hoạt động trong PostgreSQL. Trình bày đối tượng nào đóng vai trò arbiter, sự khác biệt giữa DO NOTHING và DO UPDATE, vai trò của EXCLUDED, điều gì xảy ra khi không có chỉ mục duy nhất nào khớp với đích xung đột, và vì sao cách này an toàn hơn chuỗi SELECT-rồi-INSERT dưới nhiều người ghi đồng thời.",
        "explanation": "Câu trả lời phải xác định chỉ mục duy nhất là arbiter, đối chiếu DO NOTHING với DO UPDATE, giải thích EXCLUDED, nêu lỗi khi không có chỉ mục khớp, và biện luận cho lợi thế đồng thời so với kiểm tra-rồi-chèn.",
        "option_texts": {},
        "rubrics": {
            "Incomplete": {
                "label": "Chưa đạt",
                "criteria": "Mô tả ON CONFLICT như một cờ INSERT chung không có arbiter, hoặc không nói được EXCLUDED nghĩa là gì; không tham chiếu chỉ mục duy nhất hay tính đồng thời.",
            },
            "Partial": {
                "label": "Một phần",
                "criteria": "Đúng ý tưởng mức cao nhưng nhầm DO NOTHING với DO UPDATE, hoặc bỏ sót điều xảy ra khi không có chỉ mục duy nhất khớp đích. Lập luận về đồng thời mơ hồ.",
            },
            "Mostly Complete": {
                "label": "Phần lớn đầy đủ",
                "criteria": "Đúng ngữ nghĩa arbiter và hành động với EXCLUDED được giải thích, nhưng thiếu một chi tiết, chẳng hạn lỗi khi thiếu chỉ mục hoặc cuộc đua trong kiểm tra-rồi-chèn.",
            },
            "Complete": {
                "label": "Đầy đủ",
                "criteria": "Hoàn toàn chính xác: nêu chỉ mục/ràng buộc duy nhất làm arbiter, phân biệt DO NOTHING và DO UPDATE, giải thích EXCLUDED là dòng được đề xuất, nêu lỗi khi không có chỉ mục khớp, và chỉ ra ON CONFLICT giải quyết xung đột một cách nguyên tử trong khi SELECT-rồi-INSERT có thể gặp cuộc đua.",
            },
        },
    },
}

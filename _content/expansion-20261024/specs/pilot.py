"""Three-format pilot for the Database Design expansion.

The pilot exercises the real create/validate pipeline against the restored
clone before mass authoring. Every SQL expected result is derived by running
the reference through the production SandboxRunner, never hand-written.
"""

from sources import CODD_1971, PG_AGGREGATE, PG_SELECT, WATT_DB_DESIGN

QUESTIONS = [
    {
        "key": "pilot-db-3nf-mcq",
        "question_type": "mcq",
        "original_locale": "en",
        "difficulty_level": 3,
        "points": "1.00",
        "concept_codes": ["DB-3NF"],
        "required_concept_codes": [],
        "tags": [
            "database-design",
            "normalization",
            "third-normal-form",
            "functional-dependency",
        ],
        "source_refs": [WATT_DB_DESIGN, CODD_1971],
        "prompt": (
            "The relation enrollment(student_id, course_id, instructor_id, "
            "instructor_email) has candidate key {student_id, course_id} and "
            "functional dependencies {student_id, course_id} -> instructor_id "
            "and instructor_id -> instructor_email. Assuming every determinant "
            "is minimal unless stated otherwise, which statement is correct?"
        ),
        "explanation": (
            "The candidate key is {student_id, course_id}. instructor_id "
            "depends on the whole key, so there is no partial dependency and "
            "2NF holds. But instructor_email depends on instructor_id, which "
            "is not a superkey; instructor_email is therefore transitively "
            "dependent on the key and both 3NF and BCNF fail. Decompose into "
            "enrollment(student_id, course_id, instructor_id) and "
            "instructor(instructor_id, instructor_email)."
        ),
        "options": [
            {
                "option_label": "A",
                "option_text": (
                    "The relation is in 3NF because instructor_email is "
                    "functionally determined by the candidate key."
                ),
                "is_correct": False,
            },
            {
                "option_label": "B",
                "option_text": (
                    "The relation is in 2NF but not 3NF because "
                    "instructor_email is transitively dependent on the "
                    "candidate key through instructor_id."
                ),
                "is_correct": True,
            },
            {
                "option_label": "C",
                "option_text": (
                    "The relation violates 2NF because instructor_id depends "
                    "on only part of the candidate key."
                ),
                "is_correct": False,
            },
            {
                "option_label": "D",
                "option_text": (
                    "The relation is in BCNF because every non-key attribute "
                    "is determined by the candidate key."
                ),
                "is_correct": False,
            },
        ],
        "option_rationales": {
            "A": (
                "Confuses 'determined by the key' with 'directly determined'. "
                "The dependency is transitive via instructor_id."
            ),
            "B": (
                "Correct: no partial dependency, but a non-superkey "
                "determinant creates a transitive dependency."
            ),
            "C": (
                "Incorrect: instructor_id depends on the full composite key, "
                "not a proper subset, so 2NF is not the violated form."
            ),
            "D": (
                "BCNF requires every determinant to be a superkey; "
                "instructor_id is not one."
            ),
        },
        "vi_draft": {
            "prompt": (
                "Quan hệ enrollment(student_id, course_id, instructor_id, "
                "instructor_email) có khóa ứng viên {student_id, course_id} "
                "và các phụ thuộc hàm {student_id, course_id} -> instructor_id, "
                "instructor_id -> instructor_email. Giả sử mọi yếu tố xác "
                "định đều tối tiểu trừ khi có ghi chú khác, phát biểu nào sau "
                "đây là đúng?"
            ),
            "explanation": (
                "Khóa ứng viên là {student_id, course_id}. instructor_id phụ "
                "thuộc vào toàn bộ khóa nên không có phụ thuộc bộ phận và 2NF "
                "được thỏa mãn. Tuy nhiên instructor_email phụ thuộc vào "
                "instructor_id, mà instructor_id không phải siêu khóa; do đó "
                "instructor_email phụ thuộc bắc cầu vào khóa và cả 3NF lẫn "
                "BCNF đều bị vi phạm. Tách thành "
                "enrollment(student_id, course_id, instructor_id) và "
                "instructor(instructor_id, instructor_email)."
            ),
            "option_texts": {
                "A": (
                    "Quan hệ đạt 3NF vì instructor_email được xác định hàm bởi "
                    "khóa ứng viên."
                ),
                "B": (
                    "Quan hệ đạt 2NF nhưng không đạt 3NF vì instructor_email "
                    "phụ thuộc bắc cầu vào khóa ứng viên thông qua "
                    "instructor_id."
                ),
                "C": (
                    "Quan hệ vi phạm 2NF vì instructor_id chỉ phụ thuộc vào "
                    "một phần của khóa ứng viên."
                ),
                "D": (
                    "Quan hệ đạt BCNF vì mọi thuộc tính không khóa đều được "
                    "xác định bởi khóa ứng viên."
                ),
            },
            "rubrics": {},
        },
        "review_notes": (
            "Academic-theory item: 3NF and transitive dependency are not "
            "defined by the PostgreSQL documentation; sources are Watt ch.11-12 "
            "and Codd 1971."
        ),
    },
    {
        "key": "pilot-db-fd-sql",
        "question_type": "sql",
        "original_locale": "en",
        "difficulty_level": 3,
        "points": "5.00",
        "concept_codes": ["DB-FD"],
        "required_concept_codes": [],
        "tags": [
            "database-design",
            "functional-dependency",
            "sql-practical",
            "aggregate",
        ],
        "source_refs": [WATT_DB_DESIGN, PG_AGGREGATE, PG_SELECT],
        "prompt": (
            "Table enrollment(student_id INT, course_id INT, instructor_id "
            "INT, instructor_email TEXT) records course enrollments. To audit "
            "whether instructor_id -> instructor_email holds, return one row "
            "per instructor with columns instructor_id (INT) and "
            "email_variants (BIGINT): the number of distinct non-NULL emails "
            "recorded for that instructor. Include instructors that have only "
            "NULL emails (their count is 0). Order by instructor_id ascending."
        ),
        "reference_answer": (
            "SELECT instructor_id, count(DISTINCT instructor_email) AS "
            "email_variants FROM enrollment GROUP BY instructor_id "
            "ORDER BY instructor_id"
        ),
        "explanation": (
            "COUNT(DISTINCT instructor_email) ignores NULL, so an instructor "
            "whose only email is NULL yields 0. An instructor with two "
            "distinct emails yields 2, which proves that "
            "instructor_id -> instructor_email does not hold in that dataset; "
            "the audit surfaces the violation instead of hiding it."
        ),
        "check_columns": True,
        "datasets": [
            {
                "dataset_name": "consistent_catalog",
                "is_edge_case": False,
                "setup_sql": (
                    "CREATE TABLE enrollment(student_id INT NOT NULL, "
                    "course_id INT NOT NULL, instructor_id INT NOT NULL, "
                    "instructor_email TEXT);"
                    "INSERT INTO enrollment VALUES "
                    "(1,10,100,'nguyen@example.edu'),"
                    "(2,10,100,'nguyen@example.edu'),"
                    "(3,20,200,'tran@example.edu'),"
                    "(4,20,200,'tran@example.edu'),"
                    "(5,30,300,'le@example.edu');"
                ),
            },
            {
                "dataset_name": "edge_null_and_violation",
                "is_edge_case": True,
                "setup_sql": (
                    "CREATE TABLE enrollment(student_id INT NOT NULL, "
                    "course_id INT NOT NULL, instructor_id INT NOT NULL, "
                    "instructor_email TEXT);"
                    "INSERT INTO enrollment VALUES "
                    "(1,10,100,'nguyen@example.edu'),"
                    "(2,10,100,NULL),"
                    "(3,20,100,'nguyen@example.edu'),"
                    "(4,20,200,NULL),"
                    "(5,30,300,'pham@example.edu'),"
                    "(6,40,300,'pham@clinic.example.edu');"
                ),
            },
        ],
        "vi_draft": {
            "prompt": (
                "Bảng enrollment(student_id INT, course_id INT, instructor_id "
                "INT, instructor_email TEXT) ghi lại các lượt đăng ký học "
                "phần. Để kiểm tra xem instructor_id -> instructor_email có "
                "đúng không, hãy trả về mỗi giảng viên một dòng gồm "
                "instructor_id (INT) và email_variants (BIGINT): số lượng "
                "email khác nhau và khác NULL được ghi cho giảng viên đó. Bao "
                "gồm cả giảng viên chỉ có email NULL (khi đó số đếm là 0). "
                "Sắp xếp theo instructor_id tăng dần."
            ),
            "explanation": (
                "COUNT(DISTINCT instructor_email) bỏ qua NULL, nên giảng viên "
                "chỉ có email NULL trả về 0. Giảng viên có hai email khác "
                "nhau trả về 2, chứng tỏ instructor_id -> instructor_email "
                "không đúng trên tập dữ liệu đó; truy vấn kiểm toán phơi bày "
                "vi phạm thay vì che khuất nó."
            ),
            "option_texts": {},
            "rubrics": {},
        },
        "review_notes": (
            "SQL mechanics (GROUP BY, count(DISTINCT)) are PostgreSQL 17 "
            "documented; the audit goal comes from functional-dependency theory."
        ),
    },
    {
        "key": "pilot-db-3nf-essay",
        "question_type": "essay",
        "original_locale": "en",
        "difficulty_level": 4,
        "points": "5.00",
        "concept_codes": ["DB-FD", "DB-3NF"],
        "required_concept_codes": [],
        "tags": [
            "database-design",
            "normalization",
            "third-normal-form",
            "functional-dependency",
            "decomposition",
            "essay",
        ],
        "source_refs": [WATT_DB_DESIGN, CODD_1971],
        "prompt": (
            "A hospital stores appointments in appointment(appointment_id, "
            "patient_id, clinician_id, clinician_email, room_code, "
            "room_building, appointment_date) with functional dependencies: "
            "(1) appointment_id -> patient_id, clinician_id, room_code, "
            "appointment_date; (2) clinician_id -> clinician_email; "
            "(3) room_code -> room_building. Assume each appointment has "
            "exactly one clinician and one room, and room_code identifies a "
            "room uniquely. (a) Identify the only candidate key and explain "
            "why it is minimal. (b) Determine the highest normal form of "
            "appointment and name the dependency that violates the next form. "
            "(c) Decompose into 3NF relations, listing keys and foreign keys. "
            "(d) Is your decomposition lossless-join and dependency-preserving? "
            "Justify briefly."
        ),
        "reference_answer": (
            "(a) The only candidate key is {appointment_id}. By (1) it "
            "determines every attribute; a single attribute has no proper "
            "nonempty subset, so it is minimal. "
            "(b) The highest normal form is 2NF. The key is single-attribute, "
            "so no partial dependency exists. 3NF fails because clinician_id "
            "and room_code are non-superkey determinants: clinician_email is "
            "transitively dependent on appointment_id via clinician_id, and "
            "room_building is transitively dependent on appointment_id via "
            "room_code. BCNF fails for the same reason. "
            "(c) appointment(appointment_id PK, patient_id, clinician_id "
            "REFERENCES clinician, room_code REFERENCES room, appointment_date), "
            "clinician(clinician_id PK, clinician_email), "
            "room(room_code PK, room_building). "
            "(d) Each step is a lossless decomposition by the common-attribute "
            "test: the common attribute (clinician_id, then room_code) is a "
            "key of one resulting relation. The decomposition is "
            "dependency-preserving because each functional dependency is "
            "enforced inside a single relation: (1) in appointment, (2) in "
            "clinician, (3) in room. The result is also in BCNF."
        ),
        "explanation": (
            "The key is appointment_id; single-attribute keys make 2NF "
            "automatic, but non-superkey determinants clinician_id and "
            "room_code create transitive dependencies, so 3NF fails. Splitting "
            "on those determinants yields three relations whose only "
            "determinants are keys, making the result BCNF, lossless and "
            "dependency-preserving."
        ),
        "rubrics": [
            {
                "level_name": "Incomplete",
                "min_score": "0.00",
                "max_score": "1.00",
                "criteria": (
                    "Identifies at most one candidate key or none, gives no "
                    "valid normal-form argument, and provides no usable 3NF "
                    "decomposition. A major conceptual error (for example "
                    "claiming the relation is already in 3NF) dominates."
                ),
            },
            {
                "level_name": "Partial",
                "min_score": "1.01",
                "max_score": "2.50",
                "criteria": (
                    "Correctly names appointment_id as the candidate key but "
                    "does not prove minimality; recognises at least one "
                    "transitive dependency, yet mislabels the highest normal "
                    "form or produces an incomplete decomposition missing one "
                    "dependency or one relation."
                ),
            },
            {
                "level_name": "Mostly Complete",
                "min_score": "2.51",
                "max_score": "4.00",
                "criteria": (
                    "Correct key and highest normal form; the decomposition "
                    "removes both transitive dependencies and is lossless, but "
                    "the dependency-preservation argument is incomplete or a "
                    "key/foreign-key detail is missing."
                ),
            },
            {
                "level_name": "Complete",
                "min_score": "4.01",
                "max_score": "5.00",
                "criteria": (
                    "Fully correct: appointment_id is the minimal candidate "
                    "key; the highest normal form is 2NF because clinician_id "
                    "and room_code are non-superkey determinants; the "
                    "decomposition into appointment, clinician and room is "
                    "3NF/BCNF, lossless by the common-attribute key test, and "
                    "dependency-preserving because every functional dependency "
                    "is enforced inside one relation; keys and foreign keys are "
                    "stated precisely."
                ),
            },
        ],
        "vi_draft": {
            "prompt": (
                "Một bệnh viện lưu lịch hẹn trong quan hệ appointment("
                "appointment_id, patient_id, clinician_id, clinician_email, "
                "room_code, room_building, appointment_date) với các phụ "
                "thuộc hàm: (1) appointment_id -> patient_id, clinician_id, "
                "room_code, appointment_date; (2) clinician_id -> "
                "clinician_email; (3) room_code -> room_building. Giả sử mỗi "
                "lịch hẹn có đúng một bác sĩ và một phòng, và room_code xác "
                "định duy nhất một phòng. (a) Xác định khóa ứng viên duy nhất "
                "và giải thích vì sao nó tối tiểu. (b) Xác định dạng chuẩn "
                "cao nhất của appointment và nêu phụ thuộc hàm vi phạm dạng "
                "chuẩn kế tiếp. (c) Tách quan hệ về 3NF, liệt kê khóa và khóa "
                "ngoại. (d) Phân rã có bảo toàn kết nối (lossless-join) và "
                "bảo toàn phụ thuộc không? Giải thích ngắn gọn."
            ),
            "explanation": (
                "Khóa là appointment_id; khóa một thuộc tính khiến 2NF tự "
                "động thỏa mãn, nhưng các yếu tố xác định không phải siêu "
                "khóa là clinician_id và room_code tạo ra phụ thuộc bắc cầu, "
                "nên 3NF bị vi phạm. Tách theo các yếu tố xác định đó cho ba "
                "quan hệ mà mọi yếu tố xác định đều là khóa, đưa kết quả về "
                "BCNF, bảo toàn kết nối và bảo toàn phụ thuộc."
            ),
            "option_texts": {},
            "rubrics": {
                "Incomplete": {
                    "label": "Chưa đạt",
                    "criteria": (
                        "Chỉ xác định được nhiều nhất một khóa ứng viên hoặc "
                        "không xác định được, không có lập luận dạng chuẩn hợp "
                        "lệ và không có phân rã 3NF dùng được. Sai lệch khái "
                        "niệm nghiêm trọng chiếm ưu thế (ví dụ khẳng định quan "
                        "hệ đã đạt 3NF)."
                    ),
                },
                "Partial": {
                    "label": "Một phần",
                    "criteria": (
                        "Gọi đúng appointment_id là khóa ứng viên nhưng không "
                        "chứng minh tính tối tiểu; nhận ra ít nhất một phụ "
                        "thuộc bắc cầu nhưng gọi sai dạng chuẩn cao nhất hoặc "
                        "phân rã chưa đầy đủ, thiếu một phụ thuộc hoặc một "
                        "quan hệ."
                    ),
                },
                "Mostly Complete": {
                    "label": "Phần lớn đầy đủ",
                    "criteria": (
                        "Đúng khóa và dạng chuẩn cao nhất; phân rã loại bỏ cả "
                        "hai phụ thuộc bắc cầu và bảo toàn kết nối, nhưng lập "
                        "luận bảo toàn phụ thuộc còn thiếu hoặc thiếu một chi "
                        "tiết về khóa/khóa ngoại."
                    ),
                },
                "Complete": {
                    "label": "Đầy đủ",
                    "criteria": (
                        "Hoàn toàn chính xác: appointment_id là khóa ứng viên "
                        "tối tiểu; dạng chuẩn cao nhất là 2NF vì clinician_id "
                        "và room_code là các yếu tố xác định không phải siêu "
                        "khóa; phân rã thành appointment, clinician và room "
                        "đạt 3NF/BCNF, bảo toàn kết nối theo phép thử thuộc "
                        "tính chung là khóa, và bảo toàn phụ thuộc vì mọi phụ "
                        "thuộc hàm đều được thực thi trong một quan hệ; khóa và "
                        "khóa ngoại được nêu chính xác."
                    ),
                },
            },
        },
        "review_notes": (
            "Academic-theory item; PostgreSQL 17 defines constraints and "
            "normalization mechanics but not 3NF semantics. Rubric bands are "
            "cent-precision and contiguous over 0.00-5.00."
        ),
    },
]

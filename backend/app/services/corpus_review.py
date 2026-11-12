"""Apply the recorded 2026-11-04 editorial decisions reproducibly to sources."""
from copy import deepcopy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REVIEW_DATE = "2026-11-04"
URL_REPAIRS = {"sql-syntax-expressions.html": "sql-expressions.html", "textsearch-types.html": "datatype-textsearch.html"}

# Original explanations for the foundation questions, paired with reviewed VI.
CORE_NOTES = {
    "legacy-mcq-select-filter": ("WHERE retains rows whose Boolean predicate is true before grouping; LIMIT truncates the final result.", "WHERE giữ các dòng có điều kiện Boolean đúng trước khi gom nhóm; LIMIT chỉ giới hạn số dòng kết quả."),
    "legacy-mcq-inner-join": ("INNER JOIN returns matching pairs under its join predicate; outer joins additionally preserve unmatched rows.", "INNER JOIN trả các cặp dòng thỏa điều kiện nối; outer join còn giữ dòng không khớp."),
    "legacy-sql-customer-names": ("SELECT name projects the customer name column without filtering rows. Row order is not part of this result contract.", "SELECT name chọn cột tên khách hàng và không lọc dòng. Bài này so sánh tập đa hợp dòng, không yêu cầu thứ tự."),
    "mcq-sql-select": ("The select list specifies output expressions and columns; ORDER BY sorts and HAVING filters groups.", "Danh sách biểu thức sau SELECT quy định cột đầu ra; ORDER BY sắp xếp và HAVING lọc nhóm."),
    "mcq-sql-where": ("A comparison with NULL yields unknown, so WHERE does not retain that row; IS NULL and IS NOT DISTINCT FROM NULL do retain it.", "So sánh với NULL cho kết quả unknown nên WHERE không giữ dòng đó; IS NULL và IS NOT DISTINCT FROM NULL lại giữ dòng có NULL."),
    "mcq-sql-join": ("An inner join emits only pairs satisfying the join condition; it does not invent a match or pad unmatched rows.", "INNER JOIN chỉ trả các cặp thỏa điều kiện nối, không tạo bản ghi khớp giả hay thêm NULL cho dòng không khớp."),
    "mcq-sql-group": ("GROUP BY region_id partitions input rows by region so SUM produces an aggregate per region, without promising sort order.", "GROUP BY region_id chia dòng theo vùng để SUM tính tổng từng nhóm; nó không bảo đảm thứ tự sắp xếp."),
    "mcq-sql-having": ("HAVING filters groups after grouping and aggregate calculation; WHERE filters input rows earlier.", "HAVING lọc nhóm sau khi gom nhóm và tính aggregate; WHERE lọc dòng đầu vào ở bước trước."),
    "mcq-sql-subquery": ("AVG ignores NULL inputs and returns NULL if there are no non-NULL inputs, rather than zero.", "AVG bỏ qua giá trị NULL và trả NULL nếu không còn giá trị đầu vào khác NULL, không tự trả 0."),
    "mcq-db-er": ("A junction relation represents pairs of entity keys; foreign keys enforce the references and a suitable key prevents duplicate associations.", "Bảng liên kết biểu diễn các cặp khóa thực thể; khóa ngoại bảo đảm tham chiếu và khóa phù hợp ngăn quan hệ trùng."),
    "mcq-db-norm": ("A related table models each value as its own fact, allowing explicit keys and constraints instead of an encoded multivalue string.", "Bảng liên quan biểu diễn mỗi giá trị thành một sự kiện riêng, cho phép đặt khóa và ràng buộc thay vì mã hóa nhiều giá trị trong chuỗi."),
    "mcq-db-fd": ("A functional dependency forbids two rows with the same determinant and different dependent values; it does not assert the inverse dependency.", "Phụ thuộc hàm không cho hai dòng cùng giá trị vế trái nhưng khác giá trị vế phải; không tự suy ra phụ thuộc chiều ngược lại."),
    "mcq-db-1nf": ("Under the question's atomic enrollment domains, one row per student-course pair avoids a collection of records inside one attribute.", "Theo miền giá trị nguyên tố của bài, một dòng cho mỗi cặp sinh viên–học phần tránh chứa cả tập bản ghi trong một thuộc tính."),
    "mcq-db-2nf": ("A non-prime attribute depending on only student_id is partially dependent on the composite candidate key, violating 2NF.", "Thuộc tính không khóa chỉ phụ thuộc student_id là phụ thuộc bộ phận vào khóa ứng viên ghép, vi phạm 2NF."),
    "mcq-db-3nf": ("Moving dept_id to dept_name into a department relation removes that transitive non-key dependency from the student relation.", "Đưa phụ thuộc dept_id → dept_name sang bảng phòng ban giúp loại phụ thuộc bắc cầu giữa thuộc tính không khóa khỏi bảng sinh viên."),
    "sql-sql-select": ("The select list projects both requested columns from every sales row, including rows containing NULL.", "Danh sách SELECT lấy cả hai cột được yêu cầu từ mọi dòng sales, kể cả dòng chứa NULL."),
    "sql-sql-where": ("The >= predicate includes the threshold value 20 and excludes smaller and NULL amounts.", "Điều kiện >= bao gồm giá trị biên 20, đồng thời loại amount nhỏ hơn 20 hoặc NULL."),
    "sql-sql-join": ("The explicit equality join pairs each sale with its referenced region and returns only the requested identifier and label.", "JOIN theo khóa bằng nhau ghép mỗi dòng sales với vùng tương ứng và chỉ trả mã cùng nhãn được yêu cầu."),
    "sql-sql-group": ("Grouping by region produces a SUM of non-NULL amounts for each group; an all-NULL group has a NULL sum.", "Gom theo vùng tạo SUM của các amount khác NULL trong từng nhóm; nhóm chỉ có NULL nhận tổng NULL."),
    "sql-sql-having": ("HAVING applies the inclusive threshold to the group SUM, not to individual sale amounts.", "HAVING áp dụng ngưỡng bao gồm giá trị biên lên SUM của cả nhóm, không áp dụng riêng cho từng dòng sales."),
    "sql-sql-subquery": ("The scalar aggregate subquery computes one overall average; the outer predicate keeps amounts strictly above it.", "Truy vấn con aggregate vô hướng tính một mức trung bình chung; điều kiện ngoài giữ amount lớn hơn mức đó."),
    "essay-normalization": ("Decompose using the stated dependencies, retain enrollment's composite key and grade, and justify the lossless key-based reconstruction and local enforcement of dependencies.", "Phân rã theo phụ thuộc đã nêu, giữ khóa ghép cùng grade trong Enrollment và giải thích phép nối theo khóa không mất mát cùng việc bảo toàn phụ thuộc."),
    "dml-knowledge": ("UPDATE changes values of existing rows; it does not define a table or create its schema.", "UPDATE thay đổi giá trị các dòng hiện có, không định nghĩa bảng hay tạo lược đồ."),
    "ddl-knowledge": ("CREATE TABLE defines structure and can declare a FOREIGN KEY; the other statements do not define that referential constraint.", "CREATE TABLE định nghĩa cấu trúc và có thể khai báo FOREIGN KEY; các lệnh còn lại không định nghĩa ràng buộc tham chiếu đó."),
    "essay-dml-ddl-knowledge": ("Distinguish schema definition from data changes, apply a targeted predicate, respect the declared foreign-key action, and retain the read-only sandbox boundary.", "Cần phân biệt định nghĩa lược đồ với thay đổi dữ liệu, dùng điều kiện cập nhật cụ thể, tôn trọng hành động khóa ngoại đã khai báo và giới hạn chỉ đọc của sandbox."),
}

INDEX_SAMPLE = ("A selective B-tree lookup can avoid scanning most rows, but the planner may prefer a sequential scan for small tables or unselective predicates. "
    "INSERT adds index entries and changing indexed values requires maintenance; HOT updates can avoid new index entries in suitable cases. "
    "Indexes consume storage and maintenance work, so compare measured read benefit with write frequency, selectivity and operational cost.")
INDEX_VI = "B-tree có thể tăng tốc truy vấn chọn lọc nhưng không phải mọi truy vấn đều có lợi. INSERT và thay đổi giá trị được lập chỉ mục cần bảo trì; HOT update có thể giảm một phần chi phí. Cần cân nhắc tính chọn lọc, tần suất ghi và dung lượng."


def reference(path):
    return {"url": f"https://www.postgresql.org/docs/18/{path}", "version": "18", "retrieved": REVIEW_DATE,
            "title": "PostgreSQL 18.6: " + path.removesuffix(".html")}


def apply_review(questions, translations=None):
    fixes = json.loads((ROOT / "db/reviewed_question_fixes.json").read_text(encoding="utf-8"))
    for q in questions:
        key, kind = q["key"], q["question_type"]
        vi = translations.get(key) if translations is not None else None
        for ref in q.get("source_refs", []):
            for old, new in URL_REPAIRS.items():
                ref["url"] = ref["url"].replace(old, new)
        if key in CORE_NOTES:
            q["explanation"] = CORE_NOTES[key][0]
            if vi is not None: vi["explanation"] = CORE_NOTES[key][1]
        if not q.get("source_refs"):
            codes = q["concept_codes"]
            path = ("indexes-intro.html" if "IDX" in codes else "planner-stats.html" if any(c.startswith("DB-") for c in codes)
                    else "ddl-constraints.html" if "SQL-DDL-KNOW" in codes else "dml.html" if "SQL-DML-KNOW" in codes
                    else "functions-subquery.html" if "SQL-SUBQUERY" in codes else "queries-table-expressions.html")
            q["source_refs"] = [reference(path)]
        if key in ("legacy-essay-index-read-write", "essay-index-workload-tradeoff"):
            q["reference_answer"] = INDEX_SAMPLE
            q["explanation"] = INDEX_SAMPLE
            if vi is not None: vi["explanation"] = INDEX_VI
        if key == "essay-normalization": q["difficulty_level"] = 4
        fix = fixes.get(key)
        if not fix: continue
        if "prompt" in fix: q["prompt"] = fix["prompt"]
        if vi is not None and "vi_prompt" in fix: vi["prompt"] = fix["vi_prompt"]
        if "answer" in fix:
            if kind == "mcq":
                option = next(o for o in q["options"] if o["is_correct"])
                option["option_text"] = fix["answer"]
                if vi is not None: vi["option_texts"][option["option_label"]] = fix["vi_answer"]
            else:
                q["reference_answer"] = fix["answer"]
            if kind != "sql":
                q["explanation"] = fix.get("explanation", fix["answer"])
                if vi is not None: vi["explanation"] = fix.get("vi_explanation", fix.get("vi_answer", vi.get("explanation")))
        if "distractors" in fix:
            for index, option in enumerate(o for o in q["options"] if not o["is_correct"]):
                option["option_text"] = fix["distractors"][index]
                if vi is not None: vi["option_texts"][option["option_label"]] = fix["vi_distractors"][index]
        for old, (new, translated) in fix.get("distractor_replacements", {}).items():
            matches = [o for o in q["options"] if o["option_text"] in (old, new)]
            if len(matches) != 1: raise ValueError(f"Review replacement no longer matches {key}")
            matches[0]["option_text"] = new
            if vi is not None: vi["option_texts"][matches[0]["option_label"]] = translated
        if "explanation" in fix: q["explanation"] = fix["explanation"]
        if vi is not None and "vi_explanation" in fix: vi["explanation"] = fix["vi_explanation"]
        if not any(r["url"].endswith("/" + fix["url"]) for r in q["source_refs"]):
            q["source_refs"].append(reference(fix["url"]))
        if key == "pg-s056":
            for dataset in q["datasets"]:
                if not dataset["is_edge_case"] and "9001" not in dataset["setup_sql"]:
                    dataset["setup_sql"] += " INSERT INTO employees(id,name,mgr_id) VALUES(9001,'Orphan manager reference',9999);"
        if fix.get("edge_setup_append"):
            for dataset in q.get("datasets", []):
                if dataset["is_edge_case"]:
                    if fix["edge_setup_append"] not in dataset["setup_sql"]:
                        dataset["setup_sql"] += " " + fix["edge_setup_append"]
                    if dataset["dataset_name"] == "empty-sales":
                        dataset["dataset_name"] = "boundary-sales"
    # Retired source content is repaired too; stored historical snapshots stay intact.
    legacy = next((q for q in questions if q["key"] == "legacy-essay-index-read-write"), None)
    successor = next((q for q in questions if q["key"] == "essay-index-workload-tradeoff"), None)
    if legacy and successor:
        legacy["rubrics"] = deepcopy(successor["rubrics"])
        if translations is not None:
            translations[legacy["key"]]["rubrics"] = deepcopy(translations[successor["key"]]["rubrics"])
    return questions

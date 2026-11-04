"""Reproducible Vietnamese case corpus and hash-bound PostgreSQL results."""
from collections import Counter
from functools import lru_cache
from hashlib import sha256
import json

from ..config import ROOT_DIR
from .corpus_review import reference
from .practice_config import CELL_QUOTA, DIFFICULTY_LEVELS, QUESTION_TYPES, difficulty_band
from .practice_recipes import RECIPES

RESULTS_PATH = ROOT_DIR / "db/practice_template_results.json"
# Different input classes exercise NULL, duplicate facts, boundaries, rounding,
# whitespace, quoting, non-ASCII and missing JSON/array elements. These are
# actual input changes, not numbered copies of a conceptual description.
CASES = (
    ("biên so sánh và giá trị thiếu", [10, 20, 21.25, -2.5, 0, None], ["alpha", "beta", "rated", "rate", "", None]),
    ("làm tròn âm và khoảng trắng", [-1.5, -2.5, 1.5, 2.5, None, 20], [" Alice ", "alice", "rates", " rated ", None, "a"]),
    ("dòng trùng nhãn và nhóm", [20, 20, 5, 5, 0, None], ["same", "same", "rates", "rate", "A,B", "same"]),
    ("Unicode và định danh cần trích dẫn", [31.25, 9.95, None, 20, 19.99, 0], ["Đà Nẵng", 'a"b', "An", "a_b", "a%b", None]),
    ("nhóm thiếu số tiền và khóa JSON", [None, None, 1, 0, None, 2], [None, "", "A,B,C", "rates", "alpha", None]),
    ("giá trị đúng ngưỡng và mảng rỗng", [19.99, 20, 20.01, 49.99, 50, None], ["a", "A", "ab", "b", "b", "rates"]),
    ("thứ tự đầu vào và các giá trị hòa", [30, 10, 30, None, 10, -10], ["beta", "alpha", "beta", None, "rate", "rates"]),
)


def _literal(value):
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def setup_case(code, variant, *, edge=False):
    _, amounts, labels = CASES[variant % len(CASES)]
    rows = []
    snapshot = code in {"IDX", "PG-INDEX-TYPES", "PG-EXPLAIN", "PG-STATS", "PG-TXN", "PG-MVCC",
                        "PG-LOCK", "PG-CONFIG", "PG-WAL", "PG-BACKUP", "PG-REPLICATION", "PG-MONITOR", "PG-VACUUM"}
    for index, (amount, label) in enumerate(zip(amounts, labels)):
        number = index + 1
        other = (2, 0, None, 3, 5, 2)[index]
        if snapshot:
            amount = abs(amount) if amount is not None else None
            if amount is not None and other is not None:
                if code == "PG-VACUUM":
                    amount, other = min(amount, other), max(amount, other)
                elif code in {"PG-LOCK", "PG-WAL", "PG-BACKUP", "PG-REPLICATION", "PG-MONITOR", "PG-INDEX-TYPES"}:
                    amount, other = max(amount, other), min(amount, other)
        group = "A" if index < 3 else "B"
        if variant == 6:
            group = "B" if index % 2 else "A"
        flag = ("true", "false", "NULL")[index % 3]
        doc = ({"score": amount, "nullable": index % 2 == 0} if index % 3 == 0 else
               {"nullable": False} if index % 3 == 1 else {"score": None})
        array = "'{}'" if index % 3 == 1 else "'{" + f"{number},{number+10},NULL" + "}'"
        date = ("2025-12-31", "2026-01-01", "2026-01-31", "2026-02-01", "2026-02-28", None)[index]
        if edge:
            # A smaller, reordered case with ties and missing values.
            if index not in (0, 2, 5):
                continue
            amount = None if index == 2 else amount
            group = "A"
        rows.append(f"({number},{_literal(group)},{'NULL' if amount is None else amount},{'NULL' if other is None else other},"
                    f"{_literal(label)},{flag},{_literal(json.dumps(doc, ensure_ascii=False))},{array},{_literal(date)})")
    if edge:
        rows.reverse()
    id_definition = "id integer" if code == "DB-2NF" else "id integer PRIMARY KEY"
    key = ",PRIMARY KEY(grp,id)" if code == "DB-2NF" else ""
    return (f"CREATE TABLE cases({id_definition},grp text,n numeric,b numeric,txt text,flag boolean,doc jsonb,arr integer[],day date{key}); "
            "INSERT INTO cases VALUES " + ",".join(rows) + ";")


def case_query(recipe, band):
    base = f"SELECT id,grp,({recipe.expression})::text AS value FROM cases c"
    if band == "EASY":
        return base + " ORDER BY id"
    if band == "MEDIUM":
        return f"WITH evaluated AS ({base}) SELECT grp,value,count(*) AS frequency FROM evaluated GROUP BY grp,value ORDER BY grp,value COLLATE \"C\" NULLS LAST"
    return (f"WITH evaluated AS ({base}), frequencies AS (SELECT grp,value,count(*) AS frequency FROM evaluated GROUP BY grp,value) "
            "SELECT grp,value,frequency,dense_rank() OVER(PARTITION BY grp ORDER BY frequency DESC) AS frequency_rank "
            "FROM frequencies ORDER BY grp,frequency DESC,value COLLATE \"C\" NULLS LAST")


def result_key(setup, query):
    return sha256((setup + "\n" + query).encode("utf-8")).hexdigest()


def raw_cases():
    for code, recipe in sorted(RECIPES.items()):
        for band in DIFFICULTY_LEVELS:
            for variant in range(CELL_QUOTA):
                query = case_query(recipe, band)
                datasets = [{"dataset_name": "Dữ liệu biên" if edge else "Dữ liệu chính",
                    "setup_sql": setup_case(code, variant, edge=edge), "is_edge_case": edge} for edge in (False, True)]
                yield code, recipe, band, variant, query, datasets


def _grid(result):
    return json.dumps({"columns": result["columns"], "rows": result["rows"]}, ensure_ascii=False, separators=(",", ":"))


def _choices(result, offset):
    from copy import deepcopy
    correct = _grid(result)
    wrong = []
    for kind in range(3):
        candidate = deepcopy(result)
        if kind == 0:
            candidate["rows"][0][-1] = "giá trị khác"
        elif kind == 1:
            candidate["rows"] = candidate["rows"] + [candidate["rows"][0]]
        else:
            candidate["rows"] = candidate["rows"][1:]
        wrong.append(_grid(candidate))
    texts = [correct, *wrong]
    texts = texts[offset:] + texts[:offset]
    return [{"option_label": chr(65+i), "option_text": value, "is_correct": value == correct} for i, value in enumerate(texts)]


def _rubric(feature):
    criteria = [
        "Chưa giải thích đúng quy tắc hoặc không đưa được kết quả phù hợp với dữ liệu.",
        f"Nêu được một phần quy tắc {feature}, nhưng kết quả hoặc xử lý dữ liệu biên còn sai đáng kể.",
        "Áp dụng đúng quy tắc và phần lớn kết quả; còn thiếu giải thích một bước xử lý hoặc trường hợp NULL/giá trị biên.",
        f"Giải thích đúng quy tắc {feature}, lần lượt các bước truy vấn, kết quả chính và biên; nêu rõ giới hạn của mô hình khi có snapshot.",
    ]
    return [{"level_name": name, "min_score": lo, "max_score": hi, "criteria": text}
            for name, lo, hi, text in zip(("Incomplete", "Partial", "Mostly Complete", "Complete"),
                (0, 1.01, 2.51, 4.01), (1, 2.5, 4, 5), criteria)]


@lru_cache(maxsize=1)
def template_pack():
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    if results.get("engine") != "PostgreSQL 17" or results.get("executions_per_fixture") != 2:
        raise ValueError("Template results require the recorded double PostgreSQL execution")
    questions = []
    for code, recipe, band, variant, query, datasets in raw_cases():
        for dataset in datasets:
            key = result_key(dataset["setup_sql"], query)
            dataset["expected_result"] = results["results"][key]
        main, edge = (d["expected_result"] for d in datasets)
        scope = ("Giữ từng dòng, trả id, grp, value; sắp id tăng dần." if band == "EASY" else
                 "Gom theo grp và value, đếm frequency bằng COUNT(*); sắp grp rồi value COLLATE C, NULL cuối." if band == "MEDIUM" else
                 "Gom theo grp,value để đếm frequency; DENSE_RANK theo frequency giảm dần trong từng grp. Trả grp,value,frequency,frequency_rank; sắp grp, frequency giảm, value COLLATE C với NULL cuối.")
        transform = f"Yêu cầu nghiệp vụ: {recipe.context}. Quy tắc: {recipe.explanation}"
        data = f"Dữ liệu PostgreSQL cố định ({CASES[variant][0]}):\n{datasets[0]['setup_sql']}"
        sample = (f"{recipe.explanation}\nBiểu thức cho từng dòng là {recipe.expression}. {scope}\n"
                  f"Truy vấn:\n{query}\nKết quả chính: {_grid(main)}\n"
                  f"Dữ liệu biên: {datasets[1]['setup_sql']}\nKết quả biên: {_grid(edge)}. "
                  "Nếu có bước GROUP BY, giá trị NULL trong value vẫn được gom thành nhóm; COUNT(*) đếm cả dòng có value NULL. "
                  "Thứ tự dòng đã được quy định bằng ORDER BY; không phụ thuộc thứ tự INSERT.")
        for kind in QUESTION_TYPES:
            key = f"case-{code.lower()}-{band.lower()}-{variant+1}-{kind}"
            if kind == "mcq":
                prompt = f"{transform}\n{data}\nTruy vấn dưới đây trả bảng kết quả nào?\n{query}\nChọn toàn bộ bảng đúng, kể cả NULL và số lần lặp."
            elif kind == "sql":
                prompt = f"{transform}\n{data}\nViết một SELECT chỉ đọc để tính value là ({recipe.expression})::text. {scope} Không thay đổi dữ liệu hoặc đọc catalog máy chủ."
            else:
                prompt = (f"{transform}\n{data}\nPhân tích truy vấn:\n{query}\n"
                          "Giải thích quy tắc, lần lượt bước tính, đưa toàn bộ kết quả và phân tích NULL/giá trị biên. "
                          f"Đối chiếu thêm dữ liệu biên sau:\n{datasets[1]['setup_sql']}\nNêu giới hạn mô hình nếu bài dùng snapshot.")
            q = {"key": key, "question_type": kind, "original_locale": "vi", "prompt": prompt,
                "difficulty_level": {"EASY": 2, "MEDIUM": 3, "HARD": 5}[band],
                "points": 5 if kind == "essay" else 1, "concept_codes": [code], "required_concept_codes": [],
                "explanation": sample, "source_refs": [reference(recipe.document)], "tags": ["reviewed-case-v1", code, band]}
            if kind == "sql":
                q.update(reference_answer=query, datasets=datasets)
            elif kind == "mcq":
                q["options"] = _choices(main, (variant + list(DIFFICULTY_LEVELS).index(band)) % 4)
            else:
                q.update(reference_answer=sample, rubrics=_rubric(code))
            questions.append(q)
    return {"version": "case-v1", "concepts": [], "clos": [], "dependencies": {}, "assessments": [], "questions": questions}


def coverage(questions, codes):
    counts = Counter((code, difficulty_band(q["difficulty_level"]), q["question_type"])
                     for q in questions if q.get("status") != "retired" for code in q["concept_codes"])
    return {code: {band: {kind: counts[code, band, kind] for kind in QUESTION_TYPES}
                   for band in DIFFICULTY_LEVELS} for code in sorted(codes)}

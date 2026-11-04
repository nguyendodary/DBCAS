"""Deterministic content checks shared by curated packs and live generation.

This verifies a question's executable/structural contract. Factual prose also
requires the recorded editorial review; a documentation URL is not a proof.
"""
from collections import Counter
from decimal import Decimal, InvalidOperation
from functools import lru_cache
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit

from .bank_validation import sql_fixture_problems
from .rubric_validation import rubric_problems
from .sql_result import compare, parse_expected


DOCUMENTATION_VERSION = "18"
QUESTION_TYPES = ("mcq", "sql", "essay")
_BAD_TEXT = re.compile(r"\ufffd|[\u200b-\u200f\u202a-\u202e]|Ã[\x80-\xbf]|Ä[\x80-\xbf]")
_VI_WORDS = re.compile(r"\b(?:nào|gì|của|trong|với|hãy|vì|khi|được|có|không|một|các|giá|trị|là|để|trả|"
    r"giải|thích|đúng|sai|nêu|hiểu|trình|bày|rõ|thiếu|chính|xác|đầy|đủ|cần|đáp|ứng|phân|tích|khóa|"
    r"hàm|chỉ|mục|giao|dịch|sao|lưu|kiểu|dữ|liệu|bảng|cột|truy|vấn|kết|quả|nhóm|giữa|cách|đổi|tạo|"
    r"giữ|định|tính|hợp|lệ|hiện|sử|dụng|bỏ|đề|xuất|biết|chưa|nhưng|hoặc|đưa|ra|theo|từ|đến|"
    r"dòng|chèn|bao|nhiêu|gọi|ghi|cấu|hình|vào|đâu|người|nhận|đã|cấp|tiếp|quyền|bằng|xóa|toàn|bộ|"
    r"chuỗi|phụ|thuộc|ngăn|thu|hồi|bất|ngờ|dùng|cho|mọi|tình|huống)\b", re.I)


def fingerprint(prompt):
    """Ignore cosmetic whitespace and legacy numbered filler suffixes."""
    value = " ".join(unicodedata.normalize("NFKC", prompt or "").casefold().split())
    return re.sub(r"\s*\(tình huống \d+\)\.?$", "", value)


def _value(row, name, default=None):
    return row.get(name, default) if isinstance(row, dict) else getattr(row, name, default)


def text_problems(value, label, *, vietnamese=False):
    if not isinstance(value, str) or len(value.strip()) < 8:
        return [f"{label}: meaningful text required"]
    problems = []
    if _BAD_TEXT.search(value) or any(ord(c) < 32 and c not in "\n\r\t" for c in value):
        problems.append(f"{label}: broken encoding or hidden/control characters")
    if vietnamese and not _VI_WORDS.search(value):
        problems.append(f"{label}: Vietnamese prose required")
    if re.search(r"(?:lorem ipsum|tình huống \d+\)|luôn bỏ qua tính đúng đắn)", value, re.I):
        problems.append(f"{label}: placeholder or trivial filler")
    return problems


def documentation_problems(refs):
    if not isinstance(refs, list) or not refs:
        return ["source_refs: official documentation required"]
    problems = []
    for ref in refs:
        url = _value(ref, "url", "")
        try:
            parsed = urlsplit(url) if isinstance(url, str) else None
        except ValueError:
            parsed = None
        if (parsed is None or parsed.scheme != "https" or parsed.hostname != "www.postgresql.org"
                or not parsed.path.startswith(f"/docs/{DOCUMENTATION_VERSION}/")
                or parsed.username or parsed.password or parsed.query):
            problems.append("source_refs: a versioned official PostgreSQL documentation URL is required")
        elif parsed.path.endswith(("/sql-syntax-expressions.html", "/textsearch-types.html")):
            problems.append("source_refs: obsolete documentation path")
        elif parsed.netloc != "www.postgresql.org" or parsed.path not in _document_paths():
            problems.append("source_refs: documentation page has not been verified")
    return problems


@lru_cache(maxsize=1)
def _document_paths():
    manifest = Path(__file__).resolve().parents[3] / "db/postgres_docs_sources.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return {urlsplit(row["url"]).path for row in data["sources"]}


def question_problems(item, *, known_concepts=None, vietnamese=None, runner=None):
    """Canonical dictionary contract; adapters retain the real answer and data.

    Every served fixture needs a non-empty SQL result, including edge cases.
    Empty-input behavior remains covered by separate negative regression tests.
    Running with a runner checks every fixture twice against its saved result.
    """
    if not isinstance(item, dict):
        return ["schema: question object required"]
    problems = []
    kind = item.get("question_type")
    if kind not in QUESTION_TYPES:
        problems.append("question_type: unknown type")
    problems.extend(text_problems(item.get("prompt"), "prompt", vietnamese=item.get("original_locale") == "vi"))
    problems.extend(text_problems(item.get("explanation"), "explanation", vietnamese=item.get("original_locale") == "vi"))
    problems.extend(documentation_problems(item.get("source_refs")))
    difficulty = item.get("difficulty_level")
    if type(difficulty) is not int or not 1 <= difficulty <= 5:
        problems.append("difficulty_level: integer from 1 to 5 required")
    try:
        points = Decimal(str(item.get("points")))
        if isinstance(item.get("points"), bool) or not points.is_finite() or not 0 < points <= 999.99:
            raise ValueError()
    except (ValueError, InvalidOperation):
        points = Decimal(0)
        problems.append("points: a finite positive score required")
    concepts = item.get("concept_ids", item.get("concept_codes", []))
    if (not isinstance(concepts, list) or not concepts
            or any(type(c) not in (str, int) or not str(c).strip() for c in concepts)
            or len(set(concepts)) != len(concepts)):
        problems.append("concepts: unique nonempty classifications required")
    elif known_concepts is not None and not set(concepts) <= set(known_concepts):
        problems.append("concepts: unknown classification")
    if not set(item.get("required_concept_codes", [])) <= set(item.get("concept_codes", [])):
        problems.append("concepts: required concepts must be tagged")
    options, datasets, rubrics = (item.get(field, []) for field in ("options", "datasets", "rubrics"))
    if any(not isinstance(rows, list) for rows in (options, datasets, rubrics)):
        return [*problems, "schema: options/datasets/rubrics must be lists"]
    if any(not isinstance(row, dict) for rows in (options, datasets, rubrics) for row in rows):
        return [*problems, "schema: child entries must be objects"]
    if (kind != "mcq" and options) or (kind != "sql" and datasets) or (kind != "essay" and rubrics):
        problems.append("schema: type-incompatible fields")
    if kind == "mcq":
        if (not isinstance(options, list) or not 2 <= len(options) <= 6
                or any(type(_value(o, "is_correct")) is not bool for o in options)
                or sum(_value(o, "is_correct", False) is True for o in options) != 1):
            problems.append("options: exactly one correct answer required")
        if any(not isinstance(o.get("option_text"), str) or not isinstance(o.get("option_label"), str) for o in options):
            return [*problems, "options: text and labels must be strings"]
        texts = [unicodedata.normalize("NFKC", _value(o, "option_text", "")).strip() for o in options]
        labels = [_value(o, "option_label") for o in options]
        # Case is meaningful in quoted SQL identifiers and string literals.
        if not all(texts) or len(set(texts)) != len(texts) or len(set(labels)) != len(labels):
            problems.append("options: distinct nonempty labels and choices required")
    if kind == "essay":
        problems.extend(text_problems(item.get("reference_answer"), "sample answer", vietnamese=item.get("original_locale") == "vi"))
        problems.extend(rubric_problems(rubrics, points))
        if item.get("original_locale") == "vi":
            for row in rubrics:
                problems.extend(text_problems(row.get("criteria"), "rubric criteria", vietnamese=True))
    if kind == "sql":
        from types import SimpleNamespace
        if any(set(d) != {"dataset_name", "setup_sql", "expected_result", "is_edge_case"} for d in datasets):
            return [*problems, "SQL: invalid fixture schema"]
        fixture_rows = [SimpleNamespace(**d) if isinstance(d, dict) else d for d in datasets]
        problems.extend(sql_fixture_problems(fixture_rows, item.get("reference_answer"), item.get("required_features", ())))
        primary = [d for d in fixture_rows if not d.is_edge_case]
        if not primary or any(not isinstance(d.expected_result, dict) or not d.expected_result.get("rows") for d in fixture_rows):
            problems.append("SQL: nonempty expected results required for every fixture")
        if re.search(r"\b(?:random|clock_timestamp|statement_timestamp|transaction_timestamp|now)\s*\(|\bCURRENT_(?:DATE|TIME|TIMESTAMP)\b",
                     item.get("reference_answer") or "", re.I):
            problems.append("SQL: time/random-dependent reference")
        if runner is not None and not problems:
            problems.extend(execute_fixtures(runner, fixture_rows, item["reference_answer"]))
    if vietnamese is not None:
        problems.extend(text_problems(vietnamese.get("prompt"), "Vietnamese prompt", vietnamese=True))
        problems.extend(text_problems(vietnamese.get("explanation"), "Vietnamese explanation", vietnamese=True))
        if kind == "mcq":
            translated = vietnamese.get("option_texts", {})
            if set(translated) != {_value(o, "option_label") for o in options}:
                problems.append("Vietnamese options: complete label coverage required")
            normalized = [unicodedata.normalize("NFKC", t).strip() for t in translated.values()]
            if not all(normalized) or len(set(normalized)) != len(normalized):
                problems.append("Vietnamese options: distinct nonempty choices required")
        if kind == "essay":
            translated = vietnamese.get("rubrics", {})
            if set(translated) != {_value(r, "level_name") for r in rubrics}:
                problems.append("Vietnamese rubric: complete level coverage required")
            for row in translated.values():
                problems.extend(text_problems(row.get("criteria"), "Vietnamese rubric criteria", vietnamese=True))
    return problems


def execute_fixtures(runner, datasets, reference):
    problems = []
    for dataset in datasets:
        schema = None
        try:
            schema = runner.provision_dataset(dataset.setup_sql)
            first = runner.execute(reference, schema=schema)
            second = runner.execute(reference, schema=schema)
            expected = parse_expected(dataset.expected_result)
            if not first.success or not second.success or expected is None:
                problems.append(f"SQL {dataset.dataset_name}: execution failed")
            elif compare(first.columns, first.rows, expected, first.column_types).status != "passed":
                problems.append(f"SQL {dataset.dataset_name}: expected result mismatch")
            elif (first.columns != second.columns or Counter(json.dumps(r, sort_keys=True) for r in first.rows)
                  != Counter(json.dumps(r, sort_keys=True) for r in second.rows)):
                problems.append(f"SQL {dataset.dataset_name}: nondeterministic output")
        except Exception as exc:
            problems.append(f"SQL {dataset.dataset_name}: {type(exc).__name__}")
        finally:
            if schema:
                runner.drop_dataset(schema)
    return problems


def bank_problems(packs, translations, *, runner=None):
    concepts = {c["concept_code"] for pack in packs for c in pack["concepts"]}
    keys, prompts, problems = set(), {}, {}
    for pack in packs:
        for item in pack["questions"]:
            key = item.get("key")
            found = []
            if not key or key in keys:
                found.append("key: unique stable question ID required")
            keys.add(key)
            normalized = fingerprint(item.get("prompt"))
            if normalized in prompts:
                found.append(f"prompt: duplicate of {prompts[normalized]}")
            prompts[normalized] = key
            vi = translations.get(key)
            if vi is None and item.get("original_locale", "en") != "vi":
                found.append("Vietnamese translation required")
            found.extend(question_problems(item, known_concepts=concepts, vietnamese=vi, runner=runner))
            if found:
                problems[key] = found
    return problems

"""Validate translated learner content without changing question meaning.

Run from the repository root with ``py -3.13 db/validate_question_localization.py``.
The tool checks source coverage, prose fields, MCQ labels/options, rubric bands,
likely English prose, and protected code/identifier tokens.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_QUESTIONS = 442
PACKS = (
    ROOT / "db/benchmark_pack.json",
    ROOT / "db/sql_knowledge_pack.json",
    ROOT / "db/postgres_knowledge_pack.json",
)
LEAK = re.compile(
    r"\b(?:what does|what is|which of the following|which statement|which command|"
    r"why does|why is|how does|how is|select the|return the|explain why|"
    r"given that|consider the|the following)\b",
    re.I,
)
TECHNICAL_TERMS = {
    "SELECT", "FROM", "WHERE", "JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN",
    "FULL JOIN", "GROUP BY", "HAVING", "ORDER BY", "LIMIT", "OFFSET", "WITH",
    "RECURSIVE", "CASE", "NULL", "COUNT", "SUM", "AVG", "MIN", "MAX",
    "DISTINCT", "UNION", "INTERSECT", "EXCEPT", "INSERT", "UPDATE", "DELETE",
    "CREATE", "ALTER", "DROP", "TABLE", "PRIMARY KEY", "FOREIGN KEY", "CHECK",
    "UNIQUE", "REFERENCES", "JSON", "JSONB", "ARRAY", "CTE", "MVCC", "VACUUM",
    "ANALYZE", "EXPLAIN", "PL/pgSQL", "DDL", "DML", "1NF", "2NF", "3NF", "ER",
    "FD", "B-tree", "GIN", "GiST", "PostgreSQL",
}
TECHNICAL = re.compile(
    r"(?<![\w])(?:" + "|".join(re.escape(token) for token in sorted(TECHNICAL_TERMS, key=len, reverse=True)) + r")(?![\w])",
)
CODE_SPAN = re.compile(r"`([^`]+)`")
OPERATORS = {"->", ">=", "<=", "<>", "!="}
SUSPICIOUS_LOSSY_TEXT = re.compile(r"(?:\w\?\w|\?\w)", re.UNICODE)
SQL_TABLE = re.compile(r"CREATE\s+TABLE\s+([a-zA-Z_]\w*)\s*\((.*?)\);", re.I | re.S)
SQL_COLUMN = re.compile(r"^\s*([a-zA-Z_]\w*)\s+(?:INT|INTEGER|NUMERIC|TEXT|BOOLEAN|DATE|TIMESTAMP|UUID|JSONB)\b", re.I | re.M)


def question_texts(question, translated):
    fields = [translated.get("prompt", ""), translated.get("explanation", "") or ""]
    fields.extend((translated.get("option_texts") or {}).values())
    for rubric in (translated.get("rubrics") or {}).values():
        fields.extend([rubric.get("label", ""), rubric.get("criteria", "")])
    return [item for item in fields if item]


def protected_tokens(question, english_text):
    tokens = set(CODE_SPAN.findall(english_text))
    tokens.update(TECHNICAL.findall(english_text))
    tokens.update(
        token for token in re.findall(r"\b[a-z][a-z0-9]*_[a-z0-9_]+\b", english_text)
        if token != "pg_dumps"  # English plural, not a command or schema identifier.
    )
    tokens.update(re.findall(r"->|>=|<=|<>|!=", english_text))
    identifiers = set()
    for dataset in question.get("datasets", []):
        sql = dataset.get("setup_sql", "")
        for table, body in SQL_TABLE.findall(sql):
            identifiers.add(table)
            identifiers.update(SQL_COLUMN.findall(body))
    for identifier in identifiers:
        if re.search(rf"(?<![\w]){re.escape(identifier)}(?![\w])", english_text):
            tokens.add(identifier)
    return tokens


def token_is_preserved(token, translated_text):
    if token in OPERATORS:
        return token in translated_text
    return re.search(rf"(?<![\w]){re.escape(token)}(?![\w])", translated_text, re.I) is not None


def main():
    manifest = json.loads((ROOT / "db/question_translations_vi.json").read_text(encoding="utf-8"))
    if manifest.get("locale") != "vi":
        raise SystemExit("Translation manifest locale must be vi")
    translations = manifest.get("questions", {})
    questions = []
    pack_errors = []
    for path in PACKS:
        pack = json.loads(path.read_text(encoding="utf-8"))
        if pack.get("translations_manifest") != "db/question_translations_vi.json":
            pack_errors.append(f"{path.name}: missing or incorrect translations_manifest")
        questions.extend((path.name, item) for item in pack.get("questions", []))

    keys = [question.get("key") for _, question in questions]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    missing = []
    errors = list(pack_errors)
    leaked = []
    mcq_counts = {"localized": 0, "total": 0}
    type_counts = {kind: {"localized": 0, "total": 0} for kind in ("mcq", "sql", "essay")}

    for pack_name, question in questions:
        key = question.get("key", "<missing-key>")
        kind = question.get("question_type")
        type_counts.setdefault(kind, {"localized": 0, "total": 0})["total"] += 1
        if kind == "mcq":
            mcq_counts["total"] += 1
        translated = translations.get(key)
        if not translated:
            missing.append(key)
            continue
        type_counts[kind]["localized"] += 1
        if not isinstance(translated.get("prompt"), str) or not translated["prompt"].strip():
            errors.append(f"{key}: missing VI prompt")
        if question.get("explanation") and not (translated.get("explanation") or "").strip():
            errors.append(f"{key}: missing VI explanation")

        english_options = {item["option_label"]: item["option_text"] for item in question.get("options", [])}
        vi_options = translated.get("option_texts", {})
        if set(english_options) != set(vi_options):
            errors.append(f"{key}: translated option labels do not match the canonical MCQ")
        if kind == "mcq":
            if english_options and set(english_options) == set(vi_options):
                mcq_counts["localized"] += 1
                normalized = [str(value).strip().casefold() for value in vi_options.values()]
                if len(normalized) != len(set(normalized)):
                    errors.append(f"{key}: duplicate Vietnamese MCQ options")

        english_rubrics = {item["level_name"] for item in question.get("rubrics", [])}
        vi_rubrics = translated.get("rubrics", {})
        if english_rubrics != set(vi_rubrics):
            errors.append(f"{key}: translated rubric levels do not match the canonical rubric")
        for field in ("prompt", "explanation"):
            english = question.get(field) or ""
            vi = translated.get(field) or ""
            for token in protected_tokens(question, english):
                if not token_is_preserved(token, vi):
                    errors.append(f"{key}: protected token {token!r} missing from VI {field}")
        english_option_text = " ".join(english_options.values())
        vi_option_text = " ".join(vi_options.values())
        for token in protected_tokens(question, english_option_text):
            if not token_is_preserved(token, vi_option_text):
                errors.append(f"{key}: protected option token {token!r} missing in VI")
        english_rubric_text = " ".join(item["criteria"] for item in question.get("rubrics", []))
        vi_rubric_text = " ".join(item.get("criteria", "") for item in vi_rubrics.values())
        for token in protected_tokens(question, english_rubric_text):
            if not token_is_preserved(token, vi_rubric_text):
                errors.append(f"{key}: protected rubric token {token!r} missing in VI")
        for text in question_texts(question, translated):
            if LEAK.search(text):
                leaked.append((key, text))
            if SUSPICIOUS_LOSSY_TEXT.search(text):
                errors.append(f"{key}: suspicious embedded '?' in VI text; possible lossy character encoding")

    extra = sorted(set(translations) - set(keys))
    source_total = len(questions)
    source_counts = {"Core": sum(1 for name, _ in questions if name != "postgres_knowledge_pack.json"),
                     "PostgreSQL": sum(1 for name, _ in questions if name == "postgres_knowledge_pack.json")}
    if source_total != EXPECTED_QUESTIONS:
        errors.append(f"question source count is {source_total}, expected {EXPECTED_QUESTIONS}")
    print(f"Question sources: {source_total}; checked-in core={source_counts['Core']}, PostgreSQL={source_counts['PostgreSQL']}; expected logical bank={EXPECTED_QUESTIONS}")
    print(f"Source coverage: {source_total - len(missing)}/{source_total}; owner target coverage: {source_total - len(missing)}/{EXPECTED_QUESTIONS}")
    for kind, counts in type_counts.items():
        print(f"{kind.upper()}: {counts['localized']}/{counts['total']}")
    print(f"MCQ option translations present: {mcq_counts['localized']}/{mcq_counts['total']}")
    print(f"Missing translations: {len(missing)}; extra translation keys: {len(extra)}")
    print(f"Likely English prose flags: {len(leaked)}")
    print(f"Validation errors: {len(errors)}; duplicate question keys: {duplicates}")
    for key in missing[:20]:
        print(f"MISSING: {key}")
    for key, text in leaked[:20]:
        print(f"ENGLISH-PROSE: {key}: {text[:180]}")
    for error in errors[:30]:
        print(f"ERROR: {error}")
    if missing or extra or errors or leaked or duplicates:
        return 1
    print("PASS: all question translations and integrity checks are complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())

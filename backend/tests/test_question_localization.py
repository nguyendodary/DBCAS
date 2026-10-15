import json
import re
from pathlib import Path
from types import SimpleNamespace as Record

from app.services.question_localization import (
    normalize_locale,
    source_fingerprint,
    translation_problems,
)
from app.benchmark import _validate_pack_translations
from app.errors import AppError
import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_locale_header_selection_is_stable_and_supported():
    assert normalize_locale("vi-VN,vi;q=0.9,en;q=0.8") == "vi"
    assert normalize_locale("en-US,en;q=0.9,vi;q=0.1") == "en"
    assert normalize_locale(None) == "en"


def test_translation_validates_display_options_without_changing_answer_identity():
    question = Record(
        question_type="mcq",
        prompt="Which SELECT clause chooses attributes?",
        explanation=None,
        options=[
            Record(option_label="A", option_text="The projection list"),
            Record(option_label="B", option_text="ORDER BY"),
        ],
        rubrics=[],
    )
    translation = {
        "locale": "vi",
        "prompt": "Mệnh đề SELECT chọn các thuộc tính nào?",
        "explanation": None,
        "option_texts": {"A": "Danh sách thuộc tính", "B": "ORDER BY"},
        "rubrics": {},
    }
    assert translation_problems(question, translation) == []
    answer_identity_before = [(option.option_label, option.option_text == "The projection list") for option in question.options]
    answer_identity_after = [(label, label == "A") for label in translation["option_texts"]]
    assert answer_identity_before == answer_identity_after
    translation["option_texts"] = {"A": "Trùng", "B": "Trùng"}
    assert any("duplicate" in problem for problem in translation_problems(question, translation))


def test_translation_fingerprint_marks_canonical_edits_stale():
    question = Record(
        question_type="sql",
        prompt="Return id from sales.",
        explanation=None,
        options=[],
        rubrics=[],
    )
    original = source_fingerprint(question)
    question.prompt = "Return id and amount from sales."
    assert source_fingerprint(question) != original


def test_source_pack_manifest_uses_stable_question_keys_and_preserves_mcq_labels():
    manifest = json.loads((ROOT / "db/question_translations_vi.json").read_text(encoding="utf-8"))
    assert manifest["locale"] == "vi"
    translated = manifest["questions"]
    sources = {}
    for filename in ("benchmark_pack.json", "sql_knowledge_pack.json", "postgres_knowledge_pack.json"):
        pack = json.loads((ROOT / "db" / filename).read_text(encoding="utf-8"))
        assert pack["translations_manifest"] == "db/question_translations_vi.json"
        sources.update({question["key"]: question for question in pack["questions"]})
    assert set(translated).issubset(sources)
    for key, item in translated.items():
        source = sources[key]
        option_labels = {option["option_label"] for option in source.get("options", [])}
        assert set(item.get("option_texts", {})) == option_labels
        normalized_options = [value.strip().casefold() for value in item.get("option_texts", {}).values()]
        assert len(normalized_options) == len(set(normalized_options))
        protected = set(re.findall(r"\b[A-Z][A-Z0-9_]{1,}\b|\b[a-z][a-z0-9]*_[a-z0-9_]+\b|->|>=|<=|<>|!=", source["prompt"]))
        # ID is ordinary English in prompts such as "sale ID"; the actual
        # lower-case schema identifier `id` is separately protected from DDL.
        protected.discard("ID")
        assert all(re.search(rf"(?<![\w]){re.escape(token)}(?![\w])", item["prompt"], re.I) for token in protected)


def test_import_preflight_rejects_a_missing_translation_before_any_writes():
    pack = json.loads((ROOT / "db/benchmark_pack.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "db/question_translations_vi.json").read_text(encoding="utf-8"))
    _validate_pack_translations(pack, manifest)
    incomplete = json.loads(json.dumps(manifest))
    incomplete["questions"].pop(pack["questions"][0]["key"])
    with pytest.raises(AppError) as raised:
        _validate_pack_translations(pack, incomplete)
    assert raised.value.code == "question_translation_incomplete"

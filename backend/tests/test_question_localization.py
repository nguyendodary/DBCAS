import json
import re
import runpy
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
protected_question_tokens = runpy.run_path(
    str(ROOT / "db/validate_question_localization.py")
)["protected_tokens"]


def test_locale_header_selection_is_stable_and_supported():
    assert normalize_locale("vi-VN,vi;q=0.9,en;q=0.8") == "vi"
    assert normalize_locale("en-US,en;q=0.9,vi;q=0.1") == "en"
    assert normalize_locale(None) == "en"


def test_vietnamese_essay_feedback_keeps_canonical_english_grading_contract():
    from decimal import Decimal
    from app.models import Question
    from app.services.essay_grading import grade_essay
    from test_essay_grading import StubLLM, _rubrics_model

    answer = "Giải thích đầy đủ về chuẩn hóa."
    provider = StubLLM(response={"rubric_level": "Complete", "score": 10,
        "explanation": "Câu trả lời đáp ứng tiêu chí.", "feedback": "Hãy luyện tập thêm.",
        "matched_criteria": ["Giải thích đầy đủ"], "missing_concepts": [], "evidence": [answer]})
    question = Question(question_type="essay", prompt="Explain normalization.", points=Decimal("10"))
    result = grade_essay(question, _rubrics_model(), answer, provider, locale="vi")
    prompt = provider.calls[0]["messages"][-1].content
    assert "Explain normalization." in prompt and "Fully correct" in prompt
    assert "in natural Vietnamese" in prompt
    assert result["score"] == Decimal("10")
    assert result["grading_detail"]["rubric_level"] == "Complete"
    assert result["grading_detail"]["explanation"] == "Câu trả lời đáp ứng tiêu chí."


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
        protected = protected_question_tokens(source, source["prompt"])
        # ID is ordinary English in prompts such as "sale ID"; the actual
        # lower-case schema identifier `id` is separately protected from DDL.
        protected.discard("ID")
        missing = [
            token
            for token in protected
            if (
                token not in {"->", ">=", "<=", "<>", "!="}
                and not re.search(rf"(?<![\w]){re.escape(token)}(?![\w])", item["prompt"], re.I)
            )
            or (token in {"->", ">=", "<=", "<>", "!="} and token not in item["prompt"])
        ]
        assert not missing, f"{key}: protected tokens missing from VI prompt: {sorted(missing)}"


def test_recovered_core_records_preserve_answers_fixtures_and_rubric():
    pack = json.loads((ROOT / "db/benchmark_pack.json").read_text(encoding="utf-8"))
    recovered = {
        question["key"]: question
        for question in pack["questions"]
        if question["key"].startswith("legacy-")
    }
    assert set(recovered) == {
        "legacy-mcq-select-filter",
        "legacy-mcq-inner-join",
        "legacy-sql-customer-names",
        "legacy-essay-index-read-write",
    }

    for key in ("legacy-mcq-select-filter", "legacy-mcq-inner-join"):
        question = recovered[key]
        assert len(question["options"]) == 4
        assert [option["option_label"] for option in question["options"] if option["is_correct"]] == ["A"]

    sql = recovered["legacy-sql-customer-names"]
    assert sql["reference_answer"] == "SELECT name FROM customers"
    assert [(row["dataset_name"], row["is_edge_case"]) for row in sql["datasets"]] == [
        ("basic", False),
        ("edge", True),
    ]
    assert sql["datasets"][0]["expected_result"] == {"columns": ["name"], "rows": [["Alice"]]}
    assert sql["datasets"][1]["expected_result"] == {"columns": ["name"], "rows": []}

    essay = recovered["legacy-essay-index-read-write"]
    assert essay["points"] == 5 and essay["difficulty_level"] == 3
    assert essay["status"] == "retired"
    assert essay["rubrics"] == [
        {"level_name": "Missing", "min_score": 0, "max_score": 0,
         "criteria": "No relevant content"},
        {"level_name": "Partial", "min_score": 1, "max_score": 3, "criteria": "Mentions lookup benefit OR write cost"},
        {"level_name": "Complete", "min_score": 4, "max_score": 5, "criteria": "Covers B-tree lookup cost and write amplification"},
    ]
    successor = next(question for question in pack["questions"] if question["key"] == "essay-index-workload-tradeoff")
    assert successor["concept_codes"] == ["IDX"] and successor["points"] == 5
    assert len(successor["rubrics"]) == 4


def test_import_preflight_rejects_a_missing_translation_before_any_writes():
    pack = json.loads((ROOT / "db/benchmark_pack.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "db/question_translations_vi.json").read_text(encoding="utf-8"))
    _validate_pack_translations(pack, manifest)
    incomplete = json.loads(json.dumps(manifest))
    incomplete["questions"].pop(pack["questions"][0]["key"])
    with pytest.raises(AppError) as raised:
        _validate_pack_translations(pack, incomplete)
    assert raised.value.code == "question_translation_incomplete"


@pytest.mark.parametrize("kind", ["mcq", "sql", "essay"])
@pytest.mark.parametrize("locale", ["en", "vi"])
def test_session_display_and_evidence_keep_locale_answers_and_snapshot(client, db_session, kind, locale):
    from test_draft_lifecycle import _fixture, _save
    from app.repositories import AssessmentRepository
    from app.services.evidence_context import capture_question, question_view
    from app.services.question_localization import upsert_question_translations

    _, session, attempt, question, _, headers, answer = _fixture(db_session, kind, locale)
    translated = {"locale": "vi", "prompt": "Nội dung câu hỏi bằng tiếng Việt.",
                  "option_texts": {o.option_label: "Đáp án " + o.option_label for o in question.options},
                  "rubrics": {r.level_name: {"label": "Mức " + str(i), "criteria": "Tiêu chí đánh giá."}
                              for i, r in enumerate(question.rubrics)}}
    upsert_question_translations(db_session, question, [translated])
    attempt.question_snapshot = capture_question(AssessmentRepository(db_session), question)
    db_session.commit()
    original_snapshot = json.loads(json.dumps(attempt.question_snapshot))
    assert question_view(attempt).prompt == "Original prompt"
    if kind == "essay":
        assert all(r.criteria.startswith("Criteria for ") for r in question_view(attempt).rubrics)
        assert all(r.criteria == "Tiêu chí đánh giá." for r in question_view(attempt, "vi").rubrics)
    assert _save(client, session, question, headers, answer).status_code == 200
    expected_prompt = translated["prompt"] if locale == "vi" else "Original prompt"
    for requested in ("vi", "en", "vi"):
        response = client.get(f"/api/v1/sessions/{session.session_id}",
                              headers={**headers, "Accept-Language": requested})
        assert response.status_code == 200, response.json()
        state = response.json()
        assert state["locale"] == locale
        assert state["current_question"]["prompt"] == expected_prompt
        assert state["current_question"]["draft"] == answer
        assert state["current_question"]["question_id"] == question.question_id
        assert __import__("datetime").datetime.fromisoformat(state["expires_at"]) == session.expires_at
    # Finishing with an empty persisted answer avoids any external grading call.
    assert _save(client, session, question, headers, {}, revision=2).status_code == 200
    assert client.post(f"/api/v1/sessions/{session.session_id}/finish", headers=headers).status_code == 200
    evidence = client.get(f"/api/v1/sessions/{session.session_id}/evidence", headers=headers)
    assert evidence.status_code == 200, evidence.json()
    assert evidence.json()["items"][0]["prompt"] == expected_prompt
    if kind == "essay":
        bands = evidence.json()["items"][0]["rubrics"]
        assert len(bands) == 4
        assert all(band["criteria"] == ("Tiêu chí đánh giá." if locale == "vi" else
                                       next(r.criteria for r in question.rubrics if r.level_name == band["level_name"]))
                   for band in bands)
    db_session.refresh(attempt)
    assert attempt.question_snapshot == original_snapshot
    # Old snapshots carry no translation payload and remain canonical English.
    legacy = {key: value for key, value in original_snapshot.items() if key != "localized_content"}
    legacy["version"] = 1
    historical = Record(question_snapshot=legacy)
    assert question_view(historical, "vi").prompt == "Original prompt"
    assert historical.question_snapshot == legacy

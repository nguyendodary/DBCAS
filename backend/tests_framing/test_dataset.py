"""Synthetic session generator tests: production shape, split by session, no PII."""
from __future__ import annotations

import json

from app.services.framing.dataset import generate, write_dataset
from app.services.framing.scanner import scan_text
from app.services.framing.util import canonical
from app.services.framing.validator import Framing, assemble_prompt, validate_prompt


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)


def test_generator_is_deterministic_and_splits_by_session():
    first = generate(30, seed=7, large_every=0)
    second = generate(30, seed=7, large_every=0)
    assert first.dataset_hash == second.dataset_hash
    assert first.counts == {"train": 21, "validation": 4, "test": 5}
    assert len(first.sessions) == 30
    assert len(set(session["session_id"] for session in first.sessions)) == 30
    split_ids = {}
    for split in ("train", "validation", "test"):
        for session in first.sessions:
            if session["split"] == split:
                split_ids.setdefault(split, set()).add(session["session_id"])
    assert not (split_ids["train"] & split_ids["validation"])
    assert not (split_ids["train"] & split_ids["test"])
    assert not (split_ids["validation"] & split_ids["test"])
    assert set().union(*split_ids.values()) == {session["session_id"] for session in first.sessions}


def test_session_shape_and_brief_do_not_contain_answers():
    bundle = generate(24, seed=11, large_every=0)
    for session in bundle.sessions:
        data, brief, target = session["data"], session["brief"], session["target"]
        assert set(data) >= {"version", "mode", "attempt_count", "score", "history", "dimensions",
                             "items", "recurring_weaknesses", "evidence_hash", "details_truncated"}
        assert data["version"] == "two-ai-v4"
        assert session["source_question_ids"] == [item["question_id"] for item in data["items"]]
        for item in data["items"]:
            assert set(item) >= {"attempt_id", "question_id", "type", "prompt", "answer", "points",
                                 "score", "reference_answer", "options", "concepts", "clo", "topics",
                                 "difficulty", "rubric"}
            if len(item["answer"]) >= 8:
                assert canonical(item["answer"]) not in canonical(brief)
        assert set(brief) == {"mode", "attempt_count", "score_percentage", "weak_concepts",
                              "strong_concepts", "essay_count", "mcq_count", "sql_count", "trend",
                              "details_truncated"}
        assert target["status"] == "draft" and target["reviewed_by"] is None
        assert len(session["session_hash"]) == 64
        assert len(bundle.dataset_hash) == 64
        assert len(bundle.fixture_hash) == 64


def test_generated_data_has_no_pii_or_secret_findings():
    bundle = generate(20, seed=3, large_every=0)
    for session in bundle.sessions:
        for text in _strings({"data": session["data"], "brief": session["brief"], "target": session["target"]}):
            assert scan_text(text) == [], text[:80]


def test_target_framing_passes_the_reference_validator():
    bundle = generate(12, seed=5, large_every=0)
    schema = {"title": "Evaluation", "type": "object", "additionalProperties": False}
    checked = 0
    for session in bundle.sessions:
        target = session["target"]
        if not target["focus_concepts"]:
            continue
        framing = Framing(
            task_text=target["task_text"],
            focus_text=target["focus_text"],
            focus_concepts=tuple(target["focus_concepts"]),
            format_text=target["format_text"],
        )
        prompt = assemble_prompt(session["data"], schema, framing, brief=session["brief"])
        result = validate_prompt(prompt, session["data"], schema, framing, brief=session["brief"])
        assert result.ok, (session["session_id"], result.reason_code)
        checked += 1
    assert checked > 0


def test_write_dataset_manifest(tmp_path):
    bundle = generate(12, seed=9, large_every=0)
    manifest = write_dataset(bundle, tmp_path)
    assert manifest["dataset_hash"] == bundle.dataset_hash
    assert manifest["total"] == 12
    assert manifest["pii_findings"] == 0
    assert (tmp_path / "manifest.json").exists()
    assert len((tmp_path / "sessions.jsonl").read_text(encoding="utf-8").splitlines()) == 12
    for split in ("train", "validation", "test"):
        assert (tmp_path / f"{split}.jsonl").exists()
    loaded = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert loaded["counts"] == bundle.counts

"""Question display translations, separate from scoring and SQL data."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone

from ..errors import AppError
from ..models import QuestionTranslation

logger = logging.getLogger("dbcas.questions.localization")


def normalize_locale(value: str | None) -> str:
    """Select the supported question locale from an Accept-Language value."""
    value = (value or "en").split(",", 1)[0].split(";", 1)[0].strip().lower()
    if value.startswith("vi"):
        return "vi"
    return "en"


def source_fingerprint(question) -> str:
    """Bind each translation to the exact canonical prose/options/rubric."""
    source = {
        "question_type": question.question_type,
        "prompt": question.prompt,
        "explanation": question.explanation,
        "options": [
            {"label": o.option_label, "text": o.option_text}
            for o in sorted(question.options, key=lambda o: o.option_label)
        ],
        "rubrics": [
            {"level": r.level_name, "criteria": r.criteria}
            for r in sorted(question.rubrics, key=lambda r: r.level_name)
        ],
    }
    raw = json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def translation_is_current(question, translation) -> bool:
    return translation.source_hash == source_fingerprint(question)


def translation_problems(question, translation) -> list[str]:
    if hasattr(translation, "model_dump"):
        translation = translation.model_dump()
    if not isinstance(translation, dict):
        return ["translation must be an object"]
    get = translation.get
    option_texts = get("option_texts") or {}
    translated_rubrics = get("rubrics") or {}
    problems = []
    if get("locale") == "en":
        problems.append("English is canonical; store translations under a non-English locale")
    prompt = get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        problems.append("translated prompt is required")
    explanation = get("explanation")
    if question.explanation and (not isinstance(explanation, str) or not explanation.strip()):
        problems.append("translated explanation is required when the canonical explanation is present")

    option_labels = [o.option_label for o in question.options]
    if len(option_labels) != len(set(option_labels)):
        problems.append("canonical MCQ option labels must be unique translation keys")
    expected_options = set(option_labels)
    if not isinstance(option_texts, dict):
        problems.append("translated MCQ options must be an object keyed by canonical option labels")
        option_texts = {}
    actual_options = set(option_texts)
    if expected_options != actual_options:
        problems.append("translated MCQ options must match every canonical option label")
    if any(not isinstance(text, str) or not text.strip() for text in option_texts.values()):
        problems.append("translated MCQ options must be nonempty text")
    normalized = [text.strip().casefold() for text in option_texts.values() if isinstance(text, str)]
    if len(normalized) != len(set(normalized)):
        problems.append("translated MCQ options must not duplicate one another")

    rubric_levels = [r.level_name for r in question.rubrics]
    if len(rubric_levels) != len(set(rubric_levels)):
        problems.append("canonical rubric level names must be unique translation keys")
    expected_rubrics = set(rubric_levels)
    if not isinstance(translated_rubrics, dict):
        problems.append("translated rubric bands must be an object keyed by canonical rubric level")
        translated_rubrics = {}
    actual_rubrics = set(translated_rubrics)
    if expected_rubrics != actual_rubrics:
        problems.append("translated rubric bands must match every canonical level name")
    for level, row in translated_rubrics.items():
        if not isinstance(row, dict):
            problems.append(f"translated rubric band {level!r} must be an object")
            continue
        label = row.get("label")
        criteria = row.get("criteria")
        if not isinstance(label, str) or not label.strip() or not isinstance(criteria, str) or not criteria.strip():
            problems.append(f"translated rubric band {level!r} needs a label and criteria")
    if question.question_type != "mcq" and actual_options:
        problems.append("only MCQ translations may contain option text")
    if question.question_type != "essay" and actual_rubrics:
        problems.append("only Essay translations may contain rubric text")
    return problems


def upsert_question_translations(db, question, translations) -> None:
    """Upsert provided locales without touching answer keys or technical data."""
    translations = translations or []
    if not translations:
        return
    db.flush()
    db.expire(question, ["options", "rubrics"])
    for item in translations or []:
        translation = item.model_dump() if hasattr(item, "model_dump") else dict(item)
        if translation.get("locale") == "en":
            raise AppError(422, "invalid_question_translation", "English is the canonical question content")
        problems = translation_problems(question, translation)
        if problems:
            raise AppError(
                422,
                "invalid_question_translation",
                "Question translation does not match its canonical content",
                details=[{"problem": problem} for problem in problems],
            )
        row = next((existing for existing in question.translations if existing.locale == translation["locale"]), None)
        if row is None:
            row = QuestionTranslation(question_id=question.question_id, locale=translation["locale"])
            db.add(row)
            question.translations.append(row)
        row.source_hash = source_fingerprint(question)
        row.prompt = translation["prompt"].strip()
        row.explanation = (translation.get("explanation") or "").strip() or None
        row.option_texts = {key: value.strip() for key, value in translation.get("option_texts", {}).items()}
        row.rubrics = {
            key: {
                "label": (value.label if hasattr(value, "label") else value["label"]).strip(),
                "criteria": (value.criteria if hasattr(value, "criteria") else value["criteria"]).strip(),
            }
            for key, value in translation.get("rubrics", {}).items()
        }
        row.updated_at = datetime.now(timezone.utc)
    db.flush()


def display_content(question, locale: str) -> tuple[dict, str]:
    """Return a requested display locale, falling back to canonical English."""
    canonical = {
        "prompt": question.prompt,
        "explanation": question.explanation,
        "option_texts": {o.option_label: o.option_text for o in question.options},
        "rubrics": {
            r.level_name: {"label": r.level_name, "criteria": r.criteria}
            for r in question.rubrics
        },
    }
    if locale == "en":
        return canonical, "en"
    row = next((item for item in question.translations if item.locale == locale), None)
    if row is None or not translation_is_current(question, row):
        logger.warning("Question %s is missing a current %s translation; using English", question.question_id, locale)
        return canonical, "en"
    return {
        "prompt": row.prompt,
        "explanation": row.explanation,
        "option_texts": row.option_texts or {},
        "rubrics": row.rubrics or {},
    }, locale

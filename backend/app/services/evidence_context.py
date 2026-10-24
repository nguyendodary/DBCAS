"""Immutable assessment/question context captured when a session/item starts."""
import logging
from decimal import Decimal
from types import SimpleNamespace as Record

logger = logging.getLogger("dbcas.questions.localization")


def capture_assessment(assessment):
    fields = ("assessment_id", "title", "description", "max_questions", "duration_min", "target_mcq", "target_sql", "target_essay", "result_release_policy")
    result = {key: getattr(assessment, key) for key in fields}
    result.update(version=1, assessment_version=getattr(assessment, "version_no", 1), concepts=[{
        "concept_id": t.concept_id, "concept_code": t.concept.concept_code,
        "concept_name": t.concept.concept_name, "subject_area": t.concept.subject_area,
        "description": t.concept.description, "min_difficulty": t.min_difficulty,
        "keywords": t.concept.keywords, "learning_objectives": t.concept.learning_objectives,
        "max_difficulty": t.max_difficulty, "target_pct": str(t.target_pct),
    } for t in sorted(assessment.targets, key=lambda t: t.concept_id)])
    return result


def capture_question(repo, question):
    from .question_localization import translation_is_current

    fields = ("question_id", "question_type", "prompt", "reference_answer", "difficulty_level", "explanation")
    result = {key: getattr(question, key) for key in fields}
    result["original_locale"] = getattr(question, "original_locale", None) or "en"
    result.update(version=3, question_version=getattr(question, "version_no", 1), points=str(question.points), concepts=[{
        "concept_id": t.concept_id, "concept_code": t.concept.concept_code,
        "concept_name": t.concept.concept_name, "subject_area": t.concept.subject_area,
        "description": t.concept.description, "confirmed": True, "is_required": t.is_required,
        "sql_feature": getattr(t.concept, "sql_feature", None),
        "keywords": t.concept.keywords, "learning_objectives": t.concept.learning_objectives,
    } for t in sorted(question.concept_tags, key=lambda t: t.concept_id) if t.confirmed])
    result["options"] = [{key: getattr(o, key) for key in ("option_id", "option_label", "option_text", "is_correct")} for o in question.options] if question.question_type == "mcq" else []
    result["datasets"] = [{key: getattr(d, key) for key in ("dataset_id", "dataset_name", "setup_sql", "expected_result", "is_edge_case")} for d in repo.get_datasets_for_question(question.question_id)] if question.question_type == "sql" else []
    result["rubrics"] = [{"level_name": r.level_name, "min_score": str(r.min_score), "max_score": str(r.max_score), "criteria": r.criteria} for r in repo.get_rubrics_for_question(question.question_id)] if question.question_type == "essay" else []
    result["localized_content"] = {
        item.locale: {
            "prompt": item.prompt,
            "explanation": item.explanation,
            "option_texts": item.option_texts or {},
            "rubrics": item.rubrics or {},
        }
        for item in question.translations
        if translation_is_current(question, item)
    }
    return result


def question_view(attempt, locale=None):
    snapshot = attempt.question_snapshot
    if not snapshot:
        if locale is None:
            return attempt.question
        from .question_localization import display_content
        question = attempt.question
        # No captured provenance exists for translations on these legacy rows.
        # A later bank translation cannot become historical assessment content.
        original_locale = getattr(question, "original_locale", None) or "en"
        content, content_locale = display_content(question, original_locale)
        fields = {key: getattr(question, key) for key in ("question_id", "question_type", "reference_answer", "difficulty_level", "points", "concept_tags", "datasets", "rubrics")}
        fields.update(prompt=content["prompt"], explanation=content["explanation"], content_locale=content_locale,
                      original_locale=getattr(question, "original_locale", None) or "en")
        fields["options"] = [Record(option_id=o.option_id, option_label=o.option_label, is_correct=o.is_correct,
                                    option_text=content["option_texts"][o.option_label]) for o in question.options]
        fields["rubrics"] = [Record(level_name=r.level_name, min_score=r.min_score, max_score=r.max_score,
                                    display_label=content["rubrics"][r.level_name]["label"],
                                    criteria=content["rubrics"][r.level_name]["criteria"]) for r in question.rubrics]
        return Record(**fields)
    fields = {key: snapshot.get(key) for key in ("question_id", "question_type", "prompt", "reference_answer", "difficulty_level", "explanation")}
    fields["points"] = Decimal(str(snapshot["points"]))
    fields["concept_tags"] = [Record(concept_id=c["concept_id"], confirmed=c.get("confirmed", True), is_required=c.get("is_required", False), concept=Record(**c)) for c in snapshot.get("concepts", [])]
    fields["options"] = [Record(**o) for o in snapshot.get("options", [])]
    fields["datasets"] = [Record(**d) for d in snapshot.get("datasets", [])]
    fields["rubrics"] = [Record(**{**r, "min_score": Decimal(str(r["min_score"])), "max_score": Decimal(str(r["max_score"]))}) for r in snapshot.get("rubrics", [])]
    original_locale = snapshot.get("original_locale", "en")
    fields["original_locale"] = original_locale
    localized = (snapshot.get("localized_content") or {}).get(locale) if locale and locale != original_locale else None
    if localized:
        fields["prompt"] = localized["prompt"]
        fields["explanation"] = localized.get("explanation")
        option_texts = localized.get("option_texts") or {}
        fields["options"] = [Record(**{**o.__dict__, "option_text": option_texts.get(o.option_label, o.option_text)}) for o in fields["options"]]
        rubric_rows = localized.get("rubrics") or {}
        fields["rubrics"] = [Record(**{**r.__dict__, "display_label": rubric_rows.get(r.level_name, {}).get("label", r.level_name), "criteria": rubric_rows.get(r.level_name, {}).get("criteria", r.criteria)}) for r in fields["rubrics"]]
        fields["content_locale"] = locale
    else:
        if locale and locale != original_locale:
            logger.warning(
                "Question %s snapshot is missing %s display content; using %s",
                snapshot.get("question_id"), locale, original_locale,
            )
        fields["content_locale"] = original_locale
    return Record(**fields)


def assessment_view(session, repo):
    if not session.config_snapshot:
        return repo.get_assessment(session.assessment_id)
    snapshot = session.config_snapshot
    fields = {key: snapshot.get(key) for key in ("assessment_id", "title", "description", "max_questions", "duration_min", "target_mcq", "target_sql", "target_essay")}
    fields["targets"] = [Record(concept_id=c["concept_id"], min_difficulty=c["min_difficulty"], max_difficulty=c["max_difficulty"], target_pct=Decimal(str(c["target_pct"])), concept=Record(**c)) for c in snapshot.get("concepts", [])]
    return Record(**fields)


def targets_for_session(session, repo):
    if session.config_snapshot:
        return {c["concept_id"]: Decimal(str(c["target_pct"])) for c in session.config_snapshot.get("concepts", [])}
    return repo.assessment_targets(session.assessment_id)


def concept_context(session, concept):
    for item in (session.config_snapshot or {}).get("concepts", []):
        if item["concept_id"] == concept.concept_id:
            return Record(**item)
    return concept

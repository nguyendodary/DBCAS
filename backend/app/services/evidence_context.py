"""Immutable assessment/question context captured when a session/item starts."""
from decimal import Decimal
from types import SimpleNamespace as Record


def capture_assessment(assessment):
    fields = ("assessment_id", "title", "description", "max_questions", "duration_min", "target_mcq", "target_sql", "target_essay")
    result = {key: getattr(assessment, key) for key in fields}
    result.update(version=1, assessment_version=getattr(assessment, "version_no", 1), concepts=[{
        "concept_id": t.concept_id, "concept_code": t.concept.concept_code,
        "concept_name": t.concept.concept_name, "subject_area": t.concept.subject_area,
        "description": t.concept.description, "min_difficulty": t.min_difficulty,
        "max_difficulty": t.max_difficulty, "target_pct": str(t.target_pct),
    } for t in sorted(assessment.targets, key=lambda t: t.concept_id)])
    return result


def capture_question(repo, question):
    fields = ("question_id", "question_type", "prompt", "reference_answer", "difficulty_level")
    result = {key: getattr(question, key) for key in fields}
    result.update(version=1, question_version=getattr(question, "version_no", 1), points=str(question.points), concepts=[{
        "concept_id": t.concept_id, "concept_code": t.concept.concept_code,
        "concept_name": t.concept.concept_name, "subject_area": t.concept.subject_area,
        "description": t.concept.description, "confirmed": True, "is_required": t.is_required,
        "sql_feature": getattr(t.concept, "sql_feature", None),
    } for t in sorted(question.concept_tags, key=lambda t: t.concept_id) if t.confirmed])
    result["options"] = [{key: getattr(o, key) for key in ("option_id", "option_label", "option_text", "is_correct")} for o in question.options] if question.question_type == "mcq" else []
    result["datasets"] = [{key: getattr(d, key) for key in ("dataset_id", "dataset_name", "setup_sql", "expected_result", "is_edge_case")} for d in repo.get_datasets_for_question(question.question_id)] if question.question_type == "sql" else []
    result["rubrics"] = [{"level_name": r.level_name, "min_score": str(r.min_score), "max_score": str(r.max_score), "criteria": r.criteria} for r in repo.get_rubrics_for_question(question.question_id)] if question.question_type == "essay" else []
    return result


def question_view(attempt):
    snapshot = attempt.question_snapshot
    if not snapshot:
        return attempt.question
    fields = {key: snapshot.get(key) for key in ("question_id", "question_type", "prompt", "reference_answer", "difficulty_level")}
    fields["points"] = Decimal(str(snapshot["points"]))
    fields["concept_tags"] = [Record(concept_id=c["concept_id"], confirmed=c.get("confirmed", True), is_required=c.get("is_required", False), concept=Record(**c)) for c in snapshot.get("concepts", [])]
    fields["options"] = [Record(**o) for o in snapshot.get("options", [])]
    fields["datasets"] = [Record(**d) for d in snapshot.get("datasets", [])]
    fields["rubrics"] = [Record(**{**r, "min_score": Decimal(str(r["min_score"])), "max_score": Decimal(str(r["max_score"]))}) for r in snapshot.get("rubrics", [])]
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

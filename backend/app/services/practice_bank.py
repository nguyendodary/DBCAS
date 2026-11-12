"""Efficient bank metadata selection, then full validation of selected content."""
from decimal import Decimal

from sqlalchemy import func, select

from ..errors import AppError
from ..models import Concept, ConceptDependency, Question, QuestionConcept, McqOption, Rubric, SqlTestDataset
from ..repositories import QuestionRepository
from .practice_generation import template_candidates, type_targets, validated_template
from .practice_selection import Candidate, Catalog, PreparedPlan, complete_batch, mixed_plan, recovered_plan, disclosure
from .question_localization import translation_is_current
from .question_validator import question_problems, fingerprint


def canonical_question(question):
    return {"question_type": question.question_type, "original_locale": question.original_locale,
        "prompt": question.prompt, "explanation": question.explanation, "reference_answer": question.reference_answer,
        "points": str(question.points), "difficulty_level": question.difficulty_level, "source_refs": question.source_refs,
        "concept_ids": [t.concept_id for t in question.concept_tags if t.confirmed],
        "required_features": [t.concept.sql_feature for t in question.concept_tags if t.confirmed and t.is_required],
        "options": [{k: getattr(o, k) for k in ("option_label", "option_text", "is_correct")} for o in question.options],
        "datasets": [{k: getattr(d, k) for k in ("dataset_name", "setup_sql", "expected_result", "is_edge_case")} for d in question.datasets],
        "rubrics": [{k: getattr(r, k) for k in ("level_name", "min_score", "max_score", "criteria")} for r in question.rubrics]}


def content_errors(question):
    translated = next((t for t in question.translations if t.locale == "vi" and translation_is_current(question, t)), None)
    vi = {k: getattr(translated, k) for k in ("prompt", "explanation", "option_texts", "rubrics")} if translated else None
    errors = question_problems(canonical_question(question), vietnamese=vi)
    if question.original_locale != "vi" and vi is None:
        errors.append("Vietnamese translation required")
    return errors


def bank_catalog(db):
    rows = db.execute(select(Question.question_id, Question.question_type, Question.difficulty_level,
        Question.family_id, Question.prompt, func.array_agg(QuestionConcept.concept_id))
        .join(QuestionConcept, QuestionConcept.question_id == Question.question_id)
        .where(Question.status == "validated", Question.source == "bank", QuestionConcept.confirmed.is_(True))
        .group_by(Question.question_id).order_by(Question.question_id))
    return [Candidate(qid, kind, level, frozenset(ids), family or qid, fingerprint(prompt), qid)
            for qid, kind, level, family, prompt, ids in rows]


def _persist(db, item, learner, origin):
    q = Question(question_type=item["question_type"], prompt=item["prompt"], original_locale="vi",
        reference_answer=item["reference_answer"], explanation=item["explanation"],
        source_refs=[{"url": url, "version": "18"} for url in item["source_refs"]],
        difficulty_level=item["difficulty_level"], points=Decimal(item["points"]),
        source="ai_generated", status="draft", created_by=learner.account_id,
        ai_review={"purpose": "learner_practice", "origin": origin})
    db.add(q); db.flush()
    db.add_all([QuestionConcept(question_id=q.question_id, concept_id=cid, tag_source="ai", confirmed=True, is_required=False)
                for cid in item["concept_ids"]])
    db.add_all([McqOption(question_id=q.question_id, option_label=chr(65+i), option_text=o["text"], is_correct=o["correct"])
                for i, o in enumerate(item["options"])])
    db.add_all([SqlTestDataset(question_id=q.question_id, **dataset) for dataset in item["_datasets"]])
    db.add_all([Rubric(question_id=q.question_id, **rubric) for rubric in item["rubrics"]])
    db.flush()
    result = QuestionRepository(db).get_detail(q.question_id)
    if content_errors(result):
        raise AppError(500, "generation_integrity", "Không thể lưu câu hỏi hợp lệ. Hãy thử lại.")
    return result


def preview_plan(db, learner, payload):
    """Read-only plan for the coverage preview; never generates or persists.

    Provider output is deliberately excluded. The preview describes the
    deterministic bank/template plan, so it is stable and cannot trigger an AI
    request. The real start may improve coverage with validated provider items.
    """
    concepts = list(db.scalars(select(Concept).order_by(Concept.concept_id)))
    selected = set(payload.concept_ids)
    areas = {c.subject_area for c in concepts if c.concept_id in selected}
    related = {c.concept_id for c in concepts if c.subject_area in areas} - selected
    for edge in db.scalars(select(ConceptDependency)):
        if edge.concept_id in selected:
            related.add(edge.prerequisite_concept_id)
        if edge.prerequisite_concept_id in selected:
            related.add(edge.concept_id)
    candidates = bank_catalog(db)
    templates_added = False
    seed = f"{learner.account_id}:{payload.request_id}"
    while True:
        plan = Catalog(candidates).prepare(selected, payload.difficulties, related=related, seed=seed)
        picks = recovered_plan(plan, (), payload.question_count, selected, payload.difficulties).take(payload.question_count)
        if len(picks) == payload.question_count:
            return concepts, picks
        if not templates_added:
            candidates.extend(template_candidates(concepts))
            templates_added = True
            continue
        raise AppError(422, "insufficient_question_pool",
                       "The approved bank cannot produce a valid practice test of the requested length.")


def assemble(db, learner, payload, generated=()):
    concepts = list(db.scalars(select(Concept).order_by(Concept.concept_id)))
    selected = set(payload.concept_ids)
    areas = {c.subject_area for c in concepts if c.concept_id in selected}
    related = {c.concept_id for c in concepts if c.subject_area in areas} - selected
    for edge in db.scalars(select(ConceptDependency)):
        if edge.concept_id in selected:
            related.add(edge.prerequisite_concept_id)
        if edge.prerequisite_concept_id in selected:
            related.add(edge.concept_id)
    preferred = [Candidate(f"ai:{i}", item["question_type"], item["difficulty_level"], frozenset(item["concept_ids"]),
        f"ai:{i}", fingerprint(item["prompt"]), item, "ai") for i, item in enumerate(generated)]
    candidates = [] if complete_batch(preferred, payload.question_count, selected, payload.difficulties) else bank_catalog(db)
    templates_added = False
    repo = QuestionRepository(db)
    targets = type_targets(payload.question_count)
    seed = f"{learner.account_id}:{payload.request_id}"
    while True:
        if complete_batch(preferred, payload.question_count, selected, payload.difficulties):
            bank_plan = PreparedPlan(())
        elif payload.source == "ai" and preferred:
            bank_plan = mixed_plan(Catalog(candidates), selected, payload.difficulties, preferred, targets,
                                   related=related, seed=seed)
        else:
            bank_plan = Catalog(candidates).prepare(selected, payload.difficulties, related=related,
                                                    seed=seed, preferred=preferred)
        picks = recovered_plan(bank_plan, preferred, payload.question_count, selected, payload.difficulties).take(payload.question_count)
        ids = [p.candidate.value for p in picks if p.candidate.origin == "bank"]
        rows = {q.question_id: q for q in db.scalars(select(Question).where(Question.question_id.in_(ids)).options(*repo._detail_loads()))}
        invalid = {qid for qid in ids if qid not in rows or content_errors(rows[qid])}
        if invalid:
            candidates = [c for c in candidates if c.identity not in invalid]
            continue
        if len(picks) == payload.question_count:
            break
        if not templates_added:
            candidates.extend(template_candidates(concepts))
            templates_added = True
            continue
        raise AppError(500, "bank_capacity_error", "Ngân hàng chưa khởi tạo đầy đủ. Giảng viên cần chạy lại bước khởi tạo ngân hàng.")
    questions = [rows[p.candidate.value] if p.candidate.origin == "bank" else
                 _persist(db, validated_template(p.candidate.value, concepts) if p.candidate.origin == "template" else p.candidate.value,
                          learner, p.candidate.origin) for p in picks]
    assert len(questions) == payload.question_count
    assert len({q.question_id for q in questions}) == payload.question_count
    return questions, picks, disclosure(picks, source=payload.source)

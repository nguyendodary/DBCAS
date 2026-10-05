"""Curriculum management — UC05 / Admin story 3.

CLOs, the Core PostgreSQL concept model (difficulty 1–5), and the
admin-confirmed clo_concept mappings. The passing benchmark itself lives
on assessment_concept.target_pct (DB design) and is set through the
assessment configuration endpoints (UC09).

AI-suggested mappings (mapping_source='ai', status='pending') are review
items owned by UC06: the admin confirmed-set endpoint below upserts to
'confirmed' but never silently deletes pending AI rows.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import Account
from ..repositories import CurriculumRepository
from ..schemas import (
    CloConceptLink,
    CloResult,
    CloUpdateRequest,
    CloUpsertRequest,
    ConceptDetail,
    ConceptUpdateRequest,
    ConceptUpsertRequest,
)


def _to_clo_result(clo) -> CloResult:
    return CloResult(
        clo_id=clo.clo_id,
        clo_code=clo.clo_code,
        title=clo.title,
        description=clo.description,
        status=clo.status,
        concepts=[
            CloConceptLink(
                concept_id=link.concept_id,
                concept_code=link.concept.concept_code,
                concept_name=link.concept.concept_name,
                mapping_source=link.mapping_source,
                status=link.status,
            )
            for link in sorted(clo.concept_links, key=lambda l: l.concept_id)
        ],
    )


def _to_concept_detail(c) -> ConceptDetail:
    return ConceptDetail(
        concept_id=c.concept_id,
        concept_code=c.concept_code,
        concept_name=c.concept_name,
        subject_area=c.subject_area,
        description=c.description,
        difficulty_level=c.difficulty_level,
    )


def _require_clo(repo: CurriculumRepository, clo_id: int):
    clo = repo.get_clo(clo_id)
    if clo is None:
        raise AppError(404, "clo_not_found", "Course learning outcome not found")
    return clo


# ---------- concepts ----------


def list_concepts(db: Session) -> list[ConceptDetail]:
    return [_to_concept_detail(c) for c in CurriculumRepository(db).list_concepts()]


def create_concept(db: Session, payload: ConceptUpsertRequest) -> ConceptDetail:
    repo = CurriculumRepository(db)
    if repo.find_concept_by_code(payload.concept_code) is not None:
        raise AppError(409, "concept_code_taken", "Concept code already exists")
    try:
        concept = repo.create_concept(
            concept_code=payload.concept_code.strip(),
            concept_name=payload.concept_name.strip(),
            subject_area=payload.subject_area.strip(),
            description=payload.description,
            difficulty_level=payload.difficulty_level,
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "concept_code_taken", "Concept code already exists")
    db.refresh(concept)
    return _to_concept_detail(concept)


def update_concept(
    db: Session, concept_id: int, payload: ConceptUpdateRequest
) -> ConceptDetail:
    repo = CurriculumRepository(db)
    concept = repo.get_concept(concept_id)
    if concept is None:
        raise AppError(404, "concept_not_found", "Concept not found")
    for field in ("concept_name", "subject_area", "description", "difficulty_level"):
        value = getattr(payload, field)
        if value is not None:
            setattr(concept, field, value)
    db.commit()
    db.refresh(concept)
    return _to_concept_detail(concept)


def delete_concept(db: Session, concept_id: int) -> None:
    """409s while anything references the concept — every FK is RESTRICT,
    so deletion is only safe once the concept is fully detached."""
    repo = CurriculumRepository(db)
    concept = repo.get_concept(concept_id)
    if concept is None:
        raise AppError(404, "concept_not_found", "Concept not found")
    refs = {k: v for k, v in repo.concept_reference_counts(concept_id).items() if v}
    if refs:
        raise AppError(
            409,
            "concept_in_use",
            "Concept is referenced and cannot be deleted",
            details=[{"table": t, "references": n} for t, n in sorted(refs.items())],
        )
    db.delete(concept)
    db.commit()


# ---------- CLOs ----------


def list_clos(db: Session) -> list[CloResult]:
    return [_to_clo_result(c) for c in CurriculumRepository(db).list_clos()]


def create_clo(db: Session, payload: CloUpsertRequest, admin: Account) -> CloResult:
    repo = CurriculumRepository(db)
    if repo.find_clo_by_code(payload.clo_code) is not None:
        raise AppError(409, "clo_code_taken", "CLO code already exists")
    try:
        clo = repo.create_clo(
            clo_code=payload.clo_code.strip(),
            title=payload.title.strip(),
            description=payload.description,
            created_by=admin.account_id,
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "clo_code_taken", "CLO code already exists")
    return _to_clo_result(repo.get_clo(clo.clo_id))


def update_clo(db: Session, clo_id: int, payload: CloUpdateRequest) -> CloResult:
    repo = CurriculumRepository(db)
    clo = _require_clo(repo, clo_id)
    for field in ("title", "description", "status"):
        value = getattr(payload, field)
        if value is not None:
            setattr(clo, field, value)
    db.commit()
    return _to_clo_result(repo.get_clo(clo_id))


def delete_clo(db: Session, clo_id: int) -> None:
    repo = CurriculumRepository(db)
    clo = _require_clo(repo, clo_id)
    if repo.clo_link_count(clo_id):
        raise AppError(
            409,
            "clo_in_use",
            "CLO has concept mappings and cannot be deleted",
        )
    db.delete(clo)
    db.commit()


def set_clo_concepts(
    db: Session, clo_id: int, concept_ids: list[int]
) -> CloResult:
    """Replace the admin-confirmed concept set for a CLO.

    Rows confirmed here carry mapping_source='admin', status='confirmed'.
    A pending AI suggestion the admin now includes is confirmed in place
    (its 'ai' source is preserved); pending AI rows not in the set are left
    untouched for the UC06 review flow.
    """
    repo = CurriculumRepository(db)
    _require_clo(repo, clo_id)
    ids = set(concept_ids)
    if len(ids) != len(concept_ids):
        raise AppError(422, "duplicate_concept_ids", "Concept ids must be unique")
    found = {c.concept_id for c in repo.get_concepts(ids)}
    missing = ids - found
    if missing:
        raise AppError(
            404,
            "concept_not_found",
            "Unknown concept ids",
            details=[{"concept_id": i} for i in sorted(missing)],
        )
    for concept_id in sorted(ids):
        repo.upsert_clo_link(clo_id, concept_id, source="admin", status="confirmed")
    for link in repo.links_for_clo(clo_id):
        if link.concept_id in ids:
            continue
        if link.mapping_source == "admin":
            repo.db.delete(link)
        elif link.status == "confirmed":
            link.status = "pending"  # previously confirmed AI suggestion
    repo.db.flush()
    db.commit()
    return _to_clo_result(repo.get_clo(clo_id))

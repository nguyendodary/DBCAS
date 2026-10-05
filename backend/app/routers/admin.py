from typing import Literal, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import AdminOnly, get_llm_service, get_sandbox_runner
from ..models import Account
from ..schemas import (
    AccountStatusUpdate,
    AccountSummary,
    AdminLearnerItem,
    AdminLearnerSessionsResult,
    AssessmentDetail,
    AssessmentListItem,
    AssessmentStatusUpdate,
    AssessmentUpsertRequest,
    CandidateGenerateRequest,
    CloAiSuggestResult,
    CloResult,
    CloUpdateRequest,
    CloUpsertRequest,
    CohortOverviewResult,
    CompetencyProfileResult,
    ConceptDetail,
    ConceptPrerequisitesResult,
    ConceptUpdateRequest,
    ConceptUpsertRequest,
    ProvisionAccountRequest,
    QuestionCandidateDetail,
    QuestionCandidateItem,
    QuestionDetail,
    QuestionListItem,
    QuestionStatusUpdate,
    QuestionUpsertRequest,
    SetCloConceptsRequest,
    SetPrerequisitesRequest,
    TagSuggestionResult,
)
from ..services import (
    ai_admin_service,
    analytics_service,
    assessment_service,
    auth_service,
    concept_graph_service,
    curriculum_service,
    question_service,
)
from ..services.llm.service import LLMService
from ..services.sandbox_runner import SandboxRunner

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/accounts", status_code=201, response_model=AccountSummary)
def provision_account(
    payload: ProvisionAccountRequest,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """UC04 — Administrator provisions a new account (starts disabled)."""
    return auth_service.provision_account(db, payload)


@router.get("/accounts", response_model=list[AccountSummary])
def list_accounts(
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """UC04 — the full account roster (needed to find disabled accounts)."""
    return auth_service.list_accounts(db)


@router.patch("/accounts/{account_id}", response_model=AccountSummary)
def set_account_status(
    account_id: int,
    payload: AccountStatusUpdate,
    admin: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """UC04 — activate a manually verified account, or disable one."""
    return auth_service.set_account_status(db, account_id, payload.status, admin)


@router.put(
    "/concepts/{concept_id}/prerequisites",
    response_model=ConceptPrerequisitesResult,
)
def set_concept_prerequisites(
    concept_id: int,
    payload: SetPrerequisitesRequest,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """UC05 — Administrator replaces a concept's direct prerequisite set in
    the skill graph. Self-edges and duplicate ids are rejected (422), unknown
    concepts 404, and any set that would close a dependency cycle 409."""
    return concept_graph_service.set_concept_prerequisites(
        db, concept_id, payload.prerequisite_concept_ids
    )


# ---------- UC05 — CLOs, the concept model, and confirmed mappings ----------


@router.get("/concepts", response_model=list[ConceptDetail])
def list_concepts(
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    return curriculum_service.list_concepts(db)


@router.post("/concepts", status_code=201, response_model=ConceptDetail)
def create_concept(
    payload: ConceptUpsertRequest,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    return curriculum_service.create_concept(db, payload)


@router.patch("/concepts/{concept_id}", response_model=ConceptDetail)
def update_concept(
    concept_id: int,
    payload: ConceptUpdateRequest,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    return curriculum_service.update_concept(db, concept_id, payload)


@router.delete("/concepts/{concept_id}", status_code=204)
def delete_concept(
    concept_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """409 while any table still references the concept (FKs are RESTRICT)."""
    return curriculum_service.delete_concept(db, concept_id)


@router.get("/clos", response_model=list[CloResult])
def list_clos(
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    return curriculum_service.list_clos(db)


@router.post("/clos", status_code=201, response_model=CloResult)
def create_clo(
    payload: CloUpsertRequest,
    admin: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    return curriculum_service.create_clo(db, payload, admin)


@router.patch("/clos/{clo_id}", response_model=CloResult)
def update_clo(
    clo_id: int,
    payload: CloUpdateRequest,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    return curriculum_service.update_clo(db, clo_id, payload)


@router.delete("/clos/{clo_id}", status_code=204)
def delete_clo(
    clo_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """409 while the CLO still has concept mappings."""
    return curriculum_service.delete_clo(db, clo_id)


@router.put("/clos/{clo_id}/concepts", response_model=CloResult)
def set_clo_concepts(
    clo_id: int,
    payload: SetCloConceptsRequest,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Replace the admin-confirmed concept mapping set for a CLO."""
    return curriculum_service.set_clo_concepts(db, clo_id, payload.concept_ids)


# ---------- UC06 — AI-suggested CLO→concept mappings ----------


@router.post("/clos/{clo_id}/ai-suggest", response_model=CloAiSuggestResult)
def suggest_clo_concepts(
    clo_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
    llm: LLMService = Depends(get_llm_service),
):
    """Ask the model for concept links; they are stored pending and only
    take effect once an admin confirms them."""
    return ai_admin_service.suggest_clo_concepts(db, clo_id, llm)


@router.post(
    "/clos/{clo_id}/concepts/{concept_id}/confirm",
    response_model=CloResult,
)
def confirm_clo_link(
    clo_id: int,
    concept_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Accept one AI suggestion in place ('ai' provenance is kept)."""
    return ai_admin_service.confirm_clo_link(db, clo_id, concept_id)


@router.delete("/clos/{clo_id}/concepts/{concept_id}", response_model=CloResult)
def reject_clo_link(
    clo_id: int,
    concept_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Reject a pending suggestion. Confirmed mappings must go through
    PUT /clos/{id}/concepts — 409 here."""
    return ai_admin_service.delete_clo_link(db, clo_id, concept_id)


# ---------- UC07 — question bank management ----------


@router.get("/questions", response_model=list[QuestionListItem])
def list_questions(
    concept_id: Optional[int] = None,
    question_type: Optional[Literal["mcq", "sql", "essay"]] = None,
    difficulty: Optional[int] = None,
    status: Optional[Literal["draft", "validated", "rejected"]] = None,
    q: Optional[str] = None,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Search/filter the bank by concept, format, difficulty, status, or
    prompt text."""
    return question_service.search_questions(
        db,
        concept_id=concept_id,
        question_type=question_type,
        difficulty=difficulty,
        status=status,
        q=q,
    )


@router.post("/questions", status_code=201, response_model=QuestionDetail)
def create_question(
    payload: QuestionUpsertRequest,
    admin: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    return question_service.create_question(db, payload, admin)


@router.get("/questions/{question_id}", response_model=QuestionDetail)
def get_question(
    question_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    return question_service.get_question(db, question_id)


@router.put("/questions/{question_id}", response_model=QuestionDetail)
def replace_question(
    question_id: int,
    payload: QuestionUpsertRequest,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Full replace of content + children; a validated item is demoted to
    draft so the changed material is re-validated before serving."""
    return question_service.replace_question(db, question_id, payload)


@router.patch("/questions/{question_id}", response_model=QuestionDetail)
def set_question_status(
    question_id: int,
    payload: QuestionStatusUpdate,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """draft | validated | rejected. 'validated' requires a complete item
    (type-specific children + a confirmed concept tag) — 422 otherwise."""
    return question_service.set_question_status(db, question_id, payload.status)


@router.delete("/questions/{question_id}", status_code=204)
def delete_question(
    question_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """409 while attempts/selection logs reference the question."""
    return question_service.delete_question(db, question_id)


# ---------- UC08 — AI-recommended tags & evaluation criteria ----------


@router.post(
    "/questions/{question_id}/ai-tags",
    response_model=TagSuggestionResult,
)
def suggest_question_tags(
    question_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
    llm: LLMService = Depends(get_llm_service),
):
    """Model proposes tags + difficulty + evaluation criteria. Tags are
    stored unconfirmed ('ai'); they never satisfy the validated-item
    checklist until an admin confirms them."""
    return ai_admin_service.suggest_question_tags(db, question_id, llm)


@router.post(
    "/questions/{question_id}/tags/{concept_id}/confirm",
    response_model=QuestionDetail,
)
def confirm_question_tag(
    question_id: int,
    concept_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Confirm one tag (AI-suggested or not)."""
    return ai_admin_service.confirm_question_tag(db, question_id, concept_id)


@router.delete(
    "/questions/{question_id}/tags/{concept_id}",
    response_model=QuestionDetail,
)
def reject_question_tag(
    question_id: int,
    concept_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Reject an unconfirmed suggestion; confirmed tags go through the
    question PUT so the validated-tag rule is re-checked."""
    return ai_admin_service.reject_question_tag(db, question_id, concept_id)


# ---------- UC10 — AI question candidates ----------


@router.get(
    "/question-candidates",
    response_model=list[QuestionCandidateItem],
)
def list_question_candidates(
    status: Optional[Literal["pending", "validated", "approved", "rejected"]] = None,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Candidate queue — rejected drafts are hidden unless filtered for."""
    return ai_admin_service.list_candidates(db, status)


@router.post(
    "/question-candidates/generate",
    status_code=201,
    response_model=list[QuestionCandidateDetail],
)
def generate_question_candidates(
    payload: CandidateGenerateRequest,
    admin: Account = AdminOnly,
    db: Session = Depends(get_db),
    llm: LLMService = Depends(get_llm_service),
    runner: SandboxRunner = Depends(get_sandbox_runner),
):
    """Draft candidates for one concept/type. Each runs the deterministic
    pre-review checks immediately; 'validated' means checks passed — the
    admin still has to approve before the item enters the bank."""
    return ai_admin_service.generate_candidates(
        db, payload, admin, llm, runner
    )


@router.get(
    "/question-candidates/{candidate_id}",
    response_model=QuestionCandidateDetail,
)
def get_question_candidate(
    candidate_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    return ai_admin_service.get_candidate(db, candidate_id)


@router.post(
    "/question-candidates/{candidate_id}/validate",
    response_model=QuestionCandidateDetail,
)
def revalidate_question_candidate(
    candidate_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
    runner: SandboxRunner = Depends(get_sandbox_runner),
):
    """Re-run completeness/duplicate/SQL-execution checks."""
    return ai_admin_service.validate_candidate(db, candidate_id, runner)


@router.post(
    "/question-candidates/{candidate_id}/approve",
    response_model=QuestionCandidateDetail,
)
def approve_question_candidate(
    candidate_id: int,
    admin: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Promote a validated candidate into the bank (validated question +
    confirmed ai tag). 409 until the checks pass."""
    return ai_admin_service.approve_candidate(db, candidate_id, admin)


@router.post(
    "/question-candidates/{candidate_id}/reject",
    response_model=QuestionCandidateDetail,
)
def reject_question_candidate(
    candidate_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Hide the draft from active review (kept for audit)."""
    return ai_admin_service.reject_candidate(db, candidate_id)


# ---------- UC09 — adaptive assessment configuration ----------


@router.get("/assessments", response_model=list[AssessmentListItem])
def list_assessments(
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    return assessment_service.list_assessments(db)


@router.post("/assessments", status_code=201, response_model=AssessmentDetail)
def create_assessment(
    payload: AssessmentUpsertRequest,
    admin: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    return assessment_service.create_assessment(db, payload, admin)


@router.get("/assessments/{assessment_id}", response_model=AssessmentDetail)
def get_assessment(
    assessment_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    return assessment_service.get_assessment(db, assessment_id)


@router.put("/assessments/{assessment_id}", response_model=AssessmentDetail)
def replace_assessment(
    assessment_id: int,
    payload: AssessmentUpsertRequest,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Editable only while draft — 409 once activated (close it and draft
    a new version instead)."""
    return assessment_service.replace_assessment(db, assessment_id, payload)


@router.patch("/assessments/{assessment_id}", response_model=AssessmentDetail)
def set_assessment_status(
    assessment_id: int,
    payload: AssessmentStatusUpdate,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """draft -> active -> closed -> draft. Activation requires at least one
    target concept (invalid config A1)."""
    return assessment_service.set_assessment_status(
        db, assessment_id, payload.status
    )


@router.delete("/assessments/{assessment_id}", status_code=204)
def delete_assessment(
    assessment_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """409 while any session references the assessment."""
    return assessment_service.delete_assessment(db, assessment_id)


# ---------- UC20 — cohort analytics & learner drill-down (DBCAS-25) ----------


@router.get("/analytics/cohort", response_model=CohortOverviewResult)
def cohort_overview(
    assessment_id: Optional[int] = None,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Cohort-wide per-concept standing: averages, below-benchmark counts,
    and gap prevalence over each learner's latest finalized result."""
    return analytics_service.cohort_overview(db, assessment_id)


@router.get("/learners", response_model=list[AdminLearnerItem])
def list_learners(
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Learner roster with activity counts for the drill-down picker."""
    return analytics_service.list_learners(db)


@router.get(
    "/learners/{account_id}/sessions",
    response_model=AdminLearnerSessionsResult,
)
def learner_sessions(
    account_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """One learner's assessment history (404 for non-learner ids)."""
    return analytics_service.learner_sessions(db, account_id)


@router.get(
    "/sessions/{session_id}/competency",
    response_model=CompetencyProfileResult,
)
def admin_session_competency(
    session_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Per-learner radar data: the same deterministic competency profile
    the learner sees, without the ownership restriction."""
    return analytics_service.session_competency(db, session_id)

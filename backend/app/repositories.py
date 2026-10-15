"""Repository layer: all persistence access for the current endpoints.

Services never write SQLAlchemy queries themselves; they go through these
repositories so the data-access code stays in one place.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import case, func, select, text, delete
from sqlalchemy.orm import Session, selectinload, joinedload

from .models import (
    Account,
    AccountIdentity,
    AccountRole,
    Assessment,
    AssessmentConcept,
    AssessmentSession,
    Attempt,
    CloConcept,
    CompetencyGap,
    Concept,
    ConceptCompetency,
    ConceptDependency,
    CourseLearningOutcome,
    LlmCache,
    McqOption,
    Question,
    QuestionCandidate,
    QuestionConcept,
    QuestionTranslation,
    SelectionLog,
    Role,
    Rubric,
    SqlTestDataset,
    UserProfile,
)


def _hydrate_legacy_attempts(db, attempts):
    """Snapshots already contain grading context; batch only legacy payloads."""
    ids = {a.question_id for a in attempts if not a.question_snapshot}
    if not ids:
        return
    questions = {q.question_id: q for q in db.scalars(select(Question).where(Question.question_id.in_(ids)).options(
        selectinload(Question.options), selectinload(Question.datasets), selectinload(Question.rubrics),
        selectinload(Question.concept_tags).selectinload(QuestionConcept.concept)))}
    for attempt in attempts:
        if not attempt.question_snapshot:
            attempt.question = questions.get(attempt.question_id)


class AccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_email(self, email: str) -> Optional[Account]:
        return self.db.scalar(
            select(Account)
            .options(selectinload(Account.roles), selectinload(Account.profile))
            .where(Account.email == email)
        )

    def find_identity(
        self, provider: str, provider_user_id: str
    ) -> Optional[AccountIdentity]:
        return self.db.scalar(
            select(AccountIdentity)
            .options(
                selectinload(AccountIdentity.account).selectinload(Account.roles),
                selectinload(AccountIdentity.account).selectinload(Account.profile),
            )
            .where(
                AccountIdentity.provider == provider,
                AccountIdentity.provider_user_id == provider_user_id,
            )
        )

    def link_identity(
        self,
        account_id: int,
        provider: str,
        provider_user_id: str,
        provider_email: Optional[str],
        email_verified: bool,
    ) -> AccountIdentity:
        identity = AccountIdentity(
            account_id=account_id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=provider_email,
            email_verified=email_verified,
        )
        self.db.add(identity)
        return identity

    def get_with_roles(self, account_id: int) -> Optional[Account]:
        return self.db.execute(
            select(Account)
            .options(joinedload(Account.roles), joinedload(Account.profile))
            .where(Account.account_id == account_id)
        ).unique().scalars().one_or_none()

    def get_role(self, role_name: str) -> Optional[Role]:
        return self.db.scalar(select(Role).where(Role.role_name == role_name))

    def has_administrator(self) -> bool:
        return self.db.scalar(select(Account.account_id).join(AccountRole).join(Role).where(
            Role.role_name == 'Administrator').limit(1)) is not None

    def create_learner(self, email: str, password_hash: str, full_name: str) -> Account:
        """UC01: account + profile + Learner role, always status=active."""
        account = Account(email=email, password_hash=password_hash, status="active")
        account.profile = UserProfile(full_name=full_name)
        role = self.get_role("Learner")
        if role is None:
            raise RuntimeError("Role 'Learner' is missing — apply database migrations")
        account.roles.append(role)
        self.db.add(account)
        return account

    def create_provisioned(
        self, email: str, password_hash: str, full_name: str, role_name: str
    ) -> Account:
        """UC04: admin-provisioned accounts always start disabled."""
        account = Account(email=email, password_hash=password_hash, status="disabled")
        account.profile = UserProfile(full_name=full_name)
        role = self.get_role(role_name)
        if role is None:
            raise RuntimeError(f"Role '{role_name}' is missing — apply database migrations")
        account.roles.append(role)
        self.db.add(account)
        return account


class ReadinessRepository:
    """Read-only checks for the schema required by the running application."""

    def __init__(self, db: Session):
        self.db = db

    def check_schema(self):
        self.db.execute(text("SELECT 1 FROM account_identity LIMIT 0"))
        self.db.execute(text("SELECT 1 FROM concept_dependency LIMIT 0"))
        self.db.execute(text("SELECT question_snapshot, draft_answer, grading_status FROM attempt LIMIT 0"))
        self.db.execute(text("SELECT config_snapshot FROM assessment_session LIMIT 0"))
        self.db.execute(text("SELECT family_id, version_no FROM question LIMIT 0"))
        self.db.execute(text("SELECT 1 FROM oauth_handoff LIMIT 0"))
        self.db.execute(text("SELECT 1 FROM grading_job LIMIT 0"))
        return True


class AssessmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_session(self, session_id: int) -> Optional[AssessmentSession]:
        return self.db.get(AssessmentSession, session_id)

    def lock_session(self, session_id: int):
        return self.db.scalar(select(AssessmentSession).where(AssessmentSession.session_id == session_id).with_for_update().execution_options(populate_existing=True))

    def expired_session_ids(self, limit=100):
        return list(self.db.scalars(select(AssessmentSession.session_id).where(AssessmentSession.status == "in_progress", AssessmentSession.expires_at <= func.clock_timestamp()).order_by(AssessmentSession.expires_at).limit(limit)))

    def enqueue_grading(self, attempt):
        from .models import GradingJob
        job = self.db.scalar(select(GradingJob).where(GradingJob.attempt_id == attempt.attempt_id))
        if job is None:
            job = GradingJob(attempt_id=attempt.attempt_id, status="pending", attempt_count=0)
            self.db.add(job)
        attempt.grading_status = "pending"
        self.db.flush()
        return job

    def claim_grading_job(self, *, include_essay=True, lease_seconds=180):
        from .models import GradingJob
        stmt = select(GradingJob).join(Attempt).join(Question).where(
            ((GradingJob.status == "pending") & (GradingJob.available_at <= func.now())) |
            ((GradingJob.status == "processing") & (GradingJob.lease_until < func.now()))
        )
        if not include_essay:
            stmt = stmt.where(Question.question_type != "essay")
        job = self.db.scalar(stmt.order_by(GradingJob.job_id).with_for_update(of=GradingJob, skip_locked=True).limit(1))
        if job:
            from datetime import timedelta
            job.status = "processing"
            job.attempt_count += 1
            job.lease_until = datetime.now(timezone.utc) + timedelta(seconds=lease_seconds)
            self.db.flush()
        return job

    def lock_grading_job(self, job_id):
        from .models import GradingJob
        return self.db.scalar(select(GradingJob).where(GradingJob.job_id == job_id).with_for_update().execution_options(populate_existing=True))

    def sessions_for_learner(self, learner_id: int) -> list[AssessmentSession]:
        """The learner's own sessions, newest first (UC18 history list)."""
        return list(
            self.db.scalars(
                select(AssessmentSession)
                .options(selectinload(AssessmentSession.assessment))
                .where(AssessmentSession.learner_id == learner_id)
                .order_by(
                    func.coalesce(AssessmentSession.submitted_at, AssessmentSession.started_at).desc(),
                    AssessmentSession.session_id.desc(),
                )
            )
        )

    def history_attempts(self, session_ids: list[int]) -> list[Attempt]:
        if not session_ids:
            return []
        return list(self.db.scalars(select(Attempt).where(Attempt.session_id.in_(session_ids))
            .options(selectinload(Attempt.question).selectinload(Question.concept_tags)
                     .selectinload(QuestionConcept.concept)).order_by(Attempt.session_id, Attempt.seq_no)))

    def attempt_counts(self, session_ids: list[int]) -> dict[int, tuple[int, int]]:
        """session_id -> (served, submitted) attempt counts in one query."""
        if not session_ids:
            return {}
        rows = self.db.execute(
            select(
                Attempt.session_id,
                func.count(Attempt.attempt_id),
                func.count(Attempt.submitted_at),
            )
            .where(Attempt.session_id.in_(session_ids))
            .group_by(Attempt.session_id)
        ).all()
        return {sid: (served, answered) for sid, served, answered in rows}

    def get_question_with_options(self, question_id: int) -> Optional[Question]:
        return self.db.scalar(
            select(Question)
            .options(selectinload(Question.options))
            .where(Question.question_id == question_id)
        )

    def lock_question_for_serving(self, question_id: int) -> Optional[Question]:
        self.db.scalar(select(Question).where(Question.question_id == question_id)
                       .with_for_update(read=True, key_share=True))
        return self.db.scalar(select(Question).where(Question.question_id == question_id)
            .options(selectinload(Question.options), selectinload(Question.translations), selectinload(Question.rubrics), selectinload(Question.concept_tags).selectinload(QuestionConcept.concept))
            .execution_options(populate_existing=True))

    def question_families(self, question_ids: set[int]) -> set[int]:
        if not question_ids:
            return set()
        return set(self.db.scalars(select(func.coalesce(Question.family_id, Question.question_id))
                                   .where(Question.question_id.in_(question_ids))))

    def get_attempt(self, session_id: int, question_id: int) -> Optional[Attempt]:
        return self.db.scalar(
            select(Attempt)
            .options(selectinload(Attempt.question).selectinload(Question.options))
            .where(
                Attempt.session_id == session_id,
                Attempt.question_id == question_id,
            )
        )

    # ----- assessment configuration (UC09) -----

    def get_assessment(self, assessment_id: int) -> Optional[Assessment]:
        return self.db.scalar(
            select(Assessment)
            .options(
                selectinload(Assessment.targets).selectinload(
                    AssessmentConcept.concept
                )
            )
            .where(Assessment.assessment_id == assessment_id)
        )

    def list_assessments(self) -> list[Assessment]:
        return list(
            self.db.scalars(
                select(Assessment)
                .options(
                    selectinload(Assessment.targets).selectinload(
                        AssessmentConcept.concept
                    )
                )
                .order_by(Assessment.assessment_id)
            )
        )

    def list_active_assessments(self) -> list[Assessment]:
        """Published assessments a learner may start (UC12)."""
        return list(
            self.db.scalars(
                select(Assessment)
                .options(selectinload(Assessment.targets))
                .where(Assessment.status == "published")
                .order_by(Assessment.assessment_id)
            )
        )

    def create_assessment(self, **fields) -> Assessment:
        assessment = Assessment(**fields)
        self.db.add(assessment)
        self.db.flush()
        return assessment

    def delete_assessment(self, assessment: Assessment) -> None:
        for target in list(assessment.targets):
            self.db.delete(target)
        self.db.delete(assessment)

    def clone_assessment(self, assessment: Assessment) -> Assessment:
        root = assessment.family_id or assessment.assessment_id
        SecurityRepository(self.db).lock(f"assessment-version:{root}")
        version = int(self.db.scalar(select(func.max(Assessment.version_no)).where(
            func.coalesce(Assessment.family_id, Assessment.assessment_id) == root)) or 1) + 1
        cloned = self.create_assessment(title=assessment.title, description=assessment.description,
            max_questions=13, duration_min=60, target_mcq=10, target_sql=2, target_essay=1,
            created_by=assessment.created_by, status="draft", family_id=root, version_no=version)
        for target in assessment.targets:
            self.upsert_target(cloned.assessment_id, target.concept_id, min_d=target.min_difficulty,
                               max_d=target.max_difficulty, target_pct=target.target_pct)
        return self.get_assessment(cloned.assessment_id)

    def assessment_version_count(self, assessment_id: int) -> int:
        return int(self.db.scalar(select(func.count()).select_from(Assessment)
                                  .where(Assessment.family_id == assessment_id)) or 0)

    def replace_targets(self, assessment: Assessment, concept_ids) -> None:
        """Drop all assessment_concept rows not in the keep set."""
        for t in list(assessment.targets):
            if t.concept_id not in concept_ids:
                self.db.delete(t)
        self.db.flush()

    def upsert_target(
        self, assessment_id: int, concept_id: int, *, min_d, max_d, target_pct
    ) -> None:
        row = self.db.get(AssessmentConcept, (assessment_id, concept_id))
        if row is None:
            row = AssessmentConcept(
                assessment_id=assessment_id,
                concept_id=concept_id,
                min_difficulty=min_d,
                max_difficulty=max_d,
                target_pct=target_pct,
            )
            self.db.add(row)
        else:
            row.min_difficulty = min_d
            row.max_difficulty = max_d
            row.target_pct = target_pct
        self.db.flush()

    def assessment_session_count(self, assessment_id: int) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(AssessmentSession)
                .where(AssessmentSession.assessment_id == assessment_id)
            )
            or 0
        )

    def session_counts(self) -> dict[int, int]:
        """assessment_id -> session count in one query (admin list)."""
        rows = self.db.execute(
            select(
                AssessmentSession.assessment_id,
                func.count(AssessmentSession.session_id),
            ).group_by(AssessmentSession.assessment_id)
        ).all()
        return {aid: n for aid, n in rows}

    # ----- adaptive session engine (UC12 / FR-15) -----

    def active_session_for(
        self, learner_id: int, assessment_id: int
    ) -> Optional[AssessmentSession]:
        """The learner's live session for this assessment, if any — used
        to resume instead of starting a duplicate."""
        return self.db.scalar(
            select(AssessmentSession)
            .where(
                AssessmentSession.learner_id == learner_id,
                AssessmentSession.assessment_id == assessment_id,
                AssessmentSession.status == "in_progress",
            )
            .order_by(AssessmentSession.session_id.desc())
        )

    def create_session(
        self, assessment_id: int, learner_id: int, expires_at, *, started_at=None, locale="en"
    ) -> AssessmentSession:
        session = AssessmentSession(
            assessment_id=assessment_id,
            learner_id=learner_id,
            expires_at=expires_at,
            locale=locale,
        )
        if started_at is not None:
            session.started_at = started_at
        self.db.add(session)
        self.db.flush()
        return session

    def server_time(self):
        return self.db.scalar(select(func.clock_timestamp()))

    def session_attempts(self, session_id: int) -> list[Attempt]:
        """All served attempts in serve order, with question payloads."""
        attempts = list(
            self.db.scalars(
                select(Attempt)
                .where(Attempt.session_id == session_id)
                .order_by(Attempt.seq_no)
            )
        )
        _hydrate_legacy_attempts(self.db, attempts)
        return attempts

    def pending_attempt(self, session_id: int) -> Optional[Attempt]:
        """The served-but-unanswered question, if one exists. The engine
        serves the next question only after the pending one is graded, so
        there is at most one."""
        return self.db.scalar(
            select(Attempt)
            .options(
                selectinload(Attempt.question).selectinload(Question.options),
                selectinload(Attempt.question).selectinload(
                    Question.concept_tags
                ).selectinload(QuestionConcept.concept),
            )
            .where(
                Attempt.session_id == session_id,
                Attempt.submitted_at.is_(None),
            )
            .order_by(Attempt.seq_no.desc())
        )

    def eligible_questions(
        self, assessment: Assessment, served_ids: set[int], *, opening_only=False
    ) -> list[Question]:
        """Validated bank questions confirmed-tagged to a target concept.

        The per-concept difficulty range filter is applied by the caller —
        a question qualifies when ANY confirmed target tag's range fits it.
        """
        target_ids = [t.concept_id for t in assessment.targets]
        if not target_ids:
            return []
        payloads = [selectinload(Question.options),
            selectinload(Question.concept_tags).selectinload(QuestionConcept.concept)]
        if not opening_only:
            payloads.extend([selectinload(Question.datasets), selectinload(Question.rubrics)])
        opening_filter = [Question.question_type == "mcq", Question.difficulty_level <= 2] if opening_only else []
        return list(
            self.db.scalars(
                select(Question)
                .join(Question.concept_tags)
                .options(*payloads)
                .where(
                    Question.status == "validated",
                    QuestionConcept.confirmed.is_(True),
                    QuestionConcept.concept_id.in_(target_ids),
                    Question.question_id.not_in(served_ids or {0}),
                    *opening_filter,
                )
                .distinct()
            )
        )

    def create_attempt(
        self, session_id: int, question_id: int, seq_no: int
    ) -> Attempt:
        attempt = Attempt(
            session_id=session_id, question_id=question_id, seq_no=seq_no
        )
        self.db.add(attempt)
        self.db.flush()
        return attempt

    def create_selection_log(
        self,
        session_id: int,
        seq_no: int,
        question_id: int,
        is_fallback: bool,
        decision_detail: dict,
    ) -> SelectionLog:
        row = SelectionLog(
            session_id=session_id,
            seq_no=seq_no,
            question_id=question_id,
            is_fallback=is_fallback,
            decision_detail=decision_detail,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def selection_log_for(self, session_id: int) -> list[SelectionLog]:
        return list(
            self.db.scalars(
                select(SelectionLog)
                .where(SelectionLog.session_id == session_id)
                .order_by(SelectionLog.seq_no)
            )
        )

    def get_datasets_for_question(self, question_id: int) -> list[SqlTestDataset]:
        """All test datasets of a SQL question — regular cases first."""
        return list(
            self.db.scalars(
                select(SqlTestDataset)
                .where(SqlTestDataset.question_id == question_id)
                .order_by(SqlTestDataset.is_edge_case, SqlTestDataset.dataset_id)
            )
        )

    def get_required_concepts(self, question_id: int) -> list[str]:
        """Names of concepts the question mandates (is_required tags)."""
        return list(
            self.db.scalars(
                select(Concept.concept_name)
                .join(
                    QuestionConcept,
                    QuestionConcept.concept_id == Concept.concept_id,
                )
                .where(
                    QuestionConcept.question_id == question_id,
                    QuestionConcept.is_required.is_(True),
                )
                .order_by(Concept.concept_name)
            )
        )

    def get_rubrics_for_question(self, question_id: int) -> list[Rubric]:
        """All rubric rows of an essay question, ordered by level floor."""
        return list(
            self.db.scalars(
                select(Rubric)
                .where(Rubric.question_id == question_id)
                .order_by(Rubric.min_score)
            )
        )


class ConceptGraphRepository:
    """concept / concept_dependency access — the prerequisite skill graph.

    Every read returns rows in a deterministic order so the graph services
    built on top never depend on database ordering luck.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_concept(self, concept_id: int) -> Optional[Concept]:
        return self.db.get(Concept, concept_id)

    def get_concepts(self, concept_ids: set[int]) -> list[Concept]:
        if not concept_ids:
            return []
        return list(
            self.db.scalars(
                select(Concept)
                .where(Concept.concept_id.in_(concept_ids))
                .order_by(Concept.concept_id)
            )
        )

    def list_concepts(self) -> list[Concept]:
        return list(self.db.scalars(select(Concept).order_by(Concept.concept_id)))

    def all_edges(self) -> list[ConceptDependency]:
        return list(
            self.db.scalars(
                select(ConceptDependency).order_by(
                    ConceptDependency.concept_id,
                    ConceptDependency.prerequisite_concept_id,
                )
            )
        )

    def lock_writes(self) -> None:
        # Concurrent individually valid graph edits must not jointly add a cycle.
        self.db.execute(text("SELECT pg_advisory_xact_lock(73005)"))

    def prerequisites_of(self, concept_id: int) -> list[ConceptDependency]:
        return list(
            self.db.scalars(
                select(ConceptDependency)
                .where(ConceptDependency.concept_id == concept_id)
                .order_by(ConceptDependency.prerequisite_concept_id)
            )
        )

    def dependents_of(self, concept_id: int) -> list[ConceptDependency]:
        return list(
            self.db.scalars(
                select(ConceptDependency)
                .where(ConceptDependency.prerequisite_concept_id == concept_id)
                .order_by(ConceptDependency.concept_id)
            )
        )

    def replace_prerequisites(
        self, concept_id: int, prerequisite_ids: list[int]
    ) -> None:
        """Replace one concept's direct prerequisite set atomically."""
        existing = {e.prerequisite_concept_id: e for e in self.prerequisites_of(concept_id)}
        wanted = set(prerequisite_ids)
        for pid, edge in existing.items():
            if pid not in wanted:
                self.db.delete(edge)
        for pid in sorted(wanted - existing.keys()):
            self.db.add(
                ConceptDependency(
                    concept_id=concept_id, prerequisite_concept_id=pid
                )
            )
        self.db.flush()


class CompetencyRepository:
    """concept_competency / competency_gap persistence.

    Rows are keyed (session_id, concept_id) — recompute upserts in place so
    recalculation never duplicates a competency or gap record.
    """

    def __init__(self, db: Session):
        self.db = db

    def session_evidence(self, session_id: int) -> list[Attempt]:
        """The session's graded attempts with their questions' concept tags.

        A served attempt becomes evidence only once submitted — the Sprint 3
        graders persist a deterministic ``attempt.score`` this pipeline reads.
        """
        attempts = list(
            self.db.scalars(
                select(Attempt)
                .where(
                    Attempt.session_id == session_id,
                    Attempt.submitted_at.is_not(None),
                    Attempt.score.is_not(None),
                )
                .order_by(Attempt.seq_no)
            )
        )
        _hydrate_legacy_attempts(self.db, attempts)
        return attempts

    def assessment_targets(self, assessment_id: int) -> dict[int, Decimal]:
        """concept_id -> administrator-set passing benchmark (target_pct)."""
        rows = self.db.scalars(
            select(AssessmentConcept).where(
                AssessmentConcept.assessment_id == assessment_id
            )
        )
        return {r.concept_id: r.target_pct for r in rows}

    def competencies_for_session(self, session_id: int) -> list[ConceptCompetency]:
        return list(
            self.db.scalars(
                select(ConceptCompetency)
                .options(selectinload(ConceptCompetency.concept))
                .where(ConceptCompetency.session_id == session_id)
                .order_by(ConceptCompetency.concept_id)
            )
        )

    def upsert_competency(
        self,
        session_id: int,
        concept_id: int,
        *,
        points_earned: Decimal,
        points_possible: Decimal,
        competency_pct: Decimal,
        below_target: bool,
    ) -> ConceptCompetency:
        row = self.db.scalar(
            select(ConceptCompetency).where(
                ConceptCompetency.session_id == session_id,
                ConceptCompetency.concept_id == concept_id,
            )
        )
        if row is None:
            row = ConceptCompetency(session_id=session_id, concept_id=concept_id)
            self.db.add(row)
        row.points_earned = points_earned
        row.points_possible = points_possible
        row.competency_pct = competency_pct
        row.below_target = below_target
        row.computed_at = datetime.now(timezone.utc)
        self.db.flush()
        return row

    def delete_stale_competencies(
        self, session_id: int, keep_concept_ids: set[int]
    ) -> None:
        """Drop competency rows for concepts no longer backed by evidence."""
        for row in self.competencies_for_session(session_id):
            if row.concept_id not in keep_concept_ids:
                self.db.delete(row)
        self.db.flush()

    def gaps_for_session(self, session_id: int) -> list[CompetencyGap]:
        return list(
            self.db.scalars(
                select(CompetencyGap)
                .options(selectinload(CompetencyGap.concept))
                .where(CompetencyGap.session_id == session_id)
                .order_by(CompetencyGap.concept_id)
            )
        )

    def upsert_gap(self, session_id: int, concept_id: int) -> CompetencyGap:
        row = self.db.scalar(
            select(CompetencyGap).where(
                CompetencyGap.session_id == session_id,
                CompetencyGap.concept_id == concept_id,
            )
        )
        if row is None:
            row = CompetencyGap(session_id=session_id, concept_id=concept_id)
            self.db.add(row)
            self.db.flush()
        return row

    def delete_stale_gaps(self, session_id: int, keep_concept_ids: set[int]) -> None:
        """A concept that recovered above its benchmark is no longer a gap."""
        for row in self.gaps_for_session(session_id):
            if row.concept_id not in keep_concept_ids:
                self.db.delete(row)
        self.db.flush()


class CurriculumRepository:
    """CLOs, concepts, and clo_concept mappings (UC05)."""

    def __init__(self, db: Session):
        self.db = db

    # ----- accounts (UC04 admin roster) -----

    def list_accounts(self) -> list[Account]:
        return list(
            self.db.scalars(
                select(Account)
                .options(
                    selectinload(Account.profile), selectinload(Account.roles)
                )
                .order_by(Account.email)
            )
        )

    def get_account(self, account_id: int) -> Optional[Account]:
        return self.db.scalar(
            select(Account)
            .options(
                selectinload(Account.profile), selectinload(Account.roles)
            )
            .where(Account.account_id == account_id)
        )

    # ----- concepts -----

    def list_concepts(self) -> list[Concept]:
        return list(
            self.db.scalars(select(Concept).order_by(Concept.concept_code))
        )

    def get_concept(self, concept_id: int) -> Optional[Concept]:
        return self.db.get(Concept, concept_id)

    def find_concept_by_code(self, code: str) -> Optional[Concept]:
        return self.db.scalar(
            select(Concept).where(Concept.concept_code == code)
        )

    def create_concept(self, **fields) -> Concept:
        concept = Concept(**fields)
        self.db.add(concept)
        self.db.flush()
        return concept

    def delete_concept(self, concept: Concept) -> None:
        self.db.delete(concept)

    def get_concepts(self, concept_ids: set[int]) -> list[Concept]:
        if not concept_ids:
            return []
        return list(
            self.db.scalars(
                select(Concept).where(Concept.concept_id.in_(concept_ids))
            )
        )

    def concept_reference_counts(self, concept_id: int) -> dict[str, int]:
        """References that block deletion (all FKs are RESTRICT)."""
        checks = {
            "question_concept": select(func.count()).select_from(
                QuestionConcept
            ).where(QuestionConcept.concept_id == concept_id),
            "assessment_concept": select(func.count()).select_from(
                AssessmentConcept
            ).where(AssessmentConcept.concept_id == concept_id),
            "clo_concept": select(func.count()).select_from(CloConcept).where(
                CloConcept.concept_id == concept_id
            ),
            "concept_dependency": select(func.count()).select_from(
                ConceptDependency
            ).where(
                (ConceptDependency.concept_id == concept_id)
                | (ConceptDependency.prerequisite_concept_id == concept_id)
            ),
            "concept_competency": select(func.count()).select_from(
                ConceptCompetency
            ).where(ConceptCompetency.concept_id == concept_id),
            "competency_gap": select(func.count()).select_from(
                CompetencyGap
            ).where(CompetencyGap.concept_id == concept_id),
        }
        return {
            table: int(self.db.scalar(stmt) or 0)
            for table, stmt in checks.items()
        }

    # ----- CLOs -----

    def list_clos(self) -> list[CourseLearningOutcome]:
        return list(
            self.db.scalars(
                select(CourseLearningOutcome)
                .options(selectinload(CourseLearningOutcome.concept_links).selectinload(CloConcept.concept))
                .order_by(CourseLearningOutcome.clo_code)
            )
        )

    def get_clo(self, clo_id: int) -> Optional[CourseLearningOutcome]:
        return self.db.scalar(
            select(CourseLearningOutcome)
            .options(selectinload(CourseLearningOutcome.concept_links).selectinload(CloConcept.concept))
            .where(CourseLearningOutcome.clo_id == clo_id)
        )

    def find_clo_by_code(self, code: str) -> Optional[CourseLearningOutcome]:
        return self.db.scalar(
            select(CourseLearningOutcome).where(
                CourseLearningOutcome.clo_code == code
            )
        )

    def create_clo(self, **fields) -> CourseLearningOutcome:
        clo = CourseLearningOutcome(**fields)
        self.db.add(clo)
        self.db.flush()
        return clo

    def delete_clo(self, clo: CourseLearningOutcome) -> None:
        self.db.delete(clo)

    def delete_clo_link(self, link: CloConcept) -> None:
        self.db.delete(link)

    def clo_link_count(self, clo_id: int) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(CloConcept)
                .where(CloConcept.clo_id == clo_id)
            )
            or 0
        )

    def links_for_clo(self, clo_id: int) -> list[CloConcept]:
        return list(
            self.db.scalars(
                select(CloConcept).where(CloConcept.clo_id == clo_id)
            )
        )

    def upsert_clo_link(
        self, clo_id: int, concept_id: int, *, source: str, status: str
    ) -> CloConcept:
        link = self.db.get(CloConcept, (clo_id, concept_id))
        if link is None:
            link = CloConcept(
                clo_id=clo_id, concept_id=concept_id,
                mapping_source=source, status=status,
            )
            self.db.add(link)
        else:
            link.status = status
        self.db.flush()
        return link

    def get_clo_link(
        self, clo_id: int, concept_id: int
    ) -> Optional[CloConcept]:
        return self.db.get(CloConcept, (clo_id, concept_id))

class QuestionRepository:
    """Question bank items with their child collections (UC07)."""

    def __init__(self, db: Session):
        self.db = db

    def _detail_loads(self):
        return (
            selectinload(Question.options),
            selectinload(Question.datasets),
            selectinload(Question.rubrics),
            selectinload(Question.translations),
            selectinload(Question.concept_tags).selectinload(
                QuestionConcept.concept
            ),
        )

    def search(
        self,
        *,
        concept_id: Optional[int] = None,
        question_type: Optional[str] = None,
        difficulty: Optional[int] = None,
        status: Optional[str] = None,
        q: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> list[Question]:
        stmt = select(Question).options(*self._detail_loads())
        if concept_id is not None:
            stmt = stmt.where(
                Question.concept_tags.any(
                    QuestionConcept.concept_id == concept_id
                )
            )
        if question_type is not None:
            stmt = stmt.where(Question.question_type == question_type)
        if difficulty is not None:
            stmt = stmt.where(Question.difficulty_level == difficulty)
        if status is not None:
            stmt = stmt.where(Question.status == status)
        if q:
            stmt = stmt.where(Question.prompt.ilike(f"%{q}%"))
        if tag:
            stmt = stmt.where(Question.tags.any(tag))
        return list(
            self.db.scalars(stmt.order_by(Question.question_id)).unique()
        )

    def get_detail(self, question_id: int) -> Optional[Question]:
        return self.db.scalar(
            select(Question)
            .options(*self._detail_loads())
            .where(Question.question_id == question_id)
        )

    def lock_question(self, question_id: int) -> Optional[Question]:
        root = self.db.scalar(select(func.coalesce(Question.family_id, Question.question_id))
                              .where(Question.question_id == question_id))
        if root:
            SecurityRepository(self.db).lock(f"question-version:{root}")
        return self.db.scalar(select(Question).where(Question.question_id == question_id)
                              .with_for_update().execution_options(populate_existing=True))

    def clone_for_edit(self, question: Question) -> Question:
        root = question.family_id or question.question_id
        next_version = int(self.db.scalar(select(func.max(Question.version_no)).where(
            func.coalesce(Question.family_id, Question.question_id) == root)) or 1) + 1
        cloned = self.create(**{key: getattr(question, key) for key in (
            "question_type", "prompt", "reference_answer", "difficulty_level", "points", "source", "created_by", "ai_review")},
            status="draft", family_id=root, version_no=next_version)
        for tag in self.tags_for(question.question_id):
            self.db.add(QuestionConcept(question_id=cloned.question_id, concept_id=tag.concept_id,
                tag_source=tag.tag_source, is_required=tag.is_required,
                confirmed=tag.confirmed, review_status=tag.review_status))
        for translation in question.translations:
            self.db.add(QuestionTranslation(
                question_id=cloned.question_id,
                locale=translation.locale,
                source_hash=translation.source_hash,
                prompt=translation.prompt,
                explanation=translation.explanation,
                option_texts=translation.option_texts,
                rubrics=translation.rubrics,
            ))
        question.status = "retired"
        self.db.flush()
        return self.get_detail(cloned.question_id)

    def create(self, **fields) -> Question:
        question = Question(**fields)
        self.db.add(question)
        self.db.flush()
        return question

    def replace_options(self, question: Question, options) -> None:
        for opt in list(question.options):
            self.db.delete(opt)
        self.db.flush()
        for opt in options:
            self.db.add(
                McqOption(
                    question_id=question.question_id,
                    option_label=opt.option_label,
                    option_text=opt.option_text,
                    is_correct=opt.is_correct,
                )
            )
        self.db.flush()

    def replace_datasets(self, question: Question, datasets) -> None:
        for ds in self.datasets_for(question.question_id):
            self.db.delete(ds)
        self.db.flush()
        for ds in datasets:
            self.db.add(
                SqlTestDataset(
                    question_id=question.question_id,
                    dataset_name=ds.dataset_name,
                    setup_sql=ds.setup_sql,
                    expected_result=ds.expected_result,
                    is_edge_case=ds.is_edge_case,
                )
            )
        self.db.flush()

    def replace_rubrics(self, question: Question, rubrics) -> None:
        for rb in self.rubrics_for(question.question_id):
            self.db.delete(rb)
        self.db.flush()
        for rb in rubrics:
            self.db.add(
                Rubric(
                    question_id=question.question_id,
                    level_name=rb.level_name,
                    min_score=rb.min_score,
                    max_score=rb.max_score,
                    criteria=rb.criteria,
                )
            )
        self.db.flush()

    def datasets_for(self, question_id: int) -> list[SqlTestDataset]:
        question = self.db.get(Question, question_id)
        return list(question.datasets) if question else []

    def rubrics_for(self, question_id: int) -> list[Rubric]:
        question = self.db.get(Question, question_id)
        return list(question.rubrics) if question else []

    def tags_for(self, question_id: int) -> list[QuestionConcept]:
        return list(
            self.db.scalars(
                select(QuestionConcept).where(
                    QuestionConcept.question_id == question_id
                )
            )
        )

    def upsert_tag(
        self,
        question_id: int,
        concept_id: int,
        *,
        source: str,
        confirmed: bool,
        is_required: bool,
    ) -> QuestionConcept:
        tag = self.db.get(QuestionConcept, (question_id, concept_id))
        if tag is None:
            tag = QuestionConcept(
                question_id=question_id,
                concept_id=concept_id,
                tag_source=source,
                confirmed=confirmed,
                is_required=is_required,
            )
            self.db.add(tag)
        else:
            tag.confirmed = confirmed
            tag.is_required = is_required
        self.db.flush()
        return tag

    def delete_tag(self, tag: QuestionConcept) -> None:
        self.db.delete(tag)

    def delete_with_children(self, question: Question) -> None:
        for model in (QuestionConcept, McqOption, SqlTestDataset, Rubric):
            self.db.execute(delete(model).where(model.question_id == question.question_id))
        self.db.expire(question)
        self.db.delete(question)

    def reference_counts(self, question_id: int) -> dict[str, int]:
        """References that block deletion (attempts, selection log, and an
        AI candidate that promoted into this question)."""
        checks = {
            "attempt": select(func.count()).select_from(Attempt).where(
                Attempt.question_id == question_id
            ),
            "selection_log": select(func.count()).select_from(
                SelectionLog
            ).where(SelectionLog.question_id == question_id),
            "question_candidate": select(func.count()).select_from(
                QuestionCandidate
            ).where(QuestionCandidate.promoted_question_id == question_id),
            "question_version": select(func.count()).select_from(Question).where(Question.family_id == question_id),
        }
        return {
            table: int(self.db.scalar(stmt) or 0)
            for table, stmt in checks.items()
        }

    # ----- AI question candidates (UC10) -----

    def create_candidate(
        self, concept_id: int, question_type: str, payload: dict
    ) -> QuestionCandidate:
        row = QuestionCandidate(
            concept_id=concept_id,
            question_type=question_type,
            payload=payload,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def get_candidate(self, candidate_id: int) -> Optional[QuestionCandidate]:
        return self.db.scalar(
            select(QuestionCandidate)
            .options(selectinload(QuestionCandidate.concept))
            .where(QuestionCandidate.candidate_id == candidate_id)
        )

    def list_candidates(
        self, status: Optional[str] = None
    ) -> list[QuestionCandidate]:
        stmt = (
            select(QuestionCandidate)
            .options(selectinload(QuestionCandidate.concept))
            .order_by(QuestionCandidate.candidate_id.desc())
        )
        if status == "approved":
            stmt = stmt.where(QuestionCandidate.promoted_question_id.is_not(None))
        elif status is not None:
            stmt = stmt.where(QuestionCandidate.validation_status == status)
        else:
            # rejected drafts stay out of the review queue (UC10)
            stmt = stmt.where(QuestionCandidate.validation_status != "rejected")
        return list(self.db.scalars(stmt))

    def prompt_duplicates(
        self, prompt: str, *, exclude_candidate_id: Optional[int] = None
    ) -> list[int]:
        """Ids of bank questions or live candidates whose normalized prompt
        matches — the cheap, deterministic half of UC10 duplicate checks."""
        norm = " ".join(prompt.lower().split())
        dupes: list[int] = []
        q_rows = self.db.execute(
            select(Question.question_id, Question.prompt).where(
                Question.status != "retired"
            )
        )
        for qid, text in q_rows:
            if " ".join(text.lower().split()) == norm:
                dupes.append(qid)
        c_stmt = select(
            QuestionCandidate.candidate_id, QuestionCandidate.payload
        ).where(QuestionCandidate.validation_status != "rejected")
        if exclude_candidate_id is not None:
            c_stmt = c_stmt.where(
                QuestionCandidate.candidate_id != exclude_candidate_id
            )
        for cid, payload in self.db.execute(c_stmt):
            other = " ".join(
                str((payload or {}).get("prompt", "")).lower().split()
            )
            if other == norm:
                dupes.append(-cid)  # negative id = candidate, not question
        return dupes


class LlmCacheRepository:
    """llm_cache — request-hash-keyed response store (NFR-09 caching)."""

    def __init__(self, db: Session):
        self.db = db

    def find(self, request_hash: str) -> Optional[dict]:
        row = self.db.scalar(
            select(LlmCache).where(LlmCache.request_hash == request_hash)
        )
        return row.response if row else None

    def store(self, request_hash: str, task_type: str, model: str, response: dict) -> None:
        # INSERT-first semantics: the unique index on request_hash makes
        # concurrent duplicate stores harmless.
        # A cache failure rolls back its savepoint, not the primary transaction.
        with self.db.begin_nested():
            self.db.add(
                LlmCache(
                    request_hash=request_hash,
                    task_type=task_type,
                    model=model,
                    response=response,
                )
            )
            self.db.flush()


class SecurityRepository:
    """Shared, transactional security state across application workers."""

    def __init__(self, db: Session):
        self.db = db

    def lock(self, identity: str):
        import hashlib
        key = int.from_bytes(hashlib.sha256(identity.encode()).digest()[:8], "big", signed=True)
        self.db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})

    def store_handoff(self, jti: str, account_id: int, expires_at):
        import hashlib
        from .models import OAuthHandoff
        self.db.add(OAuthHandoff(jti_hash=hashlib.sha256(jti.encode()).hexdigest(), account_id=account_id, expires_at=expires_at))
        self.db.flush()

    def consume_handoff(self, jti: str, account_id: int):
        import hashlib
        from sqlalchemy import update
        from .models import OAuthHandoff
        return self.db.scalar(update(OAuthHandoff).where(
            OAuthHandoff.jti_hash == hashlib.sha256(jti.encode()).hexdigest(),
            OAuthHandoff.account_id == account_id,
            OAuthHandoff.consumed_at.is_(None), OAuthHandoff.expires_at > func.now(),
        ).values(consumed_at=func.now()).returning(OAuthHandoff.account_id))

    def prune_handoffs(self):
        from .models import OAuthHandoff
        self.db.execute(delete(OAuthHandoff).where(OAuthHandoff.expires_at < func.now()))

    def throttle_window(self, key_hash: str, window_seconds: int):
        from .models import LoginThrottleRecord
        now = self.db.scalar(select(func.extract("epoch", func.clock_timestamp())))
        self.db.execute(delete(LoginThrottleRecord).where(LoginThrottleRecord.expires_at <= func.now()))
        row = self.db.get(LoginThrottleRecord, key_hash)
        failures = [float(t) for t in (row.failures if row else []) if float(t) > float(now) - window_seconds]
        return float(now), row, failures

    def throttle_store(self, key_hash, now, row, failures, settings):
        from .models import LoginThrottleRecord
        if row is None:
            self.lock("login-throttle-capacity")
            count = self.db.scalar(select(func.count()).select_from(LoginThrottleRecord))
            if count >= settings.login_rate_limit_max_keys:
                from .errors import AppError
                raise AppError(503, "login_capacity", "Sign-in is temporarily busy. Please retry.", headers={"Retry-After": "30"})
            row = LoginThrottleRecord(key_hash=key_hash)
            self.db.add(row)
        row.failures = failures + [now]
        row.expires_at = datetime.fromtimestamp(now + settings.login_rate_limit_window_seconds, timezone.utc)
        self.db.flush()

    def throttle_clear(self, key_hash):
        from .models import LoginThrottleRecord
        self.db.execute(delete(LoginThrottleRecord).where(LoginThrottleRecord.key_hash == key_hash))


_FINALIZED = ("completed", "timed_out")


class AnalyticsRepository:
    """Cohort/learner analytics queries (UC11 — admin overview)."""

    def __init__(self, db: Session):
        self.db = db

    def get_assessment(self, assessment_id: int) -> Optional[Assessment]:
        return self.db.get(Assessment, assessment_id)

    def finalized_sessions(
        self, assessment_id: Optional[int] = None
    ) -> list[AssessmentSession]:
        stmt = select(AssessmentSession).where(
            AssessmentSession.status.in_(_FINALIZED)
        )
        if assessment_id is not None:
            stmt = stmt.where(AssessmentSession.assessment_id == assessment_id)
        return list(self.db.scalars(stmt))

    def sessions_missing_competency(
        self, session_ids: list[int]
    ) -> list[int]:
        """Finalized sessions that have submitted evidence but no persisted
        concept_competency rows yet — candidates for a backfill compute."""
        if not session_ids:
            return []
        have_rows = select(ConceptCompetency.session_id).where(
            ConceptCompetency.session_id.in_(session_ids)
        )
        have_evidence = select(Attempt.session_id).where(
            Attempt.session_id.in_(session_ids),
            Attempt.submitted_at.is_not(None),
        )
        return list(
            self.db.scalars(
                select(AssessmentSession.session_id).where(
                    AssessmentSession.session_id.in_(session_ids),
                    AssessmentSession.session_id.in_(have_evidence),
                    AssessmentSession.session_id.not_in(have_rows),
                )
            )
        )

    def cohort_concept_stats(self, assessment_id: Optional[int] = None):
        """Per-concept cohort standing over each learner's LATEST result.

        A learner who sat several sessions contributes only the competency
        row from their most recent finalized session per concept (Postgres
        DISTINCT ON), so resits cannot skew 'how many learners fall below'.
        """
        latest = select(
            ConceptCompetency.concept_id.label("concept_id"),
            AssessmentSession.learner_id.label("learner_id"),
            ConceptCompetency.competency_pct.label("pct"),
            ConceptCompetency.below_target.label("below"),
        ).join(
            AssessmentSession,
            AssessmentSession.session_id == ConceptCompetency.session_id,
        ).where(
            AssessmentSession.status.in_(_FINALIZED)
        )
        if assessment_id is not None:
            latest = latest.where(
                AssessmentSession.assessment_id == assessment_id
            )
        latest = latest.order_by(
            AssessmentSession.learner_id,
            ConceptCompetency.concept_id,
            AssessmentSession.submitted_at.desc().nulls_last(),
            AssessmentSession.session_id.desc(),
        ).distinct(
            AssessmentSession.learner_id, ConceptCompetency.concept_id
        ).subquery()

        return self.db.execute(
            select(
                latest.c.concept_id,
                Concept.concept_code,
                Concept.concept_name,
                Concept.subject_area,
                func.count().label("learners_assessed"),
                func.avg(latest.c.pct).label("avg_pct"),
                func.sum(case((latest.c.below, 1), else_=0)).label("below"),
            )
            .join(Concept, Concept.concept_id == latest.c.concept_id)
            .group_by(
                latest.c.concept_id,
                Concept.concept_code,
                Concept.concept_name,
                Concept.subject_area,
            )
        ).all()

    def cohort_counts(self, assessment_id: Optional[int] = None):
        """(distinct learners with a finalized session, finalized sessions)."""
        stmt = select(
            func.count(func.distinct(AssessmentSession.learner_id)),
            func.count(),
        ).where(AssessmentSession.status.in_(_FINALIZED))
        if assessment_id is not None:
            stmt = stmt.where(AssessmentSession.assessment_id == assessment_id)
        learners, sessions = self.db.execute(stmt).one()
        return learners, sessions

    def finalized_count_for_learner(self, learner_id: int) -> int:
        return self.db.scalar(select(func.count()).select_from(AssessmentSession).where(
            AssessmentSession.learner_id == learner_id, AssessmentSession.status.in_(_FINALIZED)))

    def learner_accounts(self) -> list:
        """Learner accounts with session counts and last activity."""
        last = func.max(func.coalesce(AssessmentSession.submitted_at, AssessmentSession.started_at))
        rows = self.db.execute(
            select(
                Account.account_id,
                Account.email,
                Account.status,
                UserProfile.full_name,
                func.count(AssessmentSession.session_id).label("total"),
                func.sum(
                    case(
                        (AssessmentSession.status.in_(_FINALIZED), 1),
                        else_=0,
                    )
                ).label("finalized"),
                last.label("last_activity"),
            )
            .join(AccountRole, AccountRole.account_id == Account.account_id)
            .join(Role, Role.role_id == AccountRole.role_id)
            .outerjoin(UserProfile, UserProfile.account_id == Account.account_id)
            .outerjoin(
                AssessmentSession,
                AssessmentSession.learner_id == Account.account_id,
            )
            .where(Role.role_name == "Learner")
            .group_by(Account.account_id, Account.email, Account.status, UserProfile.full_name)
            .order_by(Account.email)
        ).all()
        return rows

    def get_learner_account(self, account_id: int) -> Optional[Account]:
        """The account iff it exists and holds the Learner role."""
        return self.db.scalar(
            select(Account)
            .options(selectinload(Account.profile))
            .join(AccountRole, AccountRole.account_id == Account.account_id)
            .join(Role, Role.role_id == AccountRole.role_id)
            .where(
                Account.account_id == account_id,
                Role.role_name == "Learner",
            )
        )

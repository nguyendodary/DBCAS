"""One-time wording correction for the supplied SQL question bank."""
import argparse
from datetime import datetime, timezone

import sqlglot
from sqlglot import exp
from sqlalchemy import select

from ..db import get_session_factory
from ..models import Question
from ..repositories import QuestionRepository
from ..schemas import SqlDatasetInput
from .question_localization import source_fingerprint
from .question_service import _validation_missing

QUESTION_IDS = (13, 14, 15, 16, 17, 26, 27, 38, 39, *range(70, 82))
PREFIX = "Cho sẵn "


def clarify_prompt(prompt, setup_sql):
    if prompt.startswith(PREFIX):
        return prompt
    names = []
    for statement in sqlglot.parse(setup_sql, read="postgres"):
        if isinstance(statement, exp.Create) and statement.args.get("kind") == "TABLE":
            table = statement.this.this if isinstance(statement.this, exp.Schema) else statement.this
            if isinstance(table, exp.Table) and table.name not in names:
                names.append(table.name)
    if not names:
        raise ValueError("No provided tables found")
    tables = ", ".join(names)
    return f"Cho sẵn bảng {tables} và dữ liệu được hiển thị bên dưới. Viết câu truy vấn SQL thực hiện yêu cầu sau:\n\n{prompt.strip()}"


def revise(db):
    repo = QuestionRepository(db)
    changed = []
    for question_id in QUESTION_IDS:
        question = repo.lock_question(question_id)
        if not question or question.question_type != "sql" or question.status == "retired":
            continue
        if question.prompt.startswith(PREFIX):
            continue
        datasets = [SqlDatasetInput.model_validate({key: getattr(d, key) for key in
                    ("dataset_name", "setup_sql", "expected_result", "is_edge_case")})
                    for d in repo.datasets_for(question_id)]
        primary = next((d for d in datasets if not d.is_edge_case), datasets[0] if datasets else None)
        if primary is None:
            raise ValueError("SQL question has no dataset")
        old_prompt, old_status = question.prompt, question.status
        prompt = clarify_prompt(old_prompt, primary.setup_sql)
        explanation, reference = question.explanation, question.reference_answer
        refs = repo.reference_counts(question_id)
        before_missing = _validation_missing(repo, question)
        if refs.get("attempt", 0) or refs.get("session_question_plan", 0):
            question = repo.clone_for_edit(question)
            repo.replace_datasets(question, datasets)
        question.prompt = prompt
        question.explanation = explanation
        question.updated_at = datetime.now(timezone.utc)
        # These rows repeat the canonical Vietnamese text; preserve that match.
        for translation in question.translations:
            if translation.prompt == old_prompt:
                translation.prompt = prompt
                translation.source_hash = source_fingerprint(question)
        db.flush()
        db.expire(question, ["datasets", "concept_tags"])
        if question.reference_answer != reference or _validation_missing(repo, question) != before_missing:
            raise ValueError("Question validation changed unexpectedly")
        # Only the introductory prose changes; SQL, fixtures and scoring are identical.
        question.status = old_status
        changed.append((question_id, question.question_id))
    db.flush()
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        with get_session_factory()() as db:
            changed = revise(db)
            if args.apply:
                db.commit()
            else:
                db.rollback()
            print({"applied": args.apply, "revised_questions": changed})
        if args.apply:
            from ..content_snapshot import export_snapshot
            export_snapshot()
            print("Shared content snapshot updated.")
    except Exception as error:
        print("Revision failed:", type(error).__name__)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

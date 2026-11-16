"""CLI for automatic CLO tagging and coverage reporting.

Usage (from ``backend``):

    python -m app.clo_tagging tag
    python -m app.clo_tagging tag --question-id 42
    python -m app.clo_tagging tag --limit 50
    python -m app.clo_tagging coverage

``tag`` first applies the deterministic single-reachable-CLO rule, then asks
the configured LLM provider for proposals on remaining questions. Provider
failures leave rows untouched and are reported by question ID and error code.
No question text or answer is printed or sent to the provider.
"""

import argparse
import json

from .config import get_settings
from .db import get_session_factory
from .services.clo_tagging import coverage_report, tag_unmapped_questions
from .services.llm import build_llm_service


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    tag = commands.add_parser("tag", help="Assign or propose CLOs")
    tag.add_argument(
        "--question-id",
        action="append",
        type=int,
        help="Process this question ID even if it already has a CLO row",
    )
    tag.add_argument(
        "--limit",
        type=int,
        help="Maximum number of questions to process",
    )

    commands.add_parser("coverage", help="Print CLO coverage counts and missing IDs")
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "tag" and args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be at least 1")

    with get_session_factory()() as db:
        if args.command == "coverage":
            print(json.dumps(coverage_report(db).as_dict(), indent=2, ensure_ascii=False))
            return

        llm = build_llm_service(get_settings(), db)
        report = tag_unmapped_questions(
            db,
            llm,
            question_ids=args.question_id,
            limit=args.limit,
        )
        coverage = coverage_report(db)
        print(
            json.dumps(
                {"tagging": report.as_dict(), "coverage": coverage.as_dict()},
                indent=2,
                ensure_ascii=False,
            )
        )
        if report.failed:
            raise SystemExit(1)
        if args.question_id is None and args.limit is None and coverage.questions_without_primary:
            raise SystemExit(1)


if __name__ == "__main__":
    main()

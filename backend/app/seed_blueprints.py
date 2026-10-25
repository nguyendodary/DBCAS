"""Controlled backfill of approved blueprints for published assessments.

Database-changing activation is explicit: without ``--confirm`` this command
only prints the target and the assessments that have no blueprint rows. Run it
against a restored clone first; the persistent bank requires separate approval.
"""
import argparse
from urllib.parse import urlsplit

from sqlalchemy import func, select

from .config import get_settings
from .db import get_session_factory
from .models import Assessment, AssessmentBlueprint
from .services.blueprints import ensure_all_blueprints


def _mask(url):
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.username or '?'}:***@{parts.hostname or '?'}:{parts.port or 0}{parts.path}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm", action="store_true",
                        help="Actually insert blueprint rows (otherwise dry run)")
    args = parser.parse_args()
    settings = get_settings()
    print(f"Target: {_mask(settings.database_url)}")
    with get_session_factory()() as db:
        published = list(db.scalars(select(Assessment)
                                    .where(Assessment.status == "published")
                                    .order_by(Assessment.assessment_id)))
        for assessment in published:
            count = db.scalar(select(func.count()).select_from(AssessmentBlueprint)
                              .where(AssessmentBlueprint.assessment_id == assessment.assessment_id))
            print(f"  assessment {assessment.assessment_id}: {assessment.title} "
                  f"({count} blueprint versions)")
        if not args.confirm:
            print("Dry run only; pass --confirm under the approved activation runbook.")
            return
        created = ensure_all_blueprints(db)
        db.commit()
        print(f"Inserted {len(created)} immutable blueprint versions.")


if __name__ == "__main__":
    main()

"""Read-only deployment guards; unsafe bootstrap credentials fail startup."""
from ..repositories import CurriculumRepository
from ..security import verify_password


def validate_deployment_accounts(db, settings):
    if settings.deployment_mode == "development":
        return
    # The documented seed password is public. An active account retaining it
    # must never be accepted in staging/production, regardless of email/role.
    for account in CurriculumRepository(db).list_accounts():
        if account.status == "active" and verify_password("Admin123!", account.password_hash):
            raise RuntimeError("Unsafe development account credentials detected. Rotate or disable the seeded account before deployment.")

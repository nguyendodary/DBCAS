"""Read-only deployment guards; unsafe bootstrap credentials fail startup."""
from ..repositories import CurriculumRepository
from ..security import verify_password
from ..credential_policy import DEMO_ACCOUNT_PASSWORDS


def validate_deployment_accounts(db, settings):
    if settings.deployment_mode == "development":
        return
    # Account status can later change. Even disabled demo accounts must rotate
    # their public password before this database is promoted out of development.
    for account in CurriculumRepository(db).list_accounts():
        if any(verify_password(password, account.password_hash) for password in DEMO_ACCOUNT_PASSWORDS):
            raise RuntimeError("Unsafe development account credentials detected. Rotate known demo passwords before deployment.")

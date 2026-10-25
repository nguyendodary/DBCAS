"""Authorize one existing active Administrator through an explicit operator action.

This local command requires database access and an account ID plus interactive
email confirmation. There is deliberately no unauthenticated HTTP bootstrap.
"""
import argparse
from getpass import getpass

from sqlalchemy import select

from .db import get_session_factory
from .errors import AppError
from .models import Account
from .repositories import AccountRepository, SecurityRepository


def bootstrap_role_manager(db, account_id: int, confirmed_email: str) -> int:
    security = SecurityRepository(db)
    security.lock("account-security:roles-and-status")
    security.lock("bootstrap:role-manager")
    repo = AccountRepository(db)
    if repo.active_role_manager_count():
        raise AppError(409, "role_manager_exists", "An active role manager is already configured")
    account = repo.get_for_update(account_id)
    if account is None:
        raise AppError(404, "account_not_found", "Account not found")
    if account.email.casefold() != confirmed_email.strip().casefold():
        raise AppError(409, "account_confirmation_mismatch", "Account confirmation did not match")
    if account.status != "active" or not any(role.role_name == "Administrator" for role in account.roles):
        raise AppError(409, "role_manager_target_invalid", "The selected account must be an active Administrator")
    if account.can_manage_roles:
        return account.account_id
    account.can_manage_roles = True
    repo.add_role_audit(action_type="ROLE_MANAGER_BOOTSTRAPPED", actor_account_id=None,
                        target_account_id=account.account_id, previous_role=None, new_role=None)
    db.commit()
    return account.account_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account-id", required=True, type=int)
    args = parser.parse_args()
    with get_session_factory()() as db:
        account = db.scalar(select(Account).where(Account.account_id == args.account_id))
        if account is None:
            raise SystemExit("No account exists with that ID.")
        print(f"Selected account ID: {account.account_id}")
        confirmation = getpass("Type the account email to confirm role-manager access: ")
        try:
            bootstrap_role_manager(db, args.account_id, confirmation)
        except AppError as error:
            raise SystemExit(error.message) from None
    print("Role-management capability authorized. No credentials were printed.")


if __name__ == "__main__":
    main()

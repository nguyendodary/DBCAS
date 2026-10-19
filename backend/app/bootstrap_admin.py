"""Create the first trusted deployment administrator without demo credentials."""
import argparse
from getpass import getpass
from .db import get_session_factory
from .errors import AppError
from .repositories import AccountRepository, SecurityRepository
from .schemas import ProvisionAccountRequest
from .security import hash_password


def bootstrap(db, payload):
    repo = AccountRepository(db)
    security = SecurityRepository(db)
    security.lock('account-security:roles-and-status')
    security.lock('bootstrap:first-administrator')
    if repo.has_administrator():
        raise AppError(409, 'administrator_exists', 'Use authenticated account provisioning for additional administrators')
    if repo.find_by_email(payload.email):
        raise AppError(409, 'email_exists', 'This email is already registered')
    if payload.password == 'Admin123!':
        raise AppError(422, 'unsafe_password', 'The documented development password is not allowed for deployment bootstrap')
    account = repo.create_provisioned(payload.email, hash_password(payload.password), payload.name, 'Administrator')
    account.status = 'active'
    account.can_manage_roles = True
    db.flush()
    repo.add_role_audit(action_type='ROLE_MANAGER_BOOTSTRAPPED', actor_account_id=None,
                        target_account_id=account.account_id, previous_role=None, new_role=None)
    db.commit()
    return account.account_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--email', required=True)
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    password = getpass('New administrator password: ')
    if getpass('Confirm password: ') != password:
        raise SystemExit('Passwords do not match')
    payload = ProvisionAccountRequest(name=args.name, email=args.email, password=password)
    with get_session_factory()() as db:
        bootstrap(db, payload)
    print('Initial administrator created. No credentials were printed.')


if __name__ == '__main__':
    main()

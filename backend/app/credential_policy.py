"""Public development credentials are never deployment credentials."""

DEMO_ACCOUNT_PASSWORDS = ('Demo12345!', 'Admin123!', 'Learner123!')
KNOWN_DEMO_CREDENTIALS = frozenset(value.casefold() for value in (
    *DEMO_ACCOUNT_PASSWORDS, 'postgres', 'password', 'test', 'dbcas_dev',
    'learner_ro_dev', 'changeme', 'change_me', 'change_me_sandbox', 'change_me_jwt_secret',
))


def is_demo_credential(value: str) -> bool:
    return value.strip().casefold() in KNOWN_DEMO_CREDENTIALS

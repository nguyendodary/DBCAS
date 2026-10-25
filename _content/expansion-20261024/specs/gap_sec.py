"""Practice-depth gap fill for A6 Security (row-level security).

Formal assessment is blocked by the mandatory SQL quota; practice failed
because PG-RLS had no EASY family.
"""

from lib import mcq
from sources import PG_RLS

QUESTIONS = [
    mcq(
        "sec-easy-rls-basics",
        ["PG-RLS"],
        2,
        (
            "A table has row-level security enabled with no policies defined. "
            "What happens when an ordinary user selects from it?"
        ),
        [
            "The user sees no rows, because enabling row security without a "
            "policy denies access by default.",
            "The user sees all rows, because row security filters only after a "
            "policy is added.",
            "The statement fails with a syntax error until a policy is created.",
            "The user sees every third row, because PostgreSQL applies a "
            "default sampling policy.",
        ],
        0,
        (
            "Row-level security is deny-by-default: once ENABLE ROW LEVEL "
            "SECURITY is set and no policy grants access, ordinary users see no "
            "rows. Access is granted by CREATE POLICY expressions. The table "
            "owner bypasses row security unless FORCE ROW LEVEL SECURITY is "
            "set, but an ordinary user is filtered. There is no syntax error "
            "and no implicit sampling."
        ),
        [PG_RLS],
    ),
]

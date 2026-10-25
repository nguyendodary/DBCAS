"""Practice-depth gap fill for A6 Server Programming (procedures).

The mandatory SQL quota keeps formal assessment blocked, but PG-PROC had no
EASY or HARD family, so practice failed in both bands.
"""

from lib import mcq
from sources import PG_CALL, PG_PLPGSQL_TX, PG_PROC

QUESTIONS = [
    mcq(
        "sp-easy-procedure-basics",
        ["PG-PROC"],
        2,
        (
            "How is a PostgreSQL procedure created with CREATE PROCEDURE "
            "invoked, and how does it differ from an ordinary function?"
        ),
        [
            "It is invoked with CALL and may execute transaction control "
            "statements, whereas a function is used in expressions and cannot "
            "commit or roll back.",
            "It is invoked with SELECT and must return a table, whereas a "
            "function cannot return rows.",
            "It is invoked with CALL but cannot accept parameters, whereas a "
            "function can accept parameters.",
            "It is invoked automatically by the planner whenever its name "
            "appears in a query.",
        ],
        0,
        (
            "Procedures are called with the CALL statement and are designed for "
            "procedural work that may include transaction control. Functions "
            "return a value, can be used inside SQL expressions, and may not "
            "commit or roll back. Procedures accept parameters, and the planner "
            "never invokes them implicitly."
        ),
        [PG_PROC, PG_CALL, PG_PLPGSQL_TX],
    ),
    mcq(
        "sp-hard-call-transaction-control",
        ["PG-PROC"],
        4,
        (
            "A procedure contains a COMMIT statement. Under which condition can "
            "it execute that COMMIT?"
        ),
        [
            "Only when CALL runs in its own transaction, not when CALL is "
            "executed inside an explicit transaction block.",
            "Always, because procedures are allowed to commit even inside an "
            "explicit transaction block.",
            "Only when the procedure was created with CREATE FUNCTION rather "
            "than CREATE PROCEDURE.",
            "Never, because SQL procedures cannot contain transaction control "
            "statements at all.",
        ],
        0,
        (
            "The CALL documentation states that if CALL is executed in a "
            "transaction block, the called procedure cannot execute transaction "
            "control statements; they are allowed only when CALL runs in its "
            "own transaction. Procedures do support COMMIT and ROLLBACK, which "
            "is a key difference from functions, but an enclosing explicit "
            "transaction block removes that ability."
        ),
        [PG_CALL, PG_PROC],
    ),
]

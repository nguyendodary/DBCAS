"""PostgreSQL Functions expansion, HARD band (levels 4-5).

Eight MCQs supply the numeric, string, pattern-matching and date coverage
that was absent from the HARD band while keeping the two existing SQL
practicals and the essay.
"""

from lib import mcq
from sources import (
    PG_FUNCTIONS_DATE,
    PG_FUNCTIONS_MATH,
    PG_FUNCTIONS_STRING,
    PG_PATTERN,
)

QUESTIONS = [
    mcq(
        "fn-hard-round-negative",
        ["PG-FUNC-NUM"],
        4,
        (
            "What do round(-1.7) and trunc(-1.7) return for a numeric argument?"
        ),
        [
            "round returns -2 and trunc returns -1.",
            "Both return -1, because negative values are rounded toward zero.",
            "round returns -1 and trunc returns -2.",
            "Both return -2, because trunc rounds to the nearest integer.",
        ],
        0,
        (
            "round moves to the nearest integer, so -1.7 becomes -2. trunc "
            "discards the fractional part toward zero, so -1.7 becomes -1. On "
            "negative values the two functions therefore diverge; trunc is not "
            "a synonym for rounding."
        ),
        [PG_FUNCTIONS_MATH],
    ),
    mcq(
        "fn-hard-integer-division",
        ["PG-FUNC-NUM"],
        4,
        (
            "Columns a and b are both declared INT. The expression a / b is "
            "evaluated with a = 7 and b = 2. What is the result, and how do you "
            "obtain 3.5?"
        ),
        [
            "The result is 3, because integer division truncates; cast an "
            "operand, for example a::numeric / b, to get 3.5.",
            "The result is 3.5, because division always produces a numeric "
            "value.",
            "The result is an error, because the division is not exact.",
            "The result is 4, because integer division rounds to the nearest "
            "integer.",
        ],
        0,
        (
            "Division between two integers performs integer division, which "
            "truncates the fractional part, so 7 / 2 is 3. Promoting one operand "
            "to numeric or double precision changes the operator to a "
            "fractional division and yields 3.5. No rounding and no error "
            "occurs."
        ),
        [PG_FUNCTIONS_MATH],
    ),
    mcq(
        "fn-hard-mod-sign",
        ["PG-FUNC-NUM"],
        4,
        (
            "What does mod(-7, 3) return in PostgreSQL?"
        ),
        [
            "-1",
            "1",
            "2",
            "3",
        ],
        0,
        (
            "mod returns the remainder of the division and takes the sign of "
            "the dividend, so -7 = (-3) * 3 + 2 does not describe the result; "
            "the truncating quotient is -2, leaving remainder -1. The positive "
            "counterpart mod(7, 3) is 1, which is why the sign must be checked "
            "explicitly when a non-negative remainder is required."
        ),
        [PG_FUNCTIONS_MATH],
    ),
    mcq(
        "fn-hard-concat-null",
        ["PG-FUNC-STR"],
        4,
        (
            "Given that the column middle_name is NULL, how do 'An' || "
            "middle_name || 'Le' and concat('An', middle_name, 'Le') differ?"
        ),
        [
            "The || expression evaluates to NULL, while concat returns 'AnLe' "
            "because it ignores NULL arguments.",
            "Both return NULL, because any NULL input propagates.",
            "Both return 'AnLe', because both operators skip NULL.",
            "The || expression returns 'AnLe', while concat returns NULL.",
        ],
        0,
        (
            "The || operator is NULL-propagating: a NULL operand makes the whole "
            "concatenation NULL. concat is a function that treats NULL arguments "
            "as empty strings, so it returns 'AnLe'. This difference matters "
            "when building labels from optional columns."
        ),
        [PG_FUNCTIONS_STRING],
    ),
    mcq(
        "fn-hard-char-length",
        ["PG-FUNC-STR"],
        4,
        (
            "For a UTF-8 database and the value name = 'é' (one character, two "
            "bytes), what do char_length(name) and octet_length(name) return?"
        ),
        [
            "char_length returns 1 and octet_length returns 2.",
            "Both return 1, because length is measured in characters.",
            "char_length returns 2 and octet_length returns 1.",
            "Both return 2, because PostgreSQL stores strings as bytes.",
        ],
        0,
        (
            "char_length counts characters, so the accented character counts "
            "once. octet_length counts bytes in the server encoding, and in "
            "UTF-8 'é' occupies two bytes. Neither function pads or trims the "
            "value."
        ),
        [PG_FUNCTIONS_STRING],
    ),
    mcq(
        "fn-hard-like-escape",
        ["PG-PATTERN"],
        4,
        (
            "Column code contains the value 'A_B'. Which LIKE pattern matches "
            "that literal underscore rather than treating it as the "
            "single-character wildcard?"
        ),
        [
            "code LIKE 'A\\_B' ESCAPE '\\'",
            "code LIKE 'A_B'",
            "code LIKE 'A__B'",
            "code SIMILAR TO 'A_B'",
        ],
        0,
        (
            "In LIKE, _ matches any single character, so 'A_B' also matches "
            "'AXB'. Escaping the underscore with an ESCAPE character makes it "
            "literal. 'A__B' requires two extra characters, and SIMILAR TO "
            "keeps _ as a wildcard as well."
        ),
        [PG_PATTERN],
    ),
    mcq(
        "fn-hard-like-is-whole-string",
        ["PG-PATTERN"],
        4,
        (
            "Which statement about pattern matching is correct?"
        ),
        [
            "LIKE must match the entire string, so 'PostgreSQL' LIKE 'Post' is "
            "false, whereas the regular-expression operator ~ finds a match "
            "anywhere unless anchored.",
            "LIKE finds the pattern anywhere in the string, exactly like ~.",
            "The ~ operator always requires an anchor at both ends.",
            "ILIKE is case-sensitive and LIKE is case-insensitive.",
        ],
        0,
        (
            "LIKE treats the pattern as a whole-string match unless % wildcards "
            "extend it, so 'Post' does not match 'PostgreSQL'. The ~ operator "
            "matches a substring anywhere unless the pattern is anchored with ^ "
            "and $. ILIKE is the case-insensitive counterpart of LIKE."
        ),
        [PG_PATTERN],
    ),
    mcq(
        "fn-hard-date-plus-integer",
        ["PG-FUNC-DATE"],
        4,
        (
            "Given today = DATE '2024-02-28', what is today + 1?"
        ),
        [
            "DATE '2024-02-29', because adding an integer to a date advances it "
            "by that many days and the year is a leap year.",
            "An error, because an integer cannot be added to a date.",
            "TIMESTAMP '2024-02-28 00:00:01', because the integer is read as "
            "seconds.",
            "DATE '2024-03-01', because February always has 28 days.",
        ],
        0,
        (
            "Adding an integer to a date advances the date by that number of "
            "days, and calendar rules apply, so 2024-02-28 plus one day is "
            "2024-02-29 because 2024 is a leap year. Adding an interval would "
            "also work, but an integer is not interpreted as seconds."
        ),
        [PG_FUNCTIONS_DATE],
    ),
]

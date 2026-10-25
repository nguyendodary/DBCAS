"""PostgreSQL Data Types expansion, HARD band (levels 4-5).

Six MCQs restore the HARD MCQ quota and give every data-type concept a HARD
family. Facts were checked against the running PostgreSQL 17 sandbox.
"""

from lib import mcq
from sources import (
    PG_DOMAIN,
    PG_FUNCTIONS_NET,
    PG_TYPE_BOOL,
    PG_TYPE_CHAR,
    PG_TYPE_DATE,
    PG_TYPE_NET,
    PG_TYPE_NUM,
)

QUESTIONS = [
    mcq(
        "dt-hard-numeric-vs-float-round",
        ["PG-TYPE-NUM"],
        4,
        (
            "In PostgreSQL, what do round(2.5::numeric) and round(2.5::float8) "
            "return?"
        ),
        [
            "3 for numeric and 2 for float8, because numeric rounds halves away "
            "from zero while float8 rounds ties to the nearest even integer.",
            "3 for both, because round always rounds halves away from zero.",
            "2 for both, because round always rounds halves to even.",
            "2 for numeric and 3 for float8, because float8 carries more "
            "precision.",
        ],
        0,
        (
            "numeric is exact decimal arithmetic and rounds a tie away from "
            "zero, so 2.5 becomes 3. float8 follows binary floating-point "
            "rules that round ties to the nearest even integer, so 2.5 becomes "
            "2. This is a genuine semantic difference between the two families "
            "of numeric types, not a display artifact."
        ),
        [PG_TYPE_NUM],
    ),
    mcq(
        "dt-hard-date-difference",
        ["PG-TYPE-DATE"],
        4,
        (
            "What does the expression DATE '2024-03-01' - DATE '2024-02-01' "
            "return?"
        ),
        [
            "The integer 29, because subtracting two dates returns a number of "
            "days.",
            "The interval '29 days', because date arithmetic always returns an "
            "interval.",
            "The integer 28, because February 2024 is counted as 28 days.",
            "The timestamp 2024-02-29 00:00:00, because the later date is "
            "shifted backwards.",
        ],
        0,
        (
            "The date - date operator returns an integer count of days, and "
            "2024 is a leap year so February has 29 days. Subtracting two "
            "timestamps, by contrast, returns an interval. Neither subtraction "
            "produces a timestamp."
        ),
        [PG_TYPE_DATE],
    ),
    mcq(
        "dt-hard-bool-aggregate",
        ["PG-TYPE-BOOL"],
        4,
        (
            "The table flag(v BOOLEAN) contains the three rows TRUE, NULL and "
            "TRUE. What do SELECT bool_and(v) and SELECT bool_or(v) return?"
        ),
        [
            "Both return TRUE, because the boolean aggregates ignore NULL "
            "inputs.",
            "bool_and returns NULL and bool_or returns TRUE, because any NULL "
            "input makes and-accumulation unknown.",
            "Both return NULL, because NULL propagates through aggregates.",
            "bool_and returns FALSE and bool_or returns TRUE, because NULL is "
            "treated as FALSE.",
        ],
        0,
        (
            "Like other ordinary aggregates, bool_and and bool_or ignore NULL "
            "inputs rather than propagating them. The remaining values are all "
            "TRUE, so bool_and is TRUE and bool_or is TRUE. With only NULL "
            "inputs both aggregates return NULL, but that is not this dataset."
        ),
        [PG_TYPE_BOOL],
    ),
    mcq(
        "dt-hard-char-concatenation",
        ["PG-TYPE-CHAR"],
        4,
        (
            "For the expression 'ab'::char(4) || 'cd', what does PostgreSQL "
            "return?"
        ),
        [
            "'abcd', because the trailing padding of the character value is not "
            "part of the concatenated text.",
            "'ab  cd', because the stored padding spaces are preserved.",
            "An error, because a character(4) value cannot be concatenated "
            "with an untyped literal.",
            "'abcd    ', because the result is padded to the combined declared "
            "width.",
        ],
        0,
        (
            "A character(4) value is blank-padded in storage, but trailing "
            "spaces are removed when the value is converted to text for the "
            "concatenation operator, so 'ab' becomes 'ab' and the result is "
            "'abcd'. Padding is a storage and comparison property of "
            "character(n), not content that the operator carries into the "
            "result."
        ),
        [PG_TYPE_CHAR],
    ),
    mcq(
        "dt-hard-domain-constraints",
        ["PG-DOMAIN"],
        4,
        (
            "A domain is defined as CREATE DOMAIN positive_int AS integer CHECK "
            "(VALUE > 0). Which statement about using it is correct?"
        ),
        [
            "Every column declared with positive_int rejects zero and negative "
            "values, and casting a positive_int value to integer removes the "
            "domain constraint.",
            "The CHECK is copied only into the first column that uses the "
            "domain; later columns get plain integers.",
            "The CHECK is evaluated once when the domain is created and never "
            "again, so later inserts are unchecked.",
            "Casting a plain integer to positive_int skips the CHECK, because "
            "casts do not run domain constraints.",
        ],
        0,
        (
            "A domain packages a base type with constraints, and those "
            "constraints are enforced whenever a value is stored in any column "
            "of that domain, so zero and negatives are rejected everywhere the "
            "domain is used. Casting a domain value to its base type yields an "
            "unconstrained base value, whereas casting a base value to the "
            "domain applies the domain's constraints."
        ),
        [PG_DOMAIN],
    ),
    mcq(
        "dt-hard-inet-containment",
        ["PG-TYPE-MISC"],
        4,
        (
            "What do '192.168.1.5'::inet << '192.168.1.0/24'::inet and "
            "'192.168.1.0/24'::inet >> '192.168.1.5'::inet return?"
        ),
        [
            "Both return TRUE: << tests whether the left address or network is "
            "strictly contained by the right one, and >> is the reverse test.",
            "Both return FALSE, because an address without a netmask cannot be "
            "compared with a network.",
            "The first returns TRUE and the second returns FALSE, because >> "
            "compares only identical netmask lengths.",
            "Both return the host address 192.168.1.5, because inet operators "
            "return addresses rather than booleans.",
        ],
        0,
        (
            "The inet type stores an address optionally with a netmask. The "
            "<< operator asks whether the left address or network is strictly "
            "contained by the right one, so a host address (/32) inside "
            "192.168.1.0/24 qualifies; >> asks the symmetric question and is "
            "also true here. Identical netmasks make << false, since containment "
            "is strict. Both operators return boolean."
        ),
        [PG_TYPE_NET, PG_FUNCTIONS_NET],
    ),
]

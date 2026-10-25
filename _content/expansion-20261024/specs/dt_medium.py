"""PostgreSQL Data Types expansion, MEDIUM band (level 3).

Only the boolean and fixed-length character concepts had no MEDIUM family; the
band already satisfies its type quotas.
"""

from lib import mcq
from sources import PG_TYPE_BOOL, PG_TYPE_CHAR

QUESTIONS = [
    mcq(
        "dt-medium-boolean-input",
        ["PG-TYPE-BOOL"],
        3,
        (
            "A text value is cast to boolean. Which of these input strings is "
            "NOT accepted by PostgreSQL as a boolean value?"
        ),
        [
            "'enable'",
            "'yes'",
            "'on'",
            "'1'",
        ],
        0,
        (
            "PostgreSQL accepts TRUE/FALSE, the spellings t/f, true/false, "
            "y/n, yes/no, on/off and 1/0, plus unique prefixes of true and "
            "false. 'enable' is none of these and no prefix rule makes it "
            "valid, so the cast fails. The other three options are documented "
            "synonyms for true."
        ),
        [PG_TYPE_BOOL],
    ),
    mcq(
        "dt-medium-char-padding",
        ["PG-TYPE-CHAR"],
        3,
        (
            "Which statement correctly describes how character(n) and character "
            "varying(n) store and compare values?"
        ),
        [
            "character(n) is blank-padded to n characters, but trailing spaces "
            "are insignificant in comparison, so 'ab'::char(4) = 'ab'::char(2) "
            "is true.",
            "character(n) stores exactly the characters supplied and pads only "
            "when the value is displayed.",
            "character varying(n) blank-pads every value to n, while "
            "character(n) stores the exact input length.",
            "Comparing character values of different declared lengths raises an "
            "error instead of returning a boolean.",
        ],
        0,
        (
            "Values of type character(n) are physically padded with spaces to "
            "the declared width; trailing spaces are removed when the value is "
            "converted to another string type, and comparisons ignore them, so "
            "different declared widths can compare equal. character varying(n) "
            "stores the value without padding and only enforces the maximum "
            "length. Comparisons never raise an error merely because the "
            "declared lengths differ."
        ),
        [PG_TYPE_CHAR],
    ),
]

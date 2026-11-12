"""PostgreSQL Data Types expansion, EASY band (levels 1-2).

The band already has wide MCQ coverage but no practical and no essay, and the
json, range, domain and collation concepts had no EASY family at all. Two
read-only practicals expose a JSONB payload and a range overlap test; the
essay covers domains and collations, which have no legal learner-side DDL in
the sandbox.
"""

from lib import essay, sqlq
from sources import PG_COLLATION, PG_DOMAIN, PG_TYPE_JSON, PG_TYPE_RANGE

QUESTIONS = [
    sqlq(
        "dt-easy-json-carrier",
        ["PG-TYPE-JSON"],
        2,
        (
            "The setup creates shipment(order_id INT PRIMARY KEY, payload JSONB "
            "NOT NULL) and inserts JSON objects. Return order_id and the "
            "carrier value extracted from payload as text, aliased carrier, "
            "ordered by order_id ascending. Rows whose object has no carrier "
            "key, or whose carrier value is JSON null, must show NULL."
        ),
        (
            "SELECT order_id, payload ->> 'carrier' AS carrier "
            "FROM shipment ORDER BY order_id"
        ),
        [
            (
                "mixed_payloads",
                False,
                "CREATE TABLE shipment(order_id INT PRIMARY KEY, payload JSONB "
                "NOT NULL);"
                "INSERT INTO shipment VALUES "
                "(1,'{\"carrier\": \"dhl\"}'),"
                "(2,'{\"carrier\": \"ups\"}'),"
                "(3,'{}');",
            ),
            (
                "json_null_and_missing_key",
                True,
                "CREATE TABLE shipment(order_id INT PRIMARY KEY, payload JSONB "
                "NOT NULL);"
                "INSERT INTO shipment VALUES "
                "(1,'{\"carrier\": null}'),"
                "(2,'{\"carrier\": \"fedex\"}');",
            ),
        ],
        (
            "The ->> operator extracts an object field as text, so the JSON "
            "string \"dhl\" becomes the SQL text dhl. A missing key and a JSON "
            "null both yield SQL NULL, which is why order 3 and the JSON-null "
            "row report NULL instead of an error or an empty string. Using -> "
            "instead would return a JSON value rather than text."
        ),
        [PG_TYPE_JSON],
    ),
    sqlq(
        "dt-easy-range-overlap",
        ["PG-TYPE-RANGE"],
        2,
        (
            "The setup creates booking(room_id INT PRIMARY KEY, period INT4RANGE "
            "NOT NULL) with half-open integer ranges. Return room_id for every "
            "booking whose period overlaps int4range(4, 6), ordered by room_id "
            "ascending."
        ),
        (
            "SELECT room_id FROM booking "
            "WHERE period && int4range(4, 6) ORDER BY room_id"
        ),
        [
            (
                "overlapping_and_separate_ranges",
                False,
                "CREATE TABLE booking(room_id INT PRIMARY KEY, period INT4RANGE "
                "NOT NULL);"
                "INSERT INTO booking VALUES "
                "(1,'[1,5)'),(2,'[5,9)'),(3,'[4,6)'),(4,'[10,12)');",
            ),
            (
                "adjacent_ranges_do_not_overlap",
                True,
                "CREATE TABLE booking(room_id INT PRIMARY KEY, period INT4RANGE "
                "NOT NULL);"
                "INSERT INTO booking VALUES (1,'[1,4)'),(2,'[6,9)');",
            ),
        ],
        (
            "The && operator tests whether two ranges have any common point. "
            "Because ranges are half-open, [1,5) and [5,9) both contain points "
            "that fall inside [4,6), while [10,12) does not. In the edge "
            "dataset [1,4) and [6,9) are merely adjacent to the test range and "
            "share no point with it, so the result is empty."
        ),
        [PG_TYPE_RANGE],
    ),
    essay(
        "dt-easy-domain-collation",
        ["PG-DOMAIN", "PG-COLLATION"],
        2,
        (
            "Explain what a PostgreSQL domain is and what a collation controls. "
            "For the domain, describe how a constraint attached to the domain "
            "is enforced across every column that uses it. For collation, "
            "explain how the choice between the C collation and a locale-aware "
            "collation can change ORDER BY results and comparisons."
        ),
        (
            "A domain is a user-defined data type built on an existing base "
            "type, optionally with a DEFAULT, a NOT NULL constraint and CHECK "
            "constraints. For example CREATE DOMAIN positive_price AS numeric "
            "CHECK (VALUE > 0) creates a reusable type; every column declared "
            "with positive_price rejects values that violate the check, so the "
            "rule is defined once and enforced everywhere the domain is used. "
            "ALTER DOMAIN can add or drop constraints, and by default adding a "
            "CHECK validates existing column values. Casting a domain value to "
            "its base type produces an ordinary base-type value without the "
            "domain's constraints. A collation is the set of rules for "
            "comparing and sorting text. COLLATE selects it per expression or "
            "column, while the database and column defaults apply otherwise. "
            "The C collation compares byte values, so uppercase letters sort "
            "before lowercase letters and accents are not normalized, whereas a "
            "locale-aware collation such as en_US orders letters "
            "alphabetically, ignoring case and treating accented letters near "
            "their unaccented forms. The same text can therefore sort "
            "differently, and a unique index built with one collation can "
            "consider two strings equal that another collation considers "
            "distinct."
        ),
        (
            "The answer must define a domain as a named type with optional "
            "constraints, explain that its CHECK/NOT NULL rules apply to every "
            "column of that domain, and define a collation as the comparison "
            "and sort rules for text. It must give at least one concrete "
            "consequence, such as a rejected out-of-range value or a different "
            "ORDER BY result under C versus a locale-aware collation."
        ),
        (
            "Identifies neither the domain-as-type idea nor collation as "
            "comparison rules; or describes both incorrectly.",
            "Defines one of the two concepts correctly; for example explains a "
            "domain check but treats collation only as character encoding, or "
            "vice versa.",
            "Defines both concepts correctly and gives one concrete "
            "consequence, but omits either domain reuse across columns or the "
            "effect of collation on sort/equality behavior.",
            "Defines the domain as a reusable named type whose constraints are "
            "enforced in every column that uses it, and defines collation as "
            "comparison/sort rules; gives concrete consequences for both, "
            "including a C-versus-locale ORDER BY or equality difference.",
        ),
        [PG_DOMAIN, PG_COLLATION],
    ),
]

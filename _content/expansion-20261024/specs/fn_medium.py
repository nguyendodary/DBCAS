"""PostgreSQL Functions expansion, MEDIUM band (level 3).

Three full-text-search MCQs close the MEDIUM MCQ quota (the band already has
eight SQL families and one essay).
"""

from lib import mcq
from sources import PG_TEXTSEARCH

QUESTIONS = [
    mcq(
        "fn-medium-plainto-vs-phraseto",
        ["PG-FTS"],
        3,
        (
            "For the text 'database systems', which statement correctly "
            "contrasts plainto_tsquery and phraseto_tsquery?"
        ),
        [
            "plainto_tsquery produces a query that requires both terms anywhere "
            "in the document, while phraseto_tsquery requires them adjacent and "
            "in order.",
            "plainto_tsquery requires adjacent terms, while phraseto_tsquery "
            "accepts them in any order.",
            "Both produce identical queries; they differ only in the dictionary "
            "used.",
            "phraseto_tsquery disables stemming, while plainto_tsquery applies "
            "it.",
        ],
        0,
        (
            "plainto_tsquery turns the input into terms combined with AND (&), "
            "so each term may appear anywhere. phraseto_tsquery combines the "
            "terms with the phrase operator <->, which requires them to be "
            "adjacent and in the given order. Both run the words through the "
            "text search dictionary, so stemming is applied in both."
        ),
        [PG_TEXTSEARCH],
    ),
    mcq(
        "fn-medium-tsquery-operators",
        ["PG-FTS"],
        3,
        (
            "In a tsquery, what does the expression 'alpha <-> beta' require?"
        ),
        [
            "The lexeme alpha immediately followed by beta in the document.",
            "The lexeme alpha and beta anywhere in the document.",
            "Either alpha or beta, but not both.",
            "alpha within the same sentence as beta, in any order.",
        ],
        0,
        (
            "The <-> operator is the phrase operator: it requires its operands "
            "to be adjacent and in the specified order. The & operator means "
            "both anywhere, | means either, and ! negates. Sentence proximity, "
            "not strict adjacency, would be expressed with a distance operator "
            "such as <N>."
        ),
        [PG_TEXTSEARCH],
    ),
    mcq(
        "fn-medium-websearch-to-tsquery",
        ["PG-FTS"],
        3,
        (
            "What does websearch_to_tsquery('english', 'database or network "
            "-nosql') produce?"
        ),
        [
            "A query equivalent to database OR (network AND NOT nosql); the minus "
            "negates only nosql, and AND binds more tightly than OR.",
            "A query that matches only the literal phrase 'database or network "
            "-nosql'.",
            "A syntax error, because websearch_to_tsquery does not accept the "
            "word or.",
            "A query that requires database AND network AND nosql.",
        ],
        0,
        (
            "websearch_to_tsquery parses the input as 'databas' | 'network' & "
            "!'nosql' (terms are stemmed). The minus negates only the following "
            "term, and & binds more tightly than |, so the query means database "
            "OR (network AND NOT nosql). A document that contains database and "
            "nosql but not network still matches. The function never raises an "
            "error for such input, which is why it suits raw user text."
        ),
        [PG_TEXTSEARCH],
    ),
]

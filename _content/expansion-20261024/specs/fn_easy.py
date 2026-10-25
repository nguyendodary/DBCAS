"""PostgreSQL Functions expansion, EASY band (levels 1-2).

Adds the missing full-text-search coverage plus the essay needed to satisfy
the EASY type quota. Full text search is the one Functions concept that had
no EASY family at all.
"""

from lib import essay, mcq
from sources import PG_TEXTSEARCH

QUESTIONS = [
    mcq(
        "fn-easy-tsvector",
        ["PG-FTS"],
        2,
        (
            "Which PostgreSQL type stores a document that has been parsed into "
            "searchable lexemes for full-text search?"
        ),
        [
            "tsvector",
            "tsquery",
            "text",
            "jsonb",
        ],
        0,
        (
            "to_tsvector parses a document into normalized lexemes and stores "
            "them, with positions, in a tsvector. A tsquery is the query side "
            "of the same search, built from search terms and operators. Plain "
            "text holds the original document, and jsonb is a structured "
            "document type, not a search representation."
        ),
        [PG_TEXTSEARCH],
    ),
    essay(
        "fn-easy-full-text-basics",
        ["PG-FTS"],
        2,
        (
            "Explain the roles of tsvector and tsquery and the @@ operator in "
            "PostgreSQL full-text search. Show how a document is prepared and "
            "queried, describe what normalization does to words such as "
            "'running', and explain why a LIKE '%term%' predicate is a poor "
            "substitute for full-text search."
        ),
        (
            "to_tsvector('english', body) parses body into lexemes, lowercases "
            "them, removes stop words and stems them, so 'running' becomes the "
            "lexeme 'run'. to_tsquery('english', 'run') builds a tsquery from "
            "search terms, and body_vector @@ query returns TRUE when the "
            "document matches. Because both sides pass through the same "
            "dictionary, a search for 'running' matches a document containing "
            "'runs'. A LIKE '%term%' predicate compares raw characters: it does "
            "not stem, so 'running' does not match 'run'; it cannot express "
            "phrase, AND/OR or negated term logic; and a leading wildcard "
            "prevents ordinary index use, whereas GIN/GiST indexes on tsvector "
            "support the @@ operator."
        ),
        (
            "The answer must define tsvector as the normalized document, "
            "tsquery as the normalized query, @@ as matching, and show stemming "
            "so that inflected forms match. It must state at least two concrete "
            "reasons why LIKE with a leading wildcard is worse."
        ),
        (
            "Confuses tsvector with tsquery, or claims full-text search compares "
            "raw substrings; no example of normalization.",
            "Correct roles but no stemming example, or only one reason against "
            "LIKE.",
            "Correct definitions and matching with a stemming example, but the "
            "index argument or the phrase/boolean logic argument is missing.",
            "Fully correct: tsvector holds normalized lexemes with positions, "
            "tsquery expresses the search, @@ tests a match, stemming makes "
            "'running' match 'run', and LIKE '%term%' fails on inflection, "
            "phrase/boolean logic and index support.",
        ),
        [PG_TEXTSEARCH],
    ),
]

"""Required-concept detection for SQL questions (FR-09).

When an administrator tags a question's concept as *required*
(``question_concept.is_required``), the learner's SQL must actually use that
technique. Concepts are mapped — by normalized name/code keywords — onto AST
features detected with sqlglot, so enforcement is structural rather than
keyword-regex based.

A concept we cannot map to a detectable feature is reported as *unverified*:
it is recorded in the grading evidence but does not change the score, so an
exotic concept tag never silently fails a learner.
"""

from typing import Iterable, Optional

import sqlglot
from sqlglot import exp

# Normalized concept-name fragment -> feature key. Order matters only for
# readability; the first fragment contained in the concept name wins.
_CONCEPT_KEYWORDS: list[tuple[str, str]] = [
    ("join", "join"),
    ("group by", "group_by"),
    ("aggregat", "aggregate"),
    ("grouping", "group_by"),
    ("having", "having"),
    ("subquer", "subquery"),
    ("sub-quer", "subquery"),
    ("nested quer", "subquery"),
    ("cte", "cte"),
    ("common table", "cte"),
    ("with clause", "cte"),
    ("window", "window"),
    ("set operation", "set_operation"),
    ("union", "set_operation"),
    ("intersect", "set_operation"),
    ("except", "set_operation"),
    ("distinct", "distinct"),
    ("duplicat", "distinct"),
    ("order", "order_by"),
    ("sort", "order_by"),
    ("limit", "limit"),
    ("case", "case"),
    ("where", "where"),
    ("filter", "where"),
    ("null", "null_handling"),
    ("select", "select"),
]


def concept_to_feature(concept_text: str) -> Optional[str]:
    """Map a concept name/code onto a detectable feature key (or None)."""
    text = concept_text.strip().lower()
    for fragment, feature in _CONCEPT_KEYWORDS:
        if fragment in text:
            return feature
    return None


def detect_features(sql_text: str) -> frozenset[str]:
    """Feature keys present in the statement. Empty set when unparseable —
    callers treat that as 'all required features missing' (the query will
    have already failed validation upstream anyway).
    """
    try:
        statements = [s for s in sqlglot.parse(sql_text) if s is not None]
    except sqlglot.errors.SqlglotError:
        return frozenset()
    if not statements:
        return frozenset()

    feats: set[str] = set()
    for stmt in statements:
        if stmt.find(exp.Select):
            feats.add("select")
        if stmt.find(exp.Join):
            feats.add("join")
        if stmt.find(exp.Group):
            feats.add("group_by")
        if stmt.find(exp.Having):
            feats.add("having")
        if (
            stmt.find(exp.Subquery)
            or stmt.find(exp.Exists)
            or any(
                node.find(exp.Select) is not None
                for node in stmt.find_all(exp.In)
            )
        ):
            feats.add("subquery")
        if stmt.find(exp.Union) or stmt.find(exp.Intersect) or stmt.find(
            exp.Except
        ):
            feats.add("set_operation")
        if stmt.find(exp.CTE):
            feats.add("cte")
        if stmt.find(exp.Window):
            feats.add("window")
        if stmt.find(exp.Distinct):
            feats.add("distinct")
        if stmt.find(exp.Order):
            feats.add("order_by")
        if stmt.find(exp.Limit):
            feats.add("limit")
        if stmt.find(exp.Case):
            feats.add("case")
        if stmt.find(exp.Where):
            feats.add("where")
        for agg in stmt.find_all(exp.AggFunc):
            feats.add("aggregate")
        # NULL handling: IS [NOT] NULL / COALESCE / NULLIF
        for node in stmt.find_all(exp.Anonymous):
            if (node.name or "").lower() in ("coalesce", "nullif"):
                feats.add("null_handling")
        if stmt.find(exp.Is):
            feats.add("null_handling")
    return frozenset(feats)


def check_required(
    sql_text: str, required_concepts: Iterable[str]
) -> tuple[list[str], list[str]]:
    """Evaluate required concept names against the statement.

    Returns ``(missing, unverified)``: feature names the required concepts
    demand but the SQL lacks, and concept names that cannot be mapped to any
    detectable feature.
    """
    features = detect_features(sql_text)
    missing: list[str] = []
    unverified: list[str] = []
    for concept in required_concepts:
        feature = concept_to_feature(concept)
        if feature is None:
            unverified.append(concept)
        elif feature not in features:
            missing.append(concept)
    return missing, unverified

"""Learner-content sanitization for external LLM calls (NFR-04 / privacy).

Before any learner text leaves DBCAS we strip identifiers: the learner's
known name/email tokens plus free-text patterns that look like student or
identity numbers. Regex-based and deterministic — no NLP dependency.

The sanitizer is *redaction*, not anonymization research: it exists so the
common cases (a learner writing "I, Nguyen Van A, student 20210045, think…")
never reach the provider.
"""

import re
from typing import Iterable

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Student/ID numbers: 4+ consecutive digits, or digit groups joined by
# dashes/spaces (e.g. 2021-0045, 12 34 567). Short numbers like "3" or "42"
# stay — they are content (points, years), not identifiers.
_LONG_DIGITS_RE = re.compile(r"\b\d{4,}\b")
_GROUPED_DIGITS_RE = re.compile(r"\b\d{2,}[-\s]\d{2,}(?:[-\s]\d{2,})*\b")
# Phone-ish: +84..., 0xx xxx xxxx etc.
_PHONE_RE = re.compile(r"(?<!\d)(?:\+\d{1,3}[\s-]?)?\(?\d{2,4}\)?[\s-]\d{3,4}[\s-]\d{3,4}(?!\d)")

NAME_PLACEHOLDER = "[name]"
ID_PLACEHOLDER = "[id]"


def sanitize_learner_text(
    text: str, *, identifiers: Iterable[str] = ()
) -> str:
    """Redact identifiers from learner text.

    ``identifiers`` carries known values (full name, email, student number)
    taken from the account/profile — each non-trivial token is replaced
    case-insensitively before generic pattern scrubbing runs.
    """
    out = text
    for ident in identifiers:
        if not ident:
            continue
        for token in {ident, *ident.split()}:
            token = token.strip()
            if len(token) >= 2:
                out = re.sub(
                    re.escape(token), NAME_PLACEHOLDER, out, flags=re.IGNORECASE
                )
    out = _EMAIL_RE.sub(ID_PLACEHOLDER, out)
    out = _PHONE_RE.sub(ID_PLACEHOLDER, out)
    out = _GROUPED_DIGITS_RE.sub(ID_PLACEHOLDER, out)
    out = _LONG_DIGITS_RE.sub(ID_PLACEHOLDER, out)
    return out

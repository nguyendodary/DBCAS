"""Boundary-aware redaction for outbound educational content.

Known profile identifiers and explicitly labelled IDs are removed, along with
common unlabelled phone numbers, national-ID-like digit sequences and obvious
``Name: ...`` person-name patterns. Ordinary numeric literals, years, SQL
identifiers and substrings of technical words stay.

This is a best-effort pattern filter, not a privacy guarantee: it cannot
guarantee the absence of personal names or other identifiers. Document
approval for grounded generation therefore requires an explicit administrator
confirmation that the source contains no personal data.
"""
import re
from typing import Iterable

_EMAIL_RE = re.compile(r"(?<![\w@])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w@])")
_PHONE_RE = re.compile(r"(?i)\b((?:call|phone(?:\s+number)?|telephone|mobile|tel)\s*[:=]?\s*)(?:\+\d{1,3}[ -]?)?\(?\d{2,4}\)?[ -]\d{3,4}[ -]\d{3,4}(?![\w])")
_LABELLED_ID_RE = re.compile(r"(?i)\b((?:student(?:\s+(?:id|number))?|account\s+id|learner\s+id|my\s+(?:id|record))\s*(?:is\s+|[:=#]\s*)?)(\d{4,}(?:[- ]\d{2,})*|\d{2,}(?:-\d{2,}){2,})\b")
# Unlabelled phone shapes (at least 9 digits incl. country/mobile prefix).
_BARE_PHONE_RE = re.compile(
    r"(?<![\w])(?:\+\d{1,3}[ -]?)?(?:\(\d{2,4}\)|\d{2,4})[ -]\d{3,4}[ -]\d{3,4}(?![\w])"
)
_MOBILE_RE = re.compile(r"(?<!\d)0\d{9}(?!\d)")
# 9-12 consecutive digits, optionally grouped by single separators (e.g. a
# national ID / CCCD / SSN). Shorter numerals used in course content stay.
_NATIONAL_ID_RE = re.compile(r"(?<![\w])(?:\d[ -.]?){8,11}\d(?![\w])")
_LABELLED_NAME_RE = re.compile(
    r"(?i)\b((?:full\s+name|name|họ(?:\s+và)?\s*tên)\s*[:=]\s*)"
    r"([A-ZÀ-Ỵ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỵ][a-zà-ỹ]+)*(?:\s+[A-ZÀ-Ỵ])?)"
)
NAME_PLACEHOLDER = "[name]"
ID_PLACEHOLDER = "[id]"
# Phone/ID-shaped digit strings inside SQL expressions are arithmetic or
# literals, not personal data. Keep the existing "SQL numbers survive" rule.
_SQL_BEFORE_RE = re.compile(
    r"(?i)(?:select|where|having|values|set|as|=|\+|\*|/|,|\()\s*$"
)
_SQL_AFTER_RE = re.compile(r"(?i)^\s*(?:\)|,|;|as\b|from\b|into\b|\+|\*|/|=)")


def _redact_identifier(match: re.Match) -> str:
    before = match.string[:match.start()]
    after = match.string[match.end():]
    if _SQL_BEFORE_RE.search(before) or _SQL_AFTER_RE.match(after):
        return match.group()
    return ID_PLACEHOLDER


def sanitize_learner_text(text: str, *, identifiers: Iterable[str] = ()) -> str:
    out = text
    tokens = set()
    for ident in identifiers:
        if isinstance(ident, str) and ident.strip():
            ident = ident.strip()
            tokens.add(ident)
            if "@" not in ident and not any(c.isdigit() for c in ident):
                tokens.update(t for t in ident.split() if len(t) >= 2)
    for token in sorted(tokens, key=lambda t: (-len(t), t)):
        if len(token) < 2:
            continue
        placeholder = ID_PLACEHOLDER if "@" in token or any(c.isdigit() for c in token) else NAME_PLACEHOLDER
        pattern = r"\[(?:name|id)\]|(?<!\w)" + re.escape(token) + r"(?!\w)"
        out = re.sub(pattern, lambda match: match.group() if match.group().lower() in (NAME_PLACEHOLDER, ID_PLACEHOLDER) else placeholder, out, flags=re.IGNORECASE)
    out = _EMAIL_RE.sub(ID_PLACEHOLDER, out)
    out = _LABELLED_NAME_RE.sub(lambda m: m.group(1) + NAME_PLACEHOLDER, out)
    out = _PHONE_RE.sub(lambda m: m.group(1) + ID_PLACEHOLDER, out)
    out = _BARE_PHONE_RE.sub(_redact_identifier, out)
    out = _MOBILE_RE.sub(_redact_identifier, out)
    out = _NATIONAL_ID_RE.sub(_redact_identifier, out)
    return _LABELLED_ID_RE.sub(lambda m: m.group(1) + ID_PLACEHOLDER, out)


def profile_identifiers(account) -> list[str]:
    values = [account.email, f"account id {account.account_id}", f"account_id {account.account_id}", f"learner id {account.account_id}"]
    profile = account.profile
    if profile:
        values.extend(getattr(profile, key, None) for key in ("full_name", "student_code", "phone_number"))
        if profile.date_of_birth:
            values.append(profile.date_of_birth.isoformat())
    return [v for v in values if isinstance(v, str) and v]

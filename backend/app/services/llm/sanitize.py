"""Boundary-aware redaction for outbound educational content.

Known profile identifiers and explicitly labelled IDs are removed. Ordinary
numeric literals, years, SQL identifiers and substrings of technical words stay.
"""
import re
from typing import Iterable

_EMAIL_RE = re.compile(r"(?<![\w@])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w@])")
_PHONE_RE = re.compile(r"(?i)\b((?:call|phone(?:\s+number)?|telephone|mobile|tel)\s*[:=]?\s*)(?:\+\d{1,3}[ -]?)?\(?\d{2,4}\)?[ -]\d{3,4}[ -]\d{3,4}(?![\w])")
_LABELLED_ID_RE = re.compile(r"(?i)\b((?:student(?:\s+(?:id|number))?|account\s+id|learner\s+id|my\s+(?:id|record))\s*(?:is\s+|[:=#]\s*)?)(\d{4,}(?:[- ]\d{2,})*|\d{2,}(?:-\d{2,}){2,})\b")
NAME_PLACEHOLDER = "[name]"
ID_PLACEHOLDER = "[id]"


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
    out = _PHONE_RE.sub(lambda m: m.group(1) + ID_PLACEHOLDER, out)
    return _LABELLED_ID_RE.sub(lambda m: m.group(1) + ID_PLACEHOLDER, out)


def profile_identifiers(account) -> list[str]:
    values = [account.email, f"account id {account.account_id}", f"account_id {account.account_id}", f"learner id {account.account_id}"]
    profile = account.profile
    if profile:
        values.extend(getattr(profile, key, None) for key in ("full_name", "student_code", "phone_number"))
        if profile.date_of_birth:
            values.append(profile.date_of_birth.isoformat())
    return [v for v in values if isinstance(v, str) and v]

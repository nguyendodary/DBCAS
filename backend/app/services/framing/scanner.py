"""PII and secret scanning for framing text.

The scanner never returns matched values: callers get a rule, a span and a
SHA-256 digest.  That keeps logs and test failures safe while still making a
finding actionable.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Iterable

# These patterns are deliberately scoped to text that is about to be inserted
# into a prompt (model framing), not to arbitrary learner evidence.  Evidence
# is already sanitized by ``evaluation_pipeline.sanitize_data``.
_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"(?<![\w@])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w@])"),
    "phone": re.compile(
        r"(?<![\w])(?:\+?84|0)(?:[ .-]?\d){8,10}(?![\w])"
    ),
    "phone-intl": re.compile(r"(?<![\w])\+\d{1,3}[\s.-]?(?:\d[\s.-]?){7,14}\d(?![\w])"),
    "labelled-id": re.compile(
        r"(?i)(?:\b(?:student|learner|account|user)\s+(?:id|number)\b|"
        r"\b(?:mã sinh viên|mssv|cccd|cmnd|số điện thoại|điện thoại)\b)"
        r"\s*[:#=]?\s*[A-Z0-9][A-Z0-9-]{3,}\b"
    ),
    "url": re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>\"']+"),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    "provider-key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "github-token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    "aws-key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private-key": re.compile(r"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----"),
    "client-secret": re.compile(r"(?i)\b(?:[a-z0-9]+_)*client_secret\s*[:=]\s*[\"']?([^\"'\s]+)"),
    "bearer": re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}"),
}

_SECRET_RULES = frozenset({"jwt", "provider-key", "github-token", "aws-key", "private-key", "client-secret", "bearer"})
_PII_RULES = frozenset({"email", "phone", "phone-intl", "labelled-id", "url"})


@dataclass(frozen=True)
class Finding:
    rule: str
    start: int
    end: int
    digest: str

    @property
    def is_secret(self) -> bool:
        return self.rule in _SECRET_RULES

    @property
    def is_pii(self) -> bool:
        return self.rule in _PII_RULES

    def __str__(self) -> str:
        return f"{self.rule}@{self.start}:{self.digest[:12]}"


def _finding(rule: str, match: re.Match[str]) -> Finding:
    value = match.group(0)
    return Finding(rule, match.start(), match.end(), hashlib.sha256(value.encode("utf-8")).hexdigest())


def scan_text(text: str, *, extra_terms: Iterable[str] = ()) -> list[Finding]:
    """Return deterministic findings; never include the matched value."""
    if not isinstance(text, str) or not text:
        return []
    found: list[Finding] = []
    for rule, pattern in _PATTERNS.items():
        found.extend(_finding(rule, match) for match in pattern.finditer(text))
    for term in sorted({term.strip() for term in extra_terms if isinstance(term, str) and len(term.strip()) >= 2}):
        pattern = re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)", re.IGNORECASE)
        found.extend(_finding("pii-term", match) for match in pattern.finditer(text))
    return sorted(found, key=lambda item: (item.start, item.end, item.rule))


def has_pii_or_secret(text: str, *, extra_terms: Iterable[str] = ()) -> bool:
    return bool(scan_text(text, extra_terms=extra_terms))


def rule_codes(findings: Iterable[Finding]) -> tuple[str, ...]:
    return tuple(sorted({finding.rule for finding in findings}))

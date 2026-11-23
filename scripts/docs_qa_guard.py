# -*- coding: utf-8 -*-
"""Refuse accidental writes under docs/qa/**.

The QA tree is protected by AGENTS.md.  Tooling that needs to emit previews,
reports or generated facts must write under ``_review/`` (gitignored) or a
caller-supplied path outside ``docs/qa``.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTECTED = (ROOT / "docs" / "qa").resolve()


def ensure_safe_output(path, *, label="output"):
    """Return a resolved path, or raise if it is inside docs/qa/**."""
    resolved = Path(path).resolve()
    if resolved == PROTECTED or PROTECTED in resolved.parents:
        raise ValueError(
            f"refusing to write {label} under docs/qa/** ({resolved}); "
            "choose _review/ or another non-protected path"
        )
    return resolved


def protected(path):
    resolved = Path(path).resolve()
    return resolved == PROTECTED or PROTECTED in resolved.parents

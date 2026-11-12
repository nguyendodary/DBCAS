"""Small dependency-free helpers shared by the framing modules."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

GENERATOR_VERSION = "framing-v1"


def canonical(value: Any) -> str:
    """Stable JSON used for hashes and for the verbatim data block."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def utf8_bytes(value: str) -> int:
    return len(value.encode("utf-8"))


def shorten(value: Any, limit: int) -> Any:
    """Mirror ``evaluation_service.shorten_text`` without importing it."""
    if isinstance(value, str):
        return value[:limit]
    if isinstance(value, list):
        return [shorten(item, limit) for item in value]
    if isinstance(value, dict):
        return {key: shorten(item, limit) for key, item in value.items()}
    return value

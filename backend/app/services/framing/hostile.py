"""Loader and structural checks for the committed hostile-answer corpus."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent / "data" / "hostile_cases.json"
LANGUAGES = frozenset({"vi", "en"})
MIN_CASES = 50


@dataclass(frozen=True)
class HostileCase:
    id: str
    language: str
    category: str
    answer: str


def load_hostile_cases(path: Path | None = None) -> tuple[HostileCase, ...]:
    path = Path(path or DEFAULT_PATH)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != "1.0":
        raise ValueError("hostile corpus version must be 1.0")
    rows = payload.get("cases")
    if not isinstance(rows, list):
        raise ValueError("hostile corpus cases must be a list")
    cases: list[HostileCase] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "language", "category", "answer"}:
            raise ValueError("hostile case has an invalid shape")
        case = HostileCase(
            id=str(row["id"]),
            language=str(row["language"]),
            category=str(row["category"]),
            answer=str(row["answer"]),
        )
        if not case.id or case.id in seen:
            raise ValueError("hostile case ids must be unique and non-empty")
        if case.language not in LANGUAGES:
            raise ValueError("hostile case language must be vi or en")
        if not case.category.strip() or not case.answer.strip():
            raise ValueError("hostile case category and answer must be non-empty")
        seen.add(case.id)
        cases.append(case)
    if len(cases) < MIN_CASES:
        raise ValueError(f"hostile corpus needs at least {MIN_CASES} cases")
    if {case.language for case in cases} != LANGUAGES:
        raise ValueError("hostile corpus must include both vi and en")
    return tuple(cases)


def corpus_stats(cases: tuple[HostileCase, ...]) -> dict[str, object]:
    return {
        "count": len(cases),
        "languages": sorted({case.language for case in cases}),
        "categories": sorted({case.category for case in cases}),
        "min_answer_chars": min(len(case.answer) for case in cases),
        "max_answer_chars": max(len(case.answer) for case in cases),
    }

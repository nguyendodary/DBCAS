"""Deterministic production-shaped synthetic sessions for framing training.

No database, no account rows and no learner records are read.  The only source
is the committed question-bank fixture.  Splits are by session, never by item.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
import random
from typing import Any, Iterable

from .scanner import rule_codes, scan_text
from .util import GENERATOR_VERSION, canonical, digest, shorten, sha256_file

DATASET_SCHEMA_VERSION = "framing-dataset-v1"
PROMPT_VERSION = "two-ai-v4"
DEFAULT_FIXTURE = Path(__file__).resolve().parents[4] / "backend" / "tests" / "fixtures" / "release_content_snapshot.json"
WEAK_THRESHOLD = 70.0
STRONG_THRESHOLD = 85.0
MAX_ITEMS = 80
MAX_HISTORY = 500
MAX_DATA_BYTES = 165_000


@dataclass(frozen=True)
class DatasetBundle:
    sessions: tuple[dict[str, Any], ...]
    dataset_hash: str
    counts: dict[str, int]
    fixture_hash: str
    seed: int


def _load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _index_fixture(pack: dict[str, Any]) -> dict[str, Any]:
    concepts = {row["concept_id"]: row for row in pack.get("concepts", [])}
    options = defaultdict(list)
    for row in pack.get("mcq_options", []):
        options[row["question_id"]].append(row)
    rubrics = defaultdict(list)
    for row in pack.get("rubrics", []):
        rubrics[row["question_id"]].append(row)
    question_concepts = defaultdict(list)
    for row in pack.get("question_concepts", []):
        question_concepts[row["question_id"]].append(row["concept_id"])
    clo_by_concept = defaultdict(set)
    for row in pack.get("clo_concepts", []):
        clo_by_concept[row["concept_id"]].add(row["clo_id"])
    return {
        "concepts": concepts,
        "options": options,
        "rubrics": rubrics,
        "question_concepts": question_concepts,
        "clo_by_concept": clo_by_concept,
    }


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)


def _clean_source(value: Any) -> bool:
    return not any(scan_text(text) for text in _strings(value))


def _label(level: int) -> str:
    return "Dễ" if level <= 2 else "Vừa" if level == 3 else "Khó"


def _answer_for(question: dict[str, Any], options: list[dict[str, Any]], index: int, long: bool) -> tuple[str, str | None]:
    kind = question["question_type"]
    if kind == "mcq":
        correct = next((row for row in options if row.get("is_correct")), options[0])
        wrong = next((row for row in options if not row.get("is_correct")), correct)
        chosen = wrong if index % 5 == 0 else correct
        return str(chosen.get("option_label") or chosen.get("option_text") or ""), None
    if kind == "sql":
        reference = str(question.get("reference_answer") or "SELECT * FROM students;")
        answer = reference
        if index % 4 == 0:
            answer = reference + "\n-- synthetic learner attempt: incomplete filter"
        if long:
            answer = answer + "\n-- " + ("kiểm tra kế hoạch thực thi và chi phí " * 60)
        return answer, reference
    reference = str(question.get("reference_answer") or "")
    concepts = question.get("_concept_names") or ["mô hình quan hệ"]
    criteria = [row.get("criteria") for row in question.get("_rubrics", []) if row.get("criteria")]
    sentences = [
        f"Khái niệm {concepts[index % len(concepts)]} được trình bày bằng định nghĩa và một ví dụ thiết kế.",
        "Lập luận nối khái niệm với ràng buộc dữ liệu, khóa và nhu cầu truy vấn thực tế.",
    ]
    if criteria:
        sentences.append(f"Theo rubric, câu trả lời cần nêu {criteria[index % len(criteria)]}.")
    answer = " ".join(sentences)
    if long:
        answer = answer + " " + " ".join(sentences * 20)
    return answer, reference


def _item(question: dict[str, Any], index: dict[str, Any], attempt_id: int, number: int, long: bool) -> dict[str, Any]:
    qid = question["question_id"]
    concept_ids = index["question_concepts"].get(qid, [])
    concepts = [index["concepts"][cid]["concept_name"] for cid in concept_ids if cid in index["concepts"]]
    topics = sorted({index["concepts"][cid]["subject_area"] for cid in concept_ids if cid in index["concepts"]}) or ["Chưa phân loại"]
    clo = sorted({f"CLO-{clo_id}" for cid in concept_ids for clo_id in index["clo_by_concept"].get(cid, set())})
    question["_concept_names"] = concepts or ["mô hình quan hệ"]
    question["_rubrics"] = index["rubrics"].get(qid, [])
    answer, reference = _answer_for(question, index["options"].get(qid, []), number, long)
    points = float(question.get("points") or 1)
    if question["question_type"] == "essay":
        score = None
    elif number % 3 == 0:
        score = "0.00"
    elif number % 4 == 0:
        score = f"{points / 2:.2f}"
    else:
        score = f"{points:.2f}"
    return {
        "attempt_id": attempt_id,
        "question_id": qid,
        "type": question["question_type"],
        "prompt": str(question.get("prompt") or "")[:1600],
        "answer": answer[:2400],
        "points": f"{points:.2f}",
        "score": score,
        "reference_answer": (reference or "")[:1600],
        "options": [
            {"id": row.get("option_id"), "text": row.get("option_text"), "correct": bool(row.get("is_correct"))}
            for row in index["options"].get(qid, [])
        ],
        "concepts": concepts,
        "clo": clo,
        "topics": topics,
        "difficulty": _label(int(question.get("difficulty_level") or 1)),
        "rubric": [
            {
                "level": row.get("level_name"),
                "min": str(row.get("min_score")),
                "max": str(row.get("max_score")),
                "criteria": row.get("criteria"),
            }
            for row in index["rubrics"].get(qid, [])
        ],
    }


def _aggregate(items: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    earned = sum(float(item["score"] or 0) for item in items)
    possible = sum(float(item["points"]) for item in items)
    percentage = round(earned / possible * 100, 2) if possible else 0.0
    metrics: dict[str, defaultdict[str, list[float]]] = {
        "clo": defaultdict(lambda: [0.0, 0.0]),
        "topic": defaultdict(lambda: [0.0, 0.0]),
        "difficulty": defaultdict(lambda: [0.0, 0.0]),
        "concept": defaultdict(lambda: [0.0, 0.0]),
    }
    for item in items:
        score = float(item["score"] or 0)
        for dimension, keys in (
            ("clo", item["clo"]),
            ("topic", item["topics"]),
            ("difficulty", [item["difficulty"]]),
            ("concept", item["concepts"]),
        ):
            for key in set(keys):
                metrics[dimension][key][0] += score
                metrics[dimension][key][1] += float(item["points"])
    dimensions = {
        dimension: [
            {
                "label": key,
                "earned": f"{value[0]:.2f}",
                "possible": f"{value[1]:.2f}",
                "percentage": round(value[0] / value[1] * 100, 2) if value[1] else 0.0,
            }
            for key, value in sorted(groups.items())
        ]
        for dimension, groups in metrics.items()
        if dimension != "concept"
    }
    concept_rows = [
        {"name": key, "percentage": round(value[0] / value[1] * 100, 2) if value[1] else 0.0}
        for key, value in sorted(metrics["concept"].items())
    ]
    return (
        {"earned": f"{earned:.2f}", "possible": f"{possible:.2f}", "percentage": percentage},
        dimensions,
        concept_rows,
    )


def _history(score: dict[str, Any], count: int, seed: int) -> list[dict[str, Any]]:
    rows = []
    base = float(score["percentage"])
    for ordinal in range(1, count + 1):
        delta = ((seed + ordinal * 13) % 21) - 10
        pct = max(0.0, min(100.0, base + delta))
        rows.append(
            {
                "session_id": 10_000 + ordinal,
                "ordinal": ordinal,
                "date": f"2026-{1 + (ordinal - 1) % 12:02d}-{1 + (ordinal * 3) % 28:02d}T00:00:00+00:00",
                "earned": f"{pct / 100 * float(score['possible']):.2f}",
                "possible": score["possible"],
                "percentage": round(pct, 2),
            }
        )
    return rows


def _brief(data: dict[str, Any], concept_rows: list[dict[str, Any]]) -> dict[str, Any]:
    weak = sorted((row for row in concept_rows if row["percentage"] < WEAK_THRESHOLD), key=lambda row: (row["percentage"], row["name"]))
    strong = sorted((row for row in concept_rows if row["percentage"] >= STRONG_THRESHOLD), key=lambda row: (-row["percentage"], row["name"]))
    history = data["history"]
    trend = None
    if len(history) >= 2:
        delta = float(history[-1]["percentage"]) - float(history[0]["percentage"])
        trend = "up" if delta > 2 else "down" if delta < -2 else "flat"
    counts = {kind: sum(1 for item in data["items"] if item["type"] == kind) for kind in ("mcq", "sql", "essay")}
    return {
        "mode": data["mode"],
        "attempt_count": data["attempt_count"],
        "score_percentage": data["score"]["percentage"],
        "weak_concepts": [{"name": row["name"], "percentage": row["percentage"]} for row in weak[:3]],
        "strong_concepts": [{"name": row["name"], "percentage": row["percentage"]} for row in strong[:3]],
        "essay_count": counts["essay"],
        "mcq_count": counts["mcq"],
        "sql_count": counts["sql"],
        "trend": trend,
        "details_truncated": data["details_truncated"],
    }


def _target(brief: dict[str, Any]) -> dict[str, Any]:
    weak = [row["name"] for row in brief["weak_concepts"]]
    return {
        "task_text": "Hãy tạo phần mô tả nhiệm vụ đánh giá dựa trên bằng chứng và rubric, bằng tiếng Việt.",
        "focus_text": "Tập trung vào các khái niệm được hệ thống nêu và chỉ rõ giới hạn khi dữ liệu chưa đầy đủ.",
        "focus_concepts": weak[:2],
        "format_text": None,
        "status": "draft",
        "reviewed_by": None,
    }


def _split_map(count: int, seed: int) -> dict[int, str]:
    order = list(range(count))
    random.Random(seed).shuffle(order)
    train = int(count * 0.7)
    validation = int(count * 0.15)
    mapping = {}
    for position, index in enumerate(order):
        mapping[index] = "train" if position < train else "validation" if position < train + validation else "test"
    return mapping


def _cap_data(data: dict[str, Any]) -> None:
    for limit in (800, 400, 200, 100, 50, 16):
        if len(canonical(data).encode("utf-8")) <= MAX_DATA_BYTES:
            return
        data["items"] = shorten(data["items"], limit)
        data["details_truncated"] = True
    while len(canonical(data).encode("utf-8")) > MAX_DATA_BYTES and data["items"]:
        data["items"].pop(0)
        data["details_truncated"] = True


def _build_session(index: int, rng: random.Random, pools: dict[str, list[dict[str, Any]]], bank: dict[str, Any], large_every: int) -> dict[str, Any]:
    large = bool(large_every and index % large_every == 0)
    item_count = rng.randint(40, MAX_ITEMS) if large else rng.randint(5, 20)
    essay_count = max(1, item_count // 6) if item_count >= 10 else (1 if item_count >= 4 else 0)
    sql_count = max(1, item_count // 5) if item_count >= 8 else (1 if item_count >= 5 else 0)
    mcq_count = item_count - essay_count - sql_count
    chosen = (
        [rng.choice(pools["mcq"]) for _ in range(max(0, mcq_count))]
        + [rng.choice(pools["sql"]) for _ in range(max(0, sql_count))]
        + [rng.choice(pools["essay"]) for _ in range(max(0, essay_count))]
    )
    rng.shuffle(chosen)
    items = [
        _item(question, bank, attempt_id=index * 1000 + number, number=number, long=large)
        for number, question in enumerate(chosen, start=1)
    ]
    while len(items) < 5:
        items.append(_item(rng.choice(pools["mcq"]), bank, attempt_id=index * 1000 + len(items) + 1, number=len(items) + 1, long=large))
    score, dimensions, concept_rows = _aggregate(items)
    overall = index % 4 == 0
    history_count = rng.randint(3, 8) if overall else 1
    if large:
        history_count = rng.choice([120, 300, MAX_HISTORY])
    history = _history(score, history_count, index)
    data = {
        "version": PROMPT_VERSION,
        "mode": "overall" if overall else "attempt",
        "attempt_count": len(history) if overall else 1,
        "score": score,
        "history": history,
        "history_hash": digest(history),
        "dimensions": dimensions,
        "items": items,
        "recurring_weaknesses": [
            {"concept": row["name"], "attempts": 2 + (len(row["name"]) % 2)}
            for row in sorted((row for row in concept_rows if row["percentage"] < WEAK_THRESHOLD), key=lambda row: row["percentage"])[:6]
        ] if overall else [],
        "evidence_hash": digest([items, score]),
        "details_truncated": False,
    }
    _cap_data(data)
    brief = _brief(data, concept_rows)
    target = _target(brief)
    session = {
        "session_id": f"synthetic-{index + 1:04d}",
        "split": "train",
        "learner_ref": f"synthetic-learner-{index + 1:04d}",
        "data": data,
        "brief": brief,
        "target": target,
        "source_question_ids": [item["question_id"] for item in data["items"]],
    }
    for text in _strings({key: value for key, value in session.items() if key != "split"}):
        findings = scan_text(text)
        if findings:
            raise ValueError(f"synthetic_pii:{','.join(rule_codes(findings))}")
    session["session_hash"] = digest({key: value for key, value in session.items() if key not in {"split", "session_hash"}})
    return session


def generate(count: int = 300, *, seed: int = 42, fixture: Path | None = None, large_every: int = 20) -> DatasetBundle:
    if count < 3:
        raise ValueError("count must be at least 3")
    fixture = Path(fixture or DEFAULT_FIXTURE)
    if not fixture.exists():
        raise FileNotFoundError(fixture)
    pack = _load_fixture(fixture)
    bank = _index_fixture(pack)
    pools = {"mcq": [], "sql": [], "essay": []}
    for question in pack.get("questions", []):
        if question.get("status") != "validated":
            continue
        kind = question.get("question_type")
        if kind not in pools:
            continue
        qid = question.get("question_id")
        if kind == "mcq" and not bank["options"].get(qid):
            continue
        if kind == "essay" and not bank["rubrics"].get(qid):
            continue
        if not _clean_source([
            question.get("prompt"), question.get("reference_answer"),
            bank["options"].get(qid), bank["rubrics"].get(qid),
        ]):
            continue
        pools[kind].append(question)
    if not all(pools.values()):
        raise ValueError("fixture does not provide all question types")
    rng = random.Random(seed)
    sessions = [_build_session(index, rng, pools, bank, large_every) for index in range(count)]
    splits = _split_map(count, seed)
    for index, session in enumerate(sessions):
        session["split"] = splits[index]
        session["session_hash"] = digest({key: value for key, value in session.items() if key not in {"split", "session_hash"}})
    sessions.sort(key=lambda session: session["session_id"])
    counts = {name: sum(1 for session in sessions if session["split"] == name) for name in ("train", "validation", "test")}
    dataset_hash = digest({
        "schema_version": DATASET_SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "fixture_hash": sha256_file(fixture),
        "seed": seed,
        "sessions": [session["session_hash"] for session in sessions],
    })
    return DatasetBundle(tuple(sessions), dataset_hash, counts, sha256_file(fixture), seed)


def write_dataset(bundle: DatasetBundle, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    lines = {session["session_id"]: canonical(session) for session in bundle.sessions}
    (output / "sessions.jsonl").write_text("\n".join(lines[key] for key in sorted(lines)) + "\n", encoding="utf-8")
    for split in ("train", "validation", "test"):
        rows = [canonical(session) for session in bundle.sessions if session["split"] == split]
        (output / f"{split}.jsonl").write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
    manifest = {
        "schema_version": DATASET_SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "dataset_hash": bundle.dataset_hash,
        "fixture_hash": bundle.fixture_hash,
        "seed": bundle.seed,
        "counts": bundle.counts,
        "total": len(bundle.sessions),
        "target_status": {"draft": sum(1 for session in bundle.sessions if session["target"]["status"] == "draft")},
        "pii_findings": 0,
    }
    (output / "manifest.json").write_text(canonical(manifest), encoding="utf-8")
    return manifest

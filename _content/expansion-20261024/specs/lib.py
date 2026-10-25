"""Compact constructors for expansion specs.

Every constructor returns the same dictionary shape the clone-only builder
consumes. Keeping the shape in one place removes the risk of a hand-written
field name diverging between batches.
"""

import hashlib
import re
from decimal import Decimal

LABELS = "ABCD"

# The new bank was authored with the correct option first, which would let a
# learner answer by position. Move it to a stable pseudo-random position per
# key; the same key always yields the same position, so rebuilds are
# reproducible and the staged clone can be reconciled exactly.
_LABEL_REFERENCE = re.compile(
    r"\b((?:[Oo]ptions?|[Aa]nswers?|[Cc]hoices?)\s+)([A-D])"
    r"((?:\s*(?:,|and|or)\s*[A-D])*)"
)


def _answer_position(key: str, option_count: int) -> int:
    digest = hashlib.sha256(("dbcas:" + key).encode("utf-8")).digest()
    return digest[1] % option_count


def _remap_label_references(text: str, permutation: list[int]) -> str:
    def mapped(letter: str) -> str:
        index = ord(letter) - ord("A")
        return LABELS[permutation[index]] if index < len(permutation) else letter

    def replace(match: re.Match) -> str:
        head, first, tail = match.group(1), match.group(2), match.group(3)
        tail = re.sub(r"[A-D]", lambda item: mapped(item.group(0)), tail)
        return head + mapped(first) + tail

    return _LABEL_REFERENCE.sub(replace, text or "")


def normalize_mcq_answers(item: dict) -> dict:
    """Move the correct option to a deterministic position and keep offsets."""
    if item.get("question_type") != "mcq":
        return item
    options = item.get("options") or []
    count = len(options)
    if count < 2:
        return item
    correct = [index for index, option in enumerate(options) if option.get("is_correct")]
    if len(correct) != 1:
        return item
    current = correct[0]
    target = _answer_position(item["key"], count)
    permutation = list(range(count))
    permutation[current], permutation[target] = permutation[target], permutation[current]
    # Keep the pre-rotation mapping so callers can rotate parallel content
    # (for example pending translations) by the same permutation.
    item["_rotation"] = list(permutation)
    if target == current:
        return item
    rotated = [None] * count
    for old_index, new_index in enumerate(permutation):
        option = dict(options[old_index])
        option["option_label"] = LABELS[new_index]
        rotated[new_index] = option
    item["options"] = rotated
    item["explanation"] = _remap_label_references(item.get("explanation", ""), permutation)
    draft = item.get("vi_draft")
    if draft and draft.get("option_texts"):
        source = draft["option_texts"]
        draft["option_texts"] = {
            LABELS[new_index]: source[LABELS[old_index]]
            for old_index, new_index in enumerate(permutation)
            if LABELS[old_index] in source
        }
    return item


def normalize_items(items: list[dict]) -> list[dict]:
    return [normalize_mcq_answers(item) for item in items]

_RUBRIC_NAMES = ("Incomplete", "Partial", "Mostly Complete", "Complete")
_RUBRIC_BANDS = (
    (Decimal("0.00"), Decimal("1.00")),
    (Decimal("1.01"), Decimal("2.50")),
    (Decimal("2.51"), Decimal("4.00")),
    (Decimal("4.01"), Decimal("5.00")),
)


def _base(key, question_type, concepts, diff, prompt, explanation, refs,
          points, tags):
    return {
        "key": key,
        "question_type": question_type,
        "original_locale": "en",
        "difficulty_level": diff,
        "points": points,
        "concept_codes": list(concepts),
        "required_concept_codes": [],
        "tags": list(tags) if tags else ["database-design"] + [c.lower() for c in concepts],
        "source_refs": list(refs),
        "prompt": prompt,
        "explanation": explanation,
    }


def mcq(key, concepts, diff, prompt, options, correct, explanation, refs, *,
        tags=(), points="1.00"):
    item = _base(key, "mcq", concepts, diff, prompt, explanation, refs, points, tags)
    item["options"] = [
        {"option_label": LABELS[index], "option_text": text, "is_correct": index == correct}
        for index, text in enumerate(options)
    ]
    return item


def sqlq(key, concepts, diff, prompt, reference, datasets, explanation, refs, *,
         ordered=True, check_columns=True, tags=(), points="5.00"):
    item = _base(key, "sql", concepts, diff, prompt, explanation, refs, points, tags)
    item["reference_answer"] = reference
    item["ordered"] = ordered
    item["check_columns"] = check_columns
    item["datasets"] = [
        {"dataset_name": name, "is_edge_case": edge, "setup_sql": setup}
        for name, edge, setup in datasets
    ]
    return item


def essay(key, concepts, diff, prompt, reference, explanation, criteria, refs, *,
          tags=(), points="5.00"):
    item = _base(key, "essay", concepts, diff, prompt, explanation, refs, points, tags)
    item["reference_answer"] = reference
    item["rubrics"] = [
        {
            "level_name": name,
            "min_score": f"{low:.2f}",
            "max_score": f"{high:.2f}",
            "criteria": criteria[index],
        }
        for index, (name, (low, high)) in enumerate(zip(_RUBRIC_NAMES, _RUBRIC_BANDS))
    ]
    return item

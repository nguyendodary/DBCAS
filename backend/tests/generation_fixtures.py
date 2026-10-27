"""Synthetic authoring context for strict, source-grounded provider fixtures."""
from copy import deepcopy

DESCRIPTION = "Interpret database query semantics and explain their effect on result rows."
KEYWORDS = ["SELECT", "projection", "filtering"]
OBJECTIVES = ["Distinguish result-column projection from filtering of result rows."]


def grounded(item, *, concept_id=1, locale="en", source="pg17-queries"):
    result = deepcopy(item)
    result.setdefault("concept_id", concept_id)
    result.setdefault("original_locale", locale)
    result.setdefault("source_ids", [source])
    result.setdefault("objective_indices", [0])
    result.setdefault("points", 1)
    result.setdefault("difficulty_level", 1)
    result.setdefault("explanation", "The answer follows the stated query operation and the supplied learning objective.")
    correct = next((o for o in result.get("options", []) if o.get("is_correct")), {})
    result.setdefault("reference_answer", correct.get("option_label", "See the supplied reference solution."))
    for dataset in result.get("datasets", []):
        dataset.get("expected_result", {}).setdefault("ordered", False)
        dataset.get("expected_result", {}).setdefault("check_columns", False)
    return result

"""Merge hand-authored Vietnamese drafts into the pending translation manifest.

Read-only with respect to the database. The output manifest is never imported
automatically and every entry stays ``pending_human_review``.

Usage (from this directory):
    PYTHONPATH=<backend> backend/.venv/Scripts/python.exe merge_translations.py
    ... merge_translations.py --write
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

EXPANSION = Path(__file__).resolve().parent
SPECS = EXPANSION / "specs"
TRANSLATIONS = EXPANSION / "translations"
PENDING = EXPANSION / "generated/translations_vi_pending.json"
MANIFEST = EXPANSION / "generated/staging_manifest.json"
EVIDENCE = EXPANSION / "evidence/translation_merge.json"

LEVELS = ("Incomplete", "Partial", "Mostly Complete", "Complete")
LABELS = ("A", "B", "C", "D")
IDENT = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
PLACEHOLDER = re.compile(r"\b(TODO|TBD|FIXME|lorem ipsum)\b", re.I)
VI_CHARS = re.compile(r"[ăâđêôơưàảãáạằẳẵắặầẩẫấậèẻẽéẹềểễếệìỉĩíịòỏõóọồổỗốộờởỡớợùủũúụừửữứựỳỷỹýỵ]", re.I)


def _load_items(path: Path) -> list[dict]:
    spec_dir = str(SPECS.resolve())
    if spec_dir not in sys.path:
        sys.path.insert(0, spec_dir)
    module_spec = importlib.util.spec_from_file_location(
        f"translation_spec_{path.stem}", path
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    items = getattr(module, "QUESTIONS", None)
    if not isinstance(items, list) or not items:
        raise SystemExit(f"Spec {path.name} does not expose QUESTIONS")
    return items


def _all_items() -> dict[str, dict]:
    if str(SPECS.resolve()) not in sys.path:
        sys.path.insert(0, str(SPECS.resolve()))
    from lib import normalize_items

    items: dict[str, dict] = {}
    for path in sorted(SPECS.glob("*.py")):
        if path.stem in {"lib", "gap_lib", "sources", "repairs"}:
            continue
        for item in normalize_items(_load_items(path)):
            items[item["key"]] = item
    return items


def _source_fingerprint(item: dict) -> str:
    """Same canonical fingerprint as app.services.question_localization."""
    source = {
        "question_type": item["question_type"],
        "prompt": item["prompt"],
        "explanation": item.get("explanation"),
        "options": [
            {"label": o["option_label"], "text": o["option_text"]}
            for o in sorted(item.get("options") or [], key=lambda o: o["option_label"])
        ],
        "rubrics": [
            {"level": r["level_name"], "criteria": r["criteria"]}
            for r in sorted(item.get("rubrics") or [], key=lambda r: r["level_name"])
        ],
    }
    original_locale = item.get("original_locale") or "en"
    if original_locale != "en":
        source["original_locale"] = original_locale
    raw = json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load_drafts() -> dict[str, dict]:
    drafts: dict[str, dict] = {}
    for path in sorted(TRANSLATIONS.glob("vi_*.py")):
        module_spec = importlib.util.spec_from_file_location(
            f"translation_drafts_{path.stem}", path
        )
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        batch = getattr(module, "DRAFTS", None)
        if not isinstance(batch, dict) or not batch:
            raise SystemExit(f"Translation module {path.name} has no DRAFTS dict")
        overlap = set(drafts) & set(batch)
        if overlap:
            raise SystemExit(f"Duplicate draft keys in {path.name}: {sorted(overlap)}")
        drafts.update(batch)
    return drafts


def _check_draft(item: dict, draft: dict) -> list[str]:
    problems: list[str] = []
    prompt = str(draft.get("prompt") or "").strip()
    explanation = str(draft.get("explanation") or "").strip()
    if not prompt:
        problems.append("empty prompt")
    if not explanation:
        problems.append("empty explanation")
    if PLACEHOLDER.search(prompt) or PLACEHOLDER.search(explanation):
        problems.append("placeholder text")
    if not VI_CHARS.search(prompt):
        problems.append("prompt contains no Vietnamese diacritics")
    if not VI_CHARS.search(explanation):
        problems.append("explanation contains no Vietnamese diacritics")

    english_prompt = item["prompt"]
    for token in sorted(set(IDENT.findall(english_prompt))):
        if token not in prompt:
            problems.append(f"identifier missing from prompt: {token}")
    for token in sorted(set(IDENT.findall(item.get("explanation", "")))):
        if token not in explanation:
            problems.append(f"identifier missing from explanation: {token}")

    if item["question_type"] == "mcq":
        options = draft.get("option_texts") or {}
        labels = {o["option_label"] for o in item["options"]}
        if set(options) != labels:
            problems.append(f"option labels {sorted(options)} != {sorted(labels)}")
        if not options:
            problems.append("no option translations")
        for label, text in options.items():
            if not str(text).strip():
                problems.append(f"empty option {label}")
        if set(draft.get("rubrics") or {}):
            problems.append("MCQ draft has rubrics")
        english_correct = [
            o["option_label"] for o in item["options"] if o.get("is_correct")
        ]
        if len(english_correct) != 1:
            problems.append("English MCQ does not have exactly one correct option")
        else:
            correct_text = str(options.get(english_correct[0]) or "").strip()
            if not correct_text:
                problems.append("correct option has no translation")
    elif item["question_type"] == "sql":
        if set(draft.get("option_texts") or {}):
            problems.append("SQL draft has option texts")
        if set(draft.get("rubrics") or {}):
            problems.append("SQL draft has rubrics")
    else:
        if set(draft.get("option_texts") or {}):
            problems.append("Essay draft has option texts")
        rubrics = draft.get("rubrics") or {}
        if set(rubrics) != set(LEVELS):
            problems.append(f"rubric levels {sorted(rubrics)} != {sorted(LEVELS)}")
        for level in LEVELS:
            band = rubrics.get(level) or {}
            if not str(band.get("label") or "").strip():
                problems.append(f"rubric {level} missing Vietnamese label")
            if not str(band.get("criteria") or "").strip():
                problems.append(f"rubric {level} missing criteria")
            elif not VI_CHARS.search(str(band["criteria"])):
                problems.append(f"rubric {level} criteria not Vietnamese")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-derive every pending entry from the current specs and drafts "
        "instead of keeping already-pending prose (still never imported).",
    )
    args = parser.parse_args()

    items = _all_items()
    with MANIFEST.open(encoding="utf-8") as fh:
        manifest = json.load(fh)
    with PENDING.open(encoding="utf-8") as fh:
        pending = json.load(fh)
    existing = pending["questions"]
    drafts = _load_drafts()

    unknown = sorted(set(drafts) - set(items))
    if unknown:
        raise SystemExit(f"Draft keys without a spec item: {unknown}")
    not_staged = sorted(set(drafts) - set(manifest["questions"]))
    if not_staged:
        raise SystemExit(f"Draft keys without a staged question: {not_staged}")

    report = {"checked": 0, "written": 0, "refreshed": 0, "problems": {}, "per_type": {}}
    merged: dict[str, dict] = {}
    for key, item in items.items():
        if key in existing and not args.refresh:
            merged[key] = existing[key]
            continue
        draft = drafts.get(key) or item.get("vi_draft")
        if draft is None:
            continue
        problems = _check_draft(item, draft)
        if problems:
            report["problems"][key] = problems
            continue
        entry = manifest["questions"][key]
        merged[key] = {
            "question_id": entry["question_id"],
            "source_sha256": hashlib.sha256(item["prompt"].encode("utf-8")).hexdigest(),
            "source_fingerprint": _source_fingerprint(item),
            "review_status": "pending_human_review",
            "prompt": draft["prompt"].strip(),
            "explanation": draft["explanation"].strip(),
            "option_texts": draft.get("option_texts") or {},
            "rubrics": draft.get("rubrics") or {},
        }
        if key in existing:
            report["refreshed"] += 1
        else:
            report["written"] += 1
        report["per_type"][item["question_type"]] = (
            report["per_type"].get(item["question_type"], 0) + 1
        )
    report["checked"] = len(drafts)

    if report["problems"]:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    missing = sorted(set(manifest["questions"]) - set(merged))
    report["total_drafts"] = len(merged)
    report["missing"] = len(missing)
    report["missing_keys"] = missing

    if args.write:
        ordered = {
            key: merged[key]
            for key in manifest["questions"]
            if key in merged
        }
        pending["questions"] = ordered
        pending["review_status"] = "pending_human_review"
        pending["imported"] = False
        pending["note"] = (
            "Machine-assisted drafts only. No human reviewer has approved these "
            "translations, so they are deliberately not imported."
        )
        with PENDING.open("w", encoding="utf-8") as fh:
            json.dump(pending, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        with EVIDENCE.open("w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

    print(json.dumps({k: v for k, v in report.items() if k != "missing_keys"},
                     ensure_ascii=False, indent=2))
    if missing:
        print("MISSING:", ", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Read-only content review of the staged expansion bank.

Produces evidence for editorial review; it never writes to any database. It
re-verifies SQL reference answers through the production sandbox runner, runs
structural checks, detects near-duplicate prompts and emits a readable dump of
every staged question so a subject reviewer can inspect the actual content.

Usage (from the backend directory):
    .venv/Scripts/python.exe ../_content/expansion-20261024/review_content.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from sqlalchemy import create_engine, text

BACKEND = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND))

from app.config import get_settings  # noqa: E402
from app.services.sandbox_runner import SandboxRunner  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CLONE_URL = "postgresql+psycopg://dbcas:clone_only_pw@127.0.0.1:5547/dbcas_clone"
EVIDENCE = ROOT / "_content/expansion-20261024/evidence"
MANIFEST = ROOT / "_content/expansion-20261024/generated/staging_manifest.json"
PENDING = ROOT / "_content/expansion-20261024/generated/translations_vi_pending.json"

PLACEHOLDERS = re.compile(r"\b(TODO|TBD|FIXME|lorem ipsum)\b", re.I)
NON_READ_ONLY = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|COPY|VACUUM)\b",
    re.I,
)
ALLOWED_SOURCE_HOSTS = {
    "www.postgresql.org",
    "postgresql.org",
    "open.umn.edu",
    "dblp.org",
    "doi.org",
    "www.doi.org",
    "dl.acm.org",
    "www.sciencedirect.com",
    "link.springer.com",
    "www.cs.ulm.edu",
    "web.archive.org",
    "www.cs.colorado.edu",
    "research.cs.wisc.edu",
}


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (value or "").lower())


def shingles(value: str, size: int = 4) -> set[tuple[str, ...]]:
    words = normalize(value).split()
    return {tuple(words[i:i + size]) for i in range(max(0, len(words) - size + 1))}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def fetch(conn):
    questions = conn.execute(text("""
        select q.question_id, q.question_type, q.difficulty_level, q.status,
               q.points, q.prompt, q.explanation, q.reference_answer,
               q.tags, q.source_refs, q.original_locale,
               coalesce(q.family_id, q.question_id) family_key
        from question q order by q.question_id
    """)).mappings().all()
    concepts = conn.execute(text("""
        select qc.question_id, c.concept_code, c.concept_name, c.subject_area,
               qc.is_required, qc.confirmed, qc.tag_source
        from question_concept qc join concept c using (concept_id)
    """)).mappings().all()
    options = conn.execute(text("""
        select question_id, option_label, option_text, is_correct
        from mcq_option order by question_id, option_label
    """)).mappings().all()
    rubrics = conn.execute(text("""
        select question_id, level_name, min_score, max_score, criteria
        from rubric order by question_id, min_score
    """)).mappings().all()
    datasets = conn.execute(text("""
        select question_id, dataset_name, setup_sql, expected_result, is_edge_case
        from sql_test_dataset order by question_id, dataset_name
    """)).mappings().all()
    translations = conn.execute(text("""
        select question_id, locale, source_hash, prompt, explanation,
               option_texts, rubrics
        from question_translation
    """)).mappings().all()
    return questions, concepts, options, rubrics, datasets, translations


def group(rows, key):
    out = defaultdict(list)
    for row in rows:
        out[row[key]].append(row)
    return out


def main() -> int:
    engine = create_engine(CLONE_URL)
    with engine.connect() as conn:
        questions, concepts, options, rubrics, datasets, translations = fetch(conn)
    concept_by_q = group(concepts, "question_id")
    option_by_q = group(options, "question_id")
    rubric_by_q = group(rubrics, "question_id")
    dataset_by_q = group(datasets, "question_id")
    translation_by_q = group(translations, "question_id")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    staged_ids = {entry["question_id"]: key
                  for key, entry in manifest["questions"].items()}
    pending = json.loads(PENDING.read_text(encoding="utf-8"))
    pending_qs = pending.get("questions", {})

    by_id = {q["question_id"]: q for q in questions}
    runner = SandboxRunner(get_settings())
    checks = {}
    findings = []

    def finding(qid, severity, code, message):
        findings.append({"question_id": qid, "severity": severity,
                         "code": code, "message": message})

    # ---- prompt similarity across the whole bank ----
    shingle_by_id = {q["question_id"]: shingles(q["prompt"]) for q in questions}
    prompt_by_id = {q["question_id"]: q["prompt"] for q in questions}
    duplicates = []
    for qid in sorted(staged_ids):
        for other_id, other_prompt in prompt_by_id.items():
            if other_id <= qid:
                continue
            score = jaccard(shingle_by_id[qid], shingle_by_id[other_id])
            if score >= 0.82 or normalize(prompt_by_id[qid]) == normalize(other_prompt):
                duplicates.append({
                    "question_id": qid,
                    "other_question_id": other_id,
                    "similarity": round(score, 3),
                    "other_staged": other_id in staged_ids,
                })
    if duplicates:
        for pair in duplicates:
            finding(pair["question_id"], "blocker", "duplicate_prompt",
                    f"Prompt near-duplicate of question {pair['other_question_id']} "
                    f"(Jaccard {pair['similarity']})")

    for qid, key in sorted(staged_ids.items()):
        q = by_id.get(qid)
        if q is None:
            finding(qid, "blocker", "missing", "Manifest question is absent from the clone")
            continue
        entry = {
            "key": key,
            "question_id": qid,
            "question_type": q["question_type"],
            "difficulty_level": q["difficulty_level"],
            "status": q["status"],
            "points": str(q["points"]),
            "prompt": q["prompt"],
            "explanation": q["explanation"],
            "reference_answer": q["reference_answer"],
            "tags": list(q["tags"] or []),
            "source_refs": q["source_refs"] or [],
            "original_locale": q["original_locale"],
            "concepts": [dict(row) for row in concept_by_q.get(qid, [])],
            "options": [dict(row) for row in option_by_q.get(qid, [])],
            "rubrics": [
                {**dict(row), "min_score": str(row["min_score"]),
                 "max_score": str(row["max_score"])}
                for row in rubric_by_q.get(qid, [])
            ],
            "datasets": [
                {"dataset_name": row["dataset_name"],
                 "is_edge_case": row["is_edge_case"],
                 "setup_sql": row["setup_sql"],
                 "expected_result": row["expected_result"]}
                for row in dataset_by_q.get(qid, [])
            ],
            "vi_translation": [dict(row) for row in translation_by_q.get(qid, [])
                                if row["locale"] == "vi"],
            "vi_draft": pending_qs.get(key),
            "findings": [],
        }
        local = entry["findings"]

        def add(severity, code, message):
            local.append({"severity": severity, "code": code, "message": message})
            finding(qid, severity, code, message)

        # structure
        if not q["prompt"] or not q["prompt"].strip():
            add("blocker", "empty_prompt", "Prompt is empty")
        if not q["explanation"] or not q["explanation"].strip():
            add("blocker", "empty_explanation", "Explanation is empty")
        if not q["source_refs"]:
            add("blocker", "no_source_refs", "No source references")
        if PLACEHOLDERS.search(q["prompt"] or "") or PLACEHOLDERS.search(q["explanation"] or ""):
            add("blocker", "placeholder_text", "Placeholder text found")
        if q["original_locale"] != "en":
            add("major", "original_locale", "Staged source content is not marked English")
        if not concept_by_q.get(qid):
            add("blocker", "no_concepts", "No concept link")
        for concept in concept_by_q.get(qid, []):
            if not concept["confirmed"]:
                add("blocker", "unconfirmed_concept", "Concept link is not confirmed")
        if not q["tags"]:
            add("major", "no_tags", "No tags")
        for ref in q["source_refs"] or []:
            url = str(ref.get("url") or "")
            title = str(ref.get("title") or "")
            if not url.startswith(("http://", "https://")) or not title:
                add("major", "bad_source_ref", f"Source reference incomplete: {ref}")
            else:
                host = re.sub(r"^https?://", "", url).split("/")[0].lower()
                if host not in ALLOWED_SOURCE_HOSTS:
                    add("minor", "unrecognized_source_host",
                        f"Source host not in verified allowlist: {host}")

        # MCQ
        opts = option_by_q.get(qid, [])
        if q["question_type"] == "mcq":
            correct = [o for o in opts if o["is_correct"]]
            if len(opts) != 4:
                add("major", "mcq_option_count", f"MCQ has {len(opts)} options, expected 4")
            if len(correct) != 1:
                add("blocker", "mcq_correct_count", f"MCQ has {len(correct)} correct options")
            labels = [o["option_label"] for o in opts]
            if len(set(labels)) != len(labels):
                add("blocker", "mcq_duplicate_labels", "Duplicate option labels")
            texts = [o["option_text"].strip().lower() for o in opts]
            if len(set(texts)) != len(texts):
                add("blocker", "mcq_duplicate_text", "Duplicate option text")
            if any(re.search(r"all of the above|none of the above", t["option_text"], re.I)
                   for t in opts):
                add("minor", "mcq_meta_option", "Option uses an all/none-of-the-above shortcut")
            if q["explanation"] and len(q["explanation"].strip()) < 40:
                add("minor", "mcq_explanation_short",
                    "Explanation is unusually short; reviewer should confirm")

        # SQL
        if q["question_type"] == "sql":
            sets = dataset_by_q.get(qid, [])
            if len(sets) < 2:
                add("blocker", "sql_dataset_count", f"SQL has {len(sets)} datasets")
            if not any(d["is_edge_case"] for d in sets):
                add("blocker", "sql_no_edge_case", "SQL has no edge-case dataset")
            reference = (q["reference_answer"] or "").strip()
            if not reference:
                add("blocker", "sql_no_reference", "SQL reference answer is empty")
            elif NON_READ_ONLY.search(reference):
                add("blocker", "sql_not_read_only", "Reference contains a non-read-only keyword")
            elif not re.match(r"^\s*(WITH|SELECT)\b", reference, re.I):
                add("blocker", "sql_not_select", "Reference is not a SELECT/WITH statement")

        # essay
        if q["question_type"] == "essay":
            bands = rubric_by_q.get(qid, [])
            if len(bands) != 4:
                add("major", "essay_rubric_count", f"Essay has {len(bands)} rubric bands")
            else:
                lowest = min(b["min_score"] for b in bands)
                highest = max(b["max_score"] for b in bands)
                if lowest != 0:
                    add("major", "essay_rubric_start", "Rubric does not start at 0")
                if highest != q["points"]:
                    add("major", "essay_rubric_end",
                        f"Rubric ends at {highest}, points are {q['points']}")
                ordered = sorted(bands, key=lambda b: b["min_score"])
                for left, right in zip(ordered, ordered[1:]):
                    if left["max_score"] >= right["min_score"]:
                        add("major", "essay_rubric_overlap",
                            "Rubric bands overlap or are not contiguous")
                if len({b["criteria"].strip() for b in bands}) != len(bands):
                    add("major", "essay_rubric_duplicate", "Rubric criteria are duplicated")
                for band in bands:
                    if len(band["criteria"].strip()) < 40:
                        add("minor", "essay_rubric_thin",
                            f"Rubric band {band['level_name']} criteria are very short")
            if not (q["reference_answer"] or "").strip():
                add("blocker", "essay_no_reference", "Essay reference answer is empty")

        # translation draft
        draft = pending_qs.get(key)
        if not draft:
            add("blocker", "vi_draft_missing", "No Vietnamese draft")
        else:
            prompt_hash = hashlib.sha256(q["prompt"].encode("utf-8")).hexdigest()
            if draft.get("question_id") not in (None, qid):
                add("major", "vi_draft_wrong_question",
                    f"Vietnamese draft points at question {draft.get('question_id')}")
            if draft.get("source_sha256") not in (None, prompt_hash):
                add("major", "vi_draft_stale", "Vietnamese draft source hash does not match")
            if draft.get("review_status") != "pending_human_review":
                add("major", "vi_draft_review_status",
                    "Vietnamese draft is not marked pending human review")
            if not str(draft.get("prompt") or "").strip():
                add("major", "vi_draft_empty_prompt", "Vietnamese prompt is empty")
            if not str(draft.get("explanation") or "").strip():
                add("major", "vi_draft_empty_explanation", "Vietnamese explanation is empty")
            if q["question_type"] == "mcq":
                option_map = draft.get("option_texts") or {}
                expected_labels = {o["option_label"] for o in opts}
                if set(option_map) != expected_labels:
                    add("major", "vi_draft_option_labels",
                        f"Vietnamese option labels {sorted(option_map)} != {sorted(expected_labels)}")
                if any(not str(v).strip() for v in option_map.values()):
                    add("major", "vi_draft_empty_option", "An option translation is empty")
            if q["question_type"] == "essay":
                vrubrics = draft.get("rubrics") or {}
                expected_levels = {b["level_name"] for b in rubric_by_q.get(qid, [])}
                if set(vrubrics) != expected_levels:
                    add("major", "vi_draft_rubric_levels",
                        f"Vietnamese rubric levels {sorted(vrubrics)} != {sorted(expected_levels)}")

        checks[qid] = entry

    # SQL verification using the production runner, matching build.py semantics.
    sql_ids = [qid for qid, e in checks.items() if e["question_type"] == "sql"]
    for qid in sql_ids:
        entry = checks[qid]
        reference = entry["reference_answer"]
        verification = []
        for dataset in entry["datasets"]:
            result = None
            error = None
            try:
                schema = runner.provision_dataset(dataset["setup_sql"])
                try:
                    outcome = runner.execute(reference, schema=schema)
                    if outcome.success:
                        from decimal import Decimal

                        def conv(value, kind):
                            if value is None:
                                return None
                            if kind == "number":
                                number = Decimal(str(value))
                                return int(number) if number == number.to_integral_value() else float(number)
                            if kind == "boolean":
                                return bool(value)
                            return str(value)

                        rows = [[conv(value, kind) for value, kind in zip(row, outcome.column_types)]
                                for row in outcome.rows]
                        result = {"columns": list(outcome.columns), "rows": rows}
                    else:
                        error = f"{outcome.error_type}: {outcome.error_message}"
                finally:
                    runner.drop_dataset(schema)
            except Exception as exc:  # noqa: BLE001
                error = str(exc)
            expected = dataset["expected_result"]
            matches = bool(result is not None
                           and result["columns"] == expected.get("columns")
                           and result["rows"] == expected.get("rows"))
            verification.append({
                "dataset_name": dataset["dataset_name"],
                "is_edge_case": dataset["is_edge_case"],
                "executed": result is not None,
                "error": error,
                "matches_expected": matches,
                "rows": len(result["rows"]) if result else None,
            })
            if not matches:
                finding(qid, "blocker", "sql_expected_mismatch",
                        f"Reference does not reproduce stored expectation on "
                        f"dataset {dataset['dataset_name']}: {error or 'row mismatch'}")
                entry["findings"].append({
                    "severity": "blocker", "code": "sql_expected_mismatch",
                    "message": f"Dataset {dataset['dataset_name']} mismatch: {error or 'rows differ'}",
                })
        entry["sql_verification"] = verification

    # summary
    by_severity = Counter(f["severity"] for f in findings)
    by_code = Counter(f["code"] for f in findings)
    type_counts = Counter(e["question_type"] for e in checks.values())
    key_dist = Counter(
        (e["question_type"], next((o["option_label"] for o in e["options"] if o["is_correct"]), None))
        for e in checks.values() if e["question_type"] == "mcq"
    )
    summary = {
        "staged_questions": len(checks),
        "types": dict(type_counts),
        "difficulty": dict(Counter(e["difficulty_level"] for e in checks.values())),
        "areas": dict(Counter(
            c["subject_area"] for e in checks.values() for c in e["concepts"]
        )),
        "mcq_correct_labels": {f"{k[0]}:{k[1]}": v for k, v in sorted(key_dist.items())},
        "findings_by_severity": dict(by_severity),
        "findings_by_code": dict(by_code),
        "duplicate_pairs": duplicates,
        "vi_drafts_present": sum(1 for e in checks.values() if e["vi_draft"]),
        "sql_verified": sum(1 for e in checks.values()
                            if e.get("sql_verification")
                            and all(v["matches_expected"] for v in e["sql_verification"])),
        "sql_total": len(sql_ids),
        "source_hosts": dict(Counter(
            re.sub(r"^https?://", "", str(r.get("url", ""))).split("/")[0]
            for e in checks.values() for r in e["source_refs"]
        )),
    }

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "content_review.json").write_text(
        json.dumps({"summary": summary, "questions": [checks[qid] for qid in sorted(checks)],
                    "findings": findings, "duplicates": duplicates},
                   indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    with (EVIDENCE / "content_review.txt").open("w", encoding="utf-8") as fh:
        for qid in sorted(checks):
            e = checks[qid]
            fh.write(f"\n{'='*100}\n")
            fh.write(f"Q{qid} | {e['key']} | {e['question_type'].upper()} | "
                     f"difficulty {e['difficulty_level']} | {e['points']} pts | "
                     f"{', '.join(c['concept_code'] + ' (' + c['subject_area'] + ')' for c in e['concepts'])}\n")
            fh.write(f"PROMPT: {e['prompt']}\n")
            if e["options"]:
                for option in e["options"]:
                    mark = " *CORRECT*" if option["is_correct"] else ""
                    fh.write(f"  {option['option_label']}. {option['option_text']}{mark}\n")
            if e["reference_answer"]:
                fh.write(f"REFERENCE: {e['reference_answer']}\n")
            for dataset in e["datasets"]:
                fh.write(f"DATASET [{dataset['dataset_name']}] edge={dataset['is_edge_case']}: "
                         f"{dataset['setup_sql']}\n")
                fh.write(f"EXPECTED: {json.dumps(dataset['expected_result'], ensure_ascii=False)}\n")
            if e["rubrics"]:
                for band in e["rubrics"]:
                    fh.write(f"RUBRIC {band['level_name']} {band['min_score']}-{band['max_score']}: "
                             f"{band['criteria']}\n")
            fh.write(f"EXPLANATION: {e['explanation']}\n")
            fh.write(f"TAGS: {', '.join(e['tags'])}\n")
            fh.write(f"SOURCES: {json.dumps(e['source_refs'], ensure_ascii=False)}\n")
            if e["vi_draft"]:
                fh.write(f"VI: {json.dumps(e['vi_draft'], ensure_ascii=False)}\n")
            if e["findings"]:
                for item in e["findings"]:
                    fh.write(f"FINDING [{item['severity']}] {item['code']}: {item['message']}\n")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 1 if by_severity.get("blocker") else 0


if __name__ == "__main__":
    raise SystemExit(main())

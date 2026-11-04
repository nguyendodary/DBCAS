"""Materialize expected results only from actual, repeated PostgreSQL runs."""
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.practice_corpus import RESULTS_PATH, raw_cases, result_key
from app.services.sandbox_runner import build_sandbox_runner
from app.services.sql_result import compare, parse_expected
from app.config import get_settings
from app.validate_bank import load_corpus


def build(runner, *, resume=False):
    started = time.monotonic()
    prior = json.loads(RESULTS_PATH.read_text(encoding="utf-8")) if resume and RESULTS_PATH.exists() else {}
    results, executions = dict(prior.get("results", {})), 0
    originals = [(q["key"], None, "CORE", 0, q["reference_answer"], q["datasets"])
                 for pack in load_corpus(include_templates=False)[0] for q in pack["questions"] if q["question_type"] == "sql"]
    for code, _, band, variant, query, datasets in [*raw_cases(), *originals]:
        for dataset in datasets:
            key = result_key(dataset["setup_sql"], query)
            if key in results:
                continue
            schema = runner.provision_dataset(dataset["setup_sql"])
            try:
                first = runner.execute(query, schema=schema)
                second = runner.execute(query, schema=schema)
                executions += 2
                if (not first.success or not second.success or not first.rows
                        or first.rows != second.rows or first.columns != second.columns):
                    raise ValueError(f"Invalid/nondeterministic {code}/{band}/{variant}: {first.error_type}")
                if dataset.get("expected_result") and compare(first.columns, first.rows, parse_expected(dataset["expected_result"]), first.column_types).status != "passed":
                    raise ValueError(f"Stored source result mismatch: {code}")
                results[key] = {"columns": first.columns, "rows": first.rows, "column_types": first.column_types}
            finally:
                runner.drop_dataset(schema)
        if variant == 6 and band == "HARD":
            print(f"Executed {code}: {executions} queries", flush=True)
    elapsed = round(time.monotonic()-started, 3)
    payload = {"engine": "PostgreSQL 17", "executions_per_fixture": 2,
               "actual_executions": prior.get("actual_executions", 0) + executions,
               "duration_seconds": round(prior.get("duration_seconds", 0) + elapsed, 3),
               "latest_run": {"executions": executions, "duration_seconds": elapsed}, "results": results}
    RESULTS_PATH.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "results"}))


if __name__ == "__main__":
    build(build_sandbox_runner(get_settings()), resume="--resume" in sys.argv)

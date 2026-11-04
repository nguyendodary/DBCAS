"""Reproduce the reviewed source corrections; changed SQL needs real execution."""
import argparse
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.corpus_review import apply_review, URL_REPAIRS
from app.services.question_validator import bank_problems


def expected_grid(result):
    def cell(value, index):
        if value is not None and result.column_types[index] == "number":
            number = Decimal(str(value))
            return int(number) if number == number.to_integral_value() else float(number)
        return value
    return {"columns": result.columns, "rows": [[cell(v, i) for i, v in enumerate(row)] for row in result.rows],
            "check_columns": True, "ordered": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    names = ("benchmark_pack.json", "sql_knowledge_pack.json", "postgres_knowledge_pack.json")
    packs = [json.loads((ROOT / "db" / name).read_text(encoding="utf-8")) for name in names]
    old = {q["key"]: deepcopy(q) for p in packs for q in p["questions"]}
    translations = json.loads((ROOT / "db/question_translations_vi.json").read_text(encoding="utf-8"))
    runner = None
    if args.execute:
        from app.config import get_settings
        from app.services.sandbox_runner import build_sandbox_runner
        runner = build_sandbox_runner(get_settings())
    executed = 0
    for pack in packs:
        apply_review(pack["questions"], translations["questions"])
        for q in pack["questions"]:
            previous = old[q["key"]]
            if q["question_type"] != "sql" or (q["reference_answer"] == previous["reference_answer"]
                    and q["datasets"] == previous["datasets"]):
                continue
            if runner is None:
                raise RuntimeError("Changed SQL must be executed; use --execute before --write")
            for dataset in q["datasets"]:
                schema = runner.provision_dataset(dataset["setup_sql"])
                try:
                    first = runner.execute(q["reference_answer"], schema=schema)
                    second = runner.execute(q["reference_answer"], schema=schema)
                    if not first.success or not second.success or expected_grid(first) != expected_grid(second):
                        raise RuntimeError(f"Reference execution failed or changed: {q['key']}")
                    if not dataset["is_edge_case"] and not first.rows:
                        raise RuntimeError(f"Empty primary result: {q['key']}")
                    dataset["expected_result"] = expected_grid(first)
                    executed += 2
                finally:
                    runner.drop_dataset(schema)
    # The aliases are assessed too; bind them without changing old snapshots.
    clo = next(c for c in packs[0]["clos"] if c["clo_code"] == "BENCH-SQL")
    clo["concept_codes"] = list(dict.fromkeys([*clo["concept_codes"], "SELECT", "JOIN", "IDX"]))
    errors = bank_problems(packs, translations["questions"])
    if errors:
        print(json.dumps(errors, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    if args.write:
        for name, pack in zip(names, packs):
            (ROOT / "db" / name).write_text(json.dumps(pack, ensure_ascii=False, indent=1 if name.startswith("postgres") else 2) + "\n", encoding="utf-8")
        (ROOT / "db/question_translations_vi.json").write_text(json.dumps(translations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        path = ROOT / "db/postgres_docs_sources.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        for source in manifest["sources"]:
            for before, after in URL_REPAIRS.items():
                source["url"] = source["url"].replace(before, after)
        manifest["documentation"]["retrieved"] = "2026-11-04"
        header = json.dumps({k: v for k, v in manifest.items() if k != "sources"}, ensure_ascii=False, indent=2).removesuffix("\n}")
        lines = ",\n".join("    " + json.dumps(source, ensure_ascii=False) for source in manifest["sources"])
        path.write_text(header + ',\n  "sources": [\n' + lines + "\n  ]\n}\n", encoding="utf-8")
    print(f"Reviewed {sum(len(p['questions']) for p in packs)} questions; {executed} changed-reference executions; 0 invalid")


if __name__ == "__main__":
    main()

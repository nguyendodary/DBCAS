"""Validate every source question, including Vietnamese and real SQL fixtures."""
import argparse
from collections import Counter
import json

from .config import ROOT_DIR, get_settings
from .services.question_validator import bank_problems
from .services.sandbox_runner import build_sandbox_runner


def load_corpus():
    packs = [json.loads((ROOT_DIR / "db" / name).read_text(encoding="utf-8")) for name in (
        "benchmark_pack.json", "sql_knowledge_pack.json", "postgres_knowledge_pack.json")]
    translations = json.loads((ROOT_DIR / "db/question_translations_vi.json").read_text(encoding="utf-8"))["questions"]
    return packs, translations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Execute every SQL fixture twice in the configured sandbox")
    args = parser.parse_args()
    packs, translations = load_corpus()
    runner = build_sandbox_runner(get_settings()) if args.execute else None
    failures = bank_problems(packs, translations, runner=runner)
    counts = Counter(q["question_type"] for pack in packs for q in pack["questions"])
    print(json.dumps({"questions": sum(counts.values()), "types": dict(counts), "invalid": len(failures),
                      "sql_execution": "every fixture twice" if runner else "not executed", "failures": failures}, ensure_ascii=False))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

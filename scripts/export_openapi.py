"""Export or verify the runtime API contract without database or provider calls."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main():
    from app.main import app

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    target = ROOT / "docs" / "openapi.json"
    rendered = json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if arguments.check:
        if not target.exists() or target.read_text(encoding="utf-8") != rendered:
            raise SystemExit("OpenAPI drift: run python scripts/export_openapi.py")
        print("OpenAPI matches the runtime contract")
    else:
        target.write_text(rendered, encoding="utf-8")
        print(f"Exported {len(app.openapi()['paths'])} API paths")


if __name__ == "__main__":
    main()

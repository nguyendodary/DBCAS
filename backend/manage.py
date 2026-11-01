"""Cross-platform backend development commands; always use the active interpreter."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["lint", "build", "test", "run", "init", "openapi"])
    args, extra = parser.parse_known_args()
    commands = {
        "lint": ["-m", "ruff", "check", "app", "tests/dn", "manage.py"],
        "build": ["-m", "compileall", "-q", "app"],
        "test": ["-m", "pytest", "-q"],
        "run": ["-m", "uvicorn", "app.main:app", "--reload"],
        "init": ["-m", "app.init_db"],
        "openapi": [str(ROOT.parent / "scripts/export_openapi.py")],
    }
    env = dict(os.environ, PYTHONUTF8="1")
    subprocess.run([sys.executable, *commands[args.command], *extra], cwd=ROOT, env=env, check=True)
    if args.command == "build":
        subprocess.run([sys.executable, "-c", "from app.main import app; assert app.openapi()['paths']"],
                       cwd=ROOT, env=env, check=True)


if __name__ == "__main__":
    main()

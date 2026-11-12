"""Check documented configuration names without loading any .env values."""
import ast
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def missing_names(root=ROOT):
    module = ast.parse((root / "backend/app/config.py").read_text(encoding="utf-8"))
    settings = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == "Settings")
    backend = {node.target.id.upper() for node in settings.body if isinstance(node, ast.AnnAssign)}
    frontend = set()
    for path in (root / "frontend").glob("vite*.js"):
        frontend.update(re.findall(r"process\.env\.(VITE_[A-Z0-9_]+)", path.read_text(encoding="utf-8")))
    for path in (root / "frontend/src").rglob("*.jsx"):
        frontend.update(re.findall(r"import\.meta\.env\.(VITE_[A-Z0-9_]+)", path.read_text(encoding="utf-8")))
    example = set(re.findall(r"^([A-Z][A-Z0-9_]*)=", (root / ".env.example").read_text(encoding="utf-8"), re.M))
    return sorted((backend | frontend) - example), len(backend), len(frontend)


if __name__ == "__main__":
    missing, backend_count, frontend_count = missing_names()
    if missing:
        print("Undocumented environment names: " + ", ".join(missing))
        raise SystemExit(1)
    print(f"Environment inventory: {backend_count} backend and {frontend_count} frontend keys documented; no values loaded")

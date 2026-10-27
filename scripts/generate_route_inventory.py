"""Generate the authoritative HTTP and page route inventories from source files.

Static analysis only: no FastAPI import, no settings, no database, no network.

    python scripts/generate_route_inventory.py --write    # regenerate JSON
    python scripts/generate_route_inventory.py --verify   # exit 1 on drift

Outputs
    docs/inventory/api-routes.json          backend/app/main.py + routers/*.py
    docs/inventory/frontend-routes.json     frontend/src/App.jsx

Each file records its own SHA-256 so a changed source cannot silently keep an
old inventory. The inventories describe routes only: response schemas, domain
rules and role semantics stay documented by hand in docs/api-conventions.md.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARDS = {"CurrentAccount", "LearnerOnly", "AdminOnly", "RoleManagerOnly"}
METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}
ROUTE_RE = re.compile(r"<Route\s+path=\"([^\"]+)\"\s+element=\{([^}]+)\}", re.S)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def literal(node) -> str:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else ""


def router_prefix(tree: ast.Module) -> str:
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Call):
            callee = statement.value.func
            name = getattr(callee, "id", "") or getattr(callee, "attr", "")
            if name == "APIRouter":
                for keyword in statement.value.keywords:
                    if keyword.arg == "prefix":
                        return literal(keyword.value)
    return ""


def decorators(function: ast.FunctionDef):
    for decorator in function.decorator_list:
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
            if getattr(decorator.func.value, "id", "") in {"router", "app"} \
                    and decorator.func.attr in METHODS:
                yield decorator.func.attr.upper(), literal(decorator.args[0]) if decorator.args else ""


def guards(function: ast.FunctionDef) -> list[str]:
    found = []
    for default in function.args.defaults:
        name = getattr(default, "id", "") or getattr(getattr(default, "func", None), "id", "")
        if name in GUARDS and name not in found:
            found.append(name)
    for argument in list(function.args.args) + list(function.args.kwonlyargs):
        annotation = argument.annotation
        text = ast.dump(annotation) if annotation is not None else ""
        for guard in GUARDS:
            if f"'{guard}'" in text and guard not in found:
                found.append(guard)
    return found


def response_model(decorator: ast.Call) -> str:
    for keyword in decorator.keywords:
        if keyword.arg == "response_model":
            return ast.unparse(keyword.value)
    return ""


def api_routes() -> dict:
    main = ROOT / "backend" / "app" / "main.py"
    tree = ast.parse(main.read_text(encoding="utf-8"))
    mounts = {}
    for statement in ast.walk(tree):
        if isinstance(statement, ast.Call) and getattr(statement.func, "attr", "") == "include_router":
            module = getattr(statement.args[0], "value", None) if statement.args else None
            prefix = next((literal(k.value) for k in statement.keywords if k.arg == "prefix"), "")
            if isinstance(module, ast.Name):
                mounts[module.id] = prefix
    routes = []
    for path in sorted((ROOT / "backend" / "app" / "routers").glob("*.py")):
        module = ast.parse(path.read_text(encoding="utf-8"))
        base = mounts.get(path.stem, "") + router_prefix(module)
        for function in module.body:
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for method, subpath in decorators(function):
                routes.append({
                    "method": method,
                    "path": base + subpath,
                    "router": path.name,
                    "handler": function.name,
                    "line": function.lineno,
                    "guards": guards(function),
                    "response_model": response_model(next(
                        d for d in function.decorator_list
                        if isinstance(d, ast.Call) and getattr(d.func, "attr", "") in METHODS)),
                })
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for method, subpath in decorators(statement):
                routes.append({
                    "method": method, "path": subpath, "router": "main.py",
                    "handler": statement.name, "line": statement.lineno,
                    "guards": guards(statement), "response_model": "",
                })
    routes.sort(key=lambda route: (route["path"], route["method"]))
    return {
        "generated_by": "scripts/generate_route_inventory.py",
        "note": "Static AST of backend/app/main.py and backend/app/routers/*.py. "
                "Authoritative for method and path only; roles, status codes and domain "
                "rules remain in docs/api-conventions.md.",
        "sources": {"backend/app/main.py": digest(main),
                    **{f"backend/app/routers/{path.name}": digest(path)
                       for path in sorted((ROOT / "backend" / "app" / "routers").glob("*.py"))}},
        "count": len(routes),
        "routes": routes,
    }


def frontend_routes() -> dict:
    app = ROOT / "frontend" / "src" / "App.jsx"
    text = app.read_text(encoding="utf-8")
    routes = []
    for path, element in ROUTE_RE.findall(text):
        line = text[:text.index(f'path="{path}"')].count("\n") + 1
        match = re.search(r"<(\w+)", element)
        gate = re.search(r"(authed|learner|admin)\(", element)
        routes.append({"path": path, "component": match.group(1) if match else element.strip(),
                       "access": {"authed": "authenticated", "learner": "Learner",
                                  "admin": "Administrator"}.get(gate.group(1), "public")
                                 if gate else "public",
                       "line": line})
    return {
        "generated_by": "scripts/generate_route_inventory.py",
        "note": "Static scan of the <Route> elements in frontend/src/App.jsx. Browser routes only; "
                "the built-in Help guide is a modal provided by HelpProvider, not a route.",
        "sources": {"frontend/src/App.jsx": digest(app)},
        "count": len(routes),
        "routes": routes,
    }


def targets() -> dict:
    return {"docs/inventory/api-routes.json": api_routes(),
            "docs/inventory/frontend-routes.json": frontend_routes()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="regenerate the inventory files")
    mode.add_argument("--verify", action="store_true", help="fail if a committed inventory is stale")
    arguments = parser.parse_args()
    drift = []
    for relative, payload in targets().items():
        destination = ROOT / relative
        rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        if arguments.write:
            destination.parent.mkdir(parents=True, exist_ok=True)
            previous = destination.read_text(encoding="utf-8") if destination.exists() else None
            destination.write_text(rendered, encoding="utf-8")
            print(f"{'unchanged ' if previous == rendered else 'wrote      '} {relative} "
                  f"({payload['count']} routes)")
            continue
        current = destination.read_text(encoding="utf-8") if destination.exists() else None
        if current is None:
            drift.append(f"{relative}: missing; run --write")
        elif current.rstrip("\r\n") != rendered.rstrip("\r\n"):
            stored = json.loads(current).get("sources", {})
            detail = []
            missing = sorted(set(payload["sources"]) - set(stored))
            extra = sorted(set(stored) - set(payload["sources"]))
            changed = [source for source, value in payload["sources"].items()
                       if source in stored and stored[source] != value]
            if missing:
                detail.append("sources no longer recorded: " + ", ".join(missing))
            if extra:
                detail.append("new sources: " + ", ".join(extra))
            if changed:
                detail.append("changed contents: " + ", ".join(changed))
            drift.append(f"{relative}: does not match its sources"
                         + (f" ({'; '.join(detail)})" if detail else "")
                         + "; run npm run inventory:write")
    if drift:
        print("\n".join(drift), file=sys.stderr)
        return 1
    if arguments.verify:
        print("OK: api-routes.json and frontend-routes.json match their sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""Collect architecture/context facts for the Word documents (single source).

    python scripts/doc_facts.py --write

Writes docs/qa/project-facts.json. Everything is read from the repository:
Compose files, OpenAPI generated from the real FastAPI app, frontend routes,
admin/learner navigation, Prompt Builder / Evaluator config and sandbox helper.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "qa" / "project-facts.json"


def yaml_services(text):
    block = text.split("\nnetworks:")[0]
    return re.findall(r"^  ([a-z][a-z0-9_-]*):\s*$", block, re.M)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    local = (ROOT / "docker-compose.local.yml").read_text(encoding="utf-8")
    qa = (ROOT / "docker-compose.qa.yml").read_text(encoding="utf-8")
    real = (ROOT / "docker-compose.real-qa.yml").read_text(encoding="utf-8")
    services = yaml_services(local)
    qa_services = yaml_services(qa)
    real_services = yaml_services(real)
    ports = [{"var": v, "default": int(d), "source": "docker-compose.local.yml"}
             for v, d in re.findall(r"127\.0\.0\.1:\$\{([A-Z_]+):-(\d+)\}", local)]
    qa_ports = [{"var": v, "default": int(d), "source": "docker-compose.qa.yml"}
                for v, d in re.findall(r"127\.0\.0\.1:\$\{([A-Z_]+):-(\d+)\}", qa)]
    volumes = re.findall(r"^\s*volumes:\s*\[([^\]]+)\]", local, re.M)
    volume_mounts = sorted(set(v.strip().strip("'\"") for group in volumes for v in group.split(",")))
    networks = sorted(set(re.findall(r"^\s*([a-z][a-z0-9_-]*):\s*(?:\{\}|\{internal: true\})", local, re.M)))
    sys.path.insert(0, str(ROOT / "backend"))
    from app.main import app
    spec = app.openapi()
    paths = sorted(spec["paths"])
    operations = sum(1 for item in spec["paths"].values()
                     for k in item if k in ("get", "post", "put", "patch", "delete"))
    app_jsx = (ROOT / "frontend" / "src" / "App.jsx").read_text(encoding="utf-8")
    routes = sorted(set(re.findall(r'path="([^"]+)"', app_jsx)))
    layout = (ROOT / "frontend" / "src" / "components" / "Layout.jsx").read_text(encoding="utf-8")
    admin_nav = re.findall(r"to: '(/admin[^']*)'", layout)
    learner_nav = re.findall(r"\{ to: '(/[a-z]+)'", layout)
    config = (ROOT / "backend" / "app" / "config.py").read_text(encoding="utf-8")
    oauth = sorted(set(re.findall(r"^\s*(google|github)_client_id", config, re.M)))
    facts = {
        "source": "docker-compose*.yml, app.openapi(), frontend/src, backend/app",
        "compose_services": services,
        "compose_services_all": sorted(set(services + qa_services + real_services)),
        "qa_only_services": sorted(set(qa_services) - set(services)),
        "opt_in_services": sorted(set(real_services) - set(services)),
        "ports": ports + qa_ports,
        "volume_mounts": volume_mounts,
        "networks": networks,
        "openapi_paths": paths,
        "openapi_path_count": len(paths),
        "openapi_operation_count": operations,
        "frontend_routes": routes,
        "admin_nav": admin_nav,
        "learner_nav": learner_nav,
        "oauth_providers": oauth,
        "external_llm_env": ["LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"],
        "smtp": {"host": "mailpit", "port": 1025, "ui_port_var": "LOCAL_MAIL_PORT"},
        "sandbox": {"image": "dbcas-sql-ephemeral:local", "network": "none",
                    "socket": "/var/run/docker.sock", "memory": "256m", "cpus": 1},
        "prompt_builder": {"setting": "PROMPT_BUILDER_MODEL_PATH", "timeout": "PROMPT_BUILDER_TIMEOUT_SECONDS",
                           "fallback": "template", "hash_field": "prompt_hash"},
        "evaluator": {"fallback": "rule_evaluation", "flag": "evaluator_fallback"},
        "result_flows": ["IMMEDIATE", "HUMAN_VERIFIED"],
        "question_types": ["mcq", "sql", "essay"],
        "question_count": {"min": 1, "max": 20, "default": 5},
        "difficulty_bands": ["EASY", "MEDIUM", "HARD"],
        "question_sources": ["bank", "ai"],
    }
    print(json.dumps({k: (len(v) if isinstance(v, list) else v)
                      for k, v in facts.items() if k in (
                          "compose_services", "compose_services_all", "ports", "openapi_path_count",
                          "openapi_operation_count", "frontend_routes", "admin_nav", "oauth_providers")},
                     indent=2))
    if args.write:
        OUT.write_text(json.dumps(facts, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()

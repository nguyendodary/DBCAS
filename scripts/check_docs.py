# -*- coding: utf-8 -*-
"""Fail-fast consistency gate between the Word-document sources and the repo.

    python scripts/check_docs.py

Compares the generated diagram manifest and SVGs against:
  * docs/qa/schema-introspection.json  (real PostgreSQL introspection)
  * docs/qa/project-facts.json        (Compose / OpenAPI / frontend routes)
  * the actual Compose, OpenAPI, frontend and schema files on disk
  * docs/diagrams/generated/system-context-model.json (nodes/flows + evidence)
The check FAILS on any differing count, name, missing evidence string or
missing SVG element. Wire into CI via `npm run docs:check`.
"""
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "docs" / "diagrams" / "generated"
DIAG = ROOT / "docs" / "diagrams"
SVG_NS = {"s": "http://www.w3.org/2000/svg"}
problems = []
checks = []


def digest(path):
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check(label, condition, detail=""):
    checks.append(label)
    if not condition:
        problems.append(f"{label}: {detail}")


def main():
    intro = load(ROOT / "docs/qa/schema-introspection.json")
    facts = load(ROOT / "docs/qa/project-facts.json")
    manifest = load(GEN / "manifest.json")
    model = load(GEN / "system-context-model.json")
    catalog = load(DIAG / "schema-catalog.json")
    fk_ledger = load(DIAG / "physical-schema-relationships.json")

    # 1. schema fingerprints: any schema/migration edit breaks the docs.
    check("schema.sql fingerprint", catalog["schema_sha256"] == digest(ROOT / "db/schema.sql"),
          "catalog stale; rerun introspect_schema.py / generate_schema_catalog.py")
    migs = sorted((ROOT / "db/migrations").glob("*.sql"))
    keys = {f"migration_{m.name[:3]}_sha256": digest(m) for m in migs}
    check("migration fingerprints", all(catalog.get(k) == v for k, v in keys.items()),
          "a migration changed without regenerating the catalog")

    # 2. introspection counts and names vs manifest
    n_tables = len(intro["tables"])
    n_cols = sum(len(t["columns"]) for t in intro["tables"])
    n_fks = len(intro["foreign_keys"])
    check("table count", manifest["tables"] == n_tables, f"{manifest['tables']} != {n_tables}")
    check("column count", manifest["columns"] == n_cols, f"{manifest['columns']} != {n_cols}")
    check("fk count", manifest["foreign_keys"] == n_fks, f"{manifest['foreign_keys']} != {n_fks}")
    check("index count", manifest["indexes"] == len(intro["indexes"]))
    check("migration count", manifest["migrations"] == len(migs))
    check("table names", manifest["table_names"] == [t["table"] for t in intro["tables"]])
    check("column names", manifest["column_names"] == sorted({c["name"] for t in intro["tables"] for c in t["columns"]}))
    check("fk names", manifest["fk_constraints"] == [f["constraint"] for f in intro["foreign_keys"]])
    check("catalog vs introspection tables",
          {t["table"] for t in catalog["tables"]} == {t["table"] for t in intro["tables"]})
    check("ledger vs introspection fks",
          {f["constraint"] for f in fk_ledger} == {f["constraint"] for f in intro["foreign_keys"]})

    # 3. project facts recomputed from the real files
    local = (ROOT / "docker-compose.local.yml").read_text(encoding="utf-8")
    qa = (ROOT / "docker-compose.qa.yml").read_text(encoding="utf-8")
    real = (ROOT / "docker-compose.real-qa.yml").read_text(encoding="utf-8")
    svc = re.findall(r"^  ([a-z][a-z0-9_-]*):\s*$", local.split("\nnetworks:")[0], re.M)
    svc_all = sorted(set(svc + re.findall(r"^  ([a-z][a-z0-9_-]*):\s*$", qa.split("\nnetworks:")[0], re.M)
                         + re.findall(r"^  ([a-z][a-z0-9_-]*):\s*$", real.split("\nnetworks:")[0], re.M)))
    check("compose services", facts["compose_services"] == svc,
          f"{facts['compose_services']} != {svc}")
    check("compose services (all)", facts["compose_services_all"] == svc_all)
    sys.path.insert(0, str(ROOT / "backend"))
    from app.main import app
    spec = app.openapi()
    paths = sorted(spec["paths"])
    ops = sum(1 for item in spec["paths"].values() for k in item
              if k in ("get", "post", "put", "patch", "delete"))
    check("openapi paths", facts["openapi_paths"] == paths, "OpenAPI changed; rerun doc_facts.py")
    check("openapi path count", facts["openapi_path_count"] == manifest["openapi_path_count"] == len(paths))
    check("openapi operation count", facts["openapi_operation_count"] == ops)
    app_jsx = (ROOT / "frontend/src/App.jsx").read_text(encoding="utf-8")
    routes = sorted(set(re.findall(r'path="([^"]+)"', app_jsx)))
    check("frontend routes", facts["frontend_routes"] == routes, "App.jsx changed; rerun doc_facts.py")
    layout = (ROOT / "frontend/src/components/Layout.jsx").read_text(encoding="utf-8")
    admin_nav = re.findall(r"to: '(/admin[^']*)'", layout)
    check("admin nav (5 items)", facts["admin_nav"] == admin_nav and len(admin_nav) == 5)

    # 4. context model: every node/flow has evidence and valid endpoints
    node_ids = {n["id"] for n in model["nodes"]}
    check("context nodes have evidence", all(n.get("evidence") for n in model["nodes"]))
    check("context flows have evidence", all(f.get("evidence") for f in model["flows"]))
    check("context flow endpoints", all(f["source"] in node_ids and f["destination"] in node_ids
                                       for f in model["flows"]))
    check("context flow ids unique", len({f["id"] for f in model["flows"]}) == len(model["flows"]))
    # every compose service appears as a context node (init/executor-image included)
    for s in svc:
        sid = s.replace("-", "_")
        check(f"service node {s}", sid in node_ids or s in node_ids,
              f"no context node for compose service {s}")
    check("manifest context nodes", manifest["context_nodes"] == [n["id"] for n in model["nodes"]])
    check("manifest context flows", manifest["context_flows"] == [f["id"] for f in model["flows"]])
    for provider in ("google", "github"):
        check(f"oauth node {provider}", provider in node_ids)

    # 5. generated SVGs contain exactly the required elements
    def svg_ids(name, prefix):
        text = (GEN / name).read_text(encoding="utf-8")
        return set(re.findall(r'id="(' + re.escape(prefix) + r'[^"]+)"', text))
    erd_tables = svg_ids("erd.svg", "table_")
    expected_tables = {f"table_{t['table']}" for t in intro["tables"]}
    check("ERD has every table", erd_tables == expected_tables,
          f"missing={sorted(expected_tables - erd_tables)} extra={sorted(erd_tables - expected_tables)}")
    erd_fks = svg_ids("erd.svg", "fk_")
    check("ERD lists every FK", erd_fks == {f"fk_{f['constraint']}" for f in intro["foreign_keys"]})
    ctx_nodes = svg_ids("system-context.svg", "node_")
    check("context SVG nodes", ctx_nodes == {f"node_{n['id']}" for n in model["nodes"]})
    ctx_flows = svg_ids("system-context.svg", "flow_")
    check("context SVG flows", ctx_flows == {f"flow_{f['id']}" for f in model["flows"]})
    trd = ET.parse(GEN / "table-relationships.svg").getroot()
    groups = trd.findall(".//s:g", SVG_NS)
    node_count = sum(g.get("class") == "node" for g in groups)
    edge_ids = {g.get("id") for g in groups if g.get("class") == "edge"}
    check("TRD node count", node_count == n_tables, f"{node_count} != {n_tables}")
    check("TRD edge count", len(edge_ids) == n_fks, f"{len(edge_ids)} != {n_fks}")
    check("TRD edge ids", edge_ids == {f["id"] for f in fk_ledger})

    # 6. legacy tables are explicitly marked, never hidden
    check("legacy tables declared", set(manifest["legacy_tables"]) ==
          {"assessment", "assessment_concept", "assessment_question", "assessment_blueprint"})
    check("legacy tables are real", set(manifest["legacy_tables"]) <= {t["table"] for t in intro["tables"]})
    erd_text = (GEN / "erd.svg").read_text(encoding="utf-8")
    for name in manifest["legacy_tables"]:
        block = re.search(r'<g id="table_' + re.escape(name) + r'">(.*?)</g>', erd_text, re.S)
        check(f"legacy marked in ERD {name}",
              bool(block) and "[legacy/retired]" in block.group(1))

    print(f"docs:check: {len(checks)} assertions, tables={n_tables}, columns={n_cols}, "
          f"fks={n_fks}, indexes={len(intro['indexes'])}, migrations={len(migs)}, "
          f"services={len(svc)}, services_all={len(svc_all)}, openapi_paths={len(paths)}, "
          f"operations={ops}, frontend_routes={len(routes)}, context_nodes={len(node_ids)}, "
          f"context_flows={len(model['flows'])}")
    if problems:
        for p in problems:
            print("FAIL:", p)
        sys.exit(1)
    print("PASS: Word-document sources match db/schema.sql, migrations, Compose, OpenAPI and frontend routes")


if __name__ == "__main__":
    main()

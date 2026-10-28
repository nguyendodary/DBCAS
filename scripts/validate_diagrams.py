"""Validate committed diagram models/render inventories without external services.

Run from any directory: python scripts/validate_diagrams.py
Rendering/visual inspection is a separate gate; counts are never quality targets.
"""
import hashlib
import json
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS = ROOT / "docs" / "diagrams"
NS = {"s": "http://www.w3.org/2000/svg"}


def read(name):
    model = json.loads((DIAGRAMS / name).read_text(encoding="utf-8"))
    def check_text(value):
        if isinstance(value, str):
            # Known broken punctuation encodings; a standalone Ã can be valid
            # Vietnamese (for example uppercase MÃ), so do not reject it.
            assert not any(marker in value for marker in ("\u00c3\u00a2", "\u00e2\u20ac", "\ufffd")), (name, "corrupted text", value)
        elif isinstance(value, dict):
            for item in value.values():
                check_text(item)
        elif isinstance(value, list):
            for item in value:
                check_text(item)
    check_text(model)
    return model


def rendered(name, relationships, nodes=None):
    root = ET.parse(DIAGRAMS / f"{name}.svg").getroot()
    groups = root.findall(".//s:g", NS)
    ids = {g.get("id") for g in groups}
    expected = {f["id"] for f in relationships if f.get("action") != "REMOVE"}
    assert len(expected) == sum(f.get("action") != "REMOVE" for f in relationships), name
    assert expected <= ids, (name, "missing relationships", expected - ids)
    if nodes is not None:
        assert sum(g.get("class") == "node" for g in groups) == nodes, name
        edges = {g.get("id"): g for g in groups if g.get("class") == "edge"}
        assert set(edges) == expected, (name, "unexpected or missing rendered edge")
        for flow in relationships:
            if flow.get("action") == "REMOVE":
                continue
            title = edges[flow["id"]].find("s:title", NS).text
            separator = "--" if name == "use-cases" else "->"
            endpoints = [endpoint.split(":")[0] for endpoint in title.split(separator)]
            assert endpoints == [flow["source"], flow["destination"]], (name, flow["id"], title)
    assert root.get("role") == "img", (name, "accessible image role missing")
    return len(expected)


def main():
    result = []
    context = read("system-context.json")
    originals = [f for f in context["relationships"] if int(f["id"][1:]) <= 21]
    assert len(originals) == 21
    assert all(f["action"] == "KEEP" and f["label"] == f["original_label"] for f in originals)
    assert not context["removed"]
    assert all(int(f["id"][1:]) > 21 and f.get("evidence") and f.get("reason")
               for f in context["modified"]), "Original context labels must remain intact; corrections need evidence"
    result.append(("system-context", 6, rendered("system-context", context["relationships"])))
    context_svg = ET.parse(DIAGRAMS / "system-context.svg").getroot()
    assert sum(r.get("class") == "node" for r in context_svg.findall("s:rect", NS)) == 6
    for flow in context["relationships"]:
        group = next(g for g in context_svg.findall("s:g", NS) if g.get("id") == flow["id"])
        assert group.find("s:text", NS).text == f'{flow["id"]} - {flow["label"]}', ("context label", flow["id"])
        coordinates = re.fullmatch(r"M(\d+) \d+ H(\d+)", group.find("s:path", NS).get("d"))
        rightward = int(coordinates[1]) < int(coordinates[2])
        expected_rightward = flow["source"] in ("learner", "admin") or (
            flow["source"] == "dbcas" and flow["destination"] in ("llm", "google", "github"))
        assert rightward == expected_rightward, ("context direction", flow["id"])

    for name in ("assessment-lifecycle", "use-cases", "containers", "deployment",
                 "components", "modules", "conceptual-core", "logical-architecture"):
        model = read(f"{name}.json")
        nodes = model.get("final_nodes") or len(model["nodes"])
        flows = model["relationships"]
        assert all(f.get("reason") or f.get("justification") for f in flows if f["action"] == "REMOVE")
        result.append((name, nodes, rendered(name, flows, nodes)))

    catalog = read("schema-catalog.json")
    assert catalog["schema_sha256"] == hashlib.sha256((ROOT / "db/schema.sql").read_bytes()).hexdigest()
    migrations = sorted((ROOT / "db/migrations").glob("*.sql"))
    assert len(migrations) == 15, [m.name for m in migrations]
    for migration in migrations:
        key = f"migration_{migration.name[:3]}_sha256"
        assert catalog[key] == hashlib.sha256(migration.read_bytes()).hexdigest(), migration.name
    fks = read("physical-schema-relationships.json")
    declared = {(t["table"], c["name"], c["definition"]) for t in catalog["tables"]
                for c in t["constraints"] if c["type"] == "f"}
    assert declared == {(f["source"], f["constraint"], f["definition"]) for f in fks}
    assert len(catalog["tables"]) == 36 and len(fks) == 51
    assert {"assessment_blueprint", "adaptive_event"} <= {t["table"] for t in catalog["tables"]}
    stored = {(table["table"], column["name"]) for table in catalog["tables"] for column in table["columns"]}
    assert len({f["id"] for f in fks}) == len(fks), "foreign key ids must be unique and never reused"
    for flow in fks:
        assert len(flow["columns"]) == len(flow["reference_columns"]), (flow["id"], "column count")
        assert flow["parent_per_child"] in {"1", "0..1"} and flow["children_per_parent"] in {"0..N", "0..1"}, flow["id"]
        for table, column in zip([flow["source"]] * len(flow["columns"]), flow["columns"]):
            assert (table, column) in stored, (flow["id"], "invented source column", table, column)
        for table, column in zip([flow["destination"]] * len(flow["reference_columns"]), flow["reference_columns"]):
            assert (table, column) in stored, (flow["id"], "invented target column", table, column)
    sys.path.insert(0, str(ROOT / "scripts"))
    import generate_schema_catalog
    expected_dot = generate_schema_catalog.render_dot(catalog, fks, generate_schema_catalog.migration_label())
    assert (DIAGRAMS / "physical-schema.dot").read_text(encoding="utf-8") == expected_dot, \
        "physical-schema.dot is not the current rendering of schema-catalog.json + foreign key ledger"
    result.append(("physical-schema", len(catalog["tables"]), rendered("physical-schema", fks, len(catalog["tables"]))))
    for name, nodes, edges in result:
        print(f"{name}: {nodes} nodes, {edges} relationships verified")
    print(f"PASS: {len(result)} diagram model/render inventories; "
          f"{len(catalog['tables'])} tables, {len(fks)} foreign keys, schema.sql and 15 migration fingerprints match")


if __name__ == "__main__":
    main()

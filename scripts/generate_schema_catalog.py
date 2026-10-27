"""Regenerate the schema-derived diagram artifacts from a real PostgreSQL catalog.

    python scripts/generate_schema_catalog.py --load "<libpq connection info>"           # preview
    python scripts/generate_schema_catalog.py --load "<libpq connection info>" --write   # refresh
    python scripts/generate_schema_catalog.py --verify                                   # dot vs catalog
    python scripts/generate_schema_catalog.py --check-schema                             # catalog vs schema.sql

`--load` applies db/schema.sql to an empty target first, so the artifacts always describe
the fresh application schema. The target MUST be disposable: the run aborts when any
application row or pre-existing table is found, so it can never rewrite the persistent
development database.

schema-catalog.json and physical-schema-relationships.json are generated evidence; every
FK id already in use is preserved and new constraints are appended (FK46, FK47, ...).
physical-schema.dot is rendered from those two files, so updating the ERD means changing
the schema and re-running this command instead of redrawing a picture.

Exit codes: 0 ok, 1 drift or failure, 3 --check-schema found the catalog stale.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS = ROOT / "docs" / "diagrams"
CATALOG = DIAGRAMS / "schema-catalog.json"
LEDGER = DIAGRAMS / "physical-schema-relationships.json"
DOT = DIAGRAMS / "physical-schema.dot"
GUARD_TABLES = ("account", "question", "assessment", "assessment_session")

TABLES_SQL = """
select c.relname
from pg_class c join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relkind = 'r' and c.relpersistence = 'p'
order by c.relname collate "C"
"""

COLUMNS_SQL = """
select a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod) as type, a.attnotnull
from pg_attribute a
join pg_class c on c.oid = a.attrelid
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relname = %s and a.attnum > 0 and not a.attisdropped
order by a.attnum
"""

CONSTRAINTS_SQL = """
select con.conname, con.contype, pg_get_constraintdef(con.oid) as definition
from pg_constraint con
join pg_class c on c.oid = con.conrelid
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relname = %s
order by con.conname collate "C"
"""

FOREIGN_KEYS_SQL = """
select con.conname,
       rel.relname,
       ref.relname,
       (select array_agg(att.attname order by u.ord)
          from unnest(con.conkey) with ordinality u(attnum, ord)
          join pg_attribute att on att.attrelid = con.conrelid and att.attnum = u.attnum),
       (select array_agg(att.attname order by u.ord)
          from unnest(con.confkey) with ordinality u(attnum, ord)
          join pg_attribute att on att.attrelid = con.confrelid and att.attnum = u.attnum),
       exists (select 1 from unnest(con.conkey) with ordinality u(attnum, ord)
                 join pg_attribute att on att.attrelid = con.conrelid and att.attnum = u.attnum
                where not att.attnotnull),
       exists (select 1 from pg_constraint uq
                where uq.conrelid = con.conrelid and uq.contype in ('p', 'u')
                  and uq.conkey::smallint[] <@ con.conkey::smallint[]),
       pg_get_constraintdef(con.oid)
from pg_constraint con
join pg_class rel on rel.oid = con.conrelid
join pg_class ref on ref.oid = con.confrelid
join pg_namespace n on n.oid = rel.relnamespace
where con.contype = 'f' and n.nspname = 'public'
order by con.conname collate "C"
"""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connect(info: str):
    import psycopg
    return psycopg.connect(info, autocommit=True)


def assert_disposable(connection) -> None:
    """Refuse anything that looks like the persistent development database."""
    names = {row[0] for row in connection.execute(
        "select tablename from pg_tables where schemaname = 'public'").fetchall()}
    for table in sorted(set(GUARD_TABLES) & names):
        count = connection.execute(f'select count(*) from public."{table}"').fetchone()[0]
        if count:
            sys.exit(f"refusing to run: {table} holds {count} row(s). Use a disposable database "
                     "created from db/schema.sql, never the persistent development database.")


def load_schema(connection, schema: Path) -> None:
    if connection.execute("select tablename from pg_tables where schemaname='public'").fetchall():
        sys.exit("refusing --load: the target database already holds tables")
    connection.execute(schema.read_text(encoding="utf-8"))


def collect(connection):
    version = f"PostgreSQL {connection.execute('show server_version').fetchone()[0]}"
    tables = []
    for (name,) in connection.execute(TABLES_SQL).fetchall():
        columns = [{"name": column, "type": type_name, "nullable": not not_null}
                   for column, type_name, not_null in connection.execute(COLUMNS_SQL, (name,)).fetchall()]
        constraints = [{"name": cname, "type": ctype, "definition": definition}
                       for cname, ctype, definition in connection.execute(CONSTRAINTS_SQL, (name,)).fetchall()]
        tables.append({"table": name, "columns": columns, "constraints": constraints})
    foreign_keys = []
    for (conname, source, target, columns, referenced, any_nullable, child_unique, definition) in \
            connection.execute(FOREIGN_KEYS_SQL).fetchall():
        foreign_keys.append({
            "source": source,
            "columns": columns,
            "destination": target,
            "reference_columns": referenced,
            "parent_per_child": "0..1" if any_nullable else "1",
            "children_per_parent": "0..1" if child_unique else "0..N",
            "constraint": conname,
            "definition": definition,
        })
    return tables, foreign_keys, version


def merge_ids(existing: list[dict], measured: list[dict]) -> list[dict]:
    """Keep committed FK ids, preserve their order, append constraints that are new."""
    ledger_fields = ("id", "source", "columns", "destination", "reference_columns",
                     "parent_per_child", "children_per_parent", "constraint", "definition")
    used = {item["constraint"]: item["id"] for item in existing}
    highest = max([int(re.fullmatch(r"FK(\d+)", item["id"]).group(1)) for item in existing], default=0)
    merged = [{**match, "id": used[item["constraint"]]}
              for item in existing
              if (match := next((f for f in measured if f["constraint"] == item["constraint"]), None))]
    placed = {item["constraint"] for item in merged}
    counter = highest
    for item in measured:
        if item["constraint"] in placed:
            continue
        counter += 1
        merged.append({**item, "id": f"FK{counter:02d}"})
    if len(merged) != len(measured):
        sys.exit(f"internal error: {len(measured) - len(merged)} foreign key(s) were not placed")
    # Key order is the committed order, so the reviewed diff only shows real schema changes.
    return [{field: item[field] for field in ledger_fields} for item in merged]


def _columns(definition: str, prefix: str) -> list[str]:
    inner = definition[len(prefix):].strip().removeprefix("(").removesuffix(")")
    return [part.strip() for part in inner.split(",") if part.strip()]


def annotations(table: dict) -> dict[str, str]:
    """PK/FK/nullability markers taken only from constraints that really exist."""
    marks: dict[str, set[str]] = {column["name"]: set() for column in table["columns"]}
    for constraint in table["constraints"]:
        kind, definition = constraint["type"], constraint["definition"]
        if kind == "p":
            columns = _columns(definition, "PRIMARY KEY")
        elif kind == "f":
            columns = _columns(definition.split("REFERENCES")[0], "FOREIGN KEY")
        elif kind == "n":
            columns = [definition.removeprefix("NOT NULL").strip()]
        else:
            continue
        for column in columns:
            marks.setdefault(column, set()).add(kind)
    return {
        column["name"]: " ".join(part for part in (
            "PK" if "p" in marks[column["name"]] else "",
            "FK" if "f" in marks[column["name"]] else "",
            "NULL" if column["nullable"] else "NOT NULL",
        ) if part)
        for column in table["columns"]
    }


def render_dot(catalog: dict, relationships: list[dict], header: str) -> str:
    """Render the physical ERD exactly as the committed model was drawn."""
    lines = [
        "digraph schema {",
        'graph [rankdir=LR,bgcolor="white",pad="0.5",nodesep="0.5",ranksep="1.2",fontname="Arial",fontsize=22]; '
        'node [shape=box,style="rounded,filled",fillcolor="#EFF5FB",color="#1F3864",fontname="Arial",fontsize=13,margin="0.16"]; '
        'edge [color="#2E75B6",fontname="Arial",fontsize=11];',
        f'graph [label="{header}\\n{len(catalog["tables"])} real tables; every declared foreign key; '
        'full CHECK/UNIQUE definitions in schema-catalog.json",labelloc=t];',
    ]
    by_table = {table["table"]: table for table in catalog["tables"]}
    outgoing: dict[str, list[dict]] = {}
    for edge in relationships:
        outgoing.setdefault(edge["source"], []).append(edge)
    for name in sorted(by_table):
        table = by_table[name]
        marks = annotations(table)
        rows = ['<TR><TD COLSPAN="3" BGCOLOR="#DCEAF7"><B>' + name + "</B></TD></TR>"]
        rows += [f'<TR><TD PORT="{column["name"]}" ALIGN="LEFT">{column["name"]}</TD>'
                 f'<TD ALIGN="LEFT">{column["type"]}</TD><TD>{marks[column["name"]]}</TD></TR>'
                 for column in table["columns"]]
        lines.append(f'"{name}" [shape=plain,label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" '
                     f'CELLPADDING="5">{"".join(rows)}</TABLE>>];')
        for edge in sorted(outgoing.get(name, []), key=lambda item: int(re.fullmatch(r"FK(\d+)", item["id"]).group(1))):
            action = re.search(r"\bON (?:DELETE|UPDATE)\b.*$", edge["definition"])
            label = f'{edge["id"]} {", ".join(edge["columns"])}' + (f' {action.group(0)}' if action else "")
            lines.append(f'"{edge["source"]}":"{edge["columns"][0]}" -> '
                         f'"{edge["destination"]}":"{edge["reference_columns"][0]}" '
                         f'[id="{edge["id"]}",label="{label}",'
                         f'taillabel="{edge["children_per_parent"]}",headlabel="{edge["parent_per_child"]}",'
                         f'tooltip="{edge["constraint"]}"];')
    lines.append("}")
    # No trailing newline: the committed model has none, and a byte-exact replay is the
    # acceptance test that this generator really reproduces the authored diagram.
    return "\n".join(lines)


def committed_header() -> str:
    """Reuse the committed label until the schema really moves again."""
    match = re.search(r'label="([^\\]*)\\n', DOT.read_text(encoding="utf-8"))
    return match.group(1) if match else ""


def migration_label() -> str:
    numbers = [int(path.name[:3]) for path in (ROOT / "db" / "migrations").glob("*.sql") if path.name[:3].isdigit()]
    return f"db/schema.sql through migration {max(numbers):03d}" if numbers else "db/schema.sql"


def write(path: Path, text: str) -> None:
    path.write_text(text, newline="\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({len(text.splitlines())} lines)")


def report_difference(path: Path, regenerated: str) -> None:
    committed = path.read_text(encoding="utf-8") if path.exists() else ""
    if committed == regenerated:
        print(f"{path.relative_to(ROOT)}: unchanged")
        return
    import difflib
    diff = list(difflib.unified_diff(committed.splitlines(), regenerated.splitlines(),
                                     "committed", "regenerated", lineterm="", n=1))
    print(f"{path.relative_to(ROOT)}: DIFFERS ({max(len(diff) - 2, 0)} changed line(s))")
    for line in diff[:60]:
        print("  " + line)


def main() -> None:
    parser = argparse.ArgumentParser(description="regenerate schema-derived diagram artifacts")
    parser.add_argument("dsn", nargs="?", help="libpq connection info for a DISPOSABLE database")
    parser.add_argument("--load", action="store_true", help="apply db/schema.sql to the empty target first")
    parser.add_argument("--write", action="store_true", help="overwrite the committed artifacts")
    parser.add_argument("--verify", action="store_true", help="check physical-schema.dot against the committed catalog")
    parser.add_argument("--check-schema", action="store_true", help="check the catalog fingerprint against db/schema.sql")
    parser.add_argument("--keep-header", action="store_true", help="reuse the committed header label (faithful replay test)")
    arguments = parser.parse_args()

    schema = ROOT / "db" / "schema.sql"
    if arguments.check_schema:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        print(f"catalog     schema_sha256 = {catalog['schema_sha256']}")
        print(f"db/schema.sql   sha256 = {digest(schema)}")
        sys.exit(0 if catalog["schema_sha256"] == digest(schema) else 3)

    if arguments.verify:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        relationships = json.loads(LEDGER.read_text(encoding="utf-8"))
        header = committed_header() if arguments.keep_header else migration_label()
        report_difference(DOT, render_dot(catalog, relationships, header))
        return

    if not arguments.dsn:
        parser.error("a libpq connection info string is required unless --verify/--check-schema is used")

    with connect(arguments.dsn) as connection:
        assert_disposable(connection)
        if arguments.load:
            load_schema(connection, schema)
        tables, foreign_keys, version = collect(connection)

    existing = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else []
    relationships = merge_ids(existing, foreign_keys)
    catalog = {
        "source": f"db/schema.sql, loaded ONLY into disposable {version}",
        "tables": tables,
        "schema_sha256": digest(schema),
    }
    for path in sorted((ROOT / "db" / "migrations").glob("*.sql")):
        catalog[f"migration_{path.name[:3]}_sha256"] = digest(path)

    texts = {
        CATALOG: json.dumps(catalog, indent=2, ensure_ascii=True) + "\n",
        LEDGER: json.dumps(relationships, indent=2, ensure_ascii=True) + "\n",
        DOT: render_dot(catalog, relationships, committed_header() if arguments.keep_header else migration_label()),
    }
    if arguments.write:
        for path, text in texts.items():
            write(path, text)
    else:
        for path, text in texts.items():
            report_difference(path, text)
    print(f"{len(tables)} tables, {len(relationships)} foreign keys measured from {version}")


if __name__ == "__main__":
    main()

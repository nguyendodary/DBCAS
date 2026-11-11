# -*- coding: utf-8 -*-
"""Single source of truth for the Word documents: introspect a real PostgreSQL.

    python scripts/introspect_schema.py --load "postgresql://..." --write
    python scripts/introspect_schema.py "postgresql://..."          # print summary

Writes docs/qa/schema-introspection.json (full data dictionary) and
docs/diagrams/diagram-inventory.json (counts + names used by diagrams:check).
The target database MUST be disposable; --load applies db/schema.sql first.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs" / "diagrams" / "diagram-inventory.json"
FULL = ROOT / "docs" / "qa" / "schema-introspection.json"

TABLES = """
select c.relname
from pg_class c join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relkind = 'r' and c.relpersistence = 'p'
order by c.relname collate "C"
"""

COLUMNS = """
select column_name, data_type, udt_name, is_nullable, column_default, is_identity,
       character_maximum_length, numeric_precision, numeric_scale
from information_schema.columns
where table_schema = 'public' and table_name = %s
order by ordinal_position
"""

CONSTRAINTS = """
select con.conname, con.contype, pg_get_constraintdef(con.oid),
       coalesce(array_agg(a.attname order by u.ord) filter (where a.attname is not null), '{}')
from pg_constraint con
join pg_class c on c.oid = con.conrelid
join pg_namespace n on n.oid = c.relnamespace
left join unnest(con.conkey) with ordinality u(attnum, ord) on true
left join pg_attribute a on a.attrelid = con.conrelid and a.attnum = u.attnum
where n.nspname = 'public' and c.relname = %s
group by con.conname, con.contype, con.oid
order by con.conname collate "C"
"""

FOREIGN_KEYS = """
select con.conname, rel.relname, ref.relname,
       (select array_agg(att.attname order by u.ord)
          from unnest(con.conkey) with ordinality u(attnum, ord)
          join pg_attribute att on att.attrelid = con.conrelid and att.attnum = u.attnum),
       (select array_agg(att.attname order by u.ord)
          from unnest(con.confkey) with ordinality u(attnum, ord)
          join pg_attribute att on att.attrelid = con.confrelid and att.attnum = u.attnum),
       con.confdeltype, con.confupdtype, pg_get_constraintdef(con.oid)
from pg_constraint con
join pg_class rel on rel.oid = con.conrelid
join pg_class ref on ref.oid = con.confrelid
join pg_namespace n on n.oid = rel.relnamespace
where n.nspname = 'public' and con.contype = 'f'
order by rel.relname collate "C", con.conname collate "C"
"""

INDEXES = """
select tablename, indexname, indexdef from pg_indexes
where schemaname = 'public' order by tablename collate "C", indexname collate "C"
"""

ENUMS = """
select t.typname, array_agg(e.enumlabel order by e.enumsortorder)
from pg_type t join pg_enum e on e.enumtypid = t.oid
join pg_namespace n on n.oid = t.typnamespace
where n.nspname = 'public' and t.typtype = 'e'
group by t.typname order by t.typname collate "C"
"""

ON_ACTION = {"a": "NO ACTION", "r": "RESTRICT", "c": "CASCADE", "n": "SET NULL", "d": "SET DEFAULT"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dsn", nargs="?")
    ap.add_argument("--load", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    if not args.dsn:
        ap.error("a libpq connection info string is required")
    import psycopg

    with psycopg.connect(args.dsn, autocommit=True) as conn:
        existing = conn.execute("select tablename from pg_tables where schemaname='public'").fetchall()
        if args.load:
            assert not existing, "refusing --load: target database already holds tables"
            conn.execute((ROOT / "db" / "schema.sql").read_text(encoding="utf-8"))
        else:
            assert existing, "empty database; use --load"
        version = conn.execute("show server_version").fetchone()[0]
        tables = []
        for (name,) in conn.execute(TABLES).fetchall():
            columns = []
            for (col, dtype, udt, nullable, default, identity, maxlen, prec, scale) in conn.execute(COLUMNS, (name,)).fetchall():
                columns.append({
                    "name": col, "type": dtype, "udt": udt,
                    "nullable": nullable == "YES", "default": default,
                    "identity": identity == "YES", "max_length": maxlen,
                    "numeric_precision": prec, "numeric_scale": scale,
                })
            constraints = []
            for (cname, ctype, definition, cols) in conn.execute(CONSTRAINTS, (name,)).fetchall():
                constraints.append({"name": cname, "type": ctype, "definition": definition,
                                    "columns": list(cols)})
            tables.append({"table": name, "columns": columns, "constraints": constraints})
        fks = []
        for (cname, source, dest, cols, refcols, ondel, onupd, definition) in conn.execute(FOREIGN_KEYS).fetchall():
            fks.append({
                "constraint": cname, "source": source, "columns": list(cols),
                "destination": dest, "reference_columns": list(refcols),
                "on_delete": ON_ACTION.get(ondel, ondel), "on_update": ON_ACTION.get(onupd, onupd),
                "definition": definition,
            })
        indexes = [{"table": t, "name": i, "definition": d} for (t, i, d) in conn.execute(INDEXES).fetchall()]
        enums = [{"name": n, "values": list(v)} for (n, v) in conn.execute(ENUMS).fetchall()]

    schema_sha = hashlib.sha256((ROOT / "db" / "schema.sql").read_text(encoding="utf-8").encode()).hexdigest()
    migrations = {m.name: hashlib.sha256(m.read_text(encoding="utf-8").encode()).hexdigest()
                  for m in sorted((ROOT / "db" / "migrations").glob("*.sql"))}
    full = {
        "source": "PostgreSQL introspection of db/schema.sql",
        "postgres_version": version,
        "schema_sha256": schema_sha,
        "migrations": migrations,
        "tables": tables, "foreign_keys": fks, "indexes": indexes, "enums": enums,
    }
    inventory = {
        "source": full["source"],
        "postgres_version": version,
        "schema_sha256": schema_sha,
        "tables": len(tables),
        "foreign_keys": len(fks),
        "indexes": len(indexes),
        "enums": len(enums),
        "migrations": len(migrations),
        "table_names": [t["table"] for t in tables],
        "column_names": sorted({c["name"] for t in tables for c in t["columns"]}),
        "foreign_key_constraints": [f["constraint"] for f in fks],
    }
    print(f"{len(tables)} tables, {sum(len(t['columns']) for t in tables)} columns, "
          f"{len(fks)} FKs, {len(indexes)} indexes, {len(enums)} enums, "
          f"{len(migrations)} migrations from PostgreSQL {version}")
    if args.write:
        FULL.write_text(json.dumps(full, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        INVENTORY.write_text(json.dumps(inventory, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        print("wrote", FULL.relative_to(ROOT), "and", INVENTORY.relative_to(ROOT))


if __name__ == "__main__":
    main()

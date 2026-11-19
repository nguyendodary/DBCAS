# Database schema through migration 028

PostgreSQL 17.12 introspection of a fresh database loaded from `db/schema.sql`
found **67 tables, 561 columns, 122 foreign keys, 159 indexes and 28 migrations**.
The migration ledger is operational metadata and sits outside these table,
column and index totals. Migration 028 stores each nominated administrator's
confirmation with its database timestamp in `review_deviation_confirmation`.

- [Full data dictionary](schema-introspection.json)
- [Entity relationship diagram](erd.svg)
- [Table relationship diagram](table-relationships.svg)
- [Physical diagram and FK ledger](../physical-schema.svg) · [ledger JSON](../physical-schema-relationships.json)

To reproduce, point `scripts/introspect_schema.py --load <dsn> --write` at an empty
disposable PostgreSQL database and run `scripts/generate_schema_catalog.py <dsn>
--write` against that database. Run `npm run diagrams:render` and
`python scripts/generate_doc_diagrams.py` to render the graphs. The generators
use the newest migration number when selecting the schema snapshot directory.

The approved Word v1.2 dictionary is verified against its migration-027
snapshot. The five-page TRD QA preview records the earlier 41-table database.

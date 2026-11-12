# Editable standalone diagram sources

`npm run diagrams:check` and `npm run diagrams:render` discover sources in three places:

| Extension | Discovered from | Rendered to |
|---|---|---|
| `.dot` | `docs/diagrams/*.dot` | `docs/diagrams/<name>.svg` |
| ```` ````mermaid ```` fences | any project Markdown, plus `docs/diagrams/sources/*.mmd` | `docs/diagrams/rendered/<slug>.svg` |
| `.puml` | `docs/diagrams/sources/*.puml` | `docs/diagrams/rendered/<slug>.svg` |

Put a new Mermaid or PlantUML model here when it belongs to the diagrams set rather than to
one document. The file name becomes the SVG name, so keep names lowercase and stable: existing
links elsewhere in the repository must not break when a diagram changes.

`physical-schema.dot` is generated from [schema-catalog.json](../schema-catalog.json) and the
[foreign key ledger](../physical-schema-relationships.json) by
`python scripts/generate_schema_catalog.py`; edit the schema, not that file. Every other `.dot`
file is authored by hand and is checked against its JSON relationship ledger instead.

PlantUML needs the pinned jar and a Java runtime: `npm run diagrams:setup` fetches
`tools/plantuml-1.2023.13.jar` (gitignored, SHA-256 verified) on demand. No `.puml` source exists
today, so the PlantUML gate currently reports `SKIP` rather than pretending to have checked one.

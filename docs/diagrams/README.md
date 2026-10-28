# DBCAS architecture diagrams

Current companions dated 23 October 2026, re-verified against `db/schema.sql` and the application code on 27 October 2026 (see the [documentation/codebase alignment audit](../documentation-alignment-20261027.md)). Start with the [semantic comparison and Matrix B](semantic-review.md), then the [complete workspace inventory](inventory.md). Original raster figures are retained in `originals/`; the root university DOCX/PDF files remain unchanged.

The [acceptance review](acceptance-review-20261023.md) rechecks all 51 context
flows and all ten rendered figures, records the C43 profile/email clarification,
and identifies the detailed figures that require zoom. No flow is removed.

## Requirement-to-diagram matrix

| Diagram | Required by / purpose | Status | Current artifact and action |
|---|---|---|---|
| System Context | Architecture §2 and Proposal context figure; external responsibilities | REQUIRED | [SVG](system-context.svg), [21-flow preservation comparison](system-context-review.md); 21 old flows retained and 30 evidenced flows added |
| Use Case | Architecture §1.3; actor responsibilities and UC01–UC20 | REQUIRED | [SVG](use-cases.svg), `use-cases.dot/json`; all original goals and associations retained |
| Container | Architecture §4.1; executable/runtime boundaries | REQUIRED | [SVG](containers.svg), `containers.dot/json`; distinguish browser runtime, static host, API, databases and optional processes |
| Component | Architecture §4.2; backend responsibilities and dependencies | REQUIRED | [SVG](components.svg), `components.dot/json`; correct candidate dispatch and repository-class claims |
| Module | Architecture §5; functional modules and shared dependencies | REQUIRED | [SVG](modules.svg), `modules.dot/json`; preserve every original module chain |
| Allocation / deployment | Architecture §6; supported host/service topology | REQUIRED | [SVG](deployment.svg), `deployment.dot/json`; correct networks, HTTP/TLS boundary and optional worker/migration job |
| Conceptual ER | Architecture §7 and Database Design conceptual figure; core domain relationships | REQUIRED | [SVG](conceptual-core.svg), `conceptual-core.dot/json`; preserve all entities/keys, correct candidate seeding and optionality |
| Physical schema | Architecture/database table-relationship figures; real columns, constraints and FKs | REQUIRED | [SVG](physical-schema.svg), `physical-schema.dot` (generated), [catalog](schema-catalog.json), [FK ledger](physical-schema-relationships.json); 36 application tables, 51 FKs; migrations through 015 |
| Logical architecture | Proposal logical system architecture figure; responsibility tiers | REQUIRED | [SVG](logical-architecture.svg), `logical-architecture.dot/json`; correct persistence and service-call origins |
| Assessment pipeline | Proposal evidence-based adaptive assessment figure; selection, grading and release | REQUIRED | [SVG](assessment-lifecycle.svg), `assessment-lifecycle.dot/json`; preserve legacy loop and add actual personalized / asynchronous / human-release branches |
| Sprint roadmap | Proposal planning schedule | OPTIONAL historical | Original retained unchanged; not rewritten as a current delivery claim |
| Release workflow | `docs/supervisor-implementation.md` R1–R8 extension | NECESSARY | Existing in-document Mermaid retained unchanged as the source; [rendered SVG](rendered/supervisor-implementation-lifecycle-and-confidentiality.svg); detailed pipeline companion cross-checks manual takeover and publication |
| Original-language affected-schema excerpt | Earlier UX audit | OPTIONAL historical | Mermaid fence retained unchanged as the source; [rendered SVG](rendered/ux-simplification-audit-20261023-schema-excerpt-after-migration-012.svg); a three-entity excerpt, never presented as the full ER model |
| Rejected redraws | Rejected external document variants | OPTIONAL audit references | All 10 variants inventoried; none is a current replacement or requirement |
| Separate star schema / DFD levels / new sequence diagrams | No supporting project requirement found | UNJUSTIFIED to add in this task | Not fabricated |

## Reading the figures

Counts are semantic audit evidence, not simplification targets. Context request and response arrows remain separate. Container/module edges describe architectural dependencies at their declared abstraction; they do not replace the detailed context ledger. SVG canvases intentionally support zoom and retain full labels. The physical schema is a detailed engineering artifact, not a one-page thumbnail.

The conceptual diagram is a domain subset with keys; the physical diagram and catalog supply exhaustive database nullability, keys, uniqueness, CHECK constraints and FK definitions. DDL is authoritative.

## Generated and authored diagrams

| Kind | Artifacts | How it changes |
| --- | --- | --- |
| Generated | [schema-catalog.json](schema-catalog.json), [physical-schema-relationships.json](physical-schema-relationships.json), `physical-schema.dot` + [SVG](physical-schema.svg) | `backend/.venv/Scripts/python.exe scripts/generate_schema_catalog.py "<dsn>" --load --write` against a **disposable** database created from `db/schema.sql`. The generator refuses any target that already holds rows. FK ids already in use are preserved; new constraints are appended (`FK46`-`FK49` are `013`/`014`, `FK50`-`FK51` are `015`). |
| Generated | [rendered/manifest.json](rendered/manifest.json) | `npm run diagrams:render` records each rendered SVG with the digest of its source text. |
| Authored | the other eight `.dot` models, their `.json` ledgers and `system-context.svg` | Edit the small source, keep the ledger's `evidence` and `justification` fields honest, then re-render. Drift is detected by comparison, not assumed away. |

`scripts/validate_diagrams.py` proves the authored ledgers still match their rendered SVGs,
that the 21 original context flows are unremoved, and that the committed physical ERD is byte-for-byte
the current rendering of the generated catalog. The catalog was re-extracted on 28 October 2026 from a
disposable PostgreSQL **17.11** container - the release target major version - after `db/schema.sql`
gained migration 015 (the 27 October refresh covered migrations 013 and 014). The earlier PostgreSQL 18 extraction additionally listed named
`NOT NULL` pseudo-constraints (`contype = 'n'`), which PostgreSQL 17 does not record in `pg_constraint`;
nullability is still complete because every column carries its own `nullable` flag and the ERD prints
`NOT NULL`/`NULL` per column. A fresh-schema catalog is not the Docker release-image acceptance gate,
and it does not by itself certify persistent-data migration status.

## 27 October 2026 incremental updates

Every figure below keeps its filename, identifiers and original elements; nothing was replaced by a new,
unrelated diagram. Each change carries its own `evidence` and reason inside the ledger
(`label_updates_20261027` / `additions_20261027` / `revalidated_20261027`).

| Diagram | Disposition | Detail |
|---|---|---|
| Physical schema | regenerated, additive only | 34 tables and 49 FKs through migration 014; `FK01`–`FK45` byte-identical, `FK46`–`FK49` appended, `adaptive_event` and `assessment_blueprint` tables added |
| Conceptual ER | extended | + `AssessmentBlueprint`, `AdaptiveEvent` entities and E28–E30; the recorded E09 removal and all 17 original entities untouched |
| Component | extended | + `bp` (blueprint policy) box with B49–B51, B52 bank→LLM translation flow; s6/r6/ai labels updated |
| Module | labels only | s2/s3/s4 now name `blueprints.py`, `batch_adaptive.py`, `grading_jobs.py`, `governed_generation.py`, `question_translation.py`; M21 widened |
| Logical architecture | labels only | `adaptive`, `plan`, `ai`, L15 and L17 reworded; no node or edge added or removed |
| Assessment pipeline | extended | + `bpv` (approved blueprint version) and P28; `mode` and `complete` labels, graph title; three mis-attributed evidence citations fixed |
| Use Case | unchanged | All 20 goals and 30 associations re-verified; per-row evidence corrected (no visual change) |
| Container | unchanged | Blueprint, batch-adaptive and translation code is in-process; no new deployable unit |
| Allocation / deployment | unchanged | Migrations 013/014 add tables only; topology unaffected |
| System Context | unchanged, proposal held | All 51 flows re-verified. Proposed C52/C53 translation provider flows await owner review, because this SVG is the academically scrutinized figure |

## Validation

Run `npm run diagrams:check` (or `npm run diagrams:render` after a source change). It discovers the
nine `.dot` models, every ````mermaid```` fence in project Markdown, any `docs/diagrams/sources/*.mmd`
or `*.puml` file, then compares each render with the committed SVG and runs
`scripts/validate_diagrams.py`. `npm run diagrams:setup` reports pinned versions, the installed
browser used for Mermaid, Java and PlantUML availability. `node scripts/render_diagrams.mjs` still
works and delegates to the same implementation; set `DBCAS_VIZ_MODULE` to a `dist/viz.js` path to
override the pinned `@viz-js/viz` 3.31.0. Mermaid renders use an already installed Chrome/Edge binary
through a generated Puppeteer config, download no browser and never disable the sandbox. Rendering is
deterministic for DOT; Mermaid's ER renderer randomises relationship curvature, so non-DOT SVG
comparison ignores path geometry while text, structure and identifiers must match exactly and the
manifest pins the source digest. Browser clipping/visual inspection remains a separate verification.

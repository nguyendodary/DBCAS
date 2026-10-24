# DBCAS architecture diagrams

Current companions dated 23 October 2026. Start with the [semantic comparison and Matrix B](semantic-review.md), then the [complete workspace inventory](inventory.md). Original raster figures are retained in `originals/`; the root university DOCX/PDF files remain unchanged.

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
| Physical schema | Architecture/database table-relationship figures; real columns, constraints and FKs | REQUIRED | [SVG](physical-schema.svg), `physical-schema.dot`, [catalog](schema-catalog.json), [FK ledger](physical-schema-relationships.json); 32 tables, 45 FKs; prepared 012 included |
| Logical architecture | Proposal logical system architecture figure; responsibility tiers | REQUIRED | [SVG](logical-architecture.svg), `logical-architecture.dot/json`; correct persistence and service-call origins |
| Assessment pipeline | Proposal evidence-based adaptive assessment figure; selection, grading and release | REQUIRED | [SVG](assessment-lifecycle.svg), `assessment-lifecycle.dot/json`; preserve legacy loop and add actual personalized / asynchronous / human-release branches |
| Sprint roadmap | Proposal planning schedule | OPTIONAL historical | Original retained unchanged; not rewritten as a current delivery claim |
| Release workflow | `docs/supervisor-implementation.md` R1–R8 extension | NECESSARY | Existing Mermaid retained unchanged; detailed pipeline companion cross-checks manual takeover and publication |
| Original-language affected-schema excerpt | Earlier UX audit | OPTIONAL historical | Retained as a three-entity excerpt; never presented as the full ER model |
| Rejected redraws | Rejected external document variants | OPTIONAL audit references | All 10 variants inventoried; none is a current replacement or requirement |
| Separate star schema / DFD levels / new sequence diagrams | No supporting project requirement found | UNJUSTIFIED to add in this task | Not fabricated |

## Reading the figures

Counts are semantic audit evidence, not simplification targets. Context request and response arrows remain separate. Container/module edges describe architectural dependencies at their declared abstraction; they do not replace the detailed context ledger. SVG canvases intentionally support zoom and retain full labels. The physical schema is a detailed engineering artifact, not a one-page thumbnail.

The conceptual diagram is a domain subset with keys; the physical diagram and catalog supply exhaustive database nullability, keys, uniqueness, CHECK constraints and FK definitions. DDL is authoritative. The catalog was extracted from a disposable PostgreSQL 18 cluster and its exact schema fingerprint is checked; this does not establish PostgreSQL 17 release acceptance or persistent migration status.

## Validation

Run `py scripts/validate_diagrams.py`. Optional rendering uses `node scripts/render_diagrams.mjs` with a separately installed `@viz-js/viz` 3.31.0; set `DBCAS_VIZ_MODULE` to its `dist/viz.js` path. No application package dependency or CI workflow is required. Browser clipping/visual inspection is a separate verification recorded in the completion report.

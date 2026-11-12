# Professional diagram previews (2026-11-08) — owner approval gate

**Read this before touching any `.docx`.** The hand-rolled SVGs in
`docs/diagrams/generated/` were rejected as amateurish by the owner.
The set below is redrawn with professional tools (PlantUML / DBML /
Mermaid) from `docs/qa/schema-introspection.json` (41 tables, 293 columns,
59 FKs) and `docs/qa/project-facts.json` (6 Compose services, 82 OpenAPI
paths). Sources + rendered SVG + PNG are committed in
`docs/diagrams/pro/`; CI needs no renderers.

**Stop here.** No `.docx` is edited until the owner approves these
previews. Step 4 is NOT STARTED. To approve, reply with explicit approval;
to reject, list the diagrams to fix. This sheet is the evidence record.

## Diagram list

| # | Diagram | Tool (why) | Element count vs source evidence | Source | Preview (SVG / PNG) |
| --- | --- | --- | --- | --- | --- |
| 1 | System Context (C4 Level 1) | PlantUML — standard C4 notation, system level only, offline (no remote include) | 2 actors (Learner, Administrator from `account_role`), 1 system (DBCAS), 4 externals (LLM, Google OAuth, GitHub OAuth, Email from `oauth_providers` + LLM env + SMTP), 6 flows (labels are system-level; endpoint detail is in sequence diagram) | `docs/diagrams/pro/system-context.puml` | `docs/diagrams/pro/system-context.svg` / `.png` |
| 2 | Containers (C4 Level 2) | PlantUML — deployable units + runtime components | 2 actors, 4 containers (`frontend`, `app`, `db`, `mailpit` from `docker-compose.local.yml`), 2 runtime (`sandbox`, `prompt_builder`), 4 externals, 10 flows | `docs/diagrams/pro/containers.puml` | `docs/diagrams/pro/containers.svg` / `.png` |
| 3 | Practice sequence | Mermaid `sequenceDiagram` — message order is the point; OpenAPI paths are real | 6 participants (Learner, Frontend, API, DB, Sandbox, LLM), 15 messages; paths `/api/v1/practice/start`, `/api/v1/sessions/{id}/submit`, `/evaluations/overall` verified in `project-facts.json` (82 paths) | `docs/diagrams/pro/sequence-practice.mmd` | `docs/diagrams/pro/sequence-practice.svg` / `.png` |
| 4 | ERD (crow's foot) | DBML — native crow's foot (`>` / `*`), one model for all tables | 41 `Table` statements = `len(introspection["tables"])`; 59 `Ref:` = `len(foreign_keys)`; 293 columns via `dbml_type()` exact match; 7 `TableGroup`s; 4 legacy tables in gray with `LEGACY` note | `docs/diagrams/pro/erd.dbml` | `docs/diagrams/pro/erd.svg` / `.png` (zoomable engineering reference; print via TRDs) |
| 5–11 | Table Relationship per domain (7 panels) | DBML — same crow's foot, split so each panel is printable | Union of tables = 41 (each table once); internal `Ref:` per panel; cross-domain FKs listed as comments (canonical 59 in ERD) | `docs/diagrams/pro/trd-*.dbml` | `docs/diagrams/pro/trd-*.svg` / `.png` |

Domain split (41 tables total): identity 11, curriculum 5,
question-bank 7, practice 6, evaluation 7, legacy 4, system 1.

## Self-review (notation, layout, overlap, cut text, print legibility)

- **Notation:** C4 Person/System/External for context/containers;
  DBML crow's foot `<`/`>` for ERD/TRDs; Mermaid sequence for lifecycle.
  Legacy tables are gray with dashed header + `LEGACY` note (DBML
  `headercolor: #d3d3d3`) — never hidden.
- **Palette/font:** one palette (actors gray, system blue `#dceaf7`,
  externals pink `#f3e2ef`, DB sand `#fff8dc`, sandbox purple `#e8e2f5`);
  Arial everywhere; PlantUML `defaultFontSize 12` (≥9 pt at print when
  fitted to A4 landscape). DBML renderer default sans ≥9 pt.
- **Layout/overlap:** Graphviz (DBML) and PlantUML auto-layout with
  `legend bottom` (not right) keep labels clear. Full ERD is 3817×18931 pt
  tall — it is a zoomable SVG reference; the 7 TRD panels (max 5123 pt
  tall) are the printable splits. No entity box is split across panels;
  each table appears exactly once across TRDs.
- **Cut text:** PNGs are rendered at full SVG size (PlantUML direct
  `-tpng`; DBML/Mermaid via Chrome at SVG-matched window). System Context
  and Containers were re-checked at full width (no right-edge cut after
  label shortening and `legend bottom`). ERD PNG is a 2500-px thumbnail of
  the huge SVG — use the SVG to zoom; the TRD PNGs are the print evidence.
- **Content derivation:** every name comes from code/schema —
  Compose services (`frontend`/`app`/`db`/`mailpit`), OAuth providers
  (`google`/`github` from `project-facts.json`), table/column/FK names from
  `schema-introspection.json`. No invented elements; QA-only `qa-ai`/`meter`
  are excluded from Context (system level only) by design.

## Gates (reproducible)

```bash
python scripts/generate_pro_diagrams.py   # sources from schema-introspection + facts
DBCAS_CHROME_PATH="C:/Program Files/Google/Chrome/Application/chrome.exe" npm run docs:check
# PASS: check_doc_diagrams: 60 assertions, tables=41, columns=293, fks=59, erd_refs=59, trd_tables=41
```

`npm run docs:check` now runs `diagrams:check` + `check_docs.py` (46) +
`verify_docx.py` (41) + `check_doc_diagrams.py` (60) — all PASS locally.

## Limitations (honest)

- ERD full PNG is a thumbnail; the SVG (294 KB) must be zoomed. For the
  `.docx`, embed the ERD as landscape multi-page or replace with the 7 TRD
  panels (decision needed at approval).
- PlantUML/DBML/Mermaid renderers are local-only (portable Java 21 +
  PlantUML 1.2026.9 + Chrome). CI runs only the pure-python checks because
  SVGs+PNGs are committed.
- `docs/qa/diagram-preview/smoke/` (prior agent) uses a remote C4 include
  and fails offline; it is superseded by this sheet and left untracked.

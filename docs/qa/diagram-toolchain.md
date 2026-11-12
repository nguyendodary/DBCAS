# Diagram toolchain (2026-11-08)

> **2026-11-09 update:** `@dbml/cli` and `@softwaretechnik/dbml-renderer`
> were removed from `package.json`/`package-lock.json` because npm audit
> reported 4 high advisories in their `snowflake-sdk`/`toml`/`zod` trees.
> They were only used by the rejected `docs/diagrams/pro/` set; the active
> `diagrams:check` gate uses Mermaid, Graphviz DOT and `@viz-js/viz` only.
> The rows below are kept as the 2026-11-08 historical record.

Local machine: Windows, branch `develop2`. No application code or `.docx`
content was changed while building this toolchain. CI needs no renderers —
`sources + rendered SVG and 300-dpi PNG are committed` and a pure-python
element-count check runs in CI.

## Installed / detected

| Tool | Purpose | Version | Status |
| --- | --- | --- | --- |
| Node / npm | runner scripts | 24.16.0 / 11.13.0 | already present |
| `@mermaid-js/mermaid-cli` | Mermaid `.mmd` → SVG | 12.0.0 (pinned 12.0.0) | installed via `npm ci` |
| `@viz-js/viz` | DOT via JS Graphviz build | 3.31.0 | installed via `npm ci` |
| Graphviz `dot` | optional standalone DOT check | 16.1.0 | portable under `%LOCALAPPDATA%\DBCAS-tools\Graphviz-16.1.0\Graphviz-16.1.0-win64\bin\dot.exe` (not on PATH) |
| Java (system) | legacy `diagrams.mjs` gate | 1.8.0_401 | present on PATH |
| Java (portable) | professional PlantUML renders | 21.0.13+9 LTS (Temurin) | portable under `%LOCALAPPDATA%\DBCAS-tools\jre-21.0.13\jdk-21.0.13+9-jre\bin\java.exe` |
| PlantUML | `.puml` → SVG/PNG | 1.2026.9 | portable jar `%LOCALAPPDATA%\DBCAS-tools\PlantUML\plantuml-1.2026.9.jar` (29 MB) |
| PlantUML (repo pin) | `diagrams.mjs` fetch on demand | 1.2023.13 (SHA-256 `e68a77…`) | `tools/plantuml-1.2023.13.jar` (gitignored); fetch failed HTTP 504 on 2026-11-08; gate SKIP with 0 `.puml` in `sources/` |
| `@dbml/cli` | DBML CLI validation | 10.3.1 (pinned `^10.3.1`) | installed via `npm ci` |
| `@dbml/core` | DBML parse (via CLI) | 10.3.1 | transitive |
| `@softwaretechnik/dbml-renderer` | DBML → SVG (`run(dbml,'svg')`) | 1.0.31 | installed via `npm ci` |
| Browser | Mermaid headless render | Chrome (project path) | via `DBCAS_CHROME_PATH`; Edge fails to launch locally under Puppeteer, Chrome works; CI uses Ubuntu Chrome |

Pinned deps in `package.json` after 2026-11-09: `@mermaid-js/mermaid-cli 12.0.0`
and `@viz-js/viz 3.31.0`. The DBML packages listed above were removed; `npm ci`
now reproduces the two-package set with **0 high vulnerabilities** (2 low in
Mermaid/KaTeX remain).

## Commands

```bash
npm ci
npm run diagrams:setup           # report pinned versions, browser, Graphviz, Java, PlantUML
DBCAS_CHROME_PATH="/c/Program Files/Google/Chrome/Application/chrome.exe" npm run diagrams:check
npm run docs:check
```

## Install / pin

1. **Browser / Node deps**: `npm ci` installs Mermaid CLI 12.0.0, `@viz-js/viz`
   3.31.0, `@dbml/cli` 10.3.1, `@softwaretechnik/dbml-renderer` 1.0.31.
   Mermaid uses an installed Chrome/Edge via Puppeteer; nothing is
   downloaded and the sandbox is never weakened. On Windows set
   `DBCAS_CHROME_PATH` to `C:\Program Files\Google\Chrome\Application\chrome.exe`
   (Edge fails to launch under the local Puppeteer build, Chrome succeeds).
2. **PlantUML / Java**: legacy `diagrams.mjs` fetches `tools/plantuml-1.2023.13.jar`
   with SHA-256 verification (gitignored). Professional renders use the
   portable Java 21 + PlantUML 1.2026.9 under `%LOCALAPPDATA%\DBCAS-tools\`
   (same workaround as Word toolchain's LibreOffice/Graphviz).
   Render without the jar on CI because SVGs+PNGs are committed.
3. **Graphviz**: `diagrams.mjs` renders DOT through `@viz-js/viz`; the
   portable 16.1.0 `dot.exe` is only for standalone checks.

## Render

1. **PlantUML** `.puml` → SVG/PNG: portable `java -jar plantuml-1.2026.9.jar
   -tsvg <file.puml>` (in the source directory). No remote `!include`.
2. **DBML** `.dbml` → SVG: `node -e "const {run}=require('@softwaretechnik/dbml-renderer'); ... run(dbml,'svg')"`.
   One-line DBML without newlines fails the parser; generated DBML is
   pretty-printed.
3. **Mermaid** `.mmd` → SVG: `DBCAS_CHROME_PATH=<chrome> node_modules/.bin/mmdc
   -i in.mmd -o out.svg`. SVG → 300-dpi PNG via Chrome screenshot or
   direct `-o out.png` (PlantUML `-tpng`, `mmdc -o *.png`).

## Smoke test (end to end, 2026-11-08)

| Tool | Smoke source | Result |
| --- | --- | --- |
| Mermaid 12.0.0 | `graph TD A-->B-->C` | exit 0, 193 KB SVG via Chrome |
| DBML renderer 1.0.31 | `Table users {id, email}` | `run(dbml,'svg')` exit 0, 2519-byte SVG |
| PlantUML 1.2026.9 + Java 21 | `simple.puml` (actor/component/database, no include) | exit 0, `simple.svg` written next to source |
| PlantUML remote C4 include | `smoke/context.puml` (`!include https://…C4_Context.puml`) | fails offline (expected); pro diagrams avoid remote includes |
| Graphviz JS + `diagrams:check` | existing 9 DOT + 2 Mermaid | PASS: `checked 9 Graphviz DOT, 2 Mermaid and 0 PlantUML source(s); ledger and DDL validation passed` |

## Preflight gates

Committed SVGs/PNGs are gated by `scripts/check_doc_diagrams.py`
(pure-python element counts: DBML Ref counts vs `foreign_keys`,
PlantUML node counts vs `system-context-model.json`, legacy tags,
font-size floor, SVG dimension checks). Renderers are not required in CI.

## Operations

1. **Install / pin** — versions table above; `npm ci` + portable Java/PlantUML.
2. **Render each diagram** — `scripts/prerender_diagrams.py` or the per-tool
   commands in [Render](#render); sources in `docs/diagrams/pro/`.
3. **Preview evidence** — self-review each SVG/PNG at print size for
   notation, layout, overlap, cut text and legibility; preview sheets under
   `docs/qa/diagram-preview/`; **stop for owner approval** before any `.docx` edit.

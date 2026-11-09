# Architecture Design - word verification

- original: `C1SE.70_ArchitectureDesign_DBCAS_ver1.1.docx`
- edited: `C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx`
- generated: 2026-11-09 13:54:19
- result: **PASS**

## Measurements

- original package: 2,268,194 bytes, SHA-256 `cd57e89d3f0b3498...`
- edited package: 1,685,300 bytes, SHA-256 `fa7f5b8801b333a0...`
- paragraphs: 1383 -> 1399; text runs: 1700 -> 1714
- tables: 58 -> 58; drawings: 9 -> 9; media: 9 -> 9
- Word pages: Word COM unavailable (local-only)

## Measured checks

| Check | Result | Evidence |
|---|---|---|
| Word open/field update (local-only) | SKIP | Word COM unavailable (local-only); source SHA-256 unchanged |
| Format fidelity | PASS | 0 unexplained differences |
| Run/style fidelity | PASS | 0 new font/size or unstyled-rate issues |
| Language | PASS | 0 new Vietnamese words |
| Diagrams | PASS | 0 layout/caption/page issues |
| Data | PASS | 0 mismatches |

## Format fidelity

| Element | Original | Edited | Result |
|---|---|---|---|
| styles.xml | 30 styles | 30 styles | identical definitions |
| numbering.xml | 3 abstract / 2 nums | 3 abstract / 2 nums | identical definitions |
| sections/page setup | 10 sections | 10 sections | identical size, margins, orientation, refs |
| headers/footers | 10 parts | 10 parts | identical content |
| cover page | 27 paragraphs / 3 tables | 27 paragraphs / 3 tables | identical format |
| heading style usage | 17 headings | 17 headings | identical sequence |
| table formatting | 58 captions | 58 captions | all matched; +0 new table(s) inherit the dictionary style; 3 caption rename(s) with identical table format (content) |
| caption format | 56 captions | 56 captions | matched; +0 new caption(s) use the same format |

## Content-run formatting

| Element | Style | Measure | Result |
|---|---|---|---|
| font/size combinations | 1714 runs | 0 new | identical to original per style |
| unstyled runs | 623 runs | 631 runs | no style-level increase > 10 points |
| paragraph-dominant mismatches | 0 | 0 | no new unstyled mismatch by style |

## Language

| Element | Original | Edited | Result |
|---|---|---|---|
| Vietnamese-specific words | 0 in original | 0 in edited | no new words |

## Diagrams

| Figure | Kind | Extent (EMU) | Caption | Page before/after | Rendered pt | Page pt | Result |
|---|---|---|---|---|---|---|---|
| 1 | inline | 1809750 x 533400 |  | -/- | - | - | layout matched |
| 2 | inline | 5580000 x 6138000 | Figure 1. Use Case Diagram | -/- | - | - | layout matched |
| 3 | inline | 5580000 x 4136285 | Figure 2. System Context Diagram | -/- | - | - | layout matched |
| 4 | inline | 5238750 x 5143500 | Figure 3. Container Diagram | -/- | - | - | layout matched |
| 5 | inline | 8366760 x 5047488 | Figure 4. Component Diagram | -/- | - | - | layout matched |
| 6 | inline | 8193024 x 5084064 | Figure 5. Module View | -/- | - | - | layout matched |
| 7 | inline | 4191000 x 4038600 | Figure 6. Allocation View | -/- | - | - | layout matched |
| 8 | inline | 8124825 x 4191000 | Figure 7. Entity Relationship Diagram | -/- | - | - | layout matched |
| 9 | inline | 7877175 x 4762500 | Figure 8. Table Relationship Diagram | -/- | - | - | layout matched |

Contact sheet: `diagrams/contact-before-after.png` (if rendering was available).

## Data

| Item | Expected | Measured | Result |
|---|---|---|---|
| verify_docx.py (existing) | 41 assertions | PASS | PASS: in-place v1.2 documents match the schema and language/fact rules |
| table count statement | 41 tables | present | matches schema introspection |
| OpenAPI paths coverage | 82 paths | 0/82 named | no unknown paths; coverage is informational |
| Compose services coverage | 7 services | 4/7 named | missing in this document: executor-image, mailpit, qa-ai |

## Skipped / local-only

| Check | Tool | Reason |
|---|---|---|
| PDF diagram pages | LibreOffice/PyMuPDF | unavailable or no captions |

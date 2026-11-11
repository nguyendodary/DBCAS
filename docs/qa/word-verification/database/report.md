# Database Design - word verification

- original: `C1SE.70_DatabaseDesign_DBCAS_ver1.1.docx`
- edited: `C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx`
- generated: 2026-11-11 16:36:07
- result: **PASS**

## Measurements

- original package: 992,429 bytes, SHA-256 `7152c3a4135ae8bf...`
- edited package: 2,278,780 bytes, SHA-256 `390723782cb9c2ec...`
- paragraphs: 2399 -> 2666; text runs: 2176 -> 2442
- tables: 41 -> 46; drawings: 4 -> 8; media: 4 -> 8
- Word pages: 40p -> 40p after field update

## Measured checks

| Check | Result | Evidence |
|---|---|---|
| Word open/field update (local-only) | PASS | 40p -> 40p after field update; 250 fields, 1 TOC, 2 TOF; source SHA-256 unchanged |
| Format fidelity | PASS | 0 unexplained differences |
| Run/style fidelity | PASS | 0 new font/size or unstyled-rate issues |
| Language | PASS | 0 new Vietnamese words |
| Diagrams | PASS | 0 layout/caption/page issues |
| Data | PASS | 0 mismatches |

## Format fidelity

| Element | Original | Edited | Result |
|---|---|---|---|
| styles.xml | 37 styles | 37 styles | identical definitions |
| numbering.xml | 19 abstract / 23 nums | 19 abstract / 23 nums | identical definitions |
| sections/page setup | 7 sections | 7 sections | identical size, margins, orientation, refs |
| headers/footers | 27 parts | 27 parts | identical content |
| cover page | 5 paragraphs / 2 tables | 5 paragraphs / 2 tables | identical format |
| heading style usage | 45 headings | 50 headings | +5 new table-section headings, formatting inherited |
| table formatting | 41 captions | 46 captions | all matched; +5 new table(s) inherit the dictionary style |
| caption format | 41 captions | 46 captions | matched; +5 new caption(s) use the same format |

## Content-run formatting

| Element | Style | Measure | Result |
|---|---|---|---|
| font/size combinations | 2442 runs | 0 new | identical to original per style |
| unstyled runs | 174 runs | 202 runs | no style-level increase > 10 points |
| paragraph-dominant mismatches | 0 | 0 | no new unstyled mismatch by style |

## Language

| Element | Original | Edited | Result |
|---|---|---|---|
| Vietnamese-specific words | 0 in original | 0 in edited | no new words |

## Diagrams

| Figure | Kind | Extent (EMU) | Caption | Page before/after | Rendered pt | Page pt | Result |
|---|---|---|---|---|---|---|---|
| 1 | anchor | 6618515 x 9971314 |  | -/- | - | - | layout matched |
| 2 | inline | 5943600 x 8793480 |  | -/- | - | - | layout matched |
| 3 | inline | 8649335 x 3373241 | Figure 1: Entity Relationship Diagram | None/11 | 681x266 | 842x595 | inside text margins, caption on same page |
| 4 | inline | 8649335 x 5229830 | Figure 2: Table Relationship Diagram (1/5) | None/13 | 681x412 | 842x595 | inside text margins, caption on same page |
| 5 | inline | 8649335 x 5229830 | Figure 2: Table Relationship Diagram (2/5) | None/14 | 681x412 | 842x595 | inside text margins, caption on same page |
| 6 | inline | 8649335 x 5229830 | Figure 2: Table Relationship Diagram (3/5) | None/15 | 681x412 | 842x595 | inside text margins, caption on same page |
| 7 | inline | 8649335 x 5229830 | Figure 2: Table Relationship Diagram (4/5) | None/16 | 681x412 | 842x595 | inside text margins, caption on same page |
| 8 | inline | 8649335 x 5229830 | Figure 2: Table Relationship Diagram (5/5) | None/17 | 681x412 | 842x595 | inside text margins, caption on same page |

Contact sheet: `diagrams/contact-before-after.png` (if rendering was available).

## Data

| Item | Expected | Measured | Result |
|---|---|---|---|
| verify_docx.py (existing) | 41 assertions | PASS | PASS: in-place v1.2 documents match the schema and language/fact rules |
| data dictionary | 41 tables / 293 columns | 41 sections / 293 columns | exact names, types and nullability; 0 mismatches |
| foreign-key targets | 59 FKs | 59 FK cells | all targets resolve to schema tables |
| OpenAPI paths coverage | 82 paths | 0/82 named | no unknown paths; coverage is informational |
| Compose services coverage | 7 services | 3/7 named | missing in this document: executor-image, frontend, mailpit, qa-ai |

# Proposal - word verification

- original: `C1SE.70_ProposalDocument_DBCAS_ver1.1.docx`
- edited: `C1SE.70_ProposalDocument_DBCAS_ver1.2.docx`
- generated: 2026-11-11 22:42:22
- result: **PASS**

## Measurements

- original package: 2,725,950 bytes, SHA-256 `32b8ac763c4a6c90...`
- edited package: 2,832,300 bytes, SHA-256 `ec7d20982a096946...`
- paragraphs: 951 -> 956; text runs: 1151 -> 1157
- tables: 21 -> 21; drawings: 7 -> 7; media: 5 -> 5
- Word pages: 59p -> 59p after field update

## Measured checks

| Check | Result | Evidence |
|---|---|---|
| Word open/field update (local-only) | PASS | 59p -> 59p after field update; 138 fields, 1 TOC, 2 TOF; source SHA-256 unchanged |
| Format fidelity | PASS | 0 unexplained differences |
| Run/style fidelity | PASS | 0 new font/size or unstyled-rate issues |
| Language | PASS | 0 new Vietnamese words |
| Diagrams | PASS | 0 layout/caption/page issues |
| Data | PASS | 0 mismatches |

## Format fidelity

| Element | Original | Edited | Result |
|---|---|---|---|
| styles.xml | 55 styles | 55 styles | identical definitions |
| numbering.xml | 28 abstract / 28 nums | 28 abstract / 28 nums | identical definitions |
| sections/page setup | 2 sections | 2 sections | identical size, margins, orientation, refs |
| headers/footers | 12 parts | 12 parts | identical content |
| cover page | 29 paragraphs / 3 tables | 29 paragraphs / 3 tables | identical format |
| heading style usage | 36 headings | 36 headings | identical sequence |
| table formatting | 21 captions | 21 captions | all matched; +0 new table(s) inherit the dictionary style |
| caption format | 19 captions | 19 captions | matched; +0 new caption(s) use the same format |

## Content-run formatting

| Element | Style | Measure | Result |
|---|---|---|---|
| font/size combinations | 1157 runs | 0 new | identical to original per style |
| unstyled runs | 690 runs | 690 runs | no style-level increase > 10 points |
| paragraph-dominant mismatches | 0 | 0 | no new unstyled mismatch by style |

## Language

| Element | Original | Edited | Result |
|---|---|---|---|
| Vietnamese-specific words | 0 in original | 0 in edited | no new words |

## Diagrams

| Figure | Kind | Extent (EMU) | Caption | Page before/after | Rendered pt | Page pt | Result |
|---|---|---|---|---|---|---|---|
| 1 | inline | 1887220 x 556260 |  | -/- | - | - | layout matched |
| 2 | anchor | 4737100 x 0 |  | -/- | - | - | layout matched |
| 3 | anchor | 4694767 x 4233 |  | -/- | - | - | layout matched |
| 4 | inline | 5580000 x 4141184 | Figure 1: Agile Scrum Sprint Roadmap & Official Faculty Milestones | 44/44 | 439x326 | 595x842 | inside text margins, caption on same page |
| 5 | inline | 5580000 x 4137233 | Figure 2: DBCAS System Context Diagram | 46/46 | 439x326 | 595x842 | inside text margins, caption on same page |
| 6 | inline | 5486400 x 5417820 | Figure 3: DBCAS Logical System Architecture Diagram | 49/50 | 432x427 | 595x842 | inside text margins, caption on same page |
| 7 | inline | 5579745 x 3168231 | Figure 4: Evidence-based Competency & Gap Evaluation Pipeline | 51/52 | 439x250 | 595x842 | inside text margins, caption on same page |

Contact sheet: `diagrams/contact-before-after.png` (if rendering was available).

## Data

| Item | Expected | Measured | Result |
|---|---|---|---|
| verify_docx.py (existing) | 41 assertions | PASS | PASS: in-place v1.2 documents match the schema and language/fact rules |
| table count statement | 41 tables | present | matches schema introspection |
| OpenAPI paths coverage | 82 paths | 0/82 named | no unknown paths; coverage is informational |
| Compose services coverage | 7 services | 4/7 named | missing in this document: executor-image, mailpit, qa-ai |

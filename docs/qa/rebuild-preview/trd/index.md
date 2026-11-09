# TRD rebuild — preview index

**Figure:** Architecture Fig 8 = Database Fig 2, “Table Relationship Diagram”.
**Original:** `docs/qa/diagram-originals/ArchitectureDesign_ver1.1_image9.png`
(3440 × 2080; identical `DatabaseDesign_ver1.1_image4.png`).
**Status:** Stage A clone PASS; Stage B 41-table content delta PASS on
5 consecutive pages. No `.docx` edit, no commit/push by W3b.

## Pages

| Page | Table range (reading order) | Tables | Columns | Same-page FK connectors | Stubs out / in | Caption (Architecture) | Caption (Database) | Evidence |
| ---: | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| 1 | account → assessment_question | 10 | 52 | 8 | 2 / 12 | Figure 8. Table Relationship Diagram (1/5) | Figure 2: Table Relationship Diagram (1/5) | `../../../diagrams/rebuild/trd/trd-1.svg` / `.drawio` / `.png`; `stage-b/page-1/`; `checker-b-1.txt` |
| 2 | password_reset_token → system_setting | 11 | 63 | 7 | 7 / 2 | Figure 8. Table Relationship Diagram (2/5) | Figure 2: Table Relationship Diagram (2/5) | `../../../diagrams/rebuild/trd/trd-2.svg` / `.drawio` / `.png`; `stage-b/page-2/`; `checker-b-2.txt` |
| 3 | question → competency_gap | 7 | 57 | 6 | 4 / 6 | Figure 8. Table Relationship Diagram (3/5) | Figure 2: Table Relationship Diagram (3/5) | `../../../diagrams/rebuild/trd/trd-3.svg` / `.drawio` / `.png`; `stage-b/page-3/`; `checker-b-3.txt` |
| 4 | assessment_session → result_release_event | 7 | 60 | 6 | 8 / 6 | Figure 8. Table Relationship Diagram (4/5) | Figure 2: Table Relationship Diagram (4/5) | `../../../diagrams/rebuild/trd/trd-4.svg` / `.drawio` / `.png`; `stage-b/page-4/`; `checker-b-4.txt` |
| 5 | assessment → concept_competency | 6 | 61 | 2 | 9 / 4 | Figure 8. Table Relationship Diagram (5/5) | Figure 2: Table Relationship Diagram (5/5) | `../../../diagrams/rebuild/trd/trd-5.svg` / `.drawio` / `.png`; `stage-b/page-5/`; `checker-b-5.txt` |
| **Total** |  | **41** | **293** | **29** | **30 / 30** |  |  | 59 FKs, 19 migrations |

Exact page table order is in `../../../diagrams/rebuild/trd/spec.json`
(`pages[].tables`) and in `report.md` §2.

## Counts and gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Tables / columns / FKs / migrations | 41 / 293 / 59 / 19 | `schema-introspection.json`, `spec.json` |
| Stage A checker (broken first) | FAIL 896 problems, exit 1 | `checker-a-broken.txt` |
| Stage A checker (clone) | PASS exit 0 | `checker-a-pass.txt` |
| Stage B checker (broken page 1) | FAIL 549 problems, exit 1 | `checker-b-broken.txt` |
| Stage B checker page 1 | PASS 157 labels / 266 segments / 170 shapes | `checker-b-1.txt` |
| Stage B checker page 2 | PASS 178 labels / 309 segments / 204 shapes | `checker-b-2.txt` |
| Stage B checker page 3 | PASS 158 labels / 237 segments / 168 shapes | `checker-b-3.txt` |
| Stage B checker page 4 | PASS 174 labels / 260 segments / 191 shapes | `checker-b-4.txt` |
| Stage B checker page 5 | PASS 170 labels / 229 segments / 169 shapes | `checker-b-5.txt` |
| Stage B FK verifier | PASS: 29 same-page crow’s-foot + 30 cross-page FKs, 60 stubs, no segment inside a card, no text outside canvas | `verify-stage-b.txt` |
| Top-edge check | first text glyph at y=29 on every page; no dark pixel above y=20 | rendered PNG pixel scan |

## Comparison evidence

- **Stage A (original vs clone, same canvas):**
  `stage-a/original.png`, `clone.png`, `final.png`,
  `side-by-side.png`, `overlay.png` (red original only / blue clone only),
  `diff.png`, `regions/` + `regions-contact-sheet.png`.
- **Stage B:**
  `final-contact-sheet.png` (5 pages);
  `stage-b/original.png`;
  `stage-b/side-by-side-original-page1.png`,
  `stage-b/overlay-original-page1.png`,
  `stage-b/diff-original-page1.png` (layout-grammar comparison, not an
  identity claim: 21 cards vs 41 cards on 5 pages).
- Per-page full render: `stage-b/page-N/clone.png` + 12 region tiles.

## Method / source files

- Trace: `scripts/trace_trd_w3b.py` → `trace.json`, `trace_markers.png`.
- Stage A build: `scripts/build_trd_stage_a_w3b.py` → `trd-original-style.*`,
  `spec-stage-a.json`, `text-content-stage-a.json`.
- Stage B build: `scripts/build_trd_stage_b_w3b.py` → `trd-1..5.*`,
  `spec.json`, `text-content*.json`, `cross-page-fks.json`.
- Checkers: shared `scripts/check_diagram_geometry.py` (rule 8) and
  `scripts/verify_trd_stage_b_w3b.py` (content/FK coverage).
- Broken copy: `scripts/make_broken_svg_w3b.py`.
- Preview renderer: `scripts/make_trd_previews_w3b.py`.

## Honest legibility note

Each page is 3440 × 2080 landscape. At a 9.5 in Word figure width the
32 px card names are about 6.3 pt; on screen at 100% they are comfortably
legible, and on A3 print they are readable but small. The split into five
pages is deliberate: all 293 columns are shown, no card uses “+N more”,
and the old claim that the full schema fits one 3440 × 2080 page is not
repeated. The five captions `(1/5)`…`(5/5)` are a proposal for owner
approval; no `.docx` was edited.

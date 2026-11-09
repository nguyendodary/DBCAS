# TRD rebuild — preview index (owner fix round F6)

**Figure:** Architecture Fig 8 = Database Fig 2, “Table Relationship Diagram”.
**Original:** `docs/qa/diagram-originals/ArchitectureDesign_ver1.1_image9.png`
(3440 × 2080; identical `DatabaseDesign_ver1.1_image4.png`).
**Status:** Stage A clone PASS; Stage B F6 redo PASS on 5 consecutive
pages. The top stub bar is gone; every cross-page FK is a `to <table>
(pN)` / `from <table> (pM)` stub in the owning column row, and every
same-page FK is one orthogonal crow's-foot connector in the free gutters.
No `.docx` edit, no commit/push by this workstream.

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
(`pages[].tables`) and in `report.md` §2.4.

## Counts and gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Tables / columns / FKs / migrations | 41 / 293 / 59 / 19 | `schema-introspection.json`, `spec.json` |
| Stage A checker (broken first) | FAIL 896 problems, exit 1 | `checker-a-broken.txt` |
| Stage A checker (clone) | PASS exit 0 | `checker-a-pass.txt` |
| Stage B checker page 1 | PASS 157 labels / 263 segments / 167 shapes | `checker-b-1.txt` |
| Stage B checker page 2 | PASS 178 / 281 / 176 | `checker-b-2.txt` |
| Stage B checker page 3 | PASS 158 / 212 / 143 | `checker-b-3.txt` |
| Stage B checker page 4 | PASS 174 / 218 / 149 | `checker-b-4.txt` |
| Stage B checker page 5 | PASS 170 / 170 / 110 | `checker-b-5.txt` |
| Stage B broken page 1 | FAIL 525 problems, exit 1 | `checker-b-1-broken.txt` |
| Stage B broken page 2 | FAIL 625 problems, exit 1 | `checker-b-2-broken.txt` |
| Stage B broken page 3 | FAIL 490 problems, exit 1 | `checker-b-3-broken.txt` |
| Stage B broken page 4 | FAIL 562 problems, exit 1 | `checker-b-4-broken.txt` |
| Stage B broken page 5 | FAIL 559 problems, exit 1 | `checker-b-5-broken.txt` |
| Stage B FK verifier | **PASS 59/59 exactly once** — 29 same-page connectors + 30 cross-page FK pairs (60 stubs); no segment inside a card or text; stubs in the correct column rows; no dangling endpoint | `verify-stage-b.txt` |
| FK verifier negative test | FAIL 7 problems, 58/59 (deliberately deleted stub + segment through a card) | `verify-stage-b-broken.txt` |
| Top-edge check | cards start y=42; first text ink y=65 (page 5 y=57 LEGACY tag); no top stub band | rendered PNG / `spec.json` |

## Comparison evidence

- **Stage A (original vs clone, same canvas):**
  `stage-a/original.png`, `clone.png`, `final.png`,
  `side-by-side.png`, `overlay.png` (red original only / blue clone only),
  `diff.png`, `regions/` + `regions-contact-sheet.png`.
- **Stage B page 1 vs original:**
  `stage-b/original.png`,
  `stage-b/side-by-side-original-page1.png`,
  `stage-b/overlay-original-page1.png` (red original only / blue new only),
  `stage-b/diff-original-page1.png`. This is a layout-grammar comparison,
  not an identity claim: the original is 21 cards on one page, new page 1
  is 10 cards with 52 columns and 14 stubs; measured overlay changed
  682,333 px (orig-only 394,965 / new-only 287,368).
- **Five-page contact sheet:** `final-contact-sheet.png`.
- Per-page full render: `stage-b/page-N/clone.png`; 12 region tiles
  `stage-b/page-N/regions/r11..r34.png`; contact sheet
  `stage-b/page-N/regions-contact-sheet.png`.

## Method / source files

- Trace: `scripts/trace_trd_w3b.py` → `trace.json`, `trace_markers.png`.
- Stage A build: `scripts/build_trd_stage_a_w3b.py` → `trd-original-style.*`,
  `spec-stage-a.json`, `text-content-stage-a.json`.
- Stage B F6 build: `scripts/build_trd_stage_b_f6.py` (shared helpers
  `scripts/trd_common_f6.py`) → `trd-1..5.*`, `spec.json` (with
  `connectors` + `stubs`), `text-content*.json`, `cross-page-fks.json`.
- Checkers: shared `scripts/check_diagram_geometry.py` (rule 8) and
  `scripts/verify_trd_stage_b_f6.py` (content/geometry/FK coverage).
- Broken copies: `scripts/make_broken_svg_w3b.py` (one per page).
- Preview renderer: `scripts/make_trd_previews_f6.py`; final comparison +
  contact sheets: `scripts/make_trd_final_f6.py`.

## Honest legibility note

Each page is 3440 × 2080 landscape. At a 9.5 in Word figure width the
32 px card names are about 6.3 pt; on screen at 100% they are comfortably
legible, and on A3 print they are readable but small. The 24 px stub text
is about 4.7 pt at 9.5 in — it is deliberately smaller than the column
text and is intended for the full-page/A3 view. All 293 columns are shown,
no card uses “+N more”, and the old claim that the full schema fits one
3440 × 2080 page is not repeated. The five captions `(1/5)`…`(5/5)` are a
proposal for owner approval; no `.docx` was edited.

Dense-but-verified areas: `account.account_id` (7 same-page connectors +
12 incoming stubs), `question.question_id` (6 connectors + 5 incoming
stubs) and `assessment_session.session_id` (4 connectors + 3 incoming
stubs). All connector lanes are in the 55 px column gutters / 60 px row
gaps; the verifier proves no segment midpoint or interior part is inside a
card and no segment intersects a text bbox.

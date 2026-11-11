# Pipeline - pre-build element inventory (Stage A clone)

Generated from `trace.json` (pixel-measured) + `text-content.json`
(strings read from original crops). Every element listed exactly
once.

Canvas: **1342 x 762**

## Shapes (9)

| # | id | kind | bbox (x0,y0,x1,y1) | fill | stroke | sw | extra |
|---|----|------|--------------------|------|--------|----|-------|
| 1 | S01 | boundary | [10, 107, 1322, 614] | #FFFFFF | #5E6163 | 2 | dashed 6/6 |
| 2 | S02 | rounded | [904.0, 436.0, 1295.0, 592.0] | #EDF4F7 | #3D4144 | 2 | radius 9 |
| 3 | S03 | rounded | [47.0, 436.0, 369.0, 592.0] | #F4F6F8 | #3D4144 | 2 | radius 9 |
| 4 | S04 | rounded | [509.0, 436.0, 831.0, 592.0] | #F4F6F8 | #3D4144 | 2 | radius 9 |
| 5 | S05 | rounded | [1077.0, 130.0, 1312.0, 268.0] | #F4F6F8 | #3D4144 | 2 | radius 9 |
| 6 | S06 | rounded | [26.0, 130.0, 261.0, 268.0] | #F4F6F8 | #3D4144 | 2 | radius 9 |
| 7 | S07 | rounded | [552.0, 130.0, 786.0, 268.0] | #F4F6F8 | #3D4144 | 2 | radius 9 |
| 8 | S08 | rounded | [289.0, 130.0, 524.0, 268.0] | #F4F6F8 | #3D4144 | 2 | radius 9 |
| 9 | S09 | rounded | [815.0, 130.0, 1049.0, 268.0] | #F4F6F8 | #3D4144 | 2 | radius 9 |

## Dash runs (6)

| # | axis | pos | span | dashes | on | off |
|---|------|-----|------|--------|----|-----|
| 10 | h | 107 | 10..401 | 33 | 7 | 5 |
| 11 | v | 10 | 107..615 | 43 | 7 | 5 |
| 12 | h | 614 | 10..508 | 46 | 6 | 5 |
| 13 | h | 614 | 850..1323 | 44 | 6 | 5 |
| 14 | v | 1322 | 298..615 | 27 | 6 | 6 |
| 15 | h | 294 | 1195..1322 | 11 | 6 | 6 |

## Lines (8) + arrowheads (8)

| # | id | segments | stroke | colour | arrow tip |
|---|----|----------|--------|--------|-----------|
| 16 + 17 | L01 | (261,200.5)-(289.5,200.5) | 2.0 | #34383B | [290.0, 200.5] |
| 18 + 19 | L02 | (525,200.5)-(552.5,200.5) | 2.0 | #34383B | [553.0, 200.5] |
| 20 + 21 | L03 | (786,200.5)-(814.5,200.5) | 2.0 | #34383B | [815.0, 200.5] |
| 22 + 23 | L04 | (1049,200.5)-(1077.5,200.5) | 2.0 | #34383B | [1078.0, 200.5] |
| 24 + 25 | L05 | (1195.5,267.5)-(1195.5,437.5) | 2.0 | #34383B | [1195.5, 438.5] |
| 26 + 27 | L06 | (670.5,438.5)-(670.5,384.5) -> (670.5,384.5)-(932.5,384.5) -> (932.5,384.5)-(932.5,268) | 2.0 | #34383B | [932.5, 267.5] |
| 28 + 29 | L07 | (369,514)-(510,514) | 2.0 | #34383B | [510.5, 514.0] |
| 30 + 31 | L08 | (406.5,107)-(406.5,131) | 2.0 | #34383B | [406.5, 131.5] |


## Texts (35)

| # | id | bbox | inside | ink | content |
|---|----|------|--------|-----|---------|
| 32 | X001 | [325, 11, 1018, 40] | None | #17191A | Evidence-based adaptive assessment pipeline |
| 33 | X002 | [374, 54, 968, 71] | None | #25282A | Three basic MCQs first • each later question selected from live evidence |
| 34 | X003 | [102, 150, 187, 170] | S06 | #191B1D | Opening |
| 35 | X004 | [310, 150, 506, 167] | S08 | #191B1D | Grade each answer |
| 36 | X005 | [624, 150, 716, 166] | S07 | #191B1D | Evidence |
| 37 | X006 | [838, 150, 1026, 170] | S09 | #191B1D | Adaptive selection |
| 38 | X007 | [1149, 150, 1243, 166] | S05 | #191B1D | Next item |
| 39 | X008 | [856, 183, 1004, 198] | S09 | #222527 | After opening MCQs: |
| 40 | X009 | [67, 189, 222, 201] | S06 | #222527 | 3 MCQs at levels 1–2 |
| 41 | X010 | [318, 189, 498, 204] | S08 | #222527 | MCQ key • SQL sandbox |
| 42 | X011 | [623, 189, 719, 201] | S07 | #222527 | Record result |
| 43 | X012 | [1140, 192, 1251, 204] | S05 | #222527 | Serve validated |
| 44 | X013 | [846, 203, 1019, 215] | S09 | #222527 | 3/3 harder • 2/3 medium |
| 45 | X014 | [73, 209, 216, 221] | S06 | #222527 | from validated bank |
| 46 | X015 | [336, 209, 479, 224] | S08 | #222527 | LLM-assisted essay |
| 47 | X016 | [578, 209, 763, 224] | S07 | #222527 | update concept estimates |
| 48 | X017 | [1148, 213, 1244, 228] | S05 | #222527 | question only |
| 49 | X018 | [866, 222, 1000, 234] | S09 | #222527 | 0–1/3 basic / weak |
| 50 | X019 | [988, 453, 1214, 473] | S02 | #191B1D | Complete assessment |
| 51 | X020 | [96, 456, 321, 476] | S03 | #191B1D | Candidate preparation |
| 52 | X021 | [571, 456, 771, 472] | S04 | #191B1D | Validated item bank |
| 53 | X022 | [984, 483, 1217, 498] | S02 | #222527 | At configured cap (≤13) or 00:00 |
| 54 | X023 | [119, 493, 298, 505] | S03 | #222527 | AI drafts before sessions |
| 55 | X024 | [583, 493, 759, 509] | S04 | #222527 | Store only after approval |
| 56 | X025 | [985, 503, 1217, 518] | S02 | #222527 | Deterministic per-concept profile |
| 57 | X026 | [117, 515, 301, 530] | S03 | #222527 | System checks candidate |
| 58 | X027 | [571, 515, 770, 530] | S04 | #222527 | Only validated items served |
| 59 | X028 | [937, 522, 1264, 538] | S02 | #222527 | “What to study next”: gaps ranked by shortfall |
| 60 | X029 | [125, 536, 292, 552] | S03 | #222527 | Administrator approves |
| 61 | X030 | [572, 536, 769, 548] | S04 | #222527 | Validated fallback if needed |
| 62 | X031 | [943, 542, 1258, 557] | S02 | #222527 | Concept name + description when available |
| 63 | X032 | [980, 561, 1222, 577] | S02 | #222527 | Evidence-linked gap explanations |
| 64 | X033 | [522, 609, 842, 624] | None | #222527 | Repeat after each answer until cap or timer |
| 65 | X034 | [408, 652, 934, 672] | None | #191B1D | Target mix for a full session: 10 MCQ / 2 SQL / 1 essay |
| 66 | X035 | [314, 687, 1027, 702] | None | #333638 | Ranked gap topics only; long-term learning paths and course-document retrieval are outside scope. |

## Total

9 shapes + 6 dash runs + 8 lines + 8 arrowheads + 35 texts = **66 elements**, each listed exactly once.

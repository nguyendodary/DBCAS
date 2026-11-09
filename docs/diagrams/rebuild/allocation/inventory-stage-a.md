# Allocation - pre-build element inventory (Stage A clone)

Generated from `trace.json` (pixel-measured) + `text-content.json`
(strings read from original crops). Every element listed exactly
once.

Canvas: **1331 x 1283**

## Shapes (9)

| # | id | kind | bbox (x0,y0,x1,y1) | fill | stroke | sw | extra |
|---|----|------|--------------------|------|--------|----|-------|
| 1 | S01 | boundary | [53, 541, 860, 1229] | #FFFFFF | #666666 | 2 | dashed 11/11 |
| 2 | S02 | cylinder | [455, 1056, 815, 1192] | #C0392B | #8B2B21 | 2 | cap 10, 138 outline pts |
| 3 | S03 | cylinder | [91, 1056, 363, 1192] | #1E88D0 | #0D4E8B | 2 | cap 9, 138 outline pts |
| 4 | S04 | rounded | [900, 1075, 1291, 1173] | #6A5ACD | #3F3494 | 2 | radius 15 |
| 5 | S05 | rounded | [412, 835, 791, 934] | #1E88D0 | #0E5089 | 2 | radius 19 |
| 6 | S06 | rounded | [425, 615, 769, 714] | #1E88D0 | #0E508C | 2 | radius 17 |
| 7 | S07 | rounded | [413, 208, 781, 290] | #E8EEF5 | #888888 | 2 | radius 10 |
| 8 | S08 | rounded | [441, 39, 753, 108] | #08427B | #08427B | 7 | radius 17 |
| 9 | S09 | ellipse | [498, 392, 695, 467] | #E8F5F0 | #79C1B8 | 2 |  |

## Dash runs (4)

| # | axis | pos | span | dashes | on | off |
|---|------|-----|------|--------|----|-----|
| 10 | h | 541 | 59..860 | 38 | 11 | 11 |
| 11 | h | 1229 | 53..854 | 38 | 11 | 11 |
| 12 | v | 53 | 547..1229 | 32 | 11 | 11 |
| 13 | v | 860 | 541..1223 | 32 | 11 | 11 |

## Lines (8) + arrowheads (7)

| # | id | segments | stroke | colour | arrow tip |
|---|----|----------|--------|--------|-----------|
| 14 + 15 | L01 | (1039,1075)-(860.5,968.5) -> (860.5,968.5)-(867.4,974.9) -> (867.4,974.9)-(774.3,937.3) | 2.0 | #444444 | [1039.0, 1075.0] |
| 16 + 17 | L02 | (448.3,949.6)-(295,1057) | 2.0 | #454545 | [295.0, 1057.0] |
| 18 + 19 | L03 | (597,296)-(594,392) | 2.5 | #474747 | [594.0, 392.0] |
| 20 + 21 | L04 | (597,720)-(594,835) | 2.5 | #474747 | [594.0, 835.0] |
| 22 + 23 | L05 | (597,114)-(594,208) | 3.0 | #666666 | [594.0, 208.0] |
| 24 + 25 | L06 | (623,1056)-(604.7,939.9) | 2.0 | #606060 | [623.0, 1056.0] |
| 26 + 27 | L07 | (597,473)-(597,543) | 2.5 | #000000 | None |
| 28 + 29 | L08 | (595.966,572)-(593,615) | 2.5 | #000000 | [593.0, 615.0] |


## Texts (39)

| # | id | bbox | inside | ink | content |
|---|----|------|--------|-----|---------|
| 30 | X001 | [469, 54, 726, 70] | S08 | #FFFFFF | Learner / Administrator |
| 31 | X002 | [564, 74, 629, 89] | S08 | #FFFFFF | [Person] |
| 32 | X003 | [601, 149, 639, 162] | None | #222222 | Uses |
| 33 | X004 | [522, 222, 671, 238] | S07 | #1A1A1A | User's Device |
| 34 | X005 | [438, 242, 755, 257] | S07 | #1D1D1D | Laptop / desktop with modern browser |
| 35 | X006 | [473, 262, 720, 277] | S07 | #202021 | [Chrome, Edge, Firefox, Safari] |
| 36 | X007 | [600, 333, 654, 346] | None | #222222 | HTTPS |
| 37 | X008 | [553, 417, 641, 433] | S09 | #1A1A1A | Internet |
| 38 | X009 | [610, 509, 653, 522] | None | #222222 | HTTPS |
| 39 | X010 | [248, 544, 843, 571] | None | #000000 | [Deployment Node: containerized deployment, Docker Compose] |
| 40 | X011 | [70, 548, 239, 567] | None | #000000 | Docker-capable Host |
| 41 | X012 | [531, 629, 662, 644] | S06 | #FFFFFF | Web Server |
| 42 | X013 | [551, 649, 640, 664] | S06 | #FFFFFF | [Container] |
| 43 | X014 | [476, 668, 717, 681] | S06 | #FBFDFE | Serves static content and the |
| 44 | X015 | [450, 684, 742, 700] | S06 | #FAFCFE | React + Vite single-page application |
| 45 | X016 | [607, 756, 724, 773] | None | #222222 | JSON / HTTPS |
| 46 | X017 | [600, 775, 734, 791] | None | #222222 | (REST API calls) |
| 47 | X018 | [493, 850, 699, 865] | S05 | #FFFFFF | Application Server |
| 48 | X019 | [450, 868, 776, 885] | S05 | #FFFFFF | [Container: FastAPI, Python 3.13] |
| 49 | X020 | [461, 890, 743, 905] | S05 | #F7FBFD | Business logic, JWT / RBAC, grading, |
| 50 | X021 | [437, 907, 757, 922] | S05 | #FFFFFF | adaptive selection, competency engine |
| 51 | X022 | [618, 975, 842, 991] | None | #222222 | Sandboxed SQL execution |
| 52 | X023 | [961, 975, 1131, 993] | None | #222222 | Sanitized prompts / |
| 53 | X024 | [449, 976, 553, 995] | None | #222222 | DB requests |
| 54 | X025 | [414, 995, 588, 1015] | None | #222222 | (SQL / SQLAlchemy) |
| 55 | X026 | [631, 995, 830, 1013] | None | #222222 | (read-only transaction) |
| 56 | X027 | [939, 995, 1151, 1013] | None | #222222 | structured JSON (HTTPS) |
| 57 | X028 | [175, 1088, 278, 1104] | S03 | #FFFFFF | Database |
| 58 | X029 | [559, 1089, 703, 1103] | S02 | #FFFFFF | SQL Sandbox |
| 59 | X030 | [1001, 1089, 1188, 1104] | S04 | #FFFFFF | LLM Provider API |
| 60 | X031 | [463, 1106, 795, 1125] | S02 | #FFFFFF | [Container: Docker, PostgreSQL 17] |
| 61 | X032 | [114, 1108, 343, 1125] | S03 | #FFFFFF | [Container: PostgreSQL 17] |
| 62 | X033 | [925, 1109, 1265, 1124] | S04 | #FDFDFE | [External service: provider-agnostic REST] |
| 63 | X034 | [481, 1125, 781, 1140] | S02 | #FFFFFF | Isolated, network disabled, read-only |
| 64 | X036 | [115, 1126, 335, 1140] | S03 | #FFFFFF | Application data, evidence, |
| 65 | X035 | [977, 1128, 1212, 1143] | S04 | #FFFFFF | Essay scoring, CLO mapping, |
| 66 | X038 | [497, 1144, 765, 1158] | S02 | #FFFDFD | learner role, 256 MB, 3 s timeout |
| 67 | X037 | [134, 1145, 318, 1160] | S03 | #FEFFFF | cached LLM responses |
| 68 | X039 | [955, 1147, 1234, 1163] | S04 | #FEFEFF | tag suggestions, gap explanations |

## Total

9 shapes + 4 dash runs + 8 lines + 7 arrowheads + 39 texts = **68 elements**, each listed exactly once.

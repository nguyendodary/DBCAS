# Allocation - element inventory

Generated from `trace.json` (pixel-measured) + `text-content.json`
(strings read from original crops). Every element is listed exactly
once. Stage A/B label counts are stated where they differ.

Canvas: **1331 x 1283**

## Shapes (9)

| # | id | kind | bbox (x0,y0,x1,y1) | fill | stroke | sw | extra |
|---|----|------|--------------------|------|--------|----|-------|
| 1 | S01 | boundary | [53, 541, 860, 1229] | #FFFFFF | #666666 | 2 | dashed 11/11 |
| 2 | S02 | cylinder | [455, 1056, 807, 1192] | #C0392B | #8B2B21 | 2 | cap 10, 138 outline pts |
| 3 | S03 | cylinder | [91, 1056, 363, 1192] | #1E88D0 | #0D4E8B | 2 | cap 9, 138 outline pts |
| 4 | S04 | rounded | [900, 1075, 1291, 1173] | #6A5ACD | #3F3494 | 2 | radius 15 |
| 5 | S05 | rounded | [412, 835, 782, 934] | #1E88D0 | #0E5089 | 2 | radius 19 |
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
| 14 | L01 | (1039,1075)-(860.5,968.5) -> (860.5,968.5)-(867.4,974.9) -> (867.4,974.9)-(774.3,937.3) | 2.0 | #444444 | yes |
| 15 | L01-A | arrowhead at [1039.0, 1075.0] | - | #444444 | - |
| 16 | L02 | (448.3,949.6)-(295,1057) | 2.0 | #454545 | yes |
| 17 | L02-A | arrowhead at [295.0, 1057.0] | - | #454545 | - |
| 18 | L03 | (597,296)-(594,392) | 2.5 | #474747 | yes |
| 19 | L03-A | arrowhead at [594.0, 392.0] | - | #474747 | - |
| 20 | L04 | (597,720)-(594,835) | 2.5 | #474747 | yes |
| 21 | L04-A | arrowhead at [594.0, 835.0] | - | #474747 | - |
| 22 | L05 | (597,114)-(594,208) | 3.0 | #666666 | yes |
| 23 | L05-A | arrowhead at [594.0, 208.0] | - | #666666 | - |
| 24 | L06 | (623,1056)-(604.7,939.9) | 2.0 | #606060 | yes |
| 25 | L06-A | arrowhead at [623.0, 1056.0] | - | #606060 | - |
| 26 | L07 | (597,473)-(597,543) | 2.5 | #000000 | none |
| 27 | L08 | (595.966,572)-(593,615) | 2.5 | #000000 | yes |
| 28 | L08-A | arrowhead at [593.0, 615.0] | - | #000000 | - |

## Actor stick figures (0)


## Texts (39)

| # | id | bbox | inside | ink | content |
|---|----|------|--------|-----|---------|
| 29 | X001 | [469, 54, 726, 70] | S08 | #FFFFFF | Learner / Administrator |
| 30 | X002 | [564, 74, 629, 89] | S08 | #FFFFFF | [Person] |
| 31 | X003 | [601, 149, 639, 162] | None | #222222 | Uses |
| 32 | X004 | [522, 222, 671, 238] | S07 | #1A1A1A | User's Device |
| 33 | X005 | [438, 242, 755, 257] | S07 | #1D1D1D | Laptop / desktop with modern browser |
| 34 | X006 | [473, 262, 720, 277] | S07 | #202021 | [Chrome, Edge, Firefox, Safari] |
| 35 | X007 | [600, 333, 654, 346] | None | #222222 | HTTPS |
| 36 | X008 | [553, 417, 641, 433] | S09 | #1A1A1A | Internet |
| 37 | X009 | [610, 509, 653, 522] | None | #222222 | HTTPS |
| 38 | X010 | [248, 544, 843, 571] | None | #000000 | [Deployment Node: containerized deployment, Docker Compose] |
| 39 | X011 | [70, 548, 239, 567] | None | #000000 | Docker-capable Host |
| 40 | X012 | [531, 629, 662, 644] | S06 | #FFFFFF | Web Server |
| 41 | X013 | [551, 649, 640, 664] | S06 | #FFFFFF | [Container] |
| 42 | X014 | [476, 668, 717, 681] | S06 | #FBFDFE | Serves static content and the |
| 43 | X015 | [450, 684, 742, 700] | S06 | #FAFCFE | React + Vite single-page application |
| 44 | X016 | [607, 756, 724, 773] | None | #222222 | JSON / HTTPS |
| 45 | X017 | [600, 775, 734, 791] | None | #222222 | (REST API calls) |
| 46 | X018 | [493, 850, 699, 865] | S05 | #FFFFFF | Application Server |
| 47 | X019 | [450, 868, 776, 885] | S05 | #FFFFFF | [Container: FastAPI, Python 3.13] |
| 48 | X020 | [461, 890, 743, 905] | S05 | #F7FBFD | Business logic: JWT / RBAC, grading, |
| 49 | X021 | [424, 907, 771, 922] | S05 | #FFFFFF | practice plan assembly, competency engine |
| 50 | X022 | [618, 975, 842, 991] | None | #222222 | Sandboxed SQL execution |
| 51 | X023 | [961, 975, 1131, 993] | None | #222222 | Sanitized prompts / |
| 52 | X024 | [449, 976, 553, 995] | None | #222222 | DB requests |
| 53 | X025 | [414, 995, 588, 1015] | None | #222222 | (SQL / SQLAlchemy) |
| 54 | X026 | [631, 995, 830, 1013] | None | #222222 | (read-only transaction) |
| 55 | X027 | [939, 995, 1151, 1013] | None | #222222 | structured JSON (HTTPS) |
| 56 | X028 | [175, 1088, 278, 1104] | S03 | #FFFFFF | Database |
| 57 | X029 | [559, 1089, 703, 1103] | S02 | #FFFFFF | SQL Sandbox |
| 58 | X030 | [1001, 1089, 1188, 1104] | S04 | #FFFFFF | LLM Provider API |
| 59 | X031 | [463, 1106, 795, 1125] | S02 | #FFFFFF | [Container: Docker, PostgreSQL 17] |
| 60 | X032 | [114, 1108, 343, 1125] | S03 | #FFFFFF | [Container: PostgreSQL 17] |
| 61 | X033 | [925, 1109, 1265, 1124] | S04 | #FDFDFE | [External service: provider-agnostic REST] |
| 62 | X034 | [481, 1125, 781, 1140] | S02 | #FFFFFF | Isolated, network disabled, read-only |
| 63 | X036 | [115, 1126, 335, 1140] | S03 | #FFFFFF | Application data, evidence, |
| 64 | X035 | [977, 1128, 1212, 1143] | S04 | #FFFFFF | Essay scoring, CLO mapping, |
| 65 | X038 | [501, 1144, 761, 1158] | S02 | #FFFDFD | learner role; 256 MB, 3 s timeout |
| 66 | X037 | [134, 1145, 318, 1160] | S03 | #FEFFFF | cached LLM responses |
| 67 | X039 | [955, 1147, 1234, 1163] | S04 | #FEFEFF | tag suggestions, gap explanations |

## Total

9 shapes + 4 dash runs + 8 lines + 7 arrowheads + 0 actor stick figures + 39 texts = **67 elements**, each listed exactly once.

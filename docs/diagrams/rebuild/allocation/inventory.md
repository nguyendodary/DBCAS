# Allocation - element inventory (Stage B baseline + F2 owner fix)

Generated from `trace.json` + `text-content.json` after the frame-label,
HTTPS and OAuth/Email fixes. Every element listed exactly once.

Canvas: **1725 x 1600**

## Shapes (11)

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
| 10 | S10 | rounded | [900, 1420, 1291, 1565] | #6A5ACD | #3F3494 | 2 | radius 15 |
| 11 | S11 | rounded | [1308, 1420, 1699, 1565] | #6A5ACD | #3F3494 | 2 | radius 15 |

## Dash runs (4)

| # | axis | pos | span | dashes | on | off |
|---|------|-----|------|--------|----|-----|
| 12 | h | 541 | 59..860 | 38 | 11 | 11 |
| 13 | h | 1229 | 53..854 | 38 | 11 | 11 |
| 14 | v | 53 | 547..1229 | 32 | 11 | 11 |
| 15 | v | 860 | 541..1223 | 32 | 11 | 11 |

## Lines (9) + arrowheads (9)

| # | id | segments | stroke | colour | arrow tip |
|---|----|----------|--------|--------|-----------|
| 16 + 17 | L01 | (1039,1075)-(860.5,968.5) -> (860.5,968.5)-(867.4,974.9) -> (867.4,974.9)-(774.3,937.3) | 2.0 | #444444 | [1039.0, 1075.0] |
| 18 + 19 | L02 | (448.3,949.6)-(295,1057) | 2.0 | #454545 | [295.0, 1057.0] |
| 20 + 21 | L03 | (597,296)-(594,392) | 2.5 | #474747 | [594.0, 392.0] |
| 22 + 23 | L04 | (597,720)-(594,835) | 2.5 | #474747 | [594.0, 835.0] |
| 24 + 25 | L05 | (597,114)-(594,208) | 3.0 | #666666 | [594.0, 208.0] |
| 26 + 27 | L06 | (623,1056)-(604.7,939.9) | 2.0 | #606060 | [623.0, 1056.0] |
| 28 + 29 | L07 | (597,473)-(593,615) | 2.5 | #474747 | [593, 615] |
| 30 + 31 | L09 | (791,890)-(870,890) -> (870,890)-(870,1380) -> (870,1380)-(1095,1380) -> (1095,1380)-(1095,1420) | 2.0 | #444444 | [1095, 1420] |
| 32 + 33 | L10 | (791,910)-(880,910) -> (880,910)-(880,1350) -> (880,1350)-(1503,1350) -> (1503,1350)-(1503,1420) | 2.0 | #444444 | [1503, 1420] |


## Texts (50)

| # | id | bbox | inside | ink | content |
|---|----|------|--------|-----|---------|
| 34 | X001 | [469, 54, 726, 70] | S08 | #FFFFFF | Learner / Administrator |
| 35 | X002 | [564, 74, 629, 89] | S08 | #FFFFFF | [Person] |
| 36 | X003 | [601, 149, 639, 162] | None | #222222 | Uses |
| 37 | X004 | [522, 222, 671, 238] | S07 | #1A1A1A | User's Device |
| 38 | X005 | [438, 242, 755, 257] | S07 | #1D1D1D | Laptop / desktop with modern browser |
| 39 | X006 | [473, 262, 720, 277] | S07 | #202021 | [Chrome, Edge, Firefox, Safari] |
| 40 | X007 | [600, 333, 654, 346] | None | #222222 | HTTPS |
| 41 | X008 | [553, 417, 641, 433] | S09 | #1A1A1A | Internet |
| 42 | X009 | [610, 509, 653, 522] | None | #222222 | HTTPS |
| 43 | X010 | [288, 547, 581, 566] | None | #000000 | [Deployment Node: containerized |
| 44 | X011 | [60, 547, 270, 566] | None | #000000 | Docker-capable Host |
| 45 | X012 | [531, 629, 662, 644] | S06 | #FFFFFF | Web Server |
| 46 | X013 | [551, 649, 640, 664] | S06 | #FFFFFF | [Container] |
| 47 | X014 | [476, 668, 717, 681] | S06 | #FBFDFE | Serves static content and the |
| 48 | X015 | [450, 684, 742, 700] | S06 | #FAFCFE | React + Vite single-page application |
| 49 | X016 | [607, 756, 724, 773] | None | #222222 | JSON / HTTPS |
| 50 | X017 | [600, 775, 734, 791] | None | #222222 | (REST API calls) |
| 51 | X018 | [493, 850, 699, 865] | S05 | #FFFFFF | Application Server |
| 52 | X019 | [450, 868, 776, 885] | S05 | #FFFFFF | [Container: FastAPI, Python 3.13] |
| 53 | X020 | [461, 890, 743, 905] | S05 | #F7FBFD | Business logic: JWT / RBAC, grading, |
| 54 | X021 | [424, 907, 771, 922] | S05 | #FFFFFF | practice plan assembly, competency engine |
| 55 | X022 | [618, 975, 842, 991] | None | #222222 | Sandboxed SQL execution |
| 56 | X023 | [961, 975, 1131, 993] | None | #222222 | Sanitized prompts / |
| 57 | X024 | [449, 976, 553, 995] | None | #222222 | DB requests |
| 58 | X025 | [414, 995, 588, 1015] | None | #222222 | (SQL / SQLAlchemy) |
| 59 | X026 | [631, 995, 830, 1013] | None | #222222 | (read-only transaction) |
| 60 | X027 | [939, 995, 1151, 1013] | None | #222222 | structured JSON (HTTPS) |
| 61 | X028 | [175, 1088, 278, 1104] | S03 | #FFFFFF | Database |
| 62 | X029 | [559, 1089, 703, 1103] | S02 | #FFFFFF | SQL Sandbox |
| 63 | X030 | [1001, 1089, 1188, 1104] | S04 | #FFFFFF | LLM Provider API |
| 64 | X031 | [463, 1106, 795, 1125] | S02 | #FFFFFF | [Container: Docker, PostgreSQL 17] |
| 65 | X032 | [114, 1108, 343, 1125] | S03 | #FFFFFF | [Container: PostgreSQL 17] |
| 66 | X033 | [925, 1109, 1265, 1124] | S04 | #FDFDFE | [External service: provider-agnostic REST] |
| 67 | X034 | [481, 1125, 781, 1140] | S02 | #FFFFFF | Isolated, network disabled, read-only |
| 68 | X036 | [115, 1126, 335, 1140] | S03 | #FFFFFF | Application data, evidence, |
| 69 | X035 | [977, 1128, 1212, 1143] | S04 | #FFFFFF | Essay scoring, CLO mapping, |
| 70 | X038 | [501, 1144, 761, 1158] | S02 | #FFFDFD | learner role; 256 MB, 3 s timeout |
| 71 | X037 | [134, 1145, 318, 1160] | S03 | #FEFFFF | cached LLM responses |
| 72 | X039 | [955, 1147, 1234, 1163] | S04 | #FEFEFF | tag suggestions, gap explanations |
| 73 | X040 | [66, 570, 338, 589] | None | #222222 | deployment, Docker Compose] |
| 74 | X041 | [1004.0, 1450.0, 1185.0, 1467.0] | S10 | #FFFFFF | OAuth Providers |
| 75 | X042 | [987.0, 1474.0, 1202.0, 1491.0] | S10 | #FFFFFF | [External Software System] |
| 76 | X043 | [1018.5, 1498.0, 1170.5, 1515.0] | S10 | #FFFFFF | Google and GitHub |
| 77 | X044 | [1055.0, 1522.0, 1134.0, 1535.0] | S10 | #FFFFFF | OAuth 2.0 |
| 78 | X045 | [1429.0, 1450.0, 1574.0, 1467.0] | S11 | #FFFFFF | Email Service |
| 79 | X046 | [1395.0, 1474.0, 1610.0, 1491.0] | S11 | #FFFFFF | [External Software System] |
| 80 | X047 | [1380.5, 1498.0, 1624.5, 1511.0] | S11 | #FFFFFF | Password-reset mail via SMTP |
| 81 | X048 | [1413.5, 1518.0, 1591.5, 1535.0] | S11 | #FFFFFF | Mailpit in development |
| 82 | X049 | [900, 1359, 1081, 1376] | None | #222222 | OAuth sign-in [HTTPS] |
| 83 | X050 | [1200, 1329, 1436, 1346] | None | #222222 | Password-reset email [SMTP] |

## Total

11 shapes + 4 dash runs + 9 lines + 9 arrowheads + 50 texts = **83 elements**, each listed exactly once.

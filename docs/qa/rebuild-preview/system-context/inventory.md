# System Context — pre-build element inventory (Round 1 REDO, Stage A)

Generated from `trace.json` (pixel-measured) + `text-content.json`
(content read from original PNG crops). Every element listed exactly
once. Total must be **79 elements**.

Canvas: **1431 x 1061**

## Rectangles (4)

| # | id | x | y | w | h | label |
|---|----|---|---|---|---|-------|
| 1 | R1 Learner | 87 | 96 | 263 | 95 | Learner |
| 2 | R2 Administrator | 1081 | 96 | 263 | 95 | Administrator |
| 3 | R3 LLM Provider | 104 | 865 | 386 | 95 | LLM Provider |
| 4 | R4 legend frame | 392 | 986 | 647 | 56 | (frame; holds System/Actor/Interaction) |

## Ellipse (1)

- **E1** center (715, 468), rx 210, ry 130 (pixel bbox 505..925 x 338..598) — label: DBCAS [645, 454, 788, 484]

## Legend icons (3)

| # | id | bbox (x0,y0,x1,y1) | shape |
|---|----|--------------------|-------|
| 6 | I1 oval | (444, 1000, 486, 1029) | hollow oval |
| 7 | I2 rect | (619, 1000, 660, 1029) | hollow rectangle |
| 8 | I3 arrow | (794, 1009, 881, 1020) | arrow symbol |

## Flows (21 polylines) + arrows (21) + flow labels (21)

One arrowhead per flow. Arrow tip positions measured; triangle approx. 11 px tall x 11 px base; line stroke 2 px.

| # | id | polyline points | arrow tip | label bbox | label |
|---|----|-----------------|-----------|------------|-------|
| 9 + 10 | F01 (line, arrow) | (313, 191) -> (313, 226) -> (699, 226) -> (697, 340) | (697, 340) | (419, 203, 593, 219) | Assessment requests |
| 11 + 12 | F02 (line, arrow) | (732, 340) -> (732, 226) -> (1118, 226) -> (1116, 191) | (732, 340) | (853, 202, 998, 219) | CLOs & Concepts |
| 13 + 14 | F03 (line, arrow) | (287, 191) -> (287, 260) -> (664, 260) -> (662, 344) | (662, 344) | (340, 236, 612, 253) | MCQ / SQL / Conceptual answers |
| 15 + 16 | F04 (line, arrow) | (767, 344) -> (767, 260) -> (1144, 260) -> (1142, 191) | (767, 344) | (916, 236, 997, 250) | Questions |
| 17 + 18 | F05 (line, arrow) | (261, 191) -> (261, 295) -> (629, 295) -> (627, 352) | (627, 351) | (389, 272, 503, 289) | View requests |
| 19 + 20 | F06 (line, arrow) | (802, 352) -> (802, 295) -> (1170, 295) -> (1168, 191) | (802, 351) | (956, 272, 1016, 285) | Rubrics |
| 21 + 22 | F07 (line, arrow) | (235, 191) -> (235, 330) -> (594, 330) -> (593, 364) | (593, 364) | (319, 305, 510, 322) | Authentication requests |
| 23 + 24 | F08 (line, arrow) | (837, 364) -> (837, 330) -> (1196, 330) -> (1194, 191) | (837, 364) | (913, 305, 1121, 322) | Assessment configuration |
| 25 + 26 | F09 (line, arrow) | (209, 191) -> (209, 364) -> (559, 364) -> (558, 384) | (558, 384) | (299, 341, 470, 358) | Registration requests |
| 27 + 28 | F10 (line, arrow) | (191, 191) -> (191, 407) -> (532, 407) | (191, 191) | (282, 382, 440, 395) | Assessment results |
| 29 + 30 | F11 (line, arrow) | (899, 407) -> (1240, 407) -> (1238, 191) | (1238, 191) | (986, 382, 1155, 399) | Learner performance |
| 31 + 32 | F12 (line, arrow) | (157, 191) -> (157, 451) -> (509, 451) | (157, 191) | (225, 426, 443, 443) | Competency profile & gaps |
| 33 + 34 | F13 (line, arrow) | (922, 451) -> (1274, 451) -> (1273, 191) | (1273, 191) | (992, 426, 1205, 443) | Competency gap analytics |
| 35 + 36 | F14 (line, arrow) | (122, 191) -> (122, 494) -> (512, 494) | (122, 191) | (255, 471, 379, 488) | Study guidance |
| 37 + 38 | F15 (line, arrow) | (919, 494) -> (1309, 494) -> (1308, 191) | (1308, 191) | (1017, 471, 1212, 488) | AI mapping suggestions |
| 39 + 40 | F16 (line, arrow) | (226, 867) -> (226, 753) -> (612, 753) -> (610, 580) | (226, 867) | (317, 730, 524, 747) | Gap explanation requests |
| 41 + 42 | F17 (line, arrow) | (296, 867) -> (296, 788) -> (664, 788) -> (662, 593) | (296, 867) | (376, 764, 587, 781) | Essay evaluation requests |
| 43 + 44 | F18 (line, arrow) | (366, 867) -> (366, 822) -> (716, 822) -> (715, 597) | (366, 867) | (412, 799, 672, 816) | CLO/Concept mapping requests |
| 45 + 46 | F19 (line, arrow) | (488, 883) -> (760, 883) -> (758, 595) | (758, 595) | (540, 858, 711, 875) | Mapping suggestions |
| 47 + 48 | F20 (line, arrow) | (488, 915) -> (795, 915) -> (793, 588) | (793, 588) | (545, 891, 740, 908) | Essay evaluation results |
| 49 + 50 | F21 (line, arrow) | (488, 948) -> (830, 948) -> (828, 577) | (828, 577) | (589, 924, 730, 941) | Gap explanations |

Flow labels themselves are counted once more below, in **Texts (29)** — they are referenced (not re-counted) in this table.
## Texts (29)

### Free texts (22 = 1 title + 21 flow labels)

| # | bbox | content |
|---|------|---------|
| 51 | (432, 26, 1001, 60) title | DBCAS System Context Diagram |
| 52 | (853, 202, 998, 219) flow label F02 | CLOs & Concepts |
| 53 | (419, 203, 593, 219) flow label F01 | Assessment requests |
| 54 | (340, 236, 612, 253) flow label F03 | MCQ / SQL / Conceptual answers |
| 55 | (916, 236, 997, 250) flow label F04 | Questions |
| 56 | (389, 272, 503, 289) flow label F05 | View requests |
| 57 | (956, 272, 1016, 285) flow label F06 | Rubrics |
| 58 | (319, 305, 510, 322) flow label F07 | Authentication requests |
| 59 | (913, 305, 1121, 322) flow label F08 | Assessment configuration |
| 60 | (299, 341, 470, 358) flow label F09 | Registration requests |
| 61 | (282, 382, 440, 395) flow label F10 | Assessment results |
| 62 | (986, 382, 1155, 399) flow label F11 | Learner performance |
| 63 | (225, 426, 443, 443) flow label F12 | Competency profile & gaps |
| 64 | (992, 426, 1205, 443) flow label F13 | Competency gap analytics |
| 65 | (255, 471, 379, 488) flow label F14 | Study guidance |
| 66 | (1017, 471, 1212, 488) flow label F15 | AI mapping suggestions |
| 67 | (317, 730, 524, 747) flow label F16 | Gap explanation requests |
| 68 | (376, 764, 587, 781) flow label F17 | Essay evaluation requests |
| 69 | (412, 799, 672, 816) flow label F18 | CLO/Concept mapping requests |
| 70 | (540, 858, 711, 875) flow label F19 | Mapping suggestions |
| 71 | (545, 891, 740, 908) flow label F20 | Essay evaluation results |
| 72 | (589, 924, 730, 941) flow label F21 | Gap explanations |

### Box texts (6)

| # | bbox | content | inside |
|---|------|---------|--------|
| 73 | (167, 134, 274, 155) | Learner | rect R1 Learner |
| 74 | (1116, 134, 1310, 155) | Administrator | rect R2 Administrator |
| 75 | (205, 902, 392, 924) | LLM Provider | rect R3 LLM Provider |
| 76 | (497, 1008, 550, 1023) | System | rect R4 legend frame |
| 77 | (671, 1008, 709, 1020) | Actor | rect R4 legend frame |
| 78 | (898, 1008, 973, 1020) | Interaction | rect R4 legend frame |

### Ellipse text (1)

- **79** (645, 454, 788, 484) — DBCAS

## Total

4 rects + 1 ellipse + 3 legend icons + 21 flows + 21 arrows + 29 texts = **79 elements** (flows/arrows/labels counted per item; 4+1+3+21+21+29 = 79).

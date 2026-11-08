# System Context — Stage A clone report (Round 1 REDO)

**Status: Stage B (content delta) complete 2026-11-09 — pushed, STOPPED for
owner review. Owner said "Clone OK. Proceed to Stage B"; only the content
delta in the Stage B section below was applied. Stage A section kept verbatim
as the clone record.**

Figure: `ProposalDocument_ver1.1_image3.png` (1431 x 1061), rebuilt to
`docs/diagrams/rebuild/system-context/`.

## Pipeline used

1. `scripts/trace_original.py` — pixel measurement of the original PNG →
   `trace.json` (4 rects, 1 ellipse, 3 legend icons, 21 flows with elbows,
   21 arrow tips, 29 text bboxes = 79 elements).
2. `docs/diagrams/rebuild/system-context/text-content.json` — every string
   read from individual 2x crops of the original (viewed).
3. `scripts/make_inventory.py` → `inventory.md` — pre-build inventory, each
   of the 79 elements listed exactly once (owner rule 2).
4. `scripts/calibrate_fonts.py` — PIL Arial ink-bbox calibration against the
   measured bboxes → font plan (title bold 36.5, 21 flow labels regular 18,
   Learner/Administrator bold 29, LLM Provider bold 30, legend regular 17,
   DBCAS bold 42).
5. `scripts/build_system_context.py` — snaps every polyline segment to the
   sampled stroke center of the original, builds arrow triangles from the
   verified formula, places text from measured ink bboxes →
   `system-context.svg`, `system-context.drawio`, `spec.json`.
6. SVG rendered to `system-context.png` with headless Chrome at exactly
   1431 x 1061, copied to `preview/clone.png`; `overlay.png` (50/50 blend),
   `side-by-side.png`, `diff.png` generated on the same canvas/origin.

## Rule 1 — region-by-region written description (all viewed)

Each region is a stacked crop: **original on top, clone below**
(`regions/*.png`). All six regions + the full clone + overlay + diff were
viewed before writing this.

- **r1_topleft (80,20–760,240)** — Original: bold title "DBCAS System
  Context Diagram" centred at top; Learner rectangle top-left with bold
  "Learner"; three arrow shafts rising into the Learner bottom edge at the
  left; five vertical stubs dropping from the Learner bottom edge turning
  into horizontal segments carrying labels "Assessment requests",
  "MCQ / SQL / Conceptual answers", "View requests" (partially in crop).
  Clone: identical rectangle, arrow x-positions, elbow corners, label
  positions and sizes; only sub-pixel glyph-width differences visible.
- **r2_elltop (560,315–880,410)** — Original: the ellipse's top arc with
  nine down-arrowheads landing on / piercing the arc (apexes touching the
  arc), plus two elbow corners entering horizontally from left and right
  then turning down to their arrows. Clone: same arrow x-positions, same
  apex-on-arc contact, same elbows.
- **r3_legend (380,975–1050,1055)** — Original: legend frame containing a
  hollow oval + "System", a hollow rectangle + "Actor", and a shaft-with-
  triangle arrow + "Interaction". Clone: identical layout, icon positions
  and text (icons within ±0.5 px).
- **r4_llm_top (180,845–420,895)** — Original: LLM Provider box top border
  with three down-arrowheads landing exactly on the border. Clone: same
  three arrow positions, same border row.
- **r5_ellbot (575,555–870,625)** — Original: ellipse bottom bowl with
  three verticals descending from the arc (F16/F17/F18 at x≈611/663/715)
  and three up-arrowheads whose apexes touch the arc (F19/F20/F21).
  Clone: identical — also confirmed against raw pixels (verticals at the
  same columns, apex rows within 1 px).
- **r6_admin_right (1180,180–1360,520)** — Original: Administrator box
  bottom/right with three arrow shafts rising into the box edge, elbow
  corners below, and label tails ("…tics" = Competency gap analytics,
  "…ions" = AI mapping suggestions) at the left of the crop. Clone:
  identical arrow x-positions, elbows and label placement.
- **Full canvas** — all 79 elements present exactly once: 4 rects, ellipse,
  3 legend icons, 21 flows, 21 arrowheads, 29 texts; no missing or extra
  element (Stage B boxes/labels deliberately absent).

## Rule 8 — checker

`scripts/check_diagram_geometry.py` parses the SVG itself, computes every
text bbox from the SVG's x / baseline / font-size / font-weight with PIL
Arial metrics, and runs the four required checks:

- (a) all text bboxes listed + fail on any two intersecting
- (b) fail if a text bbox intersects a foreign line segment
      (own-line exemption: horizontal segment 0–14 px below the bbox with
      ≥60 % x-overlap — reported, not silently skipped)
- (c) fail if the label set ≠ expected list (`text-content.json`)
- (d) fail if any element appears twice (type + geometry signature)

**Run 1 — previous broken output from `b51f511`: FAIL (exit 1), 79
problems** (stacked overlapping labels, labels crossing foreign lines,
wrong label set). Full failing output:

```text
rule-8 checker: C:/Users/kudot/AppData/Local/Temp/opencode/old-sc.svg
expected labels: 29 (title + 21 flow labels + 6 box + 1 ellipse)
svg: 34 text elements, 370 line segments, 36 shape elements

== (a) text label bboxes (34) ==
[ 0] (  481.0,   28.0,  950.0,   56.0)  size 30.0  bold     DBCAS System Context Diagram
[ 1] (  183.5,  135.0,  254.5,  150.0)  size 20.0  bold     Learner
[ 2] ( 1146.0,  135.0, 1278.0,  150.0)  size 20.0  bold     Administrator
[ 3] (  667.5,  500.0,  762.5,  520.0)  size 28.0  bold     DBCAS
[ 4] (  236.0,  899.5,  358.0,  913.5)  size 19.0  bold     LLM Provider
[ 5] (  669.5,  899.5,  820.5,  913.5)  size 19.0  bold     OAuth Providers
[ 6] ( 1003.5,  899.5, 1126.5,  913.5)  size 19.0  bold     Email Service
[ 7] (  471.0, 1015.0,  509.0, 1026.0)  size 12.0  regular  System
[ 8] (  590.0, 1015.0,  618.0, 1024.0)  size 12.0  regular  Actor
[ 9] (  741.0, 1015.0,  796.0, 1024.0)  size 12.0  regular  Interaction
[10] (  379.0,  185.0,  471.0,  196.0)  size 12.0  regular  Practice requests
[11] (  379.0,  190.0,  559.0,  201.0)  size 12.0  regular  MCQ / SQL / Conceptual answers
[12] (  378.0,  195.0,  454.0,  206.0)  size 12.0  regular  View requests
[13] (  378.0,  200.0,  505.0,  211.0)  size 12.0  regular  Authentication requests
[14] (  379.0,  205.0,  493.0,  216.0)  size 12.0  regular  Registration requests
[15] (  545.0,  565.0,  649.0,  574.0)  size 12.0  regular  Assessment results
[16] (  546.0,  560.0,  691.0,  571.0)  size 12.0  regular  Competency profile & gaps
[17] (  571.0,  575.0,  654.0,  586.0)  size 12.0  regular  Study guidance
[18] ( 1112.0,  185.0, 1207.0,  196.0)  size 12.0  regular  CLOs & Concepts
[19] ( 1112.0,  190.0, 1165.0,  199.0)  size 12.0  regular  Questions
[20] ( 1112.0,  195.0, 1152.0,  204.0)  size 12.0  regular  Rubrics
[21] ( 1112.0,  200.0, 1226.0,  211.0)  size 12.0  regular  Result flow & settings
[22] (  946.0,  565.0, 1059.0,  576.0)  size 12.0  regular  Learner performance
[23] (  946.0,  560.0, 1088.0,  571.0)  size 12.0  regular  Competency gap analytics
[24] (  945.0,  555.0, 1075.0,  566.0)  size 12.0  regular  AI mapping suggestions
[25] (  681.0,  610.0,  819.0,  621.0)  size 12.0  regular  Gap explanation requests
[26] (  701.0,  610.0,  842.0,  621.0)  size 12.0  regular  Essay evaluation requests
[27] (  721.0,  610.0,  894.0,  621.0)  size 12.0  regular  CLO/Concept mapping requests
[28] (  520.0,  865.0,  635.0,  876.0)  size 12.0  regular  Mapping suggestions
[29] (  520.0,  885.0,  650.0,  896.0)  size 12.0  regular  Essay evaluation results
[30] (  520.0,  920.0,  614.0,  931.0)  size 12.0  regular  Gap explanations
[31] (  791.0,  610.0,  908.0,  621.0)  size 12.0  regular  OAuth sign-in request
[32] (  651.0,  892.0,  741.0,  903.0)  size 12.0  regular  Identity assertion
[33] (  891.0,  610.0, 1007.0,  619.0)  size 12.0  regular  Password-reset email
-- pairwise text intersections --
FAIL: text-text overlap: #5 'OAuth Providers' vs #32 'Identity assertion' (71.5 x 3.5 px)
FAIL: text-text overlap: #10 'Practice requests' vs #11 'MCQ / SQL / Conceptual answers' (92.0 x 6.0 px)
FAIL: text-text overlap: #10 'Practice requests' vs #12 'View requests' (75.0 x 1.0 px)
FAIL: text-text overlap: #11 'MCQ / SQL / Conceptual answers' vs #12 'View requests' (75.0 x 6.0 px)
FAIL: text-text overlap: #11 'MCQ / SQL / Conceptual answers' vs #13 'Authentication requests' (126.0 x 1.0 px)
FAIL: text-text overlap: #12 'View requests' vs #13 'Authentication requests' (76.0 x 6.0 px)
FAIL: text-text overlap: #12 'View requests' vs #14 'Registration requests' (75.0 x 1.0 px)
FAIL: text-text overlap: #13 'Authentication requests' vs #14 'Registration requests' (114.0 x 6.0 px)
FAIL: text-text overlap: #15 'Assessment results' vs #16 'Competency profile & gaps' (103.0 x 6.0 px)
FAIL: text-text overlap: #18 'CLOs & Concepts' vs #19 'Questions' (53.0 x 6.0 px)
FAIL: text-text overlap: #18 'CLOs & Concepts' vs #20 'Rubrics' (40.0 x 1.0 px)
FAIL: text-text overlap: #19 'Questions' vs #20 'Rubrics' (40.0 x 4.0 px)
FAIL: text-text overlap: #20 'Rubrics' vs #21 'Result flow & settings' (40.0 x 4.0 px)
FAIL: text-text overlap: #22 'Learner performance' vs #23 'Competency gap analytics' (113.0 x 6.0 px)
FAIL: text-text overlap: #22 'Learner performance' vs #24 'AI mapping suggestions' (113.0 x 1.0 px)
FAIL: text-text overlap: #23 'Competency gap analytics' vs #24 'AI mapping suggestions' (129.0 x 6.0 px)
FAIL: text-text overlap: #25 'Gap explanation requests' vs #26 'Essay evaluation requests' (118.0 x 11.0 px)
FAIL: text-text overlap: #25 'Gap explanation requests' vs #27 'CLO/Concept mapping requests' (98.0 x 11.0 px)
FAIL: text-text overlap: #25 'Gap explanation requests' vs #31 'OAuth sign-in request' (28.0 x 11.0 px)
FAIL: text-text overlap: #26 'Essay evaluation requests' vs #27 'CLO/Concept mapping requests' (121.0 x 11.0 px)
FAIL: text-text overlap: #26 'Essay evaluation requests' vs #31 'OAuth sign-in request' (51.0 x 11.0 px)
FAIL: text-text overlap: #27 'CLO/Concept mapping requests' vs #31 'OAuth sign-in request' (103.0 x 11.0 px)
FAIL: text-text overlap: #27 'CLO/Concept mapping requests' vs #33 'Password-reset email' (3.0 x 9.0 px)
FAIL: text-text overlap: #31 'OAuth sign-in request' vs #33 'Password-reset email' (17.0 x 9.0 px)

== (b) text bbox vs foreign line segments ==
FAIL: text vs foreign segment: #11 'MCQ / SQL / Conceptual answers' bbox=(379,190,559,201) segment (348.0,200.0)-(410.0,200.0)
FAIL: text vs foreign segment: #11 'MCQ / SQL / Conceptual answers' bbox=(379,190,559,201) segment (410.0,200.0)-(410.0,280.0)
FAIL: text vs foreign segment: #12 'View requests' bbox=(378,195,454,206) segment (348.0,200.0)-(410.0,200.0)
FAIL: text vs foreign segment: #12 'View requests' bbox=(378,195,454,206) segment (410.0,200.0)-(410.0,280.0)
exempt (own line, 0-14px below bbox): #12 'View requests' segment y=205.0 x=348..430
FAIL: text vs foreign segment: #12 'View requests' bbox=(378,195,454,206) segment (430.0,205.0)-(430.0,295.0)
FAIL: text vs foreign segment: #13 'Authentication requests' bbox=(378,200,505,211) segment (410.0,200.0)-(410.0,280.0)
FAIL: text vs foreign segment: #13 'Authentication requests' bbox=(378,200,505,211) segment (348.0,205.0)-(430.0,205.0)
FAIL: text vs foreign segment: #13 'Authentication requests' bbox=(378,200,505,211) segment (430.0,205.0)-(430.0,295.0)
FAIL: text vs foreign segment: #13 'Authentication requests' bbox=(378,200,505,211) segment (348.0,210.0)-(450.0,210.0)
FAIL: text vs foreign segment: #13 'Authentication requests' bbox=(378,200,505,211) segment (450.0,210.0)-(450.0,310.0)
FAIL: text vs foreign segment: #14 'Registration requests' bbox=(379,205,493,216) segment (410.0,200.0)-(410.0,280.0)
FAIL: text vs foreign segment: #14 'Registration requests' bbox=(379,205,493,216) segment (430.0,205.0)-(430.0,295.0)
FAIL: text vs foreign segment: #14 'Registration requests' bbox=(379,205,493,216) segment (348.0,210.0)-(450.0,210.0)
FAIL: text vs foreign segment: #14 'Registration requests' bbox=(379,205,493,216) segment (450.0,210.0)-(450.0,310.0)
exempt (own line, 0-14px below bbox): #14 'Registration requests' segment y=215.0 x=348..470
FAIL: text vs foreign segment: #14 'Registration requests' bbox=(379,205,493,216) segment (470.0,215.0)-(470.0,325.0)
FAIL: text vs foreign segment: #15 'Assessment results' bbox=(545,565,649,574) segment (548.7,576.1)-(543.5,571.6)
FAIL: text vs foreign segment: #18 'CLOs & Concepts' bbox=(1112,185,1207,196) segment (1343.0,192.0)-(1081.0,192.0)
FAIL: text vs foreign segment: #19 'Questions' bbox=(1112,190,1165,199) segment (1343.0,192.0)-(1081.0,192.0)
exempt (own line, 0-14px below bbox): #22 'Learner performance' segment y=575.0 x=915..1100
FAIL: text vs foreign segment: #22 'Learner performance' bbox=(946,565,1059,576) segment (915.0,570.0)-(1120.0,570.0)
FAIL: text vs foreign segment: #23 'Competency gap analytics' bbox=(946,560,1088,571) segment (1081.0,580.0)-(1081.0,320.0)
exempt (own line, 0-14px below bbox): #23 'Competency gap analytics' segment y=570.0 x=915..1120
FAIL: text vs foreign segment: #25 'Gap explanation requests' bbox=(681,610,819,621) segment (817.8,609.4)-(809.3,612.0)
FAIL: text vs foreign segment: #25 'Gap explanation requests' bbox=(681,610,819,621) segment (809.3,612.0)-(800.5,614.4)
FAIL: text vs foreign segment: #25 'Gap explanation requests' bbox=(681,610,819,621) segment (800.5,614.4)-(791.5,616.6)
FAIL: text vs foreign segment: #25 'Gap explanation requests' bbox=(681,610,819,621) segment (791.5,616.6)-(782.4,618.6)
FAIL: text vs foreign segment: #25 'Gap explanation requests' bbox=(681,610,819,621) segment (782.4,618.6)-(773.1,620.3)
FAIL: text vs foreign segment: #25 'Gap explanation requests' bbox=(681,610,819,621) segment (773.1,620.3)-(763.6,621.7)
FAIL: text vs foreign segment: #26 'Essay evaluation requests' bbox=(701,610,842,621) segment (817.8,609.4)-(809.3,612.0)
FAIL: text vs foreign segment: #26 'Essay evaluation requests' bbox=(701,610,842,621) segment (809.3,612.0)-(800.5,614.4)
FAIL: text vs foreign segment: #26 'Essay evaluation requests' bbox=(701,610,842,621) segment (800.5,614.4)-(791.5,616.6)
FAIL: text vs foreign segment: #26 'Essay evaluation requests' bbox=(701,610,842,621) segment (791.5,616.6)-(782.4,618.6)
FAIL: text vs foreign segment: #26 'Essay evaluation requests' bbox=(701,610,842,621) segment (782.4,618.6)-(773.1,620.3)
FAIL: text vs foreign segment: #26 'Essay evaluation requests' bbox=(701,610,842,621) segment (773.1,620.3)-(763.6,621.7)
FAIL: text vs foreign segment: #27 'CLO/Concept mapping requests' bbox=(721,610,894,621) segment (817.8,609.4)-(809.3,612.0)
FAIL: text vs foreign segment: #27 'CLO/Concept mapping requests' bbox=(721,610,894,621) segment (809.3,612.0)-(800.5,614.4)
FAIL: text vs foreign segment: #27 'CLO/Concept mapping requests' bbox=(721,610,894,621) segment (800.5,614.4)-(791.5,616.6)
FAIL: text vs foreign segment: #27 'CLO/Concept mapping requests' bbox=(721,610,894,621) segment (791.5,616.6)-(782.4,618.6)
FAIL: text vs foreign segment: #27 'CLO/Concept mapping requests' bbox=(721,610,894,621) segment (782.4,618.6)-(773.1,620.3)
FAIL: text vs foreign segment: #27 'CLO/Concept mapping requests' bbox=(721,610,894,621) segment (773.1,620.3)-(763.6,621.7)
FAIL: text vs foreign segment: #28 'Mapping suggestions' bbox=(520,865,635,876) segment (620.0,950.0)-(620.0,865.0)
FAIL: text vs foreign segment: #28 'Mapping suggestions' bbox=(520,865,635,876) segment (580.0,880.0)-(580.0,625.0)
FAIL: text vs foreign segment: #28 'Mapping suggestions' bbox=(520,865,635,876) segment (595.0,900.0)-(595.0,625.0)
FAIL: text vs foreign segment: #28 'Mapping suggestions' bbox=(520,865,635,876) segment (600.0,935.0)-(600.0,625.0)
FAIL: text vs foreign segment: #28 'Mapping suggestions' bbox=(520,865,635,876) segment (620.0,907.0)-(620.0,700.0)
FAIL: text vs foreign segment: #29 'Essay evaluation results' bbox=(520,885,650,896) segment (620.0,950.0)-(620.0,865.0)
FAIL: text vs foreign segment: #29 'Essay evaluation results' bbox=(520,885,650,896) segment (595.0,900.0)-(595.0,625.0)
FAIL: text vs foreign segment: #29 'Essay evaluation results' bbox=(520,885,650,896) segment (600.0,935.0)-(600.0,625.0)
FAIL: text vs foreign segment: #29 'Essay evaluation results' bbox=(520,885,650,896) segment (620.0,907.0)-(620.0,700.0)
FAIL: text vs foreign segment: #30 'Gap explanations' bbox=(520,920,614,931) segment (600.0,935.0)-(600.0,625.0)
FAIL: text vs foreign segment: #31 'OAuth sign-in request' bbox=(791,610,908,621) segment (817.8,609.4)-(809.3,612.0)
FAIL: text vs foreign segment: #31 'OAuth sign-in request' bbox=(791,610,908,621) segment (809.3,612.0)-(800.5,614.4)
FAIL: text vs foreign segment: #31 'OAuth sign-in request' bbox=(791,610,908,621) segment (800.5,614.4)-(791.5,616.6)
FAIL: text vs foreign segment: #31 'OAuth sign-in request' bbox=(791,610,908,621) segment (791.5,616.6)-(782.4,618.6)

== (c) label set vs expected list ==
FAIL: missing labels: ['Assessment requests', 'Assessment configuration']
FAIL: unexpected labels: ['OAuth Providers', 'Email Service', 'Practice requests', 'Result flow & settings', 'OAuth sign-in request', 'Identity assertion', 'Password-reset email']
FAIL: distinct label count 34 (svg) != 29 (expected)

== (d) duplicate elements ==
OK: 70 elements, each appears exactly once

RESULT: FAIL (79 problem(s))
```

**Run 2 — new output: PASS (exit 0).** Full output:

```text
rule-8 checker: docs/diagrams/rebuild/system-context/system-context.svg
expected labels: 29 (title + 21 flow labels + 6 box + 1 ellipse)
svg: 29 text elements, 402 line segments, 52 shape elements

== (a) text label bboxes (29) ==
[ 0] (  432.0,   26.0, 1011.0,   60.0)  size 36.5  bold     DBCAS System Context Diagram
[ 1] (  853.0,  202.0,  995.0,  219.0)  size 18.0  regular  CLOs & Concepts
[ 2] (  419.0,  203.0,  590.0,  220.0)  size 18.0  regular  Assessment requests
[ 3] (  340.0,  236.0,  609.0,  253.0)  size 18.0  regular  MCQ / SQL / Conceptual answers
[ 4] (  916.0,  236.0,  995.0,  250.0)  size 18.0  regular  Questions
[ 5] (  389.0,  272.0,  501.0,  289.0)  size 18.0  regular  View requests
[ 6] (  956.0,  272.0, 1015.0,  285.0)  size 18.0  regular  Rubrics
[ 7] (  319.0,  305.0,  506.0,  322.0)  size 18.0  regular  Authentication requests
[ 8] (  913.0,  305.0, 1118.0,  322.0)  size 18.0  regular  Assessment configuration
[ 9] (  299.0,  341.0,  467.0,  358.0)  size 18.0  regular  Registration requests
[10] (  282.0,  382.0,  437.0,  395.0)  size 18.0  regular  Assessment results
[11] (  986.0,  382.0, 1152.0,  399.0)  size 18.0  regular  Learner performance
[12] (  225.0,  426.0,  439.0,  443.0)  size 18.0  regular  Competency profile & gaps
[13] (  992.0,  426.0, 1201.0,  443.0)  size 18.0  regular  Competency gap analytics
[14] (  255.0,  471.0,  377.0,  488.0)  size 18.0  regular  Study guidance
[15] ( 1017.0,  471.0, 1208.0,  488.0)  size 18.0  regular  AI mapping suggestions
[16] (  317.0,  730.0,  520.0,  747.0)  size 18.0  regular  Gap explanation requests
[17] (  376.0,  764.0,  584.0,  781.0)  size 18.0  regular  Essay evaluation requests
[18] (  412.0,  799.0,  667.0,  816.0)  size 18.0  regular  CLO/Concept mapping requests
[19] (  540.0,  858.0,  708.0,  875.0)  size 18.0  regular  Mapping suggestions
[20] (  545.0,  891.0,  737.0,  908.0)  size 18.0  regular  Essay evaluation results
[21] (  589.0,  924.0,  727.0,  941.0)  size 18.0  regular  Gap explanations
[22] (  167.0,  134.0,  271.0,  155.0)  size 29.0  bold     Learner
[23] ( 1116.0,  134.0, 1307.0,  155.0)  size 29.0  bold     Administrator
[24] (  205.0,  902.0,  394.0,  924.0)  size 30.0  bold     LLM Provider
[25] (  497.0, 1008.0,  552.0, 1023.0)  size 17.0  regular  System
[26] (  671.0, 1008.0,  711.0, 1020.0)  size 17.0  regular  Actor
[27] (  898.0, 1008.0,  974.0, 1020.0)  size 17.0  regular  Interaction
[28] (  645.0,  454.0,  788.0,  484.0)  size 42.0  bold     DBCAS
-- pairwise text intersections --
OK: no two text bboxes intersect

== (b) text bbox vs foreign line segments ==
OK: no text bbox intersects a foreign segment (0 own-line exemptions)

== (c) label set vs expected list ==
OK: 29 labels exactly match the expected list

== (d) duplicate elements ==
OK: 81 elements, each appears exactly once

RESULT: PASS (checks a/b/c/d all clean)
```

## Text fidelity (measured: original ink bbox vs clone rendered ink bbox)

Proving images: `diff.png` (red = original-only ink, blue = clone-only
ink, dark = both), `overlay.png`, `regions/*.png`.

| # | label | orig bbox | delta l,t,r,b |
|---|-------|-----------|---------------|
| 0 | DBCAS System Context Diagram | [432, 26, 1001, 60] | +0,+0,-3,-1 |
| 1 | CLOs & Concepts | [853, 202, 998, 219] | +0,+0,-4,-1 |
| 2 | Assessment requests | [419, 203, 593, 219] | +0,+0,-4,+0 |
| 3 | MCQ / SQL / Conceptual answers | [340, 236, 612, 253] | +0,+0,-4,-1 |
| 4 | Questions | [916, 236, 997, 250] | +0,+0,-3,-1 |
| 5 | View requests | [389, 272, 503, 289] | +0,+0,-3,-1 |
| 6 | Rubrics | [956, 272, 1016, 285] | +1,+0,-2,-1 |
| 7 | Authentication requests | [319, 305, 510, 322] | +0,+0,-5,-1 |
| 8 | Assessment configuration | [913, 305, 1121, 322] | +0,+0,-4,-1 |
| 9 | Registration requests | [299, 341, 470, 358] | +1,+0,-4,-1 |
| 10 | Assessment results | [282, 382, 440, 395] | +0,+0,-4,-1 |
| 11 | Learner performance | [986, 382, 1155, 399] | +0,+0,-4,-1 |
| 12 | Competency profile & gaps | [225, 426, 443, 443] | +0,+0,-5,-1 |
| 13 | Competency gap analytics | [992, 426, 1205, 443] | +0,+0,-5,-1 |
| 14 | Study guidance | [255, 471, 379, 488] | +0,+0,-3,-1 |
| 15 | AI mapping suggestions | [1017, 471, 1212, 488] | +0,+0,-5,-1 |
| 16 | Gap explanation requests | [317, 730, 524, 747] | +0,+0,-4,-1 |
| 17 | Essay evaluation requests | [376, 764, 587, 781] | +1,+0,-4,-1 |
| 18 | CLO/Concept mapping requests | [412, 799, 672, 816] | +0,+0,-5,-1 |
| 19 | Mapping suggestions | [540, 858, 711, 875] | +0,+0,-4,-1 |
| 20 | Essay evaluation results | [545, 891, 740, 908] | +1,+0,-4,-1 |
| 21 | Gap explanations | [589, 924, 730, 941] | +0,+0,-4,-1 |
| 22 | Learner | [167, 134, 274, 155] | +0,+0,-4,-1 |
| 23 | Administrator | [1116, 134, 1310, 155] | +0,+0,-5,-1 |
| 24 | LLM Provider | [205, 902, 392, 924] | +0,+0,+2,-1 |
| 25 | System | [497, 1008, 550, 1023] | +0,+0,+1,-1 |
| 26 | Actor | [671, 1008, 709, 1020] | +0,+0,+1,-1 |
| 27 | Interaction | [898, 1008, 973, 1020] | +0,+0,+0,-1 |
| 28 | DBCAS | [645, 454, 788, 484] | +0,+0,+0,-1 |

Every label's top-left corner is within 0–1 px of the original; right
edges land 2–5 px short (see difference 1 below).

## Line / shape fidelity probes (original run vs clone run at same pixels)

| probe | original | clone | delta |
|-------|----------|-------|-------|
| F01 horizontal @ col400 | rows 226–227 | rows 226–227 | 0 |
| F03 horizontal @ col400 | rows 260–261 | rows 260–261 | 0 |
| F10 horizontal @ col300 | rows 407–408 | rows 407–408 | 0 |
| F16 horizontal @ col400 | rows 753–754 | rows 753–754 | 0 |
| F19 horizontal @ col600 | row 883 (1 px) | rows 882–884 | 0 (centre) |
| Learner left border @ row140 | cols 87–88 | cols 87–88 | 0 |
| Learner top border @ col200 | rows 96–97 | rows 96–97 | 0 |
| Learner right border @ row140 | cols 348–349 | cols 348–349 | 0 |
| Administrator right @ row140 | cols 1342–1343 | cols 1342–1343 | 0 |
| LLM top @ col300 | rows 865–866 | rows 865–866 | 0 |
| legend left @ row1010 | cols 392–393 | cols 392–393 | 0 |
| legend bottom @ col700 | row 1042 (1 px) | rows 1042–1043 | +0.5 (see diff 7) |
| ellipse left arc @ row468 | cols 505–506 | cols 505–506 | 0 |
| ellipse right arc @ row468 | cols 924–925 | cols 924–925 | 0 |
| ellipse top @ col715 | rows 338–339 | rows 338–339 | 0 |
| ellipse bottom @ cols708–720 | rows 597–598 | rows 597–598 | 0 |

## Honest remaining differences

1. **Text is 2–5 px narrower on the right edge.** The original's glyphs
   render slightly wider than Arial as rendered by Chrome at the calibrated
   sizes (left/top corners match within 0–1 px, so no label moves onto a
   line — checker (a)/(b) pass). Flow labels are regular 18 px; calibration
   tested bold-17 candidates and rejected them as visually wrong.
2. **Title font size 36.5 px (fractional).** PIL rounds to 37 for
   measurement; Chrome renders 36.5. Rendered title ink 432..998 vs
   original 432..1001 (3 px shorter).
3. **Arrow triangles**: apex = measured tip − 1.5 px along the shaft,
   length 11, half-width 5.5 (verified against raw pixels of F01/F05/F10/
   F16). Original triangles measure base ≈11, height 9.5–11, so some clone
   tips are up to ~1 px longer than the original's shortest ones; apex
   positions are within ≤1 px.
4. **Half-pixel line coordinates** (F07 at y330.5, F17 at y788.5, F18 at
   x715.5) render with a 1 px anti-alias fringe in Chrome where the
   original has a crisp 1–2 px run — the line centre is identical, the
   inked width differs by up to 1 px.
5. **Ellipse parameters** cx 715.5, cy 468.5, rx 209.5, ry 129.5, taken
   from extremal-arc probes (left 506.0 / right 925.0 / top 339.0 /
   bottom 598.0). The tracer's earlier bbox estimate (715, 468, 210, 130)
   was ±1 px; the current values are pixel-exact on all four arcs (table
   above).
6. **Legend icons** are drawn at stroke width 1.5 from measured centres —
   ±0.5 px against the original's icon strokes.
7. **Legend frame bottom border**: clone draws 2 px at y1042.5; the
   original's bottom edge measures as a single 1 px run at y1042 (its
   rendering is thinner there) → up to 1 px extra ink below the bottom
   border. Left/top/right borders match exactly.
8. **Total ink**: original 58 983 dark px, clone 65 974 (overlap 46 031;
   original-only 12 952; clone-only 19 943). The excess is anti-aliasing
   fringes + text rendering — visible as thin red/blue edges in
   `diff.png`, not as displaced geometry (line probes above are 0).
9. **draw.io CLI is not available on this machine** (`where drawio` empty,
   no draw.io install directories found), so `system-context.drawio` is a
   hand-authored mxGraph XML file (orthogonal edges with explicit
   waypoints, Arial ≥ original sizes, original stroke widths). The
   authoritative exact export is `system-context.svg`; `system-context.png`
   was rendered from it with headless Chrome at 1431 × 1061.
10. **Stage B content not applied** (per two-stage rule): Learner still
    reads "Assessment requests", Administrator "Assessment configuration";
    no OAuth Providers / Email Service boxes, 21 flows only.

## Proof images (`docs/qa/rebuild-preview/system-context/`)

- `original.png`, `clone.png` — same canvas, same size, same origin
- `side-by-side.png` — original | clone at 1:1
- `overlay.png` — 50/50 blend (offsets would show as ghosting)
- `diff.png` — red = original-only ink, blue = clone-only ink, dark = both
- `regions/r1..r6*.png` — stacked original/clone crops (rule 1 viewing)
- `inventory.md` — pre-build element inventory (79 elements, each once)
- `checker-old-round1.txt` — checker FAIL on previous broken output
- `checker-new.txt` — checker PASS on this output

## Deliverables (`docs/diagrams/rebuild/system-context/`)

`system-context.drawio`, `system-context.svg`, `system-context.png`,
`spec.json`, `trace.json`, `text-content.json`.

---
---

# System Context — Stage B content delta report (2026-11-09)

**Status: Stage B complete — pushed, STOPPED for owner review.**

Owner approved Stage A ("Clone OK") and ordered Stage B. Only the content
delta below was applied; `scripts/check_stage_b_delta.py` proves every other
element is byte-identical to the Stage A clone.

## Delta applied (only these)

| # | what | before | after |
|---|------|--------|-------|
| 1 | flow label T02 on F01 (Learner → DBCAS) | `Assessment requests` | `Practice requests` |
| 2 | flow label T08 on F08 (Administrator → DBCAS) | `Assessment configuration` | `Result flow & settings` |
| 3 | new actor box, free space bottom right | — | `OAuth Providers` |
| 4 | new actor box, free space bottom right | — | `Email Service` |
| 5 | new flow F22 DBCAS → OAuth Providers | — | `OAuth sign-in request` |
| 6 | new flow F23 OAuth Providers → DBCAS | — | `Identity assertion` |
| 7 | new flow F24 DBCAS → Email Service | — | `Password-reset email` |

Rules honoured:

- **Nothing else moved.** Canvas stays 1431 × 1061 (the free bottom-right
  space was large enough — no enlargement needed); all 4 rects, the ellipse,
  the 4 legend icons, all 21 Stage A flows/arrowheads and 27 of 29 texts are
  byte-identical (delta checker §1). The two renamed labels keep their exact
  ink top-left anchor (419,203) and (913,305) and their size/weight — only
  the string changed.
- **Same style.** New boxes: 2 px black stroke, white fill, 300 × 95 (the
  same 95 px height as Learner/Administrator/LLM Provider), bold centred
  label size **30 ≥** the original box labels 29/29/30. New flow labels
  regular **18 =** the original flow labels. Flows: orthogonal polylines,
  stroke 2, classic filled arrowhead at the target end built with the same
  formula as Stage A.
- **Legend not updated** — correct: boxes are already "Actor", lines +
  arrowheads are already "Interaction"; no new element type appears
  (delta checker §1: legend icons identical).
- **No shrunk/merged text**: all new labels are ≥ the originals' size for
  their kind.

## New geometry (free bottom-right region)

| element | geometry |
|---|---|
| `OAuth Providers` box | rect (1020, 640) 300 × 95; label bold 30 centred at (1170, 687.5) |
| `Email Service` box | rect (1020, 830) 300 × 95; label bold 30 centred at (1170, 877.5) |
| F22 `OAuth sign-in request` | (892.3, 538) → (1170, 538) → (1170, 640); arrow into OAuth box top; label ink (944.7, 544)–(1117.7, 561) |
| F23 `Identity assertion` | (1080, 640) → (1080, 569) → (847.6, 569); arrow onto the DBCAS arc; label ink (897.3, 576)–(1030.3, 593) |
| F24 `Password-reset email` | (915.5, 507) → (1350, 507) → (1350, 782.5) → (1170, 782.5) → (1170, 830); arrow into Email box top; label ink (1047.2, 513)–(1218.2, 526) |

- F22/F23/F24 start/end points lie on the Stage A ellipse
  (cx 715.5, cy 468.5, rx 209.5, ry 129.5) within 0.05 px — same
  attach style as the original flows.
- The three new labels sit 6–8 px **below** their own horizontal run (the
  originals sit above theirs); in this band that is the only placement that
  touches no line at all — checker (b) passes with **0 own-line exemptions**.
- The four stacked horizontals in the band are y 495 (F15, existing),
  507 (F24), 538 (F22), 569 (F23) — ≥ 12 px apart, all clear.

## Rule 8 — checker (expected label set now 34: +2 renamed, +3 flow, +2 box)

`scripts/check_diagram_geometry.py` on the Stage B SVG — **PASS (exit 0)**.
Saved `checker-stage-b.txt`; full output:

```text
rule-8 checker: docs/diagrams/rebuild/system-context/system-context.svg
expected labels: 34 (title + 24 flow labels + 8 box + 1 ellipse)
svg: 34 text elements, 427 line segments, 60 shape elements

== (a) text label bboxes (34) ==
[ 0] (  432.0,   26.0, 1011.0,   60.0)  size 36.5  bold     DBCAS System Context Diagram
[ 1] (  853.0,  202.0,  995.0,  219.0)  size 18.0  regular  CLOs & Concepts
[ 2] (  419.0,  203.0,  556.0,  220.0)  size 18.0  regular  Practice requests
[ 3] (  340.0,  236.0,  609.0,  253.0)  size 18.0  regular  MCQ / SQL / Conceptual answers
[ 4] (  916.0,  236.0,  995.0,  250.0)  size 18.0  regular  Questions
[ 5] (  389.0,  272.0,  501.0,  289.0)  size 18.0  regular  View requests
[ 6] (  956.0,  272.0, 1015.0,  285.0)  size 18.0  regular  Rubrics
[ 7] (  319.0,  305.0,  506.0,  322.0)  size 18.0  regular  Authentication requests
[ 8] (  913.0,  305.0, 1083.0,  322.0)  size 18.0  regular  Result flow & settings
[ 9] (  299.0,  341.0,  467.0,  358.0)  size 18.0  regular  Registration requests
[10] (  282.0,  382.0,  437.0,  395.0)  size 18.0  regular  Assessment results
[11] (  986.0,  382.0, 1152.0,  399.0)  size 18.0  regular  Learner performance
[12] (  225.0,  426.0,  439.0,  443.0)  size 18.0  regular  Competency profile & gaps
[13] (  992.0,  426.0, 1201.0,  443.0)  size 18.0  regular  Competency gap analytics
[14] (  255.0,  471.0,  377.0,  488.0)  size 18.0  regular  Study guidance
[15] ( 1017.0,  471.0, 1208.0,  488.0)  size 18.0  regular  AI mapping suggestions
[16] (  317.0,  730.0,  520.0,  747.0)  size 18.0  regular  Gap explanation requests
[17] (  376.0,  764.0,  584.0,  781.0)  size 18.0  regular  Essay evaluation requests
[18] (  412.0,  799.0,  667.0,  816.0)  size 18.0  regular  CLO/Concept mapping requests
[19] (  540.0,  858.0,  708.0,  875.0)  size 18.0  regular  Mapping suggestions
[20] (  545.0,  891.0,  737.0,  908.0)  size 18.0  regular  Essay evaluation results
[21] (  589.0,  924.0,  727.0,  941.0)  size 18.0  regular  Gap explanations
[22] (  944.7,  544.0, 1117.7,  561.0)  size 18.0  regular  OAuth sign-in request
[23] (  897.3,  576.0, 1030.3,  593.0)  size 18.0  regular  Identity assertion
[24] ( 1047.2,  513.0, 1218.2,  526.0)  size 18.0  regular  Password-reset email
[25] (  167.0,  134.0,  271.0,  155.0)  size 29.0  bold     Learner
[26] ( 1116.0,  134.0, 1307.0,  155.0)  size 29.0  bold     Administrator
[27] (  205.0,  902.0,  394.0,  924.0)  size 30.0  bold     LLM Provider
[28] (  497.0, 1008.0,  552.0, 1023.0)  size 17.0  regular  System
[29] (  671.0, 1008.0,  711.0, 1020.0)  size 17.0  regular  Actor
[30] (  898.0, 1008.0,  974.0, 1020.0)  size 17.0  regular  Interaction
[31] ( 1052.5,  676.5, 1287.5,  698.5)  size 30.0  bold     OAuth Providers
[32] ( 1074.0,  866.5, 1266.0,  888.5)  size 30.0  bold     Email Service
[33] (  645.0,  454.0,  788.0,  484.0)  size 42.0  bold     DBCAS
-- pairwise text intersections --
OK: no two text bboxes intersect

== (b) text bbox vs foreign line segments ==
OK: no text bbox intersects a foreign segment (0 own-line exemptions)

== (c) label set vs expected list ==
OK: 34 labels exactly match the expected list

== (d) duplicate elements ==
OK: 94 elements, each appears exactly once

RESULT: PASS (checks a/b/c/d all clean)
```

## Delta checker — unchanged elements + no crossing

`scripts/check_stage_b_delta.py` (Stage A spec frozen at
`spec-stage-a.json` vs the Stage B spec) — **PASS (exit 0)**. This covers
what rule-8 cannot see: line-vs-line / line-vs-box crossings and the
"nothing moved" rule. Saved `checker-stage-b-delta.txt`; full output:

```text
stage-b delta checker
  stage A: docs/qa/rebuild-preview/system-context/spec-stage-a.json
  stage B: docs/diagrams/rebuild/system-context/spec.json

== (1) Stage A elements unchanged in Stage B ==
OK: 4 Stage A rects identical (position, size, name)
OK: ellipse identical ({'cx': 715.5, 'cy': 468.5, 'rx': 209.5, 'ry': 129.5, 'stroke_width': 2, 'label': 'DBCAS'})
OK: legend icons identical (4 icons - no new element type, legend not updated)
OK: canvas unchanged {'w': 1431, 'h': 1061}
OK: all 21 Stage A flows identical (points, arrow, tip)
OK: 27 Stage A texts unchanged; T02/T08 renamed in place (same ink top-left [419, 203] / [913, 305], same size, same weight)

== (2) Stage B delta inventory ==
added rects (2): OAuth Providers [1020.0, 640.0, 300.0, 95.0], Email Service [1020.0, 830.0, 300.0, 95.0]
added flows (3): F22 (3 pts, arrow at end), F23 (3 pts, arrow at end), F24 (5 pts, arrow at end)
added texts (5): T22 'OAuth sign-in request', T23 'Identity assertion', T24 'Password-reset email', B06 'OAuth Providers', B07 'Email Service'
renamed texts: T02 'Assessment requests' -> 'Practice requests' ; T08 'Assessment configuration' -> 'Result flow & settings'
OK: delta is exactly +2 boxes, +3 flows, +5 labels, 2 renames

== (3) new geometry vs everything else (no crossing) ==
stage A segments: 334 ; stage B segments: 359 ; new: 25
touch (connection point): new rect:OAuth Providers at (1170.0,640.0) on new F22
touch (connection point): new rect:OAuth Providers at (1080.0,640.0) on new F23
touch (connection point): new rect:Email Service at (1170.0,830.0) on new F24
OK: 25 new segments x 334 stage A segments + 300 new-new pairs + 34 texts - 0 crossings (3 endpoint connections)

== (4) new label clearances (nearest foreign segment) ==
T22  'OAuth sign-in request'  bbox=[944.7, 544.0, 1117.7, 561.0]  nearest foreign segment ellipse at 44.1 px
T23  'Identity assertion'     bbox=[897.3, 576.0, 1030.3, 593.0]  nearest foreign segment ellipse at 32.2 px
T24  'Password-reset email'   bbox=[1047.2, 513.0, 1218.2, 526.0]  nearest foreign segment F15 at 18.0 px
B06  'OAuth Providers'        bbox=[1052.5, 676.5, 1287.5, 698.5]  nearest foreign segment F22:arrow at 38.0 px
B07  'Email Service'          bbox=[1074.0, 866.5, 1266.0, 888.5]  nearest foreign segment F24:arrow at 38.0 px
T02  'Practice requests'      bbox=[419, 203, 556, 220]  nearest foreign segment F01 at 7.0 px
T08  'Result flow & settings' bbox=[913, 305, 1083, 322]  nearest foreign segment F08 at 8.5 px

RESULT: PASS (unchanged elements intact, no crossing)
```

The only three "touch" entries are the intended connections: each new flow's
endpoint landing on its box border. The three flow shafts passing through
their own arrowhead triangles are excluded as one visual unit (same as every
original flow).

## Rule 1 — region-by-region written description of the Stage B render

All viewed before writing: full `stage-b.png`, `side-by-side-stage-b.png`,
`overlay-stage-b.png`, nine `regions-stage-b/r*.png` crops and three zooms
(`zoom_stack_lines`, `zoom_box_entry`, `zoom_f23_arrow`).

- **r1_topleft (80,20–760,240)** — Bold centred title "DBCAS System Context
  Diagram"; Learner rectangle top-left with bold "Learner"; three arrow
  shafts rising into the Learner bottom edge; five vertical stubs dropping
  from its bottom edge and turning east into horizontal label runs. The top
  run now reads **"Practice requests"** (renamed, same start x=419, same
  size, 7 px above the F01 line); "MCQ / SQL / Conceptual answers" and the
  rest unchanged. Everything else pixel-identical to Stage A.
- **r2_elltop (560,315–880,410)** — The ellipse's top arc with nine
  down-arrowheads landing on / piercing the arc and elbow corners entering
  horizontally from both sides. Identical to Stage A; no new line reaches
  this region (nearest new geometry ≥ 97 px below).
- **r3_legend (380,975–1050,1055)** — Legend frame with hollow oval
  "System", hollow rectangle "Actor", shaft-with-triangle arrow
  "Interaction" — identical, not updated (no new element type).
- **r4_llm_top (180,845–420,895)** — LLM Provider box top border with three
  down-arrowheads landing exactly on the border. Identical; no new geometry
  within 450 px.
- **r5_ellbot (575,555–870,625)** — Ellipse bottom bowl with the three
  original verticals descending from the arc (F16/F17/F18) and the three
  original up-arrowheads touching the arc (F19/F20/F21 at x≈758/793/828),
  **plus the new F23 arrowhead at the right edge**: its line arrives from the
  east and the left-pointing arrowhead lands on the arc at (847.6, 569),
  about 15 px up-slope from F21's arrowhead — clearly separated, no overlap
  (confirmed at 4× in `zoom_f23_arrow.png`).
- **r6_admin_right (1180,180–1360,520)** — Administrator box bottom with
  four vertical shafts rising into it (F08/F11/F13/F15 corners at x1195 /
  1238 / 1273 / 1308) and label tails at the left ("…ics" = Competency gap
  analytics, "…ions" = AI mapping suggestions). **New**: the "…email" tail of
  "Password-reset email" and the new F24 line at y507 running east *below*
  the ends of those shafts (they stop at y330.5/408/451.5/495) and turning
  south at x1350 — passes under, never crosses, the existing geometry.
- **r7_new_flows (840,480–1431,700)** — The whole new stack: F15's line
  (y495) at the top, then F24's line (y507) with "Password-reset email"
  6 px below it, F22's line (y538) with "OAuth sign-in request" below it,
  F23's line (y569) with its arrowhead on the arc at the left and "Identity
  assertion" below it; F22's elbow dropping at x1170 with the arrowhead into
  the OAuth Providers box top; F23's plain vertical leaving the box top at
  x1080; the OAuth Providers box top edge. Four parallel horizontals with
  clear white gaps; no label touches any line.
- **r8_new_boxes (980,600–1431,950)** — `OAuth Providers` box
  (1020,640,300×95) with F22's arrowhead on its top edge at x1170 and F23's
  line rising from x1080; between the boxes F24's line runs west at y782.5
  (47 px below the OAuth box, 47 px above the Email box) and turns south at
  x1170 with an arrowhead into the `Email Service` box top
  (1020,830,300×95). Both boxes: same 95 px height, 2 px stroke, white
  fill, bold 30 centred label as the original actor boxes.
- **r9_renamed_admin (880,180–1360,345)** — Administrator box bottom with
  shafts rising into it; four label runs with elbow corners: "CLOs &
  Concepts", "Questions", "Rubrics" and the renamed **"Result flow &
  settings"** (same start x=913, 8.5 px above the F08 line at y330.5).
  Lines and positions identical to Stage A.
- **zoom_stack_lines (860,488–1400,606 @2×)** — proves the line/label ladder
  y495 → y507 → label → y538 → label → y569 → label with white gaps
  everywhere; nothing touches.
- **zoom_box_entry (1100,600–1420,850 @2×)** — F22's arrowhead into the
  OAuth box top, the box's right border, F24's vertical at x1350, the y782.5
  jog and the arrowhead into the Email box top.
- **zoom_f23_arrow (740,545–900,625 @4×)** — the three original up-arrowheads
  and the new F23 arrowhead landing on the arc with clear separation.
- **Full canvas** — 34 texts, 24 flows, 6 rects, ellipse, 4 legend icons;
  every element appears exactly once (rule-8 (c)/(d)).

## Difference overlay (Stage B onto Stage A, differences only)

`overlay-stage-b.png` — black = ink present in both renders, **red = Stage A
only**, **blue = Stage B only**, white = background in both. Viewed: the only
red ink is the two old labels ("Assessment requests", "Assessment
configuration"); the only blue ink is the two new boxes, the three new flows
with their arrowheads and the five new labels. 14 771 changed pixels total
(1 102 A-only, 13 669 B-only); every other pixel is identical — nothing else
in the figure changed.

## Honest notes (Stage B)

1. **Renamed labels are left-anchored, not re-centred.** Both keep their
   original ink top-left (419,203 / 913,305) per the "do not move" rule, so
   the shorter new strings end 37/38 px earlier and sit ~18 px left of their
   line's centre (the originals were centred over their lines). Left/top
   edges, size, weight and the 7/8.5 px gap to their own line are unchanged.
2. **New labels sit below their lines** (the originals sit above): the three
   new flows share the band between F15 (y495) and the ellipse's right side;
   placing the labels below each line is what keeps ≥ 6 px clearance from
   every existing line. Checker (b) passes with 0 exemptions.
3. **draw.io CLI is still unavailable on this machine**, so
   `system-context.drawio` is hand-authored mxGraph written by
   `scripts/build_system_context_stage_b.py` (orthogonal edges + waypoints,
   Arial ≥ original sizes, same stroke widths). Authoritative export is the
   SVG; the PNG was rendered from it with headless Chrome at exactly
   1431 × 1061.
4. **Anti-aliasing only**: text is rendered with Chrome subpixel AA, so new
   glyph edges carry ±1 px colour fringes; geometry is exact (checker b: 0
   intersections).

## Proof images (`docs/qa/rebuild-preview/system-context/`)

- `stage-b.png` — Stage B render, same canvas/origin as `clone.png`
- `side-by-side-stage-b.png` — Stage A clone | Stage B at 1:1
- `overlay-stage-b.png` — difference overlay (red = A only, blue = B only)
- `regions-stage-b/r1..r9*.png` + `zoom_*.png` — region crops (rule 1)
- `checker-stage-b.txt` — rule-8 checker PASS (34 labels)
- `checker-stage-b-delta.txt` — delta checker PASS (nothing moved, 0 crossings)
- `spec-stage-a.json`, `stage-a.svg` — frozen Stage A inputs for the delta
  comparison

## Deliverables (Stage B)

`docs/diagrams/rebuild/system-context/` — `system-context.drawio`,
`system-context.svg`, `system-context.png`, `spec.json`, `text-content.json`
(updated with the 2 renames + 5 new labels). `trace.json` stays the Stage A
pixel-measurement record. Build: `scripts/build_system_context_stage_b.py`;
checkers: `scripts/check_diagram_geometry.py`,
`scripts/check_stage_b_delta.py`; previews: `scripts/make_stage_b_previews.py`.

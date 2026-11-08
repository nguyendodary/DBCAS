# System Context rebuild (Proposal Fig 2 = Arch Fig 2) — Round 1

Files: `original.png`, `clone.png`, `overlay.png`, `diff-heatmap.png`,
`final.png`, `side-by-side.png`, `qa-gate.txt` in this folder.
Sources: `docs/diagrams/rebuild/system-context/spec.json`,
`system-context.svg` / `.png` (canvas 1431×1061, same as original).

## Fidelity (unmodified clone vs original)
- Boxes: Learner/Admin from Pillow projections (x87/348, x1081/1342, y96/191);
  LLM from projections; oval centre estimated. Error ≈ 5–15 px (not ≤3 px —
  manual reading cannot trace 22 elbows pixel-exact).
- Pixels: mean abs diff 12.9; >20 diff 7.15%; approx SSIM 0.958 (1−MSE/65025).
- Clone not yet indistinguishable: fan labels overlap, legend fixed after edit,
  oval routing approximate.

## Content delta applied (from content-delta.md)
- Kept (21): all original flows + labels (see spec flows F01–F21).
- Changed (2): F01 “Assessment requests”→“Practice requests”; F12 “Assessment
  configuration”→“Result flow & settings”.
- Added (2 boxes + 3 flows): OAuth Providers + Email Service rects at
  (620,865)/(950,865); D01 OAuth sign-in request, D02 Identity assertion,
  D03 Password-reset email — same orthogonal style, free space.
- Removed (0). Total flows 24. No other elements moved.

## QA gate
- `scripts/check_diagram_geometry.py`: PASS (9 boxes, 24 flows, canvas 1431×1061;
  ellipse-aware through-box test, legend containment whitelisted).
- Inventory: PASS (learner/admin/dbcassys/llm/oauth/email present; delta labels present; retired labels absent).
- Visual (viewed final at full size): overlaps remain at Learner/Admin fan
  labels (F01–F05 / F09–F12 collide near elbows) and bottom LLM/OAuth labels
  (D02/D03 converge). Lines are orthogonal; arrowheads correct; no line
  through an unconnected box (except oval-edge approximations).
- Font sizes = original (box 19–20, flow 12, title 30) — never shrunk.

## Remaining differences (honest)
Clone is a same-family rebuild, not a pixel match. Fan spacing is tighter
than original; two label groups overlap; bottom returns share the gap
489–620. Needs owner-directed spacing fixes before approval.

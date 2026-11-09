# Rebuilt diagram approval preview — index (owner fix round, 2026-11-09)

Owner gate: **review the final images below before any image is replaced in a
`.docx`.** No image in `docs/academic/*_ver1.2.docx` has been replaced.
Each figure has a measured Stage A clone, the owner-fix render, and the rule-8
checker evidence (PASS on the real build, FAIL on a deliberately broken copy).
Canvas sizes are stated per figure; four figures deliberately grew to fit
owner-added content or margins.

| # | Figure | Original | Stage A clone | Final | Side-by-side (original vs final) | Overlay | Diff | Checker PASS | Broken FAIL |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | System Context (Proposal Fig 2 = Arch Fig 2) | [original](system-context/original.png) | [clone](system-context/clone.png) | [final](system-context/final.png) | [side-by-side](system-context/side-by-side-final.png) | [overlay](system-context/overlay-final.png) | [diff](system-context/diff.png) | [34 labels](system-context/checker-stage-b.txt) | [179 problems](system-context/checker-stage-b-broken.txt) |
| 2 | Use Case (Arch Fig 1) | [original 3000×3300](use-case/original-source.png) | [clone](use-case/clone.png) | [final 3120×3300](use-case/final.png) | [side-by-side](use-case/side-by-side-final.png) | [overlay](use-case/overlay-final.png) | [diff](use-case/diff.png) | [27 labels / 102 elements](use-case/checker-pass-f1.txt) | [120 problems](use-case/checker-broken-f1.txt) |
| 3 | Container (Arch Fig 3) | [original](container/original.png) | [clone](container/clone.png) | [final 1780×1645](container/final.png) | [side-by-side](container/side-by-side-final.png) | [overlay](container/overlay-final.png) | [diff](container/diff.png) | [59 labels / 269 elements](container/checker-pass-fix.txt) | [193 problems](container/checker-broken-fix.txt) |
| 4 | Allocation (Arch Fig 6) | [original](allocation/original.png) | [clone](allocation/clone.png) | [final 1725×1600](allocation/final.png) | [side-by-side](allocation/side-by-side-final.png) | [overlay](allocation/overlay-final.png) | [diff](allocation/diff.png) | [50 labels / 219 elements](allocation/checker-pass-fix.txt) | [109 problems](allocation/checker-broken-fix.txt) |
| 5 | Module View (Arch Fig 5) | [original](module/original.png) | [clone](module/clone.png) | [final](module/final.png) | [side-by-side](module/side-by-side.png) | [overlay](module/overlay.png) | [diff](module/diff.png) | [58 labels / 117 elements](module/checker-stage-b.txt) | [272 problems](module/checker-stage-b-broken.txt) |
| 6 | Logical 4-tier (Proposal Fig 3) | [original](logical/original.png) | [clone](logical/clone.png) | [final](logical/final.png) | [side-by-side](logical/side-by-side.png) | [overlay](logical/overlay.png) | [diff](logical/diff.png) | [37 labels / 101 elements](logical/checker-stage-b.txt) | [192 problems](logical/checker-stage-b-broken.txt) |
| 7 | Evaluation Pipeline (Proposal Fig 4) | [original](pipeline/original.png) | [clone](pipeline/clone.png) | [final](pipeline/final.png) | [side-by-side](pipeline/side-by-side-final.png) | [overlay](pipeline/overlay-final.png) | [diff](pipeline/diff-final.png) | [41 labels / 223 elements](pipeline/checker-stage-b.txt) | [233 problems](pipeline/checker-stage-b-broken.txt) |
| 8a | Component page 1/2 (Arch Fig 4) | [original](component/original.png) | [clone](component/clone.png) | [final 1400×980](component/final-08a.png) | [side-by-side](component/side-by-side-final-08a.png) | [overlay](component/overlay-final-08a.png) | [diff](component/diff-final-08a.png) | [67 labels / 415 elements](component/checker-final-08a.txt) | [343 problems](component/checker-08a-broken.txt) |
| 8b | Component page 2/2 (Arch Fig 4) | [original](component/original.png) | [clone](component/clone.png) | [final 1400×980](component/final-08b.png) | [side-by-side](component/side-by-side-final-08b.png) | [overlay](component/overlay-final-08b.png) | [diff](component/diff-final-08b.png) | [54 labels / 341 elements](component/checker-final-08b.txt) | [286 problems](component/checker-08b-broken.txt) |
| 9 | ERD Chen (Arch Fig 7 = DB Fig 1) | [original](erd/original.png) | [clone](erd/stage-a/clone.png) | [final 4300×1677](erd/final.png) | [side-by-side](erd/side-by-side-final.png) | [overlay](erd/overlay-final.png) | [diff](erd/diff-final.png) | [139 labels / 388 elements](erd/checker-final.txt) | [295 problems](erd/checker-final-broken.txt) |
| 10 | TRD crow's foot (Arch Fig 8 = DB Fig 2) | [original](trd/stage-b/original.png) | [clone](trd/stage-a/final.png) | [5-page contact sheet](trd/final-contact-sheet.png) | [page 1 side-by-side](trd/stage-b/side-by-side-original-page1.png) | [page 1 overlay](trd/stage-b/overlay-original-page1.png) | [page 1 diff](trd/stage-b/diff-original-page1.png) | [5 pages PASS + 59/59 FK verifier](trd/index.md) | [525 problems](trd/checker-b-1-broken.txt) |

The TRD is one figure split into five consecutive pages because 293 columns
do not fit legibly on one 3440×2080 canvas. Per-page final images:
[trd-1](trd/stage-b/page-1/clone.png), [trd-2](trd/stage-b/page-2/clone.png),
[trd-3](trd/stage-b/page-3/clone.png), [trd-4](trd/stage-b/page-4/clone.png),
[trd-5](trd/stage-b/page-5/clone.png). Captions:
Architecture `Figure 8. Table Relationship Diagram (1/5)` … `(5/5)`;
Database `Figure 2: Table Relationship Diagram (1/5)` … `(5/5)`.

The Component figure is one logical figure split into two pages because the
single 2361×1423 page printed body text at 4.74–6.40 pt in Word. Each page
is 1400×980 px at 9.15 in wide; minimum printed text is **9.41 pt** on 8a and
**8.00 pt** on 8b. Proposed captions are in
[`component/caption-proposal.md`](component/caption-proposal.md).

## Checker results (measured)

| Figure | Expected labels | Text/text | Text/foreign line | Elements once | Broken build |
| --- | ---: | ---: | ---: | ---: | --- |
| System Context | 34 | 0 | 0 | 94 | FAIL 179 |
| Use Case | 27 | 0 | 0 | 102 | FAIL 120 |
| Container | 59 | 0 | 0 | 269 | FAIL 193 |
| Allocation | 50 | 0 | 0 | 219 | FAIL 109 |
| Module | 58 | 0 | 0 | 117 | FAIL 272 |
| Logical | 37 | 0 | 0 | 101 | FAIL 192 |
| Pipeline | 41 | 0 | 0 | 223 | FAIL 233 |
| Component 8a / 8b | 67 / 54 | 0 | 0 | 415 / 341 | FAIL 343 / 286 |
| ERD | 139 | 0 | 0 | 388 | FAIL 295 |
| TRD page 1 / 2 / 3 / 4 / 5 | 157 / 178 / 158 / 174 / 170 | 0 | 0 | 167 / 176 / 143 / 149 / 110 shapes | FAIL 525 / 625 / 490 / 562 / 559 |

Stage A→Stage B / fix delta checks prove the unchanged elements are intact:
[System Context](system-context/checker-stage-b-delta.txt),
[Use Case](use-case/checker-f1-delta.txt),
[Container](container/checker-delta-fix.txt),
[Allocation](allocation/checker-delta-fix.txt),
[Module](module/delta-stage-b.txt),
[Logical](logical/delta-stage-b.txt),
[Pipeline](pipeline/delta-f4.txt),
[Component split](component/delta-split-f4.txt),
[ERD](erd/delta-final.txt).

TRD content/FK verifier: **PASS — 59/59 FKs exactly once** (29 same-page
crow's-foot connectors + 30 cross-page stub pairs / 60 labels), 41 tables,
293 columns, 19 migrations, no segment through a card, no dangling endpoint
([verify-stage-b.txt](trd/verify-stage-b.txt)).

ERD evidence: [docs/qa/erd-evidence.md](../erd-evidence.md) — 24 original
relationships kept, 0 removed, 4 added (`updates`, `pools`, `versions`,
`uses`), all with real FKs.

## Remaining visual differences (honest list)

- Arial/Chrome rasterisation differs from the original font: text right
  edges and word positions differ by roughly 1–4 px; letter-spacing matches
  the measured band widths.
- Arrowheads and anti-aliased strokes differ by 0–1 px; dash phase differs
  by ±1 px on dashed boundaries.
- Use Case: the Administrator label now has a 146 px right margin; the
  3120×3300 canvas is 120 px wider than the original, so the Word height
  scales to 6.45 in at 6.10 in width (content unchanged).
- Container: boxes grew downward; the OAuth/Email boxes are in the added
  right/bottom area. Smallest text-to-border margin is 7 px. The
  password-reset/OAuth routes cross only the existing LLM diagonal and the
  dashed boundary (no unconnected box).
- Allocation: the Docker-capable Host title/bracket are back to 21/20 px;
  the HTTPS line no longer crosses the title; new OAuth/Email nodes sit in
  the added margin.
- Module: "Attempt / Evidence Repository" is three lines at 53.5 px side
  padding; font size unchanged.
- Logical: bottom frame edges are continuous; only the original top
  title-tab cut-outs remain. Administrator description has 12.9 px spec /
  12.5 px rendered inner padding at 34 px.
- Pipeline: the approved footer is two 20 px lines (164 chars measure
  1577 px); margins 204.5/359 px. Bank→plan connector is solid.
- Component: two-page split; Database is repeated on 8b as the shared sink.
  Grading & Evaluation Service is 300×185 with a 25 px body grid.
- ERD: 21 entities, 28 diamonds (24 original + 4 FK-backed additions),
  canvas 4300×1677; original left 3251 px is byte-identical in position.
  AssessmentConcept is a legacy junction attached to the retained `targets`
  diamond with a short association, not a second relationship.
- TRD: five pages; 24 px row stubs are ~4.7 pt at 9.5 in (full-page/A3
  annotation), card names 6.3 pt; no card uses `+N more`.

## Pending human decisions

1. **Use Case UC19/UC20** — the owner's Admin-nav review found `Hệ thống`
   is already UC09; `Duyệt bài` (grading review/publish) is **not** covered
   by UC09/UC10/UC11. Proposed `UC20 Review and publish human-verified
   results`; `UC19 Manage interface preferences` is the other verified
   learner capability but not an Admin-nav item. Nothing added silently.
2. **Component two-page split captions** — proposed in
   `component/caption-proposal.md`; needs acceptance before Word insertion.
3. **TRD split captions** — `(1/5)`…`(5/5)` proposed; needs acceptance.

## Resolved in this round

- Container/Allocation OAuth+Email nodes: added with labelled API/application
  edges; no longer pending.
- ERD 21-vs-24 concern: all 24 original relationships restored; 4 FK-backed
  additions; now 28 diamonds, not 21.
- Use Case Administrator label: full word with 146 px right margin.
- Module repository padding, Logical frame edges, Pipeline title/footer/
  solid flow, Component 5-line service and 7 pt legibility: fixed.

## Verification status

- `scripts/check_rebuild_figures.py` — PASS (canvas growth allowed for
  02/03/04/09; Component split pages checked explicitly).
- `npm run docs:check` — pending final run after this index update.
- No `.docx` media was replaced. The three v1.2 packages still contain their
  previous images until the owner replies **“diagrams approved”**.

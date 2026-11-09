# Rebuilt diagram approval preview — index (2026-11-09)

Owner gate: **review the final images below before any image is replaced in a
`.docx`.** No image in `docs/academic/*_ver1.2.docx` has been replaced yet.
Each figure has a measured Stage A clone, a Stage B content-delta render and
the rule-8 checker evidence (PASS on the real build, FAIL on a deliberately
broken copy). Canvas sizes are the original pixel sizes.

| # | Figure | Original | Stage A clone | Stage B final | Side-by-side (original \| final) | Overlay (original vs final) | Diff | Checker PASS | Broken FAIL |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | System Context (Proposal Fig 2 = Arch Fig 2) | [original](system-context/original.png) | [clone](system-context/clone.png) | [final](system-context/final.png) | [side-by-side](system-context/side-by-side-final.png) | [overlay](system-context/overlay-final.png) | [diff](system-context/diff.png) | [34 labels](system-context/checker-stage-b.txt) | [179 problems](system-context/checker-stage-b-broken.txt) |
| 2 | Use Case (Arch Fig 1) | [original](use-case/original.png) | [clone](use-case/clone.png) | [final](use-case/final.png) | [side-by-side](use-case/side-by-side-final.png) | [overlay](use-case/overlay-final.png) | [diff](use-case/diff.png) | [27 labels / 102 elements](use-case/checker-pass-stage-b.txt) | [120 problems](use-case/checker-broken-stage-b.txt) |
| 3 | Container (Arch Fig 3) | [original](container/original.png) | [clone](container/clone.png) | [final](container/final.png) | [side-by-side](container/side-by-side-final.png) | [overlay](container/overlay-final.png) | [diff](container/diff.png) | [49 labels / 253 elements](container/checker-pass-stage-b.txt) | [160 problems](container/checker-broken-stage-b.txt) |
| 4 | Allocation (Arch Fig 6) | [original](allocation/original.png) | [clone](allocation/clone.png) | [final](allocation/final.png) | [side-by-side](allocation/side-by-side-final.png) | [overlay](allocation/overlay-final.png) | [diff](allocation/diff.png) | [39 labels / 203 elements](allocation/checker-pass-stage-b.txt) | [87 problems](allocation/checker-broken-stage-b.txt) |
| 5 | Module View (Arch Fig 5) | [original](module/original.png) | [clone](module/clone.png) | [final](module/final.png) | [side-by-side](module/side-by-side.png) | [overlay](module/overlay.png) | [diff](module/diff.png) | [57 labels / 116 elements](module/checker-stage-b.txt) | [268 problems](module/checker-stage-b-broken.txt) |
| 6 | Logical 4-tier (Proposal Fig 3) | [original](logical/original.png) | [clone](logical/clone.png) | [final](logical/final.png) | [side-by-side](logical/side-by-side.png) | [overlay](logical/overlay.png) | [diff](logical/diff.png) | [37 labels / 105 elements](logical/checker-stage-b.txt) | [192 problems](logical/checker-stage-b-broken.txt) |
| 7 | Evaluation Pipeline (Proposal Fig 4) | [original](pipeline/original.png) | [clone](pipeline/clone.png) | [final](pipeline/final.png) | [side-by-side](pipeline/side-by-side-final.png) | [overlay](pipeline/overlay-final.png) | [diff](pipeline/diff-final.png) | [40 labels / 222 elements](pipeline/checker-stage-b.txt) | [205 problems](pipeline/checker-stage-b-broken.txt) |
| 8 | Component (Arch Fig 4) | [original](component/original.png) | [clone](component/clone.png) | [final](component/final.png) | [side-by-side](component/side-by-side-final.png) | [overlay](component/overlay-final.png) | [diff](component/diff-final.png) | [112 labels / 692 elements](component/checker-stage-b.txt) | [546 problems](component/checker-stage-b-broken.txt) |
| 9 | ERD Chen (Arch Fig 7 = DB Fig 1) | [original](erd/original.png) | [clone](erd/stage-a/clone.png) | [final](erd/final.png) | [side-by-side](erd/side-by-side-final.png) | [overlay](erd/overlay-final.png) | [diff](erd/diff-final.png) | [103 labels / 262 elements](erd/checker-final.txt) | [302 problems](erd/checker-stage-b-broken.txt) |
| 10 | TRD crow's foot (Arch Fig 8 = DB Fig 2) | [original](trd/stage-b/original.png) | [clone](trd/stage-a/final.png) | [final contact sheet](trd/final-contact-sheet.png) | [page 1 side-by-side](trd/stage-b/side-by-side-original-page1.png) | [page 1 overlay](trd/stage-b/overlay-original-page1.png) | [page 1 diff](trd/stage-b/diff-original-page1.png) | [5 pages PASS + FK verifier](trd/index.md) | [549 problems](trd/checker-b-broken.txt) |

The TRD is one figure split into five consecutive pages because 293 columns
do not fit legibly on one 3440×2080 canvas. Per-page final images:
[trd-1](trd/stage-b/page-1/clone.png), [trd-2](trd/stage-b/page-2/clone.png),
[trd-3](trd/stage-b/page-3/clone.png), [trd-4](trd/stage-b/page-4/clone.png),
[trd-5](trd/stage-b/page-5/clone.png). Captions proposed for the documents:
Architecture `Figure 8. Table Relationship Diagram (1/5)` … `(5/5)`;
Database `Figure 2: Table Relationship Diagram (1/5)` … `(5/5)`.

## Checker results (measured)

| Figure | Expected labels | Text/text | Text/foreign line | Elements once | Broken build |
| --- | ---: | ---: | ---: | ---: | --- |
| System Context | 34 | 0 | 0 | 94 | FAIL 179 |
| Use Case | 27 | 0 | 0 | 102 | FAIL 120 |
| Container | 49 | 0 | 0 | 253 | FAIL 160 |
| Allocation | 39 | 0 | 0 | 203 | FAIL 87 |
| Module | 57 | 0 | 0 | 116 | FAIL 268 |
| Logical | 37 | 0 | 0 | 105 | FAIL 192 |
| Pipeline | 40 | 0 | 0 | 222 | FAIL 205 |
| Component | 112 | 0 | 0 | 692 | FAIL 546 |
| ERD | 103 | 0 | 0 | 262 | FAIL 302 |
| TRD page 1 / 2 / 3 / 4 / 5 | 157 / 178 / 158 / 174 / 170 | 0 | 0 | 170 / 204 / 168 / 191 / 169 shapes | FAIL 549 |

Stage A→Stage B delta checks prove the unchanged elements are intact:
[Use Case](use-case/checker-stage-b-delta.txt),
[Container](container/checker-stage-b-delta.txt),
[Allocation](allocation/checker-stage-b-delta.txt),
[System Context](system-context/checker-stage-b-delta.txt).

TRD content/FK verifier: **PASS** — 41 tables, 293 columns, 59 FKs,
19 migrations, 29 same-page crow's-foot connectors, 30 cross-page FKs,
60 labelled stubs, no segment through a card, no text outside the canvas
([verify-stage-b.txt](trd/verify-stage-b.txt)).

## Remaining visual differences (honest list)

- Arial/Chrome rasterisation differs from the original font: text right
  edges and word positions differ by roughly 1–4 px; letter-spacing matches
  the measured band widths. This is present in every figure.
- Arrowheads and anti-aliased strokes differ by 0–1 px; dash phase differs
  by ±1 px on dashed boundaries.
- Use Case: the UC11 association line is opened at the “Administrator” label
  (rule-8 requirement); actor leg tips differ by 1–2 px.
- Container: the SPA box now has five lines because the exact version string
  cannot fit one 482 px line at the original font size; no text was shrunk.
- Logical: the subtitle is upright because the rule-8 metric set supports
  regular/bold; the original is italic.
- Module: long labels use measured negative tracking (never a smaller font).
- Pipeline: long body text wraps at the same font size; box/arrow geometry
  is unchanged.
- ERD: 20 diamonds (15 core + 5 legacy FK-backed relations) instead of the
  original 24; non-core entities stay in the TRD. Composite keys use larger
  ellipses so they remain legible.
- TRD: five pages are a deliberate split; the page-1 comparison is a
  layout-grammar comparison (21 cards vs 41 cards), not an identity claim.
- `.drawio` files are hand-authored mxGraph because the draw.io CLI is not
  available on this machine.

## Pending human decisions (do not guess)

1. **Container / Allocation Email + OAuth nodes**: the verified content delta
   marks them as evidence-backed but optional. They were **not added** because
   the original 8-box/8-node composition has no free block without moving
   existing elements. The context diagram already shows both external systems.
2. **Use Case UC19/UC20**: the real Settings and grading-review flows exist,
   but the figure keeps the original 18-use-case baseline. Add only if the
   owner lifts that baseline.
3. **TRD split captions**: the proposed `(1/5)`…`(5/5)` captions must be
   accepted before the `.docx` figure/table lists are updated.

## Verification status

- `scripts/check_rebuild_figures.py` — PASS (see `npm run docs:check`).
- `npm run docs:check` — includes the new figure gate; all diagrams and
  documents still match the schema/Compose/OpenAPI sources.
- No `.docx` media was replaced. The three v1.2 packages still contain their
  previous images until the owner replies **“diagrams approved”**.

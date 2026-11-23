# Diagram reproduction proof

Run:

```bash
python docs/submission/tools/reproduce_trd1.py
```

It regenerates the frozen 41-table TRD page 1 from `docs/diagrams/rebuild/trd/spec.json`
into `docs/submission/tools/out/reproduce-trd1/` and compares it with
`docs/diagrams/rebuild/trd/trd-1.png` using headless Chrome at 3440x2080.

Result on 2026-11-23:

- canvas: 3440 x 2080, 7,155,200 pixels;
- changed pixels with channel difference > 8: **0**;
- mean absolute channel difference: **0.0**;
- `pair.png` (before/after) and `diff.png` are produced in the output directory.

The 67-card continuation generator (`trd67.py`) reuses the same card grammar
and style values; its six new pages are validated by `check_diagrams.py`
(67 tables, 561 columns, 122 FKs, 28 migrations, 11 pages).

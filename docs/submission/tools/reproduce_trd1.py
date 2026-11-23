# -*- coding: utf-8 -*-
"""Reproduce a shipped core TRD page and report a pixel comparison.

This is the style-regression proof for trd67.py: the existing 41-table page 1
is regenerated from its original spec/schema into a scratch directory and
compared with the committed `docs/diagrams/rebuild/trd/trd-1.png`.  It reads
docs/qa only as the historical schema input; it never writes there.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from docs_qa_guard import ensure_safe_output  # noqa: E402
from diagram_style import render_svg  # noqa: E402


def compare(before, after, outdir):
    a = Image.open(before).convert("RGB")
    b = Image.open(after).convert("RGB")
    if a.size != b.size:
        b = b.resize(a.size, Image.LANCZOS)
    diff = ImageChops.difference(a, b)
    pixels = list(diff.getdata())
    changed = sum(1 for r, g, bl in pixels if max(r, g, bl) > 8)
    total = len(pixels)
    mean = sum(r + g + bl for r, g, bl in pixels) / (total * 3)
    overlay = Image.new("RGB", a.size, "white")
    data = []
    for pa, pb in zip(a.getdata(), b.getdata()):
        ga = sum(pa) / 3 < 160
        gb = sum(pb) / 3 < 160
        if ga and gb:
            data.append((0, 0, 0))
        elif ga:
            data.append((220, 30, 30))
        elif gb:
            data.append((30, 60, 220))
        else:
            data.append((255, 255, 255))
    overlay.putdata(data)
    overlay.save(outdir / "diff.png")
    gap = 28
    pair = Image.new("RGB", (a.width * 2 + gap, a.height + 34), "white")
    pair.paste(a, (0, 34))
    pair.paste(b, (a.width + gap, 34))
    draw = ImageDraw.Draw(pair)
    draw.text((8, 10), "BEFORE (committed)", fill="black")
    draw.text((a.width + gap + 8, 10), "AFTER (regenerated)", fill="black")
    pair.save(outdir / "pair.png")
    metrics = {
        "width": a.width, "height": a.height, "pixels": total,
        "changed_pixels_gt8": changed, "changed_fraction": changed / total,
        "mean_abs_difference": mean,
    }
    (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return metrics


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(Path(__file__).with_name("out") / "reproduce-trd1"))
    args = ap.parse_args(argv)
    outdir = ensure_safe_output(args.out, label="TRD reproduction")
    outdir.mkdir(parents=True, exist_ok=True)
    import json
    import trd_common_f6 as common
    spec_path = ROOT / "docs/diagrams/rebuild/trd/spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    tables = []
    for page in spec["pages"]:
        for card in page["cards"]:
            tables.append({
                "table": card["table"],
                "columns": card["rows"],
                "constraints": [{"type": "p", "columns": [r["name"] for r in card["rows"] if r["pk"]]}],
                "legacy": card["legacy"],
            })
    foreign_keys = []
    for page in spec["pages"]:
        for connector in page.get("connectors", []):
            foreign_keys.append({
                "constraint": connector["fk"], "source": connector["source"],
                "columns": connector["columns"], "destination": connector["destination"],
                "reference_columns": connector["reference_columns"],
            })
    for fk in spec.get("cross_page_fks", []):
        foreign_keys.append({
            "constraint": fk["constraint"], "source": fk["source"],
            "columns": fk["columns"], "destination": fk["destination"],
            "reference_columns": fk["reference_columns"],
        })
    subset = {"tables": tables, "foreign_keys": foreign_keys,
              "migrations": [""] * spec["counts"]["migrations"]}
    subset_path = outdir / "schema-41.json"
    subset_path.write_text(json.dumps(subset, indent=2) + "\n", encoding="utf-8")
    common.INTRO = str(subset_path)
    import build_trd_stage_b_f6 as generator
    original_argv = sys.argv
    try:
        sys.argv = ["build_trd_stage_b_f6.py", str(outdir)]
        generator.main()
    finally:
        sys.argv = original_argv
    generated = outdir / "trd-1.svg"
    png = outdir / "trd-1.png"
    render_svg(generated, png, 3440, 2080)
    committed = ROOT / "docs/diagrams/rebuild/trd/trd-1.png"
    metrics = compare(committed, png, outdir)
    print(json.dumps(metrics, indent=2))
    if metrics["changed_fraction"] > 0.02:
        raise SystemExit("reproduction differs by more than 2% of pixels")
    return 0


if __name__ == "__main__":
    sys.exit(main())

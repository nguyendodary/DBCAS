# -*- coding: utf-8 -*-
"""Build SVG (+PNG) deterministically from a hand-measured spec.json.

Usage:
  python scripts/build_svg_from_spec.py docs/diagrams/rebuild/system-context/spec.json docs/diagrams/rebuild/system-context/system-context.svg

No auto-layout: every element/point comes from spec.json explicit coords.
PNG rendered via Chrome at SVG-matched window (300-dpi equiv for print width).
"""
import html
import json
import subprocess
import sys
from pathlib import Path

CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def esc(s):
    return html.escape(str(s), quote=True)


def build(spec):
    W, H = spec["canvas"]["w"], spec["canvas"]["h"]
    st = spec["style"]
    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">')
    parts.append('<defs><marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
                 '<path d="M0,0 L10,5 L0,10 z" fill="#000000"/></marker></defs>')
    parts.append(f'<rect width="{W}" height="{H}" fill="{st["fill"]}"/>')
    parts.append(f'<g font-family="{st["font_family"]}">')
    parts.append(f'<text x="{W/2}" y="50" font-size="{st["font_sizes"]["title"]}" font-weight="bold" '
                 f'text-anchor="middle" fill="{st["stroke"]}">{esc(st["title"])}</text>')
    for e in spec["elements"]:
        if e["type"] == "rect":
            parts.append(f'<rect x="{e["x"]}" y="{e["y"]}" width="{e["w"]}" height="{e["h"]}" fill="{st["fill"]}" '
                         f'stroke="{st["stroke"]}" stroke-width="{st["stroke_width"]}"/>')
            if e.get("text"):
                parts.append(f'<text x="{e["x"]+e["w"]/2}" y="{e["y"]+e["h"]/2+6}" font-size="{e["font_size"]}" '
                             f'font-weight="bold" text-anchor="middle" fill="{st["stroke"]}">{esc(e["text"])}</text>')
        elif e["type"] == "ellipse":
            parts.append(f'<ellipse cx="{e["cx"]}" cy="{e["cy"]}" rx="{e["rx"]}" ry="{e["ry"]}" fill="{st["fill"]}" '
                         f'stroke="{st["stroke"]}" stroke-width="{st["stroke_width"]}"/>')
            if e.get("text"):
                parts.append(f'<text x="{e["cx"]}" y="{e["cy"]+5}" font-size="{e["font_size"]}" '
                             f'font-weight="bold" text-anchor="middle" fill="{st["stroke"]}">{esc(e["text"])}</text>')
        elif e["type"] == "line":
            pts = " ".join(f"{x},{y}" for x, y in e["points"])
            parts.append(f'<polyline points="{pts}" fill="none" stroke="{st["stroke"]}" stroke-width="1.2"/>')
    for i, t in enumerate(spec.get("legend_texts", [])):
        xs = spec.get("legend_text_x", [])
        x = xs[i] if i < len(xs) else 500 + i * 170
        parts.append(f'<text x="{x}" y="1024" font-size="{st["font_sizes"]["legend"]}" fill="{st["stroke"]}">{esc(t)}</text>')
    for f in spec.get("flows", []):
        pts = f["points"]
        d = "M" + " L".join(f"{x},{y}" for x, y in pts)
        parts.append(f'<path d="{d}" fill="none" stroke="#000000" stroke-width="1.2" marker-end="url(#arr)"/>')
        # label at first horizontal midpoint, staggered to avoid overlaps
        lx, ly = pts[0][0] + 30, pts[0][1] - 6
        parts.append(f'<text x="{lx}" y="{ly}" font-size="{st["font_sizes"]["flow"]}" fill="#000000">{esc(f["label"])}</text>')
    parts.append('</g></svg>')
    return "".join(parts)


def main():
    spec_path = Path(sys.argv[1])
    svg_path = Path(sys.argv[2])
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    svg_path.write_text(build(spec), encoding="utf-8")
    png = svg_path.with_suffix(".png")
    cmd = [str(CHROME), "--headless", "--disable-gpu", "--no-first-run",
           f"--screenshot={png.resolve()}", f"--window-size={spec['canvas']['w']+20},{spec['canvas']['h']+20}",
           "--default-background-color=FFFFFFFF", f"file:///{svg_path.resolve().as_posix()}"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    print("png rc", r.returncode, png.stat().st_size if png.exists() else "missing")


if __name__ == "__main__":
    main()

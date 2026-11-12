# -*- coding: utf-8 -*-
"""Preview evidence for a rebuilt figure: render + side-by-side + difference
overlay + region tiles for the rule-1 "view every region" pass.

Inputs:  <figure_dir>/<name>.svg, <original.png> argument
Outputs (docs/qa/rebuild-preview/<name>/):
  clone.png, side-by-side.png (original | clone), overlay.png
  (black = ink in both, red = original only, blue = clone only),
  regions/<tile>.png tiles of the clone.

Usage:
  node scripts/run_py.mjs scripts/make_figure_previews.py <figure_dir> \
      <original.png> [cols rows]
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def main():
    d = os.path.abspath(sys.argv[1])
    orig_path = os.path.abspath(sys.argv[2])
    cols = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    rows = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    name = os.path.basename(os.path.normpath(d))
    svg = os.path.join(d, name + ".svg")
    png = os.path.join(d, name + ".png")
    r = subprocess.run([CHROME, "--headless", "--disable-gpu",
                        "--no-first-run", "--force-device-scale-factor=1",
                        "--screenshot=" + png,
                        "--window-size=%d,%d" % _canvas(svg),
                        "--default-background-color=FFFFFFFF",
                        "file:///" + svg.replace("\\", "/")],
                       capture_output=True, text=True, timeout=180)
    a = Image.open(orig_path).convert("RGB")
    b = Image.open(png).convert("RGB")
    if a.size != b.size:
        raise SystemExit("size mismatch original %s vs clone %s"
                         % (a.size, b.size))
    prev = os.path.join(ROOT, "docs", "qa", "rebuild-preview", name)
    os.makedirs(prev, exist_ok=True)
    b.save(os.path.join(prev, "clone.png"))
    gap = 24
    sbs = Image.new("RGB", (a.width * 2 + gap, a.height), (255, 255, 255))
    sbs.paste(a, (0, 0))
    sbs.paste(b, (a.width + gap, 0))
    ImageDraw_line = sbs.load()
    for y in range(a.height):
        ImageDraw_line[a.width + gap // 2, y] = (120, 120, 120)
    sbs.save(os.path.join(prev, "side-by-side.png"))
    ga = np.array(a.convert("L")) < 160
    gb = np.array(b.convert("L")) < 160
    out = np.full(ga.shape + (3,), 255, dtype=np.uint8)
    out[ga & gb] = (0, 0, 0)
    out[ga & ~gb] = (220, 30, 30)
    out[~ga & gb] = (30, 60, 220)
    Image.fromarray(out).save(os.path.join(prev, "overlay.png"))
    rdir = os.path.join(prev, "regions")
    os.makedirs(rdir, exist_ok=True)
    W, H = b.size
    tw, th = W // cols, H // rows
    for r_ in range(rows):
        for c_ in range(cols):
            box = (c_ * tw, r_ * th,
                   W if c_ == cols - 1 else (c_ + 1) * tw,
                   H if r_ == rows - 1 else (r_ + 1) * th)
            b.crop(box).save(os.path.join(rdir, "r%d%d.png" % (r_ + 1, c_ + 1)))
    changed = int((ga ^ gb).sum())
    print("rendered %s %s | side-by-side, overlay, %d regions | "
          "changed px: %d (orig-only %d, clone-only %d)"
          % (name, b.size, cols * rows, changed,
             int((ga & ~gb).sum()), int((~ga & gb).sum())))


def _canvas(svg):
    with open(svg, encoding="utf-8") as f:
        head = f.read(400)
    import re
    m = re.search(r'width="(\d+)" height="(\d+)"', head)
    return int(m.group(1)), int(m.group(2))


if __name__ == "__main__":
    main()

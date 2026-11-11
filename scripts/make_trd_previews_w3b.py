# -*- coding: utf-8 -*-
"""Preview evidence for the W3b TRD pages: render, side-by-side, difference
overlay, region tiles, and a contact sheet for the multi-page Stage B set.

Usage:
  tools/.venv/Scripts/python.exe scripts/make_trd_previews_w3b.py \
      <figure_dir> <svg_name> <original.png|-> <out_dir> [cols rows]
"""
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def canvas(svg):
    with open(svg, encoding="utf-8") as f:
        head = f.read(400)
    m = re.search(r'width="(\d+)" height="(\d+)"', head)
    return int(m.group(1)), int(m.group(2))


def render(svg, png):
    W, H = canvas(svg)
    r = subprocess.run([CHROME, "--headless", "--disable-gpu",
                        "--no-first-run", "--force-device-scale-factor=1",
                        "--screenshot=" + os.path.abspath(png),
                        "--window-size=%d,%d" % (W, H),
                        "--default-background-color=FFFFFFFF",
                        "file:///" + os.path.abspath(svg).replace("\\", "/")],
                       capture_output=True, text=True, timeout=240)
    if not os.path.exists(png):
        raise SystemExit(r.stderr[-800:])
    return Image.open(png).convert("RGB")


def main():
    d = os.path.abspath(sys.argv[1])
    svg_name = sys.argv[2]
    orig = sys.argv[3]
    out = os.path.abspath(sys.argv[4])
    cols = int(sys.argv[5]) if len(sys.argv) > 5 else 4
    rows = int(sys.argv[6]) if len(sys.argv) > 6 else 3
    os.makedirs(out, exist_ok=True)
    svg = os.path.join(d, svg_name + ".svg")
    png = os.path.join(d, svg_name + ".png")
    b = render(svg, png)
    b.save(os.path.join(out, "clone.png"))

    if orig and orig != "-":
        a = Image.open(orig).convert("RGB")
        if a.size == b.size:
            gap = 24
            sbs = Image.new("RGB", (a.width * 2 + gap, a.height), (255, 255, 255))
            sbs.paste(a, (0, 0))
            sbs.paste(b, (a.width + gap, 0))
            for y in range(a.height):
                sbs.putpixel((a.width + gap // 2, y), (120, 120, 120))
            sbs.save(os.path.join(out, "side-by-side.png"))
            ga = np.array(a.convert("L")) < 160
            gb = np.array(b.convert("L")) < 160
            ov = np.full(ga.shape + (3,), 255, dtype=np.uint8)
            ov[ga & gb] = (0, 0, 0)
            ov[ga & ~gb] = (220, 30, 30)
            ov[~ga & gb] = (30, 60, 220)
            Image.fromarray(ov).save(os.path.join(out, "overlay.png"))
            from PIL import ImageChops
            diff = ImageChops.difference(a.convert("L"), b.convert("L"))
            diff = diff.point(lambda p: min(255, p * 3))
            diff.save(os.path.join(out, "diff.png"))
            print("overlay changed px: %d (orig-only %d, clone-only %d)"
                  % (int((ga ^ gb).sum()), int((ga & ~gb).sum()),
                     int((~ga & gb).sum())))

    rdir = os.path.join(out, "regions")
    os.makedirs(rdir, exist_ok=True)
    W, H = b.size
    tw, th = W // cols, H // rows
    for r_ in range(rows):
        for c_ in range(cols):
            box = (c_ * tw, r_ * th,
                   W if c_ == cols - 1 else (c_ + 1) * tw,
                   H if r_ == rows - 1 else (r_ + 1) * th)
            b.crop(box).save(os.path.join(rdir, "r%d%d.png" % (r_ + 1, c_ + 1)))
    print("rendered", png, b.size, "regions", cols * rows)


if __name__ == "__main__":
    main()

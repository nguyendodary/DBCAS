# -*- coding: utf-8 -*-
"""F3 owner fix round previews for Module + Logical.

Renders the fixed SVG at the exact original canvas with headless Chrome and
writes, under docs/qa/rebuild-preview/<figure>/:
  final.png            fixed render (same canvas/origin as original.png)
  side-by-side.png     original | fixed, 24 px divider
  overlay.png          black = ink in both, red = original only,
                       blue = fixed only, white = background in both
  diff.png             copy of overlay.png (existing naming convention)
  regions/r11..r33.png 3x3 tiles of the fixed render

Usage:
  node scripts/run_py.mjs scripts/make_fix_previews_f3.py
"""
import os
import shutil
import subprocess

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
FIGS = [("module", 3300, 2050), ("logical", 3200, 3160)]


def render(svg, png, w, h):
    r = subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--no-first-run",
         "--force-device-scale-factor=1", "--hide-scrollbars",
         "--screenshot=" + png, "--window-size=%d,%d" % (w, h),
         "--default-background-color=FFFFFFFF",
         "file:///" + svg.replace("\\", "/")],
        capture_output=True, text=True, timeout=180)
    if not os.path.exists(png):
        raise SystemExit("chrome screenshot failed: %s %s"
                         % (r.returncode, r.stderr[-500:]))
    im = Image.open(png)
    if im.size != (w, h):
        raise SystemExit("unexpected png size %s != %s" % (im.size, (w, h)))


def main():
    for name, w, h in FIGS:
        d = os.path.join(ROOT, "docs", "diagrams", "rebuild", name)
        prev = os.path.join(ROOT, "docs", "qa", "rebuild-preview", name)
        svg = os.path.join(d, name + ".svg")
        png = os.path.join(d, name + ".png")
        render(svg, png, w, h)
        b = Image.open(png).convert("RGB")
        b.save(os.path.join(prev, "final.png"))
        a = Image.open(os.path.join(prev, "original.png")).convert("RGB")
        if a.size != b.size:
            raise SystemExit("%s original %s != final %s"
                             % (name, a.size, b.size))

        gap = 24
        sbs = Image.new("RGB", (a.width * 2 + gap, a.height), (255, 255, 255))
        sbs.paste(a, (0, 0))
        sbs.paste(b, (a.width + gap, 0))
        for y in range(a.height):
            sbs.putpixel((a.width + gap // 2, y), (120, 120, 120))
        sbs.save(os.path.join(prev, "side-by-side.png"))

        ga = np.array(a.convert("L")) < 160
        gb = np.array(b.convert("L")) < 160
        out = np.full(ga.shape + (3,), 255, dtype=np.uint8)
        out[ga & gb] = (0, 0, 0)
        out[ga & ~gb] = (220, 30, 30)
        out[~ga & gb] = (30, 60, 220)
        ov = Image.fromarray(out)
        ov.save(os.path.join(prev, "overlay.png"))
        ov.save(os.path.join(prev, "diff.png"))

        rdir = os.path.join(prev, "regions")
        os.makedirs(rdir, exist_ok=True)
        tw, th = w // 3, h // 3
        for r in range(3):
            for c in range(3):
                box = (c * tw, r * th, w if c == 2 else (c + 1) * tw,
                       h if r == 2 else (r + 1) * th)
                b.crop(box).save(os.path.join(rdir, "r%d%d.png" % (r + 1, c + 1)))
        changed = int((ga ^ gb).sum())
        print("%s %s | side-by-side, overlay/diff, 9 regions | changed px %d "
              "(orig-only %d, fixed-only %d)"
              % (name, b.size, changed, int((ga & ~gb).sum()),
                 int((~ga & gb).sum())))


if __name__ == "__main__":
    main()

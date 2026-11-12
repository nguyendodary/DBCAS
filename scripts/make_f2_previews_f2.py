# -*- coding: utf-8 -*-
"""F2 owner-fix previews: final render, side-by-side, overlay, diff, regions.

Usage: node scripts/run_py.mjs scripts/make_f2_previews_f2.py <name> <W> <H>
  name = container | allocation
"""
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def main():
    name, W, H = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    reb = os.path.join(ROOT, "docs", "diagrams", "rebuild", name)
    prev = os.path.join(ROOT, "docs", "qa", "rebuild-preview", name)
    orig_path = os.path.join(ROOT, "docs", "qa", "diagram-originals",
                             "ArchitectureDesign_ver1.1_image%s.png" %
                             ("4" if name == "container" else "7"))
    svg = os.path.join(reb, name + ".svg")
    png = os.path.join(reb, name + ".png")
    cmd = [CHROME, "--headless", "--disable-gpu", "--no-first-run",
           "--force-device-scale-factor=1", "--screenshot=" + png,
           "--window-size=%d,%d" % (W, H),
           "--default-background-color=FFFFFFFF",
           "file:///" + svg.replace("\\", "/")]
    subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    im = Image.open(png)
    if im.size != (W, H):
        raise SystemExit("png %s != %s" % (im.size, (W, H)))

    shutil.copyfile(png, os.path.join(prev, "final.png"))
    a = Image.open(orig_path).convert("RGB")
    b = im.convert("RGB")

    # side-by-side (original | final), top-left aligned
    gap = 24
    sbs = Image.new("RGB", (a.width + gap + b.width, max(a.height, b.height)),
                    (255, 255, 255))
    sbs.paste(a, (0, 0))
    sbs.paste(b, (a.width + gap, 0))
    ImageDraw.Draw(sbs).line(
        [(a.width + gap // 2, 0), (a.width + gap // 2, sbs.height)],
        fill=(120, 120, 120), width=2)
    sbs.save(os.path.join(prev, "side-by-side-final.png"))

    # overlay / diff on the union canvas, same origin
    UW, UH = max(a.width, b.width), max(a.height, b.height)
    ca = Image.new("RGB", (UW, UH), (255, 255, 255))
    cb = Image.new("RGB", (UW, UH), (255, 255, 255))
    ca.paste(a, (0, 0))
    cb.paste(b, (0, 0))
    ga = np.array(ca.convert("L")) < 160
    gb = np.array(cb.convert("L")) < 160
    out = np.full(ga.shape + (3,), 255, dtype=np.uint8)
    out[ga & gb] = (0, 0, 0)
    out[ga & ~gb] = (220, 30, 30)
    out[~ga & gb] = (30, 60, 220)
    Image.fromarray(out).save(os.path.join(prev, "overlay-final.png"))
    ImageChops.difference(ca, cb).convert("L").save(
        os.path.join(prev, "diff.png"))

    # 3x3 regions of the final render
    rdir = os.path.join(prev, "regions-final")
    os.makedirs(rdir, exist_ok=True)
    tw, th = W // 3, H // 3
    for r in range(3):
        for c in range(3):
            box = (c * tw, r * th,
                   W if c == 2 else (c + 1) * tw,
                   H if r == 2 else (r + 1) * th)
            b.crop(box).save(os.path.join(rdir, "r%d%d.png" % (r + 1, c + 1)))
    # focused crops used by the report text
    if name == "container":
        b.crop((1020, 1180, 1780, 1645)).save(
            os.path.join(rdir, "r_extra_external.png"))
        b.crop((40, 190, 900, 620)).save(
            os.path.join(rdir, "r_extra_flow.png"))
    else:
        b.crop((850, 1030, 1725, 1600)).save(
            os.path.join(rdir, "r_extra_external.png"))
        b.crop((40, 500, 900, 700)).save(
            os.path.join(rdir, "r_extra_frame.png"))
    print("rendered %s %dx%d; wrote final/side-by-side/overlay/diff + 9 regions"
          % (name, W, H))


if __name__ == "__main__":
    main()

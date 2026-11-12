# -*- coding: utf-8 -*-
"""W2b helper: crop + upscale regions of a PNG for visual inspection.

Usage:
  node scripts/run_py.mjs scripts/crop_w2b.py <png> <outdir> <name:x0,y0,x1,y1> [...]
    [--scale 3]
"""
import os
import sys

from PIL import Image


def main():
    src = sys.argv[1]
    outdir = sys.argv[2]
    scale = 3
    rest = sys.argv[3:]
    specs = []
    i = 0
    while i < len(rest):
        if rest[i] == "--scale":
            scale = int(rest[i + 1])
            i += 2
            continue
        specs.append(rest[i])
        i += 1
    os.makedirs(outdir, exist_ok=True)
    img = Image.open(src).convert("RGB")
    for spec in specs:
        name, box = spec.split(":", 1)
        x0, y0, x1, y1 = [int(v) for v in box.split(",")]
        c = img.crop((x0, y0, x1, y1))
        if scale != 1:
            c = c.resize((c.width * scale, c.height * scale),
                         Image.NEAREST)
        p = os.path.join(outdir, name + ".png")
        c.save(p)
        print(p, c.size)


if __name__ == "__main__":
    main()

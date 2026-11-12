# -*- coding: utf-8 -*-
"""F4 Pipeline preview evidence: final, side-by-side, overlay, diff, 3x3 tiles.

old = final-prefix.png (Stage B as reviewed), new = pipeline.png (F4 fix).
Same 1342x762 canvas, so the overlay is a true same-origin difference:
black = ink in both, red = old only, blue = new only, white = clean in both.

Usage: python scripts/make_pipeline_f4_previews.py
"""
import os
import shutil

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REB = os.path.join(ROOT, "docs", "diagrams", "rebuild", "pipeline")
PREV = os.path.join(ROOT, "docs", "qa", "rebuild-preview", "pipeline")
W, H = 1342, 762


def main():
    old = Image.open(os.path.join(PREV, "final-prefix.png")).convert("RGB")
    new_path = os.path.join(REB, "pipeline.png")
    new = Image.open(new_path).convert("RGB")
    assert old.size == new.size == (W, H), (old.size, new.size)

    shutil.copyfile(new_path, os.path.join(PREV, "final.png"))

    gap = 24
    sbs = Image.new("RGB", (W * 2 + gap, H), (255, 255, 255))
    sbs.paste(old, (0, 0))
    sbs.paste(new, (W + gap, 0))
    d = ImageDraw.Draw(sbs)
    d.line([(W + gap // 2, 0), (W + gap // 2, H)], fill=(120, 120, 120),
           width=2)
    sbs.save(os.path.join(PREV, "side-by-side-final.png"))

    import numpy as np
    ga = np.array(old.convert("L")) < 160
    gb = np.array(new.convert("L")) < 160
    out = np.full(ga.shape + (3,), 255, dtype=np.uint8)
    out[ga & gb] = (0, 0, 0)
    out[ga & ~gb] = (220, 30, 30)
    out[~ga & gb] = (30, 60, 220)
    Image.fromarray(out).save(os.path.join(PREV, "overlay-final.png"))

    a = np.array(old, dtype=np.int16)
    b = np.array(new, dtype=np.int16)
    delta = np.abs(a - b).max(axis=2).astype(np.uint8)
    delta = np.clip(delta * 4, 0, 255)
    Image.fromarray(delta, mode="L").save(os.path.join(PREV,
                                                       "diff-final.png"))

    rdir = os.path.join(PREV, "regions-final")
    os.makedirs(rdir, exist_ok=True)
    boxes = []
    for row in range(3):
        for col in range(3):
            x0 = round(col * W / 3)
            x1 = round((col + 1) * W / 3)
            y0 = round(row * H / 3)
            y1 = round((row + 1) * H / 3)
            boxes.append((x0, y0, x1, y1))
    for i, box in enumerate(boxes, 1):
        new.crop(box).save(os.path.join(rdir, "r%d%d.png"
                                        % ((i - 1) // 3 + 1,
                                           (i - 1) % 3 + 1)))
    print("final.png, side-by-side-final.png, overlay-final.png, "
          "diff-final.png, regions-final/9 tiles")
    print("changed pixels: %d (old-only %d, new-only %d)"
          % (int((ga ^ gb).sum()), int((ga & ~gb).sum()),
             int((~ga & gb).sum())))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""F5 ERD preview evidence: render, side-by-side, overlay, diff, regions."""
import os
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REBUILD = os.path.join(ROOT, "docs", "diagrams", "rebuild", "erd")
PREV = os.path.join(ROOT, "docs", "qa", "rebuild-preview", "erd")
SVG = os.path.join(REBUILD, "erd.svg")
PNG = os.path.join(REBUILD, "erd.png")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
W, H = 4300, 1677

REGIONS = [
    ("r11_top_left", (0, 0, 1100, 560)),
    ("r12_top_midleft", (1050, 0, 2200, 560)),
    ("r13_top_midright", (2150, 0, 3300, 560)),
    ("r14_top_right", (3200, 0, 4300, 650)),
    ("r21_mid_left", (0, 520, 1100, 1120)),
    ("r22_mid_midleft", (1050, 520, 2200, 1120)),
    ("r23_mid_midright", (2150, 520, 3300, 1120)),
    ("r24_mid_right", (3200, 520, 4300, 1240)),
    ("r31_bottom_left", (0, 1080, 1100, 1677)),
    ("r32_bottom_midleft", (1050, 1080, 2200, 1677)),
    ("r33_bottom_midright", (2150, 1080, 3300, 1677)),
    ("r34_bottom_right", (3200, 1080, 4300, 1677)),
    ("r_new_column", (3150, 0, 4300, 1677)),
    ("r_legend", (700, 1440, 3150, 1677)),
    ("r_junction", (620, 700, 1120, 1220)),
]


def render_png():
    cmd = [CHROME, "--headless", "--disable-gpu", "--no-first-run",
           "--force-device-scale-factor=1",
           "--screenshot=" + PNG,
           "--window-size=%d,%d" % (W, H),
           "--default-background-color=FFFFFFFF",
           "file:///" + SVG.replace("\\", "/")]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if not os.path.exists(PNG):
        raise SystemExit("chrome screenshot failed: %s %s"
                         % (r.returncode, r.stderr[-500:]))
    im = Image.open(PNG)
    if im.size != (W, H):
        raise SystemExit("unexpected png size %s" % (im.size,))
    print("rendered %s %s" % (PNG, im.size))


def main():
    render_png()
    orig = Image.open(os.path.join(PREV, "original.png")).convert("RGB")
    final = Image.open(PNG).convert("RGB")
    assert orig.size == (3251, 1677)

    # same canvas for the comparison images
    a = Image.new("RGB", (W, H), (255, 255, 255))
    a.paste(orig, (0, 0))
    shutil.copyfile(PNG, os.path.join(PREV, "final.png"))

    gap = 24
    sbs = Image.new("RGB", (W + orig.width + gap, H), (255, 255, 255))
    sbs.paste(orig, (0, 0))
    sbs.paste(final, (orig.width + gap, 0))
    d = ImageDraw.Draw(sbs)
    d.line([(orig.width + gap // 2, 0), (orig.width + gap // 2, H)],
           fill=(120, 120, 120), width=2)
    sbs.save(os.path.join(PREV, "side-by-side-final.png"))

    ga = np.array(a.convert("L")) < 160
    gb = np.array(final.convert("L")) < 160
    out = np.full(ga.shape + (3,), 255, dtype=np.uint8)
    out[ga & gb] = (0, 0, 0)
    out[ga & ~gb] = (220, 30, 30)
    out[~ga & gb] = (30, 60, 220)
    Image.fromarray(out).save(os.path.join(PREV, "overlay-final.png"))

    # Stage A clone vs final: red must be ~zero if no original element moved.
    clone = Image.open(os.path.join(REBUILD, "stage-a",
                                    "erd-stage-a.png")).convert("RGB")
    c = Image.new("RGB", (W, H), (255, 255, 255))
    c.paste(clone, (0, 0))
    gc = np.array(c.convert("L")) < 160
    out2 = np.full(gc.shape + (3,), 255, dtype=np.uint8)
    out2[gc & gb] = (0, 0, 0)
    out2[gc & ~gb] = (220, 30, 30)
    out2[~gc & gb] = (30, 60, 220)
    Image.fromarray(out2).save(os.path.join(PREV, "overlay-stage-a-final.png"))
    sbs2 = Image.new("RGB", (W + clone.width + gap, H), (255, 255, 255))
    sbs2.paste(clone, (0, 0))
    sbs2.paste(final, (clone.width + gap, 0))
    d2 = ImageDraw.Draw(sbs2)
    d2.line([(clone.width + gap // 2, 0), (clone.width + gap // 2, H)],
            fill=(120, 120, 120), width=2)
    sbs2.save(os.path.join(PREV, "side-by-side-stage-a-final.png"))
    # 1:1 left-3251 comparison: the only region where the original drawing
    # exists; it proves the original slots did not move.
    left = final.crop((0, 0, clone.width, H))
    sbs3 = Image.new("RGB", (clone.width * 2 + gap, H), (255, 255, 255))
    sbs3.paste(clone, (0, 0))
    sbs3.paste(left, (clone.width + gap, 0))
    d3 = ImageDraw.Draw(sbs3)
    d3.line([(clone.width + gap // 2, 0), (clone.width + gap // 2, H)],
            fill=(120, 120, 120), width=2)
    sbs3.save(os.path.join(PREV, "side-by-side-left-final.png"))

    # absolute difference as a red heat map (white = identical); compare the
    # Stage A clone so only the intended delta is highlighted.
    diff = np.abs(np.array(c.convert("L"), dtype=np.int16) -
                  np.array(final.convert("L"), dtype=np.int16))
    d8 = np.clip(diff * 2, 0, 255).astype(np.uint8)
    rgb = np.stack([255 - d8 // 3, 255 - d8, 255 - d8], axis=-1)
    Image.fromarray(rgb.astype(np.uint8)).save(
        os.path.join(PREV, "diff-final.png"))

    rdir = os.path.join(PREV, "regions-final")
    os.makedirs(rdir, exist_ok=True)
    for name, box in REGIONS:
        final.crop(box).save(os.path.join(rdir, name + ".png"))

    print("wrote final.png, side-by-side-final.png, overlay-final.png, "
          "diff-final.png, regions-final/%d crops" % len(REGIONS))
    print("changed ink pixels: %d (original-only %d, final-only %d)"
          % (int((ga ^ gb).sum()), int((ga & ~gb).sum()),
             int((~ga & gb).sum())))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""F1 owner-fix previews for the Use Case figure (right-margin fix).

The figure canvas grew from 3000x3300 to 3120x3300 so the Administrator
label has a real right margin. Every traced element keeps its original
coordinates. For a 1:1 comparison the untouched original is padded with
white on the right to the new canvas:

  original-source.png       byte copy of the untouched 3000x3300 original
  original.png              original padded to 3120x3300 (comparison canvas)
  final.png                 final 3120x3300 render
  side-by-side-final.png    padded original | final, 1:1, 24 px divider
  overlay-final.png         black = both, red = original only,
                            blue = final only, white = both background
  diff.png                  3 x (sum of |RGB difference|), clipped (same
                            amplification as the Stage B diff)
  regions-final/r*.png      3 x 3 tiles of the final render
  right-edge-final.png      raw original (x 2550..3000) | final
                            (x 2550..3120), y 1400..2020, to show the added
                            right margin at the label

Usage:
  node scripts/run_py.mjs scripts/make_use_case_f1_previews.py
"""
import os
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REBUILD = os.path.join(ROOT, "docs", "diagrams", "rebuild", "use-case")
PREV = os.path.join(ROOT, "docs", "qa", "rebuild-preview", "use-case")
ORIGINAL = os.path.join(ROOT, "docs", "qa", "diagram-originals",
                        "ArchitectureDesign_ver1.1_image2.png")
SVG = os.path.join(REBUILD, "use-case.svg")
PNG = os.path.join(REBUILD, "use-case.png")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
W, H = 3120, 3300
COLS, ROWS = 3, 3


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

    raw = Image.open(ORIGINAL).convert("RGB")
    if raw.size != (3000, 3300):
        raise SystemExit("unexpected original size %s" % (raw.size,))
    raw.save(os.path.join(PREV, "original-source.png"))

    # Comparison original: same 3120x3300 canvas with white right margin.
    a = Image.new("RGB", (W, H), (255, 255, 255))
    a.paste(raw, (0, 0))
    a.save(os.path.join(PREV, "original.png"))

    b = Image.open(PNG).convert("RGB")
    shutil.copyfile(PNG, os.path.join(PREV, "final.png"))

    # side by side: padded original | final
    gap = 24
    sbs = Image.new("RGB", (W * 2 + gap, H), (255, 255, 255))
    sbs.paste(a, (0, 0))
    sbs.paste(b, (W + gap, 0))
    d = ImageDraw.Draw(sbs)
    d.line([(W + gap // 2, 0), (W + gap // 2, H)], fill=(120, 120, 120), width=2)
    sbs.save(os.path.join(PREV, "side-by-side-final.png"))

    # overlay: black = ink in both, red = original only, blue = final only
    ga = np.array(a.convert("L")) < 160
    gb = np.array(b.convert("L")) < 160
    out = np.full(ga.shape + (3,), 255, dtype=np.uint8)
    out[ga & gb] = (0, 0, 0)
    out[ga & ~gb] = (220, 30, 30)
    out[~ga & gb] = (30, 60, 220)
    Image.fromarray(out).save(os.path.join(PREV, "overlay-final.png"))

    # amplified absolute difference: 3 x sum(|dR|,|dG|,|dB|)
    diff = np.abs(np.asarray(a, dtype=np.int16) - np.asarray(b, dtype=np.int16))
    amp = np.clip(diff.sum(axis=2) * 3, 0, 255).astype(np.uint8)
    Image.fromarray(amp, "L").save(os.path.join(PREV, "diff.png"))

    # region tiles
    rdir = os.path.join(PREV, "regions-final")
    os.makedirs(rdir, exist_ok=True)
    tw, th = W // COLS, H // ROWS
    for r in range(ROWS):
        for c in range(COLS):
            box = (c * tw, r * th,
                   W if c == COLS - 1 else (c + 1) * tw,
                   H if r == ROWS - 1 else (r + 1) * th)
            b.crop(box).save(os.path.join(rdir, "r%d%d.png" % (r + 1, c + 1)))

    # focused right-edge comparison: raw original (3000 wide) vs final
    # (3120 wide), both starting at x=2550 so the added margin is visible.
    box_o = (2550, 1400, 3000, 2020)
    box_f = (2550, 1400, W, 2020)
    ra = raw.crop(box_o)
    rb = b.crop(box_f)
    edge = Image.new("RGB", (ra.width + rb.width + 24, ra.height),
                     (255, 255, 255))
    edge.paste(ra, (0, 0))
    edge.paste(rb, (ra.width + 24, 0))
    ImageDraw.Draw(edge).line(
        [(ra.width + 12, 0), (ra.width + 12, ra.height)],
        fill=(120, 120, 120), width=2)
    edge.save(os.path.join(PREV, "right-edge-final.png"))

    changed = int((ga ^ gb).sum())
    print("wrote final.png %s, side-by-side-final.png %s, "
          "overlay-final.png, diff.png, regions-final/%d tiles, "
          "right-edge-final.png"
          % (b.size, sbs.size, COLS * ROWS))
    print("changed pixels: %d (original-only %d, final-only %d)"
          % (changed, int((ga & ~gb).sum()), int((~ga & gb).sum())))
    print("label margin: final right edge %d px, canvas %d px, margin %d px"
          % (2974, W, W - 2974))


if __name__ == "__main__":
    main()

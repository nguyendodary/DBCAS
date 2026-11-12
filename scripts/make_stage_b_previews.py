# -*- coding: utf-8 -*-
"""Stage B preview evidence: copy, side-by-side, difference overlay, crops.

Inputs:
  docs/qa/rebuild-preview/system-context/clone.png      (Stage A clone)
  docs/diagrams/rebuild/system-context/system-context.png (Stage B render)

Outputs (docs/qa/rebuild-preview/system-context/):
  stage-b.png             Stage B render copy (same canvas/origin)
  side-by-side-stage-b.png  Stage A clone | Stage B at 1:1
  overlay-stage-b.png     overlay of Stage B onto Stage A showing ONLY the
                          differences: black = both, red = Stage A only,
                          blue = Stage B only, white = unchanged background
  regions-stage-b/r*.png  region crops of the Stage B render

Usage:
  node scripts/run_py.mjs scripts/make_stage_b_previews.py
"""
import os
import shutil
import subprocess

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREV = os.path.join(ROOT, "docs", "qa", "rebuild-preview", "system-context")
REBUILD = os.path.join(ROOT, "docs", "diagrams", "rebuild", "system-context")
SVG = os.path.join(REBUILD, "system-context.svg")
NEW_PNG = os.path.join(REBUILD, "system-context.png")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
W, H = 1431, 1061

REGIONS = [
    ("r1_topleft", (80, 20, 760, 240)),
    ("r2_elltop", (560, 315, 880, 410)),
    ("r3_legend", (380, 975, 1050, 1055)),
    ("r4_llm_top", (180, 845, 420, 895)),
    ("r5_ellbot", (575, 555, 870, 625)),
    ("r6_admin_right", (1180, 180, 1360, 520)),
    ("r7_new_flows", (840, 480, 1431, 700)),
    ("r8_new_boxes", (980, 600, 1431, 950)),
    ("r9_renamed_admin", (880, 180, 1360, 345)),
]


def render_png():
    """Headless Chrome screenshot of the Stage B SVG at the exact canvas."""
    cmd = [CHROME, "--headless", "--disable-gpu", "--no-first-run",
           "--force-device-scale-factor=1",
           "--screenshot=" + NEW_PNG,
           "--window-size=%d,%d" % (W, H),
           "--default-background-color=FFFFFFFF",
           "file:///" + SVG.replace("\\", "/")]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if not os.path.exists(NEW_PNG):
        raise SystemExit("chrome screenshot failed: %s %s"
                         % (r.returncode, r.stderr[-500:]))
    im = Image.open(NEW_PNG)
    if im.size != (W, H):
        raise SystemExit("unexpected png size %s" % (im.size,))
    print("rendered %s %s" % (NEW_PNG, im.size))


def main():
    render_png()
    a = Image.open(os.path.join(PREV, "clone.png")).convert("RGB")
    b = Image.open(NEW_PNG).convert("RGB")
    assert a.size == b.size == (1431, 1061), (a.size, b.size)

    shutil.copyfile(NEW_PNG, os.path.join(PREV, "stage-b.png"))

    # side by side: Stage A clone | Stage B
    gap = 24
    sbs = Image.new("RGB", (a.width * 2 + gap, a.height), (255, 255, 255))
    sbs.paste(a, (0, 0))
    sbs.paste(b, (a.width + gap, 0))
    d = ImageDraw.Draw(sbs)
    d.line([(a.width + gap // 2, 0), (a.width + gap // 2, a.height)],
           fill=(120, 120, 120), width=2)
    sbs.save(os.path.join(PREV, "side-by-side-stage-b.png"))

    # difference overlay: black = ink in both, red = Stage A only,
    # blue = Stage B only, white = background in both
    import numpy as np
    ga = np.array(a.convert("L")) < 160
    gb = np.array(b.convert("L")) < 160
    out = np.full(ga.shape + (3,), 255, dtype=np.uint8)
    out[ga & gb] = (0, 0, 0)
    out[ga & ~gb] = (220, 30, 30)
    out[~ga & gb] = (30, 60, 220)
    Image.fromarray(out).save(os.path.join(PREV, "overlay-stage-b.png"))

    # region crops of the Stage B render
    rdir = os.path.join(PREV, "regions-stage-b")
    os.makedirs(rdir, exist_ok=True)
    for name, box in REGIONS:
        b.crop(box).save(os.path.join(rdir, name + ".png"))

    print("wrote stage-b.png, side-by-side-stage-b.png, "
          "overlay-stage-b.png, regions-stage-b/%d crops" % len(REGIONS))
    diff = int((ga ^ gb).sum())
    print("changed pixels: %d (A-only %d, B-only %d)"
          % (diff, int((ga & ~gb).sum()), int((~ga & gb).sum())))


if __name__ == "__main__":
    main()

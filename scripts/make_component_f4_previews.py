# -*- coding: utf-8 -*-
"""F4 Component split preview evidence.

The approved figure is now two horizontal pages, 08a (left columns) and 08b
(right columns), each 1400x1020.  This script writes:
  final-08a.png / final-08b.png       1:1 page renders
  final.png                           2361x1423 contact sheet (keeps the
                                      existing figure gate's canvas check)
  side-by-side-final.png              old single page | new two-page sheet
  side-by-side-final-08a/-08b.png     old single page | each new page
  overlay-final.png / diff-final.png  stacked per-page proofs (prefix layout
                                      vs fixed layout, same canvas)
  overlay-final-08a/-08b.png          per-page overlays
  diff-final-08a/-08b.png             per-page abs-diff maps
  regions-final/                      3x3 tiles of 08a
  regions-final-08b/                  3x3 tiles of 08b
"""
import os
import shutil

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REB = os.path.join(ROOT, "docs", "diagrams", "rebuild", "component")
PREV = os.path.join(ROOT, "docs", "qa", "rebuild-preview", "component")
W, H = 1400, 980
OW, OH = 2361, 1423
FONT = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 30)
SMALL = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)


def overlay(a, b):
    import numpy as np
    ga = np.array(a.convert("L")) < 160
    gb = np.array(b.convert("L")) < 160
    out = np.full(ga.shape + (3,), 255, dtype=np.uint8)
    out[ga & gb] = (0, 0, 0)
    out[ga & ~gb] = (220, 30, 30)
    out[~ga & gb] = (30, 60, 220)
    return Image.fromarray(out)


def diffmap(a, b):
    import numpy as np
    da = np.abs(np.array(a, dtype=np.int16)
                - np.array(b, dtype=np.int16)).max(axis=2)
    return Image.fromarray(np.clip(da * 4, 0, 255).astype("uint8"), mode="L")


def tiles(img, outdir, n=3):
    os.makedirs(outdir, exist_ok=True)
    w, h = img.size
    for row in range(n):
        for col in range(n):
            x0 = round(col * w / n)
            x1 = round((col + 1) * w / n)
            y0 = round(row * h / n)
            y1 = round((row + 1) * h / n)
            img.crop((x0, y0, x1, y1)).save(
                os.path.join(outdir, "r%d%d.png" % (row + 1, col + 1)))


def main():
    old = Image.open(os.path.join(PREV, "final-prefix.png")).convert("RGB")
    assert old.size == (OW, OH)
    pages = {}
    for name in ("08a", "08b"):
        img = Image.open(os.path.join(REB, "component-%s.png"
                                      % name)).convert("RGB")
        assert img.size == (W, H)
        pages[name] = img
        shutil.copyfile(os.path.join(REB, "component-%s.png" % name),
                        os.path.join(PREV, "final-%s.png" % name))

    # contact sheet 2361x1423 (same canvas as the original figure)
    scale = 0.84
    sw, sh = int(W * scale), int(H * scale)
    sheet = Image.new("RGB", (OW, OH), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    x0 = (OW - (sw * 2 + 9)) // 2
    y0 = (OH - sh) // 2
    for i, name in enumerate(("08a", "08b")):
        x = x0 + i * (sw + 9)
        sheet.paste(pages[name].resize((sw, sh), Image.LANCZOS), (x, y0))
        d.rectangle([x, y0, x + sw - 1, y0 + sh - 1], outline=(120, 120, 120),
                    width=2)
        d.text((x + 12, y0 - 42), "Figure 4 (%s/2). Component — page %s  (%d x %d px)"
               % ("1" if name == "08a" else "2", name, W, H),
               font=FONT, fill=(0, 0, 0))
    sheet.save(os.path.join(PREV, "final.png"))

    gap = 24
    sbs = Image.new("RGB", (OW * 2 + gap, OH), (255, 255, 255))
    sbs.paste(old, (0, 0))
    sbs.paste(sheet, (OW + gap, 0))
    ImageDraw.Draw(sbs).line([(OW + gap // 2, 0), (OW + gap // 2, OH)],
                             fill=(120, 120, 120), width=2)
    sbs.save(os.path.join(PREV, "side-by-side-final.png"))

    # old page scaled to the new page height, then each new page 1:1
    old_h = old.resize((round(OW * H / OH), H), Image.LANCZOS)
    for name in ("08a", "08b"):
        canvas = Image.new("RGB", (old_h.width + gap + W, H),
                           (255, 255, 255))
        canvas.paste(old_h, (0, 0))
        canvas.paste(pages[name], (old_h.width + gap, 0))
        ImageDraw.Draw(canvas).line(
            [(old_h.width + gap // 2, 0), (old_h.width + gap // 2, H)],
            fill=(120, 120, 120), width=2)
        canvas.save(os.path.join(PREV, "side-by-side-final-%s.png" % name))

    overlays, diffs = [], []
    for name in ("08a", "08b"):
        pre = Image.open(os.path.join(REB, "component-%s-prefix.png"
                                      % name)).convert("RGB")
        ov = overlay(pre, pages[name])
        dm = diffmap(pre, pages[name])
        ov.save(os.path.join(PREV, "overlay-final-%s.png" % name))
        dm.save(os.path.join(PREV, "diff-final-%s.png" % name))
        overlays.append(ov)
        diffs.append(dm)
        tiles(pages[name], os.path.join(PREV, "regions-final"
                                        if name == "08a"
                                        else "regions-final-08b"))

    for fname, imgs, label in (("overlay-final.png", overlays, "overlay"),
                               ("diff-final.png", diffs, "abs diff")):
        canvas = Image.new("RGB", (W, H * 2 + 70), (255, 255, 255))
        d = ImageDraw.Draw(canvas)
        for i, im in enumerate(imgs):
            y = i * (H + 35) + 35
            canvas.paste(im.convert("RGB"), (0, y))
            d.text((10, y - 30), "08%s %s (prefix layout vs fixed layout)"
                   % ("ab"[i], label), font=SMALL, fill=(0, 0, 0))
        canvas.save(os.path.join(PREV, fname))

    print("wrote final.png, final-08a/b.png, side-by-side-final{,-08a,-08b}.png, "
          "overlay-final{,-08a,-08b}.png, diff-final{,-08a,-08b}.png, "
          "regions-final/9 + regions-final-08b/9 tiles")


if __name__ == "__main__":
    main()

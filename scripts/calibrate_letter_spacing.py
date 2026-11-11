# -*- coding: utf-8 -*-
"""Calibrate letter-spacing and x against the REAL renderer (Chrome).

PIL's hinted ink metrics differ from Chrome's by up to ~6 px per label, so
plan-derived spacing leaves residuals (and window-based measurement can be
poisoned by neighbouring labels). This script renders every label in an
ISOLATED grid probe (known position, white background, black text),
measures Chrome's exact ink offset and width, and writes
letter-spacing.json {"<id>": {"ls": ..., "x": ...}} with absolute values
that build_figure applies, so each rendered label matches its measured
band exactly.

Usage:
  node scripts/run_py.mjs scripts/calibrate_letter_spacing.py <figure_dir>
Exit 0 = every label written (residuals checked by the caller).
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    d = os.path.abspath(sys.argv[1])
    spec = json.load(open(os.path.join(d, "spec.json"), encoding="utf-8"))
    texts = spec["texts"]

    max_w = max(t["measured"][2] - t["measured"][0] for t in texts) + 60
    cols = 3
    colw = max_w + 60
    rowh = 80
    rows = (len(texts) + cols - 1) // cols
    W = cols * colw + 80
    H = rows * rowh + 80

    cells = {}
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" '
             'height="%d" viewBox="0 0 %d %d">' % (W, H, W, H),
             '<rect width="%d" height="%d" fill="#FFFFFF"/>' % (W, H),
             '<g font-family="Arial, Helvetica, sans-serif">']
    for i, t in enumerate(texts):
        cx = 40 + (i % cols) * colw
        cy = 50 + (i // cols) * rowh
        cells[t["id"]] = (cx, cy, max_w)
        ls = t.get("ls") or 0.0
        ls_attr = ' letter-spacing="%s"' % ("%.2f" % ls) if ls else ""
        parts.append('<text x="%d" y="%d" font-size="%s" font-weight="%s"%s '
                     'fill="#000000">%s</text>'
                     % (cx, cy, t["size"],
                        "bold" if t["weight"] == "bold" else "normal",
                        ls_attr, esc(t["content"])))
    parts.append("</g></svg>")
    probe = os.path.join(d, "_probe.svg")
    png = os.path.join(d, "_probe.png")
    with open(probe, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-first-run",
                    "--force-device-scale-factor=1",
                    "--screenshot=" + png, "--window-size=%d,%d" % (W, H),
                    "--default-background-color=FFFFFFFF",
                    "file:///" + probe.replace("\\", "/")],
                   capture_output=True, timeout=180)
    a = np.array(Image.open(png).convert("L"))
    dark = a < 170

    calib = {}
    print("%-6s %-38s %7s %7s %7s %7s %6s" %
          ("id", "text", "want_w", "chrome_w", "ix0", "dx", "new ls"))
    for t in texts:
        x0, y0, x1, y1 = t["measured"]
        want_w = x1 - x0
        n = max(1, len(t["content"]) - 1)
        cx, cy, mw = cells[t["id"]]
        win = dark[max(0, cy - 45):cy + 20, max(0, cx - 12):cx + mw + 12]
        xs = np.flatnonzero(win.any(axis=0))
        if not len(xs):
            print("WARN: no ink for", t["id"], t["content"][:30])
            continue
        ink_l = max(0, cx - 12) + int(xs[0])
        ink_r = max(0, cx - 12) + int(xs[-1]) + 1
        chrome_iw = ink_r - ink_l
        chrome_ix0 = ink_l - cx
        # chrome_iw already contains the probe's current spacing:
        # base = chrome_iw - gaps*old_ls  ->  new_ls = old_ls + residual/gaps
        gaps = float(n)
        old_ls = t.get("ls") or 0.0
        ls = old_ls + (want_w - chrome_iw) / gaps
        ls = max(-3.0, min(3.0, round(ls, 2)))
        new_x = x0 - chrome_ix0
        calib[t["id"]] = {"ls": ls, "x": round(new_x, 1)}
        print("%-6s %-38s %7d %7d %7d %7.1f %6.2f" %
              (t["id"], t["content"][:38], want_w, chrome_iw,
               chrome_ix0, new_x - float(t["x"]), ls))
    with open(os.path.join(d, "letter-spacing.json"), "w",
              encoding="utf-8") as f:
        json.dump(calib, f, indent=1)
    for p in (probe, png):
        if os.path.exists(p):
            os.remove(p)
    print("wrote letter-spacing.json (%d labels)" % len(calib))
    sys.exit(0 if len(calib) == len(texts) else 1)


if __name__ == "__main__":
    main()

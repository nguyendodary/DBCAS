# -*- coding: utf-8 -*-
"""Draw thin red verification markers for every traced element on a COPY of
the original PNG, so the trace can be checked visually (owner rule 4).

Usage: python scripts/draw_trace_markers.py <original_png> <trace_json> <out_png>
"""
import json
import sys

from PIL import Image, ImageDraw


def main():
    src, trace_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    t = json.load(open(trace_path, encoding="utf-8"))
    im = Image.open(src).convert("RGB")
    d = ImageDraw.Draw(im)

    # rectangles (1px red outline)
    for r in t["rects"]:
        d.rectangle([r["x"], r["y"], r["x"] + r["w"] - 1, r["y"] + r["h"] - 1],
                    outline=(255, 0, 0))

    # ellipse (1px red outline)
    if t.get("ellipse"):
        cx, cy, rx, ry = t["ellipse"]
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=(255, 0, 0))

    # flows: thin red polyline + blue dot at every vertex
    for i, fl in enumerate(t["flows"]):
        pts = [tuple(p) for p in fl]
        if len(pts) >= 2:
            d.line(pts, fill=(255, 0, 0), width=1)
        for p in pts:
            d.point((p[0] - 1, p[1]), fill=(0, 0, 255))
            d.point((p[0] + 1, p[1]), fill=(0, 0, 255))
            d.point((p[0], p[1] - 1), fill=(0, 0, 255))
            d.point((p[0], p[1] + 1), fill=(0, 0, 255))

    # arrow tips: small red circle
    for a in t.get("arrows", []):
        tx, ty = a["tip"]
        d.ellipse([tx - 4, ty - 4, tx + 4, ty + 4], outline=(255, 0, 0))

    # text bboxes: thin red rectangle
    for key in ("free_texts", "ellipse_texts", "legend_icons"):
        for b in t.get(key, []):
            d.rectangle([b[0], b[1], b[2] - 1, b[3] - 1], outline=(255, 0, 0))
    for b in t.get("box_texts", []):
        box = b["text"]
        d.rectangle([box[0], box[1], box[2] - 1, box[3] - 1], outline=(255, 0, 0))

    im.save(out)
    print("wrote", out)


if __name__ == "__main__":
    main()

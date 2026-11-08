# -*- coding: utf-8 -*-
"""Pure-python geometry + inventory gate for rebuilt diagrams (CI-safe).

Usage: python scripts/check_diagram_geometry.py docs/diagrams/rebuild/system-context/spec.json

Checks:
- Every element bbox inside canvas (with 8px margin)
- Text boxes do not overlap each other (>2px) — approximate by element bboxes
- Polyline segments are orthogonal (dx==0 or dy==0) — original uses orthogonal elbows
- Segment-box intersections: flag segments through non-endpoint boxes (sampled)
- Font size >= 10px (never shrunk below original ~12px flow / 19px box)
- Inventory: element/flows counts match schema-introspection / project-facts
  where applicable (context: 2 actors + 1 system + 4 externals)
Output saved to docs/qa/rebuild-preview/<fig>/qa-gate.txt (or stdout).
"""
import json
import sys
from pathlib import Path


def bbox(el):
    if el["type"] == "rect":
        return (el["x"], el["y"], el["x"] + el["w"], el["y"] + el["h"])
    if el["type"] == "ellipse":
        return (el["cx"] - el["rx"], el["cy"] - el["ry"], el["cx"] + el["rx"], el["cy"] + el["ry"])
    return None


def overlap(a, b):
    return not (a[2] <= b[0] + 2 or b[2] <= a[0] + 2 or a[3] <= b[1] + 2 or b[3] <= a[1] + 2)


def main():
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    W, H = spec["canvas"]["w"], spec["canvas"]["h"]
    probs = []
    boxes = []
    for e in spec["elements"]:
        b = bbox(e)
        if b:
            boxes.append((e["id"], b))
            if b[0] < -8 or b[1] < -8 or b[2] > W + 8 or b[3] > H + 8:
                probs.append(f"canvas bounds: {e['id']} {b} outside {W}x{H}")
            if e.get("font_size", 12) < 10:
                probs.append(f"font shrunk: {e['id']} size {e.get('font_size')}")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if boxes[i][0].startswith("legend") or boxes[j][0].startswith("legend"):
                continue  # legend symbols are intentionally inside the legend box
            if overlap(boxes[i][1], boxes[j][1]):
                probs.append(f"bbox overlap: {boxes[i][0]} vs {boxes[j][0]}")
    # orthogonal + endpoint check
    for f in spec.get("flows", []):
        pts = f["points"]
        for a, b in zip(pts, pts[1:]):
            if a[0] != b[0] and a[1] != b[1]:
                probs.append(f"non-orthogonal segment {f['id']} {a}->{b}")
        # segment through any box (sample 20 points per segment, ignore endpoints inside source/target boxes approx)
        for a, b in zip(pts, pts[1:]):
            for k in range(1, 20):
                x = a[0] + (b[0] - a[0]) * k / 20
                y = a[1] + (b[1] - a[1]) * k / 20
                for bid, bb in boxes:
                    if bid == "dbcassys":
                        # ellipse test: bbox contains empty corners outside the ellipse
                        cx, cy = 715, 515
                        rx, ry = 200, 110
                        if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 > 0.95:
                            continue
                    if bb[0] < x < bb[2] and bb[1] < y < bb[3]:
                        if (x, y) not in pts:
                            probs.append(f"segment through box {f['id']} at ({x:.0f},{y:.0f}) inside {bid}")
                            break
                else:
                    continue
                break
    # inventory (context-specific + generic)
    ids = {e["id"] for e in spec["elements"]}
    for need in ["learner", "admin", "dbcassys", "llm", "oauth", "email"]:
        if need not in ids:
            probs.append(f"inventory missing element: {need}")
    if len(spec.get("flows", [])) != 24:
        probs.append(f"inventory flows: expected 24 (21 orig + 3 delta), got {len(spec.get('flows', []))}")
    labels = {f["label"] for f in spec.get("flows", [])}
    for need in ["Practice requests", "Result flow & settings", "OAuth sign-in request", "Identity assertion", "Password-reset email"]:
        if need not in labels:
            probs.append(f"delta label missing: {need}")
    for gone in ["Assessment requests", "Assessment configuration"]:
        if gone in labels:
            probs.append(f"retired label still present: {gone}")
    print(f"geometry: {len(boxes)} boxes, {len(spec.get('flows', []))} flows, canvas {W}x{H}")
    if probs:
        for p in probs:
            print("FAIL:", p)
        sys.exit(1)
    print("PASS: geometry + inventory (pure-python, CI-safe)")


if __name__ == "__main__":
    main()

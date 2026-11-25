# -*- coding: utf-8 -*-
"""Check the five rendered PDFs for page counts, empty pages and margin overflow.

Usage: py scripts/verify_final_pdfs.py
Writes docs/submission/final/verification/pdf-checks.json
"""
from __future__ import annotations

import json
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "docs/submission/final"
RENDERED = FINAL / "rendered"
OUT = FINAL / "verification" / "pdf-checks.json"
CM = 28.3464567
LEFT, RIGHT, TOP, BOTTOM = 3.5 * CM, 2.0 * CM, 2.0 * CM, 2.0 * CM
TOL = 4.0


def page_margins(page):
    w, h = page.rect.width, page.rect.height
    # landscape pages keep the same physical margins
    return LEFT, w - RIGHT, TOP, h - BOTTOM


def main():
    results = {}
    for pdf in sorted(RENDERED.glob("C1SE.70_*_DBCAS_ver1.3.pdf")):
        doc = pymupdf.open(pdf)
        pages = []
        near_empty = []
        overflow = []
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            imgs = page.get_images(full=True)
            img_area = 0.0
            for im in imgs:
                try:
                    for rect in page.get_image_rects(im[0]):
                        img_area += rect.width * rect.height
                except Exception:
                    pass
            if len(text) < 100 and img_area < 0.10 * page.rect.width * page.rect.height:
                near_empty.append(i + 1)
            left, right, top, bottom = page_margins(page)
            bad_text = []
            if i > 0:  # cover is allowed its own geometry
                for block in page.get_text("blocks"):
                    x0, y0, x1, y1 = block[:4]
                    if y0 < top - TOL or y1 > bottom + TOL:
                        continue  # running header/footer live in the margins
                    if x1 > right + TOL or x0 < left - TOL:
                        bad_text.append([round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1), block[4][:50]])
                bad_images = []
                for im in imgs:
                    try:
                        for rect in page.get_image_rects(im[0]):
                            if rect.y0 < top - 20 or rect.y1 > bottom + 20:
                                continue  # cover logo / decorative image
                            if rect.x1 > right + 20 or rect.x0 < left - 20:
                                bad_images.append([round(rect.x0, 1), round(rect.y0, 1), round(rect.x1, 1), round(rect.y1, 1)])
                    except Exception:
                        pass
                if bad_text or bad_images:
                    overflow.append({"page": i + 1, "text": bad_text[:5], "images": bad_images[:5]})
            pages.append({
                "page": i + 1,
                "width_pt": round(page.rect.width, 1),
                "height_pt": round(page.rect.height, 1),
                "chars": len(text),
                "image_area_ratio": round(img_area / (page.rect.width * page.rect.height), 3),
            })
        results[pdf.name] = {
            "pages": doc.page_count,
            "near_empty": near_empty,
            "overflow": overflow,
            "page_info": pages,
        }
        doc.close()
        print(f"{pdf.name}: {results[pdf.name]['pages']} pages; near-empty={near_empty}; overflow pages={len(overflow)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

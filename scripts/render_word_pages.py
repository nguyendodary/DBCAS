# -*- coding: utf-8 -*-
"""Render the Word-exported PDF pages that contain the inserted diagrams."""
import re
import sys
from pathlib import Path

import fitz

PATTERNS = {
    "proposal": [
        "Figure 2: DBCAS System Context Diagram",
        "Figure 3: DBCAS Logical System Architecture Diagram",
        "Figure 4: Evidence-based Competency & Gap Evaluation Pipeline",
    ],
    "architecture": [
        "Figure 1. Use Case Diagram",
        "Figure 2. System Context Diagram",
        "Figure 3. Container Diagram",
        "Figure 4 (1/2)",
        "Figure 4 (2/2)",
        "Figure 5. Module View",
        "Figure 6. Allocation View",
        "Figure 7. Entity Relationship Diagram",
        "Figure 8. Table Relationship Diagram (1/5)",
        "Figure 8. Table Relationship Diagram (2/5)",
        "Figure 8. Table Relationship Diagram (3/5)",
        "Figure 8. Table Relationship Diagram (4/5)",
        "Figure 8. Table Relationship Diagram (5/5)",
    ],
    "database": [
        "Figure 1: Entity Relationship Diagram",
        "Figure 2: Table Relationship Diagram (1/5)",
        "Figure 2: Table Relationship Diagram (2/5)",
        "Figure 2: Table Relationship Diagram (3/5)",
        "Figure 2: Table Relationship Diagram (4/5)",
        "Figure 2: Table Relationship Diagram (5/5)",
    ],
}


def norm(text):
    return re.sub(r"\s+", " ", text)


def main(name):
    pdf = Path(r"C:\tmp\dbcas_word") / (name + ".pdf")
    out = Path(r"C:\tmp\dbcas_word") / (name + "_pages")
    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    print(name, "pages", len(doc))
    pats = PATTERNS[name]
    found = {}
    for pno in range(len(doc)):
        text = norm(doc[pno].get_text())
        for pat in pats:
            if pat in text:
                found.setdefault(pat, []).append(pno + 1)
    for pat in pats:
        pages = found.get(pat, [])
        print("%-55s -> %s" % (pat, pages))
        for p in pages:
            pix = doc[p - 1].get_pixmap(matrix=fitz.Matrix(2, 2))
            f = out / ("p%03d.png" % p)
            pix.save(f)
    print("rendered", len(list(out.glob("*.png"))), "page images to", out)


if __name__ == "__main__":
    main(sys.argv[1])

# -*- coding: utf-8 -*-
"""Compact table dump: one line per row, deduplicated cells."""
import json
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
slug = sys.argv[1]
rows = json.loads((here / f"{slug}-tables.json").read_text(encoding="utf-8"))
last = None
for r in rows:
    cells = r["cells"]
    # collapse merged duplicates
    out = []
    for c in cells:
        if not out or out[-1] != c:
            out.append(c)
    line = f"T{r['table']}R{r['row']}: " + " | ".join(out)
    if line != last:
        print(line)
    last = line

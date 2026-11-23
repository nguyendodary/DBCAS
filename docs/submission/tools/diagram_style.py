"""Shared diagram style extracted from the shipped v1.2 figures.

TRD values come from docs/diagrams/rebuild/trd/spec.json (41-card pages) and
the continuation pages in the submitted v1.2 docx.  ERD values come from
docs/diagrams/rebuild/erd/spec.json and the 2/2 continuation page.  C4 colours
come from docs/diagrams/rebuild/container/container.svg.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

TRD = {
    "canvas": (3440, 2080),
    "font_family": "Arial",
    "columns": 4,
    "x": [40, 890, 1740, 2590],
    "card_width": 795,
    "header_height": 74,
    "row_height": 72,
    "row_gap": 60,
    "top": 42,
    "title_size": 38,
    "name_size": 32,
    "marker_size": 22,
    "type_size": 24,
    "stub_size": 24,
    "legend_width": 795,
    "legend_height": 432,
    "colors": {
        "body": "#FFFFFF",
        "header": "#E8E8E8",
        "stroke": "#1A1A1A",
        "separator": "#DCDCDC",
        "shadow": "#B8B8B8",
        "incoming": "#0B6B3A",
        "outgoing": "#1F3A93",
        "legacy": "#7A0000",
        "paper": "#FFFFFF",
    },
}

ERD = {
    "canvas": (4300, 1677),
    "font_family": "Arial, Helvetica, sans-serif",
    "columns": 4,
    "entity_width": 500,
    "entity_height": 80,
    "x": [200, 1250, 2300, 3350],
    "y": [120, 310, 500, 690, 880, 1070, 1260],
    "title_size": 28,
    "key_size": 22,
    "colors": {
        "body": "#FFFFFF",
        "stroke": "#1A1A1A",
        "ink": "#222222",
        "paper": "#FFFFFF",
    },
}

C4 = {
    "person": "#08427B",
    "container": "#1168BD",
    "container_stroke": "#0B4884",
    "external": "#999999",
    "external_stroke": "#6B6B6B",
    "ink": "#222222",
}

LEGEND_COUNTS = "67 tables \u00b7 561 columns \u00b7 122 FKs \u00b7 28 migrations"


def chrome_path():
    candidates = [
        os.environ.get("CHROME_PATH"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    return next((c for c in candidates if c and Path(c).exists()), None)


def render_svg(svg, png, width, height):
    """Render at the exact CSS pixel size, preferring Chrome like the repo renderer."""
    svg, png = Path(svg).resolve(), Path(png).resolve()
    chrome = chrome_path()
    if chrome:
        url = "file:///" + svg.as_posix()
        result = subprocess.run([
            chrome, "--headless", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--default-background-color=FFFFFFFF", f"--window-size={width},{height}",
            f"--screenshot={png}", url,
        ], capture_output=True, text=True)
        if result.returncode == 0 and png.exists():
            return png
    import fitz
    document = fitz.open(svg)
    page = document[0]
    page.get_pixmap(matrix=fitz.Matrix(width / page.rect.width, height / page.rect.height)).save(png)
    document.close()
    return png


def trd_page_count(tables: int, per_page: int = 10) -> int:
    """Original pages were 10/11/7/7/6; continuation pages use 4-6."""
    return max(1, (tables + per_page - 1) // per_page)

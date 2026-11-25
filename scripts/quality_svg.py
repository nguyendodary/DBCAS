# -*- coding: utf-8 -*-
"""Small SVG drawing kit for the DBCAS ver1.4 document figures.

The kit fixes one visual language for every figure in the five documents:
white background, Arial labels, #23A2D9 / #083F75 (the blue pair measured in
the FITAI C4 diagrams), 2 px rules and 8 px corner radii.  It emits SVG only;
scripts/rasterize_figures.mjs turns the SVG into 300 dpi PNG for Word.
"""
from __future__ import annotations

import html
import math
from pathlib import Path

NAVY = "#083F75"
BLUE = "#23A2D9"
LIGHT = "#EAF4FB"
MID = "#D6EAF8"
BORDER = "#4472C4"
GREY = "#F2F2F2"
GREY_BORDER = "#B8C4D0"
TEXT = "#1F2937"
MUTED = "#52657A"
AMBER = "#C55A11"
AMBER_FILL = "#FBE5D6"
GREEN = "#2E7D32"
WHITE = "#FFFFFF"

FONT = "Arial, Helvetica, sans-serif"
MONO = "Consolas, 'Courier New', monospace"


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def wrap(text: str, width: int) -> list[str]:
    """Greedy word wrap for diagram labels."""
    words = str(text).split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


class SVG:
    def __init__(self, width: int, height: int, title: str, desc: str = ""):
        self.width, self.height = width, height
        self.parts: list[str] = []
        self.defs: list[str] = []
        self.marker("arrow", NAVY)
        self.marker("arrow-blue", BLUE)
        self.marker("arrow-grey", MUTED)
        self.parts.append(
            f'<rect width="{width}" height="{height}" fill="{WHITE}"/>'
        )
        self.text(40, 62, title, 54, NAVY, bold=True)
        if desc:
            self.text(42, 104, desc, 32, MUTED)

    def marker(self, name: str, color: str):
        self.defs.append(
            f'<marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
            f'<path d="M0 0 L10 5 L0 10 z" fill="{color}"/></marker>'
        )

    def add(self, fragment: str):
        self.parts.append(fragment)

    def rect(self, x, y, w, h, *, fill=WHITE, stroke=BORDER, sw=2, rx=10,
             dash=None, opacity=None):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        if opacity is not None:
            extra += f' fill-opacity="{opacity}"'
        self.add(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{extra}/>'
        )

    def line(self, x1, y1, x2, y2, *, color=NAVY, sw=2, dash=None, marker=None):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        end = f' marker-end="url(#{marker})"' if marker else ""
        self.add(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{sw}"{extra}{end}/>'
        )

    def path(self, d, *, color=NAVY, sw=2, fill="none", dash=None, marker=None):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        end = f' marker-end="url(#{marker})"' if marker else ""
        self.add(
            f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{sw}"'
            f'{extra}{end}/>'
        )

    def text(self, x, y, value, size=32, color=TEXT, *, bold=False,
             anchor="start", italic=False, family=FONT, opacity=None):
        weight = ' font-weight="bold"' if bold else ""
        style = ' font-style="italic"' if italic else ""
        extra = f' opacity="{opacity}"' if opacity is not None else ""
        self.add(
            f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'fill="{color}" text-anchor="{anchor}"{weight}{style}{extra}>'
            f'{esc(value)}</text>'
        )

    def lines(self, x, y, values, size=30, color=TEXT, *, leading=None,
              anchor="start", bold=False):
        leading = leading or int(size * 1.28)
        for index, value in enumerate(values):
            self.text(x, y + index * leading, value, size, color,
                      anchor=anchor, bold=bold)

    def pill(self, x, y, w, h, label, *, fill=LIGHT, stroke=BORDER,
             size=28, color=NAVY, bold=False):
        self.rect(x, y, w, h, fill=fill, stroke=stroke, rx=h // 2)
        self.text(x + w / 2, y + h / 2 + size * 0.35, label, size, color,
                  anchor="middle", bold=bold)

    def actor(self, x, y, label, color=NAVY):
        """Stick figure with the name below; x,y is the top of the head."""
        self.add(
            f'<circle cx="{x}" cy="{y + 24}" r="20" fill="none" '
            f'stroke="{color}" stroke-width="3"/>'
        )
        self.line(x, y + 44, x, y + 104, color=color, sw=3)
        self.line(x - 34, y + 66, x + 34, y + 66, color=color, sw=3)
        self.line(x, y + 104, x - 28, y + 148, color=color, sw=3)
        self.line(x, y + 104, x + 28, y + 148, color=color, sw=3)
        self.text(x, y + 186, label, 32, color, anchor="middle", bold=True)

    def cylinder(self, x, y, w, h, title, subtitle=""):
        ry = 16
        self.add(
            f'<path d="M{x} {y + ry} A{w/2} {ry} 0 0 1 {x+w} {y+ry} '
            f'L{x+w} {y+h-ry} A{w/2} {ry} 0 0 1 {x} {y+h-ry} Z" '
            f'fill="{BLUE}" stroke="{NAVY}" stroke-width="2"/>'
        )
        self.add(
            f'<ellipse cx="{x+w/2}" cy="{y+ry}" rx="{w/2}" ry="{ry}" '
            f'fill="{LIGHT}" stroke="{NAVY}" stroke-width="2"/>'
        )
        self.text(x + w / 2, y + h / 2 - 2, title, 32, WHITE,
                  anchor="middle", bold=True)
        if subtitle:
            self.text(x + w / 2, y + h / 2 + 32, subtitle, 24, WHITE,
                      anchor="middle")

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        head = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" '
            f'height="{self.height}" viewBox="0 0 {self.width} {self.height}" '
            f'role="img">\n<defs>{"".join(self.defs)}</defs>\n'
        )
        path.write_text(head + "\n".join(self.parts) + "\n</svg>\n",
                        encoding="utf-8")
        return path


def crow(svg: SVG, x: float, y: float, direction: str = "left",
         *, color=NAVY, size=18):
    """Draw a crow's-foot many-end at (x,y), opening towards direction."""
    if direction == "left":
        points = [(x, y), (x - size, y - size * 0.6),
                  (x, y), (x - size, y),
                  (x, y), (x - size, y + size * 0.6)]
    elif direction == "right":
        points = [(x, y), (x + size, y - size * 0.6),
                  (x, y), (x + size, y),
                  (x, y), (x + size, y + size * 0.6)]
    elif direction == "up":
        points = [(x, y), (x - size * 0.6, y - size),
                  (x, y), (x, y - size),
                  (x, y), (x + size * 0.6, y - size)]
    else:
        points = [(x, y), (x - size * 0.6, y + size),
                  (x, y), (x, y + size),
                  (x, y), (x + size * 0.6, y + size)]
    for i in range(0, len(points), 2):
        svg.line(points[i][0], points[i][1], points[i + 1][0],
                 points[i + 1][1], color=color, sw=2)


def card_label(svg: SVG, x, y, text, *, anchor="middle"):
    width = 26 + 18 * len(text)
    svg.rect(x - width / 2, y - 22, width, 34, fill=WHITE, stroke=WHITE,
             sw=0, rx=4)
    svg.text(x, y + 2, text, 26, MUTED, anchor="middle", bold=True)

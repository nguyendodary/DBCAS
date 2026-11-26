# -*- coding: utf-8 -*-
"""Draw the one genuinely-new figure in the original black-line/light-grey style.

The academic figures are restored byte-for-byte from Documents/Final-ver1.3.
This diagram has no baseline equivalent, so it is new and reuses the
baseline palette/line/font conventions: white ground, #F2F2F2 fill, black 2 px
outline, Arial, black arrows, no colour accents.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/submission/final/assets/figures"

FILL = (242, 242, 242)
LINE = (0, 0, 0)
TEXT = (0, 0, 0)
WHITE = (255, 255, 255)


def font(size, bold=False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype("C:/Windows/Fonts/" + name, size)


def wrap(draw, text, fnt, max_width):
    words = text.split()
    lines, line = [], ""
    for word in words:
        trial = (line + " " + word).strip()
        if draw.textbbox((0, 0), trial, font=fnt)[2] <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def box(draw, xy, title, body, title_size=30, body_size=24, radius=18):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=FILL, outline=LINE, width=3)
    tf, bf = font(title_size, True), font(body_size)
    lines = wrap(draw, body, bf, (x1 - x0) - 40)
    total = title_size + 10 + len(lines) * (body_size + 6)
    y = y0 + ((y1 - y0) - total) / 2
    tw = draw.textbbox((0, 0), title, font=tf)[2]
    draw.text(((x0 + x1 - tw) / 2, y), title, font=tf, fill=TEXT)
    y += title_size + 10
    for line in lines:
        lw = draw.textbbox((0, 0), line, font=bf)[2]
        draw.text(((x0 + x1 - lw) / 2, y), line, font=bf, fill=TEXT)
        y += body_size + 6


def arrow(draw, start, end, dashed=False, width=3):
    if dashed:
        # simple dashed shaft
        x0, y0 = start
        x1, y1 = end
        import math
        length = math.hypot(x1 - x0, y1 - y0)
        if length == 0:
            return
        ux, uy = (x1 - x0) / length, (y1 - y0) / length
        pos = 0.0
        while pos < length - 18:
            a = (x0 + ux * pos, y0 + uy * pos)
            b = (x0 + ux * min(pos + 12, length - 18), y0 + uy * min(pos + 12, length - 18))
            draw.line([a, b], fill=LINE, width=width)
            pos += 22
    else:
        draw.line([start, end], fill=LINE, width=width)
    import math
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 15
    p1 = (end[0] - size * math.cos(ang - 0.45), end[1] - size * math.sin(ang - 0.45))
    p2 = (end[0] - size * math.cos(ang + 0.45), end[1] - size * math.sin(ang + 0.45))
    draw.polygon([end, p1, p2], fill=LINE)


def title(draw, text, sub, width):
    tf, sf = font(42, True), font(24)
    tw = draw.textbbox((0, 0), text, font=tf)[2]
    draw.text(((width - tw) / 2, 28), text, font=tf, fill=TEXT)
    sw = draw.textbbox((0, 0), sub, font=sf)[2]
    draw.text(((width - sw) / 2, 86), sub, font=sf, fill=TEXT)


def backend_layering():
    W, H = 3000, 1650
    im = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(im)
    title(d, "Backend layering and dependency direction",
          "One-way dependencies: presentation -> API -> data and execution", W)
    # four tiers
    box(d, (520, 170, 2480, 390), "Presentation tier — React 19 single-page application",
        "Pages, components, hooks and i18n catalogues; the SPA calls the API only and never reaches PostgreSQL directly.")
    box(d, (520, 470, 2480, 800), "API tier — FastAPI application",
        "Routers own HTTP paths, request models, authentication and dependencies.\n"
        "Services own use cases, transactions and business rules.\n"
        "Repositories own SQLAlchemy queries and database locks.")
    box(d, (520, 880, 2480, 1090), "Data tier — PostgreSQL 17",
        "67 tables, 561 columns and 28 forward-only migrations; the API is the only application client.")
    box(d, (520, 1170, 2480, 1440), "Execution tier — isolated SQL sandbox",
        "Ephemeral Docker PostgreSQL; read-only learner role; no network; 256 MB; one CPU; 3 s statement timeout.")
    for x in (1500,):
        arrow(d, (x, 390), (x, 468))
        arrow(d, (x, 800), (x, 878))
        arrow(d, (x, 1090), (x, 1168))
    # side note
    box(d, (80, 880, 450, 1090), "Review rule",
        "No repository imports a service; no service imports a router.", 24, 20)
    d.text((80, 1500), "Dependency direction is checked in review and in the layered import audit.", font=font(22), fill=TEXT)
    im.save(OUT / "backend-layering.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    backend_layering()
    print("wrote backend-layering.png")

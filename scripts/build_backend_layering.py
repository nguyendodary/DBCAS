# -*- coding: utf-8 -*-
"""Build a legible backend-layering diagram for the Code Standards document."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/submission/final/assets/figures"
NAVY = "#083F75"
BLUE = "#23A2D9"
LIGHT = "#EAF4FB"
MID = "#D6EAF8"
AMBER = "#C55A11"
GREY = "#F2F2F2"
BORDER = "#4472C4"
TEXT = "#1F2937"
MUTED = "#52657A"
FONT = "Arial, Helvetica, sans-serif"


def main():
    W, H = 1000, 460
    p = [f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    p.append(f'<text x="24" y="36" font-family="{FONT}" font-size="26" font-weight="bold" fill="{NAVY}">Backend layering and dependency direction</text>')
    p.append(f'<text x="24" y="64" font-family="{FONT}" font-size="17" fill="{MUTED}">HTTP contract → use case and transaction → query and lock → PostgreSQL. Dependencies point one way; the arrow is enforced in review.</text>')
    boxes = [
        (40, 130, 190, 150, "Router", "path, status code, request/response schema, dependency"),
        (300, 130, 190, 150, "Service", "use case, transaction boundary, error code"),
        (560, 130, 190, 150, "Repository", "query, lock, pagination"),
        (820, 130, 150, 150, "PostgreSQL 17", "SQLAlchemy / psycopg"),
    ]
    for i, (x, y, w, h, title, sub) in enumerate(boxes):
        color = LIGHT if i % 2 == 0 else MID
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{color}" stroke="{NAVY}" stroke-width="2.5"/>')
        p.append(f'<text x="{x + w / 2}" y="{y + 46}" font-family="{FONT}" font-size="24" font-weight="bold" fill="{NAVY}" text-anchor="middle">{title}</text>')
        words = sub.split()
        lines, cur = [], ""
        for word in words:
            cand = (cur + " " + word).strip()
            if len(cand) <= 22 or not cur:
                cur = cand
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        for j, line in enumerate(lines):
            p.append(f'<text x="{x + w / 2}" y="{y + 82 + j * 24}" font-family="{FONT}" font-size="16" fill="{TEXT}" text-anchor="middle">{line}</text>')
    for x1, x2 in ((230, 300), (490, 560), (750, 820)):
        p.append(f'<line x1="{x1}" y1="205" x2="{x2 - 8}" y2="205" stroke="{AMBER}" stroke-width="3" marker-end="url(#arrow)"/>')
    p.append('<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#C55A11"/></marker></defs>')
    # side notes
    p.append(f'<rect x="300" y="320" width="450" height="72" rx="8" fill="{GREY}" stroke="{BORDER}" stroke-width="1.2"/>')
    p.append(f'<text x="316" y="348" font-family="{FONT}" font-size="18" font-weight="bold" fill="{NAVY}">Model / schema</text>')
    p.append(f'<text x="316" y="374" font-family="{FONT}" font-size="15" fill="{TEXT}">table mapping, validation and serialisation; no business rules</text>')
    p.append(f'<rect x="40" y="320" width="220" height="72" rx="8" fill="{GREY}" stroke="{BORDER}" stroke-width="1.2"/>')
    p.append(f'<text x="56" y="348" font-family="{FONT}" font-size="18" font-weight="bold" fill="{NAVY}">Security / config</text>')
    p.append(f'<text x="56" y="374" font-family="{FONT}" font-size="15" fill="{TEXT}">JWT, roles, settings</text>')
    p.append(f'<text x="24" y="432" font-family="{FONT}" font-size="15" fill="{MUTED}">Measured exception: six router handlers still query the session directly; they are listed as known debt in §4, not as an accepted pattern.</text>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">' + "".join(p) + "</svg>"
    (OUT / "backend-layering.svg").write_text(svg, encoding="utf-8")
    print(f"built {OUT / 'backend-layering.svg'}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Build a legible A4-width Gantt roadmap from the Proposal Table 13 schedule.

Canvas 1000x620 px is displayed at 15.5 cm, so 18 px text prints at about
7.9 pt and 16 px text at about 7.0 pt. Dates are the official Table 13 rows.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/submission/final/assets/figures"
NAVY = "#083F75"
BLUE = "#23A2D9"
LIGHT = "#D6EAF8"
MID = "#EAF4FB"
AMBER = "#C55A11"
GREEN = "#2E7D32"
GREY = "#F2F2F2"
BORDER = "#B8C4D0"
TEXT = "#1F2937"
MUTED = "#52657A"
WHITE = "#FFFFFF"
FONT = "Arial, Helvetica, sans-serif"
FONT_PATH = Path("C:/Windows/Fonts/arial.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/arialbd.ttf")


def esc(v):
    return (str(v).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def width(text, size, bold=False):
    path = FONT_BOLD if bold else FONT_PATH
    return ImageFont.truetype(str(path), size).getlength(str(text))


ROWS = [
    ("Preparation", "28/07 – 14/08", date(2026, 7, 28), date(2026, 8, 14), "team, repositories, research"),
    ("Advisor assignment", "10/08 – 16/08", date(2026, 8, 10), date(2026, 8, 16), "mentor and scope"),
    ("Proposal drafting", "17/08 – 23/08", date(2026, 8, 17), date(2026, 8, 23), "title, problem, SMART"),
    ("Proposal submission", "24/08 – 05/09", date(2026, 8, 24), date(2026, 9, 5), "v1.1 Word + PDF"),
    ("Sprint 1 — architecture and data", "14/09 – 27/09", date(2026, 9, 14), date(2026, 9, 27), "schema, concept model"),
    ("Sprint 2 — identity and MCQ", "28/09 – 11/10", date(2026, 9, 28), date(2026, 10, 11), "JWT, roles, MCQ, SQL editor"),
    ("Sprint 3 — sandbox and AI", "12/10 – 25/10", date(2026, 10, 12), date(2026, 10, 25), "sandbox, rubric, bank"),
    ("Midterm buffer", "26/10 – 31/10", date(2026, 10, 26), date(2026, 10, 31), "integration and rehearsal"),
    ("Midterm review", "01/11 – 07/11", date(2026, 11, 1), date(2026, 11, 7), "end-to-end demo"),
    ("Sprint 4 — competency", "08/11 – 22/11", date(2026, 11, 8), date(2026, 11, 22), "scoring, radar, gaps"),
    ("Sprint 5 — plan and analytics", "23/11 – 06/12", date(2026, 11, 23), date(2026, 12, 6), "plan assembly, cohort API"),
    ("Final submission", "10/12 – 13/12", date(2026, 12, 10), date(2026, 12, 13), "freeze, documents, video"),
    ("Capstone defence", "17/12 – 26/12", date(2026, 12, 17), date(2026, 12, 26), "rehearsal and committee"),
]
MONTHS = [("Aug", 8), ("Sep", 9), ("Oct", 10), ("Nov", 11), ("Dec", 12)]


def month_x(day: date, left: float, per_month: float) -> float:
    if day.month < 8:
        return left
    if day.month > 12:
        return left + 5 * per_month
    return left + (day.month - 8) * per_month + (day.day - 1) / 30 * per_month


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    W, H = 1000, 720
    left, label_w = 24, 380
    timeline_x = left + label_w
    per_month = (W - 24 - timeline_x) / 5
    top, row_h = 104, 42
    parts = [f'<rect width="{W}" height="{H}" fill="{WHITE}"/>']
    parts.append(f'<text x="24" y="36" font-family="{FONT}" font-size="28" font-weight="bold" fill="{NAVY}">Agile delivery roadmap</text>')
    parts.append(f'<text x="24" y="58" font-family="{FONT}" font-size="18" fill="{MUTED}">Five two-week sprints, four status reports and two faculty milestones · 28/07/2026 – 26/12/2026</text>')
    # month header
    for i, (name, _) in enumerate(MONTHS):
        x = timeline_x + i * per_month
        parts.append(f'<rect x="{x:.0f}" y="{top - 26}" width="{per_month:.0f}" height="24" fill="{LIGHT}" stroke="{BORDER}" stroke-width="0.6"/>')
        parts.append(f'<text x="{x + per_month / 2:.0f}" y="{top - 8}" font-family="{FONT}" font-size="16" font-weight="bold" fill="{NAVY}" text-anchor="middle">{name}</text>')
    # grid and rows
    for i, (name, dates, start, end, note) in enumerate(ROWS):
        y = top + i * row_h
        if i % 2 == 0:
            parts.append(f'<rect x="24" y="{y}" width="{W - 48}" height="{row_h}" fill="{MID}" stroke="none"/>')
        parts.append(f'<line x1="24" y1="{y + row_h}" x2="{W - 24}" y2="{y + row_h}" stroke="{BORDER}" stroke-width="0.5"/>')
        parts.append(f'<text x="30" y="{y + 18}" font-family="{FONT}" font-size="20" font-weight="bold" fill="{TEXT}">{esc(name)}</text>')
        parts.append(f'<text x="30" y="{y + 35}" font-family="{FONT}" font-size="14" fill="{MUTED}">{esc(dates)} · {esc(note)}</text>')
        # bar
        sx = month_x(start, timeline_x, per_month)
        ex = month_x(end, timeline_x, per_month)
        color = GREEN if name in ("Midterm review", "Capstone defence") else (AMBER if name in ("Proposal submission", "Final submission") else BLUE)
        if ex - sx < 5:
            ex = sx + 5
        ex = min(ex, W - 26)
        parts.append(f'<rect x="{sx:.0f}" y="{y + 11}" width="{ex - sx:.0f}" height="20" rx="4" fill="{color}" stroke="{NAVY}" stroke-width="0.7"/>')
    # milestone lines and labels
    for md, label, color, anchor in [(date(2026, 11, 1), "MIDTERM", AMBER, "start"), (date(2026, 12, 17), "DEFENCE", GREEN, "end")]:
        x = month_x(md, timeline_x, per_month)
        parts.append(f'<line x1="{x:.0f}" y1="{top - 2}" x2="{x:.0f}" y2="{top + len(ROWS) * row_h + 4}" stroke="{color}" stroke-width="2" stroke-dasharray="5,4"/>')
        dx = 4 if anchor == "start" else -4
        parts.append(f'<text x="{x + dx:.0f}" y="{top - 30}" font-family="{FONT}" font-size="13" font-weight="bold" fill="{color}" text-anchor="{anchor}">{label}</text>')
    # legend
    ly = top + len(ROWS) * row_h + 18
    items = [(BLUE, "Sprint / preparation"), (AMBER, "Submission milestone"), (GREEN, "Faculty milestone")]
    x = 30
    for color, text in items:
        parts.append(f'<rect x="{x}" y="{ly - 12}" width="18" height="12" rx="2" fill="{color}"/>')
        parts.append(f'<text x="{x + 26}" y="{ly}" font-family="{FONT}" font-size="16" fill="{TEXT}">{text}</text>')
        x += 230
    parts.append(f'<text x="30" y="{ly + 24}" font-family="{FONT}" font-size="14" fill="{MUTED}">Status reports: SR1 03/10 · SR2 17/10 · SR3 20/11 · SR4 05/12.</text>')
    parts.append(f'<text x="30" y="{ly + 44}" font-family="{FONT}" font-size="14" fill="{MUTED}">Rows and dates: Proposal §11.2. The faculty milestones are the midterm review and the final defence.</text>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">'
           + "".join(parts) + "</svg>")
    (OUT / "gantt-roadmap.svg").write_text(svg, encoding="utf-8")
    # update manifest entry
    import json
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    for item in manifest["figures"]:
        if item["file"] == "gantt-roadmap.svg":
            item.update({"title": "Agile delivery roadmap", "width": W, "height": H,
                         "source": "Proposal Table 13; docs/academic proposal calendar"})
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"built {OUT / 'gantt-roadmap.svg'} {W}x{H}")


if __name__ == "__main__":
    main()

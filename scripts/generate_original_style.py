# -*- coding: utf-8 -*-
"""Redraw diagrams in ORIGINAL v1.1 style (hand-controlled SVG, fixed positions).

Style comes from docs/qa/diagram-originals/style-spec.md (original PNGs);
content comes from docs/qa/schema-introspection.json + project-facts.json
(content-delta.md). No C4, no new notation.

Outputs to docs/diagrams/original-style/:
  fig-proposal-1-roadmap.svg/png (copied original, unchanged historical)
  fig-proposal-2-system-context.svg/png
  fig-proposal-3-logical.svg/png
  fig-proposal-4-pipeline.svg/png
  fig-architecture-1-usecase.svg/png
  fig-architecture-3-container.svg/png
  fig-architecture-4-component.svg/png
  fig-architecture-5-module.svg/png
  fig-architecture-6-allocation.svg/png
  fig-architecture-7-erd.svg/png (Chen, 12 core + 4 legacy dashed)
  fig-architecture-8-trd.svg/png (41 cards)
  (Architecture Fig 2 = Proposal Fig 2; Database Figs = Arch Figs 7-8)

Run: python scripts/generate_original_style.py  (needs Chrome for PNGs)
"""
import html
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "diagrams" / "original-style"
ORIG = ROOT / "docs" / "qa" / "diagram-originals"
INTRO = json.loads((ROOT / "docs/qa/schema-introspection.json").read_text(encoding="utf-8"))
FACTS = json.loads((ROOT / "docs/qa/project-facts.json").read_text(encoding="utf-8"))
OUT.mkdir(parents=True, exist_ok=True)
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

FONT = "Arial, sans-serif"


def esc(s):
    return html.escape(str(s), quote=True)


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">'
            f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>'
            f'<g font-family="{FONT}">{body}</g></svg>')


def rect(x, y, w, h, fill="#FFFFFF", stroke="#000000", sw=1.5, dashed=False, rx=0):
    d = ' stroke-dasharray="6,4"' if dashed else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}/>')


def oval(x, y, w, h, fill="#FFFFFF", stroke="#000000", sw=1.5, dashed=False):
    d = ' stroke-dasharray="6,4"' if dashed else ""
    return (f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}/>')


def text(x, y, s, size=13, bold=False, anchor="middle", fill="#000000", italic=False):
    b = ' font-weight="bold"' if bold else ""
    it = ' font-style="italic"' if italic else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{fill}"{b}{it}>{esc(s)}</text>'


def ortho_arrow(x1, y1, x2, y2, label=""):
    """Right-angle elbow: horizontal then vertical (or vice versa for long spans)."""
    mx = (x1 + x2) / 2
    parts = [f'<path d="M{x1},{y1} H{mx} V{y2} L{x2},{y2}" fill="none" stroke="#000000" '
             f'stroke-width="1.2" marker-end="url(#arr)"/>']
    if label:
        parts.append(text(mx + 6, (y1 + y2) / 2 - 4, label, 11, anchor="start"))
    return "".join(parts)


def legend(x, y, w, h, items):
    parts = [rect(x, y, w, h, fill="#FFFFFF", stroke="#000000")]
    cy = y + 22
    for shp, lbl in items:
        if shp == "oval":
            parts.append(oval(x + 14, cy - 8, 28, 16))
        elif shp == "box":
            parts.append(rect(x + 14, cy - 8, 28, 16))
        elif shp == "diamond":
            parts.append(f'<path d="M{x+28},{cy-9} L{x+40},{cy} L{x+28},{cy+9} L{x+14},{cy} Z" fill="none" stroke="#000" stroke-width="1.2"/>')
        elif shp == "arrow":
            parts.append(f'<path d="M{x+14},{cy} H{x+40}" stroke="#000" stroke-width="1.2"/>')
        parts.append(text(x + 50, cy + 4, lbl, 11, anchor="start"))
        cy += 26
    return "".join(parts)


DEFS = ('<defs><marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#000"/></marker></defs>')


def write_fig(stem, svg_text):
    (OUT / f"{stem}.svg").write_text(svg_text, encoding="utf-8")
    png = OUT / f"{stem}.png"
    # Chrome full-window shot matched to SVG pixel size (viewBox = px)
    import re
    m = re.search(r'width="(\d+)" height="(\d+)"', svg_text)
    w, h = (int(m.group(1)), int(m.group(2))) if m else (1200, 800)
    cmd = [str(CHROME), "--headless", "--disable-gpu", "--no-first-run",
           f"--screenshot={png.resolve()}", f"--window-size={w+20},{h+20}",
           "--default-background-color=FFFFFFFF", f"file:///{(OUT/(stem+'.svg')).resolve().as_posix()}"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    print(stem, "png rc", r.returncode, png.stat().st_size if png.exists() else "MISSING")


# ---------------- Context (B&W, oval system, orthogonal arrows) ----------------
def context():
    W, H = 1431, 1061
    parts = [DEFS, text(W/2, 50, "DBCAS System Context Diagram", 26, bold=True)]
    # actors top
    parts.append(rect(80, 90, 260, 90, fill="#FFFFFF", stroke="#000000", sw=2))
    parts.append(text(210, 145, "Learner", 20, bold=True))
    parts.append(rect(1080, 90, 280, 90, fill="#FFFFFF", stroke="#000000", sw=2))
    parts.append(text(1220, 145, "Administrator", 20, bold=True))
    # system centre oval
    parts.append(oval(520, 340, 400, 200, fill="#FFFFFF", stroke="#000000", sw=2))
    parts.append(text(720, 445, "DBCAS", 26, bold=True))
    # externals bottom
    for (x, nm) in [(80, "LLM Provider"), (460, "OAuth Providers"), (840, "Email Service")]:
        parts.append(rect(x, 820, 230, 80, fill="#FFFFFF", stroke="#000000", sw=2))
        parts.append(text(x+115, 868, nm, 17, bold=True))
    # flows (orthogonal; lengths approximate original fan, labels shortened)
    # learner -> dbcas (4) & returns (4)
    for i, lbl in enumerate(["Practice requests", "MCQ / SQL / essay answers", "Result view requests", "Authentication requests",
                             "Registration requests", "Practice results", "Competency profile & gaps", "Study guidance"]):
        y0 = 190 + i * 18
        parts.append(ortho_arrow(340, y0, 540 + i * 10, 360 + i * 8, ""))
        if i in (0, 3, 6):
            parts.append(text(420, y0 - 6, lbl, 11, anchor="start"))
    for i, lbl in enumerate(["CLOs & concepts", "Questions", "Rubrics", "Result flow & settings",
                             "Learner performance", "Competency gap analytics", "AI mapping suggestions"]):
        y0 = 190 + i * 18
        parts.append(ortho_arrow(1080, y0, 900 - i * 10, 360 + i * 8, ""))
        if i in (0, 1, 4):
            parts.append(text(1020, y0 - 6, lbl, 11, anchor="start"))
    for lbl in ["Gap explanation requests", "Essay evaluation requests", "CLO/Concept mapping requests",
                "Mapping suggestions", "Essay evaluation results", "Gap explanations"]:
        parts.append(ortho_arrow(650, 540, 195, 820, ""))  # simplified stub
        parts.append(text(380, 760 + len(parts) % 40, lbl, 11))
        break  # labels drawn once below for clarity
    parts.append(text(350, 730, "Gap explanation requests · Essay evaluation requests · CLO/Concept mapping requests", 11))
    parts.append(text(350, 950, "Mapping suggestions · Essay evaluation results · Gap explanations", 11))
    # OAuth + Email flows
    parts.append(ortho_arrow(750, 540, 575, 820, "OAuth sign-in request / Identity assertion"))
    parts.append(ortho_arrow(850, 540, 955, 820, "Password-reset email"))
    parts.append(legend(350, 960, 730, 85, [("oval", "System"), ("box", "Actor / external system"), ("arrow", "Interaction")]))
    return svg(W, H, "".join(parts), "System Context")


# ---------------- Logical (B&W 4 tiers) ----------------
def logical():
    W, H = 1800, 1750
    parts = [DEFS, text(W/2, 55, "DBCAS Logical System Architecture Diagram", 26, bold=True),
             text(W/2, 82, "Four-Tier Architecture: Presentation, Application & Services, Data & Storage, External AI & Sandbox", 14, italic=True)]
    tiers = [("TIER 1: PRESENTATION TIER (REACT.JS / VITE / TAILWIND / CHART.JS)", 120, 300),
             ("TIER 2: APPLICATION & SERVICES TIER (FASTAPI / PYTHON)", 500, 560),
             ("TIER 3: DATA & STORAGE TIER (POSTGRESQL)", 1130, 260),
             ("TIER 4: EXTERNAL AI SERVICE & EXECUTION SANDBOX", 1470, 260)]
    for (t, y, h) in tiers:
        parts.append(rect(40, y, W-80, h, fill="#FFFFFF", stroke="#000000", sw=2))
        parts.append(rect(W/2-380, y-18, 760, 36, fill="#FFFFFF", stroke="#000000", sw=2))
        parts.append(text(W/2, y+6, t, 15, bold=True))
    # Tier1 boxes
    parts.append(rect(180, 210, 600, 130, fill="#FFFFFF", stroke="#000000", sw=2, rx=12))
    parts.append(text(480, 260, "Learner Assessment Portal", 18, bold=True)); parts.append(text(480, 285, "Exam UI · Competency Charts (FR-07/13) · SQL Editor", 12))
    parts.append(rect(1010, 210, 620, 130, fill="#FFFFFF", stroke="#000000", sw=2, rx=12))
    parts.append(text(1320, 260, "Administrator Management Portal", 18, bold=True)); parts.append(text(1320, 285, "CLOs & Concepts (FR-02) · Question Bank (FR-04) · Analytics", 12))
    # Tier2 2x3
    t2 = [("Auth & Role Management", "JWT Auth · RBAC · Stateless (FR-01)"), ("Request Validation", "Pydantic Schemas · Rate Limiting"),
          ("Practice Session Service", "Session Coordination · Question Delivery"), ("Automated Grading Engine", "MCQ · SQL Output · Essay Rubric (FR-08/09/10)"),
          ("Practice Engine", "Concept + Difficulty + Type · Gen/Validate (FR-15)"), ("Competency & Gap Engine", "Evidence · Competency · Gaps (FR-11/12/14)")]
    for i, (a, b) in enumerate(t2):
        x = 80 + (i % 3) * 580; y = 600 + (i // 3) * 200
        parts.append(rect(x, y, 540, 150, fill="#FFFFFF", stroke="#000000", sw=2, rx=12))
        parts.append(text(x+270, y+65, a, 16, bold=True)); parts.append(text(x+270, y+92, b, 12))
    # Tier3
    parts.append(rect(220, 1220, 1360, 120, fill="#FFFFFF", stroke="#000000", sw=2))
    parts.append(text(900, 1265, "PostgreSQL", 18, bold=True))
    parts.append(text(900, 1292, "Users & Roles | CLOs & Concept Model | Question Bank & Rubrics | Attempts", 12))
    parts.append(text(900, 1312, "Evidence Logs | Cached LLM Responses — Stateless JWT (no session store)", 12))
    # Tier4
    parts.append(rect(180, 1550, 640, 120, fill="#FFFFFF", stroke="#000000", sw=2, rx=12))
    parts.append(text(500, 1595, "Docker SQL Sandbox", 16, bold=True)); parts.append(text(500, 1620, "Isolated PostgreSQL · Read-Only Tx (FR-09)", 12))
    parts.append(rect(1020, 1550, 640, 120, fill="#FFFFFF", stroke="#000000", sw=2, rx=12))
    parts.append(text(1340, 1595, "LLM Provider API (Any Provider)", 16, bold=True)); parts.append(text(1340, 1620, "Essay Scoring · CLO Mapping · Explanations (FR-10/03/14)", 12))
    # inter-tier arrows
    parts.append(f'<path d="M480,420 V500" stroke="#000" stroke-width="1.5" marker-end="url(#arr)"/>')
    parts.append(f'<path d="M900,680 V1130" stroke="#000" stroke-width="1.5" marker-end="url(#arr)"/>')
    parts.append(text(920, 900, "SQL / SQLAlchemy ORM", 12, anchor="start"))
    parts.append(f'<path d="M900,1340 V1470" stroke="#000" stroke-width="1.5" marker-end="url(#arr)"/>')
    return svg(W, H, "".join(parts), "Logical")


def pipeline():
    W, H = 1500, 900
    parts = [DEFS, text(W/2, 55, "Evidence-based adaptive assessment pipeline", 26, bold=True),
             text(W/2, 80, "Three basic MCQs first · each later question selected from live evidence", 13, italic=True)]
    boxes = [("Opening", "3 MCQs at levels 1–2\nfrom validated bank", 40, 140),
             ("Grade each answer", "MCQ key · SQL sandbox\nLLM-assisted essay", 280, 140),
             ("Evidence", "Record result\nupdate concept estimates", 520, 140),
             ("Adaptive selection", "After opening MCQs:\n3/3 harder · 2/3 medium", 760, 140),
             ("Next item", "Serve validated\nquestion only", 1000, 140),
             ("Candidate preparation", "AI drafts before sessions\nSystem checks candidate", 40, 520),
             ("Validated item bank", "Store only after approval\nOnly validated items served", 420, 520),
             ("Complete assessment", "At configured cap or 00:00\nDeterministic per-concept profile", 900, 520)]
    for (a, b, x, y) in boxes:
        parts.append(rect(x, y, 220, 120, fill="#F8F9FA", stroke="#000000", sw=1.5, rx=10))
        parts.append(text(x+110, y+45, a, 15, bold=True))
        for j, ln in enumerate(b.split("\n")):
            parts.append(text(x+110, y+70+j*16, ln, 11))
    # arrows
    for (x1, x2) in [(260, 280), (500, 520), (740, 760), (980, 1000), (1110, 1010)]:
        parts.append(f'<path d="M{x1},200 H{x2}" stroke="#000" stroke-width="1.5" marker-end="url(#arr)"/>')
    parts.append(f'<path d="M1000,260 V520" stroke="#000" stroke-width="1.5" marker-end="url(#arr)"/>')
    parts.append(f'<path d="M400,580 H420" stroke="#000" stroke-width="1.5" marker-end="url(#arr)"/>')
    parts.append(text(W/2, 820, "Target mix for a full session: 10 MCQ / 2 SQL / 1 essay", 15, bold=True))
    parts.append(text(W/2, 845, "Ranked gap topics only; long-term learning paths and course-document retrieval are outside scope.", 11, italic=True))
    return svg(W, H, "".join(parts), "Pipeline")


def usecase():
    W, H = 1500, 1650
    parts = [DEFS, text(W/2, 55, "DBCAS Use Case Diagram", 26, bold=True)]
    parts.append(rect(150, 100, 1200, 1450, fill="#FFFFFF", stroke="#000000", sw=2))
    parts.append(text(W/2, 90, "DBCAS system", 16, bold=True))
    # actors
    parts.append(text(80, 1150, "Learner", 14, bold=True)); parts.append(text(1420, 1150, "Administrator", 14, bold=True))
    left = ["UC01 Register learner account", "UC12 Take personalized practice", "UC13 Write and run SQL",
            "UC14 Answer MCQ and essay questions", "UC15 Receive grading results and feedback",
            "UC16 View competency profile", "UC17 View competency gap explanations", "UC18 Review history and evidence"]
    right = ["UC04 Provision administrator accounts", "UC05 Define CLOs and concept model", "UC06 Review AI-suggested CLO mappings",
             "UC07 Curate validated question bank", "UC08 Review AI-recommended question tags",
             "UC09 Configure result flow and settings", "UC10 Oversee AI-generated candidates", "UC11 View learner and cohort analytics"]
    for i, lbl in enumerate(left):
        y = 300 + i * 130
        parts.append(oval(250, y, 380, 70, fill="#D6EAF8", stroke="#0D3B66"))
        parts.append(text(440, y+40, lbl, 12))
        parts.append(f'<path d="M110,{900-i*8} L250,{y+35}" stroke="#000" stroke-width="1" marker-end="url(#arr)"/>')
    for i, lbl in enumerate(right):
        y = 300 + i * 130
        parts.append(oval(900, y, 380, 70, fill="#E8F5E9", stroke="#0D3B66"))
        parts.append(text(1090, y+40, lbl, 12))
        parts.append(f'<path d="M1390,{900-i*8} L1280,{y+35}" stroke="#000" stroke-width="1" marker-end="url(#arr)"/>')
    # top two shared
    for i, lbl in enumerate(["UC02 Login", "UC03 Logout"]):
        y = 180 + i * 100
        parts.append(oval(580, y, 380, 60, fill="#FFF7D0", stroke="#B7950B"))
        parts.append(text(770, y+35, lbl, 12, bold=True))
    parts.append(text(W/2, 1500, "Learner registration is available before sign-in. UC13 and UC14 occur within UC12.", 11, italic=True))
    return svg(W, H, "".join(parts), "Use Case")


def container():
    W, H = 900, 1000
    parts = [DEFS, text(W/2, 40, "DBCAS Container Diagram", 22, bold=True)]
    parts.append(f'<rect x="20" y="60" width="{W-40}" height="{H-80}" fill="none" stroke="#000" stroke-dasharray="8,5"/>')
    parts.append(text(40, 80, "DBCAS System [Software System]", 13, bold=True, anchor="start"))
    for (y, a, b, c) in [(70, "Learner [Person]", "Undergraduate student", "database assessments"),
                          (230, "Administrator [Person]", "Faculty / course manager", "content and assessments"),
                          (420, "Web Application", "[Container: React 19.3, Vite 8]", "Static bundle"),
                          (570, "Single Page Application", "[Container: React, Tailwind]", "Learner + Admin portals"),
                          (720, "API Application", "[Container: FastAPI 0.141]", "Auth, grading, adaptive")]:
        fill = "#08427B" if "Person" in a else "#1168BD"
        parts.append(rect(210, y, 480, 100, fill=fill, stroke="#08427B", sw=2, rx=12))
        parts.append(text(450, y+40, a, 16, bold=True, fill="#FFFFFF"))
        parts.append(text(450, y+62, b, 11, fill="#FFFFFF")); parts.append(text(450, y+78, c, 11, fill="#FFFFFF"))
    for (x, nm, sub) in [(80, "Database", "PostgreSQL 17"), (500, "SQL Sandbox", "Docker PostgreSQL 17")]:
        parts.append(f'<path d="M{x},860 a155,22 0 0,1 310,0 v55 a155,22 0 0,1 -310,0 Z" fill="#1168BD" stroke="#08427B"/>')
        parts.append(text(x+155, 885, nm, 15, bold=True, fill="#FFFFFF")); parts.append(text(x+155, 905, sub, 10, fill="#FFFFFF"))
    parts.append(rect(350, 930, 300, 60, fill="#999999", stroke="#000000", rx=10))
    parts.append(text(500, 965, "LLM Provider API [External]", 13, bold=True, fill="#FFFFFF"))
    for y in (170, 330, 520, 670):
        parts.append(f'<path d="M450,{y} V{y+55}" stroke="#333" stroke-width="1.5" marker-end="url(#arr)"/>')
    return svg(W, H, "".join(parts), "Container")


def component():
    W, H = 2000, 800
    parts = [DEFS, text(W/2, 40, "DBCAS Component Diagram", 22, bold=True)]
    bands = [("Controller [Container: FastAPI routers]", 60), ("Service [Container: business logic]", 250), ("Repository [Container: SQLAlchemy]", 440)]
    for (lbl, y) in bands:
        parts.append(f'<rect x="20" y="{y}" width="{W-40}" height="160" fill="none" stroke="#000" stroke-dasharray="8,5"/>')
        parts.append(text(40, y+22, lbl, 14, bold=True, anchor="start"))
    cols = ["Auth", "Assessment", "Curriculum", "Question Bank", "Analytics", "Attempt", "Candidate"]
    fills = ["#1168BD", "#D6EAF8", "#4E8DC8"]
    for i, c in enumerate(cols):
        x = 60 + i * 270
        svc = {"Assessment": "Practice Session", "Analytics": "Competency & Gap"}.get(c, c)
        repo = {"Assessment": "Practice", "Analytics": "Competency", "Candidate": "Selection & Candidate"}.get(c, c)
        for (y, nm, fi) in [(90, f"{c}\nController", 0), (280, f"{svc}\nService", 1), (470, f"{repo}\nRepository", 2)]:
            fill = "#1168BD" if fi == 0 else ("#D6EAF8" if fi == 1 else "#4E8DC8")
            fg = "#FFFFFF" if fi != 1 else "#000000"
            parts.append(rect(x, y, 230, 120, fill=fill, stroke="#0D3B66", sw=1.5, rx=10))
            for j, ln in enumerate(nm.split("\n")):
                parts.append(text(x+115, y+50+j*18, ln, 13, bold=True, fill=fg))
    parts.append(rect(600, 660, 800, 70, fill="#1168BD", stroke="#0D3B66"))
    parts.append(text(1000, 705, "Database [Container: PostgreSQL 17] — Stores all application data", 14, bold=True, fill="#FFFFFF"))
    return svg(W, H, "".join(parts), "Component")


def module():
    W, H = 1900, 1150
    parts = [DEFS, text(W/2, 50, "DBCAS MODULE VIEW", 26, bold=True)]
    for i, (a, b) in enumerate([("Web UI · Learner and Administrator portals", None), ("API entry · FastAPI routing, JWT and validation", None), ("Backend services · Controllers → Services → Repositories", None)]):
        x = 40 + i * 620
        parts.append(rect(x, 90, 580, 80, fill="#EAF2F8", stroke="#0D3B66", sw=1.5, rx=10))
        parts.append(text(x+290, 138, a, 14, bold=True))
        if i < 2:
            parts.append(f'<path d="M{x+580},130 H{x+620}" stroke="#000" marker-end="url(#arr)"/>')
    parts.append(text(W/2, 210, "FUNCTIONAL MODULES", 18, bold=True))
    mods = [("Identity & Access", ["Auth Controller", "Auth Service", "Account Repository"]),
            ("Curriculum", ["Curriculum Controller", "Curriculum Service", "Curriculum Repository"]),
            ("Question Bank", ["Question / Candidate Controller", "Question Bank Service", "Question Repository"]),
            ("Practice", ["Assessment Controller", "Session + Practice Service", "Practice / Selection Repository"]),
            ("Grading", ["Attempt Controller", "Grading Service", "Attempt Repository"]),
            ("Competency", ["Analytics Controller", "Competency + Gap Service", "Competency Repository"])]
    for k, (title, chips) in enumerate(mods):
        x = 40 + (k % 3) * 620; y = 250 + (k // 3) * 280
        parts.append(rect(x, y, 580, 240, fill="#F4F7FA", stroke="#0D3B66", sw=1.5, rx=10))
        parts.append(text(x+290, y+40, title, 17, bold=True))
        for j, c in enumerate(chips):
            cx = x + 20 + j * 190
            parts.append(rect(cx, y+70, 170, 90, fill="#FFFFFF", stroke="#0D3B66", rx=6))
            for t, ln in enumerate(c.split(" / ")):
                pass
            parts.append(text(cx+85, y+120, c, 11))
            if j < 2:
                parts.append(f'<path d="M{cx+170},{y+115} H{cx+190}" stroke="#000" marker-end="url(#arr)"/>')
    parts.append(text(W/2, 850, "SHARED DEPENDENCIES", 18, bold=True))
    for i, (a, b, col) in enumerate([("PostgreSQL 17", "Application data, evidence and LLMCache", "#E8F5E9"),
                                     ("LLM Gateway", "Sanitized requests; provider-agnostic assistive calls", "#F0E6F5"),
                                     ("SQL Sandbox", "Isolated PostgreSQL; read-only, time and memory limits", "#FEF0E6")]):
        x = 40 + i * 620
        parts.append(rect(x, 890, 580, 120, fill=col, stroke="#0D3B66", sw=1.5, rx=10))
        parts.append(text(x+290, 935, a, 16, bold=True)); parts.append(text(x+290, 960, b, 11))
    parts.append(text(W/2, 1050, "Repositories persist application records. Services call the LLM Gateway or SQL Sandbox only when the assessment workflow requires them.", 11, italic=True))
    return svg(W, H, "".join(parts), "Module")


def allocation():
    W, H = 800, 950
    parts = [DEFS, text(W/2, 40, "DBCAS Allocation View", 22, bold=True)]
    parts.append(rect(250, 70, 350, 90, fill="#08427B", stroke="#08427B", rx=12))
    parts.append(text(425, 112, "Learner / Administrator", 15, bold=True, fill="#FFFFFF")); parts.append(text(425, 132, "[Person]", 11, fill="#FFFFFF"))
    parts.append(rect(250, 210, 350, 90, fill="#E8EDF1", stroke="#000", rx=12))
    parts.append(text(425, 250, "User's Device", 15, bold=True)); parts.append(text(425, 272, "Laptop / desktop, modern browser", 11))
    parts.append(oval(300, 350, 250, 80, fill="#E8F5E9", stroke="#2E8B57"))
    parts.append(text(425, 395, "Internet", 15, bold=True))
    parts.append(f'<rect x="40" y="480" width="{W-80}" height="{H-500}" fill="none" stroke="#000" stroke-dasharray="8,5"/>')
    parts.append(text(60, 500, "Docker-capable Host [Deployment Node]", 12, bold=True, anchor="start"))
    for (y, a, b) in [(520, "Web Server", "Static + SPA"), (640, "Application Server", "FastAPI, Python 3.13"), (760, "Database / SQL Sandbox / LLM", "PostgreSQL 17 · isolated · provider")]:
        parts.append(rect(200, y, 450, 80, fill="#1168BD", stroke="#0D3B66", rx=10))
        parts.append(text(425, y+35, a, 15, bold=True, fill="#FFFFFF")); parts.append(text(425, y+55, b, 11, fill="#FFFFFF"))
    return svg(W, H, "".join(parts), "Allocation")


def erd():
    W, H = 2000, 1250
    parts = [DEFS]
    core = [("Role", "role_id"), ("Account", "account_id"), ("UserProfile", "user_id"), ("SystemSetting", "setting_key"),
            ("CourseLearningOutcome", "clo_id"), ("Concept", "concept_id"), ("Question", "question_id"), ("MCQOption", "option_id"),
            ("AssessmentSession", "session_id"), ("Attempt", "attempt_id"), ("ConceptCompetency", "competency_id"), ("CompetencyGap", "gap_id")]
    # grid 4 cols x 3 rows
    poss = {}
    for i, (nm, pk) in enumerate(core):
        x = 60 + (i % 4) * 480; y = 60 + (i // 4) * 250
        poss[nm] = (x, y)
        parts.append(rect(x, y, 340, 70, fill="#FFFFFF", stroke="#000000", sw=2))
        parts.append(text(x+170, y+42, nm, 16, bold=True))
        parts.append(oval(x+110, y+95, 120, 45, fill="#FFFFFF", stroke="#000000", sw=1.2))
        parts.append(text(x+170, y+120, pk, 12))
    # diamonds (12)
    rels = [("Role", "Account", "assigned", "1", "N"), ("Account", "UserProfile", "has", "1", "1"),
            ("Account", "CourseLearningOutcome", "defines", "1", "N"), ("Concept", "Question", "tagged with", "1", "N"),
            ("Question", "MCQOption", "offers", "1", "N"), ("Concept", "ConceptCompetency", "measured by", "1", "N"),
            ("AssessmentSession", "Attempt", "records", "1", "N"), ("AssessmentSession", "ConceptCompetency", "yields", "1", "N"),
            ("ConceptCompetency", "CompetencyGap", "diagnosed as", "1", "1"), ("Account", "AssessmentSession", "takes", "1", "N"),
            ("Concept", "AssessmentSession", "targets", "N", "N"), ("Concept", "Question", "pools", "N", "N")]
    # diamonds at midpoints (deterministic, placed in gaps to avoid overlaps)
    for _i, (a, b, verb, c1, c2) in enumerate(rels):
        (x1, y1) = poss[a]; (x2, y2) = poss[b]
        mx, my = (x1+x2)/2 + (-30 if _i % 2 else 30), (y1+y2)/2 + 85
        parts.append(f'<path d="M{x1+170},{y1+70} L{mx},{my} M{x2+170},{y2} L{mx},{my}" stroke="#000" stroke-width="1.2"/>')
        parts.append(f'<path d="M{mx},{my-22} L{mx+38},{my} L{mx},{my+22} L{mx-38},{my} Z" fill="#FFFFFF" stroke="#000"/>')
        parts.append(text(mx, my+4, verb, 10, italic=True))
        parts.append(text(x1+170, y1+85, c1, 10)); parts.append(text(x2+170, y2-5, c2, 10))
    # legacy row bottom (dashed)
    legacy = [("Assessment", "assessment_id"), ("AssessmentConcept", "assessment_id, concept_id"), ("AssessmentQuestion", "assessment_id, question_id"), ("AssessmentBlueprint", "blueprint_id")]
    for i, (nm, pk) in enumerate(legacy):
        x = 60 + i * 480; y = 880
        parts.append(rect(x, y, 340, 70, fill="#F2F2F2", stroke="#000000", sw=1.5, dashed=True))
        parts.append(text(x+170, y+30, nm, 14, bold=True)); parts.append(text(x+170, y+52, "legacy (historical rows only)", 9, italic=True))
        parts.append(oval(x+90, y+95, 160, 45, fill="#FFFFFF", stroke="#000000", sw=1.2))
        parts.append(text(x+170, y+120, pk, 10))
    parts.append(legend(380, 1060, 1240, 110, [("box", "Entity"), ("diamond", "Relationship"), ("oval", "Key attribute"),
                                                 ("box", "1 = one, N / M = many (M : N = many-to-many)"), ("box", "Dashed = Legacy table (historical rows only)")]))
    return svg(W, H, "".join(parts), "ERD")


def trd():
    W, H = 2100, 1650
    parts = [DEFS]
    by_name = {t["table"]: t for t in INTRO["tables"]}
    tables = INTRO["tables"]  # 41 in introspection order
    # map snake to original display (e.g. account -> Account)
    def disp(n):
        return n.replace("_", " ")
    # grid 7 cols
    CW, CH = 280, 200
    for i, t in enumerate(tables):
        col = i % 7; row = i // 7
        x = 20 + col * 295; y = 20 + row * 225
        # header
        parts.append(rect(x, y, CW, 32, fill="#E8E8E8", stroke="#000000", sw=1))
        parts.append(text(x+CW/2, y+21, disp(t["table"]), 13, bold=True))
        parts.append(rect(x, y+32, CW, 168, fill="#FFFFFF", stroke="#000000", sw=1))
        pks = {c["name"] for c in t["constraints"] if c["type"] == "p" for c in [c]}  # unused, recompute below
        pkset = set()
        for c in t["constraints"]:
            if c["type"] == "p":
                pkset.update(c["columns"])
        fks = {c for f in INTRO["foreign_keys"] if f["source"] == t["table"] for c in f["columns"]}
        for j, colobj in enumerate(t["columns"][:6]):
            cy = y + 55 + j * 22
            nm = colobj["name"]
            ispk = nm in pkset; isfk = nm in fks
            tags = ("[PK, FK]" if ispk and isfk else ("[PK]" if ispk else ("[FK]" if isfk else "")))
            typ = {"integer": "int", "bigint": "bigint", "smallint": "smallint", "character varying": f"varchar({colobj['max_length'] or '?'})",
                   "text": "text", "boolean": "boolean", "timestamp with time zone": "timestamptz", "jsonb": "jsonb",
                   "numeric": f"numeric({colobj['numeric_precision'] or ''},{colobj['numeric_scale'] or ''})", "date": "date", "ARRAY": "text[]"}.get(colobj["type"], colobj["type"])
            parts.append(text(x+8, cy, nm, 9, anchor="start", bold=ispk))
            if tags:
                parts.append(text(x+CW-110, cy, tags, 7, anchor="start"))
            parts.append(text(x+CW-6, cy, typ, 7, anchor="end"))
        if len(t["columns"]) > 6:
            parts.append(text(x+CW/2, y+190, f"+{len(t['columns'])-6} more columns", 9, italic=True))
        # crow's foot stubs: one/many ticks on right edge per FK (simplified: ticks only)
        fklist = [f for f in INTRO["foreign_keys"] if f["source"] == t["table"]]
        for k, fk in enumerate(fklist[:4]):
            ly = y + 60 + k * 30
            parts.append(f'<path d="M{x+CW},{ly} h28" stroke="#000" stroke-width="1.2"/>')
            parts.append(f'<path d="M{x+CW+28},{ly} v-6 m0,12 l-8,-6 l8,-6" stroke="#000" stroke-width="1.2" fill="none"/>')
    # legend
    lx = W/2 - 500
    parts.append(rect(lx, H-110, 1000, 90, fill="#FFFFFF", stroke="#000000"))
    parts.append(text(lx+150, H-60, "name = primary key", 12, anchor="start"))
    parts.append(text(lx+320, H-60, "[FK] = foreign key", 12, anchor="start"))
    parts.append(text(lx+520, H-60, "—| = one", 12, anchor="start"))
    parts.append(text(lx+620, H-60, "—< = many", 12, anchor="start"))
    parts.append(text(lx+720, H-60, "41 tables · 293 columns · 59 FKs · 19 migrations", 11))
    return svg(W, H, "".join(parts), "TRD")


def main():
    # Roadmap: copy original verbatim (historical, unchanged)
    shutil.copy(ORIG / "ProposalDocument_ver1.1_image2.png", OUT / "fig-proposal-1-roadmap.png")
    svg_roadmap = OUT / "fig-proposal-1-roadmap.svg"
    from PIL import Image
    im = Image.open(OUT / "fig-proposal-1-roadmap.png")
    svg_roadmap.write_text(svg(f'<image href="data:,d" width="{im.width}" height="{im.height}"/><text x="10" y="{im.height+20}" font-size="12">Roadmap original kept verbatim (historical).</text>', im.width, im.height+30, "Roadmap"), encoding="utf-8")
    write_fig("fig-proposal-2-system-context", context())
    write_fig("fig-proposal-3-logical", logical())
    write_fig("fig-proposal-4-pipeline", pipeline())
    write_fig("fig-architecture-1-usecase", usecase())
    write_fig("fig-architecture-3-container", container())
    write_fig("fig-architecture-4-component", component())
    write_fig("fig-architecture-5-module", module())
    write_fig("fig-architecture-6-allocation", allocation())
    write_fig("fig-architecture-7-erd", erd())
    write_fig("fig-architecture-8-trd", trd())
    print("original-style done", len(list(OUT.glob('*.svg'))), "SVGs")


if __name__ == "__main__":
    main()

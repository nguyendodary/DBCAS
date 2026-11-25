# -*- coding: utf-8 -*-
"""Build the measured DBCAS ver1.4 figures from repository facts.

    python scripts/build_figures.py            # all figures
    python scripts/build_figures.py --only context,logical

Outputs SVG to docs/submission/final/assets/figures/ and a manifest with the
source-of-truth note for every figure.  scripts/rasterize_figures.mjs turns the
SVG into 300 dpi PNG; no figure is hand-drawn or copied from an older document.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import OrderedDict
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quality_svg import (  # noqa: E402
    AMBER, AMBER_FILL, BLUE, BORDER, FONT, GREEN, GREY, GREY_BORDER, LIGHT,
    MID, MUTED, NAVY, TEXT, WHITE, SVG, card_label, crow, wrap,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "submission" / "final" / "assets" / "figures"
INTRO = ROOT / "docs" / "diagrams" / "schema-028" / "schema-introspection.json"
DATA = json.loads(INTRO.read_text(encoding="utf-8"))
TABLES = {t["table"]: t for t in DATA["tables"]}
FKS = DATA["foreign_keys"]
MANIFEST: list[dict] = []

DOMAINS = OrderedDict([
    ("Identity and access", [
        "account", "account_identity", "account_role", "account_role_audit",
        "refresh_session", "oauth_handoff", "login_throttle",
        "password_reset_token", "password_reset_audit", "user_profile",
        "role", "system_setting"]),
    ("Curriculum and concepts", [
        "course_learning_outcome", "concept", "concept_dependency",
        "concept_competency", "clo_concept", "course_document",
        "document_chunk", "document_clo"]),
    ("Question bank and generation", [
        "question", "question_concept", "question_clo", "question_translation",
        "question_evidence", "mcq_option", "rubric", "sql_test_dataset",
        "question_candidate", "question_rubric_profile",
        "question_rubric_criterion"]),
    ("Assessment and attempts", [
        "assessment", "assessment_blueprint", "assessment_concept",
        "assessment_question", "assessment_session", "attempt",
        "session_question_plan", "session_start_request", "selection_log",
        "adaptive_event", "tab_leave_interval", "attempt_rubric_criterion"]),
    ("Grading, results and competency", [
        "evaluation_record", "grading_job", "grade_review", "grade_edit_audit",
        "result_release_event", "session_final_result",
        "session_result_version", "session_result_version_score",
        "session_result_criterion_score", "session_result_analysis",
        "session_result_publication", "competency_gap"]),
    ("Review workflow", [
        "review_request", "question_report", "review_deviation",
        "review_deviation_confirmation"]),
    ("AI audit and retention", [
        "ai_stage_run", "ai_stage_validation", "ai_stage_attempt",
        "ai_prompt_record", "ai_prompt_content", "prompt_access_audit",
        "retention_purge_audit", "llm_cache"]),
])
LEGACY = {"assessment", "assessment_concept", "assessment_question",
          "assessment_blueprint"}


def fk_target(fk):
    return fk.get("destination") or fk.get("references_table") or fk.get("target")


def register(name, title, source, *, width=None, height=None):
    MANIFEST.append({"file": f"{name}.svg", "title": title, "source": source,
                     "width": width, "height": height})


def save(svg, name, title, source):
    path = svg.save(OUT / f"{name}.svg")
    register(name, title, source, width=svg.width, height=svg.height)
    print(f"built {path.name} {svg.width}x{svg.height}")
    return path


# --------------------------------------------------------------------------
# 1. System context (shared: Proposal Figure 2, Architecture Figure 1)
# --------------------------------------------------------------------------
def system_context():
    s = SVG(1800, 1220, "DBCAS system context",
            "Two human actors, the system and the three external services it depends on")
    # actors
    s.actor(150, 300, "Learner")
    s.actor(1650, 300, "Administrator")
    # system
    s.rect(620, 250, 560, 300, fill=BLUE, stroke=NAVY, sw=3, rx=18)
    s.text(900, 350, "DBCAS", 60, WHITE, anchor="middle", bold=True)
    s.text(900, 402, "FastAPI /api/v1 + React SPA", 30, WHITE, anchor="middle")
    s.text(900, 446, "PostgreSQL 17 application database", 27, LIGHT, anchor="middle")
    s.text(900, 492, "106 paths · 118 operations", 26, LIGHT, anchor="middle")
    # external systems
    ext = [
        (120, 860, 460, "LLM provider", "OpenAI-compatible chat completions",
         "essay rubric · question generation"),
        (670, 860, 460, "OAuth providers", "Google and GitHub",
         "authorisation-code sign-in"),
        (1220, 860, 460, "SMTP service", "Mailpit locally",
         "password-reset mail"),
    ]
    for x, y, w, title, sub, sub2 in ext:
        s.rect(x, y, w, 170, fill=GREY, stroke=GREY_BORDER, sw=3, rx=14)
        s.text(x + w / 2, y + 60, title, 34, NAVY, anchor="middle", bold=True)
        s.text(x + w / 2, y + 102, sub, 25, MUTED, anchor="middle")
        s.text(x + w / 2, y + 138, sub2, 23, MUTED, anchor="middle")
    # flows
    s.path("M255 360 C330 360 360 390 600 400", color=NAVY, sw=3, marker="arrow")
    s.path("M600 460 C380 470 340 500 255 500", color=NAVY, sw=3, marker="arrow")
    s.text(430, 335, "practice, answers, results", 26, NAVY, anchor="middle")
    s.text(430, 535, "profile, guidance", 26, NAVY, anchor="middle")
    s.path("M1545 360 C1470 360 1440 390 1200 400", color=NAVY, sw=3, marker="arrow")
    s.path("M1200 460 C1420 470 1460 500 1545 500", color=NAVY, sw=3, marker="arrow")
    s.text(1370, 335, "curriculum, bank, review", 26, NAVY, anchor="middle")
    s.text(1370, 535, "queue, audit, settings", 26, NAVY, anchor="middle")
    # system to externals
    s.path("M720 550 L720 700 L350 700 L350 850", color=NAVY, sw=3, marker="arrow")
    s.text(380, 725, "HTTPS · structured JSON", 25, NAVY)
    s.path("M1080 550 L1080 700 L900 700 L900 850", color=NAVY, sw=3, marker="arrow")
    s.text(940, 725, "OAuth 302 / callback", 25, NAVY)
    s.path("M1000 550 L1000 760 L1380 760 L1380 850", color=NAVY, sw=3, marker="arrow")
    s.text(1180, 740, "SMTP 1025", 25, NAVY)
    # legend
    s.rect(120, 1090, 1560, 86, fill=LIGHT, stroke=GREY_BORDER, sw=2, rx=10)
    s.text(150, 1132, "Solid arrow: request or response path. Every element is named in the repository; the SMTP and OAuth paths are configuration-driven and disabled only when their keys are absent.", 24, MUTED)
    s.text(150, 1164, "Source: docker-compose.local.yml, backend/app/routers/*, backend/app/services/{oauth,mail}.py, docs/openapi.json", 22, MUTED)
    return save(s, "system-context", "System context",
                "docker-compose.local.yml; backend/app/routers/*; services/oauth.py; services/mail.py; docs/openapi.json")


# --------------------------------------------------------------------------
# 2. Logical architecture (shared: Proposal Figure 3, Architecture Figure 2,
#    Technical Report Figure 1)
# --------------------------------------------------------------------------
def logical_architecture():
    s = SVG(1800, 1280, "DBCAS logical architecture",
            "Four tiers, one deployable API and an ephemeral execution tier")
    tiers = [
        (150, 230, "Presentation tier", "React 19 · Vite · Tailwind CSS 4",
         ["Learner portal: practice setup, exam, profile, guidance",
          "Administrator portal: curriculum, bank, review queue, system"]),
        (150, 510, "Application tier", "FastAPI on Python 3.13 · /api/v1",
         ["7 registered routers · 72 service modules · 13 repository classes",
          "118 operations · in-process worker with database job leases"]),
        (150, 820, "Data tier", "PostgreSQL 17",
         ["67 tables · 561 columns · 122 foreign keys · 159 indexes",
          "28 forward migrations · no external queue or cache"]),
        (150, 1060, "Execution tier", "Ephemeral PostgreSQL container",
         ["Created per SQL run · no network · 256 MB · 1 CPU · 45 s",
          "read-only root · non-root user · 3 000 ms timeout · 1 000 rows"]),
    ]
    for y, h, title, sub, lines in tiers:
        s.rect(80, y, 1240, h, fill="#F7FAFD", stroke=GREY_BORDER, sw=2,
               rx=18, dash="10 8")
        s.text(110, y + 42, title, 34, NAVY, bold=True)
        s.text(110, y + 82, sub, 27, MUTED, bold=True)
        s.text(110, y + 124, lines[0], 25, TEXT)
        s.text(110, y + 158, lines[1], 25, TEXT)
    # external column
    s.rect(1400, 300, 340, 190, fill=GREY, stroke=GREY_BORDER, sw=2, rx=14)
    s.text(1570, 350, "LLM provider", 30, NAVY, anchor="middle", bold=True)
    s.text(1570, 390, "OpenAI-compatible", 24, MUTED, anchor="middle")
    s.text(1570, 424, "essay + generation", 24, MUTED, anchor="middle")
    s.text(1570, 458, "external · no weights", 22, MUTED, anchor="middle")
    s.rect(1400, 560, 340, 160, fill=GREY, stroke=GREY_BORDER, sw=2, rx=14)
    s.text(1570, 610, "SMTP", 30, NAVY, anchor="middle", bold=True)
    s.text(1570, 650, "Mailpit locally", 24, MUTED, anchor="middle")
    s.text(1570, 684, "password reset", 24, MUTED, anchor="middle")
    s.rect(1400, 800, 340, 190, fill=GREY, stroke=GREY_BORDER, sw=2, rx=14)
    s.text(1570, 850, "OAuth", 30, NAVY, anchor="middle", bold=True)
    s.text(1570, 890, "Google · GitHub", 24, MUTED, anchor="middle")
    s.text(1570, 924, "authorisation code", 24, MUTED, anchor="middle")
    s.text(1570, 958, "external identity", 22, MUTED, anchor="middle")
    # vertical flows
    s.line(700, 460, 700, 505, color=NAVY, sw=4, marker="arrow")
    s.text(730, 492, "HTTPS / JSON", 25, NAVY)
    s.line(700, 740, 700, 815, color=NAVY, sw=4, marker="arrow")
    s.text(730, 792, "SQLAlchemy · psycopg", 25, NAVY)
    s.line(700, 1050, 700, 1055, color=NAVY, sw=4)
    s.line(380, 820, 380, 1055, color=AMBER, sw=3, dash="9 7", marker="arrow")
    s.text(405, 950, "Docker API", 25, AMBER)
    s.text(405, 985, "create / exec / rm", 23, AMBER)
    # app to externals
    s.path("M1320 620 L1390 620", color=NAVY, sw=3, marker="arrow")
    s.text(1328, 604, "HTTPS", 22, NAVY)
    s.path("M1320 680 L1390 680", color=NAVY, sw=3, marker="arrow")
    s.text(1328, 664, "SMTP", 22, NAVY)
    s.path("M1320 900 L1390 900", color=NAVY, sw=3, marker="arrow")
    s.text(1322, 884, "OAuth", 22, NAVY)
    # rules
    s.text(90, 1260, "The browser never reaches PostgreSQL. The API is the only client of the data tier and of the ephemeral execution container.", 24, MUTED)
    return save(s, "logical-architecture", "Logical architecture",
                "backend/app/main.py; backend/Dockerfile; docker-compose.local.yml; docs/openapi.json")


# --------------------------------------------------------------------------
# 3. Module view (Architecture Figure 3)
# --------------------------------------------------------------------------
def module_view():
    s = SVG(3000, 1720, "DBCAS module view",
            "Seven registered routers, seven service domains, one repository module and the data tier")
    routers = [
        ("auth", "8 paths", 60, 520), ("oauth", "4 paths", 640, 520),
        ("admin", "58 paths", 1220, 520), ("assessments", "2 paths", 1800, 300),
        ("concepts", "1 path", 2140, 300), ("sessions", "23 paths", 2480, 520),
        ("practice", "7 paths", 2100, 700),
    ]
    s.text(60, 170, "HTTP routers · backend/app/routers", 36, NAVY, bold=True)
    for name, count, x, w in routers:
        y = 210 if name in ("assessments", "concepts") else 210
        h = 150
        s.rect(x, y, w, h, fill=BLUE, stroke=NAVY, sw=3, rx=14)
        s.text(x + w / 2, y + 66, f"{name}.py", 34, WHITE, anchor="middle", bold=True)
        s.text(x + w / 2, y + 110, count, 28, LIGHT, anchor="middle")
    # service domains
    svc = [
        ("Identity and access", ["auth_service", "oauth", "login_throttle",
                                 "refresh_tokens", "password_reset"], 60, 560),
        ("Curriculum", ["curriculum_service", "concept_graph_service",
                        "clo_tagging", "document_service"], 760, 560),
        ("Bank and generation", ["question_service", "question_validator",
                                 "governed_generation", "practice_generation"], 1460, 560),
        ("Practice and assessment", ["practice_service", "adaptive_engine",
                                     "assessment_lifecycle", "fixed_paper"], 2160, 560),
        ("Grading and review", ["grading_service", "evaluation_service",
                                "essay_grading", "review_flow", "review_regrade"], 60, 1060),
        ("Competency and analytics", ["competency_service", "cumulative_competency",
                                      "guidance_service", "analytics_service"], 1460, 1060),
        ("Operations", ["system_settings", "readiness_service", "mail"], 2460, 480),
    ]
    s.text(60, 470, "Service layer · 72 top-level modules grouped by use case", 36, NAVY, bold=True)
    for title, modules, x, w in svc:
        y = 520 if title in ("Identity and access", "Curriculum", "Bank and generation",
                             "Practice and assessment") else 1000
        h = 310 if title != "Operations" else 210
        s.rect(x, y, w, h, fill=LIGHT, stroke=BORDER, sw=2, rx=14)
        s.text(x + 24, y + 44, title, 30, NAVY, bold=True)
        for i, module in enumerate(modules):
            s.text(x + 24, y + 88 + i * 38, module, 26, TEXT)
    # repositories and db
    s.rect(60, 1410, 900, 220, fill=MID, stroke=BORDER, sw=3, rx=14)
    s.text(90, 1462, "Persistence layer", 32, NAVY, bold=True)
    s.text(90, 1504, "13 repository classes in backend/app/repositories.py", 26, TEXT)
    s.text(90, 1544, "queries, locks, leases, pagination; no HTTP errors", 24, MUTED)
    s.rect(1170, 1410, 700, 220, fill=BLUE, stroke=NAVY, sw=3, rx=14)
    s.text(1520, 1470, "PostgreSQL 17", 38, WHITE, anchor="middle", bold=True)
    s.text(1520, 1520, "67 tables · 561 columns", 28, LIGHT, anchor="middle")
    s.text(1520, 1560, "122 FKs · 159 indexes", 28, LIGHT, anchor="middle")
    s.rect(2050, 1410, 890, 220, fill=GREY, stroke=GREY_BORDER, sw=2, rx=14)
    s.text(2080, 1462, "Side systems", 32, NAVY, bold=True)
    s.text(2080, 1504, "LLM provider · SMTP · OAuth", 26, TEXT)
    s.text(2080, 1544, "ephemeral SQL sandbox · in-process worker", 24, MUTED)
    # arrows
    s.line(350, 360, 350, 510, color=NAVY, sw=3, marker="arrow")
    s.line(1560, 360, 1560, 510, color=NAVY, sw=3, marker="arrow")
    s.line(2620, 360, 2620, 510, color=NAVY, sw=3, marker="arrow")
    s.line(500, 830, 500, 995, color=NAVY, sw=3, marker="arrow")
    s.line(1900, 830, 1900, 995, color=NAVY, sw=3, marker="arrow")
    s.line(510, 1380, 510, 1405, color=NAVY, sw=3, marker="arrow")
    s.line(960, 1520, 1165, 1520, color=NAVY, sw=3, marker="arrow")
    s.text(980, 1500, "SQLAlchemy", 24, NAVY)
    s.line(1875, 1520, 2045, 1520, color=NAVY, sw=3, marker="arrow")
    s.text(1885, 1500, "HTTPS / SMTP", 24, NAVY)
    s.rect(60, 1640, 2880, 56, fill=WHITE, stroke=WHITE, sw=0)
    s.text(60, 1675, "Measured at 66045b7: 7 registered routers (8 .py files), 72 top-level service modules, 13 repository classes, 106 paths / 118 operations.", 24, MUTED)
    return save(s, "module-view", "Module view",
                "backend/app/routers/*; backend/app/services/*; backend/app/repositories.py; docs/openapi.json")


# --------------------------------------------------------------------------
# 4. Deployment view (Architecture Figure 5)
# --------------------------------------------------------------------------
def deployment_view():
    s = SVG(3000, 1720, "DBCAS deployment view",
            "Default local Compose profile, the QA-only provider and the per-execution sandbox")
    # browser
    s.rect(60, 220, 520, 200, fill=GREY, stroke=GREY_BORDER, sw=2, rx=14)
    s.text(320, 286, "User's browser", 34, NAVY, anchor="middle", bold=True)
    s.text(320, 330, "Chrome, Edge, Firefox, Safari", 24, MUTED, anchor="middle")
    s.text(320, 366, "React 19 SPA", 24, MUTED, anchor="middle")
    # host boundary
    s.rect(60, 500, 2880, 1080, fill="#F7FAFD", stroke=MUTED, sw=3, rx=20, dash="12 9")
    s.text(90, 550, "Docker-capable host · Compose project dbcas-local", 32, NAVY, bold=True)
    # services
    services = [
        (100, 620, 500, 220, "frontend", "Nginx + built SPA", ["18080 → 8080", "proxies /api/v1"]),
        (680, 620, 620, 220, "app", "FastAPI + in-process worker", ["18000 → 8000", "2 uvicorn workers"]),
        (1380, 620, 440, 220, "db", "PostgreSQL 17", ["internal database network", "volume local-data"]),
        (1900, 620, 420, 220, "init", "one-shot migrate + seed", ["schema.sql + 28 migrations", "exits after seed"]),
        (2400, 620, 500, 220, "mailpit", "SMTP capture + mailbox UI", ["11025 → 1025 SMTP", "18025 → 8025 UI"]),
        (100, 980, 500, 220, "executor-image", "dbcas-sql-ephemeral:local", ["build only", "no long-running process"]),
        (680, 980, 620, 220, "SQL sandbox", "ephemeral PostgreSQL 17", ["docker create/exec/rm", "network none · 256 MB"]),
        (1380, 980, 440, 220, "qa-ai (QA only)", "deterministic fake provider", ["docker-compose.qa.yml", "never calls a real model"]),
        (1900, 980, 420, 220, "real-QA meter", "opt-in outbound counter", ["docker-compose.real-qa.yml", "counts LLM requests"]),
    ]
    for x, y, w, h, title, sub, lines in services:
        fill = BLUE if title in ("frontend", "app", "db") else GREY
        color = WHITE if fill == BLUE else NAVY
        subcolor = LIGHT if fill == BLUE else MUTED
        s.rect(x, y, w, h, fill=fill, stroke=NAVY if fill == BLUE else GREY_BORDER,
               sw=3 if fill == BLUE else 2, rx=14)
        s.text(x + w / 2, y + 62, title, 34, color, anchor="middle", bold=True)
        s.text(x + w / 2, y + 104, sub, 24, subcolor, anchor="middle")
        for i, line in enumerate(lines):
            s.text(x + w / 2, y + 148 + i * 30, line, 22, subcolor, anchor="middle")
    # external
    ext = [
        (2400, 980, 500, 220, "LLM provider", ["OpenAI-compatible HTTPS", "external · no weights"]),
        (2400, 1280, 500, 170, "OAuth providers", ["Google · GitHub", "authorisation code"]),
    ]
    for x, y, w, h, title, lines in ext:
        s.rect(x, y, w, h, fill=GREY, stroke=GREY_BORDER, sw=2, rx=14)
        s.text(x + w / 2, y + 54, title, 30, NAVY, anchor="middle", bold=True)
        for i, line in enumerate(lines):
            s.text(x + w / 2, y + 98 + i * 30, line, 22, MUTED, anchor="middle")
    # flows
    s.line(320, 420, 320, 610, color=NAVY, sw=3, marker="arrow")
    s.text(340, 525, "HTTPS :18080", 24, NAVY)
    s.line(600, 720, 675, 720, color=NAVY, sw=3, marker="arrow")
    s.text(610, 700, "proxy /api/v1", 22, NAVY)
    s.line(1300, 720, 1375, 720, color=NAVY, sw=3, marker="arrow")
    s.text(1310, 700, "SQLAlchemy", 22, NAVY)
    s.path("M1000 840 L1000 900 L950 900 L950 975", color=AMBER, sw=3, dash="8 6", marker="arrow")
    s.text(960, 890, "docker.sock", 22, AMBER)
    s.path("M2400 720 L2350 720 L2350 690 L2200 690", color=NAVY, sw=2, dash="8 6")
    s.line(2540, 960, 2540, 970, color=NAVY, sw=2, dash="8 6")
    s.line(2400, 1090, 2340, 1090, color=NAVY, sw=2, dash="8 6")
    s.text(900, 1320, "Network boundaries: web (frontend, app, mailpit) and database (internal, app and db only). The sandbox is not a Compose service.", 24, MUTED)
    s.text(900, 1360, "Sources: docker-compose.local.yml, docker-compose.qa.yml, docker-compose.real-qa.yml, backend/app/services/ephemeral_sandbox.py", 22, MUTED)
    s.text(900, 1400, "QA-only services are never started by the default profile; they exist so browser tests never call a real model.", 22, MUTED)
    return save(s, "deployment-view", "Deployment view",
                "docker-compose.local.yml; docker-compose.qa.yml; docker-compose.real-qa.yml; services/ephemeral_sandbox.py")


# --------------------------------------------------------------------------
# 5. AI pipeline (Architecture Figure 4)
# --------------------------------------------------------------------------
def ai_pipeline():
    s = SVG(3000, 1560, "AI generation, evaluation and fallback",
            "Two AI roles, one validation gate and a deterministic fallback")
    # lane titles
    s.text(60, 180, "A. Question generation (administrator path)", 38, NAVY, bold=True)
    s.text(60, 760, "B. Essay evaluation (learner path)", 38, NAVY, bold=True)
    # generation boxes
    gen = [
        ("Administrator request", "concept · band · type\nrequest id", 60),
        ("Governed generation", "governed_generation.py\nsource ids · prompt digest", 560),
        ("LLM provider", "structured JSON\nOpenAI-compatible", 1060),
        ("Schema gate", "required fields\ntypes · score caps", 1560),
        ("Domain gate", "concept tags · options\nanswer key · docs", 2060),
        ("Execution + duplicate", "SQL fixtures · fingerprint\ncandidate draft", 2560),
    ]
    for title, sub, x in gen:
        s.rect(x, 240, 440, 260, fill=LIGHT, stroke=BORDER, sw=3, rx=14)
        s.text(x + 220, 300, title, 30, NAVY, anchor="middle", bold=True)
        for i, line in enumerate(sub.split("\n")):
            s.text(x + 220, 348 + i * 30, line, 23, MUTED, anchor="middle")
    for i in range(len(gen) - 1):
        x = gen[i][2] + 440
        s.line(x + 6, 370, gen[i + 1][2] - 8, 370, color=NAVY, sw=3, marker="arrow")
    # review row
    s.rect(2560, 560, 440, 160, fill=AMBER_FILL, stroke=AMBER, sw=3, rx=14)
    s.text(2780, 612, "Administrator review", 28, AMBER, anchor="middle", bold=True)
    s.text(2780, 652, "approve / reject candidate", 23, AMBER, anchor="middle")
    s.text(2780, 688, "no auto-publication", 23, AMBER, anchor="middle")
    s.line(2780, 500, 2780, 552, color=AMBER, sw=3, marker="arrow")
    # bank + rejection
    s.rect(2060, 560, 440, 160, fill=GREEN, stroke=GREEN, sw=3, rx=14)
    s.text(2280, 612, "Validated question bank", 28, WHITE, anchor="middle", bold=True)
    s.text(2280, 652, "only approved items served", 23, WHITE, anchor="middle")
    s.line(2560, 640, 2508, 640, color=GREEN, sw=3, marker="arrow")
    s.line(2780, 720, 2780, 790, color=AMBER, sw=2, dash="8 6")
    s.text(2800, 760, "reject", 22, AMBER)
    # essay lane
    essay = [
        ("Attempt + rubric", "question version\nrubric profile", 60),
        ("Prompt builder", "prompt_builder.py\ndeterministic template\nno model call", 560),
        ("LLM evaluation", "llm/service.py\nstructured JSON", 1060),
        ("Validation", "schema + rubric\ncriterion maxima", 1560),
        ("Rubric score", "criterion scores\nfeedback · flags", 2060),
    ]
    for title, sub, x in essay:
        s.rect(x, 840, 440, 260, fill=LIGHT, stroke=BORDER, sw=3, rx=14)
        s.text(x + 220, 900, title, 30, NAVY, anchor="middle", bold=True)
        for i, line in enumerate(sub.split("\n")):
            s.text(x + 220, 948 + i * 30, line, 23, MUTED, anchor="middle")
    for i in range(len(essay) - 1):
        x = essay[i][2] + 440
        s.line(x + 6, 970, essay[i + 1][2] - 8, 970, color=NAVY, sw=3, marker="arrow")
    # fallback
    s.rect(560, 1180, 440, 170, fill=AMBER_FILL, stroke=AMBER, sw=3, rx=14)
    s.text(780, 1234, "Deterministic fallback", 28, AMBER, anchor="middle", bold=True)
    s.text(780, 1276, "template rubric · evaluator_fallback", 23, AMBER, anchor="middle")
    s.text(780, 1312, "same score contract", 23, AMBER, anchor="middle")
    s.path("M1280 1100 L1280 1265 L1008 1265", color=AMBER, sw=3, dash="9 7", marker="arrow")
    s.text(1020, 1248, "provider / schema failure", 22, AMBER)
    s.path("M1000 1265 L1000 1180", color=AMBER, sw=3, dash="9 7", marker="arrow")
    s.text(1020, 1130, "fallback grade", 22, AMBER)
    # audit strip
    s.rect(60, 1400, 2880, 120, fill=GREY, stroke=GREY_BORDER, sw=2, rx=12)
    s.text(90, 1442, "Audit and retention", 28, NAVY, bold=True)
    s.text(90, 1482, "ai_stage_run · ai_stage_attempt · ai_stage_validation · ai_prompt_record · llm_cache · prompt_access_audit · retention_purge_audit", 23, MUTED)
    return save(s, "ai-pipeline", "AI generation, evaluation and fallback",
                "services/governed_generation.py; services/prompt_builder.py; services/llm/*; services/question_validator.py; services/evaluation_pipeline.py")


# --------------------------------------------------------------------------
# 6. Assessment lifecycle (Architecture Figure 6, Technical Report Figure 2)
# --------------------------------------------------------------------------
def assessment_lifecycle():
    s = SVG(1800, 1300, "Assessment lifecycle",
            "The plan is frozen before question one; publication uses stored evidence only")
    steps = [
        ("Practice setup", "concepts · bands\ncount · source", 60, 230),
        ("Plan assembly and freeze", "exact count · quotas\nconcept spread", 500, 230),
        ("Serve planned item", "validated bank\nor approved AI item", 940, 230),
        ("Grade answer", "MCQ · SQL result or table state\nessay rubric", 1380, 230),
        ("Record evidence", "score · version\nconcept tags", 940, 560),
        ("Complete session", "all planned items\nor 30-minute expiry", 500, 560),
        ("Competency and gaps", "published evidence only\n70% target", 60, 560),
        ("Candidate preparation", "AI draft → validation\n→ administrator review", 60, 900),
        ("Validated bank", "approved items only\nSQL always bank", 500, 900),
    ]
    for title, sub, x, y in steps:
        fill = GREEN if title == "Validated bank" else LIGHT
        color = WHITE if fill == GREEN else NAVY
        subcolor = WHITE if fill == GREEN else MUTED
        s.rect(x, y, 380, 210, fill=fill, stroke=GREEN if fill == GREEN else BORDER,
               sw=3, rx=14)
        s.text(x + 190, y + 58, title, 29, color, anchor="middle", bold=True)
        for i, line in enumerate(sub.split("\n")):
            s.text(x + 190, y + 106 + i * 30, line, 23, subcolor, anchor="middle")
    arrows = [
        (440, 335, 495, 335, "arrow"), (880, 335, 935, 335, "arrow"),
        (1320, 335, 1375, 335, "arrow"), (1570, 440, 1570, 555, "arrow"),
        (1380, 665, 885, 665, "arrow"), (500, 665, 445, 665, "arrow"),
        (60, 665, 60, 665, None), (250, 665, 250, 895, "arrow"),
        (440, 1005, 495, 1005, "arrow"), (690, 900, 690, 770, "arrow"),
    ]
    for x1, y1, x2, y2, marker in arrows:
        if marker:
            s.line(x1, y1, x2, y2, color=NAVY, sw=3, marker="arrow")
    s.path("M250 770 L250 895", color=NAVY, sw=3, marker="arrow")
    s.text(270, 850, "next item", 22, NAVY)
    s.text(700, 850, "serve", 22, NAVY)
    s.text(1600, 520, "finalize", 22, NAVY)
    s.text(120, 1120, "Fixed-test finalize publishes official V1; practice and legacy sessions wait for administrator review.", 24, MUTED)
    s.text(120, 1160, "A bank shortage stops the start with insufficient_question_pool; a provider failure substitutes bank items with one notice.", 24, MUTED)
    s.text(120, 1220, "Source: services/practice_service.py (start), services/adaptive_engine.py (serve), services/assessment_lifecycle.py (submit/finalize), services/competency_service.py.", 21, MUTED)
    return save(s, "assessment-lifecycle", "Assessment lifecycle",
                "services/practice_service.py; services/adaptive_engine.py; services/assessment_lifecycle.py; services/competency_service.py")


# --------------------------------------------------------------------------
# 7. Practice-start sequence (Architecture Figure 7)
# --------------------------------------------------------------------------
def practice_sequence():
    s = SVG(3000, 1560, "Practice session start",
            "POST /api/v1/practice/start — verified call order at 66045b7")
    xs = [260, 760, 1260, 1760, 2260, 2760]
    names = ["Learner", "React SPA", "FastAPI router", "practice_service", "PostgreSQL", "Bank / LLM"]
    for x, name in zip(xs, names):
        s.rect(x - 190, 180, 380, 110, fill=BLUE, stroke=NAVY, sw=3, rx=12)
        s.text(x, 232, name, 29, WHITE, anchor="middle", bold=True)
        s.text(x, 266, "object" if name not in ("Learner", "PostgreSQL", "Bank / LLM") else "actor / store", 20, LIGHT, anchor="middle")
        s.line(x, 290, x, 1340, color=GREY_BORDER, sw=2, dash="7 8")
    msgs = [
        (0, 1, "select concepts, bands, count, source"),
        (1, 2, "POST /api/v1/practice/start"),
        (2, 3, "practice_service.start(db, learner, payload)"),
        (3, 4, "advisory lock; live-session lookup"),
        (3, 5, "assemble plan: bank + validated AI"),
        (3, 4, "persist session + plan snapshot"),
        (2, 1, "201 SessionState (first question)"),
        (1, 0, "render question 1"),
    ]
    y = 370
    for i, (a, b, label) in enumerate(msgs, 1):
        x1, x2 = xs[a], xs[b]
        direction = 1 if x2 > x1 else -1
        s.line(x1 + direction * 8, y, x2 - direction * 8, y, color=NAVY, sw=3, marker="arrow")
        s.text((x1 + x2) / 2, y - 12, f"{i}. {label}", 24, NAVY, anchor="middle")
        y += 118
    s.rect(60, 1320, 2880, 84, fill=AMBER_FILL, stroke=AMBER, sw=2, rx=10)
    s.text(80, 1358, "Alternate: no eligible item → HTTP 422 insufficient_question_pool with shortage_by_type; no silent shortening.", 23, AMBER)
    s.text(80, 1388, "The plan is committed before the first question is returned. A repeated request id returns the existing live session or 409 start_request_conflict.", 22, AMBER)
    return save(s, "practice-start-sequence", "Practice session start sequence",
                "routers/practice.py:96; services/practice_service.py:287; services/practice_selection.py:212")


# --------------------------------------------------------------------------
# 8. Answer and review sequence (Architecture Figure 8)
# --------------------------------------------------------------------------
def grading_sequence():
    s = SVG(3000, 1620, "Answer submission, grading and review",
            "POST /api/v1/sessions/{id}/submit and the administrator review queue")
    xs = [240, 700, 1160, 1620, 2080, 2540, 2900]
    names = ["Learner", "React SPA", "sessions router", "assessment_lifecycle",
             "Grader / sandbox", "PostgreSQL", "Admin"]
    for x, name in zip(xs, names):
        s.rect(x - 170, 180, 340, 106, fill=BLUE, stroke=NAVY, sw=3, rx=12)
        s.text(x, 228, name, 25, WHITE, anchor="middle", bold=True)
        s.text(x, 262, "actor" if name in ("Learner", "Admin") else "component / store", 19, LIGHT, anchor="middle")
        s.line(x, 286, x, 1430, color=GREY_BORDER, sw=2, dash="7 8")
    msgs = [
        (0, 1, "submit answer"),
        (1, 2, "POST /sessions/{id}/submit"),
        (2, 3, "assessment_lifecycle.submit()"),
        (3, 5, "lock attempt; check answer hash"),
        (3, 4, "MCQ key / SQL sandbox / essay rubric"),
        (4, 5, "score + grading_detail"),
        (3, 2, "commit answer + next state"),
        (2, 1, "SubmissionResult"),
        (1, 0, "next question or result"),
        (0, 6, "request review (≤ 7 days)"),
        (6, 5, "claim 30 min; reject or regrade"),
    ]
    y = 360
    for i, (a, b, label) in enumerate(msgs, 1):
        x1, x2 = xs[a], xs[b]
        direction = 1 if x2 > x1 else -1
        s.line(x1 + direction * 8, y, x2 - direction * 8, y, color=NAVY, sw=3, marker="arrow")
        s.text((x1 + x2) / 2, y - 10, f"{i}. {label}", 22, NAVY, anchor="middle")
        y += 96
    s.rect(60, 1410, 2880, 100, fill=LIGHT, stroke=BORDER, sw=2, rx=10)
    s.text(80, 1450, "Provider or sandbox failure: the attempt is stored and a durable grading_job is queued (pending → processing → completed/failed, three attempts); nothing is fabricated.", 22, NAVY)
    s.text(80, 1482, "A repeated submit with the same hash returns the stored result; a changed answer is 409 already_submitted. A review deviation above 30% needs a second administrator.", 22, NAVY)
    return save(s, "grading-review-sequence", "Answer submission, grading and review sequence",
                "routers/sessions.py:159,262; services/assessment_lifecycle.py:submit; services/grading_service.py; services/review_flow.py")


# --------------------------------------------------------------------------
# 9. Quality gates (Code Standards Figure 1)
# --------------------------------------------------------------------------
def quality_gates():
    s = SVG(1800, 1060, "CI quality gates",
            "Fourteen jobs in the Local quality gate workflow at commit d6df804")
    s.rect(60, 180, 320, 160, fill=BLUE, stroke=NAVY, sw=3, rx=14)
    s.text(220, 242, "changes", 32, WHITE, anchor="middle", bold=True)
    s.text(220, 282, "classifies docs-only", 22, LIGHT, anchor="middle")
    s.text(220, 312, "docs/qa forces full run", 22, LIGHT, anchor="middle")
    boxes = [
        ("secrets", ["secret-scan tests", "tree + history scan"], 460, 180),
        ("backend", ["ruff + compile", "OpenAPI + bank", "pytest + pip-audit", "image build"], 460, 420),
        ("frontend-static", ["ESLint + Prettier", "vitest + build", "audit + inventory", "docs:check"], 900, 420),
        ("frontend-shard", ["9 legs: e2e 1–3", "QA 1–3 · smoke 1–3"], 1340, 420),
        ("frontend-local", ["fan-in: all 9 shard", "reports must succeed"], 1340, 720),
    ]
    for title, lines, x, y in boxes:
        h = 120 + 30 * len(lines)
        s.rect(x, y, 380, h, fill=LIGHT, stroke=BORDER, sw=3, rx=14)
        s.text(x + 190, y + 48, title, 28, NAVY, anchor="middle", bold=True)
        for i, line in enumerate(lines):
            s.text(x + 190, y + 92 + i * 30, line, 22, MUTED, anchor="middle")
    s.line(380, 260, 450, 260, color=NAVY, sw=3, marker="arrow")
    s.line(840, 260, 900, 260, color=NAVY, sw=3, marker="arrow")
    s.line(840, 300, 840, 410, color=NAVY, sw=3, marker="arrow")
    s.line(1280, 480, 1330, 480, color=NAVY, sw=3, marker="arrow")
    s.line(1530, 620, 1530, 710, color=NAVY, sw=3, marker="arrow")
    s.rect(60, 900, 1680, 110, fill=GREY, stroke=GREY_BORDER, sw=2, rx=10)
    s.text(80, 940, "14 jobs: changes, secrets, backend, frontend-static, 9 frontend-shard legs, frontend-local fan-in. No coverage job, no type-check job.", 23, MUTED)
    s.text(80, 974, "Source: .github/workflows/dn-backend.yml; docs/agent/freeze-logs/final-ci-conclusion.log (run 45597486074, commit d6df804, 14/14 success).", 21, MUTED)
    return save(s, "quality-gates", "CI quality gates",
                ".github/workflows/dn-backend.yml; freeze-logs/final-ci-conclusion.log")


# --------------------------------------------------------------------------
# 10. Roadmap (Proposal Figure 1)
# --------------------------------------------------------------------------
def gantt():
    s = SVG(3000, 1560, "Agile delivery roadmap",
            "Five two-week sprints, four status reports and two faculty milestones (28/07/2026 – 26/12/2026)")
    start, end = date(2026, 7, 20), date(2026, 12, 31)
    left, right = 520, 2920
    span = (end - start).days
    def x_of(d):
        return left + (d - start).days / span * (right - left)
    rows = [
        ("Preparation", date(2026, 7, 28), date(2026, 8, 14), "team, repositories, research"),
        ("Advisor assignment", date(2026, 8, 10), date(2026, 8, 16), "mentor and scope"),
        ("Proposal drafting", date(2026, 8, 17), date(2026, 8, 23), "title, problem, SMART, diagrams"),
        ("Proposal submission", date(2026, 8, 24), date(2026, 9, 5), "v1.1 Word + PDF, review slides"),
        ("Sprint 1 · architecture and data", date(2026, 9, 14), date(2026, 9, 27), "schema, concept model"),
        ("Sprint 2 · identity and MCQ", date(2026, 9, 28), date(2026, 10, 11), "JWT, roles, MCQ, SQL editor"),
        ("Sprint 3 · sandbox and AI", date(2026, 10, 12), date(2026, 10, 25), "sandbox, rubric, bank"),
        ("Midterm buffer", date(2026, 10, 26), date(2026, 10, 31), "integration and rehearsal"),
        ("Midterm review", date(2026, 11, 1), date(2026, 11, 7), "end-to-end demo"),
        ("Sprint 4 · competency", date(2026, 11, 8), date(2026, 11, 22), "scoring, radar, gaps"),
        ("Sprint 5 · plan and analytics", date(2026, 11, 23), date(2026, 12, 6), "plan assembly, cohort API"),
        ("Final delivery", date(2026, 12, 10), date(2026, 12, 13), "freeze, documents, video"),
        ("Capstone defence", date(2026, 12, 17), date(2026, 12, 26), "rehearsal and committee"),
    ]
    top = 220
    row_h = 82
    # month grid
    month = date(2026, 8, 1)
    while month <= end:
        x = x_of(month)
        s.line(x, top - 24, x, top + row_h * len(rows) + 10, color="#E3E8EE", sw=2)
        s.text(x + 6, top - 36, month.strftime("%b"), 24, MUTED)
        month = date(month.year + (month.month == 12), 1 if month.month == 12 else month.month + 1, 1)
    for i, (label, a, b, note) in enumerate(rows):
        y = top + i * row_h
        fill = BLUE if label.startswith("Sprint") else (MID if "review" in label.lower() or "delivery" in label.lower() or "defence" in label.lower() else LIGHT)
        if i % 2 == 0:
            s.rect(40, y - 28, 2920, row_h - 8, fill="#FAFCFE", stroke=WHITE, sw=0, rx=0)
        s.text(60, y + 10, label, 24, NAVY, bold=True)
        s.text(60, y + 40, note, 19, MUTED)
        x1, x2 = x_of(a), x_of(b)
        s.rect(x1, y - 12, max(20, x2 - x1), 22, fill=fill, stroke=NAVY, sw=2, rx=8)
    # status reports
    for d, label in [(date(2026, 10, 3), "SR1"), (date(2026, 10, 17), "SR2"),
                     (date(2026, 11, 20), "SR3"), (date(2026, 12, 5), "SR4")]:
        x = x_of(d)
        s.add(f'<polygon points="{x},{top-40} {x+13},{top-22} {x},{top-4} {x-13},{top-22}" fill="{WHITE}" stroke="{AMBER}" stroke-width="2"/>')
        s.text(x, top - 48, label, 18, AMBER, anchor="middle", bold=True)
    # faculty milestones
    for d, label, y in [(date(2026, 11, 4), "MIDTERM REVIEW", 760), (date(2026, 12, 21), "FINAL DEFENCE", 1280)]:
        x = x_of(d)
        s.add(f'<polygon points="{x},{y-38} {x+38},{y} {x},{y+38} {x-38},{y}" fill="{AMBER_FILL}" stroke="{AMBER}" stroke-width="3"/>')
        s.text(x, y + 10, label, 21, AMBER, anchor="middle", bold=True)
    # legend
    s.rect(60, 1400, 2880, 110, fill=WHITE, stroke=GREY_BORDER, sw=2, rx=10)
    s.rect(90, 1434, 44, 24, fill=BLUE, stroke=NAVY, sw=2, rx=8)
    s.text(150, 1454, "Sprint", 24, TEXT)
    s.rect(300, 1434, 44, 24, fill=LIGHT, stroke=NAVY, sw=2, rx=8)
    s.text(360, 1454, "Preparation / delivery phase", 24, TEXT)
    s.add(f'<polygon points="720,1446 735,1434 750,1446 735,1458" fill="{WHITE}" stroke="{AMBER}" stroke-width="2"/>')
    s.text(765, 1454, "Status report (04/10, 18/10, 21/11, 06/12)", 24, TEXT)
    s.add(f'<polygon points="1350,1446 1370,1428 1390,1446 1370,1464" fill="{AMBER_FILL}" stroke="{AMBER}" stroke-width="2"/>')
    s.text(1405, 1454, "Faculty milestone", 24, TEXT)
    s.text(90, 1494, "Rows and dates are the table in Proposal §11.2. Status reports are team reports, not faculty gates; the two faculty milestones are the midterm review and the final defence.", 21, MUTED)
    return save(s, "gantt-roadmap", "Agile delivery roadmap",
                "submission_content/proposal.py §11.2; docs/academic proposal calendar")


# --------------------------------------------------------------------------
# 11. Schema overview + domain ERDs
# --------------------------------------------------------------------------
def schema_overview():
    s = SVG(1800, 1160, "Schema map",
            "67 tables in eight domains, 122 foreign keys and 28 forward migrations")
    counts = {name: len(names) for name, names in DOMAINS.items()}
    boxes = [
        ("Identity and access", counts["Identity and access"], "accounts, roles, sessions, tokens", 60, 190),
        ("Curriculum and concepts", counts["Curriculum and concepts"], "CLOs, concepts, prerequisites, documents", 620, 190),
        ("Question bank and generation", counts["Question bank and generation"], "questions, options, rubrics, candidates", 1180, 190),
        ("Assessment and attempts", counts["Assessment and attempts"], "blueprints, sessions, attempts, plans", 60, 470),
        ("Grading, results and competency", counts["Grading, results and competency"], "jobs, versions, scores, gaps", 620, 470),
        ("Review workflow", counts["Review workflow"], "requests, reports, deviations", 1180, 470),
        ("AI audit and retention", counts["AI audit and retention"], "stage runs, prompts, caches, purges", 620, 750),
    ]
    for title, count, sub, x, y in boxes:
        s.rect(x, y, 540, 200, fill=LIGHT, stroke=BORDER, sw=3, rx=14)
        s.text(x + 24, y + 48, title, 28, NAVY, bold=True)
        s.text(x + 24, y + 84, sub, 21, MUTED)
        s.text(x + 24, y + 146, f"{count} tables", 32, BLUE, bold=True)
    # totals panel
    s.rect(620, 990, 1100, 120, fill=BLUE, stroke=NAVY, sw=3, rx=14)
    s.text(1170, 1038, "67 tables · 561 columns · 122 foreign keys · 159 indexes · 28 migrations", 27, WHITE, anchor="middle", bold=True)
    s.text(1170, 1078, "PostgreSQL 17.12 introspection; no native enums and no views", 22, LIGHT, anchor="middle")
    s.text(60, 990, "Each domain is expanded in Figures 2–8. The column dictionary in Section 5 lists every column and every FK target.", 21, MUTED)
    return save(s, "schema-overview", "Schema map",
                "docs/diagrams/schema-028/schema-introspection.json; db/schema.sql; db/migrations/*")


def entity_rows(table, limit=6):
    """PK, FK and the first fill columns, never more than `limit` rows."""
    t = TABLES[table]
    cols = [c["name"] for c in t["columns"]]
    pk = set()
    for con in t.get("constraints", []):
        if con.get("type") == "p":
            body = con.get("definition", "")
            inner = body[body.find("(") + 1:body.rfind(")")]
            pk |= {x.strip() for x in inner.split(",") if x.strip()}
    fk_cols = OrderedDict()
    for fk in FKS:
        if fk["source"] == table:
            target = fk_target(fk)
            for col in fk.get("columns", []):
                fk_cols[col] = target
    ordered = []
    for col in cols:
        if col in pk:
            ordered.append((col, "PK", ""))
    for col in cols:
        if col in fk_cols and col not in pk:
            ordered.append((col, "FK", fk_cols[col]))
    for col in cols:
        if col not in pk and col not in fk_cols:
            ordered.append((col, "", ""))
    return ordered[:limit], max(0, len(ordered) - limit)


def erd_domain(name, index):
    tables = DOMAINS[name]
    n = len(tables)
    cols = 4 if n > 6 else 2
    rows = math.ceil(n / cols)
    W, H = 3000, 1800
    s = SVG(W, H, f"ERD {index}: {name}",
            f"{n} tables · {sum(1 for f in FKS if f['source'] in tables and fk_target(f) in tables)} in-domain foreign keys")
    left, top = 60, 160
    cell_w = (W - 2 * left) / cols
    cell_h = (H - top - 110) / rows
    node_w = min(660, cell_w - 70)
    row_limit = 5 if rows >= 3 else 6
    nodes = {}
    for i, table in enumerate(tables):
        c, r = i % cols, i // cols
        cx = left + c * cell_w + cell_w / 2
        cy = top + r * cell_h + cell_h / 2
        rows_data, more = entity_rows(table, row_limit)
        h = 56 + (len(rows_data) + (1 if more else 0)) * 38 + 20
        x, y = cx - node_w / 2, cy - h / 2
        nodes[table] = (x, y, node_w, h)
        legacy = table in LEGACY
        header = AMBER if legacy else MID
        border = AMBER if legacy else BORDER
        s.rect(x, y, node_w, h, fill=WHITE, stroke=border, sw=2, rx=8)
        s.add(f'<path d="M{x} {y+8} Q{x} {y} {x+8} {y} L{x+node_w-8} {y} Q{x+node_w} {y} {x+node_w} {y+8} L{x+node_w} {y+56} L{x} {y+56} Z" fill="{header}" stroke="{border}" stroke-width="2"/>')
        s.text(x + 14, y + 38, table, 30, NAVY, bold=True)
        yy = y + 90
        for col, kind, target in rows_data:
            label = f"{col}"
            if kind == "PK":
                s.text(x + 14, yy, "PK", 21, BLUE, bold=True)
                s.text(x + 54, yy, label, 25, TEXT, bold=True)
            elif kind == "FK":
                s.text(x + 14, yy, "FK", 21, AMBER, bold=True)
                s.text(x + 54, yy, label, 25, TEXT)
                s.text(x + node_w - 14, yy, f"→ {target}", 19, MUTED, anchor="end")
            else:
                s.text(x + 54, yy, label, 24, TEXT)
            yy += 38
        if more:
            s.text(x + 14, yy, f"+ {more} more columns (see §5)", 21, MUTED, italic=True)
    # in-domain edges
    edge_no = 0
    for fk in FKS:
        src, dst = fk["source"], fk_target(fk)
        if src not in tables or dst not in tables:
            continue
        edge_no += 1
        sx, sy, sw, sh = nodes[src]
        tx, ty, tw, th = nodes[dst]
        sc, sr = tables.index(src) % cols, tables.index(src) // cols
        tc, tr = tables.index(dst) % cols, tables.index(dst) // cols
        # ports: child source bottom/top, parent target top/bottom
        if sr <= tr:
            sy2 = sy + sh
            ty2 = ty
            channel_y = max(nodes[t][1] + nodes[t][3] for t in tables if tables.index(t) // cols == sr) + 18 + edge_no * 4
            sy2 = sy + sh
        else:
            sy2 = sy
            ty2 = ty + th
            channel_y = min(nodes[t][1] for t in tables if tables.index(t) // cols == sr) - 18 - edge_no * 4
        sx2 = sx + sw / 2
        tx2 = tx + tw / 2
        # vertical channel in the gutter beside the target column
        if tc >= sc:
            channel_x = tx - 28 + (edge_no % 4) * 6
        else:
            channel_x = tx + tw + 28 - (edge_no % 4) * 6
        d = (f"M{sx2} {sy2} L{sx2} {channel_y} L{channel_x} {channel_y} "
             f"L{channel_x} {ty2} L{tx2} {ty2}")
        s.path(d, color=BORDER, sw=2, marker="arrow")
        crow(s, sx2, sy2 + (12 if sr <= tr else -12),
             "down" if sr <= tr else "up", color=BORDER, size=12)
        # one tick at the parent
        s.line(tx2 - 12, ty2, tx2 + 12, ty2, color=BORDER, sw=3)
        card_label(s, sx2 + 22, sy2 + (24 if sr <= tr else -24), "N")
        card_label(s, tx2 - 24, ty2 - 10, "1")
    # legend
    s.rect(60, 1700, 2880, 70, fill=WHITE, stroke=GREY_BORDER, sw=2, rx=8)
    s.text(80, 1742, "PK primary key · FK foreign key → parent table · crow = many, tick = one · amber = legacy table (retained, not written by current code)", 22, MUTED)
    s.text(1900, 1742, f"Source: schema-introspection.json · sheet {index}/7", 21, MUTED)
    return save(s, f"erd-{index}", f"ERD sheet {index}: {name}",
                "docs/diagrams/schema-028/schema-introspection.json")


def build(only=None):
    wanted = set(only.split(",")) if only else None
    def run(name, fn):
        if wanted and name not in wanted:
            return
        fn()
    run("context", system_context)
    run("logical", logical_architecture)
    run("module", module_view)
    run("deployment", deployment_view)
    run("ai", ai_pipeline)
    run("lifecycle", assessment_lifecycle)
    run("practice-sequence", practice_sequence)
    run("grading-sequence", grading_sequence)
    run("quality", quality_gates)
    run("gantt", gantt)
    run("overview", schema_overview)
    for i, name in enumerate(DOMAINS, 1):
        if wanted and "erd" not in wanted and f"erd-{i}" not in wanted:
            continue
        if wanted and f"erd-{i}" not in wanted and "erd" not in wanted:
            continue
        erd_domain(name, i)
    (OUT / "manifest.json").write_text(
        json.dumps({"figures": MANIFEST}, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(f"wrote {OUT / 'manifest.json'} ({len(MANIFEST)} figures)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", default="")
    args = parser.parse_args()
    build(args.only)

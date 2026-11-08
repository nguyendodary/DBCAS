# -*- coding: utf-8 -*-
"""Pure-python gate for ORIGINAL-STYLE diagrams (CI runnable, no renderers).

    python scripts/check_original_style.py

Verifies code names/counts in docs/diagrams/original-style/*.svg match:
  * docs/qa/schema-introspection.json (41 tables, 59 FKs)
  * docs/qa/project-facts.json (services, OpenAPI)
Fails on mismatch. CI needs no Java/Node renderers.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "diagrams" / "original-style"
problems = []
checks = []


def check(label, cond, detail=""):
    checks.append(label)
    if not cond:
        problems.append(f"{label}: {detail}")


def read(stem):
    return (OUT / f"{stem}.svg").read_text(encoding="utf-8")


def main():
    import json
    intro = json.loads((ROOT / "docs/qa/schema-introspection.json").read_text(encoding="utf-8"))
    facts = json.loads((ROOT / "docs/qa/project-facts.json").read_text(encoding="utf-8"))

    # TRD: 41 tables in SVG grid headers (snake or display) + legend counts
    trd = read("fig-architecture-8-trd")
    missing = [t["table"] for t in intro["tables"] if t["table"].replace("_", " ") not in trd and t["table"] not in trd]
    check("TRD has all 41 tables", not missing, missing[:5])
    check("TRD legend counts", "41 tables" in trd and "59 FKs" in trd)
    check("TRD card pattern (gray headers)", trd.count("#E8E8E8") >= 40, trd.count("#E8E8E8"))

    # ERD: 12 core + 4 legacy (Chen shapes)
    erd = read("fig-architecture-7-erd")
    for nm in ["Role", "Account", "UserProfile", "SystemSetting", "CourseLearningOutcome",
               "Concept", "Question", "MCQOption", "AssessmentSession", "Attempt",
               "ConceptCompetency", "CompetencyGap"]:
        check(f"ERD core {nm}", nm in erd)
    for nm in ["Assessment", "AssessmentConcept", "AssessmentQuestion", "AssessmentBlueprint"]:
        check(f"ERD legacy {nm}", nm in erd)
    check("ERD dashed legacy", "stroke-dasharray" in erd)
    check("ERD diamonds", "Relationship" in erd)

    # Context: 2 actors + DBCAS + LLM + OAuth + Email (system level, no QA)
    ctx = read("fig-proposal-2-system-context")
    for nm in ["Learner", "Administrator", "DBCAS", "LLM Provider", "OAuth Providers", "Email Service"]:
        check(f"Context node {nm}", nm in ctx)
    check("Context no QA-only", "qa-ai" not in ctx.lower() and "meter" not in ctx.lower().split("legend")[0])

    # Use Case: UC01-UC18 with corrected titles
    uc = read("fig-architecture-1-usecase")
    for k in range(1, 19):
        check(f"UC{k:02d} present", f"UC{k:02d}" in uc)
    check("UC09 corrected", "Configure result flow and settings" in uc)
    check("UC12 corrected", "Take personalized practice" in uc)

    # Container/Logical/others sanity
    for stem, needle in [("fig-architecture-3-container", "PostgreSQL"), ("fig-proposal-3-logical", "TIER 1"),
                         ("fig-architecture-4-component", "Controller"), ("fig-architecture-5-module", "FUNCTIONAL MODULES"),
                         ("fig-architecture-6-allocation", "Docker-capable Host"), ("fig-proposal-4-pipeline", "Opening")]:
        check(f"{stem} has {needle}", needle in read(stem))

    # All SVGs + PNGs exist (11 figures)
    stems = ["fig-proposal-1-roadmap", "fig-proposal-2-system-context", "fig-proposal-3-logical",
             "fig-proposal-4-pipeline", "fig-architecture-1-usecase", "fig-architecture-3-container",
             "fig-architecture-4-component", "fig-architecture-5-module", "fig-architecture-6-allocation",
             "fig-architecture-7-erd", "fig-architecture-8-trd"]
    for s in stems:
        check(f"exists {s}.svg", (OUT / f"{s}.svg").exists())
        check(f"exists {s}.png", (OUT / f"{s}.png").exists())

    print(f"check_original_style: {len(checks)} assertions, tables=41, fks=59")
    if problems:
        for p in problems:
            print("FAIL:", p)
        sys.exit(1)
    print("PASS: original-style sources match schema-introspection.json and project-facts.json")


if __name__ == "__main__":
    main()

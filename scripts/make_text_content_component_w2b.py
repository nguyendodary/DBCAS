# -*- coding: utf-8 -*-
"""W2b helper: build text-content.json for the Component figure from an
explicit per-box line table, then verify the count.

The strings below were transcribed from 3x/4x crops of
ArchitectureDesign_ver1.1_image5.png (every box viewed, see report.md).
"""
import json
import os
import sys

FREE = [
    "Controller",
    "[Container: FastAPI routers, Pydantic validation]",
    "Service",
    "[Container: business logic]",
    "Repository",
    "[Container: SQLAlchemy data access]",
    "cache",
]

BOX = {
    # Controller row
    "S07": ["Auth", "Controller", "[FastAPI Router]", "Register, login,",
            "logout, admin", "provisioning"],
    "S13": ["Assessment", "Controller", "[FastAPI Router]",
            "Assessment setup,", "start session,", "serve next question"],
    "S09": ["Curriculum", "Controller", "[FastAPI Router]",
            "CLOs, concepts,", "CLO-concept", "mappings"],
    "S14": ["Question Bank", "Controller", "[FastAPI Router]",
            "Questions, options,", "datasets, rubrics,", "concept tags"],
    "S10": ["Analytics", "Controller", "[FastAPI Router]",
            "Competency profile,", "gaps, history,", "cohort analytics"],
    "S08": ["Attempt", "Controller", "[FastAPI Router]", "Submit MCQ / SQL /",
            "essay answers,", "run SQL"],
    "S12": ["Candidate", "Controller", "[FastAPI Router]", "Review, approve or",
            "reject AI question", "candidates"],
    # Service row
    "S24": ["Auth", "Service", "JWT, password", "hashing, RBAC"],
    "S22": ["Assessment", "Session Service", "60-min timer,", "auto-submit,",
            "13-question cap"],
    "S21": ["Curriculum", "Service", "CLO / concept rules,",
            "mapping confirmation", "uses LLM Gateway"],
    "S11": ["Question Bank", "Service", "Validated bank", "curation, tag",
            "confirmation", "uses LLM Gateway"],
    "S15": ["Competency &", "Gap Service", "Deterministic", "competency, gap",
            "flags, explanations", "uses LLM Gateway"],
    "S05": ["Grading", "Service", "MCQ key check, SQL", "result grading,",
            "rubric essay grading", "uses Sandbox Runner,", "LLM Gateway"],
    "S06": ["Adaptive Engine", "Service", "Next-question",
            "selection, candidate", "generation and checks",
            "uses LLM Gateway,", "Sandbox Runner"],
    # Repository row
    "S17": ["Account", "Repository", "Account, Role,", "AccountRole,",
            "UserProfile"],
    "S23": ["Assessment", "Repository", "Assessment,", "AssessmentConcept,",
            "AssessmentSession"],
    "S19": ["Curriculum", "Repository", "CourseLearning-",
            "Outcome, Concept,", "CLOConcept"],
    "S04": ["Question", "Repository", "Question,", "QuestionConcept,",
            "MCQOption,", "SQLTestDataset,", "Rubric"],
    "S26": ["Competency", "Repository", "ConceptCompetency,",
            "CompetencyGap"],
    "S18": ["Attempt", "Repository", "Attempt (answers,", "score, grading",
            "evidence)"],
    "S20": ["Selection &", "Candidate Repository", "SelectionLog,",
            "QuestionCandidate"],
    # bottom
    "S02": ["LLM Gateway", "[Component: Python]",
            "PII sanitizer, prompt templates,",
            "strict JSON schema, LLMCache"],
    "S01": ["Database", "[Container: PostgreSQL 17]",
            "Stores all application data"],
    "S03": ["Sandbox Runner", "[Component: Python, Docker]",
            "Read-only transaction, 3 s timeout,",
            "rollback after evaluation"],
    "S16": ["LLM Provider API", "[External System]"],
    "S25": ["SQL Sandbox", "[Container: Docker, PostgreSQL 17]"],
}

BOLD = {
    "Controller", "Service", "Repository",
    "Auth", "Controller", "[FastAPI Router]",
    "Assessment", "Curriculum", "Question", "Question Bank", "Analytics",
    "Attempt", "Competency",
    "Candidate", "Session Service", "Gap Service",
    "Grading", "Adaptive Engine",
    "Account", "Repository", "Selection &", "Candidate Repository",
    "LLM Gateway", "Sandbox Runner", "LLM Provider API", "SQL Sandbox",
    "Database",
}


def main():
    d = sys.argv[1]
    trace = json.load(open(os.path.join(d, "trace.json"), encoding="utf-8"))
    texts = trace["texts"]
    free = [x for x in texts if x["inside"] is None]
    assert len(free) == len(FREE), (len(free), len(FREE))
    by_shape = {}
    for x in texts:
        if x["inside"] is not None:
            by_shape.setdefault(x["inside"], []).append(x)
    # per-shape order is the trace's (y,x) order
    idx = {}
    for sid, lst in by_shape.items():
        assert len(lst) == len(BOX[sid]), (sid, len(lst), len(BOX[sid]))
        idx[sid] = 0
    box_ids, box_texts = [], []
    for x in texts:
        if x["inside"] is None:
            continue
        sid = x["inside"]
        s = BOX[sid][idx[sid]]
        idx[sid] += 1
        box_ids.append(x["id"])
        box_texts.append(s)
    out = {
        "note": ("Component Stage A strings, read from 3x/4x crops of "
                 "ArchitectureDesign_ver1.1_image5.png (every controller, "
                 "service, repository and bottom box viewed). "
                 "free_texts = texts with inside=null (sorted y,x); "
                 "box_texts = texts inside shapes (sorted y,x). 7 free + "
                 "132 box = 139 labels."),
        "free_ids": [x["id"] for x in free],
        "free_texts": FREE,
        "box_ids": box_ids,
        "box_texts": box_texts,
        "bold": [s for s in sorted(BOLD)],
        # exact per-id weight control: the detail lines "LLM Gateway" and
        # "Sandbox Runner" share a string with a bold box title but are
        # regular in the original.
        "bold_ids": [x["id"] for x in texts
                     if (x["inside"] is None and x["id"] in ("X001",
                                                              "X045",
                                                              "X087"))
                     or (x["inside"] is not None
                         and x["id"] not in ("X085", "X086")
                         and BOX[x["inside"]][
                             [y["id"] for y in by_shape[x["inside"]]]
                             .index(x["id"])] in BOLD
                         )],
        "ellipse_texts": [],
    }
    with open(os.path.join(d, "text-content.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print("wrote text-content.json:", len(free), "+", len(box_texts),
          "=", len(free) + len(box_texts), "labels")


if __name__ == "__main__":
    main()

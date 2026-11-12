# -*- coding: utf-8 -*-
"""W2b Component Stage B: apply the verified 7/7/7 content delta to the
Stage A clone.  Geometry (26 boxes, 3 dashed boundaries, 24 flows) is
untouched; only the text layer changes.  Font sizes are the Stage A sizes
(never smaller); new labels wrap at spaces and are re-centred in the same
boxes.

Writes trace.json / text-content.json / font-plan.json in the figure dir.
Usage:
  node scripts/run_py.mjs scripts/stage_b_component_w2b.py <figure_dir>
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_fonts import ink  # noqa: E402

# box id -> (title lines, title size, body lines, body size)
BOX = {
    # controllers (white on blue)
    "S07": (["Auth", "Controller"], 28,
            ["Register, login/logout,", "OAuth, password reset"], 22),
    "S13": (["Practice", "Controller"], 28,
            ["Practice setup, start,", "serve, submit"], 22),
    "S09": (["Curriculum", "Controller"], 28,
            ["CLOs, concepts,", "prerequisites, mappings"], 20),
    "S14": (["Question Bank", "Controller"], 28,
            ["Questions, options,", "datasets, rubrics,", "candidates"], 22),
    "S10": (["Analytics", "Controller"], 28,
            ["Profile, gaps, history,", "cohort analytics"], 22),
    "S08": (["Grading", "Controller"], 29,
            ["Answers, run SQL,", "review queue"], 20),
    "S12": (["Accounts", "Controller"], 28,
            ["Accounts, roles,", "system settings"], 21),
    # services (dark on light blue)
    "S24": (["Auth", "Service"], 28,
            ["JWT, password hashing,", "OAuth, throttling"], 21),
    "S22": (["Practice", "Service"], 27,
            ["Plan assembly, 30-min", "session, serve plan"], 23),
    "S21": (["Curriculum", "Service"], 28,
            ["CLO rules, concept", "mapping confirmation"], 22),
    "S11": (["Question Bank", "Service"], 28,
            ["Validated bank curation,", "tags, candidates"], 22),
    "S15": (["Competency &", "Gap Service"], 28,
            ["Deterministic", "competency, gaps,", "study ranking"], 22),
    "S05": (["Grading &", "Evaluation", "Service"], 28,
            ["MCQ key, SQL", "sandbox, Prompt", "Builder → Evaluator"], 23),
    "S06": (["Admin & Settings", "Service"], 28,
            ["Accounts, roles,", "global result flow"], 22),
    # repositories
    "S17": (["Account", "Repository"], 27,
            ["Account, Role,", "AccountRole, UserProfile"], 21),
    "S23": (["Session & Plan", "Repository"], 27,
            ["AssessmentSession,", "Plan, StartRequest"], 21),
    "S19": (["Curriculum", "Repository"], 28,
            ["CLO, Concept,", "CLOConcept"], 21),
    "S04": (["Question", "Repository"], 28,
            ["Question, Concept tag,", "MCQOption, Dataset,", "Rubric"], 22),
    "S26": (["Competency", "Repository"], 27,
            ["ConceptCompetency,", "Gap, EvaluationRecord"], 21),
    "S18": (["Grading", "Repository"], 29,
            ["Attempt, GradingJob,", "GradeReview, EditAudit"], 22),
    "S20": (["Audit & Settings", "Repository"], 28,
            ["SystemSetting, RoleAudit,", "Throttle, LLM cache"], 21),
    # bottom
    "S02": (["LLM Gateway"], 27,
            ["[Component: Python]", "PII sanitizer, prompt templates,",
             "strict JSON schema, LLM cache"], 21),
    "S01": (["Database"], 28,
            ["[Container: PostgreSQL 17]", "Stores all application data",
             "(41 tables)"], 22),
    "S03": (["Sandbox Runner"], 27,
            ["[Component: Python, Docker]",
             "Read-only transaction, 3 s timeout,",
             "rollback after evaluation"], 22),
    "S16": (["LLM Provider API"], 27, ["[External System]"], 21),
    "S25": (["SQL Sandbox"], 27,
            ["[Container: Docker, PostgreSQL 17]"], 17),
}

FREE = [
    ("Controller", "bold", 27, "#000000"),
    ("[Container: FastAPI routers, Pydantic validation]", "regular", 26,
     "#000000"),
    ("Service", "bold", 23, "#000000"),
    ("[Container: business logic]", "regular", 24, "#000000"),
    ("Repository", "bold", 22, "#000000"),
    ("[Container: SQLAlchemy data access]", "regular", 26, "#000000"),
    ("cache", "regular", 22, "#000000"),
]

INK = {}
for sid, (tl, ts, bl, bs) in BOX.items():
    if sid in ("S07", "S08", "S09", "S10", "S12", "S13", "S14"):
        INK[sid] = "#FFFFFF"
    elif sid in ("S17", "S18", "S19", "S04", "S26", "S20", "S23"):
        INK[sid] = "#06233F"
    elif sid in ("S24", "S22", "S21", "S11", "S15", "S05", "S06"):
        INK[sid] = "#0B2F55"
    else:
        INK[sid] = "#FFFFFF"


def main():
    d = sys.argv[1]
    trace = json.load(open(os.path.join(d, "trace-stage-a.json"),
                           encoding="utf-8"))
    shapes = {s["id"]: s for s in trace["shapes"]}

    def add(content, weight, size, x0, y0, inside, colour):
        b = ink(content, weight, size)
        iw, ih = b[2] - b[0], b[3] - b[1]
        return {"bbox": [int(round(x0)), int(y0), int(round(x0 + iw)),
                         int(y0 + ih)],
                "ink": colour, "inside": inside, "content": content,
                "weight": weight, "size": size, "x": float(round(x0)),
                "y": float(y0), "anchor": "top", "inkwh": [iw, ih]}

    texts = []
    for sid, (tlines, tsize, blines, bsize) in BOX.items():
        s = shapes[sid]
        x0, y0, x1, y1 = s["bbox"]
        cx = (x0 + x1) / 2.0
        # anchor on the Stage A measured first title/body tops
        ta = [t for t in trace["texts"] if t["inside"] == sid]
        ta.sort(key=lambda t: (t["bbox"][1], t["bbox"][0]))
        ty = ta[0]["bbox"][1]
        bi = min(len(tlines), len(ta) - 1)
        by = ta[bi]["bbox"][1]
        y = ty
        for ln in tlines:
            bb = ink(ln, "bold", tsize)
            iw = bb[2] - bb[0]
            assert x0 + 6 <= cx - iw / 2.0 and cx + iw / 2.0 <= x1 - 6, \
                (sid, "title too wide", ln, iw, x1 - x0)
            texts.append(add(ln, "bold", tsize, cx - iw / 2.0, y, sid,
                             INK[sid]))
            y += (bb[3] - bb[1]) + 2
        y = max(by, y + 4)
        for ln in blines:
            bb = ink(ln, "regular", bsize)
            iw = bb[2] - bb[0]
            assert x0 + 6 <= cx - iw / 2.0 and cx + iw / 2.0 <= x1 - 6, \
                (sid, "body too wide", ln, iw, x1 - x0)
            texts.append(add(ln, "regular", bsize, cx - iw / 2.0, y, sid,
                             INK[sid]))
            y += (bb[3] - bb[1]) + 1
        assert y - 1 <= y1 - 1, (sid, "overflow", y, y1)

    # free labels at their measured Stage A positions
    fa = [t for t in trace["texts"] if t["inside"] is None]
    fa.sort(key=lambda t: (t["bbox"][1], t["bbox"][0]))
    for (content, weight, size, colour), t in zip(FREE, fa):
        b = ink(content, weight, size)
        iw, ih = b[2] - b[0], b[3] - b[1]
        # cache keeps its measured left edge; boundary labels keep theirs
        if content == "cache":
            x0 = t["bbox"][0]
        else:
            x0 = t["bbox"][0]
        texts.append(add(content, weight, size, x0, t["bbox"][1], None,
                         colour))

    texts.sort(key=lambda t: (t["bbox"][1], t["bbox"][0]))
    for i, t in enumerate(texts):
        t["id"] = "B%03d" % (i + 1)

    free = [t for t in texts if t["inside"] is None]
    box = [t for t in texts if t["inside"] is not None]
    cont = {
        "note": ("Component Stage B (content delta verified 2026-11-09): "
                 "same canvas/boxes/boundaries/flows as Stage A; text layer "
                 "replaced with the section-7 7/7/7 labels. %d free + %d box "
                 "= %d labels." % (len(free), len(box), len(texts))),
        "free_ids": [t["id"] for t in free],
        "free_texts": [t["content"] for t in free],
        "box_ids": [t["id"] for t in box],
        "box_texts": [t["content"] for t in box],
        "bold": [t["content"] for t in texts if t["weight"] == "bold"],
        "ellipse_texts": [],
    }
    plan = {}
    for t in texts:
        plan[t["id"]] = {"weight": t["weight"], "size": t["size"],
                         "anchor": "top", "measured": t["bbox"],
                         "ink": t["inkwh"]}
    out_trace = dict(trace, texts=[{k: v for k, v in t.items()
                                    if k not in ("content", "weight",
                                                 "size", "x", "y",
                                                 "anchor", "inkwh")}
                                    for t in texts])
    json.dump(out_trace, open(os.path.join(d, "trace.json"), "w",
                              encoding="utf-8"), indent=1)
    json.dump(cont, open(os.path.join(d, "text-content.json"), "w",
                         encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump(plan, open(os.path.join(d, "font-plan.json"), "w",
                         encoding="utf-8"), indent=1, ensure_ascii=False)
    print("stage B component: %d texts (%d free + %d box)"
          % (len(texts), len(free), len(box)))


if __name__ == "__main__":
    main()

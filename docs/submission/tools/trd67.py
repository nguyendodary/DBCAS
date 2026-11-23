# -*- coding: utf-8 -*-
"""Generate the 26 continuation TRD cards in the shipped 41-card style.

The original pages 1-5 are kept as the frozen source.  This tool appends pages
6-11 for the tables introduced by migrations 020-028, using the same 4-column
card grid, typography, dividers, cross-page stubs and palette as the shipped
pages.  It reads the generated schema-028 introspection (not docs/qa) and
writes only under the requested output directory.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from docs_qa_guard import ensure_safe_output  # noqa: E402
import trd_common_f6 as common  # noqa: E402
import build_trd_stage_b_f6 as cards  # noqa: E402
from diagram_style import LEGEND_COUNTS, TRD, render_svg  # noqa: E402

ORIGINAL_PAGES = [
    ["account", "account_identity", "account_role_audit", "user_profile",
     "refresh_session", "oauth_handoff", "role", "account_role",
     "login_throttle", "assessment_question"],
    ["concept", "question_candidate", "course_learning_outcome", "clo_concept",
     "question_concept", "password_reset_token", "llm_cache", "assessment_concept",
     "concept_dependency", "password_reset_audit", "system_setting"],
    ["question", "question_translation", "mcq_option", "rubric",
     "selection_log", "sql_test_dataset", "competency_gap"],
    ["assessment_session", "attempt", "session_question_plan", "session_start_request",
     "adaptive_event", "evaluation_record", "result_release_event"],
    ["assessment", "assessment_blueprint", "grade_review", "grading_job",
     "grade_edit_audit", "concept_competency"],
]
CONTINUATION_PAGES = [
    ["ai_stage_run", "review_request", "course_document", "session_final_result"],
    ["attempt_rubric_criterion", "review_deviation", "question_report", "ai_stage_attempt"],
    ["session_result_version", "document_chunk", "question_rubric_criterion", "ai_prompt_record"],
    ["session_result_analysis", "question_evidence", "question_rubric_profile", "ai_stage_validation"],
    ["session_result_criterion_score", "session_result_publication", "question_clo", "retention_purge_audit"],
    ["session_result_version_score", "tab_leave_interval", "prompt_access_audit", "document_clo",
     "review_deviation_confirmation", "ai_prompt_content"],
]


def build(schema_path, outdir):
    outdir = ensure_safe_output(outdir, label="TRD output")
    outdir.mkdir(parents=True, exist_ok=True)
    common.INTRO = str(schema_path)
    raw, tables = common.load_schema()
    by_name = {t["table"]: t for t in tables}
    all_pages = ORIGINAL_PAGES + CONTINUATION_PAGES
    page_of = {name: i + 1 for i, names in enumerate(all_pages) for name in names}
    if set(page_of) != set(by_name):
        raise SystemExit(f"page map mismatch: missing={sorted(set(by_name) - set(page_of))} "
                         f"extra={sorted(set(page_of) - set(by_name))}")

    stubs = {}
    for fk in raw["foreign_keys"]:
        source, dest = fk["source"], fk["destination"]
        if page_of[source] < 6 and page_of[dest] < 6:
            continue
        if page_of[source] >= 6:
            stubs.setdefault((source, fk["columns"][0]), []).append({
                "text": f"to {dest} (p{page_of[dest]})",
                "color": TRD["colors"]["outgoing"], "dir": "out", "fk": fk["constraint"]})
        if page_of[dest] >= 6:
            stubs.setdefault((dest, fk["reference_columns"][0]), []).append({
                "text": f"from {source} (p{page_of[source]})",
                "color": TRD["colors"]["incoming"], "dir": "in", "fk": fk["constraint"]})

    outputs = []
    for index, names in enumerate(CONTINUATION_PAGES, start=6):
        rows = [names[i:i + 4] for i in range(0, len(names), 4)]
        page_cards = cards.make_cards(by_name, rows, TRD["row_height"], stubs)
        texts, underlines = cards.card_texts(page_cards, stubs)
        max_bottom = max(c["bbox"][1] + c["bbox"][3] for c in page_cards)
        if max_bottom > TRD["canvas"][1] - 20:
            raise SystemExit(f"page {index} overflows: {max_bottom}")
        page = {
            "page": index, "tables": names, "canvas": {"w": TRD["canvas"][0], "h": TRD["canvas"][1]},
            "cards": page_cards, "texts": texts, "underlines": underlines,
            "segments": [], "connectors": [], "legend": None,
            "stubs": [item for values in stubs.values() for item in values if item.get("text_id")],
        }
        svg = outdir / f"trd-{index}.svg"
        common.svg_page(page, str(svg))
        svg.write_text(
            svg.read_text(encoding="utf-8").replace(
                "</svg>",
                f'<text x="40" y="2040" font-family="Arial" font-size="30" fill="#1A1A1A">'
                f'Page {index} of 11 \u00b7 {LEGEND_COUNTS}</text>\n</svg>'),
            encoding="utf-8")
        png = outdir / f"trd-{index}.png"
        render_svg(svg, png, *TRD["canvas"])
        outputs.append((index, svg, png, len(page_cards), sum(len(c["rows"]) for c in page_cards), max_bottom))

    spec = {
        "schema": str(schema_path),
        "counts": {
            "tables": len(raw["tables"]),
            "columns": sum(len(t["columns"]) for t in raw["tables"]),
            "foreign_keys": len(raw["foreign_keys"]),
            "migrations": len(raw["migrations"]),
            "pages_total": 11,
            "continuation_pages": len(CONTINUATION_PAGES),
        },
        "original_pages": ORIGINAL_PAGES,
        "continuation_pages": CONTINUATION_PAGES,
        "legend": LEGEND_COUNTS,
        "style": TRD,
    }
    (outdir / "trd-spec-67.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    return outputs, spec


def check(spec):
    counts = spec["counts"]
    expected = {"tables": 67, "columns": 561, "foreign_keys": 122, "migrations": 28,
                "pages_total": 11}
    wrong = {key: (counts.get(key), value) for key, value in expected.items()
             if counts.get(key) != value}
    pages = spec["original_pages"] + spec["continuation_pages"]
    names = [name for page in pages for name in page]
    if len(names) != len(set(names)):
        wrong["duplicate_tables"] = sorted({n for n in names if names.count(n) > 1})
    if len(names) != 67:
        wrong["card_count"] = (len(names), 67)
    if wrong:
        raise SystemExit(f"TRD spec mismatch: {wrong}")
    print("TRD 67: 67 tables, 561 columns, 122 FKs, 28 migrations, 11 pages")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--schema", default=str(ROOT / "docs/diagrams/schema-028/schema-introspection.json"))
    ap.add_argument("--out", default=str(Path(__file__).with_name("out") / "trd67"))
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args(argv)
    if args.check_only:
        spec_path = Path(args.out) / "trd-spec-67.json"
        if not spec_path.exists():
            raise SystemExit(f"spec not found: {spec_path}; run without --check-only first")
        check(json.loads(spec_path.read_text(encoding="utf-8")))
        return 0
    outputs, spec = build(Path(args.schema), Path(args.out))
    check(spec)
    for index, svg, png, card_count, columns, bottom in outputs:
        print(f"page {index}: {card_count} cards, {columns} columns, bottom={bottom:.0f} -> {png.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

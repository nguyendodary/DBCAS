# -*- coding: utf-8 -*-
"""Generate the ERD 2/2 continuation page in the shipped entity style.

The first ERD page is the frozen conceptual 21-entity figure.  This page adds
the 26 migration-020-028 tables as entity cards with key ovals, using the same
4-column grid, stroke, typography and legend strip as the shipped figure.
"""
from __future__ import annotations

import argparse
import json
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from docs_qa_guard import ensure_safe_output  # noqa: E402
from diagram_style import ERD, LEGEND_COUNTS, render_svg  # noqa: E402

MISSING = [
    "ai_prompt_content", "ai_prompt_record", "ai_stage_attempt", "ai_stage_run",
    "ai_stage_validation", "attempt_rubric_criterion", "course_document",
    "document_chunk", "document_clo", "prompt_access_audit", "question_clo",
    "question_evidence", "question_report", "question_rubric_criterion",
    "question_rubric_profile", "retention_purge_audit", "review_deviation",
    "review_deviation_confirmation", "review_request", "session_final_result",
    "session_result_analysis", "session_result_criterion_score",
    "session_result_publication", "session_result_version",
    "session_result_version_score", "tab_leave_interval",
]


def camel(name):
    return "".join(part.capitalize() for part in name.split("_"))


def primary_key(table):
    for constraint in table.get("constraints", []):
        if constraint.get("type") == "p":
            return constraint.get("columns", [])
    return []


def build(schema_path, outdir):
    outdir = ensure_safe_output(outdir, label="ERD output")
    outdir.mkdir(parents=True, exist_ok=True)
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    by_name = {table["table"]: table for table in schema["tables"]}
    missing = [name for name in MISSING if name not in by_name]
    if missing:
        raise SystemExit(f"schema is missing tables: {missing}")
    width, height = ERD["canvas"]
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="{ERD["colors"]["paper"]}"/>',
    ]
    for index, table in enumerate(MISSING):
        col, row = index % ERD["columns"], index // ERD["columns"]
        x, y = ERD["x"][col], ERD["y"][row]
        w, h = ERD["entity_width"], ERD["entity_height"]
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{ERD["colors"]["body"]}" stroke="{ERD["colors"]["stroke"]}" stroke-width="4"/>')
        svg.append(f'<text x="{x + w / 2}" y="{y + 52}" font-family="{ERD["font_family"]}" font-size="{ERD["title_size"]}" font-weight="bold" text-anchor="middle" fill="{ERD["colors"]["ink"]}">{escape(camel(table))}</text>')
        keys = primary_key(by_name[table])
        key_text = ", ".join(keys)
        key_width = max(220, 6.4 * len(key_text) + 40)
        key_x = x + w / 2 - key_width / 2
        key_y = y + h + 18
        svg.append(f'<rect x="{key_x}" y="{key_y}" width="{key_width}" height="38" rx="19" fill="{ERD["colors"]["body"]}" stroke="{ERD["colors"]["stroke"]}" stroke-width="2.5"/>')
        svg.append(f'<text x="{x + w / 2}" y="{key_y + 26}" font-family="{ERD["font_family"]}" font-size="{ERD["key_size"]}" text-anchor="middle" fill="{ERD["colors"]["ink"]}">{escape(key_text)}</text>')
    legend_y = ERD["y"][-1] + ERD["entity_height"] + 150
    svg.append(f'<rect x="760" y="{legend_y}" width="2780" height="150" rx="20" fill="white" stroke="{ERD["colors"]["stroke"]}" stroke-width="2.5"/>')
    svg.append(f'<text x="800" y="{legend_y + 45}" font-family="{ERD["font_family"]}" font-size="26" font-weight="bold" fill="{ERD["colors"]["ink"]}">DBCAS full schema \u2014 additional tables</text>')
    svg.append(f'<text x="800" y="{legend_y + 85}" font-family="{ERD["font_family"]}" font-size="24" fill="{ERD["colors"]["ink"]}">{escape(LEGEND_COUNTS)}. This page extends Figure 7/1 with the 26 tables introduced by migrations 020\u2013028; keys are shown inside ovals.</text>')
    svg.append("</svg>")
    svg_path = outdir / "erd-extra.svg"
    svg_path.write_text("\n".join(svg), encoding="utf-8")
    png_path = outdir / "erd-extra.png"
    render_svg(svg_path, png_path, width, height)
    spec = {
        "schema": str(schema_path),
        "page": "2/2",
        "tables": MISSING,
        "counts": {"tables": len(schema["tables"]),
                   "columns": sum(len(t["columns"]) for t in schema["tables"]),
                   "foreign_keys": len(schema["foreign_keys"]),
                   "migrations": len(schema["migrations"])},
        "legend": LEGEND_COUNTS,
        "style": ERD,
    }
    (outdir / "erd-extra-spec.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    return svg_path, png_path, spec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--schema", default=str(ROOT / "docs/diagrams/schema-028/schema-introspection.json"))
    ap.add_argument("--out", default=str(Path(__file__).with_name("out") / "erd67"))
    args = ap.parse_args(argv)
    svg, png, spec = build(Path(args.schema), Path(args.out))
    if len(spec["tables"]) != 26:
        raise SystemExit("expected 26 continuation tables")
    print(f"ERD 2/2: 26 entities -> {svg.name}, {png.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

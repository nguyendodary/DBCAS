# -*- coding: utf-8 -*-
"""Build the five C1SE.70 DBCAS ver1.3 Word deliverables.

    python scripts/build_submission_docs.py            # all five documents
    python scripts/build_submission_docs.py --only proposal,architecture
    python scripts/build_submission_docs.py --out docs/submission/final

Content lives in scripts/submission_content/*.py; layout in
scripts/submission_style.py.  The generator writes only to the output directory
(in the repository by default) and never edits the v1.2 sources in
docs/submission or docs/academic.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import submission_style as style  # noqa: E402
from submission_content import (  # noqa: E402
    architecture, codestandards, database, proposal, technicalreport,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs" / "submission" / "final"


@dataclass
class Spec:
    key: str
    title: str
    header: str
    category: str
    filename: str
    blocks: list = field(default_factory=list)


DOCS = [
    Spec("proposal", "Project Proposal", "PROJECT PROPOSAL", "Proposal",
         "C1SE.70_ProposalDocument_DBCAS_ver1.3.docx", proposal.BLOCKS),
    Spec("architecture", "Architecture Design Document",
         "ARCHITECTURE DESIGN", "Architecture",
         "C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx",
         architecture.BLOCKS),
    Spec("database", "Database Design Document", "DATABASE DESIGN",
         "Database", "C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx",
         database.BLOCKS),
    Spec("codestandards", "Code Standards Document", "CODE STANDARDS",
         "Code standards", "C1SE.70_CodeStandards_DBCAS_ver1.3.docx",
         codestandards.BLOCKS),
    Spec("technicalreport", "Technical Report", "TECHNICAL REPORT",
         "Technical report", "C1SE.70_TechnicalReport_DBCAS_ver1.3.docx",
         technicalreport.BLOCKS),
]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--only", default="", help="comma list of document keys")
    parser.add_argument("--list", action="store_true", help="print keys and exit")
    args = parser.parse_args(argv)

    if args.list:
        for spec in DOCS:
            print(spec.key, spec.filename, len(spec.blocks), "blocks")
        return 0

    wanted = {key.strip() for key in args.only.split(",") if key.strip()}
    unknown = wanted - {spec.key for spec in DOCS}
    if unknown:
        print(f"unknown document keys: {sorted(unknown)}", file=sys.stderr)
        return 2

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for spec in DOCS:
        if wanted and spec.key not in wanted:
            continue
        target = out / spec.filename
        style.build_document(spec, spec.blocks, target)
        written.append((spec.filename, target.stat().st_size))
    for name, size in written:
        print(f"built {name} ({size:,} bytes) in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""Finalise the five submission DOCX with Word, export PDFs, record page counts.

    python scripts/finalize_submission_docs.py

Word COM updates the TOC and every field, saves the DOCX in place, exports a
PDF next to it and reports the page count.  The counts are written to
docs/submission/final/verification/page-counts.json.  This is a Windows-only
step; when Word is unavailable the script reports it and leaves the files
untouched.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "docs" / "submission" / "final"
RENDERED = FINAL / "rendered"
REPORT = FINAL / "verification" / "page-counts.json"
SCRIPT = ROOT / "scripts" / "word_finalize.ps1"

CORE = "docProps/core.xml"
NS = {
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dc": "http://purl.org/dc/elements/1.1/",
}
PROPS = {
    "dc:creator": "Do, Nguyen Quoc",
    "cp:lastModifiedBy": "Do, Nguyen Quoc",
}

DOCS = [
    "C1SE.70_ProposalDocument_DBCAS_ver1.3.docx",
    "C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx",
    "C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx",
    "C1SE.70_CodeStandards_DBCAS_ver1.3.docx",
    "C1SE.70_TechnicalReport_DBCAS_ver1.3.docx",
]


def restore_properties(path):
    """Word rewrites cp:lastModifiedBy; restore the required owner metadata."""
    tmp = path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(path) as source,             zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as target:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename == CORE:
                root = etree.fromstring(data)
                for tag, value in PROPS.items():
                    element = root.find(tag, NS)
                    if element is None:
                        element = etree.SubElement(root, f"{{{NS[tag.split(':')[0]]}}}{tag.split(':')[1]}")
                    element.text = value
                data = etree.tostring(root, xml_declaration=True,
                                      encoding="UTF-8", standalone=True)
            target.writestr(item, data)
    shutil.move(str(tmp), str(path))


def main(argv=None):
    RENDERED.mkdir(parents=True, exist_ok=True)
    counts = {}
    words = {}
    for name in DOCS:
        path = FINAL / name
        pdf = RENDERED / (path.stem + ".pdf")
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(SCRIPT), "-Path", str(path), "-Pdf", str(pdf)],
            capture_output=True, text=True)
        output = result.stdout + result.stderr
        pages = re.search(r"PAGES=(\d+)", output)
        word_count = re.search(r"WORDS=(\d+)", output)
        if result.returncode != 0 or not pages:
            print(f"FAILED {name}: {output.strip()[:400]}", file=sys.stderr)
            return 1
        restore_properties(path)
        counts[name] = int(pages.group(1))
        words[name] = int(word_count.group(1)) if word_count else None
        print(f"{name}: {counts[name]} pages, {words[name]} words")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"pages": counts, "words": words},
                                 indent=2) + "\n", encoding="utf-8")
    print("wrote", REPORT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

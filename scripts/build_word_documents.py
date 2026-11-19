"""Prepare review copies of the approved English Word documents.

Apply explicit paragraph edits with docx_inplace, keeping the original styles,
tables, numbering and media. Run verify_docx on the output before approval.
"""

import argparse
import json
import shutil
from pathlib import Path

from docx_inplace import edit_docx
from verify_docx import ACA, FILENAMES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New directory for the three review copies")
    parser.add_argument("--edits", type=Path, help="JSON object mapping document filenames to paragraph edits")
    args = parser.parse_args()
    edits = json.loads(args.edits.read_text(encoding="utf-8")) if args.edits else {}
    if not isinstance(edits, dict) or edits.keys() - set(FILENAMES):
        parser.error("edits must map approved v1.2 filenames to paragraph edits")
    args.output.mkdir()
    for name in FILENAMES:
        source, candidate = ACA / name, args.output / name
        if edits.get(name):
            edit_docx(source, candidate, edits[name], require_matches=True)
        else:
            shutil.copyfile(source, candidate)
        print(candidate)


if __name__ == "__main__":
    main()

# Extracted baseline media

`MANIFEST.sha256` records the 37 body images extracted byte-for-byte from
`Documents/Final-ver1.3/C1SE.70_*_DBCAS_ver1.3.docx` for the diagram audit.
The images themselves are not duplicated in the repository; re-extract them
with `scripts/restore_original_diagrams.py` (or any unzip of `word/media`).

Every file's SHA-256, pixel size and match result is also recorded in
[`diagram-audit.json`](../diagram-audit.json) and
[`diagram-audit.md`](../diagram-audit.md).

The five shipped DOCX embed the same bytes; do not edit the extracted files to
change a document.

# -*- coding: utf-8 -*-
"""Small, dependency-light toolkit for the DBCAS submission .docx files.

The functions are deliberately explicit: text and table edits preserve the
existing runs/paragraph/table formatting, images are replaced at the existing
display size, and package/style audits compare OOXML parts with C14N.  They do
not rebuild covers, styles or the document structure.

Usage examples are in docs/submission/tools/README.md.  All outputs are refused
under docs/qa/** by scripts/docs_qa_guard.py.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from lxml import etree
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from docx_inplace import edit_docx  # noqa: E402
from docs_qa_guard import ensure_safe_output  # noqa: E402

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
PARTS = ("word/styles.xml", "word/theme/theme1.xml", "word/settings.xml", "word/numbering.xml")


def q(ns: str, tag: str) -> str:
    return f"{{{ns}}}{tag}"


def _c14n(data: bytes) -> bytes:
    return etree.tostring(etree.fromstring(data), method="c14n")


def _paragraph_text(paragraph: Paragraph) -> str:
    return "".join(node.text or "" for node in paragraph._p.iter(q(W, "t")))


def replace_text(src, dst, edits, *, require_matches=True):
    """Replace text in runs while preserving run/paragraph formatting.

    ``edits`` is the docx_inplace format: [{"old": "...", "new": "..."}] or
    [{"paragraph": "...", "new": "..."}].  Returns the match counts.
    """
    return edit_docx(src, dst, edits, require_matches=require_matches)


def set_paragraph_text(paragraph: Paragraph, text: str):
    """Set a paragraph's text, keeping the first run's properties."""
    runs = paragraph.runs
    if runs:
        runs[0].text = text
        for run in runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(text)


def clone_paragraph(paragraph: Paragraph, *, text=None, after=True) -> Paragraph:
    """Clone a paragraph (including pPr and first-run rPr) into the same parent."""
    new_p = copy.deepcopy(paragraph._p)
    parent = paragraph._p.getparent()
    index = list(parent).index(paragraph._p)
    parent.insert(index + 1 if after else index, new_p)
    result = Paragraph(new_p, paragraph._parent)
    if text is not None:
        set_paragraph_text(result, text)
    return result


def set_cell_text(cell, text: str):
    """Set a table cell's text, keeping the first run's formatting."""
    paragraph = cell.paragraphs[0]
    set_paragraph_text(paragraph, text)


def clone_table_row(table: Table, row_index=-1, values=None):
    """Clone a row (including trPr and cell formatting) and optionally set text."""
    row = table.rows[row_index]
    new_tr = copy.deepcopy(row._tr)
    table._tbl.append(new_tr)
    from docx.table import _Row
    result = _Row(new_tr, table)
    if values is not None:
        for cell, value in zip(result.cells, values):
            set_cell_text(cell, str(value))
    return result


def replace_image(src, dst, media_name: str, new_image, *, width_emu=None):
    """Replace an embedded image and preserve its inline display size."""
    media_name = media_name.replace("\\", "/")
    if media_name.startswith("word/"):
        media_name = media_name[5:]
    new_bytes = Path(new_image).read_bytes()
    with zipfile.ZipFile(src) as zin:
        names = set(zin.namelist())
        document = etree.fromstring(zin.read("word/document.xml"))
        relationships = etree.fromstring(zin.read("word/_rels/document.xml.rels"))
        target = "media/" + Path(media_name).name
        rid = next((rel.get("Id") for rel in relationships
                    if rel.get("Target") == target), None)
        if rid is None:
            raise ValueError(f"image relationship not found for {media_name}")
        inline_count = 0
        for inline in document.iter(q(WP, "inline")):
            blip = inline.find(".//" + q(A, "blip"))
            if blip is None or blip.get(q(R, "embed")) != rid:
                continue
            inline_count += 1
            if width_emu:
                with Image.open(new_image) as image:
                    w, h = image.size
                for ext in inline.iter(q(A, "ext")):
                    ext.set("cx", str(int(width_emu)))
                    ext.set("cy", str(int(width_emu * h / w)))
                extent = inline.find(q(WP, "extent"))
                if extent is not None:
                    extent.set("cx", str(int(width_emu)))
                    extent.set("cy", str(int(width_emu * h / w)))
        if not inline_count:
            raise ValueError(f"no inline image uses {media_name}")
        new_doc = etree.tostring(document, xml_declaration=True, encoding="UTF-8", standalone=True)
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    data = new_doc
                elif item.filename == "word/" + media_name:
                    data = new_bytes
                zout.writestr(item, data)
    return inline_count


def _image_hashes(path):
    with zipfile.ZipFile(path) as z:
        return [(n, hashlib.sha256(z.read(n)).hexdigest()[:16])
                for n in sorted(z.namelist()) if n.startswith("word/media/")]


def audit_package(before, after, *, cover_paragraphs=11):
    """Compare style parts, cover and media between two docx packages."""
    before, after = Path(before), Path(after)
    with zipfile.ZipFile(before) as a, zipfile.ZipFile(after) as b:
        parts = {part: (part in a.namelist() and part in b.namelist()
                        and _c14n(a.read(part)) == _c14n(b.read(part)))
                 for part in PARTS}
    left, right = Document(before), Document(after)
    cover_equal = ([_paragraph_text(p) for p in left.paragraphs[:cover_paragraphs]]
                   == [_paragraph_text(p) for p in right.paragraphs[:cover_paragraphs]])
    images_a, images_b = _image_hashes(before), _image_hashes(after)
    changed = [i for i, (x, y) in enumerate(zip(images_a, images_b)) if x[1] != y[1]]
    return {
        "parts_c14n_equal": parts,
        "cover_text_equal": cover_equal,
        "paragraphs": {"before": len(left.paragraphs), "after": len(right.paragraphs)},
        "tables": {"before": len(left.tables), "after": len(right.tables)},
        "images": {"before": len(images_a), "after": len(images_b), "changed_indices": changed},
    }


def validate_docx(path):
    """Return package-integrity problems (empty list means valid)."""
    problems = []
    try:
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:
                problems.append("zip CRC failure")
            names = set(z.namelist())
            for required in ("word/document.xml", "word/_rels/document.xml.rels"):
                if required not in names:
                    problems.append(f"missing {required}")
            document = etree.fromstring(z.read("word/document.xml"))
            relationships = etree.fromstring(z.read("word/_rels/document.xml.rels"))
            ids = [rel.get("Id") for rel in relationships]
            if len(ids) != len(set(ids)):
                problems.append("duplicate relationship id")
            for rel in relationships:
                target = rel.get("Target") or ""
                if rel.get("TargetMode") == "External":
                    continue
                resolved = "word/" + target.lstrip("/")
                if target.startswith("media/") and resolved not in names:
                    problems.append(f"missing media {target}")
    except Exception as exc:
        problems.append(f"{type(exc).__name__}: {exc}")
    return problems


def _word_export_script():
    return Path(__file__).with_name("render_docx.ps1")


def refresh_fields(src, dst=None):
    """Refresh fields/TOC/list-of-figures.

    Prefers LibreOffice when a headless binary exists; otherwise uses the
    repository's Word COM helper (scripts/update_fields.ps1).  The output path
    is refused under docs/qa/**.
    """
    src = Path(src).resolve()
    dst = ensure_safe_output(dst or src.with_name(src.stem + "-fields.docx"),
                             label="refreshed docx")
    if dst == src:
        raise ValueError("choose a distinct output path; in-place field refresh is not performed")
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        with tempfile.TemporaryDirectory(prefix="dbcas-fields-") as tmp:
            subprocess.run([soffice, "--headless", "--convert-to", "docx",
                            "--outdir", tmp, str(src)], check=True)
            generated = Path(tmp) / (src.stem + ".docx")
            if not generated.exists():
                raise RuntimeError("LibreOffice did not produce a docx")
            shutil.copy2(generated, dst)
    else:
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-File", str(ROOT / "scripts/update_fields.ps1"),
                        "-Docx", str(src), "-Out", str(dst)], check=True)
    return dst


def render_pdf(docx, pdf=None):
    """Convert a .docx to PDF using LibreOffice when available, else Word COM."""
    docx = Path(docx).resolve()
    pdf = Path(pdf or docx.with_suffix(".pdf")).resolve()
    ensure_safe_output(pdf, label="PDF")
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        with tempfile.TemporaryDirectory(prefix="dbcas-render-") as tmp:
            subprocess.run([soffice, "--headless", "--convert-to", "pdf",
                            "--outdir", tmp, str(docx)], check=True)
            generated = Path(tmp) / (docx.stem + ".pdf")
            if not generated.exists():
                raise RuntimeError("LibreOffice did not produce a PDF")
            shutil.copy2(generated, pdf)
    else:
        script = _word_export_script()
        if not script.exists():
            raise RuntimeError("no soffice and no Word export helper")
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-File", str(script), "-Docx", str(docx), "-Pdf", str(pdf)],
                       check=True)
    return pdf


def render_pdf_pages(pdf, outdir, dpi=110):
    import fitz
    outdir = ensure_safe_output(outdir, label="rendered pages")
    outdir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    pages = []
    for i, page in enumerate(doc, 1):
        path = outdir / f"page-{i:03d}.png"
        page.get_pixmap(dpi=dpi).save(path)
        pages.append(path)
    doc.close()
    return pages


def make_pair(before, after, out, *, title="before / after"):
    """Build a labelled side-by-side image."""
    out = ensure_safe_output(out, label="pair image")
    a, b = Image.open(before).convert("RGB"), Image.open(after).convert("RGB")
    gap, label = 28, 34
    width, height = a.width + b.width + gap, max(a.height, b.height) + label
    canvas = Image.new("RGB", (width, height), "white")
    canvas.paste(a, (0, label))
    canvas.paste(b, (a.width + gap, label))
    draw = ImageDraw.Draw(canvas)
    draw.text((8, 10), f"{title}: BEFORE", fill="black")
    draw.text((a.width + gap + 8, 10), "AFTER", fill="black")
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    return out


def fact_audit(*, schema_path=None, openapi_path=None, app_jsx=None, tests=None, out=None):
    """Check document-facing counts against repository artefacts."""
    schema_path = Path(schema_path or ROOT / "docs/diagrams/schema-028/schema-introspection.json")
    openapi_path = Path(openapi_path or ROOT / "docs/openapi.json")
    app_jsx = Path(app_jsx or ROOT / "frontend/src/App.jsx")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    facts = {
        "tables": len(schema["tables"]),
        "columns": sum(len(t["columns"]) for t in schema["tables"]),
        "foreign_keys": len(schema["foreign_keys"]),
        "indexes": len(schema.get("indexes", [])),
        "migrations": len(schema.get("migrations", [])),
        "openapi_paths": None,
        "operations": None,
        "frontend_routes": len(set(re.findall(r'path="([^"]+)"', app_jsx.read_text(encoding="utf-8")))),
    }
    if openapi_path.exists():
        spec = json.loads(openapi_path.read_text(encoding="utf-8"))
        facts["openapi_paths"] = len(spec.get("paths", {}))
        facts["operations"] = sum(1 for item in spec.get("paths", {}).values()
                                  for verb in item if verb in ("get", "post", "put", "patch", "delete"))
    if tests:
        facts["tests"] = json.loads(Path(tests).read_text(encoding="utf-8"))
    if out:
        out = ensure_safe_output(out, label="fact audit")
        out.write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
    return facts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("replace")
    p.add_argument("src"); p.add_argument("dst"); p.add_argument("edits")
    p = sub.add_parser("audit")
    p.add_argument("before"); p.add_argument("after")
    p = sub.add_parser("validate")
    p.add_argument("docx")
    p = sub.add_parser("refresh")
    p.add_argument("docx"); p.add_argument("--out")
    p = sub.add_parser("render")
    p.add_argument("docx"); p.add_argument("--pdf")
    p.add_argument("--pages-dir")
    p = sub.add_parser("pair")
    p.add_argument("before"); p.add_argument("after"); p.add_argument("out")
    p = sub.add_parser("facts")
    p.add_argument("--out")
    args = ap.parse_args(argv)
    if args.command == "replace":
        edits = json.loads(Path(args.edits).read_text(encoding="utf-8"))
        for old, done, want in replace_text(args.src, args.dst, edits):
            print(f"{done}x (want {want}): {old!r}")
    elif args.command == "audit":
        print(json.dumps(audit_package(args.before, args.after), indent=2))
    elif args.command == "validate":
        problems = validate_docx(args.docx)
        print("OK" if not problems else "\n".join(problems))
        return 0 if not problems else 1
    elif args.command == "refresh":
        print(refresh_fields(args.docx, args.out))
    elif args.command == "render":
        pdf = render_pdf(args.docx, args.pdf)
        print(pdf)
        if args.pages_dir:
            print("\n".join(str(p) for p in render_pdf_pages(pdf, args.pages_dir)))
    elif args.command == "pair":
        print(make_pair(args.before, args.after, args.out))
    elif args.command == "facts":
        print(json.dumps(fact_audit(out=args.out), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
